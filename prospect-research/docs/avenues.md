# Search avenues: reasoning and results

Organisations and methods only; no individual is named here. Figures are as of 10 November 2026.

The brief needs five things to be true of one person at once: lived in the UK, Ireland or the Netherlands; worked there; now lives in mainland EU or Switzerland; is not a financial adviser; and has a phone number published for them personally. Almost no single public page shows all five. Each avenue below starts from an institution that, for its own reasons, already publishes most of them together.

## 1. Professional-firm people directories (main source)
**Idea.** International firms publish a page per person with a direct line and a short career history. Firms' sitemaps list every such page, so they can be read systematically without search engines.
**Method.** `pipeline/tools/firmcrawl.py` reads only sitemap-listed, robots-allowed pages at one request per two seconds per site, extracts the name, title, numbers with the label the page gives them, any LinkedIn link, and the sentence describing work in an origin country. A number is accepted only if it appears on no other profile. Every extracted sentence is then read and false matches removed.
**Result.** About 76,000 pages across 96 sites. About 5,000 people describe work in an origin country; about 3,900 of them are still based there and are excluded. This is the source of nearly every valid record.
**Limits.** Office location is only weak evidence of residence, so grades are C or D. Four sites refused access and were not retried.

## 2. Sector expansion
Executive search (useful: consultants have international careers), patent and trade mark firms (weak: staff mostly still in the UK), property consultancy (very low: about 2 usable in 2,200 pages), consulting (negligible), business schools and research institutes (no individual numbers, or access refused).

## 3. Estate agencies used by British buyers
**Idea.** Agents are often British, print mobile numbers and describe their move in the first person.
**Result.** The largest network publishes several hundred agent pages with exactly that first-person residence history, but prints only head-office numbers, so nobody passes the phone test. Four smaller agencies gave a handful of people.

## 4. Anglican chaplaincies (Diocese in Europe)
**Idea.** A chaplain's biography lists earlier English parishes with years; chaplains live where they serve; the occupation is unambiguous; chaplaincies print contact numbers.
**Method.** `pipeline/tools/churches.py` reads the diocese's church list (275 churches), then each mainland church's own site.
**Result.** 141 sites were readable. The biographies are the best evidence found anywhere in this project (stated residence, dated posts). But the pages with a biography rarely print the chaplain's own number, and the pages that print a chaplain's number rarely carry a biography. Six people were recorded; none passes the phone test yet. With per-person follow-up this could yield a small number of high-grade records.

## 5. Tried and not usable
- UK Foreign Office finder for English-speaking professionals abroad: unreachable from this environment.
- Open scholarly database (past UK institution, current EU institution, with years): rate-limited at once; not pursued.
- Press announcements of London-to-continent relocations: one search found no clear cases.
- Search engine queries combining career history with phone patterns: the search tool declines or rewrites them.

## 6. Not yet tested
- German "Impressum" pages: sole traders must publish name, address and phone, usually beside an "about me" career history. Discovery would start from translator and interpreter association directories.
- The European Patent Office register of professional representatives.

## 7. Member directories as a source of organisations (SNOWBALL), added 11 November
**Idea.** A bilateral chamber's directory lists companies that chose to be associated with the UK, Ireland or the Netherlands. Those companies' own websites sometimes publish founder and team pages with direct contact details. The directory is the seed; the company's sitemap is the retrieval route.
**Method.** `snowball.py` extracts external member sites from eight directory pages, probes each site's sitemap for people pages, and registers every site as an organisation. Sites with people pages go to the same crawler as the firm directories. See `handoff_merge.md`.
**Result.** 604 member sites found; 46 expose at least two people pages. Most of those are accountancy or tax firms (ambiguous occupation, so they would be `ASK`), firms already crawled, or Swiss and French law firms not reached before. Outcome of the crawl is in the status report.

## 8. Member biographies (Dutch Business Club Spain), added 11 November
**Idea.** A club that publishes short biographies of its members is publishing residence and career evidence voluntarily.
**Result.** About 30 members, each with a biography page and the member's own LinkedIn link. Biographies state current residence (often the year of the move) and past steps in the Netherlands. No phone numbers. Six members were recorded as a phone-completion reserve; none qualifies, because the members' own websites either print only a company number, print two numbers without naming whose, or refuse automated access.

## 9. Routes tested on 11 November after the handoff merge, with measured results

Each route was sampled before any large crawl, so effort went where the evidence pointed. Failures are recorded because they rule things out.

| Route | Idea | Measured result | Decision |
|---|---|---|---|
| Relocation-announcement mining (`newsmine.py`) | Firms announce moves ("relocates from our London office to Frankfurt"); a dated first-party statement of both the UK posting and the move, fused by exact name with the person's own profile for the phone number | 12 firms, about 275 announcement pages sampled, 2 sentence hits, both people *joining* London offices | Dropped. Tool and tests kept. |
| University and research-institute staff pages | CVs list postdocs and fellowships abroad; staff pages list direct lines | 125 sites probed; about 30 expose 100+ person pages. 12-14 pages sampled from 20 of them. Phone numbers are common (hospital and institute pages 12/12) but a UK, Irish or Dutch career appears in 0-8% of pages; business-school faculty was best (ESMT 8%, with LinkedIn on half the pages) | Crawled only ESMT (100 pages: 8 with a UK or Dutch career, all 100 with a phone, 43 with LinkedIn); the rest are not worth the hours at these rates |
| Consultancy expert pages (BCG, Simon-Kucher, Buro Happold) | Senior staff pages with direct line and the person's own LinkedIn link | BCG: phone on 12/12, LinkedIn on 11/12 sampled pages, 1 UK career in 12 | Stopped after 369 pages: all 21 candidates with both a phone and a UK, Irish or Dutch career were in the US (BCG prints numbers only for US staff). Simon-Kucher prints none. Buro Happold: 49 UK-history pages, mostly UK offices |
| Open-data seed (`osmseed.py`) | Generate source sites from OpenStreetMap (lawyers, architects, estate agents, clinics, schools with a website, by city) instead of from directories | Madrid: 964 sites generated. First 200 probed: 5 (2.5%) expose any people pages, because most small firms do not list individuals in their sitemaps. The service also refuses large combined queries, so smaller ones are needed | Works as a generator but the conversion is too low to scale blindly |
| Leisure and hospitality professionals | Golf pros, ski-school directors, dive-centre and guest-house owners publish personal mobiles for bookings and tell a career story | Seed tool built (resort regions, sport and tourism tags) but not run: Overpass refused the large combined queries, and the team-page parser (next row) returned nothing on the sites tested | Not pursued |
| Team-page segmentation (`teamparse.py`, `teamcrawl.py`) | Most small firms list the whole team on one page, which a per-person crawler cannot read. Split the page into people; accept a number only if it sits in that person's block and nowhere else on the page | 1,567 sites (964 Madrid firms from open data plus 603 chamber-member sites): 926 had a readable team page, 7,105 person blocks, 400 with a number of their own, 23 with a UK, Irish or Dutch sentence, **0 with both**. Parser tested on real pages; it correctly rejects shared office numbers | Null result: on small firms, people who publish their own number and people who describe a UK career are different people |
| Member-company sites from chamber directories | See section 7 | 604 sites, 46 with people pages, 16 crawled; no new valid people | Done |

**What the measurements say.** Across every route the same three rates multiply: a site must expose person pages (about 2-8% of small sites, most large firms), the page must carry a number that is the person's own (about 20-50%), and it must describe a past in the UK, Ireland or the Netherlands (about 1-8%). That is why 80,000 pages produced about 250 people. No route found so far beats the larger law firms' 6-8%.

## What limits the total
In order of effect: (1) the number must be the person's alone; (2) there must be evidence of past work, not just study or a qualification, in an origin country; (3) most people with that history have not left. Relaxing (1) to accept an office number would add roughly 180 people immediately and open up avenue 3.
