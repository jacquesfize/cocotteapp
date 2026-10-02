from datetime import timedelta
from io import StringIO

import pytest
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from apps.accounts.factories import UserFactory
from apps.accounts.models import User


@pytest.fixture(autouse=True)
def retention(settings):
    settings.INACTIVE_ACCOUNT_RETENTION_DAYS = 100
    settings.INACTIVE_ACCOUNT_WARNING_DAYS = 10


def run(**kwargs):
    call_command("purge_inactive_users", stdout=StringIO(), **kwargs)


def inactive_user(days, **kwargs):
    return UserFactory(last_login=timezone.now() - timedelta(days=days), **kwargs)


@pytest.mark.django_db
def test_active_users_are_left_alone():
    user = inactive_user(5)

    run()

    assert User.objects.filter(pk=user.pk).exists()
    assert mail.outbox == []


@pytest.mark.django_db
def test_inactive_user_is_warned_once_then_kept_until_the_notice_period_elapses():
    user = inactive_user(95)

    run()
    run()

    assert User.objects.filter(pk=user.pk).exists()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]


@pytest.mark.django_db
def test_warned_user_is_deleted_after_retention_and_notice_period():
    user = inactive_user(101)
    user.inactivity_warned_at = timezone.now() - timedelta(days=11)
    user.save()

    run()

    assert not User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_user_never_deleted_without_prior_warning():
    user = inactive_user(500)

    run()

    assert User.objects.filter(pk=user.pk).exists()
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_user_who_came_back_after_the_warning_is_not_deleted():
    user = inactive_user(1)
    user.inactivity_warned_at = timezone.now() - timedelta(days=30)
    user.save()

    run()

    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_never_logged_in_user_counts_from_registration():
    user = UserFactory(date_joined=timezone.now() - timedelta(days=95), last_login=None)

    run()

    assert len(mail.outbox) == 1
    user.refresh_from_db()
    assert user.inactivity_warned_at is not None


@pytest.mark.django_db
def test_staff_accounts_are_never_purged():
    staff = inactive_user(500, is_staff=True)

    run()

    assert User.objects.filter(pk=staff.pk).exists()
    assert mail.outbox == []


@pytest.mark.django_db
def test_dry_run_changes_nothing():
    warned = inactive_user(95)
    doomed = inactive_user(101)
    doomed.inactivity_warned_at = timezone.now() - timedelta(days=11)
    doomed.save()

    run(dry_run=True)

    assert User.objects.filter(pk=doomed.pk).exists()
    warned.refresh_from_db()
    assert warned.inactivity_warned_at is None
    assert mail.outbox == []


@pytest.mark.django_db
def test_disabled_when_retention_is_zero(settings):
    settings.INACTIVE_ACCOUNT_RETENTION_DAYS = 0
    user = inactive_user(5000)

    run()

    assert User.objects.filter(pk=user.pk).exists()
    assert mail.outbox == []
