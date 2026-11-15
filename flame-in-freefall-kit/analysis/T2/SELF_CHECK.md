# Self-check: T2 (Mohamed Shreif)

| # | Item | Result |
| --- | --- | --- |
| 1 | Tables have all required columns, in order | WARN |
| 2 | No row without source_file or source_row | PASS |
| 3 | Units stated; mixed units converted and logged | PASS |
| 4 | Every finding has source, row or page, and label | PASS |
| 5 | data_log.md covers changes; raw files unchanged | PASS |
| 6 | references.md lists every PSI record, paper and tool | FAIL |
| 7 | si_log.md is up to date | PASS |
| 8 | No file over 50 MB, no secrets, no raw video or image dumps | PASS |
| 9 | Scripts re-run from scratch and reproduce outputs | MANUAL |
| 10 | Anything unconfirmed is labelled unconfirmed | FAIL |

**1. Tables have all required columns, in order: WARN**
- no run table yet (tables/<PSI-ID>_<slug>_runs_clean.csv)

**6. references.md lists every PSI record, paper and tool: FAIL**
- references.md still has '[replace ...]' placeholders: paste the PSI 'Cite this Investigation' text

**7. si_log.md is up to date: PASS**
- 1 entries; only you can confirm it is up to date

**9. Scripts re-run from scratch and reproduce outputs: MANUAL**
- run every command of each scripts/README.md from a fresh copy and compare the outputs

**10. Anything unconfirmed is labelled unconfirmed: FAIL**
- analysis\T2\PSI-100_saffire-iii\card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis\T2\PSI-98_saffire-i\card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis\T2\PSI-99_saffire-ii\card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis\T2\PSI-100_saffire-iii\card.json: TODO left on line(s) 22, 23
- analysis\T2\PSI-98_saffire-i\card.json: TODO left on line(s) 23, 24
- analysis\T2\PSI-99_saffire-ii\card.json: TODO left on line(s) 19, 20
