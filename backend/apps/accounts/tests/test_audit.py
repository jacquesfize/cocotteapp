import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.accounts.models import AuditLog
from apps.recipes.factories import RecipeFactory


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.mark.django_db
def test_staff_edit_of_someone_elses_recipe_is_logged():
    staff = UserFactory(is_staff=True)
    recipe = RecipeFactory()

    response = _client(staff).patch(f"/api/recipes/{recipe.id}/", {"title": "Corrigée"}, format="json")

    assert response.status_code == 200
    entry = AuditLog.objects.get()
    assert (entry.actor, entry.action, entry.target_id) == (staff, AuditLog.Action.UPDATE, str(recipe.id))
    assert entry.actor_label == staff.email
    assert "title" in entry.details["fields"]


@pytest.mark.django_db
def test_staff_delete_is_logged_with_label_after_object_is_gone():
    staff = UserFactory(is_staff=True)
    recipe = RecipeFactory(title="À supprimer")

    response = _client(staff).delete(f"/api/recipes/{recipe.id}/")

    assert response.status_code == 204
    entry = AuditLog.objects.get()
    assert entry.action == AuditLog.Action.DELETE
    assert entry.target_id == str(recipe.id)
    assert "À supprimer" in entry.target_label


@pytest.mark.django_db
def test_staff_edit_of_own_recipe_is_logged_but_author_edit_is_not():
    author = UserFactory()
    staff = UserFactory(is_staff=True)
    own = RecipeFactory(author=author)
    staff_own = RecipeFactory(author=staff)

    _client(author).patch(f"/api/recipes/{own.id}/", {"title": "Mienne"}, format="json")
    assert not AuditLog.objects.exists()

    _client(staff).patch(f"/api/recipes/{staff_own.id}/", {"title": "Aussi la mienne"}, format="json")
    entry = AuditLog.objects.get()
    assert (entry.actor, entry.target_id) == (staff, str(staff_own.id))


@pytest.mark.django_db
def test_admin_user_changes_are_logged():
    staff = UserFactory(is_staff=True)
    target = UserFactory()

    _client(staff).patch(f"/api/admin/users/{target.id}/", {"is_active": False}, format="json")
    response = _client(staff).delete(f"/api/admin/users/{target.id}/")
    assert response.status_code == 204, response.content

    actions = list(AuditLog.objects.order_by("id").values_list("action", flat=True))
    assert actions == [AuditLog.Action.UPDATE, AuditLog.Action.DELETE]


@pytest.mark.django_db
def test_user_targets_are_logged_by_id_not_email():
    staff = UserFactory(is_staff=True)
    target = UserFactory(email="private@example.com")
    target_id = target.id

    _client(staff).delete(f"/api/admin/users/{target_id}/")

    entry = AuditLog.objects.get()
    assert entry.target_label == f"user #{target_id}"
    assert "private@example.com" not in str(entry.__dict__)


@pytest.mark.django_db
def test_deleting_a_staff_account_erases_their_email_from_the_log():
    from apps.accounts.services import delete_account

    staff = UserFactory(is_staff=True, email="gone@example.com")
    recipe = RecipeFactory()
    _client(staff).patch(f"/api/recipes/{recipe.id}/", {"title": "X"}, format="json")

    delete_account(staff)

    entry = AuditLog.objects.get()
    assert entry.actor is None
    assert entry.actor_label == "compte supprimé"


@pytest.mark.django_db
def test_purge_audit_logs_removes_only_expired_lines(settings):
    from datetime import timedelta

    from django.core.management import call_command
    from django.utils import timezone

    settings.AUDIT_LOG_RETENTION_DAYS = 30
    old = AuditLog.objects.create(actor_label="a", action="update", target_type="recipes.Recipe")
    AuditLog.objects.create(actor_label="b", action="update", target_type="recipes.Recipe")
    AuditLog.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=31))

    call_command("purge_audit_logs", "--dry-run")
    assert AuditLog.objects.count() == 2
    call_command("purge_audit_logs")
    assert list(AuditLog.objects.values_list("actor_label", flat=True)) == ["b"]
