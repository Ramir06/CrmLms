from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from apps.students.models import Student
from apps.courses.models import Course, CourseStudent
from apps.codecoins.models import CoinWallet, CoinTransaction, CoinScale, CoinBatch
from apps.codecoins.services import CoinService

User = get_user_model()


class CoinServiceTestCase(TestCase):
    """Тесты сервиса кодкойнов"""
    
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@example.com',
            role='student'
        )
        self.student = Student.objects.create(
            full_name='Test Student',
            phone='0990123456'
        )
        self.student.user_account = self.student_user
        self.student.save()
        
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin@example.com',
            role='admin'
        )
        
        self.mentor_user = User.objects.create_user(
            username='mentor1',
            email='mentor@example.com',
            role='mentor'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            mentor=self.mentor_user
        )
        
        CourseStudent.objects.create(
            course=self.course,
            student=self.student,
            status='active'
        )
    
    def test_get_or_create_wallet(self):
        """Тест создания кошелька"""
        wallet, created = CoinService.get_or_create_wallet(self.student)
        self.assertTrue(created)
        self.assertEqual(wallet.student, self.student)
        self.assertEqual(wallet.balance, 0)
        
        # Второй вызов не должен создавать новый кошелек
        wallet2, created2 = CoinService.get_or_create_wallet(self.student)
        self.assertFalse(created2)
        self.assertEqual(wallet.id, wallet2.id)
    
    def test_get_student_balance(self):
        """Тест получения баланса"""
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, 0)
        
        # Создаем транзакцию
        CoinService.create_transaction(
            student=self.student,
            amount=Decimal('100'),
            transaction_type='income',
            description='Test income',
            created_by=self.admin_user
        )
        
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('100'))
    
    def test_create_income_transaction(self):
        """Тест создания доходной транзакции"""
        transaction = CoinService.create_transaction(
            student=self.student,
            amount=Decimal('50'),
            transaction_type='income',
            description='Test income',
            created_by=self.admin_user
        )
        
        self.assertEqual(transaction.amount, Decimal('50'))
        self.assertEqual(transaction.transaction_type, 'income')
        self.assertEqual(transaction.wallet.student, self.student)
        
        # Проверяем баланс
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('50'))
    
    def test_create_expense_transaction(self):
        """Тест создания расходной транзакции"""
        # Сначала добавим средства
        CoinService.create_transaction(
            student=self.student,
            amount=Decimal('100'),
            transaction_type='income',
            description='Initial balance',
            created_by=self.admin_user
        )
        
        # Теперь списываем
        transaction = CoinService.create_transaction(
            student=self.student,
            amount=Decimal('-30'),
            transaction_type='expense',
            description='Test expense',
            created_by=self.admin_user
        )
        
        self.assertEqual(transaction.amount, Decimal('-30'))
        self.assertEqual(transaction.transaction_type, 'expense')
        
        # Проверяем баланс
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('70'))
    
    def test_insufficient_funds_error(self):
        """Тест ошибки недостаточных средств"""
        with self.assertRaises(Exception):
            CoinService.create_transaction(
                student=self.student,
                amount=Decimal('-50'),
                transaction_type='expense',
                description='Should fail',
                created_by=self.admin_user
            )
    
    def test_cancel_transaction(self):
        """Тест отмены транзакции"""
        # Создаем доходную транзакцию
        transaction = CoinService.create_transaction(
            student=self.student,
            amount=Decimal('100'),
            transaction_type='income',
            description='Test income',
            created_by=self.admin_user
        )
        
        # Отменяем транзакцию
        compensation = CoinService.cancel_transaction(
            transaction, self.admin_user, 'Test cancellation'
        )
        
        # Проверяем компенсационную транзакцию
        self.assertEqual(compensation.amount, Decimal('-100'))
        self.assertEqual(compensation.transaction_type, 'expense')
        
        # Проверяем, что оригинальная транзакция помечена как отмененная
        transaction.refresh_from_db()
        self.assertTrue(transaction.is_cancelled)
        
        # Проверяем баланс
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, 0)
    
    def test_adjust_student_balance(self):
        """Тест корректировки баланса"""
        # Положительная корректировка
        transaction = CoinService.adjust_student_balance(
            self.student, Decimal('25'), 'Test adjustment', self.admin_user
        )
        
        self.assertEqual(transaction.amount, Decimal('25'))
        self.assertEqual(transaction.transaction_type, 'correction')
        
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('25'))
        
        # Отрицательная корректировка
        transaction2 = CoinService.adjust_student_balance(
            self.student, Decimal('-10'), 'Test negative adjustment', self.admin_user
        )
        
        self.assertEqual(transaction2.amount, Decimal('-10'))
        
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('15'))


class CoinWithdrawalTestCase(TestCase):
    """Тесты вывода кодкойнов"""
    
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@example.com',
            role='student'
        )
        self.student = Student.objects.create(
            full_name='Test Student',
            phone='0990123456'
        )
        self.student.user_account = self.student_user
        self.student.save()
        
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin@example.com',
            role='admin'
        )
        
        # Добавляем баланс студенту
        CoinService.create_transaction(
            student=self.student,
            amount=Decimal('500'),
            transaction_type='income',
            description='Initial balance',
            created_by=self.admin_user
        )
    
    def test_create_withdrawal_request(self):
        """Тест создания заявки на вывод"""
        # Открываем вывод
        CoinService.open_withdrawal(self.admin_user)
        
        request = CoinService.create_withdrawal_request(
            student=self.student,
            amount=Decimal('100'),
            payout_method='mbank',
            phone_number='0990123456',
            comment='Test withdrawal'
        )
        
        self.assertEqual(request.student, self.student)
        self.assertEqual(request.amount, Decimal('100'))
        self.assertEqual(request.status, 'pending')
    
    def test_withdrawal_closed_error(self):
        """Тест ошибки при закрытом выводе"""
        with self.assertRaises(Exception):
            CoinService.create_withdrawal_request(
                student=self.student,
                amount=Decimal('100'),
                payout_method='mbank',
                phone_number='0990123456'
            )
    
    def test_insufficient_balance_error(self):
        """Тест ошибки недостаточного баланса"""
        # Открываем вывод
        CoinService.open_withdrawal(self.admin_user)
        
        with self.assertRaises(Exception):
            CoinService.create_withdrawal_request(
                student=self.student,
                amount=Decimal('1000'),  # Больше чем баланс
                payout_method='mbank',
                phone_number='0990123456'
            )
    
    def test_approve_withdrawal_request(self):
        """Тест подтверждения заявки на вывод"""
        # Открываем вывод
        CoinService.open_withdrawal(self.admin_user)
        
        request = CoinService.create_withdrawal_request(
            student=self.student,
            amount=Decimal('100'),
            payout_method='mbank',
            phone_number='0990123456'
        )
        
        # Подтверждаем заявку
        transaction = CoinService.approve_withdrawal_request(
            request, self.admin_user
        )
        
        self.assertEqual(transaction.amount, Decimal('-100'))
        self.assertEqual(transaction.transaction_type, 'withdrawal_approved')
        
        # Проверяем баланс
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('400'))
    
    def test_reject_withdrawal_request(self):
        """Тест отклонения заявки на вывод"""
        # Открываем вывод
        CoinService.open_withdrawal(self.admin_user)
        
        request = CoinService.create_withdrawal_request(
            student=self.student,
            amount=Decimal('100'),
            payout_method='mbank',
            phone_number='0990123456'
        )
        
        # Отклоняем заявку
        transaction = CoinService.reject_withdrawal_request(
            request, self.admin_user, 'Test rejection'
        )
        
        self.assertEqual(transaction.amount, 0)
        self.assertEqual(transaction.transaction_type, 'withdrawal_rejected')
        
        # Проверяем, что баланс не изменился
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('500'))


class CoinScaleTestCase(TestCase):
    """Тесты шкал кодкойнов"""
    
    def setUp(self):
        self.scale1 = CoinScale.objects.create(
            title='Хорошее поведение',
            value=Decimal('5'),
            is_active=True,
            sort_order=1
        )
        
        self.scale2 = CoinScale.objects.create(
            title='Плохое поведение',
            value=Decimal('-3'),
            is_active=True,
            sort_order=2
        )
        
        self.scale3 = CoinScale.objects.create(
            title='Неактивная шкала',
            value=Decimal('10'),
            is_active=False,
            sort_order=3
        )
    
    def test_get_active_scales(self):
        """Тест получения активных шкал"""
        active_scales = CoinService.get_active_scales()
        
        self.assertEqual(active_scales.count(), 2)
        self.assertIn(self.scale1, active_scales)
        self.assertIn(self.scale2, active_scales)
        self.assertNotIn(self.scale3, active_scales)
        
        # Проверяем сортировку
        self.assertEqual(active_scales[0], self.scale1)
        self.assertEqual(active_scales[1], self.scale2)


class CoinBatchTestCase(TestCase):
    """Тесты пакетных начислений"""
    
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@example.com',
            role='student'
        )
        self.student = Student.objects.create(
            full_name='Test Student',
            phone='0990123456'
        )
        self.student.user_account = self.student_user
        self.student.save()
        
        self.mentor_user = User.objects.create_user(
            username='mentor1',
            email='mentor@example.com',
            role='mentor'
        )
        
        self.course = Course.objects.create(
            title='Test Course',
            mentor=self.mentor_user
        )
        
        CourseStudent.objects.create(
            course=self.course,
            student=self.student,
            status='active'
        )
        
        self.scale = CoinScale.objects.create(
            title='Активность',
            value=Decimal('3'),
            is_active=True,
            sort_order=1
        )
    
    def test_create_coin_batch(self):
        """Тест создания пакета начислений"""
        batch = CoinService.create_coin_batch(
            course=self.course,
            mentor=self.mentor_user,
            lesson_date=timezone.now().date(),
            comment='Test batch'
        )
        
        self.assertEqual(batch.course, self.course)
        self.assertEqual(batch.mentor, self.mentor_user)
        self.assertEqual(batch.comment, 'Test batch')
    
    def test_apply_coin_batch(self):
        """Тест применения пакета начислений"""
        # Создаем пакет
        batch = CoinService.create_coin_batch(
            course=self.course,
            mentor=self.mentor_user,
            lesson_date=timezone.now().date()
        )
        
        # Добавляем элемент в пакет
        CoinService.add_batch_item(
            batch=batch,
            student=self.student,
            scale=self.scale,
            description='Test item'
        )
        
        # Применяем пакет
        applied_batch = CoinService.apply_coin_batch(batch, self.mentor_user)
        
        # Проверяем, что транзакция создана
        transaction = CoinTransaction.objects.get(
            wallet__student=self.student,
            batch=batch
        )
        
        self.assertEqual(transaction.amount, Decimal('3'))
        self.assertEqual(transaction.transaction_type, 'mentor_mass_accrual')
        
        # Проверяем баланс студента
        balance = CoinService.get_student_balance(self.student)
        self.assertEqual(balance, Decimal('3'))


class CoinViewTestCase(TestCase):
    """Тесты представлений"""
    
    def setUp(self):
        self.client = Client()
        
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin@example.com',
            role='admin'
        )
        self.admin_user.set_password('testpass123')
        self.admin_user.save()
        
        self.student_user = User.objects.create_user(
            username='student1',
            email='student@example.com',
            role='student'
        )
        self.student_user.set_password('testpass123')
        self.student_user.save()
        
        self.student = Student.objects.create(
            full_name='Test Student',
            phone='0990123456'
        )
        self.student.user_account = self.student_user
        self.student.save()
    
    def test_admin_dashboard_access(self):
        """Тест доступа к дашборду админа"""
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('codecoins:admin_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Кодкойны')
    
    def test_student_dashboard_access(self):
        """Тест доступа к дашборду студента"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('codecoins:student_dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'кодкойнов на балансе')
    
    def test_admin_access_denied_for_student(self):
        """Тест запрета доступа студента к админским функциям"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('codecoins:admin_dashboard'))
        
        self.assertEqual(response.status_code, 302)  # Redirect to login or access denied
    
    def test_student_access_denied_for_admin(self):
        """Тест запрета доступа админа к студенческим функциям"""
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('codecoins:student_dashboard'))
        
        self.assertEqual(response.status_code, 302)  # Redirect to login or access denied
