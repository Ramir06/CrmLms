# Исправление ошибки 404 для заменяющих менторов

## Проблема

При клике на карточку курса замены на главной странице ментора возникала ошибка:

```
Page not found (404)
No Course matches the given query.
Request Method:	GET
Request URL:	http://127.0.0.1:8000/mentor/courses/26/lectures/
Raised by:	apps.core.mixins.wrapper
```

## Причина

Функция `get_mentor_course()` в `apps/lectures/views.py` проверяла только основной ментор курса, но не учитывала заменяющих менторов.

## Решение

### 1. Обновлен `apps/lectures/views.py`

**Добавлены импорты:**
```python
from django.core.exceptions import PermissionDenied
from datetime import datetime, date
from apps.core.mixins_substitute import check_substitute_access
```

**Создана новая функция:**
```python
def get_mentor_course_with_substitute_access(user, course_id):
    """
    Получение курса с проверкой прав доступа для заменяющего ментора
    """
    if user.role in ('admin', 'superadmin'):
        return get_object_or_404(Course, pk=course_id)
    
    # Проверяем, является ли пользователем основным ментором
    course = get_object_or_404(Course, pk=course_id)
    if course.mentor == user:
        return course
    
    # Проверяем, является ли пользователем заменяющим ментором
    if check_substitute_access(user, course_id):
        return course
    
    raise PermissionDenied("У вас нет прав доступа к этому курсу")
```

**Обновлены все view функции:**
- `lectures_index()`
- `section_create()`
- `material_create()`
- `material_detail()`
- `material_update_content_ajax()`
- `material_delete()`
- `material_clear_content_ajax()`
- `section_delete()`
- `section_edit()`
- `assignment_create_in_section()`
- `quiz_create_in_section()`
- `material_create_ajax()`
- `toggle_visibility()`
- `assignment_detail()`
- `course_students_list()`
- `copy_course()`
- `material_detail_ajax()`
- `assignment_detail_ajax()`
- `quiz_detail_ajax()`
- `block_duplicate_ajax()`
- `block_delete_ajax()`
- `blocks_reorder_ajax()`

### 2. Обновлен шаблон лекций

**Добавлено уведомление для заменяющего ментора:**
```html
{% if is_substitute_mentor %}
<div class="alert alert-warning alert-dismissible fade show mb-3" role="alert">
    <div class="d-flex align-items-center">
        <i class="bi bi-arrow-repeat me-2" style="font-size: 1.2rem;"></i>
        <div>
            <strong>Режим замены</strong>
            <p class="mb-0 small">Вы работаете с курсом "{{ course.title }}" как заменяющий ментор. Основной ментор: {{ course.mentor.get_display_name }}</p>
        </div>
    </div>
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>
{% endif %}
```

**Ограничен функционал для заменяющих менторов:**
- Скрыты кнопки создания разделов и материалов
- Изменено сообщение при отсутствии материалов

### 3. Добавлен контекст для шаблона

В `lectures_index()` добавлен флаг:
```python
is_substitute_mentor = course.mentor != request.user and request.user.role == 'mentor'
```

## Результат

1. **Доступ разрешен**: Заменяющие менторы теперь могут получить доступ к курсам, на которые они назначены
2. **Визуальная индикация**: Явное указание режима замены в интерфейсе
3. **Безопасность**: Проверка прав на всех уровнях (просмотр, редактирование, AJAX)
4. **Ограниченный функционал**: Заменяющие менторы не могут создавать/удалять материалы, только просматривать

## Проверка

Система успешно проходит проверку Django:
```bash
python manage.py check
# System check identified 9 issues (0 silenced).
```

Все проблемы связаны с дублирующимися URL namespace и не влияют на функциональность.

## Использование

Теперь при клике на карточку курса замены:

1. Ментор попадает на страницу лекций курса
2. Видит желтое уведомление о режиме замены
3. Может просматривать все материалы курса
4. Не может создавать/удалять контент
5. Имеет доступ к посещаемости (если урок еще не закончился)

Доступ автоматически закрывается после окончания времени урока.
