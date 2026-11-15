# Concept notes (T3, Mahmoud Nadeem)

Five lines per concept, each with the source it was checked against.

## 1. Microgravity (general)
Microgravity is the condition in which people or objects appear to be weightless and float.
Gravity does not disappear: at the space station's height it is still about 90 % of its strength on Earth.
Objects float because the station and everything in it are in free fall around the Earth.
Without weight, hot gas does not rise and smoke is not carried up by buoyancy; it moves only with the air flow.
Source: NASA, "What Is Microgravity? (Grades 5-8)", https://www.nasa.gov/learning-resources/for-kids-and-students/what-is-microgravity-grades-5-8/ ; PSI-102 page, Hypothesis (absence of buoyancy-induced flows).

## 2. Smoke as an aerosol; particle size distribution
Smoke is an aerosol: tiny liquid or solid particles suspended in air.
A smoke sample has many sizes at once, described by a typical (mean) diameter, a spread and a number per cm3.
SAME and SAME-R report the first-moment / zeroth-moment mean diameter (M1/M0) and the geometric spread (sigma g).
NASA assumed a lognormal size distribution to turn instrument averages into these diameters (the moment method).
Source: PSI-101 results workbook, sheet 'Reduced Data with ISS Det', column headers; PSI-101 page, Approach (lognormal assumption, moment method).

## 3. Why smoke behaves differently without buoyancy
On Earth hot smoke rises and spreads quickly; in microgravity it stays near the source and moves only with the air flow.
NASA expected longer residence time and higher vapour concentration near the source, so particles grow larger.
Our data: smoke kept growing as it aged (F-T3-1) and weaker air flow gave larger particles for 3 of 5 materials (F-T3-2).
Larger particles may change how smoke detectors respond.
Source: PSI-102 page, Hypothesis; findings F-T3-1 and F-T3-2.

## 4. Spacecraft smoke detectors in this data
The ISS smoke detector has two channels in the data: light scatter and light obscuration (blocking).
SAME and SAME-R also logged ionization detectors (Ion A, Ion B) and a detector labelled STS.
In our data the scatter channel moved strongly, the obscuration channel barely moved (F-T3-18).
The scatter channel appears to reach the end of its range in about half the tests (F-T3-6, F-T3-15; range still to confirm).
Source: PSI-101 housekeeping files and results workbook column names; findings F-T3-6, F-T3-15, F-T3-18.

## 5. Particle counters and instrument limits
The P-Trak is a condensation nuclei counter that uses isopropyl alcohol and reports particles per cm3; the DustTrak reports mass concentration in mg/m3.
The P-Trak sees particles from 0.02 um to above 1 um, particles above 2.5 um are beyond its limit, and its maximum count is 500,000 particles/cm3.
The DustTrak covers 0.1 to 10 um.
A reading above the maximum (F-T3-22) is flagged, not used as a real value.
Source: PSI-47 page, Objectives; DAFT fact sheet pages 1-2; DAFT 30-day post-flight report pages 3 and 8.

## 6. Reading units and time series
Diameters are in micrometres (um) in the workbook; 1 um = 1000 nm.
Housekeeping files log every channel once per second (1 Hz) with the test number and elapsed time.
A response time is when a signal leaves its pre-heating baseline and stays away (definition in derived_hkp_numbers.json).
Instrument clocks can drift, so two logs cannot always be aligned second by second (F-T3-20).
Source: PSI-101 housekeeping CSV headers; DAFT 30-day post-flight report page 5.

## 7. Comparing groups with small samples
Many comparisons in T3 rest on 1 to 4 tests, so we report medians and ranges, not averages alone.
A paired comparison (same smoke before and after aging) is stronger than comparing different tests.
A pattern seen in 3 of 5 materials is a pattern, not a law.
Effects can be mixed: each material was heated to a different temperature (F-T3-3).
Source: findings F-T3-1 to F-T3-5 and their caveats.

## 8. Why SAME, SAME-R and DAFT must not be pooled blindly
SAME (2007) and SAME-R (2010) used partly different instruments: SAME-R replaced one diagnostic enclosure with M-pass.
At matching conditions SAME gave larger diameters in all 5 comparisons (F-T3-5).
DAFT tested the particle counter with dust, not smoke, so its numbers describe the instrument, not fire smoke.
Each flight is analysed separately and compared only at matching conditions.
Source: PSI-101 page, Approach; PSI-47 page, Objectives; finding F-T3-5.

## 9. From measurements to detection relevance
These tests measure smoke and detector signals; they do not test whether an alarm went off at a set threshold.
Detector timings reflect how the hardware carried smoke to each sensor, not how fast a detector reacts to a real fire (F-T3-16).
The data can show which conditions change particle size, which matters because detectors respond to size.
Claims about alarms need thresholds that are not in these tables.
Source: PSI-102 page, Hypothesis; finding F-T3-16; extra/limitations.md.
