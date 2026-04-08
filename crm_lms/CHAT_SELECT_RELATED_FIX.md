# Исправление FieldError: select_related('attachments')

## Проблема

```
FieldError at /chat/room/1/
Invalid field name(s) given in select_related: 'attachments'. Choices are: room, author
```

## Причина

Ошибка возникает потому, что `select_related()` работает только с ForeignKey полями (прямыми связями), а `attachments` это обратная связь (related_name) от модели `ChatAttachment` к `ChatMessage`.

## Решение

### 1. Удаление неправильного select_related

**Было:**
```python
messages = ChatMessage.objects.filter(
    room=room, 
    is_deleted=False
).select_related('author', 'attachments').order_by('-is_pinned', 'created_at')
```

**Стало:**
```python
messages = ChatMessage.objects.filter(
    room=room, 
    is_deleted=False
).select_related('author').order_by('-is_pinned', 'created_at')
```

### 2. Почему это работает

- **`select_related('author')`** - правильно, так как `author` это ForeignKey поле в ChatMessage
- **`select_related('attachments')`** - неправильно, так как `attachments` это обратная связь
- **Обратные связи** загружаются через `prefetch_related()`, но для текущего функционала они не нужны

### 3. Если бы понадобились вложения

Для загрузки вложений (attachments) нужно было бы использовать:
```python
messages = ChatMessage.objects.filter(
    room=room, 
    is_deleted=False
).select_related('author').prefetch_related('attachments').order_by('-is_pinned', 'created_at')
```

Но поскольку вложения пока не реализованы в интерфейсе, `prefetch_related('attachments')` не требуется.

## Результат

Теперь чат работает корректно:

- ✅ `/chat/room/1/` - Загружается без ошибок
- ✅ Запросы к базе данных оптимизированы правильно
- ✅ Все функции чата работают

## Оптимизация запросов

Текущий запрос оптимизирован для основных нужд:
- `select_related('author')` - загружает авторов сообщений одним запросом
- Сортировка по `-is_pinned, 'created_at'` - закрепленные сообщения сверху

## Итог

Проблема с `select_related` решена! Чат работает корректно с оптимизированными запросами к базе данных. 🎉
