from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
import json
from datetime import datetime

from .models import User, Message, Follow, Favorite, Notification
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    FollowSerializer,
    FavoriteRecipeSerializer,
    MessageSerializer,
    NotificationSerializer,
    UserActivitySerializer,
    UserDataExportSerializer,
    UserMinimalSerializer,
)
from .permissions import (
    IsOwnerOrAdmin,
    CanFollowUser,
    CanManageFavorites,
    CanSendMessage,
    CanGDPRExportData,
    CanDeleteAccount,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for list endpoints."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserRegistrationView(views.APIView):
    """
    API endpoint for user registration.
    POST /users/register/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Register a new user."""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    'message': 'User registered successfully',
                    'user': UserProfileSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(views.APIView):
    """
    API endpoint for user login with JWT token generation.
    POST /users/login/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileViewSet(viewsets.ViewSet):
    """
    ViewSet for user profile management.
    GET /users/<id>/ - Get user profile
    PUT /users/<id>/ - Update user profile (owner only)
    PATCH /users/<id>/ - Partial update user profile (owner only)
    """
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    serializer_class = UserProfileSerializer

    def get_object(self, pk):
        """Get user object."""
        return get_object_or_404(User, pk=pk)

    def retrieve(self, request, pk=None):
        """Get user profile."""
        user = self.get_object(pk)
        self.check_object_permissions(request, user)
        serializer = UserProfileSerializer(user, context={'request': request})
        return Response(serializer.data)

    def update(self, request, pk=None):
        """Update user profile (full update)."""
        user = self.get_object(pk)
        self.check_object_permissions(request, user)
        serializer = UserProfileSerializer(
            user,
            data=request.data,
            partial=False,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Profile updated successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        """Partial update user profile."""
        user = self.get_object(pk)
        self.check_object_permissions(request, user)
        serializer = UserProfileSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    'message': 'Profile updated successfully',
                    'data': serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FollowViewSet(viewsets.ViewSet):
    """
    ViewSet for follow/unfollow operations.
    POST /users/<id>/follow/ - Follow user
    DELETE /users/<id>/follow/ - Unfollow user
    """
    permission_classes = [IsAuthenticated, CanFollowUser]

    def get_object(self, pk):
        """Get user object."""
        return get_object_or_404(User, pk=pk)

    @action(detail=False, methods=['post'], url_path='(?P<pk>\d+)/follow')
    def follow_user(self, request, pk=None):
        """Follow a user."""
        target_user = self.get_object(pk)
        self.check_object_permissions(request, target_user)

        if request.user.follow(target_user):
            # Create notification
            Notification.create_notification(
                user=target_user,
                notification_type='follow',
                description=f"{request.user.username} started following you",
                actor=request.user,
            )
            return Response(
                {
                    'message': f'You are now following {target_user.username}',
                    'user': UserMinimalSerializer(target_user).data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {'message': 'Already following this user'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['delete'], url_path='(?P<pk>\d+)/follow')
    def unfollow_user(self, request, pk=None):
        """Unfollow a user."""
        target_user = self.get_object(pk)
        request.user.unfollow(target_user)
        return Response(
            {'message': f'You unfollowed {target_user.username}'},
            status=status.HTTP_200_OK
        )


class FavoritesViewSet(viewsets.ViewSet):
    """
    ViewSet for managing favorite recipes.
    GET /users/<id>/favorites/ - Get user's favorite recipes
    POST /users/<id>/favorites/ - Add recipe to favorites
    DELETE /users/<id>/favorites/<recipe_id>/ - Remove from favorites
    """
    permission_classes = [IsAuthenticated, CanManageFavorites]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=['get'], url_path='(?P<user_id>\d+)/favorites')
    def list_favorites(self, request, user_id=None):
        """Get user's favorite recipes."""
        user = get_object_or_404(User, pk=user_id)
        favorites = user.favorites.all().order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(favorites, request)
        if page is not None:
            serializer = FavoriteRecipeSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = FavoriteRecipeSerializer(favorites, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='(?P<user_id>\d+)/favorites')
    def add_favorite(self, request, user_id=None):
        """Add recipe to favorites."""
        if request.user.id != int(user_id):
            return Response(
                {'error': 'You can only manage your own favorites'},
                status=status.HTTP_403_FORBIDDEN
            )

        from recipes.models import Recipe
        recipe_id = request.data.get('recipe_id')
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Recipe not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        created = request.user.favorite_recipe(recipe)
        if created:
            return Response(
                {
                    'message': 'Recipe added to favorites',
                    'favorite': FavoriteRecipeSerializer(
                        Favorite.objects.get(user=request.user, recipe=recipe),
                        context={'request': request}
                    ).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'message': 'Recipe already in favorites'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['delete'], url_path='(?P<user_id>\d+)/favorites/(?P<recipe_id>\d+)')
    def remove_favorite(self, request, user_id=None, recipe_id=None):
        """Remove recipe from favorites."""
        if request.user.id != int(user_id):
            return Response(
                {'error': 'You can only manage your own favorites'},
                status=status.HTTP_403_FORBIDDEN
            )

        from recipes.models import Recipe
        try:
            recipe = Recipe.objects.get(pk=recipe_id)
        except Recipe.DoesNotExist:
            return Response(
                {'error': 'Recipe not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        request.user.unfavorite_recipe(recipe)
        return Response(
            {'message': 'Recipe removed from favorites'},
            status=status.HTTP_204_NO_CONTENT
        )


class MessagingViewSet(viewsets.ViewSet):
    """
    ViewSet for private messaging.
    GET /users/<id>/messages/ - Get messages for user
    POST /users/<id>/messages/ - Send message
    """
    permission_classes = [IsAuthenticated, CanSendMessage]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=['get'], url_path='(?P<user_id>\d+)/messages')
    def list_messages(self, request, user_id=None):
        """Get messages for authenticated user."""
        if request.user.id != int(user_id):
            return Response(
                {'error': 'You can only view your own messages'},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = Message.objects.filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(messages, request)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='(?P<user_id>\d+)/messages')
    def send_message(self, request, user_id=None):
        """Send a message to another user."""
        if request.user.id != int(user_id):
            return Response(
                {'error': 'You can only send messages from your own account'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = MessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save()

            # Create notification for receiver
            Notification.create_notification(
                user=message.receiver,
                notification_type='message',
                description=f"New message from {request.user.username}",
                actor=request.user,
                content_type='message',
                object_id=message.id,
            )

            return Response(
                MessageSerializer(message, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get', 'put'], url_path='(?P<user_id>\d+)/messages/(?P<message_id>\d+)')
    def get_or_mark_message(self, request, user_id=None, message_id=None):
        """Get message details or mark as read."""
        if request.user.id != int(user_id):
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        message = get_object_or_404(
            Message.objects.filter(
                Q(pk=message_id) &
                (Q(sender=request.user) | Q(receiver=request.user))
            )
        )


        if request.method == 'GET':
            if message.receiver == request.user:
                message.mark_as_read()
            serializer = MessageSerializer(message, context={'request': request})
            return Response(serializer.data)

        if request.method == 'PUT':
            if message.receiver != request.user:
                return Response(
                    {'error': 'Only receiver can mark message as read'},
                    status=status.HTTP_403_FORBIDDEN
                )
            message.mark_as_read()
            serializer = MessageSerializer(message, context={'request': request})
            return Response(serializer.data)


class NotificationsViewSet(viewsets.ViewSet):
    """
    ViewSet for notifications.
    GET /users/<id>/notifications/ - Get user notifications
    PUT /users/<id>/notifications/<id>/ - Mark notification as read
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    @action(detail=False, methods=['get'], url_path='(?P<user_id>\d+)/notifications')
    def list_notifications(self, request, user_id=None):
        """Get user notifications."""
        if request.user.id != int(user_id):
            return Response(
                {'error': 'You can only view your own notifications'},
                status=status.HTTP_403_FORBIDDEN
            )

        notifications = request.user.notifications.all().order_by('-created_at')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(notifications, request)
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['put'], url_path='(?P<user_id>\d+)/notifications/(?P<notif_id>\d+)')
    def mark_as_read(self, request, user_id=None, notif_id=None):
        """Mark notification as read."""
        if request.user.id != int(user_id):
            return Response(
                {'error': 'Unauthorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        notification = get_object_or_404(Notification, pk=notif_id, user=request.user)
        notification.mark_as_read()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)


class GDPRDataExportView(views.APIView):
    """
    API endpoint for GDPR user data export.
    GET /users/gdpr/export/
    """
    permission_classes = [IsAuthenticated, CanGDPRExportData]

    def get(self, request):
        """Export user data in JSON format."""
        user = request.user
        export_data = {
            'export_date': datetime.now().isoformat(),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'bio': user.bio,
                'social_links': user.social_links,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat(),
            },
            'followers': UserMinimalSerializer(user.followers.all(), many=True).data,
            'following': UserMinimalSerializer(user.follows.all(), many=True).data,
            'favorites': FavoriteRecipeSerializer(user.favorites.all(), many=True, context={'request': request}).data,
            'sent_messages': MessageSerializer(user.sent_messages.all(), many=True, context={'request': request}).data,
            'received_messages': MessageSerializer(user.received_messages.all(), many=True, context={'request': request}).data,
            'notifications': NotificationSerializer(user.notifications.all(), many=True).data,
        }

        return Response(
            export_data,
            status=status.HTTP_200_OK,
            headers={'Content-Disposition': f'attachment; filename="{user.username}_data_export.json"'}
        )


class GDPRAccountDeleteView(views.APIView):
    """
    API endpoint for GDPR account deletion (right to be forgotten).
    DELETE /users/gdpr/delete/
    """
    permission_classes = [IsAuthenticated, CanDeleteAccount]

    def delete(self, request):
        """Delete user account and all related data."""
        user = request.user
        username = user.username

        # Delete profile picture if exists
        if user.profile_picture:
            user.profile_picture.delete()

        # Delete user account (cascading deletes will handle related data)
        user.delete()

        return Response(
            {'message': f'Account {username} has been deleted. All personal data has been removed.'},
            status=status.HTTP_204_NO_CONTENT
        )