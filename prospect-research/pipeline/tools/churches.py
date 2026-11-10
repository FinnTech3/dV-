"""Avenue: Anglican chaplaincies in mainland Europe (Church of England Diocese in Europe).

Reasoning: a chaplain's public biography normally lists earlier parish posts in England with years
(previous employment and residence), chaplains live in the place they serve, the occupation is plainly
not financial, and the chaplaincy prints a contact number for the chaplain. The diocese publishes every
church with its own website; the biographies are on those church sites.

This module only collects the church list and the text of each church's own 'chaplain / clergy / who we
are' page into pipeline/evidence/churches.json (git-ignored) for a human-style read. It stages nothing.
"""
from __future__ import annotations

import json
import re
import socket
import time
import urllib.request
import urllib.robotparser
from urllib.parse import urljoin, urlsplit

from . import db
from .firmcrawl import _text
from .probe import UA

socket.setdefaulttimeout(20)
OUT = db.PIPELINE / "evidence" / "churches.json"
BASE = "https://www.europe.anglican.org"
ELIGIBLE = {"France", "Germany", "Spain", "Portugal", "Switzerland", "Italy", "Belgium", "Luxembourg", "Austria", "Sweden", "Denmark",
            "Finland", "Greece", "Poland", "Czech Republic", "Czechia", "Hungary", "Romania", "Bulgaria", "Croatia", "Slovenia",
            "Slovakia", "Estonia", "Latvia", "Lithuania"}
ISLANDS = re.compile(r"(Mallorca|Menorca|Ibiza|Tenerife|Gran Canaria|Lanzarote|Fuerteventura|La Palma|Madeira|Azores|Corsica|Sardinia|Sicily|Crete|Palma|Canar)", re.I)
TEAM = re.compile(r"(chaplain|clergy|vicar|priest|minister|rector|who[- ]?s[- ]?who|who-we-are|our-team|team|staff|people|about|contact|welcome)", re.I)


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read(1_500_000).decode("utf-8", "replace")


def allowed(url: str, cache: dict) -> bool:
    origin = "{0.scheme}://{0.netloc}".format(urlsplit(url))
    if origin not in cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            rp.parse(get(origin + "/robots.txt").splitlines())
        except Exception:
            rp.allow_all = True
        cache[origin] = rp
    return cache[origin].can_fetch(UA, url)


def collect(limit: int | None = None) -> list[dict]:
    locs = re.findall(r"<loc>([^<]+)</loc>", get(BASE + "/sitemap.xml"))
    pages = sorted(u for u in locs if "/where-we-are/churches/" in u)[:limit]
    robots: dict = {}
    out = json.loads(OUT.read_text()) if OUT.exists() else []
    done = {c["diocese_page"] for c in out}
    for u in pages:
        if u in done:
            continue
        time.sleep(2)
        rec = {"diocese_page": u}
        try:
            body = get(u)
        except Exception as exc:
            rec["error"] = str(exc)[:80]; out.append(rec); continue
        text = _text(body)
        m = re.search(r"Location\.\s*(.*?)\s*\.\s*\.\s*\.\s*(Website|Get in touch)", text)
        rec["location"] = m.group(1)[:160] if m else ""
        rec["country"] = next((c for c in ELIGIBLE if re.search(rf"\b{c}\b", rec["location"])), None)
        w = re.search(r"Website\.\s*(https?://\S+)", text)
        rec["website"] = w.group(1).rstrip(".") if w else None
        p = re.search(r"Phone\.\s*(\+[\d\s()]{8,20})", text)
        rec["church_phone"] = p.group(1).strip() if p else None
        if rec["country"] and rec["website"] and not ISLANDS.search(rec["location"]):
            rec["pages"] = []
            try:
                if allowed(rec["website"], robots):
                    home = get(rec["website"])
                    links = {urljoin(rec["website"], h) for h, a in re.findall(r'(?is)<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', home)
                             if TEAM.search(h + " " + re.sub(r"<[^>]+>", " ", a))}
                    host = urlsplit(rec["website"]).netloc
                    links = [l for l in sorted(links) if urlsplit(l).netloc == host][:6]
                    rec["pages"].append({"url": rec["website"], "text": _text(home)[:6000]})
                    for l in links:
                        time.sleep(1.5)
                        if allowed(l, robots):
                            try:
                                rec["pages"].append({"url": l, "text": _text(get(l))[:9000]})
                            except Exception:
                                pass
            except Exception as exc:
                rec["error"] = str(exc)[:80]
        out.append(rec)
        OUT.write_text(json.dumps(out, ensure_ascii=False))
    return out


if __name__ == "__main__":
    res = collect()
    print(len(res), "churches;", sum(1 for c in res if c.get("pages")), "with site text")
