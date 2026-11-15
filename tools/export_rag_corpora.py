#!/usr/bin/env python3
"""Build the unified dataset inventory and export the team's RAG corpora, one folder per dataset.

    python tools/export_rag_corpora.py            # from the project root

Writes
  docs/dataset_inventory.json   every dataset (PSI ID), its names, crew, sources, packages, corpora and conflicts
  docs/DATASET_INVENTORY.md     the same as a readable table
  deliverables/rag-corpora.zip  rag-corpora/<PSI-ID name>/corpus.txt (or MISSING_CORPUS.txt) + manifest.json + README.md

Datasets are matched on PSI ID. Names from other files join a PSI ID only through ALIASES (with evidence).
Corpora are listed explicitly in TEXT_SOURCES / JSONL_SOURCES; chunk text is copied verbatim and mapped with
per-file rules. Nothing is dropped: identical copies are kept once (and listed), differing texts that share a
chunk ID are kept side by side and recorded as conflicts, unmappable chunks go to _unmapped/. Superseded corpus
versions are compared chunk by chunk and their differences recorded, but not exported a second time.
To add a corpus: put it under RAG/, add it to TEXT_SOURCES or JSONL_SOURCES with a mapping rule, re-run.
"""
from __future__ import annotations

import csv, hashlib, io, json, re, shutil, sys, zipfile
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVALID = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
PSI = re.compile(r"PSI-\d+")

# Names used in RAG/rag-map.json and the assignment sheets -> PSI ID, with the evidence for each match.
ALIASES = {
    "BASS": ("PSI-26", "NASA acronym (psi_metadata/PSI-26.json)"),
    "BASS-II": ("PSI-25", "NASA acronym (psi_metadata/PSI-25.json)"),
    "SAFFIRE-I": ("PSI-98", "NASA acronym (psi_metadata/PSI-98.json)"),
    "SAFFIRE-II": ("PSI-99", "NASA acronym (psi_metadata/PSI-99.json)"),
    "SAFFIRE-III": ("PSI-100", "NASA acronym (psi_metadata/PSI-100.json)"),
    "SAME": ("PSI-102", "NASA acronym (psi_metadata/PSI-102.json)"),
    "SAME-R": ("PSI-101", "NASA acronym (psi_metadata/PSI-101.json)"),
    "DAFT": ("PSI-47", "NASA acronym 'DAFT / DAFT-2'; verified sheet: 'DAFT and DAFT-2, PSI-47'"),
    "FLEX": ("PSI-69", "NASA acronym (psi_metadata/PSI-69.json)"),
    "FLEX-2": ("PSI-68", "NASA acronym (psi_metadata/PSI-68.json)"),
    "FLEX-II": ("PSI-68", "Mohammed Tamer's corpus folder name PSI-68_FLEX_II; the corpus says 'FLEX-2, Flame Extinguishment Experiment-2 (PSI-68)'"),
    "ACME-E-FIELD": ("PSI-22", "NASA acronym 'ACME E-FIELD Flames' (psi_metadata/PSI-22.json); verified sheet: Khaled Adawi, ACME E-FIELD Flames, PSI-22"),
    "ACME-S-FLAME": ("PSI-23", "NASA acronym 'ACME s-Flame' (psi_metadata/PSI-23.json); verified sheet: Khaled Adawi, ACME S-Flames, PSI-23"),
    "ACME-CLD": ("PSI-21", "NASA acronym 'ACME CLD Flame' (psi_metadata/PSI-21.json); verified sheet: Mohamed Gamal, ACME CLD, PSI-21"),
    "CFI": ("PSI-39", "NASA acronym (psi_metadata/PSI-39.json)"),
    "ACME-CFI-G": ("PSI-159", "NASA acronym 'ACME CFI-G' (psi_metadata/PSI-159.json)"),
    "ACME-BRE": ("PSI-20", "NASA acronym 'ACME BRE' (psi_metadata/PSI-20.json)"),
    "ACME-FLAME-DESIGN": ("PSI-10", "NASA acronym 'ACME/Flame Design' (psi_metadata/PSI-10.json)"),
    "SPICE": ("PSI-107", "NASA acronym (psi_metadata/PSI-107.json)"),
    "SLICE": ("PSI-106", "NASA acronym (psi_metadata/PSI-106.json)"),
}
# website folder names that differ from <PSI-ID>_<NASA name>, and corpus files kept inside website folders
DASH_FOLDER = {"PSI-68": "PSI-68_FLEX_II"}
DASH_SOURCES = ["fif-dashboard/rag/PSI-68_FLEX_II/rag_corpus_flex2.txt"]
CREW_KEYS = {"morgan": "Amr Morgan", "shreif": "Mohamed Shreif", "nadeem": "Mahmoud Nadeem", "tamer": "Mohammed Tamer",
             "adwi": "Khaled Adawi", "gamal": "Mohamed Gamal"}


# ------------------------------------------------------------------ chunk mapping rules
def by_folder(psi):
    return lambda cid, header, body: ({psi}, f"per-dataset corpus file (folder {psi})")


def map_t1_v6(psi):
    """Morgan v6 per-dataset files: the file's dataset. A chunk ID naming the other BASS record would be a conflict."""
    def rule(cid, header, body):
        other = {"PSI-26": "PSI-25", "PSI-25": "PSI-26"}[psi]
        if re.match(rf"(T1-|F-T1-){other[4:]}", cid):
            return {psi, other}, f"in the {psi} file but the chunk ID names {other} (recorded as a conflict)"
        return {psi}, f"per-dataset corpus file (folder {psi}); chunks also present in the other BASS file are shared"
    return rule


def map_saffire(cid, header, body):
    m = re.search(r"^Investigation:\s*(.+)$", body, re.M)
    ids = set(PSI.findall(m.group(1))) if m else set()
    return (ids, "'Investigation:' line of the section") if ids else (set(), "no Investigation line")


T3_SOURCES = {"S1": {"PSI-102"}, "S4": {"PSI-102"}, "S2": {"PSI-101"}, "S5": {"PSI-101"}, "S8": {"PSI-101"},
              "S3": {"PSI-47"}, "S6": {"PSI-47"}, "S9": {"PSI-47"}, "S10": {"PSI-47"}, "S11": {"PSI-47"},
              "S7": {"PSI-101", "PSI-102"}}   # S7 = the SAME and SAME-R results workbook (both flights); S12/S13 are general
T3_ALL = {"PSI-102", "PSI-101", "PSI-47"}


def map_mahmoud(cid, header, body):
    ids = set(PSI.findall(header))
    if ids: return ids, "PSI ID(s) in chunk header"
    if cid.startswith("T3-TEST-SAMER-"): return {"PSI-101"}, "chunk ID T3-TEST-SAMER (SAME-R flight test)"
    if cid.startswith("T3-TEST-SAME-"): return {"PSI-102"}, "chunk ID T3-TEST-SAME (SAME flight test)"
    if cid.startswith("T3-DAFT-"): return {"PSI-47"}, "chunk ID T3-DAFT (DAFT test)"
    m = re.search(r"\|\s*source:\s*([^|]+)", header)
    src = m.group(1).strip() if m else ""
    codes = set()
    for a, b in re.findall(r"S(\d+)(?:-S(\d+))?", src):
        codes |= {f"S{k}" for k in range(int(a), int(b or a) + 1)}
    ids = set().union(*(T3_SOURCES.get(c, set()) for c in codes)) if codes else set()
    if ids: return ids, f"declared sources '{src}' (S-codes defined in the file header)"
    return set(T3_ALL), f"track-level T3 chunk (source: {src or 'none'}) covering SAME, SAME-R and DAFT"


def map_tamer_pack(cid, header, body):
    title = header.split("]", 1)[1].split("|")[0]
    if re.search(r"FLEX\s*\(2005\)\s*vs\s*FLEX-2", title): return {"PSI-69", "PSI-68"}, "header compares FLEX with FLEX-2"
    if re.match(r"\s*FLEX-2\b", title): return {"PSI-68"}, "header names FLEX-2"
    return {"PSI-69"}, "FLEX deep analysis pack (file header: FLEX, PSI-69); header names no other experiment"


def map_flex2(cid, header, body):
    """Tamer's FLEX-2 corpus: every chunk has 'Investigation: FLEX-2, Flame Extinguishment Experiment-2 (PSI-68)'."""
    m = re.search(r"^Investigation:.*\((PSI-\d+)\)", body, re.M)
    return ({m.group(1)}, "'Investigation:' line in the chunk") if m else (set(), "no Investigation line")


def map_gamal(cid, header, body):
    m = re.search(r"^Investigation:.*\((PSI-\d+)\)", body, re.M)
    if m: return {m.group(1)}, "'Investigation:' line in the chunk"
    if cid.startswith("spice-"): return {"PSI-107"}, "slug prefix spice-"
    if cid.startswith("slice-"): return {"PSI-106"}, "slug prefix slice-"
    return set(), "no rule"


ACME_COVERED = {"PSI-10", "PSI-20", "PSI-22", "PSI-23"}   # the T5 corpus README / chunk ACME-03: "four PSI accessions"


def map_acme(cid, header, body):
    inv = (re.search(r"^INVESTIGATION_ID:\s*(.+)$", body, re.M) or [None, ""])[1].strip()
    if PSI.fullmatch(inv): return {inv}, "INVESTIGATION_ID field of the chunk"
    if inv == "ACME": return set(ACME_COVERED), ("INVESTIGATION_ID 'ACME': cross-investigation content, shared by the four PSI accessions the corpus "
                                               "covers (its README; chunk ACME-03 notes NASA counts five or six ACME investigations)")
    return set(), f"INVESTIGATION_ID '{inv}' not recognised"


CHUNK_ID = lambda h: re.search(r"\[CHUNK ([^\]]+)\]", h).group(1)
SECTION_ID = lambda h: re.match(r"^=== (.+?) ===", h).group(1).split(" | ")[0].strip()
TEXT_SOURCES = [   # path, track, contributor, chunk-start pattern, chunk ID, mapping rule
    ("RAG/Morgan_RAG_Corpus_v8/PSI-26_BASS/rag_corpus.txt", "T1", "Amr Morgan", r"^\[CHUNK ", CHUNK_ID, map_t1_v6("PSI-26")),
    ("RAG/Morgan_RAG_Corpus_v8/PSI-25_BASS-II/rag_corpus.txt", "T1", "Amr Morgan", r"^\[CHUNK ", CHUNK_ID, map_t1_v6("PSI-25")),
    ("RAG/SAFFIRE_RAG_Corpora/PSI-98/rag_corpus_psi98.txt", "T2", "T2 (Mohamed Shreif by assignment; the files name no author)", r"^=== .+ ===\s*$", SECTION_ID, map_saffire),
    ("RAG/SAFFIRE_RAG_Corpora/PSI-99/rag_corpus_psi99.txt", "T2", "T2 (Mohamed Shreif by assignment; the files name no author)", r"^=== .+ ===\s*$", SECTION_ID, map_saffire),
    ("RAG/SAFFIRE_RAG_Corpora/PSI-100/rag_corpus_psi100.txt", "T2", "T2 (Mohamed Shreif by assignment; the files name no author)", r"^=== .+ ===\s*$", SECTION_ID, map_saffire),
    ("RAG/Mahmoud.txt", "T3", "Mahmoud Nadeem", r"^### \[CHUNK ", CHUNK_ID, map_mahmoud),
    ("RAG/Tamer.txt", "T4", "Mohammed Tamer", r"^### \[CHUNK ", CHUNK_ID, map_tamer_pack),
    # kept in the website's folder for this dataset (the export leaves it in place, see DASH_SOURCES)
    ("fif-dashboard/rag/PSI-68_FLEX_II/rag_corpus_flex2.txt", "T4", "Mohammed Tamer", r"^### ", lambda h: h[4:].strip(), map_flex2),
    ("RAG/Gamal.txt", "T6", "Mohamed Gamal", r"^### ", lambda h: h[4:].strip(), map_gamal),
] + [(f"RAG/NASA_ACME_RAG_Corpora_By_Dataset/{f}", "T5", "Khaled Adawi", r"^CHUNK \d+/\d+ \| ID: ", lambda h: re.search(r"ID: (\S+)", h).group(1), map_acme)
     for f in ["PSI-10_Flame_Design/PSI-10_Flame_Design_RAG_Corpus.txt", "PSI-20_Burning_Rate_Emulator/PSI-20_Burning_Rate_Emulator_RAG_Corpus.txt",
               "PSI-22_E_FIELD/PSI-22_E_FIELD_RAG_Corpus.txt", "PSI-23_s_Flame/PSI-23_s_Flame_RAG_Corpus.txt", "ACME_Shared/ACME_Shared_RAG_Corpus.txt"]]
JSONL_SOURCES = [("RAG/CompleteTamerRAGChunks/microgravity_combustion_complete_rag.jsonl", "T4", "Mohammed Tamer")]
TAMER_DOMAINS = {"cdfi": "PSI-159", "psi-159": "PSI-159", "CFI-G": "PSI-159", "flex": "PSI-69", "psi-69": "PSI-69", "FLEX": "PSI-69",
                 "flex2": "PSI-68", "psi-68": "PSI-68", "FLEX-2": "PSI-68", "cfi": "PSI-39", "CFI": "PSI-39"}
TAMER_FOLDERS = {"CDFI": "PSI-159", "Flex": "PSI-69", "Flex2": "PSI-68", "CFI": "PSI-39"}
TAMER_ALL = {"PSI-69", "PSI-68", "PSI-39", "PSI-159"}   # the corpus manifest lists FLEX, FLEX-2, CFI, CFI-G
# Older versions kept in archive/: compared with their replacement, not exported again.
T1_V8 = ["RAG/Morgan_RAG_Corpus_v8/PSI-26_BASS/rag_corpus.txt", "RAG/Morgan_RAG_Corpus_v8/PSI-25_BASS-II/rag_corpus.txt"]
SUPERSEDED = [("archive/superseded/RAG/Amr.txt", r"^### \[CHUNK ", CHUNK_ID, T1_V8,
               "T1 v5 deep analysis pack; its author ships per-dataset corpora as the retrieval files"),
              ("archive/superseded/RAG/Morgan_RAG_Corpus_v6/PSI-26/rag_corpus.txt", r"^\[CHUNK ", CHUNK_ID, T1_V8[:1], "T1 v6 PSI-26 corpus, replaced by v8"),
              ("archive/superseded/RAG/Morgan_RAG_Corpus_v6/PSI-25/rag_corpus.txt", r"^\[CHUNK ", CHUNK_ID, T1_V8[1:], "T1 v6 PSI-25 corpus, replaced by v8")]
# Other copies of corpus text in the project: checked against the exported source, not exported again.
COPIES = [("flame-in-freefall-kit/analysis/T3/extra/rag_pack_T3.txt", "RAG/Mahmoud.txt", "bytes"),
          ("flame-in-freefall-kit/analysis/T1/PSI-26_bass/rag_corpus.txt", T1_V8[0], "bytes"),
          ("flame-in-freefall-kit/analysis/T1/PSI-25_bass-ii/rag_corpus.txt", T1_V8[1], "bytes"),
          ("flame-in-freefall-kit/analysis/T1/Amr_BASS_Deep_Analysis_v8_clean.txt", "RAG/Morgan_RAG_Corpus_v8/PSI-2*/rag_corpus.txt", "chunks"),
          ("RAG/CompleteTamerRAGChunks/microgravity_combustion_complete_knowledge.txt", "RAG/CompleteTamerRAGChunks/microgravity_combustion_complete_rag.jsonl", "rendering")]
NOT_CORPUS = [("RAG/Flame in Freefall Backend and RAG Plan (FAISS).md", "design plan for the RAG backend, not corpus content"),
              ("RAG/rag-map.json", "bot-to-dataset access map (an inventory source)"),
              ("RAG/NASA_ACME_RAG_Corpora_By_Dataset/README.txt", "the T5 corpus's description (copied to _source_metadata/)"),
              ("RAG/NASA_ACME_RAG_Corpora_By_Dataset/manifest.json", "the T5 corpus's chunk manifest; its source rag_chunks.jsonl was not submitted (copied to _source_metadata/)"),
              ("archive/snapshots/RAG_Corpus_by_Dataset.zip", "an earlier export, superseded by deliverables/rag-corpora.zip")]


def split_marked(text, pattern):
    lines = text.split("\n")
    pre, chunks, cur = [], [], None
    for i, line in enumerate(lines, 1):
        if re.match(pattern, line):
            cur = [line]; chunks.append([cur, i])
        elif cur is None:
            pre.append(line)
        else:
            cur.append(line)
    out = []
    for c, start in chunks:
        while c and (not c[-1].strip() or re.fullmatch(r"=+", c[-1].strip())):   # blank lines and ===== separators end a chunk
            c = c[:-1]
        out.append((c[0], "\n".join(c), start, start + len(c) - 1))
    return re.sub(r"\n=+\s*$", "", "\n".join(pre).strip()), out


def render_jsonl(r):
    """Same layout as the author's microgravity_combustion_complete_knowledge.txt."""
    j = lambda v: json.dumps(v, ensure_ascii=False)
    lines = [f"CHUNK_ID: {r['chunk_id']}", f"DOMAIN: {r['domain']}", f"CATEGORY: {r['category']}", f"TOPIC: {r['topic']}",
             f"CONTENT_TYPE: {r['content_type']}", f"EVIDENCE_STATUS: {r['evidence_status']}", f"SOURCE_FILES: {' | '.join(r.get('source_files') or [])}"]
    if r.get("layer") and r["layer"] != r["content_type"]: lines.append(f"LAYER: {r['layer']}")
    if r.get("locator") is not None: lines.append(f"LOCATOR: {j(r['locator'])}")
    if r.get("metadata") is not None: lines.append(f"METADATA: {j(r['metadata'])}")
    known = {"chunk_id", "domain", "category", "topic", "language", "source_files", "content", "content_type", "evidence_status", "layer", "source_archive", "locator", "metadata"}
    extra = {k: v for k, v in r.items() if k not in known}
    if extra: lines.append(f"OTHER_FIELDS: {j(extra)}")
    return "\n".join(lines) + "\n\nCONTENT:\n" + r["content"]


def load_js_json(p):
    s = p.read_text(encoding="utf-8")
    return json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))


def folder_name(psi, name):
    return INVALID.sub("_", f"{psi} {name}".strip() if name else psi).rstrip(" .")


def main() -> int:
    P = ROOT
    sha = lambda p: hashlib.sha256((P / p).read_bytes()).hexdigest()
    # ================================================================ 1. dataset inventory
    meta = {p.stem: json.loads(p.read_text(encoding="utf-8-sig")) for p in (P / "flame-in-freefall-kit/data/psi_metadata").glob("PSI-*.json")}
    invs = json.loads((P / "flame-in-freefall/site_data/investigations.json").read_text(encoding="utf-8"))
    site = load_js_json(P / "fif-dashboard/data/site-data.js")
    rag_map = json.loads((P / "RAG/rag-map.json").read_text(encoding="utf-8"))
    sheet = list(csv.DictReader(open(P / "docs/psi_member_assignments_verified.csv", encoding="utf-8-sig")))
    chars = {c["id"]: c["name"] for c in site["characters"]["characters"]}
    track_of = {t["id"]: chars.get(t["member"], t["member"]) for t in site["tracks"]}

    ds: "OrderedDict[str, dict]" = OrderedDict()
    def entry(psi):
        if psi not in ds:
            m = meta.get(psi, {})
            ds[psi] = {"psi_id": psi, "nasa_acronym": m.get("acronym", ""), "title": m.get("title", ""), "project_type": m.get("project_type", ""),
                       "doi": m.get("doi", ""), "aliases": [], "listed_in": [], "track": "", "crew": [], "alias_evidence": [],
                       "kit_package": None, "dashboard": None, "rag": None, "conflicts": []}
        return ds[psi]
    add = lambda lst, v: v and v not in lst and lst.append(v)

    for psi in sorted(meta, key=lambda x: int(x[4:])):
        add(entry(psi)["listed_in"], f"flame-in-freefall-kit/data/psi_metadata/{psi}.json")
    for it in invs:
        add(entry(it["id"])["listed_in"], "flame-in-freefall/site_data/investigations.json")
    for psi, r in site["records"].items():
        e = entry(psi); add(e["listed_in"], "fif-dashboard/data/site-data.js (records)"); add(e["aliases"], r.get("acronym") or "")
        e["track"] = r["track"]; add(e["crew"], f"{track_of.get(r['track'])} (dashboard {r['track']})")
        nf = len(r.get("findings") or [])
        e["dashboard"] = {"shown": True, "display_name": r.get("acronym") or psi, "findings": nf}
    for row in sheet:
        ids = PSI.findall(row.get("PSI ID (verified)") or "") or PSI.findall(row.get("PSI ID") or "")
        if len(ids) != 1: continue
        e = entry(ids[0]); add(e["listed_in"], "docs/psi_member_assignments_verified.csv")
        add(e["aliases"], row["Investigation"].split(" - ")[0].strip())
        who = row["Member"].strip()
        add(e["crew"], f"{who} (assignment sheet, {row['Track'].split()[0]})" if who != "UNASSIGNED" else f"unassigned (sheet suggests {row['Track'].split()[0]})")
        if not e["track"] and who == "UNASSIGNED": e["track"] = ""
    unmatched = []
    for key, names in rag_map.items():
        if names == ["*"]: continue                  # the guide may read every dataset; not a dataset
        for n in names:
            if n not in ALIASES: unmatched.append((key, n)); continue
            psi, why = ALIASES[n]; e = entry(psi)
            add(e["listed_in"], "RAG/rag-map.json"); add(e["aliases"], n); add(e["alias_evidence"], f"{n}: {why}")
            add(e["crew"], f"{CREW_KEYS.get(key, key)} (rag-map key '{key}')"); e["rag_map_key"] = key
    for key, n in unmatched:
        ds[f"RAGMAP:{n}"] = {"psi_id": "", "nasa_acronym": "", "title": "", "aliases": [n], "listed_in": ["RAG/rag-map.json"], "track": "",
                             "crew": [key], "alias_evidence": ["no verified PSI match"], "kit_package": None, "dashboard": None, "rag": None, "conflicts": []}
    for card in sorted((P / "flame-in-freefall-kit/analysis").glob("T*/PSI-*/card.json")):
        c = json.loads(card.read_text(encoding="utf-8")); psi = c.get("investigation_id") or card.parent.name.split("_")[0]
        e = entry(psi); f = card.parent / "findings.md"
        n = sum(1 for l in f.read_text(encoding="utf-8").splitlines() if l.startswith("F-")) if f.exists() else 0
        e["kit_package"] = {"folder": str(card.parent.relative_to(P)).replace("\\", "/"), "findings": n,
                            "charts": sum(len(list((card.parent / d).glob("*.png"))) for d in ("charts", "eda") if (card.parent / d).is_dir()),
                            "verified_by": c.get("verified_by", ""), "verified_on": c.get("verified_on", "")}
        m = meta.get(psi, {})
        for k in ("title", "acronym", "doi", "license"):
            a, b = str(c.get(k, "")).strip(), str(m.get(k, "")).strip()
            if a != b and (a or b):
                note = ("same licence, different notation" if k == "license" and a == "CC0-1.0" and "Zero v1.0" in b else
                        "card holds a verification placeholder" if a.lower() == "unconfirmed" else "values differ")
                e["conflicts"].append({"type": "card_vs_nasa_metadata", "field": k, "card": a, "nasa_metadata": b, "note": note,
                                       "files": [e["kit_package"]["folder"] + "/card.json", f"flame-in-freefall-kit/data/psi_metadata/{psi}.json"]})
    # NASA experimental tables already in the kit (retrieved from the PSI API; data/CHECKSUMS.csv): data-row counts per file
    for psi, e in ds.items():
        e["kit_experimental_tables"] = []
        for f in sorted((P / "flame-in-freefall-kit/data/experimental_tables" / psi).glob("*/*.csv")):
            rows = list(csv.reader(io.StringIO(f.read_bytes().decode("utf-8-sig", errors="replace"))))
            e["kit_experimental_tables"].append({"file": f.relative_to(P).as_posix(), "data_rows": sum(1 for r in rows[1:] if any(x.strip() for x in r))})
    # assignment consistency: rag-map vs the assignment sheet / dashboard
    owner_key = {v: k for k, v in CREW_KEYS.items()}
    for psi, e in ds.items():
        assigned = [c.split(" (")[0] for c in e["crew"] if "(assignment sheet" in c]
        if assigned and assigned[0] in owner_key and e.get("rag_map_key") != owner_key[assigned[0]]:
            e["conflicts"].append({"type": "rag_map_omission", "note": f"assigned to {assigned[0]} in the verified sheet and the dashboard, but RAG/rag-map.json "
                                   f"does not list it under '{owner_key[assigned[0]]}': a backend using the map would not give that bot this dataset",
                                   "files": ["RAG/rag-map.json", "docs/psi_member_assignments_verified.csv"]})
    for e in ds.values():
        e["display_name"] = e["nasa_acronym"] or next((a for a in e["aliases"] if a in ALIASES), "") or ""
        e["folder"] = folder_name(e["psi_id"], e["display_name"]) if e["psi_id"] else folder_name("RAGMAP", e["aliases"][0])
    assert len({e["folder"].lower() for e in ds.values()}) == len(ds), "folder collision"

    # ================================================================ 2. corpora -> chunks
    chunks, preambles, sources = [], {}, []
    for rel, track, who, pat, idfn, rule in TEXT_SOURCES:
        txt = (P / rel).read_bytes().decode("utf-8")              # strict: invalid UTF-8 stops the export
        pre, parsed = split_marked(txt, pat); preambles[rel] = pre
        sources.append({"file": rel, "track": track, "contributor": who, "chunks": len(parsed), "sha256": sha(rel)})
        for header, body, s, e_ in parsed:
            cid = idfn(header); ids, basis = rule(cid, header, body)
            chunks.append({"source": rel, "chunk_id": cid, "text": body, "lines": f"lines {s}-{e_}", "datasets": set(ids), "basis": basis})
    for rel, track, who in JSONL_SOURCES:
        rows = [json.loads(l) for l in (P / rel).read_text(encoding="utf-8").splitlines() if l.strip()]
        knowledge = P / rel.replace("_rag.jsonl", "_knowledge.txt")
        preambles[rel] = knowledge.read_text(encoding="utf-8").split("\n\nCHUNK_ID:", 1)[0].strip() if knowledge.exists() else ""
        sources.append({"file": rel, "track": track, "contributor": who, "chunks": len(rows), "sha256": sha(rel)})
        for i, r in enumerate(rows, 1):
            folders = {f.split("/")[0] for f in r.get("source_files") or []}
            by_f = {TAMER_FOLDERS[f] for f in folders if f in TAMER_FOLDERS}
            if r["domain"] in TAMER_DOMAINS:
                ids, basis = {TAMER_DOMAINS[r["domain"]]}, f"JSONL domain '{r['domain']}'"
                if by_f and by_f != ids: ids, basis = ids | by_f, basis + f" plus source folder(s) {sorted(folders)}"
            elif by_f:
                ids, basis = by_f, f"source folder(s) {sorted(folders)}"
            else:
                ids, basis = set(TAMER_ALL), f"corpus-wide chunk (domain '{r['domain']}'), shared by the corpus's four investigations"
            chunks.append({"source": rel, "chunk_id": r["chunk_id"], "text": render_jsonl(r), "key": r["content"], "lines": f"jsonl record {i}",
                           "datasets": ids, "basis": basis})

    # identical text -> kept once (datasets merged); same ID with different text -> both kept, conflict recorded
    seen, copies = {}, []
    for c in chunks:
        k = hashlib.sha256((c.get("key") or c["text"]).encode()).hexdigest()
        if k in seen:
            keep = seen[k]; keep.setdefault("copies", []).append(f"{c['chunk_id']} ({c['source']})"); keep["datasets"] |= c["datasets"]
            c["merged_into"] = keep; copies.append({"chunk": c["chunk_id"], "source": c["source"], "kept": keep["chunk_id"], "kept_source": keep["source"]})
        else:
            seen[k] = c
    live = [c for c in chunks if "merged_into" not in c]
    by_id = defaultdict(list)
    for c in live: by_id[c["chunk_id"]].append(c)
    id_conflicts = []
    for cid, cs in by_id.items():
        if len(cs) > 1:
            id_conflicts.append({"type": "same_chunk_id_different_text", "chunk_id": cid, "sources": [c["source"] for c in cs]})
            for c in cs: c["variant"] = True
    for c in live:
        if "recorded as a conflict" in c["basis"]:
            id_conflicts.append({"type": "chunk_id_vs_file", "chunk_id": c["chunk_id"], "sources": [c["source"]], "note": c["basis"]})
    for c in live:   # chunks the author labelled as conflicts or unverified: listed with the kit's NASA table row counts
        lvl = (re.search(r"^EVIDENCE_LEVEL:\s*(\S+)", c["text"], re.M) or [None, ""])[1]
        if lvl in ("third_party_conflict", "third_party_unverified", "documented_source_difference"):
            id_conflicts.append({"type": f"author_flagged_{lvl}", "chunk_id": c["chunk_id"], "sources": [c["source"]],
                                 "note": c["text"].split("CONTENT:", 1)[-1].strip(),
                                 "kit_tables": {p: ds[p]["kit_experimental_tables"] for p in sorted(c["datasets"]) if p in ds and ds[p]["kit_experimental_tables"]},
                                 "status": "author's caveat kept verbatim; table counts are context, not a resolution of the NASA release question"})
    doi_checks = {}   # DOIs stated inside corpus chunks vs the DOI in NASA's PSI API metadata
    for c in live:
        for doi in set(re.findall(r"^DOI:\s*(\S+)", c["text"], re.M)):
            for p in c["datasets"]:
                k = (p, doi)
                if k not in doi_checks:
                    nasa = meta.get(p, {}).get("doi", "")
                    doi_checks[k] = {"dataset": p, "doi_in_corpus": doi, "doi_in_nasa_metadata": nasa, "match": doi == nasa, "chunks": 0,
                                     "corpus_label": (re.search(r"^DOI_VERIFICATION:\s*(\S+)", c["text"], re.M) or [None, ""])[1]}
                doi_checks[k]["chunks"] += 1
    known = {e["psi_id"] for e in ds.values() if e["psi_id"]}
    for c in live:
        c["outside"] = sorted(c["datasets"] - known); c["datasets"] &= known

    # superseded versions: chunk-by-chunk comparison with their replacement
    superseded = []
    def chunk_map(rel, pat, idfn):
        return {idfn(h): b for h, b, _, _ in split_marked((P / rel).read_text(encoding="utf-8"), pat)[1]}
    for rel, pat, idfn, repl, why in SUPERSEDED:
        if not (P / rel).exists():   # e.g. a project copy without archive/: keep the last recorded comparison
            prev = json.loads((P / "docs/dataset_inventory.json").read_text(encoding="utf-8")) if (P / "docs/dataset_inventory.json").exists() else {}
            kept = [s for s in prev.get("superseded_versions", []) if s.get("file") == rel]
            superseded += kept or [{"file": rel, "why": why, "comparison": "file not present in this copy"}]
            id_conflicts += [c for c in prev.get("chunk_conflicts", []) if c.get("type") == "superseded_wording_change" and rel in c.get("sources", [])]
            continue
        old = chunk_map(rel, pat, idfn); new = {}
        for r in repl: new.update(chunk_map(r, r"^\[CHUNK ", CHUNK_ID))
        strip = lambda t: re.sub(r"(?m)^### ", "", t)
        cmp = {"identical": [], "marker_format_only": [], "additions_only": [], "wording_changed": [], "missing_in_replacement": []}
        for cid, t in old.items():
            if cid not in new: cmp["missing_in_replacement"].append(cid); continue
            a, b = strip(t), new[cid]
            if t == b: cmp["identical"].append(cid)
            elif a == b: cmp["marker_format_only"].append(cid)
            elif all(l in b.splitlines() for l in a.splitlines()): cmp["additions_only"].append(cid)
            else:
                al, bl = a.splitlines(), b.splitlines()
                cmp["wording_changed"].append({"chunk_id": cid, "superseded_lines": [l for l in al if l not in bl], "current_lines": [l for l in bl if l not in al]})
        superseded.append({"file": rel, "replaced_by": repl, "why": why, "old_chunks": len(old), "new_only_chunks": sorted(set(new) - set(old)),
                           "comparison": {k: (v if k == "wording_changed" else len(v) if k != "missing_in_replacement" else v) for k, v in cmp.items()}})
        if cmp["missing_in_replacement"]:
            raise SystemExit(f"{rel}: chunks missing in the replacement {cmp['missing_in_replacement']} - export them before archiving")
        # identical-by-ID chunks with only additions are expected between versions; wording changes are listed as conflicts below
        # wording changes between an author's own versions are revisions, not source conflicts: both texts stay in
        # superseded_versions[...].comparison.wording_changed; only the current version is exported
    copy_checks = []
    for rel, of, how in COPIES:
        if not (P / rel).exists(): copy_checks.append({"file": rel, "of": of, "result": "absent"}); continue
        if how == "bytes": ok = (P / rel).read_bytes() == (P / of).read_bytes()
        elif how == "chunks":
            a = chunk_map(rel, r"^\[CHUNK ", CHUNK_ID); b = {}
            for f in sorted(P.glob(of)): b.update(chunk_map(str(f.relative_to(P)), r"^\[CHUNK ", CHUNK_ID))
            ok = a == b
        else:
            t = (P / rel).read_text(encoding="utf-8"); ok = all(f"CHUNK_ID: {json.loads(l)['chunk_id']}" in t for l in (P / of).read_text(encoding="utf-8").splitlines() if l.strip())
        copy_checks.append({"file": rel, "of": of, "check": {"bytes": "byte-identical", "chunks": "same chunk IDs and texts",
                            "rendering": "contains every chunk ID of"}[how], "result": "ok" if ok else "DIFFERS"})
        if not ok: raise SystemExit(f"{rel} is not a copy of {of}: add it as a source instead")

    # files a corpus mentions that are not in the project (e.g. extra/... tables)
    names = {p.name for p in P.rglob("*") if p.is_file() and "archive" not in p.parts}
    referenced_missing = defaultdict(set)
    for c in live:
        for ref in re.findall(r"\bextra/[\w.\-]+\.(?:csv|md|json|txt|xlsx)", c["text"]):
            if ref.split("/")[-1] not in names: referenced_missing[ref].add(c["source"])

    # ================================================================ 3. write the export
    buf = io.BytesIO(); zf = zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED)
    W = lambda path, s: zf.writestr("rag-corpora/" + path, s.encode("utf-8") if isinstance(s, str) else s)
    label = lambda psi: f"{psi} ({ds[psi]['display_name']})" if ds.get(psi, {}).get("display_name") else psi
    order = [s["file"] for s in sources]
    manifest = []
    for key, e in ds.items():
        psi = e["psi_id"]; mine = [c for c in live if psi and psi in c["datasets"]]
        own = [c for c in mine if len(c["datasets"]) == 1]
        status = "exported" if own else "shared" if mine else "missing"
        e["rag"] = {"status": status, "chunks": len(mine), "exclusive_chunks": len(own), "shared_chunks": len(mine) - len(own),
                    "corpus_files": sorted({c["source"] for c in mine}, key=order.index), "folder": f"rag-corpora/{e['folder']}/",
                    "file": "corpus.txt" if mine else "MISSING_CORPUS.txt"}
        name = e.get("display_name") or e["title"] or key
        if not mine:
            W(f"{e['folder']}/MISSING_CORPUS.txt",
              f"MISSING CORPUS\n\nDataset: {name}\nPSI ID: {psi}\nTitle: {e['title']}\nListed in: {', '.join(e['listed_in'])}\n"
              f"Crew: {', '.join(e['crew']) or 'not assigned'}\n\nNo submitted RAG file contains a chunk mapped to this dataset (checked: "
              + ", ".join(order) + ").\nNothing has been written for it here. Add a corpus for this experiment and re-run tools/export_rag_corpora.py.\n")
        else:
            out = [f"RAG CORPUS - {name}", f"Dataset ID: {psi}", f"Title: {e['title']}", f"Names and aliases: {', '.join(e['aliases'])}",
                   f"Listed in: {', '.join(e['listed_in'])}", f"Crew: {', '.join(e['crew'])}",
                   f"Chunks: {len(mine)} ({len(own)} only about this dataset, {len(mine) - len(own)} shared with other datasets)",
                   "Chunk text is copied verbatim. Each chunk is preceded by a '>>>' line: source file, chunk ID, location, mapping rule,",
                   "other datasets that share it, identical copies elsewhere. Each source file's header (source codes S1, S2 ..., evidence",
                   "tags such as [SRC] [CALC] [INF] [FLAG] [DOC] [QA]) is repeated before its chunks because the chunks cite it.", "=" * 100]
            for src in order:
                part = [c for c in mine if c["source"] == src]
                if not part: continue
                out += ["", f"##### SOURCE FILE: {src} ({len(part)} chunks)", "", "--- source-file header (context for citations; not a chunk) ---",
                        preambles.get(src) or "(none)", "--- end of header ---"]
                for c in part:
                    prov = f">>> source: {c['source']} | chunk: {c['chunk_id']} | location: {c['lines']} | mapping: {c['basis']}"
                    others = sorted(c["datasets"] - {psi}, key=lambda x: int(x[4:]))
                    if others: prov += " | SHARED with: " + ", ".join(label(o) for o in others)
                    if c.get("copies"): prov += " | identical text also in: " + "; ".join(c["copies"])
                    if c.get("variant"): prov += " | CONFLICT: another source has different text under this chunk ID (see manifest)"
                    out += ["", prov, c["text"]]
            W(f"{e['folder']}/corpus.txt", "\n".join(out) + "\n")
        manifest.append({"dataset_id": psi or None, "original_dataset_name": name, "nasa_acronym": e["nasa_acronym"], "title": e["title"],
                         "names_and_aliases": e["aliases"], "alias_evidence": e["alias_evidence"], "contributing_json_sources": e["listed_in"],
                         "crew": e["crew"], "exported_folder": e["rag"]["folder"], "corpus_filename": e["rag"]["file"],
                         "corpus_source_files": e["rag"]["corpus_files"], "chunk_count": len(mine), "exclusive_chunk_count": len(own),
                         "shared_chunk_count": len(mine) - len(own), "status": status, "conflicts": e["conflicts"]})
    unmapped = [c for c in live if not c["datasets"]]
    if unmapped:
        W("_unmapped/corpus.txt", "Chunks that could not be mapped to a dataset with confidence (verbatim, with their source).\n" + "\n".join(
            f"\n>>> source: {c['source']} | chunk: {c['chunk_id']} | location: {c['lines']} | reason: {c['basis']}"
            f"{' | refers to: ' + ', '.join(c['outside']) if c['outside'] else ''}\n{c['text']}" for c in unmapped) + "\n")
    for f in sorted((P / "RAG/CompleteTamerRAGChunks").glob("*")):
        if f.suffix in (".json", ".csv"): W(f"_source_metadata/CompleteTamerRAGChunks/{f.name}", f.read_bytes())
    for f in ("README.txt", "manifest.json"):
        W(f"_source_metadata/NASA_ACME_RAG_Corpora_By_Dataset/{f}", (P / "RAG/NASA_ACME_RAG_Corpora_By_Dataset" / f).read_bytes())
    shared = defaultdict(list)
    for c in live:
        if len(c["datasets"]) > 1: shared[" + ".join(sorted(c["datasets"], key=lambda x: int(x[4:])))].append(f"{c['chunk_id']} ({c['source']})")
    totals = {"datasets": len(manifest), "source_chunks": len(chunks), "identical_copies_merged": len(copies), "unique_chunks": len(live),
              "shared_chunks": sum(len(v) for v in shared.values()), "unmapped_chunks": len(unmapped), "conflicts_recorded":
              len(id_conflicts) + sum(len(e["conflicts"]) for e in ds.values()),
              "status_counts": {s: sum(1 for m in manifest if m["status"] == s) for s in ("exported", "shared", "missing")}}
    doc = {"generated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "generated_by": "tools/export_rag_corpora.py",
           "dataset_rule": "union of every listing below, matched on PSI ID; other names join only through explicit aliases",
           "dataset_sources": ["flame-in-freefall-kit/data/psi_metadata/*.json", "flame-in-freefall/site_data/investigations.json",
                               "fif-dashboard/data/site-data.js (records)", "docs/psi_member_assignments_verified.csv", "RAG/rag-map.json",
                               "flame-in-freefall-kit/analysis/T*/PSI-*/card.json"],
           "guide_access": "rag-map 'guide': ['*'] gives the guide every dataset; it is not a dataset",
           "unmatched_rag_map_names": [n for _, n in unmatched], "corpus_sources": sources, "copies_checked": copy_checks,
           "not_corpus": [{"file": f, "why": w} for f, w in NOT_CORPUS], "superseded_versions": superseded, "totals": totals,
           "chunk_conflicts": id_conflicts,
           "doi_cross_checks": sorted(doi_checks.values(), key=lambda d: int(d["dataset"][4:])), "referenced_files_missing": {k: sorted(v) for k, v in referenced_missing.items()},
           "identical_copies": copies, "shared_chunks_by_dataset_set": dict(shared), "datasets": manifest}
    W("manifest.json", json.dumps(doc, ensure_ascii=False, indent=2) + "\n")
    W("README.md", readme(doc))
    W("_tools/export_rag_corpora.py", Path(__file__).read_text(encoding="utf-8"))
    zf.close()

    # ================================================================ 4. validate, then write
    z = zipfile.ZipFile(io.BytesIO(buf.getvalue())); assert z.testzip() is None
    zn = set(z.namelist())
    keys = [m["dataset_id"] or m["original_dataset_name"] for m in manifest]
    assert len(keys) == len(set(keys)) == len(ds), "each dataset exactly once"
    for m in manifest: assert m["exported_folder"] + m["corpus_filename"] in zn, m
    for n in zn:
        if n.endswith((".txt", ".md", ".json", ".py", ".csv")): z.read(n).decode("utf-8")
    for c in live:
        homes = [f"rag-corpora/{ds[p]['folder']}/corpus.txt" for p in c["datasets"]] or ["rag-corpora/_unmapped/corpus.txt"]
        for h in homes: assert c["text"] in z.read(h).decode("utf-8"), (c["chunk_id"], h)
    # website copy of the corpora: one folder per dataset named <PSI-ID>_<rag-map name>, same corpus.txt as the export.
    # Corpus files that live in a website folder (DASH_SOURCES) are kept; build_rag.py skips them because corpus.txt quotes them.
    dash = P / "fif-dashboard/rag"
    keep = {(P / f).resolve() for f in DASH_SOURCES}
    if dash.exists():
        for d in dash.iterdir():
            if not d.is_dir(): continue
            for f in sorted(d.rglob("*"), reverse=True):
                if f.is_file() and f.resolve() not in keep: f.unlink()
                elif f.is_dir() and not any(f.iterdir()): f.rmdir()
            if not any(d.iterdir()): d.rmdir()
    dash.mkdir(exist_ok=True)
    name_of = {}
    for n, (psi, _) in ALIASES.items(): name_of.setdefault(psi, n)          # the first (NASA) name of each dataset
    topic = lambda psi: DASH_FOLDER.get(psi) or f"{psi}_{name_of.get(psi) or INVALID.sub('-', ds[psi]['display_name']).replace(' ', '-')}"
    for psi, e in ds.items():
        if psi in ds and e["psi_id"] and e["rag"]["status"] != "missing":
            (dash / topic(psi)).mkdir(exist_ok=True)
            (dash / topic(psi) / "corpus.txt").write_bytes(z.read(f"rag-corpora/{e['folder']}/corpus.txt"))
    site_map = {k: (["*"] if v == ["*"] else [topic(ALIASES[n][0]) for n in v if n in ALIASES]) for k, v in rag_map.items()}
    (P / "fif-dashboard/content/rag-map.json").write_text(
        "{\n" + ",\n".join(f'  "{k}": {json.dumps(v)}' for k, v in site_map.items()) + "\n}\n", encoding="utf-8")
    (dash / "README.md").write_text("# Crew RAG folders (generated)\n\nWritten by `tools/export_rag_corpora.py` from `RAG/`: one folder per dataset, "
        "`<PSI-ID>_<name>/corpus.txt`, the same text as `deliverables/rag-corpora.zip`. Which crew member reads which folder: "
        "`content/rag-map.json` (generated from `RAG/rag-map.json`). Then run `python build_rag.py`. Do not edit the corpus.txt files by "
        "hand: add or change corpora under `RAG/` and re-run the export.\n\nException: `PSI-68_FLEX_II/rag_corpus_flex2.txt` is Mohammed "
        "Tamer's FLEX-2 corpus as received and lives here; the export reads it as a source (its chunks are in that folder's corpus.txt, "
        "with their provenance) and never deletes it; `build_rag.py` reads the chunks once, from corpus.txt.\n", encoding="utf-8")
    (P / "deliverables").mkdir(exist_ok=True)
    (P / "deliverables/rag-corpora.zip").write_bytes(buf.getvalue())
    inv = {k: v for k, v in doc.items() if k not in ("identical_copies", "shared_chunks_by_dataset_set", "datasets")}
    inv["datasets"] = [{k: v for k, v in e.items() if k != "folder"} for e in ds.values()]
    (P / "docs/dataset_inventory.json").write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (P / "docs/DATASET_INVENTORY.md").write_text(inventory_md(inv), encoding="utf-8")
    print(f"{totals['datasets']} datasets {totals['status_counts']}; {totals['source_chunks']} source chunks, {totals['identical_copies_merged']} identical "
          f"copies merged, {totals['unique_chunks']} unique, {totals['shared_chunks']} shared, {totals['unmapped_chunks']} unmapped, "
          f"{totals['conflicts_recorded']} conflicts recorded")
    print("wrote deliverables/rag-corpora.zip, docs/dataset_inventory.json, docs/DATASET_INVENTORY.md")
    return 0


def readme(doc):
    t = doc["totals"]
    rows = "\n".join(f"| `{m['exported_folder'].split('/', 1)[1]}` | {m['dataset_id'] or '-'} | {', '.join(m['names_and_aliases']) or '-'} | {m['status']} | {m['chunk_count']} |"
                     for m in doc["datasets"])
    srcs = "\n".join(f"| `{s['file']}` | {s['track']} | {s['contributor']} | {s['chunks']} |" for s in doc["corpus_sources"])
    return f"""# RAG corpora by dataset

One folder per dataset: `corpus.txt` (UTF-8) or `MISSING_CORPUS.txt`. `manifest.json` records every dataset, its names and
aliases, the JSON and sheet files that list it, its crew, corpus source files, chunk counts, status and conflicts.
Generated {doc['generated']} by `_tools/export_rag_corpora.py` (in the project: `tools/export_rag_corpora.py`).

## Dataset list
The union of every listing in the project, matched on PSI ID: the kit's NASA metadata (`psi_metadata/*.json`), the pipeline's
`investigations.json`, the dashboard's records, the verified assignment sheet, `RAG/rag-map.json` and the track cards. A name
from the map or the sheet joins a PSI ID only through an explicit alias with stated evidence (`alias_evidence`), e.g.
`"guide": ["*"]` in
the map gives the guide every dataset; it is not a dataset. Folder = PSI ID + NASA acronym (or the map name when NASA lists none);
only characters invalid in folder names become `_`.

## Corpora
| Source | Track | Contributor | Chunks |
| --- | --- | --- | --- |
{srcs}

Mapping rules: T1 v6 files are per dataset (chunks present in both BASS files are shared); SAFFIRE sections by their
`Investigation:` line; T3 by PSI IDs in the header, chunk-ID families, or declared source codes (S1/S4 SAME, S2/S5/S8 SAME-R,
S3/S6/S9-S11 DAFT, S7 both flights); the FLEX pack by its header (FLEX-2 chunks to PSI-68); the complete T4 corpus by each
record's `domain` field cross-checked with its source folder; T6 by its `Investigation:` line.

Chunk text is copied verbatim, each preceded by a `>>>` provenance line. Identical text found in several files is kept once
and every copy is listed. Different texts under the same chunk ID would both be kept and flagged. The superseded T1 v5 pack
(`archive/superseded/RAG/Amr.txt`) is compared chunk by chunk with v6 in the manifest (`superseded_versions`), not exported again.

Totals: {t['source_chunks']} source chunks, {t['identical_copies_merged']} identical copies merged, {t['unique_chunks']} unique,
{t['shared_chunks']} shared across datasets, {t['unmapped_chunks']} unmapped, {t['conflicts_recorded']} conflicts recorded (see manifest).
Status: `exported` has chunks only about this dataset; `shared` only chunks shared with others; `missing` none.

| Folder | PSI ID | Names | Status | Chunks |
| --- | --- | --- | --- | --- |
{rows}
"""


def inventory_md(inv):
    lines = ["# Dataset inventory", "", f"Generated {inv['generated']} by `tools/export_rag_corpora.py` from: " + ", ".join(f"`{s}`" for s in inv["dataset_sources"]) + ".",
             "Datasets are matched on PSI ID. Full detail (aliases with evidence, sources per dataset, conflicts) is in `dataset_inventory.json`.", "",
             "| PSI ID | NASA name | Track | Crew | Kit package | Dashboard | RAG corpus | Conflicts |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for e in inv["datasets"]:
        kp = e["kit_package"]; kp_s = f"{kp['findings']} findings, {kp['charts']} charts" if kp and kp["findings"] else ("template only" if kp else "-")
        db = e["dashboard"]; db_s = f"shown, {db['findings']} findings" if db else "not shown"
        rg = e["rag"]; rg_s = f"{rg['status']} ({rg['chunks']} chunks)" if rg else "-"
        crew = "; ".join(sorted({c.split(' (')[0] for c in e["crew"]})) or "-"
        lines.append(f"| {e['psi_id']} | {e['nasa_acronym'] or e['title'][:48]} | {e['track'] or '-'} | {crew} | {kp_s} | {db_s} | {rg_s} | {len(e['conflicts']) or ''} |")
    lines += ["", "## Conflicts and open points", ""]
    for e in inv["datasets"]:
        for c in e["conflicts"]:
            lines.append(f"- **{e['psi_id']}** {c['type']}: " + (f"`{c['field']}` card `{c['card']}` vs NASA `{c['nasa_metadata']}` ({c['note']})" if "field" in c else c["note"]))
    for c in inv["chunk_conflicts"]:
        kt = "; ".join(f"{p}: " + ", ".join(f"{Path(t['file']).name} has {t['data_rows']} data rows" for t in ts) for p, ts in (c.get("kit_tables") or {}).items())
        lines.append(f"- chunk `{c['chunk_id']}` {c['type']}: {c.get('note', '')} " + (f"Superseded: {c['superseded_lines']} Current: {c['current_lines']}" if "current_lines" in c else "")
                     + (f" Kit NASA table: {kt}." if kt else ""))
    for d in inv.get("doi_cross_checks", []):
        lines.append(f"- **{d['dataset']}** DOI `{d['doi_in_corpus']}` stated in {d['chunks']} corpus chunks (label `{d['corpus_label'] or '-'}`): "
                     + ("matches" if d["match"] else f"DIFFERS from `{d['doi_in_nasa_metadata']}` in") + " NASA's PSI API metadata (kit psi_metadata); the corpus label is left as written")
    for ref, srcs in inv["referenced_files_missing"].items():
        lines.append(f"- `{ref}` is cited by {', '.join(srcs)} but is not in the project")
    for s in inv["superseded_versions"]:
        c = s["comparison"]
        if not isinstance(c, dict):
            lines.append(f"- `{s['file']}`: {c}"); continue
        lines.append(f"- `{s['file']}` superseded by {', '.join(s['replaced_by'])}: {s['old_chunks']} chunks; identical {c['identical']}, marker format only "
                     f"{c['marker_format_only']}, additions only {c['additions_only']}, wording changed {len(c['wording_changed'])}, missing {len(c['missing_in_replacement'])}; "
                     f"{len(s['new_only_chunks'])} chunks are new in the replacement. Revised chunks are the author's own updates; both texts are in dataset_inventory.json")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    sys.exit(main())
