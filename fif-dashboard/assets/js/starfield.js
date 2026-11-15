/* Low-resolution pixel space background: stars, a moon, a ringed planet and the odd shooting star.
   Drawn at 1/4 resolution and scaled up with pixelated rendering for the retro look. */
(function () {
  const FIF = window.FIF;
  const cv = document.getElementById("space");
  if (!cv) return;
  const g = cv.getContext("2d");
  const SCALE = 4;
  let W = 0, H = 0, stars = [], shoot = null, t = 0, raf = null;

  function resize() {
    W = Math.ceil(window.innerWidth / SCALE); H = Math.ceil(window.innerHeight / SCALE);
    cv.width = W; cv.height = H;
    const n = Math.round((W * H) / 90);
    stars = Array.from({ length: n }, () => ({ x: Math.random() * W | 0, y: Math.random() * H | 0,
      b: Math.random(), s: Math.random() < 0.08 ? 2 : 1, p: Math.random() * 6.28, v: 0.2 + Math.random() * 0.8 }));
    draw();
  }

  function moon(cx, cy, r) {
    for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++) {
      const d = x * x + y * y; if (d > r * r) continue;
      const shade = x + y < -r * 0.4 ? "#e9e6da" : x + y < r * 0.5 ? "#c9c5b6" : "#8f8b7f";
      g.fillStyle = shade; g.fillRect(cx + x, cy + y, 1, 1);
    }
    g.fillStyle = "#a9a596";
    [[-3, -2, 2], [2, 3, 3], [4, -4, 1], [-5, 4, 1]].forEach(([x, y, s]) => g.fillRect(cx + x, cy + y, s, s));
  }

  function planet(cx, cy, r) {
    for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++) {
      if (x * x + y * y > r * r) continue;
      const band = ((y + r) >> 1) % 3;
      g.fillStyle = x > r * 0.35 ? "#5a2f6e" : ["#c05d8f", "#a14c86", "#d97ba0"][band];
      g.fillRect(cx + x, cy + y, 1, 1);
    }
    g.fillStyle = "#f0b042";
    for (let x = -r - 6; x <= r + 6; x++) {
      const y = Math.round(x * 0.28);
      if (Math.abs(x) < r - 1 && y < 0) continue; // ring hidden behind the planet
      g.fillRect(cx + x, cy + y + 1, 1, 1);
    }
  }

  function draw() {
    g.fillStyle = "#050814"; g.fillRect(0, 0, W, H);
    // faint nebula bands
    g.fillStyle = "rgba(60, 40, 120, 0.10)"; g.fillRect(0, (H * 0.62) | 0, W, (H * 0.12) | 0);
    g.fillStyle = "rgba(240, 120, 60, 0.05)"; g.fillRect(0, (H * 0.70) | 0, W, (H * 0.05) | 0);
    for (const s of stars) {
      const tw = FIF.settings.reduceMotion ? 0.8 : 0.55 + 0.45 * Math.sin(s.p + t * 0.02 * s.v);
      const c = Math.round(120 + 135 * s.b * tw);
      g.fillStyle = `rgb(${c},${c},${Math.min(255, c + 25)})`;
      g.fillRect(s.x, s.y, s.s, s.s);
    }
    moon((W * 0.86) | 0, (H * 0.2) | 0, Math.max(8, (H * 0.05) | 0));
    planet((W * 0.08) | 0, (H * 0.82) | 0, Math.max(10, (H * 0.07) | 0));
    if (shoot) {
      g.fillStyle = "#ffffff";
      for (let i = 0; i < 8; i++) { g.globalAlpha = 1 - i / 8; g.fillRect((shoot.x - i * 2) | 0, (shoot.y - i) | 0, 1, 1); }
      g.globalAlpha = 1;
    }
  }

  function loop() {
    t++;
    if (!FIF.settings.reduceMotion && !document.hidden && !document.body.classList.contains("cinematic")) {
      if (!shoot && Math.random() < 0.002) shoot = { x: Math.random() * W * 0.6, y: Math.random() * H * 0.3 };
      if (shoot) { shoot.x += 2; shoot.y += 1; if (shoot.x > W || shoot.y > H) shoot = null; }
      if (t % 3 === 0) draw();
    }
    raf = requestAnimationFrame(loop);
  }

  window.addEventListener("resize", resize);
  FIF.redrawSpace = draw;
  resize();
  loop();
})();
