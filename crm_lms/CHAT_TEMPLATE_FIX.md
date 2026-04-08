# Исправление TemplateDoesNotExist: admin_base.html

## Проблема

```
TemplateDoesNotExist at /admin/chat/management/
admin/admin_base.html
```

## Причина

Шаблоны чата использовали неправильный путь к базовому шаблону администратора.

## Решение

### 1. Найден правильный базовый шаблон

**Правильный путь:** `base/admin_base.html`
**Неправильный путь:** `admin/admin_base.html`

### 2. Исправлены шаблоны

**Файл:** `templates/chat/room_management.html`
```django
<!-- Было -->
{% extends "admin/admin_base.html" %}

<!-- Стало -->
{% extends "base/admin_base.html" %}
```

**Файл:** `templates/chat/edit_room.html`
```django
<!-- Было -->
{% extends "admin/admin_base.html" %}

<!-- Стало -->
{% extends "base/admin_base.html" %}
```

## Результат

Теперь административные шаблоны чата работают корректно:

- ✅ `/admin/chat/management/` - Управление комнатами
- ✅ `/admin/chat/management/edit/1/` - Редактирование комнаты

## Структура шаблонов

```
templates/
├── base/
│   └── admin_base.html          # Базовый шаблон админа
└── chat/
    ├── room_management.html     # Управление комнатами
    └── edit_room.html          # Редактирование комнаты
```

Все шаблоны теперь правильно наследуются от `base/admin_base.html` и отображаются корректно! 🎉
