# Run order: PSI-47 DAFT / DAFT-2

Run every command from the kit root folder.

1. `python tools/build_run_table.py "analysis/T3/PSI-47_daft/scripts/run_table_map.yaml"`

2. `python analysis/T3/PSI-47_daft/scripts/daft_time_series.py` (needs data/raw/PSI-47/Analyzed Data: `python scripts/psi_fetch.py --datasets daft`)

Outputs: tables/derived_daft_aligned.csv, tables/derived_daft_numbers.json, charts/daft_test02_velcro.png.
