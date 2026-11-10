"""Crawl public professional-firm profile pages and extract candidate facts by rule.

Scope and safeguards:
* Only URLs listed in the firm's own sitemap and allowed by its robots.txt are fetched,
  one request every `delay` seconds per host, with an identifying User-Agent.
* A refusal (401/403/429) stops that host; nothing is retried under another identity.
* Extraction is conservative and mechanical. Every claim keeps the sentence it came from.
  Office location is recorded as WEAK evidence of residence, never as proof.
* Raw results live in pipeline/evidence/crawl.sqlite (git-ignored). Nothing here writes
  to the master database; `stage()` only produces staging batches for `cli ingest`.
"""
from __future__ import annotations

import html
import json
import re
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import phonenumbers

from . import db, linkedin
from .probe import UA, probe_urls

CRAWL_DB = db.PIPELINE / "evidence" / "crawl.sqlite"
_lock = threading.Lock()

UK = r"London|United Kingdom|\bU\.?K\.?\b|England|Scotland|Wales|Edinburgh|Manchester|Birmingham|Bristol|Leeds|Glasgow|Reading|Cambridge office|Londres|Reino Unido|Royaume-Uni|Gro(ß|ss)britannien|Vereinigte[sn]? K(ö|oe)nigreich|Londra|Regno Unito"
IE = r"Dublin|Ireland|Irland|Irlande|Irlanda"
NL = r"Amsterdam|Rotterdam|The Hague|Den Haag|Netherlands|Niederlande|Pays-Bas|Pa(í|i)ses Bajos|Utrecht|Eindhoven"
PLACE = re.compile(f"({UK}|{IE}|{NL})")
WORK = re.compile(
    r"\b(worked|working (for|at|in)|practi[sc]ed|spent|was based|were based|trained (at|with|in)|training contract|"
    r"began (his|her|their) career|started (his|her|their) career|career (at|in|with)|joined .{0,60} in|"
    r"second(ed|ment)|associate (at|in|with)|lawyer (at|in|with)|solicitor (at|in|with)|years? (at|in|with)|"
    r"previously (at|with|in)|formerly (at|with|in|a|an)|office in|(London|Dublin|Amsterdam) office|"
    r"t(ä|ae)tig|arbeitete|Stationen? in|a travaill(é|e)|a exerc(é|e)|collaborat(eur|rice)|trabaj(ó|o) en|ejerci(ó|o)|trabalhou|"
    r"exerceu|ha lavorato|werkzaam)\b", re.IGNORECASE)
EDU = re.compile(r"(LL\.?\s?M|LL\.?\s?B|universit|studied|studies|degree|college|school of|King'?s|\bUCL\b|\bLSE\b|"
                 r"Oxford|Cambridge|graduat|studium|studierte|dipl(ô|o)m|master|ph\.?d|doctor|erasmus|exchange|"
                 r"licenci|máster|mestrado|laurea|scholar)", re.IGNORECASE)
HARD_WORK = re.compile(r"\b(worked|practi[sc]ed|training contract|associate|solicitor (at|in|with)|second(ed|ment)|office|"
                       r"t(ä|ae)tig|a travaill|a exerc|trabaj|trabalh|career)\b", re.IGNORECASE)
NOISE = re.compile(r"(clients? (in|based|from)|London[- ]based|Stock Exchange|\bLCIA\b|Court of|Law Society|admitted|"
                   r"member of|lectur|speaker|conference|listed (on|in)|headquartered|investors? (in|from)|"
                   r"second(ed|ment)s? (to|at|with) (a|an|the|one of|several|various|major|leading)?[^.]{0,40}(client|bank|company|fund|group|corporate)|"
                   r"splits? (his|her|their) time|divides? (his|her|their) time|between .{0,25} and )", re.IGNORECASE)
MOBILE = re.compile(r"(mobile|mobil\b|\bcell|portable|m(ó|o)vil|handy|telem(ó|o)vel|natel|\bmob\b|(^|[\s>])M[:.]?\s*$|cellulare|gsm)", re.IGNORECASE)
DIRECT = re.compile(r"(direct|durchwahl|ligne directe|directo|\bD[:.]\s*$|\bDDI\b)", re.IGNORECASE)
YEAR = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")
LIVED = re.compile(r"\b(lived|living|grew up|born|raised|moved (from|to)|relocat|returned)\b", re.IGNORECASE)

CITIES = ["Frankfurt", "Munich", "München", "Berlin", "Hamburg", "Düsseldorf", "Dusseldorf", "Cologne", "Köln", "Stuttgart",
          "Paris", "Lyon", "Bordeaux", "Toulouse", "Marseille", "Madrid", "Barcelona", "Valencia", "Málaga", "Malaga", "Alicante",
          "Sevilla", "Seville", "Bilbao", "Lisbon", "Lisboa", "Porto", "Zurich", "Zürich", "Geneva", "Genève", "Lausanne", "Basel",
          "Zug", "Bern", "Milan", "Milano", "Rome", "Roma", "Brussels", "Bruxelles", "Luxembourg", "Vienna", "Wien", "Warsaw",
          "Prague", "Budapest", "Stockholm", "Copenhagen", "Helsinki", "Athens", "Bucharest", "Sofia", "Bratislava", "Zagreb",
          "Ljubljana", "Antwerp", "Turin", "Torino", "Krakow", "Gothenburg", "Malmö", "Aarhus", "Vilnius", "Riga", "Tallinn"]
CITY = re.compile(r"\b(" + "|".join(map(re.escape, CITIES)) + r")\b")


def crawl_conn() -> sqlite3.Connection:
    CRAWL_DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(CRAWL_DB), check_same_thread=False, timeout=60)
    c.row_factory = sqlite3.Row
    c.execute("""CREATE TABLE IF NOT EXISTS pages (url TEXT PRIMARY KEY, host TEXT, slug TEXT, status INTEGER, fetched TEXT,
                 name TEXT, role TEXT, tels TEXT, linkedin TEXT, city TEXT, regions TEXT, origin TEXT, sentence TEXT,
                 has_years INTEGER, lived INTEGER, text_len INTEGER)""")
    c.execute("CREATE TABLE IF NOT EXISTS hosts (host TEXT PRIMARY KEY, state TEXT, note TEXT)")
    c.commit()
    return c


def _text(markup: str) -> str:
    markup = re.sub(r"(?is)<(script|style|noscript|template|svg|nav|footer|header)[^>]*>.*?</\1>", " ", markup)
    markup = re.sub(r"(?is)<(br|/p|/div|/li|/h\d|/tr)[^>]*>", ". ", markup)
    markup = re.sub(r"(?s)<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(markup)).strip()


def extract(url: str, body: str) -> dict:
    """Pull name, role, phones (with the label the page gives them), LinkedIn link and work-history sentence."""
    h1 = re.search(r"(?is)<h1[^>]*>(.*?)</h1>", body)
    name = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h1.group(1)))).strip() if h1 else ""
    role = ""
    m = re.search(r'"jobTitle"\s*:\s*"([^"]{2,120})"', body)
    if m:
        role = html.unescape(m.group(1))
    else:
        og = re.search(r'(?:property|name)="(?:og:title|description|og:description)" content="([^"]{3,200})"', body)
        if og and name and name.split()[-1] in og.group(1):
            rest = re.split(r"[|\-–,]", html.unescape(og.group(1)).replace(name, ""), maxsplit=3)
            role = next((p.strip() for p in rest if 3 < len(p.strip()) < 70), "")
    tels = []
    for m in re.finditer(r'(?is)<a[^>]+href="tel:([^"]+)"[^>]*>(.*?)</a>', body):
        raw = html.unescape(m.group(1)).replace("%20", " ").replace("(0)", "")
        if not re.search(r"\d{6}", re.sub(r"\D", "", raw)):
            continue
        ctx = _text(body[max(0, m.start() - 160):m.start()])[-28:] + " " + m.group(0).split(">", 1)[0]
        try:
            num = phonenumbers.parse(raw if raw.strip().startswith("+") else "+" + re.sub(r"^00", "", raw.strip()), None)
        except phonenumbers.NumberParseException:
            continue
        if not phonenumbers.is_valid_number(num):
            continue
        e164 = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
        label = "mobile" if MOBILE.search(ctx) else ("direct_landline" if DIRECT.search(ctx) else "unknown")
        if e164 not in [t["e164"] for t in tels]:
            tels.append({"raw": raw.strip(), "e164": e164, "region": phonenumbers.region_code_for_number(num), "label": label})
    li = None
    for m in re.finditer(r'href="(https?://[a-z.]*linkedin\.com/in/[^"?#]+)', body):
        li = linkedin.clean(html.unescape(m.group(1)))
        if li:
            break
    main = re.search(r"(?is)<main[^>]*>(.*)</main>", body)
    text = _text(main.group(1) if main else body)
    origin, sentence, years, lived = None, None, 0, 0
    for s in re.split(r"(?<=[.!?])\s+", text):
        if not (25 < len(s) < 420) or not PLACE.search(s) or not WORK.search(s) or NOISE.search(s):
            continue
        if EDU.search(s) and not HARD_WORK.search(s):
            continue
        o = "GB" if re.search(UK, s) else ("IE" if re.search(IE, s) else "NL")
        score = (2 if YEAR.search(s) else 0) + (1 if o == "GB" else 0)
        if sentence is None or score > years * 2 + (1 if origin == "GB" else 0):
            origin, sentence, years, lived = o, s.strip(), 1 if YEAR.search(s) else 0, 1 if LIVED.search(s) else 0
    head = text[:1800]
    city = CITY.search(head)
    return {"name": name, "role": role[:120], "tels": tels, "linkedin": li, "city": city.group(1) if city else None,
            "origin": origin, "sentence": sentence, "has_years": years, "lived": lived, "text_len": len(text)}


def _slug(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1].lower()


def _prefer(urls: list[str]) -> list[str]:
    """One URL per person: prefer an English-locale variant of the same profile."""
    best: dict[str, str] = {}
    for u in sorted(urls):
        s = _slug(u)
        rank = 0 if re.search(r"/(en|en-gb|en-us|en-de|en-fr|global/en)(/|$)", u) else 1
        if s not in best or rank < (0 if re.search(r"/(en|en-gb|en-us|en-de|en-fr|global/en)(/|$)", best[s]) else 1):
            best[s] = u
    return sorted(best.values())


def crawl_host(host: str, limit: int | None = None, delay: float = 2.0) -> None:
    conn = crawl_conn()
    try:
        urls = _prefer(probe_urls(host))
    except Exception as exc:
        with _lock:
            conn.execute("INSERT OR REPLACE INTO hosts VALUES (?,?,?)", (host, "error", str(exc)[:200])); conn.commit()
        return
    done = {r[0] for r in conn.execute("SELECT slug FROM pages WHERE host = ?", (host,))}
    todo = [u for u in urls if _slug(u) not in done][:limit]
    with _lock:
        conn.execute("INSERT OR REPLACE INTO hosts VALUES (?,?,?)", (host, "running", f"{len(todo)} to fetch of {len(urls)}")); conn.commit()
    errors = 0
    for u in todo:
        time.sleep(delay)
        row = {"status": None}
        try:
            req = urllib.request.Request(u.replace("&amp;", "&"), headers={"User-Agent": UA, "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=25) as r:
                body = r.read(3_000_000).decode("utf-8", "replace")
                row = {"status": r.status, **extract(u, body)}
        except urllib.error.HTTPError as exc:
            row = {"status": exc.code}
            if exc.code in (401, 403, 429):
                with _lock:
                    conn.execute("INSERT OR REPLACE INTO hosts VALUES (?,?,?)", (host, "blocked", f"HTTP {exc.code}; stopped, not evaded")); conn.commit()
                return
        except Exception:
            errors += 1
            row = {"status": -1}
            if errors > 25:
                break
        with _lock:
            conn.execute("INSERT OR REPLACE INTO pages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (u, host, _slug(u), row.get("status"), db.now_iso(), row.get("name"), row.get("role"),
                          json.dumps(row.get("tels", [])), row.get("linkedin"), row.get("city"),
                          ",".join(sorted({t["region"] or "" for t in row.get("tels", [])})), row.get("origin"),
                          row.get("sentence"), row.get("has_years", 0), row.get("lived", 0), row.get("text_len", 0)))
            conn.commit()
    with _lock:
        conn.execute("INSERT OR REPLACE INTO hosts VALUES (?,?,?)", (host, "done", f"{len(todo)} fetched")); conn.commit()


def crawl(hosts: list[str], limit: int | None = None) -> None:
    threads = [threading.Thread(target=crawl_host, args=(h, limit), daemon=True) for h in hosts]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


if __name__ == "__main__":
    lim = int(sys.argv[1]) if sys.argv[1].isdigit() else None
    crawl(sys.argv[2:] if lim is not None else sys.argv[1:], lim)


FIRMS = {"www.osborneclarke.com": "Osborne Clarke", "www.wfw.com": "Watson Farley & Williams", "www.withersworldwide.com": "Withers",
         "www.pinsentmasons.com": "Pinsent Masons", "www.hoganlovells.com": "Hogan Lovells", "www.dlapiper.com": "DLA Piper",
         "www.cms.law": "CMS", "www.twobirds.com": "Bird & Bird", "www.gowlingwlg.com": "Gowling WLG",
         "www.hfw.com": "HFW", "dwfgroup.com": "DWF", "www.addleshawgoddard.com": "Addleshaw Goddard", "www.bclplaw.com": "BCLP",
         "www.squirepattonboggs.com": "Squire Patton Boggs", "www.bakermckenzie.com": "Baker McKenzie", "www.lw.com": "Latham & Watkins",
         "www.dechert.com": "Dechert", "www.mayerbrown.com": "Mayer Brown", "www.reedsmith.com": "Reed Smith", "www.klgates.com": "K&L Gates",
         "www.noerr.com": "Noerr", "www.gleisslutz.com": "Gleiss Lutz", "www.luther-lawfirm.com": "Luther", "www.cuatrecasas.com": "Cuatrecasas",
         "www.garrigues.com": "Garrigues", "www.plmj.com": "PLMJ", "www.vda.pt": "VdA", "www.gide.com": "Gide", "www.baerkarrer.ch": "Bär & Karrer",
         "www.homburger.ch": "Homburger", "www.walderwyss.com": "Walder Wyss", "www.nkf.ch": "Niederer Kraft Frey",
         "www.loyensloeff.com": "Loyens & Loeff", "www.goodwinlaw.com": "Goodwin", "www.gtlaw.com": "Greenberg Traurig",
         "www.sidley.com": "Sidley Austin", "www.cov.com": "Covington",
         "www.egonzehnder.com": "Egon Zehnder", "www.russellreynolds.com": "Russell Reynolds Associates", "www.heidrick.com": "Heidrick & Struggles",
         "www.kornferry.com": "Korn Ferry", "www.odgers.com": "Odgers", "www.stantonchase.com": "Stanton Chase", "www.jll.com": "JLL",
         "www.mewburn.com": "Mewburn Ellis", "www.marks-clerk.com": "Marks & Clerk", "www.dyoung.com": "D Young & Co", "www.maiwald.eu": "Maiwald",
         "www.kilburnstrode.com": "Kilburn & Strode", "www.boult.com": "Boult", "www.potterclarkson.com": "Potter Clarkson",
         "www.vossius.eu": "Vossius", "www.grunecker.de": "Grünecker", "www.fticonsulting.com": "FTI Consulting",
         "www.alixpartners.com": "AlixPartners", "www.teneo.com": "Teneo",
         "www.stephensonharwood.com": "Stephenson Harwood", "www.jonesday.com": "Jones Day", "www.clearygottlieb.com": "Cleary Gottlieb",
         "www.weil.com": "Weil", "www.milbank.com": "Milbank", "www.hengeler.com": "Hengeler Mueller", "www.arendt.com": "Arendt",
         "www.stibbe.com": "Stibbe", "www.legance.com": "Legance", "www.ga-p.com": "Gómez-Acebo & Pombo", "www.mlgts.pt": "Morais Leitão",
         "www.jeantet.fr": "Jeantet", "www.pestalozzilaw.com": "Pestalozzi", "www.vischer.com": "VISCHER",
         "www.kellerhals-carrard.ch": "Kellerhals Carrard", "www.mannheimerswartling.se": "Mannheimer Swartling", "www.roschier.com": "Roschier",
         "www.kromannreumert.com": "Kromann Reumert", "www.plesner.com": "Plesner", "www.liedekerke.com": "Liedekerke", "www.goerg.de": "GÖRG",
         "www.oppenhoff.eu": "Oppenhoff", "www.arqis.com": "ARQIS", "www.fgvw.de": "Friedrich Graf von Westphalen",
         "www.murgitroyd.com": "Murgitroyd", "www.withersrogers.com": "Withers & Rogers", "www.reddie.co.uk": "Reddie & Grose",
         "www.hlk-ip.com": "HLK", "www.gje.com": "Gill Jennings & Every", "www.forresters-ip.com": "Forresters",
         "www.appleyardlees.com": "Appleyard Lees", "www.barkerbrettell.co.uk": "Barker Brettell", "www.keltie.com": "Keltie",
         "www.hec.edu": "HEC Paris", "www.unibocconi.it": "Bocconi University", "www.frankfurt-school.de": "Frankfurt School of Finance & Management",
         "www.embl.org": "EMBL"}
SECTOR = {**{h: "executive search firm consultant pages" for h in ("www.egonzehnder.com", "www.russellreynolds.com", "www.heidrick.com",
                                                                    "www.kornferry.com", "www.odgers.com", "www.stantonchase.com")},
          "www.jll.com": "property consultancy broker pages",
          **{h: "patent and trade mark firm people pages" for h in ("www.mewburn.com", "www.marks-clerk.com", "www.dyoung.com", "www.maiwald.eu",
                                                                     "www.kilburnstrode.com", "www.boult.com", "www.potterclarkson.com",
                                                                     "www.vossius.eu", "www.grunecker.de")},
          **{h: "patent and trade mark firm people pages" for h in ("www.murgitroyd.com", "www.withersrogers.com", "www.reddie.co.uk", "www.hlk-ip.com",
                                                                     "www.gje.com", "www.forresters-ip.com", "www.appleyardlees.com",
                                                                     "www.barkerbrettell.co.uk", "www.keltie.com")},
          **{h: "university and research institute staff pages" for h in ("www.hec.edu", "www.unibocconi.it", "www.frankfurt-school.de", "www.embl.org")},
          **{h: "consulting and advisory firm people pages" for h in ("www.fticonsulting.com", "www.alixpartners.com", "www.teneo.com")}}
PRESENT = re.compile(r"\b(is based|currently|is a .{0,40} in (our|the) (London|Dublin|Amsterdam)|based in (London|Dublin|Amsterdam|Bristol|Manchester|Edinburgh|Leeds|Birmingham|Reading|Glasgow))\b", re.IGNORECASE)


def stage(settings: dict, out_dir: Path | None = None) -> dict:
    """Turn crawl results into staging batches (one per firm). Returns counts including why pages were left out."""
    conn = crawl_conn()
    out_dir = out_dir or (db.PIPELINE / "staging")
    eligible = set(settings["eu_mainland_eligible"])
    origin_regions = {"GB", "IE", "NL", "GG", "JE", "IM"}
    seen: dict[str, int] = {}
    rows = conn.execute("SELECT * FROM pages WHERE status = 200 AND name != ''").fetchall()
    for r in rows:
        for t in json.loads(r["tels"] or "[]"):
            seen[t["e164"]] = seen.get(t["e164"], 0) + 1
    stats = {"pages": len(rows), "no_origin_history": 0, "no_phone": 0, "office_not_eligible": 0, "present_tense_origin": 0,
             "shared_number_only": 0, "staged": 0}
    batches: dict[str, list] = {}
    for r in rows:
        tels = json.loads(r["tels"] or "[]")
        if not r["origin"] or not r["sentence"]:
            stats["no_origin_history"] += 1; continue
        if not tels:
            stats["no_phone"] += 1; continue
        regions = {t["region"] for t in tels}
        if regions & origin_regions or not regions <= eligible:
            stats["office_not_eligible"] += 1; continue
        if PRESENT.search(r["sentence"]):
            stats["present_tense_origin"] += 1; continue
        own = [t for t in tels if seen[t["e164"]] == 1]
        chosen = next((t for t in own if t["label"] == "mobile"), own[0] if own else None)
        firm = FIRMS.get(r["host"], r["host"])
        years = YEAR.findall(r["sentence"])
        place = PLACE.search(r["sentence"]).group(1)
        ev = lambda c, lv, ext, lim, **kw: {"criterion": c, "level": lv, "source_url": r["url"], "organisation": firm, "reliability": "PRIMARY",
                                           "publication_date": None, "retrieval_date": r["fetched"][:10], "extract": ext, "limitations": lim, **kw}
        role = (r["role"] or "").strip()
        cand = {
            "first_name": r["name"].split(" ", 1)[0], "last_name": r["name"].split(" ", 1)[1] if " " in r["name"] else "",
            "occupation": (f"{role}, {firm}" if role else f"Professional at {firm} (title not stated on profile)"), "employer": firm,
            "linkedin_url": r["linkedin"], "linkedin_captured_from": r["url"] if r["linkedin"] else None,
            "phone_raw": (chosen or tels[0])["raw"], "phone_type": (chosen["label"] if chosen else "switchboard"),
            "phone_attribution": ("published on the person's own firm profile; not listed on any other profile crawled" if chosen
                                  else "number on the profile is shared with other profiles"),
            "phone_source_url": r["url"],
            "prev_res_country": r["origin"], "prev_res_city": place, "prev_emp_country": r["origin"], "prev_emp_city": place,
            "prev_emp_dates": "-".join(years) if years else None,
            "cur_res_country": (chosen or tels[0])["region"], "cur_res_city": r["city"],
            "external_id": f"firm:{r['host']}:{r['slug']}",
            "evidence": [
                ev("prev_employment", "STRONG" if r["has_years"] else "MODERATE", r["sentence"],
                   "Sentence selected by rule from the firm profile" + ("" if r["has_years"] else "; no dates given")),
                ev("prev_residence", "MODERATE" if r["lived"] else "WEAK", r["sentence"],
                   "Inferred from working in the origin country; employment there does not prove residence"),
                ev("cur_residence", "WEAK", f"Profile lists a {(chosen or tels[0])['region']} office number" + (f"; page mentions {r['city']}" if r["city"] else ""),
                   "Office location only; not evidence of where the person lives"),
                ev("occupation", "STRONG" if role else "MODERATE", role or "Profile on the firm's people directory", "Live employer profile, undated",
                   live_first_party=True),
                ev("phone", "STRONG" if chosen else "WEAK", (chosen or tels[0])["raw"],
                   None if chosen else "Shared number"),
            ],
        }
        if not cand["last_name"]:
            continue
        if not chosen:
            stats["shared_number_only"] += 1
        batches.setdefault(r["host"], []).append(cand)
        stats["staged"] += 1
    for host, cands in batches.items():
        payload = {"batch_id": "FIRM-" + re.sub(r"^www\.", "", host).split(".")[0], "channel": SECTOR.get(host, "law firm people directory"), "source": FIRMS.get(host, host),
                   "country": "multi", "city": "multi", "candidates": cands}
        (out_dir / f"{payload['batch_id']}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return stats
