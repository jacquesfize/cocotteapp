from .base import *  # noqa: F401,F403

DEBUG = False

# Le conteneur backend n'est joignable qu'en HTTP depuis Caddy, qui termine le TLS : sans ceci,
# Django ne saurait jamais qu'une requête est déjà sécurisée et boucherait en redirections HTTPS.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])  # noqa: F405

# Une semaine par défaut : suffisant pour une vraie protection HSTS sans verrouiller le domaine
# en HTTPS pendant un an si jamais le certificat/la config Caddy posait problème après coup.
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 7)  # noqa: F405
