"""Retry behaviour of the PSI client and of psi_fetch when the shared PSI server is busy."""
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from pipeline import psi_api as api  # noqa: E402
import psi_fetch as pf  # noqa: E402


class FakeResponse:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code, self._payload, self.text = status, payload, text

    def json(self):
        if self._payload is None:
            raise ValueError("not JSON")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


class FakeSession:
    """Returns the queued responses (or raises queued exceptions) in order."""

    def __init__(self, *queue):
        self.queue, self.calls = list(queue), 0

    def request(self, method, url, timeout=None, **kw):
        self.calls += 1
        item = self.queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(api, "BACKOFF", 0)


def test_retries_5xx_timeouts_and_html_then_succeeds():
    s = FakeSession(FakeResponse(500), requests.Timeout(), FakeResponse(200, None, "<html>"),
                    FakeResponse(200, {"version": 2}))
    assert api.get_investigation(s, "PSI-107") == {"version": 2}
    assert s.calls == 4


def test_gives_up_with_psi_unavailable():
    s = FakeSession(*[FakeResponse(503) for _ in range(api.RETRIES)])
    with pytest.raises(api.PSIUnavailable):
        api.get_investigation(s, "PSI-107")
    assert s.calls == api.RETRIES


def test_404_is_not_retried():
    s = FakeSession(FakeResponse(404))
    with pytest.raises(requests.HTTPError):
        api.get_investigation(s, "PSI-999")
    assert s.calls == 1


def test_fetch_skips_unavailable_investigation_and_continues(monkeypatch, tmp_path, capsys):
    seen = []

    def fake_get(s, inv):
        seen.append(inv)
        if inv == "PSI-107":
            raise api.PSIUnavailable("busy")
        return {"version": 1, "doi": "x"}

    monkeypatch.setattr(pf.api, "make_session", lambda: None)
    monkeypatch.setattr(pf.api, "get_investigation", fake_get)
    monkeypatch.setattr(pf.api, "list_files", lambda s, inv, v: [])
    code = pf.main(["--datasets", "gamal", "--out", str(tmp_path)])
    assert code == 1                                   # tells the user to run again
    assert seen == ["PSI-107", "PSI-106", "PSI-21"]    # did not stop at the first failure
    assert "PSI-107" in capsys.readouterr().out


def test_track_t1_has_no_video_by_default():
    assert pf.expand(["morgan"]) == ["bass"]


# Shape of the PSI-21 listing (version 4, checked 2026-11-14): flat storage keys, one page folder per
# test, a repeated entry, folders without a setpoints file, and "Video and Image Data" folders.
def _node(name, *files):
    return {"displayName": name, "directory": True, "files": list(files)}


def _file(key, size=10):
    return {"directory": False, "key": f"psi-data/PSI-21/{key}", "bytes_size": size, "version": 4, "files": []}


PSI21_TREE = [
    _node("Experimental table", _file("Experimental table/PSI-21_Experimental table_CLD Flame.csv")),
    _node("Raw Data", _file("Raw Data/ACME_Requirements.pdf"), _node(
        "Legacy",
        _node("17319A3 Raw Data", _file("Raw Data/17319A3_data.csv"), _file("Raw Data/17319A3_mfcSetpoints.csv"),
              _file("Raw Data/17319A3_Comments.txt"), _file("Raw Data/17319A3_data.csv")),          # repeated
        _node("17324RAD1 Raw Data", _file("Raw Data/17324RAD1_data.csv")),                           # no setpoints
        _node("18008MFCA2_x Raw Data", _file("Raw Data/18008MFCA2_1_data.csv"),
              _file("Raw Data/18008MFCA2_1_mfcSetpoints.csv")),
        _node("Methane, dilute (0-40%)", _node("17319A3 Video and Image Data",
                                               _file("Raw Data/17319A3_cam_data.csv"))),           # not a Raw Data folder
        _node("21041Fiber1A Raw Data", _file("Raw Data/ACME_21041Fiber1A.mdipsug")),
    )),
]


def test_page_folders_and_cld_selection(tmp_path):
    files = api.flatten_tree(PSI21_TREE, "PSI-21")
    assert sum(f.key.endswith("17319A3_data.csv") for f in files) == 1                 # repeat dropped
    pattern = dict(pf.PROFILES["cld"])["PSI-21"]
    picked = api.select(files, pattern)
    names = sorted(f.page_path for f in picked)
    assert names == [
        "Experimental table/PSI-21_Experimental table_CLD Flame.csv",
        "Raw Data/Legacy/17319A3 Raw Data/17319A3_data.csv",
        "Raw Data/Legacy/17319A3 Raw Data/17319A3_mfcSetpoints.csv",
        "Raw Data/Legacy/17324RAD1 Raw Data/17324RAD1_data.csv",
        "Raw Data/Legacy/18008MFCA2_x Raw Data/18008MFCA2_1_data.csv",
        "Raw Data/Legacy/18008MFCA2_x Raw Data/18008MFCA2_1_mfcSetpoints.csv",
    ]
    f = next(x for x in picked if x.name == "17319A3_data.csv")
    assert f.local_path(tmp_path, "page") == tmp_path / "PSI-21" / "Raw Data" / "Legacy" / "17319A3 Raw Data" / f.name
    assert f.local_path(tmp_path) == tmp_path / "PSI-21" / "Raw Data" / f.name           # default layout unchanged


def test_fetch_cld_saves_in_page_folders(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(pf.api, "make_session", lambda: None)
    monkeypatch.setattr(pf.api, "get_investigation", lambda s, inv: {"version": 4, "doi": "10.60555/x"})
    monkeypatch.setattr(pf.api, "list_files", lambda s, inv, v: api.flatten_tree(PSI21_TREE, inv))
    monkeypatch.setattr(pf.api, "download", lambda s, f, root, layout="key": calls.append(f.local_path(root, layout)) or "ok")
    assert pf.main(["--datasets", "cld", "--out", str(tmp_path)]) == 0
    # complete-folder rule: 17324RAD1 (no setpoints) and 21041Fiber1A (no CSV) are skipped
    assert len(calls) == 5
    assert tmp_path / "PSI-21" / "Raw Data" / "Legacy" / "17319A3 Raw Data" / "17319A3_mfcSetpoints.csv" in calls
    assert not any("17324RAD1" in str(c) for c in calls)
    manifest = (tmp_path / "manifest.csv").read_text(encoding="utf-8")
    assert "17319A3 Raw Data" in manifest
    report = (tmp_path / "PSI-21" / "PSI-21_incomplete_folders.txt").read_text(encoding="utf-8")
    assert "Folders checked: 4 | complete (downloaded): 2 | skipped: 2" in report
    assert "Raw Data/Legacy/17324RAD1 Raw Data | setpoints | 17324RAD1_data.csv" in report
    assert "Raw Data/Legacy/21041Fiber1A Raw Data | data and setpoints | ACME_21041Fiber1A.mdipsug" in report
