from django.urls import path
from .views import (
    RecipeListView,
    RecipeDetailView,
    RecipeCreateView,
    RecipeDetailUpdateView,
    IngredientsListView,
    IngredientDetailView,
    IngredientDetailUpdateView,
    FavouritesCreateView,
    FavouritesListView,
    FavouritesUpdateDeleteView,
    CommentsView,
    CommentsListView
)

urlpatterns = [
    path('list/', RecipeListView.as_view(), name='recipe_list'),
    path('create/', RecipeCreateView.as_view(), name='recipe_create'),
    path('detail/<int:pk>/', RecipeDetailView.as_view(), name='recipe_detail' ),
    path('detail-u/<int:pk>/', RecipeDetailUpdateView.as_view(), name='recipe_detail' ),
    path('ingredients/list/', IngredientsListView.as_view(), name='recipe_list'),
    path('ingredient/detail/<int:pk>/', IngredientDetailView.as_view(), name='recipe_detail' ),
    path('ingredient/detail-u/<int:pk>/', IngredientDetailUpdateView.as_view(), name='recipe_detail' ),
    path('favourites/<int:recipe_id>/', FavouritesCreateView.as_view(), name='favourites'),
    path('favourites/list/', FavouritesListView.as_view(), name='favourites_list'),
    path('favourites/update-delete/<int:pk>/', FavouritesUpdateDeleteView.as_view(), name='favourites_update_delete'),
    path('comment/create/<int:recipe_id>/', CommentsView.as_view(), name='comment_create'),
    path('comment/list/<int:recipe_id>/', CommentsListView.as_view(), name='comment_list'),

   
    
]