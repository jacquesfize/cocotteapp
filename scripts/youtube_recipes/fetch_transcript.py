#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["youtube-transcript-api>=1.0"]
# ///
"""Print the transcript of a YouTube video as JSON: {video_id, language, text}.

Usage: fetch_transcript.py <youtube-url-or-id> [--lang fr,en]
"""
import argparse
import json
import re
import sys
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import YouTubeTranscriptApi


def extract_id(value: str) -> str:
    if re.fullmatch(r"[\w-]{11}", value):
        return value
    p = urlparse(value)
    host = p.netloc.lower().removeprefix("www.").removeprefix("m.")
    if host == "youtu.be":
        return p.path.lstrip("/")[:11]
    if host in {"youtube.com", "music.youtube.com"}:
        if p.path == "/watch":
            return parse_qs(p.query).get("v", [""])[0]
        parts = p.path.split("/")
        if len(parts) > 2 and parts[1] in {"embed", "shorts", "live"}:
            return parts[2]
    sys.exit(f"Not a recognizable YouTube URL/id: {value}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--lang", default="fr,en", help="preferred languages, comma-separated")
    args = ap.parse_args()

    video_id = extract_id(args.video)
    fetched = YouTubeTranscriptApi().fetch(video_id, languages=args.lang.split(","))
    text = " ".join(s.text.replace("\n", " ") for s in fetched)
    json.dump(
        {"video_id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}",
         "language": fetched.language_code, "text": text},
        sys.stdout, ensure_ascii=False,
    )


if __name__ == "__main__":
    main()
