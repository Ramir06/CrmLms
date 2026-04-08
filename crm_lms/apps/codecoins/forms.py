from django import forms
from django.utils import timezone
from .models import CoinWithdrawalRequest, CoinScale
from .services import CoinService


class WithdrawalRequestForm(forms.ModelForm):
    """Форма заявки на вывод кодкойнов"""
    
    class Meta:
        model = CoinWithdrawalRequest
        fields = ['amount', 'payout_method', 'phone_number', 'comment']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Сумма вывода',
                'min': '100',
                'step': '0.01'
            }),
            'payout_method': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '0990123456',
                'pattern': '0\\d{9}'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Комментарий (необязательно)'
            })
        }
    
    def __init__(self, student, *args, **kwargs):
        self.student = student
        super().__init__(*args, **kwargs)
        
        # Получаем баланс студента
        self.balance = CoinService.get_student_balance(student)
        
        # Устанавливаем максимальную сумму
        self.fields['amount'].widget.attrs['max'] = str(self.balance)
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Сумма должна быть положительной")
        if amount < 100:
            raise forms.ValidationError("Минимальная сумма вывода: 100 кодкойнов")
        if amount > self.balance:
            raise forms.ValidationError(f"Недостаточно кодкойнов. Доступно: {self.balance}")
        return amount
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and not phone.startswith('0'):
            raise forms.ValidationError("Номер телефона должен начинаться с 0")
        if phone and len(phone) != 10:
            raise forms.ValidationError("Номер телефона должен содержать 10 цифр")
        return phone


class BalanceAdjustmentForm(forms.Form):
    """Форма корректировки баланса"""
    
    ADJUSTMENT_TYPES = [
        ('add', 'Начислить'),
        ('subtract', 'Списать')
    ]
    
    student = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Студент'
    )
    adjustment_type = forms.ChoiceField(
        choices=ADJUSTMENT_TYPES,
        widget=forms.RadioSelect,
        label='Тип операции'
    )
    amount = forms.DecimalField(
        max_digits=10, decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Сумма',
            'min': '0.01',
            'step': '0.01'
        }),
        label='Сумма'
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Причина корректировки'
        }),
        label='Причина'
    )
    
    def __init__(self, *args, **kwargs):
        from apps.students.models import Student
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = Student.objects.filter(
            user_account__is_active=True
        ).order_by('full_name')


class WithdrawalReviewForm(forms.Form):
    """Форма обработки заявки на вывод"""
    
    rejection_reason = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Причина отклонения (только при отклонении)'
        }),
        label='Причина отклонения'
    )


class CoinScaleForm(forms.ModelForm):
    """Форма шкалы кодкойнов"""
    
    class Meta:
        model = CoinScale
        fields = ['title', 'value', 'is_active', 'sort_order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'})
        }
    
    def clean_value(self):
        value = self.cleaned_data.get('value')
        if value == 0:
            raise forms.ValidationError("Значение не может быть нулевым")
        return value


class CoinBatchForm(forms.Form):
    """Форма создания пакета начислений"""
    
    lesson_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Дата урока'
    )
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Комментарий к уроку'
        }),
        label='Комментарий'
    )
    
    def __init__(self, course, *args, **kwargs):
        self.course = course
        super().__init__(*args, **kwargs)
        # Устанавливаем текущую дату как значение по умолчанию
        self.fields['lesson_date'].initial = timezone.now().date()


class CoinMassAccrualForm(forms.Form):
    """Форма массового начисления кодкойнов"""
    
    def __init__(self, course_students, scales, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.course_students = course_students
        self.scales = scales
        
        # Создаем поля для каждого студента и шкалы
        for student in course_students:
            for scale in scales:
                field_name = f"student_{student.id}_scale_{scale.id}"
                self.fields[field_name] = forms.BooleanField(
                    required=False,
                    label=f"{student.student.full_name} - {scale.title}",
                    widget=forms.CheckboxInput(attrs={
                        'class': 'form-check-input',
                        'data-student': student.id,
                        'data-scale': scale.id,
                        'data-amount': scale.value
                    })
                )


class NextWithdrawalDateForm(forms.Form):
    """Форма установки даты следующего вывода"""
    
    next_open_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        label='Дата и время открытия'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем значение по умолчанию через неделю
        from datetime import timedelta
        default_date = timezone.now() + timedelta(days=7)
        self.fields['next_open_at'].initial = default_date
