from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import CustomUser


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ramir06',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '••••••••',
        })
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'full_name', 'phone', 'avatar', 'language', 'theme']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'theme': forms.Select(attrs={'class': 'form-select'}),
        }


class CreateUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль'
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'role', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ramir06'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UsernameChangeForm(forms.ModelForm):
    """Форма для изменения логина"""
    new_username = forms.CharField(
        label='Новый логин',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новый логин',
        }),
        help_text='Логин должен быть уникальным. Допустимы буквы, цифры, подчеркивания и дефисы.'
    )

    class Meta:
        model = CustomUser
        fields = ['new_username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_username'].initial = self.instance.username

    def clean_new_username(self):
        new_username = self.cleaned_data.get('new_username')
        
        # Проверяем, что логин изменился
        if new_username == self.instance.username:
            raise forms.ValidationError('Новый логин должен отличаться от текущего.')
        
        # Проверяем уникальность логина
        if CustomUser.objects.filter(username=new_username).exists():
            raise forms.ValidationError('Логин занят')
        
        # Проверяем допустимые символы
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', new_username):
            raise forms.ValidationError('Логин может содержать только буквы, цифры, подчеркивания и дефисы.')
        
        return new_username

    def save(self, commit=True):
        self.instance.username = self.cleaned_data['new_username']
        return super().save(commit)


class CustomPasswordChangeForm(PasswordChangeForm):
    """Кастомная форма смены пароля"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите текущий пароль',
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите новый пароль',
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Подтвердите новый пароль',
        })
        
        # Изменяем метки
        self.fields['old_password'].label = 'Текущий пароль'
        self.fields['new_password1'].label = 'Новый пароль'
        self.fields['new_password2'].label = 'Подтвердите пароль'
