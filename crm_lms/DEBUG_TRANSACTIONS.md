# Инструкция по проверке автоматических транзакций

## Проблема
Транзакции должны создаваться автоматически при:
1. Создании платежа студента (с paid_at)
2. Создании/обновлении зарплаты со статусом "Выплачено"

## Как проверить прямо сейчас:

### 1. Запустите тестовый скрипт
```bash
cd c:\Users\Admin\Desktop\CRM LMS\crm_lms
python test_signals_direct.py
```

Этот скрипт создаст тестовый платеж и тестовую зарплату и проверит появились ли транзакции.

### 2. Если транзакции не создаются, проверьте:

#### А. Правильность работы сигналов
В консоли должны быть сообщения:
```
=== SIGNAL FIRED: Payment X, created=True, paid_at=2025-03-30 ===
=== CREATING PAYMENT TRANSACTION ===
Transaction created: Y - 5000.00
```

#### Б. Организации у пользователей
Убедитесь что у студентов и менторов есть организации:
```python
# В Django shell
from apps.students.models import Student
from apps.accounts.models import CustomUser

# Проверить организацию студента
student = Student.objects.first()
print(f"Студент: {student.full_name}, организация: {student.organization}")

# Проверить организацию ментора  
mentor = CustomUser.objects.filter(role='mentor').first()
print(f"Ментор: {mentor.get_full_name()}, организация: {mentor.organization}")
```

#### В. Существование категорий и счетов
```python
from apps.finance.models import FinanceCategory, FinanceAccount

# Проверить категории для организации
org = student.organization
categories = FinanceCategory.objects.filter(organization=org)
accounts = FinanceAccount.objects.filter(organization=org)

print(f"Категорий: {categories.count()}")
print(f"Счетов: {accounts.count()}")
```

### 3. Если ничего не работает - принудительное создание

Добавьте в views.py прямые вызовы после создания:

#### В payments/views.py после Payment.objects.create():
```python
# Принудительное создание транзакции
from apps.finance.signals import create_payment_transaction
try:
    create_payment_transaction(payment)
    print("✅ Транзакция создана принудительно")
except Exception as e:
    print(f"❌ Ошибка: {e}")
```

#### В salaries/views.py после SalaryAccrual.objects.create():
```python
# Принудительное создание транзакции если статус выплачен
if salary_accrual.paid_status == 'paid':
    from apps.finance.signals import create_salary_transaction
    try:
        create_salary_transaction(salary_accrual)
        print("✅ Транзакция зарплаты создана принудительно")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
```

### 4. Команда для исправления всех данных
```bash
python manage.py fix_finance_organization
```

## Ожидаемый результат:
1. При создании платежа → автоматическая транзакция дохода
2. При выплате зарплаты → автоматическая транзакция расхода  
3. В бухгалтерии видны все транзакции с пометкой "Авто: Да"
