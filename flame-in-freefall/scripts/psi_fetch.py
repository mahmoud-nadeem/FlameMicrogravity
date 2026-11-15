#!/usr/bin/env python3
"""Download only the processed results and telemetry of NASA PSI combustion datasets.

The raw archives are terabytes of images; the files we analyse are small tables, text logs and
workbooks. Each profile below lists the investigation(s) and the file-name patterns to keep.
Each team track (t1..t6, or the member's id) groups the profiles of that track.

Usage (from the repo root):
  python scripts/psi_fetch.py --datasets t4 --list-only     # what your track would download, no download
  python scripts/psi_fetch.py --datasets t4                 # download it (resumes if interrupted)
  python scripts/psi_fetch.py --datasets tamer              # same thing, by member id
  python scripts/psi_fetch.py --datasets flex same          # single profiles
  python scripts/psi_fetch.py --datasets bass-video --max-files 10 --max-mb 40
  python scripts/psi_fetch.py --datasets cld                # PSI-21: data + setpoints CSV of every "... Raw Data" folder

Files land in data/raw/<PSI-ID>/...; every file is logged in data/raw/manifest.csv with its DOI.
Data are CC0 (PSI-10 has no license field; check before redistributing).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pipeline import psi_api as api  # noqa: E402

ET = r"/Experimental table/"
ACME = [ET, r"_data\d*\.csv$", r"_mfcSetpoints\.csv$", r"_Comments\.txt$"]  # ACME sensor logs + setpoints + notes
SAFFIRE = [ET, r"/Raw Data/.*\.(xlsx|csv)$", r"/Science Documents/"]

# Sizes in the comments were measured from the PSI file listing on 14 Nov 2026.
PROFILES: dict[str, list[tuple[str, list[str]]]] = {
    # T1 solids
    "bass": [("PSI-25", [ET, r"ProofSheet\.pdf$"]), ("PSI-26", [ET])],                  # ~0.2 GB
    "bass-video": [("PSI-25", [r"\.mp4$"]), ("PSI-26", [r"\.mp4$"])],                  # 40 GB uncapped: see LIMITS
    # T2 spacecraft-scale fire
    "saffire": [("PSI-98", SAFFIRE), ("PSI-99", SAFFIRE), ("PSI-100", SAFFIRE)],       # ~0.38 GB
    # T3 smoke and dust detection
    "same": [("PSI-101", [ET, r"SAME, SAME-R_Results\.xlsx$", r"HKPData_.*\.csv$"]),
             ("PSI-102", [ET, r"/Analyzed Data/.*\.xlsx?$"])],                          # ~0.26 GB
    "daft": [("PSI-47", [r"."])],                                                      # ~0.04 GB, everything
    # T4 droplets, suppression, cool flames
    "flex": [("PSI-69", [ET, r"_(DropletData|LLUVData|ColorCamData|TestSheet)\.txt$"])],  # ~0.02 GB
    "flex2": [("PSI-68", [ET, r"/Raw Data/.*\.txt$"])],                                # ~0.53 GB telemetry
    "cfi": [("PSI-39", [ET, r"_(Radiometer|Chamber)_Readings\.txt$", r"_Comments\.txt$", r"/Analyzed Data/"])],  # ~0.09 GB
    "cfig": [("PSI-159", ACME)],                                                       # ~1.47 GB
    # T5 ACME gas flames
    "bre": [("PSI-20", ACME)],                                                         # ~1.1 GB
    "efield": [("PSI-22", ACME)],                                                      # ~1.5 GB
    "sflame": [("PSI-23", ACME)],                                                      # ~0.77 GB
    "flamedesign": [("PSI-10", ACME)],                                                 # ~1.25 GB
    # T6 coflow and jet flames
    "spice": [("PSI-107", [ET, r"\.xls$"])],                                           # ~0.02 GB
    "slice": [("PSI-106", [ET, r"\.xlsx?$"])],                                         # ~0.01 GB (no results table)
    # PSI-21 (requested by Mohamed Gamal): in every folder whose name ends with "Raw Data" (as the PSI
    # page shows them, e.g. Raw Data/Legacy/17319A3 Raw Data), the <test>_data.csv and
    # <test>_mfcSetpoints.csv files; saved in those same folders (see LAYOUT). ~1.38 GB.
    "cld": [("PSI-21", [ET, r"page:(?i)(^|/)[^/]*Raw Data/[^/]*_(data\d*|mfcSetpoints)\.csv$"])],
}

# Applied only when the user does not pass --max-files / --max-mb.
PROFILES["t3-docs"] = [("PSI-102", [r"/Reports/", r"/Science Documents/"]),   # ~5 MB
                       ("PSI-101", [r"/Reports/", r"/Science Documents/"]),   # ~6 MB
                       ("PSI-47", [r"/Reports/"])]                             # ~14 MB

LIMITS: dict[str, dict[str, float]] = {"bass-video": {"max_files": 20, "max_mb": 60}}

# Where files are saved: "key" = folders of the storage key (default); "page" = folders as the PSI
# page shows them. PSI-21 keys are flat (Raw Data/<file>) while its page has one folder per test.
LAYOUT: dict[str, str] = {"cld": "page"}

# Complete-folder rule (requested by Mohamed Gamal for PSI-21): a folder whose page name ends with
# "Raw Data" is downloaded only if it has BOTH a <test>_data.csv and a <test>_mfcSetpoints.csv file.
# Folders missing either are skipped and listed in a text report next to the data.
COMPLETE_FOLDERS: dict[str, dict] = {
    "cld": {"folder": r"(?i)^.+\sraw data$",          # '<test> Raw Data', not the parent 'Raw Data' folder
            "require": {"data": r"(?i)_data\d*\.csv$", "setpoints": r"(?i)_mfcSetpoints\.csv$"},
            "report": "PSI-21_incomplete_folders.txt"},
}


def check_folders(all_files: list, rule: dict) -> tuple[dict, dict]:
    """-> (folders: name -> files, incomplete: name -> list of missing kinds), using the page folders."""
    folder_re = re.compile(rule["folder"])
    req = {k: re.compile(v) for k, v in rule["require"].items()}
    folders: dict[str, list] = {}
    for f in all_files:
        if f.folder and folder_re.search(f.folder.rsplit("/", 1)[-1]):
            folders.setdefault(f.folder, []).append(f)
    incomplete = {}
    for name, fs in folders.items():
        missing = [k for k, rg in req.items() if not any(rg.search(x.name) for x in fs)]
        if missing:
            incomplete[name] = missing
    return folders, incomplete


def write_folder_report(path: Path, inv: str, rule: dict, folders: dict, incomplete: dict, version) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    kinds = " and ".join(f"a file matching {v}" for v in rule["require"].values())
    lines = [f"{inv}: folders whose name ends with 'Raw Data' that were NOT downloaded",
             f"Rule: a folder is downloaded only if it has {kinds}.",
             f"Checked: {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC, PSI file listing version {version}",
             f"Folders checked: {len(folders)} | complete (downloaded): {len(folders) - len(incomplete)} | "
             f"skipped: {len(incomplete)}", "",
             "folder | missing | files in the folder on PSI"]
    for name in sorted(incomplete):
        present = ", ".join(sorted(f.name for f in folders[name])) or "(none)"
        lines.append(f"{name} | {' and '.join(incomplete[name])} | {present}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

TRACKS: dict[str, list[str]] = {
    "t1": ["bass"],  # videos are opt-in (--datasets bass-video): team rule, no raw video without agreement
    "t2": ["saffire"],
    "t3": ["same", "daft"],
    "t4": ["flex", "flex2", "cfi", "cfig"],
    "t5": ["bre", "efield", "sflame", "flamedesign"],
    "t6": ["spice", "slice", "cld"],
}
MEMBER_TRACK = {"morgan": "t1", "shreif": "t2", "mahmoud": "t3", "nadeem": "t3", "tamer": "t4", "adwi": "t5",
                "gamal": "t6"}

# Kept for backwards compatibility with tests and notebooks written on Day 1.
RemoteFile = api.RemoteFile
flatten_tree = api.flatten_tree
select = api.select


def expand(names: list[str]) -> list[str]:
    """Turn track ids, member ids, profile names or 'all' into an ordered list of profiles."""
    out: list[str] = []
    for n in names:
        n = n.lower()
        if n == "all":
            items = list(PROFILES)
        elif n in MEMBER_TRACK:
            items = TRACKS[MEMBER_TRACK[n]]
        elif n in TRACKS:
            items = TRACKS[n]
        elif n in PROFILES:
            items = [n]
        else:
            raise KeyError(n)
        out += [i for i in items if i not in out]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--datasets", nargs="+", required=True,
                    help="track (t1..t6), member id (" + ", ".join(MEMBER_TRACK) + "), profile ("
                         + ", ".join(PROFILES) + ") or 'all'")
    ap.add_argument("--out", default="data/raw", type=Path)
    ap.add_argument("--list-only", action="store_true", help="print what would be downloaded")
    ap.add_argument("--max-files", type=int, default=None, help="cap files per investigation")
    ap.add_argument("--max-mb", type=float, default=None, help="skip single files larger than this")
    args = ap.parse_args(argv)

    try:
        names = expand(args.datasets)
    except KeyError as e:
        ap.error(f"unknown dataset, track or member: {e}")

    s = api.make_session()
    args.out.mkdir(parents=True, exist_ok=True)
    manifest_path = args.out / "manifest.csv"
    new_manifest = not manifest_path.exists()
    grand_files, grand_mb = 0, 0.0
    skipped: list[str] = []
    with open(manifest_path, "a", newline="", encoding="utf-8") as mf:
        w = csv.writer(mf)
        if new_manifest:
            w.writerow(["profile", "investigation", "doi", "key", "bytes", "local_path", "status"])
        for prof in names:
            limit = LIMITS.get(prof, {})
            max_files = args.max_files if args.max_files is not None else limit.get("max_files")
            max_mb = args.max_mb if args.max_mb is not None else limit.get("max_mb")
            for inv, patterns in PROFILES[prof]:
                try:
                    meta = api.get_investigation(s, inv)
                    all_files = api.list_files(s, inv, int(meta.get("version") or 1))
                    files = api.select(all_files, patterns)
                except (api.PSIUnavailable, api.requests.HTTPError) as e:
                    print(f"[{prof}] {inv}: PSI did not answer, skipped ({e.__class__.__name__}). "
                          "Run the same command again later; finished files are kept.")
                    skipped.append(inv)
                    continue
                rule = COMPLETE_FOLDERS.get(prof)
                if rule:
                    folders, incomplete = check_folders(all_files, rule)
                    files = [f for f in files if f.folder not in incomplete]
                    report = args.out / inv / rule["report"]
                    write_folder_report(report, inv, rule, folders, incomplete, meta.get("version"))
                    print(f"[{prof}] {inv}: {len(folders)} 'Raw Data' folders, {len(folders) - len(incomplete)} complete, "
                          f"{len(incomplete)} skipped (listed in {report})")
                if max_mb is not None:
                    files = [f for f in files if f.size <= max_mb * 1e6]
                if max_files is not None:
                    files = files[: int(max_files)]
                total = sum(f.size for f in files) / 1e6
                grand_files += len(files)
                grand_mb += total
                layout = LAYOUT.get(prof, "key")
                print(f"[{prof}] {inv} {meta.get('investigationAcronym', '')}: "
                      f"{len(files)} files, {total:,.1f} MB, DOI {meta.get('doi')}"
                      + (f", in {len({f.folder for f in files})} folders as on the PSI page" if layout == "page" else ""))
                if args.list_only:
                    continue
                for i, f in enumerate(files, 1):
                    status = api.download(s, f, args.out, layout=layout)
                    w.writerow([prof, inv, meta.get("doi"), f.key, f.size, f.local_path(args.out, layout), status])
                    mf.flush()
                    if status not in ("ok", "exists"):
                        print(f"  ! {f.name}: {status}")
                    if i % 50 == 0:
                        print(f"  {i}/{len(files)}")
    print(f"total: {grand_files} files, {grand_mb / 1000:,.2f} GB" + (" (list only)" if args.list_only else ""))
    failed = sum(1 for _ in _failed_rows(manifest_path)) if not args.list_only else 0
    if skipped:
        print(f"skipped because PSI did not answer: {', '.join(skipped)}")
    if failed:
        print(f"{failed} file(s) logged as error in {manifest_path}")
    if skipped or failed:
        print("The PSI server is shared by all Space Apps teams and is often busy. "
              "Run the same command again later: it only fetches what is still missing.")
        return 1
    return 0


def _failed_rows(manifest_path: Path):
    """Rows of the latest attempt per file whose status is an error (not ok, exists or missing)."""
    latest: dict[str, str] = {}
    with open(manifest_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            latest[row["key"]] = row["status"]
    return [k for k, st in latest.items() if st.startswith("error")]


if __name__ == "__main__":
    sys.exit(main())
