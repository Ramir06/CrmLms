# 📋 Инструкция по исправлению доступа к Django admin

## Проблема
Community Manager не может получить доступ к `/admin/courses/` потому что у него `is_staff=False`

## Решение 1: Через Django shell

1. **Откройте терминал** в папке проекта
2. **Запустите Django shell:**
   ```bash
   python manage.py shell
   ```

3. **Выполните команды:**
   ```python
   from apps.accounts.models import CustomUser
   
   # Найдите пользователя Community Manager
   cm_user = CustomUser.objects.filter(custom_role__name='Community Manager').first()
   
   if cm_user:
       print(f"Найден пользователь: {cm_user.username}")
       print(f"Текущий is_staff: {cm_user.is_staff}")
       
       # Установите is_staff=True
       cm_user.is_staff = True
       cm_user.save()
       
       print(f"✅ Обновлено is_staff: {cm_user.is_staff}")
   else:
       print("❌ Пользователь Community Manager не найден")
   
   # Проверьте всех пользователей с кастомными ролями
   users = CustomUser.objects.filter(custom_role__isnull=False)
   for user in users:
       print(f"{user.username} - {user.get_role_display()} - is_staff: {user.is_staff}")
   ```

## Решение 2: Через админ-панель

1. **Зайдите в админ-панель** под суперадминистратором
2. **Перейдите:** Accounts → Users
3. **Найдите Community Manager**
4. **Отредактируйте:** установите галочку "Сотрудник" (is_staff)
5. **Сохраните**

## Решение 3: Автоматически (когда код будет работать)

Теперь в методе `save()` модели CustomUser автоматически устанавливается `is_staff=True` для:
- Всех пользователей с кастомными ролями
- Пользователей с ролями admin и superadmin

## Результат

После установки `is_staff=True` Community Manager получит доступ к:
- Django admin панели (`/admin/`)
- Разделу курсов (`/admin/courses/`)
- Всем другим разделам Django admin

## Проверка

После исправления попробуйте зайти:
1. Под Community Manager
2. На URL: http://127.0.0.1:51482/admin/courses/

Доступ должен быть разрешен! 🎉
