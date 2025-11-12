from rest_framework import serializers
from .models import Recipe, Ingredients, Favourites

class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ['name', 'quantity', 'unit', 'recipe']


class RecipeSerializers(serializers.ModelSerializer):
    ingredients = IngredientsSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'serving_size', 'cook_time', 'equipment', 'instructions', 'tips', 'user', 'created_at', 'ingredients']
        read_only_fields = ['user', 'created_at']
    


class FavouritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favourites

        fields = ['id', 'user', 'recipe', 'created_at']
        read_only_fields = ["user", "created_at"]