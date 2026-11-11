"""Tests for the research-asset merge. Synthetic CSVs only: no real organisation data and no people."""
from __future__ import annotations

import csv
from datetime import date

import pytest

from pipeline.tools import db, handoff


def write_csv(path, header, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


@pytest.fixture
def assets(tmp_path, monkeypatch):
    h = tmp_path / "handoff"
    d = tmp_path / "docs"
    (d / "plan").mkdir(parents=True)
    h.mkdir()
    monkeypatch.setattr(handoff, "HANDOFF", h)
    monkeypatch.setattr(handoff, "DOCS", d)
    return h, d


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.sqlite")
    handoff.migrate(c)
    yield c
    c.close()


def test_date_parsing_and_window():
    assert handoff.parse_dates("24–26 Nov 2026") == (date(2026, 11, 24), date(2026, 11, 26))
    assert handoff.parse_dates("28 Nov–9 Dec 2026") == (date(2026, 11, 28), date(2026, 12, 9))
    assert handoff.parse_dates("30 Nov 2026–15 Feb 2027") == (date(2026, 11, 30), date(2027, 2, 15))
    assert handoff.parse_dates("29 Jan–9 Feb 2027 (Creativeworld to 9 Feb)") == (date(2027, 1, 29), date(2027, 2, 9))
    assert handoff.parse_dates("25-26 Nov 2026")[0] == date(2026, 11, 25)
    assert handoff.parse_dates("sometime in spring") == (None, None)
    assert handoff.window_status(date(2026, 11, 9), date(2026, 11, 10)) == "finished_before_today"
    assert handoff.window_status(date(2026, 11, 9), date(2026, 11, 12)) == "underway_today"
    assert handoff.window_status(date(2026, 12, 1), date(2026, 12, 2)) == "upcoming"
    assert handoff.window_status(date(2027, 3, 1), date(2027, 3, 2)) == "outside_window"


def test_city_canonicalisation_keeps_metro_and_secondary_markets_distinct():
    assert handoff.canon_market("Porto / Matosinhos") == "Porto"
    assert handoff.canon_market("Allschwil (Basel metro)") == "Basel"
    assert handoff.canon_market("Frankfurt am Main") == "Frankfurt"
    assert handoff.canon_market("Málaga province") == "Málaga"
    assert handoff.canon_market("Alicante province (Costa Blanca)") == "Alicante province"
    assert handoff.canon_market("Davos (outside target-city list)") == "Other: Davos"


def test_query_merge_removes_repeats_keeps_executed_and_never_counts_people(assets, conn):
    h, _ = assets
    li_head = ["target_country", "LinkedIn_location_filter", "search_id", "Boolean_search_string", "variant", "main_risk", "operating_note"]
    write_csv(h / "LinkedIn_Search_Library.csv", li_head,
              [[c, c, "1", '("ex-London" OR "formerly based in the UK")', "base", "", ""] for c in ("Spain", "France", "Germany")])
    write_csv(h / "Quick_Win_Connector_Searches.csv", ["country", "target_city", "connector_type", "public_web_search_string", "note"],
              [["Spain", "Madrid", "Recruiters", "recruiter Madrid", "n"], ["Spain", "Madrid", "Recruiters", "  Recruiter   MADRID ", "n"]])
    pw = ["target_country", "target_city", "origin_country", "public_web_search_query", "use_limit"]
    write_csv(h / "Public_Web_Research_Queries.csv", pw, [["Spain", "Madrid", "United Kingdom", "lived in the UK moved to Madrid", "x"]])
    write_csv(h / "ChatGPT_Expanded_Public_Web_Queries.csv",
              ["target_country", "target_city", "origin_country", "search_angle", "public_web_query", "use_limit", "priority", "date_created"],
              [["Spain", "Madrid", "United Kingdom", "Residence-first", "lived in the UK moved to Madrid", "x", "High", "2026-11-10"]])
    stats = handoff.import_queries(conn)
    assert stats["exact_duplicates_removed"] >= 3          # 2 LinkedIn repeats + 1 connector whitespace/case variant (+1 cross-file public-web)
    rows = {r["kind"]: r for r in conn.execute("SELECT * FROM query_library")}
    assert rows["linkedin_boolean"]["executable"] == 0 and rows["linkedin_boolean"]["status"] == "planning_only"
    assert set(rows["linkedin_boolean"]["countries"].split(",")) == {"Spain", "France", "Germany"}
    assert rows["executed"]["status"] == "done"
    assert conn.execute("SELECT COUNT(*) FROM persons").fetchone()[0] == 0   # research material is never a prospect


def test_rerun_keeps_working_status(assets, conn):
    h, _ = assets
    write_csv(h / "Quick_Win_Connector_Searches.csv", ["country", "target_city", "connector_type", "public_web_search_string", "note"],
              [["Spain", "Madrid", "Recruiters", "recruiter Madrid", "n"]])
    for name, head in (("LinkedIn_Search_Library.csv", ["target_country", "LinkedIn_location_filter", "search_id", "Boolean_search_string", "variant", "main_risk", "operating_note"]),
                       ("Public_Web_Research_Queries.csv", ["target_country", "target_city", "origin_country", "public_web_search_query", "use_limit"]),
                       ("ChatGPT_Expanded_Public_Web_Queries.csv", ["target_country", "target_city", "origin_country", "search_angle", "public_web_query", "use_limit", "priority", "date_created"])):
        write_csv(h / name, head, [])
    handoff.import_queries(conn)
    conn.execute("UPDATE query_library SET status='done' WHERE kind='connector'")
    conn.commit()
    handoff.import_queries(conn)
    assert conn.execute("SELECT status FROM query_library WHERE kind='connector'").fetchone()[0] == "done"


def test_org_merge_prefers_audit_and_does_not_merge_distinct_clubs_on_shared_umbrella_site(assets, conn):
    h, d = assets
    write_csv(h / "Public_Organisations_and_Directories.csv",
              ["country", "organisation", "type", "official_url", "what_is_public", "what_is_not_verified_or_not_public", "checks_before_use"],
              [["Spain", "Example Chamber in Spain", "chamber", "https://chamber.example/", "old text", "old gap", "check"],
               ["Spain", "Dutch Club Madrid", "club", "https://www.snbn.org/", "", "", ""],
               ["Spain", "Dutch Club Barcelona", "club", "https://www.snbn.org/", "", "", ""]])
    write_csv(h / "ChatGPT_Official_Directory_Audit.csv",
              ["country", "organisation", "type", "official_url", "what_is_public_or_verified", "what_is_not_public_or_uncertain", "telephone_publication", "research_use", "status_checked_2026_11_10"],
              [["Spain", "Example Chamber in Spain", "chamber", "https://chamber.example/members", "new text", "new gap", "none", "orgs", "VERIFIED PAGE"]])
    (d / "sources.md").write_text("| Name | URL | C | Public | NonPublic | Phones | Profiles | Membership | Access | Verification |\n|---|---|---|---|---|---|---|---|---|---|\n"
                                  "| Example Chamber in Spain | https://chamber.example | ES / Madrid | p | n | not checked | nc | nc | robots allowed | Pages fetched |\n")
    stats = handoff.import_sources(conn)
    assert stats["merged_organisations"] == 3                    # chamber merged three ways; the two clubs stay separate
    r = conn.execute("SELECT * FROM sources WHERE name='Example Chamber in Spain'").fetchone()
    assert r["public_content"] == "new text" and r["non_public_content"] == "new gap" and r["audit_status"] == "VERIFIED PAGE"
    assert "claude_session" in r["origin_files"] and "robots allowed" in r["access_restriction"]
    assert "Earlier Claude session" in r["discrepancy"]


def test_event_merge_and_locality(assets, conn):
    h, d = assets
    write_csv(h / "Events_Nov2026_Feb2027.csv", ["country", "city", "event", "dates", "organiser", "official_page", "programme_or_list_page", "public_list_status"],
              [["Germany", "Basel metro", "Sample Expo 2027", "20–22 Jan 2027", "Org A", "https://a.example", "", "No attendee list verified."]])
    write_csv(h / "ChatGPT_Verified_Official_Events.csv",
              ["country", "target_city", "actual_venue_locality", "event", "date", "organiser", "organiser_verification", "official_event_page", "programme_speaker_exhibitor_page",
               "what_is_public_and_list_status", "prospecting_relevance", "date_checked", "confidence"],
              [["Switzerland", "Basel", "Muttenz", "Sample Expo", "20-22 Jan 2027", "Org A GmbH", "confirmed", "https://a.example/ev", "https://a.example/prog", "Exhibitor list only.", "tech", "2026-11-10", "HIGH"],
               ["Switzerland", "Zurich", "Zurich", "Finished Fair", "1 Nov 2026", "Org B", "", "", "", "", "", "2026-11-10", "LOW"]])
    stats = handoff.import_events(conn)
    assert stats["merged_events"] == 2 and stats["duplicates_removed"] == 1
    ev = conn.execute("SELECT * FROM events_register WHERE event LIKE 'Sample%'").fetchone()
    assert ev["venue_locality"] == "Muttenz" and ev["market"] == "Basel" and ev["organiser"] == "Org A GmbH"
    assert "separate" in ev["note"]
    assert conn.execute("SELECT window_status FROM events_register WHERE event='Finished Fair'").fetchone()[0] == "finished_before_today"
