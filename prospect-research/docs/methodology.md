# Methodology

## Qualification criteria
1. Previously **lived** in the UK, Republic of Ireland or the Netherlands.
2. Previously **worked** in the same origin country. Residence in one origin country and work in another is `ASK` (split-country).
3. Currently lives in mainland EU or Switzerland.
4. Current occupation is not financial adviser or an equivalent in any language.
5. A public telephone number reasonably attributable to the person.

Plus, to count: a genuine LinkedIn profile URL and no existing record of the person.

## Evidence levels
| Level | Meaning |
|---|---|
| STRONG | Direct, explicit, dated or current first-party source |
| MODERATE | Credible indirect source or several consistent indicators |
| WEAK | One contextual clue; says what it does not prove |
| NONE | Nothing usable |
| CONTRADICTED | A credible source conflicts and the conflict is unresolved |

The researcher assigns a level to each evidence item. `verify.py` then applies mechanical caps, and only ever lowers a level:

| Rule | Effect |
|---|---|
| Source reliability `UNVERIFIED` | Item counts as NONE |
| Source reliability `AGGREGATOR` | Capped at MODERATE |
| Current residence or occupation evidence older than 12 months, not corroborated by a newer source | Lowered one level |
| Same, older than 36 months | Capped at WEAK |
| Same, undated | Capped at MODERATE |
| Unresolved contradicting item from a non-unverified source | Criterion is CONTRADICTED |
| Shared switchboard | Telephone capped at WEAK |

The criterion level is the best remaining supporting item.

## Grades (applied in order)
| Grade | Rule |
|---|---|
| A | 5 STRONG |
| B | 4 STRONG + 1 MODERATE |
| C | ≥3 STRONG, ≤2 below STRONG |
| D | ≥2 STRONG, ≤3 below STRONG |

No grade if any criterion is NONE or CONTRADICTED, or if telephone is below MODERATE.

## Classification (first match wins)
| Status | Triggers |
|---|---|
| DUPLICATE | Exact cleaned LinkedIn URL; exact individual phone; exact name + employer; or already in the supplied sheet |
| REJECT | Lives in UK/Ireland; lives outside Europe; adviser occupation; study-only link; proven no qualifying employment; `NO NUMBER YET` (none found or number invalid) |
| ASK | Netherlands, listed islands, MT, CY, NO, IS, LI, AD, MC, other non-EU Europe; ambiguous financial role; split-country; any NONE or CONTRADICTED criterion; phone below MODERATE; more than three criteria below STRONG; no LinkedIn URL (incomplete reserve); person asked not to be contacted |
| PASS | Everything else, with grade A-D |

## Telephone
Type is what the source says: mobile, direct work/mobile, direct landline, shared switchboard, unknown. The numbering library only validates and formats to E.164. Only `mobile` enters the CRM column; other individually attributable types count towards the pool but are held in `held_for_review.tsv`.

## Deduplication
Run at ingest and again before export. Fuzzy name similarity (≥0.88) sets a review flag only. Two people on one shared number are flagged, never merged.

## Sources
Reliability classes: PRIMARY, REPUTABLE_SECONDARY, AGGREGATOR, UNVERIFIED. Publication date and retrieval date are stored separately. Search snippets are never evidence.

## Excel export
`render.py` edits only cell values in the sheet XML of a working copy, as inline text. All other package parts are copied byte-for-byte. If rows run past the table's current range (row 179) the table and dimension ranges are extended and this is reported. An export register prevents any person being written twice.

## Contact restrictions
Defaults: route `cold`, objection `unknown`, do-not-contact `unknown`. Absence of an objection is never recorded as consent. Suppressed people leave the countable pool and every export.
