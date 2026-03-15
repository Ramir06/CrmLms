import uuid
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class LessonFeedbackLink(TimeStampedModel):
    """A unique shareable link for collecting feedback on a specific lesson."""
    lesson = models.OneToOneField(
        'lessons.Lesson', on_delete=models.CASCADE,
        related_name='feedback_link', verbose_name='Занятие'
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Ссылка на отзыв'
        verbose_name_plural = 'Ссылки на отзывы'

    def __str__(self):
        return f'Feedback link for {self.lesson}'


class LessonFeedback(TimeStampedModel):
    """Individual student feedback for a lesson."""
    feedback_link = models.ForeignKey(
        LessonFeedbackLink, on_delete=models.CASCADE,
        related_name='responses', verbose_name='Ссылка'
    )
    student_name = models.CharField(max_length=200, blank=True, verbose_name='Имя студента')
    mentor_rating = models.PositiveSmallIntegerField(
        verbose_name='Оценка работы ментора',
        help_text='От 1 до 5'
    )
    self_activity = models.PositiveSmallIntegerField(
        verbose_name='Оценка своей активности',
        help_text='От 1 до 5'
    )
    mood = models.PositiveSmallIntegerField(
        verbose_name='Настроение на уроке',
        help_text='От 1 до 5'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')

    class Meta:
        verbose_name = 'Отзыв по уроку'
        verbose_name_plural = 'Отзывы по урокам'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student_name} — {self.feedback_link.lesson}'


class Review(TimeStampedModel):
    TYPE_CHOICES = [
        ('student_review', 'Отзыв о студенте'),
        ('course_review', 'Отзыв о курсе'),
        ('note', 'Заметка'),
    ]

    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='reviews', verbose_name='Курс'
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviews', verbose_name='Студент'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='written_reviews', verbose_name='Автор'
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='note', verbose_name='Тип')
    content = models.TextField(verbose_name='Содержимое')
    rating = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Оценка (1-5)')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author} — {self.course} ({self.get_type_display()})'
