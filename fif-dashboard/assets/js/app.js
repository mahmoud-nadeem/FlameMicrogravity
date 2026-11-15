/* Hash router, scene travel, console chrome (edge navigation, telemetry).
   URLs stay ordinary hashes so history, bookmarks and new tabs work; the universe travels
   to the matching scene while the page content changes. */
(function () {
  const FIF = window.FIF, D = FIF.data;
  let cleanup = null, currentRoute = null;
  const positions = new Map(), openDetails = new Map();
  if ("scrollRestoration" in history) history.scrollRestoration = "manual";
  const journey = () => (D.project && D.project.journey) || [];

  function nav(active) {
    const steps = journey();
    FIF.$("#journey").innerHTML = steps.map((s, i) =>
      `<a href="${s.route}" ${s.id === active ? 'aria-current="page"' : ""}><span class="lvl">${String(i + 1).padStart(2, "0")}</span>${FIF.esc(s.label.toUpperCase())}</a>`).join("");
    // Edge cues: the previous and next stop of the journey, like a console's side rails.
    const i = steps.findIndex((s) => s.id === active), prev = steps[i - 1], next = steps[i + 1];
    const label = (s, k) => `${String(k + 1).padStart(2, "0")} ${FIF.esc(s.label.toUpperCase())}`;
    FIF.$("#edge-nav").innerHTML =
      (prev ? `<a class="edge prev" href="${prev.route}"><span aria-hidden="true">‹</span> ${label(prev, i - 1)}</a>` : "") +
      (next ? `<a class="edge next" href="${next.route}">${label(next, i + 1)} <span aria-hidden="true">›</span></a>` : "");
  }

  // Which part of the universe each route looks at.
  function sceneFor(parts) {
    const worldOfMember = (id) => { const c = FIF.characters.find((x) => x.id === id); return c && c.track ? "w-" + c.track : null; };
    const worldOfRecord = (id) => { const r = D.records[id]; return r ? "w-" + r.track : null; };
    switch (parts[0]) {
      case undefined: return ["home", {}];
      case "explore": return ["map", {}];
      case "profile": { const w = worldOfMember(parts[1]); return w ? ["world", { id: w, side: 1, dist: 6.2 }] : ["deep", {}]; }
      case "record": { const w = worldOfRecord(decodeURIComponent(parts[1] || "")); return w ? ["world", { id: w, side: 1, dist: 15, drop: 1.6 }] : ["deep", {}]; }
      case "lab": { const w = worldOfRecord(parts[1]); return w ? ["world", { id: w, side: 1, dist: 22, drop: 2.4 }] : ["deep", {}]; }
      default: return ["deep", {}];
    }
  }

  function route() {
    const target = location.hash.replace(/^#/, "") || "/";
    if (target === currentRoute) return; // rapid back/forward can deliver the same hash twice
    if (currentRoute) {
      positions.set(currentRoute, window.scrollY);
      openDetails.set(currentRoute, FIF.$$("details[id]", FIF.$("#app")).map((d) => [d.id, d.open]));
    }
    const raw = location.hash.replace(/^#/, "") || "/";
    const [path, query] = raw.split("?");
    const params = new URLSearchParams(query || "");
    const parts = path.split("/").filter(Boolean);
    let page, active;
    if (!parts.length) { page = FIF.pages.home(); active = "home"; }
    else if (parts[0] === "profile") { page = FIF.pages.profile(parts[1]); active = "explore"; }
    else if (parts[0] === "shorts") { page = FIF.pages.shorts(); active = "explore"; }
    else if (parts[0] === "lab") { page = FIF.pages.lab(parts[1]); active = "explore"; }
    else if (parts[0] === "explore") { page = FIF.pages.explore(); active = "explore"; }
    else if (parts[0] === "record") { page = FIF.pages.record(decodeURIComponent(parts[1] || "")); active = "explore"; }
    else if (parts[0] === "results") { page = FIF.pages.results(); active = "results"; }
    else if (parts[0] === "research") { page = FIF.pages.research(params); active = "research"; }
    else if (parts[0] === "sources") { page = FIF.pages.sources(); active = "sources"; }
    else { page = FIF.pages.home(); active = "home"; }
    // Each view cleans up what it owns (charts, listeners, timers) in its own cleanup.
    if (typeof cleanup === "function") { try { cleanup(); } catch (e) { console.warn("cleanup failed", e); } }
    const app = FIF.$("#app");
    app.innerHTML = page.html;
    app.dataset.route = parts[0] || "home";
    document.body.dataset.route = parts[0] || "home";

    const [scene, opts] = sceneFor(parts);
    if (FIF.universe && FIF.universe.setScene) FIF.universe.setScene(scene, opts);
    (openDetails.get(raw) || []).forEach(([id, open]) => { const d = app.querySelector("#" + CSS.escape(id)); if (d) d.open = open; });

    cleanup = page.mount(app) || null;
    nav(active);
    currentRoute = raw;
    FIF.paintSprites(app);
    window.scrollTo({ top: positions.get(raw) || 0, behavior: "instant" });
    telemetry(scene, parts);
    if (!FIF.settings.reduceMotion) {
      app.classList.remove("route-enter"); void app.offsetWidth; app.classList.add("route-enter");
    }
    app.focus({ preventScroll: true });
  }

  function telemetry(scene, parts) {
    const el = FIF.$("#hud-telemetry"); if (!el) return;
    const names = { home: "APPROACH VECTOR", map: "MISSION MAP", world: "ORBIT LOCK", deep: "DEEP SPACE" };
    const where = parts.length ? parts.map((p) => decodeURIComponent(p).toUpperCase()).join(" / ") : "BRIEFING";
    el.textContent = `FIF-26 · ${names[scene] || "DEEP SPACE"} · ${where}`;
  }

  document.addEventListener("DOMContentLoaded", () => {
    FIF.$("#footer").innerHTML = `${FIF.esc((D.project && D.project.team) || "")}<br>${FIF.esc((D.project && D.project.disclosure) || "")}`;
    FIF.initControls();   // controls.js: view, cat and settings icons
    FIF.initChat();
    FIF.paintSprites(document);
    window.addEventListener("hashchange", route);
    route();
  });
})();
