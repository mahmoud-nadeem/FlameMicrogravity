# Findings: PSI-100 SAFFIRE-III

Format, one line each (lines that start with F- are checked by tools/self_check.py):
`F-<track>-<number> | statement in one sentence | label | source file | row or page | confidence | caveat`

Labels: OBSERVED IN DATA, REPORTED BY NASA OR A PUBLICATION (source), OUR INFERENCE. Confidence: high, medium or low.
Rows: the source_row of the run table (line number in the file, or row number in Excel; header = 1).
Example of the shape only: F-T2-1 | ... | OBSERVED IN DATA | PSI-100/Experimental table/<file>.csv | rows 2-9 | medium | ...

F-T2-10001 | PSI-100 S1 recorded its highest post-igniter sample-group reading at Sample Temp 5 (TC11) (1088.21 °C, elapsed 307.230 s) and highest plume reading at Plume Temp 3 (TC3) (95.64 °C, 109.791 s). | OBSERVED IN DATA | PSI-100/Raw Data/PSI-100_Raw Data_Saffire III Sample 1 Sensors.xlsx | Calibrated Data; exact elapsed keys 307.230 s and 109.791 s; channel labels in statement | high | Point readings from different locations; elapsed time is from recording start.
F-T2-10002 | PSI-100 S2 recorded its highest post-igniter sample-group reading at Sample Temp 6 (TC12) (20.04 °C, elapsed 138.765 s) and highest plume reading at Plume Temp 3 (TC3) (48.35 °C, 159.852 s). | OBSERVED IN DATA | PSI-100/Raw Data/PSI-100_Raw Data_Saffire III Sample 2 Sensors.xlsx | Calibrated Data; exact elapsed keys 138.765 s and 159.852 s; channel labels in statement | high | Point readings from different locations; elapsed time is from recording start.
