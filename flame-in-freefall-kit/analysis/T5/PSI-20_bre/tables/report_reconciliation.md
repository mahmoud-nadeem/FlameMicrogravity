# Task 04C — NASA report reconciliation (non-destructive)

## OBSERVED IN LOCAL FILES
- Source CSV SHA-256: `4aa5d3f98708ceacced5c620d46858b9965f8d4d941b203229f46467d53e5ab7`; 18 day-level records; sum of `Flames Ignited` = **194**.
- Four CSV-versus-report differences are preserved individually in `cross_source_discrepancies.csv`.
- One additional **explained historical source difference** is retained as a provenance record, not an unresolved date discrepancy.
- Original CSV raw values and row order, plus all Task 04 legacy outputs, remain unchanged.

## REPORTED BY NASA — independently inspected PDF pages
- **ACME/BRE Final Report (2022)**, dated **1 February 2022**, Table 1 on PDF **pages 24 and 112**: Test Day 19066 (7 March 2019, 34%, 6 flames); 19091 (1 April 2019, 21%, 0 flames); 20261 (17 September 2020, 26.5% and 34%, 13 flames); 20279 (5 October 2020, 25%, 34%, 40%, 21 flames).
- **PDF page 23 (explicit correction):** Test Day **19094** is corrected to **4 April 2019**. Older 30-day reports had listed April 5. Some testing continued past midnight in Cleveland, but NASA identifies a Test Day by **the calendar date the test day began**. Table 1 **page 24** uses April 4, while its historical Appendix reproduction on **page 112** retains April 5. The original experimental CSV lists April 4. The page-112 date remains documented as historical provenance, not an unresolved conflict.
- **PDF page 29:** **“BRE tests in orbit were finished with 196 successful ignitions.”** This is an overall orbital-test statement, in the flammability-map discussion; it does not explicitly restrict the 196 count to Round 2.
- **PDF page 110:** **62** flames in Round 1, **132** in Round 2, **194 total flames ignited**.
- **PDF page 116:** **194 flames ignited**, in the completeness/quality-of-data section.
- **PDF page 127:** **“Round 2 tests were finished with 196 successful ignitions.”** This wording explicitly invokes Round 2, whereas page 110 reports 132 Round 2 flames. **Apparent scope inconsistency unresolved.**

## OUR INFERENCE / UNRESOLVED
- The CSV sum **194** agrees numerically with the NASA total on pages 110 and 116; this does not prove equivalence of counting definitions with **196 successful ignitions** on pages 29 and 127.
- The **194 versus 196** discrepancy is **unresolved**; do not invent an explanation. The **page-127 Round 2 scope versus page-110 Round 2 count of 132** is an additional apparent scope inconsistency, not resolved by page 29.
- `3400%` versus `34%` and `2100%` versus `21%` are source-string differences, not demonstrated measurement errors or authorized corrections.
- CSV dates 2020-10-17 and 2020-12-05 differ from NASA Table 1 dates 2020-09-17 and 2020-10-05 for candidate day-level correspondences (13 and 21 flames). No raw-run identities are inferred.
- Day-level `Flames Ignited` counts do not equal raw CSV run counts. No calibration, classification, modeling, or causal inference.

## Reproduction
```bash
python scripts/reconcile_nasa_report.py --table "/mnt/data/PSI-20_Experimental table_ACME BRE.csv" --out table_audit
```
