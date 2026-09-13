from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.ingredients.models import Ingredient, IngredientCategory, Unit

# Valeurs nutritionnelles approximatives pour 100 g (ou 100 ml pour les liquides),
# arrondies à partir de tables de composition usuelles (Ciqual/USDA). Ce sont des
# ordres de grandeur pour aider à repérer les manques dans un menu, pas des valeurs
# de laboratoire ni un avis médical.
#
# Champs : category, default_unit, available_months (mois de pleine saison ; liste
# vide = disponible toute l'année, ce qui est le cas de la plupart des produits secs,
# laitiers, huiles et épices), puis les nutriments (kcal, protéines, glucides,
# lipides, fibres, fer, B12, calcium, oméga-3, zinc). Les clés absentes valent 0.
#
# carbon_kg_co2e_per_kg : empreinte carbone en kg CO2e par kg (ou litre) de produit,
# ordre de grandeur tiré d'Agribalyse (ADEME) et de Poore & Nemecek (2018, via Our
# World in Data). Ce sont des moyennes mondiales/françaises, pas des valeurs
# spécifiques à un producteur — utiles pour comparer des catégories d'aliments entre
# elles, pas pour un bilan carbone précis. Laissée à 0 pour les condiments/épices
# dont l'empreinte est mal documentée ou négligeable au regard des quantités utilisées.
INGREDIENTS = [
    # --- Légumes ---
    {"name": "Tomate", "category": "vegetable", "unit": "g", "months": [6, 7, 8, 9],
     "calories_kcal": 18, "protein_g": 0.9, "carbs_g": 3.9, "fat_g": 0.2, "fiber_g": 1.2,
     "iron_mg": 0.3, "calcium_mg": 10, "zinc_mg": 0.2, "carbon_kg_co2e_per_kg": 1.4},
    {"name": "Oignon", "category": "vegetable", "unit": "g", "months": [],
     "calories_kcal": 40, "protein_g": 1.1, "carbs_g": 9.3, "fat_g": 0.1, "fiber_g": 1.7,
     "iron_mg": 0.2, "calcium_mg": 23, "zinc_mg": 0.2, "carbon_kg_co2e_per_kg": 0.4},
    {"name": "Ail", "category": "vegetable", "unit": "g", "months": [],
     "calories_kcal": 149, "protein_g": 6.4, "carbs_g": 33.1, "fat_g": 0.5, "fiber_g": 2.1,
     "iron_mg": 1.7, "calcium_mg": 181, "zinc_mg": 1.2, "carbon_kg_co2e_per_kg": 0.6},
    {"name": "Carotte", "category": "vegetable", "unit": "g", "months": [6, 7, 8, 9, 10],
     "calories_kcal": 41, "protein_g": 0.9, "carbs_g": 9.6, "fat_g": 0.2, "fiber_g": 2.8,
     "iron_mg": 0.3, "calcium_mg": 33, "zinc_mg": 0.2, "carbon_kg_co2e_per_kg": 0.4},
    {"name": "Courgette", "category": "vegetable", "unit": "g", "months": [6, 7, 8, 9],
     "calories_kcal": 17, "protein_g": 1.2, "carbs_g": 3.1, "fat_g": 0.3, "fiber_g": 1.0,
     "iron_mg": 0.4, "calcium_mg": 16, "zinc_mg": 0.3, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Poivron rouge", "category": "vegetable", "unit": "g", "months": [7, 8, 9],
     "calories_kcal": 31, "protein_g": 1.0, "carbs_g": 6.0, "fat_g": 0.3, "fiber_g": 2.1,
     "iron_mg": 0.4, "calcium_mg": 7, "zinc_mg": 0.3, "carbon_kg_co2e_per_kg": 1.6},
    {"name": "Épinard", "category": "vegetable", "unit": "g", "months": [3, 4, 5, 10, 11],
     "calories_kcal": 23, "protein_g": 2.9, "carbs_g": 3.6, "fat_g": 0.4, "fiber_g": 2.2,
     "iron_mg": 2.7, "calcium_mg": 99, "zinc_mg": 0.5, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Chou kale", "category": "vegetable", "unit": "g", "months": [10, 11, 12, 1, 2],
     "calories_kcal": 49, "protein_g": 4.3, "carbs_g": 8.8, "fat_g": 0.9, "fiber_g": 3.6,
     "iron_mg": 1.5, "calcium_mg": 150, "zinc_mg": 0.4, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Brocoli", "category": "vegetable", "unit": "g", "months": [9, 10, 11, 12],
     "calories_kcal": 34, "protein_g": 2.8, "carbs_g": 6.6, "fat_g": 0.4, "fiber_g": 2.6,
     "iron_mg": 0.7, "calcium_mg": 47, "zinc_mg": 0.4, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Chou-fleur", "category": "vegetable", "unit": "g", "months": [9, 10, 11],
     "calories_kcal": 25, "protein_g": 1.9, "carbs_g": 5.0, "fat_g": 0.3, "fiber_g": 2.0,
     "iron_mg": 0.4, "calcium_mg": 22, "zinc_mg": 0.3, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Pomme de terre", "category": "vegetable", "unit": "g", "months": [9, 10, 11, 12, 1, 2],
     "calories_kcal": 77, "protein_g": 2.0, "carbs_g": 17.5, "fat_g": 0.1, "fiber_g": 2.2,
     "iron_mg": 0.8, "calcium_mg": 12, "zinc_mg": 0.3, "carbon_kg_co2e_per_kg": 0.3},
    {"name": "Potiron", "category": "vegetable", "unit": "g", "months": [9, 10, 11, 12],
     "calories_kcal": 26, "protein_g": 1.0, "carbs_g": 6.5, "fat_g": 0.1, "fiber_g": 0.5,
     "iron_mg": 0.8, "calcium_mg": 21, "zinc_mg": 0.3, "carbon_kg_co2e_per_kg": 0.4},
    {"name": "Poireau", "category": "vegetable", "unit": "g", "months": [10, 11, 12, 1, 2, 3],
     "calories_kcal": 61, "protein_g": 1.5, "carbs_g": 14.2, "fat_g": 0.3, "fiber_g": 1.8,
     "iron_mg": 2.1, "calcium_mg": 59, "zinc_mg": 0.1, "carbon_kg_co2e_per_kg": 0.4},
    {"name": "Champignon de Paris", "category": "vegetable", "unit": "g", "months": [],
     "calories_kcal": 22, "protein_g": 3.1, "carbs_g": 3.3, "fat_g": 0.3, "fiber_g": 1.0,
     "iron_mg": 0.5, "calcium_mg": 3, "zinc_mg": 0.5, "carbon_kg_co2e_per_kg": 1.3},
    {"name": "Aubergine", "category": "vegetable", "unit": "g", "months": [7, 8, 9],
     "calories_kcal": 25, "protein_g": 1.0, "carbs_g": 5.7, "fat_g": 0.2, "fiber_g": 3.0,
     "iron_mg": 0.2, "calcium_mg": 9, "zinc_mg": 0.2, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Haricot vert", "category": "vegetable", "unit": "g", "months": [6, 7, 8, 9],
     "calories_kcal": 31, "protein_g": 1.8, "carbs_g": 7.0, "fat_g": 0.2, "fiber_g": 3.4,
     "iron_mg": 1.0, "calcium_mg": 37, "zinc_mg": 0.2, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Salade verte", "category": "vegetable", "unit": "g", "months": [4, 5, 6, 7, 8, 9],
     "calories_kcal": 15, "protein_g": 1.4, "carbs_g": 2.9, "fat_g": 0.2, "fiber_g": 1.3,
     "iron_mg": 0.9, "calcium_mg": 36, "zinc_mg": 0.2, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Betterave", "category": "vegetable", "unit": "g", "months": [6, 7, 8, 9, 10],
     "calories_kcal": 43, "protein_g": 1.6, "carbs_g": 9.6, "fat_g": 0.2, "fiber_g": 2.8,
     "iron_mg": 0.8, "calcium_mg": 16, "zinc_mg": 0.4, "carbon_kg_co2e_per_kg": 0.4},
    # --- Fruits ---
    {"name": "Pomme", "category": "fruit", "unit": "piece", "months": [9, 10, 11, 12, 1],
     "calories_kcal": 52, "protein_g": 0.3, "carbs_g": 13.8, "fat_g": 0.2, "fiber_g": 2.4,
     "iron_mg": 0.1, "calcium_mg": 6, "carbon_kg_co2e_per_kg": 0.4},
    {"name": "Banane", "category": "fruit", "unit": "piece", "months": [],
     "calories_kcal": 89, "protein_g": 1.1, "carbs_g": 22.8, "fat_g": 0.3, "fiber_g": 2.6,
     "iron_mg": 0.3, "calcium_mg": 5, "zinc_mg": 0.2, "carbon_kg_co2e_per_kg": 0.9},
    {"name": "Orange", "category": "fruit", "unit": "piece", "months": [12, 1, 2, 3],
     "calories_kcal": 47, "protein_g": 0.9, "carbs_g": 11.8, "fat_g": 0.1, "fiber_g": 2.4,
     "iron_mg": 0.1, "calcium_mg": 40, "carbon_kg_co2e_per_kg": 0.4},
    {"name": "Citron", "category": "fruit", "unit": "piece", "months": [11, 12, 1, 2, 3],
     "calories_kcal": 29, "protein_g": 1.1, "carbs_g": 9.3, "fat_g": 0.3, "fiber_g": 2.8,
     "iron_mg": 0.6, "calcium_mg": 26, "carbon_kg_co2e_per_kg": 0.4},
    {"name": "Fraise", "category": "fruit", "unit": "g", "months": [5, 6, 7],
     "calories_kcal": 32, "protein_g": 0.7, "carbs_g": 7.7, "fat_g": 0.3, "fiber_g": 2.0,
     "iron_mg": 0.4, "calcium_mg": 16, "carbon_kg_co2e_per_kg": 1.1},
    {"name": "Avocat", "category": "fruit", "unit": "piece", "months": [],
     "calories_kcal": 160, "protein_g": 2.0, "carbs_g": 8.5, "fat_g": 14.7, "fiber_g": 6.7,
     "iron_mg": 0.6, "calcium_mg": 12, "omega3_g": 0.1, "zinc_mg": 0.6, "carbon_kg_co2e_per_kg": 2.5},
    # --- Légumineuses ---
    {"name": "Lentilles corail", "category": "legume", "unit": "g", "months": [],
     "calories_kcal": 352, "protein_g": 24.6, "carbs_g": 63.4, "fat_g": 1.1, "fiber_g": 10.7,
     "iron_mg": 7.5, "calcium_mg": 35, "zinc_mg": 3.3, "carbon_kg_co2e_per_kg": 0.9},
    {"name": "Lentilles vertes", "category": "legume", "unit": "g", "months": [],
     "calories_kcal": 353, "protein_g": 25.8, "carbs_g": 60.1, "fat_g": 1.1, "fiber_g": 10.7,
     "iron_mg": 6.5, "calcium_mg": 56, "zinc_mg": 3.6, "carbon_kg_co2e_per_kg": 0.9},
    {"name": "Pois chiches", "category": "legume", "unit": "g", "months": [],
     "calories_kcal": 364, "protein_g": 19.3, "carbs_g": 60.7, "fat_g": 6.0, "fiber_g": 17.4,
     "iron_mg": 6.2, "calcium_mg": 105, "zinc_mg": 3.4, "carbon_kg_co2e_per_kg": 0.8},
    {"name": "Haricots rouges", "category": "legume", "unit": "g", "months": [],
     "calories_kcal": 333, "protein_g": 23.6, "carbs_g": 60.0, "fat_g": 0.8, "fiber_g": 15.2,
     "iron_mg": 8.2, "calcium_mg": 143, "zinc_mg": 2.8, "carbon_kg_co2e_per_kg": 0.9},
    {"name": "Tofu nature", "category": "legume", "unit": "g", "months": [],
     "calories_kcal": 76, "protein_g": 8.1, "carbs_g": 1.9, "fat_g": 4.8, "fiber_g": 0.3,
     "iron_mg": 5.4, "calcium_mg": 350, "zinc_mg": 0.8, "carbon_kg_co2e_per_kg": 2.0},
    {"name": "Tempeh", "category": "legume", "unit": "g", "months": [],
     "calories_kcal": 195, "protein_g": 20.3, "carbs_g": 7.6, "fat_g": 11.4, "fiber_g": 9.0,
     "iron_mg": 2.7, "calcium_mg": 111, "zinc_mg": 1.1, "carbon_kg_co2e_per_kg": 1.5},
    # --- Céréales / féculents ---
    {"name": "Riz basmati", "category": "grain", "unit": "g", "months": [],
     "calories_kcal": 349, "protein_g": 7.1, "carbs_g": 78.0, "fat_g": 0.6, "fiber_g": 1.4,
     "iron_mg": 0.8, "calcium_mg": 10, "zinc_mg": 1.1, "carbon_kg_co2e_per_kg": 4.0},
    {"name": "Riz complet", "category": "grain", "unit": "g", "months": [],
     "calories_kcal": 362, "protein_g": 7.5, "carbs_g": 76.2, "fat_g": 2.7, "fiber_g": 3.5,
     "iron_mg": 1.5, "calcium_mg": 23, "zinc_mg": 2.0, "carbon_kg_co2e_per_kg": 4.0},
    {"name": "Pâtes", "category": "grain", "unit": "g", "months": [],
     "calories_kcal": 371, "protein_g": 13.0, "carbs_g": 74.7, "fat_g": 1.5, "fiber_g": 3.2,
     "iron_mg": 1.3, "calcium_mg": 21, "zinc_mg": 1.1, "carbon_kg_co2e_per_kg": 1.4},
    {"name": "Quinoa", "category": "grain", "unit": "g", "months": [],
     "calories_kcal": 368, "protein_g": 14.1, "carbs_g": 64.2, "fat_g": 6.1, "fiber_g": 7.0,
     "iron_mg": 4.6, "calcium_mg": 47, "zinc_mg": 3.1, "carbon_kg_co2e_per_kg": 1.6},
    {"name": "Flocons d'avoine", "category": "grain", "unit": "g", "months": [],
     "calories_kcal": 379, "protein_g": 13.5, "carbs_g": 67.7, "fat_g": 7.0, "fiber_g": 10.1,
     "iron_mg": 4.7, "calcium_mg": 54, "zinc_mg": 4.0, "carbon_kg_co2e_per_kg": 0.9},
    {"name": "Farine de blé", "category": "grain", "unit": "g", "months": [],
     "calories_kcal": 364, "protein_g": 10.3, "carbs_g": 76.3, "fat_g": 1.0, "fiber_g": 2.7,
     "iron_mg": 1.2, "calcium_mg": 15, "zinc_mg": 0.7, "carbon_kg_co2e_per_kg": 1.1},
    {"name": "Pain complet", "category": "grain", "unit": "g", "months": [],
     "calories_kcal": 247, "protein_g": 9.0, "carbs_g": 41.3, "fat_g": 3.4, "fiber_g": 7.0,
     "iron_mg": 2.5, "calcium_mg": 54, "zinc_mg": 1.4, "carbon_kg_co2e_per_kg": 1.2},
    {"name": "Semoule de blé", "category": "grain", "unit": "g", "months": [],
     "calories_kcal": 376, "protein_g": 12.8, "carbs_g": 77.4, "fat_g": 0.6, "fiber_g": 5.0,
     "iron_mg": 1.3, "calcium_mg": 24, "zinc_mg": 0.8, "carbon_kg_co2e_per_kg": 1.1},
    # --- Noix / graines ---
    {"name": "Amandes", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 579, "protein_g": 21.2, "carbs_g": 21.6, "fat_g": 49.9, "fiber_g": 12.5,
     "iron_mg": 3.7, "calcium_mg": 269, "zinc_mg": 3.1, "carbon_kg_co2e_per_kg": 2.3},
    {"name": "Noix", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 654, "protein_g": 15.2, "carbs_g": 13.7, "fat_g": 65.2, "fiber_g": 6.7,
     "iron_mg": 2.9, "calcium_mg": 98, "omega3_g": 9.1, "zinc_mg": 3.1, "carbon_kg_co2e_per_kg": 0.3},
    {"name": "Noix de cajou", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 553, "protein_g": 18.2, "carbs_g": 30.2, "fat_g": 43.9, "fiber_g": 3.3,
     "iron_mg": 6.7, "calcium_mg": 37, "zinc_mg": 5.8, "carbon_kg_co2e_per_kg": 2.5},
    {"name": "Graines de courge", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 559, "protein_g": 30.2, "carbs_g": 10.7, "fat_g": 49.0, "fiber_g": 6.0,
     "iron_mg": 8.8, "calcium_mg": 46, "zinc_mg": 7.8, "carbon_kg_co2e_per_kg": 1.0},
    {"name": "Graines de tournesol", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 584, "protein_g": 20.8, "carbs_g": 20.0, "fat_g": 51.5, "fiber_g": 8.6,
     "iron_mg": 5.3, "calcium_mg": 78, "zinc_mg": 5.0, "carbon_kg_co2e_per_kg": 0.8},
    {"name": "Graines de lin", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 534, "protein_g": 18.3, "carbs_g": 28.9, "fat_g": 42.2, "fiber_g": 27.3,
     "iron_mg": 5.7, "calcium_mg": 255, "omega3_g": 22.8, "zinc_mg": 4.3, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Graines de chia", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 486, "protein_g": 16.5, "carbs_g": 42.1, "fat_g": 30.7, "fiber_g": 34.4,
     "iron_mg": 7.7, "calcium_mg": 631, "omega3_g": 17.8, "zinc_mg": 4.6, "carbon_kg_co2e_per_kg": 1.0},
    {"name": "Beurre de cacahuète", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 588, "protein_g": 25.1, "carbs_g": 20.0, "fat_g": 50.4, "fiber_g": 6.0,
     "iron_mg": 1.9, "calcium_mg": 43, "zinc_mg": 2.9, "carbon_kg_co2e_per_kg": 2.9},
    {"name": "Tahin", "category": "nut_seed", "unit": "g", "months": [],
     "calories_kcal": 595, "protein_g": 17.0, "carbs_g": 21.2, "fat_g": 53.8, "fiber_g": 9.3,
     "iron_mg": 9.0, "calcium_mg": 426, "zinc_mg": 4.6, "carbon_kg_co2e_per_kg": 1.0},
    # --- Produits laitiers (et alternatives végétales) ---
    {"name": "Lait demi-écrémé", "category": "dairy", "unit": "ml", "months": [],
     "calories_kcal": 46, "protein_g": 3.3, "carbs_g": 4.8, "fat_g": 1.5,
     "vitamin_b12_ug": 0.4, "calcium_mg": 120, "zinc_mg": 0.4, "carbon_kg_co2e_per_kg": 3.2},
    {"name": "Yaourt nature", "category": "dairy", "unit": "g", "months": [],
     "calories_kcal": 61, "protein_g": 3.5, "carbs_g": 4.7, "fat_g": 3.3,
     "vitamin_b12_ug": 0.4, "calcium_mg": 125, "zinc_mg": 0.6, "carbon_kg_co2e_per_kg": 2.5},
    {"name": "Emmental", "category": "dairy", "unit": "g", "months": [],
     "calories_kcal": 380, "protein_g": 28.0, "carbs_g": 0.5, "fat_g": 29.7,
     "iron_mg": 0.3, "vitamin_b12_ug": 1.9, "calcium_mg": 970, "zinc_mg": 4.4, "carbon_kg_co2e_per_kg": 21.0},
    {"name": "Beurre", "category": "dairy", "unit": "g", "months": [],
     "calories_kcal": 745, "protein_g": 0.7, "carbs_g": 0.6, "fat_g": 82.5,
     "vitamin_b12_ug": 0.1, "calcium_mg": 15, "carbon_kg_co2e_per_kg": 12.0},
    {"name": "Crème fraîche", "category": "dairy", "unit": "g", "months": [],
     "calories_kcal": 292, "protein_g": 2.2, "carbs_g": 3.0, "fat_g": 30.0,
     "vitamin_b12_ug": 0.3, "calcium_mg": 90, "zinc_mg": 0.3, "carbon_kg_co2e_per_kg": 6.0},
    {"name": "Boisson soja nature enrichie", "category": "dairy", "unit": "ml", "months": [],
     "calories_kcal": 33, "protein_g": 3.3, "carbs_g": 0.5, "fat_g": 1.8, "fiber_g": 0.5,
     "vitamin_b12_ug": 0.38, "calcium_mg": 120, "zinc_mg": 0.3, "carbon_kg_co2e_per_kg": 1.0},
    {"name": "Boisson avoine enrichie", "category": "dairy", "unit": "ml", "months": [],
     "calories_kcal": 43, "protein_g": 1.0, "carbs_g": 6.7, "fat_g": 1.5, "fiber_g": 0.8,
     "vitamin_b12_ug": 0.38, "calcium_mg": 120, "zinc_mg": 0.1, "carbon_kg_co2e_per_kg": 0.9},
    {"name": "Yaourt de soja nature", "category": "dairy", "unit": "g", "months": [],
     "calories_kcal": 55, "protein_g": 3.8, "carbs_g": 3.9, "fat_g": 2.5, "fiber_g": 0.8,
     "calcium_mg": 45, "zinc_mg": 0.3, "carbon_kg_co2e_per_kg": 1.0},
    # --- Viande / poisson ---
    {"name": "Blanc de poulet", "category": "meat_fish", "unit": "g", "months": [],
     "calories_kcal": 165, "protein_g": 31.0, "fat_g": 3.6,
     "iron_mg": 0.7, "vitamin_b12_ug": 0.3, "zinc_mg": 1.0, "carbon_kg_co2e_per_kg": 6.9},
    {"name": "Bœuf haché 5%", "category": "meat_fish", "unit": "g", "months": [],
     "calories_kcal": 137, "protein_g": 21.0, "fat_g": 5.0,
     "iron_mg": 2.6, "vitamin_b12_ug": 2.6, "zinc_mg": 4.8, "carbon_kg_co2e_per_kg": 27.0},
    {"name": "Dinde (blanc)", "category": "meat_fish", "unit": "g", "months": [],
     "calories_kcal": 135, "protein_g": 29.0, "fat_g": 1.7,
     "iron_mg": 1.4, "vitamin_b12_ug": 0.3, "zinc_mg": 1.5, "carbon_kg_co2e_per_kg": 5.7},
    {"name": "Saumon", "category": "meat_fish", "unit": "g", "months": [],
     "calories_kcal": 208, "protein_g": 20.4, "fat_g": 13.4,
     "iron_mg": 0.3, "vitamin_b12_ug": 3.2, "omega3_g": 2.3, "zinc_mg": 0.6, "carbon_kg_co2e_per_kg": 5.4},
    {"name": "Thon frais", "category": "meat_fish", "unit": "g", "months": [],
     "calories_kcal": 144, "protein_g": 23.3, "fat_g": 4.9,
     "iron_mg": 1.0, "vitamin_b12_ug": 2.2, "omega3_g": 1.3, "zinc_mg": 0.6, "carbon_kg_co2e_per_kg": 6.1},
    # --- Œuf ---
    {"name": "Œuf", "category": "egg", "unit": "piece", "months": [],
     "calories_kcal": 143, "protein_g": 12.6, "carbs_g": 0.7, "fat_g": 9.5,
     "iron_mg": 1.8, "vitamin_b12_ug": 0.9, "calcium_mg": 56, "zinc_mg": 1.3, "carbon_kg_co2e_per_kg": 4.5},
    # --- Matières grasses ---
    {"name": "Huile d'olive", "category": "fat", "unit": "ml", "months": [],
     "calories_kcal": 884, "fat_g": 100, "omega3_g": 0.8, "carbon_kg_co2e_per_kg": 5.4},
    {"name": "Huile de colza", "category": "fat", "unit": "ml", "months": [],
     "calories_kcal": 884, "fat_g": 100, "omega3_g": 9.1, "carbon_kg_co2e_per_kg": 3.5},
    {"name": "Huile de tournesol", "category": "fat", "unit": "ml", "months": [],
     "calories_kcal": 884, "fat_g": 100, "omega3_g": 0.2, "carbon_kg_co2e_per_kg": 3.5},
    # --- Condiments / épices ---
    {"name": "Sel", "category": "condiment", "unit": "g", "months": []},
    {"name": "Poivre", "category": "condiment", "unit": "g", "months": [],
     "calories_kcal": 251, "protein_g": 10.4, "carbs_g": 63.9, "fiber_g": 25.3,
     "iron_mg": 9.7, "calcium_mg": 437, "zinc_mg": 1.2},
    {"name": "Levure maltée enrichie en B12", "category": "condiment", "unit": "g", "months": [],
     "calories_kcal": 359, "protein_g": 45.0, "carbs_g": 36.0, "fat_g": 4.0, "fiber_g": 20.0,
     "iron_mg": 4.0, "vitamin_b12_ug": 15.0, "calcium_mg": 30, "zinc_mg": 6.0},
    {"name": "Sauce soja", "category": "condiment", "unit": "ml", "months": [],
     "calories_kcal": 53, "protein_g": 8.1, "carbs_g": 4.9, "fat_g": 0.1, "calcium_mg": 20},
    {"name": "Miel", "category": "condiment", "unit": "g", "months": [],
     "calories_kcal": 304, "carbs_g": 82.4, "calcium_mg": 6, "carbon_kg_co2e_per_kg": 0.5},
    {"name": "Sucre", "category": "condiment", "unit": "g", "months": [],
     "calories_kcal": 400, "carbs_g": 100, "carbon_kg_co2e_per_kg": 0.8},
    {"name": "Moutarde", "category": "condiment", "unit": "g", "months": [],
     "calories_kcal": 66, "protein_g": 4.4, "carbs_g": 5.8, "fat_g": 3.3,
     "iron_mg": 1.6, "calcium_mg": 60},
    {"name": "Cumin", "category": "condiment", "unit": "g", "months": [],
     "calories_kcal": 375, "protein_g": 17.7, "carbs_g": 44.2, "fat_g": 22.3, "fiber_g": 10.5,
     "iron_mg": 66.4, "calcium_mg": 931, "zinc_mg": 4.8},
    {"name": "Curcuma", "category": "condiment", "unit": "g", "months": [],
     "calories_kcal": 312, "protein_g": 9.7, "carbs_g": 67.1, "fat_g": 3.3, "fiber_g": 22.7,
     "iron_mg": 41.4, "calcium_mg": 183, "zinc_mg": 4.4},
    {"name": "Paprika", "category": "condiment", "unit": "g", "months": [],
     "calories_kcal": 282, "protein_g": 14.1, "carbs_g": 54.0, "fat_g": 13.0, "fiber_g": 34.9,
     "iron_mg": 21.1, "calcium_mg": 229, "zinc_mg": 4.3},
]

NUTRIENT_FIELD_NAMES = [
    "calories_kcal",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
    "vitamin_b12_ug",
    "calcium_mg",
    "omega3_g",
    "zinc_mg",
]

CARBON_FIELD_NAME = "carbon_kg_co2e_per_kg"


class Command(BaseCommand):
    help = "Peuple des ingrédients courants avec des valeurs nutritionnelles, une empreinte carbone et une saisonnalité réalistes."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for entry in INGREDIENTS:
            defaults = {
                "name": entry["name"],
                "category": IngredientCategory(entry["category"]),
                "default_unit": Unit(entry["unit"]),
                "available_months": entry["months"],
            }
            for field in NUTRIENT_FIELD_NAMES:
                defaults[field] = Decimal(str(entry.get(field, 0)))
            defaults[CARBON_FIELD_NAME] = Decimal(str(entry.get(CARBON_FIELD_NAME, 0)))

            # Recherche insensible à la casse : un ingrédient "tomate" créé à la volée
            # (via le sélecteur de recette) doit être enrichi plutôt que dupliqué en
            # "Tomate" — les deux produiraient sinon le même slug.
            existing = Ingredient.objects.filter(name__iexact=entry["name"]).first()
            if existing:
                for field, value in defaults.items():
                    setattr(existing, field, value)
                existing.save()
                updated_count += 1
            else:
                Ingredient.objects.create(**defaults)
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Ingrédients : {created_count} créés, {updated_count} mis à jour.")
        )
