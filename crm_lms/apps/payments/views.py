from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q, Prefetch
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.core.mixins import admin_required
from apps.core.mixins_organization import get_current_organization, filter_by_organization
from .models import Payment, OrganizationReceipt
from apps.students.models import Student
from apps.courses.models import Course, CourseStudent
from apps.settings.models import PaymentMethod

from django import forms


class OrganizationReceiptForm(forms.ModelForm):
    class Meta:
        model = OrganizationReceipt
        fields = ['organization_name', 'organization_type', 'inn', 'tax_per_receipt', 'is_active']
        widgets = {
            'organization_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization_type': forms.Select(attrs={'class': 'form-select'}),
            'inn': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_per_receipt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['student', 'course', 'amount', 'payment_method', 'paid_at', 'comment']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'paid_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Фильтруем студентов по организации
        if self.request:
            from apps.core.mixins import get_current_organization
            current_org = get_current_organization(self.request.user)
            
            if current_org:
                student_queryset = Student.objects.filter(organization=current_org)
            else:
                # Если нет организации, показываем всех для суперпользователя
                if self.request.user.is_superuser:
                    student_queryset = Student.objects.all()
                else:
                    student_queryset = Student.objects.none()
            
            self.fields['student'].queryset = student_queryset
            
            # Также фильтруем курсы по организации
            if current_org:
                course_queryset = Course.objects.filter(organization=current_org, is_unlimited=False)
            else:
                if self.request.user.is_superuser:
                    course_queryset = Course.objects.filter(is_unlimited=False)
                else:
                    course_queryset = Course.objects.none()
            
            self.fields['course'].queryset = course_queryset


@login_required
@admin_required
def payment_list(request):
    # Получаем текущую организацию
    current_org = get_current_organization(request.user)
    
    qs = Payment.objects.select_related('student', 'course', 'payment_method', 'created_by').all()
    
    # Фильтруем по организации
    qs = filter_by_organization(qs, current_org)

    course_id = request.GET.get('course')
    method = request.GET.get('method')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('q', '')

    if course_id:
        qs = qs.filter(course_id=course_id)
    if method:
        qs = qs.filter(payment_method_id=method)
    if date_from:
        qs = qs.filter(paid_at__gte=date_from)
    if date_to:
        qs = qs.filter(paid_at__lte=date_to)
    if search:
        qs = qs.filter(Q(student__full_name__icontains=search))

    total = qs.aggregate(s=Sum('amount'))['s'] or 0
    
    # Фильтруем курсы и способы оплаты по организации
    courses = Course.objects.filter(is_archived=False)
    if current_org:
        courses = courses.filter(organization=current_org)
    
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    context = {
        'payments': qs[:200],
        'total': total,
        'courses': courses,
        'payment_methods': payment_methods,
        'page_title': 'Оплата за учёбу',
        'filter_course': course_id,
        'filter_method': method,
    }
    return render(request, 'admin/payments/list.html', context)


@login_required
@admin_required
def payment_create(request):
    print(f"=== PAYMENT CREATE VIEW STARTED ===")
    print(f"Request method: {request.method}")
    print(f"GET params: {dict(request.GET)}")
    print(f"POST params: {dict(request.POST)}")
    
    # Получаем student_id из GET параметра, но убеждаемся что он не равен 'null'
    student_id = request.GET.get('student')
    if student_id == 'null' or student_id == 'None':
        student_id = None
    
    print(f"Student ID: {student_id}")
    
    if request.method == 'POST':
        print("=== POST REQUEST PROCESSING ===")
        student_id = request.POST.get('student')
        course_id = request.POST.get('course')
        payment_method_id = request.POST.get('payment_method')
        months_selected = request.POST.getlist('months')
        amount = request.POST.get('amount')
        paid_at = request.POST.get('paid_at')
        comment = request.POST.get('comment', '')
        generate_receipt = request.POST.get('generate_receipt') == 'on'  # Галочка для чека
        
        print(f"Form data: student={student_id}, course={course_id}, amount={amount}, generate_receipt={generate_receipt}")
        
        if student_id and course_id and payment_method_id and months_selected and amount:
            student = get_object_or_404(Student, pk=student_id)
            course = get_object_or_404(Course, pk=course_id)
            payment_method = get_object_or_404(PaymentMethod, pk=payment_method_id)
            
            # Проверяем, что месяцы не оплачены ранее
            existing_payments = Payment.objects.filter(
                student=student,
                course=course
            ).values_list('months_paid', flat=True)
            
            # Собираем все оплаченные месяцы в один список
            all_paid_months = []
            for months_list in existing_payments:
                if months_list:
                    if isinstance(months_list, list):
                        all_paid_months.extend([int(m) for m in months_list if m is not None])
                    elif isinstance(months_list, int):
                        all_paid_months.append(months_list)
            
            # Удаляем дубликаты
            seen = set()
            unique_paid_months = []
            for month in all_paid_months:
                if month not in seen:
                    seen.add(month)
                    unique_paid_months.append(month)
            
            # Проверяем пересечения
            months_selected_int = [int(m) for m in months_selected]
            conflict_months = set(months_selected_int) & set(unique_paid_months)
            
            if conflict_months:
                conflict_str = ", ".join(map(str, sorted(conflict_months)))
                messages.error(request, f'Следующие месяцы уже оплачены: {conflict_str}')
                return render(request, 'admin/payments/form_new.html', {
                    'students': Student.objects.all(),
                    'payment_methods': PaymentMethod.objects.filter(is_active=True),
                    'page_title': 'Добавить оплату',
                    'selected_student_id': student_id,
                    'error': f'Месяцы {conflict_str} уже оплачены'
                })
            
            payment = Payment.objects.create(
                student=student,
                course=course,
                amount=amount,
                payment_method=payment_method,
                paid_at=paid_at,
                comment=comment,
                months_paid=months_selected,
                month_count=len(months_selected),
                generate_receipt=generate_receipt,
                created_by=request.user
            )
            
            # Принудительное создание транзакции в бухгалтерии
            if payment.paid_at:
                try:
                    from apps.finance.signals import create_payment_transaction
                    transaction = create_payment_transaction(payment)
                    if transaction:
                        print(f"✅ Финансовая транзакция создана: {transaction.id}")
                    else:
                        print("❌ Не удалось создать финансовую транзакцию")
                except Exception as e:
                    print(f"❌ Ошибка при создании транзакции: {e}")
            
            messages.success(request, 'Оплата добавлена.')
            
            # Если нужно сформировать чек
            if generate_receipt:
                try:
                    print(f"=== RECEIPT GENERATION STARTED ===")
                    print(f"Payment ID: {payment.id}")
                    print(f"Student: {payment.student.full_name}")
                    print(f"Course: {payment.course.title}")
                    print(f"Amount: {payment.amount}")
                    
                    # Проверяем наличие настроек организации
                    org_data = OrganizationReceipt.get_active()
                    print(f"Organization data: {org_data}")
                    
                    if not org_data:
                        print("❌ No active organization found")
                        messages.warning(request, 'Сначала настройте данные организации в разделе "Настройки чеков"')
                        return redirect('payments:create')
                    
                    print(f"✅ Organization found: {org_data.organization_name}")
                    
                    pdf_response = generate_payment_receipt(payment)
                    print(f"PDF response: {pdf_response}")
                    
                    if pdf_response:
                        print("✅ HTML receipt generated successfully")
                        # Если пришел из drawer студента, возвращаемся к списку студентов
                        if request.GET.get('student'):
                            messages.info(request, 'Чек успешно сформирован.')
                            return redirect('admin_students:list')
                        # Иначе показываем чек
                        return redirect('payments:show_receipt', payment_id=payment.id)
                    else:
                        print("❌ Receipt generation returned None")
                        messages.error(request, 'Ошибка при формировании чека. Проверьте консоль для деталей.')
                        return redirect('payments:create')
                except Exception as e:
                    print(f"❌ Receipt generation error: {e}")
                    import traceback
                    traceback.print_exc()
                    messages.error(request, f'Ошибка при формировании чека: {str(e)}')
                    return redirect('payments:create')
            
            # Если пришел из drawer студента, возвращаемся к списку студентов
            if request.GET.get('student'):
                return redirect('admin_students:list')
            return redirect('payments:create')
        else:
            messages.error(request, 'Заполните все обязательные поля')
    
    # Получаем данные для формы с фильтрацией по организации
    current_org = get_current_organization(request.user)
    
    print(f"=== PAYMENT FORM DEBUG ===")
    print(f"Current user: {request.user}")
    print(f"Current organization: {current_org}")
    
    students = Student.objects.all()
    print(f"All students count: {students.count()}")
    
    if current_org:
        students = students.filter(organization=current_org)
        print(f"Filtered students count: {students.count()}")
        print(f"Organization: {current_org.name}")
    else:
        print("No current organization found")
    
    payment_methods = PaymentMethod.objects.filter(is_active=True)
    
    # Также фильтруем курсы по организации для API
    courses = Course.objects.filter(is_unlimited=False)
    if current_org:
        courses = courses.filter(organization=current_org)
    
    context = {
        'students': students,
        'payment_methods': payment_methods,
        'courses': courses,  # Добавляем отфильтрованные курсы
        'current_organization': current_org,  # Добавляем текущую организацию
        'page_title': 'Добавить оплату',
        'selected_student_id': student_id if student_id else '',
    }
    
    return render(request, 'admin/payments/form_new.html', context)


@login_required
@admin_required
def get_student_courses(request, student_id):
    """API для получения курсов студента"""
    try:
        print(f"Getting courses for student_id: {student_id}")
        
        student = get_object_or_404(Student, pk=student_id)
        print(f"Student found: {student.full_name}")
        
        # Получаем текущую организацию
        from apps.core.mixins import get_current_organization
        current_org = get_current_organization(request.user)
        
        # Получаем курсы студента через CourseStudent с фильтрацией по организации
        student_courses = CourseStudent.objects.filter(
            student=student,
            status='active'
        ).select_related('course')
        
        # Дополнительная фильтрация по организации
        if current_org:
            student_courses = student_courses.filter(course__organization=current_org)
        
        # Исключаем бесконечные курсы
        student_courses = student_courses.filter(course__is_unlimited=False)
        
        print(f"Found {student_courses.count()} active courses")
        
        courses_data = []
        for sc in student_courses:
            course = sc.course
            print(f"Course: {course.title}, price: {course.price}, duration: {course.duration_months}")
            
            # Получаем уже оплаченные месяцы для этого курса
            payments_query = Payment.objects.filter(
                student=student,
                course=course
            )
            
            print(f"Payments query for {student.full_name} - {course.title}:")
            print(f"  Query: {payments_query.query}")
            print(f"  Found payments: {payments_query.count()}")
            
            paid_months = payments_query.values_list('months_paid', flat=True)
            print(f"  Raw months_paid values: {list(paid_months)}")
            
            # Собираем все оплаченные месяцы в один список
            all_paid_months = []
            for months_list in paid_months:
                print(f"    Processing payment: {months_list} (type: {type(months_list)})")
                if months_list:  # Проверяем, что months_list не None и не пустой
                    if isinstance(months_list, list):
                        all_paid_months.extend([int(m) for m in months_list if m is not None])
                        print(f"      Extended with list: {months_list}")
                    elif isinstance(months_list, int):
                        all_paid_months.append(months_list)
                        print(f"      Extended with int: {months_list}")
                    else:
                        print(f"      Unknown type, skipping")
                else:
                    print(f"      months_list is falsy, skipping")
            
            # Удаляем дубликаты, сохраняя порядок
            seen = set()
            unique_paid_months = []
            for month in all_paid_months:
                if month not in seen:
                    seen.add(month)
                    unique_paid_months.append(month)
            
            print(f"Final unique_paid_months: {unique_paid_months}")
            print(f"Paid months for course {course.title}: {unique_paid_months}")
            
            course_data = {
                'id': course.id,
                'title': course.title,
                'price': float(course.price) if course.price else 0,
                'duration_months': course.duration_months or 12,
                'paid_months': unique_paid_months  # Уникальные месяцы в правильном порядке
            }
            courses_data.append(course_data)
            print(f"Course data: {course_data}")
        
        result = {'courses': courses_data}
        print(f"Final result: {result}")
        
        return JsonResponse(result)
    
    except Exception as e:
        import traceback
        print(f"Error in get_student_courses: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@admin_required
def payment_delete(request, pk):
    obj = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Оплата удалена.')
    return redirect('payments:list')


@login_required
@admin_required
def payment_export(request):
    import openpyxl
    from django.utils import timezone
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Оплаты'
    ws.append(['ID', 'Студент', 'Курс', 'Сумма', 'Способ', 'Дата'])
    for p in Payment.objects.select_related('student', 'course').all():
        ws.append([p.pk, p.student.full_name, p.course.title, float(p.amount),
                   p.get_payment_method_display(), str(p.paid_at)])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=payments_{timezone.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response


def generate_payment_receipt(payment):
    """Генерирует HTML чек для платежа"""
    try:
        print(f"=== Starting HTML receipt generation for payment {payment.id} ===")
        
        from django.template.loader import render_to_string
        from datetime import datetime
        
        # Получаем данные организации
        try:
            org_data = OrganizationReceipt.get_active()
            print(f"Organization data: {org_data}")
            if not org_data:
                print("❌ No active organization found")
                return None
            print(f"✅ Organization: {org_data.organization_name}")
        except Exception as e:
            print(f"❌ Organization data error: {e}")
            return None
        
        # Расчеты
        tax_amount = 0
        total_with_tax = float(payment.amount)
        
        if org_data.tax_per_receipt > 0:
            tax_amount = float(payment.amount) * float(org_data.tax_per_receipt) / 100
            total_with_tax = float(payment.amount) + tax_amount
        
        print(f"Calculations: amount={payment.amount}, tax={tax_amount}, total={total_with_tax}")
        
        # Создаем HTML для чека
        receipt_html = render_to_string('admin/payments/receipt.html', {
            'payment': payment,
            'organization': org_data,
            'receipt_number': f"R-{payment.id:06d}",
            'current_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'tax_amount': tax_amount,
            'total_with_tax': total_with_tax,
        })
        
        print("✅ HTML receipt generated successfully!")
        return receipt_html
        
    except Exception as e:
        print(f"❌ HTML receipt generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


@login_required
@admin_required
def show_payment_receipt(request, payment_id):
    """Показывает чек на экране"""
    try:
        payment = get_object_or_404(Payment, pk=payment_id)
        receipt_html = generate_payment_receipt(payment)
        
        if receipt_html:
            return render(request, 'admin/payments/receipt.html', {
                'payment': payment,
                'organization': OrganizationReceipt.get_active(),
                'receipt_number': f"R-{payment.id:06d}",
                'current_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'tax_amount': 0,
                'total_with_tax': float(payment.amount),
                'standalone': True,  # Флаг для показа в отдельном окне
            })
        else:
            messages.error(request, 'Не удалось сформировать чек')
            return redirect('payments:create')
            
    except Exception as e:
        print(f"Error showing receipt: {e}")
        messages.error(request, 'Ошибка при показе чека')
        return redirect('payments:create')


@login_required
@admin_required
def organization_settings(request):
    """Настройки данных организации для чеков"""
    
    # Получаем или создаем запись организации
    org_instance = OrganizationReceipt.objects.first()
    
    if request.method == 'POST':
        form = OrganizationReceiptForm(request.POST, instance=org_instance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки организации сохранены.')
            return redirect('payments:organization_settings')
    else:
        form = OrganizationReceiptForm(instance=org_instance)
    
    context = {
        'form': form,
        'page_title': 'Настройки чеков',
        'org_exists': org_instance is not None
    }
    
    return render(request, 'admin/payments/organization_settings.html', context)
