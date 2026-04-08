#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== Проверка и исправление организаций пользователей ===")

from apps.accounts.models import CustomUser
from apps.organizations.models import Organization, OrganizationMember, UserCurrentOrganization
from apps.salaries.models import SalaryAccrual
from apps.finance.models import FinanceTransaction

# 1. Проверяем Айнур Сеткали
print("\n1. Поиск Айнур Сеткали:")
users = CustomUser.objects.filter(full_name__icontains='Айнур').filter(full_name__icontains='Сеткали')
print(f"Найдено пользователей: {users.count()}")

for user in users:
    print(f"  - {user.full_name} (username: {user.username}, role: {user.role})")
    
    # Проверяем текущую организацию
    try:
        current_org = user.current_organization.organization
        print(f"    Текущая организация: {current_org}")
    except AttributeError:
        print(f"    ❌ Нет текущей организации")
    
    # Проверяем membership
    memberships = OrganizationMember.objects.filter(user=user, is_active=True)
    print(f"    Членство в организациях: {memberships.count()}")
    for member in memberships:
        print(f"      - {member.organization} (роль: {member.role})")

# 2. Проверяем организацию Рамир
print("\n2. Организация Рамир:")
ramir_org = Organization.objects.filter(name__icontains='Рамир').first()
if ramir_org:
    print(f"  Найдена: {ramir_org.name}")
    print(f"  Участников: {ramir_org.members.filter(is_active=True).count()}")
    
    # Показываем участников
    for member in ramir_org.members.filter(is_active=True):
        print(f"    - {member.user.get_display_name()} ({member.role})")
else:
    print("  ❌ Организация Рамир не найдена")

# 3. Если Айнур найден и есть Рамир, добавляем в организацию
if users.exists() and ramir_org:
    user = users.first()
    
    # Проверяем есть ли уже в организации
    existing_member = OrganizationMember.objects.filter(user=user, organization=ramir_org).first()
    if not existing_member:
        print(f"\n3. Добавляем {user.get_display_name()} в организацию {ramir_org.name}")
        member = OrganizationMember.objects.create(
            user=user,
            organization=ramir_org,
            role='member'
        )
        print(f"  ✅ Добавлен как участник")
        
        # Устанавливаем как текущую организацию
        current_org, created = UserCurrentOrganization.objects.get_or_create(
            user=user,
            defaults={'organization': ramir_org}
        )
        if not created:
            current_org.organization = ramir_org
            current_org.save()
        print(f"  ✅ Установлена как текущая организация")
    else:
        print(f"\n3. {user.get_display_name()} уже состоит в организации {ramir_org.name}")

# 4. Проверяем последние зарплаты
print("\n4. Последние зарплаты:")
recent_salaries = SalaryAccrual.objects.all().order_by('-created')[:3]
for salary in recent_salaries:
    print(f"  - {salary.mentor.get_display_name()}: {salary.amount} ({salary.paid_status})")
    
    # Проверяем организацию ментора
    try:
        mentor_org = salary.mentor.current_organization.organization
        print(f"    Организация ментора: {mentor_org}")
    except AttributeError:
        print(f"    ❌ Нет организации у ментора")
    
    # Проверяем связанную транзакцию
    tx = FinanceTransaction.objects.filter(
        related_entity_type='salary_accrual',
        related_entity_id=salary.id
    ).first()
    
    if tx:
        print(f"    ✅ Транзакция: {tx.amount} в орг {tx.organization}")
    else:
        print(f"    ❌ Нет транзакции")

print("\n=== Проверка завершена ===")
