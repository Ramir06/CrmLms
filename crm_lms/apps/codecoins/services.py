from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import (
    CoinWallet, CoinTransaction, CoinWithdrawalSetting, 
    CoinWithdrawalRequest, CoinScale, CoinBatch, CoinBatchItem
)


class CoinService:
    """Сервис для работы с кодкойнами"""
    
    @staticmethod
    def get_or_create_wallet(student):
        """Получить или создать кошелек студента"""
        wallet, created = CoinWallet.objects.get_or_create(
            student=student,
            defaults={'balance': 0}
        )
        return wallet, created
    
    @staticmethod
    def get_student_balance(student):
        """Получить баланс студента"""
        wallet, _ = CoinService.get_or_create_wallet(student)
        return wallet.balance
    
    @staticmethod
    @transaction.atomic
    def create_transaction(
        student, amount, transaction_type, description,
        created_by=None, course=None, mentor=None,
        withdrawal_request=None, batch=None
    ):
        """Создать транзакцию и обновить баланс"""
        if amount == 0:
            raise ValueError("Сумма не может быть нулевой")
        
        wallet, _ = CoinService.get_or_create_wallet(student)
        
        # Проверяем достаточность средств для расходных операций
        if amount < 0 and abs(amount) > wallet.balance:
            if transaction_type not in ['correction']:
                raise ValidationError(f"Недостаточно кодкойнов. Баланс: {wallet.balance}, требуется: {abs(amount)}")
        
        # Обновляем баланс
        wallet.balance += amount
        wallet.save()
        
        # Создаем транзакцию
        transaction_obj = CoinTransaction.objects.create(
            wallet=wallet,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            created_by=created_by,
            course=course,
            mentor=mentor,
            withdrawal_request=withdrawal_request,
            batch=batch
        )
        
        return transaction_obj
    
    @staticmethod
    @transaction.atomic
    def cancel_transaction(transaction, cancelled_by, reason=''):
        """Отменить транзакцию"""
        if transaction.is_cancelled:
            raise ValidationError("Транзакция уже отменена")
        
        # Создаем компенсирующую транзакцию
        compensation_amount = -transaction.amount
        compensation_type = 'correction'
        
        if transaction.amount > 0:
            compensation_type = 'expense'
            description = f'Отмена начисления #{transaction.id}. {reason}'
        else:
            compensation_type = 'income'
            description = f'Отмена списания #{transaction.id}. {reason}'
        
        # Создаем компенсирующую транзакцию
        compensation = CoinService.create_transaction(
            student=transaction.wallet.student,
            amount=compensation_amount,
            transaction_type=compensation_type,
            description=description,
            created_by=cancelled_by,
            course=transaction.course,
            mentor=transaction.mentor
        )
        
        # Помечаем оригинальную транзакцию как отмененную
        transaction.is_cancelled = True
        transaction.cancelled_at = timezone.now()
        transaction.cancelled_by = cancelled_by
        transaction.save()
        
        return compensation
    
    @staticmethod
    def get_withdrawal_setting():
        """Получить настройки вывода"""
        setting, _ = CoinWithdrawalSetting.objects.get_or_create(
            id=1,
            defaults={'is_open': False}
        )
        return setting
    
    @staticmethod
    @transaction.atomic
    def open_withdrawal(updated_by):
        """Открыть вывод кодкойнов"""
        setting = CoinService.get_withdrawal_setting()
        setting.is_open = True
        setting.next_open_at = None
        setting.updated_by = updated_by
        setting.save()
        return setting
    
    @staticmethod
    @transaction.atomic
    def close_withdrawal(updated_by, next_open_at=None):
        """Закрыть вывод кодкойнов"""
        setting = CoinService.get_withdrawal_setting()
        setting.is_open = False
        setting.next_open_at = next_open_at
        setting.updated_by = updated_by
        setting.save()
        return setting
    
    @staticmethod
    @transaction.atomic
    def create_withdrawal_request(student, amount, payout_method, phone_number, comment=''):
        """Создать заявку на вывод"""
        # Проверяем открыт ли вывод
        setting = CoinService.get_withdrawal_setting()
        if not setting.is_open:
            raise ValidationError("Вывод кодкойнов закрыт")
        
        # Проверяем баланс
        balance = CoinService.get_student_balance(student)
        if amount > balance:
            raise ValidationError(f"Недостаточно кодкойнов. Баланс: {balance}, запрошено: {amount}")
        
        # Проверяем минимальную сумму (можно вынести в настройки)
        if amount < 100:
            raise ValidationError("Минимальная сумма вывода: 100 кодкойнов")
        
        # Создаем заявку
        request_obj = CoinWithdrawalRequest.objects.create(
            student=student,
            amount=amount,
            payout_method=payout_method,
            phone_number=phone_number,
            comment=comment
        )
        
        return request_obj
    
    @staticmethod
    @transaction.atomic
    def approve_withdrawal_request(request, reviewed_by):
        """Подтвердить заявку на вывод"""
        if request.status != 'pending':
            raise ValidationError("Заявка уже обработана")
        
        # Списываем кодкойны
        transaction_obj = CoinService.create_transaction(
            student=request.student,
            amount=-request.amount,
            transaction_type='withdrawal_approved',
            description=f'Вывод средств: {request.payout_method} {request.phone_number}',
            created_by=reviewed_by,
            withdrawal_request=request
        )
        
        # Обновляем статус заявки
        request.status = 'approved'
        request.reviewed_by = reviewed_by
        request.reviewed_at = timezone.now()
        request.save()
        
        return transaction_obj
    
    @staticmethod
    @transaction.atomic
    def reject_withdrawal_request(request, reviewed_by, rejection_reason=''):
        """Отклонить заявку на вывод"""
        if request.status != 'pending':
            raise ValidationError("Заявка уже обработана")
        
        # Обновляем статус заявки
        request.status = 'rejected'
        request.reviewed_by = reviewed_by
        request.reviewed_at = timezone.now()
        request.rejection_reason = rejection_reason
        request.save()
        
        # Создаем транзакцию отклонения (без списания средств)
        transaction_obj = CoinService.create_transaction(
            student=request.student,
            amount=0,
            transaction_type='withdrawal_rejected',
            description=f'Отклонение вывода: {rejection_reason}',
            created_by=reviewed_by,
            withdrawal_request=request
        )
        
        return transaction_obj
    
    @staticmethod
    @transaction.atomic
    def adjust_student_balance(student, amount, reason, created_by):
        """Корректировка баланса студента"""
        if amount == 0:
            raise ValueError("Сумма корректировки не может быть нулевой")
        
        transaction_type = 'correction'
        description = f'Корректировка баланса: {reason}'
        
        return CoinService.create_transaction(
            student=student,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            created_by=created_by
        )
    
    @staticmethod
    def get_active_scales():
        """Получить активные шкалы"""
        return CoinScale.objects.filter(is_active=True).order_by('sort_order')
    
    @staticmethod
    @transaction.atomic
    def create_coin_batch(course, mentor, lesson_date, comment=''):
        """Создать пакет начислений"""
        return CoinBatch.objects.create(
            course=course,
            mentor=mentor,
            lesson_date=lesson_date,
            comment=comment
        )
    
    @staticmethod
    @transaction.atomic
    def add_batch_item(batch, student, scale, description=''):
        """Добавить элемент в пакет начислений"""
        # Проверяем на дубликаты
        if CoinBatchItem.objects.filter(
            batch=batch, student=student, scale=scale
        ).exists():
            raise ValidationError("Такое начисление уже существует в пакете")
        
        return CoinBatchItem.objects.create(
            batch=batch,
            student=student,
            scale=scale,
            amount=scale.value,
            description=description or scale.title
        )
    
    @staticmethod
    @transaction.atomic
    def apply_coin_batch(batch, applied_by):
        """Применить пакет начислений"""
        if batch.items.exists():
            for item in batch.items.all():
                CoinService.create_transaction(
                    student=item.student,
                    amount=item.amount,
                    transaction_type='mentor_mass_accrual',
                    description=f'{item.description} (урок {batch.lesson_date})',
                    created_by=applied_by,
                    course=batch.course,
                    mentor=batch.mentor,
                    batch=batch
                )
        return batch
    
    @staticmethod
    def get_student_transaction_history(student, limit=50):
        """Получить историю транзакций студента"""
        wallet, _ = CoinService.get_or_create_wallet(student)
        return wallet.transactions.filter(
            is_cancelled=False
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_all_transactions(limit=100):
        """Получить все транзакции"""
        return CoinTransaction.objects.filter(
            is_cancelled=False
        ).select_related(
            'wallet__student', 'created_by', 'course', 'mentor'
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def get_pending_withdrawal_requests():
        """Получить заявки на вывод в ожидании"""
        return CoinWithdrawalRequest.objects.filter(
            status='pending'
        ).select_related('student').order_by('-created_at')
    
    @staticmethod
    def get_student_withdrawal_history(student):
        """Получить историю выводов студента"""
        return student.coin_withdrawal_requests.all().order_by('-created_at')
