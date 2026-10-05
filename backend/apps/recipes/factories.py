import factory

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory

from .models import (
    Cookware,
    IngredientAlternative,
    PersonalTag,
    Recipe,
    RecipeComment,
    RecipeIngredient,
    RecipeRating,
)


class CookwareFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cookware

    name = factory.Sequence(lambda n: f"ustensile-{n}")


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


class IngredientAlternativeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = IngredientAlternative

    recipe_ingredient = factory.SubFactory(RecipeIngredientFactory)
    ingredient = factory.SubFactory(IngredientFactory)
    quantity = 100
    unit = "g"
    tag = "vegan"


class RecipeCommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RecipeComment

    recipe = factory.SubFactory(RecipeFactory)
    author_name = factory.Sequence(lambda n: f"Invité {n}")
    body = factory.Sequence(lambda n: f"Super recette #{n} !")


class RecipeRatingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RecipeRating

    recipe = factory.SubFactory(RecipeFactory)
    value = 5
    voter_hash = factory.Sequence(lambda n: f"anon-voter-hash-{n}")


class PersonalTagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PersonalTag

    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Étiquette {n}")
