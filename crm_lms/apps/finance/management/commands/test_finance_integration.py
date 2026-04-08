from django.core.management.base import BaseCommand
from apps.accounts.models import CustomUser
from apps.courses.models import Course
from apps.students.models import Student
from apps.payments.models import Payment
from apps.salaries.models import SalaryAccrual
from apps.finance.models import FinanceTransaction, FinanceCategory, FinanceAccount
from apps.organizations.models import Organization, OrganizationMember


class Command(BaseCommand):
    help = 'Тестирует интеграцию финансовой системы'

    def handle(self, *args, **options):
        """Тестирует автоматическое создание финансовых транзакций"""
        self.stdout.write("=== Тестирование интеграции финансовой системы ===\n")
        
        # 1. Проверяем наличие организаций
        organizations = Organization.objects.all()
        self.stdout.write(f"1. Найдено организаций: {organizations.count()}")
        for org in organizations:
            self.stdout.write(f"   - {org.name}")
        
        if not organizations.exists():
            self.stdout.write("❌ Нет организаций для теста!")
            return
        
        org = organizations.first()
        
        # 2. Проверяем наличие студентов
        students = Student.objects.all()
        self.stdout.write(f"\n2. Найдено студентов: {students.count()}")
        
        if not students.exists():
            self.stdout.write("❌ Нет студентов для теста!")
            return
        
        student = students.first()
        self.stdout.write(f"   - Тестовый студент: {student.full_name}")
        
        # 3. Проверяем наличие курсов
        courses = Course.objects.all()
        self.stdout.write(f"\n3. Найдено курсов: {courses.count()}")
        
        if not courses.exists():
            self.stdout.write("❌ Нет курсов для теста!")
            return
        
        course = courses.first()
        self.stdout.write(f"   - Тестовый курс: {course.title}")
        
        # 4. Проверяем наличие менторов
        mentors = CustomUser.objects.filter(role='mentor')
        self.stdout.write(f"\n4. Найдено менторов: {mentors.count()}")
        
        if not mentors.exists():
            self.stdout.write("❌ Нет менторов для теста!")
            return
        
        mentor = mentors.first()
        self.stdout.write(f"   - Тестовый ментор: {mentor.get_display_name()}")
        
        # 5. Создаем тестовый платеж
        self.stdout.write(f"\n5. Создание тестового платежа...")
        existing_payments = Payment.objects.filter(student=student, course=course).count()
        self.stdout.write(f"   - Существующих платежей для этой пары: {existing_payments}")
        
        # Создаем платеж
        payment = Payment.objects.create(
            student=student,
            course=course,
            amount=10000.00,
            paid_at='2024-01-15',
            comment='Тестовый платеж для проверки интеграции'
        )
        self.stdout.write(f"   ✅ Создан платеж ID: {payment.id}")
        
        # Проверяем, создалась ли транзакция
        transaction = FinanceTransaction.objects.filter(
            related_entity_type='payment',
            related_entity_id=payment.id
        ).first()
        
        if transaction:
            self.stdout.write(f"   ✅ Автоматически создана транзакция ID: {transaction.id}")
            self.stdout.write(f"   - Тип: {transaction.get_type_display()}")
            self.stdout.write(f"   - Сумма: {transaction.amount}")
            self.stdout.write(f"   - Филиал: {transaction.branch}")
            self.stdout.write(f"   - Описание: {transaction.description}")
            self.stdout.write(f"   - Авто-генерация: {transaction.auto_generated}")
        else:
            self.stdout.write("   ❌ Транзакция не создана!")
        
        # 6. Создаем тестовое начисление зарплаты
        self.stdout.write(f"\n6. Создание тестового начисления зарплаты...")
        
        salary = SalaryAccrual.objects.create(
            mentor=mentor,
            course=course,
            month='2024-01-01',
            amount=15000.00,
            paid_status='paid',
            comment='Тестовая зарплата для проверки интеграции'
        )
        self.stdout.write(f"   ✅ Создано начисление зарплаты ID: {salary.id}")
        
        # Проверяем, создалась ли транзакция
        salary_transaction = FinanceTransaction.objects.filter(
            related_entity_type='salary_accrual',
            related_entity_id=salary.id
        ).first()
        
        if salary_transaction:
            self.stdout.write(f"   ✅ Автоматически создана транзакция ID: {salary_transaction.id}")
            self.stdout.write(f"   - Тип: {salary_transaction.get_type_display()}")
            self.stdout.write(f"   - Сумма: {salary_transaction.amount}")
            self.stdout.write(f"   - Филиал: {salary_transaction.branch}")
            self.stdout.write(f"   - Описание: {salary_transaction.description}")
            self.stdout.write(f"   - Авто-генерация: {salary_transaction.auto_generated}")
        else:
            self.stdout.write("   ❌ Транзакция не создана!")
        
        # 7. Общая статистика
        self.stdout.write(f"\n7. Общая статистика по транзакциям:")
        all_transactions = FinanceTransaction.objects.all()
        auto_transactions = FinanceTransaction.objects.filter(auto_generated=True)
        manual_transactions = FinanceTransaction.objects.filter(auto_generated=False)
        
        self.stdout.write(f"   - Всего транзакций: {all_transactions.count()}")
        self.stdout.write(f"   - Автоматических: {auto_transactions.count()}")
        self.stdout.write(f"   - Ручных: {manual_transactions.count()}")
        
        # 8. Статистика по категориям
        self.stdout.write(f"\n8. Категории транзакций:")
        categories = FinanceCategory.objects.all()
        for category in categories:
            count = FinanceTransaction.objects.filter(category=category).count()
            self.stdout.write(f"   - {category.name}: {count} транзакций")
        
        # 9. Статистика по счетам
        self.stdout.write(f"\n9. Счета:")
        accounts = FinanceAccount.objects.all()
        for account in accounts:
            count = FinanceTransaction.objects.filter(account=account).count()
            self.stdout.write(f"   - {account.name}: {count} транзакций")
        
        self.stdout.write(f"\n=== Тест завершен ===")
        self.stdout.write(f"Теперь вы можете проверить бухгалтерию по адресу: /admin/finance/")
        self.stdout.write(f"Платеж и зарплата должны отображаться как автоматические транзакции.")
