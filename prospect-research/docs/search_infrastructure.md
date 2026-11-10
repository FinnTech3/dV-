# Search infrastructure

Checked 10 November 2026. No API keys, cookies or secrets are recorded here.

## Runtime
- Claude Code 2.1.322 in a managed cloud container (ephemeral; Linux; Python 3.13).
- GitHub access scoped to one repository, which is **public**.

## Tools discovered

| Tool | Available in this session | Tested | Result | Extra charge | Decision |
|---|---|---|---|---|---|
| Native `WebSearch` | Yes (deferred tool, loaded on demand) | Yes, 12 queries | Works. US-only index; returns titles, URLs and a summary | None visible from inside the session; "extended" mode is described as several times the cost, so only "standard" is used | **Primary discovery provider** |
| Direct HTTP retrieval (`curl`, `pipeline/tools/fetch.py`) | Yes | Yes (example.com, a chamber site and its robots.txt returned 200) | Works through the session's outbound proxy | None | **Primary retrieval path** |
| Chromium + Playwright | Pre-installed | Not needed yet | n/a | None | Reserve for JavaScript-only public pages |
| `web-fetch` subagent | Yes | Not used | n/a | Consumes model usage | Reserve |
| Research subagents | Yes | 5 launched in parallel | **All five stopped on the account's 5-hour usage limit before writing anything** | Consumes model usage | Use sparingly, one or two at a time |
| DuckDuckGo HTML endpoint | Reachable | Yes | HTTP 202 bot challenge | Free | **Not used**: automated access is being refused, and that is not evaded |
| Bright Data plugin (skills present) | Present | No | n/a | Paid, usage-billed | **Excluded** by the no-paid-provider rule |
| Brave Search API or other keyed APIs | Not configured | No | n/a | Paid or needs a user-created key | **Excluded**; not requested |
| Companies House API | Not configured | No | n/a | Free but needs a user-created key | Optional enhancement only (`ch.py`), off |
| Gmail, Notion, Wispr, 21st, GitHub MCP servers | Connected | Not used | n/a | n/a | Not research tools; not used for prospecting |
| Other plugin servers (LSEG, S&P, Daloopa, etc.) | Need authorisation or failed to connect | No | n/a | n/a | Not relevant |

## End-to-end path test
Search → result URL → robots.txt check → page retrieval → text extraction was exercised on organisation pages only. Person-level retrieval has not been run because the compliance gate is closed.

## Limits and reliability
- `WebSearch` is US-only and can miss local-language results; queries are written in the local language where useful.
- Search summaries are generated text. They are treated as leads; every fact must be confirmed on the source page.
- `fetch.py` waits 2 seconds between requests to a host, honours robots.txt, refuses LinkedIn hosts, and records 401/403/429/captcha as a block with no retry.
- The account usage limit is the real throughput constraint. A 1,000-record run needs several thousand searches and page reads and will span many sessions.

## Outstanding blockers
1. Compliance approval not recorded (`docs/compliance_gate.md`).
2. No persistent private storage for the database in this environment (`docs/unsure.md`, item 1).
