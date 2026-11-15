#!/usr/bin/env python3
"""Build data/site-data.js for the dashboard from the team's track packages.

    python build_site_data.py --kit "../flame-in-freefall-kit"

--kit points at a folder that contains analysis/T1..T6 (Mohammed Tamer's package layout) and
data/psi_metadata/*.json (PSI records). Unzipped member packages (T3_nadeem_v1.zip, ...) can be
dropped into <kit>/analysis/ as they arrive; run this script again and refresh the page.

The site is opened straight from disk (file://), where browsers block fetch(), so everything the
pages need is written into ONE JavaScript file (window.FIF_DATA = {...}). Charts that a track ships are
copied under data/files/<track>/<PSI-ID>/ (two records may ship charts with the same file name), so the
site never needs the internet. data/files/ is generated: it is emptied and rebuilt on every run.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRACKS = {
    "T1": {"member": "morgan", "records": ["PSI-26", "PSI-25"]},
    "T2": {"member": "shreif", "records": ["PSI-98", "PSI-99", "PSI-100"]},
    "T3": {"member": "nadeem", "records": ["PSI-102", "PSI-101", "PSI-47"]},
    "T4": {"member": "tamer", "records": ["PSI-69", "PSI-68", "PSI-39", "PSI-159"]},
    "T5": {"member": "adwi", "records": ["PSI-20", "PSI-22", "PSI-23", "PSI-10"]},
    "T6": {"member": "gamal", "records": ["PSI-107", "PSI-106", "PSI-21"]},
}
PAGE = "https://psi.nasa.gov/physci/repo/data/investigations/{}"
# Verification placeholders a track card may hold. They are kept on the card and in the record's
# other fields, but are never used as an experiment's display name (the site falls back to the PSI ID).
PLACEHOLDERS = {"unconfirmed", "unknown", "todo", "tbd", "n/a", "-"}


def display_acronym(*values: str) -> str:
    """First real acronym among the candidates; placeholder words are not names."""
    for v in values:
        v = (v or "").strip()
        if v and v.lower() not in PLACEHOLDERS:
            return v
    return ""


def read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def parse_findings(p: Path) -> list[dict]:
    """Lines 'F-T3-1 | statement | label | source | rows | confidence | caveat' (section 7.4)."""
    out = []
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.startswith("F-"):
            continue
        parts = [x.strip() for x in line.split("|")]
        if len(parts) != 7:
            print(f"  skipped malformed finding in {p}: {line[:60]}")
            continue
        fid, statement, label, source, rows, confidence, caveat = parts
        kind = ("observed" if label.upper().startswith("OBSERVED") else
                "reported" if label.upper().startswith("REPORTED") else "inference")
        out.append(dict(id=fid, statement=statement, label=label, kind=kind, source=source, rows=rows,
                        rows_display=compact_rows(rows), confidence=confidence.lower(), caveat=caveat))
    return out


def parse_questions(p: Path) -> list[dict]:
    """extra/test_questions.md in either team format: numbered 'Q: ...' lines followed by 'A: ...' lines (T3),
    or one line 'N. Question? Answer (refs).' (T1). A line containing 'not answerable' (with or without '#')
    starts the unanswerable part."""
    out, q, answerable = [], None, True
    if not p.exists():
        return out

    def add(q, a):
        out.append({"q": q, "a": a, "answerable": answerable, "findings": re.findall(r"F-T\d+-\d+", a)})

    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if re.match(r"^#*\s*not answerable\b", s, re.I):
            answerable = False
        m = re.match(r"^\d+\.\s*Q:\s*(.+)$", s)
        if m:
            q = m.group(1)
            continue
        m = re.match(r"^A:\s*(.+)$", s)
        if m and q:
            add(q, m.group(1))
            q = None
            continue
        m = re.match(r"^\d+\.\s*(?!Q:)(.+?\?)\s+(.+)$", s)
        if m:
            add(m.group(1), m.group(2))
    return out


def body_text(p: Path) -> str:
    """A text file's body without its title line ('# title', or a short first line followed by a blank line)."""
    if not p.exists():
        return ""
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    if lines and (lines[0].startswith("#") or (len(lines) > 2 and not lines[1].strip() and len(lines[0]) < 80
                                               and not lines[0].rstrip().endswith("."))):
        lines = lines[1:]
    return "\n".join(lines).strip()


def compact_rows(rows: str) -> str:
    """Short display form of a long row list, same set of rows: 'sheet!9, sheet!4, sheet!5, sheet!6' -> 'sheet!4-6, 9 (4 rows)'.
    Rows are grouped by prefix and sorted (a row list is a set; the full list in source order stays in 'rows').
    Applied only when there are 6+ items and every item is <prefix><integer>; otherwise returned unchanged."""
    items = [x.strip() for x in rows.split(",") if x.strip()]
    parsed = [re.match(r"^(.*?)(\d+)$", x) for x in items]
    if len(items) < 6 or not all(parsed):
        return rows
    groups = {}   # prefix -> numbers, prefixes in order of first appearance
    for m in parsed:
        groups.setdefault(m.group(1), set()).add(int(m.group(2)))
    out = []
    for pre, nums in groups.items():
        nums = sorted(nums)
        runs, start, prev = [], nums[0], nums[0]
        for n in nums[1:] + [None]:
            if n is not None and n == prev + 1:
                prev = n
                continue
            runs.append(f"{start}\u2013{prev}" if prev != start else f"{start}")
            if n is not None:
                start = prev = n
        out.append(pre + ", ".join(runs))
    return "; ".join(out) + f" ({len(items)} rows)"


def parse_citations(p: Path) -> dict:
    out = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- (PSI-\d+): (.+?)(?: \(text of 'Cite this Investigation'.*\))?$", line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def parse_publications(p: Path) -> list[str]:
    if not p.exists():
        return []
    text = p.read_text(encoding="utf-8")
    block = text.split("## Publications", 1)[1].split("\n## ", 1)[0] if "## Publications" in text else ""
    return [l[2:].strip() for l in block.splitlines() if l.startswith("- ")]


CHART_DIRS = ("charts", "eda")   # a package's figures: charts/ (team layout) and eda/ (T5 exploratory analysis)


def chart_files(rec: Path) -> list[Path]:
    """Every PNG figure of a record folder, sorted by file name (names are unique across CHART_DIRS)."""
    return sorted((p for d in CHART_DIRS if (rec / d).is_dir() for p in (rec / d).glob("*.png")), key=lambda p: p.name)


def captions(rec: Path) -> tuple[dict, str]:
    """Chart captions from charts/CAPTIONS.md (any letter case): '- file.png: caption' or 'Chart name: caption'
    lines, then charts/<stem>_caption.txt files. Other lines of CAPTIONS.md become one note for all the charts."""
    charts = rec / "charts"
    if not charts.is_dir():
        return {}, ""
    out, notes = {}, []
    stems = {png.stem.lower(): png.name for png in chart_files(rec)}
    capfile = next((f for f in charts.iterdir() if f.name.lower() == "captions.md"), None)
    if capfile:
        for line in capfile.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s.startswith("#"):   # a heading: keep only a parenthetical note such as the charts' source
                m = re.search(r"\((.+)\)\s*$", s)
                s = (m.group(1)[0].upper() + m.group(1)[1:] + ".") if m else ""
                if s:
                    notes.append(s)
                continue
            m = re.match(r"^- ([\w\-]+\.png): (.+)$", s)
            if m:
                out[m.group(1)] = m.group(2)
                continue
            m = re.match(r"^([^:]{3,60}):\s*(.+)$", s)
            key = re.sub(r"[^a-z0-9]+", "_", m.group(1).lower()).strip("_") if m else ""
            if m and key in stems:
                out[stems[key]] = s
            elif s:
                notes.append(s)
    for stem, name in stems.items():
        txt = next((rec / d / f"{stem}_caption.txt" for d in CHART_DIRS if (rec / d / f"{stem}_caption.txt").exists()), charts / "-")
        if name not in out and txt.exists():
            out[name] = txt.read_text(encoding="utf-8").strip()
    return out, " ".join(notes)


def text(v) -> str:
    return v.strip() if isinstance(v, str) else ""


def publications(v) -> list[dict]:
    """card.json 'publications' as a list of {title, link}; anything else (a string, a malformed entry) is ignored."""
    if not isinstance(v, list):
        return []
    return [{"title": text(p.get("title")), "link": text(p.get("link"))} for p in v if isinstance(p, dict) and text(p.get("title"))]


def t3_dataset(track_dir: Path) -> dict | None:
    """Compact per-test table for the interactive smoke charts (T3)."""
    p = track_dir / "PSI-101_same-r" / "tables" / "derived_same_results_flight_tests.csv"
    if not p.exists():
        return None
    rows = []
    with open(p, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                d = float(r["mean_diam_um"] or 0)
            except ValueError:
                continue
            if d <= 0 or r.get("size_consistent") == "False":   # no size, or a size row the T3 analysis keeps out (F-T3-23)
                continue
            num = lambda k: (round(float(r[k]), 4) if r.get(k) not in ("", None) else None)
            rows.append({"mission": r["mission"], "material": r["material"], "test": r["same_no"],
                         "parent": r["parent_test"], "aged": r["aged_measurement"] == "True",
                         "flow": num("vel_cm_s"), "rt": num("rt_r0"), "temp": num("sample_temp_c"),
                         "aging_s": num("net_aging_s"), "d_um": round(d, 4), "row": int(r["source_row"])})
    return {"id": "same_tests", "title": "SAME and SAME-R flight tests with a consistent particle size",
            "source": "PSI-101/Analyzed Data/PSI-101_Analyzed Data_SAME, SAME-R_Results.xlsx, sheet 'Reduced Data with ISS Det'",
            "materials": ["Kapton", "Teflon", "Lampwick", "Pyrell", "Silicone"], "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kit", type=Path, default=HERE.parent / "flame-in-freefall-kit")
    args = ap.parse_args()
    kit = args.kit.resolve()
    files_dir = HERE / "data" / "files"   # generated: emptied and rebuilt on every run
    if files_dir.exists():
        shutil.rmtree(files_dir)
    content = {n: read_json(HERE / "content" / f"{n}.json", {}) for n in ("project", "characters", "faq", "chat")}

    tracks, records, findings, questions, datasets = [], {}, [], [], {}
    for tid, t in TRACKS.items():
        tdir = kit / "analysis" / tid
        has_pkg = any((tdir / d).is_dir() and (tdir / d / "findings.md").exists() for d in
                      [p.name for p in tdir.glob("PSI-*")]) if tdir.exists() else False
        cites = parse_citations(tdir / "references.md")
        extra = tdir / "extra"
        tr = {"id": tid, "member": t["member"], "records": t["records"], "ready": False,
              "paragraph": body_text(extra / "track_paragraph.md"),
              "limitations": body_text(extra / "limitations.md"),
              "snippets": read_json(extra / "evidence_snippets.json", []),
              "publications": parse_publications(tdir / "references.md"), "charts": [],
              # interactive Results charts: numbers transcribed from the crew member's findings, each chart cites them
              "results": read_json(extra / "results_charts.json", [])}
        for inv in t["records"]:
            meta = read_json(kit / "data" / "psi_metadata" / f"{inv}.json", {}) or {}
            recdir = next(iter(sorted(tdir.glob(f"{inv}_*"))), None) if tdir.exists() else None
            card = read_json(recdir / "card.json", {}) if recdir else {}
            rec_f = parse_findings(recdir / "findings.md") if recdir else []
            for f in rec_f:
                f.update(track=tid, record=inv)
            findings += rec_f
            caps, cap_note = captions(recdir) if recdir else ({}, "")
            for png in chart_files(recdir) if recdir else []:
                dst = files_dir / tid / inv / png.name   # per record: PSI-25 and PSI-26 ship the same file names
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(png, dst)
                tr["charts"].append({"record": inv, "file": f"data/files/{tid}/{inv}/{png.name}",
                                     "caption": caps.get(png.name, png.stem.replace("_", " ")), "note": cap_note})
            records[inv] = {
                "id": inv, "track": tid,
                "title": card.get("title") or meta.get("title") or inv,
                "acronym": display_acronym(card.get("acronym"), meta.get("acronym")),
                "doi": card.get("doi") or meta.get("doi") or "",
                "license": card.get("license") or meta.get("license") or "",
                "version": card.get("version", ""), "size": card.get("size_on_page", ""),
                "objectives": text(card.get("objectives")) if "TODO" not in text(card.get("objectives")) else "",
                "approach": text(card.get("approach")) if "TODO" not in text(card.get("approach")) else "",
                "start": meta.get("start_date", ""), "end": meta.get("end_date", ""),
                "platform": meta.get("platform", ""), "sub_area": card.get("sub_research_area") or meta.get("sub_area", ""),
                "publications": publications(card.get("publications")) or [
                    {"title": p.get("title", ""), "link": f"https://doi.org/{p['doi']}" if p.get("doi") else ""}
                    for p in meta.get("publications") or []],
                "citation": cites.get(inv, ""), "page": PAGE.format(inv),
                "findings": [f["id"] for f in rec_f],
                # The card's own words are shown on the site; a name alone does not prove the page was checked.
                "verified_by": text(card.get("verified_by")), "verified_on": text(card.get("verified_on")),
            }
        tr["ready"] = has_pkg and bool([f for f in findings if f["track"] == tid])
        for q in parse_questions(extra / "test_questions.md"):
            q["track"] = tid
            questions.append(q)
        if tid == "T3":
            ds = t3_dataset(tdir)
            if ds:
                datasets[ds["id"]] = ds
        tracks.append(tr)
        print(f"{tid}: {'package' if tr['ready'] else 'no package yet'}, "
              f"{sum(1 for f in findings if f['track'] == tid)} findings, {len(tr['charts'])} charts")

    findings.sort(key=lambda f: (f["track"], int(re.sub(r"\D", "", f["id"].split("-")[-1]) or 0)))
    data = {"built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), **content,
            "tracks": tracks, "records": records, "findings": findings, "questions": questions,
            "datasets": datasets}
    out = HERE / "data" / "site-data.js"
    out.parent.mkdir(exist_ok=True)
    out.write_text("/* generated by build_site_data.py - do not edit */\nwindow.FIF_DATA = "
                   + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"wrote {out.relative_to(HERE)} ({out.stat().st_size / 1024:.0f} KB): {len(records)} records, "
          f"{len(findings)} findings, {len(questions)} questions, {len(datasets)} datasets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
