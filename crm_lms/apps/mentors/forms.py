from django import forms
from apps.accounts.models import CustomUser
from apps.accounts.forms import CreateUserForm
from .models import MentorProfile


class MentorProfileForm(forms.ModelForm):
    class Meta:
        model = MentorProfile
        fields = ['short_name', 'specialization', 'bio', 'salary_type',
                  'fixed_salary', 'percent_salary', 'hired_at', 'is_active']
        widgets = {
            'short_name': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'salary_type': forms.Select(attrs={'class': 'form-select'}),
            'fixed_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'percent_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'hired_at': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
