/* Interactive charts (Chart.js, bundled locally). Colours: validated categorical slots for the
   five materials (fixed order, never cycled); text in ink colours; one y-axis per chart. */
(function () {
  const FIF = window.FIF;
  const INK = "#c3c9db", GRID = "rgba(58, 74, 128, 0.35)", FRESH = "#8e97b3", AGED = "#f0b042", LOW = "#f0b042", HIGH = "#8e97b3";

  if (window.Chart) {
    Chart.defaults.color = INK;
    Chart.defaults.font.family = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
    Chart.defaults.font.size = 13;
    Chart.defaults.borderColor = GRID;
    Chart.defaults.plugins.tooltip.backgroundColor = "#0a0f22";
    Chart.defaults.plugins.tooltip.borderColor = "#eef0f6";
    Chart.defaults.plugins.tooltip.borderWidth = 2;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.animation = { duration: 450 };
  }

  /* Chart ownership. Every canvas gets one ChartSlot, created and destroyed by the view that owns
     it. A slot only ever touches its own canvas: a new selection UPDATES the existing chart in place
     (no destroy, so the chart never blanks and other charts are never affected); an empty selection
     or an error replaces the canvas area with an explicit message instead of a blank box. */
  FIF.ChartSlot = function (cv) {
    const box = cv && cv.parentElement;
    let chart = null, dead = false, msg = null;
    const state = (kind, text) => {
      if (!box) return;
      box.dataset.state = kind;
      if (kind === "ready") { if (msg) msg.hidden = true; cv.hidden = false; return; }
      if (!msg) { msg = document.createElement("p"); msg.className = "chart-state"; msg.setAttribute("role", "status"); box.appendChild(msg); }
      msg.hidden = false; msg.textContent = text; cv.hidden = true;
    };
    const drop = () => { if (chart) { chart.destroy(); chart = null; } };
    return {
      // build() returns { config } or { empty: "reason" }; it may throw.
      render(build) {
        if (dead || !cv) return;
        if (!cv.isConnected) { drop(); return; }               // the view was replaced; never draw into a detached canvas
        if (!window.Chart) { state("error", "The chart library did not load, so this chart cannot be drawn. The numbers are on the Research page."); return; }
        let out;
        try { out = build(); } catch (e) { console.error("chart data", cv.id, e); drop(); state("error", `This chart could not be prepared (${e.message}). The numbers are on the Research page.`); return; }
        if (!out || out.empty) { drop(); state("empty", (out && out.empty) || "No data for this selection."); return; }
        const cfg = out.config;
        if (FIF.settings.reduceMotion) cfg.options = Object.assign({}, cfg.options, { animation: false });
        try {
          if (chart && chart.config.type === cfg.type) {           // same chart, new selection: update in place
            chart.data = cfg.data; chart.options = cfg.options; state("ready"); chart.update();
          } else {
            drop();
            const stray = Chart.getChart(cv); if (stray) stray.destroy();   // never two instances on one canvas
            state("ready"); chart = new Chart(cv, cfg);
          }
        } catch (e) { console.error("chart render", cv.id, e); drop(); state("error", `This chart could not be drawn (${e.message}). The numbers are on the Research page.`); }
      },
      get chart() { return chart; },
      destroy() { dead = true; drop(); },
    };
  };
  const EMPTY = "No data for this selection.";
  const nm = (um) => Math.round(um * 1000);
  const rowsFor = (ds, mission) => ds.rows.filter((r) => r.mission === mission);
  const fresh = (r) => !r.aged && r.aging_s != null && r.aging_s < 300;   // same rule as the analysis script

  // 1. particle size of fresh smoke at 8 cm/s, one dot per test, median bar per material
  FIF.chartSizeByMaterial = function (ds, { materials, mission }) {
    const rows = rowsFor(ds, mission).filter((r) => fresh(r) && r.flow >= 8 && materials.includes(r.material));
    const mats = materials.filter((m) => rows.some((r) => r.material === m));
    const datasets = mats.map((m, i) => ({
      label: m, backgroundColor: FIF.MATERIAL_COLORS[m], borderColor: "#050814", borderWidth: 1.5, pointRadius: 6, pointHoverRadius: 8,
      data: rows.filter((r) => r.material === m).map((r, j) => ({ x: i + ((j % 5) - 2) * 0.06, y: nm(r.d_um), r })),
    }));
    if (!rows.length) return { empty: materials.length ? `${EMPTY} No fresh-smoke tests at 8 cm/s for these materials on ${mission}.` : `${EMPTY} Pick at least one material.` };
    datasets.push({ label: "Median", type: "scatter", pointStyle: "line", pointRadius: 18, borderWidth: 3, borderColor: "#eef0f6", backgroundColor: "#eef0f6",
      data: mats.map((m, i) => ({ x: i, y: nm(FIF.median(rows.filter((r) => r.material === m).map((r) => r.d_um))) })) });
    return { config: { type: "scatter", data: { datasets }, options: {
      maintainAspectRatio: false,
      scales: { x: { min: -0.6, max: Math.max(mats.length - 0.4, 0.6), grid: { display: false },
                     afterBuildTicks: (ax) => { ax.ticks = mats.map((_, i) => ({ value: i })); },
                     ticks: { autoSkip: false, maxRotation: 0, callback: (v) => mats[v] || "" } },
                y: { title: { display: true, text: "mean particle diameter (nm)" }, beginAtZero: true } },
      plugins: { legend: { position: "bottom", labels: { usePointStyle: true } },
        tooltip: { callbacks: { label: (c) => c.raw.r ? `${c.raw.r.material} test ${c.raw.r.test}: ${c.raw.y} nm, heater Rt/R0 ${c.raw.r.rt}, workbook row ${c.raw.r.row}` : `median ${c.raw.y} nm` } } } } } };
  };

  // 2. the same smoke before and after aging (paired tests): median per material
  FIF.chartAging = function (ds, { materials, mission }) {
    const rows = rowsFor(ds, mission);
    const pairs = [];
    rows.filter((r) => !r.aged).forEach((r) => {
      const a = rows.find((x) => x.aged && x.parent === r.parent && x.material === r.material);
      if (a && materials.includes(r.material)) pairs.push({ m: r.material, before: r.d_um, after: a.d_um });
    });
    const mats = materials.filter((m) => pairs.some((p) => p.m === m));
    if (!pairs.length) return { empty: materials.length ? `${EMPTY} No paired fresh/aged tests for these materials on ${mission}.` : `${EMPTY} Pick at least one material.` };
    const med = (m, k) => nm(FIF.median(pairs.filter((p) => p.m === m).map((p) => p[k])));
    return { config: { type: "bar", data: { labels: mats.map((m) => `${m} (${pairs.filter((p) => p.m === m).length} pairs)`), datasets: [
        { label: "Fresh smoke", data: mats.map((m) => med(m, "before")), backgroundColor: FRESH, borderRadius: 4, borderSkipped: "start" },
        { label: "Same smoke after aging", data: mats.map((m) => med(m, "after")), backgroundColor: AGED, borderRadius: 4, borderSkipped: "start" }] },
      options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: "median mean diameter (nm)" } }, x: { grid: { display: false } } },
        plugins: { legend: { position: "bottom" }, tooltip: { callbacks: { label: (c) => `${c.dataset.label}: ${c.raw} nm` } } } } } };
  };

  // 3. weak air flow (0-2 cm/s) vs 8 cm/s, fresh smoke, compared WITHIN each heater setting
  //    (pooling heater settings can reverse the direction for some materials)
  FIF.chartFlow = function (ds, { materials, mission }) {
    const rows = rowsFor(ds, mission).filter(fresh), out = [];
    materials.forEach((m) => {
      const mr = rows.filter((r) => r.material === m);
      [...new Set(mr.filter((r) => r.flow <= 2).map((r) => r.rt))].sort().forEach((rt) => {
        const lo = mr.filter((r) => r.flow <= 2 && r.rt === rt), hi = mr.filter((r) => r.flow >= 8 && r.rt === rt);
        if (lo.length && hi.length) out.push({ label: `${m} ${rt} (n ${lo.length}/${hi.length})`, lo, hi });
      });
    });
    if (!out.length) return { empty: materials.length ? `${EMPTY} No heater setting on ${mission} has both weak and normal air flow for these materials.` : `${EMPTY} Pick at least one material.` };
    return { config: { type: "bar", data: { labels: out.map((o) => o.label), datasets: [
        { label: "0-2 cm/s air flow", data: out.map((o) => nm(FIF.median(o.lo.map((r) => r.d_um)))), backgroundColor: LOW, borderRadius: 4, borderSkipped: "start" },
        { label: "8 cm/s air flow", data: out.map((o) => nm(FIF.median(o.hi.map((r) => r.d_um)))), backgroundColor: HIGH, borderRadius: 4, borderSkipped: "start" }] },
      options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: "median mean diameter (nm)" } },
          x: { grid: { display: false }, title: { display: true, text: "material, heater setting Rt/R0 (tests low/normal flow)" } } },
        plugins: { legend: { position: "bottom" } } } } };
  };

  // 4. crew results charts (build_site_data.py: analysis/<track>/extra/results_charts.json). Numbers are transcribed from the
  //    crew member's findings; `series` is the list of dataset labels the viewer left switched on.
  const SERIES = ["#6da7ec", "#f0b042", "#8e97b3", "#e07a5f"];
  FIF.chartCrewResult = function (c, { series }) {
    const sets = c.datasets.map((d, i) => Object.assign({}, d, { color: SERIES[i % SERIES.length] })).filter((d) => series.includes(d.label));
    if (!sets.length) return { empty: `${EMPTY} Switch on at least one series.` };
    const line = c.type === "line";
    return { config: { type: line ? "line" : "bar", data: { labels: c.labels, datasets: sets.map((d) => ({
        label: d.label, data: d.data, backgroundColor: d.color, borderColor: d.color, spanGaps: true, pointRadius: line ? 4 : 0, borderWidth: line ? 2.5 : 0,
        borderRadius: line ? 0 : 4, borderSkipped: "start" })) },
      options: { maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, stacked: !!c.stacked, title: { display: true, text: c.y } }, x: { stacked: !!c.stacked, grid: { display: false } } },
        plugins: { legend: { position: "bottom" }, tooltip: { callbacks: { label: (x) => x.raw == null ? `${x.dataset.label}: no value` : `${x.dataset.label}: ${x.raw} ${c.y.replace(/^.*\((.*)\).*$/, "$1")}` } } } } } };
  };
})();
