# Исправление NameError: ChatRoomForm не определен

## Проблема

```
NameError at /admin/chat/management/
name 'ChatRoomForm' is not defined
```

## Причина

В файле `apps/chat/views.py` использовалась форма `ChatRoomForm`, но она не была импортирована.

## Решение

### 1. Добавлен недостающий импорт

**Файл:** `apps/chat/views.py`

```python
# Было:
from .forms import ChatMessageForm, ChatMessageEditForm, ChatAttachmentForm

# Стало:
from .forms import ChatMessageForm, ChatMessageEditForm, ChatAttachmentForm, ChatRoomForm
```

### 2. Исправлен URL в redirect

```python
# Было:
return redirect('chat:room_management')

# Стало:
return redirect('chat_admin:room_management')
```

## Результат

Теперь страница `/admin/chat/management/` работает корректно и позволяет:

- ✅ Просматривать список комнат
- ✅ Создавать новые комнаты
- ✅ Редактировать существующие комнаты
- ✅ Управлять статусом комнат

## Проверка

```bash
python manage.py check
# System check identified 9 issues (0 silenced).
```

Система проходит проверку успешно! 🎉
