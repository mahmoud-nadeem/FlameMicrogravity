/* Control dock: three quiet icons in the top bar instead of a row of text buttons.
     view      switches the cinematic universe and the original retro look (one click, no menu)
     cat       a small menu for Bondoq: show or hide him, and pause or resume him
     settings  a small menu of switches: sound, reduce motion, crew reactions, rocket cursor
   Every icon has an accessible name, a tooltip on hover and keyboard focus, and its state in ARIA (aria-pressed or
   role="switch" + aria-checked), never in colour alone. Menus close with Escape, a click outside or a second click, and
   stay inside the viewport. Changing a setting only saves it (FIF.saveSetting): the route, the conversation, the lab and
   a running tour are left alone. */
(function () {
  const F = window.FIF;
  const svg = (body) => `<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" shape-rendering="crispEdges">${body}</svg>`;
  const ICON = {
    cinema: svg('<circle cx="12" cy="12" r="6"/><path d="M2 14c4-1 16-5 20-8"/><path d="M5 4h1M19 18h1M18 3h1" stroke-width="2.4"/>'),
    retro: svg('<path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4z"/><path d="M14 14h6v6h-6z" fill="currentColor"/>'),
    cat: svg('<path d="M5 20v-9l-1-7 5 4h6l5-4-1 7v9z"/><path d="M9 13h.5M14.5 13h.5" stroke-width="2.6"/><path d="M11 16h2"/>'),
    gear: svg('<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/><circle cx="12" cy="12" r="7"/>'),
  };
  // switches in each menu: [setting key, label, short help]; "inverted" shows the opposite of the stored flag
  const SETTINGS = [
    { key: "sound", id: "sound-toggle", label: "Sound", help: "Short blips while characters talk" },
    { key: "reduceMotion", id: "motion-toggle", label: "Motion", help: "Animations, travel and the cat's walking", inverted: true },
    { key: "reactions", id: "reaction-toggle", label: "Crew reactions", help: "Characters react to what you do", def: true },
    { key: "rocketCursor", id: "rocket-toggle", label: "Rocket cursor", help: "Mouse and trackpad only", def: true },
  ];
  const CAT = [
    { key: "bondoq", id: "bondoq-toggle", label: "Show Bondoq", help: "The crew's cat on the ledge", def: true },
    { key: "bondoqPaused", id: "bondoq-pause", label: "Bondoq moving", help: "Off: he stays where he is", inverted: true },
  ];
  const on = (o) => { const v = F.settings[o.key]; const b = v === undefined ? !!o.def : !!v; return o.inverted ? !b : b; };

  let dock, open = null, toast, toastT;
  function say(msg) { toast.textContent = msg; toast.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => (toast.hidden = true), 1800); }

  function iconButton(id, label, icon, extra = "") {
    return `<button type="button" class="dock-btn" id="${id}" aria-label="${label}" data-tip="${label}" ${extra}>${icon}<span class="dock-state" aria-hidden="true"></span></button>`;
  }
  function menu(id, title, items) {
    return `<div class="dock-menu" id="${id}" role="group" aria-label="${title}" hidden><p class="dock-menu-title">${title}</p>${items.map((o) => `
      <button type="button" class="dock-switch" role="switch" id="${o.id}" data-key="${o.key}" aria-checked="false">
        <span class="dock-switch-text"><span class="dock-switch-label">${o.label}</span><span class="dock-switch-help">${o.help}</span></span>
        <span class="dock-track" aria-hidden="true"><span class="dock-knob"></span></span><span class="dock-switch-word" aria-hidden="true"></span></button>`).join("")}</div>`;
  }

  function paint() {
    const cine = !!F.settings.cinematic, view = dock.querySelector("#space-toggle");
    view.innerHTML = (cine ? ICON.cinema : ICON.retro) + '<span class="dock-state" aria-hidden="true"></span>';
    view.setAttribute("aria-pressed", String(cine));
    const tip = cine ? "Cinematic view (on): switch to retro" : "Retro view (on): switch to cinematic";
    view.dataset.tip = tip; view.setAttribute("aria-label", "Cinematic view");
    [...SETTINGS, ...CAT].forEach((o) => {
      const b = dock.querySelector("#" + o.id), v = on(o);
      b.setAttribute("aria-checked", String(v)); b.querySelector(".dock-switch-word").textContent = v ? "ON" : "OFF";
    });
    const pause = dock.querySelector("#bondoq-pause"); pause.disabled = !F.settings.bondoq;
    const cat = dock.querySelector("#dock-cat");
    cat.dataset.badge = !F.settings.bondoq ? "hidden" : F.settings.bondoqPaused ? "paused" : "";
    cat.dataset.tip = "Bondoq the cat" + (!F.settings.bondoq ? " (hidden)" : F.settings.bondoqPaused ? " (paused)" : "");
    cat.setAttribute("aria-label", "Bondoq the cat: options" + (!F.settings.bondoq ? ", hidden" : F.settings.bondoqPaused ? ", paused" : ""));
    document.body.classList.toggle("reduce-motion", !!F.settings.reduceMotion);
    document.body.classList.toggle("cinematic", cine);
    document.documentElement.classList.toggle("rocket-cursor", on(SETTINGS[3]));
    document.documentElement.classList.remove("cinematic-boot");
  }

  function place(m, btn) {                                       // below its icon, right-aligned, always inside the viewport
    m.style.left = "0px"; m.style.top = "0px";
    const b = btn.getBoundingClientRect(), w = m.offsetWidth, h = m.offsetHeight, pad = 8;
    let x = b.right - w, y = b.bottom + 8;
    x = Math.max(pad, Math.min(x, innerWidth - w - pad));
    if (y + h > innerHeight - pad) y = Math.max(pad, b.top - h - 8);
    m.style.left = x + "px"; m.style.top = y + "px";
  }
  function show(m, btn, byKey) {
    if (open && open.m === m) return close(true);
    close(false);
    m.hidden = false; btn.setAttribute("aria-expanded", "true"); place(m, btn);
    open = { m, btn };
    const first = m.querySelector(".dock-switch:not(:disabled)");          // keyboard users land on the first switch
    if (first && byKey) first.focus({ preventScroll: true });
  }
  function close(refocus) {
    if (!open) return;
    open.m.hidden = true; open.btn.setAttribute("aria-expanded", "false");
    if (refocus) open.btn.focus({ preventScroll: true });
    open = null;
  }

  F.initControls = function () {
    const bar = document.querySelector(".top-actions"); if (!bar || dock) return;
    if (F.settings.cinematic === undefined) F.settings.cinematic = document.documentElement.classList.contains("cinematic-boot");
    bar.classList.add("dock"); bar.setAttribute("role", "toolbar"); bar.setAttribute("aria-label", "Display and settings");
    bar.innerHTML = iconButton("space-toggle", "Cinematic view", ICON.cinema, 'aria-pressed="true"') +
      iconButton("dock-cat", "Bondoq the cat: options", ICON.cat, 'aria-haspopup="true" aria-expanded="false" aria-controls="menu-cat"') +
      iconButton("dock-settings", "Settings", ICON.gear, 'aria-haspopup="true" aria-expanded="false" aria-controls="menu-settings"') +
      menu("menu-cat", "BONDOQ", CAT) + menu("menu-settings", "SETTINGS", SETTINGS) +
      '<p class="dock-toast" role="status" aria-live="polite" hidden></p>';
    dock = bar; toast = bar.querySelector(".dock-toast");
    const mCat = bar.querySelector("#menu-cat"), mSet = bar.querySelector("#menu-settings");
    // menus live in the body so the top bar's overflow never clips them
    document.body.append(mCat, mSet, toast);
    const find = (id) => document.getElementById(id);
    dock = { querySelector: (q) => (q.startsWith("#") ? find(q.slice(1)) : bar.querySelector(q)) };

    find("space-toggle").onclick = () => {
      F.saveSetting("cinematic", !F.settings.cinematic); paint();
      F.universe && F.universe.refresh && F.universe.refresh(); F.redrawSpace && F.redrawSpace();   // never reloads, re-routes or resets
      say(F.settings.cinematic ? "Cinematic view" : "Retro view");
    };
    find("dock-cat").onclick = (e) => show(mCat, e.currentTarget, e.detail === 0);        // detail 0: Enter or Space
    find("dock-settings").onclick = (e) => show(mSet, e.currentTarget, e.detail === 0);
    [...SETTINGS, ...CAT].forEach((o) => {
      find(o.id).onclick = () => {
        const next = !on(o);
        F.saveSetting(o.key, o.inverted ? !next : next);
        if (o.key === "reduceMotion") F.redrawSpace && F.redrawSpace();
        paint();
      };
    });
    // keyboard: Escape closes and returns focus; arrows move between switches
    document.addEventListener("keydown", (e) => {
      if (!open) return;
      if (e.key === "Escape") { e.preventDefault(); e.stopImmediatePropagation(); close(true); return; }
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        const list = [...open.m.querySelectorAll(".dock-switch:not(:disabled)")], i = list.indexOf(document.activeElement);
        if (i >= 0) { e.preventDefault(); list[(i + (e.key === "ArrowDown" ? 1 : list.length - 1)) % list.length].focus(); }
      }
    }, true);
    document.addEventListener("pointerdown", (e) => { if (open && !open.m.contains(e.target) && !open.btn.contains(e.target)) close(false); });
    document.addEventListener("focusin", (e) => { if (open && !open.m.contains(e.target) && !open.btn.contains(e.target)) close(false); });
    window.addEventListener("resize", () => open && place(open.m, open.btn));
    window.addEventListener("hashchange", () => close(false));
    document.addEventListener("fif:settings", paint);           // other code (tests, Bondoq) may change a setting too
    paint();
  };
})();
