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
