# Generated migration for Event model

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organizations', '0003_alter_organizationmember_options_and_more'),
        ('accounts', '0010_role_customuser_custom_role'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Название')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('date', models.DateField(verbose_name='Дата')),
                ('start_time', models.TimeField(verbose_name='Начало')),
                ('end_time', models.TimeField(verbose_name='Конец')),
                ('target_type', models.CharField(choices=[('mentor', 'Ментор'), ('student', 'Студент'), ('admin', 'Администратор'), ('organization', 'Общая организация'), ('custom', 'Кому либо')], max_length=20, verbose_name='Для кого')),
                ('target_user', models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='events', to='accounts.customuser', verbose_name='Конкретный пользователь')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Создано')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Обновлено')),
                ('created_by', models.ForeignKey(on_delete=models.CASCADE, related_name='created_events', to='accounts.customuser', verbose_name='Кто создал')),
                ('organization', models.ForeignKey(on_delete=models.CASCADE, to='organizations.organization', verbose_name='Организация')),
            ],
            options={
                'verbose_name': 'Мероприятие',
                'verbose_name_plural': 'Мероприятия',
                'ordering': ['date', 'start_time'],
            },
        ),
    ]
