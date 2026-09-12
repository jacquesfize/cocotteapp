import pytest

from apps.accounts.factories import UserFactory


@pytest.mark.django_db
def test_user_default_diet_type():
    user = UserFactory()
    assert user.diet_type == "omnivore"
    assert user.activity_level == "moderate"
