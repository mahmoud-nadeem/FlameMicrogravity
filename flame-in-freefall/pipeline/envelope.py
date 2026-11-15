#!/usr/bin/env python3
"""Oxygen x pressure envelope of every PSI test, and how it covers each habitat scenario.

Reads the experimental tables written by build_catalog.py and the scenarios in
content/scenarios/*.yaml; writes

  data/derived/envelope_points.csv     one row per test that records O2 (and pressure when known)
  data/derived/scenario_coverage.json  per scenario x investigation: tests inside the envelope

Two oxygen meanings are kept apart on purpose:
  mode = ambient          the chamber atmosphere holds the O2 (closest to a cabin fire)
  mode = burner-oxidizer  inverse flames: O2 flows out of the burner into a fuel atmosphere

Usage: python -m pipeline.envelope
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .common import BAR_PER_ATM, CONTENT, DERIVED, ET_DIR, MMHG_PER_ATM, PSI_PER_ATM, load_yaml, read_table, to_number, write_json


@dataclass(frozen=True)
class Extractor:
    investigation: str
    acronym: str
    file_suffix: str            # end of the experimental-table file name
    mode: str                   # ambient | burner-oxidizer
    o2_col: str
    o2_scale: float             # multiply to get a mole fraction (1 for fractions, 0.01 for %)
    p_col: str | None
    p_to_atm: float | None      # divide by this to get atm
    fuel_col: str | None
    fuel_default: str
    outcome_col: str | None
    id_col: str
    fuel_type: str              # solid | liquid-droplet | gas


# Column names verified against the real tables on 2026-11-14 (headers are whitespace-normalised).
EXTRACTORS: list[Extractor] = [
    Extractor("PSI-69", "FLEX", "Experimental table_FLEX.csv", "ambient",
              "O initial ambient composition; mole fraction", 1.0, "Ambient pressure; mmHg", MMHG_PER_ATM,
              "Fuel", "", "Test end", "FLEX Test #", "liquid-droplet"),
    Extractor("PSI-39", "CFI", "Experimental table_CFI.csv", "ambient",
              "Oxygen", 1.0, "Pressure", 1.0, "Fuel", "", None, "Flex Number", "liquid-droplet"),
    Extractor("PSI-159", "CFI-G", "CFI-G_Normal Flames.csv", "ambient",
              "XO2 before test", 1.0, "approx p (bar)", BAR_PER_ATM, "Fuel", "", "Hot ignition", "Test", "gas"),
    Extractor("PSI-159", "CFI-G", "CFI-G_Inverse Flames.csv", "burner-oxidizer",
              "XO2", 1.0, "approx p (bar)", BAR_PER_ATM, "Fuel", "", "Hot ignition", "Test", "gas"),
    Extractor("PSI-10", "Flame Design", "Flame Design_Normal Flame.csv", "ambient",
              "XO2 (init)", 1.0, "pinit (atm)", 1.0, "Fuel", "", None, "Test", "gas"),
    Extractor("PSI-10", "Flame Design", "Flame Design_Inverse Flame.csv", "burner-oxidizer",
              "XO2", 1.0, "pinit (atm)", 1.0, None, "C2H4", None, "Test", "gas"),
    # Solids: oxygen recorded, chamber pressure not in the table (glovebox at cabin pressure).
    Extractor("PSI-25", "BASS-II", "Experimental table_BASS-II.csv", "ambient",
              "Calibrated initial O2 % by vol", 0.01, None, None, "Fuel Sample Material", "", None, "Test #", "solid"),
]


def extract_points(et_dir: Path = ET_DIR) -> pd.DataFrame:
    rows = []
    for ex in EXTRACTORS:
        matches = sorted((et_dir / ex.investigation).rglob(f"*{ex.file_suffix}"))
        if not matches:
            print(f"  ! no table for {ex.investigation} *{ex.file_suffix} (run build_catalog first)")
            continue
        df = read_table(matches[0])
        missing = [c for c in [ex.o2_col, ex.p_col, ex.fuel_col, ex.outcome_col, ex.id_col] if c and c not in df.columns]
        if missing:
            raise KeyError(f"{matches[0].name}: columns not found {missing}; headers are {list(df.columns)}")
        for _, r in df.iterrows():
            o2 = to_number(r[ex.o2_col])
            if o2 is None:
                continue  # 'RAMP', 'LOW O2', blank: no single value for this test
            p = to_number(r[ex.p_col]) if ex.p_col else None
            p_atm = p / ex.p_to_atm if (p is not None and p > 0 and ex.p_to_atm) else None  # 0 mmHg = missing
            rows.append({
                "investigation": ex.investigation, "acronym": ex.acronym, "test_id": str(r[ex.id_col]).strip(),
                "mode": ex.mode, "fuel_type": ex.fuel_type,
                "fuel": (str(r[ex.fuel_col]).strip() if ex.fuel_col else ex.fuel_default),
                "o2_frac": round(o2 * ex.o2_scale, 6), "p_atm": None if p_atm is None else round(p_atm, 6),
                "outcome": (str(r[ex.outcome_col]).strip().capitalize() if ex.outcome_col else ""),  # "yes"/"Yes" -> "Yes"
            })
    return pd.DataFrame(rows)


def load_scenarios(folder: Path = CONTENT / "scenarios") -> list[dict]:
    out = []
    for path in sorted(folder.glob("*.yaml")):
        sc = load_yaml(path)
        o2 = sc["o2_percent"]
        p = sc["pressure_psi"]
        sc["_o2"] = (o2[0] / 100.0, o2[1] / 100.0)
        sc["_p_atm"] = (p[0] / PSI_PER_ATM, p[1] / PSI_PER_ATM)
        out.append(sc)
    return out


def inside(o2: float, p_atm: float | None, sc: dict, tol: float = 0.0) -> bool:
    """True if a test lies inside the scenario envelope. tol widens both ranges by a relative margin."""
    if p_atm is None:
        return False
    (o_lo, o_hi), (p_lo, p_hi) = sc["_o2"], sc["_p_atm"]
    return (o_lo * (1 - tol) <= o2 <= o_hi * (1 + tol)) and (p_lo * (1 - tol) <= p_atm <= p_hi * (1 + tol))


def coverage(points: pd.DataFrame, scenarios: list[dict], near_tol: float = 0.05) -> dict:
    result = {}
    for sc in scenarios:
        per_inv = {}
        for inv, g in points.groupby("investigation"):
            rec = {"acronym": g["acronym"].iloc[0], "tests_with_o2": int(len(g)),
                   "tests_with_o2_and_pressure": int(g["p_atm"].notna().sum()),
                   "max_ambient_o2": None, "min_pressure_atm": None, "by_mode": {}}
            amb = g[g["mode"] == "ambient"]
            if len(amb):
                rec["max_ambient_o2"] = float(amb["o2_frac"].max())
            if g["p_atm"].notna().any():
                rec["min_pressure_atm"] = float(g["p_atm"].min())
            for mode, gm in g.groupby("mode"):
                ins = gm[[inside(o, p, sc) for o, p in zip(gm["o2_frac"], gm["p_atm"])]]
                near = gm[[inside(o, p, sc, near_tol) for o, p in zip(gm["o2_frac"], gm["p_atm"])]]
                rec["by_mode"][mode] = {
                    "inside": int(len(ins)),
                    f"within_{int(near_tol * 100)}pct": int(len(near)),
                    "outcomes_inside": {k: int(v) for k, v in ins["outcome"].value_counts().items() if k},
                }
            per_inv[inv] = rec
        result[sc["id"]] = {"name": sc["name"], "o2_frac": sc["_o2"], "pressure_atm": sc["_p_atm"],
                            "investigations": per_inv}
    return result


def main() -> int:
    pts = extract_points()
    if pts.empty:
        print("no points extracted")
        return 1
    DERIVED.mkdir(parents=True, exist_ok=True)
    pts.to_csv(DERIVED / "envelope_points.csv", index=False)
    cov = coverage(pts, load_scenarios())
    write_json(DERIVED / "scenario_coverage.json", cov)
    print(f"{len(pts)} tests with O2; {int(pts['p_atm'].notna().sum())} also with pressure")
    for sid, sc in cov.items():
        ins = {k: sum(m["inside"] for m in v["by_mode"].values()) for k, v in sc["investigations"].items()}
        print(f"  {sid}: " + json.dumps({k: v for k, v in ins.items() if v}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
