# PSI-20 BRE — General descriptive EDA

## OBSERVED IN LOCAL FILES
- Experimental summary: **18 day-level rows**, **194 flames ignited** in total, range **0–21** per day, median **10** and mean **10.78**. Source: `PSI-20_Experimental table_ACME BRE.csv`, data rows 2–19 (CSV header is row 1).
- Largest day-level counts: 2020-12-05 (21) [CSV row 13], 2020-12-04 (18) [CSV row 14], 2020-12-23 (17) [CSV row 17]. These are CSV dates, not independently corrected NASA operational dates.
- Fuel labels (display-only whitespace grouping): 100%C2H4: 11 days, 100%CH4: 2 days, 50%C2H4: 5 days. Source: CSV rows 2–19. This is descriptive grouping, not condition attribution to individual flames.
- Oxygen concentration entries are lists of approximate conditions on each day, not per-flame settings. CSV row 6 contains `3400%`; row 9 contains `2100%`. Both are retained, excluded from any numeric oxygen analysis. Source: `PSI-20_Experimental table_ACME BRE.csv` rows 6 and 9; see Task 04C reconciliation.
- Run `19056A2`: **31,316 measurement rows**, 36 channels including `Time`. Source: `19056A2_data.csv`, CSV metadata row 1, header row 2, data rows 3–31318.
- Raw time labels: **1 gaps >=1 s**, largest **123.034 s**; **1 negative time steps**. Source: raw `Time` column; gap interval from data rows 1939 to 1940 if present. Clock synchronization and timezone unverified.

## Selected raw-channel statistics

| Channel | Numeric samples | Missing/non-numeric | Min | Median | Max |
|---|---:|---:|---:|---:|---:|
| IonCurrent | 31,316 | 0 | -1.03299 | 3.79148 | 3.82757 |
| PMT1 | 31,316 | 0 | -0.00080109 | 0.868839 | 4.56777 |
| MFCA3FuelFlow | 31,316 | 0 | -0.156518 | 4.98083 | 5.10374 |

Source: `19056A2_data.csv`, named columns, measurement data rows 3–31318. Values are raw channel values; physical units and calibration not established.

## REPORTED BY NASA
NASA ACME/BRE Final Report (2022) PDF pages **110 and 116** report **194 flames ignited**; pages **29 and 127** state **196 successful ignitions** (page 127 invokes Round 2). The apparent difference in definitions/scope remains unresolved. NASA report page **23** corrects Test Day 19094 to 4 April 2019.

## OUR INFERENCE / limitations
A day-level total of 194 is numerically consistent with the NASA 194 statements, but not proof of identical definitions. The one available raw-run pair does **not** establish NASA-wide run coverage. A raw signal trace shows variation and a recording gap, not flame stability, extinction, or causal relationships.

## Source integrity
- Experimental CSV SHA-256: `4aa5d3f98708ceacced5c620d46858b9965f8d4d941b203229f46467d53e5ab7`
- Raw CSV SHA-256: `9b90a1c2b0c227823df193ba0a070d07bb30e42077fb0534ca38bc47687dad49`
- Original source files were read only; no values modified.
