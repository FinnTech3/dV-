"""Wide probe: which public sites expose per-person pages in their sitemaps, in several languages?"""
import json, socket, sys
from concurrent.futures import ThreadPoolExecutor
from .probe import probe_urls
socket.setdefaulttimeout(12)
WIDE = (r"/(people|person|personen|persons|staff|team|our-team|mitarbeiter|mitarbeitende|mitarbeiterinnen|profil|profile|profiles|professor|professors|prof|faculty|"
        r"researcher|researchers|scientists?|wissenschaftler|lehrstuhl|chercheur|chercheurs|enseignant|docente|docentes|investigador|investigadores|experts?|ansprechpartner|"
        r"consultants?|partners?|directors?|principals?|leadership|bio|biography|cv|members?|equipe|equipo|equipa|fellows?|alumni|speakers?)/[^/?]+")
def one(h):
    try:
        u = probe_urls(h, WIDE, max_maps=15)
        return {"host": h, "n": len(u), "sample": sorted(u)[len(u)//2:len(u)//2+1]}
    except Exception as e:
        return {"host": h, "n": 0, "err": str(e)[:50]}
if __name__ == "__main__":
    hosts = [l.strip() for l in open(sys.argv[1]) if l.strip()]
    with ThreadPoolExecutor(28) as ex:
        res = list(ex.map(one, hosts))
    json.dump(res, open(sys.argv[2], "w"), indent=1)
    for r in sorted(res, key=lambda r: -r["n"]):
        if r["n"] >= 20: print(f"{r['n']:6d} {r['host']:32s} {(r['sample'] or [''])[0][:90]}")
