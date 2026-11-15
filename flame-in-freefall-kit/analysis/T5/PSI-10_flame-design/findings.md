# Source-linked findings — PSI-10

Each entry: ID | statement | evidence label | source | exact row/page | confidence | caveat.

F-T5-1 | The two PSI-10 experimental tables contain 327 test-table entries: 207 normal and 120 inverse. | OBSERVED IN DATA | PSI-10_Experimental table_Flame Design_Normal Flame.csv + PSI-10_Experimental table_Flame Design_Inverse Flame.csv | normal rows 2-208; inverse rows 2-121 | high | Entry counts are not successful ignition counts.
F-T5-2 | The normal-flame table lists C2H4 in 187 entries and C3H8 in 20 entries. | OBSERVED IN DATA | PSI-10_Experimental table_Flame Design_Normal Flame.csv | rows 2-208, Fuel | high | The inverse table has no explicit Fuel column and is excluded from this fuel breakdown.
F-T5-3 | The PSI-10 conditions tables do not include a verified flame-extinction outcome for each test. | OBSERVED IN DATA | PSI-10_Experimental table_Flame Design_Normal Flame.csv + PSI-10_Experimental table_Flame Design_Inverse Flame.csv | both CSV headers (row 1) | high | No classification or success rate can be computed from these tables.
F-T5-4 | Normal versus inverse oxygen percentages refer to different source fields and must not be pooled as a single comparable metric. | OUR INFERENCE | PSI-10_flame-design_runs_clean.csv | rows 2-328, notes and oxygen_pct | high | Normal uses initial chamber XO2 and inverse uses oxidizer-stream XO2; this is a semantic constraint.
F-T5-5 | NASA describes Flame Design as an investigation of soot control and oxygen-enriched non-premixed flames. | REPORTED BY NASA OR A PUBLICATION (NASA Science: Flame Design) | https://science.nasa.gov/biological-physical/investigations/flame-design/ | Science Objectives and Experiment Description | high | These are investigation aims, not outcomes demonstrated by these CSVs.

Confidence describes confidence in the **stated observation/source transcription**, not the scientific strength of a causal claim.
