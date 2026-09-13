from unittest.mock import MagicMock, patch

import requests

from apps.ingredients.services import lookup_nutrition_suggestion


def _mock_response(status_code=200, json_data=None, raise_for_status_error=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    if raise_for_status_error:
        response.raise_for_status.side_effect = raise_for_status_error
    return response


def test_lookup_nutrition_suggestion_maps_known_macronutrients():
    payload = {
        "products": [
            {
                "product_name": "Ail",
                "nutriments": {
                    "energy-kcal_100g": 149,
                    "proteins_100g": 6.4,
                    "carbohydrates_100g": 33.1,
                    "fat_100g": 0.5,
                    "fiber_100g": 2.1,
                    "iron_100g": 1.7,
                },
            }
        ]
    }
    with patch("apps.ingredients.services.requests.get", return_value=_mock_response(json_data=payload)):
        suggestion = lookup_nutrition_suggestion("ail")

    assert suggestion == {
        "calories_kcal": 149,
        "protein_g": 6.4,
        "carbs_g": 33.1,
        "fat_g": 0.5,
        "fiber_g": 2.1,
    }


def test_lookup_nutrition_suggestion_accepts_numeric_strings():
    payload = {"products": [{"nutriments": {"energy-kcal_100g": "80.6", "proteins_100g": "1.2"}}]}
    with patch("apps.ingredients.services.requests.get", return_value=_mock_response(json_data=payload)):
        suggestion = lookup_nutrition_suggestion("garlic")

    assert suggestion == {"calories_kcal": 80.6, "protein_g": 1.2}


def test_lookup_nutrition_suggestion_returns_none_when_no_products():
    with patch(
        "apps.ingredients.services.requests.get", return_value=_mock_response(json_data={"products": []})
    ):
        assert lookup_nutrition_suggestion("ingrédient inconnu") is None


def test_lookup_nutrition_suggestion_returns_none_when_no_known_nutriments():
    payload = {"products": [{"nutriments": {"sodium_100g": 0.4}}]}
    with patch("apps.ingredients.services.requests.get", return_value=_mock_response(json_data=payload)):
        assert lookup_nutrition_suggestion("sel") is None


def test_lookup_nutrition_suggestion_returns_none_on_timeout():
    with patch("apps.ingredients.services.requests.get", side_effect=requests.Timeout):
        assert lookup_nutrition_suggestion("ail") is None


def test_lookup_nutrition_suggestion_returns_none_on_http_error():
    response = _mock_response(status_code=503, raise_for_status_error=requests.HTTPError("503"))
    with patch("apps.ingredients.services.requests.get", return_value=response):
        assert lookup_nutrition_suggestion("ail") is None


def test_lookup_nutrition_suggestion_returns_none_on_invalid_json():
    response = _mock_response()
    response.json.side_effect = ValueError("invalid json")
    with patch("apps.ingredients.services.requests.get", return_value=response):
        assert lookup_nutrition_suggestion("ail") is None
