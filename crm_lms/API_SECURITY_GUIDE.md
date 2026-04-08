# Django REST API Security Guide

## Защита REST API для CRM LMS

### 🚀 Реализованные меры безопасности

#### 1. Rate Limiting & Throttling
```python
# Настройки throttling
DEFAULT_THROTTLE_RATES = {
    'burst': '100/min',      # Burst: 100 запросов в минуту
    'sustained': '1000/hour', # Sustained: 1000 запросов в час
    'anon': '20/min',         # Анонимные: 20 в минуту
    'user': '1000/min',       # Аутентифицированные: 1000 в минуту
}
```

#### 2. Защита от DDoS
- IP-based rate limiting на уровне приложения
- Кэширование счетчиков запросов
- Автоматическая блокировка при превышении лимитов

#### 3. Валидация данных
- XSS защита
- SQL Injection защита  
- Валидация форматов (email, phone, URL)
- Ограничение длины полей
- Проверка опасных символов

#### 4. Exception Handling
- Скрытие внутренних ошибок 500
- Стандартизация формата ответов
- Логирование ошибок без утечки данных
- Request ID для отладки

#### 5. CORS Security
- Whitelist доменов
- Credentials только для доверенных источников
- Запрет wildcard origins

### 📦 Установка и настройка

#### 1. Установка зависимостей
```bash
pip install djangorestframework django-filter django-ratelimit drf-spectacular
```

#### 2. Миграции
```bash
python manage.py migrate
python manage.py drf_create_token <username>
```

#### 3. Настройка API ключей
```python
# settings.py
VALID_API_KEYS = [
    'your-production-api-key',
    'your-staging-api-key',
]
```

### 🔐 Примеры использования

#### Аутентификация через Token
```bash
# Получение токена
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Использование токена
curl -X GET http://localhost:8000/api/v1/users/ \
  -H "Authorization: Token your-token-here"
```

#### API Key аутентификация
```bash
curl -X GET http://localhost:8000/api/v1/secure/ \
  -H "X-API-Key: your-api-key-here"
```

### 🛡️ Безопасные эндпоинты

#### 1. `/api/v1/users/` - Управление пользователями
- **GET**: Список пользователей (с фильтрацией по организации)
- **POST**: Создание пользователя
- **PUT/PATCH**: Обновление пользователя
- **DELETE**: Удаление пользователя

#### 2. `/api/v1/profile/` - Профиль пользователя
- **GET**: Получение профиля (с кэшированием)
- **PUT**: Обновление профиля

#### 3. `/api/v1/public/` - Публичный API
- **GET**: Доступно без аутентификации
- **Rate Limit**: 20 запросов/час для анонимов

#### 4. `/api/v1/secure/` - Защищенные данные
- **GET**: Требует API Key
- **Высокий уровень доступа**

#### 5. `/api/v1/validate/` - Валидация данных
- **POST**: Проверка входных данных
- **Многоуровневая валидация**

### 📊 Rate Limiting стратегии

#### Для анонимных пользователей
- 20 запросов в минуту
- 50 запросов в час на публичных эндпоинтах
- IP-based блокировка

#### Для аутентифицированных пользователей
- 1000 запросов в минуту
- Без ограничений по часам
- User-based throttling

#### Для API ключей
- 10000 запросов в минуту
- Приоритетная обработка
- Мониторинг использования

### 🔍 Мониторинг и логирование

#### Логирование запросов
```python
# Формат лога
API Request: GET /api/v1/users/ by user_123 from 192.168.1.100
```

#### Мониторинг rate limits
- Кэшированные счетчики
- Redis/Memcached поддержка
- Автоматическая очистка

#### Exception логирование
- Без утечки чувствительных данных
- Request ID для трассировки
- Уровни логирования (INFO, WARNING, ERROR)

### 🚨 Обработка ошибок

#### Стандартный формат ответа об ошибке
```json
{
  "error": "Validation failed",
  "code": "validation_error",
  "details": {
    "email": ["Invalid email format"],
    "username": ["Username too short"]
  },
  "status": "error",
  "request_id": "req_123456789"
}
```

#### HTTP статусы
- `400`: Validation Error
- `401`: Authentication Error  
- `403`: Authorization Error
- `404`: Not Found
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error (без деталей)

### 🔧 Конфигурация безопасности

#### Production настройки
```python
# prod.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# CORS для production
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://api.yourdomain.com",
]

# Rate limiting для production
DEFAULT_THROTTLE_RATES = {
    'burst': '50/min',
    'sustained': '500/hour',
    'anon': '10/min',
    'user': '500/min',
}
```

### 📚 API Documentation

#### Swagger UI
- URL: `/api/v1/docs/`
- Интерактивная документация
- Тестирование эндпоинтов

#### ReDoc
- URL: `/api/v1/redoc/`
- Красивая документация
- Экспорт в PDF

#### OpenAPI Schema
- URL: `/api/v1/schema/`
- JSON схема
- Интеграция с клиентами

### ⚡ Оптимизация производительности

#### Кэширование
- Профили пользователей: 5 минут
- Счетчики rate limits: 1 минута
- Результаты валидации: 1 час

#### База данных
- select_related/prefetch_related
- Индексы для фильтров
- Оптимизированные запросы

#### Pagination
- PageNumberPagination
- Max page size: 100
- Metadata в ответах

### 🔄 Тестирование безопасности

#### Load Testing
```bash
# Использование artillery
artillery run load-test-api.yml
```

#### Security Testing
```bash
# SQL Injection тесты
curl -X POST http://localhost:8000/api/v1/validate/ \
  -d '{"email": "test'; DROP TABLE users; --"}'

# XSS тесты  
curl -X POST http://localhost:8000/api/v1/validate/ \
  -d '{"text": "<script>alert(1)</script>"}'
```

### 📝 Best Practices

#### 1. Всегда валидируйте входные данные
- Используйте SecureSerializer
- Проверяйте форматы и длину
- Фильтруйте опасные символы

#### 2. Используйте throttling
- Настраивайте лимиты по типу пользователей
- Мониторите превышения лимитов
- Логируйте подозрительную активность

#### 3. Скрывайте внутренние ошибки
- Используйте custom exception handler
- Не возвращайте stack traces
- Добавляйте request ID

#### 4. Правильно настраивайте CORS
- Используйте whitelist доменов
- Включайте credentials только для доверенных источников
- Избегайте wildcard origins

#### 5. Мониторьте API
- Логируйте все запросы
- Отслеживайте аномалии
- Настраивайте алерты

### 🚀 Следующие шаги

1. **Настроить production окружение**
2. **Добавить 2FA для API**
3. **Включить JWT аутентификацию**
4. **Настроить Web Application Firewall**
5. **Добавить API analytics**

---

**API Security Level: 🔒 HIGH**
**Compliance: OWASP API Security Top 10**
**Last Updated: 27 March 2026**
