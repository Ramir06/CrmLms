from django import template
from apps.mentors.kpi_utils import calculate_mentor_kpi, get_kpi_status_color, get_kpi_status_display

register = template.Library()


@register.inclusion_tag('mentors/kpi_card.html')
def kpi_card(mentor_user, show_refresh_button=False):
    """
    Template tag для отображения KPI карточки ментора
    
    Usage: {% kpi_card mentor_user show_refresh_button=True %}
    """
    kpi_data = calculate_mentor_kpi(mentor_user.id)
    
    # Добавляем дополнительные данные для шаблона
    kpi_data['color'] = get_kpi_status_color(kpi_data['status'])
    kpi_data['status_display'] = get_kpi_status_display(kpi_data['status'])
    kpi_data['mentor_id'] = mentor_user.id
    
    # Получаем профиль для даты обновления
    try:
        from apps.mentors.models import MentorProfile
        profile = MentorProfile.objects.get(user=mentor_user)
        kpi_data['kpi_updated_at'] = profile.kpi_updated_at
    except MentorProfile.DoesNotExist:
        kpi_data['kpi_updated_at'] = None
    
    return {
        'kpi_data': kpi_data,
        'mentor_id': mentor_user.id,
        'show_refresh_button': show_refresh_button
    }


@register.filter
def kpi_status_badge(status_code):
    """
    Filter для отображения статуса KPI в виде бейджа
    
    Usage: {{ mentor.kpi_status|kpi_status_badge }}
    """
    color = get_kpi_status_color(status_code)
    display = get_kpi_status_display(status_code)
    
    return f'<span style="background-color: {color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px;">{display}</span>'


@register.filter
def kpi_color(value):
    """
    Filter для получения цвета KPI
    
    Usage: <span style="color: {{ mentor.kpi|kpi_color }}">{{ mentor.kpi }}</span>
    """
    if value is None:
        return '#6b7280'
    
    if value >= 85:
        return '#10b981'  # green
    elif value >= 70:
        return '#3b82f6'  # blue
    elif value >= 55:
        return '#f59e0b'  # yellow
    else:
        return '#ef4444'  # red


@register.simple_tag
def get_mentor_kpi(mentor_user):
    """
    Simple tag для получения KPI данных ментора
    
    Usage: {% get_mentor_kpi mentor_user as kpi_data %}
    """
    return calculate_mentor_kpi(mentor_user.id)
