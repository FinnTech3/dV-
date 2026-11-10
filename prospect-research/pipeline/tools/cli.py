"""Command line entry point:  python -m pipeline.tools.cli <command>

  init        create the database
  seed        queue the planned research tasks from config/plan_seed.json
  status      counts, gate state and next queued task
  gate        show whether person-level research is permitted
  inspect     read-only inspection of the supplied workbook
  ingest F    ingest a staged candidate batch (refused while the gate is closed)
  dedupe      second deduplication pass
  export      append eligible rows to the working copy and write the review file
  report      write pipeline/report/report.md
  checkpoint  write pipeline/ledger/checkpoint.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ch, db, discover, gate, queue, render, report, search


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="pipeline")
    ap.add_argument("command", choices=["init", "seed", "status", "gate", "inspect", "ingest", "dedupe", "export", "report", "checkpoint"])
    ap.add_argument("path", nargs="?")
    ap.add_argument("--db", default=None)
    args = ap.parse_args(argv)
    settings = db.load_settings()
    conn = db.connect(args.db)
    private = db.PIPELINE / "private"
    template = private / settings["export"]["template_filename"]
    working = db.PIPELINE / "output" / settings["export"]["working_copy_filename"]

    if args.command == "init":
        print(f"database ready at {args.db or db.DEFAULT_DB}")
    elif args.command == "seed":
        seed = json.loads((db.PIPELINE / "config" / "plan_seed.json").read_text(encoding="utf-8"))
        added = 0
        for country, cities in seed["cities"].items():
            for city in cities:
                for source, kind in seed["non_personal_tasks"]:
                    added += queue.add_task(conn, country, city, source, kind, next_action="research and record in docs/plan", requires_person_gate=False)
                for source, kind in seed["person_level_tasks"]:
                    added += queue.add_task(conn, country, city, source, kind, next_action="HARVEST once the compliance gate is open", requires_person_gate=True)
        print(f"{added} task(s) queued")
    elif args.command == "gate":
        print(json.dumps(gate.status(), indent=2))
    elif args.command == "status":
        st = gate.status()
        print(json.dumps({"person_gate": st["open"], "gate_reason": st["reason"], **queue.counts(conn),
                          "search_provider": search.pick_provider().name, "companies_house": ch.status()}, indent=2))
    elif args.command == "inspect":
        info = render.inspect(Path(args.path) if args.path else template, settings)
        info["rows"] = len(info["rows"])
        print(json.dumps(info, indent=2))
    elif args.command == "ingest":
        try:
            gate.require_open()
            print(json.dumps(discover.ingest_batch(conn, Path(args.path), settings), indent=2))
        except gate.PersonGateClosed as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 2
    elif args.command == "dedupe":
        print(f"{discover.reclassify_all(conn, settings)} later record(s) marked DUPLICATE")
    elif args.command == "export":
        discover.reclassify_all(conn, settings)
        rep = render.export(conn, template, working, settings)
        held = render.write_review_export(conn, db.PIPELINE / "output" / "held_for_review.tsv")
        rep["held_for_review_rows"] = held
        (db.PIPELINE / "report" / "export_report.json").write_text(json.dumps(rep, indent=2, default=str), encoding="utf-8")
        print(json.dumps(rep, indent=2, default=str))
    elif args.command == "report":
        rp = db.PIPELINE / "report" / "export_report.json"
        rep = json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else None
        out = db.PIPELINE / "report" / "report.md"
        out.write_text(report.render_markdown(conn, settings, rep), encoding="utf-8")
        print(f"wrote {out}")
    elif args.command == "checkpoint":
        print(json.dumps(queue.checkpoint(conn, settings, note=args.path or ""), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
