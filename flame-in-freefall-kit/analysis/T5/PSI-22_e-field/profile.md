# Profile: PSI-22 ACME E-FIELD Flames

## Historical PSI inventory snapshot (2026-11-14; live file listing not fully verified)

| Folder | Files | Size (MB, 1 MB = 1,048,576 bytes) |
| --- | --- | --- |
| Engineering Documents | 26 | 175.4 |
| Experimental table | 1 | 0.0 |
| Presentations | 32 | 770.9 |
| Raw Data | 2502 | 905,199.9 |
| Reference Data | 2 | 3.7 |
| Reports | 9 | 17.8 |
| Representative Image(s) | 4 | 0.3 |
| Science Documents | 13 | 25.2 |
| metadata | 1 | 0.0 |

## Experimental table and downloaded files

Run from the kit root and paste or append the output here:

```bash
python tools/profile_files.py "data/experimental_tables/PSI-22" --out "analysis/T5/PSI-22_e-field/profile.md"
python tools/profile_files.py "data/raw/PSI-22" --out "analysis/T5/PSI-22_e-field/profile.md"   # after downloading
```

## Documents (PDF, presentations)

| File | Title | Pages | What it is for |
| --- | --- | --- | --- |

## Analysis of available NASA experimental table
- Physical CSV rows: 32 (rows 2–33), but only 21 contain an ignition count; 11 are continuation rows.
- Arithmetic sum across all 21 count-bearing CSV rows: 230, **not** a validated total over unique Test Days.
- Only 20 distinct Test Day IDs: `18319` appears twice, in rows 26 and 30, both listing 11 ignitions.
- **Do not silently remove either row**; any total excluding a repeated row would require checking NASA's intended convention.
- Rounds: first coflow burner 11 count-bearing records (sum 120); second gas-jet burner 10 (sum 110, including the repeated day).
- No measured voltage/ion-current relationship in the summary table.

Sources: `data/experimental_tables/PSI-22/Experimental table/PSI-22_Experimental table_ACME E-FIELD Flames.csv` (SHA-256 `69090c357b83ae38d161d29001d1d32b40fd77b13324ca6585ee990cdceef524`)
