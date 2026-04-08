#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

print("=== Исправление организаций для существующих пользователей ===")

from apps.accounts.models import CustomUser
from apps.students.models import Student
from apps.mentors.models import MentorProfile
from apps.organizations.models import Organization, OrganizationMember, UserCurrentOrganization

# 1. Исправляем менторов
print("\n1. Исправление менторов:")
mentors = MentorProfile.objects.all()
print(f"Всего менторов: {mentors.count()}")

for mentor in mentors:
    if mentor.organization:
        print(f"  - {mentor.get_display_name()}: организация {mentor.organization}")
        
        # Добавляем как участника если нет
        member, created = OrganizationMember.objects.get_or_create(
            user=mentor.user,
            organization=mentor.organization,
            defaults={'role': 'member'}
        )
        if created:
            print(f"    ✅ Добавлен в организацию")
        else:
            print(f"    ✓ Уже состоит в организации")
        
        # Устанавливаем текущую организацию
        user_current_org, created = UserCurrentOrganization.objects.get_or_create(
            user=mentor.user,
            defaults={'organization': mentor.organization}
        )
        if not created:
            user_current_org.organization = mentor.organization
            user_current_org.save()
    else:
        print(f"  - {mentor.get_display_name()}: ❌ Нет организации")

# 2. Исправляем студентов
print("\n2. Исправление студентов:")
students = Student.objects.all()
print(f"Всего студентов: {students.count()}")

for student in students:
    if student.organization:
        print(f"  - {student.full_name}: организация {student.organization}")
        
        # Добавляем как участника если нет
        if student.user:
            member, created = OrganizationMember.objects.get_or_create(
                user=student.user,
                organization=student.organization,
                defaults={'role': 'member'}
            )
            if created:
                print(f"    ✅ Добавлен в организацию")
            else:
                print(f"    ✓ Уже состоит в организации")
            
            # Устанавливаем текущую организацию
            user_current_org, created = UserCurrentOrganization.objects.get_or_create(
                user=student.user,
                defaults={'organization': student.organization}
            )
            if not created:
                user_current_org.organization = student.organization
                user_current_org.save()
    else:
        print(f"  - {student.full_name}: ❌ Нет организации")

print("\n=== Исправление завершено ===")
print("\nТеперь при создании менторов и студентов они автоматически:")
print("1. Становятся участниками организации админа")
print("2. Получают текущую организацию")
print("3. Их транзакции будут видны только в этой организации")
