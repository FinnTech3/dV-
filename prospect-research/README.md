# Prospect research pipeline

A local-first research system for a supervised trainee exercise. It discovers publicly listed professionals who previously lived and worked in the UK, Republic of Ireland or the Netherlands and now live in mainland EU or Switzerland, grades the evidence for each one, and fills a copy of the supplied six-column CRM workbook.

**It does not contact anyone.** It researches and records.

## Current state (11 November 2026)

| Item | State |
|---|---|
| Tooling, database, queue, exporter | Built |
| Synthetic test suite | 80 tests passing (`docs/tool_tests.md`) |
| Supplied workbook | Inspected; headings only, no existing prospects; working copy verified byte-identical |
| City selection and directory research | Provisional (`docs/plan/plan.md`) |
| Research library merged from the combined handoff | 476 queries, 48 organisations, 98 events, 433 employer seeds, 20 markets (`docs/handoff_merge.md`) |
| Person-level research | Running under the approval recorded on 10 November 2026 (local, git-ignored file; see `docs/compliance_gate.md`). Prospect data stays local |
| Valid prospects | See `pipeline/ledger/checkpoint.json` (counts only). Short of 1,000; reasons in `docs/avenues.md` |

## What the grades mean

Every prospect is scored on five things: previous residence, previous employment, current residence, current occupation, and whether the phone number really belongs to them.

| Grade | Meaning |
|---|---|
| A | All five points strongly evidenced |
| B | Four strong, one moderate |
| C | At least three strong; up to two moderate or weak |
| D | At least two strong; up to three moderate or weak. Exploratory, **not** fully verified |

A total of 1,000 means 1,000 evidence-graded prospects, never 1,000 verified people. Reports always show the breakdown and the A+B subtotal.

## What goes into the Excel sheet

Only Grade A, B or C records whose number the source itself describes as a mobile. Direct work lines, landlines and Grade D records stay in the database and a separate review file until the trainer confirms whether they are acceptable. Numbers are stored as text so the `+` survives. The original workbook is never modified.

## Layout

```
docs/        methodology, search infrastructure, sources, open questions, test results, compliance gate, plan
pipeline/
  config/    settings, plan seed, (compliance_approval.json - written by an authorised person)
  tools/     search, fetch, discover, verify, phone, linkedin, dedupe, render, queue, report, ch, gate, cli
  database/ staging/ evidence/ output/ private/ report/   local only, git-ignored
tests/       synthetic scenarios
```

## Running

```
pip install -r requirements.txt
python -m pytest -q
python -m pipeline.tools.cli status
```

## Data handling

Prospect data, evidence and workbooks are kept out of version control. The GitHub repository this code lives in is public, so nothing personal is ever committed. People who ask not to be contacted are suppressed and excluded from every export.
