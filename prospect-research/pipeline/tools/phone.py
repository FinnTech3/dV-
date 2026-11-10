"""Telephone parsing and E.164 normalisation.

The numbering library is used ONLY to parse, validate and format. It is never
used to decide who owns a number or whether it is a mobile: the type recorded
is the type the public source itself states (see `declared_type`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import phonenumbers

from .verify import MODERATE, NONE, PHONE_TYPES, STRONG, WEAK


@dataclass
class ParsedPhone:
    raw: str
    e164: str | None
    valid: bool
    region: str | None
    error: str | None = None


def normalise(raw: str | None, region_hint: str | None = None) -> ParsedPhone:
    if not raw or not raw.strip():
        return ParsedPhone(raw or "", None, False, None, "empty")
    text = raw.strip()
    lead = re.match(r"^\(?\s*00\s*(\d{1,3})\s*\)?", text)
    if lead:
        text = "+" + lead.group(1) + text[lead.end():]   # international access prefix written as 00 or (00xx)
    try:
        num = phonenumbers.parse(text, region_hint)
    except phonenumbers.NumberParseException as exc:
        return ParsedPhone(raw, None, False, None, str(exc))
    if not phonenumbers.is_valid_number(num):
        return ParsedPhone(raw, None, False, phonenumbers.region_code_for_number(num), "not a valid number")
    return ParsedPhone(raw, phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164), True,
                       phonenumbers.region_code_for_number(num))


def declared_type(source_label: str | None) -> str:
    """Map the label the SOURCE gives the number to a stored type. No prefix guessing."""
    label = (source_label or "").strip().lower()
    if label in PHONE_TYPES:
        return label
    table = {
        "mobile": ("mobile", "mob", "cell", "móvil", "movil", "portable", "handy", "mobil", "telemóvel", "telemovel", "natel"),
        "direct_work_mobile": ("work mobile", "direct mobile", "business mobile"),
        "direct_landline": ("direct", "direct line", "ddi", "durchwahl", "ligne directe", "línea directa", "linea directa", "tel", "office direct"),
        "shared_switchboard": ("switchboard", "reception", "main", "office", "zentrale", "standard", "centralita", "general", "contact us"),
    }
    for kind in ("direct_work_mobile", "mobile", "direct_landline", "shared_switchboard"):
        if label in table[kind]:
            return kind
    return "unknown"


def phone_evidence_ceiling(phone_type: str, published_for_individual: bool, named_listing: bool) -> str:
    """Highest telephone evidence level the publication context can support (Section 5.5)."""
    if phone_type == "shared_switchboard":
        return WEAK
    if published_for_individual:
        return STRONG
    if named_listing:
        return MODERATE
    return WEAK if phone_type != "unknown" or named_listing else NONE


def crm_hold_reason(phone_type: str | None, grade: str | None, settings: dict) -> str | None:
    """Reason a countable record is held out of the 'Mobile Number' CRM column, else None."""
    exp = settings["export"]
    if grade not in exp["grades_allowed"]:
        return f"grade {grade} is not exported to the CRM sheet (review export only)"
    if phone_type not in exp["phone_types_allowed"]:
        return f"phone type '{phone_type}' is not a confirmed mobile; held until the trainer's acceptance rule is known"
    return None
