/* Small shims that let the bundled PDF.js 6.5 run in browsers released before late 2025.
   PDF.js uses Uint8Array hex/base64 helpers, Promise.try and Map/WeakMap getOrInsert, added to browsers from 2025 on.
   Each shim is installed only when the browser lacks the feature. The vendored PDF.js files stay unmodified:
   pdf-worker-compat.mjs loads these shims before the worker, expedition.js before the library. */
const define = (obj, name, fn) => { if (!(name in obj)) Object.defineProperty(obj, name, { value: fn, writable: true, configurable: true }); };

define(Uint8Array.prototype, "toHex", function () {
  let s = "";
  for (let i = 0; i < this.length; i++) s += this[i].toString(16).padStart(2, "0");
  return s;
});
define(Uint8Array, "fromHex", function (hex) {
  if (typeof hex !== "string" || hex.length % 2 || /[^0-9a-f]/i.test(hex)) throw new SyntaxError("Invalid hex string");
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) out[i] = parseInt(hex.substr(i * 2, 2), 16);
  return out;
});
define(Uint8Array.prototype, "toBase64", function () {
  let s = "";
  for (let i = 0; i < this.length; i += 0x8000) s += String.fromCharCode.apply(null, this.subarray(i, i + 0x8000));
  return btoa(s);
});
define(Uint8Array, "fromBase64", function (b64) {
  const s = atob(String(b64).replace(/[-_]/g, (c) => (c === "-" ? "+" : "/")));
  const out = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
  return out;
});
define(Promise, "try", function (fn, ...args) { return new Promise((resolve) => resolve(fn(...args))); });
for (const M of [Map, WeakMap]) {
  define(M.prototype, "getOrInsert", function (key, value) { if (!this.has(key)) this.set(key, value); return this.get(key); });
  define(M.prototype, "getOrInsertComputed", function (key, compute) { if (!this.has(key)) this.set(key, compute(key)); return this.get(key); });
}
