from django.contrib import admin
from django.utils.html import format_html
from .models import Recipe, Ingredient, Tag, Comment, Rating, RecipeImage, RecipeVersion


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for Tag model."""
    list_display = ('name', 'type', 'slug', 'recipe_count_display', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'recipe_count_display')

    fieldsets = (
        (None, {'fields': ('name', 'type', 'slug')}),
        ('Details', {'fields': ('description',)}),
        ('Statistics', {'fields': ('recipe_count_display',)}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def recipe_count_display(self, obj):
        """Display recipe count."""
        count = obj.get_recipe_count()
        return format_html(
            '<span style="background-color: #e3f2fd; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    recipe_count_display.short_description = 'Recipes'


class IngredientInline(admin.TabularInline):
    """Inline admin for ingredients."""
    model = Ingredient
    extra = 1
    fields = ('name', 'quantity', 'unit', 'type', 'notes')


class RecipeImageInline(admin.TabularInline):
    """Inline admin for recipe images."""
    model = RecipeImage
    extra = 1
    fields = ('image', 'image_type', 'step_number', 'caption', 'order')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Admin for Recipe model."""
    list_display = (
        'title',
        'author',
        'difficulty',
        'cook_time',
        'visibility',
        'average_rating_display',
        'view_count',
        'created_at'
    )
    list_filter = ('difficulty', 'visibility', 'created_at', 'author')
    search_fields = ('title', 'description', 'author__username')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = (
        'slug', 'average_rating', 'total_ratings', 'view_count',
        'created_at', 'updated_at', 'featured_image_preview'
    )
    inlines = [IngredientInline, RecipeImageInline]
    filter_horizontal = ('tags',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'author', 'description')
        }),
        ('Cooking Details', {
            'fields': ('serving_size', 'cook_time', 'prep_time', 'difficulty', 'equipment', 'instructions', 'tips')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_preview', 'video_url')
        }),
        ('Nutrition', {
            'fields': ('nutrition_info',),
            'classes': ('collapse',)
        }),
        ('Status & Visibility', {
            'fields': ('visibility',)
        }),
        ('Statistics', {
            'fields': ('average_rating', 'total_ratings', 'view_count'),
            'classes': ('collapse',)
        }),
        ('Tags', {
            'fields': ('tags',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def average_rating_display(self, obj):
        """Display average rating."""
        if obj.total_ratings > 0:
            return format_html(
                '<span>⭐ {:.1f} ({} ratings)</span>',
                obj.average_rating,
                obj.total_ratings
            )
        return '—'
    average_rating_display.short_description = 'Rating'

    def featured_image_preview(self, obj):
        """Display featured image preview."""
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 10px;" />',
                obj.featured_image.url
            )
        return 'No image'
    featured_image_preview.short_description = 'Preview'


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Admin for Ingredient model."""
    list_display = ('name', 'recipe', 'quantity', 'unit', 'type', 'created_at')
    list_filter = ('type', 'unit', 'created_at')
    search_fields = ('name', 'recipe__title')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Ingredient Details', {
            'fields': ('recipe', 'name', 'quantity', 'unit', 'type', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin for Comment model."""
    list_display = ('user', 'recipe', 'is_approved', 'is_spam', 'created_at', 'content_preview')
    list_filter = ('is_approved', 'is_spam', 'created_at')
    search_fields = ('user__username', 'recipe__title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_comments', 'mark_as_spam']

    fieldsets = (
        ('Comment Details', {
            'fields': ('recipe', 'user', 'content')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_spam')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        """Display truncated content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def approve_comments(self, request, queryset):
        """Admin action to approve comments."""
        queryset.update(is_approved=True)
    approve_comments.short_description = 'Approve selected comments'

    def mark_as_spam(self, request, queryset):
        """Admin action to mark as spam."""
        queryset.update(is_spam=True)
    mark_as_spam.short_description = 'Mark selected as spam'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """Admin for Rating model."""
    list_display = ('user', 'recipe', 'rating_display', 'created_at')
    list_filter = ('rating', 'created_at', 'is_spam')
    search_fields = ('user__username', 'recipe__title', 'review')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Rating Details', {
            'fields': ('recipe', 'user', 'rating', 'review')
        }),
        ('Moderation', {
            'fields': ('is_spam',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def rating_display(self, obj):
        """Display rating with stars."""
        return format_html(
            '<span style="color: gold; font-size: 16px;">{"⭐" * obj.rating}</span>'
        )
    rating_display.short_description = 'Rating'


@admin.register(RecipeImage)
class RecipeImageAdmin(admin.ModelAdmin):
    """Admin for RecipeImage model."""
    list_display = ('recipe', 'image_type', 'step_number', 'order', 'image_thumbnail', 'uploaded_at')
    list_filter = ('image_type', 'uploaded_at')
    search_fields = ('recipe__title', 'caption')
    readonly_fields = ('uploaded_at', 'image_preview')

    fieldsets = (
        ('Image Details', {
            'fields': ('recipe', 'image', 'image_preview', 'image_type', 'step_number', 'caption', 'order')
        }),
        ('Timestamps', {
            'fields': ('uploaded_at',),
            'classes': ('collapse',)
        }),
    )

    def image_thumbnail(self, obj):
        """Display image thumbnail."""
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return '—'
    image_thumbnail.short_description = 'Image'

    def image_preview(self, obj):
        """Display larger image preview."""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 10px;" />',
                obj.image.url
            )
        return 'No image'
    image_preview.short_description = 'Preview'


@admin.register(RecipeVersion)
class RecipeVersionAdmin(admin.ModelAdmin):
    """Admin for RecipeVersion model."""
    list