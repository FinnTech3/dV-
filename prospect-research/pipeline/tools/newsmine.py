"""Relocation-announcement mining.

Firms announce moves on their own news pages ("X relocates from our London office to Frankfurt"). Such a page is a
dated, first-party statement of a posting in an origin country AND a move to the target country. This module:
  1. lists a firm's sitemap URLs whose slug looks like a people-move announcement,
  2. fetches those pages (robots honoured, 2 s per host),
  3. keeps sentences that tie a person to an origin-country office AND a move/joining,
  4. attaches them, by exact name match, only to people already found on that firm's own profile pages
     (so the phone number and LinkedIn link still come from the person's own profile).
No names are guessed: a name is used only if it appears verbatim on both the news page and a profile page.
"""
from __future__ import annotations

import json
import re
import socket
import sqlite3
import time
import urllib.request
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor

from . import db
from .fetch import fetch
from .firmcrawl import PLACE, YEAR, crawl_conn
from .probe import UA, get

socket.setdefaulttimeout(15)
SLUG = re.compile(r"(relocat|moves?-to-|moving-to-our|joins?-(the-)?(firm|our|us|as|in-)|joined-(the-)?(firm|our)|returns?-to-|appoint|new-partner|partner-hire|lateral|promot|welcomes-|hires?-|strengthens?-(our|its)-(team|practice|office)|from-london|from-our-london|neuzugang|verstaerk|verstärk|rejoint|nombra|incorpora)", re.I)
ORIGIN_TIE = re.compile(r"(from (our |the |its )?(London|Dublin|Amsterdam|Manchester|Edinburgh|Leeds|Birmingham|Bristol|Glasgow|Rotterdam|The Hague|UK|U\.K\.|England|Ireland|Netherlands)"
                        r"|(London|Dublin|Amsterdam|Manchester|Edinburgh|Rotterdam|Utrecht|Cork)[- ]based|in (our |the )?(London|Dublin|Amsterdam|Manchester|Edinburgh|Rotterdam) office"
                        r"|(our |the )(London|Dublin|Amsterdam|Manchester|Edinburgh) office|(previously|formerly|until) (at|with|in)[^.]{0,60}(London|Dublin|Amsterdam|UK))", re.I)
MOVE = re.compile(r"(relocat\w+|moves? to|moving to|transfer\w*|returns? to|returning to|joins?|joined|appoint\w+|has been appointed|will be based|is based|takes? over|heads?|lead)", re.I)
NOISE = re.compile(r"(client|advis(ed|es|ing) |acted for|transaction|mandate|deal\b|merger|acquisition|court|ruling|judgment|webinar|event|conference)", re.I)


def sitemap_urls(host: str, max_maps: int = 40) -> list[str]:
    robots = get(f"https://{host}/robots.txt")[1]
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(robots.splitlines())
    maps = re.findall(r"(?im)^sitemap:\s*(\S+)", robots) or [f"https://{host}/{x}" for x in ("sitemap.xml", "wp-sitemap.xml", "sitemap_index.xml")]
    out, seen, queue = set(), set(), list(maps)
    while queue and len(seen) < max_maps:
        m = queue.pop(0)
        if m in seen:
            continue
        seen.add(m)
        try:
            xml = get(m)[1]
        except Exception:
            continue
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
        if "<sitemapindex" in xml:
            queue += [l for l in locs if re.search(r"(news|press|insight|media|article|post|publication|update|sitemap)", l, re.I)] or locs[:8]
        else:
            out |= set(locs)
    return [u for u in out if rp.can_fetch(UA, u)]


def announcement_urls(host: str) -> list[str]:
    urls = sitemap_urls(host)
    keep = [u for u in urls if re.search(r"/(news|press|media|insights?|articles?|posts?|publications?|updates?|actualit|noticias|aktuelles|presse|newsroom)", u, re.I)
            and SLUG.search(u.rsplit("/", 1)[-1]) and not re.search(r"\.(pdf|jpg|png)$", u, re.I)]
    return sorted(set(keep))


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if 30 < len(s) < 500]


def extract_moves(text: str, names: dict[str, list[dict]]) -> list[dict]:
    """names: {full_name: [profile rows]}. Returns matches of (profile, sentence)."""
    hits = []
    for s in sentences(text):
        if not (ORIGIN_TIE.search(s) and MOVE.search(s)) or NOISE.search(s):
            continue
        for full, profs in names.items():
            if full in s or full.split()[0] + " " + full.split()[-1] in s:
                hits.append({"name": full, "sentence": s})
    return hits


if __name__ == "__main__":
    import sys
    for h in sys.argv[1:]:
        try:
            u = announcement_urls(h)
            print(f"{len(u):5d} {h}  {u[0] if u else ''}", flush=True)
        except Exception as e:
            print(f"    - {h} ERR {str(e)[:50]}", flush=True)
