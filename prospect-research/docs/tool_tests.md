# Tool and quality tests

Run 10 November 2026 with synthetic records only (invented names, example.com sources, test numbers). No real person appears in any test.

```
........................................................................ [ 97%]
..                                                                       [100%]
74 passed in 3.23s
```

## Scenario coverage (section 14 of the brief)

| # | Scenario | Test |
|---|---|---|
| 1 | Strong, moderate, weak residence evidence | `test_01` |
| 2 | Employment with full, year-only and missing dates | `test_02` |
| 3 | Work without residence evidence | `test_03` |
| 4 | Study without employment | `test_04` |
| 5-10 | Mainland EU, Switzerland, Netherlands, UK/Ireland, excluded island, outside Europe | `test_05_to_10` |
| 11 | Disqualifying adviser occupation (EN, ES, FR, DE, PT, NL) | `test_11` |
| 12 | Ambiguous financial occupation | `test_12` |
| 13 | Strong, moderate, weak phone attribution | `test_13` |
| 14 | Mobile, work mobile, landline, switchboard | `test_14` |
| 15 | Two people sharing a company number | `test_15` |
| 16 | Invalid telephone number | `test_16` |
| 17 | Duplicate LinkedIn URL | `test_17` |
| 18 | Duplicate individual phone | `test_18` |
| 19 | Same name and employer | `test_19` |
| 20 | Similar names not merged | `test_20` |
| 21 | Missing or guessed LinkedIn URL | `test_21` |
| 22 | Conflicting residence sources | `test_22` |
| 23 | Stale and undated evidence | `test_23` |
| 24 | Person asking not to be contacted | `test_24` |
| 25 | Re-running a candidate batch | `test_25` |
| 26 | Re-running the Excel export | `test_26` |
| 27 | Existing populated spreadsheet | `test_27` |
| 28 | Search provider unavailable | `test_28` |
| 29 | Search rate limit | `test_29` |
| 30 | Website blocks retrieval, robots.txt, LinkedIn host, captcha | `test_30` |
| 31 | Prompt injection in page text | `test_31` |
| 32 | Irrelevant or fabricated-looking snippets | `test_32` |

Additional tests: grade arithmetic table (A/B/C/D and every non-gradeable case), split-country origin, source-reliability caps, table-range extension past row 179, compliance gate refusing real ingest, queue resume and checkpoint, and a check that no record with NONE evidence or a sub-MODERATE phone is ever PASS.

## Tool checks on real, non-personal targets

| Check | Result |
|---|---|
| Supplied workbook inspection | Sheet1; headings exactly `First name ` (trailing space), `Last Name`, `Occupation`, `Mobile Number`, `Email`, `Linkedin profile link`; 0 data rows; table `Table_1` A1:F179 |
| Working copy `Prospect_List_.xlsx` with zero rows | SHA-256 identical to the original |
| Export against a copy of the real template in tests | Only the sheet part changes; phone cells are text; no formulas |
| Native web search | 12 queries returned results |
| Page retrieval | example.com and a chamber site returned 200; DuckDuckGo HTML returned a 202 challenge and is not used |
| `cli ingest` with gate closed | Refused, exit code 2 |
