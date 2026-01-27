from django.apps import AppConfig


class TestsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tests_app'
    verbose_name = 'Testlar'

    def ready(self):
        import tests_app.signals  