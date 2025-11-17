from django.shortcuts import render
from .models import(
    Recipe,
    Ingredients, 
    Favourites,
    Comments
)
from .serializers import(
    RecipeSerializers, 
    IngredientsSerializer, 
    FavouritesSerializer,
    CommentsSerializer
)
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from rest_framework import status
from rest_framework import filters
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import AllowAny
from django.db import transaction




class RecipeCreateView(generics.CreateAPIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        try:
            # Validate required fields
            required_fields = ['title', 'serving_size', 'cook_time', 'equipment', 'instructions', 'tips', 'ingredients']
            missing = [field for field in required_fields if not request.data.get(field)]

            if missing:
                return Response(
                    {"error": f"Missing required fields: {', '.join(missing)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            title = request.data.get("title")
            serving_size = request.data.get("serving_size")
            cook_time = request.data.get("cook_time")
            equipment = request.data.get("equipment", "")
            instructions = request.data.get("instructions", "")
            tips = request.data.get("tips", "")
            ingredients_data = request.data.get("ingredients", [])

            # Validate ingredients list format
            if not isinstance(ingredients_data, list):
                return Response(
                    {"error": "Ingredients must be a list."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Optional: Validate ingredient structure
            for item in ingredients_data:
                if not isinstance(item, dict) or "name" not in item:
                    return Response(
                        {"error": "Each ingredient must be an object with at least a 'name' field."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Create recipe and ingredients safely
            with transaction.atomic():
                recipe = Recipe.objects.create(
                    title=title,
                    serving_size=serving_size,
                    cook_time=cook_time,
                    equipment=equipment,
                    instructions=instructions,
                    tips=tips,
                    user=request.user
                )

                # Create ingredient entries
                for ing in ingredients_data:
                    Ingredients.objects.create(
                        recipe=recipe,
                        name=ing.get("name"),
                        quantity=ing.get("quantity", ""),
                        unit=ing.get("unit", "")
                    )

            return Response(
                {
                    "message": "Recipe created successfully.",
                    "recipe_id": recipe.id
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            # Return a readable error instead of crashing
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class RecipeListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'cook_time', 'serving_size', 'user__username']
    ordering_fields = ['created_at', 'cook_time']



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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers

    def get_query(self):
        return Recipe.objects.filter(user = self.request.user)


class IngredientDetailUpdateView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer

    def get_query(self):
        return Ingredients.objects.filter(self.request.user.recipe)

class FavouritesCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        favorites = Favourites.objects.filter(user=request.user)
        serializer = FavouritesSerializer(favorites, many=True)
        return Response(
            serializer.data,
            status= status.HTTP_200_OK
        )
class FavouritesUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = FavouritesSerializer
    
    def get_queryset(self):
        # Use the current logged-in user
        return Favourites.objects.filter(user=self.request.user)

class CommentsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, recipe_id):

        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'error':'Recipe does not exists'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        comment_text = request.data.get('comment_text')
        rating = request.data.get('rating') 


        comment = Comments.objects.create(
            user=request.user, 
            recipe=recipe,
            comment_text = comment_text,
            rating = rating
            
            )
        serializer = CommentsSerializer(comment)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )
    
class CommentsListView(APIView):
    def get(self, request, recipe_id):

        try:
            recipe = Recipe.objects.get(id=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'error':'Recipe does not exists'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        recipe_comments= Comments.objects.filter(recipe=recipe)
        serializer = CommentsSerializer(recipe_comments, many=True)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
