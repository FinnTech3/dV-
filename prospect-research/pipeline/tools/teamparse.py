"""Segment a multi-person team page into per-person blocks.

Most small firms put the whole team on one page. This splits such a page at the headings that look like personal
names and runs the normal extractor on each block. A telephone number is accepted for a person only when it sits
inside that person's own block AND appears nowhere else on the page (a number repeated in the header, footer or other
blocks is the firm's, not theirs). Nothing is guessed: no block, no person.
"""
from __future__ import annotations

import html as _html
import re

from . import firmcrawl

_HEAD = re.compile(r"(?is)<h([1-6])[^>]*>(.*?)</h\1>")
_PARTICLES = {"de", "van", "von", "der", "den", "del", "della", "di", "da", "dos", "das", "du", "la", "le", "el", "al", "bin", "ten", "ter", "mc", "mac"}
_STOP = re.compile(r"^(our|the|meet|about|contact|team|staff|people|services?|home|news|blog|welcome|who|we|what|why|how|join|careers?|jobs?|"
                   r"partners?|clients?|testimonials?|follow|get|call|email|office|offices|location|locations|opening|hours|faq|privacy|terms|"
                   r"cookie|menu|search|login|register|book|booking|read|more|see|view|all|latest|recent|related|share|subscribe|newsletter|"
                   r"nuestro|nuestra|equipo|notre|équipe|equipe|unser|über|ueber|kontakt|wir|nosotros|sobre|contacto|ons|over)$", re.I)


_ROLE = re.compile(r"\b(manager|director|founder|co-?founder|owner|partner|consultant|lawyer|attorney|associate|assistant|engineer|agent|advis[eo]r|head|ceo|cto|cfo|coo|chair|"
                   r"president|chaplain|coach|teacher|secretary|treasurer|administrator|coordinator|specialist|expert|officer|analyst|architect|designer|developer|dentist|"
                   r"doctor|physician|therapist|principal|senior|junior|sales|marketing|gesch(ä|ae)ftsf(ü|ue)hrer|inhaber|gr(ü|u)nder|leiter|berater|anwalt|rechtsanwalt|"
                   r"directeur|g(é|e)rant|fondateur|associ(é|e)|avocat|conseill(er|ère)|gerente|socio|abogado|fundador|consultor|diretor|sócio|advogado|"
                   r"dr\.?|prof\.?|solicitor|barrister|translator|notary|agent|broker|manageress|proprietor|host|instructor)\b", re.I)


def split_name_role(text: str) -> str | None:
    """'Sharon Richards Company Founder and Owner Manager' -> 'Sharon Richards'; returns None if no clean name leads the text."""
    t = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", text))).strip(" :-–|,.")
    words = t.split()
    if not 4 <= len(words) <= 12 or len(t) > 110 or not _ROLE.search(t):
        return None
    for k in (3, 2):
        lead = " ".join(words[:k])
        if looks_like_name(lead) and _ROLE.search(" ".join(words[k:])):
            return lead
    return None


def looks_like_name(text: str) -> bool:
    t = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", text))).strip(" :-–|,.")
    t = re.sub(r"^(dr|prof|mr|mrs|ms|mag|dipl|ing|rev|revd|fr|sir|dame)\.?\s+", "", t, flags=re.I)
    words = t.split()
    if not 2 <= len(words) <= 4 or len(t) > 42 or re.search(r"\d|@|/|&", t):
        return False
    if _STOP.match(words[0]) or any(_STOP.match(w) and w.lower() not in _PARTICLES for w in words[:2]):
        return False
    caps = [w for w in words if w[0].isupper() or w.lower() in _PARTICLES]
    return len(caps) == len(words) and sum(1 for w in words if w[0].isupper()) >= 2


def blocks(page_html: str) -> list[dict]:
    body = re.sub(r"(?is)<(script|style|noscript|template|svg|nav)[^>]*>.*?</\1>", " ", page_html)
    heads = [(m.start(), m.end(), int(m.group(1)), m.group(2)) for m in _HEAD.finditer(body)]
    out = []
    heads = [(s_, e_, l_, (split_name_role(i_) or i_)) for s_, e_, l_, i_ in heads]
    for i, (s, e, lvl, inner) in enumerate(heads):
        if not looks_like_name(inner):
            continue
        end = len(body)
        for s2, _e2, lvl2, inner2 in heads[i + 1:]:
            if lvl2 <= lvl or looks_like_name(inner2):
                end = s2
                break
        chunk = body[e:min(end, e + 6000)]
        name = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", inner))).strip(" :-–|,.")
        if len(re.sub(r"<[^>]+>", " ", chunk).strip()) >= 40:
            out.append({"name": name, "html": chunk})
    return out


def extract_team(url: str, page_html: str) -> list[dict]:
    """Return one record per person-block, with the page-level 'shared number' test applied."""
    page_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page_html))
    digits_page = re.sub(r"\D", "", page_text)
    res = []
    for b in blocks(page_html):
        r = firmcrawl.extract(url, f"<main><h1>{b['name']}</h1>{b['html']}</main>")
        own = []
        for t in r["tels"]:
            tail = re.sub(r"\D", "", t["e164"])[-9:]
            if digits_page.count(tail) + len(re.findall(re.escape(tail), re.sub(r"\D", "", _html.unescape(page_html)))) // 2 <= 2:
                own.append(t)                      # appears once in the text and once in its tel: link at most
        r["tels"] = own
        r["name"] = b["name"]
        res.append(r)
    return res
