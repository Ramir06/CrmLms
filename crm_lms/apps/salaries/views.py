from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db.models import Sum

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
        super().__init__(*args, **kwargs)
        # Убираем стандартное поле month и заменяем на наше
        if 'month' in self.fields:
            del self.fields['month']
        
        # Устанавливаем начальное значение для month_input
        if self.instance and self.instance.month:
            self.initial['month_input'] = self.instance.month.strftime('%Y-%m')

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
    
    qs = SalaryAccrual.objects.select_related('mentor', 'course').all()
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

    total = qs.aggregate(s=Sum('amount'))['s'] or 0
    mentors = CustomUser.objects.filter(role='mentor', is_active=True)
    
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
    form = SalaryAccrualForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Начисление добавлено.')
        return redirect('salaries:list')
    return render(request, 'admin/salaries/form.html', {'form': form, 'page_title': 'Добавить начисление'})


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
