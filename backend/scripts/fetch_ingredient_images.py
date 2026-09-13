#!/usr/bin/env python3
"""Récupère une image Wikipédia par ingrédient de seed_common_ingredients.py.

Interroge l'API MediaWiki (prop=pageimages) pour la miniature "page image" de
l'article Wikipédia dont le titre correspond au nom de chaque ingrédient, et
télécharge l'image à la taille demandée (pithumbsize). Sert à évaluer la
couverture réelle avant de décider d'un pipeline d'import définitif : la
licence/l'attribution de chaque image Wikimedia Commons n'est pas gérée ici.

Usage:
    python3 scripts/fetch_ingredient_images.py
    python3 scripts/fetch_ingredient_images.py --size 500 --out /tmp/images
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SEED_FILE = (
    Path(__file__).resolve().parent.parent
    / "apps/ingredients/management/commands/seed_common_ingredients.py"
)
API_URL_TEMPLATE = "https://{lang}.wikipedia.org/w/api.php"
USER_AGENT = (
    "Cocotte-IngredientImageFetcher/1.0 "
    "(https://github.com/jacquesfize/testrecetteapp; exploration script)"
)


def load_ingredient_names() -> list[str]:
    text = SEED_FILE.read_text(encoding="utf-8")
    return re.findall(r'"name":\s*"([^"]+)"', text)


LIGATURES = {"œ": "oe", "Œ": "Oe", "æ": "ae", "Æ": "Ae"}


def slugify(name: str) -> str:
    for ligature, expansion in LIGATURES.items():
        name = name.replace(ligature, expansion)
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def fetch_page_image_url(name: str, lang: str, size: int) -> str | None:
    params = {
        "action": "query",
        "format": "json",
        "prop": "pageimages",
        "piprop": "thumbnail",
        "pithumbsize": str(size),
        "titles": name,
        "redirects": "1",
    }
    url = f"{API_URL_TEMPLATE.format(lang=lang)}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.load(response)
    for page in data.get("query", {}).get("pages", {}).values():
        thumbnail = page.get("thumbnail")
        if thumbnail:
            return thumbnail["source"]
    return None


def download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=15) as response, dest.open("wb") as fh:
        fh.write(response.read())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=300, help="Largeur de la miniature en pixels")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "ingredient_images",
        help="Dossier de sortie pour les images téléchargées",
    )
    parser.add_argument("--lang", default="fr", help="Code langue Wikipedia (fr, en, ...)")
    parser.add_argument("--delay", type=float, default=0.3, help="Délai entre requêtes, en secondes")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    names = load_ingredient_names()

    found, missing = [], []
    for name in names:
        try:
            image_url = fetch_page_image_url(name, args.lang, args.size)
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            print(f"[erreur]  {name}: {exc}", file=sys.stderr)
            missing.append(name)
            time.sleep(args.delay)
            continue

        if not image_url:
            missing.append(name)
            print(f"[absent]  {name}")
            time.sleep(args.delay)
            continue

        ext = Path(urllib.parse.urlparse(image_url).path).suffix or ".jpg"
        dest = args.out / f"{slugify(name)}{ext}"
        download(image_url, dest)
        found.append(name)
        print(f"[ok]      {name} -> {dest.name}")
        time.sleep(args.delay)

    print(f"\n{len(found)}/{len(names)} images récupérées, {len(missing)} manquantes.")
    if missing:
        print("Manquants :", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
