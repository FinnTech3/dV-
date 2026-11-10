"""Person-level research gate (Section 18, step 13).

Person-level harvesting stays disabled until the organisation's compliance
approval is recorded in `pipeline/config/compliance_approval.json`. The file is
written by a human with authority to give that approval; the pipeline never
creates or edits it and never treats its absence as approval.
"""
from __future__ import annotations

import json
from pathlib import Path

from .db import PIPELINE

APPROVAL_PATH = PIPELINE / "config" / "compliance_approval.json"
REQUIRED_FIELDS = ("approved_by", "role", "organisation", "date", "scope", "lawful_basis", "countries_covered",
                   "telephone_contact_rules_confirmed", "retention_and_deletion_process")


class PersonGateClosed(PermissionError):
    pass


def status(path: Path | None = None) -> dict:
    path = path or APPROVAL_PATH
    if not path.exists():
        return {"open": False, "reason": f"no approval record at {path.name}"}
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"open": False, "reason": f"approval record is not valid JSON: {exc}"}
    missing = [f for f in REQUIRED_FIELDS if not str(record.get(f, "")).strip()]
    if missing:
        return {"open": False, "reason": "approval record incomplete: missing " + ", ".join(missing)}
    if record.get("approved") is not True:
        return {"open": False, "reason": "approval record does not state approved: true"}
    return {"open": True, "reason": "approval recorded", "record": {k: record[k] for k in REQUIRED_FIELDS}}


def require_open(path: Path | None = None) -> None:
    st = status(path)
    if not st["open"]:
        raise PersonGateClosed("person-level research is not permitted yet: " + st["reason"])
