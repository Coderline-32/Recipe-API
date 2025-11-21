"""
Main URL configuration for Recipe API project.

This module defines the primary URL patterns for the Django application,
including admin, API endpoints, and media serving.
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

# Health check endpoint
class HealthCheckView(APIView):
    """Simple health check endpoint."""
    def get(self, request):
        """Return API health status."""

        permission_classes = [AllowAny]
        
        return Response(
            {
                'status': 'ok',
                'message': 'Recipe API is running',
                'version': '1.0.0'
            },
            status=status.HTTP_200_OK
        )


class StatusView(APIView):
    """API status endpoint."""
    def get(self, request):
        """Return API status information."""
        return Response(
            {
                'name': 'Recipe API',
                'version': '1.0.0',
                'environment': 'production' if not settings.DEBUG else 'development',
                'database': 'connected',
                'cache': 'configured',
            },
            status=status.HTTP_200_OK
        )


# URL patterns
urlpatterns = [
    # ============================================================================
    # ADMIN
    # ============================================================================
    path('admin/', admin.site.urls),

    # ============================================================================
    # HEALTH & STATUS
    # ============================================================================
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('status/', StatusView.as_view(), name='status'),

    # ============================================================================
    # API - AUTHENTICATION & TOKENS
    # ============================================================================
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ============================================================================
    # API - USERS
    # ============================================================================
    path('api/v1/users/', include('accounts.urls', namespace='users')),

    # ============================================================================
    # API - RECIPES
    # ============================================================================
    path('api/v1/recipes/', include('recipe.urls', namespace='recipes')),

    # ============================================================================
    # API DOCUMENTATION
    # ============================================================================
    # OpenAPI 3.0 schema
    #path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
   # path(
    #    'api/v1/docs/',
    #    SpectacularSwaggerView.as_view(url_name='schema'),
    #    name='swagger-ui'
    #),

    # ReDoc
    #path(
     #   'api/v1/docs/redoc/',
     #   SpectacularRedocView.as_view(url_name='schema'),
     #   name='redoc'
    #),
]

# ============================================================================
# MEDIA & STATIC FILES (Development Only)
# ============================================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# ============================================================================
# ADMIN CUSTOMIZATION
# ============================================================================
admin.site.site_header = "Recipe API Admin"
admin.site.site_title = "Recipe API Administration"
admin.site.index_title = "Welcome to Recipe API Administration"