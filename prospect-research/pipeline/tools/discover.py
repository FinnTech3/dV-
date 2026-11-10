"""Candidate ingest: validate staged candidates, deduplicate, grade, classify and save.

Research agents write candidate batches to `pipeline/staging/*.json`. Only this
module (run by the main agent) writes to the master database. Real person
records are refused unless the compliance gate is open; synthetic test records
are allowed into a test database only.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

from . import db, dedupe, gate, linkedin, phone, verify
from .fetch import flag_injection

REQUIRED = ("first_name", "last_name")


def validate(cand: dict) -> list[str]:
    errors = [f"missing {f}" for f in REQUIRED if not str(cand.get(f, "")).strip()]
    for ev in cand.get("evidence", []):
        if not ev.get("source_url"):
            errors.append("evidence item without source_url")
        if ev.get("criterion") not in verify.CRITERIA + ("linkedin",):
            errors.append(f"unknown criterion {ev.get('criterion')!r}")
        if ev.get("reliability") not in verify.RELIABILITIES:
            errors.append(f"unknown reliability {ev.get('reliability')!r}")
    return errors


def _quarantine(text: str | None) -> str | None:
    """Notes/extracts are data. Instruction-like text is replaced by a marker, never obeyed."""
    if text and flag_injection(text):
        return "[extract withheld: source text contained instruction-like content]"
    return text


def ingest_candidate(conn: sqlite3.Connection, cand: dict, settings: dict, as_of: date | None = None,
                     batch_id: str | None = None, synthetic: bool = False, gate_path: Path | None = None) -> dict:
    """Insert one candidate. Returns {'uuid', 'status', 'grade', 'reason', 'new'}."""
    if not synthetic:
        gate.require_open(gate_path)
    errors = validate(cand)
    if errors:
        raise ValueError("; ".join(errors))
    as_of = as_of or date.today()
    c = dict(cand)

    c["linkedin_url"] = linkedin.clean(c.get("linkedin_url"))
    if c["linkedin_url"] and linkedin.built_from_name(c["linkedin_url"], c["first_name"], c["last_name"], c.get("linkedin_captured_from")):
        c["linkedin_url"] = None                       # no capture source recorded: treat as unverified, do not store
    parsed = phone.normalise(c.get("phone_raw"), c.get("phone_region_hint"))
    c["phone_e164"] = parsed.e164
    c["phone_valid"] = parsed.valid or not c.get("phone_raw")
    c["phone_type"] = phone.declared_type(c.get("phone_type")) if c.get("phone_raw") else None

    evidence = [dict(e) for e in c.get("evidence", [])]
    levels = verify.criterion_levels(evidence, as_of, settings["freshness_months"], settings["stale_weak_cap_months"])
    if not parsed.valid:
        levels["phone"] = verify.NONE if not c.get("phone_raw") else levels["phone"]
    if c.get("phone_type") == "shared_switchboard" and levels["phone"] in (verify.STRONG, verify.MODERATE):
        levels["phone"] = verify.WEAK                 # a switchboard is never individually attributable

    # idempotent re-run: the same staged candidate (same external_id) is not inserted twice
    ext = c.get("external_id")
    if ext:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (f"ext:{ext}",)).fetchone()
        if row:
            p = conn.execute("SELECT uuid, status, grade, status_reason FROM persons WHERE uuid = ?", (row["value"],)).fetchone()
            return {"uuid": p["uuid"], "status": p["status"], "grade": p["grade"], "reason": p["status_reason"], "new": False}

    dup_uuid, dup_crit = dedupe.find_duplicate(conn, c)
    result = verify.classify(c, levels, settings, dup_uuid, dup_crit)
    fuzzy = [] if dup_uuid else dedupe.possible_duplicates(conn, c, settings["fuzzy_name_threshold"])
    collisions = dedupe.shared_number_collisions(conn, c) if c.get("phone_type") in ("shared_switchboard", "unknown") else []

    hold = phone.crm_hold_reason(c.get("phone_type"), result["grade"], settings) if result["grade"] else None
    notes = [n for n in [_quarantine(c.get("notes"))] if n]
    if collisions:
        notes.append(f"shared number also listed for {len(collisions)} other record(s); not treated as the same person")

    uid = db.new_uuid()
    today = as_of.isoformat()
    conn.execute(
        """INSERT INTO persons (uuid, first_name, last_name, occupation, employer, linkedin_url, email,
            phone_raw, phone_e164, phone_type, phone_attribution, phone_source_url,
            prev_res_country, prev_res_city, prev_res_period, prev_res_level,
            prev_emp_country, prev_emp_employer, prev_emp_city, prev_emp_role, prev_emp_dates, prev_emp_level,
            cur_res_country, cur_res_city, cur_res_region, cur_res_since, cur_res_level,
            occupation_level, phone_level, grade, status, status_reason, reserve, crm_export_hold,
            possible_duplicate_of, duplicate_of, duplicate_criterion, date_found, date_last_checked,
            research_channel, contact_route, contact_objection, do_not_contact, suppressed, suppression_date,
            notes, batch_id, synthetic)
           VALUES (?,?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?, ?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?,?,?,?, ?,?,?,?,?, ?,?,?,?,?,?, ?,?,?)""",
        (uid, c["first_name"].strip(), c["last_name"].strip(), c.get("occupation"), c.get("employer"), c["linkedin_url"], c.get("email"),
         c.get("phone_raw"), c["phone_e164"], c.get("phone_type"), c.get("phone_attribution"), c.get("phone_source_url"),
         c.get("prev_res_country"), c.get("prev_res_city"), c.get("prev_res_period"), levels["prev_residence"],
         c.get("prev_emp_country"), c.get("prev_emp_employer"), c.get("prev_emp_city"), c.get("prev_emp_role"),
         c.get("prev_emp_dates"), levels["prev_employment"],
         c.get("cur_res_country"), c.get("cur_res_city"), c.get("cur_res_region"), c.get("cur_res_since"), levels["cur_residence"],
         levels["occupation"], levels["phone"], result["grade"], result["status"], result["reason"], result["reserve"], hold,
         ",".join(u for u, _ in fuzzy) or None, dup_uuid, dup_crit, today, today,
         c.get("channel"), c.get("contact_route") or "cold", c.get("contact_objection") or "unknown",
         c.get("do_not_contact") or "unknown", 1 if (c.get("suppressed") or c.get("do_not_contact") == "yes") else 0,
         today if (c.get("suppressed") or c.get("do_not_contact") == "yes") else None,
         " | ".join(notes) or None, batch_id, 1 if synthetic else 0))
    for ev in evidence:
        conn.execute(
            """INSERT INTO evidence (person_uuid, criterion, field, source_url, organisation, reliability, publication_date,
                   retrieval_date, extract, level, effective_level, contradicts, resolved, limitations)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (uid, ev["criterion"], ev.get("field"), ev["source_url"], ev.get("organisation"), ev["reliability"],
             ev.get("publication_date"), ev.get("retrieval_date") or today, _quarantine(ev.get("extract")),
             ev.get("level", verify.NONE), ev.get("effective_level"), 1 if ev.get("contradicts") else 0,
             1 if ev.get("resolved") else 0, ev.get("limitations")))
    if ext:
        conn.execute("INSERT INTO meta (key, value) VALUES (?, ?)", (f"ext:{ext}", uid))
    conn.commit()
    return {"uuid": uid, "status": result["status"], "grade": result["grade"], "reason": result["reason"], "new": True}


def ingest_batch(conn: sqlite3.Connection, staging_file: Path, settings: dict, synthetic: bool = False,
                 as_of: date | None = None, gate_path: Path | None = None) -> dict:
    """Ingest a staged JSON batch ({'batch_id', 'channel', 'candidates': [...]}) and log a ledger row."""
    payload = json.loads(Path(staging_file).read_text(encoding="utf-8"))
    batch_id = payload.get("batch_id") or Path(staging_file).stem
    counts = {"new": 0, "skipped": 0, "invalid": 0, "PASS": 0, "ASK": 0, "REJECT": 0, "DUPLICATE": 0, "grades": {}}
    for cand in payload.get("candidates", []):
        cand.setdefault("external_id", f"{batch_id}:{cand.get('first_name')}:{cand.get('last_name')}:{cand.get('employer')}")
        cand.setdefault("channel", payload.get("channel"))
        try:
            res = ingest_candidate(conn, cand, settings, as_of, batch_id, synthetic, gate_path)
        except ValueError:
            counts["invalid"] += 1
            continue
        if not res["new"]:
            counts["skipped"] += 1
            continue
        counts["new"] += 1
        counts[res["status"]] += 1
        if res["grade"]:
            counts["grades"][res["grade"]] = counts["grades"].get(res["grade"], 0) + 1
    db.log(conn, mode="HARVEST", source=payload.get("source"), country=payload.get("country"), city=payload.get("city"),
           discovered=counts["new"], reviewed=counts["new"], grades=json.dumps(counts["grades"]),
           duplicates=counts["DUPLICATE"], ask=counts["ASK"], reject=counts["REJECT"], note=f"batch {batch_id}")
    return counts


def set_linkedin(conn: sqlite3.Connection, person_uuid: str, url: str, captured_from: str, settings: dict) -> str:
    """Attach a profile URL supplied later; a reserve record that lacked only the URL becomes PASS."""
    clean = linkedin.clean(url)
    if not clean:
        raise ValueError("not a personal LinkedIn profile URL")
    dup = conn.execute("SELECT uuid FROM persons WHERE linkedin_url = ? AND uuid != ?", (clean, person_uuid)).fetchone()
    if dup:
        conn.execute("UPDATE persons SET status='DUPLICATE', grade=NULL, duplicate_of=?, duplicate_criterion='exact LinkedIn URL' WHERE uuid=?",
                     (dup["uuid"], person_uuid))
        conn.commit()
        return "DUPLICATE"
    row = conn.execute("SELECT status, grade, reserve, status_reason FROM persons WHERE uuid = ?", (person_uuid,)).fetchone()
    only_missing = row["reserve"] and row["grade"] and row["status_reason"].startswith("INCOMPLETE RESERVE")
    conn.execute("UPDATE persons SET linkedin_url = ?, notes = COALESCE(notes || ' | ', '') || ? WHERE uuid = ?",
                 (clean, f"LinkedIn URL captured from: {captured_from}", person_uuid))
    if only_missing:
        conn.execute("UPDATE persons SET status='PASS', reserve=0, status_reason=? WHERE uuid=?", (f"PASS grade {row['grade']}", person_uuid))
    conn.commit()
    return "PASS" if only_missing else row["status"]


def suppress(conn: sqlite3.Connection, person_uuid: str, basis: str = "individual asked not to be contacted") -> None:
    """Mark a person as not to be contacted: removed from the countable pool and from every export."""
    conn.execute("""UPDATE persons SET suppressed = 1, do_not_contact = 'yes', contact_objection = 'yes',
                    suppression_date = ?, suppression_basis = ?, status = CASE WHEN status = 'PASS' THEN 'ASK' ELSE status END,
                    grade = CASE WHEN status = 'PASS' THEN NULL ELSE grade END,
                    status_reason = 'SUPPRESSED: person asked not to be contacted' WHERE uuid = ?""",
                 (db.now_iso(), basis, person_uuid))
    conn.commit()


def reclassify_all(conn: sqlite3.Connection, settings: dict) -> int:
    """Second deduplication pass before export: later records matching an earlier one become DUPLICATE."""
    changed = 0
    rows = conn.execute("SELECT * FROM persons WHERE status != 'DUPLICATE' ORDER BY date_found, rowid").fetchall()
    for row in rows:
        cand = dict(row)
        orig, crit = dedupe.find_duplicate(conn, cand, exclude_uuid=row["uuid"])
        if orig:
            first = conn.execute("SELECT rowid FROM persons WHERE uuid = ?", (orig,)).fetchone()[0]
            mine = conn.execute("SELECT rowid FROM persons WHERE uuid = ?", (row["uuid"],)).fetchone()[0]
            if first < mine:
                conn.execute("UPDATE persons SET status='DUPLICATE', grade=NULL, duplicate_of=?, duplicate_criterion=?, status_reason=? WHERE uuid=?",
                             (orig, crit, f"duplicate of {orig} ({crit})", row["uuid"]))
                changed += 1
    conn.commit()
    return changed
