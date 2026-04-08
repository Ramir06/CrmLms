from django import template
from django.utils.html import format_html
import math

register = template.Library()

@register.filter
def mul(value, arg):
    """Умножение"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Деление"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def action_type_color(action_type):
    """Возвращает цвет для типа действия"""
    colors = {
        'create': 'success',
        'update': 'info',
        'status_change': 'warning',
        'assign': 'primary',
        'comment': 'secondary',
        'merge': 'warning',
        'archive': 'dark',
        'delete': 'danger',
        'convert_to_student': 'success',
        'import': 'info',
    }
    return colors.get(action_type, 'secondary')

@register.filter
def truncatechars_safe(value, arg):
    """Безопасное обрезание текста"""
    try:
        length = int(arg)
        if len(value) <= length:
            return value
        return value[:length] + '...'
    except (ValueError, TypeError):
        return value

@register.filter
def get_full_name_safe(user):
    """Безопасное получение полного имени пользователя"""
    if not user:
        return ''
    return getattr(user, "full_name", "") or user.username

@register.filter
def get_initials_safe(user):
    """Безопасное получение инициалов пользователя"""
    if not user:
        return ''
    full_name = getattr(user, "full_name", "") or user.username
    return full_name[:2].upper()

@register.simple_tag
def get_progress_percentage(value, total):
    """Возвращает процент для прогресс бара"""
    try:
        if total == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError):
        return 0
