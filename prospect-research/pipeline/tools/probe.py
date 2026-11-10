"""Probe organisation sites: robots.txt, sitemaps and how many people-profile URLs they expose."""
from __future__ import annotations
import re, sys, urllib.request, urllib.robotparser, gzip
UA = "prospect-research-bot/0.1 (supervised training exercise; respects robots.txt)"
def get(url, limit=30_000_000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        data = r.read(limit)
        if url.endswith(".gz") or data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        return r.status, data.decode("utf-8", "replace")
def probe(host, pat=r"/(people|lawyers|professionals|team|our-people|experts|anwaelte|avocats|personen|en/people|profiles?)/"):
    out = {"host": host}
    try:
        st, robots = get(f"https://{host}/robots.txt")
    except Exception as e:
        return {**out, "error": f"robots: {e}"[:90]}
    rp = urllib.robotparser.RobotFileParser(); rp.parse(robots.splitlines())
    maps = re.findall(r"(?im)^sitemap:\s*(\S+)", robots) or [f"https://{host}/sitemap.xml"]
    urls, seen, queue = set(), set(), list(maps)
    while queue and len(seen) < 60:
        m = queue.pop(0)
        if m in seen: continue
        seen.add(m)
        try: _, xml = get(m)
        except Exception as e:
            out.setdefault("map_errors", []).append(str(e)[:50]); continue
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
        if "<sitemapindex" in xml: queue += [l for l in locs if re.search(r"(people|lawyer|profess|team|person|profile|bio|sitemap)", l, re.I)] or locs[:10]
        else: urls |= {l for l in locs if re.search(pat, l)}
    allowed = [u for u in urls if rp.can_fetch(UA, u)]
    out.update(sitemaps=len(seen), people_urls=len(urls), allowed=len(allowed), sample=sorted(allowed)[:2])
    return out
def probe_urls(host, pat=r"/(people|lawyers|professionals|team|our-people|experts|profiles?|consultants?|advisors?|attorneys(-professionals/profile)?|bio-broker|agents?|anwaelte(/detail)?|avocats?|person|faculty(-research)?(/faculty)?(/faculty-directory)?(/[a-z-]+)?)/[^/?]+"):
    """All robots-allowed people-profile URLs listed in a host's sitemaps."""
    _, robots = get(f"https://{host}/robots.txt")
    rp = urllib.robotparser.RobotFileParser(); rp.parse(robots.splitlines())
    maps = re.findall(r"(?im)^sitemap:\s*(\S+)", robots) or [f"https://{host}/sitemap.xml"]
    urls, seen, queue = set(), set(), list(maps)
    while queue and len(seen) < 120:
        m = queue.pop(0)
        if m in seen: continue
        seen.add(m)
        try: _, xml = get(m)
        except Exception: continue
        locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
        if "<sitemapindex" in xml: queue += [l for l in locs if re.search(r"(people|lawyer|profess|team|person|profile|bio|sitemap)", l, re.I)] or locs[:10]
        else: urls |= {l for l in locs if re.search(pat, l)}
    return [u for u in urls if rp.can_fetch(UA, u) and u.startswith("https://")]


if __name__ == "__main__":
    for h in sys.argv[1:]:
        print(probe(h), flush=True)
