# References — T5

## NASA PSI datasets (DOI citation text, constructed from archived NASA metadata)

The following are reproducible DOI-style data citations, **not verbatim** text copied from the interactive “Cite this Investigation” menu (its text was inaccessible to this review). Each DOI should be retained in the submission References field.

- NASA Physical Sciences Informatics (PSI). *Advanced Combustion via Microgravity Experiments / Flame Design* (PSI-10). Dataset/investigation record. https://doi.org/10.60555/w4zy-bt45 . Investigation: https://psi.nasa.gov/physci/repo/data/investigations/PSI-10 (metadata cross-checked 2026-11-15).
- NASA Physical Sciences Informatics (PSI). *Advanced Combustion via Microgravity Experiments - Burning Rate Emulator* (PSI-20). Dataset/investigation record. https://doi.org/10.60555/vb93-3y72 . Investigation: https://psi.nasa.gov/physci/repo/data/investigations/PSI-20 (metadata cross-checked 2026-11-15).
- NASA Physical Sciences Informatics (PSI). *Advanced Combustion via Microgravity Experiments Electric-Field Effects on Laminar Diffusion Flames* (PSI-22). Dataset/investigation record. https://doi.org/10.60555/se5a-8c73 . Investigation: https://psi.nasa.gov/physci/repo/data/investigations/PSI-22 (metadata cross-checked 2026-11-15).
- NASA Physical Sciences Informatics (PSI). *Advanced Combustion via Microgravity Experiments-Structure and Response of Spherical Diffusion Flames* (PSI-23). Dataset/investigation record. https://doi.org/10.60555/k57n-p030 . Investigation: https://psi.nasa.gov/physci/repo/data/investigations/PSI-23 (metadata cross-checked 2026-11-15).

## Official NASA Science context (objectives, NOT measured results)

- NASA Science. PSI-10 ACME investigation overview. https://science.nasa.gov/biological-physical/investigations/flame-design/ (accessed 2026-11-15).
- NASA Science. PSI-20 ACME investigation overview. https://science.nasa.gov/biological-physical/investigations/bre/ (accessed 2026-11-15).
- NASA Science. PSI-22 ACME investigation overview. https://science.nasa.gov/biological-physical/investigations/e-field-flames/ (accessed 2026-11-15).
- NASA Science. PSI-23 ACME investigation overview. https://science.nasa.gov/biological-physical/investigations/s-flame/ (accessed 2026-11-15).

## Reports / source datasets inspected

- NASA ACME/BRE Final Report (February 1, 2022), PDF pages 23, 24, 29, 110, 112, 116, 127. Locally supplied file: `BRE_final_report_20220201.pdf`.
- NASA ACME/Flame Design Final Report (2023). Locally supplied file: `PSI-10_Reports_FinalRpt_ACMEFlameDesign.pdf`. Numerical findings here are primarily from CSV tables, not modelled report conclusions.
- Four original NASA PSI experimental table CSVs, separately traceable in `data/experimental_tables/`, with SHA-256 in `SOURCE_CHECKSUMS.csv`.
- Raw BRE `19056A2_data.csv` and `19056A2_mfcSetpoints.csv`, SHA-256 in the approved audit and handoff manifest.

## Software / AI attribution

- Python 3, pandas, NumPy, Matplotlib and Python standard library.
- Starter kit authored by team; pre-existing tools described as Claude-assisted in original `si_log.md`.
- ChatGPT (OpenAI): source inspection, scientific limitation review, citation drafting, T5 descriptive package assembly; calculations independently validated by reproducible code.
- Codex (OpenAI): previously supplied PSI-20 audit/EDA scripts and source reconstruction packages, as disclosed in handoff.
- PSI-10 approved normalization script and verifier bundled in `supporting_packages/PSI-10_phase2_verified.zip`.

No external scientific measurement sources were added to the NASA PSI observations.
