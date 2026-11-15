# Review: T1 (Amr Morgan), BASS / BASS-II v8

Reviewed 15 November 2026 from `contributions/BASS_Python_AmrProject_v8.zip` (integrated in `flame-in-freefall-kit/analysis/T1/`).

## Verdict

The analysis is sound and reproducible. Every number in the 12 findings was recomputed from the raw NASA files with
independent code and agrees; the pipeline regenerates all 97 output files with the same content. The open points below
are documentation and schema issues, plus the source gaps Amr already lists himself.

## What was checked

| Check | Result |
| --- | --- |
| Re-run `main.py` from scratch (output folder deleted) and compare with the shipped outputs | 97/97 files regenerated; content identical (differences only in Windows line endings, PNG bytes from the Matplotlib version, and `\` vs `/` in one self-check path) |
| Independent re-computation from `data/` (own code, not his pipeline): run counts, distinct materials, O2 ranges, air-display categories, O2 pairs, the 5 NASA-flagged exclusions, medians, CO counts | 20/20 agree with F-T1-2501..2513 and F-T1-2601..2610 |
| PSI-26 non-run rows | rows 69 ("SOOT Cleaning") and 85-88 ("STOW", "SETUP", "Dilution test") are correctly left out: 121 runs |
| Analysis-ready table | 250 records, 250 unique run IDs, every selected date's day-of-year equals its GMT day, the 5 flagged final O2 values are blank |
| Team validator `tools/self_check.py T1` | 8 PASS, 1 FAIL (item 1, below), 1 MANUAL (re-run: done above) |
| v6 to v8 corpora | every v6 chunk ID is still present; 266 chunks revised (date verification, verified units, context materials); 7 new chunks |

## To fix (for Amr)

1. **Team schema (validator item 1 FAIL).** `PSI-25_bass-ii_runs_clean.csv` and `PSI-26_bass_runs_clean.csv` gained four columns
   without the `x_` prefix: `date`, `date_verification`, `date_session_reference`, `date_usable_for_chronology`. The v6 README
   itself says date columns use `x_`. Rename them (e.g. `x_date_selected`) or move them to `dashboard_runs_analysis_ready.csv` only.
2. **`HANDOFF.md` contradicts v8.** Its first paragraph (v1) still says the PSI-26 oxygen fraction conversion "needs reviewer
   confirmation" and "PSI-26 airflow not populated"; `SCIENTIFIC_SOURCE_AUDIT.txt` now documents both (workbook AA3/AA46 and 67
   formulas; K3 air display in cm/s, NTRS 20140011099). Update or mark the v1 paragraph as superseded.
3. **README.** Title still "Morgan T1 V6"; the "V8 source verification" line appears twice.
4. **Windows.** `python main.py` stops in `bass_audit_v2.py` with a `UnicodeDecodeError` unless Python runs in UTF-8 mode
   (`set PYTHONUTF8=1`). Add `encoding="utf-8"` to the file reads, or note it in the README.
5. **`verify_v8.py` is a pipeline step, not a verifier.** It reads `Amr_BASS_Deep_Analysis_v7_clean.txt` (made by `finalize_v7.py`)
   and fails on the shipped output, where only the v8 file exists. Rename it or document that it must run inside `main.py`.

## Still open (Amr's own list, unchanged)

- Nine run dates lack exact-run evidence: PSI-26 as-run 93, 111, 112-116; PSI-25 T9, T18 (original video/log overlays needed).
- PSI-26 live PSI registry fields (DOI, licence, project dates) are from the supplied snapshot, not re-verified.
- No outcome coding, safety threshold, hazard ranking or model is claimed; retrieval questions are fixtures, not measured performance.
