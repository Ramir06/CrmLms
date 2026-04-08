# Система "Кодкойнов"

Полноценная система внутренней валюты для LMS/CRM проекта с ролевым доступом для администраторов, менторов и студентов.

## 🚀 Возможности

### Для администраторов:
- ✅ Управление всеми операциями с кодкойнами
- ✅ Открытие/закрытие вывода средств
- ✅ Обработка заявок на вывод
- ✅ Корректировка баланса студентов
- ✅ Управление шкалами начислений
- ✅ Просмотр полной истории транзакций

### Для менторов:
- ✅ Массовое начисление кодкойнов студентам курса
- ✅ Использование готовых шкал активности
- ✅ Создание пакетов начислений по урокам
- ✅ Просмотр истории начислений по курсу

### Для студентов:
- ✅ Просмотр текущего баланса кодкойнов
- ✅ Создание заявок на вывод средств
- ✅ Просмотр истории всех операций
- ✅ Просмотр истории выводов

## 📋 Установка и настройка

### 1. Активация приложения
Приложение уже добавлено в `INSTALLED_APPS` в `config/settings/base.py`.

### 2. Создание миграций
```bash
python manage.py makemigrations codecoins
python manage.py migrate
```

### 3. Инициализация системы
```bash
python manage.py init_codecoins
```

Эта команда создаст:
- Настройки вывода кодкойнов
- Базовые шкалы начислений

## 🎯 Основные модели

### CoinWallet - Кошелек студента
- `student` - студент (OneToOne)
- `balance` - текущий баланс

### CoinTransaction - Транзакция
- `wallet` - кошелек студента
- `amount` - сумма (положительная для доходов, отрицательная для расходов)
- `transaction_type` - тип операции
- `description` - описание
- `created_by` - кто создал
- `course` - курс (опционально)
- `mentor` - ментор (опционально)

### CoinWithdrawalRequest - Заявка на вывод
- `student` - студент
- `amount` - сумма
- `payout_method` - способ вывода
- `phone_number` - номер телефона
- `status` - статус (pending/approved/rejected)

### CoinScale - Шкала начисления
- `title` - название
- `value` - значение в кодкойнах
- `is_active` - активна ли
- `sort_order` - порядок отображения

### CoinBatch - Пакет начислений
- `course` - курс
- `mentor` - ментор
- `lesson_date` - дата урока
- `comment` - комментарий

## 🔧 Сервисы (CoinService)

### Основные методы:
```python
# Получение/создание кошелька
wallet, created = CoinService.get_or_create_wallet(student)

# Получение баланса
balance = CoinService.get_student_balance(student)

# Создание транзакции
transaction = CoinService.create_transaction(
    student=student,
    amount=Decimal('100'),
    transaction_type='income',
    description='Начисление за активность',
    created_by=request.user
)

# Корректировка баланса
transaction = CoinService.adjust_student_balance(
    student=student,
    amount=Decimal('50'),
    reason='Премиальные',
    created_by=request.user
)

# Создание заявки на вывод
request = CoinService.create_withdrawal_request(
    student=student,
    amount=Decimal('100'),
    payout_method='mbank',
    phone_number='0990123456'
)

# Подтверждение вывода
transaction = CoinService.approve_withdrawal_request(request, request.user)

# Отклонение вывода
transaction = CoinService.reject_withdrawal_request(
    request, request.user, 'Недостаточно документов'
)

# Управление выводом
CoinService.open_withdrawal(request.user)
CoinService.close_withdrawal(request.user, next_open_at)

# Работа с пакетами
batch = CoinService.create_coin_batch(course, mentor, date, comment)
CoinService.add_batch_item(batch, student, scale, description)
CoinService.apply_coin_batch(batch, mentor)
```

## 🌐 URL-маршруты

### Административный раздел:
- `/admin/codecoins/` - главная страница админки
- `/admin/codecoins/transactions/` - все операции
- `/admin/codecoins/withdrawal-requests/` - заявки на вывод
- `/admin/codecoins/scales/` - управление шкалами

### Раздел студента:
- `/lms/student/codecoins/` - дашборд студента
- `/lms/student/codecoins/transactions/` - история операций
- `/lms/student/codecoins/withdrawals/` - история выводов

### Раздел ментора:
- `/mentor/course/<int:course_id>/codecoins/` - кодкойны курса
- `/mentor/course/<int:course_id>/codecoins/create-batch/` - создание пакета
- `/mentor/course/<int:course_id>/codecoins/batch/<int:batch_id>/` - массовое начисление

## 🎨 Шаблоны

### Административные шаблоны:
- `codecoins/admin/base.html` - базовый шаблон админки
- `codecoins/admin/dashboard.html` - главная страница
- `codecoins/admin/transactions.html` - операции
- `codecoins/admin/withdrawal_requests.html` - заявки на вывод

### Шаблоны студента:
- `codecoins/student/base.html` - базовый шаблон студента
- `codecoins/student/dashboard.html` - дашборд студента

### Шаблоны ментора:
- `codecoins/mentor/base.html` - базовый шаблон ментора
- `codecoins/mentor/course_dashboard.html` - дашборд курса

## 🧪 Тесты

Запуск тестов:
```bash
python manage.py test apps.codecoins
```

Тесты покрывают:
- ✅ Создание и управление кошельками
- ✅ Транзакции (начисление, списание, отмена)
- ✅ Заявки на вывод (создание, подтверждение, отклонение)
- ✅ Шкалы начислений
- ✅ Пакетные начисления
- ✅ Права доступа и представления

## 📊 Типы операций

- `income` - Начисление
- `expense` - Списание
- `withdrawal_request` - Заявка на вывод
- `withdrawal_approved` - Вывод подтвержден
- `withdrawal_rejected` - Вывод отклонен
- `correction` - Корректировка
- `mentor_mass_accrual` - Массовое начисление ментором

## 🔄 Бизнес-логика

### Безопасность:
- ✅ Все операции в `transaction.atomic()`
- ✅ Проверка достаточности средств
- ✅ Защита от двойного списания
- ✅ Ролевые проверки доступа

### Финансовая целостность:
- ✅ Баланс хранится в кошельке
- ✅ Все операции логируются
- ✅ Отмена через компенсирующие транзакции
- ✅ История не удаляется физически

## 🎮 Использование

### Для администратора:
1. Зайдите в `/admin/codecoins/`
2. Настройте шкалы начислений
3. Откройте вывод средств при необходимости
4. Обрабатывайте заявки на вывод
5. Корректируйте балансы при необходимости

### Для ментора:
1. Перейдите в курс → "Кодкойны"
2. Создайте пакет начислений для урока
3. Отметьте студентов и шкалы активности
4. Примените начисления

### Для студента:
1. Зайдите в "Кодкойны" в личном кабинете
2. Просмотрите свой баланс и историю
3. При открытом выводе создайте заявку на вывод
4. Следите за статусом заявки

## 🚨 Важные моменты

- Минимальная сумма вывода: 100 кодкойнов
- Вывод можно открыть/закрыть только через админку
- Все финансовые операции атомарны
- История операций сохраняется навсегда
- Кошелек создается автоматически при регистрации студента

## 🔄 Интеграция с существующим кодом

Система использует существующие модели:
- `Student` из `apps.students.models`
- `CustomUser` из `apps.accounts.models`
- `Course` и `CourseStudent` из `apps.courses.models`

Сигналы автоматически создают кошелек при создании студента.

## 📝 Примеры кода

### Начисление кодкойнов за выполнение задания:
```python
from apps.codecoins.services import CoinService

def award_student(student, amount, reason):
    CoinService.create_transaction(
        student=student,
        amount=Decimal(amount),
        transaction_type='income',
        description=f'Выполнение задания: {reason}',
        created_by=request.user
    )
```

### Массовое начисление за урок:
```python
def award_lesson_participation(course, mentor, lesson_date):
    batch = CoinService.create_coin_batch(
        course=course,
        mentor=mentor,
        lesson_date=lesson_date,
        comment='Начисления за урок'
    )
    
    # Добавление студентов в пакет
    for enrollment in course.course_students.filter(status='active'):
        CoinService.add_batch_item(
            batch=batch,
            student=enrollment.student,
            scale=scale,  # Шкала активности
            description='Активность на уроке'
        )
    
    # Применение начислений
    CoinService.apply_coin_batch(batch, mentor)
```

---

**Система готова к использованию! 🎉**
