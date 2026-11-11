"""Turn a sub-agent's host list into crawled pages: clean -> sitemap probe -> link probe (for sites without a sitemap) -> crawl.

Usage: python -m pipeline.tools.hostpipeline <hosts.json> <work_dir> [workers]
Every step honours robots.txt and the 2 s per-host delay; hosts already crawled are skipped; provenance is recorded in host_meta.
"""
from __future__ import annotations

import json
import re
import socket
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import firmcrawl, linkprobe, osmseed
from .probe import probe_urls
from .widepatrol import WIDE

BAD = ("linkedin.", "facebook.", "twitter.", "x.com", "wikipedia.", "youtube.", "instagram.", "google.", "idealista.", "rightmove.", "kyero.")


def clean(hosts: dict) -> dict:
    have = {r[0] for r in firmcrawl.crawl_conn().execute("SELECT DISTINCT host FROM pages")}
    return {h: v for h, v in hosts.items() if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", h) and not any(b in h for b in BAD) and h not in have}


def main(src: str, work: str, workers: int = 40) -> None:
    socket.setdefaulttimeout(12)
    work_dir = Path(work); work_dir.mkdir(parents=True, exist_ok=True)
    hosts = clean(json.load(open(src)))
    print(f"{len(hosts)} new hosts", flush=True)
    found: dict = {}

    def sitemap(h):
        try:
            return h, probe_urls(h, WIDE, max_maps=10)
        except Exception:
            return h, []

    with ThreadPoolExecutor(32) as ex:
        for h, urls in ex.map(sitemap, list(hosts)):
            if len(urls) >= 3:
                found[h] = {"urls": urls[:500], "how": "sitemap"}
    rest = [h for h in hosts if h not in found]
    print(f"sitemap: {len(found)}; trying directory links on {len(rest)}", flush=True)

    def links(h):
        try:
            return h, linkprobe.probe_host(h)
        except Exception:
            return h, []

    with ThreadPoolExecutor(24) as ex:
        for h, urls in ex.map(links, rest):
            if len(urls) >= 5:
                found[h] = {"urls": urls, "how": "directory links"}
    res = {h: {"label": hosts[h].get("label", h), "market": hosts[h].get("country", "agent seed"), "urls": v["urls"],
               "channel": "sub-agent web search: " + (hosts[h].get("category") or "organisation people pages"),
               "source": f"WebSearch (sub-agent) host; people pages found via {v['how']}"} for h, v in found.items()}
    out = work_dir / (Path(src).stem + "_probe.json")
    json.dump(res, open(out, "w"), ensure_ascii=False)
    print(f"{len(res)} hosts with people pages; {sum(len(v['urls']) for v in res.values())} URLs; crawling", flush=True)
    osmseed.crawl(str(out), workers)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 40)
