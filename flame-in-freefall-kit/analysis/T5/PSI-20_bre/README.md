# NASA PSI-20 BRE — T5 Task 02B final safety patch raw-data audit

This is an incremental safety patch to the existing Task 02 T5 audit. No modeling, extinction detection, physical calibration, or causal interpretation.

## Requirements and exact reproduction commands

Python 3.10+ with `numpy`, `pandas`, `matplotlib` installed.

```bash
python -m pip install numpy pandas matplotlib
cd /mnt/data
python analysis/T5/PSI-20_BRE/scripts/audit_pipeline.py \
  --data 19056A2_data.csv --mfc 19056A2_mfcSetpoints.csv \
  --out analysis/T5/PSI-20_BRE --run-id 19056A2 \
  --major-gap-seconds 1 --alignment-preview
python -m unittest discover -s analysis/T5/PSI-20_BRE/tests -v
```

`--run-id` is optional: the pipeline infers it from the `Test Point` metadata of BOTH files, rejects missing/mismatched IDs, conflicting or invalid experiment calendar dates, and unsafe output path characters. Output names are run-specific. No multi-run processing is performed.

## Parsing and quality

CSV record 1 is metadata, record 2 is header, subsequent records are measurements. UTF-8-SIG decoding with Latin-1 fallback; comma delimiter. Metadata fields preserved in order. Raw input files never modified. Invalid numeric strings, NaN tokens, missing values, and infinities are counted separately. MFC columns are control setpoints and are excluded from saturation screening; distributional saturation candidates on measured data are NOT confirmed physical saturation.

## Timing rules and limitations

Date is taken from first metadata field; Time uses HH:MM:SS:fraction as decimal seconds. Naive timestamps, no timezone, rollover correction, deduplication, or fixed acquisition rate. All positive interval frequencies and quantiles are retained. Negative jumps and zero intervals are separately classified. Positive deviations shorter than the operational gap threshold are normal interval variation, NOT necessarily uniform sampling. `--major-gap-seconds 1` flags positive intervals >=1 s; this is an operational screening threshold, **not** a NASA instrument specification. The threshold can be changed and may miss shorter acquisition interruptions or flag legitimate pauses.

Observed in data: 123.034 s gap 15:59:20.905–16:01:23.939; -0.003 s jump at data measurement row 12455; MFC change at 15:59:20.911 inside the gap. These are timestamp-label observations, not physical responses.

## Alignment safety

Optional `--alignment-preview` performs backward as-of lookup (no tolerance) by timestamp label; equal MFC timestamps resolve to last original-order record. All data source rows and their identifiers are retained, including invalid timestamp rows (unmatched). Both clocks' synchronization is **UNVERIFIED**. Matching MFC timestamps is NOT a measured MFC response. No interpolation, causal inference or flame-event detection. The preview distinguishes matched MFC **records** from actual setpoint-change **events**: `matched_record_change_event_id` is populated only when the matched original MFC row itself is in the change-event table; repeated rows have no event identity. The change-event table assigns stable run-specific IDs and labels the first row `initial_state`. `matched_mfc_age_seconds` gives lookup age; `stale_lookup_age_exceeds_threshold` flags ages > `--major-gap-seconds`, `lookup_crosses_major_data_gap` flags full-gap crossings, and `stale_timestamp_lookup` combines them. `matched_mfc_timestamp_within_major_data_gap` identifies MFC timestamps strictly inside data measurement gaps. These operational flags are NOT physical latency or synchronized response measurements. The structurally uninformative `data_inside_major_gap` column was removed. No missing measurements are interpolated.

## Outputs

`audit/<run>_metadata.json`, `_schema.json`, `_quality_report.csv`, `_timing_report.json`, `_mfc_events.csv`, `_audit_summary.md`, optionally `_alignment_preview.csv`; `charts/<run>_raw_*.png` (RAW SENSOR SIGNALS); `data_log.md`; `audit/file_inventory_sha256.txt` (generated automatically; self excluded). Files are deterministically serialized under identical dependencies and source files; PNG byte reproducibility may depend on Matplotlib/runtime versions.

## Scientific uncertainty

Sensor definitions and limits, physical units/calibration, clock synchronization/timezone, acquisition schedule, MFC controller semantics, gap cause and experiment outcomes require authoritative NASA documentation. Metadata alone is not independent verification. No flame extinction or causal conclusion is supported.

## Task 02B changelog

- Reject differing metadata experiment dates with an informative `ValueError`; preserve original metadata fields.
- Add `mfc_change_event_id` and `event_kind` to change-event table. Distinguish repeated MFC records from change events in the alignment preview.
- Rename ambiguous gap flags, report timestamp lookup age and operational stale-lookup flags; remove `data_inside_major_gap`.
- Add three regression tests (cross-date rejection, repeated-row/stale-gap identity, actual-event identity); 10 tests total.
- No changes to raw CSV inputs; no calibration, extinction labeling, modeling, or causal inference.

## Task 03 — local multi-run FILE INVENTORY ONLY

Inventory does not analyze multiple runs scientifically. It streams SHA-256 for recognized CSVs, reads only their metadata and header records, and never changes sources. It supports plain and `PSI-20_Raw Data_`-prefixed filenames, nested paths, and paths containing spaces.

```bash
python scripts/build_run_inventory.py --input-dir "/mnt/data/psi20_inputs" --out inventory
python -m unittest discover -s tests -v
```

Optional authoritative expected-run list must be explicitly supplied as a UTF-8 text file (one run ID per line) or JSON array / `{ "expected_runs": [...] }`:

```bash
python scripts/build_run_inventory.py --input-dir "/path/with spaces/PSI-20 CSV" --out inventory --expected-runs "/path/expected_runs.json" --strict
```

`--strict` writes all reports, then exits nonzero if pairing issues exist. The supplied manifest's path and SHA-256 are recorded; its NASA authority is **not** assumed. Keep `--out` outside `--input-dir` to avoid recursive self-discovery. Inventory products: `run_inventory.csv`, `file_inventory.csv`, `pairing_issues.csv`, `inventory_manifest.json`, `inventory_report.md`, and self-excluding `inventory_sha256.txt`.

Inventory pairing validates only first two records, filenames, Test Point and calendar dates. It does **not** validate full CSV measurement rows, synchronization, calibration, or completeness of NASA's run collection. Unrelated files are listed without hashing. Re-running with the same directory paths and identical inputs regenerates deterministic bytes; timestamps and execution time are deliberately excluded.

## Task 03B — run-ID naming compatibility

Inventory accepts **safe** filename-derived run IDs matching `[A-Za-z0-9]+(?:_[A-Za-z0-9]+)*`, including `19051K1_1`. The same validation is applied to optional expected-run manifests (JSON or plain text). Both short (`19051K1_1_data.csv`) and NASA-prefixed (`PSI-20_Raw Data_19051K1_1_data.csv`) forms remain supported, with `_mfcSetpoints.csv` partners. Exact run IDs, filenames, relative paths, and source hashes are preserved.

Run-like CSV filenames with malformed identifiers (for example `19051K1__1_data.csv`) are **not silently treated as unrelated**: they appear in `file_inventory.csv` with `invalid_filename_run_id` and in `pairing_issues.csv`; `--strict` fails. Arbitrary unrelated files remain separately listed. The filename rule is a conservative local safety rule, not a claim about all NASA naming conventions.

```bash
cd /mnt/data/analysis/T5/PSI-20_BRE
python scripts/build_run_inventory.py --input-dir "/mnt/data/psi20_inputs" --out inventory
python -m unittest discover -s tests -v
sha256sum /mnt/data/psi20_inputs/19056A2_data.csv /mnt/data/psi20_inputs/19056A2_mfcSetpoints.csv
sha256sum inventory/*
```

**Task 03B changelog:** generalized filename regex and expected-run validation consistently; reported malformed run-like CSVs as explicit issues; added 9 synthetic regression tests. All 6 existing `19056A2` inventory products remain byte-identical to the Task 03 approved ZIP. No scientific analysis, calibration, classification, modeling, or downloading was performed. The `19051K1_1` filenames and Test Point metadata have **not** been verified against NASA source files.

## Task 04 — Experimental table quality and day-level crosswalk

Requires the original user-provided `PSI-20_Experimental table_ACME BRE.csv` and the Task 03B `inventory/run_inventory.csv`. Do **not** interpret the table's day-level `Flames Ignited` as raw-run count. No automatic downloads or scientific modeling.

```bash
cd /mnt/data/analysis/T5/PSI-20_BRE
python scripts/audit_experimental_table.py \
  --table "/mnt/data/PSI-20_Experimental table_ACME BRE.csv" \
  --run-inventory inventory/run_inventory.csv \
  --out table_audit
python -m unittest discover -s tests -v
sha256sum "/mnt/data/PSI-20_Experimental table_ACME BRE.csv" /mnt/data/psi20_inputs/*.csv
sha256sum table_audit/*
```

Outputs: `table_audit/experimental_table_profile.md`, `table_quality_issues.csv`, `day_run_crosswalk.csv`, `coverage_summary.json`, `reconciliation_questions.md`, and `table_audit_sha256.txt` (self-excluded). Source CSV text is preserved. A calendar date equality between a locally validated run and a summary record is only a *candidate day link*, never proof of one-to-one correspondence. All unmatched rows remain visible. No source/page-specific NASA report total was independently established for reconciliation. The table source was supplied as a NASA starter-kit file; attribution is not independently authenticated.

## Task 04B — NASA ACME/BRE Final Report (2022) cross-source reconciliation

Incremental, non-destructive report comparison. The report was independently inspected at PDF pages **24, 110, 112, 116, 127**. No report PDF is repackaged: the original NASA report is a separately maintained source document. The page-specific, manually transcribed reference manifest is **not** an authoritative raw-run mapping.

```bash
cd /mnt/data/analysis/T5/PSI-20_BRE
python scripts/reconcile_nasa_report.py \
  --table "/mnt/data/PSI-20_Experimental table_ACME BRE.csv" \
  --out table_audit
python -m unittest discover -s tests -v
sha256sum "/mnt/data/PSI-20_Experimental table_ACME BRE.csv" /mnt/data/psi20_inputs/*.csv
sha256sum table_audit/report_*
```

New files: `scripts/reconcile_nasa_report.py`, `tests/test_report_reconciliation.py`, `table_audit/report_reference_manifest.csv`, `table_audit/cross_source_discrepancies.csv`, `table_audit/report_reconciliation.md`, and `table_audit/report_reconciliation_sha256.txt`. Existing Task 04 audit outputs remain unchanged. The reconciliation reports four CSV-vs-report differences and an additional internal difference between report Table 1 copies on PDF pages 24 and 112. Page 127's 196 statement refers specifically to *Round 2 successful ignitions* and is **not presumed directly equivalent** to the 194 total flames ignited in pages 110 and 116. No source data are modified or normalized. A source mismatch is not a CSV parsing failure.

The script uses explicitly documented day-level dates and counts to associate four CSV records with four report rows. This is a constrained comparison, not a run-level identity join; it raises an error if any selected comparison is not unique. All NASA statements are anchored to the report pages above. No physical or causal interpretation is permitted.

## Task 04C — final report interpretation correction

PDF page **23** of *ACME/BRE Final Report (2022)* explicitly corrects Test Day `19094` to **2019-04-04** (operational day start). PDF page **112** preserves the historical April 5 listing; PDF page **24** uses April 4. The reconciliation now labels this `explained_historical_source_difference` and retains both records with page-specific provenance.

PDF page **29** describes **196 successful ignitions** across orbital BRE tests; page **127** uses **196** with wording referring to Round 2, while page **110** reports **62 Round 1 + 132 Round 2 = 194 total flames** and page **116** also reports **194 flames ignited**. These are distinct source statements and their apparent scope/count differences remain unresolved. Four CSV-versus-report differences remain unchanged in number and raw source values. No source correction is applied.

```bash
cd /mnt/data/analysis/T5/PSI-20_BRE
python scripts/reconcile_nasa_report.py --table "/mnt/data/PSI-20_Experimental table_ACME BRE.csv" --out table_audit
python -m unittest discover -s tests -v
sha256sum "/mnt/data/PSI-20_Experimental table_ACME BRE.csv" /mnt/data/psi20_inputs/*.csv
sha256sum table_audit/report_*
```

The PDF report is an external evidence source, not included in the ZIP. No scientific modeling or classification.
