"""SQLite single source of truth: schema, connection and small helpers."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "pipeline"
DEFAULT_DB = PIPELINE / "database" / "prospects.sqlite"
SETTINGS_PATH = PIPELINE / "config" / "settings.json"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS persons (
    uuid TEXT PRIMARY KEY,                 -- immutable identifier, never derived from name/phone
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    occupation TEXT,
    employer TEXT,
    linkedin_url TEXT,
    email TEXT,
    phone_raw TEXT,
    phone_e164 TEXT,
    phone_type TEXT,                       -- mobile | direct_work_mobile | direct_landline | shared_switchboard | unknown
    phone_attribution TEXT,                -- free-text description of how the number is tied to the person
    phone_source_url TEXT,
    prev_res_country TEXT, prev_res_city TEXT, prev_res_period TEXT, prev_res_level TEXT,
    prev_emp_country TEXT, prev_emp_employer TEXT, prev_emp_city TEXT, prev_emp_role TEXT,
    prev_emp_dates TEXT,                   -- stored at the precision published, never padded
    prev_emp_level TEXT,
    cur_res_country TEXT, cur_res_city TEXT, cur_res_region TEXT, cur_res_since TEXT, cur_res_level TEXT,
    occupation_level TEXT,
    phone_level TEXT,
    grade TEXT,                            -- A | B | C | D | NULL
    status TEXT NOT NULL DEFAULT 'ASK',    -- DUPLICATE | REJECT | ASK | PASS
    status_reason TEXT,
    reserve INTEGER NOT NULL DEFAULT 0,    -- 1 = incomplete reserve (e.g. no LinkedIn URL); never countable
    crm_export_hold TEXT,                  -- reason the record is held out of the six-column CRM sheet
    possible_duplicate_of TEXT,            -- fuzzy flag only; never auto-merged
    duplicate_of TEXT,
    duplicate_criterion TEXT,
    date_found TEXT,
    date_last_checked TEXT,
    research_channel TEXT,
    contact_route TEXT NOT NULL DEFAULT 'cold',                       -- cold | warm | existing
    contact_objection TEXT NOT NULL DEFAULT 'unknown',                -- yes | no recorded objection | unknown
    do_not_contact TEXT NOT NULL DEFAULT 'unknown',                   -- yes | no recorded request | unknown
    suppressed INTEGER NOT NULL DEFAULT 0,
    suppression_date TEXT,
    suppression_basis TEXT,
    notes TEXT,
    batch_id TEXT,
    synthetic INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_persons_linkedin ON persons(linkedin_url);
CREATE INDEX IF NOT EXISTS ix_persons_phone ON persons(phone_e164);
CREATE INDEX IF NOT EXISTS ix_persons_name ON persons(last_name, first_name);
CREATE INDEX IF NOT EXISTS ix_persons_status ON persons(status, grade);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_uuid TEXT NOT NULL REFERENCES persons(uuid) ON DELETE CASCADE,
    criterion TEXT NOT NULL,               -- prev_residence | prev_employment | cur_residence | occupation | phone | linkedin
    field TEXT,                            -- exact person field supported
    source_url TEXT NOT NULL,
    organisation TEXT,
    reliability TEXT NOT NULL,             -- PRIMARY | REPUTABLE_SECONDARY | AGGREGATOR | UNVERIFIED
    publication_date TEXT,                 -- as published; NULL when undated
    retrieval_date TEXT NOT NULL,
    extract TEXT,
    level TEXT NOT NULL,                   -- level asserted by the researcher for this item
    effective_level TEXT,                  -- after reliability / freshness caps
    contradicts INTEGER NOT NULL DEFAULT 0,
    resolved INTEGER NOT NULL DEFAULT 0,
    limitations TEXT
);
CREATE INDEX IF NOT EXISTS ix_evidence_person ON evidence(person_uuid, criterion);

CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source_type TEXT,
    country TEXT, city TEXT,
    public_content TEXT, non_public_content TEXT,
    publishes_individual_phones TEXT,      -- yes | no | not checked
    profiles_public TEXT,
    membership_required TEXT,
    automated_access TEXT,
    reliability TEXT,
    date_checked TEXT,
    access_restriction TEXT,
    searches INTEGER NOT NULL DEFAULT 0,
    discovered INTEGER NOT NULL DEFAULT 0,
    reviewed INTEGER NOT NULL DEFAULT 0,
    seconds_spent REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL, session TEXT, mode TEXT, country TEXT, city TEXT,
    source TEXT, query TEXT, provider TEXT,
    discovered INTEGER DEFAULT 0, reviewed INTEGER DEFAULT 0,
    grades TEXT, duplicates INTEGER DEFAULT 0, ask INTEGER DEFAULT 0, reject INTEGER DEFAULT 0,
    source_blocks INTEGER DEFAULT 0, usage_limits INTEGER DEFAULT 0, technical_failures INTEGER DEFAULT 0,
    checkpoint TEXT, note TEXT               -- no personal details belong in this table
);

CREATE TABLE IF NOT EXISTS work_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country TEXT, city TEXT, source TEXT, source_type TEXT, query TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | in_progress | done | blocked | failed
    batch_id TEXT, discovered INTEGER DEFAULT 0, reviewed INTEGER DEFAULT 0, graded INTEGER DEFAULT 0,
    errors TEXT, next_action TEXT, requires_person_gate INTEGER NOT NULL DEFAULT 1,
    created TEXT, updated TEXT,
    UNIQUE(country, city, source, query)
);

CREATE TABLE IF NOT EXISTS searched (
    key TEXT PRIMARY KEY,                  -- normalised query / page / organisation already processed
    kind TEXT NOT NULL, provider TEXT, ts TEXT NOT NULL, result_count INTEGER
);

CREATE TABLE IF NOT EXISTS export_register (
    person_uuid TEXT PRIMARY KEY REFERENCES persons(uuid),
    workbook TEXT NOT NULL, sheet TEXT NOT NULL, row INTEGER NOT NULL, exported_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS suppression_markers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marker_hash TEXT NOT NULL UNIQUE,      -- minimal salted hash kept only where approved policy allows
    policy_basis TEXT NOT NULL, created TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_uuid() -> str:
    return str(uuid.uuid4())


def load_settings(path: Path | None = None) -> dict:
    return json.loads((path or SETTINGS_PATH).read_text(encoding="utf-8"))


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def log(conn: sqlite3.Connection, **fields) -> None:
    """Append an activity-ledger row. Callers must not pass personal details."""
    fields.setdefault("ts", now_iso())
    cols = ", ".join(fields)
    conn.execute(f"INSERT INTO ledger ({cols}) VALUES ({', '.join('?' * len(fields))})", list(fields.values()))
    conn.commit()
