from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.apps.ai'
    verbose_name = 'CareGrid X AI'

    def ready(self):
        pass
