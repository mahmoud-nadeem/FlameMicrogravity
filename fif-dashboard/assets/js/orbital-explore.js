/* Explore = the mission map. Six research worlds orbit the mission star; you pick a
   destination like in a game's world-select screen and the camera travels there.
   The universe (space-engine.js) draws the worlds. This file draws the interface:
   accessible world buttons that follow the planets, the network lines between them,
   reticles, the preview card, the guide's reactions and the approach. */
(function () {
  const F = window.FIF, E = F.esc;
  // Survives route changes, so returning to the map restores where you were.
  const memory = { selected: 0, yaw: null, pitch: null, dist: null, paused: false, visited: [], lastProfile: null };
  F.mapMemory = memory;
  const TAU = Math.PI * 2;

  F.pages.explore = function () {
    const tracks = F.data.tracks, directory = F.pages.crewDirectory();
    const items = tracks.map((t, i) => {
      const ch = F.characterForTrack(t.id) || {}, w = (F.worlds || [])[i] || { name: t.id, theme: "" };
      const recs = t.records.map((id) => F.data.records[id]).filter(Boolean);
      return { t, i, ch, w, recs, n: F.data.findings.filter((f) => f.track === t.id).length, id: "w-" + t.id };
    });
    const label = (x) => `World 0${x.i + 1}, ${x.w.name}, ${x.w.theme}: ${x.ch.name}, ${x.ch.role}. ${x.n ? x.n + " findings published" : "Findings pending"}. Press Enter to approach.`;
    return {
      html: `<section class="map-stage" id="map-stage" aria-label="Mission map: six research worlds around the mission star">
        <header class="map-head">
          <p class="eyebrow">LEVEL 02 &middot; MISSION MAP</p>
          <h1 class="map-title">CHOOSE A WORLD</h1>
          <p class="map-hint">Hover or focus a world to preview it. Click to approach. Drag empty space to orbit the system. Arrow keys move between worlds.</p>
        </header>
        <div class="map-nodes" id="map-nodes">
          <button class="map-hub" id="map-hub" type="button" aria-label="Mission star: ask the guide a question"><span class="node-label"><b>MISSION STAR</b><small>ASK THE GUIDE</small></span></button>
          ${items.map((x) => `<button class="map-node" type="button" data-index="${x.i}" data-id="${x.id}" aria-label="${E(label(x))}"><span class="node-hit" aria-hidden="true"></span><span class="node-label" aria-hidden="true"><b>0${x.i + 1} ${E(x.w.name)}</b><small>${E(x.ch.name)}</small></span></button>`).join("")}
        </div>
        <aside class="map-preview hud-panel" id="map-preview" aria-live="polite"></aside>
        <div class="map-dock hud-panel">
          <button class="hud-btn" id="map-prev" aria-label="Previous world">&#9664; PREV</button>
          <span class="telemetry" id="map-count"></span>
          <button class="hud-btn" id="map-next" aria-label="Next world">NEXT &#9654;</button>
          <button class="hud-btn" id="map-orbits" aria-pressed="false">PAUSE ORBITS</button>
          <button class="hud-btn" id="map-reset">RESET VIEW</button>
          <a class="hud-btn" href="#/explore" id="map-dir-link">CREW DIRECTORY &#8595;</a>
        </div>
        <div class="map-transmission hud-panel">${F.spriteHTML("guide", "mid", "Mission guide")}<div><span class="who">GUIDE</span><p id="map-comment" role="status"></p><button class="chip" id="map-continue" type="button" hidden>CONTINUE</button></div></div>
      </section>
      <section class="block directory-sec" id="map-directory" aria-labelledby="dir-title">
        <p class="eyebrow">NO ANIMATION NEEDED</p>
        <h2 id="dir-title">CREW DIRECTORY</h2>
        <p class="lede">The same six worlds as a list: every crew member and every NASA experiment.</p>
        <div class="exp-console discovery-link"><p class="eyebrow">ORBITAL ARCHIVE</p><h3>MISSION DOCUMENTS</h3><p>Read original NASA documents one at a time in the spacecraft viewport.</p><a class="px-btn" href="#/shorts">OPEN THE VIEWPORT &#9654;</a></div>
        <div id="map-directory-list">${directory.html}</div>
      </section>`,

      mount(root) {
        const $ = (s) => root.querySelector(s), U = F.universe;
        const stage = $("#map-stage"), nodes = [...root.querySelectorAll(".map-node")], hub = $("#map-hub"), preview = $("#map-preview");
        const n = items.length;
        directory.mount($("#map-directory-list"));
        const reduced = () => (U && U.reduceMotion ? U.reduceMotion() : !!F.settings.reduceMotion);
        const mobile = window.matchMedia ? window.matchMedia("(max-width: 720px)") : { matches: false, addEventListener() {}, removeEventListener() {} };
        let dead = false, hovered = null, lastPointer = "mouse", approaching = false, drag = null, touch = null;
        const guideSprite = root.querySelector(".map-transmission canvas.sprite");

        if (U && U.mapView) {
          if (memory.yaw != null) { U.mapView.yaw = memory.yaw; U.mapView.pitch = memory.pitch; U.mapView.dist = memory.dist; }
          U.state.orbitsPaused = memory.paused;
        }

        const comment = (text) => { $("#map-comment").textContent = text; };
        const react = (text, neutral) => comment(F.settings.reactions === false ? neutral : text);

        function previewHTML(x) {
          return `<p class="eyebrow">WORLD 0${x.i + 1} / 0${n} &middot; ${E(x.w.theme.toUpperCase())}</p>
            <h2 class="preview-name">${E(x.w.name)}</h2>
            <p class="preview-member"><b>${E(x.ch.name)}</b><br><span>${E(x.t.id)} &middot; ${E(x.ch.role)}</span></p>
            <p class="preview-status ${x.n ? "ready" : "wait"}">${x.n ? `&#9679; ${x.n} TRACEABLE FINDINGS` : "&#9675; FINDINGS PENDING"}</p>
            <p class="small">Experiments in orbit: ${x.recs.map((r) => `<span class="tag">${E(r.acronym || r.id)}</span>`).join(" ")}</p>
            <p class="small muted">${x.n ? "Land to read the evidence, open the experiment records and ask the scientist." : "Land to browse the NASA experiment records while the research package is written."}</p>
            <div class="row"><a class="px-btn" href="#/profile/${E(x.ch.id)}" data-approach="${x.i}">APPROACH &#9654;</a><button class="hud-btn" type="button" data-ask="${E(x.ch.id)}">ASK ${E((x.ch.name || "").split(" ")[0].toUpperCase())}</button></div>`;
        }
        let previewShown = -1;
        function showPreview(i) {
          if (i === previewShown) return;
          previewShown = i;
          preview.innerHTML = previewHTML(items[i]);
          preview.querySelector("[data-approach]").addEventListener("click", (e) => { if (e.button || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return; e.preventDefault(); approach(i); });
          preview.querySelector("[data-ask]").onclick = () => F.openChat(items[i].ch.id);
        }

        function select(i, { focus = false, notify = true } = {}) {
          memory.selected = ((i % n) + n) % n;
          const x = items[memory.selected];
          nodes.forEach((b, j) => { b.classList.toggle("is-selected", j === memory.selected); b.setAttribute("aria-current", j === memory.selected ? "true" : "false"); });
          $("#map-count").textContent = `WORLD ${memory.selected + 1} / ${n}`;
          showPreview(memory.selected);
          if (U) { U.state.mobileFocus = mobile.matches ? U.body(x.id) : null; U.requestFrame(); }
          if (focus) nodes[memory.selected].focus({ preventScroll: true });
          if (notify) react(`${x.w.name} is ${x.ch.name}'s world: ${x.ch.role.toLowerCase()}. ${x.n ? "Their evidence is published and ready to read." : "Their NASA records are ready; the findings are still being written."}`,
            `${x.w.name}: ${x.ch.name}.`);
          lookAt(nodes[memory.selected]);
        }
        // The guide turns toward the world you are looking at (only when reactions are on).
        function lookAt(el) {
          if (!guideSprite || F.settings.reactions === false || !el) return;
          const a = guideSprite.getBoundingClientRect(), b = el.getBoundingClientRect();
          F.setSpriteState && F.setSpriteState(guideSprite, { look: b.left + b.width / 2 > a.left + a.width / 2 ? 1 : -1, gesture: "point" }, 1600);
        }

        function setHover(i) {
          hovered = i;
          if (U) { U.state.hover = i == null ? null : items[i].id; U.requestFrame(); }
          showPreview(i == null ? memory.selected : i);
        }

        function approach(i) {
          if (approaching) return;
          const x = items[i];
          approaching = true; memory.lastProfile = x.ch.id; memory.selected = i;
          if (!memory.visited.includes(x.ch.id)) memory.visited.push(x.ch.id);
          stage.classList.add("approaching");
          react(`Approaching ${x.w.name}. Hold on.`, `Opening ${x.ch.name}'s world.`);
          const go = () => { if (!dead) location.hash = "#/profile/" + x.ch.id; };
          if (!U || reduced() || U.mode === "off") { go(); return; }
          U.state.dimOthers = x.id;
          U.approach(x.id).then(go);
        }

        nodes.forEach((b, i) => {
          b.addEventListener("pointerdown", (e) => { lastPointer = e.pointerType || "mouse"; });
          b.addEventListener("pointerenter", (e) => { if (e.pointerType !== "touch") setHover(i); });
          b.addEventListener("pointerleave", () => { if (hovered === i) setHover(null); });
          b.addEventListener("focus", () => { select(i, { notify: false }); setHover(i); });
          b.addEventListener("blur", () => { if (hovered === i) setHover(null); });
          b.addEventListener("click", () => {
            // Touch has no hover: the first tap selects and previews, the second approaches.
            if (lastPointer === "touch" && memory.selected !== i) { select(i); lastPointer = "mouse"; return; }
            approach(i);
          });
          b.addEventListener("keydown", (e) => {
            const k = e.key;
            if (k === "ArrowRight" || k === "ArrowDown") { e.preventDefault(); select(i + 1, { focus: true }); }
            else if (k === "ArrowLeft" || k === "ArrowUp") { e.preventDefault(); select(i - 1, { focus: true }); }
            else if (k === "Home") { e.preventDefault(); select(0, { focus: true }); }
            else if (k === "End") { e.preventDefault(); select(n - 1, { focus: true }); }
          });
        });
        hub.onclick = () => F.openChat("guide");
        $("#map-prev").onclick = () => select(memory.selected - 1);
        $("#map-next").onclick = () => select(memory.selected + 1);
        const paintOrbits = () => {
          const b = $("#map-orbits");
          b.textContent = memory.paused ? "RESUME ORBITS" : "PAUSE ORBITS"; b.setAttribute("aria-pressed", String(memory.paused));
          b.disabled = reduced(); if (reduced()) b.textContent = "ORBITS STILL";
        };
        $("#map-orbits").onclick = () => { memory.paused = !memory.paused; if (U) U.state.orbitsPaused = memory.paused; paintOrbits(); };
        $("#map-reset").onclick = () => { if (!U) return; Object.assign(U.mapView, { yaw: 0.55, pitch: 0.46, dist: 58 }); U.setScene("map"); };
        $("#map-dir-link").onclick = (e) => { e.preventDefault(); $("#map-directory").scrollIntoView({ behavior: reduced() ? "auto" : "smooth" }); };
        $("#map-continue").onclick = () => { const i = (memory.selected + 1) % n; select(i, { focus: true }); $("#map-continue").hidden = true; };

        // Drag empty space to orbit the system (mouse/pen). Touch swipes change worlds.
        const onDown = (e) => {
          if (e.target.closest("button, a, .map-preview, .map-dock, .map-transmission")) return;
          if (e.pointerType === "touch") { touch = [e.clientX, e.clientY]; return; }
          if (!U) return;
          drag = { x: e.clientX, y: e.clientY, yaw: U.mapView.yaw, pitch: U.mapView.pitch };
          stage.setPointerCapture && stage.setPointerCapture(e.pointerId);
          stage.classList.add("dragging");
        };
        const onMove = (e) => {
          if (!drag) return;
          U.mapView.yaw = drag.yaw - (e.clientX - drag.x) * 0.005;
          U.mapView.pitch = Math.max(0.1, Math.min(1.15, drag.pitch + (e.clientY - drag.y) * 0.004));
          U.requestFrame();
        };
        const onUp = (e) => {
          if (touch && e.pointerType === "touch") {
            const dx = e.clientX - touch[0], dy = e.clientY - touch[1];
            if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) select(memory.selected + (dx < 0 ? 1 : -1));
            touch = null;
          }
          drag = null; stage.classList.remove("dragging");
        };
        stage.addEventListener("pointerdown", onDown);
        stage.addEventListener("pointermove", onMove);
        stage.addEventListener("pointerup", onUp);
        stage.addEventListener("pointercancel", onUp);

        const applyMobile = () => { stage.classList.toggle("is-mobile", mobile.matches); select(memory.selected, { notify: false }); };
        mobile.addEventListener && mobile.addEventListener("change", applyMobile);
        const settingsChanged = () => { paintOrbits(); if (U) U.requestFrame(); };
        document.addEventListener("fif:settings", settingsChanged);

        // ---- per-frame interface: buttons follow the worlds; lines, orbits and reticles on the overlay
        const hubBody = U && U.body("sun");
        let off = () => {};
        if (U && U.onFrame) off = U.onFrame((ctx, info) => {
          if (dead) return;
          const t = info.now / 1000;
          // Buttons live inside the stage (they scroll with it); the planets are in the fixed universe.
          const rect = stage.getBoundingClientRect();
          if (rect.bottom < 0 || rect.top > info.H) return;
          const hp = U.projectBody("sun");
          if (hp) placeHub(hp, rect);
          const sel = items[memory.selected].id, hov = hovered == null ? null : items[hovered].id;
          const proj = items.map((x) => U.projectBody(x.id));
          proj.forEach((p, i) => placeNode(nodes[i], p, rect));
          placePreview(proj[hovered == null ? memory.selected : hovered], rect);
          if (!ctx) return;
          ctx.save(); ctx.beginPath(); ctx.rect(rect.left, rect.top, rect.width, rect.height); ctx.clip();
          // orbits
          ctx.lineWidth = 1;
          items.forEach((x, i) => {
            const b = U.body(x.id), o = b.orbit, focus = x.id === sel || x.id === hov;
            ctx.strokeStyle = focus ? "rgba(240,176,66,.38)" : "rgba(150,180,230,.12)";
            ctx.beginPath();
            for (let k = 0; k <= 120; k++) {
              const th = (k / 120) * TAU, pt = U.project([o.a * Math.cos(th), o.a * Math.sin(th) * Math.sin(o.inc), o.a * Math.sin(th) * Math.cos(o.inc)]);
              if (pt.depth < 0.3) { ctx.moveTo(pt.x, pt.y); continue; }
              k ? ctx.lineTo(pt.x, pt.y) : ctx.moveTo(pt.x, pt.y);
            }
            ctx.stroke();
          });
          // network lines from the star to every world; travelling pulses on the focused one
          if (hp && hp.depth > 0) items.forEach((x, i) => {
            const p = proj[i]; if (!p || p.depth < 0.3) return;
            const focus = x.id === sel || x.id === hov;
            ctx.strokeStyle = focus ? "rgba(240,176,66,.55)" : "rgba(190,210,255,.14)";
            ctx.setLineDash(focus ? [] : [2, 6]);
            ctx.beginPath(); ctx.moveTo(hp.x, hp.y); ctx.lineTo(p.x, p.y); ctx.stroke(); ctx.setLineDash([]);
            if (focus && !info.reduced) for (let k = 0; k < 3; k++) {
              const f = (t * 0.45 + k / 3) % 1, px = hp.x + (p.x - hp.x) * f, py = hp.y + (p.y - hp.y) * f;
              ctx.fillStyle = "rgba(255,206,120," + (0.9 - f * 0.6) + ")"; ctx.fillRect(Math.round(px) - 2, Math.round(py) - 2, 4, 4);
            }
          });
          // experiment moons of the focused world: thin tethers
          const fw = U.body(hov || sel);
          if (fw) fw.moons.forEach((m) => {
            if (m.alpha < 0.1) return;
            const a = U.project(fw.pos), b = U.project(m.pos);
            if (a.depth < 0.3 || b.depth < 0.3) return;
            ctx.strokeStyle = "rgba(160,200,255," + 0.35 * m.alpha + ")"; ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
          });
          // reticles: game-style brackets around the selected and hovered worlds
          items.forEach((x, i) => {
            if (x.id !== sel && x.id !== hov) return;
            const p = proj[i]; if (!p || p.depth < 0.3) return;
            bracket(ctx, p.x, p.y, Math.max(16, p.r * 1.35) + 6, x.id === hov ? "#ffffff" : "#f0b042", info.reduced ? 0 : t);
          });
          ctx.restore();
        });
        function bracket(ctx, x, y, s, color, t) {
          const l = Math.max(6, s * 0.35), g = s + Math.sin(t * 2.2) * 1.5;
          ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath();
          [[-1, -1], [1, -1], [1, 1], [-1, 1]].forEach(([sx, sy]) => {
            ctx.moveTo(x + sx * g, y + sy * (g - l)); ctx.lineTo(x + sx * g, y + sy * g); ctx.lineTo(x + sx * (g - l), y + sy * g);
          });
          ctx.stroke(); ctx.lineWidth = 1;
        }
        function placeNode(el, p, rect = { left: 0, top: 0 }) {
          if (!p || !p.visible) { el.style.visibility = "hidden"; return; }
          el.style.visibility = "";
          const size = Math.max(44, Math.min(220, p.r * 2.3 + 10));
          el.style.transform = `translate3d(${p.x - rect.left - size / 2}px, ${p.y - rect.top - size / 2}px, 0)`;
          el.style.setProperty("--size", size + "px");
          el.style.setProperty("--depth", Math.max(0.45, Math.min(1, 40 / p.depth)).toFixed(2));
        }
        // On wide screens the compact preview floats beside the world it describes.
        function placePreview(p, rect) {
          const floating = !mobile.matches;
          preview.classList.toggle("floating", floating);
          if (!floating) { preview.style.transform = ""; preview.style.visibility = ""; return; }
          if (!p || !p.visible) { preview.style.visibility = "hidden"; return; }
          preview.style.visibility = "";
          // Put the card on the side of the world that faces away from the star, so the star,
          // its label and the world itself stay visible. Fall back to whichever side fits.
          const w = preview.offsetWidth, h = preview.offsetHeight, r = Math.max(18, p.r * 1.35);
          const hp = U.projectBody("sun"), px = p.x - rect.left, py = p.y - rect.top;
          const sx = hp ? hp.x - rect.left : rect.width / 2, sy = hp ? hp.y - rect.top : rect.height / 2;
          const top = 96, bottom = rect.height - 96;
          const fitsX = (x) => x >= 16 && x + w <= rect.width - 16;
          const right = px + r + 170, left = px - r - 28 - w;
          let x, y = Math.max(top, Math.min(bottom - h, py - h / 2));
          if (px < sx && fitsX(left)) x = left;
          else if (px >= sx && fitsX(right)) x = right;
          else if (fitsX(right) && px < sx - w) x = right;
          else {
            x = Math.max(16, Math.min(rect.width - w - 16, px - w / 2));
            y = py < sy ? py - r - 30 - h : py + r + 44;
            if (y < top || y + h > bottom) y = py < sy ? py + r + 44 : py - r - 30 - h;
            y = Math.max(top, Math.min(bottom - h, y));
          }
          preview.style.transform = `translate3d(${Math.round(x)}px, ${Math.round(y)}px, 0)`;
        }
        function placeHub(p, rect) {
          if (!p.visible) { hub.style.visibility = "hidden"; return; }
          hub.style.visibility = "";
          const size = Math.max(56, Math.min(200, p.r * 2.4));
          hub.style.transform = `translate3d(${p.x - rect.left - size / 2}px, ${p.y - rect.top - size / 2}px, 0)`;
          hub.style.setProperty("--size", size + "px");
        }
        // Without the universe (no WebGL and no 2D canvas), lay the buttons out on a ring.
        if (!U) nodes.forEach((el, i) => { const a = (i / n) * TAU; placeNode(el, { visible: true, x: stage.clientWidth / 2 + Math.cos(a) * 260, y: stage.clientHeight / 2 + Math.sin(a) * 160, r: 30, depth: 40 }); });

        // first visit vs return: a real event, not a random line
        const last = memory.lastProfile && items.find((x) => x.ch.id === memory.lastProfile);
        memory.lastProfile = null; // the welcome-back line is said once per return
        if (last) {
          const next = items[(last.i + 1) % n];
          react(`Welcome back from ${last.w.name}. ${next.w.name} is next on the route: ${next.ch.name}. Continue?`, "Choose a destination.");
          if (F.settings.reactions !== false) { $("#map-continue").hidden = false; $("#map-continue").textContent = `CONTINUE TO ${next.w.name}`; }
          memory.selected = last.i;
        } else {
          react("Six worlds orbit the mission star. Hover one to see who lives there, then approach it.", "Choose a destination.");
        }
        applyMobile(); paintOrbits();
        select(memory.selected, { notify: false });

        return () => {
          dead = true; off();
          if (U) { memory.yaw = U.mapView.yaw; memory.pitch = U.mapView.pitch; memory.dist = U.mapView.dist;
            Object.assign(U.state, { hover: null, mobileFocus: null, dimOthers: null }); }
          mobile.removeEventListener && mobile.removeEventListener("change", applyMobile);
          document.removeEventListener("fif:settings", settingsChanged);
        };
      },
    };
  };
})();
