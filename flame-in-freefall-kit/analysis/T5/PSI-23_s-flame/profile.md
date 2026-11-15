# Profile: PSI-23 ACME s-Flame

## Historical PSI inventory snapshot (2026-11-14; live file listing not fully verified)

| Folder | Files | Size (MB, 1 MB = 1,048,576 bytes) |
| --- | --- | --- |
| Engineering Documents | 29 | 181.6 |
| Experimental table | 1 | 0.0 |
| Presentations | 17 | 48.3 |
| Raw Data | 4058 | 744,626.3 |
| Reference Data | 50 | 1,068.5 |
| Reports | 2 | 3.3 |
| Science Documents | 7 | 9.4 |
| metadata | 1 | 0.0 |

## Experimental table and downloaded files

Run from the kit root and paste or append the output here:

```bash
python tools/profile_files.py "data/experimental_tables/PSI-23" --out "analysis/T5/PSI-23_s-flame/profile.md"
python tools/profile_files.py "data/raw/PSI-23" --out "analysis/T5/PSI-23_s-flame/profile.md"   # after downloading
```

## Documents (PDF, presentations)

| File | Title | Pages | What it is for |
| --- | --- | --- | --- |

## Analysis of available NASA experimental table
- 18 summary records (rows 2–19) with a count for each; sum 276, range 7–23.
- 10 first-round records sum to 152; 8 second-round records sum to 124.
- Original atmosphere/fuel descriptions include N3, N4, N5 and N6 strings, some unusual; retain without correction.
- This table lacks per-flame extinction classifications or raw physical sensor traces.

Sources: `data/experimental_tables/PSI-23/Experimental table/PSI-23_Experimental table_ACME s-Flame.csv` (SHA-256 `16cd10f50bd2e962887c8eb4077e5a9b3e790c78de8e0361c0b77e19300be7cf`)
