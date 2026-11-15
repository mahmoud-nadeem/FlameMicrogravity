"""Shared helpers: repository paths, YAML/Markdown I/O, strict number parsing."""
from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
SCHEMAS = ROOT / "schemas"
DATA = ROOT / "data"
ET_DIR = DATA / "experimental_tables"     # raw experimental tables downloaded from PSI
DERIVED = DATA / "derived"                # everything the pipeline computes for the site

PSI_ID = re.compile(r"^PSI-\d+$")
PSI_PER_ATM = 14.696
BAR_PER_ATM = 1.01325
MMHG_PER_ATM = 760.0

# Leading number only. "1 atm" -> 1.0, "21.5 - 21.7" -> 21.5, "RAMP" -> None, "LOW O2" -> None.
# (Stripping letters instead turned "LOW O2" into 2.0 during the Day-1 study.)
_LEADING_NUMBER = re.compile(r"^\s*([-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)")


def to_number(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return None if value != value else float(value)  # NaN -> None
    m = _LEADING_NUMBER.match(str(value))
    return float(m.group(1)) if m else None


def norm_header(name: str) -> str:
    """Collapse runs of whitespace: 'Calibrated  initial O2 % by vol ' -> 'Calibrated initial O2 % by vol'."""
    return " ".join(str(name).split())


def read_table(path: Path) -> pd.DataFrame:
    """Read a PSI experimental-table CSV as strings with normalised headers."""
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    df.columns = [norm_header(c) for c in df.columns]
    return df


def load_yaml(path: Path):
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_markdown(path: Path) -> tuple[dict, str]:
    """Split a Markdown file into (front-matter dict, body). Front matter is required."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("file must start with a '---' front-matter block")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("front-matter block is not closed with '---'")
    meta = yaml.safe_load(parts[1]) or {}
    return meta, parts[2].strip()


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
