from django.apps import AppConfig


class CodecoinsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.codecoins'
    verbose_name = 'Кодкойны'
    
    def ready(self):
        import apps.codecoins.signals
