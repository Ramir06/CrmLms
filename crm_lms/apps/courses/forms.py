from django import forms
from django.utils import timezone
from .models import Course, CourseStudent


DAYS_OF_WEEK = [
    ('mon', 'Понедельник'),
    ('tue', 'Вторник'),
    ('wed', 'Среда'),
    ('thu', 'Четверг'),
    ('fri', 'Пятница'),
    ('sat', 'Суббота'),
    ('sun', 'Воскресенье'),
]


class CourseForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Дни недели'
    )
    
    # Дополнительные поля для разных типов зарплаты
    hourly_rate = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Почасовая ставка (₽)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    
    salary_percentage = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        label='Процент от оплат (%)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем менторов по текущей организации
        current_org = None
        if hasattr(self, '_current_org'):
            current_org = self._current_org
        
        if current_org:
            from apps.mentors.models import MentorProfile
            from apps.accounts.models import CustomUser
            
            # Получаем менторов текущей организации
            mentor_profiles = MentorProfile.objects.filter(organization=current_org, is_active=True).select_related('user')
            mentor_users = [profile.user for profile in mentor_profiles]
            
            # Обновляем queryset для полей менторов
            self.fields['mentor'].queryset = CustomUser.objects.filter(
                id__in=[user.id for user in mentor_users],
                role='mentor'
            ).order_by('full_name')
            
            self.fields['assistant_mentor'].queryset = CustomUser.objects.filter(
                id__in=[user.id for user in mentor_users],
                role='mentor'
            ).order_by('full_name')
        
        # Инициализация значений из модели
        if self.instance and self.instance.pk:
            self.fields['hourly_rate'].initial = self.instance.hourly_rate
        
        # Добавляем JavaScript для динамического отображения полей
        self.fields['salary_type'].widget.attrs.update({
            'onchange': 'toggleSalaryFields(this.value)'
        })
    
    def clean(self):
        cleaned_data = super().clean()
        salary_type = cleaned_data.get('salary_type')
        
        # Устанавливаем значения по умолчанию для полей оплаты
        if cleaned_data.get('hourly_rate') is None:
            cleaned_data['hourly_rate'] = 0
        if cleaned_data.get('salary_percentage') is None:
            cleaned_data['salary_percentage'] = 0
        
        if salary_type == 'hourly':
            if not cleaned_data.get('hourly_rate') or cleaned_data.get('hourly_rate') <= 0:
                self.add_error('hourly_rate', 'Укажите почасовую ставку больше 0')
        elif salary_type == 'percentage':
            if not cleaned_data.get('salary_percentage') or cleaned_data.get('salary_percentage') <= 0:
                self.add_error('salary_percentage', 'Укажите процент от оплат больше 0')
        elif salary_type == 'monthly':
            # Разрешаем price = 0 для создания курса, но показываем предупреждение
            price = cleaned_data.get('price')
            if price is None or price < 0:
                self.add_error('price', 'Укажите корректную сумму (0 или больше)')
        
        return cleaned_data
    
    class Meta:
        model = Course
        fields = [
            'title', 'subject', 'status', 'mentor', 'assistant_mentor',
            'start_date', 'end_date', 'duration_months', 'price', 'salary_type',
            'hourly_rate', 'salary_percentage',
            'room', 'format', 'days_of_week', 'lesson_start_time', 'lesson_end_time',
            'capacity', 'description', 'is_unlimited', 'color',
            'online_lesson_link', 'chat_link'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'mentor': forms.Select(attrs={'class': 'form-select'}),
            'assistant_mentor': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control', 'readonly': True}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'salary_type': forms.Select(attrs={'class': 'form-select'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'format': forms.Select(attrs={'class': 'form-select'}),
            'lesson_start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'lesson_end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_unlimited': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'online_lesson_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://zoom.us/j/...'}),
            'chat_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://t.me/...'}),
        }
        labels = {
            'price': 'Фиксированная зарплата (₽)',
            'salary_type': 'Тип оплаты ментора',
        }


class CourseStudentForm(forms.ModelForm):
    class Meta:
        model = CourseStudent
        fields = ['student', 'joined_at', 'status', 'note']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'joined_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AddTicketsForm(forms.Form):
    """Форма добавления талонов"""
    quantity = forms.IntegerField(
        min_value=1,
        label='Количество талонов',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )
    price_per_ticket = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        label='Стоимость одного талона',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'})
    )
    comment = forms.CharField(
        required=False,
        label='Комментарий',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Необязательно'})
    )


class MarkAttendanceForm(forms.Form):
    """Форма отметки посещения"""
    lessons_count = forms.IntegerField(
        min_value=1,
        initial=1,
        label='Количество занятий',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )
    lesson_date = forms.DateField(
        initial=timezone.now().date,
        label='Дата занятия',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    comment = forms.CharField(
        required=False,
        label='Комментарий',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Необязательно'})
    )


class AdjustTicketsForm(forms.Form):
    """Форма корректировки количества талонов"""
    new_total = forms.IntegerField(
        min_value=0,
        label='Новое общее количество талонов',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '0'})
    )
    comment = forms.CharField(
        required=False,
        label='Причина корректировки',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
