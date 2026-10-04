from django.db import transaction

from apps.ingredients.services import merge_translations


@transaction.atomic
def merge_cookware(source, target):
    """Fusionne le doublon `source` dans `target`, puis supprime `source` (et sa photo).

    Les recettes qui utilisaient `source` utilisent désormais `target` ; les traductions sont
    fusionnées (celles de `target` priment). Le texte des étapes (`#nom`) n'est pas réécrit."""
    target.recipes.add(*source.recipes.all())
    target.translations = merge_translations(source.translations, target.translations)
    target.save(update_fields=["translations"])
    if source.image:
        source.image.delete(save=False)
    source.delete()
    return target
