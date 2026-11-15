#!/usr/bin/env python3
"""Merge everything in content/ and data/derived/ into the JSON files the website reads.

The site never reads content/ directly. It reads only site_data/*.json, so a new card, finding,
model or member appears on the site after `python -m pipeline.build` with no code change.

  site_data/investigations.json   psi.json + card.yaml (+ si.json when present) per investigation
  site_data/findings.json         front matter + Markdown body
  site_data/models.json           model cards (+ predictions.json when present)
  site_data/members.json          members with their contribution counts
  site_data/scenarios.json        habitat envelopes
  site_data/ranking.json          copied from data/derived (if built)
  site_data/envelope_points.json  copied from data/derived (if built)
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import Counter

import pandas as pd

from .common import CONTENT, DERIVED, ROOT, load_markdown, load_yaml, write_json

SITE = ROOT / "site_data"


def _json_or_none(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def export() -> dict:
    SITE.mkdir(exist_ok=True)
    investigations = []
    for d in sorted((CONTENT / "investigations").glob("PSI-*"), key=lambda p: int(p.name.split("-")[1])):
        card = load_yaml(d / "card.yaml") if (d / "card.yaml").exists() else None
        investigations.append({"id": d.name, "psi": _json_or_none(d / "psi.json"), "card": card,
                               "si": _json_or_none(d / "si.json"), "curated": card is not None})

    findings = []
    for p in sorted((CONTENT / "findings").glob("*.md")):
        if p.name.startswith("_"):
            continue
        meta, body = load_markdown(p)
        if hasattr(meta.get("date"), "isoformat"):
            meta["date"] = meta["date"].isoformat()
        findings.append({"slug": p.stem, **meta, "body_markdown": body})

    models = []
    for d in sorted((CONTENT / "models").glob("*")):
        if d.is_dir() and not d.name.startswith("_") and (d / "model.yaml").exists():
            m = load_yaml(d / "model.yaml")
            art = m.get("artifact")
            if art and art.endswith(".json") and (d / art).exists():
                m["predictions"] = json.loads((d / art).read_text(encoding="utf-8"))
            models.append(m)

    authored = Counter()
    for inv in investigations:
        if inv["card"]:
            authored[(inv["card"]["author"], "cards")] += 1
    for f in findings:
        authored[(f["author"], "findings")] += 1
    for m in models:
        authored[(m["author"], "models")] += 1
    members = []
    for p in sorted((CONTENT / "members").glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        m = load_yaml(p)
        m["contributions"] = {k: authored[(m["id"], k)] for k in ("cards", "findings", "models")}
        members.append(m)

    scenarios = [load_yaml(p) for p in sorted((CONTENT / "scenarios").glob("*.yaml"))]

    write_json(SITE / "investigations.json", investigations)
    write_json(SITE / "findings.json", findings)
    write_json(SITE / "models.json", models)
    write_json(SITE / "members.json", members)
    write_json(SITE / "scenarios.json", scenarios)
    if (DERIVED / "ranking.json").exists():
        shutil.copy(DERIVED / "ranking.json", SITE / "ranking.json")
    if (DERIVED / "envelope_points.csv").exists():
        pts = pd.read_csv(DERIVED / "envelope_points.csv")
        write_json(SITE / "envelope_points.json", json.loads(pts.to_json(orient="records")))
    return {"investigations": len(investigations), "curated": sum(i["curated"] for i in investigations),
            "findings": len(findings), "models": len(models), "members": len(members)}


def main() -> int:
    print("site_data:", export())
    return 0


if __name__ == "__main__":
    sys.exit(main())
