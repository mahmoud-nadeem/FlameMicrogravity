# Self-check: T5 (Khaled Adwi)

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
| 10 | Anything unconfirmed is labelled unconfirmed | FAIL |

**5. data_log.md covers changes; raw files unchanged: PASS**
- analysis/T5/PSI-10_flame-design/data_log.md: table exists but no build_run_table section (built by hand? log every change)

**7. si_log.md is up to date: PASS**
- 3 entries; only you can confirm it is up to date

**9. Scripts re-run from scratch and reproduce outputs: MANUAL**
- run every command of each scripts/README.md from a fresh copy and compare the outputs

**10. Anything unconfirmed is labelled unconfirmed: FAIL**
- analysis/T5/PSI-10_flame-design/card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis/T5/PSI-20_bre/card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis/T5/PSI-22_e-field/card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis/T5/PSI-23_s-flame/card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
