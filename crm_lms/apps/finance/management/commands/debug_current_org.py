from django.core.management.base import BaseCommand
from apps.core.mixins_organization import get_current_organization
from apps.accounts.models import CustomUser
from apps.organizations.models import UserCurrentOrganization, StaffMember


class Command(BaseCommand):
    help = 'Отладка текущей организации пользователя'

    def handle(self, *args, **options):
        print("🔍 Отладка текущей организации пользователя...")
        
        # Получаем первого пользователя (предположим, что это вы)
        user = CustomUser.objects.filter(is_superuser=True).first()
        if not user:
            user = CustomUser.objects.first()
        
        if not user:
            print("❌ Пользователи не найдены")
            return
            
        print(f"👤 Пользователь: {user.get_display_name()} (ID: {user.id})")
        print(f"🔐 Суперадмин: {user.is_superuser}")
        
        # Проверяем UserCurrentOrganization
        try:
            current_org_relation = UserCurrentOrganization.objects.select_related('organization').get(user=user)
            print(f"📋 UserCurrentOrganization: {current_org_relation.organization.name} (ID: {current_org_relation.organization.id})")
        except UserCurrentOrganization.DoesNotExist:
            print("📋 UserCurrentOrganization: НЕ НАЙДЕНО")
        
        # Проверяем StaffMember
        try:
            staff_member = StaffMember.objects.select_related('organization').filter(
                user=user, 
                is_active=True
            ).first()
            if staff_member:
                print(f"👔 StaffMember: {staff_member.organization.name} (ID: {staff_member.organization.id})")
            else:
                print("👔 StaffMember: НЕ НАЙДЕН")
        except Exception as e:
            print(f"👔 StaffMember ошибка: {e}")
        
        # Вызываем get_current_organization
        current_org = get_current_organization(user)
        if current_org:
            print(f"✅ Текущая организация (get_current_organization): {current_org.name} (ID: {current_org.id})")
        else:
            print("❌ Текущая организация (get_current_organization): НЕ НАЙДЕНА")
        
        # Проверяем атрибут пользователя
        user_current_org = getattr(user, 'current_organization', None)
        if user_current_org:
            print(f"🏷️ Атрибут user.current_organization: {user_current_org}")
        else:
            print("🏷️ Атрибут user.current_organization: НЕ НАЙДЕН")
