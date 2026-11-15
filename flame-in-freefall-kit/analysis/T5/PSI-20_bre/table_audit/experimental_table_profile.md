# PSI-20 BRE experimental table — source-preserving profile

## OBSERVED IN LOCAL FILES
- Source: `PSI-20_Experimental table_ACME BRE.csv`; SHA-256 `4aa5d3f98708ceacced5c620d46858b9965f8d4d941b203229f46467d53e5ab7`
- Table records: **18**; columns: **8**; distinct parsed calendar days: **18**
- Sum of valid integer `Flames Ignited` cells: **194** (18 cells). This is not a raw run count.
- Source header: `["Year", "Month", "Date", "Burner Size (mm)", "Fuel Bottle", "Oxygen Conc (percent)", "Flames Ignited", "Notes"]`
- Units are only those literally in column labels: `Burner Size (mm)` and `Oxygen Conc (percent)`; no physical conversion performed.
- Source notes describe oxygen concentrations as approximate and chamber pressure variations as omitted.
- Source notes state the day counts neglect the day change on ISS.

## Missing values (including optional Notes)
- `Year`: 0
- `Month`: 0
- `Date`: 0
- `Burner Size (mm)`: 0
- `Fuel Bottle`: 0
- `Oxygen Conc (percent)`: 0
- `Flames Ignited`: 0
- `Notes`: 16

## Raw-value distributions (no normalization)
### Year
- `"2019"`: 9
- `"2020"`: 7
- `"2021"`: 2
### Month
- `"April"`: 2
- `"Dec"`: 5
- `"Feb"`: 3
- `"Jan"`: 2
- `"March"`: 4
- `"Oct"`: 1
- `"Sept"`: 1
### Date
- `"1"`: 1
- `"11"`: 2
- `"17"`: 2
- `"20"`: 2
- `"23"`: 1
- `"25"`: 1
- `"28"`: 2
- `"3"`: 1
- `"4"`: 3
- `"5"`: 1
- `"7"`: 1
- `"8"`: 1
### Burner Size (mm)
- `"25"`: 16
- `"50"`: 2
### Fuel Bottle
- `"100% C2H4"`: 8
- `"100% CH4"`: 2
- `"100%C2H4"`: 3
- `"50% C2H4"`: 5
### Oxygen Conc (percent)
- `"2100%"`: 1
- `"21; 26.5; 34"`: 2
- `"21; 26.5; 34; 40"`: 1
- `"21; 26.5; 40"`: 1
- `"25; 34; 40"`: 4
- `"25; 40"`: 2
- `"26.5; 34"`: 4
- `"26.5; 40"`: 1
- `"3400%"`: 1
- `"34; 40"`: 1
### Flames Ignited
- `"0"`: 1
- `"10"`: 2
- `"12"`: 1
- `"13"`: 3
- `"15"`: 1
- `"17"`: 1
- `"18"`: 1
- `"21"`: 1
- `"6"`: 2
- `"7"`: 1
- `"8"`: 3
- `"9"`: 1
### Notes
- `""`: 16
- `"Flames Ignited is the number ignited on that day (neglecting the day change on ISS)."`: 1
- `"Oxygen Conc. (as diluted with nitrogen on a volume basis) was varied between tests where approximate concentrations for tests that ignited are listed. The chamber pressures were also varied but are not identified in this summary table."`: 1

## Suspicious raw values
- `3400%` and `2100%` occur in `Oxygen Conc (percent)` and exceed 100 when read literally. These are preserved unchanged; intended meaning unknown.
- `100%C2H4` and `100% C2H4` differ in spacing; no canonicalization.
- Month abbreviations and full month names coexist.
- Summary rows are not strictly chronological (2020 Dec 5 precedes Dec 4).

## OUR INFERENCE
- The percent strings warrant documentation review; do not assume decimal or formatting correction.
- Date-only matching cannot identify which flame ignition corresponds to which raw run.

## REPORTED BY NASA
- No independent report-page comparison was performed. The uploaded table is attributed to the NASA starter kit by the user; this provenance has not been independently authenticated.
