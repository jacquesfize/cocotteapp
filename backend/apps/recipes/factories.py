import factory

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory

from .models import Recipe, RecipeComment, RecipeIngredient


class RecipeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Recipe

    title = factory.Sequence(lambda n: f"Recette {n}")
    author = factory.SubFactory(UserFactory)
    servings = 4
    prep_time_minutes = 10
    cook_time_minutes = 20


class RecipeIngredientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RecipeIngredient

    recipe = factory.SubFactory(RecipeFactory)
    ingredient = factory.SubFactory(IngredientFactory)
    quantity = 100
    unit = "g"


class RecipeCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RecipeComment

    recipe = factory.SubFactory(RecipeFactory)
    author_name = factory.Sequence(lambda n: f"Invité {n}")
    body = factory.Sequence(lambda n: f"Super recette #{n} !")
