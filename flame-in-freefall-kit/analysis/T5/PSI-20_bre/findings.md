# Source-linked findings — PSI-20

Each entry: ID | statement | evidence label | source | exact row/page | confidence | caveat.

F-T5-6 | The PSI-20 summary table contains 18 date-level records totaling 194 flames ignited. | OBSERVED IN DATA | PSI-20_Experimental table_ACME BRE.csv | rows 2-19, Flames Ignited | high | Counts represent recorded summary days, not 194 individual raw-run files.
F-T5-7 | The 18 recorded ignition counts range from 0 to 21 per day and have mean 10.78 and median 10. | OBSERVED IN DATA | PSI-20_Experimental table_ACME BRE.csv | rows 2-19, Flames Ignited | high | Summary days may aggregate multiple flames and have known date discrepancies.
F-T5-8 | The local 19056A2 data file contains 31,316 samples and a 123.034-second timestamp gap. | OBSERVED IN DATA | 19056A2_data.csv | metadata/header rows 1-2 and data rows 3-31318, Time | high | One raw run is not representative of all PSI-20 runs; clock sync unverified.
F-T5-9 | NASA Final Report references 194 flames ignited and 196 successful ignitions in different passages. | REPORTED BY NASA OR A PUBLICATION (ACME BRE Final Report 2022) | BRE_final_report_20220201.pdf | PDF pp. 29, 110, 116, 127 | high | Different wording or scope is not reconciled; do not equate the totals.
F-T5-10 | Two PSI-20 CSV date entries and two oxygen entries differ from the final report and must remain source-preserved. | OBSERVED IN DATA | PSI-20_Experimental table_ACME BRE.csv + BRE_final_report_20220201.pdf | CSV rows 6, 9, 13-14; NASA PDF p. 24; 04C cross_source_discrepancies.csv | high | Do not silently normalize 3400%/2100% or replace calendar dates in original CSV.

Confidence describes confidence in the **stated observation/source transcription**, not the scientific strength of a causal claim.
