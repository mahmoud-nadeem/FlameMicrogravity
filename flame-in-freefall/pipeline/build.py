#!/usr/bin/env python3
"""One command for the whole data pipeline.

  python -m pipeline.build              validate -> envelope -> rank -> export (offline, uses local files)
  python -m pipeline.build --fetch      first refresh the PSI catalog and experimental tables

Stops at the first failing step so a broken contribution never reaches the site.
"""
from __future__ import annotations

import argparse
import sys

from . import build_catalog, envelope, export_site, rank, validate
from .common import ET_DIR


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="refresh catalog from the PSI API first")
    args = ap.parse_args(argv)

    if args.fetch and build_catalog.main([]) != 0:
        return 1
    print("== validate")
    if validate.main() != 0:
        return 1
    if any(ET_DIR.rglob("*.csv")):
        print("== envelope")
        if envelope.main() != 0:
            return 1
    else:
        print("== envelope skipped: no experimental tables yet (run with --fetch, or import a browser bundle)")
    print("== rank")
    rank.main()
    print("== export")
    return export_site.main()


if __name__ == "__main__":
    sys.exit(main())
