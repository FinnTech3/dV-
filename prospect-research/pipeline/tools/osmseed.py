"""Open-data seed: generate a large list of professional-service websites from OpenStreetMap, then find the ones that
publish people pages.

Why: every earlier route started from a directory somebody else wrote. OpenStreetMap lists, per city, the lawyers,
architects, estate agents, consultancies, clinics and dental practices that have a website. That gives thousands of
candidate firm sites without a search engine. Each site is then probed with the same sitemap-based, robots-honouring
method as before. OpenStreetMap's own phone tags are deliberately NOT used: they are business numbers, not people's.

  python -m pipeline.tools.osmseed seed  <out.json>
  python -m pipeline.tools.osmseed probe <seed.json> <out.json> [workers]
  python -m pipeline.tools.osmseed crawl <probe.json> [workers]
"""
from __future__ import annotations

import json
import re
import socket
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

from . import firmcrawl
from .probe import UA, probe_urls

socket.setdefaulttimeout(70)
BOX = {  # south, west, north, east
    "Madrid": (40.30, -3.80, 40.55, -3.55), "Barcelona": (41.32, 2.05, 41.47, 2.23), "Marbella-Malaga": (36.45, -4.95, 36.80, -4.35),
    "Alicante-Costa Blanca": (37.95, -0.80, 38.70, 0.20), "Valencia": (39.40, -0.45, 39.55, -0.30), "Seville": (37.33, -6.05, 37.43, -5.93),
    "Lisbon": (38.68, -9.25, 38.80, -9.08), "Cascais": (38.68, -9.50, 38.75, -9.35), "Porto": (41.10, -8.70, 41.20, -8.55), "Algarve": (36.95, -8.95, 37.25, -7.40),
    "Paris": (48.81, 2.25, 48.91, 2.42), "Paris-West": (48.84, 2.05, 48.92, 2.25), "Lyon": (45.70, 4.77, 45.80, 4.90), "Nice-Cannes": (43.55, 6.95, 43.74, 7.30),
    "Bordeaux": (44.80, -0.65, 44.90, -0.52), "Toulouse": (43.55, 1.38, 43.65, 1.50), "Montpellier": (43.58, 3.82, 43.64, 3.92), "Chamonix-Annecy": (45.85, 6.05, 45.95, 6.95),
    "Berlin": (52.40, 13.25, 52.60, 13.55), "Munich": (48.07, 11.45, 48.22, 11.70), "Frankfurt": (50.05, 8.58, 50.20, 8.78), "Hamburg": (53.48, 9.90, 53.65, 10.10),
    "Duesseldorf-Cologne": (50.90, 6.85, 51.30, 7.05), "Stuttgart": (48.74, 9.12, 48.82, 9.25),
    "Zurich": (47.33, 8.45, 47.43, 8.60), "Geneva": (46.17, 6.10, 46.24, 6.20), "Basel": (47.53, 7.55, 47.60, 7.65), "Lausanne-Vevey": (46.45, 6.55, 46.56, 6.90), "Zug-Lucerne": (47.05, 8.25, 47.20, 8.55),
    "Brussels": (50.80, 4.30, 50.90, 4.45), "Luxembourg": (49.57, 6.07, 49.65, 6.18), "Milan": (45.42, 9.12, 45.52, 9.25), "Rome": (41.85, 12.42, 41.95, 12.55),
    "Vienna": (48.17, 16.30, 48.25, 16.45), "Stockholm": (59.30, 18.00, 59.37, 18.12), "Copenhagen": (55.65, 12.50, 55.72, 12.62),
}
CATS = ['["office"~"^(lawyer|estate_agent|architect|employment_agency|consulting|advertising_agency|it|research|coworking|company|physician|therapist|educational_institution|property_management|relocation)$"]',
        '["amenity"~"^(dentist|clinic|doctors|school|language_school|university)$"]', '["healthcare"~"^(doctor|dentist|clinic|psychotherapist|physiotherapist)$"]']
LEISURE_BOX = {  # places where British, Irish and Dutch professionals run sport, leisure and hospitality businesses
    "Algarve-golf": (36.95, -8.95, 37.25, -7.40), "Costa-del-Sol": (36.40, -5.30, 36.80, -4.35), "Costa-Blanca": (37.90, -0.80, 38.75, 0.25),
    "Costa-Brava-Dorada": (41.00, 1.00, 42.35, 3.35), "Dordogne-SW-France": (44.60, -0.30, 45.30, 1.60), "Provence-Cote-d-Azur": (43.20, 4.80, 43.80, 7.40),
    "Alps-Chamonix-Morzine": (45.85, 6.05, 46.30, 6.95), "Alps-Savoie-Tarentaise": (45.30, 6.40, 45.60, 6.95), "Verbier-Valais": (45.95, 7.15, 46.20, 7.90),
    "Gstaad-Bernese-Oberland": (46.40, 7.20, 46.70, 8.20), "Engadin-Davos": (46.45, 9.50, 46.90, 10.10), "Silver-Coast-Alentejo": (38.80, -9.50, 39.60, -8.60),
    "Lake-Geneva-Vaud": (46.35, 6.40, 46.55, 7.00),
}
LEISURE_CATS = ['["leisure"~"^(golf_course|sports_centre|fitness_centre|swimming_pool|horse_riding|marina|dance|yoga)$"]',
                '["sport"~"^(golf|tennis|scuba_diving|sailing|skiing|equestrian|surfing|climbing|padel|yoga|kitesurfing)$"]',
                '["shop"~"^(ski|bicycle|outdoor|wine)$"]', '["tourism"~"^(guest_house|chalet|apartment|camp_site|hostel)$"]',
                '["craft"~"^(winery|brewery|photographer|carpenter|builder)$"]']
SKIP = re.compile(r"(facebook|instagram|linkedin|google|linktr|doctolib|jameda|wixsite|yelp|tripadvisor|booking\.com|twitter|youtube|wikipedia|"
                  r"pagesjaunes|paginasamarillas|11880|gelbeseiten|local\.ch|search\.ch|xing|kununu|treatwell|idealista|immobilienscout|seloger)", re.I)


def overpass(q: str) -> list[dict] | None:
    """None means the service refused or timed out (not 'no results'). Waits grow; the limit is respected, not evaded."""
    for attempt, wait in enumerate((0, 45, 90, 180)):
        time.sleep(wait)
        for ep in ("https://overpass-api.de/api/interpreter", "https://lz4.overpass-api.de/api/interpreter"):
            try:
                req = urllib.request.Request(ep, data=urllib.parse.urlencode({"data": q}).encode(), headers={"User-Agent": UA})
                return json.loads(urllib.request.urlopen(req, timeout=100).read())["elements"]
            except Exception:
                continue
    return None


def host_of(url: str) -> str | None:
    u = url if "//" in url else "http://" + url
    h = (urlsplit(u).hostname or "").lower()
    return h if "." in h and not SKIP.search(h) else None


def seed(out: str, leisure: bool = False) -> None:
    import os
    BOX_ = LEISURE_BOX if leisure else BOX
    CATS_ = LEISURE_CATS if leisure else CATS
    found: dict[str, dict] = json.load(open(out)) if os.path.exists(out) else {}
    done = set(json.load(open(out + ".done"))) if os.path.exists(out + ".done") else ({"Madrid"} if found else set())
    for market, (s, w, n, e) in BOX_.items():
        if market in done:
            continue
        union = "".join(f'nwr{c}["website"]({s},{w},{n},{e});' for c in CATS_)
        els = overpass(f"[out:json][timeout:80];({union});out tags 3000;")
        if els is None:
            print(f"{market:24s} REFUSED by the service after back-off; skipped for now", flush=True)
            continue
        done.add(market)
        json.dump(sorted(done), open(out + ".done", "w"))
        new = 0
        for el in els:
            t = el.get("tags", {})
            h = host_of(t.get("website") or t.get("contact:website") or "")
            if h and h not in found:
                found[h] = {"market": market, "name": t.get("name", ""), "category": t.get("office") or t.get("amenity") or t.get("healthcare") or ""}
                new += 1
        print(f"{market:24s} elements={len(els):5d} new domains={new:5d} total={len(found)}", flush=True)
        json.dump(found, open(out, "w"), ensure_ascii=False)
        time.sleep(30)


def probe(seed_path: str, out: str, workers: int = 32) -> None:
    seeds = json.load(open(seed_path))
    socket.setdefaulttimeout(12)
    def one(h):
        try:
            urls = probe_urls(h, firmcrawl.SMALL_SITE_PAT, max_maps=8)
            return h, urls
        except Exception:
            return h, []
    res = {}
    with ThreadPoolExecutor(workers) as ex:
        for i, (h, urls) in enumerate(ex.map(one, list(seeds))):
            if len(urls) >= 2:
                res[h] = {"label": seeds[h]["name"] or h, "market": seeds[h]["market"], "urls": urls[:400]}
            if i % 200 == 0:
                print(f"probed {i}/{len(seeds)}; with people pages: {len(res)}", flush=True)
                json.dump(res, open(out, "w"), ensure_ascii=False)
    json.dump(res, open(out, "w"), ensure_ascii=False)
    print(f"done: {len(res)} sites with >=2 people pages; {sum(len(v['urls']) for v in res.values())} profile URLs", flush=True)


def crawl(probe_path: str, workers: int = 48) -> None:
    res = json.load(open(probe_path))
    cc = firmcrawl.crawl_conn()
    for h, m in res.items():
        channel = m.get("channel") or ("open-data seed: professional websites in " + m["market"])
        cc.execute("INSERT OR REPLACE INTO host_meta VALUES (?,?,?,?)", (h, m["label"][:80], channel, m.get("source") or "OpenStreetMap"))
    cc.commit()
    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(lambda h: firmcrawl.crawl_host(h, None, 2.0, None, res[h]["urls"]), list(res)))
    print("crawl finished", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "seed":
        seed(sys.argv[2], leisure=len(sys.argv) > 3 and sys.argv[3] == "leisure")
    elif cmd == "probe":
        probe(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 32)
    elif cmd == "crawl":
        crawl(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 48)
