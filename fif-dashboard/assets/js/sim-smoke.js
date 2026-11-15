/* Smoke illustration (T3). NOT a physics model: it shows, in pixels, the patterns the flight data
   report (F-T3-1 smoke grows as it ages, F-T3-2 weak air flow gives larger particles) and the
   difference buoyancy makes (on Earth smoke rises; in orbit it only follows the air). */
(function () {
  const FIF = window.FIF;

  FIF.SmokeSim = function (cv, ui) {
    const W = 192, H = 108;
    cv.width = W; cv.height = H;
    const g = cv.getContext("2d");
    const state = { flow: 8, earth: false, heating: true, parts: [], arrived: 0, t: 0, raf: null };
    const SRC = { x: 22, y: 62 }, DET = { x: 168, y: 40, w: 14, h: 44 };

    function spawn() {
      state.parts.push({ x: SRC.x + 6, y: SRC.y - 2 + Math.random() * 4, vx: 0, vy: 0, age: 0, r: 1 });
    }
    function step() {
      state.t++;
      if (state.heating && state.t % 2 === 0) spawn();
      const flowPx = 0.04 + state.flow * 0.055;           // air carries smoke to the right
      const growth = 1 + (8 - state.flow) * 0.09;         // weak flow: smoke stays dense and grows faster
      for (const p of state.parts) {
        p.age++;
        p.vx = flowPx + (Math.random() - 0.5) * 0.25;
        p.vy = (Math.random() - 0.5) * 0.25 + (state.earth ? -0.35 : 0);   // buoyancy only on Earth
        p.x += p.vx; p.y += p.vy;
        p.r = Math.min(4, 1 + (p.age / 260) * growth);
        if (p.x > DET.x && p.y > DET.y && p.y < DET.y + DET.h && !p.hit) { p.hit = true; state.arrived++; }
      }
      state.parts = state.parts.filter((p) => p.x < W + 4 && p.y > -4 && p.y < H + 4 && p.age < 1400);
    }
    function draw() {
      g.fillStyle = "#070b18"; g.fillRect(0, 0, W, H);
      // chamber
      g.strokeStyle = "#2a3660"; g.lineWidth = 1; g.strokeRect(4.5, 14.5, W - 9, H - 22);
      // air flow arrows
      g.fillStyle = "#26304f";
      for (let y = 26; y < H - 12; y += 16) for (let x = 40 + (state.t * state.flow * 0.05) % 20; x < 160; x += 20) g.fillRect(x | 0, y, 5, 1);
      // heater and sample
      const hot = state.heating && (state.t >> 3) % 2;
      g.fillStyle = "#3a4a80"; g.fillRect(SRC.x - 8, SRC.y + 4, 16, 6);
      g.fillStyle = hot ? "#ff7a3d" : "#f0b042"; g.fillRect(SRC.x - 6, SRC.y + 1, 12, 3);
      g.fillStyle = "#d9d6ca"; g.fillRect(SRC.x - 4, SRC.y - 2, 8, 3);
      // particles: square pixels whose size grows with age
      for (const p of state.parts) {
        const shade = Math.max(110, 230 - p.age * 0.12) | 0;
        g.fillStyle = `rgb(${shade},${shade},${shade + 10})`;
        const s = Math.round(p.r);
        g.fillRect(Math.round(p.x), Math.round(p.y), s, s);
      }
      // detector
      g.fillStyle = "#131c38"; g.fillRect(DET.x, DET.y, DET.w, DET.h);
      g.fillStyle = "#6da7ec"; g.fillRect(DET.x + 4, DET.y + 4, 6, 6);
      if (ui.mode) ui.mode.textContent = state.earth ? "ON EARTH (1 g): HOT SMOKE RISES" : "IN ORBIT (MICROGRAVITY): SMOKE ONLY FOLLOWS THE AIR";
    }
    function loop() {
      step(); draw();
      if (ui.meter) ui.meter.style.width = Math.min(100, state.arrived / 4) + "%";
      if (ui.avg) {
        const live = state.parts.filter((p) => p.x > 120);
        ui.avg.textContent = live.length ? (live.reduce((a, p) => a + p.r, 0) / live.length).toFixed(1) + " px" : "-";
      }
      state.raf = requestAnimationFrame(loop);
    }

    ui.flow && ui.flow.addEventListener("input", () => { state.flow = +ui.flow.value; ui.flowOut.textContent = state.flow + " cm/s"; });
    ui.earth && ui.earth.addEventListener("click", () => { state.earth = true; ui.earth.setAttribute("aria-pressed", "true"); ui.orbit.setAttribute("aria-pressed", "false"); });
    ui.orbit && ui.orbit.addEventListener("click", () => { state.earth = false; ui.orbit.setAttribute("aria-pressed", "true"); ui.earth.setAttribute("aria-pressed", "false"); });
    ui.reset && ui.reset.addEventListener("click", () => { state.parts = []; state.arrived = 0; state.t = 0; });

    if (FIF.settings.reduceMotion) { for (let i = 0; i < 700; i++) step(); draw(); }
    else loop();
    return { stop: () => cancelAnimationFrame(state.raf) };
  };
})();
