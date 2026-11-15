"""Parsers for the PSI combustion files used in Flame in Freefall.

Each function encodes a quirk found while inspecting the real files on 2026-11-14:
  * FLEX .txt files are tab-separated and use old Mac line endings (\\r only).
  * ACME *_data.csv files start with ONE metadata line before the real header.
  * The SAME results workbook has two header rows; the data header is row 2.
"""
from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------- FLEX (PSI-69)
def _read_text(path_or_text: str | Path) -> str:
    """Accept a file path or the file's text; normalise \\r\\n and bare \\r to \\n."""
    if isinstance(path_or_text, Path) or ("\n" not in path_or_text and "\r" not in path_or_text):
        raw = Path(path_or_text).read_text(encoding="latin-1")
    else:
        raw = path_or_text
    return raw.replace("\r\n", "\n").replace("\r", "\n")


def read_flex_series(path_or_text: str | Path) -> pd.DataFrame:
    """DropletData / LLUVData / ColorCamData -> numeric DataFrame (time column first)."""
    text = _read_text(path_or_text)
    df = pd.read_csv(io.StringIO(text), sep="\t")
    df.columns = [c.strip() for c in df.columns]
    return df.apply(pd.to_numeric, errors="coerce").dropna(how="all")


_TS_NUM = re.compile(r"^\s*(?P<key>[^=:]+?)\s*[=:]\s*(?P<val>.*?)\s*$")


def read_flex_testsheet(path_or_text: str | Path) -> dict:
    """TestSheet.txt -> dict of conditions + free-text comments."""
    text = _read_text(path_or_text)
    lines = text.split("\n")
    out: dict = {"test_id": lines[0].strip()}
    comments: list[str] = []
    in_comments = False
    for line in lines[1:]:
        if line.strip().upper().startswith("COMMENTS"):
            in_comments = True
            continue
        if in_comments:
            if line.strip():
                comments.append(line.strip())
            continue
        m = _TS_NUM.match(line.replace("\t", " "))
        if m and m.group("key").strip() and m.group("key").strip().upper() == m.group("key").strip() and not m.group("val"):
            continue  # section title such as "AMBIENT ENVIRONMENT"
        if m:
            key, val = m.group("key").strip(), m.group("val").strip()
            try:
                out[key] = float(val)
            except ValueError:
                out[key] = None if val.lower() == "nan" else val
    out["comments"] = " ".join(comments)
    return out


def d2_burning_rate(series: pd.DataFrame, t0: float = 0.0) -> float:
    """Least-squares slope k (mm^2/s) of d^2 vs t after ignition (d^2 = d0^2 - k t)."""
    s = series[(series.iloc[:, 0] > t0) & series.iloc[:, 1].gt(0)]
    if len(s) < 5:
        return float("nan")
    t, d = s.iloc[:, 0].to_numpy(), s.iloc[:, 1].to_numpy()
    slope = ((t - t.mean()) * (d**2 - (d**2).mean())).sum() / ((t - t.mean()) ** 2).sum()
    return float(-slope)


# ---------------------------------------------------------------- ACME (PSI-159, PSI-10, PSI-20..23)
def read_acme_csv(path_or_text: str | Path) -> tuple[dict, pd.DataFrame]:
    """*_data.csv -> (metadata dict from line 1, DataFrame from line 2 on)."""
    text = _read_text(path_or_text)
    first, rest = text.split("\n", 1)
    meta: dict = {}
    for i, part in enumerate(first.split(",")):
        part = part.strip()
        if i == 0:
            meta["timestamp"] = part
        elif ":" in part:
            k, v = part.split(":", 1)
            v = v.strip()
            try:
                meta[k.strip()] = float(v)
            except ValueError:
                meta[k.strip()] = v
    df = pd.read_csv(io.StringIO(rest))
    # Time is "HH:MM:SS:mmm" -> seconds from the first sample
    t = df["Time"].astype(str).str.split(":", expand=True).astype(float)
    secs = t[0] * 3600 + t[1] * 60 + t[2] + t[3] / 1000.0
    df.insert(0, "t_s", secs - secs.iloc[0])
    return meta, df


# ---------------------------------------------------------------- SAME / SAME-R (PSI-101, PSI-102)
def read_same_results(xlsx_path: str | Path, sheet: str = "SAME Combined Results") -> pd.DataFrame:
    """Per-test smoke results (one row per test). Header is on the 2nd row of the sheet."""
    df = pd.read_excel(xlsx_path, sheet_name=sheet, header=1)
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(subset=["Sample Type"])
    df["campaign"] = df.iloc[:, 0].map({1: "SAME", 2: "SAME-R"}).fillna(df.iloc[:, 0].astype(str))
    return df


def read_same_hkp(path: str | Path) -> pd.DataFrame:
    """1 Hz housekeeping log; -999 is a missing-value sentinel."""
    df = pd.read_csv(path)
    return df.replace(-999, pd.NA)
