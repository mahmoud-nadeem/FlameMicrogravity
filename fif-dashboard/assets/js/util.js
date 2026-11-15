/* Shared helpers. Every script attaches to window.FIF; no build step, works from file://. */
(function () {
  const FIF = (window.FIF = window.FIF || {});
  const D = window.FIF_DATA || { tracks: [], records: {}, findings: [], questions: [], datasets: {}, characters: { characters: [] } };
  FIF.data = D;

  FIF.esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  FIF.$ = (sel, root = document) => root.querySelector(sel);
  FIF.$$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  // settings kept per browser when possible (storage can be unavailable: always fall back)
  const store = {
    get(k, d) { try { const v = localStorage.getItem("fif." + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem("fif." + k, JSON.stringify(v)); } catch (e) { /* ignore */ } },
  };
  const systemReduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  FIF.settings = { sound: store.get("sound", false), reduceMotion: store.get("reduceMotion", systemReduce), reactions: store.get("reactions", true), cinematic: store.get("cinematic", true), rocketCursor: store.get("rocketCursor", true) };
  FIF.saveSetting = (k, v) => { FIF.settings[k] = v; store.set(k, v); document.dispatchEvent(new CustomEvent("fif:settings",{detail:{key:k,value:v}})); };

  FIF.characters = (D.characters && D.characters.characters) || [];
  FIF.character = (id) => FIF.characters.find((c) => c.id === id) || FIF.characters[0];
  FIF.characterForTrack = (tid) => FIF.characters.find((c) => c.track === tid);
  FIF.track = (tid) => D.tracks.find((t) => t.id === tid);
  FIF.finding = (fid) => D.findings.find((f) => f.id === fid);

  FIF.MATERIAL_COLORS = { Kapton: "#3987e5", Teflon: "#d95926", Lampwick: "#199e70", Pyrell: "#c98500", Silicone: "#d55181" };
  FIF.KIND_LABEL = { observed: "OBSERVED IN DATA", reported: "REPORTED BY NASA", inference: "OUR INFERENCE" };

  // tiny retro "blip" for dialogue text (off by default)
  let ctx = null;
  FIF.blip = function () {
    if (!FIF.settings.sound) return;
    try {
      ctx = ctx || new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = "square"; o.frequency.value = 520 + Math.random() * 120;
      g.gain.setValueAtTime(0.03, ctx.currentTime); g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.05);
      o.connect(g).connect(ctx.destination); o.start(); o.stop(ctx.currentTime + 0.05);
    } catch (e) { /* no audio */ }
  };

  FIF.median = (a) => { const s = a.filter((x) => x != null && !isNaN(x)).sort((x, y) => x - y); if (!s.length) return null;
    const m = Math.floor(s.length / 2); return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

  FIF.downloadCSV = function (name, rows) {
    if (!rows.length) return;
    const cols = Object.keys(rows[0]);
    const q = (v) => { const s = String(v ?? ""); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
    const text = [cols.join(","), ...rows.map((r) => cols.map((c) => q(r[c])).join(","))].join("\n");
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
    a.download = name; document.body.appendChild(a); a.click(); a.remove();
  };
})();
