# Profile: PSI-101 SAME-R

## Folders on PSI (from the PSI file listing; check against the page)

| Folder | Files | Size (MB, 1 MB = 1,048,576 bytes) |
| --- | --- | --- |
| Analyzed Data | 86 | 472.2 |
| Engineering Documents | 24 | 52.6 |
| Experimental table | 1 | 0.0 |
| Presentations | 4 | 31.8 |
| Raw Data | 223 | 5,453.5 |
| Reference Data | 2 | 0.6 |
| Reports | 1 | 4.4 |
| Science Documents | 2 | 0.9 |
| metadata | 1 | 0.0 |

## Experimental table and downloaded files

Run from the kit root and paste or append the output here:

```bash
python tools/profile_files.py "data/experimental_tables/PSI-101" --out "analysis/T3/PSI-101_same-r/profile.md"
python tools/profile_files.py "data/raw/PSI-101" --out "analysis/T3/PSI-101_same-r/profile.md"   # after downloading
```

## Documents (PDF, presentations)

| File | Title | Pages | What it is for |
| --- | --- | --- | --- |

### data/experimental_tables/PSI-101/Experimental table/PSI-101_Experimental table_SAME-R.csv
- type: .csv; size: 5,674 bytes
- rows: 109 (data rows 2 to 110, header = row 1); fully empty rows: 0; duplicate rows: 0
- columns: 10

| Column | Empty cells | Example value |
| --- | --- | --- |
| Sample Type | 0 | Kapton |
| SAME Test # | 0 | 51 |
| Description | 0 | B.L. new formula |
| Date | 0 | 21-Jul |
| Inlet velocity (cm/s) | 0 | 8.1 |
| Rt/R0 | 0 | 1.38 |
| Duration (sec) | 41 | 60 |
| Primary aging time (sec) | 42 | 11 |
| Primary mixing time (sec) | 42 | 8 |
| Net aging time (sec) | 0 | 38 |

## Downloaded analyzed and raw data (profiled 2026-11-14 by tools/kitlib.read_source and openpyxl)

### data/raw/PSI-101/Analyzed Data/PSI-101_Analyzed Data_SAME, SAME-R_Results.xlsx
- type: .xlsx; size: 4,061,669 bytes; 43 sheets (rows x columns as Excel reports them):

| Sheet | Rows | Columns |
| --- | --- | --- |
| DBP | 43 | 87 |
| Pyrell R&T plots | 45 | 88 |
| Pyrell V plots | 78 | 87 |
| Lampwick R&T Plots | 60 | 88 |
| Lampwick V Plots | 60 | 87 |
| Silicone R&T plots | 97 | 88 |
| Silicone V plots | 73 | 87 |
| ICES 2012 Paper data table | 28 | 20 |
| AIAA 2012 Paper data table | 18 | 20 |
| Teflon R&T plots | 83 | 88 |
| Teflon V plots | 58 | 87 |
| Kapton R&T plots | 95 | 88 |
| Kapton V plots | 70 | 87 |
| IAASS Paper data table | 17 | 20 |
| 2012 ICESpaper Plots | 42 | 27 |
| Material Sort | 188 | 87 |
| Reduced data sheet | 177 | 21 |
| Reduced Data with ISS Det | 177 | 93 |
| REduced data mass weighted | 177 | 95 |
| REduced data MPASS | 177 | 92 |
| Reduced Data with STS Det | 177 | 93 |
| Combined Rslts Copy this sheet | 188 | 95 |
| Mass loss plots | 43 | 20 |
| D~T(C) | 1 | 1 |
| 3-tests Compar. | 166 | 101 |
| Flight-ground plot  | 39 | 20 |
| Drum 8-2012 | 159 | 82 |
| Gnd Verif. 8-2012 | 68 | 81 |
| DFischer data run number | 88 | 16 |
| SAME R Results | 174 | 94 |
| SAME1 Flight Tests 8-27-09 | 99 | 74 |
| SAME Ground Test Results | 80 | 53 |
| Material Sort 02122013 | 168 | 92 |
| Flow and Temp plots | 2 | 8 |
| detection June 14 | 295 | 105 |
| detection Mar 14 | 295 | 104 |
| Dust Trak flow data | 48 | 7 |
| Ground weight loss | 66 | 82 |
| DTrakratio plots | 1 | 1 |
| DFischer data row number 112013 | 88 | 11 |
| Moment Comparisons Jan 14 (2) | 178 | 95 |
| Moment Comparisons unagedJan 21 | 178 | 185 |
| Moment Comparisons  aged Jan 21 | 178 | 150 |

Sheet used for analysis: 'Reduced Data with ISS Det' (header on Excel row 2, one row per flight test, column 'Flight 1=same 2=sameR').
- data rows: 156 (Excel rows 3-158); rows with a material: 154

| Column | Empty cells |
| --- | --- |
| Flight 1=same 2=sameR, g=ground | 2 |
| Sample Type | 2 |
| SAME # | 2 |
| Description | 2 |
| Inlet Velocity (cm/sec) | 2 |
| Rt/R0 | 2 |
| Net Aging Duration | 6 |
| ISS Detector Scatter (volts) | 2 |
| STS Detector (volts) | 2 |
| STS Detector offset (volts) | 47 |
| M0 best Diameter | 3 |
| M1 (mm/cm^3) | 2 |
| Mpass_3rd offset and dilution corrected | 47 |
| DustTrak A (mg/m3) Mpass_2nd offset, dilution and Gain corrected | 47 |
| DustTrak A calibratred and corrected for dilution (mg/m3) | 156 |
| DustTrak B calibratred and corrected for dilution (mg/m3) | 3 |
| M1/M0 (micro-m)--AMD | 2 |
| Diameter of Average mass (micro-m) | 3 |
| MPASS 3/2 | 47 |
| Hatch Choate Sigma g | 9 |
| Hatch Choate Dg | 9 |
| Ion B Mment (mm/cm^3) | 47 |
| Sample Temperature C | 2 |
| Mass Loss mg | 22 |
| Yeild: Dust Trak mass/mass lostt | 2 |
| STS detector delta | 139 |

### data/raw/PSI-101/Raw Data/*HKPData*.csv (44 files, 27.7 MB)
- housekeeping time series per flight day; 98 columns, e.g. TimeString, TestNumber, ElapsedTestTime(Secs), GasPlumeTemperature(DegC), SampleResistance(Ohms), ISSDetectorScatterMeasurement(Volts), STSDetectorMeasurement(Volts), IonDetectorA/B, PTrakMeasurement(PtPerCC), DustTrakA/B (MgPerM3), MFCPressure(PSIA), SampleSidePressure[AT20](PSIA)
- pressures are hardware lines (MFC, GN2, vacuum, sample side), not the cabin atmosphere: pressure_kpa is left empty in the run table.
- not yet analysed (v2: detector response over time).
