"""Find people-profile URLs on sites that publish no usable sitemap, by following the site's own directory pages.

Honours robots.txt (a missing robots.txt means no restrictions; a server error or timeout means the host is skipped), waits 2 s between
requests to a host, reads only the home page and a handful of staff/people/team directory pages (plus their pagination), and never
leaves the host. Output has the same shape as probe_json so `osmseed crawl` can read it.
"""
from __future__ import annotations

import html
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor

UA = "prospect-research-bot/0.1 (supervised training exercise; respects robots.txt)"
DIR_WORDS = re.compile(r"(?i)(people|staff|faculty|team|personen|personal|mitarbeit|lehrende|professor|forschende|researchers?|members?|"
                       r"experts?|directory|equipo|equipe|equipa|personas|pessoas|collaborat|medewerkers|lawyers|attorneys|advisors|"
                       r"our-people|nos-equipes|team-members|leadership|management|partners)")
SKIP = re.compile(r"(?i)\.(pdf|jpe?g|png|gif|svg|zip|docx?|xlsx?)($|\?)|/(news|events?|blog|press|careers?|jobs?|tag|category|search|login|cart)/")
NOT_PERSON = re.compile(r"(?i)(contact|welcome|study|studi|forschung|research|aktuell|news|international|career|karriere|werden|apply|bewerb|"
                        r"admission|about|ueber|uber|overview|ubersicht|uebersicht|list-of|liste|team-?uebersicht|mitarbeiterinnen-team|"
                        r"faculty-members|our-people|people-overview|directory|search|service|support|download|form|policy|privacy|impressum)")
SLUG = re.compile(r"^(?:[a-zA-Z\u00c0-\u017f.]{2,20}[-_]){1,3}[a-zA-Z\u00c0-\u017f.]{2,24}(?:\.html?)?/?$")
PERSON = re.compile(r"[?&](id|person|staff|profile)=\w+|/(person|people|staff|profile|team|mitarbeiter|experts?|faculty)/[^/?#]+")
HREF = re.compile(r'(?is)<a\b[^>]*?href="([^"#]+)"[^>]*>(.*?)</a>')


def _get(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ctype = r.headers.get("Content-Type", "")
        if "html" not in ctype and "xml" not in ctype and "text" not in ctype:
            return ""
        return r.read(2_000_000).decode("utf-8", "replace")


def _robots(host: str):
    try:
        body = _get(f"https://{host}/robots.txt")
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            rp = urllib.robotparser.RobotFileParser(); rp.parse([]); return rp      # no robots.txt: no restrictions
        return None                                                                  # 401/403/5xx: treat as closed
    except Exception:
        return None
    rp = urllib.robotparser.RobotFileParser(); rp.parse(body.splitlines()); return rp


def links(page: str, base: str, host: str) -> list[tuple[str, str]]:
    out = []
    for href, text in HREF.findall(page):
        u = urllib.parse.urljoin(base, html.unescape(href)).split("#")[0]
        p = urllib.parse.urlparse(u)
        if p.scheme != "https" or p.netloc != host or SKIP.search(u):
            continue
        out.append((u, re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(text))).strip()))
    return out


def probe_host(host: str, max_dirs: int = 6, max_pages: int = 14, delay: float = 2.0) -> list[str]:
    rp = _robots(host)
    if rp is None:
        return []
    allowed = lambda u: rp.can_fetch(UA, u)
    try:
        home = _get(f"https://{host}/")
    except Exception:
        return []
    dirs = []
    for u, text in links(home, f"https://{host}/", host):
        if (DIR_WORDS.search(urllib.parse.urlparse(u).path) or DIR_WORDS.search(text)) and allowed(u) and u not in dirs:
            dirs.append(u)
    people: set[str] = set()
    fetched = 0
    queue = dirs[:max_dirs]
    seen = set(queue)
    while queue and fetched < max_pages:
        d = queue.pop(0)
        time.sleep(delay)
        try:
            page = _get(d)
        except Exception:
            continue
        fetched += 1
        d_path = urllib.parse.urlparse(d).path.rstrip("/")
        for u, text in links(page, d, host):
            path = urllib.parse.urlparse(u).path
            if re.search(r"[?&](page|p|seite|pagina)=\d+", u) and u not in seen and allowed(u) and len(seen) < 40:
                seen.add(u); queue.append(u); continue                                  # pagination of the directory
            last = path.rstrip("/").rsplit("/", 1)[-1]
            if u == d or not allowed(u) or NOT_PERSON.search(path):
                continue
            if PERSON.search(u) or (SLUG.match(last) and d_path and path.startswith(d_path + "/")):
                people.add(u)
    return sorted(people)[:300]


def main(src: str, out_path: str, workers: int = 24) -> None:
    socket.setdefaulttimeout(15)
    hosts = json.load(open(src))
    res: dict = {}

    def one(h: str):
        try:
            return h, probe_host(h)
        except Exception:
            return h, []

    with ThreadPoolExecutor(workers) as ex:
        for i, (h, urls) in enumerate(ex.map(one, list(hosts))):
            if len(urls) >= 5:
                m = hosts[h]
                res[h] = {"label": m.get("label", h), "market": m.get("country", "agent seed"), "urls": urls,
                          "channel": m.get("channel") or "sub-agent web search: organisation people pages",
                          "source": "WebSearch (sub-agent) host; people pages found by following the site's own directory links"}
            if i % 25 == 0:
                print(f"probed {i}/{len(hosts)}; with people pages: {len(res)}", flush=True)
                json.dump(res, open(out_path, "w"), ensure_ascii=False)
    json.dump(res, open(out_path, "w"), ensure_ascii=False)
    print(f"done: {len(res)} hosts; {sum(len(v['urls']) for v in res.values())} URLs", flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
