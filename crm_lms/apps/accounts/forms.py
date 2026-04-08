from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .models import CustomUser, Role
from django.core.exceptions import ValidationError


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Рамир1',
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
    avatar = forms.ImageField(
        label='Аватар',
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        help_text='Загрузите свой аватар. Если не загружать, будет использоваться автоматически сгенерированный аватар.'
    )
    
    delete_avatar = forms.BooleanField(
        label='Удалить текущий аватар',
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'full_name', 'phone', 'avatar', 'language']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Показываем текущий аватар и информацию о RoboHash
        if self.instance and self.instance.pk:
            if self.instance.has_custom_avatar():
                self.fields['delete_avatar'].help_text = 'Отметьте, чтобы удалить свой аватар и вернуться к автоматически сгенерированному.'
            else:
                # Скрываем чекбокс удаления если нет своего аватара
                self.fields.pop('delete_avatar', None)
                self.fields['avatar'].help_text = 'У вас нет своего аватара. Загрузите фото или будет использоваться автоматически сгенерированный аватар.'

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Проверяем размер файла (максимум 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError('Размер файла не должен превышать 5MB.')
            
            # Проверяем формат файла через content_type или magic number
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            
            # Для загруженного файла проверяем content_type
            if hasattr(avatar, 'content_type'):
                if avatar.content_type not in allowed_types:
                    raise ValidationError('Допустимые форматы: JPEG, PNG, GIF, WebP.')
            # Для существующего файла проверяем по расширению
            else:
                import os
                file_ext = os.path.splitext(avatar.name)[1].lower()
                allowed_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                if file_ext not in allowed_exts:
                    raise ValidationError('Допустимые форматы: JPEG, PNG, GIF, WebP.')
        
        return avatar

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Если отмечено удаление аватара
        if self.cleaned_data.get('delete_avatar'):
            user.delete_avatar()
        
        if commit:
            user.save()
        return user


class CreateUserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Пароль'
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'full_name', 'phone', 'role', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите логин'}),
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


class RoleForm(forms.ModelForm):
    """Форма для создания и редактирования ролей"""
    
    # Определяем все возможные разрешения в системе
    PERMISSION_CHOICES = [
        # Управление пользователями
        ('view_users', 'Просмотр пользователей'),
        ('add_users', 'Добавление пользователей'),
        ('edit_users', 'Редактирование пользователей'),
        ('delete_users', 'Удаление пользователей'),
        
        # Управление студентами
        ('view_students', 'Просмотр студентов'),
        ('add_students', 'Добавление студентов'),
        ('edit_students', 'Редактирование студентов'),
        ('delete_students', 'Удаление студентов'),
        ('manage_student_payments', 'Управление оплатами студентов'),
        
        # Управление менторами
        ('view_mentors', 'Просмотр менторов'),
        ('add_mentors', 'Добавление менторов'),
        ('edit_mentors', 'Редактирование менторов'),
        ('delete_mentors', 'Удаление менторов'),
        
        # Управление курсами
        ('view_courses', 'Просмотр курсов'),
        ('add_courses', 'Добавление курсов'),
        ('edit_courses', 'Редактирование курсов'),
        ('delete_courses', 'Удаление курсов'),
        ('manage_course_content', 'Управление содержимым курсов'),
        
        # Управление организациями
        ('view_organizations', 'Просмотр организаций'),
        ('add_organizations', 'Добавление организаций'),
        ('edit_organizations', 'Редактирование организаций'),
        ('delete_organizations', 'Удаление организаций'),
        ('manage_organization_members', 'Управление участниками организаций'),
        
        # Управление финансами
        ('view_payments', 'Просмотр платежей'),
        ('add_payments', 'Добавление платежей'),
        ('edit_payments', 'Редактирование платежей'),
        ('delete_payments', 'Удаление платежей'),
        ('view_reports', 'Просмотр финансовых отчетов'),
        
        # Управление расписанием
        ('view_calendar', 'Просмотр расписания'),
        ('edit_calendar', 'Редактирование расписания'),
        ('manage_lessons', 'Управление занятиями'),
        
        # Управление настройками
        ('view_settings', 'Просмотр настроек'),
        ('edit_settings', 'Редактирование настроек'),
        ('manage_roles', 'Управление ролями'),
        
        # Управление отчетами
        ('view_reports', 'Просмотр отчетов'),
        ('generate_reports', 'Генерация отчетов'),
        
        # Управление уведомлениями
        ('view_notifications', 'Просмотр уведомлений'),
        ('send_notifications', 'Отправка уведомлений'),
        
        # Системные права
        ('access_admin_panel', 'Доступ к админ-панели'),
        ('view_logs', 'Просмотр логов'),
        ('manage_system', 'Управление системой'),
    ]
    
    # Создаем поля для каждого разрешения
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем поля разрешений
        for permission_code, permission_name in self.PERMISSION_CHOICES:
            self.fields[f'perm_{permission_code}'] = forms.BooleanField(
                label=permission_name,
                required=False,
                widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
            )
        
        # Устанавливаем начальные значения из JSON поля permissions
        if self.instance and self.instance.permissions:
            for permission_code, _ in self.PERMISSION_CHOICES:
                field_name = f'perm_{permission_code}'
                if field_name in self.fields:
                    self.fields[field_name].initial = self.instance.permissions.get(permission_code, False)
    
    class Meta:
        model = Role
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название роли'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Введите описание роли'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Собираем все разрешения в словарь
        permissions = {}
        for permission_code, _ in self.PERMISSION_CHOICES:
            field_name = f'perm_{permission_code}'
            if field_name in self.cleaned_data:
                permissions[permission_code] = self.cleaned_data[field_name]
        
        instance.permissions = permissions
        
        if commit:
            instance.save()
        
        return instance
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        # Проверка, что роль с таким названием еще не существует (кроме текущей)
        queryset = Role.objects.filter(name=name)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise forms.ValidationError('Роль с таким названием уже существует.')
        
        return name
