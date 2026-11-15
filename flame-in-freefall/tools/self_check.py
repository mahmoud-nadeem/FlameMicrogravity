#!/usr/bin/env python3
"""Run the 10-item self-check (section 7.6) on one track and write SELF_CHECK.md.

    python tools/self_check.py T3          # or your surname: nadeem, tamer, ...

Each item is PASS, FAIL, WARN (looks wrong, a person must judge) or MANUAL (cannot be checked
by a script). Paste SELF_CHECK.md into HANDOFF.md. Exit code 1 when any item fails.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import kitlib as K  # noqa: E402

MAX_BYTES = 50 * 1024 * 1024
MEDIA = {".mp4", ".avi", ".mov", ".mpg", ".mpeg", ".ts", ".tif", ".tiff", ".nef", ".raw", ".zip"}
IMAGES = {".png", ".jpg", ".jpeg", ".svg", ".gif"}
SECRET = re.compile(r"(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|hf_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{30,}|"
                    r"(?i:(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{8,}))")
TEXT_EXT = {".md", ".json", ".yaml", ".yml", ".py", ".csv", ".txt", ".ipynb"}


def _tables(rec: Path) -> list[Path]:
    return sorted((rec / "tables").glob("*_runs_clean.csv")) if (rec / "tables").exists() else []


def _read(p: Path) -> pd.DataFrame:
    return pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def check(track: str, root: Path = K.ROOT) -> list[tuple[int, str, str, list[str]]]:
    root = Path(root)
    base = root / "analysis" / track
    recs = K.record_dirs(root, track)
    res = []

    def add(n, title, status, details):
        res.append((n, title, status, details))

    # 1. required columns, in order; card fields present
    d, bad = [], False
    tables = [t for r in recs for t in _tables(r)]
    for t in tables:
        cols = list(_read(t).columns)
        if cols[: len(K.REQUIRED_COLUMNS)] != K.REQUIRED_COLUMNS:
            bad = True
            missing = [c for c in K.REQUIRED_COLUMNS if c not in cols]
            d.append(f"{t.relative_to(root)}: first columns are not the required ones in order"
                     + (f" (missing: {', '.join(missing)})" if missing else ""))
        extra = [c for c in cols[len(K.REQUIRED_COLUMNS):] if not c.startswith(("x_", "raw_"))]
        if extra:
            bad = True
            d.append(f"{t.relative_to(root)}: extra columns must start with x_ or raw_: {', '.join(extra)}")
    for r in recs:
        cj = r / "card.json"
        if not cj.exists():
            bad = True
            d.append(f"{cj.relative_to(root)} is missing")
            continue
        card = json.loads(cj.read_text(encoding="utf-8"))
        miss = [f for f in K.CARD_FIELDS if f not in card]
        if miss:
            bad = True
            d.append(f"{cj.relative_to(root)}: missing fields {', '.join(miss)}")
    if not tables:
        d.append("no run table yet (tables/<PSI-ID>_<slug>_runs_clean.csv)")
    add(1, "Tables have all required columns, in order", "FAIL" if bad else ("WARN" if not tables else "PASS"), d)

    # 2. source_file and source_row on every row, and they point at a real row
    d, bad = [], False
    for t in tables:
        df = _read(t)
        if "source_file" not in df or "source_row" not in df:
            bad = True
            d.append(f"{t.relative_to(root)}: source_file or source_row column missing")
            continue
        empty = df[(df["source_file"] == "") | (df["source_row"] == "")]
        if len(empty):
            bad = True
            d.append(f"{t.relative_to(root)}: {len(empty)} rows without source_file or source_row")
        for f, grp in df.groupby("source_file"):
            src = K.find_source(root, f)
            if src is None:
                d.append(f"{t.relative_to(root)}: source file not found locally: {f}")
                continue
            n_lines = len(K.decode(src.read_bytes()).replace("\r\n", "\n").replace("\r", "\n").rstrip("\n").split("\n")) \
                if src.suffix.lower() not in (".xlsx", ".xls", ".xlsm") else None
            for v in grp["source_row"]:
                if not str(v).isdigit():
                    bad = True
                    d.append(f"{t.relative_to(root)}: source_row '{v}' is not a row number")
                    break
                if n_lines is not None and not (2 <= int(v) <= n_lines):
                    bad = True
                    d.append(f"{t.relative_to(root)}: source_row {v} is outside {f} (1..{n_lines})")
                    break
    add(2, "No row without source_file or source_row", "FAIL" if bad else "PASS", d)

    # 3. units
    d, bad, warn = [], False, False
    for t in tables:
        df = _read(t)
        for col in K.NUMERIC_COLUMNS:
            vals = df[col][df[col] != ""] if col in df else []
            for v in vals:
                try:
                    float(v)
                except ValueError:
                    bad = True
                    d.append(f"{t.relative_to(root)}: {col} has a non-number '{v}'")
                    break
        if "flow_speed_value" in df:
            no_unit = df[(df["flow_speed_value"] != "") & (df["flow_speed_unit"] == "")]
            if len(no_unit):
                bad = True
                d.append(f"{t.relative_to(root)}: {len(no_unit)} flow speeds without flow_speed_unit")
            units = sorted(set(df["flow_speed_unit"]) - {""})
            if len(units) > 1:
                warn = True
                d.append(f"{t.relative_to(root)}: mixed flow units {units}: convert and log, or explain in notes")
        if "gravity_level" in df:
            odd = sorted(set(df["gravity_level"]) - K.GRAVITY_LEVELS - {""})
            if odd:
                warn = True
                d.append(f"{t.relative_to(root)}: gravity_level values not in the standard list: {odd}")
    add(3, "Units stated; mixed units converted and logged", "FAIL" if bad else ("WARN" if warn else "PASS"), d)

    # 4. findings
    d, bad, n_find = [], False, 0
    pat = re.compile(rf"^F-{track}-\d+$")
    for r in recs:
        fm = r / "findings.md"
        if not fm.exists():
            continue
        for ln, line in enumerate(fm.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip().startswith("F-"):
                continue
            n_find += 1
            parts = [p.strip() for p in line.split("|")]
            where = f"{fm.relative_to(root)} line {ln}"
            if len(parts) != 7:
                bad = True
                d.append(f"{where}: needs 7 fields separated by |, has {len(parts)}")
                continue
            fid, stmt, label, sfile, rowpage, conf, caveat = parts
            if not pat.match(fid):
                bad = True
                d.append(f"{where}: id '{fid}' should look like F-{track}-1")
            if not label.upper().startswith(K.FINDING_LABELS):
                bad = True
                d.append(f"{where}: label must be one of {', '.join(K.FINDING_LABELS)}")
            if label.upper().startswith("REPORTED BY NASA") and "(" not in label:
                bad = True
                d.append(f"{where}: REPORTED BY NASA OR A PUBLICATION needs the source in brackets")
            if not sfile or not rowpage:
                bad = True
                d.append(f"{where}: source file and row or page are required")
            if conf.lower() not in K.CONFIDENCE:
                bad = True
                d.append(f"{where}: confidence must be high, medium or low")
            if not stmt or not caveat:
                bad = True
                d.append(f"{where}: statement and caveat are required")
    if n_find == 0:
        d.append("no findings yet")
    add(4, "Every finding has source, row or page, and label", "FAIL" if bad else ("WARN" if not n_find else "PASS"), d)

    # 5. data log present; raw files unchanged
    d, bad = [], False
    for r in recs:
        dl = r / "data_log.md"
        if not dl.exists() or K.DATA_LOG_HEADER not in dl.read_text(encoding="utf-8"):
            bad = True
            d.append(f"{dl.relative_to(root)}: missing, or without the format line")
        elif _tables(r) and K.AUTO_START not in dl.read_text(encoding="utf-8"):
            d.append(f"{dl.relative_to(root)}: table exists but no build_run_table section (built by hand? log every change)")
    sums = root / "data" / "CHECKSUMS.csv"
    if sums.exists():
        changed = []
        with open(sums, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                p = root / row["path"]
                if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != row["sha256"]:
                    changed.append(row["path"])
        if changed:
            bad = True
            d.append("raw files changed or missing: " + ", ".join(changed[:5]))
    else:
        d.append("data/CHECKSUMS.csv not found: experimental tables not checked")
    man = root / "data" / "raw" / "manifest.csv"
    if man.exists():
        latest = {}
        with open(man, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                latest[row["local_path"]] = row
        changed = []
        for lp, row in latest.items():
            lp = lp.replace("\\", "/")  # manifests written on Windows use backslashes
            p = Path(lp) if Path(lp).is_absolute() else root / lp
            if row["status"] in ("ok", "exists") and p.exists() and row["bytes"].isdigit() and int(row["bytes"]) \
                    and p.stat().st_size != int(row["bytes"]):
                changed.append(lp)
        if changed:
            bad = True
            d.append("downloaded files whose size changed since download: " + ", ".join(changed[:5]))
    add(5, "data_log.md covers changes; raw files unchanged", "FAIL" if bad else "PASS", d)

    # 6. references
    d, bad = [], False
    ref = base / "references.md"
    text = ref.read_text(encoding="utf-8") if ref.exists() else ""
    used = {r.name.split("_")[0] for r in recs}
    for t in tables:
        used |= set(_read(t).get("investigation_id", []))
    missing = sorted(i for i in used if i and i not in text)
    if not ref.exists():
        bad = True
        d.append("references.md is missing")
    if missing:
        bad = True
        d.append("PSI records not in references.md: " + ", ".join(missing))
    if "[replace" in text.lower():
        bad = True
        d.append("references.md still has '[replace ...]' placeholders: paste the PSI 'Cite this Investigation' text")
    add(6, "references.md lists every PSI record, paper and tool", "FAIL" if bad else "PASS", d)

    # 7. si_log
    si = base / "si_log.md"
    entries = [l for l in si.read_text(encoding="utf-8").splitlines() if l.count("|") >= 5 and not l.startswith("time")] \
        if si.exists() else []
    add(7, "si_log.md is up to date", "FAIL" if not si.exists() else ("PASS" if entries else "WARN"),
        [f"{len(entries)} entries; only you can confirm it is up to date"] if si.exists() else ["si_log.md is missing"])

    # 8. size, secrets, media dumps
    d, bad = [], False
    for p in base.rglob("*") if base.exists() else []:
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if p.stat().st_size > MAX_BYTES:
            bad = True
            d.append(f"{rel}: larger than 50 MB")
        if p.suffix.lower() in MEDIA:
            bad = True
            d.append(f"{rel}: raw video, image or archive file")
        if p.suffix.lower() in IMAGES and "charts" not in p.parts:
            d.append(f"{rel}: image outside charts/")
        if p.suffix.lower() in TEXT_EXT and p.stat().st_size < 5 * 1024 * 1024:
            if SECRET.search(p.read_text(encoding="utf-8", errors="ignore")):
                bad = True
                d.append(f"{rel}: looks like it contains a key, token or password")
    add(8, "No file over 50 MB, no secrets, no raw video or image dumps", "FAIL" if bad else "PASS", d)

    # 9. reproducible scripts
    d = []
    for r in recs:
        rd = r / "scripts" / "README.md"
        if not rd.exists():
            d.append(f"{rd.relative_to(root)} is missing (write the run order)")
            continue
        listed = rd.read_text(encoding="utf-8")
        for s in sorted((r / "scripts").glob("*.py")):
            if s.name not in listed:
                d.append(f"{s.relative_to(root)} is not in the run order")
    d.append("run every command of each scripts/README.md from a fresh copy and compare the outputs")
    add(9, "Scripts re-run from scratch and reproduce outputs", "MANUAL", d)

    # 10. unconfirmed labelled
    d, bad = [], False
    for r in recs:
        cj = r / "card.json"
        if cj.exists():
            card = json.loads(cj.read_text(encoding="utf-8"))
            if not str(card.get("verified_by", "")).strip() or not str(card.get("verified_on", "")).strip():
                bad = True
                d.append(f"{cj.relative_to(root)}: not checked on the PSI page yet (fill verified_on and verified_by "
                         "after checking every field, and write 'unconfirmed' where the page does not show it)")
    for p in base.rglob("*") if base.exists() else []:
        if p.is_file() and p.suffix.lower() in (".md", ".json", ".yaml", ".yml") and p.name != "SELF_CHECK.md":
            hits = [i for i, l in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1)
                    if K.TODO in l and not l.lstrip().startswith("#")]
            if hits:
                bad = True
                d.append(f"{p.relative_to(root)}: TODO left on line(s) {', '.join(map(str, hits[:8]))}")
    add(10, "Anything unconfirmed is labelled unconfirmed", "FAIL" if bad else "PASS", d)
    return res


def render(track: str, res) -> str:
    t = K.TRACKS[track]
    lines = [f"# Self-check: {track} ({t['member']})", "",
             "| # | Item | Result |", "| --- | --- | --- |"]
    lines += [f"| {n} | {title} | {status} |" for n, title, status, _ in res]
    for n, title, status, details in res:
        if details:
            lines += ["", f"**{n}. {title}: {status}**", *[f"- {x}" for x in details]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", help="T1..T6 or your surname")
    args = ap.parse_args(argv)
    track = K.track_id(args.track)
    res = check(track)
    md = render(track, res)
    out = K.ROOT / "analysis" / track / "SELF_CHECK.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(md)
    print(f"written to {out.relative_to(K.ROOT)}")
    return 1 if any(s == "FAIL" for _, _, s, _ in res) else 0


if __name__ == "__main__":
    sys.exit(main())
