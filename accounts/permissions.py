from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that allows only the owner or admin to modify their profile.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is owner or admin."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user or request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission that allows only the owner to modify their data.
    """

    def has_object_permission(self, request, view, obj):
        """Check permission."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_staff


class CanFollowUser(permissions.BasePermission):
    """
    Permission that prevents users from following themselves.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check if user is not trying to follow themselves."""
        return obj.id != request.user.id


class CanManageFavorites(permissions.BasePermission):
    """
    Permission that allows authenticated users to manage their favorites.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated


class CanSendMessage(permissions.BasePermission):
    """
    Permission that allows authenticated users to send messages.
    Prevents users from sending messages to themselves.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated


class CanGDPRExportData(permissions.BasePermission):
    """
    Permission that allows users to export only their own data.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated


class CanDeleteAccount(permissions.BasePermission):
    """
    Permission that allows users to delete only their own account.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated