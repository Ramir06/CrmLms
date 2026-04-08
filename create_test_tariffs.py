import os
import sys
import django

# Устанавливаем путь к Django проекту
sys.path.append(r'c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Инициализируем Django
django.setup()

from apps.courses.models import TicketTariff

def create_test_tariffs():
    """Создание тестовых тарифов"""
    
    tariffs_data = [
        {
            'title': 'Пробный - 1 занятие',
            'lessons_count': 1,
            'price_per_lesson': 500,
            'description': 'Пробное занятие для новых студентов'
        },
        {
            'title': 'Мини - 4 занятия',
            'lessons_count': 4,
            'price_per_lesson': 450,
            'description': 'Небольшой пакет для начала обучения'
        },
        {
            'title': 'Стандарт - 8 занятий',
            'lessons_count': 8,
            'price_per_lesson': 400,
            'description': 'Стандартный пакет на месяц'
        },
        {
            'title': 'Оптимальный - 12 занятий',
            'lessons_count': 12,
            'price_per_lesson': 380,
            'description': 'Выгодный пакет на 1.5 месяца'
        },
        {
            'title': 'Максимальный - 16 занятий',
            'lessons_count': 16,
            'price_per_lesson': 350,
            'description': 'Самый выгодный пакет на 2 месяца'
        }
    ]
    
    print("Создание тестовых тарифов...")
    
    for tariff_data in tariffs_data:
        tariff, created = TicketTariff.objects.get_or_create(
            title=tariff_data['title'],
            defaults={
                'lessons_count': tariff_data['lessons_count'],
                'price_per_lesson': tariff_data['price_per_lesson'],
                'description': tariff_data['description'],
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Создан тариф: {tariff.title} - {tariff.lessons_count} зан. ({tariff.total_price} сом)")
        else:
            print(f"⚠️ Тариф уже существует: {tariff.title}")
    
    print(f"\nВсего тарифов в системе: {TicketTariff.objects.filter(is_active=True).count()}")

if __name__ == '__main__':
    try:
        create_test_tariffs()
        print("\n✅ Тестовые тарифы успешно созданы!")
    except Exception as e:
        print(f"❌ Ошибка при создании тарифов: {e}")
