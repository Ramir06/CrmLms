from django import forms
from django.core.validators import validate_email
from django.core.exceptions import ValidationError


class FeedbackForm(forms.Form):
    """Форма обратной связи"""
    
    title = forms.CharField(
        label='Заголовок',
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите заголовок сообщения...',
            'required': True
        })
    )
    
    description = forms.CharField(
        label='Описание',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Подробно опишите ваш отзыв, идею или проблему...',
            'rows': 5,
            'required': True
        })
    )
    
    email = forms.EmailField(
        label='Email для связи',
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            try:
                validate_email(email)
            except ValidationError:
                raise ValidationError('Введите корректный email адрес')
        return email
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 3:
            raise ValidationError('Заголовок должен содержать минимум 3 символа')
        return title.strip()
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description and len(description.strip()) < 10:
            raise ValidationError('Описание должно содержать минимум 10 символов')
        return description.strip()
