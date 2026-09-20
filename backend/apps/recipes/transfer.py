"""Export / import d'une bibliothèque de recettes sous forme d'archive ZIP portable.

L'archive contient `recipes.json` (format versionné) et un dossier `images/` avec les images
téléversées. Les ingrédients sont embarqués en entier (nutrition, saisonnalité...) pour pouvoir
être recréés sur une instance qui ne les connaît pas ; à l'import ils sont rapprochés d'abord
par slug puis par nom, et l'ingrédient existant de l'instance cible n'est jamais modifié.
"""

import json
import zipfile
from io import BytesIO
from pathlib import PurePosixPath

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import DatabaseError, transaction
from django.db.models import Q

from apps.accounts.models import DietType
from apps.ingredients.models import Ingredient, IngredientCategory, Unit

from .models import Recipe, RecipeIngredient, RecipeStep, SourceType, Tag, TagKind

FORMAT_NAME = "cocotte-recipes"
FORMAT_VERSION = 1
MANIFEST_NAME = "recipes.json"
IMAGES_DIR = "images/"

MAX_ARCHIVE_BYTES = 200 * 1024 * 1024  # taille décompressée cumulée (protection zip bomb)
MAX_RECIPES = 5000
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

INGREDIENT_NUMERIC_FIELDS = [
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
    "carbon_kg_co2e_per_kg",
]


class ArchiveError(Exception):
    """L'archive n'est pas un export Cocotte lisible."""


# --- Export ---------------------------------------------------------------------------------


def _serialize_ingredient(ingredient):
    data = {
        "name": ingredient.name,
        "slug": ingredient.slug,
        "category": ingredient.category,
        "default_unit": ingredient.default_unit,
        "available_months": list(ingredient.available_months),
        "translations": ingredient.translations,
    }
    for field in INGREDIENT_NUMERIC_FIELDS:
        data[field] = str(getattr(ingredient, field))
    return data


def build_export_archive(recipes):
    """Renvoie les octets d'une archive ZIP contenant `recipes` (un queryset de Recipe)."""
    recipes = list(
        recipes.select_related("author").prefetch_related("recipe_ingredients__ingredient", "steps", "tags").order_by("id")
    )
    refs = {recipe.pk: f"r{index}" for index, recipe in enumerate(recipes, start=1)}

    payload = []
    images = {}
    for recipe in recipes:
        image_path = ""
        if recipe.image:
            try:
                extension = PurePosixPath(recipe.image.name).suffix.lower()
                with recipe.image.open("rb") as handle:
                    content = handle.read()
                image_path = f"{IMAGES_DIR}{refs[recipe.pk]}{extension}"
                images[image_path] = content
            except (FileNotFoundError, ValueError, OSError):
                image_path = ""  # fichier disparu du disque : on exporte la recette sans image

        payload.append(
            {
                "ref": refs[recipe.pk],
                "title": recipe.title,
                "author": recipe.author.username,  # informatif : l'import rattache à l'importeur
                "description": recipe.description,
                "servings": recipe.servings,
                "prep_time_minutes": recipe.prep_time_minutes,
                "cook_time_minutes": recipe.cook_time_minutes,
                "diet_type": recipe.diet_type,
                "source_type": recipe.source_type,
                "source_url": recipe.source_url,
                "video_url": recipe.video_url,
                "raw_cooklang": recipe.raw_cooklang,
                "image": image_path,
                "image_url": recipe.image_url,
                "is_public": recipe.is_public,
                # Seules les versions dont la racine fait partie de l'export restent liées.
                "root_ref": refs.get(recipe.root_recipe_id, ""),
                "version_label": recipe.version_label,
                "tags": [{"name": tag.name, "kind": tag.kind} for tag in recipe.tags.all()],
                "ingredients": [
                    {
                        "ingredient": _serialize_ingredient(line.ingredient),
                        "quantity": str(line.quantity),
                        "unit": line.unit,
                        "group_name": line.group_name,
                        "order": line.order,
                    }
                    for line in recipe.recipe_ingredients.all()
                ],
                "steps": [{"order": step.order, "instruction": step.instruction} for step in recipe.steps.all()],
            }
        )

    manifest = {"format": FORMAT_NAME, "version": FORMAT_VERSION, "recipes": payload}
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_NAME, json.dumps(manifest, indent=2, ensure_ascii=False))
        for path, content in images.items():
            archive.writestr(path, content)
    return buffer.getvalue()


# --- Import ---------------------------------------------------------------------------------


def _choice(value, choices, default):
    return value if value in choices.values else default


def _get_or_create_ingredient(data):
    name = str(data["name"]).strip()
    if not name:
        raise ValueError("ingredient sans nom")
    slug = str(data.get("slug") or "")
    lookup = Q(name__iexact=name)
    if slug:
        lookup |= Q(slug=slug)
    existing = Ingredient.objects.filter(lookup).first()
    if existing:
        return existing

    months = [m for m in data.get("available_months", []) if isinstance(m, int) and 1 <= m <= 12]
    translations = data.get("translations")
    fields = {field: data[field] for field in INGREDIENT_NUMERIC_FIELDS if field in data}
    return Ingredient.objects.create(
        name=name,
        category=_choice(data.get("category"), IngredientCategory, IngredientCategory.OTHER),
        default_unit=_choice(data.get("default_unit"), Unit, Unit.GRAM),
        available_months=months,
        translations=translations if isinstance(translations, dict) else {},
        **fields,
    )


def _read_manifest(archive):
    names = archive.namelist()
    if MANIFEST_NAME not in names:
        raise ArchiveError(f"{MANIFEST_NAME} est absent de l'archive.")
    if sum(info.file_size for info in archive.infolist()) > MAX_ARCHIVE_BYTES:
        raise ArchiveError("L'archive est trop volumineuse.")
    try:
        manifest = json.loads(archive.read(MANIFEST_NAME))
    except ValueError as exc:
        raise ArchiveError(f"{MANIFEST_NAME} n'est pas un JSON valide.") from exc
    if not isinstance(manifest, dict) or manifest.get("format") != FORMAT_NAME:
        raise ArchiveError("Ce fichier n'est pas un export de recettes Cocotte.")
    if not isinstance(manifest.get("version"), int) or manifest["version"] > FORMAT_VERSION:
        raise ArchiveError("Version de format non supportée : mettez à jour cette instance de Cocotte.")
    recipes = manifest.get("recipes")
    if not isinstance(recipes, list):
        raise ArchiveError("Liste de recettes manquante.")
    if len(recipes) > MAX_RECIPES:
        raise ArchiveError(f"Trop de recettes (maximum {MAX_RECIPES}).")
    return recipes


def _attach_image(recipe, archive, image_path):
    path = PurePosixPath(image_path)
    if (
        not image_path.startswith(IMAGES_DIR)
        or ".." in path.parts
        or path.suffix.lower() not in ALLOWED_IMAGE_EXTENSIONS
    ):
        return
    try:
        content = archive.read(image_path)
    except KeyError:
        return
    from PIL import Image

    try:
        Image.open(BytesIO(content)).verify()
    except Exception:  # noqa: BLE001 - tout fichier illisible par Pillow est simplement ignoré
        return
    recipe.image.save(f"{recipe.slug}{path.suffix.lower()}", ContentFile(content), save=True)


def _import_recipe(data, author, archive):
    title = str(data["title"]).strip()[:200]
    if not title:
        raise ValueError("recette sans titre")

    recipe = Recipe.objects.create(
        title=title,
        description=str(data.get("description", "")),
        author=author,
        servings=int(data.get("servings", 4)),
        prep_time_minutes=int(data.get("prep_time_minutes", 0)),
        cook_time_minutes=int(data.get("cook_time_minutes", 0)),
        diet_type=_choice(data.get("diet_type"), DietType, DietType.OMNIVORE),
        source_type=_choice(data.get("source_type"), SourceType, SourceType.MANUAL),
        source_url=str(data.get("source_url", "")),
        video_url=str(data.get("video_url", "")),
        raw_cooklang=str(data.get("raw_cooklang", "")),
        image_url=str(data.get("image_url", "")),
        is_public=bool(data.get("is_public", True)),
        version_label=str(data.get("version_label", ""))[:80],
    )

    for tag_data in data.get("tags", []):
        name = str(tag_data["name"]).strip()[:60]
        if name:
            tag, _ = Tag.objects.get_or_create(
                name=name, defaults={"kind": _choice(tag_data.get("kind"), TagKind, TagKind.OTHER)}
            )
            recipe.tags.add(tag)

    for index, line in enumerate(data.get("ingredients", [])):
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=_get_or_create_ingredient(line["ingredient"]),
            quantity=line["quantity"],
            unit=_choice(line.get("unit"), Unit, Unit.GRAM),
            group_name=str(line.get("group_name", ""))[:60],
            order=int(line.get("order", index)),
        )

    for index, step in enumerate(data.get("steps", [])):
        RecipeStep.objects.create(
            recipe=recipe, order=int(step.get("order", index)), instruction=str(step["instruction"])
        )

    if data.get("image"):
        _attach_image(recipe, archive, str(data["image"]))
    return recipe


def import_archive(file, author):
    """Importe une archive dans le compte `author`.

    Une recette dont le titre existe déjà chez `author` est ignorée (l'import est donc rejouable
    sans créer de doublons). Une recette invalide n'empêche pas les autres d'être importées.
    Renvoie `{"created": int, "skipped": int, "errors": [{"title", "detail"}]}`.
    """
    try:
        archive = zipfile.ZipFile(file)
    except zipfile.BadZipFile as exc:
        raise ArchiveError("Le fichier n'est pas une archive ZIP valide.") from exc

    with archive:
        entries = _read_manifest(archive)
        existing_titles = {t.lower() for t in Recipe.objects.filter(author=author).values_list("title", flat=True)}
        created = {}  # ref -> Recipe
        skipped = 0
        errors = []
        links = []  # (recipe, root_ref) à résoudre une fois toutes les recettes créées

        for data in entries:
            title = str(data.get("title", "")).strip() if isinstance(data, dict) else ""
            if title.lower() in existing_titles:
                skipped += 1
                continue
            try:
                with transaction.atomic():
                    recipe = _import_recipe(data, author, archive)
            except (KeyError, TypeError, ValueError, ArithmeticError, ValidationError, DatabaseError) as exc:
                errors.append({"title": title, "detail": f"{type(exc).__name__}: {exc}"})
                continue
            existing_titles.add(recipe.title.lower())
            created[data.get("ref")] = recipe
            if data.get("root_ref"):
                links.append((recipe, data["root_ref"]))

        for recipe, root_ref in links:
            root = created.get(root_ref)
            if root:
                recipe.root_recipe = root
                recipe.save(update_fields=["root_recipe"])

    return {"created": len(created), "skipped": skipped, "errors": errors}
