"""Quantity fill requested by the project lead: people with a name, a number and a LinkedIn link on their own profile page, but NO
UK/IE/NL link found. They are ingested as ASK (prior residence and employment unestablished) in batch FILLER, noted as such,
ordered last in the presentation sheet, and never counted as valid prospects.

Ranking: mobile label first, then a number unique to the page, then a stated job title; at most `per_host` people per site.
Excluded: anyone whose title is a financial-adviser or financially ambiguous role, UK/IE numbers, names that are not a person's name.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict

from . import db, firmcrawl, render, verify

NAME_TOKEN = re.compile(r"^(?:[A-ZÀ-ÖØ-Þ][a-zà-öø-ÿ'’-]{1,}|[A-ZÀ-ÖØ-Þ]\.)$")
PARTICLES = {"van", "von", "de", "der", "den", "da", "di", "del", "della", "dos", "du", "la", "le", "ter", "zu", "af", "al", "el", "bin", "y"}
JUNK = re.compile(r"(?i)(faculty|alumni|fellows|unit\b|institut|department|lab\b|voices|gallery|members|student|keynote|club|contact|profiles?\b|team\b|"
                  r"staff|directory|overview|group\b|centre|center|school|university|news|about|our |archive|speakers|partners|office|law\b|legal|"
                  r"consult|capital|bank|fund|management|solutions|services|holding|international|global|europe|group)")


def looks_like_person(name: str) -> bool:
    first, last = render.clean_name(*(name.strip().split(" ", 1) + [""])[:2])
    full = f"{first} {last}".split()
    if not (2 <= len(full) <= 4) or len(name) > 40 or JUNK.search(name):
        return False
    return all(t.lower() in PARTICLES or NAME_TOKEN.match(t) for t in full)


def pick(settings: dict, n: int, per_host: int = 6) -> list[dict]:
    eligible = set(settings["eu_mainland_eligible"])
    cr = firmcrawl.crawl_conn()
    conn = db.connect()
    have_ext = {r[0][4:] for r in conn.execute("SELECT key FROM meta WHERE key LIKE 'ext:%'")}
    have_names = {(r["first_name"] + " " + r["last_name"]).lower() for r in conn.execute("SELECT first_name, last_name FROM persons")}
    meta = {m["host"]: m["label"] for m in cr.execute("SELECT * FROM host_meta")}
    seen_phone = Counter()
    rows = cr.execute("SELECT * FROM pages WHERE status=200 AND name!='' AND tels!='[]' AND linkedin IS NOT NULL").fetchall()
    for r in rows:
        for t in json.loads(r["tels"]):
            seen_phone[t["e164"]] += 1
    scored = []
    for r in rows:
        if r["origin"] and r["sentence"]:
            continue                                  # already considered as a UK/IE/NL candidate
        tels = json.loads(r["tels"])
        regions = {t["region"] for t in tels}
        if not regions or regions & {"GB", "IE"} or not regions <= eligible:
            continue
        if f"firm:{r['host']}:{r['slug']}" in have_ext or not looks_like_person(r["name"]):
            continue
        first, last = render.clean_name(*(r["name"].strip().split(" ", 1) + [""])[:2])
        key = f"{first} {last}".lower()
        if not last or key in have_names:
            continue
        role = firmcrawl.clean_role(re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), r["role"] or ""), meta.get(r["host"], r["host"]), r["name"])
        if role and (not role[0].isalnum() or role[0].islower() or len(role) > 90):
            role = ""                                 # a sentence fragment, not a title
        if role and verify.screen_occupation(role) != "clear":
            continue                                  # advisers and financially ambiguous roles stay out
        mobile = next((t for t in tels if t["label"] == "mobile"), None)
        own = [t for t in tels if seen_phone[t["e164"]] == 1]
        chosen = mobile or (own[0] if own else tels[0])
        scored.append((0 if mobile else 1, 0 if own else 1, 0 if role else 1, r["host"], key, r, chosen, role))
    scored.sort(key=lambda x: x[:4])
    out, per, names = [], defaultdict(int), set()
    for *_, key, r, chosen, role in scored:
        if per[r["host"]] >= per_host or key in names:
            continue
        per[r["host"]] += 1
        names.add(key)
        firm = meta.get(r["host"]) or firmcrawl.FIRMS.get(r["host"], r["host"])
        first, last = r["name"].strip().split(" ", 1)
        ev = lambda c, lv, ext, lim, **kw: {"criterion": c, "level": lv, "source_url": r["url"], "organisation": firm, "reliability": "PRIMARY",
                                           "publication_date": None, "retrieval_date": r["fetched"][:10], "extract": ext, "limitations": lim, **kw}
        out.append({
            "first_name": first, "last_name": last,
            "occupation": f"{role}, {firm}" if role else f"Professional at {firm} (title not stated on profile)", "employer": firm,
            "linkedin_url": r["linkedin"], "linkedin_captured_from": r["url"],
            "phone_raw": chosen["e164"], "phone_type": chosen["label"] if chosen["label"] != "unknown" else "unknown",
            "phone_attribution": "published on the person's own profile page", "phone_source_url": r["url"],
            "cur_res_country": chosen["region"], "external_id": f"firm:{r['host']}:{r['slug']}",
            "notes": "FILLER: no UK/IE/NL link found on the page; added for quantity at the project lead's request",
            "evidence": [
                ev("prev_employment", "NONE", "No UK/IE/NL link found on the profile page", "Not established"),
                ev("prev_residence", "NONE", "No UK/IE/NL link found on the profile page", "Not established"),
                ev("cur_residence", "WEAK", f"Profile lists a {chosen['region']} office number", "Office location only"),
                ev("occupation", "STRONG" if role else "MODERATE", role or "Profile on the firm's people directory", "Live profile, undated", live_first_party=True),
                ev("phone", "STRONG" if seen_phone[chosen["e164"]] == 1 else "WEAK", chosen["raw"], None if seen_phone[chosen["e164"]] == 1 else "Shared number"),
            ]})
        if len(out) >= n:
            break
    return out


if __name__ == "__main__":
    n = int(sys.argv[1])
    cands = pick(db.load_settings(), n)
    path = db.PIPELINE / "staging" / "FILLER.json"
    path.write_text(json.dumps({"batch_id": "FILLER", "channel": "crawl: people pages without a UK/IE/NL link", "source": "firm people pages",
                                "country": "multi", "city": "multi", "candidates": cands}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(cands), "candidates;", Counter(c["employer"] for c in cands).most_common(5))
