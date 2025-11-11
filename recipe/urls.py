from django.urls import path
from .views import RecipeListView, RecipeDetailView, RecipeCreateView, RecipeDetailUpdateView


urlpatterns = [
    path('list/', RecipeListView.as_view(), name='recipe_list'),
    path('create/', RecipeCreateView.as_view(), name='recipe_create'),
    path('detail/<int:pk>', RecipeDetailView.as_view(), name='recipe_detail' ),
    path('detail-u/<int:pk>', RecipeDetailUpdateView.as_view(), name='recipe_detail' ),

   
    
]