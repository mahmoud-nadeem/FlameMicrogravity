#!/usr/bin/env python3
"""Profile downloaded files for profile.md (Phase 1).

    python tools/profile_files.py "data/experimental_tables/PSI-102"
    python tools/profile_files.py "data/raw/PSI-102" --out "analysis/T3/PSI-102_same/profile.md"

For each table (csv, txt, tsv, xlsx, xls): size, rows, columns, column names, empty cells per
column, fully empty rows and duplicate rows. For every other file: type and size; open documents
yourself and record title, pages and purpose. --out appends to the file instead of printing.
Units are not guessed: read them from the column names and the documents.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import kitlib as K  # noqa: E402

TABLES = {".csv", ".tsv", ".txt", ".xlsx", ".xls", ".xlsm"}


def _sheets(p: Path) -> list:
    if p.suffix.lower() in (".xlsx", ".xls", ".xlsm"):
        try:
            return list(pd.ExcelFile(p).sheet_names)
        except Exception:  # noqa: BLE001
            return []
    return [None]


def profile_table(p: Path, sheet=None) -> list[str]:
    try:
        df, rows = K.read_source(p, sheet=sheet)
    except Exception as e:  # noqa: BLE001
        return [f"- could not be read as a simple table ({e.__class__.__name__}); "
                "see scripts/psi_parsers.py or open it and note its structure"]
    blank = df.apply(lambda r: all(not str(v).strip() for v in r), axis=1) if len(df) else pd.Series([], dtype=bool)
    data = df[~blank] if len(df) else df
    dup = int(data.duplicated().sum()) if len(data) else 0
    out = [f"- rows: {len(df)} (data rows {rows[0] if rows else '-'} to {rows[-1] if rows else '-'}, header = row 1)"
           f"; fully empty rows: {int(blank.sum())}; duplicate rows: {dup}",
           f"- columns: {len(df.columns)}", "", "| Column | Empty cells | Example value |", "| --- | --- | --- |"]
    for c in df.columns:
        vals = data[c].astype(str).str.strip() if len(data) else pd.Series([], dtype=str)
        empty = int((vals == "").sum())
        example = next((v for v in vals if v), "")
        out.append(f"| {c} | {empty} | {example[:40].replace('|', '/')} |")
    return out


def profile(paths: list[Path]) -> str:
    files = []
    for p in paths:
        files += sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else [p]
    lines = []
    for f in files:
        if f.name in ("manifest.csv",) or f.suffix == ".part":
            continue
        size = f.stat().st_size
        lines += ["", f"### {f.as_posix()}", f"- type: {f.suffix.lower() or '(none)'}; size: {size:,} bytes"]
        if f.suffix.lower() in TABLES:
            for sh in _sheets(f):
                if sh is not None:
                    lines.append(f"- sheet: {sh}")
                lines += profile_table(f, sh)
        else:
            lines.append("- not a table: open it and record title, pages and what it is for")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", type=Path, nargs="+")
    ap.add_argument("--out", type=Path, help="append the result to this file (e.g. profile.md)")
    args = ap.parse_args(argv)
    missing = [p for p in args.paths if not p.exists()]
    if missing:
        print("not found: " + ", ".join(map(str, missing)), file=sys.stderr)
        return 1
    md = profile(args.paths)
    if args.out:
        with open(args.out, "a", encoding="utf-8") as fh:
            fh.write(md)
        print(f"appended to {args.out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
