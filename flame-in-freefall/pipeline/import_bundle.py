#!/usr/bin/env python3
"""Import psi_catalog_bundle.json produced by tools/psi_browser_export.js.

Writes the same outputs as build_catalog.py, so the rest of the pipeline does not care which
route fetched the data:
  content/investigations/<ID>/psi.json
  data/experimental_tables/<ID>/Experimental table/<file>.csv

Usage: python -m pipeline.import_bundle path/to/psi_catalog_bundle.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import psi_api as api
from .build_catalog import slim, table_summary
from .common import CONTENT, ET_DIR, write_json


def import_bundle(bundle: dict, content: Path = CONTENT, et_dir: Path = ET_DIR) -> list[str]:
    done = []
    for item in bundle["investigations"]:
        inv = item["id"]
        files = [api.RemoteFile(inv, key, int(size or 0), int(version or 1)) for key, size, version in item["files"]]
        tables = []
        for t in item.get("tables", []):
            if t.get("status") != 200 or not t.get("text"):
                print(f"  ! {inv} {t.get('name')}: status {t.get('status')}")
                continue
            rf = api.RemoteFile(inv, t["key"], len(t["text"]), 1)
            dest = rf.local_path(et_dir)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(t["text"], encoding="utf-8")
            tables.append(table_summary(dest))
        write_json(content / "investigations" / inv / "psi.json", slim(item["meta"], item.get("hit"), files, tables))
        done.append(inv)
    return done


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if len(argv) != 1:
        print(__doc__)
        return 2
    bundle = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    done = import_bundle(bundle)
    print(f"imported {len(done)} investigations: {' '.join(done)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
