from django.db import models

class Recipe(models.Model):
    title = models.CharField(max_length=100)
    serving_size = models.CharField(max_length=100)
    cook_time = models.CharField(max_length=100)
    ingredients = models.TextField()
    equipment = models.TextField()
    instructions = models.TextField()
    tips = models.TextField

    def __str__(self):
        return f" Title: {self.title}"
