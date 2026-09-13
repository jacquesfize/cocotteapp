from django.core.management.base import BaseCommand

from apps.recipes.models import ThematicPage

# Quelques pages thématiques de base, éditables ensuite depuis l'admin Django
# (django-admin > Recipes > Thematic pages) : ajouter/retirer un filtre, changer l'ordre
# d'affichage sur la page d'accueil, désactiver une page sans la supprimer.
THEMATIC_PAGES = [
    {
        "title": "Produits de saison",
        "icon": "🌱",
        "description": "Des recettes composées uniquement d'ingrédients de saison, ce mois-ci.",
        "filters": {"in_season": "true"},
        "order": 1,
    },
    {
        "title": "Spécial végan",
        "icon": "🌍",
        "description": "Des recettes 100% végétales, pour découvrir ou faire découvrir.",
        "filters": {"diet_type": "vegan"},
        "order": 2,
    },
    {
        "title": "Prêt en 30 minutes",
        "icon": "⏱️",
        "description": "Des recettes rapides à préparer, pour les soirs de semaine.",
        "filters": {"max_prep_time": "30"},
        "order": 3,
    },
]


class Command(BaseCommand):
    help = "Peuple quelques pages thématiques de base pour la page d'accueil."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0
        for entry in THEMATIC_PAGES:
            _, was_created = ThematicPage.objects.update_or_create(
                title=entry["title"],
                defaults={
                    "icon": entry["icon"],
                    "description": entry["description"],
                    "filters": entry["filters"],
                    "order": entry["order"],
                },
            )
            if was_created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Pages thématiques : {created_count} créées, {updated_count} mises à jour."))
