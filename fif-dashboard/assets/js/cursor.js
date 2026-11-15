/* Rocket cursor. The cursor itself is a native CSS cursor (assets/cursors/*.svg, nose = hotspot), switched by the
   "rocket-cursor" class that controls.js sets from the Rocket cursor setting; it applies to precise pointers only
   (@media (pointer: fine)), so touch screens never get a fake pointer. This file adds an optional, restrained exhaust:
   a few fading puffs behind the rocket while a mouse moves. The puffs are drawn on one canvas that ignores the pointer
   (pointer-events: none), the drawing loop runs only while puffs are visible, and nothing is drawn with reduced motion,
   in a background tab, on touch or pen input, or with the rocket cursor off. */
(function () {
  const F = window.FIF;
  const fine = window.matchMedia ? matchMedia("(pointer: fine)") : { matches: false };
  const sysReduce = window.matchMedia ? matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };
  const MAX = 18, TAIL = 17;                       // the tail is 17 px right and below the nose (the hotspot)
  let cv = null, g = null, puffs = [], raf = 0, last = 0;
  const allowed = () => fine.matches && F.settings.rocketCursor !== false && !F.settings.reduceMotion && !sysReduce.matches && !document.hidden;

  function frame() {
    raf = 0;
    if (!g) return;
    g.clearRect(0, 0, cv.width, cv.height);
    const now = performance.now();
    puffs = puffs.filter((p) => now - p.t < 420);
    puffs.forEach((p) => {
      const k = (now - p.t) / 420;
      g.globalAlpha = 0.45 * (1 - k);
      g.fillStyle = k < 0.35 ? "#ff7a3d" : "#8e97b3";
      const s = Math.round(2 + k * 3);
      g.fillRect(Math.round(p.x + k * 6), Math.round(p.y + k * 6), s, s);   // square puffs: pixel style
    });
    g.globalAlpha = 1;
    if (puffs.length) raf = requestAnimationFrame(frame);
  }
  function ensure() {
    if (cv) return;
    cv = document.createElement("canvas"); cv.className = "rocket-exhaust"; cv.setAttribute("aria-hidden", "true");
    document.body.appendChild(cv); g = cv.getContext("2d"); size();
  }
  function size() { if (cv) { cv.width = innerWidth; cv.height = innerHeight; } }
  function clear() { puffs = []; if (raf) cancelAnimationFrame(raf); raf = 0; if (g) g.clearRect(0, 0, cv.width, cv.height); }

  document.addEventListener("pointermove", (e) => {
    if (e.pointerType !== "mouse" || !allowed()) { if (puffs.length) clear(); return; }
    const now = performance.now();
    if (now - last < 45) return;                   // at most about 22 puffs a second
    last = now; ensure();
    puffs.push({ x: e.clientX + TAIL, y: e.clientY + TAIL, t: now });
    if (puffs.length > MAX) puffs.shift();
    if (!raf) raf = requestAnimationFrame(frame);
  }, { passive: true });
  window.addEventListener("resize", size);
  document.addEventListener("visibilitychange", () => { if (document.hidden) clear(); });
  document.addEventListener("fif:settings", (e) => { const k = e.detail && e.detail.key; if (k === "rocketCursor" || k === "reduceMotion") clear(); });
  F.rocketCursor = { get active() { return document.documentElement.classList.contains("rocket-cursor") && fine.matches; }, get puffs() { return puffs.length; } };
})();
