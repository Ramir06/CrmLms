from django import template

register = template.Library()


@register.filter
def has_permission(user, permission):
    """
    Template filter для проверки прав доступа пользователя
    Usage: {% if request.user|has_permission:'view_calendar' %}
    """
    return user.has_permission(permission)


@register.simple_tag
def check_permission(user, permission):
    """
    Template tag для проверки прав доступа пользователя
    Usage: {% check_permission request.user 'view_calendar' as has_perm %}
    """
    return user.has_permission(permission)


@register.filter
def can_access_section(user, section):
    """
    Template filter для проверки доступа к разделу
    Суперадминистратор имеет доступ ко всем разделам
    """
    if user.is_superuser:
        return True
    
    # Определяем права для каждого раздела
    section_permissions = {
        'calendar': 'view_calendar',
        'courses': 'view_courses',
        'students': 'view_students',
        'mentors': 'view_mentors',
        'leads': 'view_leads',  # Исправлено с 'add_users' на 'view_leads'
        'payments': 'view_payments',
        'debts': 'manage_student_payments',
        'salaries': 'view_reports',
        'finance': 'view_payments',  # или view_reports
        'reports': 'view_reports',
        'settings': 'view_settings',
        'organizations': 'view_organizations',
    }
    
    # Для дашборда даем доступ если есть кастомная роль или хотя бы одно право на управление
    if section == 'dashboard':
        # Если у пользователя есть кастомная роль, даем доступ к дашборду
        if user.custom_role:
            return True
        
        # Иначе проверяем наличие прав на управление
        management_permissions = [
            'view_students', 'view_mentors', 'view_courses', 'view_organizations',
            'view_payments', 'view_reports', 'add_users', 'edit_users', 'delete_users',
            'add_students', 'edit_students', 'delete_students',
            'add_mentors', 'edit_mentors', 'delete_mentors',
            'add_courses', 'edit_courses', 'delete_courses',
            'view_settings', 'edit_settings'
        ]
        return any(user.has_permission(perm) for perm in management_permissions)
    
    required_permission = section_permissions.get(section)
    if required_permission:
        return user.has_permission(required_permission)
    
    return False
