from rest_framework import permissions


class IsPostAuthorOrStaff(permissions.BasePermission):
    """Restricts an action (e.g. hiding a comment) to the blog post's author or staff."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        user = request.user
        return bool(user.is_authenticated and (user.is_staff or obj.post.author_id == user.id))
