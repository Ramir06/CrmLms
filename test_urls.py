import os
import sys
import django

# Устанавливаем путь к Django проекту
sys.path.append(r'c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms')
os.chdir(r'c:\Users\Admin\Desktop\CRM LMS — копия\crm_lms')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

# Инициализируем Django
django.setup()

from django.urls import reverse
from apps.courses import views_tariffs

try:
    # Проверяем что view доступен
    print("create_tariff view:", views_tariffs.create_tariff)
    
    # Проверяем URL reverse
    url = reverse('courses:create_tariff')
    print("URL for create_tariff:", url)
    
except Exception as e:
    print("Error:", e)
    import traceback
    traceback.print_exc()
