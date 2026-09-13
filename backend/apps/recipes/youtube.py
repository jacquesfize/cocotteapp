import re
from urllib.parse import parse_qs, urlparse

_ID_PATTERN = re.compile(r"^[\w-]{11}$")


def extract_youtube_id(url: str) -> str:
    """Return the 11-character video id from a YouTube URL, or '' if not recognized."""
    if not url:
        return ""

    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")

    candidate = ""
    if host == "youtu.be":
        candidate = parsed.path.lstrip("/")
    elif host in {"youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            candidate = parse_qs(parsed.query).get("v", [""])[0]
        elif parsed.path.startswith(("/embed/", "/shorts/", "/live/")):
            candidate = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else ""

    return candidate if _ID_PATTERN.match(candidate) else ""
