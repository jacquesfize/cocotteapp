"""Minimal parser for a subset of the Cooklang recipe markup language."""
import re
from dataclasses import dataclass, field

INGREDIENT_RE = re.compile(r"@(?P<name>[^\s@#~{}]+)(?:\{(?P<meta>[^}]*)\})?")
COOKWARE_RE = re.compile(r"#(?P<name>[^\s@#~{}]+)(?:\{(?P<meta>[^}]*)\})?")
TIMER_RE = re.compile(r"~(?P<name>[^\s@#~{}]*)\{(?P<meta>[^}]*)\}")


@dataclass
class ParsedIngredient:
    name: str
    quantity: str | None = None
    unit: str | None = None


@dataclass
class ParsedRecipe:
    steps: list = field(default_factory=list)
    # Même texte d'étape, mais avec les balises @ingrédient / ~{durée} conservées (le frontend les
    # affiche en lien / minuteur). Seul le matériel #cookware est aplati.
    tagged_steps: list = field(default_factory=list)
    ingredients: list = field(default_factory=list)
    cookware: list = field(default_factory=list)


def _split_meta(meta):
    if not meta:
        return None, None
    if "%" in meta:
        quantity, unit = meta.split("%", 1)
        return quantity.strip() or None, unit.strip() or None
    return meta.strip() or None, None


def parse(text: str) -> ParsedRecipe:
    result = ParsedRecipe()
    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("--"):
            continue

        for match in COOKWARE_RE.finditer(line):
            result.cookware.append(match.group("name").replace("_", " "))

        for match in INGREDIENT_RE.finditer(line):
            quantity, unit = _split_meta(match.group("meta"))
            result.ingredients.append(
                ParsedIngredient(name=match.group("name").replace("_", " "), quantity=quantity, unit=unit)
            )

        tagged = COOKWARE_RE.sub(lambda m: m.group("name").replace("_", " "), line)
        result.tagged_steps.append(tagged.strip())

        step_text = INGREDIENT_RE.sub(lambda m: m.group("name").replace("_", " "), line)
        step_text = COOKWARE_RE.sub(lambda m: m.group("name").replace("_", " "), step_text)
        step_text = TIMER_RE.sub(lambda m: m.group("meta"), step_text)
        result.steps.append(step_text.strip())

    return result
