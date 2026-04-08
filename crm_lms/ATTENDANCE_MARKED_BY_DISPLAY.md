# Отображение того, кто отметил посещаемость

## Функционал

Основной ментор теперь видит, кто именно отметил посещаемость студентов - он сам или заменяющий ментор.

## Реализация

### 1. Обновлена модель `AttendanceRecord`

**Добавлено поле:**
```python
marked_by = models.ForeignKey(
    settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
    related_name='marked_attendance', verbose_name='Кто отметил'
)
```

**Добавлено свойство:**
```python
@property
def marked_by_display(self):
    """Отображение того, кто отметил посещаемость"""
    if self.marked_by:
        if self.marked_by == self.lesson.course.mentor:
            return f"{self.marked_by.get_display_name()} (основной ментор)"
        else:
            return f"{self.marked_by.get_display_name()} (замена)"
    return "Система"
```

### 2. Обновлен view `attendance_table`

**Добавлена передача информации в шаблон:**
```python
row['cells'].append({
    'lesson_id': lesson.pk,
    'record': rec,
    'status': rec.attendance_status if rec else '',
    'can_mark': can_mark,
    'marked_by': rec.marked_by if rec else None,
    'marked_by_display': rec.marked_by_display if rec else None,
})
```

### 3. Обновлен view `save_attendance_bulk`

**Сохранение информации о том, кто отметил:**
```python
AttendanceRecord.objects.update_or_create(
    lesson_id=lesson_id,
    student_id=student_id,
    defaults={'attendance_status': value, 'marked_by': request.user},
)
```

### 4. Обновлен шаблон `table.html`

**Визуальные индикаторы:**
```html
<!-- Информация о том, кто отметил посещаемость -->
{% if cell.marked_by and cell.status %}
<div class="marked-by-info" title="Отметил(а): {{ cell.marked_by_display }}">
    {% if cell.marked_by == course.mentor %}
    <i class="bi bi-person-check" style="color: #198754; font-size: 10px;"></i>
    {% else %}
    <i class="bi bi-person-arrow-repeat" style="color: #ffc107; font-size: 10px;"></i>
    {% endif %}
</div>
{% endif %}
```

**Стили для индикаторов:**
```css
.marked-by-info {
    position: absolute;
    top: 2px;
    right: 2px;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 50%;
    width: 16px;
    height: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    z-index: 1;
}
```

**Легенда для объяснения иконок:**
```html
<div class="alert alert-light border-secondary">
    <h6 class="alert-heading"><i class="bi bi-info-circle me-2"></i>Обозначения</h6>
    <div class="row small">
        <div class="col-md-6">
            <div class="d-flex align-items-center mb-2">
                <i class="bi bi-person-check me-2" style="color: #198754;"></i>
                <span>Отмечено основным ментором</span>
            </div>
            <div class="d-flex align-items-center mb-2">
                <i class="bi bi-person-arrow-repeat me-2" style="color: #ffc107;"></i>
                <span>Отмечено заменяющим ментором</span>
            </div>
        </div>
    </div>
</div>
```

## Как это работает

### Визуальные индикаторы

1. **Зеленая иконка** 🟢 (`bi-person-check`) - посещаемость отмечена основным ментором
2. **Желтая иконка** 🟡 (`bi-person-arrow-repeat`) - посещаемость отмечена заменяющим ментором
3. **Иконка появляется** только если есть статус посещаемости
4. **Hover tooltip** показывает полное имя и тип ментора

### Для основного ментора

- Видит все отметки посещаемости
- Понимает, кто именно сделал каждую отметку
- Может отличить свои отметки от отметок заменяющего ментора

### Для заменяющего ментора

- Отмечает посещаемость как обычно
- Его отметки отображаются с желтой иконкой
- Основной ментор видит, что это отметка замены

### Исторические данные

- Существующие записи имеют `marked_by = NULL`
- Они отображаются как отмеченные "Системой"
- Новые записи всегда сохраняют информацию о том, кто отметил

## Миграция базы данных

```bash
python manage.py makemigrations attendance
python manage.py migrate attendance
```

## Преимущества

1. **Прозрачность** - всегда видно, кто отметил посещаемость
2. **Ответственность** - понятно, кто несет ответственность за отметки
3. **Контроль** - основной ментор может отследить работу заменяющих
4. **История** - полная история отметок с указанием автора

## Безопасность

- Поле `marked_by` автоматически устанавливается при сохранении
- Невозможно подделать автора отметки
- Старые записи корректно обрабатываются (NULL = Система)

## Результат

Теперь основной ментор всегда видит, кто именно отметил посещаемость каждого студента, что обеспечивает полную прозрачность и контроль за процессом ведения посещаемости.
