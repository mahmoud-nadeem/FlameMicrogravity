"""Tests built from the exact layouts of real PSI files read on 2026-11-14."""
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import psi_fetch as pf  # noqa: E402
import psi_parsers as pp  # noqa: E402

# First rows of PSI-69 FLEX-008_DropletData.txt (tab-separated, \r line endings)
FLEX_DROPLET = (
    "DropletTime_sec\tDropletDiameter_mm\tZeroedDropletXpos_mm\tZeroedDropletYpos_mm\r"
    "-1.333333000002312\t2.91919793102564\t0.05931506849315227\t-0.8870841487279861\r"
    "-1.30000000000291\t2.926074731911878\t0.04448630136986509\t-0.8870841487279861\r"
    "-1.266667000003508\t2.929888202488706\t0.02965753424657436\t-0.8870841487279861\r"
)

# PSI-69 FLEX-008_TestSheet.txt (abridged, same structure)
FLEX_SHEET = (
    "FLEX-008 \n\nTEST PARAMETERS \n\tTest Date: \tFriday, April 10, 2009\n\tTest Time: \t18:07:15 (GMT)\n"
    "\tCIR Test Number: \t30CAL06\n\nAMBIENT ENVIRONMENT \n\tPressure (atm) = \t 1.00 \n"
    "\tO2 Mole Fraction = \t 0.21 \n\tN2 Mole Fraction = \t 0.79 \n\tCO2 Mole Fraction = \t 0.00 \n"
    "\tHe Mole Fraction = \t 0.00 \n\tTemperature (K) = \t 300.50 \n\nTEST CONDITIONS \n\tFuel: \tHeptane \n"
    "\tD0  (mm) = \t2.95 \n\tkavg  (mm2/s) = \t0.79 \n\tFiber: \tNo\n\tDext  (mm) = \t nan \n\n"
    "COMMENTS:\n\nFreely deployed heptane droplet burning in a cabin air environment.\n"
)

# PSI-159 21256A1_data.csv: metadata line, header line, data rows (columns abridged)
ACME = (
    "2021-09-13 256 16:09:37:957 ,Experiment: 5,Test Point: 21256A1,MFCA1 Gas: 3,PMT 1 Gain: 10.000000\n"
    "Time,MFCA3FuelFlow,IonCurrent,PMT1,TCA\n"
    "16:10:15:704,0.000572207,-0.892147,4.42075,0.000163515\n"
    "16:10:15:712,0.000572207,-0.891000,4.41000,0.000163000\n"
    "16:11:24:695,0.00286103,-0.890621,-0.000495913,0.000193169\n"
)


def test_flex_series_handles_mac_line_endings():
    df = pp.read_flex_series(FLEX_DROPLET)
    assert list(df.columns)[:2] == ["DropletTime_sec", "DropletDiameter_mm"]
    assert len(df) == 3
    assert abs(df["DropletDiameter_mm"].iloc[0] - 2.919) < 1e-3


def test_flex_testsheet_fields():
    d = pp.read_flex_testsheet(FLEX_SHEET)
    assert d["test_id"] == "FLEX-008"
    assert d["Pressure (atm)"] == 1.0
    assert d["O2 Mole Fraction"] == 0.21
    assert d["Fuel"] == "Heptane"
    assert d["D0  (mm)"] == 2.95
    assert d["kavg  (mm2/s)"] == 0.79
    assert math.isnan(d["Dext  (mm)"])  # "nan" in the sheet = not measured
    assert d["Test Time"] == "18:07:15 (GMT)"
    assert "heptane droplet" in d["comments"]


def test_d2_law_slope_recovers_k():
    t = pd.Series([i / 30 for i in range(1, 300)])
    d = (2.9**2 - 0.8 * t) ** 0.5
    k = pp.d2_burning_rate(pd.DataFrame({"t": t, "d": d}))
    assert abs(k - 0.8) < 1e-6


def test_acme_csv_skips_metadata_line():
    meta, df = pp.read_acme_csv(ACME)
    assert meta["Test Point"] == "21256A1"
    assert meta["PMT 1 Gain"] == 10.0
    assert list(df.columns)[:3] == ["t_s", "Time", "MFCA3FuelFlow"]
    assert len(df) == 3
    assert abs(df["t_s"].iloc[-1] - 68.991) < 1e-6  # 16:11:24.695 - 16:10:15.704


def test_flatten_and_select_match_real_tree_shape():
    # Shape copied from a real POST /files/v2 response for PSI-98
    tree = [
        {"displayName": "Engineering Documents", "files": [
            {"directory": False, "bytes_size": 13957.0, "version": 1,
             "key": "psi-data/PSI-69/Engineering Documents/PSI-69_Engineering Documents_Ops.pdf"}]},
        {"displayName": "Raw Data", "files": [{"displayName": "Reduced Gravity", "files": [
            {"directory": False, "bytes_size": 12000.0, "version": 1,
             "key": "psi-data/PSI-69/Raw Data/PSI-69_Raw Data_FLEX-008_DropletData.txt"},
            {"directory": False, "bytes_size": 1982080000.0, "version": 1,
             "key": "psi-data/PSI-69/Raw Data/PSI-69_Raw Data_053F001A.zip"}]}]},
        {"displayName": "Experimental table", "files": [
            {"directory": False, "bytes_size": 24776.0, "version": 1,
             "key": "psi-data/PSI-69/Experimental table/PSI-69_Experimental table_FLEX.csv"}]},
    ]
    files = pf.flatten_tree(tree, "PSI-69")
    assert len(files) == 4
    chosen = pf.select(files, pf.PROFILES["flex"][0][1])
    names = sorted(f.name for f in chosen)
    assert names == ["PSI-69_Experimental table_FLEX.csv", "PSI-69_Raw Data_FLEX-008_DropletData.txt"]
    p = chosen[0].local_path(Path("data/raw"))
    assert p.parts[:3] == ("data", "raw", "PSI-69")


def test_track_expansion_covers_leader_tracks():
    assert pf.expand(["t4"]) == ["flex", "flex2", "cfi", "cfig"]
    assert pf.expand(["tamer"]) == pf.expand(["t4"])
    assert pf.expand(["mahmoud", "same"]) == ["same", "daft"]   # no duplicates
    assert set(pf.expand(["all"])) == set(pf.PROFILES)
    covered = {inv for p in pf.expand(["all"]) for inv, _ in pf.PROFILES[p]}
    assert covered == {"PSI-25", "PSI-26", "PSI-98", "PSI-99", "PSI-100", "PSI-101", "PSI-102", "PSI-47",
                       "PSI-69", "PSI-68", "PSI-39", "PSI-159", "PSI-20", "PSI-22", "PSI-23", "PSI-10",
                       "PSI-107", "PSI-106", "PSI-21"}
    import pytest
    with pytest.raises(KeyError):
        pf.expand(["nobody"])
