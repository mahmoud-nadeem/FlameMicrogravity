/* Crew profile (the landing deck of each world), the mission-document viewport and the
   Crew panel's closing behaviour. Explore lives in orbital-explore.js; the record page in
   pages.js; the universe in space-engine.js. */
(function () {
  const F = window.FIF, P = F.pages, E = F.esc;
  const visits = new Set();

  // ---------------------------------------------------------------- crew profile
  P.profile = function (id) {
    const ch = F.characters.find((c) => c.id === id), t = ch && F.track(ch.track);
    if (!t) return { html: '<h1 class="page-title">PROFILE NOT FOUND</h1><a class="hud-btn" href="#/explore">&#9664; BACK TO EXPLORE</a>', mount() {} };
    const i = F.data.tracks.findIndex((x) => x.id === t.id), w = (F.worlds || [])[i] || { name: t.id, theme: "" };
    const recs = t.records.map((r) => F.data.records[r]).filter(Boolean);
    const n = F.data.findings.filter((f) => f.track === t.id).length;
    const labs = ["PSI-101", "PSI-102", "PSI-47"];
    return {
      html: `<div class="deck-nav"><a class="hud-btn" href="#/explore">&#9664; BACK TO EXPLORE</a><span class="telemetry">ORBIT LOCKED &middot; WORLD 0${i + 1} / 0${F.data.tracks.length} &middot; ${E(w.name)}</span></div>
      <section class="deck hud-panel" aria-labelledby="deck-name">
        <p class="eyebrow">${E(t.id)} &middot; CREW PROFILE &middot; ${E((w.theme || "").toUpperCase())}</p>
        <div class="deck-id">${F.spriteHTML(ch.id, "big", ch.name)}<div><h1 class="page-title" id="deck-name">${E(ch.name)}</h1><p class="lede">${E(ch.role)}</p>
          <p class="preview-status ${n ? "ready" : "wait"}">${n ? `&#9679; ${n} TRACEABLE FINDINGS` : "&#9675; FINDINGS PENDING"}</p></div></div>
        <p class="deck-reaction context-reaction" id="deck-reaction" role="status"></p>
        <p>${E(t.paragraph || ch.greeting)}</p>
        <div class="row"><button id="profile-ask" class="px-btn" type="button">ASK ${E(ch.name.split(" ")[0].toUpperCase())}</button><a class="hud-btn" href="#/research?q=${E(t.id)}">EVIDENCE TABLE</a></div>
        <h2 class="deck-h">EXPERIMENTS IN ORBIT</h2>
        <ol class="moon-list">${recs.map((r, k) => {
          const nf = F.data.findings.filter((f) => f.record === r.id).length;
          return `<li><a class="moon-link" href="#/record/${E(r.id)}" data-moon="m-${E(r.id)}" data-k="${k}"><span class="moon-no">MOON ${k + 1}</span><b>${E(r.acronym || r.id)}</b><span class="moon-title">${E(r.title)}</span><span class="moon-meta">${nf ? nf + " findings" : "record only"}${labs.includes(r.id) ? " &middot; simulation lab" : ""}</span></a></li>`;
        }).join("")}</ol>
        <details class="notes" id="profile-notes-${E(id)}"><summary>Research notes and limitations</summary><p>${E(t.limitations || "The full research package for this track has not been published yet.")}</p><a href="#/research">Open the evidence table</a></details>
      </section>`,
      mount(root) {
        const U = F.universe, sprite = root.querySelector(".deck-id canvas.sprite"), reaction = root.querySelector("#deck-reaction");
        root.querySelector("#profile-ask").onclick = () => F.openChat(ch.id);
        if (F.mapMemory) { F.mapMemory.lastProfile = ch.id; F.mapMemory.selected = Math.max(0, i); }
        const quiet = () => F.settings.reactions === false;
        reaction.textContent = quiet() ? "Explore the experiments below." :
          visits.has(id) ? `You're back on ${w.name}. Pick up wherever your curiosity left off.` :
          `You landed on ${w.name}. Each moon is one NASA experiment: start with one, then follow its evidence.`;
        visits.add(id);
        let highlight = null;
        // Hovering or focusing an experiment: the moon is marked in space and the scientist turns to it.
        root.querySelectorAll(".moon-link").forEach((a) => {
          const on = () => {
            highlight = a.dataset.moon; if (U) { U.state.highlight = highlight; U.requestFrame(); }
            const r = F.data.records[a.dataset.moon.slice(2)], nf = F.data.findings.filter((f) => f.record === r.id).length;
            if (!quiet()) reaction.textContent = `${r.acronym || r.id}: ${nf ? nf + " findings with sources are ready." : "the NASA record is here; findings are still being written."} It is marked in orbit.`;
            if (F.setSpriteState && sprite && !quiet()) F.setSpriteState(sprite, { look: 1, gesture: "point" }, 1800);
          };
          const offH = () => { if (highlight === a.dataset.moon) { highlight = null; if (U) { U.state.highlight = null; U.requestFrame(); } } };
          a.addEventListener("pointerenter", on); a.addEventListener("focus", on);
          a.addEventListener("pointerleave", offH); a.addEventListener("blur", offH);
        });
        let off = () => {};
        if (U && U.onFrame) off = U.onFrame((ctx, info) => {
          if (!ctx || !highlight) return;
          const p = U.projectBody(highlight); if (!p || !p.visible) return;
          const s = Math.max(10, p.r * 1.6) + 6, l = 6, g = s + (info.reduced ? 0 : Math.sin(info.now / 450) * 1.5);
          ctx.strokeStyle = "#f0b042"; ctx.lineWidth = 2; ctx.beginPath();
          [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(([sx, sy]) => { ctx.moveTo(p.x + sx * g, p.y + sy * (g - l)); ctx.lineTo(p.x + sx * g, p.y + sy * g); ctx.lineTo(p.x + sx * (g - l), p.y + sy * g); });
          ctx.stroke(); ctx.lineWidth = 1;
        });
        return () => { off(); if (U) U.state.highlight = null; };
      },
    };
  };

  // ---------------------------------------------------------------- mission documents (discovery viewport)
  // PDF.js is bundled in assets/vendor/pdfjs and loaded only here. Browsers block ES modules
  // and workers on file:// pages, so there the original PDF is embedded natively instead.
  // pdf-compat.mjs adds the few newer built-ins PDF.js needs (missing before Chrome/Edge 140), in this
  // page and, through pdf-worker-compat.mjs, in the worker; the vendored files stay unmodified.
  let pdfLibrary;
  function pdfjs() {
    const at = (p) => new URL(p, location.href).href;
    if (!pdfLibrary) pdfLibrary = import(at("assets/js/pdf-compat.mjs")).then(() => import(at("assets/vendor/pdfjs/pdf.min.mjs"))).then((lib) => {
      lib.GlobalWorkerOptions.workerSrc = at("assets/js/pdf-worker-compat.mjs"); return lib;
    });
    return pdfLibrary;
  }
  const viewerState = { index: 0, pages: {}, zoom: 1 };
  P.shorts = function () {
    return {
      html: `<div class="deck-nav"><a class="hud-btn" href="#/explore">&#9664; BACK TO EXPLORE</a><span class="telemetry">ORBITAL ARCHIVE &middot; DISCOVERY VIEWPORT</span></div>
      <section class="viewport-frame" id="viewport" tabindex="0" aria-label="Spacecraft document viewport">
        <div class="viewport-head">
          <p class="eyebrow">MISSION DOCUMENTS &middot; <span id="short-kind"></span></p>
          <h1 class="page-title" id="short-title"></h1>
          <div class="exp-toolbar"><button class="hud-btn" id="short-prev" type="button">&#9664; PREVIOUS</button><span class="exp-status" id="short-counter" aria-live="polite"></span><button class="hud-btn" id="short-next" type="button">NEXT &#9654;</button></div>
          <p class="small muted">These are original documents (NASA reports and a project figure), not a video collection. Left/right arrows or a sideways swipe on the frame change documents; scrolling inside a document only scrolls the document.</p>
        </div>
        <div id="pdf-controls" class="exp-toolbar" hidden><button class="hud-btn" id="pdf-prev" type="button">PAGE &minus;</button><span id="pdf-counter" class="telemetry"></span><button class="hud-btn" id="pdf-next" type="button">PAGE +</button><button class="hud-btn" id="pdf-minus" aria-label="Zoom out" type="button">&minus;</button><span id="pdf-zoom" class="telemetry"></span><button class="hud-btn" id="pdf-plus" aria-label="Zoom in" type="button">+</button><button class="hud-btn" id="pdf-fit" type="button">FIT WIDTH</button></div>
        <p id="pdf-status" class="pdf-status" role="status"></p>
        <div class="viewport-glass"><div class="pdf-stage" id="pdf-stage"></div></div>
        <details id="pdf-accessible" hidden><summary>Accessible page text</summary><div class="pdf-text" id="pdf-text"></div></details>
        <p class="small muted" id="short-source"></p><a id="pdf-download" class="hud-btn" download>DOWNLOAD ORIGINAL PDF</a>
      </section>`,
      mount(root) {
        const $ = (s) => root.querySelector(s), list = window.FIF_SHORTS || [], box = $("#viewport"), stage = $("#pdf-stage");
        let doc = null, task = null, loadTask = null, version = 0, dead = false, touch = null, page = 1;
        function release() { task?.cancel(); task = null; loadTask?.destroy(); loadTask = null; doc = null; }
        const status = (text, kind = "") => { $("#pdf-status").textContent = text; $("#pdf-status").dataset.kind = kind; };
        async function render() {
          if (!doc || dead) return; const token = ++version; task?.cancel(); task = null;
          try {
            const pdfPage = await doc.getPage(page); if (dead || token !== version) return;
            const base = pdfPage.getViewport({ scale: 1 }), scale = Math.max(0.2, (stage.clientWidth - 24) / base.width) * viewerState.zoom;
            const view = pdfPage.getViewport({ scale }), dpr = Math.min(devicePixelRatio || 1, 2);
            const cv = document.createElement("canvas"); cv.width = Math.ceil(view.width * dpr); cv.height = Math.ceil(view.height * dpr);
            cv.style.width = view.width + "px"; cv.style.height = view.height + "px"; cv.setAttribute("role", "img"); cv.setAttribute("aria-label", list[viewerState.index].title + ", page " + page);
            task = pdfPage.render({ canvas: cv, viewport: view, transform: [dpr, 0, 0, dpr, 0, 0] }); await task.promise;
            if (dead || token !== version) return; stage.replaceChildren(cv); stage.scrollTop = 0;
            $("#pdf-counter").textContent = `PAGE ${page} / ${doc.numPages}`; $("#pdf-zoom").textContent = Math.round(viewerState.zoom * 100) + "%";
            $("#pdf-prev").disabled = page <= 1; $("#pdf-next").disabled = page >= doc.numPages; $("#pdf-minus").disabled = viewerState.zoom <= 0.5; $("#pdf-plus").disabled = viewerState.zoom >= 3;
            status("High-resolution rendering of the original document.", "ok");
            const text = await pdfPage.getTextContent(); if (dead || token !== version) return;
            $("#pdf-text").textContent = text.items.map((i) => i.str + (i.hasEOL ? "\n" : " ")).join("");
          } catch (e) { if (e && e.name !== "RenderingCancelledException" && !dead) { status("This page could not be rendered here, so the original PDF is embedded instead.", "error"); native(); } }
        }
        function native() {
          if (dead) return; $("#pdf-controls").hidden = true; $("#pdf-accessible").hidden = true;
          const iframe = document.createElement("iframe"); iframe.title = list[viewerState.index].title; iframe.src = list[viewerState.index].url + "#toolbar=1&view=FitH";
          stage.replaceChildren(iframe);
          if (location.protocol === "file:") status("Opened from disk: showing the original PDF with your browser's own viewer. Serve the folder (see README) for page and zoom controls here. If nothing appears, use DOWNLOAD ORIGINAL PDF.", "info");
        }
        async function show() {
          release(); const token = ++version; const item = list[viewerState.index];
          if (!item) { status("No documents available.", "error"); return; }
          page = viewerState.pages[item.id] || 1;
          $("#short-title").textContent = item.title; $("#short-kind").textContent = item.kind || "DOCUMENT";
          $("#short-counter").textContent = `DISCOVERY ${viewerState.index + 1} / ${list.length}`; $("#short-source").textContent = "Source: " + item.source;
          $("#short-prev").disabled = viewerState.index === 0; $("#short-next").disabled = viewerState.index === list.length - 1; $("#pdf-download").href = item.url;
          stage.replaceChildren();
          if (location.protocol === "file:") { native(); return; }
          status("Loading document…", "loading");
          try {
            const lib = await pdfjs(); if (dead || token !== version) return;
            loadTask = lib.getDocument({ url: item.url, isEvalSupported: false, verbosity: 0 });
            loadTask.onProgress = (p) => { if (p.total && token === version) status(`Loading document… ${Math.round((p.loaded / p.total) * 100)}%`, "loading"); };
            const loaded = await loadTask.promise; if (dead || token !== version) { loaded.destroy(); return; }
            doc = loaded; $("#pdf-controls").hidden = false; $("#pdf-accessible").hidden = false;
            await render();
          } catch (e) { if (!dead && token === version) { status("The document viewer could not start, so the original PDF is embedded instead.", "error"); native(); } }
        }
        function move(d) { const next = Math.max(0, Math.min(list.length - 1, viewerState.index + d)); if (next === viewerState.index) return; viewerState.index = next; show(); }
        $("#short-prev").onclick = () => move(-1); $("#short-next").onclick = () => move(1);
        $("#pdf-prev").onclick = () => { if (doc && page > 1) { viewerState.pages[list[viewerState.index].id] = --page; render(); } };
        $("#pdf-next").onclick = () => { if (doc && page < doc.numPages) { viewerState.pages[list[viewerState.index].id] = ++page; render(); } };
        $("#pdf-minus").onclick = () => { viewerState.zoom = Math.max(0.5, viewerState.zoom - 0.25); render(); };
        $("#pdf-plus").onclick = () => { viewerState.zoom = Math.min(3, viewerState.zoom + 0.25); render(); };
        $("#pdf-fit").onclick = () => { viewerState.zoom = 1; render(); };
        box.onkeydown = (e) => {
          if (/INPUT|TEXTAREA|SELECT/.test(e.target.tagName) || e.ctrlKey || e.metaKey || e.altKey) return;
          if (e.key === "ArrowRight" || e.key === "ArrowLeft") { e.preventDefault(); move(e.key === "ArrowRight" ? 1 : -1); }
          else if (e.key === "PageDown" && doc) { e.preventDefault(); $("#pdf-next").click(); }
          else if (e.key === "PageUp" && doc) { e.preventDefault(); $("#pdf-prev").click(); }
          else if ((e.key === "+" || e.key === "=") && doc) { e.preventDefault(); $("#pdf-plus").click(); }
          else if (e.key === "-" && doc) { e.preventDefault(); $("#pdf-minus").click(); }
        };
        // Swipes on the frame (not inside the document) change discoveries; document scrolling stays normal.
        box.addEventListener("touchstart", (e) => { touch = !e.target.closest(".pdf-stage") && e.touches.length === 1 ? [e.touches[0].clientX, e.touches[0].clientY] : null; }, { passive: true });
        box.addEventListener("touchend", (e) => { if (!touch) return; const dx = e.changedTouches[0].clientX - touch[0], dy = e.changedTouches[0].clientY - touch[1]; if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) move(dx < 0 ? 1 : -1); touch = null; }, { passive: true });
        let resizeTimer; const ro = new ResizeObserver(() => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { if (doc) render(); }, 200); }); ro.observe(stage);
        show(); box.focus({ preventScroll: true });
        return () => { dead = true; ++version; clearTimeout(resizeTimer); ro.disconnect(); release(); };
      },
    };
  };

  // ---------------------------------------------------------------- Crew panel closing
  document.addEventListener("DOMContentLoaded", () => {
    // Non-modal panel: X, Escape and a pointer outside close it; actions inside never do.
    const panel = document.querySelector("#chat"), launch = document.querySelector("#chat-launch");
    let closeTimer, returnFocus = launch;
    const original = F.openChat;
    F.openChat = function (id) {
      document.querySelectorAll(".dialog .txt").forEach((el) => el._finishTyping?.());
      clearTimeout(closeTimer); panel.classList.remove("closing");
      if (panel.hidden) returnFocus = document.activeElement;
      original(id);
    };
    F.closeChat = function (restore = false) {
      if (panel.hidden || panel.classList.contains("closing")) return;
      panel.classList.add("closing"); launch.setAttribute("aria-expanded", "false");
      closeTimer = setTimeout(() => { panel.hidden = true; panel.classList.remove("closing"); launch.hidden = false; if (restore) (returnFocus?.isConnected ? returnFocus : launch).focus(); }, F.settings.reduceMotion ? 0 : 200);
    };
    document.addEventListener("pointerdown", (e) => { if (!panel.hidden && !panel.contains(e.target) && !launch.contains(e.target)) F.closeChat(false); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) { e.preventDefault(); F.closeChat(true); } });
  });
})();
