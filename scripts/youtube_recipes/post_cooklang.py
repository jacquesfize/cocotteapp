#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27"]
# ///
"""Create a Cocotte recipe from a .cook file via the API.

Logs in with COCOTTE_EMAIL / COCOTTE_PASSWORD (JWT), POSTs to
/api/recipes/import-cooklang/, then PATCHes video_url/source_url (and the video thumbnail as image_url) onto the recipe.

Usage: post_cooklang.py recipe.cook --title "Tarte" [--servings 4] [--prep 15] [--cook 30]
       [--diet omnivore] [--video-url URL] [--image-url URL] [--dry-run]
Env:   COCOTTE_API (default http://localhost:8000/api), COCOTTE_EMAIL, COCOTTE_PASSWORD
"""
import argparse
import os
import re
import sys

import httpx


# The backend parser takes everything up to the next space as the name, so `@sel,` would
# create an ingredient called "sel,". Force explicit braces before trailing punctuation.
_UNBRACED_PUNCT_RE = re.compile(r"([@#][^\s@#~{}]*?[^\s@#~{},.;:!?)»])([,.;:!?)»]+)(?=\s|$)")


def sanitize_cooklang(text: str) -> str:
    return _UNBRACED_PUNCT_RE.sub(r"\1{}\2", text)


def youtube_thumbnail(url: str, client: httpx.Client | None = None) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url)
    if not m:
        return None
    for name in ("maxresdefault", "hqdefault"):
        thumb = f"https://img.youtube.com/vi/{m.group(1)}/{name}.jpg"
        try:
            if httpx.head(thumb, timeout=10).status_code == 200:
                return thumb
        except httpx.HTTPError:
            pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--title", required=True)
    ap.add_argument("--servings", type=int)
    ap.add_argument("--prep", type=int, help="prep time, minutes")
    ap.add_argument("--cook", type=int, help="cook time, minutes")
    ap.add_argument("--diet", help="diet_type value (e.g. omnivore, vegetarian, vegan)")
    ap.add_argument("--video-url")
    ap.add_argument("--image-url", help="recipe image; defaults to the YouTube thumbnail of --video-url")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    raw = sanitize_cooklang(open(args.file, encoding="utf-8").read())
    payload = {"title": args.title, "raw_cooklang": raw}
    for key, val in [("servings", args.servings), ("prep_time_minutes", args.prep),
                     ("cook_time_minutes", args.cook), ("diet_type", args.diet)]:
        if val is not None:
            payload[key] = val

    if args.dry_run:
        print(payload)
        return

    api = os.environ.get("COCOTTE_API", "http://localhost:8000/api").rstrip("/")
    email, password = os.environ.get("COCOTTE_EMAIL"), os.environ.get("COCOTTE_PASSWORD")
    if not (email and password):
        sys.exit("Set COCOTTE_EMAIL and COCOTTE_PASSWORD")

    with httpx.Client(base_url=api, timeout=30) as c:
        r = c.post("/auth/token/", json={"email": email, "password": password})
        r.raise_for_status()
        c.headers["Authorization"] = f"Bearer {r.json()['access']}"

        r = c.post("/recipes/import-cooklang/", json=payload)
        if r.status_code >= 400:
            sys.exit(f"import failed {r.status_code}: {r.text}")
        recipe = r.json()

        if args.video_url:
            patch = {"video_url": args.video_url, "source_url": args.video_url}
            if image := args.image_url or youtube_thumbnail(args.video_url):
                patch["image_url"] = image
            r = c.patch(f"/recipes/{recipe['id']}/", json=patch)
            if r.status_code >= 400:
                print(f"warning: recipe created but video_url patch failed: {r.text}", file=sys.stderr)

    print(f"created recipe {recipe['id']} slug={recipe.get('slug')}")


if __name__ == "__main__":
    main()
