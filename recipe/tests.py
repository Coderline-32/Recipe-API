from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from decimal import Decimal
from datetime import datetime

from .models import Recipe, Ingredient, Tag, Comment, Rating, RecipeImage, RecipeVersion
from accounts.models import Notification

User = get_user_model()


class TagModelTestCase(TestCase):
    """Test cases for Tag model."""

    def setUp(self):
        """Set up test data."""
        self.tag = Tag.objects.create(
            name='Vegan',
            type='dietary',
            description='Vegan recipes'
        )

    def test_tag_creation(self):
        """Test tag creation."""
        self.assertEqual(self.tag.name, 'Vegan')
        self.assertEqual(self.tag.type, 'dietary')

    def test_tag_slug_generation(self):
        """Test automatic slug generation."""
        self.assertEqual(self.tag.slug, 'vegan')

    def test_tag_string_representation(self):
        """Test tag string representation."""
        self.assertEqual(str(self.tag), 'Vegan (Dietary Restriction)')

    def test_tag_unique_name(self):
        """Test that tag names are unique."""
        with self.assertRaises(Exception):
            Tag.objects.create(name='Vegan', type='dietary')

    def test_tag_recipe_count(self):
        """Test recipe count for tag."""
        user = User.objects.create_user(
            username='chef',
            email='chef@example.com',
            password='testpass123'
        )
        recipe = Recipe.objects.create(
            title='Vegan Pasta',
            author=user,
            cook_time=20,
            visibility='public',
            instructions=[]
        )
        recipe.tags.add(self.tag)
        self.assertEqual(self.tag.get_recipe_count(), 1)


class RecipeModelTestCase(TestCase):
    """Test cases for Recipe model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='chef',
            email='chef@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Pasta Carbonara',
            description='Classic Italian pasta',
            author=self.user,
            serving_size=4,
            cook_time=20,
            prep_time=15,
            difficulty='easy',
            visibility='draft',
            instructions=['Cook pasta', 'Mix sauce', 'Combine'],
        )

    def test_recipe_creation(self):
        """Test recipe creation."""
        self.assertEqual(self.recipe.title, 'Pasta Carbonara')
        self.assertEqual(self.recipe.author, self.user)
        self.assertEqual(self.recipe.visibility, 'draft')
        self.assertEqual(self.recipe.average_rating, 0.0)

    def test_recipe_slug_generation(self):
        """Test automatic slug generation."""
        self.assertEqual(self.recipe.slug, 'pasta-carbonara')

    def test_recipe_unique_slug(self):
        """Test that recipe slugs are unique."""
        with self.assertRaises(Exception):
            Recipe.objects.create(
                title='Pasta Carbonara',
                author=self.user,
                cook_time=20,
                instructions=[]
            )

    def test_total_cook_time(self):
        """Test total cook time calculation."""
        total = self.recipe.get_total_time()
        self.assertEqual(total, 35)

    def test_is_owned_by(self):
        """Test recipe ownership check."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        self.assertTrue(self.recipe.is_owned_by(self.user))
        self.assertFalse(self.recipe.is_owned_by(other_user))

    def test_is_public(self):
        """Test public visibility check."""
        self.assertFalse(self.recipe.is_public())
        self.recipe.visibility = 'public'
        self.recipe.save()
        self.assertTrue(self.recipe.is_public())

    def test_increment_view_count(self):
        """Test incrementing view count."""
        initial_count = self.recipe.view_count
        self.recipe.increment_view_count()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.view_count, initial_count + 1)

    def test_update_rating_with_no_ratings(self):
        """Test rating update with no ratings."""
        self.recipe.update_rating()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.average_rating, 0.0)
        self.assertEqual(self.recipe.total_ratings, 0)

    def test_update_rating_with_ratings(self):
        """Test rating update with actual ratings."""
        Rating.objects.create(user=self.user, recipe=self.recipe, rating=5)
        Rating.objects.create(
            user=User.objects.create_user(
                username='user2',
                email='user2@example.com',
                password='testpass123'
            ),
            recipe=self.recipe,
            rating=3
        )
        self.recipe.update_rating()
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.average_rating, 4.0)
        self.assertEqual(self.recipe.total_ratings, 2)

    def test_get_ingredients(self):
        """Test getting recipe ingredients."""
        Ingredient.objects.create(
            recipe=self.recipe,
            name='Pasta',
            quantity=Decimal('500'),
            unit='g'
        )
        ingredients = self.recipe.get_ingredients()
        self.assertEqual(ingredients.count(), 1)

    def test_scale_ingredients(self):
        """Test scaling ingredients to different serving size."""
        Ingredient.objects.create(
            recipe=self.recipe,
            name='Pasta',
            quantity=Decimal('500'),
            unit='g'
        )
        Ingredient.objects.create(
            recipe=self.recipe,
            name='Eggs',
            quantity=Decimal('4'),
            unit='units'
        )
        scaled = self.recipe.get_ingredients_scaled(8)
        self.assertEqual(len(scaled), 2)
        self.assertEqual(float(scaled[0]['quantity']), 1000.0)  # 500 * 2
        self.assertEqual(float(scaled[1]['quantity']), 8.0)  # 4 * 2

    def test_scale_ingredients_invalid_serving_size(self):
        """Test scaling with invalid serving size."""
        with self.assertRaises(ValueError):
            self.recipe.get_ingredients_scaled(0)

    def test_recipe_visibility_choices(self):
        """Test recipe visibility options."""
        for visibility, _ in Recipe.VISIBILITY_CHOICES:
            recipe = Recipe.objects.create(
                title=f'Recipe {visibility}',
                author=self.user,
                cook_time=20,
                visibility=visibility,
                instructions=[]
            )
            self.assertEqual(recipe.visibility, visibility)


class IngredientModelTestCase(TestCase):
    """Test cases for Ingredient model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='chef',
            email='chef@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Pasta',
            author=self.user,
            cook_time=20,
            instructions=[]
        )
        self.ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name='Pasta',
            quantity=Decimal('500'),
            unit='g',
            type='main',
            notes='al dente'
        )

    def test_ingredient_creation(self):
        """Test ingredient creation."""
        self.assertEqual(self.ingredient.name, 'Pasta')
        self.assertEqual(self.ingredient.recipe, self.recipe)
        self.assertEqual(self.ingredient.quantity, Decimal('500'))
        self.assertEqual(self.ingredient.unit, 'g')

    def test_ingredient_string_representation(self):
        """Test ingredient string representation."""
        self.assertEqual(str(self.ingredient), '500 g Pasta')

    def test_ingredient_scaling(self):
        """Test ingredient quantity scaling."""
        scaled = self.ingredient.scale(Decimal('2'))
        self.assertEqual(scaled, Decimal('1000'))

    def test_ingredient_display_quantity(self):
        """Test quantity display formatting."""
        # Test with decimal
        self.ingredient.quantity = Decimal('500.50')
        display = self.ingredient.get_display_quantity()
        self.assertEqual(display, '500.5')

        # Test with trailing zeros
        self.ingredient.quantity = Decimal('500.00')
        display = self.ingredient.get_display_quantity()
        self.assertEqual(display, '500')

    def test_ingredient_full_name_with_notes(self):
        """Test full ingredient name with notes."""
        full_name = self.ingredient.get_full_name()
        self.assertEqual(full_name, 'Pasta (al dente)')

    def test_ingredient_full_name_without_notes(self):
        """Test full ingredient name without notes."""
        self.ingredient.notes = ''
        self.ingredient.save()
        full_name = self.ingredient.get_full_name()
        self.assertEqual(full_name, 'Pasta')

    def test_ingredient_types(self):
        """Test all ingredient types."""
        for ingredient_type, _ in Ingredient.INGREDIENT_TYPES:
            ingredient = Ingredient.objects.create(
                recipe=self.recipe,
                name=f'Ingredient {ingredient_type}',
                quantity=Decimal('100'),
                unit='g',
                type=ingredient_type
            )
            self.assertEqual(ingredient.type, ingredient_type)


class CommentModelTestCase(TestCase):
    """Test cases for Comment model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='testpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            author=self.author,
            cook_time=30,
            visibility='public',
            instructions=[]
        )
        self.comment = Comment.objects.create(
            recipe=self.recipe,
            user=self.user,
            content='Great recipe!'
        )

    def test_comment_creation(self):
        """Test comment creation."""
        self.assertEqual(self.comment.content, 'Great recipe!')
        self.assertEqual(self.comment.user, self.user)
        self.assertEqual(self.comment.recipe, self.recipe)
        self.assertFalse(self.comment.is_spam)
        self.assertTrue(self.comment.is_approved)

    def test_comment_string_representation(self):
        """Test comment string representation."""
        expected = f"Comment by {self.user.username} on {self.recipe.title}"
        self.assertEqual(str(self.comment), expected)

    def test_comment_timestamps(self):
        """Test comment timestamp fields."""
        self.assertIsNotNone(self.comment.created_at)
        self.assertIsNotNone(self.comment.updated_at)

    def test_multiple_comments_on_recipe(self):
        """Test multiple comments on same recipe."""
        user2 = User.objects.create_user(
            username='commenter2',
            email='commenter2@example.com',
            password='testpass123'
        )
        comment2 = Comment.objects.create(
            recipe=self.recipe,
            user=user2,
            content='Also great!'
        )
        comments = self.recipe.comments.all()
        self.assertEqual(comments.count(), 2)


class RatingModelTestCase(TestCase):
    """Test cases for Rating model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='rater',
            email='rater@example.com',
            password='testpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            author=self.author,
            cook_time=30,
            visibility='public',
            instructions=[]
        )
        self.rating = Rating.objects.create(
            user=self.user,
            recipe=self.recipe,
            rating=5,
            review='Excellent recipe!'
        )

    def test_rating_creation(self):
        """Test rating creation."""
        self.assertEqual(self.rating.rating, 5)
        self.assertEqual(self.rating.review, 'Excellent recipe!')
        self.assertEqual(self.rating.user, self.user)
        self.assertEqual(self.rating.recipe, self.recipe)

    def test_rating_string_representation(self):
        """Test rating string representation."""
        expected = f"5⭐ by {self.user.username} on {self.recipe.title}"
        self.assertEqual(str(self.rating), expected)

    def test_one_rating_per_user_per_recipe(self):
        """Test unique constraint on user-recipe pair."""
        with self.assertRaises(Exception):
            Rating.objects.create(
                user=self.user,
                recipe=self.recipe,
                rating=4
            )

    def test_rating_values(self):
        """Test rating values 1-5."""
        for rating_value in range(1, 6):
            rating = Rating.objects.create(
                user=User.objects.create_user(
                    username=f'user{rating_value}',
                    email=f'user{rating_value}@example.com',
                    password='testpass123'
                ),
                recipe=self.recipe,
                rating=rating_value
            )
            self.assertEqual(rating.rating, rating_value)

    def test_invalid_rating_values(self):
        """Test that invalid rating values are rejected."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        recipe = Recipe.objects.create(
            title='Test',
            author=self.author,
            cook_time=20,
            instructions=[]
        )
        # Rating below 1 should be invalid
        with self.assertRaises(Exception):
            Rating.objects.create(
                user=user,
                recipe=recipe,
                rating=0
            )

        # Rating above 5 should be invalid
        with self.assertRaises(Exception):
            Rating.objects.create(
                user=user,
                recipe=recipe,
                rating=6
            )


class RecipeVersionTestCase(TestCase):
    """Test cases for RecipeVersion model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='chef',
            email='chef@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Pasta',
            author=self.user,
            cook_time=20,
            instructions=['Cook', 'Serve']
        )

    def test_create_version(self):
        """Test creating a recipe version."""
        version = RecipeVersion.create_version(
            self.recipe,
            self.user,
            'Initial version'
        )
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.recipe, self.recipe)
        self.assertEqual(version.changed_by, self.user)

    def test_version_increments(self):
        """Test that version numbers increment."""
        version1 = RecipeVersion.create_version(self.recipe, self.user, 'v1')
        version2 = RecipeVersion.create_version(self.recipe, self.user, 'v2')
        self.assertEqual(version1.version_number, 1)
        self.assertEqual(version2.version_number, 2)

    def test_version_snapshots_ingredients(self):
        """Test that version captures ingredient snapshot."""
        Ingredient.objects.create(
            recipe=self.recipe,
            name='Pasta',
            quantity=Decimal('500'),
            unit='g'
        )
        version = RecipeVersion.create_version(self.recipe, self.user, 'v1')
        self.assertEqual(len(version.ingredients_snapshot), 1)
        self.assertEqual(version.ingredients_snapshot[0]['name'], 'Pasta')


class RecipeImageTestCase(TestCase):
    """Test cases for RecipeImage model."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='chef',
            email='chef@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Pasta',
            author=self.user,
            cook_time=20,
            instructions=[]
        )

    def test_recipe_image_creation(self):
        """Test recipe image creation."""
        image = RecipeImage.objects.create(
            recipe=self.recipe,
            image='test.jpg',
            image_type='gallery',
            caption='Finished dish'
        )
        self.assertEqual(image.recipe, self.recipe)
        self.assertEqual(image.image_type, 'gallery')

    def test_recipe_image_ordering(self):
        """Test recipe images are ordered."""
        img1 = RecipeImage.objects.create(
            recipe=self.recipe,
            image='img1.jpg',
            order=1
        )
        img2 = RecipeImage.objects.create(
            recipe=self.recipe,
            image='img2.jpg',
            order=2
        )
        images = self.recipe.images.all()
        self.assertEqual(images[0].id, img1.id)
        self.assertEqual(images[1].id, img2.id)


class RecipeAPITestCase(APITestCase):
    """Test cases for Recipe API endpoints."""

    def setUp(self):
        """Set up test client and data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='chef',
            email='chef@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otherchef',
            email='other@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Pasta Carbonara',
            description='Classic Italian pasta',
            author=self.user,
            serving_size=4,
            cook_time=20,
            difficulty='easy',
            visibility='public',
            instructions=['Cook pasta', 'Mix sauce'],
        )
        self.tag = Tag.objects.create(name='Italian', type='cuisine')
        self.recipe.tags.add(self.tag)

    def test_list_public_recipes(self):
        """Test listing public recipes."""
        response = self.client.get('/api/v1/recipes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_create_recipe_authenticated(self):
        """Test creating recipe as authenticated user."""
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'New Recipe',
            'description': 'A new recipe',
            'cook_time': 30,
            'serving_size': 2,
            'difficulty': 'easy',
            'instructions': ['Step 1', 'Step 2'],
            'tag_ids': []
        }
        response = self.client.post('/api/v1/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Recipe.objects.filter(title='New Recipe').exists())

    def test_create_recipe_anonymous(self):
        """Test that anonymous users cannot create recipes."""
        data = {
            'title': 'New Recipe',
            'cook_time': 30,
            'instructions': []
        }
        response = self.client.post('/api/v1/recipes/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_public_recipe(self):
        """Test retrieving a public recipe."""
        response = self.client.get(f'/api/v1/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Pasta Carbonara')

    def test_update_own_recipe(self):
        """Test updating own recipe."""
        self.client.force_authenticate(user=self.user)
        data = {'description': 'Updated description'}
        response = self.client.patch(f'/api/v1/recipes/{self.recipe.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.description, 'Updated description')

    def test_cannot_update_others_recipe(self):
        """Test that user cannot update others' recipes."""
        self.client.force_authenticate(user=self.other_user)
        data = {'description': 'Hacked'}
        response = self.client.patch(f'/api/v1/recipes/{self.recipe.id}/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_recipe(self):
        """Test deleting own recipe."""
        recipe_id = self.recipe.id
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(f'/api/v1/recipes/{recipe_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe_id).exists())

    def test_cannot_delete_others_recipe(self):
        """Test that user cannot delete others' recipes."""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(f'/api/v1/recipes/{self.recipe.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_publish_draft_recipe(self):
        """Test publishing a draft recipe."""
        draft_recipe = Recipe.objects.create(
            title='Draft Recipe',
            author=self.user,
            cook_time=20,
            visibility='draft',
            instructions=[]
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/recipes/{draft_recipe.id}/publish/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        draft_recipe.refresh_from_db()
        self.assertEqual(draft_recipe.visibility, 'public')

    def test_cannot_publish_already_public_recipe(self):
        """Test that already public recipes cannot be published again."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/publish/', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_scale_ingredients_endpoint(self):
        """Test ingredient scaling endpoint."""
        Ingredient.objects.create(
            recipe=self.recipe,
            name='Pasta',
            quantity=Decimal('500'),
            unit='g'
        )
        self.client.force_authenticate(user=self.user)
        data = {'new_serving_size': 8}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/scale-ingredients/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('scaled_ingredients', response.data)

    def test_recipe_stats_endpoint(self):
        """Test recipe stats endpoint."""
        response = self.client.get(f'/api/v1/recipes/{self.recipe.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_views', response.data)
        self.assertIn('average_rating', response.data)

    def test_trending_recipes_endpoint(self):
        """Test trending recipes endpoint."""
        response = self.client.get('/api/v1/recipes/trending/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_advanced_endpoint(self):
        """Test advanced search endpoint."""
        response = self.client.get('/api/v1/recipes/search-advanced/?search=Pasta&difficulty=easy')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_recipe_versions_endpoint(self):
        """Test recipe versions endpoint."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/v1/recipes/{self.recipe.id}/versions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CommentAPITestCase(APITestCase):
    """Test cases for Comment API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='commenter',
            email='commenter@example.com',
            password='testpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            author=self.author,
            cook_time=30,
            visibility='public',
            instructions=[]
        )

    def test_create_comment_authenticated(self):
        """Test creating a comment as authenticated user."""
        self.client.force_authenticate(user=self.user)
        data = {'content': 'Great recipe!'}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Comment.objects.filter(content='Great recipe!').exists())

    def test_create_comment_anonymous(self):
        """Test that anonymous users cannot create comments."""
        data = {'content': 'Great recipe!'}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_comments(self):
        """Test listing comments for a recipe."""
        Comment.objects.create(
            recipe=self.recipe,
            user=self.user,
            content='Great!'
        )
        response = self.client.get(f'/api/v1/recipes/{self.recipe.id}/comments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_comment_empty_content_validation(self):
        """Test that empty comments are rejected."""
        self.client.force_authenticate(user=self.user)
        data = {'content': '   '}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_too_long_validation(self):
        """Test that very long comments are rejected."""
        self.client.force_authenticate(user=self.user)
        data = {'content': 'x' * 5001}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RatingAPITestCase(APITestCase):
    """Test cases for Rating API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='rater',
            email='rater@example.com',
            password='testpass123'
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            author=self.author,
            cook_time=30,
            visibility='public',
            instructions=[]
        )

    def test_create_rating_authenticated(self):
        """Test creating a rating as authenticated user."""
        self.client.force_authenticate(user=self.user)
        data = {'rating': 5, 'review': 'Excellent!'}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/ratings/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_rating_anonymous(self):
        """Test that anonymous users cannot rate."""
        data = {'rating': 5}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/ratings/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_rating(self):
        """Test updating a rating."""
        self.client.force_authenticate(user=self.user)
        # Create initial rating
        data = {'rating': 3}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/ratings/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Update rating
        data = {'rating': 5}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/ratings/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify only one rating exists
        self.assertEqual(Rating.objects.filter(user=self.user, recipe=self.recipe).count(), 1)

    def test_invalid_rating_value(self):
        """Test that invalid rating values are rejected."""
        self.client.force_authenticate(user=self.user)
        data = {'rating': 10}
        response = self.client.post(f'/api/v1/recipes/{self.recipe.id}/ratings/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recipe_average_rating_updated(self):
        """Test that recipe average rating is updated after rating."""
        self.client.force_authenticate(user=self.user)
        data = {'rating': 5}
        self.client.post(f'/api/v1/recipes/{self.recipe.id}/ratings/', data, format='json')

        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.average_rating, 5.0)
        self.assertEqual(self.recipe.total_ratings, 1)

    def test_list_ratings(self):
        """Test listing ratings for a recipe."""
        Rating.objects.create(
            user=self.user,
            recipe=self.recipe,
            rating=5
        )
        response = self.client.get(f'/api/v1/recipes/{self.recipe.id}/ratings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class TagAPITestCase(APITestCase):
    """Test cases for Tag API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.tag = Tag.objects.create(
            name='Vegan',
            type='dietary'
        )

    def test_list_tags(self):
        """Test listing tags."""
        response = self.client.get('/tags/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_retrieve_tag(self):
        """Test retrieving a tag by slug."""
        response = self.client.get(f'/tags/{self.tag.slug}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Vegan')

    def test_search_tags(self):
        """Test searching tags."""
        response = self.client.get('/tags/?search=Vegan')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)


class IngredientAPITestCase(APITestCase):
    """Test cases for Ingredient API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='chef',
            email='chef@example.com',
            password='testpass123'
        )
        self.recipe = Recipe.objects.create(
            title='Test Recipe',
            author=self.user,
            cook_time=20,
            instructions=[]
        )
        self.ingredient = Ingredient.objects.create(
            recipe=self.recipe,
            name='Pasta',
            quantity=Decimal('500'),
            unit='g'
        )

    def test_list_ingredients(self):
        """Test listing ingredients."""
        response = self.client.get('/ingredients/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)

    def test_retrieve_ingredient(self):
        """Test retrieving an ingredient."""
        response = self.client.get(f'/ingredients/{self.ingredient.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Pasta')

    def test_search_ingredients(self):
        """Test searching ingredients."""
        response = self.client.get('/ingredients/?search=Pasta')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)