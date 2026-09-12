from django.core.management.base import BaseCommand

from apps.accounts.models import ActivityLevel, DietType
from apps.nutrition.models import NutrientRequirement

# Seuils journaliers de référence, volontairement simplifiés (pas un avis médical) :
# le fer et le zinc sont moins bien absorbés depuis les sources végétales, d'où des
# minimums plus élevés en végétarien/végan ; la B12 n'existe pratiquement pas dans les
# plantes non enrichies, d'où un seuil unique difficile à atteindre sans aliments
# enrichis ou complément pour un régime végan.
PROTEIN_G_BY_ACTIVITY = {
    ActivityLevel.SEDENTARY: 50,
    ActivityLevel.MODERATE: 65,
    ActivityLevel.ATHLETE: 100,
}

IRON_MG_BY_DIET = {
    DietType.OMNIVORE: 10,
    DietType.VEGETARIAN: 14,
    DietType.VEGAN: 18,
}

ZINC_MG_BY_DIET = {
    DietType.OMNIVORE: 10,
    DietType.VEGETARIAN: 13,
    DietType.VEGAN: 13,
}

ATHLETE_MICRONUTRIENT_MULTIPLIER = 1.2
VITAMIN_B12_UG = 2.4
CALCIUM_MG = 950
OMEGA3_G = 1.1

UNITS = {
    "protein_g": "g",
    "iron_mg": "mg",
    "vitamin_b12_ug": "µg",
    "calcium_mg": "mg",
    "omega3_g": "g",
    "zinc_mg": "mg",
}


class Command(BaseCommand):
    help = "Peuple les seuils nutritionnels journaliers de référence (utilisés pour détecter les carences)."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for diet_type in DietType.values:
            for activity_level in ActivityLevel.values:
                iron = IRON_MG_BY_DIET[diet_type]
                zinc = ZINC_MG_BY_DIET[diet_type]
                if activity_level == ActivityLevel.ATHLETE:
                    iron *= ATHLETE_MICRONUTRIENT_MULTIPLIER
                    zinc *= ATHLETE_MICRONUTRIENT_MULTIPLIER

                requirements = {
                    "protein_g": PROTEIN_G_BY_ACTIVITY[activity_level],
                    "iron_mg": iron,
                    "vitamin_b12_ug": VITAMIN_B12_UG,
                    "calcium_mg": CALCIUM_MG,
                    "omega3_g": OMEGA3_G,
                    "zinc_mg": zinc,
                }

                for nutrient, minimum in requirements.items():
                    _, was_created = NutrientRequirement.objects.update_or_create(
                        diet_type=diet_type,
                        activity_level=activity_level,
                        nutrient=nutrient,
                        defaults={"unit": UNITS[nutrient], "daily_minimum": minimum},
                    )
                    if was_created:
                        created_count += 1
                    else:
                        updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Seuils nutritionnels : {created_count} créés, {updated_count} mis à jour.")
        )
