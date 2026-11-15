# HANDOFF (T3)

Track and name: T3, Mahmoud Nadeem
Version and time: v1, 2026-11-15, sent at:
Records covered (with VERIFIED or UNCONFIRMED for each ID):
- PSI-102 SAME: VERIFIED against the PSI page on 2026-11-15 (version 4, 627.14 MB, CC0-1.0, related PSI-101)
- PSI-101 SAME-R: VERIFIED against the PSI page on 2026-11-15 (version 4, 5.87 GB, CC0-1.0, related PSI-102)
- PSI-47 DAFT / DAFT-2: VERIFIED against the PSI page on 2026-11-15 (version 5, 39.83 MB, CC0-1.0, related PSI-102; one record, plus a DAFT-3 series in 2006 in its files)
What is done (tables, findings count, charts):
- Standard run tables from the three experimental tables: PSI-102 8 rows, PSI-101 109 rows, PSI-47 2 rows (every change in data_log.md).
- PSI-101: analysis of the SAME/SAME-R flight results workbook (154 flight tests) and of the 44 SAME-R housekeeping time series (1 Hz); derived tables with source rows; numbers in tables/derived_*.json.
- PSI-47: analysis of the DAFT P-Trak and DustTrak logs (7 tests) and of the DAFT post-flight report and fact sheet.
- 23 findings: F-T3-1..7, 15..19 and 23 in PSI-101_same-r, F-T3-8..10 in PSI-102_same, F-T3-11..14 and 20..22 in PSI-47_daft. 6 charts with captions (charts/CAPTIONS.md in each record).
- Extra work: extra/test_questions.md (5 + 2), extra/evidence_snippets.json (16 cited snippets), extra/limitations.md, extra/track_paragraph.md, demo chart named in extra/README.md; notes/concepts.md (9 concepts).
Model status (gate passed, failed or not attempted, and why):
- PSI-101: gate passed, modest gain. Ridge on log particle diameter, grouped CV by test pair: log MAE 0.274 vs baseline 0.372 (PSI-101_same-r/model/README.md). OUR INFERENCE, limits stated.
- PSI-102 and PSI-47: no model (no target; 8 and 2 rows): model/no_model.md.
Data quirks and traps another person must know:
- SAME and SAME-R must not be pooled (F-T3-5); the SAME experimental table does not match the SAME flight records (F-T3-8).
- Results workbook: 40 sheets, several near-copies; the analysis uses only 'Reduced Data with ISS Det' (header on Excel row 2). Test 'NNa' is test 'NN' re-measured after aging: keep pairs together.
- DBP tests (rows 3-22) and three Kapton runs without a P-Trak count (rows 32, 41, 45) have no size result; 6 rows with an impossible size pair (47, 48, 145, 147, 149, 155) are kept out of the size analyses (F-T3-23); all logged in PSI-101_same-r/data_log.md. In the SAME-R experimental table test 57 is duplicated (table rows 57, 75).
- Housekeeping files: some repeated timestamps (first kept) and a repeated header line in gmt251_4 (skipped), both logged; the column DustTrakAMeasurement(MgPerM3) is not a mass concentration (F-T3-19); the ISS scatter raw signal is negative and pins near -6.25 V (F-T3-15).
- DAFT: the instrument clocks drift, so logs cannot be aligned second by second (F-T3-20); one P-Trak reading of 524,291 pt/cc exceeds its 500,000 maximum (F-T3-22, kept and flagged).
- No oxygen or cabin pressure in any T3 table; housekeeping pressures are hardware lines, not the atmosphere.
- source_row: Excel row for xls/xlsx, line number for csv (header = 1).
What I could not do and why:
- The SAME and SAME-R reports were not downloaded yet (python scripts/psi_fetch.py --datasets t3-docs), so the ISS detector output range (F-T3-6 caveat) and the meaning of Rt/R0 (F-T3-4 caveat) remain unconfirmed.
- P-Trak, STS and ion detector A were left out of the timing comparison (intermittent or partial data); DAFT tests 3-7 could not be aligned in time.
- The PSI-102 per-run workbooks were downloaded but not analysed (the same tests are in the PSI-101 combined workbook).
Self-check results (items 1 to 10 of 7.6): see SELF_CHECK.md in the zip (python tools/self_check.py T3). Item 9 checked by hand on 2026-11-15: every command in the three scripts/README.md files was re-run and all 9 derived tables and number files came out byte-identical.
Questions for Mohammed Tamer:
- Should the derived tables (workbook and time-series level) go into the shared warehouse, or only the standard run tables?
- Is a modest model (error factor 1.33 vs 1.47) worth showing, or keep it out of the dashboard?
Idea tickets raised (titles): Member characters that explain each track's findings (idea_ticket_member_characters.md).
Hours spent:
