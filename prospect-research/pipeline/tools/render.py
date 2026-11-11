"""Excel export into a working copy of the supplied CRM template.

The workbook is edited at the XML level: only the target cells in the sheet
part are given inline-string values (and, if rows run past the existing table
or dimension range, those two range references are extended). Every other part
of the package - styles, theme, table definition, printer settings, widths - is
copied byte-for-byte, so no formatting or structure can change by accident.
The original template is never opened for writing.
"""
from __future__ import annotations

import hashlib
import posixpath
import re
import shutil
import sqlite3
import zipfile
from pathlib import Path

import openpyxl
from lxml import etree

from . import db, dedupe

M = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
COLS = "ABCDEF"

_TITLES = re.compile(r"(?i)^(?:(?:prof(?:essor)?|dr|mag|dipl|ing|sir|dame|rechtsanwalt|rechtsanw[aä]ltin|avv|me|maître|mr|mrs|ms)\.?\s*(?:iur\.?|jur\.?|habil\.?|h\.c\.|med\.?|rer\.?\s*nat\.?|rer\.?\s*pol\.?|-?\s*\w+\.)?\s+)+")
_DEGREES = re.compile(r"(?i)[,\s]+(?:LL\.?\s?M\.?|LLB|LL\.B\.|M\.?\s?Jur\.?|MBA|M\.?Sc\.?|B\.?Sc\.?|Ph\.?D\.?|M\.?Phil|MLaw|Dipl\.[- ]\w+\.?|MA|BA)(?![A-Za-z])[^,]*$")


def clean_name(first: str, last: str) -> tuple[str, str]:
    """Presentation-only tidy: titles ('Dr.') out of the first name, degrees ('LL.M. (Cambridge)') out of the last name."""
    full = f"{first or ''} {last or ''}".strip()
    full = re.sub(r"\s*\([^)]*\)\s*", " ", full).strip()                 # nicknames and place-of-degree in brackets
    if re.match(r"^\S+\s*,", full) or re.search(r"(?i),\s*(lawyer|attorney|partner|counsel)\b.*\bin\b", full):
        return (first or "").strip(), ""                   # the 'last name' is a job description: no usable surname
    full = re.sub(r"(?i),\s*(née|nee|geb\.)\s.*$", "", full)
    full = re.sub(r"(?i),\s*(dr|prof)\.?$", "", full)
    for _ in range(3):
        full = _DEGREES.sub("", full).strip(" ,")
    full = _TITLES.sub("", full).strip(" ,")
    parts = full.split()
    if len(parts) < 2:
        return (first or "").strip(), (last or "").strip()
    given = _TITLES.sub("", (first or "").strip() + " ").strip()
    if given and full.lower().startswith(given.lower() + " ") and len(full) > len(given) + 1:
        return given, full[len(given):].strip()
    i = 1
    while i < len(parts) - 1 and re.fullmatch(r"[A-Z]\.?", parts[i]):
        i += 1                                          # middle initials stay with the first name
    return " ".join(parts[:i]), " ".join(parts[i:])


_SENTENCEISH = re.compile(r"(?i)(\bis an?\b|\bist\b|\bber[aä]t\b|\bspecialis|\badvises\b|\bhas\b|\bwhich\b|\bwho\b|\bwith over\b|^(he|she|they)\b)")


def clean_occupation(occ: str | None, employer: str | None) -> str | None:
    """Presentation-only: a sentence fragment is not a job title; fall back to the neutral 'Professional at <firm>'."""
    occ = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), (occ or "")).strip()    # undecoded \u00fc escapes from page metadata
    if occ and (not occ[0].isalnum() or len(occ) > 90 or _SENTENCEISH.search(occ) or occ[0].islower()):
        return f"Professional at {employer}" if employer else None
    return occ or None


class ExportBlocked(RuntimeError):
    pass


def _q(tag: str) -> str:
    return f"{{{M}}}{tag}"


def _sheet_part(z: zipfile.ZipFile, sheet_name: str) -> str:
    wb = etree.fromstring(z.read("xl/workbook.xml"))
    rels = etree.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    targets = {r.get("Id"): r.get("Target") for r in rels}
    for s in wb.find(_q("sheets")):
        if s.get("name") == sheet_name:
            target = targets[s.get(f"{{{R}}}id")]
            return target.lstrip("/") if target.startswith("/") else posixpath.normpath("xl/" + target)
    raise ExportBlocked(f"worksheet {sheet_name!r} not found")


def _table_parts(z: zipfile.ZipFile, sheet_part: str) -> list[str]:
    rel_path = posixpath.join(posixpath.dirname(sheet_part), "_rels", posixpath.basename(sheet_part) + ".rels")
    if rel_path not in z.namelist():
        return []
    rels = etree.fromstring(z.read(rel_path))
    return [posixpath.normpath(posixpath.join(posixpath.dirname(sheet_part), r.get("Target")))
            for r in rels if r.get("Type", "").endswith("/table")]


def inspect(path: Path, settings: dict) -> dict:
    """Read-only inspection of a workbook: headings, populated rows and structure."""
    exp = settings["export"]
    wb = openpyxl.load_workbook(path)
    if exp["sheet"] not in wb.sheetnames:
        raise ExportBlocked(f"expected worksheet {exp['sheet']!r}; found {wb.sheetnames}")
    ws = wb[exp["sheet"]]
    headings = [ws.cell(1, i).value for i in range(1, 7)]
    extra = [c.value for c in ws[1][6:] if c.value is not None]
    rows = []
    for r in ws.iter_rows(min_row=2, max_col=6):
        vals = [c.value for c in r]
        if any(v not in (None, "") for v in vals):
            rows.append({"row": r[0].row, "first": vals[0], "last": vals[1], "occupation": vals[2], "phone": vals[3],
                         "email": vals[4], "linkedin": vals[5], "phone_is_text": isinstance(vals[3], str) or vals[3] is None})
    return {"sheetnames": wb.sheetnames, "headings": headings, "extra_headings": extra, "rows": rows,
            "tables": {t.name: t.ref for t in ws.tables.values()}, "dimension": ws.dimensions}


def eligible(conn: sqlite3.Connection, settings: dict) -> list[sqlite3.Row]:
    """Countable records suitable for the six-column CRM sheet and not yet exported."""
    exp = settings["export"]
    g = ",".join("?" * len(exp["grades_allowed"]))
    t = ",".join("?" * len(exp["phone_types_allowed"]))
    return conn.execute(
        f"""SELECT * FROM persons WHERE status='PASS' AND suppressed=0 AND synthetic=0 AND reserve=0
              AND grade IN ({g}) AND phone_type IN ({t}) AND linkedin_url IS NOT NULL AND phone_e164 IS NOT NULL
              AND uuid NOT IN (SELECT person_uuid FROM export_register)
            ORDER BY date_found, rowid""", (*exp["grades_allowed"], *exp["phone_types_allowed"])).fetchall()


def held_for_review(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM persons WHERE status='PASS' AND suppressed=0 AND synthetic=0 "
                        "AND crm_export_hold IS NOT NULL ORDER BY grade, date_found").fetchall()


def _set_cell(row_el, ref: str, value: str, col_styles: dict[str, str]) -> None:
    col = ref.rstrip("0123456789")
    cell = next((c for c in row_el.findall(_q("c")) if c.get("r") == ref), None)
    if cell is None:
        cell = etree.Element(_q("c"))
        cell.set("r", ref)
        if col in col_styles:
            cell.set("s", col_styles[col])
        after = [c for c in row_el.findall(_q("c")) if _col_index(c.get("r")) < _col_index(ref)]
        row_el.insert(len(after), cell)
    for child in list(cell):
        cell.remove(child)
    cell.set("t", "inlineStr")                      # stored as text: '+' is preserved, nothing is coerced to a number
    t = etree.SubElement(etree.SubElement(cell, _q("is")), _q("t"))
    t.text = value
    if value != value.strip():
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")


def _col_index(ref: str) -> int:
    n = 0
    for ch in ref.rstrip("0123456789"):
        n = n * 26 + ord(ch) - 64
    return n


def _patch_sheet(xml: bytes, records: list[tuple[int, list[str | None]]]) -> bytes:
    root = etree.fromstring(xml)
    data = root.find(_q("sheetData"))
    col_styles: dict[str, str] = {}
    cols = root.find(_q("cols"))
    if cols is not None:
        for c in cols:
            if c.get("style"):
                for i in range(int(c.get("min")), int(c.get("max")) + 1):
                    if 1 <= i <= 6:
                        col_styles[COLS[i - 1]] = c.get("style")
    rows = {int(r.get("r")): r for r in data.findall(_q("row"))}
    for rownum, values in records:
        row_el = rows.get(rownum)
        if row_el is None:
            row_el = etree.Element(_q("row"))
            row_el.set("r", str(rownum))
            position = sum(1 for n in rows if n < rownum)
            data.insert(position, row_el)
            rows[rownum] = row_el
        for letter, value in zip(COLS, values):
            if value not in (None, ""):
                _set_cell(row_el, f"{letter}{rownum}", str(value), col_styles)
    last = max(n for n, _ in records)
    dim = root.find(_q("dimension"))
    if dim is not None and ":" in dim.get("ref", ""):
        start, end = dim.get("ref").split(":")
        if int("".join(ch for ch in end if ch.isdigit())) < last:
            dim.set("ref", f"{start}:{end.rstrip('0123456789')}{last}")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _patch_table(xml: bytes, last_row: int) -> bytes | None:
    root = etree.fromstring(xml)
    start, end = root.get("ref").split(":")
    if int("".join(ch for ch in end if ch.isdigit())) >= last_row:
        return None
    new_ref = f"{start}:{end.rstrip('0123456789')}{last_row}"
    root.set("ref", new_ref)
    af = root.find(_q("autoFilter"))
    if af is not None:
        af.set("ref", new_ref)
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _digests(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as z:
        return {n: hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}


def export(conn: sqlite3.Connection, template: Path, out_path: Path, settings: dict) -> dict:
    """Append eligible, not-yet-exported records to the working copy. Idempotent across runs."""
    template, out_path = Path(template), Path(out_path)
    if template.resolve() == out_path.resolve():
        raise ExportBlocked("refusing to write to the original template")
    exp = settings["export"]
    template_sha = hashlib.sha256(template.read_bytes()).hexdigest()
    if not out_path.exists():
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template, out_path)
    before = inspect(out_path, settings)
    if before["headings"] != exp["expected_headings"] or before["extra_headings"]:
        raise ExportBlocked(f"heading row differs from the expected template: {before['headings']!r} {before['extra_headings']!r}")
    registered = {r["row"]: r["person_uuid"] for r in conn.execute(
        "SELECT row, person_uuid FROM export_register WHERE workbook = ?", (out_path.name,))}
    existing_rows = before["rows"]
    row_numbers = [r["row"] for r in existing_rows]
    if row_numbers and row_numbers != list(range(2, 2 + len(row_numbers))):
        raise ExportBlocked("existing rows are not contiguous from row 2; their meaning cannot be established")
    if any(not (r["first"] or r["last"]) for r in existing_rows):
        raise ExportBlocked("existing rows without a name; their meaning cannot be established")
    foreign = [r for r in existing_rows if r["row"] not in registered]   # rows that were already in the supplied sheet

    to_write, skipped_as_existing = [], []
    for p in eligible(conn, settings):
        hit = dedupe.spreadsheet_duplicate(dict(p), foreign)
        if hit:
            skipped_as_existing.append((p["uuid"], hit))
            continue
        to_write.append(p)
    report = {"output": str(out_path), "sheet": exp["sheet"], "headings": before["headings"], "rows_written": 0,
              "first_row": None, "last_row": None, "pre_existing_rows": len(foreign), "skipped_already_in_sheet": skipped_as_existing,
              "grades": {}, "template_sha256_unchanged": True, "structural_changes": []}
    for uid, hit in skipped_as_existing:
        conn.execute("UPDATE persons SET status='DUPLICATE', grade=NULL, duplicate_criterion=?, status_reason=? WHERE uuid=?",
                     ("already in supplied spreadsheet", f"duplicate of spreadsheet row {hit}", uid))
    conn.commit()
    if not to_write:
        report["verification"] = verify_workbook(out_path, template, [], settings)
        return report

    first = (row_numbers[-1] + 1) if row_numbers else 2
    records = [(first + i, [p["first_name"], p["last_name"], p["occupation"], p["phone_e164"], p["email"], p["linkedin_url"]])
               for i, p in enumerate(to_write)]
    last = records[-1][0]
    tmp = out_path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(out_path) as zin:
        sheet_part = _sheet_part(zin, exp["sheet"])
        tables = _table_parts(zin, sheet_part)
        with zipfile.ZipFile(tmp, "w") as zout:
            for info in zin.infolist():
                payload = zin.read(info.filename)
                if info.filename == sheet_part:
                    payload = _patch_sheet(payload, records)
                elif info.filename in tables:
                    patched = _patch_table(payload, last)
                    if patched is not None:
                        payload = patched
                        report["structural_changes"].append(f"table range in {info.filename} extended to row {last} to contain the new rows")
                zout.writestr(info, payload, compress_type=info.compress_type)
    tmp.replace(out_path)
    stamp = db.now_iso()
    for (rownum, _), p in zip(records, to_write):
        conn.execute("INSERT INTO export_register (person_uuid, workbook, sheet, row, exported_at) VALUES (?,?,?,?,?)",
                     (p["uuid"], out_path.name, exp["sheet"], rownum, stamp))
        report["grades"][p["grade"]] = report["grades"].get(p["grade"], 0) + 1
    conn.commit()
    report.update(rows_written=len(records), first_row=first, last_row=last)
    report["template_sha256_unchanged"] = hashlib.sha256(template.read_bytes()).hexdigest() == template_sha
    report["verification"] = verify_workbook(out_path, template, records, settings)
    return report


def verify_workbook(out_path: Path, template: Path, records: list, settings: dict) -> dict:
    """Reopen the saved workbook and confirm content and structure."""
    exp = settings["export"]
    info = inspect(out_path, settings)
    wb = openpyxl.load_workbook(out_path)
    ws = wb[exp["sheet"]]
    mismatches = 0
    for rownum, values in records:
        got = [ws.cell(rownum, i).value for i in range(1, 7)]
        if got != [v if v not in ("",) else None for v in values]:
            mismatches += 1
    phones_text = sum(1 for r in info["rows"] if r["phone"] is not None and isinstance(r["phone"], str))
    phones_total = sum(1 for r in info["rows"] if r["phone"] is not None)
    formulas = sum(1 for row in ws.iter_rows() for c in row if c.data_type == "f")
    a, b = _digests(template), _digests(out_path)
    changed = sorted(n for n in a if a[n] != b.get(n))
    return {"sheetnames": info["sheetnames"], "headings": info["headings"], "headings_exact": info["headings"] == exp["expected_headings"],
            "populated_rows": len(info["rows"]), "value_mismatches": mismatches, "phone_cells_text": phones_text,
            "phone_cells_total": phones_total, "formulas": formulas, "parts_added_or_removed": sorted(set(a) ^ set(b)),
            "parts_changed_vs_template": changed, "tables": info["tables"]}


def write_tsv(rows: list[list[str | None]], path: Path) -> Path:
    """Fallback: six tab-separated columns, no header row."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        for r in rows:
            fh.write("\t".join("" if v is None else str(v).replace("\t", " ") for v in r) + "\n")
    return path


def write_review_export(conn: sqlite3.Connection, path: Path) -> int:
    """Separate review file for countable records held out of the CRM sheet (Grade D, non-mobile numbers)."""
    rows = held_for_review(conn)
    write_tsv([[p["first_name"], p["last_name"], p["occupation"], p["phone_e164"], p["phone_type"], p["email"],
                p["linkedin_url"], p["grade"], p["crm_export_hold"]] for p in rows], path)
    return len(rows)

def everyone(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Everyone with a name and a telephone number who is not a duplicate, not rejected and not suppressed.

    Used for the quantity-first presentation sheet the project lead asked for. Order: complete records first, then people
    whose LinkedIn URL has not been found yet, then the quantity fill (batch FILLER) last.
    """
    return conn.execute(
        """SELECT * FROM persons WHERE status IN ('PASS','ASK') AND suppressed=0 AND synthetic=0
              AND COALESCE(do_not_contact,'unknown') != 'yes'
              AND phone_e164 IS NOT NULL AND TRIM(COALESCE(first_name,'')) != '' AND TRIM(COALESCE(last_name,'')) != ''
           ORDER BY (COALESCE(batch_id,'') LIKE 'FILLER%') ASC, (status='PASS') DESC, (linkedin_url IS NOT NULL) DESC, employer, last_name, first_name""").fetchall()


def export_everyone(conn: sqlite3.Connection, template: Path, out_path: Path, settings: dict, details: bool = False) -> dict:
    """Write everyone from `everyone()` into a fresh copy of the template (same six columns, table and styles).

    The export register is not touched; this is a separate presentation workbook. Numbers go in the Mobile Number column as text
    whatever their type; with details=True the type, firm and status are also written to a companion workbook (`<name>_details.xlsx`).
    """
    template, out_path = Path(template), Path(out_path)
    if template.resolve() == out_path.resolve():
        raise ExportBlocked("refusing to write to the original template")
    exp = settings["export"]
    before = inspect(template, settings)
    if before["headings"] != exp["expected_headings"] or before["rows"]:
        raise ExportBlocked("template heading row differs from expected, or it already holds rows")
    people, seen, rows = [], set(), []
    for p in everyone(conn):
        first, last = clean_name(p["first_name"], p["last_name"])
        key = ((first + " " + last).lower(), p["cur_res_country"] or "")
        if not first or not last or key in seen:
            continue                                   # same person listed twice under different spellings of the title or degree
        seen.add(key)
        people.append(p)
        rows.append([first, last, clean_occupation(p["occupation"], p["employer"]), p["phone_e164"], p["email"], p["linkedin_url"]])
    if not people:
        raise ExportBlocked("nobody to export")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    records = [(2 + i, r) for i, r in enumerate(rows)]
    last = records[-1][0]
    with zipfile.ZipFile(template) as zin:
        sheet_part = _sheet_part(zin, exp["sheet"])
        tables = _table_parts(zin, sheet_part)
        with zipfile.ZipFile(out_path, "w") as zout:
            for info in zin.infolist():
                payload = zin.read(info.filename)
                if info.filename == sheet_part:
                    payload = _patch_sheet(payload, records)
                elif info.filename in tables:
                    patched = _patch_table(payload, last)
                    if patched is not None:
                        payload = patched
                zout.writestr(info, payload, compress_type=info.compress_type)
    if not details:
        check = verify_workbook(out_path, template, records, settings)
        return {"output": str(out_path), "details": None, "rows_written": len(records), "with_linkedin": sum(1 for p in people if p["linkedin_url"]),
                "complete": sum(1 for p in people if p["status"] == "PASS"), "verification": check}
    # companion workbook: what each number is and how certain the record is
    labels = {"mobile": "mobile", "direct_work_mobile": "direct work mobile", "direct_landline": "direct landline",
              "shared_switchboard": "shared office number", "unknown": "number type not stated"}
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Details"
    ws.append(["Row in main sheet", "First name", "Last name", "Telephone", "Telephone type", "Occupation", "Firm", "LinkedIn", "Current country",
               "City", "Status", "Grade", "Why not complete", "Source page"])
    for (rownum, vals), p in zip(records, people):
        ws.append([rownum, vals[0], vals[1], p["phone_e164"], labels.get(p["phone_type"], p["phone_type"]), vals[2],
                   p["employer"], p["linkedin_url"], p["cur_res_country"], p["cur_res_city"],
                   "complete" if p["status"] == "PASS" else "incomplete", p["grade"], None if p["status"] == "PASS" else p["status_reason"],
                   p["phone_source_url"]])
    for col in ws.iter_cols(min_row=2, min_col=4, max_col=4):
        for c in col:
            c.data_type = "s"
    details = out_path.with_name(out_path.stem + "_details.xlsx")
    wb.save(details)
    check = verify_workbook(out_path, template, records, settings)
    return {"output": str(out_path), "details": str(details), "rows_written": len(records), "with_linkedin": sum(1 for p in people if p["linkedin_url"]),
            "complete": sum(1 for p in people if p["status"] == "PASS"), "verification": check}
