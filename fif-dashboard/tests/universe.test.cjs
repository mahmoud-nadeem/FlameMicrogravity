/* Universe engine: camera framing and the 2D fallback, without a browser.
   WebGL is unavailable here, so the engine must fall back to its 2D canvas. */
const fs = require("node:fs"), vm = require("node:vm"), path = require("node:path"), assert = require("node:assert/strict");
const root = path.join(__dirname, "..");
const ctx2d = new Proxy({}, { get: (t, k) => (k in t ? t[k] : () => ({ addColorStop() {} })) });
function canvas() { return { width: 0, height: 0, id: "", className: "", classList: { toggle() {} }, setAttribute() {}, addEventListener() {}, remove() {}, after() {},
  getContext: (type) => (type === "2d" ? ctx2d : null) }; }
const listeners = {};
const doc = { readyState: "complete", hidden: false, createElement: canvas, addEventListener(k, f) { listeners[k] = f; },
  body: { prepend() {}, classList: { contains: (c) => c === "cinematic" }, dataset: {} },
  documentElement: { classList: { contains: () => false }, scrollHeight: 2000 }, dispatchEvent() {} };
const win = { innerWidth: 1440, innerHeight: 900, devicePixelRatio: 1, scrollY: 0, addEventListener() {}, matchMedia: () => ({ matches: false, addEventListener() {} }) };
const context = vm.createContext({ window: win, document: doc, requestAnimationFrame: () => 1, cancelAnimationFrame() {}, performance: { now: () => 0 },
  CustomEvent: class { constructor(n) { this.type = n; } }, console: { info() {}, warn() {}, log: console.log } });
for (const f of ["data/site-data.js", "assets/js/util.js", "assets/js/planet-renderer.js", "assets/js/space-engine.js"])
  vm.runInContext(fs.readFileSync(path.join(root, f), "utf8"), context, { filename: f });
const F = context.window.FIF, U = F.universe, D = F.data;

assert.equal(U.mode, "2d", "falls back to the 2D universe when WebGL is missing");
const moons = D.tracks.reduce((n, t) => n + t.records.length, 0);
assert.equal(U.bodies.length, 1 + D.tracks.length + moons, "one star, one world per track, one moon per experiment record");

const { worldShot, homeKey, basis, scenes, FOV } = U._debug, W = 1440, H = 900;
function project(cam, p) {
  const b = basis(cam.eye, cam.target), d = [p[0] - cam.eye[0], p[1] - cam.eye[1], p[2] - cam.eye[2]];
  const dot = (a, c) => a[0] * c[0] + a[1] * c[1] + a[2] * c[2], z = dot(d, b.f), k = (H / 2) / Math.tan(FOV / 2) / z;
  return { x: W / 2 + dot(d, b.r) * k, y: H / 2 - dot(d, b.u) * k, z, k };
}
const worlds = U.bodies.filter((b) => b.kind === "planet");
for (const w of worlds) for (const side of [1, -1]) {
  const p = project(worldShot(w, 6.2, side), w.pos), r = w.r * p.k;
  assert.ok(p.z > 0, "world in front of the camera");
  assert.ok(side > 0 ? p.x > W / 2 : p.x < W / 2, `${w.id} framed on the ${side > 0 ? "right" : "left"}`);
  assert.ok(p.x - r > -r * 0.2 && p.x + r < W + r * 0.2 && p.y > 0 && p.y < H, `${w.id} on screen`);
  assert.ok(r > H * 0.08 && r < H * 0.45, `${w.id} has a readable size (${Math.round(r)} px)`);
}
// home story: each world section frames its own world on the side opposite the text
for (let k = 4; k <= 9; k++) { const w = worlds[k - 4], p = project(homeKey(k), w.pos); assert.ok(p.z > 0 && p.x > 0 && p.x < W, `home key ${k} shows ${w.id}`); assert.ok(k % 2 ? p.x < W / 2 : p.x > W / 2, `home key ${k} side`); }
// mission map: every world is in view at the default camera
const map = scenes.map();
for (const w of worlds) { const p = project(map, w.pos); assert.ok(p.z > 0 && p.x > 0 && p.x < W && p.y > 0 && p.y < H, `${w.id} visible on the map`); }
// travel resolves immediately with reduced motion
F.settings.reduceMotion = true;
let done = false; U.setScene("map").then(() => (done = true));
setTimeout(() => { assert.ok(done, "scene change resolves under reduced motion");
  console.log("Passed: 2D fallback, body graph, world framing (both sides), home keyframes, map framing, reduced-motion travel."); }, 0);
