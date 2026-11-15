#!/usr/bin/env python3
"""Run the self-check and zip your track for Mohammed Tamer (section 8).

    python tools/package.py T3 --version 1     ->  T3_nadeem_v1.zip in the kit root

The zip holds analysis/<track>/ only (with SELF_CHECK.md); files over 50 MB and caches are left
out. A failing self-check does not stop the package (late is better than missing), but HANDOFF.md
must say what failed.
"""
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import kitlib as K  # noqa: E402
from tools import self_check  # noqa: E402

SKIP_DIRS = {"__pycache__", ".ipynb_checkpoints", ".pytest_cache"}


def package(track: str, version: int, root: Path = K.ROOT) -> tuple[Path, list[str], list]:
    root = Path(root)
    res = self_check.check(track, root)
    base = root / "analysis" / track
    (base / "SELF_CHECK.md").write_text(self_check.render(track, res), encoding="utf-8")
    out = root / f"{track}_{K.TRACKS[track]['surname']}_v{version}.zip"
    left_out = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(base.rglob("*")):
            if not p.is_file() or SKIP_DIRS & set(p.parts) or p.name == ".DS_Store":
                continue
            if p.stat().st_size > self_check.MAX_BYTES:
                left_out.append(p.relative_to(root).as_posix())
                continue
            z.write(p, p.relative_to(root).as_posix())
    return out, left_out, res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", help="T1..T6 or your surname")
    ap.add_argument("--version", type=int, required=True, help="1, 2, 3 ... (one more each time you resend)")
    args = ap.parse_args(argv)
    track = K.track_id(args.track)
    out, left_out, res = package(track, args.version)
    for n, title, status, _ in res:
        print(f"{n:>2}. {status:<6} {title}")
    if left_out:
        print("left out (over 50 MB): " + ", ".join(left_out))
    print(f"\npackage: {out.name}  ({out.stat().st_size / 1024:,.0f} KB)")
    failed = [n for n, _, s, _ in res if s == "FAIL"]
    if failed:
        print(f"self-check items failing: {failed}. Send anyway if the deadline is now, and say so in HANDOFF.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
