from apps.recipes.youtube import extract_youtube_id


def test_extracts_id_from_watch_url():
    assert extract_youtube_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extracts_id_from_watch_url_with_extra_params():
    assert extract_youtube_id("https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s") == "dQw4w9WgXcQ"


def test_extracts_id_from_short_url():
    assert extract_youtube_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extracts_id_from_shorts_url():
    assert extract_youtube_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_returns_empty_string_for_non_youtube_url():
    assert extract_youtube_id("https://example.com/video") == ""


def test_returns_empty_string_for_blank_input():
    assert extract_youtube_id("") == ""
