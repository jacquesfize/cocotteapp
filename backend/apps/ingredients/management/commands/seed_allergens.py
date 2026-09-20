from django.core.management.base import BaseCommand

from apps.ingredients.models import Allergen

# Les 14 allergènes à déclaration obligatoire (règlement UE 1169/2011) + le lactose,
# qui est une intolérance distincte de l'allergie aux protéines de lait.
ALLERGENS = [
    ("gluten", "Gluten"),
    ("milk", "Lait"),
    ("lactose", "Lactose"),
    ("egg", "Œufs"),
    ("peanut", "Arachides"),
    ("tree_nuts", "Fruits à coque"),
    ("soy", "Soja"),
    ("fish", "Poisson"),
    ("crustaceans", "Crustacés"),
    ("molluscs", "Mollusques"),
    ("celery", "Céleri"),
    ("mustard", "Moutarde"),
    ("sesame", "Sésame"),
    ("sulphites", "Sulfites"),
    ("lupin", "Lupin"),
]


def seed_allergens():
    for slug, name in ALLERGENS:
        Allergen.objects.update_or_create(slug=slug, defaults={"name": name})


class Command(BaseCommand):
    help = "Crée la liste de référence des allergènes (idempotent)."

    def handle(self, *args, **options):
        seed_allergens()
        self.stdout.write(self.style.SUCCESS(f"Allergènes : {len(ALLERGENS)} en base."))
