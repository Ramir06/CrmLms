# Generated migration for block_after_deadline field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0003_assignmentgrade_ai_confidence_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignment',
            name='block_after_deadline',
            field=models.BooleanField(default=False),
        ),
    ]
