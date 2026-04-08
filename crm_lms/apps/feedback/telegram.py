import requests
import os
from django.conf import settings
from django.utils import timezone


def send_feedback_to_telegram(feedback):
    """Отправка обратной связи в Telegram бот"""
    
    bot_token = '8694401842:AAGTCP-wBru4AzGtjC9YP-i7oRsa0dzLLtI'
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
    
    if not bot_token or not chat_id:
        print("Telegram bot token or chat ID not configured")
        return None
    
    # Формируем сообщение
    type_emoji = {
        'review': '⭐',
        'idea': '💡', 
        'bug': '🐛'
    }
    
    emoji = type_emoji.get(feedback.type, '📝')
    type_name = feedback.get_type_display()
    
    message = f"""{emoji} *{type_name}*

*Заголовок:* {feedback.title}
*Тип:* {type_name}
*Дата:* {feedback.created_at.strftime('%d.%m.%Y %H:%M')}

*Описание:*
{feedback.description}

*Автор:* {feedback.get_user_display()}
*Email:* {feedback.email or 'Не указан'}

---
#feedback_{feedback.type} #{feedback.id}"""
    
    # Отправляем сообщение
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get('ok'):
            return str(result['result']['message_id'])
        else:
            print(f"Telegram API error: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Error sending Telegram message: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error sending Telegram message: {e}")
        return None
