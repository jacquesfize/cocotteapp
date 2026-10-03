"""Cooklang parsing, delegated to the `cooklang-py` library (https://cooklang.org).

`cooklang-py` does the actual markup parsing (YAML front matter, `@ingredient{qty%unit}(note)`,
multi-word names, `#cookware{}`, `~name{timer}`, comments). This module only adapts its output
to what Cocotte needs (see `cooklang_import.py` for the mapping onto the data model):

- **Steps.** Per the Cooklang spec a step is a paragraph (blocks separated by a blank line).
  Cocotte historically used "one step per line" (the YouTube importer agent still writes that),
  so when the body contains no blank line at all, each line is a step instead.
- **Sections** (`= Name` / `== Name ==`) are not steps: they label the ingredients used below
  them (`ParsedIngredient.section`, stored as `RecipeIngredient.group_name`).
- **Notes** (`> text`) are not steps either: they're collected in `ParsedRecipe.notes`.
- **Legacy metadata** (`>> key: value`, Cooklang v1) is merged into the front-matter metadata.
- **Tagged steps** are re-serialized in the syntax the frontend renders
  (`frontend/src/utils/cooklangMentions.ts` / `cooklangTimers.ts`): names can't contain spaces
  there, so `@pasteuriseret æggeblomme{80%g}` becomes `@pasteuriseret_æggeblomme{80%g}`.
  Cookware is flattened to its plain name.
"""
import re
from dataclasses import dataclass, field

import frontmatter
import yaml
from cooklang_py import Cookware, Ingredient, Metadata, Step, Timing

SECTION_RE = re.compile(r"^=+\s*(?P<name>.*?)\s*=*\s*$")
NOTE_RE = re.compile(r"^>(?!>)\s?(?P<text>.*)$")
LEGACY_METADATA_RE = re.compile(r"^>>\s*(?P<key>[^:]+?)\s*:\s*(?P<value>.*?)\s*$")
LINE_COMMENT_RE = re.compile(r"--.*$", re.MULTILINE)
BLOCK_COMMENT_RE = re.compile(r"\[-.*?-\]", re.DOTALL)
# cooklang-py captures a `(note)` greedily up to the *last* ")" before the next tag; the spec
# note ends at the first ")". Truncating the raw text first keeps the rest as step text.
_TAG_WITH_NOTE_RE = re.compile(r"^.[^{}@#~]*?\{[^}]*\}\([^)]*\)")


class CooklangParseError(ValueError):
    """The text can't be parsed as Cooklang (invalid front matter, no step at all)."""


class _Ingredient(Ingredient):
    @classmethod
    def factory(cls, raw: str):
        match = _TAG_WITH_NOTE_RE.match(raw)
        return super().factory(match.group(0) if match else raw)


class _Cookware(Cookware):
    @classmethod
    def factory(cls, raw: str):
        match = _TAG_WITH_NOTE_RE.match(raw)
        return super().factory(match.group(0) if match else raw)


_PREFIXES = {"@": _Ingredient, "#": _Cookware, "~": Timing}


@dataclass
class ParsedIngredient:
    name: str
    quantity: str | None = None
    unit: str | None = None
    note: str | None = None
    # Titre de la section Cooklang (`= Pâte`) où l'ingrédient apparaît, "" hors section.
    section: str = ""


@dataclass
class ParsedRecipe:
    metadata: Metadata = field(default_factory=lambda: Metadata({}))
    steps: list = field(default_factory=list)
    # Même texte d'étape, mais avec les balises @ingrédient / ~{durée} conservées (le frontend les
    # affiche en lien / minuteur). Seul le matériel #cookware est aplati.
    tagged_steps: list = field(default_factory=list)
    ingredients: list = field(default_factory=list)
    cookware: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def _split_quantity(raw_quantity: str | None) -> tuple[str | None, str | None]:
    if not raw_quantity:
        return None, None
    amount, _, unit = raw_quantity.partition("%")
    return amount.strip() or None, unit.strip() or None


def _display_name(name: str) -> str:
    # Convention Cocotte historique : `@huile_olive` désigne l'ingrédient "huile olive".
    return name.replace("_", " ").strip()


def _token_name(name: str) -> str:
    return re.sub(r"\s+", "_", name.strip())


def _render_step(step: Step) -> tuple[str, str]:
    """(texte brut, texte balisé pour le frontend) d'une étape parsée par cooklang-py."""
    plain, tagged = [], []
    for part in step:
        if isinstance(part, Ingredient):
            name = _display_name(part.name)
            note = f" ({part.notes})" if part.notes else ""
            meta = f"{{{part._quantity}}}" if part._quantity else ""
            plain.append(name + note)
            tagged.append(f"@{_token_name(part.name)}{meta}{note}")
        elif isinstance(part, Cookware):
            plain.append(_display_name(part.name))
            tagged.append(_display_name(part.name))
        elif isinstance(part, Timing):
            amount, unit = _split_quantity(part._quantity)
            plain.append(" ".join(filter(None, [amount, unit])) or _display_name(part.name))
            tagged.append(f"~{_token_name(part.name)}{{{part._quantity or ''}}}")
        else:
            plain.append(str(part))
            tagged.append(str(part))
    return "".join(plain).strip(), "".join(tagged).strip()


def _extract_legacy_metadata(body: str) -> tuple[dict, str]:
    metadata, kept = {}, []
    for line in body.splitlines():
        match = LEGACY_METADATA_RE.match(line.strip())
        if match:
            metadata[match.group("key")] = match.group("value")
        else:
            kept.append(line)
    return metadata, "\n".join(kept)


def _blocks(body: str) -> list[str]:
    """Découpe le corps en blocs : paragraphes (spec) si le texte contient une ligne vide entre
    deux lignes de contenu, sinon une ligne = un bloc (convention Cocotte historique). Un titre de
    section est toujours un bloc à part entière."""
    lines = [line.strip() for line in body.strip().splitlines()]
    paragraph_mode = "" in lines

    blocks, current = [], []

    def flush():
        if current:
            if current[0].startswith(">") and not current[0].startswith(">>"):
                current[1:] = [NOTE_RE.sub(r"\g<text>", line) for line in current[1:]]
            blocks.append(" ".join(current))
            current.clear()

    for line in lines:
        if not line:
            flush()
        elif SECTION_RE.match(line):
            flush()
            blocks.append(line)
        else:
            current.append(line)
            if not paragraph_mode:
                flush()
    flush()
    return blocks


def parse(text: str) -> ParsedRecipe:
    try:
        raw_metadata, body = frontmatter.parse(text)
    except yaml.YAMLError as exc:
        raise CooklangParseError(f"Invalid front matter: {exc}") from exc

    legacy_metadata, body = _extract_legacy_metadata(body)
    body = BLOCK_COMMENT_RE.sub("", body)
    # Une ligne entièrement commentée disparaît (sans laisser de ligne vide, qui ferait basculer
    # un texte "une étape par ligne" en mode paragraphes).
    body = "\n".join(line for line in body.splitlines() if not line.strip().startswith("--"))
    body = LINE_COMMENT_RE.sub("", body)

    result = ParsedRecipe(metadata=Metadata({**legacy_metadata, **(raw_metadata or {})}))
    section = ""
    for block in _blocks(body):
        if block.startswith("="):
            section = SECTION_RE.match(block).group("name")
            continue
        note = NOTE_RE.match(block)
        if note:
            if note.group("text").strip():
                result.notes.append(note.group("text").strip())
            continue

        step = Step(block, prefixes=_PREFIXES)
        if not len(step):
            continue
        for ingredient in step.ingredients:
            quantity, unit = _split_quantity(ingredient._quantity)
            result.ingredients.append(
                ParsedIngredient(
                    name=_display_name(ingredient.name),
                    quantity=quantity,
                    unit=unit,
                    note=ingredient.notes,
                    section=section,
                )
            )
        result.cookware.extend(_display_name(cookware.name) for cookware in step.cookware)

        plain, tagged = _render_step(step)
        if plain:
            result.steps.append(plain)
            result.tagged_steps.append(tagged)

    if not result.steps:
        raise CooklangParseError("No Cooklang step found.")
    return result
