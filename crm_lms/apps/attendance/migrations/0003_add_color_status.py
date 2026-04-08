# Generated migration to add color_status field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_attendancerecord_marked_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='color_status',
            field=models.CharField(blank=True, default='', max_length=20, verbose_name='Цветовой статус'),
        ),
    ]
