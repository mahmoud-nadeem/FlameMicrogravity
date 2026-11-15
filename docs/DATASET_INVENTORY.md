# Dataset inventory

Generated 2026-11-15 21:05 UTC by `tools/export_rag_corpora.py` from: `flame-in-freefall-kit/data/psi_metadata/*.json`, `flame-in-freefall/site_data/investigations.json`, `fif-dashboard/data/site-data.js (records)`, `docs/psi_member_assignments_verified.csv`, `RAG/rag-map.json`, `flame-in-freefall-kit/analysis/T*/PSI-*/card.json`.
Datasets are matched on PSI ID. Full detail (aliases with evidence, sources per dataset, conflicts) is in `dataset_inventory.json`.

| PSI ID | NASA name | Track | Crew | Kit package | Dashboard | RAG corpus | Conflicts |
| --- | --- | --- | --- | --- | --- | --- | --- |
| PSI-10 | ACME/Flame Design | T5 | Khaled Adawi | 5 findings, 1 charts | shown, 5 findings | exported (68 chunks) | 1 |
| PSI-20 | ACME BRE | T5 | Khaled Adawi | 5 findings, 13 charts | shown, 5 findings | exported (71 chunks) |  |
| PSI-21 | ACME CLD Flame | T6 | Mohamed Gamal | 6 findings, 0 charts | shown, 6 findings | missing (0 chunks) |  |
| PSI-22 | ACME E-FIELD Flames | T5 | Khaled Adawi | 5 findings, 1 charts | shown, 5 findings | exported (68 chunks) |  |
| PSI-23 | ACME s-Flame | T5 | Khaled Adawi | 4 findings, 1 charts | shown, 4 findings | exported (68 chunks) |  |
| PSI-25 | BASS-II | T1 | Amr Morgan | 8 findings, 5 charts | shown, 8 findings | exported (164 chunks) | 1 |
| PSI-26 | BASS | T1 | Amr Morgan | 4 findings, 4 charts | shown, 4 findings | exported (151 chunks) | 1 |
| PSI-39 | CFI | T4 | Mohammed Tamer | template only | shown, 0 findings | exported (277 chunks) |  |
| PSI-47 | DAFT / DAFT-2 | T3 | Mahmoud Nadeem | 7 findings, 1 charts | shown, 7 findings | exported (28 chunks) | 1 |
| PSI-62 | Concurrent Flame Spread Modeling using Flamelet  | - | unassigned | - | not shown | missing (0 chunks) |  |
| PSI-68 | FLEX-2 | T4 | Mohammed Tamer | template only | shown, 0 findings | exported (626 chunks) |  |
| PSI-69 | FLEX | T4 | Mohammed Tamer | 23 findings, 0 charts | shown, 23 findings | exported (461 chunks) |  |
| PSI-98 | SAFFIRE-I | T2 | Mohamed Shreif | 2 findings, 0 charts | shown, 2 findings | exported (16 chunks) |  |
| PSI-99 | SAFFIRE-II | T2 | Mohamed Shreif | 9 findings, 0 charts | shown, 9 findings | exported (30 chunks) |  |
| PSI-100 | SAFFIRE-III | T2 | Mohamed Shreif | 2 findings, 0 charts | shown, 2 findings | exported (15 chunks) |  |
| PSI-101 | SAME-R | T3 | Mahmoud Nadeem | 13 findings, 5 charts | shown, 13 findings | exported (148 chunks) | 1 |
| PSI-102 | SAME | T3 | Mahmoud Nadeem | 3 findings, 0 charts | shown, 3 findings | exported (71 chunks) | 1 |
| PSI-106 | SLICE | T6 | Mohamed Gamal | 7 findings, 0 charts | shown, 7 findings | exported (51 chunks) |  |
| PSI-107 | SPICE | T6 | Mohamed Gamal | 8 findings, 0 charts | shown, 8 findings | exported (169 chunks) |  |
| PSI-115 | Utilization of the Smoke Aerosol Measurement Exp | - | unassigned | - | not shown | missing (0 chunks) |  |
| PSI-117 | Effect of External Thermo-Convective Perturbatio | - | unassigned | - | not shown | missing (0 chunks) |  |
| PSI-142 | Quantitative Studies of Cool Flame Transitions a | - | unassigned | - | not shown | missing (0 chunks) |  |
| PSI-159 | ACME CFI-G | T4 | Mohammed Tamer | template only | shown, 0 findings | exported (1300 chunks) |  |

## Conflicts and open points

- **PSI-10** card_vs_nasa_metadata: `license` card `unconfirmed` vs NASA `` (card holds a verification placeholder)
- **PSI-25** card_vs_nasa_metadata: `license` card `CC0-1.0` vs NASA `Creative Commons Zero v1.0 Universal` (same licence, different notation)
- **PSI-26** card_vs_nasa_metadata: `license` card `CC0-1.0` vs NASA `Creative Commons Zero v1.0 Universal` (same licence, different notation)
- **PSI-47** card_vs_nasa_metadata: `license` card `CC0-1.0` vs NASA `Creative Commons Zero v1.0 Universal` (same licence, different notation)
- **PSI-101** card_vs_nasa_metadata: `license` card `CC0-1.0` vs NASA `Creative Commons Zero v1.0 Universal` (same licence, different notation)
- **PSI-102** card_vs_nasa_metadata: `license` card `CC0-1.0` vs NASA `Creative Commons Zero v1.0 Universal` (same licence, different notation)
- chunk `PSI10-07` author_flagged_third_party_unverified: Secondary research dashboards describe separate Flame Design normal and inverse CSV tables, reportedly containing 207 and 120 experimental-test rows respectively. These numbers were not independently checked against NASA downloads in this build; they are catalog hints, not validated NASA counts.  Kit NASA table: PSI-10: PSI-10_Experimental table_Flame Design_Inverse Flame.csv has 120 data rows, PSI-10_Experimental table_Flame Design_Normal Flame.csv has 207 data rows.
- chunk `PSI20-09` author_flagged_third_party_conflict: One secondary catalog describes 18 BRE experimental-table test-day rows, while another describes 43 assembled test rows. These are different representations or processing snapshots; neither number is certified as the current NASA PSI raw table count here.  Kit NASA table: PSI-20: PSI-20_Experimental table_ACME BRE.csv has 18 data rows.
- chunk `QA-020` author_flagged_third_party_conflict: Question: How many BRE table rows are there?
Answer: This package has no independently validated primary BRE CSV. Secondary reports use 18 or 43 with differing representation; retrieve the specific NASA file version before using a count.  Kit NASA table: PSI-20: PSI-20_Experimental table_ACME BRE.csv has 18 data rows.
- chunk `PSI22-08` author_flagged_third_party_conflict: Secondary compilers disagree on whether the PSI-22 published tabular representation contains 21 or 32 records. Until the actual file and version are available, classify each reported count by source, extraction date and observation unit.  Kit NASA table: PSI-22: PSI-22_Experimental table_ACME E-FIELD Flames.csv has 32 data rows.
- chunk `PSI23-09` author_flagged_third_party_conflict: A third-party methodology describes 18 s-Flame test-day CSV rows; another summary describes 23 test rows. Neither row count is independently established as NASA’s current authoritative release in this package.  Kit NASA table: PSI-23: PSI-23_Experimental table_ACME s-Flame.csv has 18 data rows.
- chunk `ACME-03` author_flagged_documented_source_difference: NASA Science describes ACME as a group of five independent experiments, while a 2022 NASA technical paper lists six, including the later Cool Flames Investigation with Gases (CFI-G). The four PSI accessions covered here are a subset of the broader program. Do not silently collapse or reconcile differing scope definitions.  Kit NASA table: PSI-10: PSI-10_Experimental table_Flame Design_Inverse Flame.csv has 120 data rows, PSI-10_Experimental table_Flame Design_Normal Flame.csv has 207 data rows; PSI-20: PSI-20_Experimental table_ACME BRE.csv has 18 data rows; PSI-22: PSI-22_Experimental table_ACME E-FIELD Flames.csv has 32 data rows; PSI-23: PSI-23_Experimental table_ACME s-Flame.csv has 18 data rows.
- chunk `QA-019` author_flagged_documented_source_difference: Question: How many ACME investigations are there?
Answer: Different NASA pages describe five or six depending on inclusion of CFI-G. This package covers four specified PSI accessions.  Kit NASA table: PSI-10: PSI-10_Experimental table_Flame Design_Inverse Flame.csv has 120 data rows, PSI-10_Experimental table_Flame Design_Normal Flame.csv has 207 data rows; PSI-20: PSI-20_Experimental table_ACME BRE.csv has 18 data rows; PSI-22: PSI-22_Experimental table_ACME E-FIELD Flames.csv has 32 data rows; PSI-23: PSI-23_Experimental table_ACME s-Flame.csv has 18 data rows.
- **PSI-10** DOI `10.60555/w4zy-bt45` stated in 15 corpus chunks (label `secondary_reported_pending_direct_resolution`): matches NASA's PSI API metadata (kit psi_metadata); the corpus label is left as written
- **PSI-20** DOI `10.60555/vb93-3y72` stated in 18 corpus chunks (label `secondary_reported_pending_direct_resolution`): matches NASA's PSI API metadata (kit psi_metadata); the corpus label is left as written
- **PSI-22** DOI `10.60555/se5a-8c73` stated in 15 corpus chunks (label `secondary_reported_pending_direct_resolution`): matches NASA's PSI API metadata (kit psi_metadata); the corpus label is left as written
- **PSI-23** DOI `10.60555/k57n-p030` stated in 15 corpus chunks (label `secondary_reported_pending_direct_resolution`): matches NASA's PSI API metadata (kit psi_metadata); the corpus label is left as written
- `extra/saffire_threshold_sensitivity.csv` is cited by RAG/SAFFIRE_RAG_Corpora/PSI-98/rag_corpus_psi98.txt but is not in the project
- `extra/run_crosswalk.csv` is cited by RAG/SAFFIRE_RAG_Corpora/PSI-98/rag_corpus_psi98.txt but is not in the project
- `extra/normalization_audit.csv` is cited by RAG/SAFFIRE_RAG_Corpora/PSI-98/rag_corpus_psi98.txt but is not in the project
- `extra/coverage.csv` is cited by RAG/SAFFIRE_RAG_Corpora/PSI-98/rag_corpus_psi98.txt but is not in the project
- `archive/superseded/RAG/Amr.txt` superseded by RAG/Morgan_RAG_Corpus_v8/PSI-26_BASS/rag_corpus.txt, RAG/Morgan_RAG_Corpus_v8/PSI-25_BASS-II/rag_corpus.txt: 283 chunks; identical 0, marker format only 27, additions only 0, wording changed 256, missing 0; 22 chunks are new in the replacement. Revised chunks are the author's own updates; both texts are in dataset_inventory.json
- `archive/superseded/RAG/Morgan_RAG_Corpus_v6/PSI-26/rag_corpus.txt` superseded by RAG/Morgan_RAG_Corpus_v8/PSI-26_BASS/rag_corpus.txt: 147 chunks; identical 19, marker format only 0, additions only 0, wording changed 128, missing 0; 4 chunks are new in the replacement. Revised chunks are the author's own updates; both texts are in dataset_inventory.json
- `archive/superseded/RAG/Morgan_RAG_Corpus_v6/PSI-25/rag_corpus.txt` superseded by RAG/Morgan_RAG_Corpus_v8/PSI-25_BASS-II/rag_corpus.txt: 161 chunks; identical 23, marker format only 0, additions only 0, wording changed 138, missing 0; 3 chunks are new in the replacement. Revised chunks are the author's own updates; both texts are in dataset_inventory.json
