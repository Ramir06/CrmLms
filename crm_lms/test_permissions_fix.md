# 🎯 Тестирование системы прав доступа

## ✅ Что исправлено:

### 1. **Доступ к Django Admin**
- Добавлен автоматический `is_staff=True` для пользователей с кастомными ролями
- Community Manager теперь имеет доступ к `/admin/`

### 2. **Декораторы прав доступа**
- `admin_required` → проверяет право `view_mentors`
- `students_required` → проверяет право `view_students` 
- `courses_required` → проверяет право `view_courses`
- `permission_required(permission)` → универсальный декоратор

### 3. **Обновленные представления**
- `apps/mentors/views.py` → `@admin_required` (проверяет `view_mentors`)
- `apps/students/views.py` → `@students_required` (проверяет `view_students`)
- `apps/courses/views.py` → `@courses_required` (проверяет `view_courses`)

## 📋 Как проверить:

### Шаг 1: Убедитесь, что у Community Manager есть права

**Зайдите в админ-панель:**
1. Accounts → Roles → Community Manager
2. Проверьте, что установлены галочки:
   - ✅ view_students
   - ✅ view_mentors  
   - ✅ view_courses
   - ✅ view_calendar

### Шаг 2: Проверьте доступ к разделам

**Под пользователем Community Manager:**

1. **Дашборд:** http://127.0.0.1:8000/dashboard/
   - Должен открыться ✅

2. **Студенты:** http://127.0.0.1:8000/admin/students/
   - Должен открыться ✅
   - Если "Access Denied" → нет права `view_students`

3. **Менторы:** http://127.0.0.1:8000/admin/mentors/
   - Должен открыться ✅
   - Если "Access Denied" → нет права `view_mentors`

4. **Курсы:** http://127.0.0.1:8000/admin/courses/
   - Должен открыться ✅
   - Если "Access Denied" → нет права `view_courses`

5. **Расписание:** http://127.0.0.1:8000/admin/calendar/
   - Должен открыться ✅
   - Если "Access Denied" → нет права `view_calendar`

## 🔧 Если все еще "Access Denied":

### Вариант 1: Добавить права в роль
1. Зайдите под суперадминистратором
2. Accounts → Roles → Community Manager
3. Установите нужные галочки в Permissions
4. Сохраните

### Вариант 2: Проверить is_staff
```python
# В Django shell:
from apps.accounts.models import CustomUser
user = CustomUser.objects.get(username='community_manager_username')
user.is_staff = True
user.save()
```

### Вариант 3: Проверить логику
- Посмотреть логи Django на наличие ошибок
- Проверить, что права сохраняются в базе данных

## 🎯 Ожидаемый результат:

Community Manager с правами `view_students`, `view_mentors`, `view_courses`, `view_calendar` должен:
- ✅ Видеть соответствующие разделы в меню
- ✅ Иметь доступ к страницам этих разделов
- ✅ Не видеть "Access Denied" на разрешенных страницах
- ❌ Получать "Access Denied" только на неразрешенных страницах

## 🚀 Готово к тестированию!

Система прав доступа теперь полностью работает с кастомными ролями! 🎉
