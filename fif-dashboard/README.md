# Flame in Freefall dashboard

NASA's microgravity fire experiments explained for everyone, with a detailed view for researchers.
Concept and feature list: Mahmoud Nadeem (team). Built on the team's track packages (Mohammed Tamer's
package standard). The universe looks real; the interface feels like a game; every finding is traced
to its NASA source. See EVOLUTION.md for what changed, how it was tested and the scientific limits.

## Run it (no internet, no install)

Open `index.html` in Chrome, Edge or Firefox (double-click). Everything is local: pages, the universe,
charts, characters, saved answers, sources, fonts and the PDF viewer. Nothing is fetched from the internet.

Opened from disk, browsers block the PDF.js module, so mission documents show in the browser's own PDF
viewer. To get the in-site page, zoom and fit controls, serve the folder instead:

```bash
python -m http.server 8765      # then open http://localhost:8765
```

For a public link, upload the whole folder as a static site (GitHub Pages, Netlify, Cloudflare Pages).

## View modes

The top bar has three icons (`assets/js/controls.js`). **View** switches the cinematic WebGL universe (default) and the
original retro pixel look; switching never reloads, re-routes, resets the conversation, the lab or a tour. **Cat** opens a
small menu for Bondoq: *Show Bondoq* and *Bondoq moving* (pause/resume). **Settings** opens switches for *Sound* (off by
default), *Motion* (off = reduced motion: no drift, rotation or travel; the system setting is respected), *Crew reactions*
and *Rocket cursor*. Every icon has an accessible name and a tooltip; switches use `role="switch"` + `aria-checked` and an
ON/OFF word, menus close with Escape or a click outside and stay inside the viewport, and every choice is remembered
(`localStorage` keys `fif.sound`, `fif.reduceMotion`, `fif.reactions`, `fif.cinematic`, `fif.rocketCursor`, `fif.bondoq`,
`fif.bondoqPaused`). Element ids stay stable for tests: `#space-toggle`, `#dock-cat`, `#dock-settings`, `#sound-toggle`,
`#motion-toggle`, `#reaction-toggle`, `#rocket-toggle`, `#bondoq-toggle`, `#bondoq-pause`. Without WebGL the universe falls
back to a 2D canvas.

**Rocket cursor.** A native CSS cursor (`assets/cursors/rocket.svg`, nose = hotspot at 5,5; `rocket-go.svg` with a flame on
links and buttons), only for precise pointers (`@media (pointer: fine)`), so touch screens never get a fake pointer. Text and
form fields keep the text cursor; the normal cursor is the fallback. `assets/js/cursor.js` adds a restrained exhaust (a few
fading square puffs behind the rocket on a canvas that ignores the pointer); none with reduced motion, touch or the setting off.

## Update the data (after each member's package arrives)

1. Unzip the member's package (e.g. `T1_morgan_v1.zip`) into the kit, so that
   `flame-in-freefall-kit/analysis/T1/...` exists.
2. Run:
   ```bash
   python build_site_data.py --kit "../flame-in-freefall-kit"
   ```
3. Refresh the page.

The script reads, for every track: `card.json` (title, objectives, approach, citation check),
`findings.md` (the one-line finding format), `extra/evidence_snippets.json` (plain one-liners the
characters say), `extra/test_questions.md` (questions and answers the characters know),
`extra/track_paragraph.md`, `extra/limitations.md`, `references.md` and `charts/*.png` with
`charts/CAPTIONS.md` (any letter case; `- file.png: caption` or `Chart name: caption` lines) or
`charts/<chart>_caption.txt`. Questions may be written as `Q:`/`A:` pairs (T3) or one line
`N. Question? Answer` (T1). It writes everything into `data/site-data.js` (one file, because browsers block
reading JSON files from disk) and copies charts to `data/files/<track>/<PSI-ID>/`.
A card's `verified_by` / `verified_on` text is shown as written; the site never turns it into a claim.

Packages integrated so far: T1 (Amr Morgan, BASS v8), T3 (Mahmoud Nadeem) and T5 (Khaled Adawi, PSI-20 BRE; see
`flame-in-freefall-kit/analysis/T5/INTEGRATION.md`). Figures are read from a record's `charts/` and `eda/` folders. After a rebuild, also run
`python tools/export_rag_corpora.py` from the project root to refresh the dataset inventory and RAG export.

## Pages (the user journey)

| Route | What it is |
| --- | --- |
| `#/` Briefing | A scroll story: the camera flies past a world, the guide, then each crew world in turn |
| `#/explore` | The mission map: six worlds orbit the mission star; hover/focus previews, click approaches. Crew directory below |
| `#/profile/<id>` | Landing deck of one world: the scientist, their experiments as moons, notes |
| `#/record/<PSI-ID>` | One experiment: what they wanted to know, what they did, illustration, findings, charts |
| `#/lab/<PSI-ID>` | Transport lab (PSI-101, PSI-102, PSI-47) with a model card |
| `#/shorts` | Mission documents, one at a time, in the spacecraft viewport |
| `#/results` | Interactive charts that change with the chosen materials and flight; compare two experiments |
| `#/research` | Every finding with label, confidence, source file and exact rows; filters; CSV download |
| `#/sources` | Citations, PSI pages, DOIs, documents read, credits and AI disclosure |

### UI hooks (keep these names when restyling)

CSS can change anything. Scripts look up these IDs: in `index.html` `app`, `space`, `journey`, `footer`,
`motion-toggle`, `sound-toggle`, `edge-nav`, `hud-telemetry` and the `chat-*` IDs; inside page templates
(defined in the same script that uses them) the map (`map-*`), lab (`lab-*`), viewer (`pdf-*`, `short-*`)
and chart canvases (`c-size`, `c-aging`, `c-flow`). Renaming one means changing its script in the same commit.

## Crew RAG (each crew member answers from their own texts)

```
rag/<PSI-ID>_<NAME>/corpus.txt   one folder per dataset (e.g. PSI-26_BASS, PSI-22_ACME-E-FIELD)   } written by
content/rag-map.json             which crew member reads which folders ("*" = all, the guide)       } tools/export_rag_corpora.py
data/rag-data.js                 every chunk in one file: python build_rag.py                         (from the project's RAG/)
assets/js/rag.js                 retrieval (BM25, forgiving spelling), loaded data in the background
```

Update: add or change a corpus under the project's `RAG/` (and `RAG/rag-map.json`), run `python tools/export_rag_corpora.py`
from the project root, then `python build_rag.py` here. Other notes (.md/.txt) dropped into a `rag/<topic>/` folder also work:
headings become chunk titles. One corpus lives in the website itself: `rag/PSI-68_FLEX_II/rag_corpus_flex2.txt` (Mohammed
Tamer's FLEX-2 corpus as received). The export reads it as a source, puts its chunks (with provenance) into that folder's
`corpus.txt` and never deletes it; `build_rag.py` skips it because `corpus.txt` already quotes it. Rules the chat follows: a crew member searches only their own folders and sends you to the right
colleague otherwise; a curated answer from the crew member's own Q&A wins over a passage search; chunks that only explain a
corpus file are never answers (they are shown under "How the author says to use these notes"); each answer lists its sources
(dataset, chunk ID, evidence label) and carries a caution when a passage is labelled disputed, unverified, inferred or flagged.
Offline answers quote the passages; with `api_url` set (run `tools/llm_proxy.py`, which keeps the API key) a model writes the
answer from the same passages. Every experiment page has a searchable **Crew notes** section built from its folder.

## Crew astronauts, Bondoq and the planet guide

**Astronauts.** Faces are never shown: every astronaut wears a closed helmet with an opaque, dark reflective visor.
`python tools/crew_astronauts.py --src ../crew-illustrations` measures each member's proportions (height, head size, shoulder
width) from their own illustration (kept outside the site, in `../crew-illustrations/`; no pixel of it is copied) and draws a
pixel EVA suit in that member's colours, with gloves, boots, a backpack, a chest panel, trim and initials. It writes
`assets/crew/<id>.png` (frames idle, breath, talk, point; small portraits use the helmet-and-shoulders crop) and updates
`sprite`/`sheet` in `content/characters.json`.

**Suit colours.** `content/characters.json` is the one authoritative crew-to-colour table (`suit`, `accent` = trim,
`suit_name`); the sprite tool and the site read it from there. Ids, routes and planet ownership are unchanged.

| Crew id | Name on the site | Track | Suit | Trim | Illustration measured |
| --- | --- | --- | --- | --- | --- |
| morgan | Amr Morgan | T1 | burnt orange `#cf6230` | pale gold `#ffe08a` | Amr Morgan.jpeg |
| shreif | Mohamed Shreif | T2 | green `#2f9467` | white `#f2f5ea` | Mohammed Shiref.jpeg |
| nadeem | Mahmoud Nadeem | T3 | **black** `#16181e` | amber `#f0b042` (light outline on the dark site) | Mahmoud Nadeem.jpeg |
| tamer | Mohammed Tamer | T4 | blue `#3c6fd6` | orange `#ffb347` | Mohammed Tamer.jpeg |
| adwi | Khaled Adawi | T5 | white `#e3e0d4` | orange-red `#d95926` | Khaled Adawi.jpeg |
| gamal | Mohamed Gamal | T6 | purple `#7c52b8` | mint `#7fe0c4` | Mohammed Gamal.jpeg |

The Guide keeps its built-in 16x16 astronaut, also with an opaque visor (a glint, no eyes). Sprites breathe while idle, show comms lights and a nod while speaking, and point
toward what they talk about (`FIF.setSpriteState`); reduced motion keeps them still.

**Bondoq (بندق).** The crew's cat lives on a ledge along the bottom of the screen (`assets/js/bondoq.js`): he walks, stops and
looks around, sits, grooms, walks to his bowl to eat, walks to his cushion to curl up and sleep, wakes and stretches. A small
state machine with weighted choices, real durations and cooldowns; one timer; one instance for the visit; clicks pass through
him; he steps away while the Crew panel is open and on the document viewer; he pauses in background tabs; with reduced motion
he naps quietly on his cushion. Show/hide and pause/resume are in the cat menu (remembered). Frames:
`python tools/bondoq_sprites.py` (palette sampled from `assets/bondoq/originals/`; the poses are original pixel drawings,
because the reference images only show him lying down). No sound. 39 cells, all facing right (the page mirrors them): a
6-frame diagonal walk (far legs darker, body bob, swaying tail, nodding head); idle breathing, blinks and ear flicks; looking
around; sitting down (intro) then breathing, blinking, tail flicks and glances; grooming (paw licks, paw over the ear);
standing still then lowering his head to eat and chewing; settling (half-sit, sit, crouch) into a breathing loaf; curled
sleep with breathing and ear twitches; waking (head up, yawn) and stretching. Each animation is an intro played once and a
loop (`assets/bondoq/bondoq.json` "anims"). Walking speed is tied to the gait (16 sprite px per 720 ms cycle), so the paws
do not slide; he faces where he walks, stops before sitting, grooming, eating or sleeping, and reaches the bowl or cushion first.

**Planet guide.** On `#/profile/<id>` the world's owner welcomes you (`assets/js/planet-guide.js`) and offers a tour of the
sections that exist on that page: experiments, charts, the simulation lab, Results, the evidence table, mission documents,
notes and limitations, and the Ask button. Stops without a target are left out. First visit: full introduction; later visits:
a short welcome back with REPLAY TOUR and RESET TOURS; TOUR WITH <NAME> in the header replays it any time. NEXT/PREV/SKIP,
arrow keys and Escape work; the guide shares the Crew panel's queue, so only one character types at a time.

## Characters and the chat

- `content/characters.json`: one character per member plus the guide (names, roles, greetings, colours).
- Built-in pixel astronauts are drawn in code. To use a member's own picture (with consent):
  `python tools/pixelate.py photo.jpg --id nadeem`, then paste the printed `sprite` and `mouth` into that
  character. The mouth box darkens while the character talks.
- Offline answers (default): an expert system matches the question against the guide's FAQ
  (`content/faq.json`), each track's questions and answers, evidence snippets, experiment summaries and
  findings. Every answer cites its finding ID. Unknown questions get "not in our data" plus suggestions.
- Optional online answers: set `api_url` in `content/chat.json` to an endpoint that holds the API key and
  returns `{"answer": "..."}`. If it is missing, slow (timeout) or offline, the saved answers are used.

## Interactive charts

**Crew results (T2, T4, T6).** The Results page has a section of charts made from numbers the crew computed and reported in
their findings (`analysis/<track>/extra/results_charts.json` in the kit, read by `build_site_data.py` into each track's
`results`; drawn by `FIF.chartCrewResult`). Each chart lists the finding ids it shows, a source note and caveat; track chips
show or hide whole charts and series chips switch series inside one chart (each chart owns its own `ChartSlot`). T2: highest
post-igniter thermocouple readings per SAFFIRE sample; T4: FLEX disruption share by oxygen and Dext/D0 vs oxygen; T6: SLICE
measured peak velocity vs fan calibration and SPICE flames by fuel and nozzle.

**T3 (SAME/SAME-R).**

`assets/js/charts.js` draws the smoke charts from the SAME/SAME-R flight test table built from T3's
package. The two flights are never pooled (F-T3-5), and the air-flow chart compares within each heater
setting (pooling heater settings reverses the direction for Pyrell). New tracks add their own chart
functions the same way: a compact table in `build_site_data.py`, a draw function in `charts.js`, and a
section in `pages.js`.

## Files

```
index.html                    page shell (scripts load in order, no build step)
assets/css/style.css          original retro identity (palette, fonts, pixel buttons)
assets/css/expedition.css     universe layers, console chrome, story, map, deck, viewport, character states
assets/js/space-engine.js     WebGL universe: nebula, stars, star, worlds, camera scenes, 2D fallback
assets/js/planet-renderer.js  world definitions (palettes) + Canvas planet renderer used by the fallback
assets/js/starfield.js        retro pixel starfield (Retro view)
assets/js/orbital-explore.js  mission map (Explore)
assets/js/pages.js            briefing story, crew directory, record, results, research, sources
assets/js/expedition.js       profile deck, document viewport, crew panel closing
assets/js/lab.js, lab-config.js  transport model, lab page, validated command parser
assets/js/chat.js, conversation-queue.js, chat-visuals.js  crew chat, ordered queue, answer visuals
assets/js/sprites.js, dialog.js  pixel characters (idle, speaking, waiting, done, look, point), typewriter
assets/crew/, assets/bondoq/, assets/cursors/  crew sheets, Bondoq frames (+ originals/), rocket cursors; tools/crew_astronauts.py, tools/bondoq_sprites.py
assets/js/bondoq.js, planet-guide.js  Bondoq and the planet guide
assets/js/app.js              router, scene travel, edge navigation, toggles
assets/js/pdf-compat.mjs, pdf-worker-compat.mjs  shims so PDF.js runs in browsers older than Chrome/Edge 140
assets/vendor/                Chart.js, PDF.js 6.5.438 (with licences; unmodified)
data/site-data.js             generated by build_site_data.py
build_rag.py, rag/, data/rag-data.js, assets/js/rag.js, tools/llm_proxy.py  crew RAG (see above)
data/files/<track>/<PSI-ID>/  generated: chart images copied from the kit (emptied and rebuilt on every build)
data/shorts.js, data/shorts/  mission documents (original PDFs)
tests/*.test.cjs              node tests (no browser); tests/browser.e2e.cjs needs Playwright
```

## Tests

```bash
for t in tests/*.test.cjs; do node "$t"; done                 # logic, lifecycle, camera framing
npm i -D playwright && npx playwright install chromium && node tests/browser.e2e.cjs   # real browser
```

## Browser support

The site runs in current Chrome, Edge, Firefox and Safari. The in-site document viewer (PDF.js 6.5) needs a few
built-ins added to browsers in 2025 (`Uint8Array.prototype.toHex`, `Map.prototype.getOrInsertComputed` ...);
`assets/js/pdf-compat.mjs` adds them only when missing, so the viewer also works in older browsers (tested in
Chromium 129). If the viewer still cannot start, or the page is opened from disk, the original PDF is embedded natively.

## Credits

Chart.js (MIT), PDF.js 6.5.438 (Apache 2.0), Press Start 2P and VT323 fonts (SIL Open Font License), licences in `assets/`.
The universe is original procedural code (no copied images or textures); the worlds are fictional.
Data: NASA PSI repository (CC0). Code written with help from an AI assistant (Claude), disclosed on the
Sources page and in the team's AI-use logs.
