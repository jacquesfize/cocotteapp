from .base import *  # noqa: F401,F403

DEBUG = True

# L'admin Django est atteint via le proxy Vite (http://localhost:5173/django-admin/) : ce
# n'est pas l'hôte vu par Django, donc l'origine du navigateur doit être déclarée de confiance
# pour que les POST de l'admin (connexion, formulaires) passent la vérification CSRF.
CSRF_TRUSTED_ORIGINS = [FRONTEND_URL]  # noqa: F405
