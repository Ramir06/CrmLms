from django import template

register = template.Library()

@register.filter
def get_ticket(enrollment_id, ticket_data):
    """Получить данные талонов для студента"""
    return ticket_data.get(enrollment_id, {'total': 0, 'used': 0, 'remaining': 0})

@register.filter
def get_monthly_spent(enrollment_id, monthly_spent_data):
    """Получить потраченные талоны за месяц для студента"""
    return monthly_spent_data.get(enrollment_id, 0)
