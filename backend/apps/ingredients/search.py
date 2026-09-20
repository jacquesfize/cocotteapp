"""Recherche d'ingrédients tolérante : casse, accents, ligatures (œ/æ) et fautes de frappe."""

import unicodedata

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, F, FloatField, Func, IntegerField, Q, TextField, Value, When
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Coalesce, Greatest, Lower, Replace
from rest_framework.filters import BaseFilterBackend

SIMILARITY_THRESHOLD = 0.3
_LIGATURES = {"œ": "oe", "æ": "ae"}


def normalize(text: str) -> str:
    """Minuscule, sans accents, œ->oe, æ->ae."""
    text = text.lower()
    for src, dst in _LIGATURES.items():
        text = text.replace(src, dst)
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).strip()


class _Unaccent(Func):
    function = "unaccent"
    output_field = TextField()


def _normalized_expr(expr):
    out = Lower(expr, output_field=TextField())
    for src, dst in _LIGATURES.items():
        out = Replace(out, Value(src), Value(dst), output_field=TextField())
    return _Unaccent(out)


def fuzzy_search(queryset, term: str):
    term = normalize(term)
    if not term:
        return queryset
    name = _normalized_expr(F("name"))
    en = _normalized_expr(Coalesce(KeyTextTransform("en", "translations"), Value(""), output_field=TextField()))
    queryset = queryset.annotate(_n_name=name, _n_en=en).annotate(
        _sim=Coalesce(TrigramSimilarity("_n_name", term), Value(0.0)),
        _sim_en=Coalesce(TrigramSimilarity("_n_en", term), Value(0.0)),
    )
    queryset = queryset.filter(
        Q(_n_name__contains=term)
        | Q(_n_en__contains=term)
        | Q(_sim__gte=SIMILARITY_THRESHOLD)
        | Q(_sim_en__gte=SIMILARITY_THRESHOLD)
    )
    rank = Case(
        When(Q(_n_name=term) | Q(_n_en=term), then=Value(0)),
        When(Q(_n_name__startswith=term) | Q(_n_en__startswith=term), then=Value(1)),
        When(Q(_n_name__contains=term) | Q(_n_en__contains=term), then=Value(2)),
        default=Value(3),
        output_field=IntegerField(),
    )
    best = Greatest(F("_sim"), F("_sim_en"), output_field=FloatField())
    return queryset.annotate(_rank=rank).order_by("_rank", best.desc(), "name")


class FuzzySearchFilter(BaseFilterBackend):
    search_param = "search"

    def filter_queryset(self, request, queryset, view):
        term = request.query_params.get(self.search_param, "")
        return fuzzy_search(queryset, term) if term.strip() else queryset


def fuzzy_exact_ingredients(name: str):
    """Ingrédients dont le nom (ou la traduction) égale `name` à la casse/accents/ligatures près."""
    from .models import Ingredient

    term = normalize(name)
    return Ingredient.objects.annotate(
        _n_name=_normalized_expr(F("name")),
        _n_en=_normalized_expr(Coalesce(KeyTextTransform("en", "translations"), Value(""), output_field=TextField())),
    ).filter(Q(_n_name=term) | Q(_n_en=term)).values("pk")
