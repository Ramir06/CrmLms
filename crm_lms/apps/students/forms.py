from django import forms
from apps.accounts.models import CustomUser
from .models import Student
from apps.settings.views import get_student_form_fields


class StudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Получаем настроенные поля
        enabled_fields = get_student_form_fields()
        
        # Настраиваем поля в зависимости от системных настроек
        if 'login' not in enabled_fields:
            self.fields.pop('username', None)
        else:
            self.fields['username'] = forms.CharField(
                label='Username (логин)',
                widget=forms.TextInput(attrs={'class': 'form-control'}),
                help_text='Уникальный логин для входа (например: student01, anna, aria)'
            )
        
        if 'email' not in enabled_fields:
            self.fields.pop('email', None)
        else:
            self.fields['email'] = forms.EmailField(
                label='Email',
                widget=forms.EmailInput(attrs={'class': 'form-control'}),
                required=False,
                help_text='Необязательное поле'
            )
        
        if 'password' not in enabled_fields:
            self.fields.pop('password', None)
        else:
            self.fields['password'] = forms.CharField(
                label='Пароль',
                widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
                required=False,
                help_text='Оставьте пустым, чтобы не менять (при редактировании)',
            )
        
        # Настраиваем остальные поля
        if 'firstname' not in enabled_fields:
            self.fields.pop('first_name', None)
        
        if 'lastname' not in enabled_fields:
            self.fields.pop('last_name', None)
        
        if 'phone' not in enabled_fields:
            self.fields.pop('phone', None)
        
        if 'birthdate' not in enabled_fields:
            self.fields.pop('birth_date', None)
        
        if 'address' not in enabled_fields:
            self.fields.pop('parent_name', None)
            self.fields.pop('parent_phone', None)
        
        if 'source' not in enabled_fields:
            self.fields.pop('source', None)
        
        if 'status' not in enabled_fields:
            self.fields.pop('status', None)
        
        # Логика для редактирования
        if self.instance and self.instance.pk:
            # Editing existing student
            if self.instance.user_account:
                if 'login' in enabled_fields:
                    self.fields['username'].initial = self.instance.user_account.username
                if 'email' in enabled_fields:
                    self.fields['email'].initial = self.instance.user_account.email
            if 'password' in enabled_fields:
                self.fields['password'].required = False
        else:
            # Creating new student
            if 'password' in enabled_fields:
                self.fields['password'].required = True

    class Meta:
        model = Student
        fields = ['full_name', 'first_name', 'last_name', 'phone', 'parent_name',
                  'parent_phone', 'birth_date', 'gender', 'source', 'note', 'status']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'source': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not username:
            return None
            
        qs = CustomUser.objects.filter(username=username)
        if self.instance and self.instance.pk and self.instance.user_account:
            qs = qs.exclude(pk=self.instance.user_account.pk)
        if qs.exists():
            raise forms.ValidationError('Пользователь с таким username уже существует.')
        return username

    def save(self, commit=True):
        student = super().save(commit=False)
        
        # Получаем данные с проверкой наличия полей
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        # Получаем текущие настройки
        enabled_fields = get_student_form_fields()

        if student.pk and student.user_account:
            # Update existing user
            user = student.user_account
            if 'login' in enabled_fields:
                user.username = username
            if 'email' in enabled_fields:
                user.email = email or ''
            user.full_name = student.full_name
            if 'firstname' in enabled_fields:
                user.first_name = student.first_name
            if 'lastname' in enabled_fields:
                user.last_name = student.last_name
            if 'phone' in enabled_fields:
                user.phone = student.phone
            if password and 'password' in enabled_fields:
                user.set_password(password)
            user.save()
        else:
            # Create new user account
            if 'login' in enabled_fields and username:
                # Создаем пользователя с username
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email or '',
                    password=password,
                    full_name=student.full_name,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    phone=student.phone,
                    role='student',
                )
            else:
                # Создаем пользователя без username (генерируем автоматически)
                import uuid
                auto_username = f"student_{uuid.uuid4().hex[:8]}"
                user = CustomUser.objects.create_user(
                    username=auto_username,
                    email=email or '',
                    password=password or 'defaultpassword123',
                    full_name=student.full_name,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    phone=student.phone,
                    role='student',
                )
            
            student.user_account = user

        if commit:
            student.save()
        return student
