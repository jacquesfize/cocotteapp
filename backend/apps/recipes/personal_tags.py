"""Rapprochement des étiquettes personnelles : à la création, on montre à l'utilisateur ses
étiquettes déjà existantes qui ressemblent au nom tapé (« Pâte » / « pates » / « Pâtes fraîches »),
pour éviter les doublons à une faute de frappe ou un accent près.

Un utilisateur n'a que quelques dizaines d'étiquettes au plus : la comparaison se fait en Python,
sur toutes ses étiquettes, plutôt qu'en SQL (pg_trgm), sans enjeu de performance."""

from difflib import SequenceMatcher

from apps.ingredients.search import normalize

# Ratio difflib à partir duquel deux noms normalisés sont jugés proches (« gateau » / « gateaux »).
SIMILARITY_THRESHOLD = 0.75
# En dessous, l'inclusion d'un nom dans l'autre n'est pas significative (« a » dans « apéro »).
MIN_CONTAINED_LENGTH = 3


def similarity(a: str, b: str) -> float:
    """Score de 0 à 1 entre deux noms d'étiquette, à la casse, aux accents et ligatures près ;
    un nom contenu dans l'autre compte comme proche (« Pâtes » / « Pâtes fraîches »)."""
    a, b = normalize(a), normalize(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ratio = SequenceMatcher(None, a, b).ratio()
    shorter, longer = sorted((a, b), key=len)
    if len(shorter) >= MIN_CONTAINED_LENGTH and shorter in longer:
        ratio = max(ratio, 0.9)
    return ratio


def similar_tags(tags, name: str, limit: int = 5):
    """Étiquettes de `tags` proches de `name`, de la plus proche à la moins proche."""
    scored = [(similarity(tag.name, name), tag) for tag in tags]
    matches = [(score, tag) for score, tag in scored if score >= SIMILARITY_THRESHOLD]
    matches.sort(key=lambda item: (-item[0], item[1].name.lower()))
    return [tag for _score, tag in matches[:limit]]
