from rest_framework import serializers
from .models import (
    Recipe, 
    Ingredients, 
    Favourites,
    Comments
)

class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ['name', 'quantity', 'unit', 'recipe']


class RecipeSerializers(serializers.ModelSerializer):
    ingredients = IngredientsSerializer(many=True)
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'serving_size', 'cook_time', 'equipment', 'instructions', 'tips', 'user_username', 'created_at', 'ingredients']
        read_only_fields = ['user', 'created_at']
    


class FavouritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favourites

        fields = ['id', 'user', 'recipe', 'created_at']
        read_only_fields = ["id", "user", "created_at"]

class CommentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments

        fields = ['id', 'user', 'recipe', 'comment_text', 'rating', 'created_at']
        read_only_fields = ['id', 'user', 'recipe', 'created_at']