import os
import sys
import django

# Устанавливаем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Инициализируем Django
django.setup()

from apps.courses.models import CourseStudent, TicketTariff, TicketBalance, TicketTransaction
from apps.accounts.models import CustomUser

def test_add_tickets():
    """Тест добавления талонов"""
    try:
        # Находим студента
        cs = CourseStudent.objects.get(id=119)
        print(f"Студент: {cs.student.full_name}")
        print(f"Курс: {cs.course.title}")
        print(f"Курс бесконечный: {cs.course.is_unlimited}")
        
        # Находим тариф (создадим тестовый если нет)
        tariff, created = TicketTariff.objects.get_or_create(
            title="Тестовый тариф",
            defaults={
                'lessons_count': 5,
                'price_per_lesson': 10000,
                'is_active': True
            }
        )
        print(f"Тариф: {tariff.title} ({tariff.lessons_count} талонов)")
        
        # Проверяем баланс
        balance, created = TicketBalance.objects.get_or_create(
            enrollment=cs,
            defaults={
                'total_tickets': 0,
                'used_tickets': 0
            }
        )
        print(f"Баланс до: {balance.total_tickets} всего, {balance.used_tickets} использовано")
        
        # Добавляем транзакцию
        transaction = TicketTransaction.objects.create(
            enrollment=cs,
            transaction_type='add',
            quantity=tariff.lessons_count,
            price_per_ticket=tariff.price_per_lesson,
            comment=f'Добавлено по тарифу "{tariff.title}"',
            created_by=CustomUser.objects.first()
        )
        print(f"Транзакция создана: {transaction.id}")
        
        # Обновляем баланс
        balance.total_tickets += tariff.lessons_count
        balance.save()
        print(f"Баланс после: {balance.total_tickets} всего, {balance.used_tickets} использовано")
        print(f"Осталось талонов: {balance.remaining_tickets}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_add_tickets()
