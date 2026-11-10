"""Deduplication (Section 10): exact LinkedIn URL, exact individual phone, exact name + employer.

Fuzzy name similarity only FLAGS a possible duplicate; nothing is merged automatically.
Shared business numbers never prove two people are the same person.
"""
from __future__ import annotations

import re
import sqlite3
import unicodedata
from difflib import SequenceMatcher

from . import linkedin

INDIVIDUAL_PHONE_TYPES = ("mobile", "direct_work_mobile", "direct_landline")


def norm_text(value: str | None) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    value = value.replace(".", "").replace("'", "")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", value)).strip()


def name_key(first: str | None, last: str | None) -> str:
    return f"{norm_text(first)}|{norm_text(last)}"


def find_duplicate(conn: sqlite3.Connection, cand: dict, exclude_uuid: str | None = None) -> tuple[str | None, str | None]:
    """Return (original_uuid, criterion) for a defined duplicate, else (None, None)."""
    excl = exclude_uuid or ""
    base = "SELECT uuid FROM persons WHERE status != 'DUPLICATE' AND uuid != ? AND "
    url = linkedin.clean(cand.get("linkedin_url"))
    if url:
        row = conn.execute(base + "linkedin_url = ? ORDER BY date_found, rowid LIMIT 1", (excl, url)).fetchone()
        if row:
            return row["uuid"], "exact LinkedIn URL"
    phone = cand.get("phone_e164")
    if phone and cand.get("phone_type") in INDIVIDUAL_PHONE_TYPES:
        row = conn.execute(
            base + "phone_e164 = ? AND phone_type IN ('mobile','direct_work_mobile','direct_landline') "
                   "ORDER BY date_found, rowid LIMIT 1", (excl, phone)).fetchone()
        if row:
            return row["uuid"], "exact individual phone number"
    if cand.get("employer"):
        for row in conn.execute(base + "employer IS NOT NULL ORDER BY date_found, rowid", (excl,)).fetchall():
            other = conn.execute("SELECT first_name, last_name, employer FROM persons WHERE uuid = ?", (row["uuid"],)).fetchone()
            if (name_key(other["first_name"], other["last_name"]) == name_key(cand.get("first_name"), cand.get("last_name"))
                    and norm_text(other["employer"]) == norm_text(cand.get("employer"))):
                return row["uuid"], "exact first name, last name and employer"
    return None, None


def shared_number_collisions(conn: sqlite3.Connection, cand: dict, exclude_uuid: str | None = None) -> list[str]:
    """Other people listed against the same shared/unknown number: flagged, never merged."""
    phone = cand.get("phone_e164")
    if not phone:
        return []
    rows = conn.execute("SELECT uuid FROM persons WHERE phone_e164 = ? AND uuid != ?", (phone, exclude_uuid or "")).fetchall()
    return [r["uuid"] for r in rows]


def possible_duplicates(conn: sqlite3.Connection, cand: dict, threshold: float = 0.88,
                        exclude_uuid: str | None = None) -> list[tuple[str, float]]:
    """Fuzzy name matches for human review only."""
    target = name_key(cand.get("first_name"), cand.get("last_name"))
    out = []
    for row in conn.execute("SELECT uuid, first_name, last_name FROM persons WHERE uuid != ?", (exclude_uuid or "",)):
        other = name_key(row["first_name"], row["last_name"])
        if other == target:
            out.append((row["uuid"], 1.0))
            continue
        ratio = SequenceMatcher(None, target, other).ratio()
        if ratio >= threshold:
            out.append((row["uuid"], round(ratio, 3)))
    return out


def spreadsheet_duplicate(cand: dict, sheet_rows: list[dict]) -> int | None:
    """Match against rows already in the supplied workbook. Returns the sheet row number or None."""
    url = linkedin.clean(cand.get("linkedin_url"))
    for r in sheet_rows:
        if url and linkedin.clean(r.get("linkedin")) == url:
            return r["row"]
        if cand.get("phone_e164") and re.sub(r"[^\d+]", "", r.get("phone") or "") == cand["phone_e164"]:
            return r["row"]
    return None
