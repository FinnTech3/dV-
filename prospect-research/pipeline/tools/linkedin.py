"""LinkedIn URL cleaning only. This module performs no network access and no scraping.

A URL is accepted only when it was captured from a permitted non-LinkedIn
source (for example a link on the person's own employer biography). It is
never constructed from a name.
"""
from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

_PROFILE = re.compile(r"^/in/([^/?#]+)/?", re.IGNORECASE)


def clean(url: str | None) -> str | None:
    """Return the canonical https://www.linkedin.com/in/<slug> form, or None if not a personal profile URL."""
    if not url or not url.strip():
        return None
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if host != "linkedin.com" and not host.endswith(".linkedin.com"):
        return None
    m = _PROFILE.match(parts.path)
    if not m:
        return None  # company pages, /pub/dir, posts, search results are not profile links
    slug = unquote(m.group(1)).strip().lower()
    if not slug:
        return None
    return f"https://www.linkedin.com/in/{slug}"


def built_from_name(url: str, first_name: str, last_name: str, captured_from: str | None) -> bool:
    """Guard: flag a URL that has no capture source and merely mirrors the name (possible guess)."""
    if captured_from:
        return False
    slug = (clean(url) or "").rsplit("/", 1)[-1]
    guess = re.sub(r"[^a-z]", "", (first_name + last_name).lower())
    return bool(slug) and re.sub(r"[^a-z]", "", slug) == guess
