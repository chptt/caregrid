from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caregrid.apps.ai'
    verbose_name = 'AI Services'

    def ready(self):
        pass
