from django import forms
from django.contrib.auth import get_user_model
from .models import StaffMember, StaffOrganizationAccess, Organization
from apps.accounts.models import Role

User = get_user_model()


class SuperAdminStaffCreateForm(forms.ModelForm):
    """Форма для создания персонала суперадминистратором"""
    
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
    
    birth_date = forms.DateField(
        label="Дата рождения",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    pin_fl = forms.CharField(
        max_length=14, 
        label="ПИН Паспорта",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ПИН паспорта'
        })
    )
    
    passport_photo = forms.ImageField(
        label="Фото паспорта",
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
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
            ('staff', 'Персонал'),
        ],
        label="Базовая роль",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    custom_role = forms.ModelChoiceField(
        queryset=Role.objects.filter(is_active=True),
        label="Кастомная роль",
        required=False,
        empty_label="Без кастомной роли",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    organizations = forms.ModelMultipleChoiceField(
        queryset=Organization.objects.filter(is_active=True),
        label="Доступные для него организации",
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input'
        }),
        required=False
    )
    
    is_active = forms.BooleanField(
        label="Активен",
        required=False,  # Changed from True to False since it's a checkbox
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
        
        # Устанавливаем значение по умолчанию для поля is_active
        self.fields['is_active'].initial = True
        
        # Если передана организация по умолчанию, устанавливаем ее
        if 'initial' in kwargs and 'organizations' in kwargs['initial']:
            self.fields['organizations'].initial = kwargs['initial']['organizations']
        elif not self.is_bound and 'organizations' not in self.initial:
            # Если форма не связана и нет начальных организаций, оставляем поле пустым
            pass

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
        # Создаем пользователя через CustomUserManager
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            role=self.cleaned_data['role'],
            custom_role=self.cleaned_data.get('custom_role'),
            is_active=self.cleaned_data.get('is_active', True)
        )
        
        # Сохраняем дополнительные данные
        # Временно сохраняем в сессию или создаем профиль если модель существует
        try:
            from apps.students.models import StudentProfile
            profile, created = StudentProfile.objects.get_or_create(user=user)
            profile.birth_date = self.cleaned_data['birth_date']
            profile.pin_fl = self.cleaned_data['pin_fl']
            if self.cleaned_data.get('passport_photo'):
                profile.passport_photo = self.cleaned_data['passport_photo']
            profile.save()
        except ImportError:
            # Если модель профиля не найдена, пропускаем сохранение дополнительных полей
            pass
        
        # Создаем запись персонала
        staff_member = StaffMember.objects.create(user=user)
        
        # Назначаем доступ к организациям
        for org in self.cleaned_data.get('organizations', []):
            StaffOrganizationAccess.objects.create(
                staff_member=staff_member,
                organization=org,
                is_active=True
            )
        
        # Автоматически добавляем созданного пользователя в мультиаккаунты
        # текущего пользователя (если это не он сам)
        try:
            from apps.accounts.models import UserAccount
            # Получаем текущего пользователя из контекста (если доступно)
            # Это может потребовать передачи request в форму
            current_user = getattr(self, 'current_user', None)
            if current_user and current_user != user:
                role_name = user.get_role_display()
                UserAccount.objects.get_or_create(
                    user=current_user,
                    account_user=user,
                    defaults={'name': f'{user.get_display_name()} ({role_name})'}
                )
        except ImportError:
            pass
        
        return staff_member
