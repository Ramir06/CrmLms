#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.payments.models import Payment
from apps.finance.models import FinanceTransaction
from apps.salaries.models import SalaryAccrual

print("=== Проверка сигналов ===")

# Проверяем количество записей
payments_count = Payment.objects.count()
transactions_count = FinanceTransaction.objects.count()
salaries_count = SalaryAccrual.objects.count()

print(f'Платежей в системе: {payments_count}')
print(f'Транзакций в системе: {transactions_count}')
print(f'Начислений зарплат: {salaries_count}')

# Проверяем последние платежи и их транзакции
print("\n=== Последние платежи ===")
recent_payments = Payment.objects.all()[:5]
for p in recent_payments:
    print(f'Платеж {p.id}: студент={p.student.full_name if p.student else "None"}, сумма={p.amount}, paid_at={p.paid_at}')
    # Проверим есть ли транзакция для этого платежа
    tx = FinanceTransaction.objects.filter(related_entity_type='payment', related_entity_id=p.id).first()
    print(f'  -> Транзакция: {tx.amount if tx else "НЕТ"} ({tx.get_type_display() if tx else "Нет"})')

# Проверяем последние зарплаты и их транзакции
print("\n=== Последние зарплаты ===")
recent_salaries = SalaryAccrual.objects.all()[:5]
for s in recent_salaries:
    print(f'Зарплата {s.id}: ментор={s.mentor.get_full_name() if s.mentor else "None"}, сумма={s.amount}, статус={s.paid_status}')
    # Проверим есть ли транзакция для этой зарплаты
    tx = FinanceTransaction.objects.filter(related_entity_type='salary_accrual', related_entity_id=s.id).first()
    print(f'  -> Транзакция: {tx.amount if tx else "НЕТ"} ({tx.get_type_display() if tx else "Нет"})')

# Проверим автоматические транзакции
print("\n=== Автоматические транзакции ===")
auto_tx = FinanceTransaction.objects.filter(auto_generated=True)
print(f'Автоматических транзакций: {auto_tx.count()}')
for tx in auto_tx[:5]:
    print(f'  {tx.get_type_display()}: {tx.amount} - {tx.description[:50]}...')

print("\n=== Проверка завершена ===")
