from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class Assignment(TimeStampedModel):
    section = models.ForeignKey(
        'lectures.Section', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assignments', verbose_name='Раздел'
    )
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='assignments', verbose_name='Курс'
    )
    quiz = models.OneToOneField(
        'quizzes.Quiz', on_delete=models.CASCADE, null=True, blank=True,
        related_name='assignment', verbose_name='Связанный тест'
    )
    title = models.CharField(max_length=200, verbose_name='Название задания')
    description = models.TextField(blank=True, verbose_name='Описание')
    max_score = models.PositiveSmallIntegerField(default=100, verbose_name='Макс. балл')
    due_date = models.DateField(null=True, blank=True, verbose_name='Срок сдачи')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')
    is_required = models.BooleanField(default=True, verbose_name='Обязательное')
    is_visible = models.BooleanField(default=True, verbose_name='Видимое')

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['order', 'id']

    def __str__(self):
        return f'{self.course.title} — {self.title}'
    
    def get_quiz_score(self, student):
        """Получает результат студента по связанному тесту"""
        if not self.quiz:
            return None
        
        from apps.courses.models import CourseStudent
        try:
            course_student = CourseStudent.objects.get(course=self.course, student=student)
            attempt = self.quiz.attempts.filter(course_student=course_student, submitted_at__isnull=False).first()
            if attempt:
                return {
                    'score': attempt.score,
                    'max_score': attempt.max_score,
                    'percentage': attempt.percentage,
                    'passed': attempt.passed,
                    'submitted_at': attempt.submitted_at
                }
        except CourseStudent.DoesNotExist:
            pass
        return None


class AssignmentSubmission(TimeStampedModel):
    STATUS_CHOICES = [
        ('not_submitted', 'Не сдано'),
        ('submitted', 'Сдано'),
        ('checked', 'Проверено'),
        ('revision', 'На доработке'),
    ]

    assignment = models.ForeignKey(
        Assignment, on_delete=models.CASCADE,
        related_name='submissions', verbose_name='Задание'
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE,
        related_name='submissions', verbose_name='Студент'
    )
    answer_text = models.TextField(blank=True, verbose_name='Ответ текстом')
    file = models.FileField(upload_to='submissions/', null=True, blank=True, verbose_name='Файл ответа')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата отправки')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='not_submitted', verbose_name='Статус'
    )

    class Meta:
        verbose_name = 'Ответ на задание'
        verbose_name_plural = 'Ответы на задания'
        unique_together = ('assignment', 'student')

    def __str__(self):
        return f'{self.student} — {self.assignment}'


class AssignmentGrade(TimeStampedModel):
    submission = models.OneToOneField(
        AssignmentSubmission, on_delete=models.CASCADE,
        related_name='grade', verbose_name='Ответ'
    )
    score = models.DecimalField(max_digits=6, decimal_places=2, verbose_name='Оценка')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='checked_grades', verbose_name='Проверил'
    )
    checked_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата проверки')
    
    # AI-оценка поля
    ai_graded = models.BooleanField(default=False, verbose_name='Проверено ИИ')
    ai_confidence = models.IntegerField(null=True, blank=True, verbose_name='Уверенность ИИ (%)')
    ai_feedback = models.JSONField(null=True, blank=True, verbose_name='AI обратная связь')
    ai_strengths = models.TextField(blank=True, verbose_name='Сильные стороны (ИИ)')
    ai_weaknesses = models.TextField(blank=True, verbose_name='Слабые стороны (ИИ)')
    ai_suggestions = models.TextField(blank=True, verbose_name='Рекомендации (ИИ)')
    plagiarism_suspicious = models.BooleanField(default=False, verbose_name='Подозрение на плагиат')
    plagiarism_reason = models.TextField(blank=True, verbose_name='Причина подозрения')

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'

    def __str__(self):
        return f'{self.submission} — {self.score}'
