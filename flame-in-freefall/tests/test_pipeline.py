"""Pipeline tests: number parsing, envelope extraction, scenario coverage, catalog slimming, validation."""
import shutil
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from pipeline import build_catalog, common, envelope, psi_api, validate  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "et"


@pytest.mark.parametrize("raw,expected", [
    ("1 atm", 1.0), ("0.21", 0.21), ("21.5 - 21.7", 21.5), ("RAMP", None), ("LOW O2", None),
    ("", None), ("~ 21.5", None), ("-5.92", -5.92), ("2.4E-3", 0.0024), (float("nan"), None), (3, 3.0),
])
def test_to_number_is_strict(raw, expected):
    assert common.to_number(raw) == expected


def test_extract_points_handles_real_quirks():
    pts = envelope.extract_points(FIX)
    flex = pts[pts.investigation == "PSI-69"].set_index("test_id")
    assert flex.loc["114", "p_atm"] is None or flex.loc["114", "p_atm"] != flex.loc["114", "p_atm"]  # 0 mmHg -> missing
    assert abs(flex.loc["1", "p_atm"] - 757.7 / 760) < 1e-6
    fd = pts[pts.investigation == "PSI-10"]
    assert "22024K2" not in set(fd.test_id)          # 'LOW O2' is not 2.0
    assert set(fd["mode"]) == {"ambient", "burner-oxidizer"}
    bass = pts[pts.investigation == "PSI-25"]
    assert bass.o2_frac.max() == pytest.approx(0.222)  # percent -> fraction
    assert bass.p_atm.isna().all()                      # pressure not recorded
    cfi = pts[pts.investigation == "PSI-39"]
    assert set(cfi.p_atm) == {1.0}                      # '1 atm'


def test_coverage_counts_moon_base():
    pts = envelope.extract_points(FIX)
    scen = envelope.load_scenarios(ROOT / "content" / "scenarios")
    cov = envelope.coverage(pts, scen)
    moon = cov["moon-base"]["investigations"]
    assert moon["PSI-159"]["by_mode"]["ambient"]["inside"] == 2
    assert moon["PSI-159"]["by_mode"]["ambient"]["outcomes_inside"] == {"Yes": 1, "No": 1}
    assert moon["PSI-159"]["by_mode"]["burner-oxidizer"]["inside"] == 1
    assert moon["PSI-69"]["by_mode"]["ambient"]["inside"] == 0
    assert moon["PSI-69"]["by_mode"]["ambient"]["within_5pct"] == 1   # 0.34 O2 at 0.703 atm
    assert cov["earth-sea-level"]["investigations"]["PSI-39"]["by_mode"]["ambient"]["inside"] == 2
    assert all(v["by_mode"].get("ambient", {}).get("inside", 0) == 0 for v in cov["spacesuit"]["investigations"].values())


def test_slim_drops_contact_details_and_summarises_files():
    meta = {
        "accession": "PSI-69", "title": "Flame Extinguishment Experiment", "investigationAcronym": "FLEX",
        "doi": "10.60555/mbq8-0451", "licenseName": "Creative Commons Zero v1.0 Universal",
        "projectType": "Microgravity Investigation", "flightProgram": "International Space Station (ISS)",
        "researchArea": "Combustion Science", "subResearchArea": "Spacecraft Fire Safety",
        "experimentHardware": "Combustion Integrated Rack (CIR)-Fluids and Combustion Facility (FCF), Multi-user Droplet Combustion Appartatus (MDCA)",
        "objective": "The FLEX investigation aims to map the flammability limits ...", "version": 5,
        "contacts": [{"firstName": "Benjamin", "lastName": "Shaw", "midInitials": "", "email": "x@y.edu", "phone": "1",
                      "affiliation": "University of California, Davis",
                      "roles": [{"annotationValue": "Co-Investigator (Co-I)"}]}],
        "publications": [{"title": "Methanol Droplet Combustion in Oxygen-Inert Environments in Microgravity",
                          "authorList": "V Nayagam, DL Dietrich, MC Hicks, FA Williams", "doi": ""}],
        "totalFileSize": 923832535657,
    }
    hit = {"Keywords": "droplet     extinction     CO2", "Related Investigations": "PSI-68     PSI-39"}
    files = [psi_api.RemoteFile("PSI-69", "psi-data/PSI-69/Raw Data/PSI-69_Raw Data_FLEX-008_DropletData.txt", 12000, 1),
             psi_api.RemoteFile("PSI-69", "psi-data/PSI-69/Experimental table/PSI-69_Experimental table_FLEX.csv", 24776, 1)]
    rec = build_catalog.slim(meta, hit, files, [])
    assert rec["people"] == [{"name": "Benjamin Shaw", "affiliation": "University of California, Davis",
                              "roles": ["Co-Investigator (Co-I)"]}]
    assert "x@y.edu" not in str(rec)
    assert rec["keywords"] == ["droplet", "extinction", "CO2"]
    assert rec["related"] == ["PSI-68", "PSI-39"]
    assert rec["file_categories"]["Raw Data"] == {"files": 1, "bytes": 12000}
    assert rec["doi_url"] == "https://doi.org/10.60555/mbq8-0451"


def test_repository_content_is_valid():
    errors, counts = validate.validate()
    assert errors == []
    assert counts["cards"] >= 6 and counts["findings"] >= 1


def test_validator_reports_broken_contribution(tmp_path):
    shutil.copytree(ROOT / "content", tmp_path / "content")
    card = tmp_path / "content" / "investigations" / "PSI-69" / "card.yaml"
    obj = yaml.safe_load(card.read_text())
    obj["author"] = "nobody"
    obj["fuel_type"] = "plasma"
    obj["conditions"]["o2_percent"] = [34, 12]
    card.write_text(yaml.safe_dump(obj))
    errors, _ = validate.validate(tmp_path / "content")
    text = "\n".join(errors)
    assert "author 'nobody' is not in content/members/" in text
    assert "fuel_type" in text and "'plasma' is not one of" in text
    assert "min 34 is larger than max 12" in text


def test_rank_without_coverage_uses_card_ranges():
    from pipeline import rank
    res = rank.rank(coverage={})  # independent of whatever data/derived holds
    moon = {r["id"]: r for r in res["scenarios"]["moon-base"]["ranking"]}
    # CFI-G card ranges (12-85% O2, 0.49-3.27 atm) overlap the Moon-base envelope
    assert moon["PSI-159"]["envelope"] == 0.8
    # BASS-II never exceeded 22.2% O2 and has no pressure: partial proximity only
    assert 0 < moon["PSI-25"]["envelope"] < 0.5
    ranks = [r["rank"] for r in res["scenarios"]["moon-base"]["ranking"]]
    assert ranks == sorted(ranks)


def test_envelope_component_prefers_ambient_tests():
    from pipeline import rank
    sc = {"_o2": (0.30, 1.0), "_p_atm": (0.293, 0.694)}
    card = {"conditions": {"o2_percent": [12, 85], "pressure_atm": [0.5, 3]}}
    assert rank.envelope_component(card, sc, {"by_mode": {"ambient": {"inside": 20}}})[0] == 1.0
    assert rank.envelope_component(card, sc, {"by_mode": {"ambient": {"inside": 0}, "burner-oxidizer": {"inside": 5}}})[0] == 0.6
    assert rank.envelope_component(card, sc, {"by_mode": {"ambient": {"inside": 0, "within_5pct": 3}}})[0] == 0.5


def test_import_bundle_from_browser_export(tmp_path):
    """Fixture = a real bundle record from tools/psi_browser_export.js (texts shortened, e-mail replaced)."""
    import json
    from pipeline import import_bundle
    bundle = json.loads((ROOT / "tests" / "fixtures" / "psi_bundle_PSI-142.json").read_text())
    done = import_bundle.import_bundle(bundle, content=tmp_path / "content", et_dir=tmp_path / "et")
    assert done == ["PSI-142"]
    rec = json.loads((tmp_path / "content" / "investigations" / "PSI-142" / "psi.json").read_text())
    assert rec["doi_url"] == "https://doi.org/10.60555/80qf-vj95"
    assert rec["platform"] == "Not Applicable"
    assert rec["people"][0]["name"] == "Yiguang Ju" and "email" not in rec["people"][0]
    assert rec["experimental_tables"][0]["rows"] == 2
    assert rec["experimental_tables"][0]["columns"][0] == "Data ID"
    assert rec["file_categories"]["Analyzed Data"]["files"] == 1
    assert (tmp_path / "et" / "PSI-142" / "Experimental table" / "PSI-142_Experimental table_Data Summary Table.csv").exists()
