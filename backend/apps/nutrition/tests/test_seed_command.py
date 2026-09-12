import pytest
from django.core.management import call_command

from apps.nutrition.models import NutrientRequirement


@pytest.mark.django_db
def test_seed_command_creates_requirements_for_every_combination():
    call_command("seed_nutrient_requirements")

    # 3 régimes x 3 niveaux d'activité x 6 nutriments suivis
    assert NutrientRequirement.objects.count() == 54


@pytest.mark.django_db
def test_seed_command_is_idempotent():
    call_command("seed_nutrient_requirements")
    call_command("seed_nutrient_requirements")

    assert NutrientRequirement.objects.count() == 54


@pytest.mark.django_db
def test_vegan_iron_requirement_is_higher_than_omnivore():
    call_command("seed_nutrient_requirements")

    vegan = NutrientRequirement.objects.get(diet_type="vegan", activity_level="moderate", nutrient="iron_mg")
    omnivore = NutrientRequirement.objects.get(
        diet_type="omnivore", activity_level="moderate", nutrient="iron_mg"
    )

    assert vegan.daily_minimum > omnivore.daily_minimum


@pytest.mark.django_db
def test_athlete_protein_requirement_is_higher_than_sedentary():
    call_command("seed_nutrient_requirements")

    athlete = NutrientRequirement.objects.get(
        diet_type="omnivore", activity_level="athlete", nutrient="protein_g"
    )
    sedentary = NutrientRequirement.objects.get(
        diet_type="omnivore", activity_level="sedentary", nutrient="protein_g"
    )

    assert athlete.daily_minimum > sedentary.daily_minimum
