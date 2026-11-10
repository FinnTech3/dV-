# Compliance gate for person-level research

**Status on 10 November 2026: CLOSED.** No approval record was found in the project or the session. Under section 18, step 13 of the brief, only non-personal research has been carried out. No individual has been named, searched for or stored.

## What is needed (one time)

Someone with authority at the organisation (compliance officer, DPO or the supervising trainer acting on their instruction) creates `pipeline/config/compliance_approval.json` from `pipeline/config/compliance_approval.example.json`. The pipeline checks that every field is filled and `approved` is `true`. The file is git-ignored. Claude does not create or edit it, and a chat message saying "approved" is not treated as the record.

## Why this matters: what the checks found

The brief asks for a list of private individuals with personal telephone numbers and residence history, in five countries, for a financial services group. That is processing of personal data under GDPR (and the Swiss FADP), and if the numbers are used for calls, national telemarketing rules apply. These rules were looked up on 10 November 2026; they are summaries of secondary sources and regulator pages, not legal advice.

| Country | Finding | Source |
|---|---|---|
| France | Since 11 August 2026, telephone canvassing of consumers is prohibited without prior consent (opt-in); Bloctel abolished. Law 2025-594 of 30 June 2025, art. 13; decree 2026-662. | [DGCCRF](https://www.economie.gouv.fr/dgccrf/les-fiches-pratiques/demarchage-telephonique-professionnels-mettez-vous-en-conformite-avec-la-reglementation), [Club des Juristes](https://www.leclubdesjuristes.com/en-bref/demarchage-telephonique-le-consentement-prealable-devient-obligatoire-a-partir-du-11-aout-2026-17147/) |
| Spain | Art. 66.1.b of Ley 11/2022: right not to receive unsolicited commercial calls without prior consent or another GDPR art. 6.1 basis; AEPD Circular 1/2023. Calling to ask for consent is also not allowed. | [AEPD](https://www.aepd.es/prensa-y-comunicacion/notas-de-prensa/la-aepd-publica-la-circular-sobre-el-derecho-de-los-usuarios), [BOE](https://www.boe.es/eli/es/cir/2023/06/26/1/con/20230628) |
| Germany | §7 UWG: advertising calls to consumers require prior express consent, which must be documented; calls to businesses need at least presumed consent. | [Bundesnetzagentur](https://bundesnetzagentur.de/DE/Vportal/TK/Aerger/Faelle/UEW/start.html), [IHK](https://www.ihk.de/bodensee-oberschwaben/recht/werbung-und-vertrieb/was-ist-erlaubt-1943228) |
| Portugal | Lei 41/2004 and CNPD Guidelines 2022/1: without an existing customer relationship, direct marketing to individuals needs prior express consent. Sources disagree on how live (non-automated) calls are treated; needs confirming against the statute. | [Garrigues](https://www.garrigues.com/pt/pt-PT/news/nova-diretriz-da-cnpd-marketing-direto-o-tem-mudar-na-forma-empresas-fazem-marketing), [Mondaq](https://www.mondaq.com/privacy-protection/1160114/new-cnpd-guidelines-on-direct-marketing-electronic-communications) |
| Switzerland | UCA art. 3(1)(u): calling people with a "no advertising" asterisk in the directory is unfair competition; one source says this also covers people with no directory entry. Art. 3(1)(w) also prohibits using data obtained in breach of these rules. | [BAKOM](https://www.bakom.admin.ch/en/when-is-mass-sending-allowed), [Schellenberg Wittmer](https://www.swlegal.com/en/insights/newsletter-detail/stricter-fairness-rules-for-telemarketing-in-switz/) |

A number published on someone's professional page for their own business is not consent to be called about an unrelated personal financial product. In at least France, Spain and Germany the list as specified cannot lawfully be used for unsolicited calls to individuals without consent or another documented legal basis.

## Questions the approval should answer

1. Lawful basis under GDPR art. 6 for collecting and storing these records, and how the art. 14 notice to each person will be given.
2. Whether and how the numbers will be used, country by country, given the rules above.
3. Whether the organisation is authorised to market financial services in each target country.
4. Retention period and the deletion process (section 12A of the brief).
5. Where the database may be stored. The current environment is a temporary cloud container and the code repository is public.
