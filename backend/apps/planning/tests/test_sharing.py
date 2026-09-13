import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.planning.factories import PlanningShareFactory
from apps.planning.models import MealPlanEntry, PlanningPermission, PlanningShare
from apps.recipes.factories import RecipeFactory


@pytest.mark.django_db
def test_create_share_by_email():
    owner = UserFactory()
    target = UserFactory(email="alice@example.com")
    client = APIClient()
    client.force_authenticate(owner)

    response = client.post(
        "/api/planning-shares/", {"email": "alice@example.com", "permission": "read"}
    )

    assert response.status_code == 201
    share = PlanningShare.objects.get(owner=owner, shared_with=target)
    assert share.permission == PlanningPermission.READ


@pytest.mark.django_db
def test_create_share_unknown_email_is_rejected():
    owner = UserFactory()
    client = APIClient()
    client.force_authenticate(owner)

    response = client.post(
        "/api/planning-shares/", {"email": "nobody@example.com", "permission": "read"}
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_share_with_self_is_rejected():
    owner = UserFactory(email="owner@example.com")
    client = APIClient()
    client.force_authenticate(owner)

    response = client.post(
        "/api/planning-shares/", {"email": "owner@example.com", "permission": "read"}
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_resharing_updates_existing_share_instead_of_duplicating():
    owner = UserFactory()
    target = UserFactory(email="bob@example.com")
    client = APIClient()
    client.force_authenticate(owner)

    client.post("/api/planning-shares/", {"email": "bob@example.com", "permission": "read"})
    response = client.post("/api/planning-shares/", {"email": "bob@example.com", "permission": "write"})

    assert response.status_code == 201
    assert PlanningShare.objects.filter(owner=owner, shared_with=target).count() == 1
    assert PlanningShare.objects.get(owner=owner, shared_with=target).permission == PlanningPermission.WRITE


@pytest.mark.django_db
def test_owner_can_update_share_permission():
    share = PlanningShareFactory(permission=PlanningPermission.READ)
    client = APIClient()
    client.force_authenticate(share.owner)

    response = client.patch(f"/api/planning-shares/{share.id}/", {"permission": "write"})

    assert response.status_code == 200
    share.refresh_from_db()
    assert share.permission == PlanningPermission.WRITE


@pytest.mark.django_db
def test_owner_can_revoke_share():
    share = PlanningShareFactory()
    client = APIClient()
    client.force_authenticate(share.owner)

    response = client.delete(f"/api/planning-shares/{share.id}/")

    assert response.status_code == 204
    assert not PlanningShare.objects.filter(id=share.id).exists()


@pytest.mark.django_db
def test_non_owner_cannot_manage_someone_elses_share():
    share = PlanningShareFactory()
    stranger = UserFactory()
    client = APIClient()
    client.force_authenticate(stranger)

    response = client.delete(f"/api/planning-shares/{share.id}/")

    assert response.status_code == 404


@pytest.mark.django_db
def test_list_shares_only_shows_shares_i_own():
    owner = UserFactory()
    other_owner = UserFactory()
    PlanningShareFactory(owner=owner)
    PlanningShareFactory(owner=other_owner)

    client = APIClient()
    client.force_authenticate(owner)
    response = client.get("/api/planning-shares/")

    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_shared_with_me_lists_received_shares():
    recipient = UserFactory()
    share = PlanningShareFactory(shared_with=recipient, permission=PlanningPermission.WRITE)

    client = APIClient()
    client.force_authenticate(recipient)
    response = client.get("/api/planning-shares/shared-with-me/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["owner"] == share.owner.id
    assert response.data[0]["owner_username"] == share.owner.username
    assert response.data[0]["permission"] == "write"


@pytest.mark.django_db
def test_owner_param_without_share_is_rejected():
    owner = UserFactory()
    stranger = UserFactory()

    client = APIClient()
    client.force_authenticate(stranger)
    response = client.get(f"/api/meal-plan-entries/?owner={owner.id}")

    assert response.status_code == 403


@pytest.mark.django_db
def test_read_share_allows_get_but_rejects_writes():
    recipe = RecipeFactory()
    share = PlanningShareFactory(permission=PlanningPermission.READ)
    entry = MealPlanEntry.objects.create(
        user=share.owner, recipe=recipe, date="2026-02-01", meal_type="lunch"
    )

    client = APIClient()
    client.force_authenticate(share.shared_with)

    list_response = client.get(f"/api/meal-plan-entries/?owner={share.owner.id}")
    assert list_response.status_code == 200
    assert len(list_response.data) == 1

    create_response = client.post(
        f"/api/meal-plan-entries/?owner={share.owner.id}",
        {"recipe": recipe.id, "date": "2026-02-02", "meal_type": "dinner", "servings": 2},
    )
    assert create_response.status_code == 403

    update_response = client.patch(
        f"/api/meal-plan-entries/{entry.id}/?owner={share.owner.id}", {"servings": 3}
    )
    assert update_response.status_code == 403

    delete_response = client.delete(f"/api/meal-plan-entries/{entry.id}/?owner={share.owner.id}")
    assert delete_response.status_code == 403


@pytest.mark.django_db
def test_write_share_allows_writes_and_keeps_entry_owned_by_agenda_owner():
    recipe = RecipeFactory()
    share = PlanningShareFactory(permission=PlanningPermission.WRITE)

    client = APIClient()
    client.force_authenticate(share.shared_with)

    create_response = client.post(
        f"/api/meal-plan-entries/?owner={share.owner.id}",
        {"recipe": recipe.id, "date": "2026-02-02", "meal_type": "dinner", "servings": 2},
    )
    assert create_response.status_code == 201
    entry = MealPlanEntry.objects.get(id=create_response.data["id"])
    assert entry.user == share.owner

    update_response = client.patch(
        f"/api/meal-plan-entries/{entry.id}/?owner={share.owner.id}", {"servings": 4}
    )
    assert update_response.status_code == 200
    entry.refresh_from_db()
    assert entry.servings == 4
    assert entry.user == share.owner

    delete_response = client.delete(f"/api/meal-plan-entries/{entry.id}/?owner={share.owner.id}")
    assert delete_response.status_code == 204
    assert not MealPlanEntry.objects.filter(id=entry.id).exists()


@pytest.mark.django_db
def test_nutrition_summary_respects_owner_param():
    recipe = RecipeFactory()
    share = PlanningShareFactory(permission=PlanningPermission.READ)
    MealPlanEntry.objects.create(
        user=share.owner, recipe=recipe, date="2026-02-05", meal_type="lunch", servings=1
    )

    client = APIClient()
    client.force_authenticate(share.shared_with)
    response = client.get(
        f"/api/meal-plan-entries/nutrition_summary/"
        f"?owner={share.owner.id}&date_after=2026-02-05&date_before=2026-02-05"
    )

    assert response.status_code == 200


@pytest.mark.django_db
def test_week_pdf_respects_owner_param():
    recipe = RecipeFactory(title="Curry partagé")
    share = PlanningShareFactory(permission=PlanningPermission.READ)
    MealPlanEntry.objects.create(user=share.owner, recipe=recipe, date="2026-02-05", meal_type="dinner")

    client = APIClient()
    client.force_authenticate(share.shared_with)
    response = client.get(
        f"/api/meal-plan-entries/week-pdf/"
        f"?owner={share.owner.id}&date_after=2026-02-05&date_before=2026-02-11"
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
def test_share_model_rejects_sharing_with_self():
    from django.core.exceptions import ValidationError

    user = UserFactory()
    share = PlanningShare(owner=user, shared_with=user, permission=PlanningPermission.READ)
    with pytest.raises(ValidationError):
        share.full_clean()
