import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.planning.ics import build_ics, fold_line
from apps.planning.models import CalendarFeedToken, MealPlanEntry
from apps.recipes.factories import RecipeFactory


def _entry(user, title="Tarte, aux; pommes", date="2026-03-02", meal="dinner"):
    return MealPlanEntry.objects.create(
        user=user, recipe=RecipeFactory(title=title), date=date, meal_type=meal, servings=2
    )


@pytest.mark.django_db
def test_ics_download_range_and_escaping():
    user = UserFactory()
    _entry(user)
    _entry(user, title="Hors plage", date="2026-04-01")
    client = APIClient()
    client.force_authenticate(user)
    r = client.get("/api/meal-plan-entries/ics/", {"date_after": "2026-03-01", "date_before": "2026-03-07"})
    assert r.status_code == 200
    assert r["Content-Type"].startswith("text/calendar")
    body = r.content.decode()
    assert body.startswith("BEGIN:VCALENDAR\r\n")
    assert "SUMMARY:Tarte\\, aux\\; pommes" in body
    assert "DTSTART:20260302T193000" in body
    assert "Hors plage" not in body
    assert body.count("BEGIN:VEVENT") == 1


@pytest.mark.django_db
def test_ics_download_requires_auth_and_scopes_to_user():
    _entry(UserFactory())
    assert APIClient().get("/api/meal-plan-entries/ics/").status_code == 401
    client = APIClient()
    client.force_authenticate(UserFactory())
    assert "BEGIN:VEVENT" not in client.get("/api/meal-plan-entries/ics/").content.decode()


@pytest.mark.django_db
def test_feed_token_flow_and_regeneration():
    user = UserFactory()
    _entry(user)
    client = APIClient()
    client.force_authenticate(user)
    data = client.get("/api/planning/calendar-feed/").json()
    assert data["webcal_url"].startswith("webcal://")
    assert data["url"].endswith(f"/api/planning/feed/{data['token']}.ics")
    assert client.get("/api/planning/calendar-feed/").json()["token"] == data["token"]

    feed = APIClient().get(f"/api/planning/feed/{data['token']}.ics")
    assert feed.status_code == 200
    assert "BEGIN:VEVENT" in feed.content.decode()

    new = client.post("/api/planning/calendar-feed/").json()
    assert new["token"] != data["token"]
    assert APIClient().get(f"/api/planning/feed/{data['token']}.ics").status_code == 404
    assert APIClient().get(f"/api/planning/feed/{new['token']}.ics").status_code == 200
    assert CalendarFeedToken.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_feed_unknown_token_404_and_management_requires_auth():
    assert APIClient().get("/api/planning/feed/nope.ics").status_code == 404
    assert APIClient().get("/api/planning/calendar-feed/").status_code == 401


def test_fold_line_limits_octets_and_keeps_content():
    line = "SUMMARY:" + "é" * 100
    folded = fold_line(line)
    assert all(len(p.encode()) <= 75 for p in folded.split("\r\n"))
    assert folded.replace("\r\n ", "") == line


def test_build_ics_empty():
    assert "BEGIN:VEVENT" not in build_ics([])
