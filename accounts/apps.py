from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Django app configuration for the Users module.
    
    This app handles user authentication, profiles, social features,
    messaging, and GDPR compliance for the Recipe API.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Users & Authentication'

    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        Import signal handlers here if needed.
        
        Example:
            from . import signals  # Uncomment when signals are needed
        """
        pass