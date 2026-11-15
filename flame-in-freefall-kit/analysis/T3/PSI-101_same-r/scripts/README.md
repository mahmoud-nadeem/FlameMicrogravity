# Run order: PSI-101 SAME-R

Run every command from the kit root folder.

1. `python tools/build_run_table.py "analysis/T3/PSI-101_same-r/scripts/run_table_map.yaml"`

2. `python analysis/T3/PSI-101_same-r/scripts/same_results_analysis.py` (needs the PSI-101 results workbook in data/raw: `python scripts/psi_fetch.py --datasets same`)
3. `python analysis/T3/PSI-101_same-r/scripts/hkp_time_series.py` (needs data/raw/PSI-101/Raw Data/*HKPData*.csv and the output of step 2)

Outputs: tables/derived_same_results_flight_tests.csv, tables/derived_numbers.json, charts/*.png, model/evaluation.json.
Step 3 outputs: tables/derived_hkp_test_events.csv, tables/derived_hkp_numbers.json, charts/iss_scatter_floor.png, charts/smoke_arrival_times.png, and its own block in data_log.md.
