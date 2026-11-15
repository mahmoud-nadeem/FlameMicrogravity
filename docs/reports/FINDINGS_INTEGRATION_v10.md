# Crew findings integrated in v10: Mohamed Shreif (T2), Mohammed Tamer (T4), Mohamed Gamal (T6)

Source folder: `Findings/` (left as received). Rules followed: only measured or computed results become findings; objectives,
methods, recommendations and general explanations do not. Labels follow each author's own tags. Nothing provisional is
marked as verified, and no result was added that the authors did not report.

## Where each contribution went

| Contributor | Source file(s) in `Findings/` | Integrated into (kit `flame-in-freefall-kit/analysis/`) | Findings |
| --- | --- | --- | --- |
| Mohamed Shreif (T2) | `SAFFIRE_Findings.zip` → `PSI-98_saffire-i/findings.md`, `PSI-99_saffire-ii/findings.md`, `PSI-100_saffire-iii/findings.md` | `T2/PSI-98_saffire-i`, `T2/PSI-99_saffire-ii`, `T2/PSI-100_saffire-iii` (copied as delivered, already in team format) | F-T2-9801, 9802; F-T2-9901 to 9909; F-T2-10001, 10002 (13) |
| Mohammed Tamer (T4) | `FLEX_analysis_findings.txt` (analysis pack v2, 15 FINDING sections) | `T4/PSI-69_flex/findings.md` (transcribed), `T4/extra/limitations.md` | F-T4-6901 to 6923 (23) |
| Mohamed Gamal (T6) | `findings_and_analysis.txt`; `gamal.zip` (finding notes, PSI-106/107 cards); `card.yaml` (newer PSI-21 card) | `T6/PSI-106_slice`, `T6/PSI-107_spice`, `T6/PSI-21_cld` findings.md (transcribed), `T6/extra/limitations.md`, card `approach` fields | F-T6-10601 to 10607, F-T6-10701 to 10708, F-T6-2101 to 2106 (21) |

On the site these appear in: the Research evidence table (filter by track/experiment/label, CSV download), each experiment
page and each crew planet (findings count, evidence step of the planet tour), the Results page (five charts, below), and the
Ask-the-crew assistant (every finding with its caveat is in the assistant's knowledge base, answered by its owner).

Label mapping for Tamer: `[CALC]` → OBSERVED IN DATA; `[SRC]` → REPORTED BY NASA OR A PUBLICATION; `[INF]` and `[CALC/INF]`
→ OUR INFERENCE; `[FLAG]` items → caveats and limitations. Gamal's computed numbers → OBSERVED IN DATA; his gas-code reading
(21-F2) → OUR INFERENCE (see conflicts). Confidence is "not stated" where the author gave none (Tamer throughout; Gamal except
the two finding notes that say "high").

## Results charts (numbers transcribed from the findings; each chart cites them)

| Chart | Findings | Source numbers |
| --- | --- | --- |
| SAFFIRE: highest post-igniter readings per sample (sample-group and plume thermocouples, °C) | F-T2-9801/9802, 9901-9909, 10001/10002 | Shreif's findings.md |
| FLEX: share of tests ending in disruption by O2 | F-T4-6905 | 0/48, 2/67, 20/91, 39/68 (re-checked against the PSI-69 table: match) |
| FLEX: mean Dext/D0 vs O2, methanol and heptane (1 atm, N2) | F-T4-6907 | Tamer's FINDING 4 table |
| SLICE: measured peak velocity vs fan calibration u2 (2009 scans) | F-T6-10606, 10604 | Gamal's 106-F5 table |
| SPICE: flames by fuel and nozzle (147 flames) | F-T6-10702 | Gamal's 107-F1 table |

## Checks made against the NASA tables in the kit

- Tamer, PSI-69 (274 rows): fuels 157/117; outcomes 186/61/27 and per-fuel splits; O2 range 0.12–0.34; diluent counts;
  disruption by O2 bin; 85 rows without a usable extinction diameter: all match. Pressure ~0.7 atm: 104 rows in the table
  against his 103; the difference is test 114 (0 mmHg), which he flags as suspect.
- Gamal: SPICE 469 rows with 34 exact duplicates, SLICE 12 test days, CLD 32 test days and 344 flames ignited: all match.
  His SLICE workbook and CLD test-point summary (`cld_testpoints.csv`) are not in the project, so those numbers were not re-run.
- Shreif: the SAFFIRE sensor workbooks he cites (e.g. `PSI-98_Raw Data_Saffire-I Sample 1 Sensor Data Complete TM graphs.xlsx`)
  are not in the project, so his readings were integrated as delivered and not re-checked.

## Conflicts and how attribution was kept

1. **PSI-21 fuel claims (Gamal 21-F2, 21-F3).** His per-fuel table lists every test point as "not in experiment table": his join
   to the NASA experiment table failed, although these test days (17319, 17324, … 21062) are in that table. So the gas-code
   pattern (21-F2) is kept as OUR INFERENCE with that caveat, and the "ethylene flames radiate more than methane" part of 21-F3
   is not presented as a finding (the caveat of F-T6-2102 explains why). The campaign-wide correlation in 21-F3 is kept.
2. **SPICE fuel-rate steps.** His earlier note (`spice-fuel-rate-steps.md`) read the rate changes as stepping up to the smoke
   point; his later 107-F3 says the table alone does not support that. 107-F3 is used; the revision is stated in F-T6-10704.
3. **Two PSI-21 cards.** The card in `gamal.zip` describes one test point; `Findings/card.yaml` describes 385 and matches his
   findings. The newer card is used; the method field holds no result numbers.
4. **FLEX planned envelopes.** Tamer notes that three planning documents and a slide give different envelopes and suppressant
   lists; the limitation says to name the document a range came from.

## Not turned into findings (by design)

Tamer's recommendations and "suggested dashboard views", Gamal's "how computed" notes, investigation-card summaries
(used only as each experiment's *approach* text), and all `[FLAG]` items (kept as caveats and limitations).

## Khaled Adawi (T5), final package (v10.2)

`Khaled_T5_FINAL_INTEGRATION.zip` (kept locally in `Important/`, not published) is merged into `flame-in-freefall-kit/analysis/T5/`:
19 findings in his own words and format, F-T5-1 to F-T5-19, confidence high, replacing the earlier 6-line transcription of his
PSI-20 EDA. Re-checked against the NASA tables: PSI-10 207 normal + 120 inverse entries (C2H4 187, C3H8 20); PSI-20 18 days,
194 ignitions, 0-21 per day, mean 10.78, median 10; PSI-22 32 rows, 21 with counts, sum 230 over 20 distinct days, Test Day
18319 on rows 26 and 30 (11 each); PSI-23 18 days, 276 ignitions (10 days / 152 and 8 days / 124): all match. F-T5-5, 15 and 19
state NASA's aims for each investigation (label REPORTED, caveat says they are not results). Not merged: his optional
`rag_chunks.jsonl` seed (his full ACME corpus is already exported).

## Remaining gaps (exact)

- **T4 PSI-68 FLEX-2, PSI-39 CFI, PSI-159 CFI-G:** no findings supplied (only PSI-69 is covered by Tamer's file).
- **Tamer's analysis pack v2** (`CompleteTamerRAGChunks_plus_FLEX_analysis`, chunks FLEXA-01 to FLEXA-29) and
  **`FLEX_flight_tests_clean.csv`** are cited but not supplied; his numbers were checked against the PSI-69 table instead.
- **Gamal's scripts, `cld_testpoints.csv` and the SLICE boundary-condition workbook** are not supplied; SLICE units are
  assumed (cm/s, mm) by him and stated so.
- **SAFFIRE raw sensor workbooks** (PSI-98/99/100 `Raw Data`) are not in the project; Shreif's readings are unverified here.
- **No track paragraph or test questions** for T2, T4, T6 (`extra/track_paragraph.md`, `extra/test_questions.md`); the
  assistant answers "what is your part about" from the role and the list of findings instead.
- **No T2 limitations file;** Shreif's caveats are per finding only.
- **No result files for flames themselves** in T6 (SLICE flame images, SPICE smoke points, CLD video): the T6 findings are
  about airflow, test conditions and sensor records, and say so.

## Team validator (`flame-in-freefall-kit/tools/self_check.py`, reports in `analysis/T2|T4|T6/SELF_CHECK.md`)

- Item 4 (every finding has source, row or page, and label): **T2 passes**. T4 and T6 fail **only** because the validator
  requires confidence `high`, `medium` or `low` and the authors did not state one (all 23 T4 lines; 19 of 21 T6 lines). The
  integrator did not invent confidence levels: Tamer and Gamal should add them.
- Items 6 and 10 fail for all three tracks for reasons that predate this round: `references.md` still has the template's
  `[replace ...]` placeholders, and the cards are not yet checked against the PSI pages (`verified_by`/`verified_on`
  empty, `objectives` TODO). The site shows these records as "not yet checked against the PSI page".
