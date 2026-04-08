from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from .models import StaffMember, StaffOrganizationAccess, Organization

User = get_user_model()


class StaffCreationForm(forms.ModelForm):
    """Форма создания персонала"""
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('superadmin', 'Супер администратор'),
    ]
    
    first_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
        label='Имя'
    )
    last_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
        label='Фамилия'
    )
    username = forms.CharField(
        max_length=150, required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'}),
        label='Логин'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        label='Email'
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}),
        label='Пароль',
        help_text='Минимум 8 символов'
    )
    password_confirm = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Подтвердите пароль'}),
        label='Подтвердите пароль'
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Роль',
        required=True
    )
    
    # Доступные организации
    organizations = forms.ModelMultipleChoiceField(
        queryset=Organization.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label='Доступные организации',
        help_text='Выберите организации, к которым у пользователя будет доступ'
    )
    
    class Meta:
        model = StaffMember
        fields = []
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Пользователь с таким логином уже существует')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует')
        return email
    
    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Пароли не совпадают')
        
        if password and len(password) < 8:
            raise forms.ValidationError('Пароль должен содержать минимум 8 символов')
        
        return password_confirm
    
    def save(self, commit=True, created_by=None):
        # Создаем пользователя
        user = User.objects.create(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=make_password(self.cleaned_data['password']),
            role=self.cleaned_data['role'],
            is_active=True,
        )
        
        # Создаем запись персонала
        staff_member = StaffMember.objects.create(
            user=user,
            created_by=created_by
        )
        
        # Предоставляем доступ к выбранным организациям
        for organization in self.cleaned_data['organizations']:
            StaffOrganizationAccess.objects.create(
                staff_member=staff_member,
                organization=organization,
                granted_by=created_by
            )
        
        return staff_member


class StaffOrganizationAccessForm(forms.ModelForm):
    """Форма управления доступом персонала к организациям"""
    organizations = forms.ModelMultipleChoiceField(
        queryset=Organization.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label='Доступные организации'
    )
    
    class Meta:
        model = StaffOrganizationAccess
        fields = ['organizations']
    
    def __init__(self, staff_member, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.staff_member = staff_member
        
        # Устанавливаем текущие организации
        current_orgs = staff_member.organizations.values_list('id', flat=True)
        self.fields['organizations'].initial = current_orgs
    
    def save(self, commit=True, granted_by=None):
        # Получаем выбранные организации
        selected_orgs = self.cleaned_data['organizations']
        
        # Удаляем старые доступы
        StaffOrganizationAccess.objects.filter(staff_member=self.staff_member).delete()
        
        # Создаем новые доступы
        for organization in selected_orgs:
            StaffOrganizationAccess.objects.create(
                staff_member=self.staff_member,
                organization=organization,
                granted_by=granted_by
            )
        
        return self.staff_member
