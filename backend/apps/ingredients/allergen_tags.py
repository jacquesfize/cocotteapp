"""Allergènes des ingrédients de la bibliothèque (`seed_common_ingredients`).

Clé : nom exact de l'ingrédient. Tout ingrédient de la bibliothèque absent de ce
dictionnaire est considéré comme vérifié *sans* allergène. Les préparations
industrielles (bouillon cube, sauce soja, chorizo, ketchup…) varient selon les marques :
on retient ici les allergènes usuels, à confirmer sur l'étiquette.
"""

DAIRY = ["milk", "lactose"]

ALLERGEN_TAGS = {
    # Céréales à gluten
    "Pâtes": ["gluten"],
    "Flocons d'avoine": ["gluten"],
    "Farine de blé": ["gluten"],
    "Pain complet": ["gluten"],
    "Pain blanc": ["gluten"],
    "Semoule de blé": ["gluten"],
    "Boulgour": ["gluten"],
    "Orge perlé": ["gluten"],
    "Chapelure": ["gluten"],
    # Soja
    "Tofu nature": ["soy"],
    "Tempeh": ["soy"],
    "Edamame": ["soy"],
    "Protéines de soja texturées": ["soy"],
    "Boisson soja nature enrichie": ["soy"],
    "Yaourt de soja nature": ["soy"],
    "Sauce soja": ["soy", "gluten"],
    # Fruits à coque, arachides, sésame
    "Amandes": ["tree_nuts"],
    "Noix": ["tree_nuts"],
    "Noix de cajou": ["tree_nuts"],
    "Noisettes": ["tree_nuts"],
    "Pistaches": ["tree_nuts"],
    "Noix de pécan": ["tree_nuts"],
    "Beurre de cacahuète": ["peanut"],
    "Tahin": ["sesame"],
    "Graines de sésame": ["sesame"],
    "Huile de sésame": ["sesame"],
    # Produits laitiers
    "Lait demi-écrémé": DAIRY,
    "Lait entier": DAIRY,
    "Lait écrémé": DAIRY,
    "Yaourt nature": DAIRY,
    "Emmental": ["milk"],
    "Beurre": DAIRY,
    "Crème fraîche": DAIRY,
    "Fromage blanc": DAIRY,
    "Mozzarella": DAIRY,
    "Feta": DAIRY,
    "Parmesan": ["milk"],
    "Chèvre frais": DAIRY,
    "Comté": ["milk"],
    "Mascarpone": DAIRY,
    "Ricotta": DAIRY,
    "Margarine": ["milk"],
    "Chocolat noir pâtissier": ["milk", "soy"],
    # Œufs
    "Œuf": ["egg"],
    "Mayonnaise": ["egg", "mustard"],
    # Poissons, crustacés, mollusques
    "Saumon": ["fish"],
    "Thon frais": ["fish"],
    "Thon au naturel (boîte)": ["fish"],
    "Cabillaud": ["fish"],
    "Colin": ["fish"],
    "Sardine": ["fish"],
    "Maquereau": ["fish"],
    "Crevettes": ["crustaceans"],
    "Moules": ["molluscs"],
    # Céleri, moutarde, sulfites
    "Céleri branche": ["celery"],
    "Moutarde": ["mustard", "sulphites"],
    "Vinaigre balsamique": ["sulphites"],
    "Bouillon de légumes (cube)": ["celery", "gluten"],
    "Ketchup": ["celery"],
}
