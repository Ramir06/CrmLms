from django import template

register = template.Library()

@register.filter
def div(value, divisor):
    """Division filter for templates"""
    try:
        return int(value) // int(divisor)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def make_range(value):
    """Create range from 1 to value (inclusive)"""
    try:
        return range(1, int(value) + 1)
    except (ValueError, TypeError):
        return range(1, 5)  # Default to 1-4
