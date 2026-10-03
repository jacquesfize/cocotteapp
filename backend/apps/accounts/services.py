from django.contrib.auth import get_user_model
from django.db import transaction

ANONYMOUS_EMAIL = "deleted-user@cocotte.invalid"
ANONYMOUS_NAME = "Utilisateur supprimé"


def get_anonymous_user():
    """Compte « fantôme » partagé qui reprend les recettes publiques d'un compte supprimé.

    Il ne peut pas se connecter (inactif, sans mot de passe) et n'est jamais purgé.
    """
    User = get_user_model()
    user = User.objects.filter(email=ANONYMOUS_EMAIL).first()
    if user is None:
        username, n = ANONYMOUS_NAME, 1
        while User.objects.filter(username=username).exists():
            n += 1
            username = f"{ANONYMOUS_NAME} {n}"
        user = User(email=ANONYMOUS_EMAIL, username=username, is_active=False)
        user.set_unusable_password()
        user.save()
    return user


@transaction.atomic
def delete_account(user, keep_recipes=False):
    """Supprime un compte (RGPD art. 17).

    Avec `keep_recipes`, les recettes publiques sont rattachées au compte anonyme au lieu
    d'être supprimées (les recettes privées, elles, le sont toujours), et les commentaires
    laissés par l'utilisateur perdent son nom. Sans, tout ce qu'il a écrit disparaît avec lui.
    """
    if keep_recipes:
        anonymous = get_anonymous_user()
        user.recipes.filter(is_public=True).update(author=anonymous)
    # Les commentaires survivent à la suppression (SET_NULL) : on retire le nom d'affichage.
    user.recipe_comments.update(author_name=ANONYMOUS_NAME)
    user.blog_comments.update(author_name=ANONYMOUS_NAME)
    user.delete()
