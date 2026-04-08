from django.db import transaction
from django.utils import timezone
from django.db.models import Sum
from .models import CourseStudent
from apps.courses.tickets import TicketBalance, TicketTransaction, TicketAttendance


class TicketService:
    """Сервис для работы с талонами"""
    
    @staticmethod
    def get_or_create_balance(enrollment):
        """Получить или создать баланс талонов"""
        balance, created = TicketBalance.objects.get_or_create(
            enrollment=enrollment,
            defaults={'total_tickets': 0, 'used_tickets': 0}
        )
        return balance
    
    @staticmethod
    def get_remaining_tickets(enrollment):
        """Получить количество оставшихся талонов"""
        balance = TicketService.get_or_create_balance(enrollment)
        return balance.remaining_tickets
    
    @staticmethod
    def get_student_ticket_summary(enrollment):
        """Получить сводку по талонам студента"""
        balance = TicketService.get_or_create_balance(enrollment)
        attendances = enrollment.ticket_attendances.all().order_by('-lesson_date')[:5]
        
        return {
            'remaining': balance.remaining_tickets,
            'total': balance.total_tickets,
            'used': balance.used_tickets,
            'recent_attendances': attendances
        }
    
    @staticmethod
    @transaction.atomic
    def consume_tickets(enrollment, lessons_count, marked_by=None, lesson_date=None, comment=''):
        """Списать талоны за посещение"""
        if lessons_count <= 0:
            raise ValueError("Количество уроков должно быть положительным")
        
        balance = TicketService.get_or_create_balance(enrollment)
        
        if balance.remaining_tickets < lessons_count:
            raise ValueError(f"Недостаточно талонов. Осталось: {balance.remaining_tickets}, требуется: {lessons_count}")
        
        # Пересчитываем used_tickets на основе всех посещений
        total_used = enrollment.ticket_attendances.aggregate(
            total_used=Sum('lessons_count')
        )['total_used'] or 0
        
        # Обновляем баланс - уменьшаем total_tickets и устанавливаем правильный used_tickets
        balance.total_tickets -= lessons_count
        balance.used_tickets = total_used + lessons_count
        balance.save()
        
        # Создаем транзакцию
        transaction_obj = TicketTransaction.objects.create(
            enrollment=enrollment,
            transaction_type='consume',
            quantity=lessons_count,
            comment=comment,
            created_by=marked_by
        )
        
        # Создаем запись о посещаемости
        attendance = TicketAttendance.objects.create(
            enrollment=enrollment,
            lesson_date=lesson_date or timezone.now().date(),
            lessons_count=lessons_count,
            marked_by=marked_by,
            comment=comment
        )
        
        return transaction_obj, attendance
    
    @staticmethod
    @transaction.atomic
    def add_tickets(enrollment, lessons_count, marked_by=None, comment=''):
        """Добавить талоны студенту"""
        if lessons_count <= 0:
            raise ValueError("Количество уроков должно быть положительным")
        
        balance = TicketService.get_or_create_balance(enrollment)
        
        # Обновляем баланс
        balance.total_tickets += lessons_count
        balance.save()
        
        # Создаем транзакцию
        transaction_obj = TicketTransaction.objects.create(
            enrollment=enrollment,
            transaction_type='add',
            quantity=lessons_count,
            comment=f"Добавление талонов. {comment}",
            created_by=marked_by
        )
        
        return transaction_obj
    
    @staticmethod
    @transaction.atomic
    def adjust_tickets(enrollment, new_total, created_by=None, comment=''):
        """Скорректировать общее количество талонов"""
        if new_total < 0:
            raise ValueError("Общее количество талонов не может быть отрицательным")
        
        balance = TicketService.get_or_create_balance(enrollment)
        old_total = balance.total_tickets
        difference = new_total - old_total
        
        if difference == 0:
            return None
        
        # Обновляем баланс
        balance.total_tickets = new_total
        # Если новое количество меньше использованных, корректируем used_tickets
        if new_total < balance.used_tickets:
            balance.used_tickets = new_total
        balance.save()
        
        # Создаем транзакцию корректировки
        transaction_obj = TicketTransaction.objects.create(
            enrollment=enrollment,
            transaction_type='adjust',
            quantity=difference,
            comment=f"Корректировка с {old_total} до {new_total}. {comment}",
            created_by=created_by
        )
        
        return transaction_obj
