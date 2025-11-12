from django.urls import path
from .views import RecipeListView, RecipeDetailView, RecipeCreateView, RecipeDetailUpdateView, IngredientsListView, IngredientDetailView, IngredientDetailUpdateView


urlpatterns = [
    path('list/', RecipeListView.as_view(), name='recipe_list'),
    path('create/', RecipeCreateView.as_view(), name='recipe_create'),
    path('detail/<int:pk>', RecipeDetailView.as_view(), name='recipe_detail' ),
    path('detail-u/<int:pk>', RecipeDetailUpdateView.as_view(), name='recipe_detail' ),
    path('ingredients/list/', IngredientsListView.as_view(), name='recipe_list'),
    path('ingredient/detail/<int:pk>', IngredientDetailView.as_view(), name='recipe_detail' ),
    path('ingredient/detail-u/<int:pk>', IngredientDetailUpdateView.as_view(), name='recipe_detail' ),

   
    
]