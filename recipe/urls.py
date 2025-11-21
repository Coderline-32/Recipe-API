from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RecipeViewSet,
    TagViewSet,
    IngredientViewSet,
    CommentViewSet,
    RatingViewSet,
    RecipeImageViewSet,
    RecipeVersionViewSet,
)

app_name = 'recipes'

router = DefaultRouter()
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'ingredients', IngredientViewSet, basename='ingredient')

urlpatterns = [
    # Recipes main endpoints
    path('', include(router.urls)),
    path('recipes/', RecipeViewSet.as_view({'get': 'list', 'post': 'create'}), name='recipe-list'),
    path('recipes/trending/', RecipeViewSet.as_view({'get': 'trending'}), name='recipe-trending'),
    path('recipes/search-advanced/', RecipeViewSet.as_view({'get': 'search_advanced'}), name='recipe-search-advanced'),
    path('recipes/<int:pk>/', RecipeViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='recipe-detail'),
    path('recipes/<int:pk>/publish/', RecipeViewSet.as_view({'post': 'publish'}), name='recipe-publish'),
    path('recipes/<int:pk>/scale-ingredients/', RecipeViewSet.as_view({'post': 'scale_ingredients'}), name='recipe-scale'),
    path('recipes/<int:pk>/versions/', RecipeViewSet.as_view({'get': 'versions'}), name='recipe-versions'),
    path('recipes/<int:pk>/stats/', RecipeViewSet.as_view({'get': 'stats'}), name='recipe-stats'),

    # Comments for a recipe
    path('recipes/<int:recipe_id>/comments/', CommentViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='recipe-comments-list'),
    path('recipes/<int:recipe_id>/comments/<int:pk>/', CommentViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='recipe-comments-detail'),

    # Ratings for a recipe
    path('recipes/<int:recipe_id>/ratings/', RatingViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='recipe-ratings-list'),
    path('recipes/<int:recipe_id>/ratings/<int:pk>/', RatingViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='recipe-ratings-detail'),

    # Images for a recipe
    path('recipes/<int:recipe_id>/images/', RecipeImageViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='recipe-images-list'),
    path('recipes/<int:recipe_id>/images/<int:pk>/', RecipeImageViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='recipe-images-detail'),

    # Versions for a recipe
    path('recipes/<int:recipe_id>/versions/', RecipeVersionViewSet.as_view({
        'get': 'list'
    }), name='recipe-recipe-versions-list'),
    path('recipes/<int:recipe_id>/versions/<int:pk>/', RecipeVersionViewSet.as_view({
        'get': 'retrieve'
    }), name='recipe-recipe-versions-detail'),
]