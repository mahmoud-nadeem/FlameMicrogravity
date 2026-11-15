# RAG corpora

Every corpus the team has submitted, as received. `tools/export_rag_corpora.py` reads them, maps each chunk to its
dataset (PSI ID) and writes `deliverables/rag-corpora.zip` plus `docs/dataset_inventory.json`.

| File or folder | Track, contributor | Datasets | Format | Status |
| --- | --- | --- | --- | --- |
| `Morgan_RAG_Corpus_v8/PSI-26_BASS/`, `PSI-25_BASS-II/` (`rag_corpus.txt`) | T1, Amr Morgan | PSI-26 BASS, PSI-25 BASS-II | `[CHUNK id] title` | current (v8). The author: use these two files, not the combined v8 TXT alongside them |
| `SAFFIRE_RAG_Corpora/PSI-98, PSI-99, PSI-100/` | T2 (Mohamed Shreif by assignment; the files name no author) | PSI-98, 99, 100 | `=== id \| title ===` + `Investigation:` line | current. Cites four `extra/*.csv` tables that were not submitted |
| `Mahmoud.txt` | T3, Mahmoud Nadeem | PSI-102, 101, 47 | `### [CHUNK id] title \| source \| tags` | current; written by `flame-in-freefall-kit/analysis/T3/extra/build_rag_pack.py` (keep this path) |
| `Tamer.txt` | T4, Mohammed Tamer | PSI-69 FLEX (+ FLEX-2 chunks) | `### [CHUNK id] ...` | current |
| `CompleteTamerRAGChunks/` | T4, Mohammed Tamer | PSI-69, 68, 39, 159 | JSONL (+ schema, manifest, inventory; `_knowledge.txt` is a text rendering of the same chunks) | current |
| `NASA_ACME_RAG_Corpora_By_Dataset/` | T5, Khaled Adawi | PSI-10 Flame Design, PSI-20 BRE, PSI-22 E-FIELD, PSI-23 s-Flame (+ `ACME_Shared`, shared by the four) | `CHUNK n/N \| ID: x` blocks with `INVESTIGATION_ID`, `EVIDENCE_LEVEL`, `DOI_VERIFICATION` fields | current. Its source `rag_chunks.jsonl` was not submitted; the per-dataset TXT files hold every field |
| `../fif-dashboard/rag/PSI-68_FLEX_II/rag_corpus_flex2.txt` (kept in the website's folder, not here) | T4, Mohammed Tamer | PSI-68 FLEX-2 (470 chunks: the two FLEX-2 SRD PDFs page by page, 8 experiment-table rows, ISA-Tab metadata, investigation summary, glossary, cross-experiment notes) | `### slug` + `Investigation: ... (PSI-68)` + `Topic:` + `Sources:` | current (15 Nov 2026). Every chunk names PSI-68. The two SRD PDFs (with and without hypertext) are the same document, so most page chunks appear twice under different ids |
| `Gamal.txt` | T6, Mohamed Gamal | PSI-107 SPICE, PSI-106 SLICE | `### slug` + `Investigation:` line | current |
| `rag-map.json` | team | which bot may read which dataset (`"guide": ["*"]` = all) | JSON | current (see below) |
| `Flame in Freefall Backend and RAG Plan (FAISS).md` | Mahmoud Nadeem | - | design plan | not a corpus |

Superseded: the T1 v5 pack (`Amr.txt`) and the v6 corpora are in `archive/superseded/RAG/`. Every earlier chunk ID is still in
v8; the author's revisions (266 chunks from v6) are listed with both texts in `docs/dataset_inventory.json`.

The website reads these corpora through `tools/export_rag_corpora.py`, which also writes `fif-dashboard/rag/<PSI-ID>_<NAME>/`
(one folder per dataset) and `fif-dashboard/content/rag-map.json` from `rag-map.json` here.

`rag-map.json` follows the verified assignment sheet and the website (updated 15 Nov 2026: FLEX-II (= FLEX-2, PSI-68) for `tamer`,
ACME-E-FIELD and ACME-S-FLAME for `adwi`, ACME-CLD for `gamal`; PSI-60, the SPICE ground-analysis record, was removed from the
project on 15 Nov 2026 and is no longer mapped). On the website PSI-68's folder is `rag/PSI-68_FLEX_II/`.
