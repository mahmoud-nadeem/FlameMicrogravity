#!/usr/bin/env python3
"""Build the investigation catalog from the PSI API.

For every PSI investigation that matches the search term (default: combustion) it writes

  content/investigations/<ID>/psi.json           machine-generated metadata (never hand-edit)
  data/experimental_tables/<ID>/Experimental table/<file>.csv   its experimental tables

psi.json keeps the scientific metadata the dashboard needs (objectives, approach, hardware,
publications, file inventory, experimental-table shape) and drops contact e-mails and phones.

Usage (from the repo root):
  python -m pipeline.build_catalog                      # all combustion investigations
  python -m pipeline.build_catalog --only PSI-69 PSI-159
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from collections import defaultdict

from . import psi_api as api
from .common import CONTENT, ET_DIR, read_table, write_json

# Matched the search word but are not combustion investigations (verified 2026-11-14).
NOT_COMBUSTION = {"PSI-181": "solder microstructure study", "PSI-108": "surface-tension convection (STDCE-1)"}


def _clean(text) -> str:
    return " ".join(str(text or "").split())


def slim(meta: dict, hit: dict | None, files: list[api.RemoteFile], tables: list[dict]) -> dict:
    """Reduce a raw /repo/investigations record to the fields the dashboard uses."""
    hit = hit or {}
    by_cat: dict[str, dict] = defaultdict(lambda: {"files": 0, "bytes": 0})
    exts: dict[str, int] = defaultdict(int)
    for f in files:
        by_cat[f.category]["files"] += 1
        by_cat[f.category]["bytes"] += f.size
        exts[f.name.rsplit(".", 1)[-1].lower() if "." in f.name else ""] += 1
    people = []
    for c in meta.get("contacts") or []:
        name = " ".join(p for p in [c.get("firstName"), c.get("midInitials"), c.get("lastName")] if p).strip()
        roles = [r.get("annotationValue") for r in (c.get("roles") or []) if r.get("annotationValue")]
        if name:
            people.append({"name": name, "affiliation": c.get("affiliation") or "", "roles": roles})
    pubs = [{"title": _clean(p.get("title")), "authors": _clean(p.get("authorList")), "doi": p.get("doi") or ""}
            for p in meta.get("publications") or [] if p.get("title")]
    acc = meta["accession"]
    return {
        "id": acc,
        "title": _clean(meta.get("title")),
        "acronym": meta.get("investigationAcronym") or "",
        "doi": meta.get("doi") or "",
        "doi_url": f"https://doi.org/{meta['doi']}" if meta.get("doi") else "",
        "psi_url": f"https://psi.nasa.gov/physci/repo/data/investigations/{acc}",
        "license": meta.get("licenseName") or "",
        "project_type": meta.get("projectType") or "",
        "platform": meta.get("flightProgram") or hit.get("Flight Platform") or "",
        "research_area": meta.get("researchArea") or "",
        "sub_area": meta.get("subResearchArea") or "",
        "hardware": _clean(meta.get("experimentHardware")),
        "managing_center": meta.get("managingNasaCenter") or "",
        "start_date": meta.get("investigationStartDate") or "",
        "end_date": meta.get("investigationEndDate") or "",
        "release_date": meta.get("releaseDate") or "",
        "keywords": [k.strip() for k in re.split(r"\s{2,}", hit.get("Keywords") or "") if k.strip()],
        "related": [k.strip() for k in (hit.get("Related Investigations") or "").split() if k.strip()],
        "objective": (meta.get("objective") or "").strip(),
        "approach": (meta.get("approach") or "").strip(),
        "hypothesis": (meta.get("hypothesis") or "").strip(),
        "impacts": (meta.get("researchImpacts") or "").strip(),
        "people": people,
        "publications": pubs,
        "total_size_bytes": int(meta.get("totalFileSize") or 0),
        "files_listed": len(files),
        "file_categories": dict(sorted(by_cat.items())),
        "file_extensions": dict(sorted(exts.items(), key=lambda kv: -kv[1])),
        "experimental_tables": tables,
        "retrieved_at": dt.date.today().isoformat(),
        "source": "NASA Physical Sciences Informatics (PSI) repository API",
    }


def table_summary(path) -> dict:
    df = read_table(path)
    df = df[df.apply(lambda r: any(str(v).strip() for v in r), axis=1)]
    return {"file": path.name, "rows": int(len(df)), "columns": list(df.columns)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--term", default="combustion")
    ap.add_argument("--only", nargs="*", help="limit to these PSI IDs")
    args = ap.parse_args(argv)

    s = api.make_session()
    hits = {h["Accession"]: h for h in api.search(s, args.term)}
    ids = args.only or sorted(hits, key=lambda x: int(x.split("-")[1]))
    print(f"{len(hits)} search hits for '{args.term}'; building {len(ids)}")
    for inv in ids:
        if inv in NOT_COMBUSTION and not args.only:
            print(f"  skip {inv}: {NOT_COMBUSTION[inv]}")
            continue
        meta = api.get_investigation(s, inv)
        files = api.list_files(s, inv, int(meta.get("version") or 1))
        tables = []
        for f in api.select(files, [r"/Experimental table/.*\.csv$"]):
            status = api.download(s, f, ET_DIR)  # -> data/experimental_tables/<ID>/Experimental table/<file>
            if status in ("ok", "exists"):
                tables.append(table_summary(f.local_path(ET_DIR)))
            else:
                print(f"  ! {inv} {f.name}: {status}")
        record = slim(meta, hits.get(inv), files, tables)
        write_json(CONTENT / "investigations" / inv / "psi.json", record)
        print(f"  {inv:8} {record['acronym'][:22]:22} files={len(files):6} tables={len(tables)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
