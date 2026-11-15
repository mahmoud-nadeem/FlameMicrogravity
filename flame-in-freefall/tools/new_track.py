#!/usr/bin/env python3
"""Create the folder layout of section 7.1 for a track, with what the PSI API already tells us.

    python tools/new_track.py T3        # or your surname; 'all' for every track

Never overwrites a file that already exists, so it is safe to run again.
Prefilled facts come from the PSI API (the same data the PSI pages show) and stay unconfirmed
until you check them on the page and fill verified_on / verified_by in card.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import kitlib as K  # noqa: E402

PAGE = "https://psi.nasa.gov/physci/repo/data/investigations/{}"
MIB = 1024 * 1024


def _write(path: Path, text: str, created: list[Path]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    created.append(path)


def _card(inv: str, meta: dict | None) -> dict:
    if not meta:
        card = {f: "unconfirmed" for f in K.CARD_FIELDS}
        card.update(investigation_id=inv, objectives=f"{K.TODO}: 2 sentences in your own words",
                    approach=f"{K.TODO}: 2 sentences in your own words", verified_on="", verified_by="")
        card["x_prefilled_from"] = "nothing: no PSI metadata in this kit, fill every field from the page"
        return card
    pubs = [{"title": p.get("title", ""), "link": f"https://doi.org/{p['doi']}" if p.get("doi") else "unconfirmed"}
            for p in meta.get("publications") or []]
    card = {
        "investigation_id": inv,
        "title": meta.get("title") or "unconfirmed",
        "acronym": meta.get("acronym") or "unconfirmed",
        "doi": meta.get("doi") or "unconfirmed",
        "license": meta.get("license") or "unconfirmed",
        "version": "unconfirmed",
        "sub_research_area": meta.get("sub_area") or "unconfirmed",
        "related_investigations": meta.get("related") or [],
        "size_on_page": f"{(meta.get('total_size_bytes') or 0) / MIB:,.0f} MB" if meta.get("total_size_bytes") else "unconfirmed",
        "file_types_and_counts": meta.get("file_extensions") or {},
        "has_experiment_table": "yes" if meta.get("experimental_tables") else "no",
        "objectives": f"{K.TODO}: 2 sentences in your own words (read Description on the PSI page)",
        "approach": f"{K.TODO}: 2 sentences in your own words",
        "publications": pubs,
        "verified_on": "",
        "verified_by": "",
        "x_prefilled_from": f"NASA PSI API (investigation record and file listing), retrieved "
                            f"{meta.get('retrieved_at', 'on 2026-11-14')}; NOT yet checked on the page",
        "x_psi_page": PAGE.format(inv),
        "x_how_to_verify": "Open x_psi_page, compare every field, correct what differs, read the version from "
                           "the page, then fill verified_on (date and time) and verified_by (your name). "
                           "size_on_page uses 1 MB = 1,048,576 bytes, as the page does.",
    }
    return card


def _profile(inv: str, meta: dict | None, root: Path, track: str, rec: Path) -> str:
    title = (meta or {}).get("acronym") or inv
    lines = [f"# Profile: {inv} {title}", ""]
    if meta and meta.get("file_categories"):
        lines += ["## Folders on PSI (from the PSI file listing; check against the page)", "",
                  "| Folder | Files | Size (MB, 1 MB = 1,048,576 bytes) |", "| --- | --- | --- |"]
        for name, c in sorted(meta["file_categories"].items()):
            lines.append(f"| {name} | {c['files']} | {c['bytes'] / MIB:,.1f} |")
        lines.append("")
    rel_rec = rec.relative_to(root).as_posix()
    lines += ["## Experimental table and downloaded files", "",
              "Run from the kit root and paste or append the output here:", "", "```bash",
              f'python tools/profile_files.py "data/experimental_tables/{inv}" --out "{rel_rec}/profile.md"',
              f'python tools/profile_files.py "data/raw/{inv}" --out "{rel_rec}/profile.md"   # after downloading',
              "```", "",
              "## Documents (PDF, presentations)", "",
              "| File | Title | Pages | What it is for |", "| --- | --- | --- | --- |", ""]
    return "\n".join(lines)


def _map(inv: str, meta: dict | None, root: Path) -> str | None:
    ets = (meta or {}).get("experimental_tables") or []
    if not ets:
        return None
    out = ["# Mapping for tools/build_run_table.py. You decide every line; the tool applies it and logs it.",
           "# Start with columns: {} to get a table with the identity columns and raw_ copies, then map step by step.",
           "# A constant (value:) needs a reason: say where you read it (PSI page section, document, page).",
           f"investigation_id: {inv}", f"slug: {K.SLUGS[inv]}", "sources:"]
    for et in ets:
        rel = f"{inv}/Experimental table/{et['file']}"
        src = K.find_source(root, rel)
        cols = list(K.read_source(src)[0].columns) if src else et.get("columns", [])
        out += [f"  - file: \"{rel}\"",
                "    header_row: 1",
                "    # source columns (exact names):"] + [f"    #   - {c}" for c in cols] + [
                "    # run_id: \"<column>\"            # or a list of columns; leave out to use r<source_row>",
                "    # run_id_prefix: \"\"              # e.g. N- / I- when two files share test numbers",
                "    keep_raw: true                   # copy every original column as raw_<name>",
                "    columns: {}",
                "    # columns:",
                "    #   material_or_fuel: {from: \"<column>\"}",
                "    #   gravity_level: {value: microgravity_ISS, reason: \"<where you read it>\"}   # microgravity_ISS | ground_1g | partial_gravity | unknown",
                "    #   oxygen_pct: {from: \"<column>\", convert: fraction_to_pct}     # none | fraction_to_pct",
                "    #   pressure_kpa: {from: \"<column>\", convert: atm_to_kpa}        # none | atm_to_kpa | bar_to_kpa | psi_to_kpa | mmhg_to_kpa | torr_to_kpa | mpa_to_kpa | pa_to_kpa",
                "    #   flow_speed_value: {from: \"<column>\"}",
                "    #   flow_speed_unit: {value: \"cm/s\", reason: \"<where the unit is stated>\"}",
                "    #   outcome_raw: {from: \"<column>\"}",
                "    #   notes: {from: \"<column>\"}",
                "    # outcome_map: {\"<raw value>\": \"<your normalised value>\"}    # your category mapping table",
                "    # extra:",
                "    #   x_<name>_<unit>: {from: \"<column>\"}",
                "    # partial_numbers: flag             # flag (default): '21.5 - 21.7' stays empty and is flagged; leading: keep 21.5 and log it",
                ]
    return "\n".join(out) + "\n"


def scaffold(track: str, root: Path = K.ROOT) -> list[Path]:
    root = Path(root)
    t = K.TRACKS[track]
    base = root / "analysis" / track
    created: list[Path] = []
    metas = {inv: K.load_meta(root, inv) for inv in t["records"]}
    for inv in t["records"]:
        meta = metas[inv]
        rec = K.record_dir(root, track, inv)
        name = (meta or {}).get("acronym") or inv
        _write(rec / "card.json", json.dumps(_card(inv, meta), indent=2, ensure_ascii=False) + "\n", created)
        _write(rec / "profile.md", _profile(inv, meta, root, track, rec), created)
        _write(rec / "findings.md", "\n".join([
            f"# Findings: {inv} {name}", "",
            "Format, one line each (lines that start with F- are checked by tools/self_check.py):",
            "`F-<track>-<number> | statement in one sentence | label | source file | row or page | confidence | caveat`",
            "",
            "Labels: OBSERVED IN DATA, REPORTED BY NASA OR A PUBLICATION (source), OUR INFERENCE. "
            "Confidence: high, medium or low.",
            "Rows: the source_row of the run table (line number in the file, or row number in Excel; header = 1).",
            f"Example of the shape only: F-{track}-1 | ... | OBSERVED IN DATA | {inv}/Experimental table/<file>.csv | rows 2-9 | medium | ...",
            "", ""]), created)
        _write(rec / "data_log.md", "\n".join([
            f"# Data log: {inv} {name}", "", f"Format: {K.DATA_LOG_HEADER}", "",
            "tools/build_run_table.py writes its lines between its markers; add your own lines below them.", "", ""]),
            created)
        _write(rec / "tables" / ".gitkeep", "", created)
        _write(rec / "charts" / ".gitkeep", "", created)
        rel_rec = rec.relative_to(root).as_posix()
        mp = _map(inv, meta, root)
        steps = [f"# Run order: {inv} {name}", "", "Run every command from the kit root folder.", ""]
        if mp:
            _write(rec / "scripts" / "run_table_map.yaml", mp, created)
            steps += [f'1. `python tools/build_run_table.py "{rel_rec}/scripts/run_table_map.yaml"`', ""]
        else:
            steps += ["(no experimental table on PSI for this record)", ""]
        steps += ["Add your own scripts below, in the order they must run.", ""]
        _write(rec / "scripts" / "README.md", "\n".join(steps), created)

    _write(base / "notes" / "concepts.md", "\n".join([
        f"# Concept notes ({track}, {t['member']})", "",
        "For each concept: five lines in your own words, then the source you checked it against "
        "(PSI page, NASA page or paper), not just 'the assistant said so'.", "", ""]), created)
    _write(base / "si_log.md", "\n".join([
        f"# AI-use log ({track}, {t['member']})", "",
        "time | tool used | what I asked for | what I used from the answer | where it appears | whether I checked it, and how",
        "",
        "2026-11-14 | Claude (Anthropic), used by Mahmoud Nadeem | the team kit tools (PSI downloader, file parsers, "
        "folder templates, run-table builder, self-check, packager) | the tools as published in the kit (prefilled "
        "line: keep it if you use the kit) | scripts/, tools/, pipeline/, analysis/ templates | automated tests in "
        "tests/; card fields prefilled from the PSI API are checked by me on the PSI page",
        "", ""]), created)
    refs = [f"# References ({track}, {t['member']})", "", "## NASA PSI records", ""]
    for inv in t["records"]:
        m = metas[inv] or {}
        refs.append(f"- {inv} {m.get('acronym') or ''}, DOI {m.get('doi') or 'unconfirmed'}, {PAGE.format(inv)} "
                    "[replace this line with the text of 'Cite this Investigation' on the PSI page]")
    refs += ["", "## Publications (every paper you read, with DOI)", "", "",
             "## Software and tools", "",
             "- Python and the open-source libraries in requirements.txt (pandas, NumPy, Matplotlib, SciPy, "
             "scikit-learn, openpyxl, xlrd, requests, PyYAML)",
             "- Team kit tools, made by Mahmoud Nadeem with AI assistance (see si_log.md)", "",
             "## Other sources (web pages, images)", "", ""]
    _write(base / "references.md", "\n".join(refs), created)
    hand = [f"# HANDOFF ({track})", "",
            f"Track and name: {track}, {t['member']}",
            "Version and time:",
            "Records covered (with VERIFIED or UNCONFIRMED for each ID):"]
    hand += [f"- {inv} {(metas[inv] or {}).get('acronym') or ''}: UNCONFIRMED" for inv in t["records"]]
    hand += ["What is done (tables, findings count, charts):",
             "Model status (gate passed, failed or not attempted, and why):",
             "Data quirks and traps another person must know:",
             "What I could not do and why:",
             f"Self-check results (items 1 to 10 of 7.6): run `python tools/self_check.py {track}` and paste "
             f"analysis/{track}/SELF_CHECK.md here",
             "Questions for Mohammed Tamer:",
             "Idea tickets raised (titles):",
             "Hours spent:", ""]
    _write(base / "HANDOFF.md", "\n".join(hand), created)
    return created


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track", help="T1..T6, your surname, or 'all'")
    args = ap.parse_args(argv)
    tracks = list(K.TRACKS) if args.track.lower() == "all" else [K.track_id(args.track)]
    for tr in tracks:
        created = scaffold(tr)
        print(f"{tr}: {len(created)} files created" + ("" if created else " (everything already existed)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
