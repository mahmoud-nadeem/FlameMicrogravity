# Findings: PSI-98 SAFFIRE-I

Format, one line each (lines that start with F- are checked by tools/self_check.py):
`F-<track>-<number> | statement in one sentence | label | source file | row or page | confidence | caveat`

Labels: OBSERVED IN DATA, REPORTED BY NASA OR A PUBLICATION (source), OUR INFERENCE. Confidence: high, medium or low.
Rows: the source_row of the run table (line number in the file, or row number in Excel; header = 1).
Example of the shape only: F-T2-1 | ... | OBSERVED IN DATA | PSI-98/Experimental table/<file>.csv | rows 2-9 | medium | ...

F-T2-9801 | PSI-98 S1 recorded its highest post-igniter sample-group reading at Sample Temp 5 (TC11) (1091.76 °C, elapsed 369.039 s) and highest plume reading at Plume Temp 3 (TC3) (121.70 °C, 477.675 s). | OBSERVED IN DATA | PSI-98/Raw Data/PSI-98_Raw Data_Saffire-I Sample 1 Sensor Data Complete TM graphs.xlsx | Calibrated Data; exact elapsed keys 369.039 s and 477.675 s; channel labels in statement | high | Point readings from different locations; elapsed time is from recording start.
F-T2-9802 | PSI-98 S2 recorded its highest post-igniter sample-group reading at Sample Temp 6 (TC12) (24.88 °C, elapsed 512.753 s) and highest plume reading at Plume Temp 3 (TC3) (94.40 °C, 106.490 s). | OBSERVED IN DATA | PSI-98/Raw Data/PSI-98_Raw Data_Saffire-I Sample 2 Sensor Data Complete TM graphs.xlsx | Calibrated Data; exact elapsed keys 512.753 s and 106.490 s; channel labels in statement | high | Point readings from different locations; elapsed time is from recording start.
