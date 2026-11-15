#!/usr/bin/env python3
"""Rank investigations by relevance to each habitat scenario, with every score explained.

score = w_env * envelope + w_mat * material + w_data * readiness      (each component is 0..1)

  envelope   do the investigation's tests sit inside the scenario's O2/pressure envelope?
             1.0 ambient-atmosphere tests inside | 0.6 only burner-oxygen (inverse) tests inside
             0.5 tests within 5% of the envelope | 0.8 card ranges overlap (no per-test data)
             otherwise up to 0.5 by how close the card ranges reach the envelope
  material   how close the fuel is to what burns in a habitat (solids and smoke rank highest)
  readiness  how usable the data are for analysis and modeling

The weights are defaults, not truths: the dashboard lets users move them and re-rank.
Writes data/derived/ranking.json.  Usage: python -m pipeline.rank
"""
from __future__ import annotations

import json
import sys

from .common import CONTENT, DERIVED, load_yaml, write_json
from .envelope import load_scenarios

DEFAULT_WEIGHTS = {"envelope": 0.5, "material": 0.3, "readiness": 0.2}
MATERIAL = {"solid": 1.0, "smoke-aerosol": 0.9, "mixed": 0.7, "gas": 0.6, "liquid-droplet": 0.6, "dust-aerosol": 0.3}
READINESS = {"per-test-time-series": 1.0, "processed-table": 0.8, "raw-only": 0.4, "metadata-only": 0.1}


def _overlaps(a, b) -> bool:
    return a is not None and b is not None and a[0] <= b[1] and b[0] <= a[1]


def envelope_component(card: dict, scenario: dict, cov: dict | None) -> tuple[float, str]:
    if cov:
        modes = cov.get("by_mode", {})
        if modes.get("ambient", {}).get("inside", 0) > 0:
            return 1.0, f"{modes['ambient']['inside']} ambient-atmosphere tests inside the envelope"
        if modes.get("burner-oxidizer", {}).get("inside", 0) > 0:
            return 0.6, f"{modes['burner-oxidizer']['inside']} inverse-flame tests inside (oxygen from the burner)"
        near = sum(m.get("within_5pct", 0) for m in modes.values())
        if near > 0:
            return 0.5, f"{near} tests within 5% of the envelope edge"
    cond = card.get("conditions") or {}
    o2 = [x / 100.0 for x in cond["o2_percent"]] if cond.get("o2_percent") else None
    p = cond.get("pressure_atm")
    s_o2, s_p = scenario["_o2"], scenario["_p_atm"]
    if _overlaps(o2, s_o2) and _overlaps(p, s_p):
        return 0.8, "card ranges overlap the envelope (no per-test check)"
    reach_o2 = 0.5 if o2 is None else (1.0 if o2[1] >= s_o2[0] and o2[0] <= s_o2[1] else
                                       (o2[1] / s_o2[0] if o2[1] < s_o2[0] else s_o2[1] / o2[0]))
    reach_p = 0.5 if p is None else (1.0 if _overlaps(p, s_p) else
                                     (s_p[1] / p[0] if p[0] > s_p[1] else p[1] / s_p[0]))
    known = "O2 and pressure" if (o2 and p) else ("O2 only" if o2 else ("pressure only" if p else "no O2 or pressure"))
    return round(0.5 * reach_o2 * reach_p, 3), f"outside the envelope; proximity from card ranges ({known})"


def rank(weights: dict | None = None, coverage: dict | None = None) -> dict:
    """coverage=None reads data/derived/scenario_coverage.json if it exists; pass {} to rank from card ranges only."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    if coverage is None:
        cov_path = DERIVED / "scenario_coverage.json"
        coverage = json.loads(cov_path.read_text()) if cov_path.exists() else {}
    cards = {d.name: load_yaml(d / "card.yaml") for d in sorted((CONTENT / "investigations").glob("PSI-*"))
             if (d / "card.yaml").exists()}
    out = {"weights": w, "material_scores": MATERIAL, "readiness_scores": READINESS,
           "coverage_available": bool(coverage), "scenarios": {}}
    for sc in load_scenarios():
        rows = []
        sc_cov = coverage.get(sc["id"], {}).get("investigations", {})
        for inv, card in cards.items():
            env, why = envelope_component(card, sc, sc_cov.get(inv))
            mat = MATERIAL.get(card["fuel_type"], 0.5)
            rdy = READINESS.get(card["data_readiness"], 0.5)
            score = w["envelope"] * env + w["material"] * mat + w["readiness"] * rdy
            rows.append({"id": inv, "score": round(score, 3), "envelope": env, "material": mat,
                         "readiness": rdy, "why_envelope": why, "fuel_type": card["fuel_type"],
                         "pillars": card["pillars"]})
        rows.sort(key=lambda r: -r["score"])
        for i, r in enumerate(rows, 1):
            r["rank"] = i
        out["scenarios"][sc["id"]] = {"name": sc["name"], "ranking": rows}
    return out


def main() -> int:
    result = rank()
    write_json(DERIVED / "ranking.json", result)
    if not result["coverage_available"]:
        print("note: data/derived/scenario_coverage.json missing; envelope uses card ranges only")
    for sid, sc in result["scenarios"].items():
        top = ", ".join(f"{r['id']} {r['score']:.2f}" for r in sc["ranking"][:4])
        print(f"  {sid}: {top}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
