from django.db import models
from apps.core.models import TimeStampedModel, OrganizationMixin


class Student(OrganizationMixin, TimeStampedModel):
    GENDER_CHOICES = [('male', 'Мужской'), ('female', 'Женский')]
    SOURCE_CHOICES = [
        ('instagram', 'Instagram'), ('telegram', 'Telegram'),
        ('referral', 'Реферал'), ('website', 'Сайт'), ('other', 'Другое'),
    ]
    STATUS_CHOICES = [
        ('active', 'Активный'), ('inactive', 'Неактивный'),
        ('graduated', 'Окончил'), ('expelled', 'Отчислен'),
        ('left', 'Ушедший'),
    ]

    full_name = models.CharField(max_length=200, verbose_name='Полное имя')
    first_name = models.CharField(max_length=100, blank=True, verbose_name='Имя')
    last_name = models.CharField(max_length=100, blank=True, verbose_name='Фамилия')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    parent_name = models.CharField(max_length=200, blank=True, verbose_name='Имя родителя')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон родителя')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, verbose_name='Пол')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, blank=True, verbose_name='Источник')
    note = models.TextField(blank=True, verbose_name='Примечание')
    bio = models.TextField(blank=True, verbose_name='О себе')
    profile_image = models.ImageField(upload_to='student_avatars/', null=True, blank=True, verbose_name='Аватар')
    language = models.CharField(max_length=5, default='ru', choices=[
        ('ru', 'Русский'), ('ky', 'Кыргызский'), ('en', 'English')
    ], verbose_name='Язык интерфейса')
    email_notifications = models.JSONField(default=dict, blank=True, verbose_name='Email уведомления')
    two_factor_enabled = models.BooleanField(default=False, verbose_name='Двухфакторная аутентификация')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name='Статус')
    user_account = models.OneToOneField(
        'accounts.CustomUser', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='student_profile',
        verbose_name='Аккаунт пользователя'
    )

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'
        ordering = ['full_name']

    def __str__(self):
        return self.full_name

    def get_full_name(self):
        """Возвращает полное имя студента"""
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        return self.full_name

    def get_active_courses(self):
        return self.course_enrollments.filter(status='active').select_related('course')


class StudentNote(TimeStampedModel):
    """Заметки ментора о студенте"""
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, 
        related_name='mentor_notes',
        verbose_name='Студент'
    )
    mentor = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.CASCADE,
        verbose_name='Ментор'
    )
    text = models.TextField(verbose_name='Текст заметки')
    
    class Meta:
        verbose_name = 'Заметка ментора'
        verbose_name_plural = 'Заметки менторов'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заметка о {self.student.full_name} от {self.mentor.get_display_name}'


class AdminStudentNote(TimeStampedModel):
    """Заметки администратора о студенте"""
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, 
        related_name='admin_notes',
        verbose_name='Студент'
    )
    admin = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.CASCADE,
        verbose_name='Администратор'
    )
    text = models.TextField(verbose_name='Текст заметки')
    
    class Meta:
        verbose_name = 'Заметка администратора'
        verbose_name_plural = 'Заметки администраторов'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заметка администратора о {self.student.full_name} от {self.admin.get_display_name}'
