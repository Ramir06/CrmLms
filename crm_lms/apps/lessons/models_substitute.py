from django.db import models
from django.utils import timezone
from apps.accounts.models import CustomUser
from apps.mentors.models import MentorProfile


class MentorSubstitution(models.Model):
    """Замена ментора на конкретном уроке"""
    
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('completed', 'Завершено'),
        ('cancelled', 'Отменено'),
    ]
    
    lesson = models.ForeignKey(
        'lessons.Lesson', 
        on_delete=models.CASCADE,
        related_name='substitutions',
        verbose_name='Урок'
    )
    original_mentor = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='substitutions_as_original',
        verbose_name='Основной ментор',
        limit_choices_to={'role': 'mentor'}
    )
    substitute_mentor = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='substitutions_as_substitute',
        verbose_name='Заменяющий ментор',
        limit_choices_to={'role': 'mentor'}
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    reason = models.TextField(
        blank=True,
        verbose_name='Причина замены'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата подтверждения'
    )
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_substitutions',
        verbose_name='Кто создал'
    )
    
    class Meta:
        verbose_name = 'Замена ментора'
        verbose_name_plural = 'Замены менторов'
        ordering = ['-lesson__lesson_date', '-lesson__start_time']
        unique_together = ['lesson', 'original_mentor', 'substitute_mentor']
    
    def __str__(self):
        return f"Замена: {self.original_mentor.get_full_name()} → {self.substitute_mentor.get_full_name()} ({self.lesson.title})"
    
    def confirm(self):
        """Подтвердить замену"""
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
    
    def complete(self):
        """Завершить замену"""
        self.status = 'completed'
        self.save()
        
        # Устанавливаем временного ментора в урок
        self.lesson.temporary_mentor = self.substitute_mentor
        self.lesson.save(update_fields=['temporary_mentor'])
        
        # Создаем запись о проведенной замене
        from .models_substitute import CompletedSubstitution
        CompletedSubstitution.objects.get_or_create(
            substitute_mentor=self.substitute_mentor,
            original_mentor=self.original_mentor,
            course=self.lesson.course,
            lesson=self.lesson
        )
    
    def cancel(self):
        """Отменить замену"""
        self.status = 'cancelled'
        self.save()


class SubstituteAccess(models.Model):
    """Права доступа для заменяющего ментора"""
    
    substitution = models.OneToOneField(
        MentorSubstitution,
        on_delete=models.CASCADE,
        related_name='access',
        verbose_name='Замена'
    )
    can_mark_attendance = models.BooleanField(
        default=True,
        verbose_name='Может отмечать посещаемость'
    )
    can_create_materials = models.BooleanField(
        default=True,
        verbose_name='Может создавать материалы'
    )
    can_view_grades = models.BooleanField(
        default=True,
        verbose_name='Может просматривать оценки'
    )
    can_create_assignments = models.BooleanField(
        default=True,
        verbose_name='Может создавать задания'
    )
    can_grade_assignments = models.BooleanField(
        default=False,
        verbose_name='Может оценивать задания'
    )
    
    class Meta:
        verbose_name = 'Права доступа замены'
        verbose_name_plural = 'Права доступа замен'
    
    def __str__(self):
        return f"Права доступа для {self.substitution}"


class CompletedSubstitution(models.Model):
    """Отслеживание проведенных уроков заменяющим ментором"""
    
    substitute_mentor = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='completed_substitutions',
        verbose_name='Заменяющий ментор',
        limit_choices_to={'role': 'mentor'}
    )
    original_mentor = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='completed_substitutions_as_original',
        verbose_name='Основной ментор',
        limit_choices_to={'role': 'mentor'}
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='completed_substitutions',
        verbose_name='Курс'
    )
    lesson = models.ForeignKey(
        'lessons.Lesson',
        on_delete=models.CASCADE,
        related_name='completed_substitution',
        verbose_name='Урок'
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата проведения'
    )
    
    class Meta:
        verbose_name = 'Проведенная замена'
        verbose_name_plural = 'Проведенные замены'
        unique_together = ['substitute_mentor', 'course', 'lesson']
    
    def __str__(self):
        return f"Проведена замена: {self.substitute_mentor.get_full_name()} → {self.original_mentor.get_full_name()} ({self.course.title})"
