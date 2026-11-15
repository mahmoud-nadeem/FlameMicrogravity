# Flame in Freefall: Backend and RAG Plan (FAISS)

Nov 15, 2026 · @Mahmoud

## Summary

Add a small Python backend (FastAPI + FAISS) next to the static dashboard; the dashboard keeps working alone offline, and talks to the backend only through one versioned JSON API. Nothing is built yet: this is the study and the edit list for approval.

- **What it does:** reads the team's RAG text files, embeds every chunk, stores the vectors in a FAISS index, and answers each bot's questions from that bot's own chunks with cited chunk IDs.
- **Models:** one switch in a config file picks the answer model: a free local model through Ollama (the default), or no model at all (extractive answers); an optional OpenAI-compatible API stays switched off. Any key would live only in the backend's `.env`.
- **Safety net:** if the backend is down or slow, the site falls back to today's offline expert system, so the demo never breaks.
- **Style freedom:** the frontend touches the backend in one new file (`api.js`) and a short list of element IDs; CSS can change freely.

Decisions already taken (change any of them in a comment): Python + FastAPI; exact FAISS search (`IndexFlatIP` on normalised vectors = cosine); everything free and local, with Ollama running both the answer model (`qwen3.5:4b`) and the embedding model (`qwen3-embedding:0.6b`); hybrid search (FAISS + keyword BM25) so IDs like PSI-102 or F-T3-7 are found exactly; the backend also serves the site on `http://localhost:8000`, which avoids browser cross-origin problems. Details and licences are under **Free and offline stack**.

What I need from the team is listed under **Missing inputs**. The edits wait for approval under **Proposed edit list**.

## Free and offline stack

Every service in the plan now runs free, with no request limits and no internet at the venue: the models run on our own laptop through Ollama, and nothing depends on a paid plan or an API key.

| Service | Choice | Licence | Cost and limits | Works offline | Alternative considered |
| --- | --- | --- | --- | --- | --- |
| Model runtime (answers and embeddings) | [Ollama](https://github.com/ollama/ollama) | MIT | Free; no request caps, it runs on our machine | Yes, after `ollama pull` | llama.cpp `llama-server` (MIT) as a backup runtime |
| Answer model | [`qwen3.5:4b`](https://ollama.com/library/qwen3.5), download 3.3–4.0 GB, thinking off | Apache-2.0 | Free | Yes | `qwen3.5:2b` (2.7–3.1 GB) or `qwen3.5:0.8b` (1.2–1.3 GB) on a weak laptop; [`gemma4:e4b`](https://ollama.com/library/gemma4) (6.6–9.5 GB) |
| Embedding model | [`qwen3-embedding:0.6b`](https://ollama.com/library/qwen3-embedding), 639 MB | Apache-2.0 | Free | Yes | `bge-m3` (MIT); `multilingual-e5-small` (first draft) |
| Vector search | FAISS, `faiss-cpu` 1.16.0 | MIT | Free | Yes | None needed; flat index fits the corpus |
| Keyword search | Our own BM25 (about 40 lines) | Ours | Free | Yes | `rank_bm25`, last released February 2022 |
| API server | FastAPI + Uvicorn | MIT, BSD | Free | Yes | – |
| Frontend | Static HTML and JS, Chart.js, Press Start 2P and VT323 fonts | MIT, OFL | Free | Yes, already | – |
| Public website | GitHub Pages from a public repo | – | Free; site up to 1 GB, soft 100 GB a month of traffic | – | Cloudflare Pages free plan: 500 builds a month, 20,000 files, 25 MiB per file |
| Public AI chat (optional) | The demo laptop opened to the internet with a Cloudflare Quick Tunnel during judging | – | Free, no account; 200 requests in flight; meant for testing, no uptime guarantee, new URL each start | – | Hugging Face Spaces: Docker and Gradio Spaces now need a paid plan; only static Spaces are free |
| Code home | GitHub, public repo | – | Free (Pages from a private repo needs a paid plan) | Git works offline | – |
| Tests | pytest, Playwright | MIT, Apache-2.0 | Free | Yes | – |

**What changed from the first draft, and why:**

- **Embeddings move into Ollama, with `qwen3-embedding:0.6b`.** On the vendor's multilingual table its retrieval score is 64.64, against 57.12 for `multilingual-e5-large-instruct` and 54.60 for BGE-M3; the small e5 of the first draft is not listed and should score below its large sibling (my inference). It reads up to 32K tokens instead of 512, and it removes PyTorch from our install: the Python side keeps only `fastapi`, `uvicorn`, `faiss-cpu`, `numpy` and `httpx`. Queries take a one-line English instruction (`Instruct: ...\nQuery: ...`); passages take none.
- **One local answer model by default, `qwen3.5:4b`.** Apache-2.0, 201 languages and dialects (the page does not name Arabic, so the Arabic test in Verification decides), 256K context. Its thinking mode is on by default; the backend calls Ollama's native `/api/chat` with `think: false`, which Ollama documents, to keep answers fast. The laptop test picks 4b, 2b or 0.8b by speed and score.
- **No API key in the plan.** Free hosted tiers are capped, not unlimited: Groq's free table lists, for one model, 30 requests a minute and 1,000 a day; Gemini's free tier is rate-limited with limits "not guaranteed". Both also need internet. The OpenAI-compatible provider stays in the code, switched off, for anyone who adds a key later.
- **The public link stays free.** The static site goes on GitHub Pages with the saved answers that already work offline. The live AI chat runs on the demo laptop; if remote judges need it, a Quick Tunnel opens it for the judging window.

Optional later, not in this build: [Transformers.js](https://github.com/huggingface/transformers.js) (Apache-2.0) can run an embedding model in the visitor's browser, so the public site could search by meaning with no server. [WebLLM](https://github.com/mlc-ai/web-llm) (Apache-2.0) runs chat models in the browser, but needs WebGPU and lists older model families, so it is not recommended for judges' devices.

**Offline kit, downloaded before the event (about 7 GB with the backup model):**

1. Python 3.10 or later (`faiss-cpu` needs it).
2. The Ollama installer; on Windows it needs Windows 10 22H2 or later and at least 4 GB for the install, models extra.
3. `ollama pull qwen3.5:4b`, `ollama pull qwen3-embedding:0.6b`, and `ollama pull qwen3.5:2b` as the backup.
4. `pip download -r requirements.txt -d wheels/`, then on the laptop `pip install --no-index --find-links wheels -r requirements.txt`.
5. The built index folder (`data/index/`), copied with the code.
6. `cloudflared`, only if remote judges need the live chat.

Not yet confirmed: the Ollama Windows page does not say whether a laptop without a GPU is supported, and nobody has measured our models' speed on our hardware. Both are settled by the laptop test (C1) before anything else is tuned.

## Current state

The dashboard is a static site with no backend; its chat already has one hook for an online answer service, which is where the backend plugs in.

| Part | Where | What it does today |
| --- | --- | --- |
| Site | `fif-dashboard/index.html` + 9 scripts in `assets/js` (859 lines) | Pages, charts, characters; opens by double-click, no build step, no internet |
| Data | `data/site-data.js` from `build_site_data.py` | Reads each member's kit package (findings, snippets, questions); today only T3 has a package, so 23 findings |
| Chat | `assets/js/chat.js` | Offline expert system: TF-IDF over FAQ, questions, snippets and findings; each answer cites a finding ID |
| Online hook | `content/chat.json` → `api_url` | If set, POSTs `{question, character, track, context}` and expects `{answer}`; falls back offline on error or after 8 s |
| Bots | `content/characters.json` | 7 bots: the guide + one per member (T1–T6), with name, role, greeting, colours |
| Style | `assets/css/style.css` (190 lines) | Colours and fonts as variables in `:root` |
| RAG content | `RAG/Tamer.txt`, `RAG/Gamal.txt`, `RAG/Mahmoud.txt` | Three text packs, three slightly different formats (next section) |

Two gaps in the current hook: the browser picks the context itself (6 snippets from the saved answers, not the RAG files), and the answer carries no citations of its own. The new contract moves retrieval into the backend and returns citations.

## Content study per bot

Three of the six member bots have content today, and each pack needs a different fix before indexing; the backend can handle all three without anyone rewriting their file.

| Bot | Track and assigned records | RAG file | Chunks | Words per chunk (median / max) | Covered | Missing |
| --- | --- | --- | --- | --- | --- | --- |
| Guide | All tracks | none of its own | – | – | Reads every pack + `content/faq.json` | – |
| Amr Morgan | T1: BASS PSI-26, BASS-II PSI-25 | none | 0 | – | – | Whole track |
| Mohamed Shreif | T2: SAFFIRE PSI-98, 99, 100 | none | 0 | – | – | Whole track |
| Mahmoud Nadeem | T3: SAME PSI-102, SAME-R PSI-101, DAFT PSI-47 | `Mahmoud.txt` | 213 | 79 / 722 | All three records | – |
| Mohammed Tamer | T4: FLEX PSI-69, FLEX-2 PSI-68, CFI PSI-39, CFI-G PSI-159 | `Tamer.txt` | 28 | 355 / 1,169 | FLEX; FLEX-2 requirements and test matrix | CFI, CFI-G |
| Khaled Adawi | T5: BRE PSI-20, E-FIELD PSI-22, s-Flame PSI-23, Flame Design PSI-10 | none | 0 | – | – | Whole track |
| Mohamed Gamal | T6: SPICE PSI-107, SLICE PSI-106, CLD PSI-21 | `Gamal.txt` | 220 | 129 / 346 | SPICE (169 chunks), SLICE (51) | CLD |

What the study found, and what the backend will do about each point:

1. **Two header formats.** Tamer and Mahmoud use `### [CHUNK id] title | source: ... | tags: ...`; Gamal uses `### id` with `Investigation:`, `Topic:` and `Sources:` lines and `-----` separators. The ingester gets one adapter per format and turns both into the same chunk record. New packs should use the `[CHUNK]` format.
2. **Long chunks.** The chosen embedding model reads up to 32K tokens, so nothing is cut off, but a 1,169-word chunk mixes many topics and matches questions poorly. About half of Tamer's chunks (p90: 646 words) and Mahmoud's Q&A chunk (722) are over 350 words. The ingester splits them into windows of about 350 words with 50 words of overlap, at line breaks; each window keeps its parent ID and title.
3. **Missing metadata.** In `Tamer.txt` 13 of 28 chunks have no `source:` and 11 no `tags:`; `Gamal.txt` has no tags and no confidence tags (\[SRC\], \[CALC\], \[INF\]), but every section names its sources and it has 1,035 inline `[Source: ...]` notes. The ingester reports each gap; a chunk without a source inherits the file's source list and is marked so.
4. **Uneven granularity.** Gamal has 147 one-per-flame chunks, Mahmoud 154 one-per-test chunks, Tamer 28 long topic chunks. Plain similarity would let per-test chunks crowd out summaries. Each chunk gets a `doc_type` (overview, finding, concept, test, qa, meta) from its ID and tags; the guide takes at most 3 chunks per track, and broad questions prefer overview and finding chunks.
5. **Housekeeping chunks.** "How to use this file" and "Dashboard integration" chunks (FLEX-00, FLEX-16, T3-00, T3-DASH) describe the file, not the science; they are kept out of answers.
6. **Q&A chunks.** FLEX-15 and T3-QA hold question–answer pairs; each pair becomes its own chunk and also feeds the retrieval test set. Gamal's pack has none yet.
7. **Source codes.** Tamer and Mahmoud cite S1…Sn from a list at the top of the file; citations expand them to the full source line.
8. **Links to dashboard findings.** Only Mahmoud's chunks carry finding IDs (F-T3-1 to F-T3-23) that open a row on the Research page. Tamer's F1–F9 are data-quality flag numbers, not finding IDs. Other packs cite chunk ID + source until their kit packages arrive.
9. **Points to check in `Tamer.txt`.** Source S2 is "dashboard v2 HTML", and flag F9 says FLEX-2 has no PSI ID, while our assignment list gives FLEX-2 as PSI-68. Chunk IDs FLEX-19 to FLEX-22 do not exist and FLEX-17/18 sit at the end of the file; probably harmless, but worth one look.
10. **Equations.** Tamer and Mahmoud write LaTeX; the chat shows plain text, so answers spell formulas in words.

## Architecture

The site and the backend meet only at the API; content flows up from the packs into the index, and questions flow down from the chat to the answer model.

&#91;embedded content: architecture · browser, backend, answer models, content\]

A question goes chat → `api.js` → `/api/v1/chat` → hybrid retrieval over the FAISS index → the answer writer → back with citations. The index is built offline by a command from the RAG packs, never by the running server.

## Backend design

The backend has four steps, and each one is a separate module with its own test: ingest the packs, embed and index them, retrieve for a question, and write the answer.

### 1. Ingest

`RAG/rag_sources.yaml` maps each file to its bot and track (`Mahmoud.txt` → `nadeem`, T3). The parser turns every chunk or window into one record:

```json
{"chunk_id": "T3-F01", "window": 0, "bot": "nadeem", "track": "T3",
 "records": ["PSI-101"], "doc_type": "finding", "title": "F-T3-1 (PSI-101)",
 "sources": ["S7: SAME/SAME-R results workbook ..."], "tags": ["finding", "observed-in-data"],
 "finding_ids": ["F-T3-1"], "confidence": ["CALC"], "text": "...", "file": "RAG/Mahmoud.txt", "line": 214}
```

`ingest --check` prints a report per file (chunks, windows, missing sources or tags, duplicate IDs) and stops on real errors, so a member sees problems in their pack before anything is indexed.

### 2. Embed and index (FAISS)

An embedding model turns each text into a list of numbers (a vector) so that texts with similar meaning sit close together. FAISS stores those vectors and finds the nearest ones to a question's vector.

- **Model:** `qwen3-embedding:0.6b` through Ollama's `POST /api/embed`, up to 1,024 numbers per text, 32K-token input, Apache-2.0, 100+ languages. Questions get a one-line English instruction in front (`Instruct: Given a question, find the passages that answer it` then `Query: ...`); passages get none.
- **Index:** `IndexFlatIP` over vectors normalised with `faiss.normalize_L2`, which makes the inner product equal to cosine similarity. A flat index compares the question with every vector exactly, needs no training, and is the right size for our corpus (about 460 chunks today, a few thousand windows when all six packs exist).
- **Files:** `faiss.write_index` / `faiss.read_index` for `faiss.index`, plus `chunks.jsonl` (the records, same order) and `manifest.json` (model name, dimension, chunk count, hash of each source file, build time). The server refuses to start if the manifest's model differs from the configured one, so a mixed index cannot happen. FAISS warns to load only index files you built yourself; we never load downloaded ones.
- **If Ollama is down:** retrieval runs on BM25 alone and answers are extractive, so the chat still answers with citations.

### 3. Retrieve (hybrid)

Vectors catch meaning ("does smoke get bigger with time?" finds the aging finding); keywords catch exact IDs ("PSI-102", "F-T3-7", "test 57"), which vectors handle poorly. The backend runs both and merges the two ranked lists with reciprocal rank fusion:

```latex
\text{score}(c) = \sum_{r \in \{\text{FAISS},\ \text{BM25}\}} \frac{1}{60 + \text{rank}_r(c)}
```

- **Keyword side:** a short in-house BM25 (about 40 lines, tokens keep hyphens so `PSI-102` stays one word). The `rank_bm25` package was last released in February 2022, so we do not depend on it.
- **Who sees what:** a member bot searches its own track first, then the guide's FAQ; the guide searches everything, at most 3 chunks per track. Meta chunks are never returned.
- **No answer:** if the best chunk is weak on both sides, the reply is "not in our data" plus the bot that covers the topic, the same rule the offline chat uses today.

### 4. Answer

The top 6 chunks go to the answer model with fixed rules: answer only from these chunks; cite chunk IDs in brackets; keep the label (observed in data, reported by NASA, our inference); never present our inference as a NASA finding; plain words, no LaTeX; at most about 120 words for the public view, more numbers in the researcher view; answer in the language of the question. Chunk text is passed as data, not as instructions.

After the model answers, a check removes any cited ID that was not in the 6 chunks; an answer left with no valid citation is replaced by the extractive answer. **Extractive mode** (no model) returns the best sentences of the top chunks with their citations; it is the fallback, and also a valid setting for a laptop with no model.

The server keeps no chat state: the frontend sends the last 4 turns with each question, so a follow-up such as "and for Teflon?" still works.

## API contract

Four endpoints under `/api/v1` are the only coupling between the two sides; either side can change freely as long as these shapes hold, and a contract test pins them.

| Endpoint | Request | Response | Used by |
| --- | --- | --- | --- |
| `GET /api/v1/health` | – | `status`, `version`, index (`chunks`, `model`, `built_at`), answer model (`provider`, `model`, `reachable`) | Chat panel, on open: decides online or offline mode |
| `GET /api/v1/bots` | – | Each bot's `id`, `track`, chunk count, records covered | Chat panel: greys out bots with no content |
| `POST /api/v1/chat` | `question`, `bot_id`, `audience` (public or researcher), `history` (last 4 turns) | `answer`, `mode` (llm or extractive), `citations[]`, `not_in_data`, `timing_ms`, `request_id` | Chat panel |
| `POST /api/v1/search` | `query`, `bot_id` (optional), `k` | Ranked chunks with scores | Research page "search the evidence"; debugging retrieval |

Each citation carries `chunk_id`, `title`, `bot`, `records`, `source`, `finding_ids` and `score`, so the frontend can link a finding to the Research page and a record to its experiment page.

```json
{"answer": "Yes. The same smoke measured again after 4 to 33 minutes was larger in 42 of 44 paired tests [T3-F01].",
 "mode": "llm", "not_in_data": false,
 "citations": [{"chunk_id": "T3-F01", "title": "F-T3-1 (PSI-101)", "bot": "nadeem", "records": ["PSI-101"],
   "source": "S7: SAME/SAME-R results workbook", "finding_ids": ["F-T3-1"], "score": 0.031}],
 "timing_ms": {"retrieve": 40, "generate": 2100}, "request_id": "..."}
```

Errors return a JSON `error` with a code (`bad_request`, `model_unavailable`, `index_missing`); the frontend treats any error or a timeout as "use offline answers". The timing numbers above are placeholders until measured. Reindexing is a command, not an endpoint, so nobody can rebuild the index from the browser.

## Frontend edits

The frontend change is small: one new file holds every backend call, the chat swaps its online function for it, and nothing in the pages, charts or CSS depends on the backend.

| File | Change | Why |
| --- | --- | --- |
| `assets/js/api.js` (new) | `FIF.api.health()`, `FIF.api.chat()`, `FIF.api.search()`; base URL, timeout, one health check when the chat opens; returns `null` on any failure | The only file that knows endpoints; a backend change touches only this file |
| `assets/js/chat.js` | `answerOnline()` calls `FIF.api.chat` with the bot ID and last 4 turns; citations become the existing evidence links; a line under each answer says "answer from our files" or "saved answer" | Today the browser picks the context; the backend should |
| `content/chat.json` | `api_url` becomes `api_base` (empty = same server); `mode`: `auto` or `offline`; `timeout_ms` set after measuring the local model | One place to switch online answers on or off |
| `index.html` | One `<script>` line for `api.js` before `chat.js` | Load order |
| `assets/css/style.css` | Two small rules appended (`.cite`, `.answer-mode`) | Look of the new answer line |
| `README.md` | "UI hooks" list and "run with the backend" steps | So a restyle never breaks the chat |

**Restyling safely.** CSS can change anything. What must keep its name is the set of IDs the scripts look up: 15 in the page shell `index.html` (`app`, `space`, `journey`, `footer`, `motion-toggle`, `sound-toggle` and the 9 `chat-*` IDs), and the rest inside the page templates in `pages.js` (charts, simulation, filters), next to the code that uses them. The README will list them all as the UI hooks; renaming one means changing its script in the same commit.

**Opening the file directly still works.** When the page is opened from disk (`file://`), `api.js` skips the backend and the chat uses saved answers, exactly as today. When the page comes from the backend (`http://localhost:8000`), page and API share one origin, so the browser needs no cross-origin setup.

Later, optional: a "search the evidence" box on the Research page that calls `/search` and shows the matching chunks with their sources.

## Model connections

The default is fully local and free; the answer model and the embedding model are each one setting in `fif-backend/.env`, so a different local model, or a paid API added later, needs no code change.

| Setting | Default: local (Ollama) | No model | Optional, off: hosted OpenAI-compatible API |
| --- | --- | --- | --- |
| `LLM_PROVIDER` | `ollama` (native `/api/chat`, `think: false`) | `extractive` | `openai_compatible` |
| `LLM_BASE_URL` | `http://localhost:11434` | – | The provider's base URL |
| `LLM_API_KEY` | – | – | Someone's key |
| Internet at the event | Not needed once models are pulled | Not needed | Needed |
| Cost and limits | Free, no caps; speed depends on the laptop | Free | Per request, or a capped free tier |

The local provider uses Ollama's native chat endpoint because it documents `think: false` ([source](https://docs.ollama.com/api/chat)); the OpenAI-compatible endpoint ([source](https://docs.ollama.com/api/openai-compatibility)) stays available for other runtimes such as llama.cpp's `llama-server`, which gets a 5-minute test before use.

```bash
# fif-backend/.env  (never committed; .env.example is)
LLM_PROVIDER=ollama              # ollama | extractive | openai_compatible
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=qwen3.5:4b             # qwen3.5:2b or qwen3.5:0.8b on a weak laptop
EMBED_PROVIDER=ollama
EMBED_MODEL=qwen3-embedding:0.6b
ANSWER_TIMEOUT_S=60              # set from the laptop test
# LLM_API_KEY=                   # only for openai_compatible, off by default
```

**Embeddings** run in the same Ollama through `POST /api/embed` ([source](https://docs.ollama.com/api/embed)), so the backend needs no PyTorch and one runtime serves both models. Models are pulled once and then work offline, so they must be pulled before the event. Changing the embedding model means rebuilding the index; the manifest check enforces that.

**Fallback order on every question:** the configured model, then extractive answers on the server, then saved answers in the browser. A slow or missing model never leaves the user without an answer.

**Keys:** only in the backend's `.env`, listed in `.gitignore`; never in `content/chat.json`, the frontend, a commit or a screenshot. The default setup has no key at all; if one is ever added, a public link using it also needs a spending cap and a per-visitor rate limit.

## Development cycle and repo layout

Each person edits one area, and a check command catches a broken handoff before it reaches the demo.

| Who | Edits | Leaves alone | Runs before handing in |
| --- | --- | --- | --- |
| Each member | Their pack in `RAG/` and their kit package | Code | `python -m fif_backend ingest --check` |
| Frontend (style, pages) | `fif-dashboard/assets`, `content/*.json` | `api.js` contract, UI hook IDs | Open the page from disk and from the backend; chat answers in both |
| Backend | `fif-backend/` | Frontend files | `pytest` and `python -m fif_backend eval` |

The cycle after any content change:

1. A member updates their pack in `RAG/`.
2. `ingest --check` reports chunks, windows and gaps; real errors stop here.
3. `build-index` embeds the chunks and writes `faiss.index`, `chunks.jsonl` and `manifest.json`.
4. `eval` runs the question set and prints whether each expected chunk came back in the top 5.
5. `serve` starts the API and serves the site on `http://localhost:8000`.
6. `build_site_data.py` refreshes the offline answers, so the site still works with the backend off.

```text
Project 3-nasa/
  RAG/                    content: one pack per member + rag_sources.yaml (file -> bot, track)
  fif-dashboard/          frontend, works alone from disk (unchanged except the edits above)
  fif-backend/
    requirements.txt      fastapi, uvicorn, faiss-cpu, numpy, httpx, pydantic, pyyaml (no PyTorch)
    .env.example          settings without secrets
    offline_kit.md        what to download before the event (models, wheels)
    fif_backend/
      config.py           reads .env, checks values at start
      ingest/             parsers (one per pack format), windows, --check report
      index/              embedder (Ollama /api/embed), FAISS store + manifest
      retrieve/           bm25.py, hybrid.py (fusion, bot filter, per-track cap)
      generate/           providers (ollama, extractive, optional openai_compatible), prompts, citation check
      bots.py             bots from fif-dashboard/content/characters.json
      api/                FastAPI app, /api/v1 routes, request and response schemas, static site
    data/index/           generated, not committed
    eval/questions.jsonl  questions with the chunk IDs that must come back
    tests/
```

The bots come from the dashboard's `characters.json`, so adding a member or renaming a bot happens in one file for both sides. FAISS 1.16.0 (`pip install faiss-cpu`) has wheels for Windows, macOS and Linux on Python 3.10 or later ([source](https://pypi.org/project/faiss-cpu/)), so every member can run the backend on their own laptop.

## Verification

We call the backend done when every row below passes on the demo laptop, with the measured numbers written into the README.

| Check | How | Pass when |
| --- | --- | --- |
| Parsers | Unit tests on the three real packs | 28 / 220 / 213 chunks; no duplicate IDs; no window over the model's limit |
| Index | Manifest check at start | Vector count = window count; model and dimension match the config |
| Retrieval | The 32 existing Q&A pairs (13 in FLEX-15, 19 in T3-QA), each mapped to the content chunk that holds the answer | Expected chunk in the top 5 for at least 80% of questions (my starting target; revisit after the first run) |
| Arabic questions | 10 of those questions translated to Arabic | Same measure, reported; no target until we see it |
| Out of scope | 10 questions our data cannot answer (oxygen in SAME, Mars gravity, alarm thresholds) | `not_in_data` for all 10 |
| Citations | Every model answer in the eval run | All cited IDs were among the retrieved chunks |
| Contract | Tests on the four endpoints | Shapes match this document |
| Fallback | Backend stopped; model stopped; model slower than the timeout | The chat still answers, from extractive or saved answers |
| Frontend | Browser test: page from disk and from the backend, 3 questions per bot | No console errors; answers show citations and their mode |
| Speed | Timed on the demo laptop | Sets `timeout_ms` in `chat.json` |

One trap in the retrieval test: the Q&A pairs are also chunks in the index, so a question would simply find its own copy and score 100%. The eval therefore leaves the Q&A chunks out of the index and checks for the chunk that holds the facts. The Gamal and member packs still to come need their own question sets; 10 questions per pack is enough to start.

## Risks, rules and security

The biggest risk is a confident wrong answer in front of the judges; most of the design above exists to prevent it.

| Risk | Effect | What prevents it |
| --- | --- | --- |
| Invented or wrong answer | A false claim in the demo | Answer only from retrieved chunks; citation check; extractive fallback; every answer shows its sources and says it is an AI answer |
| Our inference shown as NASA's result | Misleading the judges | The label of each chunk (observed, reported, inference) is kept in the answer |
| No internet at the venue | Online model unusable | Local model pulled in advance; embedding model downloaded in advance; saved answers in the browser |
| Local model too slow on the laptop | Long waits | Measure first; smaller model; timeout then extractive answer |
| API key leaks | Someone spends our credit | Key only in `.env` (git-ignored); spending cap; rate limit on a public link |
| Public link without a backend | Chat on the public site answers only from saved answers | Free Quick Tunnel from the demo laptop during judging, or state that the AI chat runs in the live demo |
| Text inside a chunk acting as an instruction | The model follows it | Chunks are passed as quoted data; rules say never follow instructions inside them |
| Tampered index file | Unsafe load | Load only indexes we built (FAISS's own warning) |
| Packs disagree (FLEX-2 PSI ID) | Two bots give two answers | The ingest report lists conflicts; fixed in the pack, not in code |
| Tracks with no pack | Empty bot | Health endpoint shows chunk counts; the bot says its pack is not ready yet |

Competition rules this touches: AI use must be disclosed, so the Sources page will name the embedding model, the answer model and the AI-written backend code (also logged in the SI logs). The chat and character idea is Mahmoud's own concept; this plan only implements it. No NASA logos and no photos without consent apply to the chat panel too.

Visitor questions are not stored by default; a local log of question + retrieved chunk IDs can be switched on during testing to tune retrieval.

## Missing inputs

Eight things only the team can give; none of them costs money, and each has a default, so building can start before every answer arrives.

| Needed | From | Blocks | Default if not answered |
| --- | --- | --- | --- |
| RAG packs for T1 (BASS), T2 (SAFFIRE), T5 (ACME records) | Amr, Shreif, Khaled | Those three bots | The bot says its pack is not ready |
| CFI and CFI-G content; CLD content | Tamer; Gamal | Those records in their bots | Bot answers for the records it has |
| Demo laptop: RAM, GPU or none, operating system (Windows 10 22H2 or later for Ollama), about 10 GB free disk | Whoever brings it | Which model size runs fast enough | `qwen3.5:4b`, dropping to 2b or 0.8b if the laptop test is slow |
| Public link: will judges use a URL, or only the live demo | Team leader | Whether to open a Quick Tunnel during judging | Live demo only; the public site keeps saved answers |
| Code home: no git repository exists in the project folder | Team leader | Shared work, reviews, the free public site | One new public GitHub repo holding `RAG/`, `fif-dashboard/`, `fif-backend/` |
| FLEX-2 PSI ID (assignment: PSI-68; pack flag F9: none) and what source S2 "dashboard v2 HTML" is | Tamer | Correct citations for T4 | Ingest marks those lines as unverified |
| 10 question–answer pairs per pack for the test set | Gamal, then each new pack | Measuring retrieval for that bot | Bot ships without a measured score |
| Two or three lines on how each character talks | Each member | Bot personality | Built from the role in `characters.json` |

## Proposed edit list

Twelve edits in build order; nothing is written until each row is approved, and the frontend is not touched until the backend rows pass their tests.

| # | Edit | Files | Changes existing code | Decision |
| --- | --- | --- | --- | --- |
| A1 | Map each pack to its bot and track | `RAG/rag_sources.yaml` (new) | No |  |
| A2 | Backend skeleton: settings, requirements, example env, offline kit list (models to pull, wheels to download) | `fif-backend/` (new) | No |  |
| A3 | Ingest: two pack parsers, windows, `--check` report, tests on the 3 real packs | `fif_backend/ingest/` (new) | No |  |
| A4 | Embeddings through Ollama + FAISS index + manifest | `fif_backend/index/` (new) | No |  |
| A5 | Hybrid retrieval (FAISS + BM25, fusion, bot filter) + eval set from the 32 Q&A pairs | `fif_backend/retrieve/`, `eval/` (new) | No |  |
| A6 | Answer providers (Ollama local by default, extractive, optional OpenAI-compatible switched off), prompts, citation check | `fif_backend/generate/` (new) | No |  |
| A7 | FastAPI app: 4 endpoints, serves the site | `fif_backend/api/` (new) | No |  |
| B1 | Connection layer | `assets/js/api.js` (new), one line in `index.html` | One line |  |
| B2 | Chat uses the backend, shows citations and answer mode | `assets/js/chat.js` (`answerOnline`, `refsHTML`) | Yes, two functions |  |
| B3 | Settings and two style rules | `content/chat.json`, `assets/css/style.css` (append) | Settings only |  |
| B4 | UI hooks and run steps; models named on the Sources page | `README.md`, `assets/js/pages.js` (Sources text) | Text only |  |
| C1 | Run the verification table on the demo laptop; numbers into the README | – | No |  |

Pick a decision per row, or comment on a row to change it. Rows A1–A7 can start now with the defaults in **Missing inputs**; B1–B4 wait until A7 passes its tests.

## Sources

Pages opened for this plan on 15 Nov 2026; project files read from the team folder.

- [FAISS: metric types and distances](https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances) (cosine = inner product on normalised vectors)
- [FAISS: index IO](https://github.com/facebookresearch/faiss/wiki/Index-IO,-cloning-and-hyper-parameter-tuning) (`write_index`, `read_index`, load only trusted files)
- [FAISS: getting started](https://github.com/facebookresearch/faiss/wiki/Getting-started)
- [faiss-cpu on PyPI](https://pypi.org/project/faiss-cpu/) (1.16.0, Python 3.10+, Windows/macOS/Linux)
- [intfloat/multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) (384 dimensions, 512 tokens, prefixes, Arabic, MIT)
- [sentence-transformers on PyPI](https://pypi.org/project/sentence-transformers/) (6.3.0)
- [rank-bm25 on PyPI](https://pypi.org/project/rank-bm25/) (0.2.2, February 2022)
- [Ollama: OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility) and [Ollama: embed](https://docs.ollama.com/api/embed)
- [FastAPI: CORS](https://fastapi.tiangolo.com/tutorial/cors/)
- Team files: `RAG/Tamer.txt`, `RAG/Gamal.txt`, `RAG/Mahmoud.txt`, `fif-dashboard/` (`chat.js`, `content/*.json`, `index.html`, `README.md`)

Added for the free and offline check (15 Nov 2026):

- [Ollama model search](https://ollama.com/search) and [embedding models](https://ollama.com/search?c=embedding)
- [Ollama: qwen3.5](https://ollama.com/library/qwen3.5), [qwen3-embedding](https://ollama.com/library/qwen3-embedding), [gemma4](https://ollama.com/library/gemma4)
- [Qwen/Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) (Apache-2.0, 32K, multilingual table) and [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3) (MIT, 8,192 tokens)
- [Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) (Apache-2.0, 201 languages, thinking on by default) and [google/gemma-4-E4B-it](https://huggingface.co/google/gemma-4-E4B-it)
- [Ollama: chat API](https://docs.ollama.com/api/chat) (`think: false`) and [Ollama on Windows](https://docs.ollama.com/windows)
- [Ollama repository](https://github.com/ollama/ollama) (MIT) and [llama.cpp](https://github.com/ggml-org/llama.cpp) (MIT)
- [Groq rate limits](https://console.groq.com/docs/rate-limits) and [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Hugging Face Spaces overview](https://huggingface.co/docs/hub/spaces-overview), [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/), [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits), [Cloudflare Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
- [Transformers.js docs](https://huggingface.co/docs/transformers.js/index) and [WebLLM](https://github.com/mlc-ai/web-llm)
