/* Mission map lifecycle without a browser: selection, keyboard, approach, return, cleanup. */
const fs = require("node:fs"), vm = require("node:vm"), path = require("node:path"), assert = require("node:assert/strict");
const root = path.join(__dirname, "..");

class Node {
  constructor(sel = "") { this.sel = sel; this.style = { setProperty() {}, transform: "" }; this.attrs = {}; this.handlers = {}; this.dataset = {}; this.hidden = false;
    this.textContent = ""; this.classes = new Set(); this.children = {}; this.disabled = false; this.offsetWidth = 300; this.offsetHeight = 260;
    this.classList = { toggle: (c, on) => (on === undefined ? (this.classes.has(c) ? this.classes.delete(c) : this.classes.add(c)) : on ? this.classes.add(c) : this.classes.delete(c)),
      add: (c) => this.classes.add(c), remove: (c) => this.classes.delete(c), contains: (c) => this.classes.has(c) }; }
  setAttribute(k, v) { this.attrs[k] = String(v); } getAttribute(k) { return this.attrs[k]; }
  addEventListener(k, f) { (this.handlers[k] = this.handlers[k] || []).push(f); }
  removeEventListener() {} focus() { focused = this; } closest() { return null; } scrollIntoView() {}
  getBoundingClientRect() { return { top: 0, left: 0, bottom: 800, width: 1440, height: 800 }; }
  querySelector(s) { return (this.children[s] = this.children[s] || new Node(s)); } querySelectorAll() { return []; }
  set innerHTML(v) { this._html = v; this.children = {}; } get innerHTML() { return this._html || ""; }
  fire(k, e = {}) { (this.handlers[k] || []).forEach((f) => f(Object.assign({ preventDefault() {}, pointerType: "mouse", button: 0 }, e))); }
}
let focused = null;
const nodes = Array.from({ length: 6 }, (_, i) => Object.assign(new Node(".map-node"), { dataset: { index: String(i) } }));
const els = new Map(), $ = (s) => { if (!els.has(s)) els.set(s, new Node(s)); return els.get(s); };
const rootEl = { querySelector: $, querySelectorAll: (s) => (s === ".map-node" ? nodes : []) };

// A fake universe that records what the map asks of it.
const frames = new Set(); let approached = null, resolveApproach;
const U = { mapView: { yaw: 0.55, pitch: 0.46, dist: 58 }, state: {}, mode: "webgl",
  body: (id) => ({ id, pos: [0, 0, 0], r: 1, moons: [], orbit: { a: 10, inc: 0 } }), reduceMotion: () => false, requestFrame() {},
  onFrame(fn) { frames.add(fn); return () => frames.delete(fn); }, setScene() { return Promise.resolve(); },
  approach(id) { approached = id; return new Promise((r) => (resolveApproach = r)); },
  projectBody: () => ({ x: 700, y: 400, r: 20, depth: 40, visible: true }), project: () => ({ x: 0, y: 0, depth: 40 }) };
const location = { hash: "#/explore" };
const docListeners = new Map();
const ctx = vm.createContext({ window: { matchMedia: () => ({ matches: false, addEventListener() {}, removeEventListener() {} }) }, location, innerWidth: 1440,
  document: { addEventListener: (k, f) => docListeners.set(k, f), removeEventListener: (k) => docListeners.delete(k) } });
vm.runInContext(fs.readFileSync(path.join(root, "data/site-data.js"), "utf8"), ctx);
const data = ctx.window.FIF_DATA;
ctx.window.FIF = { data, settings: { reduceMotion: false, reactions: true }, esc: String, universe: U,
  worlds: Array.from({ length: 6 }, (_, i) => ({ name: "WORLD" + i, theme: "theme" })),
  pages: { crewDirectory: () => ({ html: "directory", mount() {} }) },
  characterForTrack: (id) => data.characters.characters.find((c) => c.track === id), spriteHTML: () => "", openChat() {}, setSpriteState() {} };
vm.runInContext(fs.readFileSync(path.join(root, "assets/js/orbital-explore.js"), "utf8"), ctx);
const F = ctx.window.FIF, page = F.pages.explore();

assert.equal((page.html.match(/class="map-node"/g) || []).length, 6, "one button per world");
let cleanup = page.mount(rootEl);
assert.equal($("#map-count").textContent, "WORLD 1 / 6");
assert.equal(frames.size, 1, "one per-frame callback while mounted");
$("#map-next").onclick(); assert.equal($("#map-count").textContent, "WORLD 2 / 6");
assert.ok(nodes[1].classes.has("is-selected"));
nodes[1].fire("keydown", { key: "ArrowRight" }); assert.equal($("#map-count").textContent, "WORLD 3 / 6"); assert.equal(focused, nodes[2], "focus follows arrow keys");
nodes[0].fire("pointerenter"); assert.ok(U.state.hover, "hover stabilises the system"); nodes[0].fire("pointerleave"); assert.equal(U.state.hover, null);
// touch: first tap selects, second tap approaches
nodes[4].fire("pointerdown", { pointerType: "touch" }); nodes[4].fire("click"); assert.equal($("#map-count").textContent, "WORLD 5 / 6"); assert.equal(approached, null);
nodes[4].fire("pointerdown", { pointerType: "touch" }); nodes[4].fire("click"); assert.equal(approached, "w-T5");
resolveApproach();
setTimeout(() => {
  assert.equal(location.hash, "#/profile/" + data.characters.characters.find((c) => c.track === "T5").id, "navigates after the approach");
  U.mapView.yaw = 1.23; cleanup();
  assert.equal(frames.size, 0, "frame callback removed"); assert.equal(docListeners.size, 0, "document listeners removed");
  assert.equal(U.state.hover, null); assert.equal(U.state.dimOthers, null);
  // returning restores the view and the world, and the guide notices the return once
  U.mapView.yaw = 0; cleanup = page.mount(rootEl);
  assert.equal(U.mapView.yaw, 1.23, "camera angle restored");
  assert.equal($("#map-count").textContent, "WORLD 5 / 6", "selection restored");
  assert.match($("#map-comment").textContent, /Welcome back/);
  cleanup(); cleanup = page.mount(rootEl); assert.doesNotMatch($("#map-comment").textContent, /Welcome back/, "said once per return"); cleanup();
  console.log("Passed: selection, keyboard focus, hover stabilisation, touch select-then-approach, navigation, cleanup, restored view, return reaction.");
}, 0);
