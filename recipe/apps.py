from django.apps import AppConfig


class RecipesConfig(AppConfig):
    """
    Django app configuration for the Recipes module.
    
    This app handles recipe management, ingredients, tags, comments,
    ratings, media uploads, and recipe versioning for the Recipe API.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    verbose_name = 'recipe'

    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        Import signal handlers here if needed.
        """
        pass