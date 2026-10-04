"""Rendu HTML des balises Cooklang d'une étape pour les documents serveur (PDF).

Mêmes regex que l'affichage web (frontend/src/utils/cooklangMentions.ts et cooklangTimers.ts) :
`@huile_olive{2%cs}` -> **huile olive**, `#Four` -> matériel souligné, `~{20%minutes}` ->
**20 minutes**. Le texte autour est échappé, seules nos propres balises sont marquées sûres.
"""
import re

from django import template
from django.utils.html import escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()

STEP_TAG_RE = re.compile(
    r"@(?P<ingredient>[^\s@#~{}]+)(?:\{[^}]*\})?"
    # Le nom d'un matériel ne commence pas par un chiffre ("étape #2" reste du texte) et s'arrête
    # à la ponctuation ("le #four." désigne le four).
    r"|#(?P<cookware>[^\s\d@#~{}.,;:!?()][^\s@#~{}.,;:!?()]*)(?:\{[^}]*\})?"
    r"|~(?P<timer_name>[^\s@#~{}]*)\{(?P<timer_meta>[^}]*)\}"
)


def _display_name(name: str) -> str:
    return name.replace("_", " ")


def _timer_text(name: str, meta: str) -> str:
    quantity, _, unit = meta.partition("%")
    return " ".join(filter(None, [quantity.strip(), unit.strip()])) or _display_name(name)


def _render_tag(match: re.Match) -> str:
    if match.group("ingredient"):
        return format_html('<strong class="step-ingredient">{}</strong>', _display_name(match.group("ingredient")))
    if match.group("cookware"):
        return format_html('<span class="step-cookware">{}</span>', _display_name(match.group("cookware")))
    text = _timer_text(match.group("timer_name"), match.group("timer_meta"))
    if not text:
        return ""
    return format_html('<span class="step-timer">{}</span>', text)


@register.filter
def cooklang_step(instruction: str) -> str:
    parts, cursor = [], 0
    for match in STEP_TAG_RE.finditer(instruction or ""):
        parts.append(escape(instruction[cursor : match.start()]))
        parts.append(_render_tag(match))
        cursor = match.end()
    parts.append(escape((instruction or "")[cursor:]))
    return mark_safe("".join(parts))
