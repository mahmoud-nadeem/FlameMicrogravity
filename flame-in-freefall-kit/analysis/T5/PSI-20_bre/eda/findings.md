# Presentation findings

1. **OBSERVED IN LOCAL FILES:** 18 summary days contain 194 recorded flames ignited; day-level counts range from 0 to 21. Source: `PSI-20_Experimental table_ACME BRE.csv`, rows 2–19. See Charts 1–2.
2. **OBSERVED IN LOCAL FILES:** The largest recorded day is CSV 2020-12-05 with 21 ignitions (CSV row 13); NASA Table 1 lists Test Day 20279 as 2020-10-05, also 21. This is a source-date discrepancy, not an authorized correction. Source: experimental CSV row 13; NASA Final Report PDF page 24; Task 04C cross-source report.
3. **OBSERVED IN LOCAL FILES:** Fuel-bottle categories vary across summary days, but the summary table does not link individual flames to unique oxygen settings. Source: experimental CSV rows 2–19, `Fuel Bottle` and `Oxygen Conc (percent)` columns. See Chart 3.
4. **OBSERVED IN LOCAL FILES:** Run `19056A2` has 31,316 raw samples and a 123.034-second timestamp gap. The plotted channels vary over time; raw units are unspecified. Source: `19056A2_data.csv`, metadata/header rows 1–2, `Time`, `IonCurrent`, `PMT1`, `MFCA3FuelFlow` columns. See Chart 4.
5. **REPORTED BY NASA:** Final Report PDF pages 110 and 116 say 194 flames ignited, whereas pages 29 and 127 mention 196 successful ignitions. **OUR INFERENCE:** the discrepancy remains unresolved; the figures must not be treated as equivalent counts.
