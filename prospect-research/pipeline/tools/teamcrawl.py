"""Find each site's team page(s), segment them into people, and store the results as pseudo-pages that the normal
staging step (firmcrawl.stage) can grade. robots.txt honoured, 2 s per host, no logins, no bypass.

  python -m pipeline.tools.teamcrawl <hosts.txt | probe.json | seed.json> [workers]
"""
from __future__ import annotations

import json
import re
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit

from . import db, fetch, firmcrawl, teamparse

socket.setdefaulttimeout(20)
TEAMLINK = re.compile(r"(team|people|staff|meet|about|equipo|equipe|[uü]ber[- ]?uns|nosotros|qui[eé]nes|who[- ]we|notre[- ]?[eé]quipe|unser[- ]?team|owners?|hosts?|"
                      r"lawyers?|attorneys?|partners?|professionals?|specialists?|doctors?|dentists?|[aä]rzte|zahn[aä]rzte|m[eé]dicos|dentistas|abogados|avocats|anw[aä]lte|"
                      r"our-story|our-people|sobre|[aà]-propos|wir|das-team|mitarbeiter|collaborateurs|nuestro)", re.I)
COMMON = ("/team", "/about", "/about-us", "/our-team", "/the-team", "/meet-the-team", "/equipo", "/equipe", "/ueber-uns", "/nosotros", "/people", "/staff")
SKIP_EXT = re.compile(r"\.(pdf|jpe?g|png|gif|zip|docx?)$", re.I)


def team_urls(host: str, settings: dict) -> tuple[list[str], str]:
    base = f"https://{host}/"
    r = fetch.fetch(base, settings, keep_html=True)
    if not r.ok:
        return [], r.reason or "unreachable"
    own = (urlsplit(r.url).hostname or host).replace("www.", "")
    cand: list[str] = []
    for m in re.finditer(r'(?is)<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', r.html):
        href, anchor = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
        u = urljoin(base, href)
        if urlsplit(u).hostname and own in urlsplit(u).hostname.replace("www.", "") and not SKIP_EXT.search(u) and (TEAMLINK.search(href) or TEAMLINK.search(anchor[:60])):
            if u.rstrip("/") != base.rstrip("/") and u not in cand:
                cand.append(u)
    for c in COMMON:
        u = urljoin(base, c)
        if u not in cand:
            cand.append(u)
    return cand[:6], ""


def one_host(host: str, settings: dict, cc) -> dict:
    stats = {"host": host, "pages": 0, "blocks": 0, "own_phone": 0, "origin": 0}
    urls, why = team_urls(host, settings)
    got = 0
    for u in urls:
        if got >= 4:
            break
        r = fetch.fetch(u, settings, keep_html=True)
        if not r.ok:
            continue
        got += 1
        stats["pages"] += 1
        for b in teamparse.extract_team(u, r.html):
            stats["blocks"] += 1
            stats["own_phone"] += bool(b["tels"])
            stats["origin"] += bool(b["origin"])
            slug = re.sub(r"[^a-z0-9]+", "-", b["name"].lower()).strip("-")
            cc.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (f"{u}#{slug}", host, slug, 200, db.now_iso(), b["name"], b["role"], json.dumps(b["tels"]), b["linkedin"], b["city"],
                        ",".join(sorted({t["region"] or "" for t in b["tels"]})), b["origin"], b["sentence"], b["has_years"], b["lived"], b["text_len"]))
        cc.commit()
    return stats


def load_hosts(path: str) -> dict[str, dict]:
    if path.endswith(".json"):
        d = json.load(open(path))
        return {h: {"label": (v.get("label") or v.get("name") or h), "channel": "team pages (" + v.get("market", "seed") + ")"} for h, v in d.items()}
    return {l.strip(): {"label": l.strip(), "channel": "team pages"} for l in open(path) if l.strip()}


if __name__ == "__main__":
    hosts = load_hosts(sys.argv[1])
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    st = db.load_settings()
    st["fetch"]["min_seconds_between_requests_per_host"] = 2.0
    cc = firmcrawl.crawl_conn()
    cc.execute("PRAGMA busy_timeout=60000")
    for h, m in hosts.items():
        cc.execute("INSERT OR IGNORE INTO host_meta VALUES (?,?,?,?)", (h, m["label"][:80], m["channel"], "team-page parser"))
    cc.commit()
    import threading
    lock = threading.Lock()
    def run(h):
        c2 = firmcrawl.crawl_conn()
        try:
            s = one_host(h, st, c2)
        except Exception as e:
            s = {"host": h, "err": str(e)[:60]}
        with lock:
            print(json.dumps(s), flush=True)
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(run, list(hosts)))
    print("team crawl finished", flush=True)
