# T5 final handoff — ACME gaseous flames

**Owner:** Khaled Adwi. **Handoff:** 2026-11-15. **Status:** READY FOR INTEGRATION WITH DISCLOSED LIMITS.

## Coverage

| PSI | What is actually analyzed | Supported source counts | Evidence status |
|---|---|---|---|
| PSI-10 Flame Design | Normal/inverse test-table EDA + verified standardized rows | 207 Normal + 120 Inverse = 327 entries | Source observations HIGH; not flame success labels |
| PSI-20 BRE | Final source audit + four visual charts; local run 19056A2 | 18 summary days; 194 table ignitions; 31,316 raw samples in one run | Source observations HIGH; outcome interpretation limited |
| PSI-22 E-FIELD | Day-level descriptive analysis, chart and provenance | 32 physical rows; 21 count-bearing rows, 20 unique Test Days; source sum 230 includes repeat | Source count HIGH; uniqueness of total UNRESOLVED |
| PSI-23 s-Flame | Day-level descriptive analysis and chart | 18 day-level rows; source sum 276 | Source observations HIGH; no extinction labels |

**Deliverables:** source-linked high/medium/low confidence `findings.md` for four studies; `card.json` with partial-verification disclosures; `profile.md`; `data_log.md`; `references.md` with DOI text; `rag_chunks.jsonl`; 7 PNG charts (4 BRE previously approved, 1 for each other study); PSI-10 clean table (only source_file path prefixed for team-kit compatibility) and PSI-22/23 traceable day-level extracts.

**No model attempted:** no per-run outcomes for PSI-10 and no calibrated run-level outcomes for PSI-22/23; BRE has one available local paired run, insufficient for generalizable model. This is descriptive work only.

## Critical caveats for site cards / presentation

1. **E-FIELD repeat:** Test Day 18319, 11 flames, repeated on source CSV rows 26 and 30 (with continuation rows). Arithmetic sum of 21 count-bearing entries = 230, **NOT an independently verified unique-day ignition total**. Do not use 230 as definitive without NASA clarification.
2. **BRE total:** 194 day-table ignitions vs 196 successful ignitions in NASA report pp.29/127; comparison remains unresolved. Report pp.110/116 also state 194. Avoid forcing equivalence.
3. **BRE source mismatch:** original summary table oxygen values 3400% and 2100% vs report 34%, 21%; two date entries also differ (see `PSI-20_bre/tables/cross_source_discrepancies.csv`). Test Day 19094 older April 5 vs corrected April 4 is explained (NASA PDF p.23).
4. **PSI-10:** 327 table entries are not 327 successful ignitions. Normal and inverse oxygen columns have different semantics. Inverse table has no Fuel column.
5. **s-Flame:** N3/N4/N5/N6 source labels are retained unaltered; unverified whether typos.
6. **Cards:** ID/title/DOI were cross-checked with the starter kit's NASA API metadata, and objectives against independent official NASA Science pages. **Live PSI version/file counts/size and verbatim 'Cite this Investigation' were NOT fully checked** (interactive page unavailable). `verified_on`/`verified_by` remain blank deliberately; fields under `x_review_status` explain partial review.
7. **RAG:** `rag_chunks.jsonl` is a tiny optional source-linked seed. It is **not** proof of retrieval evaluation or compatibility with the app's vector store/schema. All science claims remain sourced.
8. **Site:** no human manual browser click-through or live dashboard integration was performed by this handoff. A team member must check cards, links and chart readability in the deployed UI.

## Integration steps (one pass)

1. Merge `analysis/T5/` into the canonical `flame-in-freefall-kit/analysis/T5/` folder; copy the four accompanying `data/experimental_tables/PSI-*/` directories if missing.
2. Incorporate four `card.json` records plus each `findings.md` (do not make a global risk score). Use 7 chart PNGs. Import RAG chunks only if the app already accepts this JSONL schema.
3. Use `analysis/T5/references.md` in the submission References; keep NASA DOI links and AI usage disclosure. Preserve source discrepancy warnings in cards.
4. Test the four study cards and DOI/charts in a real browser before submission. This cannot be certified from the files alone.

**Does not include:** Gamal's PSI-21/60 or unassigned PSI-62/115/117/142 corpora; Shreif's SAFFIRE T2 tables/findings; T4 FLEX/CFI; T6 SPICE/SLICE; Amr's provisional-unit/date decisions. Those are other owners' work, not quietly claimed as fixed.

**Validation:** See `SELF_CHECK.md` and `VERIFY_RESULTS.md`. The kit's manual full-page check is explicitly incomplete because direct live PSI detail pages could not be inspected in full.
