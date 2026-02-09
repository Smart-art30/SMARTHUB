from django.apps import AppConfig


class FinanceConfig(AppConfig):
    name = 'finance'


from django.apps import AppConfig

class FeesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fees'

    def ready(self):
        import fees.signals
