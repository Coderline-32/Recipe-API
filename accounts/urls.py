from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserProfileViewSet,
    FollowViewSet,
    FavoritesViewSet,
    MessagingViewSet,
    NotificationsViewSet,
    GDPRDataExportView,
    GDPRAccountDeleteView,
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # User Profile
    path('<int:pk>/', UserProfileViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='user-profile'),

    # Follow/Unfollow
    path('<int:pk>/follow/', FollowViewSet.as_view({'post': 'follow_user', 'delete': 'unfollow_user'}), name='user-follow'),

    # Favorites
    path('<int:user_id>/favorites/', FavoritesViewSet.as_view({'get': 'list_favorites', 'post': 'add_favorite'}), name='user-favorites-list'),
    path('<int:user_id>/favorites/<int:recipe_id>/', FavoritesViewSet.as_view({'delete': 'remove_favorite'}), name='user-favorites-detail'),

    # Messaging
    path('<int:user_id>/messages/', MessagingViewSet.as_view({'get': 'list_messages', 'post': 'send_message'}), name='user-messages-list'),
    path('<int:user_id>/messages/<int:message_id>/', MessagingViewSet.as_view({'get': 'get_or_mark_message', 'put': 'get_or_mark_message'}), name='user-messages-detail'),

    # Notifications
    path('<int:user_id>/notifications/', NotificationsViewSet.as_view({'get': 'list_notifications'}), name='user-notifications-list'),
    path('<int:user_id>/notifications/<int:notif_id>/', NotificationsViewSet.as_view({'put': 'mark_as_read'}), name='user-notifications-detail'),

    # GDPR
    path('gdpr/export/', GDPRDataExportView.as_view(), name='gdpr-export'),
    path('gdpr/delete/', GDPRAccountDeleteView.as_view(), name='gdpr-delete'),
]