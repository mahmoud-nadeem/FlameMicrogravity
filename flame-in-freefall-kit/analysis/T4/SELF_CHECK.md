# Self-check: T4 (Mohammed Tamer)

| # | Item | Result |
| --- | --- | --- |
| 1 | Tables have all required columns, in order | WARN |
| 2 | No row without source_file or source_row | PASS |
| 3 | Units stated; mixed units converted and logged | PASS |
| 4 | Every finding has source, row or page, and label | FAIL |
| 5 | data_log.md covers changes; raw files unchanged | PASS |
| 6 | references.md lists every PSI record, paper and tool | FAIL |
| 7 | si_log.md is up to date | PASS |
| 8 | No file over 50 MB, no secrets, no raw video or image dumps | PASS |
| 9 | Scripts re-run from scratch and reproduce outputs | MANUAL |
| 10 | Anything unconfirmed is labelled unconfirmed | FAIL |

**1. Tables have all required columns, in order: WARN**
- no run table yet (tables/<PSI-ID>_<slug>_runs_clean.csv)

**4. Every finding has source, row or page, and label: FAIL**
- analysis\T4\PSI-69_flex\findings.md line 11: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 12: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 13: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 14: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 15: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 16: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 17: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 18: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 19: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 20: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 21: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 22: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 23: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 24: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 25: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 26: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 27: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 28: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 29: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 30: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 31: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 32: confidence must be high, medium or low
- analysis\T4\PSI-69_flex\findings.md line 33: confidence must be high, medium or low

**6. references.md lists every PSI record, paper and tool: FAIL**
- references.md still has '[replace ...]' placeholders: paste the PSI 'Cite this Investigation' text

**7. si_log.md is up to date: PASS**
- 1 entries; only you can confirm it is up to date

**9. Scripts re-run from scratch and reproduce outputs: MANUAL**
- run every command of each scripts/README.md from a fresh copy and compare the outputs

**10. Anything unconfirmed is labelled unconfirmed: FAIL**
- analysis\T4\PSI-159_cfi-g\card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis\T4\PSI-39_cfi\card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis\T4\PSI-68_flex-2\card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis\T4\PSI-69_flex\card.json: not checked on the PSI page yet (fill verified_on and verified_by after checking every field, and write 'unconfirmed' where the page does not show it)
- analysis\T4\PSI-159_cfi-g\card.json: TODO left on line(s) 27, 28
- analysis\T4\PSI-39_cfi\card.json: TODO left on line(s) 28, 29
- analysis\T4\PSI-68_flex-2\card.json: TODO left on line(s) 23, 24
- analysis\T4\PSI-69_flex\card.json: TODO left on line(s) 24, 25
