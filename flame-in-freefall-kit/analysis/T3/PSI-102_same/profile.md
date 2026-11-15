# Profile: PSI-102 SAME

## Folders on PSI (from the PSI file listing; check against the page)

| Folder | Files | Size (MB, 1 MB = 1,048,576 bytes) |
| --- | --- | --- |
| Analyzed Data | 59 | 217.5 |
| Engineering Documents | 28 | 345.2 |
| Experimental table | 1 | 0.0 |
| Presentations | 6 | 58.6 |
| Reference Data | 3 | 1.3 |
| Reports | 1 | 3.5 |
| Science Documents | 2 | 0.9 |
| metadata | 1 | 0.0 |

## Experimental table and downloaded files

Run from the kit root and paste or append the output here:

```bash
python tools/profile_files.py "data/experimental_tables/PSI-102" --out "analysis/T3/PSI-102_same/profile.md"
python tools/profile_files.py "data/raw/PSI-102" --out "analysis/T3/PSI-102_same/profile.md"   # after downloading
```

## Documents (PDF, presentations)

| File | Title | Pages | What it is for |
| --- | --- | --- | --- |

### data/experimental_tables/PSI-102/Experimental table/PSI-102_Experimental table_SAME.csv
- type: .csv; size: 331 bytes
- rows: 8 (data rows 2 to 9, header = row 1); fully empty rows: 0; duplicate rows: 0
- columns: 5

| Column | Empty cells | Example value |
| --- | --- | --- |
| Sample # | 0 | 1 |
| Sample Material | 0 | Teflon |
| Air Flow (cm/s) | 4 | 5 |
| Weight loss rate (mg/min) | 4 | 2 |
| Aging Duration (minutes) | 4 | 1 |

## Downloaded analyzed data (2026-11-14)

- 60 files in data/raw/PSI-102/Analyzed Data (228.1 MB so far; download continuing): one Excel housekeeping/log workbook per SAME flight run, named by GMT day, run number and material (e.g. 'GMT271kapton29.xls').
- The per-test SAME results (sizes, detectors) used in the findings are in the PSI-101 combined workbook (rows where the flight column is 1).
- not yet analysed (v2: time series of each run).
