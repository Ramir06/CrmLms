# Функционал: Расписание с заменяющими менторами

## Описание

Добавлена система, которая автоматически обновляет расписание менторов при замене:
- **Основной ментор:** Исчезает из расписания на время замены
- **Заменяющий ментор:** Появляется в расписании на день замены

## Реализация

### 1. Новое поле в модели Lesson

**Файл:** `apps/lessons/models.py`

```python
temporary_mentor = models.ForeignKey(
    settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    related_name='temporarily_mentoring_lessons', verbose_name='Временный ментор (замена)',
    limit_choices_to={'role': 'mentor'}
)
```

### 2. Свойства для работы с заменами

```python
@property
def current_mentor(self):
    """Возвращает актуального ментора урока (основной или временный)"""
    return self.temporary_mentor or self.course.mentor

@property
def is_substituted(self):
    """Проверяет, есть ли замена на урок"""
    return bool(self.temporary_mentor)

@property
def mentor_display(self):
    """Отображение имени ментора с учетом замены"""
    if self.temporary_mentor:
        return f"{self.temporary_mentor.get_full_name()} (замена)"
    return self.course.mentor.get_full_name()
```

### 3. Обновление метода complete()

**Файл:** `apps/lessons/models_substitute.py`

```python
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
```

### 4. Обновление dashboard

**Файл:** `apps/dashboard/views.py`

```python
# Уроки основного ментора (без замен)
today_lessons = Lesson.objects.filter(
    course__mentor=user, 
    lesson_date=today,
    temporary_mentor__isnull=True  # Только уроки без замены
).count()
```

### 5. Обновление шаблона

**Файл:** `templates/mentor/dashboard/index.html`

```html
<div class="text-muted mb-2" style="font-size:12px;">
    {% if sub_course.lesson.is_substituted %}
        Замена: {{ sub_course.original_mentor.get_full_name() }} → {{ sub_course.lesson.current_mentor.get_full_name() }}
    {% else %}
        Замена: {{ sub_course.original_mentor.get_full_name() }} → {{ sub_course.substitution.substitute_mentor.get_full_name() }}
    {% endif %}
</div>
```

## Как это работает

### 1. Процесс замены
1. Создается замена ментора (`MentorSubstitution`)
2. Заменяющий ментор подтверждает замену
3. При отметке посещаемости замена автоматически завершается
4. В урок устанавливается временный ментор

### 2. Обновление расписания
1. **Основной ментор:** Уроки с `temporary_mentor` исключаются из его расписания
2. **Заменяющий ментор:** Курс появляется в его расписании на день замены
3. **После проведения:** Курс исключается из списка доступных для замены

### 3. Отображение в интерфейсе
- **До замены:** Показывается основной ментор
- **Во время замены:** Показывается "Замена: Основной → Заменяющий"
- **После замены:** Сохраняется история проведенных замен

## Преимущества

### 1. Для менторов
- **Четкое расписание:** Понятно, кто проводит урок
- **Без конфликтов:** Исключаются двойные назначения
- **Визуальные индикаторы:** Явное отображение замен

### 2. Для системы
- **Автоматизация:** Не требует ручного управления расписанием
- **История:** Сохраняются все замены
- **Надежность:** Исключает человеческий фактор

## Миграции

Созданы и применены миграции:
- `0004_lesson_temporary_mentor.py` - Добавление поля `temporary_mentor` в модель `Lesson`

## Использование

### Проверка текущего ментора урока
```python
from apps.lessons.models import Lesson

lesson = Lesson.objects.get(pk=lesson_id)
current_mentor = lesson.current_mentor  # Основной или временный
is_substituted = lesson.is_substituted  # Есть ли замена
mentor_name = lesson.mentor_display  # Отображение с учетом замены
```

### Фильтрация уроков без замен
```python
# Уроки основного ментора (только его)
mentor_lessons = Lesson.objects.filter(
    course__mentor=mentor_user,
    temporary_mentor__isnull=True
)

# Уроки с заменами
substituted_lessons = Lesson.objects.filter(
    temporary_mentor__isnull=False
).select_related('temporary_mentor')
```

### Получение истории замен
```python
from apps.lessons.models_substitute import CompletedSubstitution

# Все проведенные замены ментора
completed_substitutions = CompletedSubstitution.objects.filter(
    substitute_mentor=request.user
).select_related('course', 'lesson', 'original_mentor')
```

## Итог

Система обеспечивает корректное отображение расписания с учетом замен, делая его понятным и актуальным для всех участников учебного процесса.
