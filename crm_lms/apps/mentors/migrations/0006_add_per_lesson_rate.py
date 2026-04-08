# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentors', '0005_mentorprofile_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentorprofile',
            name='per_lesson_rate',
            field=models.DecimalField(blank=True, default=0, decimal_places=2, help_text='Фиксированная оплата за одно проведенное занятие', max_digits=10, verbose_name='Ставка за занятие'),
        ),
        migrations.AlterField(
            model_name='mentorprofile',
            name='salary_type',
            field=models.CharField(choices=[('fixed', 'Фиксированная'), ('hourly', 'Почасовая'), ('percent', 'Процент'), ('mixed', 'Смешанная'), ('per_lesson', 'По занятиям')], default='fixed', max_length=10, verbose_name='Тип зарплаты'),
        ),
    ]
