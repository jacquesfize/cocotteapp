import factory

from apps.accounts.factories import UserFactory
from apps.recipes.factories import RecipeFactory

from .models import MealPlanEntry, PlanningPermission, PlanningShare


class MealPlanEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = MealPlanEntry

    user = factory.SubFactory(UserFactory)
    recipe = factory.SubFactory(RecipeFactory)
    date = "2026-01-01"
    meal_type = "dinner"
    servings = 2


class PlanningShareFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PlanningShare

    owner = factory.SubFactory(UserFactory)
    shared_with = factory.SubFactory(UserFactory)
    permission = PlanningPermission.READ
