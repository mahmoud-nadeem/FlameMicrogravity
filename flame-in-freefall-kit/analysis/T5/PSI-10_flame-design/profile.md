# Profile: PSI-10 ACME/Flame Design

## Historical PSI inventory snapshot (2026-11-14; live file listing not fully verified)

| Folder | Files | Size (MB, 1 MB = 1,048,576 bytes) |
| --- | --- | --- |
| Engineering Documents | 1 | 7.1 |
| Experimental table | 2 | 0.0 |
| Raw Data | 3792 | 2,079,410.3 |
| Reports | 3 | 4.3 |
| Representative Image(s) | 5 | 0.8 |
| Science Documents | 3 | 2.5 |
| metadata | 1 | 0.0 |

## Experimental table and downloaded files

Run from the kit root and paste or append the output here:

```bash
python tools/profile_files.py "data/experimental_tables/PSI-10" --out "analysis/T5/PSI-10_flame-design/profile.md"
python tools/profile_files.py "data/raw/PSI-10" --out "analysis/T5/PSI-10_flame-design/profile.md"   # after downloading
```

## Documents (PDF, presentations)

| File | Title | Pages | What it is for |
| --- | --- | --- | --- |

## Analysis of available NASA experimental tables
- 327 source rows across two tables: 207 Normal (rows 2–208) and 120 Inverse (rows 2–121).
- Normal fuel labels: C2H4 187; C3H8 20. No explicit Fuel column for inverse.
- Approved standardization stored in `tables/PSI-10_flame-design_runs_clean.csv`. No outcome labels.
- Oxygen semantics differ between normal and inverse geometries. Data rows are tests, not a success count.

Sources: `data/experimental_tables/PSI-10/Experimental table/PSI-10_Experimental table_Flame Design_Inverse Flame.csv` (SHA-256 `97933ee9ae0b9ebc6b948a67485a0fe2f8218f753253a4f2be93c40d374c44e4`), `data/experimental_tables/PSI-10/Experimental table/PSI-10_Experimental table_Flame Design_Normal Flame.csv` (SHA-256 `4a663292bd3f65201943cc71bd661a70383639276a9176f64105b285bf0b6deb`)
