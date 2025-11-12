from django.contrib import admin
from .models import Recipe, Ingredients, Favourites, Comments
# Register your models here.

admin.site.register(Recipe)
admin.site.register(Ingredients)
admin.site.register(Favourites)
admin.site.register(Comments)