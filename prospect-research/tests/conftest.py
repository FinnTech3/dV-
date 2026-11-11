"""Shared fixtures. Every record here is SYNTHETIC: invented names, example.com sources, test numbers."""
from __future__ import annotations

import copy
import shutil
from datetime import date
from pathlib import Path

import openpyxl
import pytest

from pipeline.tools import db, fetch

AS_OF = date(2026, 11, 10)
_counter = {"n": 0}


def ev(criterion, level="STRONG", reliability="PRIMARY", publication_date="2026-09-01", **kw):
    return {"criterion": criterion, "level": level, "reliability": reliability, "publication_date": publication_date,
            "retrieval_date": "2026-11-10", "source_url": f"https://example.com/{criterion}", "extract": "synthetic", **kw}


def make(levels: dict | None = None, **overrides) -> dict:
    """A synthetic candidate that is Grade A unless levels/overrides say otherwise."""
    _counter["n"] += 1
    n = _counter["n"]
    lv = {"prev_residence": "STRONG", "prev_employment": "STRONG", "cur_residence": "STRONG", "occupation": "STRONG", "phone": "STRONG"}
    lv.update(levels or {})
    cand = {
        "first_name": f"Synthetic{n}", "last_name": f"Person{n}", "occupation": "Architect", "employer": f"Example Studio {n}",
        "linkedin_url": f"https://www.linkedin.com/in/synthetic-record-{n:04d}", "linkedin_captured_from": "https://example.com/bio",
        "phone_raw": f"+34 612 34{n % 10} {n:03d}"[:16], "phone_type": "mobile", "phone_attribution": "published on own bio page",
        "prev_res_country": "GB", "prev_res_city": "Leeds", "prev_res_period": "2012-2019",
        "prev_emp_country": "GB", "prev_emp_employer": "Example Ltd", "prev_emp_city": "Leeds", "prev_emp_dates": "2012-2019",
        "cur_res_country": "ES", "cur_res_city": "Valencia",
        "evidence": [ev(c, l) for c, l in lv.items() if l != "NONE"],
        "external_id": f"synthetic-{n}",
    }
    cand["phone_raw"] = f"+346123{n:05d}"
    cand.update(overrides)
    return copy.deepcopy(cand)


@pytest.fixture
def settings():
    s = db.load_settings()
    s["waivers"] = {}          # tests describe the strict rules unless a test turns a waiver on
    return s


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "test.sqlite")
    yield c
    c.close()


@pytest.fixture(autouse=True)
def _clean_fetch_state():
    fetch.reset_state()
    yield


@pytest.fixture
def template(tmp_path, settings) -> Path:
    """A synthetic workbook with the same heading row and an Excel table, standing in for the supplied template."""
    real = db.PIPELINE / "private" / settings["export"]["template_filename"]
    path = tmp_path / "template.xlsx"
    if real.exists():
        shutil.copy2(real, path)
        return path
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(settings["export"]["expected_headings"])
    from openpyxl.worksheet.table import Table
    ws.add_table(Table(displayName="Table_1", ref="A1:F5"))
    wb.save(path)
    return path
