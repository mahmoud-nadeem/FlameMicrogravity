# Flame in Freefall: team kit (v4)

Mohammed Tamer's prompt is the plan and his package standard is the rule. This kit only saves
time on the mechanical parts of that plan: getting the data, keeping every row traceable, logging
every change, checking the package and zipping it. It contains no analysis and no ideas: those are
yours. If Mohammed changes the standard, his announcement wins over anything written here.

## 0. Set up once

1. Python 3.10 or newer (on Windows tick "Add Python to PATH").
2. Unzip, open a terminal in the `flame-in-freefall-kit` folder (all commands below run from there).
3. `pip install -r requirements.txt`
4. Optional check that everything works: `python -m pytest -q`

## 1. Your folder already exists

| Track | Member | Folder | Records |
| --- | --- | --- | --- |
| T1 | Amr Morgan | `analysis/T1/` | PSI-26 BASS, PSI-25 BASS-II |
| T2 | Mohamed Shreif | `analysis/T2/` | PSI-98, PSI-99, PSI-100 SAFFIRE-I, II, III |
| T3 | Mahmoud Nadeem | `analysis/T3/` | PSI-102 SAME, PSI-101 SAME-R, PSI-47 DAFT / DAFT-2 |
| T4 | Mohammed Tamer | `analysis/T4/` | PSI-69 FLEX, PSI-68 FLEX-2, PSI-39 CFI, PSI-159 CFI-G |
| T5 | Khaled Adawi | `analysis/T5/` | PSI-20 BRE, PSI-22 E-FIELD, PSI-23 s-Flame, PSI-10 Flame Design |
| T6 | Mohamed Gamal | `analysis/T6/` | PSI-107 SPICE, PSI-106 SLICE, PSI-21 CLD |

Each record folder follows section 7.1: `card.json`, `profile.md`, `tables/`, `data_log.md`,
`findings.md`, `charts/`, `scripts/` (with `README.md` = run order). The track folder has
`notes/concepts.md`, `si_log.md`, `references.md` and `HANDOFF.md`. Work only in your own folder.

## 2. Phase by phase

**Phase 0: access and census**
- `card.json` is prefilled from the PSI API (the same data the page shows) and marked NOT checked.
  Open the page in `x_psi_page`, compare every field, correct what differs, read the version from
  the page, write objectives and approach in your own words, then fill `verified_on` and `verified_by`.
- In `references.md`, replace each `[replace ...]` line with the page's "Cite this Investigation" text.
- Experimental tables of all records are already in `data/experimental_tables/` (do not edit them).
- Download the processed data of your track (see the size first):
  ```bash
  python scripts/psi_fetch.py --datasets T3 --list-only
  python scripts/psi_fetch.py --datasets T3
  ```
  Use your track or surname. Files go to `data/raw/<PSI-ID>/` (outside `analysis/`), logged in
  `data/raw/manifest.csv`. Re-running resumes. The PSI server is shared by every team and is often
  slow: the downloader retries, skips what does not answer and tells you; run it again later.
  No raw video: BASS videos are a separate profile and need Mohammed's agreement.
  PSI-21 (CLD): only the `<test>_data.csv` and `<test>_mfcSetpoints.csv` files of every folder whose
  name ends with "Raw Data", saved in those same per-test folders as the PSI page shows them
  (`python scripts/psi_fetch.py --datasets cld`, about 1.4 GB).
- Documents (reports, science and engineering documents) are not in the downloader for most
  records: tick them on the PSI page and save them under `data/raw/<PSI-ID>/`.

**Phase 1: profile**
```bash
python tools/profile_files.py "data/experimental_tables/PSI-102" --out "analysis/T3/PSI-102_same/profile.md"
python tools/profile_files.py "data/raw/PSI-102" --out "analysis/T3/PSI-102_same/profile.md"
```
Rows, columns, empty cells, empty and duplicate rows for every table; for documents, open them and
fill the table in `profile.md` (title, pages, purpose). Units are not guessed: read them yourself.

**Phase 2: clean and standardise**
- Edit `scripts/run_table_map.yaml` in your record folder. It lists the exact source column names.
  You decide which column feeds which standard column, the unit conversion, constants (each with
  the reason: where you read it), and your outcome mapping table. Then:
  ```bash
  python tools/build_run_table.py "analysis/T3/PSI-102_same/scripts/run_table_map.yaml"
  ```
- What the tool guarantees: the 13 required columns in order; `source_file` = the PSI path;
  `source_row` = the line number in the file, or the row number in Excel, header = row 1 (so the
  first data row is 2) - exactly what Mohammed will open when he spot-checks; every original column
  kept as `raw_<name>`; values that are not plain numbers left empty and flagged, never guessed;
  suspicious values flagged in `notes`, never fixed; every change written to `data_log.md`.
- Other tables (analyzed data, xlsx sheets, txt logs): add a source with `header_row`, `sheet` or
  `sep`. Files the tool cannot read simply: write your own script in `scripts/`, use
  `scripts/psi_parsers.py` (FLEX, ACME, SAME readers) and log your changes by hand.

**Phases 3 and 4: describe, baseline**
Your own scripts go in `scripts/` and in the run order of `scripts/README.md`. Charts go in
`charts/` with a one-line caption naming the source file. Findings, one line each, in `findings.md`:
`F-T3-1 | statement | OBSERVED IN DATA | <source file> | <rows or page> | high/medium/low | caveat`.

**Phase 5: model gate**
Copy `tools/templates/model_README.md` (gate passed) or `tools/templates/no_model.md` (gate failed)
into `model/` of the record.

**Phases 6 and 8: package**
```bash
python tools/self_check.py T3            # writes analysis/T3/SELF_CHECK.md (items 1-10 of 7.6)
python tools/package.py T3 --version 1   # self-check + T3_nadeem_v1.zip with analysis/T3 only
```
Paste SELF_CHECK.md into HANDOFF.md, fill the rest of HANDOFF.md, send the zip and your status line.
PASS / FAIL / WARN / MANUAL: item 9 (re-run from scratch) and the truth of si_log are yours to
confirm. A FAIL does not block the zip: late is better than missing, but say it in HANDOFF.md.
Using git instead: copy `analysis/<track>/` into the team repository on branch `track/<surname>`.

**New ideas**: write them yourself, then use `tools/templates/idea_ticket.md`.

## 3. AI disclosure

The kit tools were written by Mahmoud Nadeem with an AI assistant (Claude). Your `si_log.md` has a
prefilled line saying so; keep it if you use the kit. `references.md` lists the kit and the
open-source libraries. Card fields prefilled from the PSI API stay unconfirmed until you check them.
