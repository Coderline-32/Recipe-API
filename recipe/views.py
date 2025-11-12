from django.shortcuts import render
from .models import Recipe, Ingredients, Favourites
from .serializers import RecipeSerializers, IngredientsSerializer, FavouritesSerializer
from rest_framework.views import APIView
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
        serving_size = request.data.get("serving_size")
        cook_time = request.data.get("cook_time")
        equipment = request.data.get("equipment", "")
        instructions = request.data.get("instructions", "")
        tips = request.data.get("tips", "")
        ingredients_data = request.data.get("ingredients", [])

    # Create recipe linked to current user
        recipe = Recipe.objects.create(
            title=title,
            serving_size=serving_size,
            cook_time=cook_time,
            equipment=equipment,
            instructions=instructions,
            tips=tips,
            user=request.user
        )

    # Create ingredients linked to the recipe
        for ingredient in ingredients_data:
            Ingredients.objects.create(
                recipe=recipe,
                name=ingredient.get("name", ""),
                quantity=ingredient.get("quantity", ""),
                unit=ingredient.get("unit", "")
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

class IngredientsListView(generics.ListAPIView):
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer

       
class RecipeDetailView(generics.RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers


class IngredientDetailView(generics.RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = IngredientsSerializer



class RecipeDetailUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers

    def get_query(self):
        return Recipe.objects.filter(user = self.request.user)


class IngredientDetailUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer

    def get_query(self):
        return Ingredients.objects.filter(self.request.user.recipe)

class FavouritesView(APIView):
    def post(self, request, recipe_id):
        try:
            recipe = Recipe.objects.get(id=recipe_id)
        
        except Recipe.DoesNotExist:
            return Response(
                {'message': 'Recipe does not exist'},
                status = status.HTTP_404_NOT_FOUND
                )
        fav,created = Favourites.objects.get_or_create(user=request.user, recipe=recipe)

        if not created:
            return Response(
                {'message':'Recipe already in favourites'},
                status = status.HTTP_200_OK
            )
        serializer = FavouritesSerializer(fav)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    def delete(self, request, recipe_id):
        try:
            recipe = Favourites.objects.get(user=request.user, recipe_id=recipe_id)
        
        except Favourites.DoesNotExist:
            return Response(
                {'message':'Recipe not in favourites'},
                status = status.HTTP_404_NOT_FOUND
            )
        recipe.delete()
        return Response(
            {
            'message':'recipe deleted'
        },
        status = status.HTTP_200_OK
        )

class FavouritesListView(generics.ListAPIView):
    queryset = Favourites.objects.all()
    serializer_class = FavouritesSerializer