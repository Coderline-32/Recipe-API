from rest_framework import permissions


class IsRecipeAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission that allows only recipe author to edit/delete.
    Others can only read.
    """

    def has_object_permission(self, request, view, obj):
        """Check if user is recipe author."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff


class IsPublicOrAuthor(permissions.BasePermission):
    """
    Permission to view recipes:
    - Public recipes can be viewed by anyone
    - Private/draft recipes only by author
    """

    def has_object_permission(self, request, view, obj):
        """Check visibility and ownership."""
        if obj.visibility == 'public':
            return True
        if request.user and request.user.is_authenticated:
            return obj.author == request.user
        return False


class CanCommentOrReadOnly(permissions.BasePermission):
    """
    Permission to comment on recipes.
    Only authenticated users can comment.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated for comment actions."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated


class CanRateRecipe(permissions.BasePermission):
    """
    Permission to rate recipes.
    Only authenticated users can rate.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated


class CanManageRecipes(permissions.BasePermission):
    """
    Permission to create and manage recipes.
    Only authenticated users can create recipes.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated