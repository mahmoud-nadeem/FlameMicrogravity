#!/usr/bin/env python3
"""Build data/rag-data.js from the rag/ folder.

    rag/
      PSI-26_BASS/      corpus.txt, notes.md, ...   <- one folder per dataset (the folder name IS the topic)
      PSI-22_ACME-E-FIELD/ ...

    python build_rag.py --init     # once: create the empty folders listed in content/rag-map.json
    python build_rag.py            # then refresh the page

The team's corpora are written into rag/ by tools/export_rag_corpora.py (project root), together with
content/rag-map.json, which says which character reads which folder:
    {"nadeem": ["PSI-102_SAME", ...], "tamer": [...], "guide": ["*"]}
"*" means every folder.

Two kinds of files are read (.md or .txt):
  * team corpus files (corpus.txt from the export): every chunk is preceded by a '>>> source: ... | chunk: ID ...' line.
    Each chunk stays whole and keeps its chunk ID, source file, title, evidence label and the datasets it is shared with.
  * any other notes: markdown headings (# ... ####) become the chunk title and long sections are split into
    ~120-word chunks (write each fact under a clear heading).
Chunks are marked kind "record" (one data row or test), "policy" (the author's rules for using the corpus, shown on
the record page but never used as an answer) or "text". Everything is written into ONE JS file because browsers
block fetch() on file://; the page loads it in the background (assets/js/rag.js).
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTS = {".md", ".txt"}
PROV = re.compile(r"^>>> source: (?P<source>.+?) \| chunk: (?P<id>.+?) \| location: (?P<loc>.+?) \| mapping: (?P<rest>.*)$")
RECORD_ID = re.compile(r"(-RUN-\d|-TEST-|^T3-DAFT-\d|^spice-(flame|day)-|^slice-(bc|testday)-|^SAFFIRE-\d+-S\d+(-SENSORS)?$)", re.I)
POLICY_TITLE = re.compile(r"\b(how to (use|read)( and index)? this (file|corpus)|usage and scope|corpus guide)\b", re.I)


def split_sections(text: str) -> list[tuple[str, str]]:
    sections, title, buf = [], "", []
    for line in text.splitlines():
        m = re.match(r"^#{1,4}\s+(.*\S)\s*$", line)
        if m:
            if "".join(buf).strip():
                sections.append((title, "\n".join(buf)))
            title, buf = m.group(1), []
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((title, "\n".join(buf)))
    return sections


def pieces(paragraph: str, max_words: int) -> list[str]:
    """Split one very long paragraph on sentence ends."""
    if len(paragraph.split()) <= max_words:
        return [paragraph]
    out, cur, n = [], [], 0
    for s in re.split(r"(?<=[.!?])\s+", paragraph):
        w = len(s.split())
        if cur and n + w > max_words:
            out.append(" ".join(cur))
            cur, n = [], 0
        cur.append(s)
        n += w
    if cur:
        out.append(" ".join(cur))
    return out


def chunk(body: str, max_words: int, overlap_words: int) -> list[str]:
    paras = []
    for p in re.split(r"\n\s*\n", body):
        p = p.strip()
        if p:
            paras += pieces(p, max_words)
    chunks, cur, n = [], [], 0
    for p in paras:
        w = len(p.split())
        if cur and n + w > max_words:
            chunks.append("\n\n".join(cur))
            last = cur[-1]
            cur = [last] if len(last.split()) <= overlap_words else []
            n = sum(len(x.split()) for x in cur)
        cur.append(p)
        n += w
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def field(text: str, name: str) -> str:
    m = re.search(rf"^{name}:\s*(.+)$", text, re.M)
    return m.group(1).strip() if m else ""


def corpus_chunks(text: str, topic: str) -> list[dict]:
    """Chunks of a team corpus file (export format: '>>> source: ...' line, then the chunk text verbatim)."""
    out, cur = [], None
    for line in text.splitlines():
        m = PROV.match(line)
        if m:
            cur = {"meta": m.groupdict(), "lines": []}
            out.append(cur)
        elif line.startswith("##### SOURCE FILE:"):
            cur = None                                   # a file header block follows: not a chunk
        elif cur is not None:
            cur["lines"].append(line)
    items = []
    for c in out:
        body = "\n".join(c["lines"]).strip()
        meta, rest = c["meta"], c["meta"]["rest"]
        mapping = rest.split(" | ")[0]
        shared = re.findall(r"PSI-\d+", rest.split("SHARED with:", 1)[1].split(" | identical")[0]) if "SHARED with:" in rest else []
        first = body.splitlines()[0] if body else ""
        # title and evidence label from whichever chunk format the author used
        title = (field(body, "TITLE") or field(body, "TOPIC") or field(body, "Topic") or
                 re.sub(r"^#*\s*(\[CHUNK [^\]]+\]|===|CHUNK \d+/\d+ \| ID: \S+)\s*", "", first).split(" | ")[0].strip(" =") or meta["id"])
        if re.match(r"^=== .+ ===$", first):
            title = first.strip("= ").split(" | ", 1)[-1].strip()
        evidence = field(body, "EVIDENCE_LEVEL") or field(body, "EVIDENCE_STATUS")
        if "\nCONTENT:" in body:                         # JSONL and ACME formats: metadata fields, then CONTENT
            content = body.split("\nCONTENT:", 1)[1].strip()
        else:                                            # other formats: drop the header line (its title is kept above)
            content = "\n".join(body.splitlines()[1:]).strip() if re.match(r"^(#+ |\[CHUNK |=== )", first) else body
        kind_field = field(body, "RECORD_KIND") or field(body, "CATEGORY")
        # "policy": instructions about the corpus file itself (kept for the record page, never an answer);
        # "guidance": the author's scientific cautions (rag_policy / rag_guidance), answerable and shown as usage rules
        kind = ("policy" if kind_field == "corpus_guide" or POLICY_TITLE.search(title) else
                "guidance" if kind_field in ("rag_policy", "rag_guidance") else
                "record" if kind_field == "experimental_record" or RECORD_ID.search(meta["id"]) else "text")
        items.append({"id": meta["id"], "source": meta["source"], "title": title[:160], "text": content, "psi": topic.split("_")[0],
                      "evidence": evidence, "kind": kind, "shared": shared, "location": meta["loc"], "mapping": mapping,
                      "url": (field(body, "SOURCE_URLS").split(" | ")[0] if field(body, "SOURCE_URLS") else "")})
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rag", type=Path, default=HERE / "rag")
    ap.add_argument("--max-words", type=int, default=120)
    ap.add_argument("--overlap-words", type=int, default=30)
    ap.add_argument("--init", action="store_true", help="create an empty rag/<TOPIC>/ folder for every topic in content/rag-map.json")
    args = ap.parse_args()

    if args.init:
        mp0 = HERE / "content" / "rag-map.json"
        for lst in json.loads(mp0.read_text(encoding="utf-8-sig")).values():
            for t in lst:
                if t != "*":
                    (args.rag / t).mkdir(parents=True, exist_ok=True)
        print("created folders under", args.rag)

    topics: dict[str, list[dict]] = {}
    if not args.rag.is_dir():
        print(f"no folder {args.rag} - create rag/<TOPIC>/ with .md or .txt files")
    else:
        for folder in sorted(p for p in args.rag.iterdir() if p.is_dir()):
            items = []
            # a corpus file kept beside corpus.txt (e.g. PSI-68_FLEX_II/rag_corpus_flex2.txt) whose chunks the export already put
            # into corpus.txt, quoted with '>>> source: <path>', is read once: from corpus.txt
            cp = folder / "corpus.txt"
            quoted = set(re.findall(r"(?m)^>>> source: (.+?) \|", cp.read_text(encoding="utf-8-sig", errors="replace"))) if cp.is_file() else set()
            for f in sorted(folder.rglob("*")):
                if f.suffix.lower() not in EXTS or not f.is_file():
                    continue
                if f.name != "corpus.txt" and any(q.endswith(f"{folder.name}/{f.relative_to(folder).as_posix()}") for q in quoted):
                    print(f"  {folder.name}/{f.name}: chunks read from corpus.txt (the export quotes this file)")
                    continue
                text = f.read_text(encoding="utf-8-sig", errors="replace")
                rel = f.relative_to(folder).as_posix()
                if PROV.search(text) or re.search(r"(?m)^>>> source: ", text):
                    items += corpus_chunks(text, folder.name)
                    continue
                n = 0
                for title, body in split_sections(text):
                    for c in chunk(body, args.max_words, args.overlap_words):
                        n += 1
                        items.append({"id": f"{folder.name}/{rel}#{n}", "source": rel, "title": title or f.stem.replace("_", " "),
                                      "text": c, "psi": folder.name.split("_")[0] if folder.name.upper().startswith("PSI-") else "",
                                      "evidence": "", "kind": "text", "shared": []})
            topics[folder.name] = items
            kinds = {k: sum(1 for i in items if i["kind"] == k) for k in ("text", "guidance", "record", "policy")}
            print(f"{folder.name}: {len(items)} chunks ({kinds['text']} text, {kinds['guidance']} cautions, {kinds['record']} data records, "
                  f"{kinds['policy']} file instructions)")

    rag_map = {}
    mp = HERE / "content" / "rag-map.json"
    if mp.exists():
        rag_map = json.loads(mp.read_text(encoding="utf-8-sig"))
    known = {t.lower() for t in topics}
    for cid, lst in rag_map.items():
        for t in lst:
            if t != "*" and t.lower() not in known:
                print(f"  note: {cid} is assigned '{t}' but rag/{t}/ does not exist (no corpus submitted yet)")

    data = {"built": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "map": rag_map, "topics": topics}
    out = HERE / "data" / "rag-data.js"
    out.parent.mkdir(exist_ok=True)
    out.write_text("/* generated by build_rag.py - do not edit */\nwindow.FIF_RAG_DATA = "
                   + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(f"wrote {out.relative_to(HERE)} ({out.stat().st_size / 1024:.0f} KB): "
          f"{len(topics)} topics, {sum(len(v) for v in topics.values())} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
