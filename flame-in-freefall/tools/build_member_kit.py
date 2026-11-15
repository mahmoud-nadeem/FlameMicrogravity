#!/usr/bin/env python3
"""Assemble the team kit zip from this repository (run by the kit maintainer, not by members).

    python tools/build_member_kit.py --version 3     ->  ../flame-in-freefall-kit_v3.zip

Builds the kit in a temporary folder, generates every track folder, runs the kit's tests there,
and only then writes the zip. The dashboard pipeline, content/ cards and site_data are not part
of the kit: the team package standard is Mohammed Tamer's.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import kitlib as K  # noqa: E402

REPO = K.ROOT
FILES = [
    "scripts/psi_fetch.py", "scripts/psi_parsers.py", "pipeline/__init__.py", "pipeline/psi_api.py",
    "tools/__init__.py", "tools/kitlib.py", "tools/new_track.py", "tools/profile_files.py",
    "tools/build_run_table.py", "tools/self_check.py", "tools/package.py",
    "tools/templates/no_model.md", "tools/templates/model_README.md", "tools/templates/idea_ticket.md",
    "tests/test_parsers.py", "tests/test_psi_api.py", "tests/test_kit_tools.py",
]
REQUIREMENTS = """requests>=2.31
pandas>=2.1
numpy>=1.26
matplotlib>=3.8
scipy>=1.11
scikit-learn>=1.3
openpyxl>=3.1
xlrd>=2.0
PyYAML>=6.0
pytest>=8.0
"""
GITIGNORE = "data/raw/\n__pycache__/\n*.pyc\n.pytest_cache/\n*.part\n.env\nT*_v*.zip\n"
SKIP = {"__pycache__", ".pytest_cache"}


def build(version: int, out_dir: Path) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="ffkit_"))
    kit = tmp / "flame-in-freefall-kit"
    for rel in FILES:
        dst = kit / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dst)
    shutil.copy2(REPO / "tools" / "START_HERE.md", kit / "START_HERE.md")
    (kit / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
    (kit / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
    shutil.copytree(REPO / "data" / "experimental_tables", kit / "data" / "experimental_tables")
    meta_dir = kit / "data" / "psi_metadata"
    meta_dir.mkdir(parents=True)
    for p in sorted((REPO / "content" / "investigations").glob("PSI-*/psi.json")):
        shutil.copy2(p, meta_dir / f"{p.parent.name}.json")
    with open(kit / "data" / "CHECKSUMS.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["path", "sha256", "bytes"])
        for p in sorted((kit / "data" / "experimental_tables").rglob("*")):
            if p.is_file():
                w.writerow([p.relative_to(kit).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size])

    r = subprocess.run([sys.executable, "tools/new_track.py", "all"], cwd=kit, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        raise SystemExit(r.stderr)
    t = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=kit,
                       capture_output=True, text=True)
    print(t.stdout.strip().splitlines()[-1] if t.stdout.strip() else t.stderr)
    if t.returncode:
        raise SystemExit("kit tests failed:\n" + t.stdout[-3000:])
    for p in list(kit.rglob("__pycache__")):
        shutil.rmtree(p, ignore_errors=True)

    out = out_dir / f"flame-in-freefall-kit_v{version}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(kit.rglob("*")):
            if p.is_file() and not (SKIP & set(p.parts)):
                z.write(p, p.relative_to(tmp).as_posix())
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", type=int, required=True)
    ap.add_argument("--out-dir", type=Path, default=REPO.parent)
    args = ap.parse_args(argv)
    out = build(args.version, args.out_dir)
    n = len(zipfile.ZipFile(out).namelist())
    print(f"{out}  ({n} files, {out.stat().st_size / 1024:,.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
