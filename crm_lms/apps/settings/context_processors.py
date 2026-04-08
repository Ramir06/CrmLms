from .models import FooterContent, FooterNavigationLink

def footer_content(request):
    """Добавляет контент футера в контекст всех шаблонов."""
    try:
        footer = FooterContent.objects.filter(is_active=True).first()
        nav_links = FooterNavigationLink.objects.filter(is_active=True).order_by('order', 'title')
        return {
            'footer_content': footer,
            'nav_links': nav_links
        }
    except:
        return {
            'footer_content': None,
            'nav_links': None
        }
