from django import forms
from apps.accounts.models import CustomUser
from .models import Student


class StudentForm(forms.ModelForm):
    email = forms.EmailField(
        label='Email (логин)',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
        required=False,
        help_text='Оставьте пустым, чтобы не менять (при редактировании)',
    )

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Editing existing student
            if self.instance.user_account:
                self.fields['email'].initial = self.instance.user_account.email
            self.fields['password'].required = False
        else:
            # Creating new student — password is required
            self.fields['password'].required = True

    def clean_email(self):
        email = self.cleaned_data['email']
        qs = CustomUser.objects.filter(email=email)
        if self.instance and self.instance.pk and self.instance.user_account:
            qs = qs.exclude(pk=self.instance.user_account.pk)
        if qs.exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        student = super().save(commit=False)
        email = self.cleaned_data['email']
        password = self.cleaned_data.get('password')

        if student.pk and student.user_account:
            # Update existing user
            user = student.user_account
            user.email = email
            user.full_name = student.full_name
            user.first_name = student.first_name
            user.last_name = student.last_name
            user.phone = student.phone
            if password:
                user.set_password(password)
            user.save()
        else:
            # Create new user account
            # Генерируем уникальный логин на основе имени
            import re
            from django.utils.text import slugify
            
            # Создаем базовый логин из имени
            base_login = slugify(student.first_name.lower() if student.first_name else student.full_name.split()[0].lower())
            if not base_login:
                base_login = 'student'
            
            # Добавляем цифры для уникальности
            login = base_login
            counter = 1
            while CustomUser.objects.filter(username=login).exists():
                login = f"{base_login}{counter}"
                counter += 1
            
            user = CustomUser.objects.create_user(
                username=login,  # Уникальный логин
                email=email,
                password=password,
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
