# Self-check: T1 (Amr Morgan)

| # | Item | Result |
| --- | --- | --- |
| 1 | Tables have all required columns, in order | PASS |
| 2 | No row without source_file or source_row | PASS |
| 3 | Units stated; mixed units converted and logged | PASS |
| 4 | Every finding has source, row or page, and label | PASS |
| 5 | data_log.md covers changes; raw files unchanged | PASS |
| 6 | references.md lists every PSI record, paper and tool | PASS |
| 7 | si_log.md is up to date | PASS |
| 8 | No file over 50 MB, no secrets, no raw video or image dumps | PASS |
| 9 | Scripts re-run from scratch and reproduce outputs | MANUAL |
| 10 | Anything unconfirmed is labelled unconfirmed | PASS |

**5. data_log.md covers changes; raw files unchanged: PASS**
- analysis/T1/PSI-25_bass-ii/data_log.md: table exists but no build_run_table section (built by hand? log every change)
- analysis/T1/PSI-26_bass/data_log.md: table exists but no build_run_table section (built by hand? log every change)

**7. si_log.md is up to date: PASS**
- 3 entries; only you can confirm it is up to date

**9. Scripts re-run from scratch and reproduce outputs: MANUAL**
- run every command of each scripts/README.md from a fresh copy and compare the outputs

Live NASA metadata and human sign-off are not authenticated by the automated validator.
