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
