from django.db import models
from accounts.models import User

class Recipe(models.Model):
    title = models.CharField(max_length=100)
    serving_size = models.CharField(max_length=100)
    cook_time = models.CharField(max_length=100)
    equipment = models.TextField()
    instructions = models.TextField()
    tips = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


    def __str__(self):
        return f" Title: {self.title}"

class Ingredients(models.Model):
    name = models.CharField(max_length=15)
    quantity = models.CharField(max_length=15)
    unit = models.CharField(max_length=15)
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")


class Favourites(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_id')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name='recipe_id')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    class Meta:
        unique_together = ('user', 'recipe')
    
    def __str__(self):
        return f"{self.user.username} - {self.recipe.title}"