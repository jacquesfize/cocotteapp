from rest_framework import permissions


class CanEditLibraryItem(permissions.BasePermission):
    """Modification/suppression d'un élément d'une bibliothèque partagée (ingrédient, matériel) :
    délègue à `can_be_edited_by` du modèle, qui porte la règle (staff, ou créateur d'un élément
    non vérifié que personne d'autre n'utilise)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.can_be_edited_by(request.user)
