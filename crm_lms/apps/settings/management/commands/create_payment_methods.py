from django.core.management.base import BaseCommand
from apps.settings.models import PaymentMethod

class Command(BaseCommand):
    help = 'Создание начальных способов оплаты'

    def handle(self, *args, **options):
        payment_methods = [
            {'name': 'Наличные', 'description': 'Оплата наличными', 'sort_order': 1},
            {'name': 'Карта', 'description': 'Оплата банковской картой', 'sort_order': 2},
            {'name': 'Mbank', 'description': 'Перевод через Mbank', 'sort_order': 3},
            {'name': 'Перевод', 'description': 'Банковский перевод', 'sort_order': 4},
            {'name': 'PayPal', 'description': 'Оплата через PayPal', 'sort_order': 5},
        ]

        created_count = 0
        for method_data in payment_methods:
            method, created = PaymentMethod.objects.get_or_create(
                name=method_data['name'],
                defaults=method_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Создан способ оплаты: {method.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Способ оплаты уже существует: {method.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Завершено. Создано: {created_count} способов оплаты')
        )
