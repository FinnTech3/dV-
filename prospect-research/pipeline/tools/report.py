"""Counts, evidence-quality, phone and source-performance reporting (Section 17)."""
from __future__ import annotations

import sqlite3

GRADE_MEANING = {
    "A": "highly supported - all five criteria STRONG",
    "B": "well supported - four STRONG, one MODERATE",
    "C": "plausible - at least three STRONG, up to two MODERATE/WEAK",
    "D": "exploratory but usable - at least two STRONG, up to three MODERATE/WEAK; NOT fully verified",
}
PHONE_LABEL = {"mobile": "confirmed mobile", "direct_work_mobile": "direct work/mobile", "direct_landline": "direct landline",
               "shared_switchboard": "shared organisation number", "unknown": "unknown"}


def summary(conn: sqlite3.Connection, settings: dict) -> dict:
    real = "synthetic = 0"
    total = conn.execute(f"SELECT COUNT(*) FROM persons WHERE {real}").fetchone()[0]
    status = {s: 0 for s in ("PASS", "ASK", "REJECT", "DUPLICATE")}
    for r in conn.execute(f"SELECT status, COUNT(*) n FROM persons WHERE {real} GROUP BY status"):
        status[r["status"]] = r["n"]
    grades = {g: 0 for g in "ABCD"}
    for r in conn.execute(f"SELECT grade, COUNT(*) n FROM persons WHERE {real} AND status='PASS' AND suppressed=0 GROUP BY grade"):
        grades[r["grade"]] = r["n"]
    countable = sum(grades.values())
    phones = {k: 0 for k in PHONE_LABEL}
    for r in conn.execute(f"SELECT COALESCE(phone_type,'unknown') t, COUNT(*) n FROM persons WHERE {real} AND status='PASS' AND suppressed=0 GROUP BY t"):
        phones[r["t"]] = phones.get(r["t"], 0) + r["n"]
    return {
        "discovered": total, "reviewed": total, "status": status, "grades": grades, "countable": countable,
        "a_plus_b": grades["A"] + grades["B"],
        "reserve": conn.execute(f"SELECT COUNT(*) FROM persons WHERE {real} AND reserve=1").fetchone()[0],
        "suppressed": conn.execute(f"SELECT COUNT(*) FROM persons WHERE {real} AND suppressed=1").fetchone()[0],
        "pending_linkedin": {r["grade"]: r["n"] for r in conn.execute(
            f"SELECT grade, COUNT(*) n FROM persons WHERE {real} AND status='ASK' AND reserve=1 AND grade IS NOT NULL AND suppressed=0 GROUP BY grade")},
        "remaining": max(settings["target_countable"] - countable, 0),
        "target": settings["target_countable"], "phones": phones,
    }


def channel_performance(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """SELECT COALESCE(research_channel,'(unrecorded)') channel, COALESCE(cur_res_country,'?') country,
                  COUNT(*) reviewed,
                  SUM(status='PASS' AND grade='A') a, SUM(status='PASS' AND grade='B') b,
                  SUM(status='PASS' AND grade='C') c, SUM(status='PASS' AND grade='D') d,
                  SUM(status='ASK') ask, SUM(status='REJECT') reject, SUM(status='DUPLICATE') dup,
                  SUM(phone_level IN ('STRONG','MODERATE')) phone_ok
           FROM persons WHERE synthetic = 0 GROUP BY channel, country
           ORDER BY (a + b) DESC, (a + b + c + d) DESC""").fetchall()
    return [dict(r) for r in rows]


def _table(headers: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    out += ["| " + " | ".join("" if v is None else str(v).replace("|", "/") for v in r) + " |" for r in rows]
    return "\n".join(out)


def render_markdown(conn: sqlite3.Connection, settings: dict, export_report: dict | None = None) -> str:
    s = summary(conn, settings)
    g = s["grades"]
    pct = lambda n: f"{(100 * n / s['countable']):.1f}%" if s["countable"] else "n/a"
    real = "synthetic = 0"
    parts = ["# Prospect research report", "",
             "The countable total is a pool of **evidence-graded prospects**, not fully verified people. "
             "Grade D in particular is exploratory.", "",
             "## 1. Overall counts",
             _table(["Measure", "Count"], [
                 ["Total candidates discovered", s["discovered"]], ["Total reviewed", s["reviewed"]],
                 ["PASS Grade A", g["A"]], ["PASS Grade B", g["B"]], ["PASS Grade C", g["C"]], ["PASS Grade D", g["D"]],
                 ["Total countable PASS", s["countable"]], ["ASK", s["status"]["ASK"]],
                 ["  of which incomplete reserve (no LinkedIn URL)", s["reserve"]],
                 ["  of which valid on every other test, waiting only for a LinkedIn URL", sum(s["pending_linkedin"].values())],
                 ["    by grade", ", ".join(f"{k}: {v}" for k, v in sorted(s["pending_linkedin"].items())) or "-"],
                 ["  of which suppressed (asked not to be contacted)", s["suppressed"]],
                 ["REJECT", s["status"]["REJECT"]], ["DUPLICATE", s["status"]["DUPLICATE"]],
                 [f"Remaining to {s['target']}", s["remaining"]]]), "",
             "## 2. Evidence quality",
             _table(["Grade", "Count", "Share of countable", "Meaning"],
                    [[k, g[k], pct(g[k]), GRADE_MEANING[k]] for k in "ABCD"]),
             f"\nA+B subtotal (strongest support): **{s['a_plus_b']}** ({pct(s['a_plus_b'])}).", ""]

    crm = conn.execute(f"""SELECT first_name, last_name, occupation, phone_e164, email, linkedin_url FROM persons
                           WHERE {real} AND status='PASS' AND suppressed=0 AND crm_export_hold IS NULL
                           ORDER BY date_found, rowid""").fetchall()
    parts += ["## 3. PASS table (rows suitable for the CRM template)",
              _table(["First name", "Last Name", "Occupation", "Mobile Number", "Email", "Linkedin profile link"],
                     [list(r) for r in crm]) if crm else "_No rows._", ""]

    ask = conn.execute(f"SELECT rowid, first_name, last_name, status_reason FROM persons WHERE {real} AND status='ASK' ORDER BY rowid").fetchall()
    parts += ["## 4. ASK table",
              _table(["Record", "Name", "Missing or uncertain area", "Evidence already found", "What would resolve it"],
                     [[r["rowid"], f"{r['first_name']} {r['last_name']}", r["status_reason"], _evidence_summary(conn, r["rowid"]),
                       _resolution(r["status_reason"])] for r in ask]) if ask else "_No rows._", ""]

    rej = conn.execute(f"SELECT rowid, first_name, last_name, status_reason FROM persons WHERE {real} AND status='REJECT' ORDER BY rowid").fetchall()
    parts += ["## 5. REJECT table",
              _table(["Record", "Name", "Reason"], [[r["rowid"], f"{r['first_name']} {r['last_name']}", r["status_reason"]] for r in rej])
              if rej else "_No rows._", ""]

    dup = conn.execute(f"""SELECT p.rowid later, o.rowid original, p.duplicate_criterion crit FROM persons p
                           LEFT JOIN persons o ON o.uuid = p.duplicate_of WHERE p.synthetic = 0 AND p.status='DUPLICATE'""").fetchall()
    parts += ["## 6. Duplicates",
              _table(["Later record", "Original record", "Matching criterion"], [list(r) for r in dup]) if dup else "_No rows._", ""]

    parts += ["## 7. Phone breakdown (countable records only)",
              _table(["Type", "Count"], [[PHONE_LABEL[k], v] for k, v in s["phones"].items()]),
              "\nShared or unattributed numbers never count towards the target.", ""]

    perf = channel_performance(conn)
    parts += ["## 8. Sourcing performance",
              _table(["Channel", "Country", "Reviewed", "A", "B", "C", "D", "ASK", "REJECT", "DUP", "Phone attributed"],
                     [[p["channel"], p["country"], p["reviewed"], p["a"], p["b"], p["c"], p["d"], p["ask"], p["reject"], p["dup"], p["phone_ok"]]
                      for p in perf]) if perf else "_No person-level sourcing has been run._", ""]

    parts += ["## 9. Excel export"]
    if export_report:
        v = export_report.get("verification", {})
        parts += [_table(["Item", "Value"], [
            ["Output filename", export_report["output"]], ["Worksheet", export_report["sheet"]],
            ["Exact heading row", repr(export_report["headings"])], ["Rows written", export_report["rows_written"]],
            ["First / last row written", f"{export_report['first_row']} / {export_report['last_row']}"],
            ["Phone cells stored as text", f"{v.get('phone_cells_text')} of {v.get('phone_cells_total')}"],
            ["Grade breakdown of exported rows", export_report["grades"]],
            ["Package parts changed vs template", v.get("parts_changed_vs_template")],
            ["Parts added or removed", v.get("parts_added_or_removed")], ["Formulas present", v.get("formulas")],
            ["Deliberate structural changes", export_report["structural_changes"] or "none"]])]
    else:
        parts += ["_No export has been run._"]
    parts += [""]

    unc = conn.execute(f"""SELECT p.rowid, p.first_name, p.last_name, p.grade, e.criterion, e.level, e.effective_level, e.limitations, e.source_url
                           FROM evidence e JOIN persons p ON p.uuid = e.person_uuid
                           WHERE p.synthetic = 0 AND p.status='PASS' AND (e.effective_level != 'STRONG' OR e.limitations IS NOT NULL)
                           ORDER BY p.rowid""").fetchall()
    parts += ["## 10. Uncertainty register",
              _table(["Record", "Name", "Grade", "Claim", "Assigned level", "Limitation", "Source"],
                     [[r["rowid"], f"{r['first_name']} {r['last_name']}", r["grade"], r["criterion"], r["effective_level"] or r["level"],
                       r["limitations"] or "indirect or partial evidence", r["source_url"]] for r in unc]) if unc else "_No rows._", ""]

    parts += ["## 11. Next target",
              (f"Target of {s['target']} reached. The run is complete; waiting for a new target." if s["remaining"] == 0
               else f"{s['remaining']} countable records still required to reach {s['target']}.")]
    return "\n".join(parts) + "\n"


def _evidence_summary(conn: sqlite3.Connection, rowid: int) -> str:
    rows = conn.execute("""SELECT criterion, COALESCE(effective_level, level) lv FROM evidence
                           WHERE person_uuid = (SELECT uuid FROM persons WHERE rowid = ?)""", (rowid,)).fetchall()
    return ", ".join(f"{r['criterion']}={r['lv']}" for r in rows) or "none recorded"


def _resolution(reason: str | None) -> str:
    reason = reason or ""
    hints = [("LinkedIn", "a profile URL captured from a permitted public source"),
             ("split-country", "confirmation of whether split-country origin is acceptable"),
             ("geographical exception", "a ruling on this location"), ("island", "a ruling on island residence"),
             ("financially related", "a source describing the person's actual function"),
             ("telephone attribution", "a number published for the named individual"),
             ("contradiction", "a newer or first-party source that settles the conflict"),
             ("no usable evidence", "a source supporting the missing criterion"),
             ("SUPPRESSED", "none - the person must not be contacted")]
    return "; ".join(h for key, h in hints if key in reason) or "additional source evidence"
