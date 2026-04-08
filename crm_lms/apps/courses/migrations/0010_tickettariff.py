# Generated manually

from django.db import migrations, models
import django.db.models.deletion
import apps.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0001_initial'),
        ('core', '0001_initial'),
        ('courses', '0009_course_hourly_rate_course_salary_percentage_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketTariff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Название тарифа')),
                ('lessons_count', models.PositiveIntegerField(verbose_name='Количество занятий')),
                ('price_per_lesson', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена за занятие')),
                ('total_price', models.DecimalField(decimal_places=2, editable=False, max_digits=12, verbose_name='Общая стоимость')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создан')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлен')),
                ('organization', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='organizations.organization', verbose_name='Организация')),
            ],
            options={
                'verbose_name': 'Тариф талонов',
                'verbose_name_plural': 'Тарифы талонов',
                'ordering': ['lessons_count'],
            },
        ),
    ]
