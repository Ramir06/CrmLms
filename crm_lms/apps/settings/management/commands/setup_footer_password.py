from django.core.management.base import BaseCommand
from apps.settings.models import SystemSetting


class Command(BaseCommand):
    help = 'Set up footer password for accessing footer editor'

    def add_arguments(self, parser):
        parser.add_argument('password', type=str, help='Password for footer editor')

    def handle(self, *args, **options):
        password = options['password']
        
        # Create or update the footer password setting
        setting, created = SystemSetting.objects.update_or_create(
            key='footer_password',
            defaults={
                'value': password,
                'description': 'Пароль для доступа к редактору футера',
                'is_public': False
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Footer password created successfully: {password}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Footer password updated successfully: {password}')
            )
        
        self.stdout.write(
            self.style.WARNING('Remember this password to access the footer editor!')
        )
