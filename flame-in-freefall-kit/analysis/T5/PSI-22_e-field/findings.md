# Source-linked findings — PSI-22

Each entry: ID | statement | evidence label | source | exact row/page | confidence | caveat.

F-T5-11 | The E-FIELD table contains 32 physical data rows but only 21 rows with an ignition count. | OBSERVED IN DATA | PSI-22_Experimental table_ACME E-FIELD Flames.csv | rows 2-33; Flames Ignited column | high | 11 rows are supplemental/continuation entries, not zero-ignition test days.
F-T5-12 | The 21 count-bearing E-FIELD rows sum to 230 entries as printed, but represent only 20 distinct Test Day IDs. | OBSERVED IN DATA | PSI-22_Experimental table_ACME E-FIELD Flames.csv | rows 2-33, Test Day and Flames Ignited | high | Test Day 18319 is repeated verbatim on rows 26 and 30; 230 is not a validated unique-day total.
F-T5-13 | Both appearances of Test Day 18319 list 11 flames ignited, so double-counting cannot be ruled out. | OBSERVED IN DATA | PSI-22_Experimental table_ACME E-FIELD Flames.csv | rows 26-33 | high | Do not assume whether the repetition is intentional or a duplicate; do not silently deduplicate.
F-T5-14 | E-FIELD source entries distinguish coflow and gas-jet test rounds and recorded mesh polarities. | OBSERVED IN DATA | PSI-22_Experimental table_ACME E-FIELD Flames.csv | rows 2-33, Test Type and Mesh Polarity | high | Categories describe test setup; they do not establish an electric-field causal effect.
F-T5-15 | NASA describes E-FIELD as examining field-driven ion transport and flame responses in microgravity. | REPORTED BY NASA OR A PUBLICATION (NASA Science: E-FIELD Flames) | https://science.nasa.gov/biological-physical/investigations/e-field-flames/ | Science Objectives and Experiment Description | high | No numerical voltage-current relationship is calculated from this day-level table.

Confidence describes confidence in the **stated observation/source transcription**, not the scientific strength of a causal claim.
