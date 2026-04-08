from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.students.models import Student
from .models import CoinWallet


@receiver(post_save, sender=Student)
def create_coin_wallet(sender, instance, created, **kwargs):
    """Автоматическое создание кошелька при создании студента"""
    if created:
        CoinWallet.objects.get_or_create(
            student=instance,
            defaults={'balance': 0}
        )
