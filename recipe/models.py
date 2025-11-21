from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.urls import reverse
from decimal import Decimal
import json

User = get_user_model()


class Tag(models.Model):
    """
    Tag/Category model for organizing recipes.
    """
    TAG_TYPES = (
        ('tag', 'Tag'),
        ('category', 'Category'),
        ('dietary', 'Dietary Restriction'),
        ('cuisine', 'Cuisine'),
    )

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Tag or category name (e.g., 'Vegan', 'Italian', 'Gluten-Free')"
    )
    type = models.CharField(
        max_length=20,
        choices=TAG_TYPES,
        default='tag',
        help_text="Type of tag"
    )
    slug = models.SlugField(
        unique=True,
        blank=True,
        help_text="URL-friendly version of the name"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of the tag"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recipes_tag'
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_recipe_count(self):
        """Get number of recipes with this tag."""
        return self.recipe_set.filter(visibility='public').count()


class Recipe(models.Model):
    """
    Main Recipe model with comprehensive fields and features.
    """
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    )

    VISIBILITY_CHOICES = (
        ('draft', 'Draft'),
        ('private', 'Private'),
        ('pending', 'Pending Review'),
        ('public', 'Public'),
    )

    # Basic Information
    title = models.CharField(
        max_length=255,
        help_text="Recipe title"
    )
    slug = models.SlugField(
        unique=True,
        blank=True,
        help_text="URL-friendly version of the title"
    )
    description = models.TextField(
        blank=True,
        help_text="Recipe description or introduction"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        help_text="Author of the recipe",
        blank=True,
        null=True
    )

    # Cooking Details
    serving_size = models.PositiveIntegerField(
        default=4,
        validators=[MinValueValidator(1)],
        help_text="Number of servings"
    )
    cook_time = models.PositiveIntegerField(
        help_text="Cooking time in minutes",
        validators=[MinValueValidator(1)]
    )
    prep_time = models.PositiveIntegerField(
        default=0,
        help_text="Preparation time in minutes"
    )
    equipment = models.JSONField(
        default=list,
        blank=True,
        help_text="List of required equipment"
    )
    instructions = models.JSONField(
        default=list,
        help_text="Step-by-step instructions as JSON array"
    )
    tips = models.TextField(
        blank=True,
        help_text="Chef tips and variations"
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        help_text="Difficulty level"
    )

    # Nutrition Information
    nutrition_info = models.JSONField(
        default=dict,
        blank=True,
        help_text="Nutrition info: {calories, protein_g, carbs_g, fat_g, fiber_g}"
    )

    # Media
    featured_image = models.ImageField(
        upload_to='recipes/featured/',
        null=True,
        blank=True,
        help_text="Featured image for the recipe"
    )
    video_url = models.URLField(
        blank=True,
        help_text="Optional YouTube or video tutorial link"
    )

    # Tags and Categories
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='recipes',
        help_text="Tags for this recipe"
    )

    # Status and Visibility
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='draft',
        help_text="Recipe visibility"
    )

    # Ratings and Reviews
    average_rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="Average rating (0-5)"
    )
    total_ratings = models.PositiveIntegerField(
        default=0,
        help_text="Total number of ratings"
    )

    # Tracking
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of times recipe was viewed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipes_recipe'
        verbose_name = 'Recipe'
        verbose_name_plural = 'Recipes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['author', '-created_at']),
            models.Index(fields=['visibility', '-created_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['-average_rating']),
            models.Index(fields=['difficulty']),
            models.Index(fields=['title']),
            models.Index(fields=['description']),
            models.Index(fields=['cook_time']),
            models.Index(fields=['serving_size']),
        ]
        permissions = [
            ('approve_recipe', 'Can approve pending recipes'),
            ('flag_recipe', 'Can flag inappropriate recipes'),
        ]

    def __str__(self):
        return f"{self.title} by {self.author.username}"

    def save(self, *args, **kwargs):
        """Auto-generate slug and update recipe version."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Get the absolute URL for the recipe."""
        return reverse('recipe-detail', kwargs={'pk': self.pk})

    def get_total_time(self):
        """Get total time (prep + cook)."""
        return self.prep_time + self.cook_time

    def increment_view_count(self):
        """Increment view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])

    def update_rating(self):
        """Recalculate average rating from reviews."""
        ratings = self.ratings.all()
        if ratings.exists():
            avg = ratings.aggregate(models.Avg('rating'))['rating__avg']
            self.average_rating = avg or 0.0
            self.total_ratings = ratings.count()
        else:
            self.average_rating = 0.0
            self.total_ratings = 0
        self.save(update_fields=['average_rating', 'total_ratings'])

    def get_ingredients(self):
        """Get all ingredients for this recipe."""
        return self.ingredients.all()

    def get_ingredients_scaled(self, new_serving_size):
        """
        Get ingredients scaled to a different serving size.
        Returns a list of dict with scaled quantities.
        """
        if new_serving_size <= 0:
            raise ValueError("Serving size must be greater than 0")

        scale_factor = Decimal(new_serving_size) / Decimal(self.serving_size)
        scaled_ingredients = []

        for ingredient in self.get_ingredients():
            scaled = {
                'name': ingredient.name,
                'quantity': float(ingredient.quantity * scale_factor),
                'unit': ingredient.unit,
                'type': ingredient.type,
            }
            scaled_ingredients.append(scaled)

        return scaled_ingredients

    def is_owned_by(self, user):
        """Check if recipe is owned by user."""
        return self.author == user

    def is_public(self):
        """Check if recipe is publicly visible."""
        return self.visibility == 'public'


class Ingredient(models.Model):
    """
    Ingredient model with automatic recipe FK assignment.
    """
    INGREDIENT_TYPES = (
        ('main', 'Main Ingredient'),
        ('spice', 'Spice'),
        ('seasoning', 'Seasoning'),
        ('garnish', 'Garnish'),
        ('other', 'Other'),
    )

    UNIT_CHOICES = (
        ('g', 'Grams'),
        ('kg', 'Kilogram'),
        ('ml', 'Milliliter'),
        ('l', 'Liter'),
        ('oz', 'Ounce'),
        ('lb', 'Pound'),
        ('cup', 'Cup'),
        ('tbsp', 'Tablespoon'),
        ('tsp', 'Teaspoon'),
        ('pint', 'Pint'),
        ('units', 'Units'),
        ('whole', 'Whole'),
        ('to_taste', 'To taste'),
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        help_text="Recipe this ingredient belongs to"
    )
    name = models.CharField(
        max_length=200,
        help_text="Ingredient name"
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Quantity of ingredient"
    )
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default='units',
        help_text="Unit of measurement"
    )
    type = models.CharField(
        max_length=20,
        choices=INGREDIENT_TYPES,
        default='main',
        help_text="Type of ingredient"
    )
    notes = models.TextField(
        blank=True,
        help_text="Optional notes (e.g., 'finely diced', 'room temperature')"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recipes_ingredient'
        verbose_name = 'Ingredient'
        verbose_name_plural = 'Ingredients'
        ordering = ['type', 'name']
        indexes = [
            models.Index(fields=['recipe']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.quantity} {self.unit} {self.name}"

    def scale(self, factor):
        """
        Return scaled quantity (does not save).
        """
        return self.quantity * factor

    def get_display_quantity(self):
        """Get quantity as string, removing trailing zeros."""
        qty = str(self.quantity)
        if '.' in qty:
            qty = qty.rstrip('0').rstrip('.')
        return qty

    def get_full_name(self):
        """Get full ingredient name with notes."""
        if self.notes:
            return f"{self.name} ({self.notes})"
        return self.name


class RecipeImage(models.Model):
    """
    Model for multiple images per recipe.
    Supports step-by-step images and gallery images.
    """
    IMAGE_TYPES = (
        ('featured', 'Featured Image'),
        ('step', 'Step Image'),
        ('gallery', 'Gallery Image'),
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='images',
        help_text="Recipe this image belongs to"
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        help_text="Recipe image"
    )
    image_type = models.CharField(
        max_length=20,
        choices=IMAGE_TYPES,
        default='gallery',
        help_text="Type of image"
    )
    step_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Step number if this is a step image"
    )
    caption = models.TextField(
        blank=True,
        help_text="Image caption or description"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recipes_recipe_image'
        verbose_name = 'Recipe Image'
        verbose_name_plural = 'Recipe Images'
        ordering = ['order', 'uploaded_at']
        indexes = [
            models.Index(fields=['recipe', 'image_type']),
        ]

    def __str__(self):
        return f"{self.get_image_type_display()} for {self.recipe.title}"


class Comment(models.Model):
    """
    Model for recipe comments.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="Recipe being commented on"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_comments',
        help_text="User who commented"
    )
    content = models.TextField(
        help_text="Comment content"
    )
    is_spam = models.BooleanField(
        default=False,
        help_text="Flag for spam detection"
    )
    is_approved = models.BooleanField(
        default=True,
        help_text="Whether comment is approved for display"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipes_comment'
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipe', '-created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['is_spam', 'is_approved']),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.recipe.title}"


class Rating(models.Model):
    """
    Model for recipe ratings/reviews.
    One rating per user per recipe.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ratings',
        help_text="Recipe being rated"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_ratings',
        help_text="User who rated"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating (1-5 stars)"
    )
    review = models.TextField(
        blank=True,
        help_text="Optional written review"
    )
    is_spam = models.BooleanField(
        default=False,
        help_text="Flag for spam detection"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recipes_rating'
        verbose_name = 'Rating'
        verbose_name_plural = 'Ratings'
        ordering = ['-created_at']
        unique_together = ('user', 'recipe')
        indexes = [
            models.Index(fields=['recipe']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
        ]

    def __str__(self):
        return f"{self.rating}⭐ by {self.user.username} on {self.recipe.title}"


class RecipeVersion(models.Model):
    """
    Model to track recipe edit history/versioning.
    """
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='versions',
        help_text="Recipe this version belongs to"
    )
    version_number = models.PositiveIntegerField(
        help_text="Version number"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.JSONField()
    ingredients_snapshot = models.JSONField(
        help_text="JSON snapshot of ingredients at this version"
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recipe_edits'
    )
    change_summary = models.TextField(
        blank=True,
        help_text="Description of changes in this version"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recipes_recipe_version'
        verbose_name = 'Recipe Version'
        verbose_name_plural = 'Recipe Versions'
        ordering = ['-version_number']
        unique_together = ('recipe', 'version_number')
        indexes = [
            models.Index(fields=['recipe', '-version_number']),
        ]

    def __str__(self):
        return f"{self.recipe.title} v{self.version_number}"

    @classmethod
    def create_version(cls, recipe, user, change_summary=""):
        """Factory method to create a new version."""
        # Get next version number
        last_version = cls.objects.filter(recipe=recipe).order_by('-version_number').first()
        version_number = (last_version.version_number + 1) if last_version else 1

        # Snapshot ingredients
        ingredients_snapshot = [
            {
                'name': ing.name,
                'quantity': str(ing.quantity),
                'unit': ing.unit,
                'type': ing.type,
                'notes': ing.notes,
            }
            for ing in recipe.ingredients.all()
        ]

        return cls.objects.create(
            recipe=recipe,
            version_number=version_number,
            title=recipe.title,
            description=recipe.description,
            instructions=recipe.instructions,
            ingredients_snapshot=ingredients_snapshot,
            changed_by=user,
            change_summary=change_summary,
        )