from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.announcements.factories import AnnouncementFactory


def _ids(response):
    return [a["id"] for a in response.json()]


@pytest.mark.django_db
def test_anonymous_sees_active_announcements():
    announcement = AnnouncementFactory(title_en="Hello")
    response = APIClient().get("/api/announcements/")
    assert response.status_code == 200
    assert _ids(response) == [announcement.id]
    assert response.json()[0]["title_en"] == "Hello"


@pytest.mark.django_db
def test_inactive_and_out_of_window_announcements_are_hidden():
    now = timezone.now()
    AnnouncementFactory(is_active=False)
    AnnouncementFactory(starts_at=now + timedelta(hours=1))
    AnnouncementFactory(ends_at=now - timedelta(hours=1))
    current = AnnouncementFactory(starts_at=now - timedelta(hours=1), ends_at=now + timedelta(hours=1))
    assert _ids(APIClient().get("/api/announcements/")) == [current.id]


@pytest.mark.django_db
def test_most_severe_first():
    info = AnnouncementFactory(level="info")
    critical = AnnouncementFactory(level="critical")
    assert _ids(APIClient().get("/api/announcements/")) == [critical.id, info.id]


@pytest.mark.django_db
def test_test_instance_banner_follows_setting(settings):
    settings.TEST_INSTANCE = False
    assert _ids(APIClient().get("/api/announcements/")) == []
    settings.TEST_INSTANCE = True
    response = APIClient().get("/api/announcements/")
    assert response.json() == [{"id": "test-instance", "level": "warning", "dismissible": False}]
