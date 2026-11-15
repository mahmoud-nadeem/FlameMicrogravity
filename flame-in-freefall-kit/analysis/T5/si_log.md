# AI-use log (T5, Khaled Adwi)

time | tool used | what I asked for | what I used from the answer | where it appears | whether I checked it, and how

2026-11-14 | Claude (Anthropic), used by Mahmoud Nadeem | the team kit tools (PSI downloader, file parsers, folder templates, run-table builder, self-check, packager) | the tools as published in the kit (prefilled line: keep it if you use the kit) | scripts/, tools/, pipeline/, analysis/ templates | automated tests in tests/; card fields prefilled from the PSI API are checked by me on the PSI page
2026-11-15 | ChatGPT (OpenAI) | Inspect kit and original PSI tables; produce source-linked findings, caveats, citations, charts and package | Generated T5 findings and descriptive material after independently recomputing counts | analysis/T5/; supporting_packages/ | Programmatic CSV checks, SHA-256 validation, NASA Science cross-check; exact live PSI Cite menu not verified
2026-11-15 | Codex (OpenAI), directed by team | PSI-20 BRE audit, source reconciliation and EDA | Previously approved outputs incorporated unchanged | analysis/T5/PSI-20_bre/charts; supporting_packages | Independent earlier review: original hashes, 51/51 tests on Task04C and Task05 charts/reproduction
