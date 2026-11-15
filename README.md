# Flame in Freefall (NASA Space Apps 2026)

NASA's microgravity fire experiments explained for everyone, with every number traced to its NASA source.
This folder holds the website, the team's analysis kit, the RAG corpora and the documents behind them.

## What is where

| Folder | What it is | Edit by hand? |
| --- | --- | --- |
| `fif-dashboard/` | **The website** (static, offline). Entry point `index.html`. See its `README.md` | yes (except `data/site-data.js`, `data/files/`) |
| `flame-in-freefall-kit/` | The track kit: each member's analysis package in `analysis/T1..T6/`, NASA metadata and tables in `data/`, kit tools | packages come from members |
| `flame-in-freefall/` | The original team pipeline (schemas, investigation cards, ranking, catalog) and its tests | yes |
| `RAG/` | All submitted RAG corpora and `rag-map.json` (which bot reads which dataset). See `RAG/README.md` | corpora come from members |
| `tools/export_rag_corpora.py` | Builds the dataset inventory and the per-dataset RAG export | yes |
| `docs/` | Challenge brief, status report, assignment sheets, **dataset inventory**, reorganization log, `reviews/` (e.g. the T1 v8 review) | inventory is generated |
| `Findings/` | The T2/T4/T6 findings as received from Mohamed Shreif, Mohammed Tamer and Mohamed Gamal (integrated in v10; see `docs/reports/FINDINGS_INTEGRATION_v10.md`) | no |
| `crew-illustrations/` | The six crew illustrations; `fif-dashboard/tools/crew_astronauts.py` measures proportions from them. Not shipped with the site (faces are never shown) | no |
| `contributions/` | Submissions kept as received when their content is not fully unpacked elsewhere (BASS v8 project, Khaled Adawi's T5 delivery) | no |
| `deliverables/` | Generated: website ZIP, RAG corpus ZIP, clean project ZIP | no (rebuild) |
| `archive/` | Superseded versions and files kept for reference only. See `archive/ARCHIVE.md` | no |

The website reads only `fif-dashboard/`. Its data file is generated from the kit:
`flame-in-freefall-kit/analysis/*` + `data/psi_metadata/*.json` -> `fif-dashboard/build_site_data.py` -> `fif-dashboard/data/site-data.js`.

## Run the website

Double-click `fif-dashboard/index.html` (Chrome, Edge, Firefox or Safari). The crew appear as helmeted astronauts, each in
their own suit colour (faces covered), each world's owner offers a guided tour, and Bondoq the cat lives on the ledge at the
bottom. Three icons in the top bar: view mode, the cat menu and settings (sound, motion, crew reactions, rocket cursor).
Everything is local. For the in-site PDF
viewer, serve the folder instead: `cd fif-dashboard && python -m http.server 8765`, then open http://localhost:8765.

## After a member sends a package or a corpus

1. Analysis package (`T<n>_<name>_v<k>.zip` or a project ZIP with `output/analysis/T<n>/`): unpack it so that
   `flame-in-freefall-kit/analysis/T<n>/PSI-*/findings.md` exists (archive the replaced files), then
   `cd flame-in-freefall-kit && python tools/self_check.py T<n>` (the team validator).
2. Rebuild the site data: `cd fif-dashboard && python build_site_data.py --kit ../flame-in-freefall-kit`.
   After step 4 also `cd fif-dashboard && python build_rag.py` (crew chat texts).
3. RAG corpus: put it under `RAG/`, add it to `TEXT_SOURCES` or `JSONL_SOURCES` in `tools/export_rag_corpora.py`
   with a mapping rule (the existing rules are examples), and update `RAG/rag-map.json` if a bot should read it.
4. Refresh the inventory, the RAG export and the website's crew RAG folders (`fif-dashboard/rag/`, `content/rag-map.json`):
   `python tools/export_rag_corpora.py` (from this folder).
   It stops with a message if a file it treats as a copy has started to differ, and validates its own output.
5. Package: see "Deliverables" below.

## Checks

```bash
cd fif-dashboard && for t in tests/*.test.cjs; do node "$t"; done     # needs Node 18+
cd fif-dashboard && npm i -D playwright && npx playwright install chromium && node tests/browser.e2e.cjs
cd flame-in-freefall-kit && python -m pytest -q
cd flame-in-freefall && python -m pytest -q
```

## Deliverables

`deliverables/fif-dashboard-v10.zip` (the website folder), `deliverables/rag-corpora.zip` (written by the export tool)
and `deliverables/flame-in-freefall-project.zip` (this folder without `archive/`, `deliverables/` and the kit's
`data/raw/`, which holds NASA downloads that `flame-in-freefall-kit/scripts/psi_fetch.py` re-creates and that the
kit's `.gitignore` already excludes).

## Current coverage (from `docs/DATASET_INVENTORY.md`)

23 NASA PSI datasets: 19 assigned to six tracks, 4 unassigned ground studies. Findings on the site (111): T1 (12), T2 (13, SAFFIRE I-III), T3 (23), T4 (23, PSI-69 FLEX), T5 (19: Flame Design, BRE, E-FIELD, s-Flame), T6 (21: SLICE, SPICE, ACME CLD).
RAG corpora exist for 18 datasets: T1, T2 (SAFFIRE), T3, T4 (FLEX, FLEX-2 incl. Tamer's rag_corpus_flex2 in `fif-dashboard/rag/PSI-68_FLEX_II/`, CFI, CFI-G), T5 (BRE, E-FIELD, s-Flame, Flame Design)
and part of T6 (SPICE, SLICE). None yet for ACME CLD (PSI-21) or the four unassigned studies. Conflicts are in the inventory.
