from django.db import models
from accounts.models import User

class Recipe(models.Model):
    title = models.CharField(max_length=100)
    serving_size = models.CharField(max_length=100)
    cook_time = models.CharField(max_length=100)
    ingredients = models.TextField()
    equipment = models.TextField()
    instructions = models.TextField()
    tips = models.TextField
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)


    def __str__(self):
        return f" Title: {self.title}"