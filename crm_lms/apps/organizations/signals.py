from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Organization, UserCurrentOrganization


@receiver(post_save, sender=Organization)
def create_finance_data_for_organization(sender, instance, created, **kwargs):
    """Создает начальные финансовые данные для новой организации."""
    if created:
        from apps.finance.signals import create_initial_categories_and_accounts
        create_initial_categories_and_accounts(instance)


@receiver(post_save, sender=User)
def create_default_organization_for_superuser(sender, instance, created, **kwargs):
    """Создает организацию по умолчанию для суперадмина."""
    if created and instance.is_superuser:
        # Создаем организацию по умолчанию
        organization, created = Organization.objects.get_or_create(
            slug='default',
            defaults={
                'name': 'Организация по умолчанию',
                'description': 'Автоматически созданная организация для суперадминистратора',
                'is_active': True,
            }
        )
        
        # Добавляем суперадмина как владельца
        from .models import OrganizationMember
        OrganizationMember.objects.get_or_create(
            user=instance,
            organization=organization,
            defaults={'role': 'owner'}
        )
        
        # Устанавливаем как текущую организацию
        UserCurrentOrganization.objects.get_or_create(
            user=instance,
            defaults={'organization': organization}
        )
