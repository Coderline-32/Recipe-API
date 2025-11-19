from rest_framework import serializers
from django.db.models import Avg
from .models import Recipe, Ingredient, Tag, Comment, Rating, RecipeImage, RecipeVersion
from users.serializers import UserMinimalSerializer


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    recipe_count = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['id', 'name', 'type', 'slug', 'description', 'recipe_count', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at', 'recipe_count']

    def get_recipe_count(self, obj):
        """Get count of public recipes with this tag."""
        return obj.get_recipe_count()


class IngredientSerializer(serializers.ModelSerializer):
    """Serializer for Ingredient model."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'quantity', 'unit', 'type', 'notes', 'full_name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_full_name(self, obj):
        """Get full ingredient name with notes."""
        return obj.get_full_name()


class RecipeImageSerializer(serializers.ModelSerializer):
    """Serializer for RecipeImage model."""
    class Meta:
        model = RecipeImage
        fields = ['id', 'image', 'image_type', 'step_number', 'caption', 'order', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for Comment model."""
    user_detail = UserMinimalSerializer(source='user', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'user_detail', 'content', 'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create comment with current user as author."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def validate_content(self, value):
        """Validate comment content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment cannot be empty.")
        if len(value) > 5000:
            raise serializers.ValidationError("Comment is too long (max 5000 characters).")
        return value.strip()


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for Rating model."""
    user_detail = UserMinimalSerializer(source='user', read_only=True)

    class Meta:
        model = Rating
        fields = ['id', 'user', 'user_detail', 'rating', 'review', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Create or update rating."""
        user = self.context['request'].user
        recipe_id = self.context.get('recipe_id')
        validated_data['user'] = user

        rating, created = Rating.objects.update_or_create(
            user=user,
            recipe_id=recipe_id,
            defaults=validated_data
        )

        # Update recipe's average rating
        if rating.recipe:
            rating.recipe.update_rating()

        return rating

    def validate_rating(self, value):
        """Validate rating is between 1-5."""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_review(self, value):
        """Validate review length."""
        if value and len(value) > 5000:
            raise serializers.ValidationError("Review is too long (max 5000 characters).")
        return value


class RecipeVersionSerializer(serializers.ModelSerializer):
    """Serializer for RecipeVersion model."""
    changed_by_detail = UserMinimalSerializer(source='changed_by', read_only=True)

    class Meta:
        model = RecipeVersion
        fields = [
            'id', 'version_number', 'title', 'description', 'instructions',
            'ingredients_snapshot', 'changed_by', 'changed_by_detail',
            'change_summary', 'created_at'
        ]
        read_only_fields = fields


class RecipeListSerializer(serializers.ModelSerializer):
    """Serializer for listing recipes (minimal data)."""
    author = UserMinimalSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    rating_count = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'slug', 'featured_image', 'description',
            'author', 'difficulty', 'cook_time', 'serving_size',
            'average_rating', 'rating_count', 'tags', 'created_at'
        ]
        read_only_fields = [
            'id', 'slug', 'average_rating', 'created_at'
        ]

    def get_rating_count(self, obj):
        """Get count of ratings."""
        return obj.total_ratings


class RecipeDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed recipe view."""
    author = UserMinimalSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientSerializer(many=True, read_only=True)
    images = RecipeImageSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    ratings = RatingSerializer(many=True, read_only=True)
    versions = RecipeVersionSerializer(many=True, read_only=True)
    user_rating = serializers.SerializerMethodField()
    user_has_favorited = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            'id', 'title', 'slug', 'description', 'author', 'featured_image',
            'serving_size', 'cook_time', 'prep_time', 'equipment',
            'instructions', 'tips', 'difficulty', 'nutrition_info',
            'visibility', 'average_rating', 'total_ratings', 'view_count',
            'tags', 'video_url', 'ingredients', 'images', 'comments',
            'ratings', 'versions', 'user_rating', 'user_has_favorited',
            'is_owner', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'author', 'average_rating', 'total_ratings',
            'view_count', 'created_at', 'updated_at', 'comments', 'ratings'
        ]

    def get_user_rating(self, obj):
        """Get current user's rating for this recipe."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rating = obj.ratings.filter(user=request.user).first()
            if rating:
                return RatingSerializer(rating).data
        return None

    def get_user_has_favorited(self, obj):
        """Check if current user has favorited this recipe."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False

    def get_is_owner(self, obj):
        """Check if current user is the recipe owner."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.author == request.user
        return False


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating recipes."""
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        source='tags'
    )
    ingredients_data = IngredientSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Recipe
        fields = [
            'title', 'description', 'serving_size', 'cook_time', 'prep_time',
            'equipment', 'instructions', 'tips', 'difficulty', 'nutrition_info',
            'visibility', 'featured_image', 'video_url', 'tag_ids', 'ingredients_data'
        ]

    def validate_title(self, value):
        """Validate recipe title."""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty.")
        if len(value) > 255:
            raise serializers.ValidationError("Title is too long (max 255 characters).")
        return value.strip()

    def validate_cook_time(self, value):
        """Validate cook time."""
        if value < 1:
            raise serializers.ValidationError("Cook time must be at least 1 minute.")
        return value

    def validate_serving_size(self, value):
        """Validate serving size."""
        if value < 1:
            raise serializers.ValidationError("Serving size must be at least 1.")
        return value

    def validate_nutrition_info(self, value):
        """Validate nutrition info structure."""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("Nutrition info must be a JSON object.")
        return value

    def create(self, validated_data):
        """Create recipe with author and ingredients."""
        ingredients_data = validated_data.pop('ingredients_data', [])
        user = self.context['request'].user
        
        recipe = Recipe.objects.create(author=user, **validated_data)

        # Create ingredients
        for ingredient_data in ingredients_data:
            Ingredient.objects.create(recipe=recipe, **ingredient_data)

        # Create initial version
        RecipeVersion.create_version(recipe, user, "Initial version")

        return recipe

    def update(self, instance, validated_data):
        """Update recipe and track version."""
        ingredients_data = validated_data.pop('ingredients_data', None)
        user = self.context['request'].user

        # Update recipe fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update ingredients if provided
        if ingredients_data is not None:
            instance.ingredients.all().delete()
            for ingredient_data in ingredients_data:
                Ingredient.objects.create(recipe=instance, **ingredient_data)

        # Create version record
        RecipeVersion.create_version(instance, user, "Recipe updated")

        return instance


class RecipeScalePreviewSerializer(serializers.Serializer):
    """Serializer for ingredient scaling preview."""
    new_serving_size = serializers.IntegerField(min_value=1)
    scaled_ingredients = serializers.SerializerMethodField()

    def get_scaled_ingredients(self, obj):
        """Get scaled ingredients list."""
        recipe = self.context.get('recipe')
        serving_size = obj.get('new_serving_size')
        if recipe:
            return recipe.get_ingredients_scaled(serving_size)
        return []