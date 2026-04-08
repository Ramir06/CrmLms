from django.core.management.base import BaseCommand
from django.db import transaction
from apps.leads.models import LeadStatus, LeadSource


class Command(BaseCommand):
    help = 'Создает стандартные статусы и источники лидов'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Создаем стандартные статусы
            default_statuses = [
                {'name': 'Новый', 'slug': 'new', 'color': '#6c757d', 'order': 1, 'is_default': True},
                {'name': 'Консультация', 'slug': 'consultation', 'color': '#0dcaf0', 'order': 2},
                {'name': 'Пробный урок', 'slug': 'trial_lesson', 'color': '#0d6efd', 'order': 3},
                {'name': 'Не пришел', 'slug': 'no_show', 'color': '#ffc107', 'order': 4},
                {'name': 'Зачисление', 'slug': 'enrolling', 'color': '#198754', 'order': 5},
                {'name': 'Отказ', 'slug': 'rejected', 'color': '#dc3545', 'order': 6},
            ]
            
            for status_data in default_statuses:
                status, created = LeadStatus.objects.get_or_create(
                    slug=status_data['slug'],
                    defaults=status_data
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Создан статус: {status.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Статус уже существует: {status.name}')
                    )

            # Создаем стандартные источники
            default_sources = [
                {'name': 'Instagram', 'slug': 'instagram', 'order': 1, 'is_default': True},
                {'name': 'Telegram', 'slug': 'telegram', 'order': 2},
                {'name': 'Реферал', 'slug': 'referral', 'order': 3},
                {'name': 'Сайт', 'slug': 'website', 'order': 4},
                {'name': 'ВКонтакте', 'slug': 'vk', 'order': 5},
                {'name': 'Другое', 'slug': 'other', 'order': 6},
                {'name': 'Форма', 'slug': 'form', 'order': 7},
            ]
            
            for source_data in default_sources:
                source, created = LeadSource.objects.get_or_create(
                    slug=source_data['slug'],
                    defaults=source_data
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Создан источник: {source.name}')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'Источник уже существует: {source.name}')
                    )

            self.stdout.write(
                self.style.SUCCESS('Стандартные статусы и источники успешно созданы!')
            )
