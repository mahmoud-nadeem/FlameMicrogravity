"""Shared definitions for the team kit tools.

The package standard (folder layout, card fields, run-table columns, finding and data-log formats,
self-check items) is Mohammed Tamer's. These tools only help members follow it; if he changes the
standard, change the constants here and nothing else.
"""
from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

TRACKS = {
    "T1": {"member": "Amr Morgan", "surname": "morgan", "records": ["PSI-26", "PSI-25"]},
    "T2": {"member": "Mohamed Shreif", "surname": "shreif", "records": ["PSI-98", "PSI-99", "PSI-100"]},
    "T3": {"member": "Mahmoud Nadeem", "surname": "nadeem", "records": ["PSI-102", "PSI-101", "PSI-47"]},
    "T4": {"member": "Mohammed Tamer", "surname": "tamer", "records": ["PSI-69", "PSI-68", "PSI-39", "PSI-159"]},
    "T5": {"member": "Khaled Adawi", "surname": "adwi", "records": ["PSI-20", "PSI-22", "PSI-23", "PSI-10"]},
    "T6": {"member": "Mohamed Gamal", "surname": "gamal", "records": ["PSI-107", "PSI-106", "PSI-21"]},
}
ALIASES = {"mahmoud": "T3"}  # first names people may type

SLUGS = {
    "PSI-26": "bass", "PSI-25": "bass-ii", "PSI-98": "saffire-i", "PSI-99": "saffire-ii", "PSI-100": "saffire-iii",
    "PSI-102": "same", "PSI-101": "same-r", "PSI-47": "daft", "PSI-69": "flex", "PSI-68": "flex-2",
    "PSI-39": "cfi", "PSI-159": "cfi-g", "PSI-20": "bre", "PSI-22": "e-field", "PSI-23": "s-flame",
    "PSI-10": "flame-design", "PSI-107": "spice", "PSI-106": "slice", "PSI-21": "cld",
}

# Standard cleaned run table (section 7.3): required columns, in this order.
REQUIRED_COLUMNS = [
    "investigation_id", "run_id", "source_file", "source_row", "material_or_fuel", "gravity_level",
    "oxygen_pct", "pressure_kpa", "flow_speed_value", "flow_speed_unit", "outcome_raw", "outcome_norm", "notes",
]
NUMERIC_COLUMNS = {"oxygen_pct", "pressure_kpa", "flow_speed_value"}
GRAVITY_LEVELS = {"microgravity_ISS", "ground_1g", "partial_gravity", "unknown"}

# card.json (section 7.2)
CARD_FIELDS = [
    "investigation_id", "title", "acronym", "doi", "license", "version", "sub_research_area",
    "related_investigations", "size_on_page", "file_types_and_counts", "has_experiment_table",
    "objectives", "approach", "publications", "verified_on", "verified_by",
]

FINDING_LABELS = ("OBSERVED IN DATA", "REPORTED BY NASA OR A PUBLICATION", "OUR INFERENCE")
CONFIDENCE = {"high", "medium", "low"}

DATA_LOG_HEADER = "file | row | column | before | after | reason | script and line"
AUTO_START = "<!-- build_run_table: start (generated, do not edit between these markers) -->"
AUTO_END = "<!-- build_run_table: end -->"
TODO = "TODO"


def track_id(name: str) -> str:
    """'T3', 't3', 'nadeem' or 'mahmoud' -> 'T3'."""
    key = name.strip()
    if key.upper() in TRACKS:
        return key.upper()
    low = key.lower()
    for tid, t in TRACKS.items():
        if t["surname"] == low:
            return tid
    if low in ALIASES:
        return ALIASES[low]
    raise KeyError(f"unknown track or member '{name}' (use T1..T6 or a surname: "
                   + ", ".join(t["surname"] for t in TRACKS.values()) + ")")


def record_dir(root: Path, track: str, inv: str) -> Path:
    return Path(root) / "analysis" / track / f"{inv}_{SLUGS[inv]}"


def record_dirs(root: Path, track: str) -> list[Path]:
    base = Path(root) / "analysis" / track
    return sorted(p for p in base.glob("PSI-*_*") if p.is_dir()) if base.exists() else []


def load_meta(root: Path, inv: str) -> dict | None:
    """PSI metadata saved from the PSI API (kit: data/psi_metadata, repo: content/investigations)."""
    for p in (Path(root) / "data" / "psi_metadata" / f"{inv}.json",
              Path(root) / "content" / "investigations" / inv / "psi.json"):
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    return None


def find_source(root: Path, rel: str) -> Path | None:
    """Locate a source file given as its PSI path, e.g. 'PSI-102/Experimental table/x.csv'."""
    rel = rel.replace("\\", "/").strip("/")
    for base in ("data/experimental_tables", "data/raw", ""):
        p = Path(root) / base / rel if base else Path(root) / rel
        if p.is_file():
            return p
    return None


def decode(raw: bytes) -> str:
    for enc in ("utf-8-sig", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace")


def norm_header(name) -> str:
    return " ".join(str(name).split())


def read_source(path: Path, header_row: int = 1, sep: str | None = None, sheet=None) -> tuple[pd.DataFrame, list[int]]:
    """Read a table as strings and return (frame, source_rows).

    source_rows[i] is the row number a person sees for frame row i: the line number in a text
    file, or the row number in Excel (header_row is counted the same way, 1 = first line).
    Blank lines are kept so that the numbering never shifts.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xlsm", ".xls"):
        df = pd.read_excel(path, sheet_name=sheet if sheet is not None else 0, header=None, dtype=str)
        df = df.fillna("")
        hdr = header_row - 1
        columns = [norm_header(c) for c in df.iloc[hdr].tolist()]
        body = df.iloc[hdr + 1:].reset_index(drop=True)
        body.columns = columns
        rows = [header_row + 1 + i for i in range(len(body))]
        return body, rows
    text = decode(path.read_bytes()).replace("\r\n", "\n").replace("\r", "\n")
    if sep is None:
        sep = "\t" if suffix in (".txt", ".tsv") and "\t" in text.split("\n", header_row)[header_row - 1] else ","
    df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, keep_default_na=False, skiprows=header_row - 1,
                     skip_blank_lines=False)
    df.columns = [norm_header(c) for c in df.columns]
    df = df.fillna("")
    rows = [header_row + 1 + i for i in range(len(df))]
    return df, rows


_PLAIN_NUMBER = re.compile(r"^\s*[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?\s*$")
_LEADING_NUMBER = re.compile(r"^\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")


def parse_number(value: str) -> tuple[float | None, str]:
    """-> (number, kind) with kind 'empty', 'plain', 'partial' (leading number + other text) or 'text'."""
    s = "" if value is None else str(value).strip()
    if not s:
        return None, "empty"
    if _PLAIN_NUMBER.match(s):
        return float(s), "plain"
    m = _LEADING_NUMBER.match(s)
    return (float(m.group(1)), "partial") if m else (None, "text")


def compact_ranges(rows: list[int]) -> str:
    """[2,3,4,7] -> '2-4, 7'."""
    if not rows:
        return ""
    rows = sorted(rows)
    out, start, prev = [], rows[0], rows[0]
    for r in rows[1:]:
        if r == prev + 1:
            prev = r
            continue
        out.append(f"{start}-{prev}" if prev > start else f"{start}")
        start = prev = r
    out.append(f"{start}-{prev}" if prev > start else f"{start}")
    return ", ".join(out)
