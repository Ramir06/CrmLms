import os
import sys
import django

# Устанавливаем путь к Django проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Инициализируем Django
django.setup()

from apps.courses.models import CourseStudent, TicketBalance, TicketTransaction
from apps.courses.services import TicketService

def test_ticket_consume():
    """Тест потребления талонов"""
    try:
        # Находим студента с балансом 24
        cs = CourseStudent.objects.get(id=119)
        print(f"Студент: {cs.student.full_name}")
        print(f"Курс: {cs.course.title}")
        
        # Получаем баланс до
        balance = TicketService.get_or_create_balance(cs)
        print(f"Баланс до: {balance.total_tickets} всего, {balance.used_tickets} использовано")
        print(f"Осталось: {balance.remaining_tickets}")
        
        # Потребляем 1 талон
        print("\nПотребляем 1 талон...")
        transaction, attendance = TicketService.consume_tickets(
            enrollment=cs,
            lessons_count=1,
            lesson_date=timezone.now().date(),
            comment="Тестовое посещение"
        )
        
        # Получаем баланс после
        balance_after = TicketService.get_or_create_balance(cs)
        print(f"Баланс после: {balance_after.total_tickets} всего, {balance_after.used_tickets} использовано")
        print(f"Осталось: {balance_after.remaining_tickets}")
        
        # Проверяем что изменилось
        if balance_after.total_tickets == balance.total_tickets - 1:
            print("✅ total_tickets уменьшился на 1")
        else:
            print(f"❌ total_tickets не изменился: {balance.total_tickets} -> {balance_after.total_tickets}")
            
        if balance_after.used_tickets == balance.used_tickets + 1:
            print("✅ used_tickets увеличился на 1")
        else:
            print(f"❌ used_tickets не изменился: {balance.used_tickets} -> {balance_after.used_tickets}")
        
        if balance_after.remaining_tickets == balance.remaining_tickets - 1:
            print("✅ remaining_tickets уменьшился на 1")
        else:
            print(f"❌ remaining_tickets не изменился: {balance.remaining_tickets} -> {balance_after.remaining_tickets}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    from django.utils import timezone
    test_ticket_consume()
