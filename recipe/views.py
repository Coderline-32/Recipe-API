from django.shortcuts import render
from .models import Recipe, Ingredients
from .serializers import RecipeSerializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status


class RecipeCreateView(generics.CreateAPIView):
    serializer_class = RecipeSerializers  # used only for validation/output
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # Extract recipe fields from request
        title = request.data.get("title")
        cook_time = request.data.get("cook_time")
        ingredients_data = request.data.get("ingredients", [])

        # Create recipe linked to current user
        recipe = Recipe.objects.create(title=title, cook_time=cook_time, user=request.user)

        # Create ingredients linked to the recipe
        for ingredient in ingredients_data:
            Ingredients.objects.create(
                recipe=recipe,
                name=ingredient["name"],
                quantity=ingredient["quantity"],
                unit=ingredient["unit"]
            )

        # Serialize the recipe for response
        serializer = self.get_serializer(recipe)
        return Response(
            {"message": "Recipe created successfully", "recipe": serializer.data},
            status=status.HTTP_201_CREATED
        ) 
    
class RecipeListView(generics.ListAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers


        
class RecipeDetailView(generics.RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers

class RecipeDetailUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers

    def get_query(self):
        return Recipe.objects.filter(user = self.request.user)



