# Инструкции по исправлению ошибок в базе данных

## Проблема
1. **Ошибка color_status**: Поле `color_status` в таблице `attendance_attendancerecord` имеет ограничение NOT NULL, но в модели разрешены NULL значения
2. **Ошибка per_lesson_rate**: Поле `per_lesson_rate` отсутствует в таблице `mentors_mentorprofile`

## Решение

### Вариант 1: Через SQL (рекомендуется)

1. Подключитесь к вашей базе данных PostgreSQL
2. Выполните SQL скрипты:

```sql
-- Сначала исправляем color_status
\i fix_color_status.sql

-- Затем добавляем per_lesson_rate
\i add_per_lesson_rate.sql
```

### Вариант 2: Через Django migrate

Если получится настроить Django, то:

1. Примените миграции поочередно:
   ```bash
   python manage.py migrate attendance
   python manage.py migrate mentors
   ```

## Что делают скрипты

### fix_color_status.sql
- Убирает ограничение NOT NULL с поля `color_status`
- Обновляет все NULL значения на пустые строки
- Устанавливает значение по умолчанию ''
- Возвращает ограничение NOT NULL

### add_per_lesson_rate.sql
- Добавляет поле `per_lesson_rate` в таблицу `mentors_mentorprofile`
- Тип: DECIMAL(10, 2)
- Значение по умолчанию: 0.00
- NOT NULL ограничение

## После исправления

После применения скриптов все ошибки должны быть исправлены:
- ✅ Ошибка с color_status в attendance_attendancerecord
- ✅ Ошибка с отсутствующим полем per_lesson_rate
- ✅ Ошибка с должниками (бесконечные курсы исключены)
- ✅ Ошибка с отчётами (данные теперь корректно рассчитываются)
- ✅ Ошибка 404 в calendar event drawer (улучшена обработка)

## Проверка

1. Перезапустите Django сервер
2. Проверьте страницу /admin/mentors/ - должна работать без ошибок
3. Проверьте страницу /admin/salaries/auto-create/ - должна работать
4. Проверьте страницу /admin/debts/ - должны отображаться только актуальные долги
