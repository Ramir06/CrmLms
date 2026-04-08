from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum
from django.views.decorators.http import require_POST

from apps.core.mixins import admin_required
from .models import SalaryAccrual
from apps.accounts.models import CustomUser


from django import forms


class SalaryAccrualForm(forms.ModelForm):
    month_input = forms.DateField(
        label='Месяц',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'month'}),
        input_formats=['%Y-%m']
    )

    class Meta:
        model = SalaryAccrual
        fields = ['mentor', 'course', 'amount', 'paid_status', 'comment']
        widgets = {
            'mentor': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'paid_status': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        # Убираем стандартное поле month и заменяем на наше
        if 'month' in self.fields:
            del self.fields['month']
        
        # Устанавливаем начальное значение для month_input
        if self.instance and self.instance.month:
            self.initial['month_input'] = self.instance.month.strftime('%Y-%m')
        
        # Фильтруем менторов по организации
        if self.request:
            from apps.core.mixins import get_current_organization
            current_org = get_current_organization(self.request.user)
            
            if current_org:
                mentor_queryset = CustomUser.objects.filter(
                    role='mentor', 
                    is_active=True,
                    current_organization__organization=current_org
                )
            else:
                # Если нет организации, показываем всех для суперпользователя
                if self.request.user.is_superuser:
                    mentor_queryset = CustomUser.objects.filter(role='mentor', is_active=True)
                else:
                    mentor_queryset = CustomUser.objects.none()
            
            self.fields['mentor'].queryset = mentor_queryset

    def clean_month_input(self):
        month_data = self.cleaned_data.get('month_input')
        print(f"DEBUG: month_data = {month_data}, type = {type(month_data)}")
        
        if month_data:
            # Устанавливаем дату на первое число месяца
            from datetime import datetime
            try:
                if isinstance(month_data, str):
                    # Формат "2024-01" из month input
                    year, month = month_data.split('-')
                    result_date = datetime(int(year), int(month), 1).date()
                    print(f"DEBUG: parsed date = {result_date}")
                    return result_date
                else:
                    # Если уже дата, устанавливаем на первое число
                    result_date = month_data.replace(day=1)
                    print(f"DEBUG: existing date = {result_date}")
                    return result_date
            except (ValueError, AttributeError) as e:
                print(f"DEBUG: error = {e}")
                raise forms.ValidationError('Неверный формат месяца. Используйте формат ГГГГ-ММ')
        return month_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Сохраняем month_input в поле month
        instance.month = self.cleaned_data.get('month_input')
        if commit:
            instance.save()
        return instance


@login_required
@admin_required
def salary_list(request):
    from django.utils import timezone
    from apps.mentors.models import MentorProfile
    from apps.core.mixins import get_current_organization
    
    current_org = get_current_organization(request.user)
    
    qs = SalaryAccrual.objects.select_related('mentor', 'course').all()
    
    # Фильтруем по организации
    if current_org:
        # Показываем зарплаты менторов из текущей организации
        mentor_ids = CustomUser.objects.filter(
            role='mentor',
            is_active=True,
            current_organization__organization=current_org
        ).values_list('id', flat=True)
        qs = qs.filter(mentor_id__in=mentor_ids)
    else:
        # Если нет организации, показываем все для суперпользователя
        if not request.user.is_superuser:
            qs = qs.none()
    
    mentor_id = request.GET.get('mentor')
    month = request.GET.get('month')
    current_month = request.GET.get('current_month')
    auto_calculate = request.GET.get('auto_calculate')

    if mentor_id:
        qs = qs.filter(mentor_id=mentor_id)
    if month:
        qs = qs.filter(month__startswith=month)
    if current_month:
        current_month_date = timezone.now().replace(day=1).date()
        qs = qs.filter(month=current_month_date)

    # Фильтруем менторов по организации
    if current_org:
        mentors = CustomUser.objects.filter(
            role='mentor', 
            is_active=True,
            current_organization__organization=current_org
        )
    else:
        # Если нет организации, показываем всех для суперпользователя
        if request.user.is_superuser:
            mentors = CustomUser.objects.filter(role='mentor', is_active=True)
        else:
            mentors = CustomUser.objects.none()
    
    # Автоматический расчет зарплат
    calculated_salaries = []
    if auto_calculate or current_month:
        current_date = timezone.now()
        year = current_date.year
        month = current_date.month
        
        for mentor_user in mentors:
            try:
                profile = mentor_user.mentor_profile
                calculated_amount = profile.calculate_monthly_salary(year, month)
                breakdown = profile.get_salary_breakdown(year, month)
                
                calculated_salaries.append({
                    'mentor': mentor_user,
                    'profile': profile,
                    'amount': calculated_amount,
                    'breakdown': breakdown,
                    'month': current_date.replace(day=1).date()
                })
            except MentorProfile.DoesNotExist:
                continue

    # Рассчитываем общую сумму ПОСЛЕ всех фильтров
    total = qs.aggregate(s=Sum('amount'))['s'] or 0
    
    # Отладочная информация
    print(f"DEBUG: Total salary records: {qs.count()}")
    print(f"DEBUG: Total amount: {total}")
    print(f"DEBUG: Filters applied - mentor_id: {mentor_id}, month: {month}, current_month: {current_month}")
    print(f"DEBUG: Organization: {current_org}")
    
    # Показываем первые 3 записи для отладки
    for i, salary in enumerate(qs[:3]):
        print(f"DEBUG: Salary {i+1}: {salary.mentor.get_display_name()} - {salary.amount} - {salary.paid_status}")

    context = {
        'accruals': qs[:200],
        'total': total,
        'mentors': mentors,
        'page_title': 'Зарплаты',
        'current_month_filter': current_month,
        'calculated_salaries': calculated_salaries,
        'auto_calculate': auto_calculate,
    }
    return render(request, 'admin/salaries/list.html', context)


@login_required
@admin_required
def salary_create(request):
    form = SalaryAccrualForm(request.POST or None, request=request)
    if request.method == 'POST' and form.is_valid():
        salary_accrual = form.save()
        
        print(f"=== ЗАРПЛАТА СОЗДАНА ===")
        print(f"ID: {salary_accrual.id}")
        print(f"Ментор: {salary_accrual.mentor.get_display_name()}")
        
        # Получаем организацию ментора
        try:
            mentor_org = salary_accrual.mentor.current_organization.organization
            print(f"Организация ментора: {mentor_org}")
        except AttributeError:
            mentor_org = None
            print("❌ У ментора нет организации!")
        
        print(f"Сумма: {salary_accrual.amount}")
        print(f"Статус: {salary_accrual.paid_status}")
        print(f"Месяц: {salary_accrual.month}")
        
        # Принудительное создание транзакции в бухгалтерии если выплачено
        if salary_accrual.paid_status == 'paid':
            try:
                from apps.finance.signals import create_salary_transaction
                transaction = create_salary_transaction(salary_accrual)
                if transaction:
                    print(f"✅ Финансовая транзакция зарплаты создана: {transaction.id}")
                    messages.success(request, 'Зарплата выплачена и транзакция создана.')
                else:
                    print("❌ Не удалось создать финансовую транзакцию зарплаты")
                    messages.warning(request, 'Зарплата выплачена, но транзакция не создана.')
            except Exception as e:
                print(f"❌ Ошибка при создании транзакции зарплаты: {e}")
                import traceback
                traceback.print_exc()
                messages.error(request, f'Ошибка при создании транзакции: {e}')
        else:
            print(f"❌ Статус зарплаты не 'paid', а '{salary_accrual.paid_status}' - транзакция не создается")
        
        messages.success(request, 'Начисление добавлено.')
        return redirect('salaries:list')
    return render(request, 'admin/salaries/form.html', {'form': form, 'page_title': 'Добавить начисление'})


@login_required
@admin_required
def salary_edit(request, pk):
    salary = get_object_or_404(SalaryAccrual, pk=pk)
    old_status = salary.paid_status
    
    form = SalaryAccrualForm(request.POST or None, instance=salary, request=request)
    if request.method == 'POST' and form.is_valid():
        salary_accrual = form.save()
        
        # Если статус изменился на "Выплачено", создаем транзакцию
        if old_status != 'paid' and salary_accrual.paid_status == 'paid':
            try:
                from apps.finance.signals import create_salary_transaction
                transaction = create_salary_transaction(salary_accrual)
                if transaction:
                    print(f"✅ Финансовая транзакция зарплаты создана: {transaction.id}")
                    messages.success(request, 'Зарплата выплачена и транзакция создана.')
                else:
                    print("❌ Не удалось создать финансовую транзакцию зарплаты")
                    messages.warning(request, 'Зарплата выплачена, но транзакция не создана.')
            except Exception as e:
                print(f"❌ Ошибка при создании транзакции зарплаты: {e}")
                messages.error(request, f'Ошибка при создании транзакции: {e}')
        
        messages.success(request, 'Начисление обновлено.')
        return redirect('salaries:list')
    
    return render(request, 'admin/salaries/form.html', {'form': form, 'page_title': 'Редактировать начисление'})


@login_required
@admin_required
def salary_auto_create(request):
    """Автоматическое создание начислений на основе расчета"""
    from django.utils import timezone
    from apps.mentors.models import MentorProfile
    
    if request.method == 'POST':
        month_str = request.POST.get('month')
        if month_str:
            try:
                year, month = map(int, month_str.split('-'))
                month_date = timezone.datetime(year, month, 1).date()
                
                created_count = 0
                mentors = CustomUser.objects.filter(role='mentor', is_active=True)
                
                for mentor_user in mentors:
                    try:
                        profile = mentor_user.mentor_profile
                        calculated_amount = profile.calculate_monthly_salary(year, month)
                        
                        if calculated_amount > 0:
                            # Проверяем существует ли уже начисление
                            existing = SalaryAccrual.objects.filter(
                                mentor=mentor_user,
                                month=month_date
                            ).first()
                            
                            if existing:
                                existing.amount = calculated_amount
                                existing.save()
                            else:
                                SalaryAccrual.objects.create(
                                    mentor=mentor_user,
                                    month=month_date,
                                    amount=calculated_amount,
                                    paid_status='pending',
                                    comment=f'Автоматически рассчитано ({profile.get_salary_type_display()})'
                                )
                            created_count += 1
                    except MentorProfile.DoesNotExist:
                        continue
                
                messages.success(request, f'Создано {created_count} начислений за {month_str}')
                
            except (ValueError, AttributeError):
                messages.error(request, 'Неверный формат месяца')
        
        return redirect('salaries:list')
    
    # GET запрос - показываем форму
    context = {
        'page_title': 'Автоматический расчет зарплат',
        'current_month': timezone.now().strftime('%Y-%m')
    }
    return render(request, 'admin/salaries/auto_create.html', context)


@login_required
def mentor_salary_view(request):
    """Mentor sees their own salary history."""
    qs = SalaryAccrual.objects.filter(mentor=request.user).select_related('course').order_by('-month')
    total_pending = qs.filter(paid_status='pending').aggregate(s=Sum('amount'))['s'] or 0
    total_paid = qs.filter(paid_status='paid').aggregate(s=Sum('amount'))['s'] or 0
    context = {
        'accruals': qs,
        'total_pending': total_pending,
        'total_paid': total_paid,
        'page_title': 'Моя зарплата',
    }
    return render(request, 'mentor/salary/index.html', context)


@login_required
@admin_required
def salary_details(request, pk):
    """Детальная информация о расчете зарплаты"""
    salary = get_object_or_404(SalaryAccrual, pk=pk)
    details = salary.get_salary_details()
    
    context = {
        'salary': salary,
        'details': details,
        'page_title': f'Детали зарплаты - {salary.mentor.get_full_name()}'
    }
    return render(request, 'admin/salaries/details.html', context)


@login_required
@admin_required
def salary_auto_calculate(request):
    """Автоматический расчет зарплат за месяц"""
    from django.utils import timezone
    
    if request.method == 'POST':
        month_str = request.POST.get('month')
        if month_str:
            try:
                year, month = map(int, month_str.split('-'))
                
                # Запускаем автоматический расчет
                SalaryAccrual.auto_generate_accruals(year, month)
                
                messages.success(request, f'Зарплаты автоматически рассчитаны за {month_str}')
                
            except (ValueError, AttributeError) as e:
                messages.error(request, f'Ошибка при расчете: {str(e)}')
        
        return redirect('salaries:list')
    
    # GET запрос
    context = {
        'page_title': 'Автоматический расчет зарплат',
        'current_month': timezone.now().strftime('%Y-%m')
    }
    return render(request, 'admin/salaries/auto_calculate.html', context)


@login_required
@admin_required
def salary_export(request):
    import openpyxl
    from django.utils import timezone
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Зарплаты'
    ws.append(['ID', 'Ментор', 'Курс', 'Месяц', 'Сумма', 'Статус'])
    for s in SalaryAccrual.objects.select_related('mentor', 'course').all():
        ws.append([s.pk, s.mentor.get_display_name(),
                   s.course.title if s.course else '',
                   str(s.month), float(s.amount), s.get_paid_status_display()])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=salaries_{timezone.now().strftime("%Y%m%d")}.xlsx'
    wb.save(response)
    return response


@login_required
@admin_required
@require_POST
def mark_salary_paid(request, salary_id):
    """Отметить зарплату как выплаченную"""
    salary = get_object_or_404(SalaryAccrual, id=salary_id)
    
    if salary.paid_status == 'paid':
        return JsonResponse({
            'success': False,
            'error': 'Зарплата уже выплачена'
        })
    
    try:
        # Изменяем статус на выплачено
        salary.paid_status = 'paid'
        salary.save()
        
        # Логируем действие
        from apps.core.models import ActionHistory
        ActionHistory.log_action(
            user=request.user,
            action=f'Отметил зарплату как выплаченную',
            action_type='salary_paid',
            description=f'Зарплата ментора {salary.mentor.get_display_name()} в размере {salary.amount} за {salary.month} отмечена как выплаченная',
            object_type='SalaryAccrual',
            object_id=salary.id
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Зарплата успешно отмечена как выплаченная'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Ошибка при обновлении статуса: {str(e)}'
        })
