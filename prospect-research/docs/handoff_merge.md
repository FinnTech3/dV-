# Merge of the combined research handoff (11 November 2026)

Received: a 20-file archive combining the master prompt, a PLAN-stage pack from an earlier Claude Code run, and an independent supplement from ChatGPT. The originals are kept unmodified in `pipeline/sources/handoff/`. The merge is code (`pipeline/tools/handoff.py`, tested in `tests/test_handoff.py`), safe to re-run, and writes only to research tables. It never creates a person record.

**Nothing in this merge is a prospect.** Queries, organisations, employers, events and cities are research material. The count of individual prospects is unchanged by the merge itself.

## 1. What was merged, and how duplicates were removed

| Asset | Rows in | After merge | Removed | Rule |
|---|---|---|---|---|
| Search queries (4 CSVs + 16 searches already run here) | 516 | 476 | 40 | Exact match on normalised text. All 40 are the same LinkedIn strings repeated across destination-country filters; they are now 25 strings listing their countries. No near-duplicates exist between the 45 base and 270 expanded public-web queries (highest wording overlap 0.32). |
| Organisations and directories (34 + 37 + 14 from this project) | 85 | 48 | 37 | Same country plus same normalised name, or same dedicated host. Shared umbrella hosts (embassy pages, the Dutch diaspora portal) never merge distinct clubs. 9 appear in all three sources. |
| Events (69 + 52 + 15 verified here) | 136 | 98 | 38 | Same start date, same market and similar name. 37 appear in more than one file. |
| Employer seeds (375 + Berlin top 50 + 36 from this project) | 461 | 433 employer-market pairs (349 distinct organisations) | 28 | Normalised organisation name plus canonical market. |
| City lists (3) | 45 | 20 markets | | See section 3. |
| ChatGPT run log | 62 URLs | 61 added to the "already reviewed" register | 1 | Prevents re-fetching pages already assessed. |

Where files disagreed on a field, the independent audit won (it was checked on 10 November and is more specific); this project's own access findings were kept alongside in `access_restriction` and `discrepancy`.

## 2. Discrepancies found, with the evidence for each

All access checks were repeated on 11 November with the project's robots-aware fetcher.

| # | Claim in one source | What was found | Resolution |
|---|---|---|---|
| 1 | **This project** listed `bscc.info` as the British-Swiss Chamber of Commerce. | That site is the **British-Swedish** Chamber. The audit's `bscc.co.uk` is the British-Swiss chamber and loads normally. | My entry was wrong (taken from a search result). Corrected in `docs/sources.md` and the register. |
| 2 | **This project** found no BCCS member directory (guessed URL returned 404). Addendum: live directory at `/en/socios.html`. | `/en/socios.html` loads and lists member companies by sector and city. | Addendum is right; my URL was a guess, not a block. Directory is company-level. |
| 3 | **Addendum**: BPCC directory fetch returned 403. | Loads (HTTP 200) here, but the member records are rendered by the page's scripts, not present in the page source. | Access is allowed; the content is company-level and not retrievable without running page scripts. Not pursued. |
| 4 | **This project**: Franco-British Chamber site connection reset. | `francobritishchamber.com` (without `www`) loads; the directory page lists members alphabetically with sector filters. It says the 150-page printed directory carries managers' contact details; the web page does not. | Addendum URL is right. Company-level; contact details are in the printed directory only. |
| 5 | **Addendum**: the German-language BCCG route `/mitgliederverzeichnis/` displays named representatives while the English route needs a login. | Both routes return the same page: the login panel and category, country and plan filters, with no member rows in the page source. | Not confirmed. No named representatives could be read, and no login was attempted or bypassed. |
| 6 | **Addendum**: Irish Business Network Germany committee biographies carry Ireland-origin and Germany-residence clues. | Confirmed. Seven committee biographies on one page, several stating how many years the person has lived in Germany. None gives a phone number or a past job in Ireland. | Useful residence evidence; cannot qualify anyone alone. Kept as a lead. |
| 7 | **Addendum**: Dutch Business Club Spain shows selected member biographies. | Confirmed: about 30 members, each with a biography page, **and the member's own LinkedIn link**. No phone numbers. | New lane. See section 4. |
| 8 | **Addendum**: IPBN profiles exist but personal contacts go through the coordinator. | Consistent: the members page lists organisations; no personal contacts. | Not used for people. |
| 9 | **Addendum**: Irish Business Network Switzerland has public committee biographies. | The `/about` page loads; the `/committee` and `/members` pages I tried return 404. | Committee route not found yet. |
| 10 | **Packs**: 15 cities. **This project**: a different 15. | 10 are shared. | Union of 20 markets, tiered. Section 3. |
| 11 | **Packs**: 270 Boolean web queries as ready-to-run. | The native search tool ignores Boolean operators. Two ran as written and returned a news story about one founder, job boards and freelancer sites; a plain-language variant returned self-published personal pages with emails but no phone numbers. The tool also declines to identify private individuals from a combination of place and career. | The queries are kept as templates and marked pending. They are not a route to volume with this tool. |
| 12 | **Packs**: LinkedIn Boolean strings. | Following the instruction: planning aids only, `executable = 0`. No LinkedIn automation. | Unchanged. |

## 3. City plan after the merge (geographical caveats preserved)

| Country | Primary markets (both packs) | Secondary markets (from this project's resident-count evidence) |
|---|---|---|
| Spain | Madrid, Barcelona, Málaga | Alicante province |
| Portugal | Lisbon, Porto, Cascais | Algarve |
| France | Paris, Lyon, Nice | Bordeaux, Toulouse |
| Germany | Berlin, Munich, Frankfurt | |
| Switzerland | Zurich, Geneva, Basel | Lausanne |

Secondary markets skew towards older residents and small agencies, and produced few people in practice. The master prompt asks for three cities per country; the primary column is that set. The caveats travel with each row: Cascais is Lisbon metro; Matosinhos is not Porto; Nice leads may be Sophia Antipolis, Cannes or Grasse; Paris statistics are Île-de-France; Zurich and Geneva sector figures are cantonal; Frankfurt is Rhine-Main; Muttenz and Allschwil are not Basel municipality. Events keep venue locality in its own column and flag venues that differ from the market.

## 4. What the merged material changed in the discovery process

1. **SNOWBALL from member directories** (`pipeline/tools/snowball.py`). Chamber and network directories are lists of organisations. The tool pulls the member companies' own websites out of eight directory pages (604 external sites), probes each site's sitemap for public people pages, and sends those that have some to the existing crawler. Directory pages are read once; no login, no bypass.
2. **Member biographies as a residence source.** The Dutch Business Club pilot showed what the firm-directory crawl cannot: stated residence (the year or period of the move to Spain), career steps in the Netherlands, and a first-party LinkedIn link, all on one page. Six members were recorded (see the results file). None can count yet: no page gives them a personal number, and one studio page prints two numbers for two founders without saying whose is whose.
3. **Source status refreshed**, including three corrections to this project's own earlier register (items 1, 2 and 4 above).

## 5. Rules kept

No query, organisation, employer, event, exhibitor or event participant is counted as an individual. No residence is inferred from an employer's address or an office, and no phone ownership from a switchboard or a country code. Event pages are separated into programme, speaker, exhibitor and attendee lists; no attendee list was found for any event.
