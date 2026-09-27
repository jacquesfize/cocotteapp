from rest_framework.throttling import AnonRateThrottle


class CommentCreateAnonThrottle(AnonRateThrottle):
    """Conservative anti-spam limit applied to anonymous recipe comment creation.

    Authenticated requests are never throttled by ``AnonRateThrottle`` (it only tracks requests
    without a resolved user), so this only affects unauthenticated posters.
    """

    scope = "comment_create"


class RatingCreateAnonThrottle(AnonRateThrottle):
    """Anti-spam limit for anonymous rating submission. More permissive than comments (a star
    click is a much lighter action than writing text), but still bounds how fast one IP can spam
    votes across many recipes before the per-recipe unique constraint even comes into play."""

    scope = "rating_create"
