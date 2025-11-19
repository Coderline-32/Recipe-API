from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.utils import timezone
import json


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser with recipe API specific fields.
    """
    username = models.CharField(
        max_length=30,
        unique=True,
        validators=[MinLengthValidator(3)],
        help_text="3-30 characters, unique username for login"
    )
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        null=True,
        blank=True,
        help_text="User's profile picture"
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        default="",
        help_text="User biography (max 500 characters)"
    )
    social_links = models.JSONField(
        default=dict,
        blank=True,
        help_text="Social media links as JSON (e.g., {'twitter': 'link', 'instagram': 'link'})"
    )
    follows = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='followers',
        blank=True,
        help_text="Users that this user follows"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.username} ({self.email})"

    def get_full_name(self):
        """Return user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.username

    def follow(self, user):
        """Follow another user."""
        if user != self:
            self.follows.add(user)
            return True
        return False

    def unfollow(self, user):
        """Unfollow another user."""
        self.follows.remove(user)

    def is_following(self, user):
        """Check if following another user."""
        return self.follows.filter(pk=user.pk).exists()

    def get_follower_count(self):
        """Get number of followers."""
        return self.followers.count()

    def get_following_count(self):
        """Get number of users this user follows."""
        return self.follows.count()

    def favorite_recipe(self, recipe):
        """Add recipe to favorites."""
        favorite, created = Favorite.objects.get_or_create(user=self, recipe=recipe)
        return created

    def unfavorite_recipe(self, recipe):
        """Remove recipe from favorites."""
        Favorite.objects.filter(user=self, recipe=recipe).delete()

    def is_favorite(self, recipe):
        """Check if recipe is in favorites."""
        return Favorite.objects.filter(user=self, recipe=recipe).exists()

    def get_favorites_count(self):
        """Get number of favorite recipes."""
        return self.favorites.count()

    def get_activity_summary(self):
        """Get user activity summary."""
        return {
            'followers': self.get_follower_count(),
            'following': self.get_following_count(),
            'favorites': self.get_favorites_count(),
        }


class Follow(models.Model):
    """
    Model for managing user follow relationships.
    """
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_follows'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_followers'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_follow'
        unique_together = ('follower', 'following')
        verbose_name = 'Follow'
        verbose_name_plural = 'Follows'
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

    def save(self, *args, **kwargs):
        """Prevent user from following themselves."""
        if self.follower == self.following:
            raise ValueError("Users cannot follow themselves")
        super().save(*args, **kwargs)


class Message(models.Model):
    """
    Model for private messaging between users.
    """
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_message'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sender', 'receiver', '-created_at']),
            models.Index(fields=['receiver', 'is_read']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"

    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    def get_conversation_key(self):
        """Get unique key for conversation between two users."""
        user_ids = sorted([self.sender.id, self.receiver.id])
        return f"conversation_{user_ids[0]}_{user_ids[1]}"


class Favorite(models.Model):
    """
    Model for managing user's favorite recipes.
    Uses a generic ForeignKey relationship to Recipe model.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_favorite'
        unique_together = ('user', 'recipe')
        verbose_name = 'Favorite'
        verbose_name_plural = 'Favorites'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['recipe']),
        ]

    def __str__(self):
        return f"{self.user.username} favorited {self.recipe.title}"


class Notification(models.Model):
    """
    Model for user notifications.
    Tracks various notification types (new message, new follower, recipe update, etc.)
    """
    NOTIFICATION_TYPES = (
        ('message', 'New Message'),
        ('follow', 'New Follower'),
        ('recipe_update', 'Recipe Updated'),
        ('comment', 'New Comment'),
        ('like', 'Recipe Liked'),
        ('mention', 'Mentioned'),
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications_created',
        null=True,
        blank=True
    )
    description = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    content_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of related object (e.g., 'recipe', 'message')"
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_notification'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.description}"

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])

    @classmethod
    def create_notification(cls, user, notification_type, description, actor=None, content_type=None, object_id=None):
        """Factory method to create notifications."""
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            description=description,
            actor=actor,
            content_type=content_type,
            object_id=object_id,
        )