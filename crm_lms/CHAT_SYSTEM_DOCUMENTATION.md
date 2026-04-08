# Общий чат для администраторов, суперадминистраторов и менторов

## Функционал

Создан полнофункциональный чат для общения между администраторами, суперадминистраторами и менторами с возможностью:

- **Отправка сообщений** в реальном времени
- **Редактирование** своих сообщений (в течение 1 часа)
- **Удаление** сообщений (авторы - в течение 24 часов, админы - всегда)
- **Закрепление** важных сообщений (только администраторы)
- **Статус прочтения** сообщений
- **Автообновление** новых сообщений каждые 5 секунд

## Архитектура

### Модели данных

**ChatRoom** - Комнаты чата
```python
class ChatRoom(TimeStampedModel):
    name = models.CharField(max_length=100, verbose_name='Название комнаты')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
```

**ChatMessage** - Сообщения
```python
class ChatMessage(TimeStampedModel):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(verbose_name='Содержание')
    is_pinned = models.BooleanField(default=False, verbose_name='Закреплено')
    is_edited = models.BooleanField(default=False, verbose_name='Отредактировано')
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, verbose_name='Удалено')
    deleted_at = models.DateTimeField(null=True, blank=True)
```

**ChatReadStatus** - Статус прочтения
```python
class ChatReadStatus(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    last_read_message = models.ForeignKey(ChatMessage, on_delete=models.SET_NULL, null=True)
```

**ChatAttachment** - Вложения (заготовлено для будущего)
```python
class ChatAttachment(TimeStampedModel):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE)
    file = models.FileField(upload_to='chat_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
```

### View функции

**Основные страницы:**
- `chat_room_list()` - Список комнат чата
- `chat_room()` - Конкретная комната чата

**AJAX функции:**
- `send_message()` - Отправка сообщения
- `edit_message()` - Редактирование сообщения
- `delete_message()` - Удаление сообщения
- `pin_message()` - Закрепление/открепление
- `get_new_messages()` - Получение новых сообщений
- `get_unread_count()` - Количество непрочитанных

**Администрирование:**
- `room_management()` - Управление комнатами
- `edit_room()` - Редактирование комнаты

### Права доступа

**Доступ к чату:**
- Администраторы (`admin`)
- Суперадминистраторы (`superadmin`) 
- Менторы (`mentor`)

**Действия с сообщениями:**
- **Отправка**: Все пользователи с доступом
- **Редактирование**: Только автор, в течение 1 часа
- **Удаление**: Автор (24 часа) + администраторы (всегда)
- **Закрепление**: Только администраторы и суперадминистраторы

## URL маршруты

```
/chat/                          # Список комнат
/chat/room/<int:room_id>/       # Комната чата
/chat/send/<int:room_id>/      # Отправка сообщения (POST)
/chat/edit/<int:message_id>/    # Редактирование (POST)
/chat/delete/<int:message_id>/  # Удаление (POST)
/chat/pin/<int:message_id>/     # Закрепление (POST)
/chat/new-messages/<int:room_id>/  # Новые сообщения (GET)
/chat/unread-count/             # Непрочитанные (GET)
/chat/management/               # Управление комнатами (админ)
/chat/management/edit/<int:room_id>/  # Редактирование комнаты (админ)
```

## Интерфейс

### Список комнат (`room_list.html`)
- Карточки комнат с описанием
- Статистика (количество комнат, сообщений, пользователей онлайн)
- Индикаторы непрочитанных сообщений
- Ссылка на управление комнатами для админов

### Комната чата (`room.html`)
- **Заголовок**: Название комнаты и описание
- **Сообщения**: 
  - Разные цвета для своих/чужих сообщений
  - Индикаторы закрепленных сообщений
  - Время отправки
  - Кнопки действий при наведении
- **Форма отправки**: Автоматическое изменение высоты
- **Модальное окно**: Редактирование сообщений

### Визуальные особенности
- **Свои сообщения**: Синий фон, выравнивание вправо
- **Чужие сообщения**: Белый фон, выравнивание влево  
- **Закрепленные**: Желтая полоса слева
- **Редактированные**: Индикатор "отредактировано в HH:MM"
- **Удаленные**: Полупрозрачность, текст "[Сообщение удалено]"

## JavaScript функционал

### Основные функции
- `sendMessage()` - Отправка сообщений
- `addMessageToChat()` - Добавление новых сообщений в DOM
- `checkNewMessages()` - Проверка обновлений каждые 5 секунд
- `startEdit()` / `saveEdit()` - Редактирование
- `deleteMessage()` - Удаление
- `pinMessage()` - Закрепление

### Особенности
- Автоматическая прокрутка вниз при новых сообщениях
- Автоматическое изменение высоты поля ввода
- Обработка ошибок и уведомления пользователя
- CSRF защита для всех POST запросов

## Безопасность

### Проверка прав доступа
```python
def can_access_chat(user):
    return user.role in ('admin', 'superadmin', 'mentor')
```

### Ограничения времени
- **Редактирование**: 1 час после создания
- **Удаление**: 24 часа для авторов, без ограничений для админов

### Валидация
- Максимальная длина сообщения: 2000 символов
- Обязательное поле содержания
- Проверка CSRF токена

## Установка и настройка

### 1. Добавление приложения
```python
# config/settings/base.py
LOCAL_APPS = [
    # ... другие приложения
    'apps.chat',
]
```

### 2. URL маршруты
```python
# config/urls.py
path('chat/', include('apps.chat.urls', namespace='chat')),
```

### 3. Миграции
```bash
python manage.py makemigrations chat
python manage.py migrate
```

### 4. Создание начальной комнаты
```python
from apps.chat.models import ChatRoom
room, created = ChatRoom.objects.get_or_create(
    name='Общий чат команды',
    defaults={'description': 'Основной чат для общения'}
)
```

## Использование

### Доступ к чату
1. Войти как администратор, суперадминистратор или ментор
2. Перейти по URL: `/chat/`
3. Выбрать комнату (сейчас одна "Общий чат команды")

### Базовые операции
1. **Отправка сообщения**: Ввести текст и нажать Enter или кнопку отправки
2. **Редактирование**: Навести на свое сообщение → нажать карандаш
3. **Удаление**: Навести → нажать корзину (подтверждение)
4. **Закрепление**: Админ может закрепить важные сообщения

### Для администраторов
- Управление комнатами: `/chat/management/`
- Создание новых комнат
- Редактирование названий и описаний
- Закрепление сообщений для важных объявлений

## Возможные улучшения

### В ближайшем будущем
- [ ] Вложения файлов и изображений
- [ ] Индикатор "печатает..."
- [ ] Поиск по сообщениям
- [ ] Emoji-picker
- [ ] Звуковые уведомления

### В долгосрочной перспективе
- [ ] WebSocket для реального времени
- [ ] Приватные комнаты
- [ ] Интеграция с уведомлениями
- [ ] Мобильное приложение
- [ ] Голосовые сообщения

## Технические детали

### Производительность
- Оптимизированные запросы с `select_related()`
- Индексы по полям `room` и `created_at`
- Ленивая загрузка вложений
- Кэширование статуса прочтения

### Масштабируемость
- Разделение на комнаты для разных тем
- Архивация старых сообщений
- Пагинация для больших объемов
- CDN для статических файлов

## Результат

Создан полнофункциональный чат с современным интерфейсом, который обеспечивает эффективное общение между администраторами, суперадминистраторами и менторами. Система безопасна, масштабируема и готова к дальнейшему развитию.
