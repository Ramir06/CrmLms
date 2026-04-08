# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0003_merge_20260404_2108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendancerecord',
            name='color_status',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Цветовой статус'),
        ),
    ]
