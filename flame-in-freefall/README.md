# Flame in Freefall — data pipeline and contribution repo

NASA Space Apps 2026, challenge "Flame in Freefall". An SI-powered dashboard that summarises, ranks
and interprets the combustion investigations in NASA's Physical Sciences Informatics (PSI) repository.

This repo holds everything except the website code: the content members contribute, the schemas
that check it, and the Python pipeline that merges it with PSI data into `site_data/*.json`,
the only files the website reads.

## Quick start

```bash
pip install -r requirements.txt
python -m pipeline.build_catalog      # PSI metadata + experimental tables for all combustion investigations
python -m pipeline.build              # validate -> envelope -> rank -> export site_data/
python -m pytest -q tests             # 41 tests
```

If `build_catalog` cannot reach the PSI API from Python, use the browser fallback:
open https://psi.nasa.gov/physci/repo/search?q=combustion, paste `tools/psi_browser_export.js`
into the DevTools console, then `python -m pipeline.import_bundle psi_catalog_bundle.json`.

New team member? Start with `GETTING_STARTED.md`. To contribute, read `CONTRIBUTING.md`.

## Layout

| Path | What it is |
| --- | --- |
| `content/members/` | One YAML per team member |
| `content/scenarios/` | Habitat atmospheres from the challenge text (Earth, Moon base, spacesuit) |
| `content/investigations/<PSI-ID>/` | `psi.json` (generated, do not edit) + `card.yaml` (curated by a member) + `si.json` (SI drafts) |
| `content/findings/` | Findings as Markdown with front matter |
| `content/models/<id>/` | Model cards and exported predictions |
| `schemas/` | JSON Schemas the validator enforces |
| `templates/` | Starting points for every contribution type |
| `pipeline/` | `build_catalog`, `import_bundle`, `validate`, `envelope`, `rank`, `export_site`, `build` |
| `scripts/` | `psi_fetch.py` (download processed data for modeling), `psi_parsers.py` (file quirks) |
| `tools/psi_browser_export.js` | Browser fallback for the catalog |
| `data/experimental_tables/` | PSI experimental tables (small CSVs) |
| `data/derived/` | Envelope points, scenario coverage, ranking |
| `site_data/` | What the website reads |

## Pipeline steps

| Step | Command | Output |
| --- | --- | --- |
| Catalog | `python -m pipeline.build_catalog` | `content/investigations/*/psi.json`, `data/experimental_tables/` |
| Validate | `python -m pipeline.validate` | OK or a list of file:field problems |
| Envelope | `python -m pipeline.envelope` | `data/derived/envelope_points.csv`, `scenario_coverage.json` |
| Rank | `python -m pipeline.rank` | `data/derived/ranking.json` |
| Export | `python -m pipeline.export_site` | `site_data/*.json` |
| All | `python -m pipeline.build [--fetch]` | everything above, stops at the first failure |

## Model data

`scripts/psi_fetch.py` downloads only processed results and telemetry (the raw archives are terabytes).
Each team track has a profile group; see `GETTING_STARTED.md` for sizes.

```bash
python scripts/psi_fetch.py --datasets t4 --list-only        # size of a track, no download
python scripts/psi_fetch.py --datasets t4                    # or a member id: tamer, adwi, ...
```

## Status (14 Nov 2026)

- The Python client ran live on 14 Nov evening: metadata for all 24 investigations and 22 experimental tables.
- Envelope headline numbers were computed from the real tables in the browser; re-running
  `pipeline.envelope` on downloaded tables should reproduce them (20 ambient tests inside the
  Moon-base envelope, all CFI-G).

## Data credit and SI disclosure

Data: NASA Physical Sciences Informatics. Cite each investigation by its DOI (in `psi.json`).
All selected investigations are CC0 except PSI-10, whose license field is empty.
Code in this repo was written with AI assistance (Claude); see the project page's SI section.

## Team member kit

Team members work with Mohammed Tamer's package standard. Build their kit (download, parsers,
track folders, run-table builder, self-check, packager) with:

```bash
python tools/build_member_kit.py --version 4
```

It is assembled in a temporary folder, its tests run there, and the zip is written next to this repository.
