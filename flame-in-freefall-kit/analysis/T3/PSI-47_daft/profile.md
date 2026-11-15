# Profile: PSI-47 DAFT / DAFT-2

## Folders on PSI (from the PSI file listing; check against the page)

| Folder | Files | Size (MB, 1 MB = 1,048,576 bytes) |
| --- | --- | --- |
| Analyzed Data | 12 | 3.3 |
| Engineering Documents | 6 | 7.6 |
| Experimental table | 1 | 0.0 |
| Presentations | 3 | 14.4 |
| Raw Data | 6 | 0.0 |
| Reports | 3 | 13.3 |
| Representative Image(s) | 1 | 1.3 |
| metadata | 1 | 0.0 |

## Experimental table and downloaded files

Run from the kit root and paste or append the output here:

```bash
python tools/profile_files.py "data/experimental_tables/PSI-47" --out "analysis/T3/PSI-47_daft/profile.md"
python tools/profile_files.py "data/raw/PSI-47" --out "analysis/T3/PSI-47_daft/profile.md"   # after downloading
```

## Documents (PDF, presentations)

| File | Title | Pages | What it is for |
| --- | --- | --- | --- |

### data/experimental_tables/PSI-47/Experimental table/PSI-47_Experimental table_DAFT.csv
- type: .csv; size: 518 bytes
- rows: 2 (data rows 2 to 3, header = row 1); fully empty rows: 0; duplicate rows: 0
- columns: 5

| Column | Empty cells | Example value |
| --- | --- | --- |
| Session Name | 0 | D1 |
| Actual Day | 0 | GMT 54 (2005) |
| Hardware Description | 0 | Contained the modified P-Trak with Alcoh |
| Sample Material | 0 | Arizona Road Dust (ARD Fine) in combinat |
| Sampled Location | 0 | Sampled air near Express rack 4 |

## Downloaded data

- data/raw/PSI-47/Analyzed Data: 12 Excel files: per-test P-Trak (pt/cc) and DustTrak (mg/m3) logs at 1 s (sheets PTrkNNNN, DTrkNNNN with a header block in columns A-B and time/value in E-F), a TIMING sheet linking logs to the video, 'DAFT Retrieved Data Summary.xls' (sheets 'Raw PTrak Data' 2331 x 21, 'Raw DustTrak Data' 2427 x 21, 'Headers' 24 x 9: serials, dates, durations and points of tests 1-7), and two August 2006 bag-test sheets (38 and 28 rows) with voice-downlinked readings.
- Engineering Documents: P-Trak condenser tube modification (PDF) and DAFT images (download in progress).
- The 1 s logs are not analysed yet (v2).
