"""Search-provider registry and query bookkeeping.

In this Claude Code runtime the only discovery provider is the session's
native `WebSearch` tool. It is invoked by the agent, not by Python, so this
module does not issue network searches itself: it decides WHAT to search,
prevents repeated queries, records outcomes, and sanitises results that the
agent hands back. Search snippets are leads only and are never stored as
evidence; evidence must come from the retrieved source page.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

from . import db


class SearchUnavailable(RuntimeError):
    """No permitted no-cost provider can be used right now."""


class RateLimited(RuntimeError):
    """The provider asked us to slow down. The limit is respected, not evaded."""


@dataclass
class Provider:
    name: str
    kind: str            # agent_tool | http
    cost: str            # statement of cost position
    available: bool
    note: str = ""


PROVIDERS = [
    Provider("native_websearch", "agent_tool", "included in the existing Claude Code arrangement as far as can be seen from inside the session",
             True, "US-only index; invoked by the agent; standard mode only"),
    Provider("direct_site_navigation", "http", "free", True, "official sites, sitemaps, RSS, public registers via fetch.py"),
    Provider("duckduckgo_html", "http", "free", False, "returned an HTTP 202 bot challenge when tested; automated use not permitted - not used"),
    Provider("brave_search_api", "http", "paid / needs user credential", False, "excluded by the no-paid-provider rule"),
    Provider("bright_data", "agent_tool", "paid, usage-billed", False, "plugin present in the runtime but excluded by the cost rule"),
]


def pick_provider(providers: list[Provider] | None = None) -> Provider:
    for p in providers or PROVIDERS:
        if p.available and p.name != "direct_site_navigation":
            return p
    raise SearchUnavailable("no permitted no-cost search provider is available; fall back to direct site navigation")


def norm_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def already_searched(conn: sqlite3.Connection, query: str, kind: str = "query") -> bool:
    return conn.execute("SELECT 1 FROM searched WHERE key = ? AND kind = ?", (norm_query(query), kind)).fetchone() is not None


def record_search(conn: sqlite3.Connection, query: str, provider: str, result_count: int, kind: str = "query") -> bool:
    """Record a completed query/page/organisation. Returns False if it was already recorded."""
    if already_searched(conn, query, kind):
        return False
    conn.execute("INSERT INTO searched (key, kind, provider, ts, result_count) VALUES (?,?,?,?,?)",
                 (norm_query(query), kind, provider, db.now_iso(), result_count))
    conn.commit()
    return True


def backoff_seconds(attempt: int, base: float = 30.0, ceiling: float = 900.0) -> float:
    """Wait time after a rate-limit signal. Waiting is the only response; the limit is never bypassed."""
    return min(base * (2 ** max(attempt - 1, 0)), ceiling)


def run_query(conn: sqlite3.Connection, query: str, executor, provider: Provider | None = None, max_attempts: int = 3,
              sleep=None) -> list[dict]:
    """Execute a query through `executor(query) -> list[dict]`, honouring the searched register and rate limits."""
    provider = provider or pick_provider()
    if already_searched(conn, query):
        return []
    for attempt in range(1, max_attempts + 1):
        try:
            results = sanitise_results(executor(query))
            record_search(conn, query, provider.name, len(results))
            return results
        except RateLimited:
            db.log(conn, mode="HARVEST", provider=provider.name, query=query, usage_limits=1, note=f"rate limited, attempt {attempt}")
            if attempt == max_attempts:
                raise
            if sleep:
                sleep(backoff_seconds(attempt))
    return []


_SUSPECT = re.compile(r"(ignore (previous|prior|all) instructions|guaranteed|100% verified|click here to reveal|unlock (the )?(phone|mobile|number))", re.IGNORECASE)


def sanitise_results(results: list[dict]) -> list[dict]:
    """Keep only well-formed results and mark them as leads, never as evidence."""
    clean = []
    for r in results or []:
        url = (r.get("url") or "").strip()
        if not re.match(r"^https?://[^\s/]+\.[^\s/]+", url):
            continue
        snippet = r.get("snippet") or ""
        clean.append({
            "url": url,
            "title": (r.get("title") or "").strip(),
            "snippet": snippet,
            "is_evidence": False,                      # a snippet must be confirmed on the source page
            "suspect": bool(_SUSPECT.search(snippet + " " + (r.get("title") or ""))),
        })
    return clean
