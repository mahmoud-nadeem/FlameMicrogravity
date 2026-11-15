# v10.2: Khaled Adawi's final T5 package, 15 November 2026

- Khaled's `Khaled_T5_FINAL_INTEGRATION.zip` is merged into the kit (`flame-in-freefall-kit/analysis/T5/INTEGRATION.md` says
  what went where): his own 19 findings for all four ACME records (PSI-10 Flame Design, PSI-20 BRE, PSI-22 E-FIELD, PSI-23
  s-Flame) with his confidence levels, his cards (partial review, disclosed), profiles, data logs, references, charts and
  tables. They replace the earlier transcription of his PSI-20 findings (F-T5-1..6 had other meanings). All his counts were
  re-checked against the NASA tables. 111 findings in total.

# v10.1: FLEX-2 corpus for Mohammed Tamer, PSI-60 removed, 15 November 2026

- **FLEX-2 (PSI-68) corpus.** Mohammed Tamer's `rag_corpus_flex2.txt` (470 chunks, every one labelled PSI-68) is in
  `rag/PSI-68_FLEX_II/` (the website folder for PSI-68, renamed from `PSI-68_FLEX-2`). The export reads it as a T4 source,
  so it is in `deliverables/rag-corpora.zip` and the inventory; Tamer's crew bot and the guide answer from it (PSI-68 now has
  626 chunks). `content/rag-map.json` points `tamer` at `PSI-68_FLEX_II`; `RAG/rag-map.json` names it `FLEX-II`.
- **PSI-60 removed.** The SPICE ground-analysis record (metadata only, no data files) is gone from the T6 track, the kit
  (package folder and NASA metadata), the pipeline (investigation folder; `site_data/` regenerated: 23 investigations), the
  RAG map, the export tool, the assignment sheets, READMEs, the RAG plan and the status report (PDF rebuilt). Its folders are
  in `archive/removed/PSI-60/`. Earlier entries below still mention it as part of what was true then.

# v10: closed helmets, suit colours, crew findings T2/T4/T6, icon controls, Bondoq animation, rocket cursor, 15 November 2026

- **Faces covered.** Every astronaut wears a closed helmet with an opaque, dark reflective visor; the sprite tool now measures
  only proportions from the illustrations (moved out of the site to `../crew-illustrations/`) and copies no face pixels. The
  Guide's built-in astronaut lost its eyes behind the visor too.
- **Suit colours.** One table in `content/characters.json` (`suit`, `accent`, `suit_name`): Morgan burnt orange, Shreif green,
  Mahmoud Nadeem black with amber trim and a light outline, Tamer blue, Adawi white, Gamal purple. Ids and routes unchanged.
- **Findings added.** Mohamed Shreif (T2 SAFFIRE I-III, 13 lines, his own files), Mohammed Tamer (T4 PSI-69 FLEX, 23 lines
  transcribed from his tagged analysis) and Mohamed Gamal (T6 PSI-106 SLICE, PSI-107 SPICE, PSI-21 CLD, 21 lines transcribed)
  are in the kit's `findings.md` files with labels, sources, rows and caveats; limitations for T4 and T6; Gamal's card
  summaries fill the empty `approach` of PSI-106/107/21. 98 findings in total. The placeholder templates are archived.
- **Results.** Five crew results charts (T2, T4, T6) with track and series filters; each names its findings. The planet guide
  adds a Results stop for these tracks; the assistant's "what is your part about" answer no longer says "not in yet".
- **Controls.** Six text buttons became three icons (view, cat menu, settings menu) with tooltips, ARIA states, keyboard and
  Escape support, viewport-safe menus and remembered settings.
- **Bondoq.** 39 frames (was 19): gait cycle, idle breathing/blinks/ears, transitions (sit down, settle, wake, stretch),
  grooming, eating; intro + loop sequences; walking speed tied to the stride; lying poses mirrored to face the same way.
- **Rocket cursor.** Native SVG cursor for mouse/trackpad, hover variant on links and buttons, text cursor kept on text,
  optional exhaust that never takes clicks; a setting turns it off.
- Fixed: on phones the home story could widen the page by 46 px (a decorative frame); `.story` now clips horizontal overflow.

# v9: crew astronauts, Bondoq and the planet guide, 15 November 2026

1. **Crew astronauts from the team's own illustrations.** No image model was used: `tools/crew_astronauts.py` keeps each
   person's head pixel for pixel (cut from their illustration, background removed, defringed) and draws a pixel EVA suit
   around their measured build, with a clear bubble helmet that leaves the face uncovered. Mapping by file name (README table).
   Used everywhere `FIF.spriteHTML` draws a crew member: crew bar, chat, map transmissions, profiles, the guide.
2. **Bondoq.** A cat companion on a ledge at the bottom of the screen: walk, look, sit, groom, eat at his bowl, sleep on his
   cushion, wake, stretch. One instance and one timer; pauses with the tab, the PAUSE control, reduced motion (static nap) and
   while the Crew panel or the document viewer is open; clicks pass through.
3. **Planet guide.** Each world's owner welcomes you and offers a tour built from the sections that exist on the page, with
   saved progress per planet, replay, reset, keyboard control, and the shared conversation queue (`FIF.voiceQueue`) so tour
   narration and Crew answers never type at the same time. Mission documents now carry the track they belong to
   (`data/shorts.js`), and planets with documents get a MISSION DOCUMENTS button.

# v8: crew RAG and T1 v8, 15 November 2026

1. **Crew RAG.** The colleague's `rag.js`, `chat.js`, `build_rag.py` and `llm_proxy.py` (from `Important/`) are integrated.
   `rag/<PSI-ID>_<NAME>/` holds the 18 dataset corpora (incl. Khaled's PSI-22 E-FIELD and PSI-23 s-Flame), and
   `content/rag-map.json` gives Khaled all four ACME folders, Tamer FLEX-2, Gamal CLD and PSI-60 (no corpus yet).
   Changes to the delivered files: `build_rag.py` reads the team corpus format and keeps chunk IDs, sources, titles and
   evidence labels; `rag.js` loads its 4.3 MB of data after the page, indexes shared chunks once, never answers from
   corpus-file instructions, quotes the answer of a question-and-answer chunk instead of its question, keeps decimals inside
   sentences, ranks single data rows lower, recognises "E-FIELD", "CFI-G" and "PSI-26" mentions, and returns chunk IDs, evidence
   labels and cautions; `chat.js` shows those sources (linked to the experiment page), prefers a crew member's own curated
   answer when it matches strongly, and keeps the PSI-ID fallback for PSI-60. `chat.json` pointed at port 8899 while the proxy
   serves 8787; the site now defaults to offline answers (`api_url` empty) and documents how to switch the proxy on.
2. **Crew notes** on every experiment page: the folder's passages with chunk ID, evidence and source, searchable, with the
   author's usage instructions shown separately.
3. **T1 v8** (Amr Morgan) replaces v6; review in `docs/reviews/T1_Amr_v8_review.md`.

# v7: T5 (Khaled Adawi), 15 November 2026

1. **T5 is live.** PSI-20 BRE shows 6 findings (his EDA findings, confidence "not stated" because he gave none), 9 figures
   (4 EDA charts, 5 raw-signal plots, captioned with his own titles and the note that units and calibration are not
   established), his limitations, and objectives for BRE, E-FIELD, s-Flame and Flame Design from his corpus. Khaled answers
   20 questions from his corpus's FAQ chunks. The NASA ACME/BRE Final Report (2022) he supplied is the fourth mission document.
2. **Build:** figures are read from `charts/` and `eda/`; `extra/build_site_inputs.py` in the kit derives the T5 inputs.
3. **Document viewer:** PDF.js now reports errors only (`verbosity: 0`), so harmless font warnings from NASA PDFs no
   longer reach the console.

# v6 integration, 15 November 2026

1. **T1 (Amr Morgan, BASS v6) is live.** The package from `contributions/BASS_Python_AmrProject_v6.zip` is in
   `flame-in-freefall-kit/analysis/T1/` (the unfilled template is archived). The site now shows 12 T1 findings,
   9 charts, the track paragraph and limits, and Amr answers his 11 test questions (4 marked not answerable).
2. **Build fixes found while integrating it** (`build_site_data.py`):
   - charts were copied to `data/files/<track>/<file>`; PSI-25 and PSI-26 ship the same file names, so one
     record showed the other's charts. Now `data/files/<track>/<PSI-ID>/`, and the folder is rebuilt each run;
   - captions: `captions.md` in any case, `Chart name: caption` lines and `<chart>_caption.txt` files are read;
     other caption lines become one source note under the charts;
   - `test_questions.md` in the T1 one-line format was ignored (0 questions); both formats are read now;
   - the first two lines of `track_paragraph.md` / `limitations.md` were always dropped, which would have cut
     T1's first sentence; only a title line is removed now;
   - a card with any `verified_by` text made the site print "checked against the PSI page". T1's says "User
     screenshots; reviewer confirmation pending". The site now prints the card's own words, or "record not yet
     checked against the PSI page";
   - `publications`, `objectives`, `approach` are type-checked;
   - findings get a `rows_display`: T1 lists up to 129 row references (2,200 characters); the cards and the
     research table show the same set as ranges ("as run matrix!4-68, 70-84, 89-129 (121 rows)"); the CSV
     download keeps the full list.
3. **Document viewer in older browsers.** PDF.js 6.5 calls built-ins that browsers added in 2025
   (`Uint8Array.prototype.toHex`, `Map.prototype.getOrInsertComputed` ...), so before Chrome/Edge 140 the viewer
   fell back to the native PDF. `assets/js/pdf-compat.mjs` (page) and `pdf-worker-compat.mjs` (worker) add them
   only when missing; the vendored PDF.js files are unchanged. Verified: all three documents render in Chromium 129.
4. **Small fixes.** Amr's greeting no longer says his findings are "on their way"; an inline empty favicon removes
   the 404 every page load logged; the envelope figure's source path follows its move to `docs/reports/`.

# v5 fixes, 15 November 2026

1. **T6 world label.** PSI-60's track card holds the verification placeholder `"acronym": "unconfirmed"`
   (NASA's record lists no acronym), and the build copied it into the display name, so the T6 world showed
   an "UNCONFIRMED" badge. `build_site_data.py` now never uses placeholder words as a display name; the
   site falls back to the PSI ID ("PSI-60"). The card itself and every other "unconfirmed" verification
   field (versions, licence, publication links) are unchanged and still shown where they were. Chat
   questions also fall back to the PSI ID.
2. **Experiment selectors (Results).** Experiment A carried the `filters` container class, which added a
   bottom margin and pushed it out of line. Both are now the same native `<select>` in a HUD frame:
   label above, 46 px tall, chevron, hover / focus-visible / disabled / selected-option states, full
   experiment title under each control, two columns on wide screens and stacked below 640 px.
3. **Results charts.** Cause: every material or flight click called a global `FIF.destroyCharts()` that
   destroyed all three charts and rebuilt them, so all of them went blank and regrew from zero (measured:
   0 painted pixels in all three canvases for the first frame after each click; under rapid clicks they
   stayed blank or half-drawn). Now each canvas has one `FIF.ChartSlot` owned by the Results view: a new
   selection updates that chart in place, an empty selection shows "No data for this selection", a
   missing library or a data error shows an explanatory message, and the view destroys only its own
   charts when it is left. The router no longer flushes a global chart list.
4. **Crew name.** "Khaled Adwi" corrected to **Khaled Adawi** in `content/characters.json` (the source of
   `data/site-data.js`, rebuilt) and in the kit and pipeline text. IDs, routes and file keys stay `adwi`.

# Flame in Freefall — cinematic universe, 15 November 2026 (v4)

Direction: the universe looks realistic, the interface feels like a game. Navigation is spatial
(fly to a world, travel back) instead of tabs. Scientific content, routes and research features are
unchanged; the original Retro look stays available.

## References

- Video 1 (rs69.dev, supplied recording, watched frame by frame): nebula and a large lit planet behind
  centred display type; content reveals as you scroll; each project is a celestial object that sits on
  alternating sides with its card and an ENTER button. Used for the Briefing scroll story.
- Video 2 (seunghyuk.com, supplied recording): a hub with labelled spokes that sway with the cursor and
  carry travelling dots; a 3D constellation of labelled nodes; a horizontal-line transition between
  scenes; side cues ("< MAIN", "PORTFOLIO >"); a sound toggle in words. Used for the mission map, the
  scanline route transition, the edge navigation and the toggles.
- airshifumi.hands.agency (opened in the in-app browser): layered foreground/background parallax and a
  slow title reveal. Informed the depth layers (far sky, near dust, worlds, interface).
- The Pinterest pin could not be retrieved (robots disallowed). Nothing here claims to match it.

## What changed

1. **Universe engine** (`assets/js/space-engine.js`, new). One persistent WebGL1 canvas behind every
   page: procedural nebula rendered to a low-resolution buffer and re-rendered only when the view
   changes; 2,600 far stars and 520 near dust points for parallax; a mission star with limb darkening and
   a restrained corona; six worlds and 20 experiment moons drawn as lit sphere impostors with 3D noise
   surfaces (ocean world with clouds and specular sea, desert with canyons, banded gas giant with a storm,
   fractured ice moon, volcanic world whose fissures glow on the night side, cratered moon), axial
   rotation independent of orbits, atmospheric rims and halos, light from the star. The camera drifts
   slowly, follows the pointer slightly, responds to scroll, and travels between scenes with
   interruptible tweens. Resolution is capped (DPR ≤ 1.5) and lowered automatically when frames are
   slow. Rendering stops while the tab is hidden. Retro view renders the same scene at low resolution
   with posterised colour over the original pixel starfield. Without WebGL a 2D canvas takes over.
2. **Briefing** is a scroll story: hero over a world, the "why", the guide (who starts talking when you
   reach him), then each world flies past on alternating sides with its scientist, experiments,
   publication status and ENTER WORLD, then the route.
3. **Explore is the mission map.** Accessible buttons follow the worlds; orbits, network spokes with
   travelling pulses and game reticles are drawn on an overlay. Hover or focus previews a compact card
   beside the world (placed away from the star); click approaches: the camera flies in, the interface
   fades, then the profile route opens with the camera already there. Hover, focus and preview stop
   orbital motion. Drag empty space to orbit the system; arrow keys move between worlds; touch selects
   on first tap and approaches on the second; phones get a focused selector with PREV/NEXT and swipes.
   The crew directory remains below as the no-animation alternative.
4. **Profile = landing deck.** The world fills the right side; the scientist's panel lists the
   experiments as moons. Hovering or focusing an experiment marks its moon in orbit, the scientist turns
   and points, and the line reports that experiment's real number of findings.
5. **Travel and history.** Every route maps to a camera scene (record and lab pull back from the owner's
   world). URLs are normal hashes. Returning to Explore restores the selected world, camera angle,
   orbit pause, scroll position and open details; the guide offers to continue to the next world once.
6. **Game controls.** `hud-btn` with hover, focus, pressed depth, selected and disabled states; console
   corners and telemetry; edge cues to the previous/next journey stop; scanline route entry.
7. **Characters.** States idle (big sprites float), speaking (only the speaker moves its mouth),
   waiting (visor scan), done (nod); blinking; eyes and pointing arm follow `look`. Reactions are tied
   to events: selecting or returning on the map, hovering an experiment, changing a lab parameter
   (with the calculated pulse position). `CREW: QUIET` turns them off.
8. **Crew conversation.** A message slot appears the moment a greeting or question is requested, so
   the log keeps request order while earlier messages are still typing; one speaker at a time; the
   recipient is captured at submission; a failed request marks its own slot and the queue continues;
   switching back to a character says a short "here again" instead of repeating the greeting.
9. **Answer visuals.** Answers citing F-T3-1, F-T3-2 or F-T3-3/4/5 can open a MEASURED view built from
   the same flight-test rows as the Results page. Transport answers (F-T3-16/17/20) can open the
   CALCULATED transport view. Each view is labelled measured or calculated.
10. **Lab model card**: model, purpose, parameters with units and bounds (from the validation schema),
    equation, assumptions, limitations, calibration status (not calibrated) and the AI's role.
11. **Document viewport.** PDF.js 6.5.438 is bundled (no CDN). Frame, PREVIOUS/NEXT, counter, page,
    zoom, fit width, keyboard (arrows, PageUp/Down, +/−), swipes on the frame only, loading percentage,
    error fallback, accessible page text and download. The three files are labelled as two NASA
    documents and one project figure, not as Shorts.

## Science boundaries

The universe is illustrative: fictional worlds stand for research tracks. Measured values come only
from the NASA tables (Results, Research, MEASURED views). The lab's 1-D advection–diffusion model is an
educational transport lesson; it is not calibrated to the SAME/SAME-R hardware and predicts no detector
response or alarm. The offline assistant matches saved questions and parses bounded lab commands; no
model produces numbers.

## Verification

Node tests (no browser), all passing: `planet`, `conversation`, `lab-config`, `expedition` (routes,
model card, bundled PDF.js, local assets), `scene-lifecycle` (mission map: selection, keyboard, hover
stabilisation, touch select-then-approach, navigation, cleanup, restored view, one return reaction) and
`universe` (2D fallback, body graph, world framing on both sides, home keyframes, map framing,
reduced-motion travel).

Browser test (`tests/browser.e2e.cjs`, Chromium with SwiftShader WebGL), passing: WebGL running;
hovered world holds still; hover preview; click approach and navigation; back restores the world and the
guide's return line; no frame callbacks accumulate over repeated route changes; lab reaction uses the
actual airflow; one speaker at a time; answer keeps its recipient after switching; view switch keeps the
lab value and the conversation; Escape closes the panel; PDF.js renders locally; rapid document changes
settle; no page errors; phone tap approaches; reduced motion keeps worlds still.

Also checked by screenshots: desktop and phone layouts, Retro view, 2D fallback (`--disable-webgl`),
file:// opening (universe works, PDFs fall back to the browser viewer). Not verified: real-GPU frame
rate, Safari and Firefox, real touch hardware, screen readers.

## Open points

- The DAFT fact sheet is an original NASA document and shows the NASA insignia inside the viewer. The
  competition asks teams not to use NASA logos; decide whether to keep the document, show only its
  first page text, or link to it instead.
- Members' own pixel portraits (with consent) can replace the generated astronauts.
