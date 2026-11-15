/* Planet guide: when you land on a crew member's world (#/profile/<id>), that member's astronaut welcomes you and can show you
   around the sections that really exist on the page. The steps are built from the data and the rendered page; a step is
   dropped when its target is missing, so the guide never points at something that is not there.

   First visit: a fuller introduction with "Show me around". Later visits: a short welcome back with "Replay tour".
   Progress is stored per planet ("fif.tour"); "Reset tours" clears it. "Replay tour" stays in the page header.
   Narration goes through the site's shared conversation queue (FIF.voiceQueue, also used by the Crew panel), so the guide and
   the Crew never type at the same time. Every line carries the planet's token: lines queued for a planet you have left are
   dropped, and the panel lives inside the page, so leaving the planet removes it (and stops its typing). */
(function () {
  const F = window.FIF, P = F.pages, E = F.esc;
  const KEY = "fif.tour";
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } };
  const save = (v) => { try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) { /* storage unavailable: progress is not kept */ } };
  const DATASET_TRACK = { same_tests: "T3" };          // interactive Results charts exist only for these datasets
  let gen = 0;                                         // token of the planet currently guided
  // reset(): every planet; reset(id): one planet
  F.planetTour = { reset(id) { if (id) { const all = load(); delete all[id]; save(all); } else save({}); }, get progress() { return load(); }, get token() { return gen; } };

  function stepsFor(root, ch, t, w) {
    const recs = t.records.map((r) => F.data.records[r]).filter(Boolean);
    const fOf = (id) => F.data.findings.filter((f) => f.record === id).length;
    const n = F.data.findings.filter((f) => f.track === t.id).length, first = ch.name.split(" ")[0];
    const names = recs.map((r) => r.acronym || r.id);
    const rag = window.FIF_RAG && window.FIF_RAG.data && Object.keys(window.FIF_RAG.data.topics);
    const hasNotes = rag && recs.some((r) => rag.some((k) => k.toUpperCase().startsWith(r.id.toUpperCase() + "_")));
    const withCharts = recs.find((r) => (t.charts || []).some((c) => c.record === r.id));
    const labMoon = root.querySelector('.moon-link[data-lab="1"]');
    const docs = (window.FIF_SHORTS || []).filter((d) => (d.tracks || []).includes(t.id));
    const results = Object.keys(F.data.datasets || {}).some((k) => DATASET_TRACK[k] === t.id) || (t.results || []).length > 0;
    const S = [
      { id: "welcome", target: null, text: `Welcome to ${w.name}! I'm ${ch.name}, and this world is my track, ${t.id}: ${ch.role}. ` +
          (n ? `${n} traceable findings are published here.` : `My findings are not published yet, but every NASA record of my experiments is here.`) },
      { id: "experiments", target: ".moon-list", text: `Each moon is one NASA experiment I cover: ${names.join(", ")}. Open one to see what it did` +
          `${recs.some((r) => fOf(r.id)) ? ", its findings" : ""}${withCharts ? " and charts" : ""}${hasNotes ? ", and the crew notes I answer from" : ""}.` },
    ];
    if (withCharts) S.push({ id: "charts", target: `.moon-link[href="#/record/${withCharts.id}"]`,
      text: `${withCharts.acronym || withCharts.id} has charts from my analysis on its page, each with its caption and source.` });
    if (labMoon) S.push({ id: "lab", target: '.moon-link[data-lab="1"]', text: "This experiment has an interactive simulation: open it and press LAUNCH SIMULATION." });
    if (results) S.push({ id: "results", target: '#journey a[href="#/results"]', text: (t.results || []).length
      ? `The Results page has charts of my results: ${t.results.map((c) => c.title.split(":")[0]).filter((v, i, a) => a.indexOf(v) === i).join(", ")}. Switch series on and off; each chart names its findings.`
      : "The Results page has interactive charts of my flight data: pick materials and a flight." });
    if (n) S.push({ id: "evidence", target: "#pg-evidence", text: "The evidence table lists every finding with its label, source file, rows and caveat. You can download it as CSV." });
    if (docs.length) S.push({ id: "docs", target: "#pg-docs", text: `Original documents: ${docs.map((d) => `"${d.title}"`).join(", ")}. They open in the spacecraft viewport.` });
    S.push({ id: "notes", target: ".deck details.notes", text: n ? "Research notes and limitations: what my data can and cannot tell you." : "Research notes: what is still missing from my package." });
    S.push({ id: "ask", target: "#profile-ask", text: `Questions? Ask me here. I answer from my own notes and show where each answer comes from.` });
    return S.filter((s) => !s.target || root.querySelector(s.target) || document.querySelector(s.target));
  }

  const orig = P.profile;
  P.profile = function (id) {
    const page = orig(id);
    const ch = F.characters.find((c) => c.id === id), t = ch && F.track(ch.track);
    if (!t || !page.mount) return page;
    const i = F.data.tracks.findIndex((x) => x.id === t.id), w = (F.worlds || [])[i] || { name: t.id };
    const docs = (window.FIF_SHORTS || []).filter((d) => (d.tracks || []).includes(t.id));
    const n = F.data.findings.filter((f) => f.track === t.id).length;
    // real navigation targets for the tour, added next to the existing buttons
    let html = page.html.replace(`<a class="hud-btn" href="#/research?q=${E(t.id)}">EVIDENCE TABLE</a>`,
      `<a class="hud-btn" id="pg-evidence" href="#/research?q=${E(t.id)}">EVIDENCE TABLE</a>${docs.length ? `<a class="hud-btn" id="pg-docs" href="#/shorts">MISSION DOCUMENTS (${docs.length})</a>` : ""}`)
      .replace(`<span class="telemetry">ORBIT LOCKED`, `<button class="hud-btn" id="pg-replay" type="button">TOUR WITH ${E(ch.name.split(" ")[0].toUpperCase())}</button><span class="telemetry">ORBIT LOCKED`);
    html = html.replace(/(<a class="moon-link" href="#\/record\/(PSI-\d+)")/g, (m, a, psi) => ["PSI-101", "PSI-102", "PSI-47"].includes(psi) ? `${a} data-lab="1"` : a);
    html += `<aside class="planet-guide hud-panel" id="planet-guide" aria-label="Guide: ${E(ch.name)}" hidden>
      ${F.spriteHTML(ch.id, "full", ch.name + " in an astronaut suit")}
      <div class="pg-body"><span class="who">${E(ch.name.toUpperCase())} &middot; ${E(t.id)}</span>
        <p class="pg-text" aria-live="polite"></p><p class="pg-step small muted"></p>
        <div class="pg-actions"></div></div>
      <button class="pg-x icon-btn" type="button" aria-label="Close the guide">&times;</button></aside>`;
    const mount = page.mount;
    page.html = html;
    page.mount = (root) => {
      const c1 = mount(root);
      const c2 = guide(root, ch, t, w, n);
      return () => { if (c1) c1(); c2(); };
    };
    return page;
  };

  function guide(root, ch, t, w, n) {
    const token = ++gen;
    const panel = root.querySelector("#planet-guide"), text = panel.querySelector(".pg-text"), stepEl = panel.querySelector(".pg-step");
    const actions = panel.querySelector(".pg-actions"), cv = panel.querySelector("canvas.sprite");
    const voice = F.voiceQueue || (F.voiceQueue = F.createConversationQueue());
    const reduced = () => !!F.settings.reduceMotion;
    let steps = [], k = -1, line = 0, marked = null, alive = true;
    const prog = () => load()[ch.id] || {};
    const remember = (patch) => { const all = load(); all[ch.id] = Object.assign({}, all[ch.id], patch); save(all); };

    // one line at a time, in the shared queue; a line for an older step or another planet is dropped
    function say(s) {
      const my = ++line;
      if (text._finishTyping) text._finishTyping();
      text.textContent = "";
      return voice.add(async () => {
        if (!alive || token !== gen || my !== line || !panel.isConnected) return;
        await F.typeText(text, s, cv ? [cv] : [], ch.id);
      }).catch(() => {});
    }
    const btn = (label, fn, cls = "hud-btn") => { const b = document.createElement("button"); b.type = "button"; b.className = cls; b.textContent = label; b.onclick = fn; return b; };

    function unmark() { if (marked) { marked.classList.remove("pg-target"); marked.removeAttribute("data-pg-label"); marked = null; } }
    function mark(sel) {
      unmark();
      const el = sel && (root.querySelector(sel) || document.querySelector(sel));
      if (!el) return;
      marked = el; el.classList.add("pg-target");
      const r = el.getBoundingClientRect();
      if (r.top < 70 || r.bottom > window.innerHeight - 220) el.scrollIntoView({ block: "center", behavior: reduced() ? "auto" : "smooth" });
      if (cv && F.setSpriteState) {                                   // the guide turns and points toward the target
        const a = cv.getBoundingClientRect();
        F.setSpriteState(cv, { look: r.left + r.width / 2 >= a.left + a.width / 2 ? 1 : -1, gesture: "point" }, 2600);
      }
    }

    function open(intro) {
      panel.hidden = false; k = -1; unmark();
      steps = stepsFor(root, ch, t, w);
      actions.replaceChildren(
        btn(intro ? "SHOW ME AROUND" : "REPLAY TOUR", () => go(0), "px-btn"),
        btn(intro ? "NOT NOW" : "CLOSE", close));
      if (!intro) actions.append(btn("RESET TOURS", () => { F.planetTour.reset(); open(true); }));   // forget the progress of every planet
      stepEl.textContent = intro ? `${steps.length} short stops. You can leave the tour at any time.` : "";
      say(intro ? steps[0].text + " Want a quick tour of this world?" : `Welcome back to ${w.name}! ${n ? `${n} findings are here.` : "My NASA records are here."} Want the tour again?`);
      remember({ seen: true });
      actions.querySelector("button").focus({ preventScroll: true });
    }
    function go(j) {
      k = Math.max(0, Math.min(j, steps.length - 1));
      const s = steps[k];
      stepEl.textContent = `Stop ${k + 1} of ${steps.length}`;
      actions.replaceChildren(
        btn("◀ PREV", () => go(k - 1)), btn(k === steps.length - 1 ? "FINISH" : "NEXT ▶", () => (k === steps.length - 1 ? finish() : go(k + 1)), "px-btn"),
        btn("SKIP TOUR", close));
      actions.children[0].disabled = k === 0;
      mark(s.target);
      say(s.text);
      remember({ step: k });
      actions.children[1].focus({ preventScroll: true });
    }
    function finish() { remember({ done: true, step: 0 }); close(); }
    function close() {
      line++; if (text._finishTyping) text._finishTyping();
      unmark(); panel.hidden = true; k = -1;
      const replay = root.querySelector("#pg-replay"); if (replay && panel.contains(document.activeElement)) replay.focus({ preventScroll: true });
    }

    panel.querySelector(".pg-x").onclick = close;
    text.addEventListener("click", () => { if (text._finishTyping) text._finishTyping(); });   // show the full line now
    const replay = root.querySelector("#pg-replay");
    if (replay) replay.onclick = () => { open(false); go(0); };
    const onKey = (e) => {
      if (panel.hidden) return;
      const chat = document.getElementById("chat");
      if (e.key === "Escape" && (!chat || chat.hidden)) { e.preventDefault(); close(); }
      else if (k >= 0 && !/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) && (e.key === "ArrowRight" || e.key === "ArrowLeft") && panel.contains(document.activeElement)) {
        e.preventDefault(); go(k + (e.key === "ArrowRight" ? 1 : -1));
      }
    };
    document.addEventListener("keydown", onKey);
    // after the arrival and the RAG data (used only to mention crew notes), the owner greets you
    const greet = setTimeout(() => { if (alive && token === gen) open(!prog().seen); }, reduced() ? 0 : 900);
    return () => { alive = false; clearTimeout(greet); line++; unmark(); document.removeEventListener("keydown", onKey); if (text._finishTyping) text._finishTyping(); };
  }
})();
