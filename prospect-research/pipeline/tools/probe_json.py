"""Probe hosts from a JSON dict {host: {label,...}} with the wide multi-language person-page pattern; write {host: {label, urls}}."""
import json, socket, sys
from concurrent.futures import ThreadPoolExecutor
from .probe import probe_urls
from .widepatrol import WIDE

if __name__ == "__main__":
    socket.setdefaulttimeout(12)
    hosts = json.load(open(sys.argv[1]))
    def one(h):
        try:
            return h, probe_urls(h, WIDE, max_maps=10)
        except Exception:
            return h, []
    res = {}
    with ThreadPoolExecutor(32) as ex:
        for i, (h, urls) in enumerate(ex.map(one, list(hosts))):
            if len(urls) >= 3:
                res[h] = {"label": hosts[h]["label"], "market": hosts[h].get("country", "agent seed"), "urls": urls[:500]}
            if i % 50 == 0:
                print(f"probed {i}/{len(hosts)}; with people pages: {len(res)}", flush=True)
                json.dump(res, open(sys.argv[2], "w"), ensure_ascii=False)
    json.dump(res, open(sys.argv[2], "w"), ensure_ascii=False)
    print(f"done: {len(res)} hosts with people pages; {sum(len(v['urls']) for v in res.values())} URLs", flush=True)
