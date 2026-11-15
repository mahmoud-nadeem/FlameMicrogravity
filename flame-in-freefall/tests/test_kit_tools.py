"""Kit tools: exact source rows, logged conversions, no guessing, scaffolds, self-check, package."""
import json
import sys
import zipfile
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import build_run_table as B  # noqa: E402
from tools import kitlib as K  # noqa: E402
from tools import new_track, package, self_check  # noqa: E402

ET_REL = "PSI-102/Experimental table/PSI-102_Experimental table_TEST.csv"
ET = ("Test,Fuel,XO2,P (atm),Result\n"
      "1,Ethylene,0.30,0.5,Yes\n"
      ",,,,\n"
      "2,Ethylene,LOW O2,0.6,No\n"
      "3,Ethylene,0.35 - 0.36,0,Maybe\n")


def _kit(tmp_path: Path) -> Path:
    et = tmp_path / "data" / "experimental_tables" / ET_REL
    et.parent.mkdir(parents=True)
    et.write_text(ET, encoding="utf-8")
    meta = {"id": "PSI-102", "title": "Smoke test", "acronym": "SAME", "doi": "10.0/x", "license": "CC0",
            "sub_area": "Spacecraft Fire Safety", "related": ["PSI-101"], "total_size_bytes": 657_600_000,
            "file_extensions": {"csv": 1}, "file_categories": {"Experimental table": {"files": 1, "bytes": 331}},
            "experimental_tables": [{"file": Path(ET_REL).name, "rows": 4, "columns": []}],
            "publications": [{"title": "Paper", "doi": "10.1/p"}], "retrieved_at": "2026-11-14"}
    md = tmp_path / "data" / "psi_metadata" / "PSI-102.json"
    md.parent.mkdir(parents=True)
    md.write_text(json.dumps(meta), encoding="utf-8")
    return tmp_path


def _map(tmp_path: Path, columns: dict, **src) -> Path:
    rec = K.record_dir(tmp_path, "T3", "PSI-102")
    mp = rec / "scripts" / "run_table_map.yaml"
    mp.parent.mkdir(parents=True, exist_ok=True)
    import yaml
    mp.write_text(yaml.safe_dump({"investigation_id": "PSI-102", "slug": "same",
                                  "sources": [{"file": ET_REL, "columns": columns, **src}]}), encoding="utf-8")
    return mp


FULL = {
    "material_or_fuel": {"from": "Fuel"},
    "gravity_level": {"value": "microgravity_ISS", "reason": "PSI page, Overview: ISS"},
    "oxygen_pct": {"from": "XO2", "convert": "fraction_to_pct"},
    "pressure_kpa": {"from": "P (atm)", "convert": "atm_to_kpa"},
    "outcome_raw": {"from": "Result"},
}


def test_run_table_rows_units_flags_and_log(tmp_path):
    root = _kit(tmp_path)
    mp = _map(root, FULL, run_id="Test", outcome_map={"Yes": "ignition", "No": "no_ignition"})
    out, n, log = B.build(mp, root)
    df = pd.read_csv(out, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert list(df.columns[:13]) == K.REQUIRED_COLUMNS
    assert n == 3 and df["source_row"].tolist() == ["2", "4", "5"]          # line numbers, blank row 3 left out
    assert df["run_id"].tolist() == ["1", "2", "3"]
    assert float(df.loc[0, "oxygen_pct"]) == 30.0 and float(df.loc[0, "pressure_kpa"]) == pytest.approx(50.6625)
    assert df.loc[1, "oxygen_pct"] == "" and "LOW O2" in df.loc[1, "notes"]   # never guessed
    assert df.loc[2, "oxygen_pct"] == "" and "0.35 - 0.36" in df.loc[2, "notes"]
    assert "SUSPICIOUS pressure_kpa" in df.loc[2, "notes"]                   # flagged, kept
    assert df.loc[2, "outcome_norm"] == "" and "not in outcome_map" in df.loc[2, "notes"]
    assert df.loc[0, "outcome_norm"] == "ignition" and df.loc[0, "raw_XO2"] == "0.30"
    text = (mp.parent.parent / "data_log.md").read_text(encoding="utf-8")
    assert "rows 3 (1 rows)" in text and "| 4 | oxygen_pct | LOW O2 | (empty) |" in text
    assert "microgravity_ISS | PSI page, Overview: ISS" in text and "x 101.325 (atm_to_kpa)" in text
    B.build(mp, root)                                                        # re-run: one generated block
    assert (mp.parent.parent / "data_log.md").read_text(encoding="utf-8").count(K.AUTO_START) == 1


def test_partial_numbers_leading_is_logged(tmp_path):
    root = _kit(tmp_path)
    mp = _map(root, {"oxygen_pct": {"from": "XO2", "convert": "fraction_to_pct"}}, partial_numbers="leading")
    out, _, log = B.build(mp, root)
    df = pd.read_csv(out, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    assert float(df.loc[2, "oxygen_pct"]) == 35.0
    assert any("| 5 | oxygen_pct | 0.35 - 0.36 |" in line for line in log)
    assert df.loc[0, "run_id"] == "r2"                                       # generated id, logged
    assert any("run_id generated" in line for line in log)


@pytest.mark.parametrize("columns,msg", [
    ({"gravity_level": {"value": "microgravity_ISS"}}, "reason"),
    ({"oxygen_pct": {"from": "Nope"}}, "not in"),
    ({"run_id": {"from": "Test"}}, "cannot be mapped"),
    ({"material_or_fuel": {"from": "Fuel", "convert": "atm_to_kpa"}}, "convert only"),
])
def test_mapping_errors(tmp_path, columns, msg):
    root = _kit(tmp_path)
    with pytest.raises(B.MapError, match=msg):
        B.build(_map(root, columns), root)


def test_excel_rows_follow_excel_numbering(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws["A1"] = "note line"
    ws["A2"], ws["B2"] = "Test", "O2"
    ws["A3"], ws["B3"] = "1", 0.21
    ws["A5"], ws["B5"] = "2", 0.3
    p = tmp_path / "t.xlsx"
    wb.save(p)
    df, rows = K.read_source(p, header_row=2)
    assert rows == [3, 4, 5] and df.loc[0, "Test"] == "1"


def test_scaffold_self_check_and_package(tmp_path):
    root = _kit(tmp_path)
    created = new_track.scaffold("T3", root)
    assert created and new_track.scaffold("T3", root) == []                 # never overwrites
    rec = K.record_dir(root, "T3", "PSI-102")
    card = json.loads((rec / "card.json").read_text(encoding="utf-8"))
    assert card["size_on_page"] == "627 MB" and card["version"] == "unconfirmed" and card["verified_by"] == ""
    B.build(rec / "scripts" / "run_table_map.yaml", root)                    # columns: {} works
    res = {n: s for n, _, s, _ in self_check.check("T3", root)}
    assert res[1] == "PASS" and res[2] == "PASS" and res[6] == "FAIL" and res[10] == "FAIL"
    assert res[4] == "WARN" and res[8] == "PASS"                             # fresh template is not a bad finding

    for r in K.record_dirs(root, "T3"):
        c = json.loads((r / "card.json").read_text(encoding="utf-8"))
        c.update(objectives="Mine.", approach="Mine.", verified_on="2026-11-14 21:00", verified_by="Mahmoud Nadeem")
        (r / "card.json").write_text(json.dumps(c), encoding="utf-8")
    (root / "analysis" / "T3" / "references.md").write_text("PSI-102 PSI-101 PSI-47 cited", encoding="utf-8")
    (rec / "findings.md").write_text(
        "F-T3-1 | Eight samples are listed. | OBSERVED IN DATA | " + ET_REL + " | rows 2-5 | high | small table\n"
        "F-3-2 | Bad id and label. | MY GUESS | x.csv | 2 | sure | none\n", encoding="utf-8")
    res = {n: (s, d) for n, _, s, d in self_check.check("T3", root)}
    assert res[6][0] == "PASS" and res[10][0] == "PASS"
    assert res[4][0] == "FAIL" and any("F-3-2" in x or "line 2" in x for x in res[4][1])

    out, left_out, _ = package.package("T3", 1, root)
    assert out.name == "T3_nadeem_v1.zip" and not left_out
    names = zipfile.ZipFile(out).namelist()
    assert "analysis/T3/HANDOFF.md" in names and "analysis/T3/SELF_CHECK.md" in names
    assert all(n.startswith("analysis/T3/") for n in names)


def test_track_ids():
    assert K.track_id("t3") == K.track_id("nadeem") == K.track_id("mahmoud") == "T3"
    with pytest.raises(KeyError):
        K.track_id("nobody")
