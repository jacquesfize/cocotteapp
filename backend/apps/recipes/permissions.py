from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Only the recipe's author, or a staff/admin account, may update, upload an image for,
    or delete it."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.author_id == request.user.id


class IsRecipeAuthorOrStaff(permissions.BasePermission):
    """Restricts an action (e.g. hiding a comment) to the recipe's author or staff."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user.is_authenticated and (user.is_staff or obj.recipe.author_id == user.id))
