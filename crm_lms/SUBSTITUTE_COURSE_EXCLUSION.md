# Функционал: Исключение курсов после проведения замен

## Описание

Добавлена система, которая автоматически исключает курсы из списка доступных для заменяющего ментора после того, как он провел урок в качестве замены.

## Реализация

### 1. Новая модель CompletedSubstitution

**Файл:** `apps/lessons/models_substitute.py`

```python
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
```

### 2. Обновление метода complete()

**Файл:** `apps/lessons/models_substitute.py`

```python
def complete(self):
    """Завершить замену"""
    self.status = 'completed'
    self.save()
    
    # Создаем запись о проведенной замене
    from .models_substitute import CompletedSubstitution
    CompletedSubstitution.objects.get_or_create(
        substitute_mentor=self.substitute_mentor,
        original_mentor=self.original_mentor,
        course=self.lesson.course,
        lesson=self.lesson
    )
```

### 3. Фильтрация курсов в dashboard

**Файл:** `apps/dashboard/views.py`

```python
# Основные курсы ментора
my_courses = Course.objects.filter(mentor=user, is_archived=False).prefetch_related('course_students').order_by('status', 'title')

# Исключаем курсы, где ментор был заменяющим и уже провел урок
from apps.lessons.models_substitute import CompletedSubstitution
completed_course_ids = CompletedSubstitution.objects.filter(
    substitute_mentor=user
).values_list('course_id', flat=True)

my_courses = my_courses.exclude(id__in=completed_course_ids)
```

### 4. Автоматическое завершение замен

**Файл:** `apps/attendance/views.py`

При отметке посещаемости для урока, система автоматически проверяет, является ли отмечающий заменяющим ментором, и если да - завершает замену:

```python
# Проверяем, был ли это заменой и завершаем ее если нужно
from apps.lessons.models_substitute import MentorSubstitution
try:
    substitution = MentorSubstitution.objects.get(
        lesson=lesson,
        substitute_mentor=request.user,
        status='confirmed'
    )
    substitution.complete()
except MentorSubstitution.DoesNotExist:
    pass
```

## Как это работает

### 1. Процесс замены
1. Создается замена ментора (`MentorSubstitution`)
2. Заменяющий ментор подтверждает замену
3. Заменяющий ментор проводит урок и отмечает посещаемость

### 2. Автоматическое исключение курса
1. При отметке посещаемости система определяет, что это замена
2. Вызывается метод `substitution.complete()`
3. Создается запись в `CompletedSubstitution`
4. Курс исключается из списка доступных для этого ментора

### 3. Результат для ментора
- **До проведения урока:** Курс виден в списке замен на сегодня
- **После проведения урока:** Курс исчезает из основного списка курсов
- **Постоянная запись:** Система помнит, что ментор уже провел урок по этому курсу

## Преимущества

### 1. Для заменяющего ментора
- **Четкая логика:** Понятно, какие курсы доступны для замены
- **Без дублирования:** Не будет показывать курсы, где уже был
- **История:** Сохраняется информация о всех проведенных заменах

### 2. Для системы
- **Автоматизация:** Не требует ручного вмешательства
- **Надежность:** Исключает человеческий фактор
- **Масштабируемость:** Легко расширить функционал

## Миграции

Созданы и применены миграции:
- `0003_completedsubstitution.py` - Создание модели `CompletedSubstitution`

## Использование

### Проверка проведенных замен
```python
from apps.lessons.models_substitute import CompletedSubstitution

# Получить все проведенные замены ментора
completed = CompletedSubstitution.objects.filter(
    substitute_mentor=request.user
).select_related('course', 'lesson', 'original_mentor')

# Получить курсы, где ментор уже проводил уроки
completed_course_ids = completed.values_list('course_id', flat=True)
```

### Исключение из запросов
```python
# Исключить курсы с проведенными уроками
available_courses = Course.objects.filter(
    is_archived=False
).exclude(
    id__in=CompletedSubstitution.objects.filter(
        substitute_mentor=user
    ).values_list('course_id', flat=True)
)
```

## Итог

Система обеспечивает логичное и автоматическое управление доступом заменяющих менторов к курсам, предотвращая путаницу и дублирование в интерфейсе.
