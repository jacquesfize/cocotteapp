import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_register_and_login():
    client = APIClient()
    response = client.post(
        "/api/auth/register/",
        {"username": "alice", "password": "s3cret-pass", "email": "alice@example.com"},
    )
    assert response.status_code == 201

    token_response = client.post(
        "/api/auth/token/", {"username": "alice", "password": "s3cret-pass"}
    )
    assert token_response.status_code == 200
    assert "access" in token_response.data


@pytest.mark.django_db
def test_me_endpoint_requires_authentication():
    client = APIClient()
    response = client.get("/api/auth/me/")
    assert response.status_code == 401
