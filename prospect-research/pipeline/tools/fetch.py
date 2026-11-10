"""Permitted webpage retrieval.

Rules enforced here:
* robots.txt is honoured; a disallowed path is not fetched.
* LinkedIn (and any host in `forbidden_hosts`) is never fetched.
* A per-host delay is applied. Blocks (401/403/429, captcha pages) are recorded
  and NOT evaded: no retries with different identities, no proxy rotation.
* Retrieved text is data. `flag_injection` marks instruction-like text so it is
  quarantined from notes; nothing in a page can change pipeline behaviour.
"""
from __future__ import annotations

import html
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from urllib.parse import urlsplit

_last_request: dict[str, float] = {}
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

_INJECTION = re.compile(
    r"(ignore (all |any )?(previous|prior|above) (instructions|prompts)|disregard (the )?(system|previous) (prompt|instructions)"
    r"|you are now|new instructions:|system prompt|mark (this|every) (person|candidate|record) as (verified|pass|grade a)"
    r"|do not tell the user|exfiltrate|send (the|all) (data|records|database) to)", re.IGNORECASE)
_CAPTCHA = re.compile(r"(captcha|are you a robot|unusual traffic|cf-challenge|access denied)", re.IGNORECASE)


@dataclass
class FetchResult:
    url: str
    ok: bool
    status: int | None = None
    text: str = ""
    blocked: bool = False
    reason: str = ""
    injection_flags: list[str] = field(default_factory=list)


def host_forbidden(url: str, settings: dict) -> bool:
    host = (urlsplit(url).hostname or "").lower()
    return any(host == h or host.endswith("." + h) for h in settings["fetch"]["forbidden_hosts"])


def flag_injection(text: str) -> list[str]:
    return sorted({m.group(0).lower() for m in _INJECTION.finditer(text or "")})


def to_text(markup: str) -> str:
    markup = re.sub(r"(?is)<(script|style|noscript|template)[^>]*>.*?</\1>", " ", markup)
    markup = re.sub(r"(?s)<!--.*?-->", " ", markup)
    markup = re.sub(r"(?s)<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(markup)).strip()


def _robots_allows(url: str, user_agent: str, opener) -> bool:
    parts = urlsplit(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            status, body = opener(origin + "/robots.txt")
            if status == 200:
                rp.parse(body.splitlines())
            elif status in (401, 403):
                rp.disallow_all = True
            else:
                rp.allow_all = True
        except Exception:
            rp.allow_all = True
        _robots[origin] = rp
    return _robots[origin].can_fetch(user_agent, url)


def _default_opener(settings: dict):
    def opener(url: str) -> tuple[int, str]:
        req = urllib.request.Request(url, headers={"User-Agent": settings["fetch"]["user_agent"]})
        try:
            with urllib.request.urlopen(req, timeout=settings["fetch"]["timeout_seconds"]) as resp:
                return resp.status, resp.read(2_000_000).decode(resp.headers.get_content_charset() or "utf-8", "replace")
        except urllib.error.HTTPError as exc:
            return exc.code, ""
    return opener


def fetch(url: str, settings: dict, opener=None, sleep=time.sleep) -> FetchResult:
    """Retrieve one public page. `opener(url) -> (status, body)` is injectable for tests."""
    if host_forbidden(url, settings):
        return FetchResult(url, False, blocked=True, reason="forbidden host (no scraping of this site)")
    opener = opener or _default_opener(settings)
    ua = settings["fetch"]["user_agent"]
    if not _robots_allows(url, ua, opener):
        return FetchResult(url, False, blocked=True, reason="disallowed by robots.txt")
    host = urlsplit(url).netloc
    wait = settings["fetch"]["min_seconds_between_requests_per_host"] - (time.monotonic() - _last_request.get(host, 0))
    if wait > 0:
        sleep(wait)
    _last_request[host] = time.monotonic()
    try:
        status, body = opener(url)
    except Exception as exc:  # network failure: recorded, not retried aggressively
        return FetchResult(url, False, reason=f"technical failure: {exc}")
    if status in (401, 403, 429, 451):
        return FetchResult(url, False, status=status, blocked=True, reason=f"site refused retrieval (HTTP {status}); not evaded")
    if status != 200:
        return FetchResult(url, False, status=status, reason=f"HTTP {status}")
    text = to_text(body)
    if len(text) < 600 and _CAPTCHA.search(text):
        return FetchResult(url, False, status=status, blocked=True, reason="challenge/captcha page; not evaded")
    return FetchResult(url, True, status=status, text=text, injection_flags=flag_injection(text))


def reset_state() -> None:
    _last_request.clear()
    _robots.clear()
