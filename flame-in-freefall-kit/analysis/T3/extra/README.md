# T3 extra work (section 9, done after the data work)

- test_questions.md: 5 questions the T3 data can answer and 2 it cannot, with answers (item 3).
- evidence_snippets.json: one-sentence evidence lines with finding ID, label, source file and rows, for the dashboard to cite (item 4).
- limitations.md: plain-English limitations paragraph for the project page (item 5).
- Demo chart (item 6): ../PSI-101_same-r/charts/aging_growth_by_material.png (no logo, no people; source in its caption).
- track_paragraph.md: the plain paragraph explaining the track (section 6), from Mahmoud's own summary.
- build_rag_pack.py -> rag_pack_T3.txt (also written to RAG/Mahmoud.txt): the whole track as self-contained chunks for the site's RAG system (record metadata and NASA text, concepts with equations, one chunk per finding, per-material summaries, one chunk per flight test and per DAFT test, data-quality flags, limits, Q&A). Regenerate after any change: `python analysis/T3/extra/build_rag_pack.py` from the kit folder.
