from django import forms
from django.utils import timezone
from .models import Course, CourseStudent


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 'subject', 'status', 'mentor', 'assistant_mentor',
            'start_date', 'end_date', 'duration_months', 'price',
            'room', 'format', 'days_of_week', 'lesson_start_time', 'lesson_end_time',
            'capacity', 'description', 'is_unlimited', 'color',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'mentor': forms.Select(attrs={'class': 'form-select'}),
            'assistant_mentor': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'format': forms.Select(attrs={'class': 'form-select'}),
            'days_of_week': forms.Select(attrs={'class': 'form-select'}),
            'lesson_start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'lesson_end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_unlimited': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
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
