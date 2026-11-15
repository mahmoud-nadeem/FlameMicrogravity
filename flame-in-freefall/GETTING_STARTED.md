# Getting started (team members)

> Superseded on 2026-11-14 (evening) for team members: the team follows Mohammed Tamer's package
> standard, and the member kit (`tools/START_HERE.md`, built with `python tools/build_member_kit.py --version N`)
> replaces this guide. This file describes the integration repository only.


Everything you need is in this folder: the data downloader, the file templates, and the checker
that tells you whether your work is ready to hand over.

## 1. Set up once

1. Install Python 3.10 or newer (python.org). On Windows, tick "Add Python to PATH".
2. Unzip this folder and open a terminal inside it (Windows: right-click in the folder, "Open in Terminal").
3. Install the libraries:

```bash
pip install -r requirements.txt
```

## 2. Download only the data of your track

The PSI archives are terabytes of images. You only need the processed results and telemetry,
which the downloader picks for you. First see the size, then download:

```bash
python scripts/psi_fetch.py --datasets t4 --list-only    # shows files and total size, downloads nothing
python scripts/psi_fetch.py --datasets t4                # downloads into data/raw/<PSI-ID>/
```

Use your track (`t1`..`t6`) or your member id instead of `t4`:

| Track | Member id | Investigations | Download size |
| --- | --- | --- | --- |
| t1 | `morgan` | BASS PSI-26, BASS-II PSI-25 (tables and proof sheets) | about 0.1 GB |
| t2 | `shreif` | SAFFIRE-I, II, III PSI-98, 99, 100 | about 0.4 GB |
| t3 | `mahmoud` | SAME PSI-102, SAME-R PSI-101, DAFT PSI-47 | about 0.3 GB |
| t4 | `tamer` | FLEX PSI-69, FLEX-2 PSI-68, CFI PSI-39, CFI-G PSI-159 | about 2.1 GB |
| t5 | `adwi` | BRE PSI-20, E-FIELD PSI-22, s-Flame PSI-23, Flame Design PSI-10 | about 4.7 GB |
| t6 | `gamal` | SPICE PSI-107, SLICE PSI-106, CLD PSI-21 | about 1.4 GB |

- Raw video is not downloaded unless Mohammed Tamer agrees. The BASS videos (34 files, about 1.1 GB)
  are a separate profile: `python scripts/psi_fetch.py --datasets bass-video --list-only`.
- The download resumes if it stops: run the same command again.
- The PSI server is shared by every Space Apps team and is sometimes busy (HTTP 500, long waits).
  The downloader retries each request, skips an investigation that still does not answer and tells you.
  Run the same command again later: it only fetches what is still missing.
- Every file is logged in `data/raw/manifest.csv` with its status (`ok`, `exists`, `missing`, `error`).
  `missing` means PSI lists the file but it is not in storage: note it and continue.
- Limit a big download: `--max-files 50` (per investigation) or `--max-mb 20` (skip larger files).
- The experimental tables of all 24 investigations are already in `data/experimental_tables/`,
  and their metadata in `content/investigations/<PSI-ID>/psi.json`.

## 3. Read the files

`scripts/psi_parsers.py` already handles the file quirks:

```python
import sys; sys.path.insert(0, "scripts")
from psi_parsers import read_flex_series, read_flex_testsheet, read_acme_csv, read_same_results

meta, df = read_acme_csv("data/raw/PSI-159/Raw Data/...._data.csv")   # ACME sensor logs (36 channels)
```

## 4. Write your work in the shared format

| What | Copy from | To |
| --- | --- | --- |
| Investigation card | `templates/card.yaml` | `content/investigations/<PSI-ID>/card.yaml` |
| Finding | `templates/finding.md` | `content/findings/<short-name>.md` |
| Model card | `templates/model.yaml` | `content/models/<model-id>/model.yaml` |

Never edit `psi.json`: it is regenerated from NASA's API.

## 5. Check, then hand over

```bash
python -m pipeline.validate
```

When it prints `OK`, send only the files you added or changed under `content/` to the integrator
(or push a branch). See `CONTRIBUTING.md` for the rules.
