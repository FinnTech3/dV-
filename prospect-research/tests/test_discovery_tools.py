"""Synthetic tests for the newer discovery tools. No real people, no network."""
from __future__ import annotations

from pipeline.tools import firmcrawl, newsmine, osmseed, snowball

PAGE = """<html><body><main><h1>Dr Example Person</h1>
<p>Professor of Testing. Tel <a href="tel:+41 44 123 45 67">+41 44 123 45 67</a></p>
<p>2010-2013 Postdoctoral Fellow, University of Oxford. PhD, University of Cambridge, 2008.</p>
<p>She is a member of a learned society in London.</p>
<a href="https://www.linkedin.com/in/example-person-0001">LinkedIn</a></main></body></html>"""


def test_academic_career_line_is_recognised_but_study_only_is_not():
    r = firmcrawl.extract("https://uni.example/people/dr-example", PAGE)
    assert r["name"] == "Dr Example Person" and r["tels"][0]["region"] == "CH"
    assert r["origin"] == "GB" and "Postdoctoral Fellow" in r["sentence"]       # the PhD-only line and the society line are not chosen
    assert r["linkedin"] == "https://www.linkedin.com/in/example-person-0001"


def test_osm_host_filter_drops_platforms_and_keeps_firms():
    assert osmseed.host_of("https://www.facebook.com/somefirm") is None
    assert osmseed.host_of("doctolib.fr/x") is None
    assert osmseed.host_of("http://www.kanzlei-example.de/kontakt") == "www.kanzlei-example.de"
    assert osmseed.host_of("not a url") is None


def test_snowball_label_replaces_generic_anchor_text():
    assert snowball.label_for("www.example-law.ch", "Zur Webseite") == "Example Law"
    assert snowball.label_for("www.example-law.ch", "Example & Partner AG") == "Example & Partner AG"


def test_announcement_miner_needs_name_origin_office_and_a_move_and_ignores_client_news():
    names = {"Alex Sample": [{"url": "u"}]}
    good = "Alex Sample relocates from our London office to the Frankfurt team as partner."
    client = "Alex Sample advised the client on a merger announced by the London office."
    assert newsmine.extract_moves(good, names)[0]["name"] == "Alex Sample"
    assert newsmine.extract_moves(client, names) == []
    assert newsmine.extract_moves("Someone Else relocates from our London office to Madrid.", names) == []   # unknown names are never guessed
    assert newsmine.SLUG.search("alex-sample-relocates-to-frankfurt") and not newsmine.SLUG.search("transfer-pricing-update")


def test_title_taken_from_page_element_not_from_page_title_fragment():
    from pipeline.tools import firmcrawl
    page = ('<head><meta property="og:title" content="Synthetic Person | Example Firm" /></head><body><h1>Synthetic Person</h1>'
            '<h4><span class="positions"><span class="position">Counsel</span></span></h4><p>T +49 69 000000</p></body>')
    assert firmcrawl.extract("https://example.com/p", page)["role"] == "Counsel"
    bare = '<h1>Synthetic Person</h1><p>Welcome to our firm and the people who make it work every day.</p>'
    assert firmcrawl.extract("https://example.com/q", bare)["role"] == ""          # no stated title: stays blank, never invented


def test_refresh_titles_upgrades_in_place_and_keeps_linkedin(conn, settings, tmp_path):
    import sqlite3
    from pipeline.tools import discover, firmcrawl
    from tests.conftest import make
    settings["waivers"] = {}
    cand = make(occupation="Professional at Example Firm (title not stated on profile)", employer="Example Firm",
                levels={"occupation": "MODERATE"}, external_id="firm:example.com:synthetic-slug")
    res = discover.ingest_candidate(conn, cand, settings, synthetic=True)
    crawl = sqlite3.connect(str(tmp_path / "crawl.sqlite")); crawl.row_factory = sqlite3.Row
    crawl.execute("CREATE TABLE pages (host TEXT, slug TEXT, role TEXT, name TEXT)")
    crawl.execute("INSERT INTO pages VALUES ('example.com','synthetic-slug','Counsel','Synthetic Person')")
    out = discover.refresh_titles(conn, settings, crawl)
    assert [o["uuid"] for o in out] == [res["uuid"]]
    row = conn.execute("SELECT occupation, occupation_level, linkedin_url FROM persons WHERE uuid=?", (res["uuid"],)).fetchone()
    assert row["occupation"] == "Counsel, Example Firm" and row["occupation_level"] == "STRONG" and row["linkedin_url"]
    crawl.execute("UPDATE pages SET role='Example Firm'")                     # a firm name is not a title
    assert discover.refresh_titles(conn, settings, crawl) == []


def test_linkprobe_keeps_person_style_links_and_drops_service_pages():
    from pipeline.tools import linkprobe
    page = ('<a href="/people/jane-example">Jane Example</a><a href="/people/contact-persons">Contacts</a>'
            '<a href="/people/page.pdf">x</a><a href="https://other.example.org/people/john-example">elsewhere</a>'
            '<a href="/people/?page=2">next</a>')
    got = linkprobe.links(page, "https://example.com/people/", "example.com")
    urls = [u for u, _ in got]
    assert "https://example.com/people/jane-example" in urls                      # same host
    assert not any("other.example.org" in u or u.endswith(".pdf") for u in urls)      # never leaves the host, skips documents
    assert linkprobe.NOT_PERSON.search("/people/contact-persons") and not linkprobe.NOT_PERSON.search("/people/jane-example")


def test_national_format_number_read_against_site_country_and_fax_ignored():
    from pipeline.tools import firmcrawl
    page = '<h1>Synthetic Person</h1><p>Tel. 02 2399 4567 Fax 02 2399 4568 Order 12345678</p>'
    tels = firmcrawl.extract("https://www.example.it/p", page)["tels"]
    assert [t["e164"] for t in tels] == ["+390223994567"] and tels[0]["region"] == "IT"
    assert firmcrawl.extract("https://www.example.com/p", page)["tels"] == []         # no country domain: no guess
