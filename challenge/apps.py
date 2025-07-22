from django.apps import AppConfig


class ChallengeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'challenge'


    def ready(self):
        """
        Import signals when the app is ready.
        """
        try:
           import challenge.signals
        except ImportError:
            pass 