from django import forms
from django.contrib.auth.models import User
from .models import StaffMember, StaffOrganizationAccess, Organization


class StaffCreateForm(forms.ModelForm):
    """Форма для создания персонала с организациями"""
    
    first_name = forms.CharField(
        max_length=100, 
        label="Имя",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
    )
    
    last_name = forms.CharField(
        max_length=100, 
        label="Фамилия",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
    )
    
    username = forms.CharField(
        max_length=150, 
        label="Логин",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите логин'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    
    role = forms.ChoiceField(
        choices=[
            ('admin', 'Администратор'),
            ('manager', 'Менеджер'),
        ],
        label="Роль",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    organizations = forms.ModelMultipleChoiceField(
        queryset=Organization.objects.filter(is_active=True),
        label="Разрешенные организации",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )
    
    is_active = forms.BooleanField(
        label="Активен",
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    class Meta:
        model = StaffMember
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organizations'].queryset = Organization.objects.filter(is_active=True)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        # Создаем пользователя
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            role=self.cleaned_data['role'],
            is_active=self.cleaned_data.get('is_active', True)
        )
        
        # Создаем запись персонала
        staff_member = StaffMember.objects.create(user=user)
        
        # Назначаем доступ к организациям
        for org in self.cleaned_data.get('organizations', []):
            StaffOrganizationAccess.objects.create(
                staff_member=staff_member,
                organization=org,
                is_active=True
            )
        
        return staff_member
