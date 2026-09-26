import hashlib

from django.conf import settings
from rest_framework.throttling import BaseThrottle


def voter_hash_for_request(request) -> str:
    """Salted hash of the requester's IP (via DRF's own IP resolution, so it agrees with
    `RatingCreateAnonThrottle`), used to let an anonymous voter update their own rating later
    without ever storing or exposing their IP address."""

    ident = BaseThrottle().get_ident(request)
    return hashlib.sha256(f"{settings.SECRET_KEY}:{ident}".encode()).hexdigest()
