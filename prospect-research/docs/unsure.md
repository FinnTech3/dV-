# Open questions and judgement calls

## Needs a decision from you or the trainer

| # | Question | Current handling |
|---|---|---|
| 1 | **Where may the prospect database live?** This session runs in a temporary cloud container and the only persistent store is a public GitHub repository. The brief forbids pushing personal data. As things stand, any person-level work would be lost when the container is reclaimed, so the run could not resume. | Person-level work not started. Options: run Claude Code locally on a work machine, or provide approved private storage. |
| 2 | **Compliance approval** is not recorded. | Gate closed. See `compliance_gate.md`. |
| 3 | Are direct work numbers and landlines acceptable in the `Mobile Number` column? | Held out of the sheet; kept in the review file. |
| 4 | Should Grade D ever go into the CRM sheet? | No; review file only. |
| 5 | Is split-country origin (lived in one origin country, worked in another) acceptable? | `ASK`. |

## Places where the brief was ambiguous

| # | Issue | Choice made |
|---|---|---|
| 6 | Section 5.5 says a WEAK or switchboard-only number is `REJECT: NO NUMBER YET`; section 11 says phone attribution below MODERATE is `ASK`. | No number or invalid number → REJECT `NO NUMBER YET`. A number exists but is only organisation-level → ASK. Neither counts. |
| 7 | "Exactly one of four statuses" versus a separate "incomplete reserve" list. | Reserve records are `ASK` with a reserve flag and reported as a sub-count. |
| 8 | Suppressed people are not one of the four statuses. | `ASK` with reason `SUPPRESSED`; never countable or exported. |
| 9 | European countries not named in the brief (e.g. Serbia, Turkey, Ukraine). | `ASK`. |
| 10 | Undated but live first-party pages (typical staff biographies) as evidence of *current* role or residence. | Capped at MODERATE, because retrieval date is not publication date. This makes Grade A rare; say if a live employer page should be treated as current. |
| 11 | Grade B "equivalent evidence quality" discretion. | Not automated; only the strict 4 STRONG + 1 MODERATE rule is applied. |
| 12 | A LinkedIn URL with no recorded capture source whose slug is just the person's name. | Treated as possibly guessed and dropped; record goes to reserve. |
