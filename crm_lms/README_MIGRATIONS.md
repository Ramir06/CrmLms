# Инструкция по применению миграций

## Проблемы
- `ОШИБКА: столбец mentors_mentorprofile.hourly_rate не существует`
- `ОШИБКА: столбец mentors_mentorprofile.two_factor_enabled не существует`

## Решение

### Шаг 1: Применить миграции через консоль
```bash
cd "c:\Users\Admin\Desktop\Новая папка (2)\crm_lms"
python manage.py migrate mentors
```

### Шаг 2: Если первый способ не сработал, применить через SQL
Выполните в PostgreSQL:
```sql
-- Обновляем тип зарплаты (добавляем 'hourly')
ALTER TABLE mentors_mentorprofile 
ALTER COLUMN salary_type TYPE VARCHAR(10) 
USING salary_type::VARCHAR(10);

-- Добавляем поле hourly_rate
ALTER TABLE mentors_mentorprofile 
ADD COLUMN hourly_rate DECIMAL(8, 2) DEFAULT 0.00;

-- Добавляем поля 2FA
ALTER TABLE mentors_mentorprofile 
ADD COLUMN two_factor_enabled BOOLEAN DEFAULT FALSE;

ALTER TABLE mentors_mentorprofile 
ADD COLUMN two_factor_code VARCHAR(6) DEFAULT '';

ALTER TABLE mentors_mentorprofile 
ADD COLUMN two_factor_code_expires TIMESTAMP NULL;
```

### Шаг 3: После применения миграций
1. Раскомментируйте поля в `apps/mentors/models.py`:
   - `hourly_rate`
   - `two_factor_enabled`
   - `two_factor_code`
   - `two_factor_code_expires`

2. Добавьте `hourly_rate` обратно в форму `apps/mentors/forms.py`

3. Уберите временные `getattr()` из методов

4. Восстановите нормальную работу 2FA views

## Временное решение (уже применено)
Код временно изменен для работы без новых полей:
- **hourly_rate:** используется значение по умолчанию 500
- **2FA поля:** закомментированы, методы возвращают заглушки
- **Формы:** убраны новые поля
- **Views:** показывают предупреждения о недоступности

## После миграций
Система будет поддерживать:
- **Фиксированную** оплату
- **Почасовую** оплату (часы × ставка)
- **Процентную** оплату (% от оплат)
- **Смешанную** оплату (фикс + %)
- **2FA аутентификацию** для менторов

## Проверка
После применения миграций проверьте:
1. Страница менторов открывается без ошибок
2. Можно выбрать тип оплаты "Почасовая"
3. Автоматический расчет зарплат работает
4. 2FA настройки доступны и работают
