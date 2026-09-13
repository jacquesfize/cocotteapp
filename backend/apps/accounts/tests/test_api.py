import re
import zipfile
from io import BytesIO

import pytest
from django.core import mail
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.recipes.factories import RecipeFactory


def _extract_reset_link(email_body):
    match = re.search(r"http\S+/reset-password/(\S+)/(\S+)", email_body)
    assert match, f"No reset link found in email body: {email_body!r}"
    return match.group(1), match.group(2)


@pytest.mark.django_db
def test_register_and_login():
    client = APIClient()
    response = client.post(
        "/api/auth/register/",
        {"username": "alice", "password": "s3cret-pass", "email": "alice@example.com"},
    )
    assert response.status_code == 201

    token_response = client.post(
        "/api/auth/token/", {"email": "alice@example.com", "password": "s3cret-pass"}
    )
    assert token_response.status_code == 200
    assert "access" in token_response.data


@pytest.mark.django_db
def test_login_with_username_instead_of_email_is_rejected():
    UserFactory(username="alice", email="alice@example.com")
    client = APIClient()

    response = client.post("/api/auth/token/", {"username": "alice", "password": "password123"})

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_me_endpoint_requires_authentication():
    client = APIClient()
    response = client.get("/api/auth/me/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_can_update_username_and_email():
    user = UserFactory(username="oldname")
    client = APIClient()
    client.force_authenticate(user)

    response = client.patch("/api/auth/me/", {"username": "newname", "email": "new@example.com"})

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.username == "newname"
    assert user.email == "new@example.com"


@pytest.mark.django_db
def test_cannot_update_username_to_an_existing_one():
    UserFactory(username="taken")
    user = UserFactory(username="mine")
    client = APIClient()
    client.force_authenticate(user)

    response = client.patch("/api/auth/me/", {"username": "taken"})

    assert response.status_code == 400


@pytest.mark.django_db
def test_change_password_with_correct_old_password():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        "/api/auth/me/change-password/",
        {"old_password": "password123", "new_password": "a-new-password"},
    )

    assert response.status_code == 204
    login_response = APIClient().post(
        "/api/auth/token/", {"email": user.email, "password": "a-new-password"}
    )
    assert login_response.status_code == 200


@pytest.mark.django_db
def test_change_password_rejects_wrong_old_password():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        "/api/auth/me/change-password/",
        {"old_password": "not-the-password", "new_password": "a-new-password"},
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.check_password("password123")


@pytest.mark.django_db
def test_deleting_account_removes_the_user_and_their_recipes():
    user = UserFactory()
    recipe = RecipeFactory(author=user)
    client = APIClient()
    client.force_authenticate(user)

    response = client.delete("/api/auth/me/")

    assert response.status_code == 204
    assert not user.__class__.objects.filter(id=user.id).exists()
    assert not recipe.__class__.objects.filter(id=recipe.id).exists()


@pytest.mark.django_db
def test_export_data_returns_a_zip_scoped_to_the_user():
    user = UserFactory()
    RecipeFactory(author=user, title="Ma recette")
    other_user = UserFactory()
    RecipeFactory(author=other_user, title="Pas la mienne")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/api/auth/me/export/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/zip"
    archive = zipfile.ZipFile(BytesIO(response.content))
    assert set(archive.namelist()) == {
        "profil.json",
        "recettes.json",
        "agenda.json",
        "listes_de_courses.json",
    }
    recettes_json = archive.read("recettes.json").decode("utf-8")
    assert "Ma recette" in recettes_json
    assert "Pas la mienne" not in recettes_json


@pytest.mark.django_db
def test_admin_users_list_requires_staff():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/admin/users/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_list_and_toggle_users():
    admin = UserFactory(is_staff=True)
    target = UserFactory(is_active=True)
    client = APIClient()
    client.force_authenticate(admin)

    list_response = client.get("/api/admin/users/")
    assert list_response.status_code == 200
    assert list_response.data["count"] >= 2

    patch_response = client.patch(f"/api/admin/users/{target.id}/", {"is_active": False})
    assert patch_response.status_code == 200
    target.refresh_from_db()
    assert target.is_active is False


@pytest.mark.django_db
def test_admin_can_delete_another_user():
    admin = UserFactory(is_staff=True)
    target = UserFactory()
    client = APIClient()
    client.force_authenticate(admin)

    response = client.delete(f"/api/admin/users/{target.id}/")

    assert response.status_code == 204
    assert not target.__class__.objects.filter(id=target.id).exists()


@pytest.mark.django_db
def test_admin_cannot_deactivate_or_delete_their_own_account_via_admin_api():
    admin = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(admin)

    patch_response = client.patch(f"/api/admin/users/{admin.id}/", {"is_active": False})
    assert patch_response.status_code == 403

    delete_response = client.delete(f"/api/admin/users/{admin.id}/")
    assert delete_response.status_code == 403

    admin.refresh_from_db()
    assert admin.is_active is True


@pytest.mark.django_db
def test_registering_with_an_email_already_in_use_is_rejected():
    UserFactory(email="taken@example.com")
    client = APIClient()

    response = client.post(
        "/api/auth/register/",
        {"username": "someone", "password": "s3cret-pass", "email": "taken@example.com"},
    )

    assert response.status_code == 400
    assert "email" in response.data


@pytest.mark.django_db
def test_password_reset_request_sends_an_email_for_an_existing_account():
    user = UserFactory(email="bob@example.com")

    response = APIClient().post("/api/auth/password-reset/", {"email": "bob@example.com"})

    assert response.status_code == 204
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
    uid, token = _extract_reset_link(mail.outbox[0].body)
    assert uid and token


@pytest.mark.django_db
def test_password_reset_request_does_not_leak_whether_an_email_is_registered():
    response = APIClient().post("/api/auth/password-reset/", {"email": "nobody@example.com"})

    assert response.status_code == 204
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_confirm_with_valid_token_changes_the_password():
    user = UserFactory(email="carol@example.com")
    APIClient().post("/api/auth/password-reset/", {"email": "carol@example.com"})
    uid, token = _extract_reset_link(mail.outbox[0].body)

    response = APIClient().post(
        "/api/auth/password-reset/confirm/",
        {"uid": uid, "token": token, "new_password": "a-brand-new-pass"},
    )

    assert response.status_code == 204
    login_response = APIClient().post(
        "/api/auth/token/", {"email": user.email, "password": "a-brand-new-pass"}
    )
    assert login_response.status_code == 200


@pytest.mark.django_db
def test_password_reset_confirm_rejects_an_invalid_token():
    user = UserFactory(email="dave@example.com")
    APIClient().post("/api/auth/password-reset/", {"email": "dave@example.com"})
    uid, _token = _extract_reset_link(mail.outbox[0].body)

    response = APIClient().post(
        "/api/auth/password-reset/confirm/",
        {"uid": uid, "token": "not-a-valid-token", "new_password": "a-brand-new-pass"},
    )

    assert response.status_code == 400
    user.refresh_from_db()
    assert user.check_password("password123")


@pytest.mark.django_db
def test_password_reset_token_cannot_be_reused_after_the_password_changed():
    UserFactory(email="erin@example.com")
    APIClient().post("/api/auth/password-reset/", {"email": "erin@example.com"})
    uid, token = _extract_reset_link(mail.outbox[0].body)

    first_use = APIClient().post(
        "/api/auth/password-reset/confirm/",
        {"uid": uid, "token": token, "new_password": "first-new-pass"},
    )
    assert first_use.status_code == 204

    second_use = APIClient().post(
        "/api/auth/password-reset/confirm/",
        {"uid": uid, "token": token, "new_password": "second-new-pass"},
    )
    assert second_use.status_code == 400


@pytest.mark.django_db
def test_password_reset_confirm_rejects_a_malformed_uid():
    response = APIClient().post(
        "/api/auth/password-reset/confirm/",
        {"uid": "not-base64!!", "token": "whatever", "new_password": "a-brand-new-pass"},
    )

    assert response.status_code == 400
