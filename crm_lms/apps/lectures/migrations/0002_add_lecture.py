# Generated migration for lectures app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = False

    dependencies = [
        ('courses', '0001_initial'),
        ('core', '0001_initial'),
        ('lectures', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lecture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lectures', to='courses.course', verbose_name='Курс')),
                ('section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='lectures', to='lectures.section', verbose_name='Раздел')),
                ('title', models.CharField(max_length=200, verbose_name='Название')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('lesson_date', models.DateField(verbose_name='Дата урока')),
                ('start_time', models.TimeField(blank=True, null=True, verbose_name='Время начала')),
                ('end_time', models.TimeField(blank=True, null=True, verbose_name='Время окончания')),
                ('status', models.CharField(choices=[('scheduled', 'Запланирован'), ('completed', 'Завершен'), ('cancelled', 'Отменен')], default='scheduled', max_length=20, verbose_name='Статус')),
                ('temporary_mentor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='temporary_lectures', to='accounts.customuser', verbose_name='Временный ментор')),
            ],
            options={
                'verbose_name': 'Урок',
                'verbose_name_plural': 'Уроки',
                'ordering': ['lesson_date', 'start_time'],
            },
        ),
    ]
