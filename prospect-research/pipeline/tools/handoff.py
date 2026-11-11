"""Merge external research assets (the PLAN pack, the ChatGPT supplement and this project's own findings)
into one deduplicated library inside the master database.

Nothing here is a prospect. Queries, organisations, employers, events and city plans are research
material; they are stored in their own tables and are never counted as individuals.

The merge is deterministic and safe to re-run: descriptive fields are refreshed from the files, but the
working status of a query (pending, done, ...) is never overwritten.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from . import db

HANDOFF = db.PIPELINE / "sources" / "handoff"
DOCS = db.ROOT / "docs"
TODAY = date(2026, 11, 11)
WINDOW = (date(2026, 11, 10), date(2027, 2, 10))
MON = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

EXTRA_SCHEMA = """
CREATE TABLE IF NOT EXISTS query_library (
    key TEXT PRIMARY KEY, kind TEXT NOT NULL, query TEXT NOT NULL, countries TEXT, cities TEXT, origins TEXT,
    angle TEXT, connector_type TEXT, priority TEXT, executable INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending', origin_files TEXT, merged_into TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS employer_seeds (
    key TEXT PRIMARY KEY, organisation TEXT NOT NULL, country TEXT, market TEXT, city_as_published TEXT, industry_cluster TEXT,
    source_url TEXT, geography_caveat TEXT, berlin_rank INTEGER, employees_reported INTEGER, origin_files TEXT,
    verified TEXT NOT NULL DEFAULT 'seed only: not a ranking, local presence unverified', people_directory TEXT);
CREATE TABLE IF NOT EXISTS events_register (
    key TEXT PRIMARY KEY, event TEXT NOT NULL, country TEXT, market TEXT, venue_locality TEXT, date_text TEXT, start_date TEXT, end_date TEXT,
    window_status TEXT, organiser TEXT, organiser_verification TEXT, official_page TEXT, programme_page TEXT, list_status TEXT,
    relevance TEXT, confidence TEXT, date_checked TEXT, origin_files TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS city_plan (
    market TEXT PRIMARY KEY, country TEXT, tier TEXT, wave TEXT, origin_lists TEXT, rationale TEXT, geography_caveat TEXT);
CREATE TABLE IF NOT EXISTS merge_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, asset TEXT, action TEXT, detail TEXT);
"""
SOURCE_COLS = {"extra_urls": "TEXT", "origin_files": "TEXT", "audit_status": "TEXT", "discrepancy": "TEXT", "person_lane": "TEXT"}


def migrate(conn: sqlite3.Connection) -> None:
    conn.executescript(EXTRA_SCHEMA)
    have = {r["name"] for r in conn.execute("PRAGMA table_info(sources)")}
    for col, typ in SOURCE_COLS.items():
        if col not in have:
            conn.execute(f"ALTER TABLE sources ADD COLUMN {col} {typ}")
    conn.commit()


# ------------------------------------------------------------------ normalisation
def fold(s: str | None) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def norm_q(q: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[\"“”()]", " ", fold(q))).strip()


def toks(q: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]{3,}", norm_q(q))) - {"and", "the", "for", "not", "site"}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def norm_org(name: str) -> str:
    n = re.sub(r"\(.*?\)", " ", fold(name))
    n = re.sub(r"\b(the|of|and|e v|ev|gmbh|ltd|sl|sa|ag|association|assoc)\b", " ", n)
    return re.sub(r"[^a-z0-9]+", " ", n).strip()


def host(url: str | None) -> str:
    h = (urlsplit(url or "").hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


SHARED_HOSTS = {"snbn.org", "snbn.nl", "ireland.ie", "api.ireland.ie", "dfa.ie", "gov.uk", "linkedin.com", "facebook.com", "eventbrite.com", "kvk.nl", "google.com"}

MARKETS = [("Madrid", "Spain"), ("Barcelona", "Spain"), ("Málaga", "Spain"), ("Alicante province", "Spain"),
           ("Lisbon", "Portugal"), ("Porto", "Portugal"), ("Cascais", "Portugal"), ("Algarve", "Portugal"),
           ("Paris", "France"), ("Lyon", "France"), ("Nice", "France"), ("Bordeaux", "France"), ("Toulouse", "France"),
           ("Berlin", "Germany"), ("Munich", "Germany"), ("Frankfurt", "Germany"),
           ("Zurich", "Switzerland"), ("Geneva", "Switzerland"), ("Basel", "Switzerland"), ("Lausanne", "Switzerland")]
_CITY_KEYS = [("malaga", "Málaga"), ("alicante", "Alicante province"), ("costa blanca", "Alicante province"), ("algarve", "Algarve"),
              ("cascais", "Cascais"), ("lisbon", "Lisbon"), ("lisboa", "Lisbon"), ("porto", "Porto"), ("matosinhos", "Porto"),
              ("paris", "Paris"), ("lyon", "Lyon"), ("nice", "Nice"), ("bordeaux", "Bordeaux"), ("toulouse", "Toulouse"),
              ("berlin", "Berlin"), ("munich", "Munich"), ("munchen", "Munich"), ("frankfurt", "Frankfurt"),
              ("zurich", "Zurich"), ("lausanne", "Lausanne"), ("vaud", "Lausanne"), ("geneva", "Geneva"), ("geneve", "Geneva"),
              ("basel", "Basel"), ("allschwil", "Basel"), ("muttenz", "Basel"), ("madrid", "Madrid"), ("barcelona", "Barcelona"),
              ("davos", "Other: Davos")]


def canon_market(s: str | None) -> str:
    f = fold(s)
    for k, v in _CITY_KEYS:
        if re.search(rf"\b{k}", f):
            return v
    return (s or "").strip() or "Unspecified"


# ------------------------------------------------------------------ date parsing
def parse_dates(text: str) -> tuple[date | None, date | None]:
    s = re.sub(r"\(.*?\)", "", text or "").replace("–", "-").replace("—", "-").strip()
    pats = [
        (r"(\d{1,2}) ([a-z]{3})[a-z]* (\d{4})\s*-\s*(\d{1,2}) ([a-z]{3})[a-z]* (\d{4})", lambda m: ((m[3], m[2], m[1]), (m[6], m[5], m[4]))),
        (r"(\d{1,2}) ([a-z]{3})[a-z]*\s*-\s*(\d{1,2}) ([a-z]{3})[a-z]* (\d{4})", lambda m: ((m[5], m[2], m[1]), (m[5], m[4], m[3]))),
        (r"(\d{1,2})\s*-\s*(\d{1,2}) ([a-z]{3})[a-z]* (\d{4})", lambda m: ((m[4], m[3], m[1]), (m[4], m[3], m[2]))),
        (r"(\d{1,2}) ([a-z]{3})[a-z]* (\d{4})", lambda m: ((m[3], m[2], m[1]), (m[3], m[2], m[1]))),
    ]
    for pat, f in pats:
        m = re.fullmatch(pat, s, re.I)
        if m:
            try:
                (y1, mo1, d1), (y2, mo2, d2) = f((None,) + m.groups())
                return (date(int(y1), MON[mo1.lower()[:3]], int(d1)), date(int(y2), MON[mo2.lower()[:3]], int(d2)))
            except (KeyError, ValueError):
                return None, None
    return None, None


def window_status(start: date | None, end: date | None) -> str:
    if not start:
        return "date_unparsed"
    end = end or start
    if end < TODAY:
        return "finished_before_today"
    if end < WINDOW[0] or start > WINDOW[1]:
        return "outside_window"
    return "underway_today" if start <= TODAY <= end else "upcoming"


# ------------------------------------------------------------------ readers
def rows(name: str) -> list[dict]:
    with (HANDOFF / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def md_table(path: Path, min_cols: int) -> list[list[str]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and not re.match(r"^\|[-| ]+\|$", line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= min_cols:
                out.append(cells)
    return out[1:] if out else out


def log(conn, asset: str, action: str, detail: str) -> None:
    conn.execute("INSERT INTO merge_log (ts, asset, action, detail) VALUES (?,?,?,?)", (db.now_iso(), asset, action, detail[:500]))


# ------------------------------------------------------------------ queries
CLAUDE_EXECUTED = [  # discovery and compliance searches already run in this project's earlier sessions (WebSearch, standard mode)
    "British Chamber of Commerce in Spain member directory",
    "estate agents Costa Blanca meet the team moved to Spain worked in London mobile +34 6",
    "Algarve property agency our team originally from England moved to Portugal mobile +351 9",
    "Marbella law firm English-speaking solicitor qualified in England practised in London team direct mobile",
    "Immobilienmakler Berlin OR München English-speaking team born in England moved to Germany worked in London mobil +49 1",
    "agence immobilière Dordogne OR Bordeaux OR Toulouse English-speaking agents team moved to France worked in UK portable +33 6",
    "law firm Frankfurt lawyer profiles Solicitor (England and Wales) Rechtsanwalt team page direct dial",
    "law firm press release partner relocates from London OR relocating from London to Frankfurt OR Paris OR Madrid OR Milan OR Luxembourg office 2025 2026",
    "British Chamber of Commerce in Germany BCCG official website regions Berlin Munich Frankfurt events",
    "Franco-British Chamber of Commerce Paris official website members directory events",
    "British-Portuguese Chamber of Commerce bpcc.pt members directory events Lisbon Algarve Porto",
    "Ireland Spain Economic Association, Ireland Portugal Business Network, Irish Business Network Germany, Ireland France Chamber of Commerce, Irish Business Network Switzerland official sites",
    "Dutch business association abroad: Netherlands Chamber of Commerce Spain, Câmara de Comércio Portugal-Holanda, Nederlandse Vereniging Zürich, Dutch business club Paris, Deutsch-Niederländische Handelskammer",
    "British Chamber of Commerce Germany, British-Swiss Chamber of Commerce, Franco-British Chamber, British-Portuguese Chamber of Commerce events calendar December 2026 January 2027",
    "Live Spain For Life Albatera Sharon Richards LinkedIn",
    "Inmo Investments La Zenia Mike Harrison marketing manager LinkedIn",
]


def import_queries(conn: sqlite3.Connection) -> dict:
    items: list[dict] = []
    for r in rows("LinkedIn_Search_Library.csv"):
        items.append(dict(kind="linkedin_boolean", query=r["Boolean_search_string"], countries=r["target_country"], cities="", origins="", angle=r["variant"],
                          connector_type="", priority="", executable=0, f="LinkedIn_Search_Library.csv",
                          note="Planning template only: no scraping and no logged-in automation. Same wording is repeated across destination filters."))
    for r in rows("Quick_Win_Connector_Searches.csv"):
        items.append(dict(kind="connector", query=r["public_web_search_string"], countries=r["country"], cities=r["target_city"], origins="", angle="",
                          connector_type=r["connector_type"], priority="", executable=1, f="Quick_Win_Connector_Searches.csv", note=r["note"]))
    for r in rows("Public_Web_Research_Queries.csv"):
        items.append(dict(kind="public_web", query=r["public_web_search_query"], countries=r["target_country"], cities=r["target_city"], origins=r["origin_country"],
                          angle="base", connector_type="", priority="", executable=1, f="Public_Web_Research_Queries.csv", note=r["use_limit"]))
    for r in rows("ChatGPT_Expanded_Public_Web_Queries.csv"):
        items.append(dict(kind="public_web", query=r["public_web_query"], countries=r["target_country"], cities=r["target_city"], origins=r["origin_country"],
                          angle=r["search_angle"], connector_type="", priority=r["priority"], executable=1, f="ChatGPT_Expanded_Public_Web_Queries.csv", note=r["use_limit"]))
    for q in CLAUDE_EXECUTED:
        items.append(dict(kind="executed", query=q, countries="", cities="", origins="", angle="", connector_type="", priority="", executable=0,
                          f="claude_session", note="Already run in an earlier session; do not repeat."))
    by_key: dict[str, dict] = {}
    exact = 0
    for it in items:
        key = hashlib.sha1((it["kind"] + "|" + norm_q(it["query"])).encode()).hexdigest()[:16]
        it["key"] = key
        if key in by_key:
            exact += 1
            e = by_key[key]
            for fld in ("countries", "cities", "origins"):
                vals = set(filter(None, (e[fld] + "," + it[fld]).split(",")))
                e[fld] = ",".join(sorted(vals))
            e["files"].add(it["f"])
        else:
            it["files"] = {it["f"]}
            it["merged_into"] = None
            by_key[key] = it
    # near-duplicates: same kind, city and origin, very similar wording
    near = 0
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for it in by_key.values():
        if it["kind"] in ("public_web", "connector"):
            groups[(it["kind"], it["cities"], it["origins"], it["connector_type"])].append(it)
    for g in groups.values():
        for i, a in enumerate(g):
            if a["merged_into"]:
                continue
            for b in g[i + 1:]:
                if not b["merged_into"] and jaccard(toks(a["query"]), toks(b["query"])) >= 0.85:
                    b["merged_into"] = a["key"]
                    near += 1
    conn.execute("DELETE FROM query_library WHERE key NOT IN (%s)" % ",".join("?" * len(by_key)), list(by_key))
    for it in by_key.values():
        status = "merged_near_duplicate" if it["merged_into"] else ("planning_only" if not it["executable"] and it["kind"] == "linkedin_boolean"
                                                                    else ("done" if it["kind"] == "executed" else "pending"))
        conn.execute(
            """INSERT INTO query_library (key, kind, query, countries, cities, origins, angle, connector_type, priority, executable, status, origin_files, merged_into, note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(key) DO UPDATE SET countries=excluded.countries, cities=excluded.cities, origins=excluded.origins, angle=excluded.angle,
                 connector_type=excluded.connector_type, priority=excluded.priority, origin_files=excluded.origin_files, merged_into=excluded.merged_into,
                 note=excluded.note, executable=excluded.executable""",
            (it["key"], it["kind"], it["query"], it["countries"], it["cities"], it["origins"], it["angle"], it["connector_type"], it["priority"],
             it["executable"], status, ",".join(sorted(it["files"])), it["merged_into"], it["note"]))
    conn.commit()
    c = Counter((r["kind"], r["status"]) for r in conn.execute("SELECT kind, status FROM query_library"))
    stats = {"input_rows": len(items), "exact_duplicates_removed": exact, "near_duplicates_merged": near, "library_rows": len(by_key),
             "by_kind_status": {f"{k}/{s}": n for (k, s), n in sorted(c.items())}}
    log(conn, "queries", "merged", json.dumps(stats))
    return stats


# ------------------------------------------------------------------ organisations and directories
def _claude_sources() -> list[dict]:
    out = []
    for c in md_table(DOCS / "sources.md", 10):
        url = c[1] if c[1].startswith("http") else ""
        out.append(dict(name=c[0], url=url, country=ISO.get(c[2].split("/")[0].strip(), c[2].split("/")[0].strip()), type="", public=c[3], nonpublic=c[4], phones=c[5], profiles=c[6],
                        membership=c[7], automated=c[8], status=c[9], f="claude_session"))
    return out


ISO = {"ES": "Spain", "PT": "Portugal", "FR": "France", "DE": "Germany", "CH": "Switzerland", "NL": "Netherlands", "GB": "United Kingdom"}


def _cities_in(name: str) -> set[str]:
    f = fold(name)
    return {v for k, v in _CITY_KEYS if re.search(rf"\b{k}", f)}


def import_sources(conn: sqlite3.Connection) -> dict:
    recs: list[dict] = []
    for r in rows("Public_Organisations_and_Directories.csv"):
        recs.append(dict(name=r["organisation"], url=r["official_url"], country=r["country"], type=r["type"], public=r["what_is_public"],
                         nonpublic=r["what_is_not_verified_or_not_public"], phones="", profiles="", membership="", automated=r["checks_before_use"], status="", f="Public_Organisations_and_Directories.csv"))
    for r in rows("ChatGPT_Official_Directory_Audit.csv"):
        recs.append(dict(name=r["organisation"], url=r["official_url"], country=r["country"], type=r["type"], public=r["what_is_public_or_verified"],
                         nonpublic=r["what_is_not_public_or_uncertain"], phones=r["telephone_publication"], profiles=r["research_use"], membership="", automated="",
                         status=r["status_checked_2026_11_10"], f="ChatGPT_Official_Directory_Audit.csv"))
    recs += _claude_sources()
    merged: list[dict] = []
    log_lines = []
    for r in recs:
        n, h = norm_org(r["name"]), host(r["url"])
        target = None
        for m in merged:
            same_country = fold(m["country"])[:4] == fold(r["country"])[:4]
            ca, cb = _cities_in(r["name"]), _cities_in(m["name"])
            if same_country and (m["norm"] == n or (h and h == m["host"] and h not in SHARED_HOSTS and not (ca and cb and ca != cb))):
                target = m
                break
        if target is None:
            merged.append(dict(r, norm=n, host=h, files={r["f"]}, extra=set(), names={r["name"]}))
            continue
        target["files"].add(r["f"])
        target["names"].add(r["name"])
        if r["url"] and r["url"] != target["url"]:
            target["extra"].add(r["url"])
        # the independent audit is newer and more precise: it wins where it has a value; other files fill gaps
        audit = r["f"].startswith("ChatGPT")
        for fld in ("type", "public", "nonpublic", "phones", "profiles", "membership", "automated", "status"):
            if r[fld] and (audit or not target[fld]):
                if target[fld] and audit and r[fld] != target[fld] and fld in ("nonpublic", "automated", "status"):
                    target.setdefault("prev", {})[fld] = target[fld]
                target[fld] = r[fld]
        if audit and r["url"]:
            if target["url"] and target["url"] != r["url"]:
                target["extra"].add(target["url"])
            target["url"] = r["url"]
            target["extra"].discard(r["url"])
        if r["f"] == "claude_session":
            target["claude_access"] = r["automated"]
            target["claude_status"] = r["status"]
        log_lines.append(f"{sorted(target['names'])[0]} <- {r['name']} ({r['f']})")
    # keep this project's own access findings on merged records
    for m in merged:
        if m["f"] == "claude_session" or "claude_session" in m["files"]:
            m.setdefault("claude_access", m["automated"] if m["f"] == "claude_session" else m.get("claude_access", ""))
    conn.execute("DELETE FROM sources WHERE origin_files IS NULL OR origin_files NOT LIKE 'snowball:%'")   # keep member sites found by the snowball
    for m in merged:
        url = m["url"] or "urn:unconfirmed:" + re.sub(r"[^a-z0-9]+", "-", m["norm"])
        disc = []
        if m.get("claude_status") and m.get("status") and "claude_session" in m["files"] and len(m["files"]) > 1:
            disc.append(f"Earlier Claude session: {m['claude_status']}")
        conn.execute(
            """INSERT OR REPLACE INTO sources (name, url, source_type, country, city, public_content, non_public_content, publishes_individual_phones, profiles_public,
               membership_required, automated_access, reliability, date_checked, access_restriction, extra_urls, origin_files, audit_status, discrepancy)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (m["name"], url, m["type"], m["country"], "", m["public"], m["nonpublic"], m["phones"], m["profiles"],
             m["membership"], m["automated"], "", "2026-11-10", m.get("claude_access", ""), " | ".join(sorted(m["extra"])), ",".join(sorted(m["files"])),
             m["status"], "; ".join(disc)))
    conn.commit()
    stats = {"input_rows": len(recs), "merged_organisations": len(merged), "duplicates_removed": len(recs) - len(merged),
             "in_all_three": sum(1 for m in merged if len(m["files"]) == 3), "only_claude_pack": sum(1 for m in merged if m["files"] == {"Public_Organisations_and_Directories.csv"}),
             "only_chatgpt_audit": sum(1 for m in merged if m["files"] == {"ChatGPT_Official_Directory_Audit.csv"}),
             "only_this_project": sum(1 for m in merged if m["files"] == {"claude_session"}), "merge_examples": log_lines[:12]}
    log(conn, "sources", "merged", json.dumps(stats)[:480])
    return stats


# ------------------------------------------------------------------ events
def import_events(conn: sqlite3.Connection) -> dict:
    recs: list[dict] = []
    for r in rows("Events_Nov2026_Feb2027.csv"):
        recs.append(dict(event=r["event"], country=r["country"], city=r["city"], venue="", date=r["dates"], organiser=r["organiser"], orgv="", page=r["official_page"],
                         prog=r["programme_or_list_page"], lists=r["public_list_status"], rel="", conf="", checked="", f="Events_Nov2026_Feb2027.csv"))
    for r in rows("ChatGPT_Verified_Official_Events.csv"):
        recs.append(dict(event=r["event"], country=r["country"], city=r["target_city"], venue=r["actual_venue_locality"], date=r["date"], organiser=r["organiser"],
                         orgv=r["organiser_verification"], page=r["official_event_page"], prog=r["programme_speaker_exhibitor_page"], lists=r["what_is_public_and_list_status"],
                         rel=r["prospecting_relevance"], conf=r["confidence"], checked=r["date_checked"], f="ChatGPT_Verified_Official_Events.csv"))
    for c in md_table(DOCS / "plan" / "events.md", 8):
        recs.append(dict(event=c[0], country="", city=c[2], venue="", date=c[3], organiser=c[1], orgv="", page=c[4], prog=c[5],
                         lists="Attendee list: " + c[6], rel="", conf="verified on organiser's own page", checked="2026-11-10", f="claude_session"))
    merged: list[dict] = []
    for r in recs:
        s, e = parse_dates(r["date"])
        r.update(start=s, end=e, norm=re.sub(r"[^a-z0-9]+", " ", re.sub(r"\b20\d\d\b", "", fold(r["event"]))).strip())
        tgt = None
        for m in merged:
            if r["start"] and m["start"] == r["start"] and canon_market(r["city"]) == canon_market(m["city"]) or (r["start"] and m["start"] == r["start"] and not r["country"]):
                a, b = toks(r["norm"]), toks(m["norm"])
                if r["norm"] == m["norm"] or r["norm"] in m["norm"] or m["norm"] in r["norm"] or jaccard(a, b) >= 0.5 or (a & b and r["f"] == "claude_session"):
                    tgt = m
                    break
            elif not r["start"] and r["norm"] == m["norm"] and canon_market(r["city"]) == canon_market(m["city"]):
                tgt = m
                break
        if tgt is None:
            merged.append(dict(r, files={r["f"]}))
            continue
        tgt["files"].add(r["f"])
        audit = r["f"].startswith("ChatGPT")
        for fld in ("venue", "organiser", "orgv", "page", "prog", "lists", "rel", "conf", "checked", "country"):
            if r[fld] and (audit or not tgt[fld]):
                tgt[fld] = r[fld]
    conn.execute("DELETE FROM events_register")
    for m in merged:
        mk = canon_market(m["city"])
        ws = window_status(m["start"], m["end"])
        key = hashlib.sha1(f"{m['norm']}|{m['start']}|{mk}".encode()).hexdigest()[:16]
        note = ("Venue locality differs from the target market and is kept separately; do not assign the market's municipality."
                if m["venue"] and fold(mk.split(" province")[0]) not in fold(m["venue"]) else "")
        conn.execute("INSERT OR REPLACE INTO events_register VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (key, m["event"], m["country"], mk, m["venue"], m["date"], m["start"].isoformat() if m["start"] else None,
                      m["end"].isoformat() if m["end"] else None, ws, m["organiser"], m["orgv"], m["page"], m["prog"], m["lists"], m["rel"], m["conf"],
                      m["checked"], ",".join(sorted(m["files"])), note))
    conn.commit()
    c = Counter(r["window_status"] for r in conn.execute("SELECT window_status FROM events_register"))
    stats = {"input_rows": len(recs), "merged_events": len(merged), "duplicates_removed": len(recs) - len(merged), "by_window_status": dict(c),
             "in_two_or_more_files": sum(1 for m in merged if len(m["files"]) > 1)}
    log(conn, "events", "merged", json.dumps(stats))
    return stats


# ------------------------------------------------------------------ employers
def import_employers(conn: sqlite3.Connection) -> dict:
    recs: list[dict] = []
    for r in rows("City_Industry_Employer_Seeds.csv"):
        recs.append(dict(org=r["organisation"], country=r["country"], city=r["target_city"], cluster=r["industry_cluster"], url=r["source_url"], cav=r["verification_note"],
                         rank=None, emp=None, f="City_Industry_Employer_Seeds.csv"))
    for r in rows("ChatGPT_Berlin_Top50_Employers_2025.csv"):
        recs.append(dict(org=r["employer_as_published_or_translated"], country="Germany", city="Berlin", cluster=r["industry_as_reported"], url=r["source_url"],
                         cav=r["geography"], rank=int(r["rank_2025"]), emp=int(float(r["employees_reported_2025"] or 0)) or None, f="ChatGPT_Berlin_Top50_Employers_2025.csv"))
    ctry = {m: c for m, c in MARKETS}
    for c in md_table(DOCS / "plan" / "industries.md", 6):
        for org in re.split(r";", re.sub(r"\(.*?\)", "", c[3])):
            org = org.strip()
            if org and org.lower() not in ("none named", "none"):
                recs.append(dict(org=org, country=c[0], city=c[1], cluster=c[2], url=re.sub(r".*\((https?://[^)]+)\).*", r"\1", c[4]) if "](" in c[4] else "",
                                 cav=c[5], rank=None, emp=None, f="claude_session"))
    merged: dict[str, dict] = {}
    for r in recs:
        mk = canon_market(r["city"])
        key = norm_org(r["org"]) + "|" + mk
        m = merged.get(key)
        if not m:
            merged[key] = dict(r, market=mk, files={r["f"]}, cities={r["city"]})
        else:
            m["files"].add(r["f"])
            m["cities"].add(r["city"])
            if r["rank"] and not m["rank"]:
                m["rank"], m["emp"] = r["rank"], r["emp"]
            if r["f"] == "ChatGPT_Berlin_Top50_Employers_2025.csv":
                m["cav"] = r["cav"]
    conn.execute("DELETE FROM employer_seeds")
    PRO = re.compile(r"(professional|consulting|law|legal|recruit|real estate|property)", re.I)
    for key, m in merged.items():
        pd = "candidate: professional-services cluster; check for a public people directory" if PRO.search(m["cluster"] or "") else ""
        conn.execute("INSERT OR REPLACE INTO employer_seeds (key, organisation, country, market, city_as_published, industry_cluster, source_url, geography_caveat, berlin_rank, employees_reported, origin_files, people_directory) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                     (key, m["org"], m["country"], m["market"], " / ".join(sorted(m["cities"])), m["cluster"], m["url"], m["cav"], m["rank"], m["emp"], ",".join(sorted(m["files"])), pd))
    conn.commit()
    c = Counter(r["market"] for r in conn.execute("SELECT market FROM employer_seeds"))
    stats = {"input_rows": len(recs), "merged_employer_market_pairs": len(merged), "duplicates_removed": len(recs) - len(merged),
             "unique_organisations": len({norm_org(m['org']) for m in merged.values()}), "by_market": dict(c)}
    log(conn, "employers", "merged", json.dumps(stats)[:480])
    return stats


# ------------------------------------------------------------------ city plan and run log
def import_city_plan(conn: sqlite3.Connection) -> dict:
    pri = {canon_market(r["target_city"]): r for r in rows("ChatGPT_City_Research_Priority.csv")}
    econ = {canon_market(r["target_city"]): r for r in rows("ChatGPT_City_Economy_Evidence.csv")}
    pack = {"Madrid", "Barcelona", "Málaga", "Lisbon", "Porto", "Cascais", "Paris", "Lyon", "Nice", "Berlin", "Munich", "Frankfurt", "Zurich", "Geneva", "Basel"}
    mine = {"Barcelona", "Málaga", "Alicante province", "Lisbon", "Porto", "Algarve", "Paris", "Bordeaux", "Toulouse", "Berlin", "Munich", "Frankfurt", "Zurich", "Lausanne", "Geneva"}
    conn.execute("DELETE FROM city_plan")
    for market, country in MARKETS:
        lists = [n for n, s in (("claude_plan_pack", pack), ("chatgpt_supplement", set(pri)), ("claude_session", mine)) if market in s]
        p, e = pri.get(market), econ.get(market)
        tier = "primary" if market in pack else "secondary"
        rat = (p["evidence_based_reason"] if p else "Selected in this project's own session from resident-count evidence (British nationals), skewing to older residents; kept as a secondary market.")
        cav = "; ".join(x for x in [(p or {}).get("geography_or_source_caveat", ""), (e or {}).get("geography_and_limitations", "")] if x)
        conn.execute("INSERT INTO city_plan VALUES (?,?,?,?,?,?,?)", (market, country, tier, p["recommended_research_wave"] if p else "Wave 2 (secondary)", ",".join(lists), rat, cav[:600]))
    conn.commit()
    return {"markets": len(MARKETS), "primary": sum(1 for m, _ in MARKETS if m in pack), "secondary": sum(1 for m, _ in MARKETS if m not in pack)}


def import_run_log(conn: sqlite3.Connection) -> dict:
    n = 0
    for r in rows("ChatGPT_Web_Research_Run_Log.csv"):
        if r["source_url"].startswith("http"):
            if conn.execute("INSERT OR IGNORE INTO searched (key, kind, provider, ts, result_count) VALUES (?,?,?,?,NULL)",
                            (r["source_url"].strip().lower(), "page", "chatgpt_run_log", db.now_iso())).rowcount:
                n += 1
    conn.commit()
    return {"urls_already_reviewed_by_chatgpt_added_to_searched_register": n}


def run_all(db_path=None) -> dict:
    conn = db.connect(db_path)
    migrate(conn)
    out = {"queries": import_queries(conn), "sources": import_sources(conn), "events": import_events(conn), "employers": import_employers(conn),
           "city_plan": import_city_plan(conn), "run_log": import_run_log(conn)}
    conn.commit()
    return out


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=1, ensure_ascii=False, default=str))
