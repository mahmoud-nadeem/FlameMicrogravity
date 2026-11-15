# Crew RAG folders (generated)

Written by `tools/export_rag_corpora.py` from `RAG/`: one folder per dataset, `<PSI-ID>_<name>/corpus.txt`, the same text as `deliverables/rag-corpora.zip`. Which crew member reads which folder: `content/rag-map.json` (generated from `RAG/rag-map.json`). Then run `python build_rag.py`. Do not edit the corpus.txt files by hand: add or change corpora under `RAG/` and re-run the export.

Exception: `PSI-68_FLEX_II/rag_corpus_flex2.txt` is Mohammed Tamer's FLEX-2 corpus as received and lives here; the export reads it as a source (its chunks are in that folder's corpus.txt, with their provenance) and never deletes it; `build_rag.py` reads the chunks once, from corpus.txt.
