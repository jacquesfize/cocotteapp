import factory

from .models import Ingredient, IngredientCategory, Unit


class IngredientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Ingredient

    name = factory.Sequence(lambda n: f"ingredient-{n}")
    category = IngredientCategory.VEGETABLE
    default_unit = Unit.GRAM
