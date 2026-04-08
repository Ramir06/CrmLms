# Generated migration for adding color field to Event

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendar_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='color',
            field=models.CharField(
                choices=[
                    ('#28a745', 'Зеленый'),
                    ('#dc3545', 'Красный'),
                    ('#007bff', 'Синий'),
                    ('#ffc107', 'Желтый'),
                    ('#6f42c1', 'Фиолетовый'),
                    ('#fd7e14', 'Оранжевый'),
                    ('#20c997', 'Бирюзовый'),
                    ('#e83e8c', 'Розовый'),
                    ('#6c757d', 'Серый'),
                    ('#343a40', 'Темный')
                ],
                default='#28a745',
                max_length=7,
                verbose_name='Цвет'
            ),
        ),
    ]
