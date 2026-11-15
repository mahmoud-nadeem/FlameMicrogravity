# Profile: PSI-20 ACME BRE

## Historical PSI inventory snapshot (2026-11-14; live file listing not fully verified)

| Folder | Files | Size (MB, 1 MB = 1,048,576 bytes) |
| --- | --- | --- |
| Engineering Documents | 25 | 153.9 |
| Experimental table | 1 | 0.0 |
| Presentations | 13 | 175.8 |
| Raw Data | 2297 | 1,940,853.3 |
| Reports | 2 | 17.5 |
| Science Documents | 22 | 68.8 |
| metadata | 1 | 0.0 |

## Experimental table and downloaded files

Run from the kit root and paste or append the output here:

```bash
python tools/profile_files.py "data/experimental_tables/PSI-20" --out "analysis/T5/PSI-20_bre/profile.md"
python tools/profile_files.py "data/raw/PSI-20" --out "analysis/T5/PSI-20_bre/profile.md"   # after downloading
```

## Documents (PDF, presentations)

| File | Title | Pages | What it is for |
| --- | --- | --- | --- |

## Analysis of available sources
- 18 CSV summary-day rows; 194 ignitions; range 0–21; mean 10.78, median 10.
- One locally verified raw run `19056A2`: 31,316 measurement rows, one 123.034 s gap and one negative time interval.
- Four approved EDA charts included in `charts/`; supporting approved audit reports in `tables/`.
- Report inconsistencies retained without silent correction, see `tables/report_reconciliation.md`.

Sources: `data/experimental_tables/PSI-20/Experimental table/PSI-20_Experimental table_ACME BRE.csv` (SHA-256 `4aa5d3f98708ceacced5c620d46858b9965f8d4d941b203229f46467d53e5ab7`)
