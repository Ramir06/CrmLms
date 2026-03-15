import uuid
from django.db import models
from apps.core.models import TimeStampedModel


class Quiz(TimeStampedModel):
    course = models.ForeignKey(
        'courses.Course', on_delete=models.CASCADE,
        related_name='quizzes', verbose_name='Курс'
    )
    section = models.ForeignKey(
        'lectures.Section', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='quizzes', verbose_name='Раздел'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    time_limit = models.PositiveIntegerField(default=0, verbose_name='Лимит времени (мин, 0=без лимита)')
    pass_score = models.PositiveSmallIntegerField(default=60, verbose_name='Проходной балл (%)')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} ({self.course.title})'

    def total_points(self):
        return sum(q.points for q in self.questions.all())

    def questions_count(self):
        return self.questions.count()


class Question(TimeStampedModel):
    TYPE_SINGLE = 'single'
    TYPE_MULTIPLE = 'multiple'
    TYPE_CHOICES = [
        ('single', 'Один правильный ответ'),
        ('multiple', 'Несколько правильных ответов'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name='Тест')
    text = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='single', verbose_name='Тип')
    points = models.PositiveSmallIntegerField(default=1, verbose_name='Баллы')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]

    def correct_choices(self):
        return self.choices.filter(is_correct=True)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices', verbose_name='Вопрос')
    text = models.CharField(max_length=500, verbose_name='Текст варианта')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответа'
        ordering = ['order', 'id']

    def __str__(self):
        return self.text[:60]


class QuizAttempt(TimeStampedModel):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts', verbose_name='Тест')
    course_student = models.ForeignKey(
        'courses.CourseStudent', on_delete=models.CASCADE,
        related_name='quiz_attempts', verbose_name='Студент курса'
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Начало')
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Сдано')
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Набрано баллов')
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Макс. баллов')
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Процент')
    passed = models.BooleanField(default=False, verbose_name='Сдан')

    class Meta:
        verbose_name = 'Попытка теста'
        verbose_name_plural = 'Попытки тестов'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.course_student.student} — {self.quiz.title}'

    @property
    def is_submitted(self):
        return self.submitted_at is not None


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name='Попытка')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос')
    selected_choices = models.ManyToManyField(Choice, blank=True, verbose_name='Выбранные варианты')
    is_correct = models.BooleanField(default=False, verbose_name='Правильно')
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Заработано баллов')

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'
        unique_together = ('attempt', 'question')

    def __str__(self):
        return f'Ответ на: {self.question}'
