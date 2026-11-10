"""Evidence assessment, grading (Section 5) and classification (Section 11).

The researcher assigns a level to every evidence item. This module applies the
mechanical safeguards (source reliability, freshness, contradictions), derives
one level per criterion, the overall grade A-D and exactly one final status.
It never upgrades evidence and never invents a level for a missing criterion.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date

STRONG, MODERATE, WEAK, NONE, CONTRADICTED = "STRONG", "MODERATE", "WEAK", "NONE", "CONTRADICTED"
_RANK = {NONE: 0, WEAK: 1, MODERATE: 2, STRONG: 3}
_BY_RANK = {v: k for k, v in _RANK.items()}

CRITERIA = ("prev_residence", "prev_employment", "cur_residence", "occupation", "phone")
CURRENT_CRITERIA = ("cur_residence", "occupation")  # subject to the 12-month freshness rule

RELIABILITIES = ("PRIMARY", "REPUTABLE_SECONDARY", "AGGREGATOR", "UNVERIFIED")

PHONE_TYPES = ("mobile", "direct_work_mobile", "direct_landline", "shared_switchboard", "unknown")


def _cap(level: str, ceiling: str) -> str:
    return level if _RANK[level] <= _RANK[ceiling] else ceiling


def _months_between(earlier: date, later: date) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month) - (1 if later.day < earlier.day else 0)


def parse_date(value: str | None) -> date | None:
    """Parse a publication date at the precision given (YYYY, YYYY-MM or YYYY-MM-DD).

    A year-only or month-only date is placed at the END of its period for the
    freshness test, which is the most favourable reading consistent with the
    source; the stored string itself is never padded.
    """
    if not value:
        return None
    m = re.fullmatch(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", value.strip())
    if not m:
        return None
    y, mo, d = int(m.group(1)), m.group(2), m.group(3)
    if mo is None:
        return date(y, 12, 31)
    if d is None:
        nxt = date(y + (int(mo) == 12), 1 if int(mo) == 12 else int(mo) + 1, 1)
        return date.fromordinal(nxt.toordinal() - 1)
    return date(y, int(mo), int(d))


def effective_item_level(item: dict, as_of: date, corroborated_recently: bool = False,
                         freshness_months: int = 12, weak_cap_months: int = 36) -> str:
    """Apply reliability and freshness caps to one evidence item."""
    level = item.get("level", NONE)
    if level not in _RANK:
        return NONE
    reliability = item.get("reliability", "UNVERIFIED")
    if reliability == "UNVERIFIED":
        return NONE                      # unverified sources cannot support a PASS grade
    if reliability == "AGGREGATOR":
        level = _cap(level, MODERATE)    # an aggregator alone is never STRONG
    live = (item.get("live_first_party") and item.get("criterion") == "occupation" and reliability == "PRIMARY")
    if item.get("criterion") in CURRENT_CRITERIA and not corroborated_recently and not live:
        pub = parse_date(item.get("publication_date"))
        if pub is None:
            level = _cap(level, MODERATE)            # undated: cannot be shown to be current
        else:
            age = _months_between(pub, as_of)
            if age > weak_cap_months:
                level = _cap(level, WEAK)
            elif age > freshness_months:
                level = _BY_RANK[max(_RANK[level] - 1, 1)] if level != NONE else NONE
    return level


def criterion_levels(evidence: list[dict], as_of: date, freshness_months: int = 12,
                     weak_cap_months: int = 36) -> dict[str, str]:
    """Derive one level per criterion from all evidence items."""
    out: dict[str, str] = {}
    for crit in CRITERIA:
        items = [e for e in evidence if e.get("criterion") == crit]
        supporting = [e for e in items if not e.get("contradicts")]
        conflicts = [e for e in items if e.get("contradicts") and not e.get("resolved")
                     and e.get("reliability", "UNVERIFIED") != "UNVERIFIED"]
        if conflicts:
            out[crit] = CONTRADICTED     # never downgraded to WEAK to keep a candidate
            continue
        # a recent, dated item corroborates older items for the same criterion
        recent = False
        for e in supporting:
            pub = parse_date(e.get("publication_date"))
            if pub and _months_between(pub, as_of) <= freshness_months and e.get("reliability") in ("PRIMARY", "REPUTABLE_SECONDARY"):
                recent = True
        best = NONE
        for e in supporting:
            e["effective_level"] = effective_item_level(dict(e, criterion=crit), as_of, recent, freshness_months, weak_cap_months)
            if _RANK[e["effective_level"]] > _RANK[best]:
                best = e["effective_level"]
        out[crit] = best
    return out


def grade(levels: dict[str, str]) -> str | None:
    """Section 5.6, applied in strict order A, B, C, D. Returns None when not gradeable."""
    vals = [levels.get(c, NONE) for c in CRITERIA]
    if any(v in (NONE, CONTRADICTED) or v not in _RANK for v in vals):
        return None
    if levels["phone"] not in (STRONG, MODERATE):
        return None                       # telephone hard gate
    strong = vals.count(STRONG)
    moderate = vals.count(MODERATE)
    below = 5 - strong
    if strong == 5:
        return "A"
    if strong == 4 and moderate == 1:
        return "B"
    if strong >= 3 and below <= 2:
        return "C"
    if strong >= 2 and below <= 3:
        return "D"
    return None


# ---------------------------------------------------------------- occupation

def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


_ADVISER_PATTERNS = [
    r"\bfinancial advis[eo]rs?\b", r"\bifa\b", r"\bindependent financial\b", r"\bwealth managers?\b",
    r"\bwealth advis[eo]rs?\b", r"\bfinancial planners?\b", r"\binvestment advis[eo]rs?\b",
    r"\bchartered financial planner\b", r"\bpension advis[eo]rs?\b",
    # Spanish / Portuguese
    r"\basesora? financier[oa]\b", r"\basesora? de inversion(es)?\b", r"\bgestora? de patrimonios?\b",
    r"\bplanificadora? financier[oa]\b", r"\bconsultora? financeir[oa]\b", r"\bconsultora? de investimentos?\b",
    r"\bgestora? de patrimonios?\b", r"\bplaneadora? financeir[oa]\b",
    # French
    r"\bconseill(er|ere) financi(er|ere)\b", r"\bconseill(er|ere) en gestion de patrimoine\b", r"\bcgp\b",
    r"\bconseill(er|ere) en investissements?( financiers?)?\b", r"\bgestionnaire de patrimoine\b",
    # German
    r"\bfinanzberater(in)?\b", r"\bvermogensberater(in)?\b", r"\banlageberater(in)?\b",
    r"\bvermogensverwalter(in)?\b", r"\bfinanzplaner(in)?\b", r"\bhonorarberater(in)?\b",
    # Dutch / Italian
    r"\bfinancieel advis(eu|o)r\b", r"\bvermogensbeheerder\b", r"\bbeleggingsadviseur\b",
    r"\bconsulente finanziari[oa]\b",
]
_AMBIGUOUS_PATTERNS = [
    r"\bprivate bank(er|ing)\b", r"\brelationship manager\b", r"\binsurance broker\b", r"\bmortgage (broker|advis[eo]r)\b",
    r"\bpensions? consultant\b", r"\btax (advis[eo]r|consultant)\b", r"\baccountant\b", r"\bfund manager\b",
    r"\bportfolio manager\b", r"\btrader\b", r"\bfinancial consultant\b", r"\bfinancial services\b",
    r"\bsteuerberater(in)?\b", r"\bexpert[- ]comptable\b", r"\bcomptable\b", r"\basesora? fiscal\b", r"\bcontable\b",
    r"\bcontabilista\b", r"\bcourtier en (assurances?|credit)\b", r"\bversicherungsmakler(in)?\b",
    r"\bcorredora? de seguros\b", r"\bbankberater(in)?\b", r"\bkundenberater(in)?\b",
]


def screen_occupation(occupation: str | None) -> str:
    """Return 'adviser' (hard reject), 'ambiguous' (ASK), 'clear' or 'missing'."""
    if not occupation or not occupation.strip():
        return "missing"
    text = _fold(occupation)
    if any(re.search(p, text) for p in _ADVISER_PATTERNS):
        return "adviser"
    if any(re.search(p, text) for p in _AMBIGUOUS_PATTERNS):
        return "ambiguous"
    return "clear"


# ----------------------------------------------------------------- geography

def screen_residence(country: str | None, region_or_city: str | None, settings: dict) -> tuple[str, str]:
    """Return (decision, reason) with decision in eligible | ask | reject | missing."""
    if not country:
        return "missing", "current residence country not established"
    c = country.upper()
    place = _fold(region_or_city or "")
    if c in settings["residence_reject_countries"]:
        return "reject", f"current residence in {c} (UK/Republic of Ireland)"
    if c in settings["residence_ask_countries"]:
        return "ask", f"current residence in {c} is a geographical exception"
    if place and any(re.search(rf"\b{re.escape(_fold(r))}\b", place) for r in settings["residence_ask_regions"]):
        return "ask", f"current residence appears to be an island exception ({region_or_city})"
    if c in settings["eu_mainland_eligible"]:
        return "eligible", ""
    if c in settings["other_european_ask_countries"]:
        return "ask", f"current residence in {c}: European but outside mainland EU/Switzerland"
    return "reject", f"current residence in {c} is outside Europe"


# ------------------------------------------------------------ classification

def classify(cand: dict, levels: dict[str, str], settings: dict, duplicate_of: str | None = None,
             duplicate_criterion: str | None = None) -> dict:
    """Assign exactly one status in the order DUPLICATE -> REJECT -> ASK -> PASS."""
    result = {"status": None, "grade": None, "reason": "", "reserve": 0, "countable": False}
    origin = set(settings["origin_countries"])

    if duplicate_of:
        result.update(status="DUPLICATE", reason=f"duplicate of {duplicate_of} ({duplicate_criterion})")
        return result

    # ---- REJECT: clear disqualifiers only
    rejects: list[str] = []
    res_decision, res_reason = screen_residence(cand.get("cur_res_country"),
                                                " ".join(filter(None, [cand.get("cur_res_region"), cand.get("cur_res_city")])),
                                                settings)
    if res_decision == "reject":
        rejects.append(res_reason)
    occ = screen_occupation(cand.get("occupation"))
    if occ == "adviser":
        rejects.append("current occupation is financial adviser or equivalent")
    if cand.get("study_only"):
        rejects.append("only link to an origin country is study; no qualifying employment")
    if cand.get("no_qualifying_employment"):
        rejects.append("reliable evidence of no qualifying previous employment")
    if cand.get("phone_valid") is False:
        rejects.append("NO NUMBER YET (the published number failed validation)")
    elif not cand.get("phone_e164") or levels.get("phone", NONE) == NONE:
        rejects.append("NO NUMBER YET")
    if rejects:
        result.update(status="REJECT", reason="; ".join(rejects))
        return result

    # ---- ASK: absent, ambiguous, contradictory or exceptional material facts
    asks: list[str] = []
    if cand.get("suppressed") or cand.get("do_not_contact") == "yes":
        asks.append("SUPPRESSED: person asked not to be contacted; not an actionable prospect")
    if res_decision in ("ask", "missing"):
        asks.append(res_reason)
    if occ == "ambiguous":
        asks.append("financially related occupation; exact function not established")
    if occ == "missing":
        asks.append("current occupation not established")
    pr, pe = cand.get("prev_res_country"), cand.get("prev_emp_country")
    if pr and pe and pr.upper() in origin and pe.upper() in origin and pr.upper() != pe.upper():
        asks.append(f"split-country origin: lived in {pr}, worked in {pe}")
    if pr and pr.upper() not in origin:
        asks.append(f"previous residence country {pr} is not a qualifying origin country")
    if pe and pe.upper() not in origin:
        asks.append(f"previous employment country {pe} is not a qualifying origin country")
    for crit in CRITERIA:
        lv = levels.get(crit, NONE)
        if lv == CONTRADICTED:
            asks.append(f"unresolved contradiction on {crit}")
        elif lv == NONE:
            asks.append(f"no usable evidence for {crit}")
    if levels.get("phone") == WEAK or cand.get("phone_type") == "shared_switchboard":
        asks.append("telephone attribution below MODERATE (organisation-level or shared number)")
    if not cand.get("phone_valid", True):
        asks.append("telephone number failed validation")
    g = grade(levels)
    if g is None and not asks:
        asks.append("more than three criteria below STRONG")
    if not cand.get("linkedin_url"):
        asks.append("INCOMPLETE RESERVE: no LinkedIn profile URL found")
        result["reserve"] = 1
    if asks:
        result.update(status="ASK", reason="; ".join(a for a in asks if a))
        if len(asks) == 1 and result["reserve"]:
            result["grade"] = g              # valid on every other test; waiting only for a profile URL
        return result

    result.update(status="PASS", grade=g, reason=f"PASS grade {g}", countable=True)
    return result
