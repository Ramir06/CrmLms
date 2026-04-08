from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Получить значение из словаря по ключу"""
    if dictionary is None:
        return None
    return dictionary.get(key)
