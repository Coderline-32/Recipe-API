from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import re
from .models import User, Message, Follow, Favorite, Notification


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with password validation and hashing.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters"
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text="Password confirmation"
    )
    username = serializers.CharField(
        min_length=3,
        max_length=30,
        help_text="Username must be 3-30 characters"
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
        read_only_fields = ['id']

    def validate_username(self, value):
        """Validate username format and uniqueness."""
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError(
                "Username can only contain letters, numbers, hyphens, and underscores."
            )
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate(self, data):
        """Validate password confirmation."""
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        """Create user with hashed password."""
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login with JWT token generation.
    """
    username = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate(self, data):
        """Authenticate user and return tokens."""
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        data['user'] = user
        return data

    def create(self, validated_data):
        """Generate JWT tokens."""
        user = validated_data['user']
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserProfileSerializer(user).data,
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile with read/update capabilities.
    Restricts certain fields to owner only.
    """
    followers_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'bio',
            'profile_picture', 'social_links', 'created_at', 'updated_at',
            'followers_count', 'following_count', 'favorites_count', 'is_following'
        ]
        read_only_fields = ['id', 'username', 'email', 'created_at', 'updated_at']

    def get_followers_count(self, obj):
        """Get follower count."""
        return obj.get_follower_count()

    def get_following_count(self, obj):
        """Get following count."""
        return obj.get_following_count()

    def get_favorites_count(self, obj):
        """Get favorites count."""
        return obj.get_favorites_count()

    def get_is_following(self, obj):
        """Check if current user is following this user."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.is_following(obj)
        return False

    def validate_bio(self, value):
        """Validate bio length."""
        if len(value) > 500:
            raise serializers.ValidationError("Bio cannot exceed 500 characters.")
        return value

    def update(self, instance, validated_data):
        """Update allowed fields only."""
        allowed_fields = ['bio', 'profile_picture', 'social_links', 'first_name', 'last_name']
        for field, value in validated_data.items():
            if field in allowed_fields:
                setattr(instance, field, value)
        instance.save()
        return instance


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for user references in other models.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'profile_picture']
        read_only_fields = fields


class FollowSerializer(serializers.Serializer):
    """
    Serializer for follow/unfollow operations.
    """
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        """Validate user exists."""
        try:
            User.objects.get(pk=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return value

    def validate(self, data):
        """Prevent self-following."""
        request = self.context.get('request')
        if request and request.user.id == data['user_id']:
            raise serializers.ValidationError("Cannot follow yourself.")
        return data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """
    Serializer for managing favorite recipes.
    """
    recipe_detail = serializers.SerializerMethodField()

    class Meta:
        model = Favorite
        fields = ['id', 'recipe', 'recipe_detail', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_recipe_detail(self, obj):
        """Return recipe details if available."""
        try:
            from recipe.serializers import RecipeMinimalSerializer
            return RecipeMinimalSerializer(obj.recipe).data
        except ImportError:
            return None

    def validate_recipe(self, value):
        """Validate recipe exists and is accessible."""
        if value.visibility == 'private' and value.author != self.context['request'].user:
            raise serializers.ValidationError("Cannot favorite this recipe.")
        return value


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for private messages between users.
    """
    sender_detail = UserMinimalSerializer(source='sender', read_only=True)
    receiver_detail = UserMinimalSerializer(source='receiver', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id', 'sender', 'sender_detail', 'receiver', 'receiver_detail',
            'content', 'is_read', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'sender', 'is_read', 'read_at', 'created_at']

    def validate_receiver(self, value):
        """Validate receiver exists and is not sender."""
        request = self.context.get('request')
        if request and value == request.user:
            raise serializers.ValidationError("Cannot send message to yourself.")
        return value

    def validate_content(self, value):
        """Validate message content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        if len(value) > 5000:
            raise serializers.ValidationError("Message is too long (max 5000 characters).")
        return value.strip()

    def create(self, validated_data):
        """Create message with current user as sender."""
        validated_data['sender'] = self.context['request'].user
        return super().create(validated_data)


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for user notifications.
    """
    actor_detail = UserMinimalSerializer(source='actor', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'actor', 'actor_detail',
            'description', 'is_read', 'read_at', 'content_type',
            'object_id', 'created_at'
        ]
        read_only_fields = fields


class UserActivitySerializer(serializers.Serializer):
    """
    Serializer for user activity summary.
    """
    followers = serializers.IntegerField()
    following = serializers.IntegerField()
    favorites = serializers.IntegerField()


class UserDataExportSerializer(serializers.Serializer):
    """
    Serializer for GDPR data export.
    """
    profile = UserProfileSerializer()
    followers = UserMinimalSerializer(many=True)
    following = UserMinimalSerializer(many=True)
    favorites = FavoriteRecipeSerializer(many=True)
    messages_sent = MessageSerializer(many=True)
    notifications = NotificationSerializer(many=True)
    created_at = serializers.DateTimeField()