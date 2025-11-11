from rest_framework import serializers
from .models import Recipe, Ingredients

class IngredientsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredients
        fields = ['name', 'quantity', 'unit']


class RecipeSerializers(serializers.ModelSerializer):
    ingredients = IngredientsSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ['title', 'serving_size', 'cook_time', 'equipment', 'instructions', 'tips', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']
    
    