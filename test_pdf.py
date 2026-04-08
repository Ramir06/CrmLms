#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.join(os.path.dirname(__file__), 'crm_lms'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.payments.models import Payment
from apps.payments.views import generate_payment_receipt

def test_pdf():
    try:
        payment = Payment.objects.first()
        print(f'Тест платежа: {payment.id} - {payment.student.full_name}')
        
        pdf_response = generate_payment_receipt(payment)
        if pdf_response:
            print('✅ PDF успешно создан!')
            print(f'Content-Type: {pdf_response.get("Content-Type")}')
            print(f'Content-Disposition: {pdf_response.get("Content-Disposition")}')
            return True
        else:
            print('❌ Ошибка создания PDF')
            return False
    except Exception as e:
        print(f'❌ Исключение: {e}')
        return False

if __name__ == '__main__':
    test_pdf()
