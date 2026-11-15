#!/usr/bin/env python3
"""Build the standard cleaned run table of one record from a mapping file you write.

    python tools/build_run_table.py analysis/T3/PSI-102_same/scripts/run_table_map.yaml

You decide the mapping (which source column feeds which standard column, which unit conversion,
which outcome categories); this tool applies it the same way every time and guarantees:

- source_file and source_row are exact: source_row is the line number in a text file, or the row
  number in Excel, with the header counted (header on line 1 -> first data row is 2);
- the raw files are only read, never changed;
- nothing is guessed: a value that is not a plain number is left empty in the standard column,
  kept in its raw_ column and flagged in notes (unless you set partial_numbers: leading);
- every change is written to data_log.md (between the build_run_table markers; your own lines
  outside the markers are kept): unit conversions, constant values with your reason, generated
  run ids, empty rows left out, non-numeric values;
- suspicious values (oxygen outside 0-100 %, pressure <= 0, negative flow, duplicate run id) are
  flagged in notes, never fixed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import kitlib as K  # noqa: E402

CONVERSIONS = {  # name -> factor to the schema unit (oxygen_pct in %, pressure_kpa in kPa)
    "none": 1.0,
    "fraction_to_pct": 100.0,
    "atm_to_kpa": 101.325,
    "bar_to_kpa": 100.0,
    "psi_to_kpa": 6.894757,
    "mmhg_to_kpa": 0.1333224,
    "torr_to_kpa": 0.1333224,
    "mpa_to_kpa": 1000.0,
    "pa_to_kpa": 0.001,
}
SCRIPT = "tools/build_run_table.py"


class MapError(ValueError):
    pass


def _spec_columns(spec: dict) -> dict:
    cols = dict(spec.get("columns") or {})
    for name in cols:
        fixed = ("investigation_id", "run_id", "source_file", "source_row", "outcome_norm")
        if name not in K.REQUIRED_COLUMNS or name in fixed:
            raise MapError(f"columns: '{name}' cannot be mapped here (allowed: "
                           f"{', '.join(c for c in K.REQUIRED_COLUMNS if c not in fixed)}; run_id and "
                           f"outcome_map are set at source level)")
    return cols


def build(map_path: Path, root: Path = K.ROOT) -> tuple[Path, int, list[str]]:
    """Apply one mapping file. Returns (table path, number of rows, data-log lines)."""
    map_path = Path(map_path).resolve()
    spec = yaml.safe_load(map_path.read_text(encoding="utf-8")) or {}
    inv, slug = spec.get("investigation_id"), spec.get("slug")
    if not inv or not slug:
        raise MapError("the mapping needs investigation_id and slug")
    record = map_path.parent.parent
    sources = spec.get("sources") or []
    if not sources:
        raise MapError("the mapping needs at least one entry under sources")

    frames, log = [], []
    for src in sources:
        rel = str(src.get("file") or "").replace("\\", "/")
        path = K.find_source(root, rel)
        if path is None:
            raise MapError(f"source file not found: {rel} (looked in data/experimental_tables and data/raw)")
        df, rows = K.read_source(path, header_row=int(src.get("header_row", 1)), sep=src.get("sep"),
                                 sheet=src.get("sheet"))
        frames.append(_one_source(spec, src, rel, df, rows, log))

    table = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=K.REQUIRED_COLUMNS)
    out = record / "tables" / f"{inv}_{slug}_runs_clean.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False, encoding="utf-8-sig")
    _write_log(record / "data_log.md", log)
    return out, len(table), log


def _one_source(spec: dict, src: dict, rel: str, df: pd.DataFrame, rows: list[int], log: list[str]) -> pd.DataFrame:
    inv = spec["investigation_id"]
    cols = _spec_columns(src)
    partial = src.get("partial_numbers", "flag")
    if partial not in ("flag", "leading"):
        raise MapError("partial_numbers must be 'flag' or 'leading'")

    for name, m in cols.items():
        if not isinstance(m, dict) or (("from" in m) == ("value" in m)):
            raise MapError(f"columns.{name}: give either 'from: <source column>' or 'value: ...' with 'reason: ...'")
        if "from" in m and m["from"] not in df.columns:
            raise MapError(f"columns.{name}: source column '{m['from']}' is not in {rel}. "
                           f"Columns: {list(df.columns)}")
        if "value" in m and not str(m.get("reason") or "").strip():
            raise MapError(f"columns.{name}: a constant value needs a 'reason'")
        conv = m.get("convert", "none")
        if conv not in CONVERSIONS:
            raise MapError(f"columns.{name}: unknown convert '{conv}' (use one of {', '.join(CONVERSIONS)})")
        if conv != "none" and name not in K.NUMERIC_COLUMNS:
            raise MapError(f"columns.{name}: convert only applies to {', '.join(sorted(K.NUMERIC_COLUMNS))}")
        if name == "gravity_level" and "value" in m and m["value"] not in K.GRAVITY_LEVELS:
            raise MapError(f"gravity_level must be one of {', '.join(sorted(K.GRAVITY_LEVELS))}")
    extra = dict(src.get("extra") or {})
    for name, m in extra.items():
        if not name.startswith("x_"):
            raise MapError(f"extra column '{name}' must start with x_")
        if not isinstance(m, dict) or m.get("from") not in df.columns:
            raise MapError(f"extra.{name}: 'from' must name a column of {rel}")
        if m.get("convert", "none") not in CONVERSIONS:
            raise MapError(f"extra.{name}: unknown convert '{m.get('convert')}'")

    # Empty rows (every cell blank) are left out, and logged.
    blank = df.apply(lambda r: all(not str(v).strip() for v in r), axis=1)
    if blank.any():
        skipped = [rows[i] for i in range(len(df)) if blank.iloc[i]]
        log.append(f"{rel} | rows {K.compact_ranges(skipped)} ({len(skipped)} rows) | all | (every cell empty) | "
                   f"(left out of the run table) | empty rows carry no measurement | {SCRIPT} (empty rows)")

    run_id_spec = src.get("run_id")
    run_cols = [] if not run_id_spec else ([run_id_spec] if isinstance(run_id_spec, str) else list(run_id_spec))
    for c in run_cols:
        if c not in df.columns:
            raise MapError(f"run_id: column '{c}' is not in {rel}")
    if not run_cols:
        log.append(f"{rel} | all | run_id | (no run id column chosen) | r<source_row> | "
                   f"run_id generated from the source row | {SCRIPT} (run_id)")
    prefix = str(src.get("run_id_prefix") or "")

    out_rows, nonnum, partial_rows = [], {}, {}
    for i in range(len(df)):
        if blank.iloc[i]:
            continue
        r = df.iloc[i]
        srow = rows[i]
        notes = []
        rec = {c: "" for c in K.REQUIRED_COLUMNS}
        rec.update(investigation_id=inv, source_file=rel, source_row=srow)
        rid = "-".join(str(r[c]).strip() for c in run_cols) if run_cols else f"r{srow}"
        rec["run_id"] = prefix + rid
        for name, m in cols.items():
            if "value" in m:
                rec[name] = m["value"]
                continue
            raw = str(r[m["from"]]).strip()
            if name not in K.NUMERIC_COLUMNS:
                rec[name] = raw
                continue
            num, kind = K.parse_number(raw)
            if kind == "text" or (kind == "partial" and partial == "flag"):
                if raw:
                    notes.append(f"{name}: '{raw}' is not a plain number, kept in raw_{m['from']}")
                    nonnum.setdefault((name, m["from"]), []).append((srow, raw))
                continue
            if kind == "partial":
                partial_rows.setdefault((name, m["from"]), []).append((srow, raw, num))
            if num is not None:
                rec[name] = round(num * CONVERSIONS[m.get("convert", "none")], 6)
        for name, m in extra.items():
            raw = str(r[m["from"]]).strip()
            conv = m.get("convert", "none")
            if conv == "none":
                rec[name] = raw
            else:
                num, kind = K.parse_number(raw)
                rec[name] = round(num * CONVERSIONS[conv], 6) if kind == "plain" else ""
                if raw and kind != "plain":
                    notes.append(f"{name}: '{raw}' is not a plain number")
        if src.get("outcome_map") is not None and cols.get("outcome_raw"):
            omap = {str(k).strip(): v for k, v in (src.get("outcome_map") or {}).items()}
            if rec["outcome_raw"] in omap:
                rec["outcome_norm"] = omap[rec["outcome_raw"]]
            elif rec["outcome_raw"]:
                notes.append(f"outcome '{rec['outcome_raw']}' is not in outcome_map")
        # suspicious values: flag, never fix
        o2, p, v = rec["oxygen_pct"], rec["pressure_kpa"], rec["flow_speed_value"]
        if o2 != "" and not (0 <= o2 <= 100):
            notes.append(f"SUSPICIOUS oxygen_pct {o2} outside 0-100")
        if p != "" and p <= 0:
            notes.append(f"SUSPICIOUS pressure_kpa {p} <= 0")
        if v != "" and v < 0:
            notes.append(f"SUSPICIOUS negative flow_speed_value {v}")
        if rec["gravity_level"] and rec["gravity_level"] not in K.GRAVITY_LEVELS:
            notes.append(f"gravity_level '{rec['gravity_level']}' is not one of {sorted(K.GRAVITY_LEVELS)}")
        if cols.get("notes", {}).get("from"):
            src_note = str(r[cols["notes"]["from"]]).strip()
            if src_note:
                notes.insert(0, src_note)
        rec["notes"] = "; ".join(n for n in notes if n)
        if src.get("keep_raw", True):
            for c in df.columns:
                rec[f"raw_{c}"] = str(r[c])
        out_rows.append(rec)

    table = pd.DataFrame(out_rows)
    if table.empty:
        table = pd.DataFrame(columns=K.REQUIRED_COLUMNS)
    dup = table["run_id"].duplicated(keep=False) & table["run_id"].ne("")
    for idx in table.index[dup]:
        n = table.at[idx, "notes"]
        table.at[idx, "notes"] = (n + "; " if n else "") + f"SUSPICIOUS run_id '{table.at[idx, 'run_id']}' repeated"

    # data log: one line per column-wide decision, one line per changed cell
    srows = [s for s, b in zip(rows, blank) if not b]
    span = K.compact_ranges(srows)
    for name, m in cols.items():
        if "value" in m:
            log.append(f"{rel} | rows {span} | {name} | (not in the table) | {m['value']} | {m['reason']} | "
                       f"{SCRIPT} (columns.{name})")
        elif m.get("convert", "none") != "none":
            log.append(f"{rel} | rows {span} | {name} | value of '{m['from']}' | value x {CONVERSIONS[m['convert']]} "
                       f"({m['convert']}) | the standard table uses {'%' if name == 'oxygen_pct' else 'kPa'} | "
                       f"{SCRIPT} (columns.{name}.convert)")
    for name, m in extra.items():
        if m.get("convert", "none") != "none":
            log.append(f"{rel} | rows {span} | {name} | value of '{m['from']}' | value x {CONVERSIONS[m['convert']]} "
                       f"({m['convert']}) | unit conversion | {SCRIPT} (extra.{name}.convert)")
    for (name, col), items in nonnum.items():
        for srow, raw in items:
            log.append(f"{rel} | {srow} | {name} | {raw} | (empty) | not a plain number; original kept in raw_{col} "
                       f"and flagged in notes | {SCRIPT} (numbers)")
    for (name, col), items in partial_rows.items():
        for srow, raw, num in items:
            log.append(f"{rel} | {srow} | {name} | {raw} | {num} before unit conversion | leading number kept "
                       f"(partial_numbers: leading) | {SCRIPT} (numbers)")
    cols_order = K.REQUIRED_COLUMNS + [c for c in table.columns if c not in K.REQUIRED_COLUMNS]
    return table[cols_order]


def _write_log(path: Path, lines: list[str]) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else f"# Data log\n\nFormat: {K.DATA_LOG_HEADER}\n"
    block = "\n".join([K.AUTO_START, *lines, K.AUTO_END])
    if K.AUTO_START in text and K.AUTO_END in text:
        head, rest = text.split(K.AUTO_START, 1)
        tail = rest.split(K.AUTO_END, 1)[1]
        text = head + block + tail
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mapping", type=Path, nargs="+", help="scripts/run_table_map.yaml of a record")
    args = ap.parse_args(argv)
    code = 0
    for m in args.mapping:
        try:
            out, n, log = build(m)
            print(f"{out.relative_to(K.ROOT) if out.is_relative_to(K.ROOT) else out}: {n} rows; "
                  f"{len(log)} data-log lines written to data_log.md")
        except (MapError, FileNotFoundError, KeyError) as e:
            print(f"{m}: {e}", file=sys.stderr)
            code = 1
    return code


if __name__ == "__main__":
    sys.exit(main())
