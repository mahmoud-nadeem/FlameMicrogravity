/* Pixel characters. Built-in: an original 16x16 astronaut in each character's colours, with a closed, opaque visor.
   A character may instead use a pixel PNG made by tools/pixelate.py (with the member's consent);
   then the mouth box from characters.json is darkened while the character talks.

   Characters are alive but calm. Each sprite canvas carries its state in data attributes:
     data-state   idle | speaking | waiting | done   (CSS gives each a different motion)
     data-look    -1 | 0 | 1                         (eyes and pointing arm follow it)
     data-gesture point                               (arm raised toward something)
   One slow ticker handles blinking and the waiting scan for every sprite on screen. It stops
   while the page is hidden and with reduced motion. */
(function () {
  const FIF = window.FIF;
  // K outline, S suit, V visor, W visor glint, M mouth, A accent (chest), . transparent
  const BODY = [
    "................",
    ".....KKKKKK.....",
    "....KSSSSSSK....",
    "...KSSSSSSSSK...",
    "...KSVVVVVVSK...",
    "...KSVWWVVVSK...",
    "...KSVWVVVVSK...",
    "...KSVVMMVVSK...",
    "...KSSVVVVSSK...",
    "....KSSSSSSK....",
  ];
  const ARMS_DOWN = [
    "...KKSAAAASKK...",
    "..KSSSAKKASSSK..",
    "..KSSSAAAASSSK..",
    "..KSSKSSSSKSSK..",
    "...KK.KSSK.KK...",
    "......KKKK......",
  ];
  const ARM_POINT = [ // right arm raised toward what the character is looking at
    "...KKSAAAASSSSK.",
    "..KSSSAKKASKKKK.",
    "..KSSSAAAASK....",
    "..KSSKSSSSK.....",
    "...KK.KSSK......",
    "......KKKK......",
  ];
  const images = {};
  const reduced = () => !!(FIF.settings && FIF.settings.reduceMotion) || (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  function drawGenerated(g, c, talking, cv) {
    const pal = { K: "#0a0f22", S: c.suit || "#d9d6ca", V: c.visor || "#3987e5", W: "#eef6ff", A: c.accent || "#c98500" };
    const d = (cv && cv.dataset) || {};
    const look = +d.look || 0, point = d.gesture === "point", blink = d.blink === "1", scan = d.scan != null ? +d.scan : -1;
    const rows = BODY.concat(point ? ARM_POINT : ARMS_DOWN);
    g.save(); g.clearRect(0, 0, 16, 16);
    if (look < 0) { g.translate(16, 0); g.scale(-1, 1); } // mirrored: turned and pointing left
    rows.forEach((row, y) => [...row].forEach((ch, x) => {
      if (ch === ".") return;
      let col = pal[ch];
      if (ch === "M") col = talking ? "#3a4a78" : pal.V;
      if (ch === "W" && scan >= 0) col = pal.V;                 // the glint moves while waiting
      g.fillStyle = col; g.fillRect(x, y, 1, 1);
    }));
    if (scan >= 0) { g.fillStyle = "#eef6ff"; g.fillRect(5 + (scan % 6), 4, 1, 3); }
    // the visor is opaque (no face); a small reflection glints now and then
    if (blink) { g.fillStyle = "#eef6ff"; g.fillRect(9, 5, 1, 1); }
    g.restore();
  }

  function drawImage(cv, g, c, talking) {
    let img = images[c.sprite];
    if (!img) { img = images[c.sprite] = new Image(); img.onload = () => FIF.drawSprite(cv, c.id, talking); img.src = c.sprite; return; }
    if (!img.complete) return;
    if (cv.width !== img.width) { cv.width = img.width; cv.height = img.height; }
    g.clearRect(0, 0, cv.width, cv.height); g.drawImage(img, 0, 0);
    if (talking && c.mouth) { g.fillStyle = "#1a0b0b"; g.fillRect(c.mouth.x, c.mouth.y, c.mouth.w, c.mouth.h); }
  }

  // Crew astronauts (assets/crew/<id>.png, made by tools/crew_astronauts.py from each member's own illustration):
  // a sheet of frames idle | breath | talk | point. Small portraits show the helmet-and-shoulders crop ("bust");
  // a canvas with class "full" shows the whole astronaut.
  function drawSheet(cv, g, c, talking) {
    let img = images[c.sprite];
    if (!img) { img = images[c.sprite] = new Image(); img.onload = () => FIF.paintSprites(document); img.src = c.sprite; }
    const s = c.sheet, full = cv.classList.contains("full"), [fw, fh] = s.frame, [bx, by, bs] = s.bust;
    const w = full ? fw : bs, h = full ? fh : bs;
    if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h; }
    cv.classList.add("sheet");
    if (!img.complete || !img.naturalWidth) return;
    const d = cv.dataset;
    const pose = d.gesture === "point" ? "point" : talking ? "talk" : d.breath === "1" ? "breath" : "idle";
    const k = Math.max(0, s.frames.indexOf(pose));
    g.save(); g.clearRect(0, 0, w, h); g.imageSmoothingEnabled = false;
    if (+d.look < 0) { g.translate(w, 0); g.scale(-1, 1); }       // turned toward the left
    g.drawImage(img, k * fw + (full ? 0 : bx), full ? 0 : by, w, h, 0, 0, w, h);
    g.restore();
  }

  FIF.drawSprite = function (cv, id, talking = false) {
    const c = FIF.character(id);
    if (!c || !cv) return;
    cv._talking = talking;
    const g = cv.getContext("2d");
    if (c.sheet && c.sprite) drawSheet(cv, g, c, talking);
    else if (c.sprite && c.sprite !== "generated") drawImage(cv, g, c, talking);
    else { if (cv.width !== 16) { cv.width = 16; cv.height = 16; } drawGenerated(g, c, talking, cv); }
  };

  FIF.paintSprites = function (root = document) {
    FIF.$$("canvas.sprite[data-character]", root).forEach((cv) => { if (!cv.dataset.state) cv.dataset.state = "idle"; FIF.drawSprite(cv, cv.dataset.character, cv._talking); });
  };

  /** Change a sprite's pose; with `ms` it returns to idle afterwards. Event-driven only. */
  FIF.setSpriteState = function (cv, patch, ms) {
    if (!cv) return;
    clearTimeout(cv._poseTimer);
    Object.entries(patch).forEach(([k, v]) => { if (v == null || v === 0 && k === "look") delete cv.dataset[k]; else cv.dataset[k] = String(v); });
    FIF.drawSprite(cv, cv.dataset.character, cv._talking);
    if (ms) cv._poseTimer = setTimeout(() => { if (!cv.isConnected) return; delete cv.dataset.look; delete cv.dataset.gesture; if (cv.dataset.state === "done") cv.dataset.state = "idle"; FIF.drawSprite(cv, cv.dataset.character, cv._talking); }, ms);
  };

  FIF.spriteHTML = (id, cls = "", label = "") =>
    `<canvas class="sprite ${cls}" data-character="${FIF.esc(id)}" data-state="idle" width="16" height="16" ${label ? `role="img" aria-label="${FIF.esc(label)}"` : 'aria-hidden="true"'}></canvas>`;

  // One ticker for blinking and the waiting scan of every visible sprite.
  const blinkAt = new WeakMap();
  let tick = 0;
  setInterval(() => {
    if (document.hidden || reduced()) return;
    tick++;
    const now = performance.now();
    document.querySelectorAll("canvas.sprite[data-character]").forEach((cv) => {
      if (!cv.offsetParent && cv.closest("[hidden]")) return;
      let changed = false;
      if (cv.classList.contains("sheet")) {                          // crew astronauts: a slow breath while idle
        if (cv.dataset.state === "idle" && tick % 12 === (cv._phase = cv._phase ?? Math.floor(Math.random() * 12))) {
          cv.dataset.breath = cv.dataset.breath === "1" ? "0" : "1"; FIF.drawSprite(cv, cv.dataset.character, cv._talking);
        }
        return;
      }
      if (cv.dataset.state === "waiting") { cv.dataset.scan = String(tick % 6); changed = true; }
      else if (cv.dataset.scan != null) { delete cv.dataset.scan; changed = true; }
      const next = blinkAt.get(cv);
      if (next == null) blinkAt.set(cv, now + 1500 + Math.random() * 4000);
      else if (cv.dataset.blink === "1") { delete cv.dataset.blink; blinkAt.set(cv, now + 2600 + Math.random() * 4200); changed = true; }
      else if (now >= next) { cv.dataset.blink = "1"; changed = true; }
      if (changed) FIF.drawSprite(cv, cv.dataset.character, cv._talking);
    });
  }, 160);
})();
