# Generated manually to populate avatar_seed and add uniqueness

from django.db import migrations, models
import uuid


def populate_avatar_seeds(apps, schema_editor):
    """Заполняем avatar_seed для существующих пользователей"""
    CustomUser = apps.get_model('accounts', 'CustomUser')
    
    for user in CustomUser.objects.filter(avatar_seed=''):
        # Генерируем уникальный seed
        seed = f"user_{user.id}_{uuid.uuid4().hex[:12]}"
        user.avatar_seed = seed
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_customuser_avatar_seed'),
    ]

    operations = [
        # Сначала заполняем пустые значения
        migrations.RunPython(populate_avatar_seeds, migrations.RunPython.noop),
        
        # Затем добавляем уникальность
        migrations.AlterField(
            model_name='customuser',
            name='avatar_seed',
            field=models.CharField(max_length=100, unique=True, verbose_name='Seed для аватара'),
        ),
    ]
