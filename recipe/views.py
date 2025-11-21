from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.core.cache import cache
from django.views.decorators.cache import cache_page

from .models import Recipe, Ingredient, Tag, Comment, Rating, RecipeImage, RecipeVersion
from .serializers import (
    RecipeListSerializer,
    RecipeDetailSerializer,
    RecipeCreateUpdateSerializer,
    IngredientSerializer,
    TagSerializer,
    CommentSerializer,
    RatingSerializer,
    RecipeImageSerializer,
    RecipeVersionSerializer,
    RecipeScalePreviewSerializer,
)
from .permissions import (
    IsRecipeAuthorOrReadOnly,
    IsPublicOrAuthor,
    CanCommentOrReadOnly,
    CanRateRecipe,
    CanManageRecipes,
)
from accounts.models import Notification


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for list endpoints."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and filtering tags.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    lookup_field = 'slug'


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing ingredients (read-only).
    Ingredients are created/updated through recipes.
    """
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'type']
    ordering_fields = ['name', 'type', 'created_at']
    ordering = ['name']
    pagination_class = StandardResultsSetPagination


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for recipe comments.
    """
    serializer_class = CommentSerializer
    permission_classes = [CanCommentOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        """Get comments for a specific recipe."""
        recipe_id = self.kwargs.get('recipe_id')
        return Comment.objects.filter(
            recipe_id=recipe_id,
            is_approved=True
        ).select_related('user')

    def perform_create(self, serializer):
        """Create comment and notify recipe author."""
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        comment = serializer.save(recipe=recipe)

        # Create notification for recipe author
        if recipe.author != self.request.user:
            Notification.create_notification(
                user=recipe.author,
                notification_type='comment',
                description=f"{self.request.user.username} commented on your recipe: {recipe.title}",
                actor=self.request.user,
                content_type='comment',
                object_id=comment.id,
            )


class RatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for recipe ratings/reviews.
    One rating per user per recipe.
    """
    serializer_class = RatingSerializer
    permission_classes = [CanRateRecipe]
    filter_backends = [OrderingFilter]
    ordering = ['-created_at']

    def get_queryset(self):
        """Get ratings for a specific recipe."""
        recipe_id = self.kwargs.get('recipe_id')
        return Rating.objects.filter(recipe_id=recipe_id).select_related('user')

    def get_serializer_context(self):
        """Add recipe_id to context."""
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def perform_create(self, serializer):
        """Create rating and notify recipe author."""
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        rating = serializer.save(recipe=recipe)

        # Create notification for recipe author
        if recipe.author != self.request.user:
            Notification.create_notification(
                user=recipe.author,
                notification_type='like',
                description=f"{self.request.user.username} rated your recipe {rating.rating}⭐",
                actor=self.request.user,
                content_type='rating',
                object_id=rating.id,
            )


class RecipeImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for recipe images.
    """
    serializer_class = RecipeImageSerializer
    permission_classes = [IsRecipeAuthorOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """Get images for a specific recipe."""
        recipe_id = self.kwargs.get('recipe_id')
        return RecipeImage.objects.filter(recipe_id=recipe_id).order_by('order')

    def perform_create(self, serializer):
        """Create image for recipe."""
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        self.check_object_permissions(self.request, recipe)
        serializer.save(recipe=recipe)


class RecipeVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for recipe version history (read-only).
    """
    serializer_class = RecipeVersionSerializer
    permission_classes = [IsPublicOrAuthor]

    def get_queryset(self):
        """Get versions for a specific recipe."""
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        # Check permission
        if recipe.visibility != 'public' and recipe.author != self.request.user:
            return RecipeVersion.objects.none()
        return RecipeVersion.objects.filter(recipe_id=recipe_id).order_by('-version_number')


class RecipeViewSet(viewsets.ModelViewSet):
    """
    Complete ViewSet for Recipe CRUD operations.
    
    Supports:
    - Listing recipes (with filtering, searching, pagination)
    - Creating recipes (authenticated users)
    - Viewing recipe details
    - Updating/deleting recipes (author only)
    - Filtering by tags, difficulty, cook time
    - Searching by title, description, ingredients
    - Scaling ingredients to different serving sizes
    - Managing recipe comments and ratings
    """
    permission_classes = [IsPublicOrAuthor, CanManageRecipes]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['difficulty', 'visibility', 'author']
    search_fields = ['title', 'description', 'ingredients__name', 'tags__name']
    ordering_fields = ['created_at', 'average_rating', 'cook_time', 'title']
    ordering = ['-created_at']
    lookup_field = 'id'

    def get_queryset(self):
        """Get recipes based on visibility and permissions with selective prefetching."""
        user = self.request.user
        if user.is_authenticated:
            # Show public recipes + own recipes
            queryset = Recipe.objects.filter(
                Q(visibility='public') | Q(author=user)
            ).select_related('author').prefetch_related('tags', 'ingredients')
        else:
            # Anonymous users see only public recipes
            queryset = Recipe.objects.filter(
                visibility='public'
            ).select_related('author').prefetch_related('tags', 'ingredients')

        # For detail views, prefetch additional related objects to avoid N+1 queries
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('images', 'comments', 'versions', 'ratings')

        return queryset

    @method_decorator(cache_page(300))  # Cache for 5 minutes
    def list(self, request, *args, **kwargs):
        """List recipes with caching for performance."""
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return RecipeDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        elif self.action == 'scale_ingredients':
            return RecipeScalePreviewSerializer
        return RecipeListSerializer

    def perform_create(self, serializer):
        """Create recipe with current user as author."""
        recipe = serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """Retrieve recipe and increment view count."""
        recipe = self.get_object()
        self.check_object_permissions(request, recipe)

        # Increment view count for public recipes
        if recipe.visibility == 'public':
            recipe.increment_view_count()

        serializer = self.get_serializer(recipe)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsRecipeAuthorOrReadOnly])
    def publish(self, request, pk=None):
        """
        Publish a draft or pending recipe.
        POST /recipes/<id>/publish/
        """
        recipe = self.get_object()
        self.check_object_permissions(request, recipe)

        if recipe.visibility in ['draft', 'pending']:
            recipe.visibility = 'public'
            recipe.save()
            return Response(
                {'message': 'Recipe published successfully', 'visibility': recipe.visibility},
                status=status.HTTP_200_OK
            )
        return Response(
            {'error': 'Only draft or pending recipes can be published'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def scale_ingredients(self, request, pk=None):
        """
        Preview ingredients scaled to a different serving size.
        POST /recipes/<id>/scale_ingredients/
        Body: {"new_serving_size": 8}
        """
        recipe = self.get_object()
        self.check_object_permissions(request, recipe)

        serializer = RecipeScalePreviewSerializer(
            request.data,
            context={'recipe': recipe}
        )
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        Get recipe edit history/versions.
        GET /recipes/<id>/versions/
        """
        recipe = self.get_object()
        self.check_object_permissions(request, recipe)

        versions = recipe.versions.all().order_by('-version_number')
        page = self.paginate_queryset(versions)
        if page is not None:
            serializer = RecipeVersionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RecipeVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get recipe statistics.
        GET /recipes/<id>/stats/
        """
        recipe = self.get_object()
        self.check_object_permissions(request, recipe)

        stats = {
            'total_views': recipe.view_count,
            'total_ratings': recipe.total_ratings,
            'average_rating': recipe.average_rating,
            'total_comments': recipe.comments.filter(is_approved=True).count(),
            'favorites_count': recipe.favorited_by.count(),
        }
        return Response(stats, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(300))  # Cache for 5 minutes
    def trending(self, request):
        """
        Get trending recipes (by views and ratings).
        GET /recipes/trending/
        """
        cache_key = 'trending_recipes'
        recipes = cache.get(cache_key)
        if recipes is None:
            recipes = Recipe.objects.filter(
                visibility='public'
            ).annotate(
                rating_score=F('average_rating') * F('total_ratings')
            ).order_by('-rating_score', '-view_count')[:20]
            cache.set(cache_key, recipes, 300)  # Cache for 5 minutes

        serializer = RecipeListSerializer(recipes, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search_advanced(self, request):
        """
        Advanced recipe search with multiple filters.
        GET /recipes/search_advanced/?tags=1,2&difficulty=easy&max_cook_time=30
        """
        queryset = self.get_queryset()

        # Filter by tags
        tags = request.query_params.get('tags', '').split(',')
        if tags[0]:
            queryset = queryset.filter(tags__id__in=[t for t in tags if t])

        # Filter by difficulty
        difficulty = request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # Filter by cook time
        max_cook_time = request.query_params.get('max_cook_time')
        if max_cook_time:
            try:
                queryset = queryset.filter(cook_time__lte=int(max_cook_time))
            except ValueError:
                pass

        # Filter by serving size
        serving_size = request.query_params.get('serving_size')
        if serving_size:
            try:
                queryset = queryset.filter(serving_size__gte=int(serving_size))
            except ValueError:
                pass

        # Search by title or description
        search_term = request.query_params.get('search', '')
        if search_term:
            queryset = queryset.filter(
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term)
            )

        # Remove distinct() as it's often unnecessary and slow; ensure unique results via query optimization
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = RecipeListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = RecipeListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
