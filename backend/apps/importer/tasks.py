from celery import shared_task


@shared_task
def import_recipe_from_url_task(user_id, url):
    from django.contrib.auth import get_user_model

    from .services import create_recipe_from_url

    user = get_user_model().objects.get(pk=user_id)
    recipe = create_recipe_from_url(user, url)
    return recipe.id
