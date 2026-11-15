# Source-linked findings — PSI-23

Each entry: ID | statement | evidence label | source | exact row/page | confidence | caveat.

F-T5-16 | The s-Flame summary contains 18 Test Day rows with 276 ignitions recorded in total. | OBSERVED IN DATA | PSI-23_Experimental table_ACME s-Flame.csv | rows 2-19, Flames Ignited* | high | The total is a sum over summary records, not raw files or an independently audited NASA success metric.
F-T5-17 | s-Flame has 10 first-round summary days with 152 ignitions and 8 second-round days with 124 ignitions. | OBSERVED IN DATA | PSI-23_Experimental table_ACME s-Flame.csv | rows 2-11 and 12-19, Test Type and Flames Ignited* | high | The groups differ in fuel/diluent configurations; their totals are not causal comparisons.
F-T5-18 | The s-Flame table includes source strings such as N3, N4, N5 and N6 in atmosphere/fuel descriptions. | OBSERVED IN DATA | PSI-23_Experimental table_ACME s-Flame.csv | rows 3-10, Atmosphere* and Fuel Bottle | high | Unusual source strings may be transcription issues but are retained verbatim and not reinterpreted as N2.
F-T5-19 | NASA describes s-Flame as investigating spherical diffusion flame structure, extinction and instabilities. | REPORTED BY NASA OR A PUBLICATION (NASA Science: s-Flame) | https://science.nasa.gov/biological-physical/investigations/s-flame/ | Science Objectives and Experiment Description | high | These research objectives do not establish observed extinction from the summary CSV.

Confidence describes confidence in the **stated observation/source transcription**, not the scientific strength of a causal claim.
