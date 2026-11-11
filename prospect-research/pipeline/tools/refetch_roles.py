"""Re-read crawled profile pages whose job title was missed and store the title the page itself states.

Only pages that already carry an origin-country work-history sentence and a telephone number are re-read
(about 1,500 of ~97k). Same fetcher as the crawl: robots.txt honoured, 2 s between requests per host, no LinkedIn.
Writes only the `role` column of the crawl database; nothing is invented, a page with no stated title stays blank.
"""
from __future__ import annotations

import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from . import db, fetch, firmcrawl


def targets(conn: sqlite3.Connection) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for r in conn.execute("SELECT url, host, role FROM pages WHERE status=200 AND name!='' AND origin IS NOT NULL AND sentence IS NOT NULL "
                          "AND tels != '[]'"):
        if not r["role"] or not firmcrawl.TITLE_WORDS.search(r["role"]):
            out[r["host"]].append(r["url"])
    return out


def run_host(host: str, urls: list[str], settings: dict) -> tuple[int, int, int]:
    conn = firmcrawl.crawl_conn()
    fixed = checked = 0
    for u in urls:
        res = fetch.fetch(u, settings, keep_html=True)
        checked += 1
        if not res.ok or not res.html:
            continue
        role = firmcrawl.extract(u, res.html)["role"]
        if role and firmcrawl.TITLE_WORDS.search(role):
            conn.execute("UPDATE pages SET role=? WHERE url=?", (role, u))
            fixed += 1
        if checked % 25 == 0:
            conn.commit()
    conn.commit()
    return len(urls), checked, fixed


def main(workers: int = 40) -> None:
    settings = db.load_settings()
    tg = targets(firmcrawl.crawl_conn())
    total = sum(len(v) for v in tg.values())
    print(f"{total} pages on {len(tg)} hosts", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {h: ex.submit(run_host, h, u, settings) for h, u in tg.items()}
        done = fixed = 0
        for h, f in futs.items():
            n, c, x = f.result()
            done += c; fixed += x
            print(f"{h}: {x}/{c} titles found", flush=True)
    print(f"done: {fixed} titles found in {done} pages", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
