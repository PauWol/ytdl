import re
from urllib.parse import urlparse, parse_qs


YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "youtu.be", "music.youtube.com", "m.youtube.com"}


def is_valid_youtube_url(url: str) -> bool:
    """Return True if the URL looks like a valid YouTube link."""
    try:
        parsed = urlparse(url)
        return parsed.netloc in YOUTUBE_DOMAINS
    except Exception:
        return False


def is_playlist_url(url: str) -> bool:
    """Return True if the URL contains a playlist ID."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return "list" in params
    except Exception:
        return False


def sanitize_dirname(name: str) -> str:
    """Strip characters that are invalid in directory names."""
    return re.sub(r'[<>:"/\\|?*]', "_", name).strip()
