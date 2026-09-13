from rest_framework.throttling import AnonRateThrottle


class CommentCreateAnonThrottle(AnonRateThrottle):
    """Conservative anti-spam limit applied to anonymous recipe comment creation.

    Authenticated requests are never throttled by ``AnonRateThrottle`` (it only tracks requests
    without a resolved user), so this only affects unauthenticated posters.
    """

    scope = "comment_create"
