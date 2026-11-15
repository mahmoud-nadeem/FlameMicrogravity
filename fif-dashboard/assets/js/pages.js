/* Page renderers. Each returns { html, mount(root) -> cleanup }. Text comes from data/site-data.js. */
(function () {
  const FIF = window.FIF, D = FIF.data, esc = FIF.esc;
  const P = (FIF.pages = {});
  const recsOf = (t) => t.records.map((r) => D.records[r]).filter(Boolean);
  const findingsOf = (pred) => D.findings.filter(pred);
  const kindLegend = `<div class="legend-kinds"><span style="--k:var(--observed)">Observed in NASA data</span><span style="--k:var(--reported)">Reported by NASA or a paper</span><span style="--k:var(--inference)">Our interpretation</span></div>`;

  function findingCard(f) {
    return `<article class="finding ${f.kind}">
      <span class="fid">${esc(f.id)}</span><span class="label">${esc(FIF.KIND_LABEL[f.kind])}</span><span class="conf">CONFIDENCE ${esc(f.confidence.toUpperCase())}</span>
      <p>${esc(f.statement)}</p>
      <details class="more"><summary>Caveat and source</summary><p>${esc(f.caveat)}</p><p class="small"><b>Source:</b> ${esc(f.source)}<br><b>Rows / page:</b> ${esc(f.rows_display || f.rows)}</p></details>
    </article>`;
  }
  P.findingCard = findingCard;

  // ---------------------------------------------------------------- briefing (home)
  // A scroll story: each section is a keyframe for the universe camera (space-engine.js).
  // Keys: 0 hero, 1 why, 2 guide, 3 crew title, 4..9 the six worlds, 10 the route.
  P.home = function () {
    const pj = D.project || {}, nRec = Object.keys(D.records).length, nF = D.findings.length, ready = D.tracks.filter((t) => t.ready).length;
    const worlds = D.tracks.map((t, i) => {
      const ch = FIF.characterForTrack(t.id) || {}, w = (FIF.worlds || [])[i] || { name: t.id, theme: "" };
      const n = findingsOf((f) => f.track === t.id).length, side = i % 2 ? "right" : "left";
      return `<section class="story-sec world-sec" data-k="${4 + i}" aria-labelledby="sw-${i}">
        <article class="story-copy ${side} world-card hud-panel">
          <p class="eyebrow">WORLD 0${i + 1} &middot; ${esc((w.theme || "").toUpperCase())} &middot; ${esc(t.id)}</p>
          <h2 class="display-2" id="sw-${i}">${esc(w.name)}</h2>
          <p class="world-member"><b>${esc(ch.name || "")}</b> &middot; ${esc(ch.role || "")}</p>
          <p class="status ${n ? "ready" : "wait"}">${n ? `${n} traceable findings published` : "Research package in progress &middot; experiment records available"}</p>
          <ul class="exp-tags">${recsOf(t).map((r) => `<li><a href="#/record/${esc(r.id)}">${esc(r.acronym || r.id)}</a></li>`).join("")}</ul>
          <div class="row"><a class="px-btn" href="#/profile/${esc(ch.id)}">ENTER WORLD &#9654;</a><button class="chip" data-ask="${esc(ch.id)}">ASK ${esc((ch.name || "").split(" ")[0].toUpperCase())}</button></div>
        </article>
      </section>`;
    }).join("");
    const steps = [
      ["01", "Briefing", "What this project is and why fire in space is different.", "#/"],
      ["02", "Explore", "Fly the mission map and meet each world's scientist.", "#/explore"],
      ["03", "Results", "Interactive charts: pick a material or an experiment.", "#/results"],
      ["04", "Research", "Every finding with its label, rows and caveats.", "#/research"],
      ["05", "Sources", "Every number traced to its NASA record.", "#/sources"],
    ];
    return {
      html: `<div class="story">
      <section class="story-sec hero-sec" data-k="0" aria-labelledby="hero-title">
        <div class="story-copy left">
          <p class="eyebrow">NASA SPACE APPS 2026 &middot; MISSION BRIEFING</p>
          <h1 class="display" id="hero-title">FLAME IN<br><span class="flame">FREEFALL</span></h1>
          <p class="tagline">${esc(pj.tagline || "")}</p>
          <div class="row"><a class="px-btn" href="#/explore">OPEN THE MISSION MAP &#9654;</a><button class="px-btn ghost" id="ask-guide">ASK THE GUIDE</button></div>
        </div>
        <a class="scroll-cue" href="#story-why" id="scroll-cue">SCROLL TO DESCEND <span aria-hidden="true">&#8595;</span></a>
      </section>
      <section class="story-sec" id="story-why" data-k="1" aria-labelledby="why-title">
        <div class="story-copy right">
          <p class="eyebrow" id="why-title">WHY THIS MATTERS</p>
          <p class="statement">Up here, fire does not rise.</p>
          ${(pj.intro || []).map((x) => `<p class="lede">${esc(x)}</p>`).join("")}
        </div>
      </section>
      <section class="story-sec" data-k="2" aria-label="Mission guide">
        <div class="story-copy left guide-block">
          <div class="guide-stage">${FIF.spriteHTML("guide", "big", "Guide character")}${FIF.dialogHTML("guide-dialog", FIF.character("guide").name.toUpperCase())}</div>
          <div class="stats">
            <div class="stat"><b>${nRec}</b><span>NASA experiment records</span></div>
            <div class="stat"><b>6</b><span>crew members, one world each</span></div>
            <div class="stat"><b>${nF}</b><span>traceable findings so far</span></div>
            <div class="stat"><b>${ready}/6</b><span>research packages published</span></div>
          </div>
        </div>
      </section>
      <section class="story-sec title-sec" data-k="3" aria-labelledby="crew-title">
        <div class="story-copy center">
          <p class="eyebrow">THE CREW</p>
          <h2 class="display-2" id="crew-title">SIX WORLDS<br>ONE MISSION</h2>
          <p class="lede">Each crew member took one group of NASA experiments, and each group became a world around the mission star. Keep scrolling to fly past them, or open the map.</p>
        </div>
      </section>
      ${worlds}
      <section class="story-sec final-sec" data-k="10" aria-labelledby="route-title">
        <div class="story-copy center">
          <p class="eyebrow">YOUR ROUTE</p>
          <h2 class="display-2" id="route-title">READY FOR<br>THE MAP?</h2>
          <div class="steps">${steps.map(([n, t, d, h]) => `<a class="step" href="${h}"><span class="n">LEVEL ${n}</span><h3>${t}</h3><p>${d}</p></a>`).join("")}</div>
          <p><a class="px-btn" href="#/explore">OPEN THE MISSION MAP &#9654;</a></p>
        </div>
      </section></div>`,
      mount(root) {
        const box = FIF.$("#guide-dialog", root), cv = FIF.$("canvas.sprite.big", root);
        const g = FIF.character("guide");
        FIF.$("#ask-guide", root).onclick = () => FIF.openChat("guide");
        FIF.$$("[data-ask]", root).forEach((b) => (b.onclick = () => FIF.openChat(b.dataset.ask)));
        const U = FIF.universe;
        const sections = FIF.$$(".story-sec", root);
        // Scroll position -> continuous camera keyframe (k may be fractional between sections).
        let frame = 0;
        const progress = () => {
          // k equals a section's key exactly when that section's centre is at the viewport centre.
          frame = 0;
          const mid = window.innerHeight * 0.5;
          const centres = sections.map((sec) => { const r = sec.getBoundingClientRect(); return r.top + r.height / 2; });
          let k = +sections[0].dataset.k;
          for (let i = 0; i < sections.length; i++) {
            if (centres[i] > mid) {
              if (i > 0) { const a = +sections[i - 1].dataset.k, b = +sections[i].dataset.k; k = a + (b - a) * Math.max(0, Math.min(1, (mid - centres[i - 1]) / Math.max(1, centres[i] - centres[i - 1]))); }
              break;
            }
            k = +sections[i].dataset.k;
          }
          if (U && U.setHomeProgress) U.setHomeProgress(k);
        };
        const onScroll = () => { if (!frame) frame = requestAnimationFrame(progress); };
        window.addEventListener("scroll", onScroll, { passive: true });
        window.addEventListener("resize", onScroll);
        progress();
        // Sections reveal as they arrive; the guide starts talking when you reach it.
        let talked = false;
        const io = new IntersectionObserver((entries) => entries.forEach((e) => {
          if (!e.isIntersecting) return;
          e.target.classList.add("in-view");
          if (!talked && e.target.contains(box)) {
            talked = true;
            FIF.runDialog(box, [g.greeting, "Fire in space does not rise. Smoke drifts with the air, flames grow round and slow, and detectors must catch it all.",
              "Each crew member studied one group of NASA experiments. Scroll on to fly past their worlds, or open the mission map."], "guide", [cv]);
          }
        }), { threshold: 0.25 });
        sections.forEach((s) => io.observe(s));
        return () => { io.disconnect(); window.removeEventListener("scroll", onScroll); window.removeEventListener("resize", onScroll); cancelAnimationFrame(frame); root.querySelector(".dialog .txt")?._finishTyping?.(); };
      },
    };
  };

  // ---------------------------------------------------------------- crew directory (accessible list of every world)
  P.crewDirectory = function () {
    return {
      html: `<div class="grid">${D.tracks.map((t, i) => {
        const ch = FIF.characterForTrack(t.id) || {}, n = findingsOf((f) => f.track === t.id).length, w = (FIF.worlds || [])[i] || {};
        return `<article class="panel track-card">
          <div class="track-head">${FIF.spriteHTML(ch.id, "mid", ch.name)}<div><span class="tid">${esc(t.id)} &middot; ${esc(w.name || "")}</span><h3>${esc(ch.name)}</h3><p class="small muted">${esc(ch.role)}</p></div></div>
          <span class="badge ${t.ready ? "ready" : "wait"}">${t.ready ? n + " FINDINGS" : "COMING SOON"}</span>
          ${recsOf(t).map((r) => `<a class="record-link" href="#/record/${esc(r.id)}"><b>${esc(r.acronym || r.id)}</b><br><span class="small">${esc(r.title)}</span></a>`).join("")}
          <div class="row"><a class="chip" href="#/profile/${esc(ch.id)}">EXPLORE PROFILE &#9654;</a><button class="chip" data-ask="${esc(ch.id)}">ASK ${esc((ch.name || "").split(" ")[0].toUpperCase())}</button></div>
        </article>`; }).join("")}</div>`,
      mount(root) { FIF.paintSprites(root); FIF.$$("[data-ask]", root).forEach((b) => (b.onclick = () => FIF.openChat(b.dataset.ask))); },
    };
  };

  // ---------------------------------------------------------------- one experiment
  P.record = function (id) {
    const r = D.records[id];
    if (!r) return { html: `<h1 class="page-title">NOT FOUND</h1><p><a href="#/explore">Back to the experiments</a></p>`, mount() {} };
    const t = FIF.track(r.track), ch = FIF.characterForTrack(r.track) || {};
    const fs = findingsOf((f) => f.record === id);
    const charts = (t.charts || []).filter((c) => c.record === id);
    const smoke = ["PSI-101", "PSI-102"].includes(id);
    const years = [r.start, r.end].filter(Boolean).map((d) => String(d).slice(0, 10)).join(" to ");
    return {
      html: `<div class="exp-toolbar deck-nav"><a class="hud-btn" href="#/profile/${esc(ch.id)}">&#9664; ${esc((ch.name || "CREW").split(" ")[0].toUpperCase())}'S WORLD</a><a class="hud-btn" href="#/explore">MISSION MAP</a>${["PSI-101", "PSI-102", "PSI-47"].includes(id) ? `<a class="px-btn" href="#/lab/${esc(id)}">LAUNCH SIMULATION &#9654;</a>` : ""}</div>
      <section class="deck-sheet"><p class="eyebrow">LEVEL 03 &middot; UNDERSTAND &middot; ${esc(r.track)}</p>
      <h1 class="page-title">${esc(r.acronym || r.id)}</h1><p class="lede">${esc(r.title)}</p>
      <p class="small muted">${esc(r.platform || "")}${years ? " &middot; " + esc(years) : ""} &middot; <a href="${esc(r.page)}" target="_blank" rel="noopener">NASA PSI page ${esc(r.id)}</a></p>
      <section class="block grid">
        <div class="panel"><h2>WHAT THEY WANTED TO KNOW</h2><p>${esc(r.objectives || "Coming soon from " + (ch.name || "the crew") + ".")}</p></div>
        <div class="panel"><h2>WHAT THEY DID</h2><p>${esc(r.approach || "Coming soon.")}</p></div>
        <div class="panel"><h2>YOUR CREW CONTACT</h2><div class="row">${FIF.spriteHTML(ch.id, "mid", ch.name)}<div><b>${esc(ch.name)}</b><p class="small muted">${esc(ch.role)}</p></div></div>
          <button class="px-btn" data-ask="${esc(ch.id)}">ASK ${esc((ch.name || "").split(" ")[0].toUpperCase())}</button></div>
      </section>
      ${smoke ? `<section class="block panel"><h2>SEE IT: SMOKE IN ORBIT VS ON EARTH</h2>
        <div class="sim"><div><p class="sim-mode" id="sim-mode"></p><canvas id="sim-canvas" aria-label="Pixel illustration of smoke leaving a heated sample and drifting to a detector"></canvas>
          <p class="small muted">Left: heated material sample. Right: smoke detector.</p></div>
        <div><div class="seg"><button class="chip" id="sim-orbit" aria-pressed="true">ORBIT</button><button class="chip" id="sim-earth" aria-pressed="false">EARTH</button></div>
        <label for="sim-flow">Air flow: <b id="sim-flow-out">8 cm/s</b></label><input id="sim-flow" type="range" min="0" max="8" step="1" value="8">
        <label>Smoke reaching the detector</label><div class="meter"><i id="sim-meter"></i></div>
        <label>Average particle size near the detector: <b id="sim-avg">-</b></label>
        <button class="chip" id="sim-reset">RESTART</button>
        <p class="small muted">An illustration, not a physics model. It shows what the flight data report: smoke keeps growing as it ages (F-T3-1) and grows larger when the air barely moves (F-T3-2). On Earth smoke rises; in orbit it only follows the air.</p></div></div></section>` : ""}
      <section class="block"><h2>WHAT THE DATA SHOW</h2>${fs.length ? kindLegend + "<br>" + fs.map(findingCard).join("") : `<p class="muted">${esc(ch.name || "The crew")} is still working on this experiment.</p>`}</section>
      ${charts.length ? `<section class="block"><h2>CHARTS FROM THE ANALYSIS</h2><div class="grid">${charts.map((c) => `<figure class="static-chart"><img src="${esc(c.file)}" alt="${esc(c.caption)}" loading="lazy"><figcaption>${esc(c.caption)}</figcaption></figure>`).join("")}</div>${charts[0].note ? `<p class="chart-note">${esc(charts[0].note)}</p>` : ""}</section>` : ""}
      <section class="block" id="rag-notes" aria-labelledby="rag-title" hidden>
        <h2 id="rag-title">CREW NOTES (RAG)</h2>
        <p class="small muted" id="rag-summary"></p>
        <div class="filters"><input id="rag-q" type="search" placeholder="Search these notes" aria-label="Search the crew notes for this experiment"></div>
        <div id="rag-list"></div>
        <details class="more" id="rag-rules" hidden><summary>How the author says to use these notes</summary><div></div></details>
      </section>
      <p><a class="px-btn ghost" href="#/research?record=${esc(id)}">SEE THE NUMBERS AND SOURCES &#9654;</a></p></section>`,
      mount(root) {
        FIF.paintSprites(root);
        FIF.$$("[data-ask]", root).forEach((b) => (b.onclick = () => FIF.openChat(b.dataset.ask)));
        let alive = true;
        if (window.FIF_RAG) window.FIF_RAG.ready().then(() => { if (alive) ragNotes(root, id, ch); });
        if (!smoke) return () => { alive = false; };
        const sim = FIF.SmokeSim(FIF.$("#sim-canvas", root), { flow: FIF.$("#sim-flow", root), flowOut: FIF.$("#sim-flow-out", root), meter: FIF.$("#sim-meter", root),
          avg: FIF.$("#sim-avg", root), earth: FIF.$("#sim-earth", root), orbit: FIF.$("#sim-orbit", root), reset: FIF.$("#sim-reset", root), mode: FIF.$("#sim-mode", root) });
        return () => { alive = false; sim.stop(); };
      },
    };
  };

  // The experiment's RAG folder (rag/<PSI-ID>_<NAME>/, the texts its crew member answers from), readable on the page:
  // passages in the author's order with chunk ID, evidence label and source; data rows are counted and searchable;
  // the author's instructions for using the corpus are shown separately and are never used as chat answers.
  function ragNotes(root, id, ch) {
    const R = window.FIF_RAG, sec = FIF.$("#rag-notes", root);
    if (!R || !sec) return;
    const topic = Object.keys(R.data.topics).find((t) => t.toUpperCase().startsWith(id.toUpperCase() + "_"));
    const all = topic ? R.data.topics[topic] : [];
    if (!all.length) return;
    sec.hidden = false;
    const notes = all.filter((c) => c.kind !== "policy"), rules = all.filter((c) => c.kind === "policy");
    const n = (k) => all.filter((c) => c.kind === k).length;
    FIF.$("#rag-summary", root).textContent = `${all.length} passages from ${ch.name || "the crew"}'s RAG folder ${topic}: ${n("text")} notes, ` +
      `${n("guidance")} usage cautions, ${n("record")} data rows. These are the texts ${((ch.name || "").split(" ")[0]) || "the crew member"} answers from in the chat, copied verbatim from the team's corpus files.`;
    const item = (c) => `<details class="more rag-note"><summary><b>${esc(c.title)}</b> <span class="muted">&middot; ${esc(c.id)}${c.evidence ? " &middot; " + esc(c.evidence.replace(/_/g, " ")) : ""}${c.kind === "guidance" ? " &middot; usage caution" : c.kind === "record" ? " &middot; data row" : ""}</span></summary>
      <p class="rag-text">${esc(c.text.length > 2400 ? c.text.slice(0, 2400) + " …" : c.text)}</p>
      <p class="small muted">Source: ${esc(c.source)}${c.location ? " (" + esc(c.location) + ")" : ""}${c.shared && c.shared.length ? " &middot; also in " + esc(c.shared.join(", ")) : ""}${c.url ? ` &middot; <a href="${esc(c.url)}" target="_blank" rel="noopener">original source</a>` : ""}</p></details>`;
    const list = FIF.$("#rag-list", root), input = FIF.$("#rag-q", root), PAGE = 12;
    const render = () => {
      const q = input.value.trim().toLowerCase();
      const hits = notes.filter((c) => !q || (c.title + " " + c.id + " " + c.text).toLowerCase().includes(q));
      const prose = hits.filter((c) => c.kind !== "record"), rows = hits.filter((c) => c.kind === "record");
      const shown = (q ? hits : prose).slice(0, PAGE);
      list.innerHTML = (shown.length ? shown.map(item).join("") : `<p class="muted">No passage matches "${esc(q)}".</p>`) +
        `<p class="small muted">${q ? `${hits.length} matching passages` : `${prose.length} notes`}${(q ? hits : prose).length > PAGE ? `, first ${PAGE} shown` : ""}` +
        `${!q && rows.length ? `; ${rows.length} data rows (search to see them)` : ""}.</p>`;
    };
    input.addEventListener("input", render);
    render();
    if (rules.length) {
      const box = FIF.$("#rag-rules", root); box.hidden = false;
      box.querySelector("div").innerHTML = rules.map((c) => `<p class="small"><b>${esc(c.id)}</b> (${esc(c.source)}): ${esc(c.text)}</p>`).join("");
    }
  }

  // ---------------------------------------------------------------- results (interactive)
  P.results = function () {
    const ds = D.datasets.same_tests;
    const recs = Object.values(D.records);
    const crew = D.tracks.filter((t) => (t.results || []).length);
    const opt = (sel) => recs.map((r) => `<option value="${esc(r.id)}" ${r.id === sel ? "selected" : ""}>${esc(r.track)} &middot; ${esc(r.acronym || r.id)}</option>`).join("");
    return {
      html: `<p class="eyebrow">LEVEL 04 &middot; RESULTS</p><h1 class="page-title">EXPLORE THE RESULTS</h1>
      <p class="lede">Pick materials and a flight: every chart updates. Each dot is one NASA flight test; hover it to see its source row.</p>
      ${ds ? `<section class="block panel">
        <h2>SMOKE FROM OVERHEATED SPACECRAFT MATERIALS (T3)</h2>
        <div class="row" id="mat-chips">${ds.materials.map((m) => `<button class="chip" aria-pressed="true" data-m="${esc(m)}" style="--chip:${FIF.MATERIAL_COLORS[m]}"><span class="dot"></span>${esc(m.toUpperCase())}</button>`).join("")}</div>
        <div class="row" style="margin-top:10px"><span class="small muted">Flight:</span>
          <button class="chip" data-mission="SAME-R" aria-pressed="true">SAME-R 2010</button><button class="chip" data-mission="SAME" aria-pressed="false">SAME 2007</button>
          <span class="small muted">The two flights are shown separately: they used partly different instruments (F-T3-5).</span></div>
        <div class="grid" style="margin-top:16px">
          <div><h3>Fresh smoke particle size</h3><div class="chart-box"><canvas id="c-size"></canvas></div><p class="chart-note">Fresh smoke, 8 cm/s air flow, all heater settings. Source: ${esc(ds.source)}.</p></div>
          <div><h3>The same smoke after aging</h3><div class="chart-box"><canvas id="c-aging"></canvas></div><p class="chart-note">Median of paired tests: each fresh test and its re-measurement after aging (F-T3-1).</p></div>
          <div><h3>Weak vs normal air flow</h3><div class="chart-box"><canvas id="c-flow"></canvas></div><p class="chart-note">Fresh smoke, only heater settings that have both flows (F-T3-2). Small groups.</p></div>
        </div></section>` : ""}
      ${crew.length ? `<section class="block panel" id="crew-results">
        <h2>RESULTS FROM THE CREW'S ANALYSES</h2>
        <p class="small">Charts of numbers the crew computed from NASA tables, transcribed from their findings. Each chart names the findings it shows; open them on the Research page for the rows, labels and caveats.</p>
        <div class="row" id="cr-tracks"><span class="small muted">Tracks:</span>${crew.map((t) => `<button class="chip" aria-pressed="true" data-track="${esc(t.id)}">${esc(t.id)} &middot; ${esc((FIF.characterForTrack(t.id) || {}).name || "")}</button>`).join("")}</div>
        <div class="grid" style="margin-top:16px">${crew.flatMap((t) => t.results.map((c) => `<div class="cr-chart" data-track="${esc(t.id)}">
          <h3>${esc(c.title)}</h3>
          ${c.datasets.length > 1 ? `<div class="row cr-series">${c.datasets.map((d) => `<button class="chip" aria-pressed="true" data-series="${esc(d.label)}">${esc(d.label)}</button>`).join("")}</div>` : ""}
          <div class="chart-box"><canvas id="cr-${esc(c.id)}"></canvas></div>
          <p class="chart-note">${esc(c.note)} Findings: ${c.findings.map((f) => `<a href="#/research?q=${esc(f)}">${esc(f)}</a>`).join(", ")}.</p></div>`)).join("")}</div>
        <p class="small muted" id="cr-empty" hidden>No track selected: switch one on above.</p></section>` : ""}
      <section class="block panel">
        <h2>COMPARE TWO EXPERIMENTS</h2>
        <div class="cmp-pickers">${[["a", "A", "PSI-101"], ["b", "B", "PSI-47"]].map(([k, L, id]) => `
          <div class="cmp-field">
            <label class="cmp-label" for="cmp-${k}"><span class="cmp-key" aria-hidden="true">${L}</span>EXPERIMENT ${L}</label>
            <div class="hud-select"><select id="cmp-${k}" aria-describedby="cmp-${k}-title">${opt(id)}</select></div>
            <p class="cmp-title" id="cmp-${k}-title">${esc((D.records[id] || {}).title || "")}</p>
          </div>`).join("")}</div>
        <div class="grid" id="cmp-out" style="margin-top:14px"></div>
      </section>`,
      mount(root) {
        const sel = { materials: ds ? [...ds.materials] : [], mission: "SAME-R" };
        // This view owns exactly these three charts; each slot updates only its own canvas.
        const slots = ds ? [["#c-size", FIF.chartSizeByMaterial], ["#c-aging", FIF.chartAging], ["#c-flow", FIF.chartFlow]]
          .map(([q, build]) => ({ slot: FIF.ChartSlot(FIF.$(q, root)), build })) : [];
        const draw = () => slots.forEach(({ slot, build }) => slot.render(() => build(ds, sel)));
        // crew results: one slot per chart; series chips filter that chart, track chips show or hide whole charts
        const crewSlots = crew.flatMap((t) => t.results.map((c) => {
          const box = FIF.$(`#cr-${c.id}`, root).closest(".cr-chart");
          const s = { c, box, slot: FIF.ChartSlot(FIF.$(`#cr-${c.id}`, root)), series: c.datasets.map((d) => d.label) };
          s.draw = () => { if (!box.hidden) s.slot.render(() => FIF.chartCrewResult(c, s)); };
          FIF.$$(".cr-series .chip", box).forEach((b) => (b.onclick = () => {
            b.setAttribute("aria-pressed", String(b.getAttribute("aria-pressed") !== "true"));
            s.series = FIF.$$(".cr-series .chip", box).filter((x) => x.getAttribute("aria-pressed") === "true").map((x) => x.dataset.series); s.draw(); }));
          return s;
        }));
        FIF.$$("#cr-tracks .chip", root).forEach((b) => (b.onclick = () => {
          b.setAttribute("aria-pressed", String(b.getAttribute("aria-pressed") !== "true"));
          const on = FIF.$$("#cr-tracks .chip", root).filter((x) => x.getAttribute("aria-pressed") === "true").map((x) => x.dataset.track);
          crewSlots.forEach((s) => { s.box.hidden = !on.includes(s.box.dataset.track); s.draw(); });
          FIF.$("#cr-empty", root).hidden = on.length > 0; }));
        crewSlots.forEach((s) => s.draw());
        FIF.$$("#mat-chips .chip", root).forEach((b) => (b.onclick = () => {
          const on = b.getAttribute("aria-pressed") !== "true"; b.setAttribute("aria-pressed", String(on));
          sel.materials = FIF.$$("#mat-chips .chip", root).filter((x) => x.getAttribute("aria-pressed") === "true").map((x) => x.dataset.m); draw(); }));
        FIF.$$("[data-mission]", root).forEach((b) => (b.onclick = () => {
          FIF.$$("[data-mission]", root).forEach((x) => x.setAttribute("aria-pressed", String(x === b))); sel.mission = b.dataset.mission; draw(); }));
        const cmp = () => {
          const side = (id) => { const r = D.records[id], fs = findingsOf((f) => f.record === id);
            return `<div class="panel"><h3>${esc(r.acronym || r.id)}</h3><p class="small muted">${esc(r.title)}</p>
              <p class="small"><b>Platform:</b> ${esc(r.platform || "-")}<br><b>Dates:</b> ${esc([r.start, r.end].filter(Boolean).join(" to ") || "-")}<br><b>Findings:</b> ${fs.length}</p>
              <p class="small">${esc(r.objectives || "Objectives coming soon.")}</p>
              ${fs.slice(0, 3).map((f) => `<p class="small">&#9656; ${esc(f.statement)} <span class="muted">(${esc(f.id)})</span></p>`).join("")}</div>`; };
          ["a", "b"].forEach((k) => { const r = D.records[FIF.$("#cmp-" + k, root).value]; FIF.$(`#cmp-${k}-title`, root).textContent = r ? r.title : ""; });
          FIF.$("#cmp-out", root).innerHTML = side(FIF.$("#cmp-a", root).value) + side(FIF.$("#cmp-b", root).value);
        };
        FIF.$("#cmp-a", root).onchange = cmp; FIF.$("#cmp-b", root).onchange = cmp;
        draw(); cmp();
        return () => { slots.forEach(({ slot }) => slot.destroy()); crewSlots.forEach((s) => s.slot.destroy()); };
      },
    };
  };

  // ---------------------------------------------------------------- research (detailed)
  P.research = function (params) {
    const tracks = D.tracks.map((t) => t.id), recs = Object.keys(D.records);
    return {
      html: `<p class="eyebrow">FOR RESEARCHERS</p><h1 class="page-title">FINDINGS, NUMBERS AND SOURCES</h1>
      <p class="lede">Every finding with its label, confidence, NASA source file and exact rows (Excel row number, or line number with the header as 1).</p>
      <div class="filters">
        <input id="f-q" type="search" placeholder="Search findings or ID" value="${esc(params.get("q") || "")}" aria-label="Search">
        <select id="f-track" aria-label="Track"><option value="">All tracks</option>${tracks.map((t) => `<option>${t}</option>`).join("")}</select>
        <select id="f-rec" aria-label="Experiment"><option value="">All experiments</option>${recs.map((r) => `<option ${params.get("record") === r ? "selected" : ""}>${r}</option>`).join("")}</select>
        <select id="f-kind" aria-label="Label"><option value="">All labels</option><option value="observed">Observed in data</option><option value="reported">Reported by NASA</option><option value="inference">Our inference</option></select>
        <button class="chip" id="f-csv">DOWNLOAD CSV</button>
      </div>
      <p class="small muted" id="f-count"></p>
      <div class="table-wrap"><table><thead><tr><th>ID</th><th>FINDING</th><th>LABEL</th><th>CONF.</th><th>SOURCE FILE</th><th>ROWS / PAGE</th><th>CAVEAT</th></tr></thead><tbody id="f-body"></tbody></table></div>
      ${D.datasets.same_tests ? `<section class="block"><h2>DATA BEHIND THE CHARTS</h2><p class="small">SAME and SAME-R flight tests with a particle size (${D.datasets.same_tests.rows.length} rows, with workbook row numbers). <button class="chip" id="d-csv">DOWNLOAD</button></p></section>` : ""}`,
      mount(root) {
        let shown = [];
        const render = () => {
          const q = FIF.$("#f-q", root).value.trim().toLowerCase(), tr = FIF.$("#f-track", root).value, rc = FIF.$("#f-rec", root).value, k = FIF.$("#f-kind", root).value;
          shown = D.findings.filter((f) => (!tr || f.track === tr) && (!rc || f.record === rc) && (!k || f.kind === k) &&
            (!q || (f.id + " " + f.statement + " " + f.caveat + " " + f.source).toLowerCase().includes(q)));
          FIF.$("#f-count", root).textContent = `${shown.length} of ${D.findings.length} findings`;
          FIF.$("#f-body", root).innerHTML = shown.map((f) => `<tr><td><b>${esc(f.id)}</b><br><a href="#/record/${esc(f.record)}">${esc(f.record)}</a></td><td>${esc(f.statement)}</td>
            <td><span class="label" style="--kind:var(--${f.kind});margin:0">${esc(FIF.KIND_LABEL[f.kind])}</span></td><td>${esc(f.confidence)}</td>
            <td class="src">${esc(f.source)}</td><td class="src">${esc(f.rows_display || f.rows)}</td><td class="small">${esc(f.caveat)}</td></tr>`).join("");
        };
        ["#f-q", "#f-track", "#f-rec", "#f-kind"].forEach((s) => FIF.$(s, root).addEventListener("input", render));
        FIF.$("#f-csv", root).onclick = () => FIF.downloadCSV("flame-in-freefall-findings.csv", shown.map(({ id, track, record, statement, label, confidence, source, rows, caveat }) => ({ id, track, record, statement, label, confidence, source, rows, caveat })));
        const d = FIF.$("#d-csv", root); if (d) d.onclick = () => FIF.downloadCSV("same-same-r-flight-tests.csv", D.datasets.same_tests.rows.map((r) => Object.assign({ source_file: D.datasets.same_tests.source }, r)));
        render();
      },
    };
  };

  // ---------------------------------------------------------------- sources
  P.sources = function () {
    const general = [
      ["NASA Physical Sciences Informatics (PSI) repository", "https://psi.nasa.gov/physci/repo/"],
      ["NASA, What Is Microgravity? (Grades 5-8)", "https://www.nasa.gov/learning-resources/for-kids-and-students/what-is-microgravity-grades-5-8/"],
    ];
    return {
      html: `<p class="eyebrow">LEVEL 05 &middot; SOURCES</p><h1 class="page-title">WHERE EVERY NUMBER COMES FROM</h1>
      <p class="lede">All experiment data come from NASA's PSI repository (CC0). Citations below are copied from each record's "Cite this Investigation" button where a crew member has checked the record.</p>
      <section class="block">${D.tracks.map((t) => `<h2>${esc(t.id)} &middot; ${esc((FIF.characterForTrack(t.id) || {}).name || "")}</h2>
        ${recsOf(t).map((r) => `<div class="panel" style="margin-bottom:10px"><b>${esc(r.acronym || r.id)}</b> &middot; ${esc(r.title)}
          <p class="cite">${r.citation ? esc(r.citation) : `${esc(r.title)}, NASA PSI Data Repository${r.doi ? ", https://doi.org/" + esc(r.doi) : ""}`}</p>
          <p class="small"><a href="${esc(r.page)}" target="_blank" rel="noopener">PSI page ${esc(r.id)}</a>${r.doi ? ` &middot; <a href="https://doi.org/${esc(r.doi)}" target="_blank" rel="noopener">DOI ${esc(r.doi)}</a>` : ""} &middot; licence ${esc(r.license || "see page")}${r.verified_by ? ` &middot; record check: ${esc(r.verified_by)}${r.verified_on ? ", " + esc(r.verified_on) : ""}` : " &middot; record not yet checked against the PSI page"}</p>
          ${(r.publications || []).length ? `<details class="more"><summary>${r.publications.length} publications listed on the record</summary>${r.publications.map((p) => `<p>${esc(p.title)}${p.link && p.link !== "unconfirmed" ? ` <a href="${esc(p.link)}" target="_blank" rel="noopener">link</a>` : ""}</p>`).join("")}</details>` : ""}
        </div>`).join("")}
        ${(t.publications || []).length ? `<p class="small muted">Documents read by the crew: ${t.publications.map(esc).join("; ")}</p>` : ""}`).join("")}</section>
      <section class="block panel"><h2>OTHER SOURCES AND CREDITS</h2>
        ${general.map(([n, u]) => `<p class="small">${esc(n)}: <a href="${u}" target="_blank" rel="noopener">${u}</a></p>`).join("")}
        <p class="small">Chart.js (MIT licence), PDF.js 6.5.438 by Mozilla (Apache 2.0 licence), Press Start 2P and VT323 fonts (SIL Open Font Licence), all bundled with the site so it works offline.</p>
        <p class="small">The universe (nebula, stars, the mission star and the six worlds) is original procedural code written for this project: no images or textures are copied. The worlds are fictional and stand for research tracks; they are not depictions of real planets.</p>
        <p class="small">${esc((D.project || {}).disclosure || "")}</p>
        <p class="small muted">Site data built ${esc(D.built || "")}.</p></section>`,
      mount() {},
    };
  };
})();
