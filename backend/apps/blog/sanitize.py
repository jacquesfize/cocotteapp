"""Server-side sanitization of blog post HTML: the frontend renders it with `v-html`, so this is
the only barrier against stored XSS — never trust the editor's output."""

import html as html_lib
import re

import nh3

ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "a", "h2", "h3", "h4",
    "ul", "ol", "li", "blockquote", "code", "pre", "hr", "img", "iframe",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title"},
    "iframe": {"src", "title", "data-cocotte-recipe", "loading"},
}
URL_SCHEMES = {"http", "https", "mailto"}

# An iframe may only point at Cocotte's own recipe embed view, never at an arbitrary site.
RECIPE_EMBED_SRC = re.compile(r"^/embed/recipes/\d+$")
IMG_SRC = re.compile(r"^(https?://|/media/)", re.IGNORECASE)


def _filter_attribute(tag, attribute, value):
    if tag == "iframe":
        if attribute == "src":
            return value if RECIPE_EMBED_SRC.match(value) else None
        if attribute == "data-cocotte-recipe":
            return value if value.isdigit() else None
        if attribute == "loading":
            return "lazy"
    if tag == "img" and attribute == "src":
        return value if IMG_SRC.match(value) else None
    return value


def clean_post_html(html):
    cleaned = nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=URL_SCHEMES,
        attribute_filter=_filter_attribute,
    )
    # Drop images and iframes left without a valid source by the filter above.
    cleaned = re.sub(r"<iframe(?![^>]*\ssrc=)[^>]*>\s*</iframe>", "", cleaned)
    return re.sub(r"<img(?![^>]*\ssrc=)[^>]*>", "", cleaned)


# Closing a block (or a line break) separates words: keep a space there once tags are stripped.
BLOCK_END = re.compile(r"(</(?:p|h[1-6]|li|blockquote|pre)>|<br\s*/?>)", re.IGNORECASE)


def html_to_text(html):
    text = nh3.clean(BLOCK_END.sub(r"\1 ", html), tags=set())
    return html_lib.unescape(text).strip()
