from pipeline.tools import teamparse

PAGE = """<html><body><header><a href="tel:+34 900 111 222">+34 900 111 222</a></header><main><h1>Our Team</h1>
<h3>Alex Sample</h3><p>Founder. Alex moved to Spain in 2010 after working for ten years in London as an engineer.
Call <a href="tel:+34 612 345 678">+34 612 345 678</a>.</p>
<h3>Sam Example</h3><p>Office manager. Born in Valencia. Reach the office on +34 900 111 222.</p>
<h3>Contact us</h3><p>Write to us.</p></main></body></html>"""


def test_name_heuristic():
    assert teamparse.looks_like_name("Alex Sample") and teamparse.looks_like_name("Dr. Jan van der Berg")
    assert not teamparse.looks_like_name("Our Team") and not teamparse.looks_like_name("Contact us") and not teamparse.looks_like_name("Call 612 345 678")


def test_each_person_gets_only_their_own_number_and_shared_numbers_are_dropped():
    r = {x["name"]: x for x in teamparse.extract_team("https://firm.example/team", PAGE)}
    assert set(r) == {"Alex Sample", "Sam Example"}                      # 'Our Team' and 'Contact us' are not people
    assert [t["e164"] for t in r["Alex Sample"]["tels"]] == ["+34612345678"]
    assert r["Alex Sample"]["origin"] == "GB" and "London" in r["Alex Sample"]["sentence"]
    assert r["Sam Example"]["tels"] == []                                # the office number also appears in the header
