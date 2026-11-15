# Run 19056A2 — raw audit summary

All statements below: **OBSERVED IN DATA** unless labeled as assumptions.

| Source | Records | Exact duplicates beyond first | Duplicate timestamps | Negative intervals | Non-modal/zero intervals |
|---|---:|---:|---:|---:|---:|
| data | 31,316 | 0 | 0 | 1 | 7,747 |
| mfc | 60 | 48 | 52 | 0 | 57 |

No raw measurement records were dropped. All numerical channel summaries are uncalibrated.
Potential saturation screening applies only to measured data channels, never MFC control setpoints; no physical saturation is confirmed.
Major data gaps (threshold >= 1.0 s): 1. Full interval statistics and source positions in timing_report.json.
No flame-extinction classification, causal inference, physical calibration, or modeling was performed.

## Alignment safety (ASSUMPTIONS / OPERATIONAL SCREENING)
MFC record timestamp lookup is not a change-event measurement or response. Repeated records have no independent change-event ID. Staleness uses the operational gap threshold and gap crossing; clocks remain unverified.

## MFC events within major data gaps (OBSERVED TIMESTAMP LABELS; clock synchronization UNVERIFIED)
- MFC source row 26 at 2019-02-25 15:59:20.911 lies within a data timestamp gap; this is NOT measured response.
