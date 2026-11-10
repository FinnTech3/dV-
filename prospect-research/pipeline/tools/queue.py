"""Persistent work queue and checkpoints so that AUTO can resume without repeating work."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from . import db

CHECKPOINT_PATH = db.PIPELINE / "ledger" / "checkpoint.json"


def add_task(conn: sqlite3.Connection, country: str, city: str | None, source: str, source_type: str, query: str | None = None,
             next_action: str = "", requires_person_gate: bool = True) -> bool:
    """Queue a unit of work. Returns False when the same task already exists."""
    cur = conn.execute(
        """INSERT OR IGNORE INTO work_queue (country, city, source, source_type, query, next_action, requires_person_gate, created, updated)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (country, city or "", source, source_type, query or "", next_action, 1 if requires_person_gate else 0, db.now_iso(), db.now_iso()))
    conn.commit()
    return cur.rowcount == 1


def next_task(conn: sqlite3.Connection, person_gate_open: bool) -> sqlite3.Row | None:
    """Claim the next pending task; person-level tasks are skipped while the gate is closed."""
    row = conn.execute(
        "SELECT * FROM work_queue WHERE status IN ('in_progress','pending') AND (requires_person_gate = 0 OR ?) "
        "ORDER BY CASE status WHEN 'in_progress' THEN 0 ELSE 1 END, id LIMIT 1", (1 if person_gate_open else 0,)).fetchone()
    if row:
        conn.execute("UPDATE work_queue SET status='in_progress', updated=? WHERE id=?", (db.now_iso(), row["id"]))
        conn.commit()
    return row


def finish_task(conn: sqlite3.Connection, task_id: int, status: str = "done", batch_id: str | None = None, discovered: int = 0,
                reviewed: int = 0, graded: int = 0, errors: str | None = None, next_action: str | None = None) -> None:
    assert status in ("done", "blocked", "failed", "pending")
    conn.execute(
        """UPDATE work_queue SET status=?, batch_id=COALESCE(?, batch_id), discovered=discovered+?, reviewed=reviewed+?,
               graded=graded+?, errors=?, next_action=COALESCE(?, next_action), updated=? WHERE id=?""",
        (status, batch_id, discovered, reviewed, graded, errors, next_action, db.now_iso(), task_id))
    conn.commit()


def counts(conn: sqlite3.Connection) -> dict:
    by_status = {r["status"]: r["n"] for r in conn.execute(
        "SELECT status, COUNT(*) n FROM persons WHERE synthetic = 0 GROUP BY status")}
    grades = {r["grade"]: r["n"] for r in conn.execute(
        "SELECT grade, COUNT(*) n FROM persons WHERE synthetic = 0 AND status='PASS' AND suppressed=0 GROUP BY grade")}
    queue = {r["status"]: r["n"] for r in conn.execute("SELECT status, COUNT(*) n FROM work_queue GROUP BY status")}
    return {"persons_by_status": by_status, "pass_by_grade": grades, "countable": sum(grades.values()), "queue": queue}


def checkpoint(conn: sqlite3.Connection, settings: dict, note: str = "", path: Path | None = None) -> dict:
    """Write a resumable checkpoint (counts and queue position only; no personal data)."""
    state = counts(conn)
    nxt = conn.execute("SELECT id, country, city, source, next_action FROM work_queue WHERE status IN ('in_progress','pending') ORDER BY id LIMIT 1").fetchone()
    payload = {
        "written": db.now_iso(),
        "target": settings["target_countable"],
        "remaining": max(settings["target_countable"] - state["countable"], 0),
        **state,
        "next_task": dict(nxt) if nxt else None,
        "note": note,
    }
    path = path or CHECKPOINT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)
    db.log(conn, mode="CHECKPOINT", checkpoint=str(path.name), note=note)
    return payload
