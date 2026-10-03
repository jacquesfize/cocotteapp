from pathlib import Path

import pytest

from apps.recipes.cooklang import CooklangParseError, parse

# Fichier réel fourni par le PO : https://recipes.cooklang.org/api/recipes/9441/download
TIRAMISU = (Path(__file__).parent / "fixtures" / "tiramisu.cook").read_text(encoding="utf-8")


def test_parse_ingredient_with_quantity():
    result = parse("Add @salt{1%tsp} and @olive_oil{2%tbsp} to the pan #pan{}.")
    names = [i.name for i in result.ingredients]
    assert "salt" in names
    assert "olive oil" in names
    assert result.cookware == ["pan"]

    salt = next(i for i in result.ingredients if i.name == "salt")
    assert salt.quantity == "1"
    assert salt.unit == "tsp"


def test_parse_ingredient_without_quantity():
    result = parse("Peel the @potato and slice it.")
    assert result.ingredients[0].name == "potato"
    assert result.ingredients[0].quantity is None


def test_parse_strips_annotations_from_steps():
    result = parse("Fry the @onion{1%piece} in a #pan{}.")
    assert result.steps == ["Fry the onion in a pan."]


# --- Parsing délégué à cooklang-py : fichier réel publié sur recipes.cooklang.org -------------


def test_parse_real_world_recipe_metadata():
    result = parse(TIRAMISU)
    assert result.metadata.get("title") == "Tiramisu"
    assert result.metadata.get("servings") == 6
    assert result.metadata.get("prepMinutes") == {"min": 30, "max": 40}


def test_parse_real_world_recipe_ingredients_and_sections():
    result = parse(TIRAMISU)
    names = [i.name for i in result.ingredients]
    assert names[:4] == ["kaffe", "vand", "marsala", "pasteuriseret æggeblomme"]
    assert names.count("sukker") == 2

    kaffe = result.ingredients[0]
    assert (kaffe.quantity, kaffe.unit, kaffe.note, kaffe.section) == ("30", "g", "malet", "Kaffe")
    assert result.ingredients[-1].section == "Servering"
    assert "fin sigte" in result.cookware


def test_parse_real_world_recipe_steps_and_notes():
    result = parse(TIRAMISU)
    # 10 paragraphes d'instructions ; les titres "= Section" et les notes "> ..." n'en sont pas.
    assert len(result.tagged_steps) == 10
    assert not any(step.startswith(("=", ">")) for step in result.tagged_steps)
    assert len(result.notes) == 3
    assert result.notes[0].startswith("Marsala kan udelades.")

    # Noms multi-mots re-sérialisés sans espace pour le rendu frontend, minuteurs conservés.
    assert "@pasteuriseret_æggeblomme{80%g}" in result.tagged_steps[2]
    assert "~piskning_af_æggesnaps{4-5%minutter}" in result.tagged_steps[2]
    assert result.tagged_steps[0].startswith("Bryg stærk kaffe af @kaffe{30%g} (malet) og @vand{300%ml}.")
    assert result.steps[0].startswith("Bryg stærk kaffe af kaffe (malet) og vand.")


def test_paragraphs_span_several_lines():
    result = parse("Mix @flour{200%g}\nwith @water{100%ml}.\n\nBake.")
    assert result.steps == ["Mix flour with water.", "Bake."]


def test_one_step_per_line_without_blank_lines_legacy_metadata_and_comments():
    text = (
        ">> servings: 3\n"
        "-- un commentaire ne fait pas basculer en mode paragraphes\n"
        "Émincer @oignon{2}. -- commentaire de fin de ligne\n"
        "Faire dorer l'@oignon dans @huile_olive{1%cs}."
    )
    result = parse(text)
    assert result.metadata.get("servings") == "3"
    assert result.tagged_steps == ["Émincer @oignon{2}.", "Faire dorer l'@oignon dans @huile_olive{1%cs}."]


def test_note_after_quantity_stops_at_first_closing_parenthesis():
    result = parse("Add @tomato{400%g}(fresh) and stir (gently).")
    assert result.ingredients[0].note == "fresh"
    assert result.steps == ["Add tomato (fresh) and stir (gently)."]


def test_parse_rejects_invalid_front_matter():
    with pytest.raises(CooklangParseError):
        parse("---\ntitle: [unclosed\n---\nMix @flour{1%kg}.")


def test_parse_rejects_text_without_any_step():
    with pytest.raises(CooklangParseError):
        parse("---\ntitle: Vide\n---\n-- rien que des commentaires\n")
