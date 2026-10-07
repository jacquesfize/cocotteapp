from .models import AuditLog

ERASED_LABEL = "compte supprimé"


def record_staff_action(request, action, obj, *, details=None, owner_field=None, pk=None, label=None):
    """Journalise une action d'un compte staff sur `obj`. Ne fait rien pour un utilisateur non
    staff, ni quand `obj` appartient à l'acteur (`owner_field` : nom de la FK vers l'auteur ;
    `None` = toujours journaliser, pour les objets sans propriétaire comme les comptes).

    `pk` et `label` servent aux suppressions, où `obj` a déjà perdu son identité. Un compte
    n'est jamais désigné par son e-mail ou son nom (donnée personnelle) mais par son id."""
    user = request.user
    if not (user and user.is_authenticated and user.is_staff):
        return None
    if owner_field and getattr(obj, f"{owner_field}_id", None) == user.id:
        return None
    pk = obj.pk if pk is None else pk
    if obj._meta.label == "accounts.User":
        label = f"user #{pk}"
    elif label is None:
        label = str(obj)
    return AuditLog.objects.create(
        actor=user,
        actor_label=user.email,
        action=action,
        target_type=obj._meta.label,
        target_id=str(pk) if pk is not None else "",
        target_label=label[:255],
        details=details or {},
    )


def erase_actor(user):
    """Droit à l'effacement : retire l'e-mail du staff `user` des lignes qu'il a produites
    (à appeler avant la suppression du compte). Les lignes elles-mêmes restent, anonymisées."""
    AuditLog.objects.filter(actor=user).update(actor_label=ERASED_LABEL)


class StaffAuditMixin:
    """Mixin de ModelViewSet : journalise les modifications et suppressions faites par le staff.
    `audit_owner_field` : FK vers le propriétaire (voir `record_staff_action`)."""

    audit_owner_field = None

    def perform_update(self, serializer):
        super().perform_update(serializer)
        record_staff_action(
            self.request,
            AuditLog.Action.UPDATE,
            serializer.instance,
            details={"fields": sorted(serializer.validated_data.keys())},
            owner_field=self.audit_owner_field,
        )

    def perform_destroy(self, instance):
        pk, label = instance.pk, str(instance)
        super().perform_destroy(instance)
        # Journalisé après la suppression, qui peut échouer (p. ex. ProtectedError).
        record_staff_action(
            self.request,
            AuditLog.Action.DELETE,
            instance,
            owner_field=self.audit_owner_field,
            pk=pk,
            label=label,
        )
