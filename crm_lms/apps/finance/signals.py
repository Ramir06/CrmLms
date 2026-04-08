from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from apps.payments.models import Payment
from apps.salaries.models import SalaryAccrual
from apps.organizations.models import Organization
from .models import FinanceTransaction, FinanceCategory, FinanceAccount


@receiver(post_save, sender=Payment)
def create_transaction_on_payment(sender, instance, created, **kwargs):
    """
    Автоматически создает транзакцию при создании или обновлении платежа
    """
    print(f"=== SIGNAL FIRED: Payment {instance.id}, created={created}, paid_at={instance.paid_at} ===")
    
    # Платеж считается завершенным, если есть дата оплаты
    if instance.paid_at:
        print(f"Payment has paid_at: {instance.paid_at}")
        
        # Проверяем, существует ли уже транзакция для этого платежа
        existing_transaction = FinanceTransaction.objects.filter(
            related_entity_type='payment',
            related_entity_id=instance.id,
            auto_generated=True
        ).first()
        
        if existing_transaction:
            print(f"Updating existing transaction {existing_transaction.id}")
            # Обновляем существующую транзакцию только если сумма или дата изменились
            if existing_transaction.amount != instance.amount or existing_transaction.transaction_date != instance.paid_at:
                existing_transaction.amount = instance.amount
                existing_transaction.transaction_date = instance.paid_at
                existing_transaction.description = f"Оплата курса: {instance.course.title if instance.course else 'Без курса'} - {instance.student.full_name}"
                existing_transaction.save()
                print(f"Transaction updated")
            else:
                print(f"No changes needed")
        else:
            print(f"Creating new transaction for payment {instance.id}")
            # Создаем новую транзакцию
            create_payment_transaction(instance)
    else:
        print("Payment has no paid_at - skipping transaction creation")


@receiver(post_save, sender=SalaryAccrual)
def create_transaction_on_salary(sender, instance, created, **kwargs):
    """
    Автоматически создает транзакцию при создании или обновлении зарплаты
    """
    print(f"=== SIGNAL FIRED: SalaryAccrual {instance.id}, created={created}, paid_status={instance.paid_status} ===")
    
    if instance.paid_status == 'paid':
        print(f"Salary is paid - creating transaction")
        
        # Проверяем, существует ли уже транзакция для этой зарплаты
        existing_transaction = FinanceTransaction.objects.filter(
            related_entity_type='salary_accrual',
            related_entity_id=instance.id,
            auto_generated=True
        ).first()
        
        if existing_transaction:
            print(f"Updating existing transaction {existing_transaction.id}")
            # Обновляем существующую транзакцию только если сумма изменилась
            if existing_transaction.amount != instance.amount:
                existing_transaction.amount = instance.amount
                existing_transaction.description = f"Зарплата: {instance.mentor.get_display_name()}"
                existing_transaction.save()
                print(f"Transaction updated")
            else:
                print(f"No changes needed")
        else:
            print(f"Creating new transaction for salary {instance.id}")
            # Создаем новую транзакцию
            create_salary_transaction(instance)
    else:
        print(f"Salary is not paid (status={instance.paid_status}) - skipping transaction creation")


def create_payment_transaction(payment):
    """
    Создает транзакцию для платежа
    """
    try:
        print(f"=== CREATING PAYMENT TRANSACTION ===")
        print(f"Payment ID: {payment.id}")
        print(f"Student: {payment.student}")
        
        # Получаем организацию студента
        try:
            # У студента есть прямая связь с организацией через OrganizationMixin
            organization = payment.student.organization
            if not organization:
                print("❌ У студента нет организации!")
                # Пробуем найти организацию через membership
                from apps.organizations.models import OrganizationMember
                member = OrganizationMember.objects.filter(user=payment.student.user_account, is_active=True).first()
                if member:
                    organization = member.organization
                    print(f"✅ Найдена организация через membership: {organization}")
                else:
                    print("❌ Студент не состоит ни в одной организации!")
                    return None
            else:
                print(f"✅ Организация студента: {organization}")
        except AttributeError as e:
            print(f"❌ Ошибка получения организации студента: {e}")
            return None
        
        # Получаем или создаем категорию для оплат курсов
        category, _ = FinanceCategory.objects.get_or_create(
            name='Оплата курсов',
            type='income',
            organization=organization,
            defaults={
                'color': '#10b981'
            }
        )
        print(f"Category: {category.name}")
        
        # Получаем или создаем основной счёт
        account, _ = FinanceAccount.objects.get_or_create(
            name='Основной счёт',
            organization=organization,
            defaults={
                'balance': 0,
                'description': 'Основной счёт организации'
            }
        )
        print(f"Account: {account.name}")
        
        # Создаем транзакцию
        transaction = FinanceTransaction.objects.create(
            type='income',
            category=category,
            amount=payment.amount,
            account=account,
            description=f"Оплата курса: {payment.course.title if payment.course else 'Без курса'} - {payment.student.full_name}",
            transaction_date=payment.paid_at,
            auto_generated=True,
            related_entity_type='payment',
            related_entity_id=payment.id,
            organization=organization,
            branch=organization.name  # Устанавливаем филиал как название организации
        )
        
        print(f"Transaction created: {transaction.id} - {transaction.amount}")
        return transaction
        
    except Exception as e:
        # Логируем ошибку, но не прерываем процесс
        print(f"Error creating finance transaction for payment {payment.id}: {e}")
        return None


def create_salary_transaction(salary_accrual):
    """
    Создает транзакцию для зарплаты
    """
    try:
        print(f"=== CREATING SALARY TRANSACTION ===")
        print(f"Salary Accrual ID: {salary_accrual.id}")
        print(f"Mentor: {salary_accrual.mentor}")
        
        # Получаем организацию ментора
        try:
            # У ментора есть прямая связь с организацией через UserCurrentOrganization
            from apps.organizations.models import UserCurrentOrganization
            current_org = UserCurrentOrganization.objects.filter(user=salary_accrual.mentor).first()
            organization = current_org.organization if current_org else None
            
            if not organization:
                print("❌ У ментора нет текущей организации!")
                # Пробуем найти организацию через membership
                from apps.organizations.models import OrganizationMember
                member = OrganizationMember.objects.filter(user=salary_accrual.mentor, is_active=True).first()
                if member:
                    organization = member.organization
                    print(f"✅ Найдена организация через membership: {organization}")
                else:
                    print("❌ Ментор не состоит ни в одной организации!")
                    return None
            else:
                print(f"✅ Организация ментора: {organization}")
        except AttributeError as e:
            print(f"❌ Ошибка получения организации ментора: {e}")
            return None
        
        # Получаем или создаем категорию для зарплат
        category, _ = FinanceCategory.objects.get_or_create(
            name='Зарплаты',
            type='expense',
            organization=organization,
            defaults={
                'color': '#ef4444'
            }
        )
        
        # Получаем или создаем основной счёт
        account, _ = FinanceAccount.objects.get_or_create(
            name='Основной счёт',
            organization=organization,
            defaults={
                'balance': 0,
                'description': 'Основной счёт организации'
            }
        )
        
        # Создаем транзакцию
        transaction = FinanceTransaction.objects.create(
            type='expense',
            category=category,
            amount=salary_accrual.amount,
            account=account,
            description=f"Зарплата: {salary_accrual.mentor.get_display_name()} за {salary_accrual.month.strftime('%B %Y') if hasattr(salary_accrual.month, 'strftime') else str(salary_accrual.month)}",
            transaction_date=salary_accrual.month,
            auto_generated=True,
            related_entity_type='salary_accrual',
            related_entity_id=salary_accrual.id,
            organization=organization,
            branch=organization.name  # Устанавливаем филиал как название организации
        )
        
        print(f"✅ Transaction created successfully!")
        print(f"   ID: {transaction.id}")
        print(f"   Amount: {transaction.amount}")
        print(f"   Organization: {transaction.organization}")
        print(f"   Category: {transaction.category}")
        print(f"   Account: {transaction.account}")
        print(f"   Auto: {transaction.auto_generated}")
        
        # Проверим что транзакция действительно сохранилась
        try:
            check_tx = FinanceTransaction.objects.get(id=transaction.id)
            print(f"✅ Transaction verified in database: {check_tx.id}")
        except FinanceTransaction.DoesNotExist:
            print(f"❌ Transaction NOT found in database after save!")
        
        return transaction
        
    except Exception as e:
        # Логируем ошибку, но не прерываем процесс
        print(f"Error creating finance transaction for salary accrual {salary_accrual.id}: {e}")
        return None


def create_initial_categories_and_accounts(organization):
    """
    Создает начальные категории и счета для организации
    """
    # Создаем основные категории доходов
    income_categories = [
        {'name': 'Оплата курсов', 'color': '#10b981'},
        {'name': 'Консультации', 'color': '#22c55e'},
        {'name': 'Другие доходы', 'color': '#14b8a6'},
    ]
    
    for cat_data in income_categories:
        FinanceCategory.objects.get_or_create(
            name=cat_data['name'],
            type='income',
            organization=organization,
            defaults={
                'color': cat_data['color']
            }
        )
    
    # Создаем основные категории расходов
    expense_categories = [
        {'name': 'Зарплаты', 'color': '#ef4444'},
        {'name': 'Аренда', 'color': '#f97316'},
        {'name': 'Маркетинг', 'color': '#eab308'},
        {'name': 'Коммунальные услуги', 'color': '#f59e0b'},
        {'name': 'Программное обеспечение', 'color': '#8b5cf6'},
        {'name': 'Другие расходы', 'color': '#6b7280'},
    ]
    
    for cat_data in expense_categories:
        FinanceCategory.objects.get_or_create(
            name=cat_data['name'],
            type='expense',
            organization=organization,
            defaults={
                'color': cat_data['color']
            }
        )
    
    # Создаем основные счета
    accounts = [
        {'name': 'Основной счёт', 'description': 'Основной счёт организации'},
        {'name': 'Банковская карта', 'description': 'Корпоративная банковская карта'},
        {'name': 'Наличные', 'description': 'Наличные средства'},
    ]
    
    for acc_data in accounts:
        FinanceAccount.objects.get_or_create(
            name=acc_data['name'],
            organization=organization,
            defaults={
                'balance': 0,
                'description': acc_data['description']
            }
        )
