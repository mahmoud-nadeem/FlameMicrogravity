/* Visual companions for Crew answers. A visual is attached only when the answer's evidence
   matches it, and each one says what kind of thing it is:
   - MEASURED: NASA flight-test values from the SAME/SAME-R table (aging, size, air flow).
   - CALCULATED: the educational transport equation (lab.js), for smoke-transport answers.
   Nothing here invents numbers; the measured views read the same rows as the Results page. */
(function () {
  const F = window.FIF;
  const MED = (a) => F.median(a);

  // ---- measured views ------------------------------------------------------------
  function rows() { return (F.data.datasets && F.data.datasets.same_tests && F.data.datasets.same_tests.rows) || []; }
  function agingPairs() {
    const R = rows(), out = {};
    R.filter((r) => r.aged).forEach((a) => {
      const f = R.find((r) => !r.aged && r.mission === a.mission && r.test === a.parent);
      if (!f) return;
      (out[a.material] = out[a.material] || { fresh: [], aged: [] });
      out[a.material].fresh.push(f.d_um * 1000); out[a.material].aged.push(a.d_um * 1000);
    });
    return Object.entries(out).map(([m, v]) => ({ label: m, bars: [{ name: "fresh", v: MED(v.fresh) }, { name: "aged", v: MED(v.aged) }], n: v.fresh.length }));
  }
  function sizeByMaterial() {
    const R = rows().filter((r) => r.mission === "SAME-R" && !r.aged && r.flow >= 8 && (r.aging_s == null || r.aging_s < 300));
    const mats = [...new Set(R.map((r) => r.material))];
    return mats.map((m) => { const v = R.filter((r) => r.material === m).map((r) => r.d_um * 1000); return { label: m, bars: [{ name: "median", v: MED(v) }], n: v.length }; });
  }
  function flowContrast() {
    const R = rows().filter((r) => r.mission === "SAME-R" && !r.aged && (r.aging_s == null || r.aging_s < 300));
    const out = [];
    [...new Set(R.map((r) => r.material))].forEach((m) => {
      const lo = [], hi = [];
      [...new Set(R.filter((r) => r.material === m && r.flow <= 2).map((r) => r.rt))].forEach((rt) => {
        const a = R.filter((r) => r.material === m && r.rt === rt && r.flow <= 2), b = R.filter((r) => r.material === m && r.rt === rt && r.flow >= 8);
        if (a.length && b.length) { lo.push(...a.map((r) => r.d_um * 1000)); hi.push(...b.map((r) => r.d_um * 1000)); }
      });
      if (lo.length) out.push({ label: m, bars: [{ name: "0-2 cm/s", v: MED(lo) }, { name: "8 cm/s", v: MED(hi) }], n: lo.length + hi.length });
    });
    return out;
  }
  const MEASURED = [
    { refs: ["F-T3-1"], title: "SEE THE MEASURED AGING DATA", note: "Median number-mean particle diameter of the same smoke, fresh and after aging (paired SAME and SAME-R flight tests).", data: agingPairs, fid: "F-T3-1" },
    { refs: ["F-T3-2"], title: "SEE THE MEASURED AIR-FLOW DATA", note: "Median diameter of fresh SAME-R smoke at weak (0-2 cm/s) and normal (8 cm/s) air flow, at heater settings that have both.", data: flowContrast, fid: "F-T3-2" },
    { refs: ["F-T3-3", "F-T3-4", "F-T3-5"], title: "SEE THE MEASURED PARTICLE SIZES", note: "Median diameter of fresh SAME-R smoke at 8 cm/s air flow, by material (all heater settings).", data: sizeByMaterial, fid: "F-T3-3" },
  ];

  function drawBars(canvas, groups) {
    const g = canvas.getContext("2d"), W = canvas.width, H = canvas.height;
    g.fillStyle = "#050814"; g.fillRect(0, 0, W, H);
    const max = Math.max(1, ...groups.flatMap((x) => x.bars.map((b) => b.v || 0)));
    const gw = (W - 20) / Math.max(1, groups.length);
    g.font = "11px monospace"; g.textAlign = "center";
    groups.forEach((grp, i) => {
      const bw = Math.min(26, (gw - 10) / grp.bars.length);
      grp.bars.forEach((b, k) => {
        const h = ((b.v || 0) / max) * (H - 48), x = 10 + i * gw + gw / 2 - (grp.bars.length * bw) / 2 + k * bw, y = H - 28 - h;
        g.fillStyle = k === 0 ? (F.MATERIAL_COLORS[grp.label] || "#6da7ec") : "#f0b042";
        g.fillRect(x + 1, y, bw - 2, h);
        g.fillStyle = "#c3c9db"; g.fillText(Math.round(b.v), x + bw / 2, y - 4);
      });
      g.fillStyle = "#8e97b3"; g.fillText(grp.label, 10 + i * gw + gw / 2, H - 12);
    });
  }

  function attachMeasured(bubble, spec) {
    const groups = spec.data();
    if (!groups.length) return false;
    const legend = groups[0].bars.map((b, k) => `<span class="lg ${k ? "b" : "a"}"></span>${b.name}`).join(" ");
    const d = document.createElement("details"); d.className = "chat-visual measured";
    d.innerHTML = `<summary>&#9654; ${spec.title}</summary><p class="kind-tag measured">MEASURED NASA DATA</p><p class="small">${spec.note}</p>
      <canvas width="320" height="150" role="img"></canvas><p class="small legend">${legend} &middot; values in nm</p>
      <p class="small muted">Source: SAME/SAME-R results workbook rows, as on the Results page. Small groups: read as indications, not general laws.</p>
      <div class="exp-toolbar"><a class="chip" href="#/results">OPEN THE RESULTS CHARTS &#9654;</a><a class="chip" href="#/research?q=${spec.fid}">EVIDENCE ${spec.fid}</a></div>`;
    bubble.append(d);
    const cv = d.querySelector("canvas");
    cv.setAttribute("aria-label", spec.note + " " + groups.map((x) => x.label + ": " + x.bars.map((b) => b.name + " " + Math.round(b.v) + " nm").join(", ")).join("; "));
    d.addEventListener("toggle", () => { if (d.open) drawBars(cv, groups); });
    return true;
  }

  // ---- calculated transport view ---------------------------------------------------
  function attachTransport(bubble) {
    const details = document.createElement("details"); details.className = "chat-visual";
    details.innerHTML = '<summary>&#9654; EXPLORE THE TRANSPORT EXPLANATION</summary><p class="kind-tag calc">CALCULATED &middot; EDUCATIONAL MODEL</p><p class="small">Air moves the pulse; mixing spreads it. Calculated from the 1-D advection-diffusion equation with mixing fixed at 1 cm²/s. It explains transport; it does not predict flight detector performance.</p><canvas width="320" height="130" role="img" aria-label="Calculated smoke transport"></canvas><label>Flow (cm/s) <input type="range" min="0" max="8" step="1" value="2"></label><div class="exp-toolbar"><button class="chip" type="button">PLAY</button><button class="chip" type="button">RESET</button></div><p class="small mini-result" aria-live="polite"></p><a class="chip" href="#/lab/PSI-101">OPEN FULL LAB & EQUATIONS &#9654;</a>';
    bubble.append(details);
    const canvas = details.querySelector("canvas"), g = canvas.getContext("2d"), input = details.querySelector("input"), buttons = details.querySelectorAll("button");
    let time = 0, playing = false, raf = 0, last = 0, paintAt = 0;
    function draw() {
      const u = +input.value; g.fillStyle = "#050814"; g.fillRect(0, 0, 320, 130);
      g.strokeStyle = "#6da7ec"; g.beginPath(); for (let x = 0; x < 300; x++) { const y = 105 - F.transport(x / 3, time, u, 1) * 420; x ? g.lineTo(x + 10, y) : g.moveTo(x + 10, y); } g.stroke();
      g.strokeStyle = "#f0b042"; g.beginPath(); g.moveTo(160, 10); g.lineTo(160, 108); g.stroke();
      g.fillStyle = "#c3c9db"; g.font = "11px monospace"; g.fillText("0 cm", 10, 123); g.fillText("sensor: 50 cm", 120, 123); g.fillText("100 cm", 270, 123);
      const message = time.toFixed(1) + " s · " + u + " cm/s · pulse centre " + (time * u).toFixed(1) + " cm (calculated)";
      details.querySelector(".mini-result").textContent = message; canvas.setAttribute("aria-label", message);
    }
    function pause() { playing = false; cancelAnimationFrame(raf); buttons[0].textContent = "PLAY"; }
    function loop(now) {
      if (!details.isConnected || !details.open) { pause(); return; }
      const visible = !document.hidden && !document.querySelector("#chat").hidden;
      if (visible) { time = Math.min(60, time + Math.min((now - last) / 1000, 0.1)); if (now - paintAt > 120) { draw(); paintAt = now; } }
      last = now; if (time >= 60) { pause(); draw(); return; } raf = requestAnimationFrame(loop);
    }
    buttons[0].onclick = () => { if (playing) return pause(); if (time >= 60) time = 0; playing = true; last = performance.now(); buttons[0].textContent = "PAUSE"; raf = requestAnimationFrame(loop); };
    buttons[1].onclick = () => { pause(); time = 0; input.value = 2; draw(); };
    input.oninput = () => { pause(); draw(); };
    details.addEventListener("toggle", () => { if (!details.open) pause(); else draw(); });
    draw();
  }

  F.attachChatVisual = function (bubble, answer, text) {
    const ids = answer.refs || [];
    const spec = MEASURED.find((m) => m.refs.some((r) => ids.includes(r)));
    if (spec && attachMeasured(bubble, spec)) return;
    if (ids.some((id) => ["F-T3-16", "F-T3-17", "F-T3-20"].includes(id)) || (/flow|transport|airflow/i.test(text) && /smoke/i.test(text) && !ids.length)) attachTransport(bubble);
  };
})();
