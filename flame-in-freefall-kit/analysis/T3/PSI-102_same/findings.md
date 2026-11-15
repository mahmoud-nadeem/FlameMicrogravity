# Findings: PSI-102 SAME

Format, one line each (lines that start with F- are checked by tools/self_check.py):
`F-<track>-<number> | statement in one sentence | label | source file | row or page | confidence | caveat`

Labels: OBSERVED IN DATA, REPORTED BY NASA OR A PUBLICATION (source), OUR INFERENCE. Confidence: high, medium or low.
Rows: the source_row of the run table (line number in the file, or row number in Excel; header = 1).
Example of the shape only: F-T3-1 | ... | OBSERVED IN DATA | PSI-102/Experimental table/<file>.csv | rows 2-9 | medium | ...

F-T3-8 | The SAME experimental table lists Teflon at air flows of 5 and 10 cm/s with 1 or 20 minutes of aging (rows 2-5) and says the other four materials used the same conditions (rows 6-9), but the 45 SAME flight rows of the SAME/SAME-R results workbook record inlet velocities of 2, 4, 7.5 and 8 cm/s and net aging of 11-1964 s. | OBSERVED IN DATA | PSI-102/Experimental table/PSI-102_Experimental table_SAME.csv; PSI-101/Analyzed Data/PSI-101_Analyzed Data_SAME, SAME-R_Results.xlsx, sheet 'Reduced Data with ISS Det' | table rows 2-9; workbook rows 3-139 where the flight column is 1 | high | The table may describe a planned matrix; use the workbook values for analysis and confirm with the SAME final report.
F-T3-9 | All 20 SAME tests with dibutyl phthalate (DBP) have no particle-size result in the results workbook (all moment columns are 0); SAME-R did not fly DBP. | OBSERVED IN DATA | PSI-101/Analyzed Data/PSI-101_Analyzed Data_SAME, SAME-R_Results.xlsx, sheet 'Reduced Data with ISS Det' | rows 3-22 | high | NASA reports SAME-R introduced Pyrell to replace the DBP samples (PSI-101 page, Approach); the reason for the missing DBP sizes is not stated in this sheet.
F-T3-10 | NASA hypothesised that smoke grown in microgravity forms larger particles than in 1 g and that this change could keep some smoke detectors from alarming. | REPORTED BY NASA OR A PUBLICATION (PSI-102 page, Hypothesis) | https://psi.nasa.gov/physci/repo/data/investigations/PSI-102 | page section Hypothesis | high | This is NASA's hypothesis, not a result; findings F-T3-1 to F-T3-6 are what the flight data show.
