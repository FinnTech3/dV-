"""Re-read crawled pages that carry a UK/IE/NL work-history sentence but no recorded number, reading labelled national-format numbers
('Tel. 02 2399 4567') against the country of the site's domain. Same fetcher and politeness as the crawl; only `tels` and `regions` change.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from . import db, fetch, firmcrawl


def targets(conn: sqlite3.Connection) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for r in conn.execute("SELECT url, host FROM pages WHERE status=200 AND name!='' AND origin IS NOT NULL AND sentence IS NOT NULL AND tels='[]'"):
        if firmcrawl.tld_region(r["url"]):
            out[r["host"]].append(r["url"])
    return out


def run_host(urls: list[str], settings: dict) -> tuple[int, int]:
    conn = firmcrawl.crawl_conn()
    found = 0
    for u in urls:
        res = fetch.fetch(u, settings, keep_html=True)
        if not res.ok or not res.html:
            continue
        row = firmcrawl.extract(u, res.html)
        if row["tels"]:
            for attempt in range(5):
                try:
                    conn.execute("UPDATE pages SET tels=?, regions=? WHERE url=?",
                                 (json.dumps(row["tels"]), ",".join(sorted({t["region"] or "" for t in row["tels"]})), u))
                    conn.commit()
                    found += 1
                    break
                except sqlite3.OperationalError:
                    time.sleep(5 * (attempt + 1))
    return len(urls), found


def main(workers: int = 40) -> None:
    settings = db.load_settings()
    tg = targets(firmcrawl.crawl_conn())
    print(f"{sum(len(v) for v in tg.values())} pages on {len(tg)} hosts", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {h: ex.submit(run_host, u, settings) for h, u in tg.items()}
        total = 0
        for h, f in futs.items():
            try:
                n, found = f.result()
            except Exception as exc:
                print(f"{h}: failed ({type(exc).__name__})", flush=True); continue
            total += found
            if found:
                print(f"{h}: {found}/{n} numbers found", flush=True)
    print(f"done: numbers found on {total} pages", flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
