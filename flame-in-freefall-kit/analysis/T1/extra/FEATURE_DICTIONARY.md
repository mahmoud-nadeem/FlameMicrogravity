V6 additive data dictionary

- dashboard_runs.csv: preserved V5 interface. dashboard_runs_enriched.csv: same rows plus traceable x_ features. Per-PSI clean tables use x_ prefix for date columns to comply with the team schema.
- x_as_run_id is the execution sequence in BASS; x_test_id is the planned test identifier. They are not interchangeable or unique on their own. Use run_id.
- x_material_family_context is an optional PI/FAQ-based family hypothesis; x_material_family_keyword is the original conservative label. Never report the inferred label as observed composition.
- x_air_listed_values_json retains order of literal numbers only for complete numeric lists. Qualified strings, ranges, pot values and text are excluded rather than stripped; raw retained. No timing, steady state, extinction or local airflow asserted. PSI-25 FAQ states cm/s and ~1 min instrument response; PSI-26 nominal duct air display in cm/s supported by workbook K/U/AD and NASA BASS documentation. Fan display and flow restriction are separate.
- x_co/ co2 phase status, valid_value, lower_bound: exact physically nonnegative numerics only; CO OR is >1000 ppm per FAQ, >500 is explicit lower bound. Over unspecified remains unknown; negatives kept raw. No imputation. CO2 units as source (% by volume).
- x_o2_change_pp: final minus initial calibrated oxygen, percentage points, not a combustion rate. Review flag unchanged.

V7 publication: NASA/TM-20210011385 Appendix A (Tables A.1, A.3, A.6) shows missing underlying O2 readings for B2, P22A, P22B, T28A, T28B. Their five reported final O2 readings are excluded from the analytical final O2 and change fields; two other final O2 readings are not reported. There are 122 usable pairs. Negative CO, nonnumeric and overrange readings are not exact concentrations; explicit censoring bounds remain. Raw source values and audit records are retained outside the primary RAG run fields. No fabricated replacements.
