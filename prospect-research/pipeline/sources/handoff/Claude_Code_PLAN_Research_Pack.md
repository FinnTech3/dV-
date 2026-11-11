# AUTONOMOUS PROSPECT RESEARCH: PLAN OUTPUT AND SOURCE PACK

**Prepared:** 10 November 2026 (Europe/London)  
**Research window for events:** 10 November 2026 to 10 February 2027  
**Initial stopping target:** 1,000 countable evidence-graded records  
**Origin countries:** United Kingdom, Republic of Ireland and Netherlands  
**Destination countries:** Spain, Portugal, France, Germany and Switzerland  
**Intended use:** Feed this file and its CSV companions into the supplied Claude Code master prompt.

## 0. How Claude should use this pack

This file is a **PLAN-stage research pack**, not a harvested prospect database. It supplies target-city choices, employer and industry leads, reusable queries, public organisation directories and event leads. Claude must verify current operation, access permissions and all person-level facts independently before counting any prospect.

**Do not interpret any company list below as a definitive ranking of the five largest companies.** Comparable city-level rankings were not available for every city and cluster. The organisation names are significant employer / ecosystem research seeds, not proof that a specific person currently works there or qualifies. The CSV explicitly labels them as seeds, not ranks.

**No attendee lists are invented.** Where a public event page exposes speakers, programme or exhibitors, that is identified separately. An exhibitor directory is not an attendee list. Where no public attendee list could be verified, the pack says so.

**No LinkedIn scraping is authorised.** The Boolean library is a search reference. The user's operating rule says search wording should remain unchanged when changing destination location filters. The same ten queries therefore repeat across all five target-country filters. Claude must not automate logged-in LinkedIn research or scrape member profiles. Use only authorised LinkedIn integrations or URLs published by other permitted sources.

**No paid search-provider signup is authorised.** Do not create a Brave, Tavily or other paid search account, do not request payment details, and do not incur charges. First inspect Claude Code's existing WebSearch, WebFetch, browser and MCP capabilities, plus any installed free/approved tools. Use them where permitted. Report any capability gap honestly.

**Evidence grading:** follow the current master prompt. Residence evidence may be indirect or loose at lower grades, but it must be genuinely source-based. Employment still requires employer, city and dates. Current residence cannot be inferred solely from an employer's location. Telephone attribution must be at least MODERATE for a record to count towards 1,000. Every countable record also needs a real LinkedIn URL and an occupation field. See the master prompt for grade A-D definitions and CRM export restrictions.

## 1. Target-city recommendations

| Country | Recommended cities | Why these cities are in scope | Research priority |
|---|---|---|---|
| Spain | Madrid, Barcelona, Málaga | Madrid and Barcelona are prominent international employment centres. Málaga has a substantial international technology park ecosystem with hundreds of businesses and major technology / consulting employers. | 1 Madrid, 2 Barcelona, 3 Málaga |
| Portugal | Lisbon, Porto, Cascais | Lisbon has a broad service and digital economy. Porto has a strong export / industrial base and growing tech and business-service centres. Cascais has a dense local company base in professional services, property, health and hospitality, but is part of the Lisbon metro market. | 1 Lisbon, 2 Porto, 3 Cascais |
| France | Paris, Lyon, Nice | Paris has the widest multinational and executive base. Lyon has substantial pharma, biotech and industrial clusters. Nice connects to the wider Côte d'Azur technology, fragrance, tourism and R&D economy. | 1 Paris, 2 Lyon, 3 Nice |
| Germany | Berlin, Munich, Frankfurt | Berlin has technology, health, media and mobility employers. Munich has automotive, ICT, insurance and life sciences. Frankfurt has financial services, logistics, life sciences and IT. | 1 Berlin, 2 Munich, 3 Frankfurt |
| Switzerland | Zurich, Geneva, Basel | Zurich has a dense multinational, ICT and financial base. Geneva has international organisations, trading, life sciences, watchmaking and fragrance. Basel is a major pharma/life-sciences and logistics cluster. | 1 Zurich, 2 Geneva, 3 Basel |

### Geographic boundary notes

- Cascais is best treated as a municipality within the Lisbon metropolitan market. Record city/municipality separately from metro area.
- Porto event venues at Exponor are in Matosinhos, in the Porto metropolitan area. Do not mislabel Matosinhos as Porto municipality.
- Nice company and cluster leads frequently refer to the Alpes-Maritimes / Côte d'Azur, including Sophia Antipolis, Cannes, Grasse and Carros. Verify the exact workplace municipality before recording it as Nice.
- Basel leads may relate to Basel-Stadt, Basel-Landschaft or the wider Basel Area. Preserve the exact locality.
- Zurich statistics refer in some cases to the Canton of Zurich, not the city municipality.

### Supporting economic sources

- [Madrid Region investor presentation, 2025](https://www.comunidad.madrid/sites/default/files/img/profesiones/24.02.2025_investor_presentation_final.pdf): digital economy, aerospace, gaming/content, banking/insurance/fintech, pharma/biotech and logistics.
- [Madrid Facts & Figures 2025](https://wemadrid.es/wp-content/uploads/2025/07/MEC2025_ENG_digital.pdf): company counts, investment and employment context.
- [Barcelona Activa economic sectors](https://treball.barcelonactiva.cat/infografies/en/): ICT, life sciences, manufacturing 4.0, mobility/logistics, creative industries, trade/tourism and other sectors.
- [Barcelona Activa strategic industries](https://empreses.barcelonactiva.cat/en/strategic-industries): city and metro-area strategic clusters.
- [Málaga Valley official ecosystem](https://openforbusiness.malaga.eu/es/Malaga-Valley/): public company/sector directory. [Málaga TechPark leadership ecosystem](https://www.pta.es/noticias/club-directivos-malaga-techpark-execs-eurecat-bhs/) provides additional employer names.
- [Málaga TechPark leadership ecosystem](https://www.pta.es/noticias/club-directivos-malaga-techpark-execs-eurecat-bhs/): employer/leadership network with many businesses.
- [Lisboa Economy in Figures 2025](https://www.lisboa.pt/): use the official city publication and verify the exact downloaded report before using city employment percentages.
- [AICEP Digital Sector in Portugal report](https://www.portugalglobal.pt/media/ztlmymv3/digital-industry-report.pdf): Lisbon and Porto digital-sector company examples and employment concentration.
- [InvestPorto competitive economy](https://investporto.pt/en/why-porto/competitive-economy/): Porto/Northwest Portugal clusters, FDI and named international employers.
- [Cascais company-sector profile](https://empresadb.pt/relatorios/cascais): secondary compilation citing INE; use cautiously and seek the underlying INE series for formal rankings.
- [Paris Region Facts and Figures 2025](https://www.investparisregion.eu/sites/default/files/pdf/Paris-Region-Facts-Figures-2025/Paris-Region-Facts-and-Figures-2025-BD.pdf): regional sector and company examples. It is regional, not Paris municipality only.
- [ONLYLYON pharma and biotechnology](https://invest.onlylyon.com/en/sectors-of-excellence/health-and-life-sciences/pharma-and-biotechnology/): regional health/pharma ecosystem and company examples.
- [Invest in Côte d'Azur, working in the region](https://www.investincotedazur.com/en/welcome-guide-cote-dazur/welcome-guide-work-cote-azur/): employers in Sophia Antipolis, Cannes and Grasse; regional rather than Nice-city only.
- [Berlin Top 200 employers](https://www.businesslocationcenter.de/en/information-for-new-berliners/working-in-berlin/employers-berlin): 2025 employer ranking with workforce by company.
- [Make it in Munich industries](https://www.make-it-in-munich.com/living-in-munich/why-munich/industries/): Munich sectors and insurance/ICT firms.
- [Meet Frankfurt key industries](https://www.meetfrankfurt.de/en/why-frankfurt/key-industries): chemicals/pharma/life sciences, financial services, IT/telecoms, creative industry and logistics/mobility.
- [Canton Zurich business location](https://www.zh.ch/en/wirtschaft-arbeit/wirtschaftsstandort/standortvorteile.html): international company presence and business context.
- [Canton Zurich cluster data](https://www.zh.ch/en/wirtschaft-arbeit/zuercher-wirtschaftszahlen/cluster-daten.html): ICT, finance, life sciences, cleantech, creative and tourism.
- [Canton Geneva key sectors](https://www.ge.ch/en/teaser/entreprendre-geneve/key-sectors): life sciences, finance, trading/shipping, digital economy, watchmaking/luxury, aroma/fragrance and engineering.
- [Canton Basel-Stadt important industries and companies](https://www.bs.ch/en/schwerpunkte/portrait/economie-et-arbeit/important-industries-and-companies): life sciences, logistics/trade, finance, digital and company examples.
- [Messe Berlin calendar](https://www.messe-berlin.de/en/events/event-calendar): GFFA, Grüne Woche and Fruit Logistica dates in January/February 2027.
- [IFEMA Madrid calendar](https://www.ifema.es/en/calendar): 2026/27 fairs including SIMO Educación, Accountex, Matelec, Genera, FITUR, C!Print and Intergift.
- [Fira de Barcelona calendar](https://www.firabarcelona.com/en/trade_show/): IBTM World, ICE, iGB Affiliate, ISE, Barcelona Wine Week and other venue events.
- [FYCMA calendar](https://fycma.com/calendario/): SIMED, Andalucía TRADE Global, Málaga Sun&Tech, Talent Land and additional Málaga events.
- [FIL Lisbon calendar](https://fil.lisbonvenues.pt/en/calendar/): Web Summit, Lisboa Games Week, dental congress and other Lisbon venue dates.
- [Exponor calendar](https://exponor.pt/en/calendario/): Concreta, Eléctrica, 360 Tech Industry and Inforce event leads in the Porto metropolitan area.
- [Paris Convention Bureau trade-show calendar](https://parisjetaime.com/eng/convention/article/fairs-and-trade-shows-a1194): updated 10 November 2026 with Paris event dates through the research window.
- [Messe München events](https://tickets.messe-muenchen.de/MM-SHOP/Events): electronica, SEMICON Europa, BAU and f.re.e dates.
- [Messe Frankfurt calendar](https://configurator.messefrankfurt.com/messeffmstorefront/ffm/en/veranstaltungskalender/kalender): Formnext, Heimtextil, Ambiente and related events.
- [Messe Zürich events](https://www.messe-zuerich.com/en/events): Berufsmesse, Data Center Nation, Logistics & Automation, Empack and FESPO.
- [Genève internationale calendar](https://www.geneve-int.ch/calendar): Geneva Health Forum and UN / international organisation events.

## 2. Five-by-five industry and company research seeds

**How to interpret this section:** each city has five relevant industry clusters and five company/organisation leads per cluster. This is a discovery map, not a statistically ranked top-five employer list. Some examples operate at metro, regional or cantonal scale. Claude must verify the exact office, site or local operating presence before using an employer to identify people. The structured file `City_Industry_Employer_Seeds.csv` contains 375 seed rows.

### Madrid, Spain
**Market scope:** Madrid.  **Evidence source:** [Madrid Region investor presentation and Madrid Facts & Figures 2025](https://www.comunidad.madrid/sites/default/files/img/profesiones/24.02.2025_investor_presentation_final.pdf).
- **Digital, telecoms and software:** Telefónica; Indra; IBM; Microsoft; Google.
- **Banking, insurance and professional services:** Banco Santander; BBVA; Mapfre; Deloitte; Accenture.
- **Pharmaceuticals and healthcare:** Lilly España; Pfizer España; Roche Farma España; Sanofi España; Quirónsalud.
- **Aerospace, engineering and energy:** Airbus; Iberdrola; Repsol; Siemens; Acciona.
- **Transport, aviation and logistics:** Aena; Iberia; Renfe; DHL; SEUR.

### Barcelona, Spain
**Market scope:** Barcelona.  **Evidence source:** [Barcelona Activa strategic sectors and Barcelona Activa economic sector map](https://treball.barcelonactiva.cat/infografies/en/).
- **IT, digital and telecommunications:** Amazon; Google; Microsoft; Cisco; NTT DATA.
- **Life sciences and healthcare:** AstraZeneca; Almirall; Bayer; Sanofi; Novartis.
- **Manufacturing, mobility and engineering:** SEAT / CUPRA; Ficosa; Gestamp; Schneider Electric; HP.
- **Creative, fashion and consumer brands:** Puig; Mango; Desigual; Pronovias; Damm.
- **Tourism, transport and logistics:** Port of Barcelona; Aena; DHL; Kuehne+Nagel; Meliá Hotels International.

### Málaga, Spain
**Market scope:** Málaga.  **Evidence source:** [Málaga TechPark official ecosystem and EC digital innovation hub profile](https://openforbusiness.malaga.eu/es/Malaga-Valley/).
- **Technology and software:** Accenture; Oracle; Ericsson; Google; Huawei.
- **Engineering, aerospace and industrial technology:** Aertec Solutions; ADIF Centro de Tecnologías Ferroviarias; TDK; Keysight Technologies; DEKRA.
- **IT services and consulting:** CGI; NTT DATA; Capgemini; PwC; EY.
- **Tourism and hospitality:** Meliá Hotels International; Barceló Hotel Group; Hilton; Marriott International; Minor Hotels.
- **Transport, property and infrastructure:** Aena; Port of Málaga; FCC; Sacyr; Neinor Homes.

### Lisbon, Portugal
**Market scope:** Lisbon.  **Evidence source:** [Lisboa Economy in Figures 2025 and AICEP digital-sector report](https://www.portugalglobal.pt/media/ztlmymv3/digital-industry-report.pdf).
- **Digital, IT and software:** Microsoft; Cisco; Capgemini; Accenture; NTT DATA.
- **Professional and business services:** Deloitte; PwC; EY; KPMG; CGI.
- **Banking and insurance:** Caixa Geral de Depósitos; Millennium bcp; Santander Portugal; Fidelidade; Ageas Portugal.
- **Tourism, aviation and hospitality:** TAP Air Portugal; Pestana Hotel Group; Vila Galé; SANA Hotels; Altis Hotels.
- **Ports, freight and logistics:** Port of Lisbon; Administração do Porto de Lisboa; DHL; Maersk; FedEx.

### Porto, Portugal
**Market scope:** Porto / Porto Metropolitan Area.  **Evidence source:** [InvestPorto competitive economy and AICEP digital-sector report](https://investporto.pt/en/why-porto/competitive-economy/).
- **Digital, IT and business services:** Natixis; Critical TechWorks; Farfetch; Kantar; TeamViewer.
- **Automotive, engineering and manufacturing:** Continental; Bosch; Vestas; Simoldes; CaetanoBus.
- **Finance, trade and logistics:** Euronext; BNP Paribas; FedEx; Maersk; Kuehne+Nagel.
- **Healthcare and life sciences:** BIAL; CUF; Unilabs; Trofa Saúde; Lusíadas Saúde.
- **Tourism, retail and food groups:** Sonae; Pestana Hotel Group; Vila Galé; Symington Family Estates; Super Bock Group.

### Cascais, Portugal
**Market scope:** Cascais / Lisbon Metropolitan Area.  **Evidence source:** [Cascais municipal company-sector profile (secondary compilation citing INE) and IPBN public member directory](https://empresadb.pt/relatorios/cascais).
- **Real estate and property services:** JLL; Savills; Engel & Völkers; RE/MAX; Coldwell Banker.
- **Hotels and hospitality:** Onyria Quinta da Marinha; Sheraton Cascais Resort; Hotel Cascais Miragem; Martinhal Lisbon Cascais; InterContinental Cascais-Estoril.
- **Healthcare and private clinics:** Hospital de Cascais; CUF Cascais; Joaquim Chaves Saúde; Hospital da Luz; Lusíadas Saúde.
- **Professional and business services:** PwC Portugal; Deloitte Portugal; EY Portugal; KPMG Portugal; Abreu Advogados.
- **Technology and business ecosystem:** DNA Cascais; OutSystems; Cisco Portugal; Microsoft Portugal; Capgemini Portugal.
  - **Location caution:** several company names refer to the Lisbon metropolitan employment market, not necessarily a Cascais address. Confirm the exact municipality.

### Paris, France
**Market scope:** Paris / Île-de-France.  **Evidence source:** [Choose Paris Region and Institut Paris Region Facts & Figures 2025](https://www.investparisregion.eu/sites/default/files/pdf/Paris-Region-Facts-Figures-2025/Paris-Region-Facts-and-Figures-2025-BD.pdf).
- **Technology, telecoms and digital:** Google; Microsoft; IBM; Orange; Capgemini.
- **Financial services and insurance:** BNP Paribas; Société Générale; Crédit Agricole; AXA; Euronext.
- **Luxury, fashion and cosmetics:** LVMH; Kering; Chanel; Hermès; L’Oréal.
- **Healthcare and life sciences:** Sanofi; Servier; Ipsen; Pfizer; AstraZeneca.
- **Transport, aviation and logistics:** Air France-KLM; SNCF; RATP; Groupe ADP; Geodis.

### Lyon, France
**Market scope:** Lyon / Auvergne-Rhône-Alpes.  **Evidence source:** [ONLYLYON Invest and Lyon tourism / economic cluster sources](https://invest.onlylyon.com/en/sectors-of-excellence/health-and-life-sciences/pharma-and-biotechnology/).
- **Pharmaceuticals and biotechnology:** Sanofi; bioMérieux; Boehringer Ingelheim; Bayer; Eli Lilly / Alexion.
- **Chemicals and environmental industries:** Arkema; Solvay; Kem One; Elkem; BASF.
- **Digital and software:** Cegid; Esker; LDLC; Worldline; Ubisoft.
- **Mobility, automotive and engineering:** Renault Trucks; Volvo Group; Alstom; OPmobility; Plastic Omnium.
- **Professional services, events and consumer goods:** GL events; Adecco; Groupe SEB; Descours & Cabaud; April.

### Nice, France
**Market scope:** Nice / Alpes-Maritimes / Côte d’Azur.  **Evidence source:** [Invest in Côte d’Azur and Nice Côte d’Azur official business ecosystem pages](https://www.investincotedazur.com/en/welcome-guide-cote-dazur/welcome-guide-work-cote-azur/).
- **Technology, software and R&D:** Amadeus; IBM; SAP; Orange; Thales Alenia Space.
- **Fragrance, flavour and perfumery:** Mane; Robertet; Givaudan; DSM-Firmenich; Expressions Parfumées.
- **Tourism and hospitality:** Accor; Marriott International; Hyatt; Barrière; Radisson Hotel Group.
- **Healthcare, pharma and health technology:** Virbac; Arkopharma; CHU de Nice; Centre Antoine Lacassagne; Clinique Saint-Georges.
- **Engineering, construction and industrial services:** Fayat; KONE; Banque Populaire Méditerranée; Vishay; Schneider Electric.
  - **Location caution:** the Côte d’Azur ecosystem includes Nice, Sophia Antipolis, Cannes, Grasse and Carros. Keep the actual municipality in the database.

### Berlin, Germany
**Market scope:** Berlin.  **Evidence source:** [Berlin Business Location Center Top 200 employers and sector pages](https://www.businesslocationcenter.de/en/information-for-new-berliners/working-in-berlin/employers-berlin).
- **Transport and logistics:** Deutsche Bahn; Berliner Verkehrsbetriebe (BVG); Deutsche Post DHL; Tesla; Mercedes-Benz.
- **Healthcare and life sciences:** Charité; Vivantes; Alexianer; Johannesstift Diakonie; Bayer.
- **Digital platforms and technology:** SAP; Zalando; Delivery Hero; N26; HelloFresh.
- **Media, entertainment and creative industries:** Axel Springer; Universal Music Group; Sony Music; RTL; Netflix.
- **Energy and industrial technology:** 50Hertz; Siemens Energy; Vattenfall; Berliner Energie und Wärme AG; Enpal.

### Munich, Germany
**Market scope:** Munich.  **Evidence source:** [City of Munich / Make it in Munich official industry overview](https://www.make-it-in-munich.com/living-in-munich/why-munich/industries/).
- **Automotive and engineering:** BMW; MAN Truck & Bus; MTU Aero Engines; Knorr-Bremse; Siemens Mobility.
- **ICT, software and digital:** Google; Apple; Microsoft; IBM; Salesforce.
- **Insurance, banking and financial institutions:** Allianz; Munich Re; Swiss Re; Generali; HypoVereinsbank / UniCredit.
- **Life sciences and healthcare:** Roche Diagnostics; Daiichi Sankyo; Amgen; MSD; Dr. von Hauner Children’s Hospital / LMU Klinikum.
- **Consulting and professional services:** Accenture; Capgemini; Deloitte; EY; PwC.

### Frankfurt, Germany
**Market scope:** Frankfurt / Frankfurt Rhine-Main.  **Evidence source:** [Meet Frankfurt official five-sector economic overview](https://www.meetfrankfurt.de/en/why-frankfurt/key-industries).
- **Financial services and market infrastructure:** Deutsche Bank; Commerzbank; Deutsche Börse; DZ Bank; European Central Bank.
- **Aviation, logistics and mobility:** Fraport; Lufthansa Cargo; DHL; DB Schenker; Kuehne+Nagel.
- **Pharma, chemicals and life sciences:** Sanofi; Merz; Fresenius; Clariant; Bayer.
- **IT and telecommunications:** T-Systems; IBM; SAP; NTT DATA; Accenture.
- **Consulting and professional services:** PwC; EY; KPMG; Deloitte; McKinsey & Company.

### Zurich, Switzerland
**Market scope:** Zurich / Canton of Zurich.  **Evidence source:** [Canton Zurich business-location and cluster data pages](https://www.zh.ch/en/wirtschaft-arbeit/wirtschaftsstandort/standortvorteile.html).
- **ICT, software and digital research:** Google; Microsoft; IBM; Meta; Avaloq.
- **Banking, asset management and insurance:** UBS; Zurich Insurance; Swiss Re; AXA; Swiss Life.
- **Life sciences and medtech:** Takeda; CSL Vifor; Roche Innovation Center Zurich; Molecular Partners; Sonova.
- **Engineering and industrial technology:** ABB; Hitachi Energy; Sulzer; Siemens Schweiz; Sensirion.
- **Consumer, trade and transport:** Lindt & Sprüngli; Migros; Coop; DKSH; Flughafen Zürich.

### Geneva, Switzerland
**Market scope:** Geneva / Canton of Geneva.  **Evidence source:** [Canton Geneva key-sector guide and International Geneva Who’s Who](https://www.ge.ch/en/teaser/entreprendre-geneve/key-sectors).
- **Commodity trading and shipping:** Trafigura; Mercuria; Gunvor; Vitol; Cargill International.
- **Life sciences, fragrance and chemicals:** Givaudan; DSM-Firmenich; OM Pharma; Debiopharm; Merck Serono.
- **Watchmaking and luxury:** Rolex; Patek Philippe; Richemont; Chopard; Vacheron Constantin.
- **International organisations and institutions:** United Nations Office at Geneva; World Health Organization; World Trade Organization; International Committee of the Red Cross; CERN.
- **Digital, audit and professional services:** Temenos; SGS; SICPA; ID Quantique; Lombard Odier.

### Basel, Switzerland
**Market scope:** Basel / Basel Area.  **Evidence source:** [Canton Basel-Stadt official important industries and companies](https://www.bs.ch/en/schwerpunkte/portrait/economie-et-arbeit/important-industries-and-companies).
- **Pharmaceuticals and biotechnology:** Roche; Novartis; Lonza; Bayer; BeOne Medicines.
- **Chemicals and agribusiness:** Syngenta; Clariant; BASF; CABB Group; Huntsman.
- **Logistics, trade and distribution:** DSV; DHL; Rhenus; Swiss Rhine Ports; Coop.
- **Financial services and insurance:** Bank for International Settlements; UBS; Helvetia Baloise Group; Pax; Sympany.
- **ICT, medtech and engineering:** Adobe; Unblu; Karakun; Endress+Hauser; Medartis.
  - **Location caution:** distinguish Basel city from Basel Area / Basel-Landschaft sites.

### Method for improving the 5-by-5 lists

For each sector, Claude should:
1. Check the relevant city/region investor agency, chamber, employer directory and official company location page.
2. Determine whether the company has a local establishment, office or material local workforce.
3. Record the exact municipality and source date.
4. Search for the company's public staff biographies and career / leadership pages.
5. Avoid ranking five companies as "the largest" unless an official ranking or comparable employment data actually supports that claim.
6. Replace weak location leads with better documented local employers.

## 3. LinkedIn Boolean search library

The trainer's rule is to keep wording constant and change only the LinkedIn Location filter when repeating searches across destination countries. Therefore, the ten queries below are deliberately shared across Spain, Portugal, France, Germany and Switzerland. The CSV companion repeats the ten strings for each target-country location filter and adds three experimental dialling-code versions per target country.

**Important:** These are search references only. Do not automate LinkedIn scraping or execute searches through a logged-in browser bot. Use only an authorised LinkedIn API/integration if one is actually available. The autonomous person-discovery engine must use permitted public-web sources, not depend on manual LinkedIn searches.

### Ten principal searches

**Search 1.**

```text
"lived in the UK" AND ("moved to" OR "relocated to" OR "now based in") AND (engineer OR "project manager" OR "IT manager" OR developer) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 2.**

```text
"worked in the UK" AND ("moved to" OR "relocated to" OR expatriate OR expat) AND (recruiter OR consultant OR "business development" OR sales OR marketing) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 3.**

```text
("ex-London" OR "formerly based in London" OR "previously lived in Britain" OR "moved from the UK") AND (hospitality OR "hotel manager" OR property OR construction OR operations) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 4.**

```text
("lived in Britain" OR "lived in England" OR "based in the UK") AND ("moved to" OR "relocated to" OR "based in") AND (healthcare OR education OR technology OR logistics) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 5.**

```text
("lived in the Republic of Ireland" OR "lived in Dublin" OR "lived in Cork") AND ("moved to" OR "relocated to" OR "now based in") AND (engineer OR consultant OR "project manager" OR technology) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 6.**

```text
("worked in Dublin" OR "worked in Cork" OR "worked in the Republic of Ireland") AND ("moved to" OR "relocated to" OR expatriate OR expat) AND (sales OR recruiter OR marketing OR hospitality OR operations) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 7.**

```text
("ex-Dublin" OR "formerly based in the Republic of Ireland" OR "moved from the Republic of Ireland" OR "previously lived in the Republic of Ireland") AND (manager OR founder OR director OR healthcare OR education) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 8.**

```text
("lived in the Netherlands" OR "lived in Holland" OR "woonde in Nederland") AND ("moved to" OR "relocated to" OR "now based in") AND (engineer OR technology OR consulting OR management) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 9.**

```text
"worked in Amsterdam" AND ("moved to" OR "relocated to" OR expat OR expatriate) AND (recruiter OR marketing OR finance OR logistics OR sales) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

**Search 10.**

```text
("ex-Amsterdam" OR "formerly based in the Netherlands" OR "verhuisd uit Nederland" OR "previously lived in Holland") AND (hospitality OR property OR healthcare OR "business development" OR operations) NOT ("financial advisor" OR "financial adviser" OR "independent financial adviser" OR IFA OR "wealth manager" OR "financial planner" OR "investment adviser" OR "asesor financiero" OR "asesor financiero independiente" OR "conseiller financier" OR "conseiller en gestion de patrimoine" OR Finanzberater OR Finanzplaner OR "financieel adviseur" OR vermogensadviseur OR "consultor financeiro" OR "consultor financeiro independente" OR "consultor financiero" OR "consulente finanziario" OR "consulente finanziario indipendente")
```

### Destination location filters

Use the same ten query wordings and change only the LinkedIn Location filter:

| Destination | Location filter |
|---|---|
| Spain | Spain, then city/metro filters Madrid, Barcelona, Málaga if needed |
| Portugal | Portugal, then Lisbon, Porto, Cascais |
| France | France, then Paris, Lyon, Nice |
| Germany | Germany, then Berlin, Munich, Frankfurt |
| Switzerland | Switzerland, then Zurich, Geneva, Basel |

### Experimental dialling-code variants

For the first three queries only, the CSV contains experimental variants with the destination calling code appended using `AND "+34"`, `AND "+351"`, `AND "+33"`, `AND "+49"` or `AND "+41"` as applicable. This method may return no result or irrelevant results. Do not treat it as a dependable filter or evidence of telephone availability.

### Query quality warning

The broad phrases `ex-London`, `formerly based`, `expat` and `now based in` can retrieve people who have not lived and worked in the same qualifying origin country. Use them for discovery, never as a qualification decision. A hit on "worked in London" does not prove residence in London.

## 4. Quick-win connector search strings

The CSV `Quick_Win_Connector_Searches.csv` contains 120 bilingual, city-specific search queries: eight connector types across all fifteen cities. They are designed to discover relevant organisations, not personal prospects. Use official firm websites and permitted directories to identify staff biographies later.

The eight categories are:
1. Recruiters / executive search.
2. Real estate and lettings.
3. Car sales and vehicle leasing.
4. Relocation and destination services.
5. Corporate event planners.
6. Five-star and luxury hotels.
7. International law firms.
8. English-speaking dental practices.

Do not assume a hotel general manager, recruiter, lawyer, dentist or estate agent is an expatriate. They qualify only after the normal evidence process.

## 5. Public places and directories by country

The CSV `Public_Organisations_and_Directories.csv` holds the full country-by-country register of 34 organisations, directories and professional-body leads. Key findings are summarised here.

### Spain

- **British Chamber of Commerce in Spain:** [official website](https://www.britishchamberspain.com/). Public site shows patron/corporate members, board/team, events, working groups and chamber office contacts in Barcelona, Madrid and Andalucía. The chamber's switchboard numbers are not prospect telephone numbers. Check whether member directory details beyond company names are open or member-only.
- **Dutch business networks:** the Dutch associations in Spain directory lists organisations including Dutch Business Club Madrid and De Kring Dutch Business Club Barcelona. Treat the directory as a lead to verify each club's current operation, website and access rules. It does not itself establish that a member is an eligible prospect.
- **Royal British Legion overseas branches:** branch locations and public branch contacts can help map local British communities, but this is a community network, not a professional employment directory.
- **Páginas Amarillas:** public Spanish business listings can include category, business address and phone. A business number is not automatically a named person's number. Verify terms before automated use.
- **Professional colleges:** regional bar, dental, medical and accountancy bodies may have professional registers. Check each body's public fields, update dates and commercial-use restrictions.

### Portugal

- **British-Portuguese Chamber of Commerce:** [BPCC](https://bpcc.pt/). Public information includes chamber, network and event information. The public directory access and personal contact availability were not independently confirmed during this pass because the site blocked direct access. Verify before automated collection.
- **Ireland Portugal Business Network:** [member directory](https://www.ireland-portugal.com/members). Public member pages include company and sector descriptions and in some cases named member biographies. The site explicitly directs users to its coordinator for personal contacts and introductions. Do not bypass this process or treat it as an unrestricted contact dump.
- **Dutch-Portuguese Chamber (CCPH):** [website](https://ccph.pt/). Organisation presence is identified; an open person-level directory was not confirmed. Check member pages and access terms.
- **Páginas Amarelas:** [business directory](https://www.paginasamarelas.pt/). Business search pages may carry phone numbers. They do not establish that a number belongs to a named individual.
- **Professional orders:** Ordem dos Advogados, Ordem dos Médicos Dentistas and other official orders can provide member-register information. Confirm the scope and permitted use of each register.

### France

- **Franco-British Chamber of Commerce & Industry:** [official website](https://francobritishchamber.com/en/). Public site shows board, team, regions, events, member navigation and a directory section. Detailed contact information may require membership. The chamber reports a programme of 50+ events per year; verify current regional chapter coverage.
- **British Community Committee of France:** [official website](https://www.britishinfrance.com/). Public network of member organisations includes business/professional, alumni, community and regional associations. This is an organisation directory, not a private individual directory.
- **PagesJaunes:** [professional directory](https://www.pagesjaunes.fr/). Searchable professional/business listings may expose office contact numbers. A private-person directory is different. Check terms and licensing carefully before automated use. Do not bulk-download pages absent permission.
- **Professional orders:** local bar associations, dental councils and accountancy bodies may expose practice details. A practice number is not a personal mobile.

### Germany

- **British Chamber of Commerce in Germany (BCCG):** [official website](https://bccg.de/en/). Public information describes around 600 members and 5,000 business contacts, with regional committees and events. The member directory is linked in site navigation, but access may be member-only. Focus on Berlin/Brandenburg, Bavaria and Rhine-Main regional committees.
- **German-British AHK / chamber directory:** [official chamber network](https://grossbritannien.ahk.de/). A searchable organisation/member directory has been surfaced. Company listings do not automatically provide individual names or phones.
- **Irish Business Network Germany:** [website](https://www.irishbusinessnetwork.de/). Local chapter/event activity has been identified around Berlin, Munich and Frankfurt; a publicly searchable person-level phone list was not verified.
- **Das Örtliche and Das Telefonbuch:** [Das Örtliche](https://www.dasoertliche.de/). Public telephone/business directories can expose company or individual numbers. Check terms and opt-outs and confirm the number's attribution. Do not bulk-scrape.
- **Professional chambers:** Bundesrechtsanwaltskammer and regional Rechtsanwaltskammern, Zahnärztekammern and Steuerberaterkammern. Verify access and contact-field rules region by region.

### Switzerland

- **British-Swiss Chamber of Commerce:** [BSCC](https://www.bscc.co.uk/). Public organisation, events and membership information. An open full person-level member directory with phone numbers was not verified.
- **Irish Business Network Switzerland:** [about and chapters](https://www.irishbusinessnetwork.ch/about). The network says it has 1,000+ professionals and four active chapters: Basel, Geneva, Lausanne and Zurich. Committee information is linked publicly; member contact details are not an open bulk directory.
- **local.ch:** [Swiss telephone search](https://www.local.ch/en/phone-number-search). Official page describes telephone-number lookup and more than 500,000 businesses. Listings may give business phone numbers, not an employee's direct number.
- **search.ch:** [telephone directory](https://search.ch/tel/index.php/). Official page displays around 1.9 million directory entries and a who/what/where/phone search. Inspect terms and developer access before using automation.
- **Genève internationale Who's Who:** [official organisation directory](https://www.geneve-int.ch/whoswho). Public directory of international organisations, NGOs, permanent missions and academic bodies. Useful for employer discovery, not a person-level contact list.
- **Professional registers:** FMH and cantonal bar/dental associations can expose practice or firm contacts. Check whether numbers are direct or general office.

### General directory rule

A public directory listing may be a business, clinic, law firm or central reception. Store `phone_attribution` separately from `phone_type`. Do not count a number toward the 1,000 unless the evidence reasonably connects it to the named person. Respect directory terms and any restrictions on automated reuse.

## 6. Events in the next three months

Exact window: **10 November 2026 to 10 February 2027**. Some events begin on 10 November itself. The CSV `Events_Nov2026_Feb2027.csv` contains the complete list and page status. The table below contains 69 event leads across the 15 city markets plus one additional Switzerland-wide opportunity in Davos. Some entries are professional-sector relevant, some are local market-discovery leads, and several require organiser or event-page revalidation before use.

| City | Event | Date | Organiser | Official event page | Speaker / exhibitor / attendee-list page and availability |
|---|---|---|---|---|---|
| Madrid | **Construtec / Veteco / Smart Doors / Piscimad** | 10–13 Nov 2026 | IFEMA MADRID | [Official page](https://www.ifema.es/en/calendar) | Official IFEMA calendar; detailed event pages and exhibitors vary by fair. Calendar confirms dates; check each fair page for exhibitor / agenda list. No attendee list verified. |
| Madrid | **Empack Madrid / Logistics & Automation** | 11–12 Nov 2026 | IFEMA MADRID | [Official page](https://www.ifema.es/en/calendar) | Official IFEMA calendar. Exhibitor / programme pages should be checked on event microsites; no attendee list verified. |
| Madrid | **Interihotel** | 17–19 Nov 2026 | Interihotel organiser, venue IFEMA Madrid | [Official page](https://www.ifema.es/en/calendar) | IFEMA calendar listing. Check official Interihotel programme and exhibitor directory; attendee list not verified. |
| Madrid | **FITUR 2027** | 20–24 Jan 2027 | IFEMA MADRID | [Official page](https://www.ifema.es/en/fitur/activities-schedule) | Official activities schedule and exhibitor catalogue. Schedule page says programme is forthcoming; official exhibitor catalogue/Liveconnect is available. No public attendee list verified. |
| Madrid | **Madrid Fusión Alimentos de España 2027** | 1–3 Feb 2027 | Madrid Fusión / IFEMA Madrid | [Official page](https://www.esmadrid.com/en/events-calendar) | Official Madrid tourism calendar; check event programme page. Calendar confirms event date. Verify organiser and speaker programme on event site before treating as final. |
| Madrid | **INTERGIFT 2027** | 3–6 Feb 2027 | IFEMA MADRID | [Official page](https://www.ifema.es/en/intergift/activities-schedule) | Official schedule and exhibitors catalogue. Programme marked forthcoming; exhibitor catalogue/Liveconnect is the public directory. No attendee list verified. |
| Madrid | **SIMO EDUCACIÓN 2026** | 11–13 Nov 2026 | IFEMA MADRID | [Official page](https://www.ifema.es/en/simo-educacion) | Official exhibitor catalogue, expo map and conference/workshop programme. Exhibitor catalogue and conference/workshop information are public; no attendee name list verified. |
| Madrid | **Accountex España 2026** | 18–19 Nov 2026 | IFEMA MADRID | [Official page](https://www.ifema.es/en/calendar) | Official IFEMA event listing; event-specific programme page to be checked. Calendar confirms dates; verify official agenda/speaker directory on event microsite. No attendee list verified. |
| Madrid | **Matelec and Genera 2026** | 24–26 Nov 2026 | IFEMA MADRID | [Official page](https://www.ifema.es/en/calendar) | Official IFEMA event listings; exhibitor and programme pages vary by fair. Dates confirmed by IFEMA calendar; inspect each fair microsite for exhibitor and conference lists. No attendee list verified. |
| Madrid | **C!Print Madrid 2027 and PMG Promogift 2027** | 12–14 Jan 2027 | IFEMA MADRID | [Official page](https://www.ifema.es/en/calendar/technology) | Official IFEMA calendar lists both events and technology category. Dates confirmed on IFEMA calendar; follow event pages for exhibitors and programme. No attendee list verified. |
| Barcelona | **EORTC-NCI-AACR Symposium 2026** | 18–20 Nov 2026 | EORTC, National Cancer Institute and American Association for Cancer Research | [Official page](https://www.firabarcelona.com/en/trade_show/) | Fira Barcelona calendar; follow official symposium programme. Official venue calendar confirms event dates; specialist scientific programme should be checked. No attendee list verified. |
| Barcelona | **AVEPA-SEVC Congress 2026** | 19–21 Nov 2026 | AVEPA / SEVC | [Official page](https://www.firabarcelona.com/en/trade_show/) | Fira Barcelona calendar and event programme. Venue calendar confirms dates; check congress programme and exhibitors. No attendee list verified. |
| Lisbon | **Lisboa Games Week 2026** | 19–22 Nov 2026 | Fundação AIP / FIL; verify event imprint | [Official page](https://fil.lisbonvenues.pt/en/calendar/) | FIL official venue calendar; follow event page for exhibitor and programme details. Venue calendar confirms date; confirm legal organiser and public programme. No attendee list verified. |
| Lisbon | **35th Congresso da Ordem dos Médicos Dentistas** | 19–21 Nov 2026 | Ordem dos Médicos Dentistas | [Official page](https://www.fil.pt/calendario-fil/) | FIL official events calendar; organiser event programme. Venue calendar confirms dates; check official congress programme. No attendee list verified. |
| Porto / Matosinhos | **Eléctrica 2026** | 18–21 Nov 2026 | Exponor | [Official page](https://exponor.pt/en/calendario/) | Official Exponor event calendar and exhibitor information. Calendar confirms event dates; check exhibitors/programme. No attendee list verified. Venue is Exponor in Matosinhos, Porto metro, not Porto municipality. |
| Porto / Matosinhos | **360 Tech Industry 2026** | 26–27 Nov 2026 | Exponor; legal organiser to verify | [Official page](https://exponor.pt/en/calendario/) | Official Exponor calendar. Calendar lists event date and industrial technology theme; verify organiser and programme. No attendee list verified. |
| Porto / Matosinhos | **INFORCE 2027** | 28–30 Jan 2027 | Exponor / Profair; verify official event imprint | [Official page](https://exponor.pt/en/calendario/) | Official Exponor calendar. Calendar lists the event and dates; verify the organiser and exhibitor list on the event page. |
| Paris | **Supply Chain Event 2026** | 1–2 Dec 2026 | RX France; verify event imprint | [Official page](https://parisjetaime.com/eng/convention/article/fairs-and-trade-shows-a1194) | Paris Convention Bureau current trade-show calendar; follow organiser programme. Official Paris Convention Bureau lists date and business focus; speaker/exhibitor page to be checked. No attendee list verified. |
| Paris | **SIMI 2026** | 8–10 Dec 2026 | Infopro Digital; verify event imprint | [Official page](https://parisjetaime.com/eng/convention/article/fairs-and-trade-shows-a1194) | Paris Convention Bureau calendar; official event programme/exhibitor page. Calendar describes real-estate investment trade show and dates; verify official exhibitor/programme directory. No attendee list verified. |
| Paris | **Open Source Experience 2026** | 9–10 Dec 2026 | Event organiser to verify from official imprint | [Official page](https://parisjetaime.com/eng/convention/article/fairs-and-trade-shows-a1194) | Paris Convention Bureau trade-show calendar; official event agenda. Calendar lists event dates and professional IT audience; organiser and speaker list require confirmation. |
| Paris | **Maison&Objet January 2027** | 14–18 Jan 2027 | SAFI | [Official page](https://parisjetaime.com/eng/convention/article/fairs-and-trade-shows-a1194) | Paris Convention Bureau trade-show calendar; Maison&Objet exhibitor directory/programme. Calendar confirms date; check official exhibitor and programme pages. No attendee list verified. |
| Paris | **Cosmet’Agora 2027** | 12–13 Jan 2027 | Société Française de Cosmétologie; verify organiser | [Official page](https://parisjetaime.com/eng/convention/article/fairs-and-trade-shows-a1194) | Paris Convention Bureau trade-show calendar; official event programme. Calendar confirms dates; verify organiser, exhibitor and speaker information. No attendee list verified. |
| Berlin | **Global Forum for Food and Agriculture (GFFA) 2027** | 13–15 Jan 2027 | Federal Ministry of Agriculture, Food and Regional Identity / GFFA organisers; verify exact organiser | [Official page](https://www.messe-berlin.de/en/events/event-calendar) | Messe Berlin event calendar; official GFFA programme. Calendar confirms Berlin event dates; programme and participant information should be checked on official GFFA page. No attendee list verified. |
| Berlin | **Grüne Woche 2027** | 15–24 Jan 2027 | Messe Berlin | [Official page](https://www.gruenewoche.de/en/visit/our-exhibitors) | Official exhibitor directory, which is online and updated regularly. Exhibitor directory public; no attendee list verified. |
| Berlin | **Fuels of the Future 2027** | 18–19 Jan 2027 | Conference organiser to verify from official event page | [Official page](https://www.messe-berlin.de/en/events/event-calendar) | Messe Berlin calendar; official conference programme. Calendar confirms date and venue; verify organiser and programme. No attendee list verified. |
| Barcelona | **IBTM World 2026** | 17–19 Nov 2026 | RX | [Official page](https://www.ibtmworld.com/en-gb/show-agenda/speakers.html) | Public conference speaker directory (73 speaker entries shown) and event agenda. Speaker page publicly available; no attendee list verified. |
| Barcelona | **Tech Spirit Barcelona 2026** | 2–3 Dec 2026 | Tech Barcelona | [Official page](https://techspirit.barcelona/agenda) | Official agenda with sessions and programme. Speaker/session page is public; no attendee list verified. |
| Barcelona | **ICE Barcelona 2027** | 18–20 Jan 2027 | WorldGaming (formerly Clarion Gaming) | [Official page](https://www.icegaming.com/) | Official exhibitor list and event information. Exhibitor directory is public; verify conference agenda. No attendee list verified. |
| Barcelona | **iGB Affiliate Barcelona 2027** | 19–20 Jan 2027 | Clarion Gaming / WorldGaming group | [Official page](https://barcelona.igbaffiliate.com/speakers) | Official speaker directory. Speakers page public; no attendee list verified. |
| Barcelona | **Integrated Systems Europe (ISE) 2027** | 2–5 Feb 2027 | Integrated Systems Events; AVIXA and CEDIA | [Official page](https://www.iseurope.org/content-programme) | Official content programme, exhibitor list and show information. Public speaker programme and exhibitor list; no attendee list verified. |
| Barcelona | **Barcelona Wine Week 2027** | 8–10 Feb 2027 | Fira de Barcelona | [Official page](https://www.barcelonawineweek.com/en/activities-programme/) | Official activity programme and speakers page. Public speakers/activity programme; 2027 goals page publishes expected exhibitor and professional visitor totals, not an attendee name list. |
| Málaga | **SIMED Mediterranean Real Estate Exhibition** | 12–14 Nov 2026 | FYCMA | [Official page](https://simed.fycma.com/) | Official programme, participant list, protagonists page and exhibitor map. Participant and protagonist pages are public; distinguish exhibitors/participants from attendee list. |
| Málaga | **Andalucía TRADE Global 2026** | 17–18 Nov 2026 | Andalucía TRADE | [Official page](https://fycma.com/agenda/?lang=en) | FYCMA official calendar. Calendar confirms date and organiser context. Check event microsite for programme; no public attendee list verified. |
| Málaga | **Málaga Sun&Tech by Alhambra Venture** | 18–19 Nov 2026 | Alhambra Venture / FYCMA venue | [Official page](https://fycma.com/agenda/?lang=en) | FYCMA official calendar. Calendar confirms event; check event-specific page for speaker list. No attendee list verified. |
| Málaga | **Talent Land España 2026** | 24–26 Nov 2026 | Talent Land España / FYCMA venue | [Official page](https://fycma.com/agenda/?lang=en) | FYCMA official calendar. Calendar confirms date; check programme / speaker list on event page. No attendee list verified. |
| Lisbon | **Web Summit 2026** | 9–12 Nov 2026 | Web Summit | [Official page](https://websummit.com/schedule/date/2026-11-09/) | Public session schedule with talks, masterclasses and meetups. Schedule and speaker pages public. Event began before the research start date and runs through 12 Nov. No attendee list verified. |
| Lisbon | **IPBN Conversation with a Leader** | 17 Nov 2026 | Ireland Portugal Business Network | [Official page](https://www.ireland-portugal.com/events/) | IPBN events page; verify the 17 Nov listing and event-specific details. Event listing should be checked for programme and attendance visibility; no public attendee list verified. |
| Porto / Matosinhos | **Concreta 2026** | 18–21 Nov 2026 | Exponor | [Official page](https://exponor.pt/concreta/) | Official programme and exhibitor list. Public exhibitor directory; official event copy describes qualified networking. No attendee list verified. Venue is Exponor in Matosinhos, Porto metro area, not Porto municipality. |
| Cascais | **No separate major B2B event independently verified in this pass** | 10 Nov 2026–10 Feb 2027 | Not established | [Official page](https://www.cascais.pt/) | Municipal event/business pages require further date-specific checking. Use Lisbon metropolitan events where relevant, but do not relabel a Lisbon event as taking place in Cascais. |
| Paris | **HEAVENT Paris 2026** | 17–19 Nov 2026 | Weyou Group | [Official page](https://www.heavent-paris.com/en/visit) | Official visitor page and exhibitor information. Exhibitor information public; no attendee list verified. |
| Paris | **Tech Show Paris 2026** | 18–19 Nov 2026 | Tech Show Paris organiser; verify legal organiser on event imprint | [Official page](https://www.techshowparis.fr/en/liste-de-nos-exposants) | Public exhibitor directory. Exhibitor list public; no attendee list verified. |
| Paris | **Tech for Retail 2026** | 30 Nov–1 Dec 2026 | Tech for Retail | [Official page](https://www.visit.techforretail.com/en/) | Public speakers, programme and exhibitor information. Speaker and conference pages public; no attendee name list verified. |
| Paris | **TRUSTECH 2026** | 1–3 Dec 2026 | TRUSTECH organiser; verify legal organiser on event imprint | [Official page](https://www.trustech-event.com/en/press-area/press-releases/highlights-2026) | Official event overview and programme announcements. Event page cites speakers and conferences; separate public speaker list should be checked. No attendee list verified. |
| Paris | **Paris Packaging Week 2027** | 3–4 Feb 2027 | Easyfairs / Paris Packaging Week | [Official page](https://www.parispackagingweek.com/en/) | Official exhibitor and conference information. Exhibitor list and expert speaker/conference pages; no attendee list verified. |
| Lyon | **Sirha Lyon 2027** | 21–25 Jan 2027 | GL events / Sirha Lyon | [Official page](https://www.sirha-lyon.com/en) | Official exhibitor, innovation and event programme portal. Public event information and exhibitor details; use Sirha Connect/programme pages for sessions. No attendee list verified. |
| Nice | **Salon IBT Côte d’Azur** | 17 Nov 2026 | Co-organised by CCI Nice Côte d’Azur, UIMM Côte d’Azur & Corse, Fédération BTP Alpes-Maritimes, PRODAROM and UPE06 | [Official page](https://business.nicecotedazur.org/salon-ibt-cote-dazur-rendez-vous-le-17-novembre-a-lallianz-riviera/) | Official event page and programme information. The official page confirms B2B focus and co-organisers. No public attendee list verified. |
| Berlin | **DigiFin26** | 10 Nov 2026 | Bitkom and Payment & Banking | [Official page](https://www.visitberlin.de/en/events-kongresskalender-berlin) | VisitBerlin event listing; follow DigiFin event page. Date is the first day of the research window. Event page indicates decision-maker audience; no attendee list verified. |
| Berlin | **NextTruck 2026** | 11–12 Nov 2026 | NextTruck organiser; verify legal organiser on event site | [Official page](https://www.next-truck.eu/) | Official event page. Event listing public; confirm programme/exhibitor page. No attendee list verified. |
| Berlin | **AI Engineering Summit** | 16–20 Nov 2026 | AI Engineering Summit organiser; verify legal entity on event imprint | [Official page](https://ai-engineering-summit.de/) | Official event page and programme. Agenda/public sessions should be checked. No attendee list verified. |
| Berlin | **Digital Health Conference 2026** | 24 Nov 2026 | Bitkom | [Official page](https://health-conference.de/) | Official event page; VisitBerlin event listing. Public event information; speaker/agenda details need checking. No attendee list verified. |
| Berlin | **Fruit Logistica 2027** | 3–5 Feb 2027 | Messe Berlin | [Official page](https://www.fruitlogistica.com/en/exhibitors) | Official exhibitor directory. Exhibitor directory public; no attendee list verified. |
| Munich | **electronica 2026** | 10–13 Nov 2026 | Messe München | [Official page](https://tickets.messe-muenchen.de/MM-SHOP/Events) | Official event overview and exhibitor / conference pages. Dates confirmed on organiser event portal; check event page for exhibitor directory. |
| Munich | **SEMICON Europa 2026** | 10–13 Nov 2026 | SEMI Europe | [Official page](https://www.semi.org/en/semicon-europa) | Official event and programme pages. Dates confirmed; public exhibitors/conference pages should be checked. |
| Munich | **BAU 2027** | 11–15 Jan 2027 | Messe München | [Official page](https://bau-muenchen.com/en/) | Official event and exhibitor information. Exhibitor directory and supporting programme should be checked; no attendee list verified. |
| Munich | **f.re.e 2027** | 10–14 Feb 2027 | Messe München | [Official page](https://tickets.messe-muenchen.de/MM-SHOP/Events) | Official event overview. Only 10 February falls within the exact three-month window; most of the event is outside it. |
| Frankfurt | **This Is Marketing** | 11–12 Nov 2026 | Fastlane Marketing | [Official page](https://www.messefrankfurt.com/frankfurt/en/press/press-releases/2026/guest-events.html) | Messe Frankfurt official event announcement. Event description and expected scale public; follow organiser for programme/speaker directory. |
| Frankfurt | **Fi Europe 2026** | 17–19 Nov 2026 | Informa | [Official page](https://www.messefrankfurt.com/frankfurt/en/press/press-releases/2026/guest-events.html) | Messe Frankfurt official announcement; event site for exhibitor list. Exhibitor list and conference programme should be checked. No attendee list verified. |
| Frankfurt | **Formnext 2026** | 17–20 Nov 2026 | Mesago Messe Frankfurt GmbH | [Official page](https://formnext.mesago.com/frankfurt/en.html) | Official event, exhibitor and programme pages. Public exhibitors and conference programme; no attendee list verified. |
| Frankfurt | **Impact Festival 2026** | 25–26 Nov 2026 | TechQuartier | [Official page](https://impact-festival.earth/) | Official festival programme and speaker information. Official page advertises speaker and solution-provider programme; no attendee list verified. |
| Frankfurt | **Heimtextil 2027** | 12–15 Jan 2027 | Messe Frankfurt | [Official page](https://heimtextil.messefrankfurt.com/frankfurt/en.html) | Official event programme and exhibitor search. Programme and exhibitor directory public; no attendee list verified. |
| Frankfurt | **Ambiente / Christmasworld / Creativeworld** | 29 Jan–2 Feb 2027 (Creativeworld to 1 Feb) | Messe Frankfurt | [Official page](https://www.messefrankfurt.com/frankfurt/en.html) | Official fair calendar, programmes and exhibitor directories. Public exhibitor and programme pages; no attendee list verified. |
| Zurich | **Berufsmesse Zürich** | 17–21 Nov 2026 | MCH Exhibitions & Events GmbH and KMU- und Gewerbeverband Kanton Zürich | [Official page](https://www.messe-zurich.com/en/events) | Official Messe Zürich event calendar. Event page public; not a strong international professional networking event, but local employers may exhibit. |
| Zurich | **Data Center Nation Zurich** | 25 Nov 2026 | Data Center Nation | [Official page](https://www.messe-zurich.com/en/events) | Official Messe Zürich calendar; event website for agenda. Check conference speaker/agenda page; no attendee list verified. |
| Zurich | **LOGISTICS & AUTOMATION Schweiz / EMPACK Schweiz** | 27–28 Jan 2027 | Easyfairs Switzerland | [Official page](https://www.messe-zurich.com/en/events) | Official Messe Zürich calendar; event pages for programme/exhibitors. Exhibitor directories should be checked; no attendee list verified. |
| Zurich | **FESPO & Golfmesse Zürich** | 4–7 Feb 2027 | BERNEXPO AG | [Official page](https://www.messe-zurich.com/en/events) | Official Messe Zürich event calendar. Exhibitor information may be public; no attendee list verified. |
| Geneva | **Geneva Health Forum Conference 2026** | 10–12 Nov 2026 | Geneva Health Forum / Institute of Global Health, University of Geneva | [Official page](https://conference2026.genevahealthforum.com/agenda-tuesday-10-november/) | Official daily agenda for 10–12 November. Detailed session agenda public; no attendee list verified. Event began on the research start date. |
| Geneva | **Global Framework on Chemicals First International Conference** | 16–20 Nov 2026 | United Nations Environment Programme (UNEP) | [Official page](https://www.unep.org/global-framework-chemicals/international-conference-1) | Official UNEP event page and programme. Check official session programme; no public attendee list verified. |
| Basel | **Basel Coin Fair** | 7 Feb 2027 | Event organiser to verify via Congress Center Basel | [Official page](https://www.mqbasel.ch/en/events) | Official MesseQuartier Basel calendar. Calendar confirms date. It is a collector/coin event, not a priority professional networking event; no attendee list verified. |
| Davos (outside target-city list) | **World Economic Forum Annual Meeting 2027** | 18–22 Jan 2027 | World Economic Forum | [Official page](https://www.davos.ch/en/experience/events/world-economic-forum-annual-meeting-2027) | Davos official event page and WEF site. Major international business gathering; public programme may exist, but attendee list is restricted/not verified. Davos is an additional national opportunity, not a selected target city. |

**Event validation rule for Claude:** Re-check every event's date and organiser before using the page. The list is a research lead, not permission to collect attendees. Use public programme/speaker/exhibitor pages only as permitted. Do not harvest speaker or attendee names as prospects merely because they appear on event pages.

## 7. Public web search plan for individual discovery

Run the following query families through the free/approved search tools already available in the Claude Code environment. Search engines interpret syntax differently, so adapt each query to the chosen provider instead of assuming LinkedIn Boolean works on the open web.

### A. Previous UK residence and current destination

- `"lived in the UK" "now based in" Madrid professional biography`
- `"lived in London" "relocated to" Barcelona executive biography`
- `"moved from the UK" "based in" Málaga company biography`
- `"former UK resident" Spain business founder biography`
- `"spent several years in London" "based in" Lisbon professional`
- `"previously lived in the UK" Portugal company director biography`

### B. Previous Republic of Ireland residence and current destination

- `"lived in Ireland" "now based in" Madrid professional`
- `"lived in Dublin" "relocated to" Barcelona founder`
- `"moved from Ireland" "based in" Lisbon professional biography`
- `"previously based in Dublin" France company biography`
- `"spent years in Ireland" "now based in" Germany executive`

### C. Previous Netherlands residence and current destination

- `"lived in the Netherlands" "now based in" Spain professional`
- `"lived in Amsterdam" "relocated to" Portugal executive`
- `"moved from the Netherlands" "based in" France founder`
- `"previously based in Amsterdam" Germany company biography`
- `"woonde in Nederland" verhuisd naar Spanje professional`

### D. Candidate enrichment searches

For a discovered candidate, run separate searches for:
- Exact full name + previous employer + city.
- Exact full name + prior role + dates.
- Exact full name + "lived in" / "moved to" / "based in" + origin country.
- Exact full name + current employer + current city.
- Exact full name + phone / contact / direct / mobile / office.
- Exact full name + LinkedIn, using only results and pages that are permitted to access.

Do not fill the spreadsheet from snippets alone. Open the source, store the page URL and extract the specific text supporting each fact.

## 8. Research channels and priorities

### Priority 1: Bilateral business chambers and Irish/Dutch business networks

Reason: concentrated cross-border business exposure, professional events, member organisations, employer names and occasionally professional biographies. Start with British Chamber of Commerce in Spain, IPBN in Portugal, Franco-British Chamber in France, BCCG in Germany, BSCC and Irish Business Network Switzerland.

### Priority 2: International employer and technology-park directories

Reason: large employer networks, named organisations, public staff pages, and opportunities to discover current and former employees. Strong starting points include Málaga TechPark, Porto's InvestPorto ecosystem, Berlin's Top 200 employers, Munich's industry pages, Frankfurt's sector clusters, and Geneva's International Geneva Who's Who.

### Priority 3: Professional firms and relocation / property connectors

Reason: businesses often serve internationally mobile professionals. Discover firm websites and management biographies first. Do not assume an employee is an expat because the firm serves expats.

### Priority 4: Official professional registers and public business directories

Reason: potential direct office numbers, current occupations and locality. These sources often expose firms or practice phones rather than the individual's mobile. Keep phone attribution graded separately.

### Priority 5: Event exhibitor and speaker programmes

Reason: public programmes and exhibitor directories can identify organisations, brands and professional ecosystems. Do not use attendee lists that are private or collect named speakers as prospects without independently proving all criteria.

## 9. Daily autonomous schedule and scale controls

Claude should continue the pipeline in resumable batches until **1,000 countable Grade A-D records** have been accepted. The target is not 42. Do not set a daily count based on assumptions.

Recommended operating cycle:

1. Check source register and avoid repeated queries.
2. Choose the highest-yield unsearched source and city.
3. Discover candidates in batches.
4. Enrich with separate origin-residence, origin-employment, current-residence, occupation and phone searches.
5. Find a permitted LinkedIn profile URL.
6. Grade each evidence criterion independently.
7. Apply deduplication and hard gates.
8. Add eligible records to the database with source snapshots/extracts.
9. Produce source yield and cost/usage measurements.
10. Persist a checkpoint before ending a session.

Track:
- Candidates discovered.
- Candidates with origin-residence support.
- Candidates with qualifying prior employment (employer, city and dates).
- Candidates with current-residence support.
- Candidates with a clear current occupation.
- Candidates with public phone numbers.
- Candidates with moderate or strong phone attribution.
- Candidates with LinkedIn URLs.
- Grades A, B, C and D.
- ASK, REJECT and DUPLICATE.
- Source failures and access restrictions.
- Search requests/credits consumed, where visible.

At 1,000 countable A-D records, stop, deduplicate, verify exports and report. Do not continue to 1,500 or 2,000 unless the user specifies a new target.

## 10. Uncertainty and verification register

The following are not resolved by this PLAN-stage search and must remain visible:

1. **City-level company rankings:** Comparable official top-five company rankings were not found for all 15 target cities and five industries. Employer lists above are significant research seeds, not a verified ranking. Claude must not call them "the five largest" unless it finds comparable employment data.
2. **Cascais versus Lisbon metro:** Many employers serve the Cascais market from Lisbon or Oeiras. Confirm municipality and workplace for each employer and candidate.
3. **Nice versus wider Côte d'Azur:** Several relevant companies are based in Cannes, Grasse, Carros or Sophia Antipolis, not Nice city. Preserve the actual municipality.
4. **Porto event venue:** Exponor is in Matosinhos, not Porto municipality. Store the actual venue locality and metro tag.
5. **Chamber directories:** Access levels can change. BCCG, BPCC, CCPH, BSCC and Franco-British Chamber should be checked directly for current member-directory visibility and terms. A public list of member companies does not prove personal phone numbers are published.
6. **IPBN Portugal personal contacts:** The website says personal contacts are obtained by contacting its coordinator for an introduction. Do not bypass this.
7. **Telephone directories:** Páginas Amarillas, PagesJaunes, Das Örtliche, Das Telefonbuch, local.ch and search.ch may show business or private phone numbers, but terms and commercial/automated use must be checked. A published business line is not automatically an individual's number.
8. **Event attendee lists:** No public attendee lists were verified for the events in this pack. Some publish speakers, exhibitors, programmes or participant directories. These are different things.
9. **Paris event organisers:** For Tech Show Paris and TRUSTECH, confirm the legal organiser from the official event imprint before entering the organiser field as final.
10. **Berlin event organisers:** For NextTruck and AI Engineering Summit, confirm the organiser's legal entity from the official event pages. VisitBerlin's calendar is a discovery source, not necessarily the organiser.
11. **Málaga event organisers:** FYCMA's calendar confirms SIMED and other dates. For co-organised events, verify the full organiser and programme on their own event pages.
12. **Current event programmes:** IFEMA pages for FITUR and INTERGIFT indicated that activity programmes were still forthcoming. Re-check before treating speaker pages as published.
13. **No standalone Cascais B2B event verified:** This pass did not identify a separate major Cascais business event within the date window. Check the municipality's own event calendar and use Lisbon-region events without relabelling their location.
14. **No major Basel business fair verified in window:** One Basel Coin Fair appeared in the venue calendar, but it is lower priority. Continue checking local chamber and industry calendars rather than assuming no events exist.
15. **Residence evidence quality:** The requested lower evidence threshold is implemented through grades. A weak residence indicator must still be a real source-based reason, not an inference from employer address, university attendance, an old search snippet or a registered office.
16. **Employment dates:** The user's original brief requires employer, city and dates. If any are missing, do not treat employment as fully qualifying. Use the prescribed ASK/grade handling.
17. **Same-origin-country rule:** The supplied autonomous master prompt interprets the requirement as previous residence and employment in at least one same qualifying origin country. If the evidence only shows residence in one origin country and employment in a different one, mark ASK rather than combine them.
18. **LinkedIn URLs:** A usable LinkedIn profile URL is required for the 1,000 countable working list under the current master prompt. Do not invent one. Missing URLs stay in the non-counting reserve.
19. **No paid search provider:** Claude must first inspect its existing WebSearch/WebFetch/MCP tools and permitted free access. Do not create a paid Brave/Tavily account or incur usage-based charges without explicit permission.
20. **Compliance approval:** This pack does not authorise person-level collection. The firm's compliance approval must be recorded before collecting identifiable prospect data.

## 11. Files in this research pack

- `Claude_Code_PLAN_Research_Pack.md`: this narrative research pack.
- `LinkedIn_Search_Library.csv`: 50 base-query/location combinations plus 15 experimental dialling-code variants (65 rows total).
- `Quick_Win_Connector_Searches.csv`: 120 bilingual city/category-specific organisation discovery queries.
- `Public_Web_Research_Queries.csv`: 45 city/origin-specific automated web discovery queries.
- `City_Industry_Employer_Seeds.csv`: 375 company/organisation research seed rows across 15 cities.
- `Events_Nov2026_Feb2027.csv`: event leads for the next three months with organiser, dates, official page and list availability notes.
- `Public_Organisations_and_Directories.csv`: 34 chamber, network, directory and professional-body leads with public/not-public checks.

**Final instruction to Claude:** treat this pack as a starting source register. Re-verify facts before use, update dates and access conditions, do not treat company leads or event pages as individual prospect evidence, and continue the autonomous research process until 1,000 countable Grade A-D prospects have been accepted or the permitted research sources have been exhausted.
