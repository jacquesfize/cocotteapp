from apps.recipes.cooklang import parse


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
