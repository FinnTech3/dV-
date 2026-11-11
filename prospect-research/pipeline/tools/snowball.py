"""SNOWBALL: from a public member directory to the member companies' own websites, then to their public people pages.

Only the directory page itself and each company's own sitemap-listed people pages are read (robots.txt honoured,
no logins, no bypassing). A directory is a source of ORGANISATIONS; nobody is counted until a named person has
been separately researched and graded.
"""
from __future__ import annotations

import json
import re
import socket
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

from . import db, fetch
from .firmcrawl import SMALL_SITE_PAT, crawl_conn
from .probe import probe_urls

socket.setdefaulttimeout(12)
SKIP = re.compile(r"(linkedin|facebook|twitter|\bx\.com|instagram|youtube|google|apple\.com|wordpress|gstatic|cloudflare|bit\.ly|goo\.gl|whatsapp|"
                  r"vimeo|issuu|eventbrite|mailchimp|calendly|flickr|wikipedia|cookiedatabase|gov\.uk|\.gov\.|europa\.eu|ireland\.ie|dfa\.ie|snbn\.|"
                  r"zoom\.us|paypal|stripe|shopify|wixsite|squarespace|jimdo|typeform|hubspot|elementor|jsdelivr)", re.I)


GENERIC_LABEL = re.compile(r"^(zur webseite|website|homepage|visit( website)?|www\..*|more|mehr|read more|link|site web|sitio web|webseite|click here)$", re.I)


def label_for(host: str, anchor: str) -> str:
    """Anchor text is only a label when it is a name; 'Zur Webseite' (to the website) and similar is replaced by the domain name."""
    if anchor and 2 < len(anchor) < 70 and not GENERIC_LABEL.match(anchor.strip()):
        return anchor.strip()
    sld = (host[4:] if host.startswith("www.") else host).split(".")[0]
    return sld.replace("-", " ").title()


def _registrable(h: str) -> str:
    h = h.lower()
    return h[4:] if h.startswith("www.") else h


def collect(directory_urls: list[str], settings: dict) -> dict[str, dict]:
    """Return {host: {label, discovered_from}} for external sites linked from the directory pages."""
    found: dict[str, dict] = {}
    for u in directory_urls:
        r = fetch.fetch(u, settings, keep_html=True)
        if not r.ok:
            print(f"  skip {u}: {r.reason}")
            continue
        own = _registrable(urlsplit(u).hostname or "")
        own_root = ".".join(own.split(".")[-2:])
        for m in re.finditer(r'(?is)<a[^>]+href="(https?://[^"#]+)"[^>]*>(.*?)</a>', r.html):
            link, anchor = m.group(1), re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip()
            host = urlsplit(link).hostname or ""
            if not host or SKIP.search(link) or own_root in host:
                continue
            h = host.lower()
            found.setdefault(h, {"label": label_for(h, anchor), "discovered_from": u})
    return found


def probe_hosts(hosts: dict[str, dict], workers: int = 16) -> list[dict]:
    def one(h: str) -> dict:
        try:
            urls = probe_urls(h, SMALL_SITE_PAT, max_maps=12)
            return {"host": h, "people_urls": len(urls), "sample": sorted(urls)[:1]}
        except Exception as exc:
            return {"host": h, "people_urls": 0, "error": str(exc)[:60]}
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(one, hosts))


def register(conn: sqlite3.Connection, hosts: dict[str, dict], probed: list[dict], channel: str) -> int:
    cc = crawl_conn()
    n = 0
    by = {p["host"]: p for p in probed}
    for h, meta in hosts.items():
        p = by.get(h, {})
        cc.execute("INSERT OR REPLACE INTO host_meta VALUES (?,?,?,?)", (h, meta["label"], channel, meta["discovered_from"]))
        conn.execute("""INSERT OR IGNORE INTO sources (name, url, source_type, country, public_content, origin_files, audit_status, discrepancy)
                        VALUES (?,?,?,?,?,?,?,?)""",
                     (meta["label"], f"https://{h}/", "member company website", "", f"{p.get('people_urls', 0)} people-profile URLs in sitemap",
                      "snowball:" + meta["discovered_from"], "PROBED" if p else "NOT PROBED", ""))
        n += 1
    cc.commit()
    conn.commit()
    return n


def run(seeds: list[str], channel: str, out_path: str) -> dict:
    st = db.load_settings()
    hs = collect(seeds, st)
    print(f"{len(hs)} external member sites found", flush=True)
    pr = probe_hosts(hs, workers=24)
    conn = db.connect()
    register(conn, hs, pr, channel)
    rich = [p for p in pr if p["people_urls"] >= 2]
    res = {"hosts": len(hs), "with_people_pages": len(rich), "people_urls_total": sum(p["people_urls"] for p in rich),
           "rich_hosts": sorted(rich, key=lambda p: -p["people_urls"])}
    open(out_path, "w").write(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    args = sys.argv[1:]
    res = run([a for a in args[2:] if a.startswith("http")], args[0], args[1])
    print(res["hosts"], "hosts;", res["with_people_pages"], "with people pages;", res["people_urls_total"], "profile URLs")
