"""Minimal client for the public NASA PSI repository API.

The endpoints are the ones the PSI web app (https://psi.nasa.gov/physci/repo) calls;
each was verified from a browser session on 2026-11-14:

  GET  /geode-py/ws/repo/search?term=...&source=psi&type=investigation&size=N
  GET  /geode-py/ws/repo/investigations/{ID}
  POST /geode-py/ws/files/v2            {"folder","fileType","studyId","version"}
  GET  /geode-py/ws/studies/{ID}/download?file=...&version=N&redirect=false  -> signed S3 URL
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

import requests

BASE = "https://psi.nasa.gov/geode-py/ws"
USER_AGENT = "flame-in-freefall-hackathon/0.3 (NASA Space Apps 2026)"

# The PSI server is shared by every Space Apps team and slows down or answers 5xx under load
# (seen on 2026-11-14 evening: 500s, 30 s+ hangs and HTML error pages instead of JSON).
# Every metadata call is therefore retried with exponential backoff before giving up.
RETRY_STATUS = {429, 500, 502, 503, 504}
RETRIES = 4
BACKOFF = 3.0              # seconds; waits 3, 6, 12 between the 4 attempts
TIMEOUT = (10, 45)         # (connect, read) seconds


class PSIUnavailable(RuntimeError):
    """PSI kept failing after all retries: the server is busy or down, try again later."""


def _request(s: requests.Session, method: str, url: str, *, want_json: bool = False,
             retries: int | None = None, timeout=TIMEOUT, **kw):
    """Call PSI, retrying 5xx/429, timeouts, dropped connections and HTML error pages.

    Other 4xx (e.g. 404 for a wrong ID) are real errors and raise requests.HTTPError at once.
    """
    retries = RETRIES if retries is None else retries
    last = "no response"
    for attempt in range(1, retries + 1):
        try:
            r = s.request(method, url, timeout=timeout, **kw)
            if r.status_code in RETRY_STATUS:
                last = f"HTTP {r.status_code}"
            else:
                r.raise_for_status()
                return r.json() if want_json else r
        except (requests.ConnectionError, requests.Timeout) as e:
            last = e.__class__.__name__
        except ValueError:  # 200 with an HTML error page instead of JSON
            last = "invalid JSON"
        if attempt < retries:
            time.sleep(BACKOFF * 2 ** (attempt - 1))
    raise PSIUnavailable(f"{method} {url} failed {retries} times ({last})")


_BAD_WIN_CHARS = re.compile(r'[<>:"|?*]')


@dataclass
class RemoteFile:
    investigation: str
    key: str          # e.g. psi-data/PSI-69/Experimental table/PSI-69_Experimental table_FLEX.csv
    size: int
    version: int
    folder: str = ""  # folder as the PSI page shows it, e.g. "Raw Data/Legacy/17319A3 Raw Data"
                      # (can differ from the key: PSI-21 shows per-test folders, its keys are flat)

    @property
    def page_path(self) -> str:
        return f"{self.folder}/{self.name}" if self.folder else self.name

    @property
    def name(self) -> str:
        return self.key.rsplit("/", 1)[-1]

    @property
    def category(self) -> str:
        """Top folder under the investigation, e.g. 'Raw Data', 'Experimental table'."""
        prefix = f"psi-data/{self.investigation}/"
        rest = self.key[len(prefix):] if self.key.startswith(prefix) else self.key
        return rest.split("/", 1)[0] if "/" in rest else "(root)"

    def local_path(self, root: Path, layout: str = "key") -> Path:
        """layout 'key': folders of the storage key; 'page': folders as shown on the PSI page."""
        if layout == "page" and self.folder:
            parts = [_BAD_WIN_CHARS.sub("_", part).strip() or "_" for part in self.folder.split("/")]
            return Path(root) / self.investigation / Path(*parts) / self.name
        prefix = f"psi-data/{self.investigation}/"
        rel = self.key[len(prefix):] if self.key.startswith(prefix) else self.name
        return Path(root) / self.investigation / rel


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def search(s: requests.Session, term: str, size: int = 200) -> list[dict]:
    data = _request(s, "GET", f"{BASE}/repo/search", want_json=True,
                    params={"term": term, "source": "psi", "type": "investigation", "size": size, "from": 0})
    return [h["_source"] for h in data["hits"]["hits"]]


def get_investigation(s: requests.Session, inv: str) -> dict:
    return _request(s, "GET", f"{BASE}/repo/investigations/{inv}", want_json=True)


def flatten_tree(nodes: list[dict], inv: str) -> list[RemoteFile]:
    """Turn the nested /files/v2 tree into a flat, sorted list of files.

    Each file keeps the folder path shown on the PSI page (displayName of its parent folders).
    The listing sometimes repeats the same entry; repeats are dropped.
    """
    out: dict[tuple[str, str], RemoteFile] = {}
    stack = [(n, "") for n in (nodes or [])]
    while stack:
        n, folder = stack.pop()
        if n.get("directory") is False:
            f = RemoteFile(inv, n["key"], int(n.get("bytes_size") or 0), int(n.get("version") or 1), folder)
            out.setdefault((f.key, folder), f)
        else:
            name = str(n.get("displayName") or "").strip()
            sub = f"{folder}/{name}" if folder and name else (name or folder)
            stack.extend((c, sub) for c in (n.get("files") or []))
    return sorted(out.values(), key=lambda f: (f.key, f.folder))


def list_files(s: requests.Session, inv: str, version: int) -> list[RemoteFile]:
    body = {"folder": f"psi-data/{inv}/", "fileType": "study", "studyId": inv, "version": version}
    data = _request(s, "POST", f"{BASE}/files/v2", want_json=True, json=body, timeout=(10, 120))
    return flatten_tree(data.get("files", []), inv)


def select(files: list[RemoteFile], patterns: list[str]) -> list[RemoteFile]:
    """Keep files matching any pattern. Patterns match the storage key, or, when they start with
    'page:', the path shown on the PSI page (folder + file name)."""
    regs = [(True, re.compile(p[5:])) if p.startswith("page:") else (False, re.compile(p)) for p in patterns]
    return [f for f in files if any(rg.search(f.page_path if page else f.key) for page, rg in regs)]


def signed_url(s: requests.Session, f: RemoteFile, retries: int | None = None) -> str:
    url = (f"{BASE}/studies/{f.investigation}/download?file={quote(f.name)}"
           f"&version={f.version}&redirect=false")
    return _request(s, "GET", url, retries=retries).text.strip()


def download(s: requests.Session, f: RemoteFile, root: Path, retries: int = 3, layout: str = "key") -> str:
    """Download one file under root/<ID>/...; returns ok | exists | missing | error: <type>."""
    dest = f.local_path(root, layout)
    if dest.exists() and f.size and dest.stat().st_size == f.size:
        return "exists"
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, retries + 1):
        try:
            url = signed_url(s, f, retries=2)  # fresh URL each attempt: signatures expire
            with s.get(url, stream=True, timeout=300) as r:
                if r.status_code == 404:
                    return "missing"  # listed in PSI but absent in storage (S3 NoSuchKey)
                r.raise_for_status()
                tmp = dest.with_suffix(dest.suffix + ".part")
                with open(tmp, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        fh.write(chunk)
                tmp.replace(dest)
            return "ok"
        except (requests.RequestException, PSIUnavailable) as e:
            if attempt == retries:
                return f"error: {e.__class__.__name__}"
            time.sleep(BACKOFF * attempt)
    return "error"
