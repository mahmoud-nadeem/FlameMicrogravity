/* Flame in Freefall universe: one persistent WebGL scene behind every page.
   The universe is drawn here; the game interface (DOM) is drawn by the pages.

   - Procedural nebula and two star layers (far sky + near dust for parallax).
   - A central star (the mission hub) and six research worlds rendered as lit sphere
     impostors with 3D procedural surfaces, axial rotation, clouds and atmospheric rims.
   - A camera that drifts, follows the pointer slightly, responds to scroll and travels
     between scenes ("home", "map", "world", "deep") with interruptible tweens.
   - Cinematic mode renders at screen resolution; Retro mode renders the same scene at
     low resolution with posterised colour over the original pixel starfield.
   - No WebGL: a 2D canvas fallback keeps stars and the procedural planet renderer.

   Everything is original code; no textures, images or libraries are loaded. */
(function () {
  "use strict";
  const F = window.FIF;
  const TAU = Math.PI * 2;
  const U = (F.universe = { mode: "off", scene: "deep" });

  // ------------------------------------------------------------------ small vector/matrix kit
  const v3 = {
    add: (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]],
    sub: (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]],
    mul: (a, s) => [a[0] * s, a[1] * s, a[2] * s],
    dot: (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2],
    cross: (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]],
    len: (a) => Math.hypot(a[0], a[1], a[2]),
    norm: (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; },
    lerp: (a, b, t) => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t],
  };
  U.v3 = v3;
  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  const smooth = (t) => t * t * (3 - 2 * t);
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));

  // Camera basis for a look-at camera (right-handed, y up). Returns view rows.
  function basis(eye, target) {
    const f = v3.norm(v3.sub(target, eye));
    let r = v3.cross(f, [0, 1, 0]);
    if (v3.len(r) < 1e-4) r = [1, 0, 0];
    r = v3.norm(r);
    const u = v3.cross(r, f);
    return { r, u, f };
  }

  // ------------------------------------------------------------------ the world layout
  // Worlds orbit the hub star. Orbit radius, inclination, phase and size per track.
  const ORBITS = [
    { a: 7.5, inc: 0.14, phase: 0.55, r: 0.95, speed: 0.020 },
    { a: 10.5, inc: -0.09, phase: 1.75, r: 1.05, speed: 0.016 },
    { a: 13.8, inc: 0.07, phase: 3.0, r: 1.2, speed: 0.013 },
    { a: 17.2, inc: -0.12, phase: 4.15, r: 0.95, speed: 0.011 },
    { a: 21.5, inc: 0.05, phase: 5.05, r: 2.05, speed: 0.008 },
    { a: 25.5, inc: 0.17, phase: 5.95, r: 0.85, speed: 0.007 },
  ];
  const SUN = { id: "sun", kind: "star", pos: [0, 0, 0], r: 2.3, alpha: 1 };
  const bodies = [SUN];
  const byId = new Map([["sun", SUN]]);

  function buildBodies() {
    const tracks = (F.data && F.data.tracks) || [];
    tracks.forEach((t, i) => {
      const o = ORBITS[i % ORBITS.length], w = (F.worlds || [])[i] || {};
      const ch = F.characterForTrack ? F.characterForTrack(t.id) : null;
      const body = { id: "w-" + t.id, kind: "planet", track: t.id, member: ch && ch.id, index: i, orbit: o, theta: o.phase,
        r: o.r, pos: [0, 0, 0], spin: i * 1.3, spinSpeed: 0.05 + 0.012 * (i % 3), tilt: [0.32, -0.18, 0.41, 0.12, 0.05, -0.36][i % 6],
        type: w.type ?? i % 6, seed: (w.seed || i * 17) * 0.137, pal: w.pal || [[0.2, 0.3, 0.5], [0.5, 0.4, 0.3], [0.8, 0.8, 0.8]],
        atm: w.atm || [0.4, 0.6, 1.0], atmK: w.atmK ?? 0.8, alpha: 1, moons: [] };
      bodies.push(body); byId.set(body.id, body);
      t.records.forEach((rid, k) => {
        const m = { id: "m-" + rid, kind: "moon", record: rid, parent: body, k, n: t.records.length, r: 0.16 + 0.03 * ((k + i) % 3),
          pos: [0, 0, 0], spin: k, spinSpeed: 0.03, tilt: 0.2, type: 5, seed: (i * 7 + k) * 0.71 + 3.1,
          pal: [[0.32, 0.31, 0.3], [0.5, 0.48, 0.45], [0.7, 0.68, 0.65]], atm: [0.6, 0.6, 0.65], atmK: 0.0, alpha: 0 };
        body.moons.push(m); bodies.push(m); byId.set(m.id, m);
      });
    });
    placeBodies(0);
  }

  let orbitClock = 0;
  function placeBodies() {
    for (const b of bodies) {
      if (b.kind === "planet") {
        const o = b.orbit, th = b.theta;
        b.pos = [o.a * Math.cos(th), o.a * Math.sin(th) * Math.sin(o.inc), o.a * Math.sin(th) * Math.cos(o.inc)];
      }
    }
    for (const b of bodies) {
      if (b.kind === "moon") {
        const p = b.parent, d = p.r * 1.9 + b.k * 0.62, th = (b.k / b.n) * TAU + orbitClock * 0.06 + p.index;
        b.pos = v3.add(p.pos, [d * Math.cos(th), d * Math.sin(th) * 0.22, d * Math.sin(th)]);
      }
    }
  }
  U.bodies = bodies;
  U.body = (id) => byId.get(id);
  U.worldOf = (track) => byId.get("w-" + track);

  // ------------------------------------------------------------------ camera and scenes
  const view = { yaw: 0.55, pitch: 0.46, dist: 58, ptrX: 0, ptrY: 0, ptrTX: 0, ptrTY: 0, scroll: 0 };
  U.mapView = view;
  let cam = { eye: [0, 18, 52], target: [0, 0, 0] };
  let tween = null; // {from, to: fn, t0, dur, resolve}
  let sceneFn = () => ({ eye: [0, 18, 52], target: [0, 0, 0] });
  U.state = { hover: null, focus: null, orbitsPaused: false, homeK: 0, highlight: null };

  // Camera that looks at a world, with the world pushed to one side of the screen.
  function worldShot(body, distR, side, lift = 0.22, dropY = 0, shift = 0.18) {
    const s = v3.norm(v3.sub(body.pos, SUN.pos));               // from sun to world
    const across = v3.norm(v3.cross([0, 1, 0], s));
    const dir = v3.norm(v3.add(v3.add(v3.mul(s, -0.62), v3.mul(across, 0.78 * (side >= 0 ? 1 : -1))), [0, lift, 0]));
    const eye = v3.add(body.pos, v3.mul(dir, body.r * distR));
    const b = basis(eye, body.pos);
    const target = v3.add(v3.add(body.pos, v3.mul(b.r, -side * body.r * distR * shift)), v3.mul(b.u, dropY * body.r));
    return { eye, target };
  }

  const scenes = {
    deep: () => {
      const yaw = 2.6 + view.scroll * 0.05, pitch = 0.18;
      const d = 74;
      return { eye: [d * Math.cos(pitch) * Math.sin(yaw), d * Math.sin(pitch) + 6, d * Math.cos(pitch) * Math.cos(yaw)], target: [-14, 4, 0] };
    },
    map: () => {
      const p = clamp(view.pitch + view.scroll * 0.18, 0.12, 1.25), d = view.dist * (1 + view.scroll * 0.25);
      const target = U.state.mobileFocus ? U.state.mobileFocus.pos : [0, 0, 0];
      const dist = U.state.mobileFocus ? U.state.mobileFocus.r * 12 : d;
      const eye = v3.add(target, [dist * Math.cos(p) * Math.sin(view.yaw), dist * Math.sin(p), dist * Math.cos(p) * Math.cos(view.yaw)]);
      if (U.state.mobileFocus) return { eye, target };
      const right = basis(eye, target).r, shift = v3.mul(right, dist * (W > 900 ? 0.06 : 0));   // a little room for the dock and cards
      return { eye: v3.add(eye, shift), target: v3.add(target, shift) };
    },
    world: (opts) => {
      const b = byId.get(opts.id) || byId.get("w-T3");
      return worldShot(b, (opts.dist || 6.2) * (1 + view.scroll * 0.35), opts.side ?? 1, 0.22, opts.drop || 0);
    },
    home: () => homeCamera(U.state.homeK),
  };

  // Home: keyframes along the scroll story. 0 hero, 1 statement, 2 guide, 3 worlds title, 4..9 worlds, 10 final.
  function homeKey(k) {
    const w = (i) => bodies.filter((b) => b.kind === "planet")[i];
    const hero = w(2);
    if (!hero) return { eye: [0, 10, 40], target: [0, 0, 0] };
    if (k <= 0) return worldShot(hero, 3.0, 1, 0.1, 0.42, 0.36);
    if (k === 1) return worldShot(hero, 5.8, -1, 0.3, 0.1, 0.24);
    if (k === 2) return worldShot(hero, 9.5, 1, 0.45, 0.4);
    if (k === 3) return { eye: [-10, 30, 46], target: [2, -2, 4] };
    if (k >= 4 && k <= 9) { const p = w(k - 4); return p ? worldShot(p, p.r > 1.6 ? 4.8 : 5.4, (k % 2 ? -1 : 1), 0.22, 0, 0.25) : homeKey(3); }
    return { eye: [12, 26, 54], target: [0, -2, 0] };
  }
  function homeCamera(k) {
    const a = Math.floor(k), f = smooth(clamp(k - a, 0, 1));
    const A = homeKey(a), B = homeKey(a + 1);
    return { eye: v3.lerp(A.eye, B.eye, f), target: v3.lerp(A.target, B.target, f) };
  }

  /** Switch scene. Returns a promise resolved when the camera has (almost) arrived. */
  U.setScene = function (name, opts = {}) {
    U.scene = name; U.sceneOpts = opts;
    const fn = scenes[name] || scenes.deep;
    sceneFn = () => fn(opts);
    document.body.dataset.scene = name;
    return travel(opts.duration ?? (name === "home" ? 1300 : 1100));
  };
  function travel(dur) {
    if (tween && tween.resolve) tween.resolve();
    const reduced = reduceMotion();
    return new Promise((resolve) => {
      if (reduced || dur <= 0 || U.mode === "off") { tween = null; cam = sceneFn(); requestFrame(); resolve(); return; }
      tween = { from: { eye: cam.eye.slice(), target: cam.target.slice() }, t0: performance.now(), dur, resolve };
      requestFrame();
    });
  }
  /** Short approach into a world (used before navigating to its profile). */
  U.approach = function (bodyId) {
    const b = byId.get(bodyId);
    if (!b) return Promise.resolve();
    U.state.focus = bodyId;
    U.scene = "world"; U.sceneOpts = { id: bodyId, side: 1 };
    sceneFn = () => scenes.world(U.sceneOpts);
    return travel(950);
  };

  // ------------------------------------------------------------------ settings helpers
  const media = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false, addEventListener() {} };
  function reduceMotion() { return !!(F.settings && F.settings.reduceMotion) || media.matches; }
  U.reduceMotion = reduceMotion;
  U.isRetro = () => !(document.body.classList.contains("cinematic") || document.documentElement.classList.contains("cinematic-boot"));

  // ------------------------------------------------------------------ canvases
  let cv = null, gl = null, ui = null, uiCtx = null;
  let W = 0, H = 0, dpr = 1, quality = 1, scale = 1;
  const listeners = new Set();
  U.onFrame = (fn) => { listeners.add(fn); requestFrame(); return () => listeners.delete(fn); };
  U._listeners = () => listeners.size;   // diagnostics for tests

  // ------------------------------------------------------------------ WebGL programs
  const GLSL_NOISE = `
    float h31(vec3 p){ p = fract(p * 0.3183099 + vec3(0.71, 0.113, 0.419)); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
    float vnoise(vec3 x){ vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
      return mix(mix(mix(h31(i), h31(i + vec3(1,0,0)), f.x), mix(h31(i + vec3(0,1,0)), h31(i + vec3(1,1,0)), f.x), f.y),
                 mix(mix(h31(i + vec3(0,0,1)), h31(i + vec3(1,0,1)), f.x), mix(h31(i + vec3(0,1,1)), h31(i + vec3(1,1,1)), f.x), f.y), f.z); }
    float fbm(vec3 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 6; i++){ s += a * vnoise(p); p = p * 2.03 + vec3(1.7, 9.2, 3.1); a *= 0.5; } return s; }
    float fbm4(vec3 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 4; i++){ s += a * vnoise(p); p = p * 2.07 + vec3(4.1, 1.3, 7.7); a *= 0.5; } return s; }
  `;

  const VS_QUAD = `
    attribute vec2 aPos; varying vec2 vQ;
    uniform vec2 uCenter; uniform vec2 uHalf;   // clip-space centre and half size
    void main(){ vQ = aPos; gl_Position = vec4(uCenter + aPos * uHalf, 0.0, 1.0); }`;

  const FS_PLANET = `
    precision highp float;
    varying vec2 vQ;
    uniform float uQ, uPx, uType, uSeed, uTime, uAlpha, uRetro, uAtmK;
    uniform mat3 uM; uniform vec3 uL, uA, uB, uC, uAtm;
    ${GLSL_NOISE}
    float crater(vec3 p){                       // cellular craters on the sphere
      vec3 i = floor(p), f = fract(p); float h = 0.0;
      for (int x = -1; x <= 1; x++) for (int y = -1; y <= 1; y++) for (int z = -1; z <= 1; z++) {
        vec3 g = vec3(float(x), float(y), float(z));
        vec3 o = vec3(h31(i + g), h31(i + g + 13.1), h31(i + g + 27.7));
        float r = 0.18 + 0.32 * h31(i + g + 5.3);
        float d = length(g + o - f) / r;
        if (d < 1.25) h += d < 1.0 ? -0.55 * (1.0 - d * d) : 0.35 * (1.25 - d) * 4.0 * (d - 1.0);
      }
      return h;
    }
    void main(){
      vec2 p = vQ * uQ; float d2 = dot(p, p); float d = sqrt(d2);
      if (d > 1.0) {                            // atmospheric halo around the limb
        if (uAtmK <= 0.0) discard;
        float t = (d - 1.0) / (uQ - 1.0);
        float lit = smoothstep(-0.55, 0.65, dot(vec3(p / d, 0.0), uL));
        float g = exp(-t * 7.0) * uAtmK * (0.15 + 0.85 * lit) * 0.75;
        gl_FragColor = vec4(uAtm * g * uAlpha, 0.0);              // additive glow
        return;
      }
      vec3 n = vec3(p, sqrt(1.0 - d2));
      vec3 sp = normalize(uM * n);
      vec3 q = sp * 2.2 + uSeed;
      vec3 alb; vec3 emit = vec3(0.0); float spec = 0.0; float cloud = 0.0; float ndl = dot(n, uL);
      int type = int(uType + 0.5);
      if (type == 0) {                          // ocean world with continents and weather
        float h = fbm(q);
        float land = smoothstep(0.515, 0.545, h);
        vec3 sea = mix(uA * 0.45, uA, smoothstep(0.25, 0.51, h));
        vec3 ground = mix(uB, uC, smoothstep(0.56, 0.74, h + 0.08 * fbm4(q * 6.0)));
        alb = mix(sea, ground, land);
        float ice = smoothstep(0.78, 0.86, abs(sp.y) + 0.08 * fbm4(q * 3.0));
        alb = mix(alb, vec3(0.86, 0.9, 0.95), ice);
        spec = (1.0 - land) * (1.0 - ice);
        cloud = smoothstep(0.52, 0.72, fbm(sp * 3.1 + vec3(uTime * 0.004, 0.0, uTime * 0.002) + uSeed * 1.7));
      } else if (type == 1) {                   // dusty desert world with canyons and a cap
        float h = fbm(q * 1.1);
        float canyon = 1.0 - smoothstep(0.0, 0.035, abs(fbm4(sp * 1.6 + uSeed * 2.0) - 0.5));
        alb = mix(uA, uB, smoothstep(0.35, 0.7, h));
        alb = mix(alb, uC, smoothstep(0.62, 0.78, fbm4(q * 2.5)) * 0.5);
        alb *= 1.0 - canyon * 0.45;
        alb = mix(alb, vec3(0.9, 0.88, 0.85), smoothstep(0.9, 0.95, sp.y + 0.05 * fbm4(q * 4.0)));
        cloud = smoothstep(0.66, 0.85, fbm4(sp * 2.0 + vec3(uTime * 0.003))) * 0.35;
      } else if (type == 2) {                   // banded gas giant with a long-lived storm
        float lat = sp.y;
        float turb = fbm(vec3(sp.x * 2.4, lat * 9.0, sp.z * 2.4) + uSeed + vec3(uTime * 0.002, 0.0, 0.0));
        float bands = sin(lat * 15.0 + turb * 3.4);
        alb = mix(uA, uB, bands * 0.5 + 0.5);
        alb = mix(alb, uC, smoothstep(0.55, 0.9, fbm4(vec3(sp.x * 4.0, lat * 22.0, sp.z * 4.0) + uSeed)) * 0.55);
        vec3 storm = normalize(vec3(0.75, -0.32, 0.58));
        float sd = length((sp - storm) * vec3(1.0, 2.3, 1.0));
        alb = mix(alb, uC * vec3(1.05, 0.62, 0.45), smoothstep(0.24, 0.08, sd) * 0.85);
        alb *= 0.92 + 0.12 * fbm4(sp * 9.0);
      } else if (type == 3) {                   // ice moon crossed by stained fractures
        float h = fbm(q * 1.3);
        alb = mix(uA, uB, smoothstep(0.35, 0.75, h));
        float c1 = 1.0 - smoothstep(0.0, 0.016, abs(fbm4(sp * 2.6 + uSeed) - 0.5));
        float c2 = 1.0 - smoothstep(0.0, 0.012, abs(fbm4(sp * 4.3 + uSeed * 3.0) - 0.5));
        alb = mix(alb, uC, clamp(c1 + c2 * 0.7, 0.0, 1.0) * 0.8);
        spec = 0.25;
      } else if (type == 4) {                   // volcanic world: dark crust, glowing fissures
        float h = fbm(q * 1.2);
        alb = mix(uA, uB, smoothstep(0.3, 0.75, h)) * (0.8 + 0.3 * crater(sp * 3.0 + uSeed));
        float f1 = 1.0 - smoothstep(0.0, 0.03, abs(fbm4(sp * 2.2 + uSeed) - 0.5));
        float f2 = 1.0 - smoothstep(0.0, 0.02, abs(fbm4(sp * 5.0 + uSeed * 2.0) - 0.5));
        float lava = clamp(f1 + f2 * 0.6, 0.0, 1.0) * (0.6 + 0.4 * vnoise(sp * 30.0 + uTime * 0.05));
        alb = mix(alb, uC * 0.6, lava * 0.6);
        emit = uC * lava * 1.2;
      } else {                                  // cratered moon
        float h = fbm(q * 1.4);
        float cr = crater(sp * 4.0 + uSeed) + 0.5 * crater(sp * 9.0 + uSeed * 2.0);
        alb = mix(uA, uB, smoothstep(0.3, 0.7, h)) * (1.0 + cr * 0.35);
        alb = mix(alb, uC, smoothstep(0.62, 0.75, fbm4(q * 3.0)) * 0.4);
      }
      float diff = clamp(ndl * 1.04 + 0.03, 0.0, 1.0);
      vec3 col = alb * diff;
      if (cloud > 0.0) {                        // clouds lit separately, softly shadowing the ground
        col = mix(col, vec3(0.97) * clamp(ndl * 1.1 + 0.06, 0.0, 1.0), cloud * 0.92);
        spec *= 1.0 - cloud;
      }
      vec3 h = normalize(uL + vec3(0.0, 0.0, 1.0));
      col += vec3(1.0, 0.95, 0.85) * pow(max(dot(n, h), 0.0), 55.0) * spec * 0.55 * step(0.0, ndl);
      float fres = pow(1.0 - n.z, 2.6);
      float sunSide = smoothstep(-0.25, 0.55, ndl);
      col += uAtm * fres * sunSide * uAtmK * 0.85;
      col = mix(col, uAtm * diff, uAtmK * 0.12 * (1.0 - n.z));
      col += emit * (1.0 - 0.75 * smoothstep(-0.15, 0.35, ndl));
      col += alb * 0.012;
      col = 1.0 - exp(-col * 1.35);
      if (uRetro > 0.5) col = floor(col * 6.0 + 0.5) / 6.0;
      float a = clamp((1.0 - d) * uPx * 1.2, 0.0, 1.0);
      gl_FragColor = vec4(col * a * uAlpha, a * uAlpha);
    }`;

  const FS_STAR = `
    precision highp float;
    varying vec2 vQ; uniform float uQ, uPx, uTime, uAlpha, uRetro;
    ${GLSL_NOISE}
    void main(){
      vec2 p = vQ * uQ; float d = length(p);
      vec3 col; float a;
      if (d < 1.0) {
        float mu = sqrt(1.0 - d * d);
        float gran = fbm4(vec3(p * 9.0, uTime * 0.04));
        col = vec3(1.0, 0.86, 0.62) * (0.55 + 0.45 * mu) * (0.88 + 0.24 * gran) * 1.15;
        a = clamp((1.0 - d) * uPx * 1.2, 0.0, 1.0);
      } else {
        float t = d - 1.0;
        float corona = exp(-t * 2.6) * 0.55 + exp(-t * 0.7) * 0.09;
        corona *= 0.9 + 0.1 * vnoise(vec3(normalize(p) * 6.0, uTime * 0.05));
        corona *= 1.0 - smoothstep((uQ - 1.0) * 0.5, uQ - 1.0, t);   // fade out before the quad edge
        col = vec3(1.0, 0.62, 0.32) * corona; a = 0.0;
      }
      if (uRetro > 0.5) col = floor(col * 6.0 + 0.5) / 6.0;
      gl_FragColor = vec4(col * uAlpha, a * uAlpha);
    }`;

  const VS_FULL = `attribute vec2 aPos; varying vec2 vQ; void main(){ vQ = aPos; gl_Position = vec4(aPos, 0.0, 1.0); }`;
  const FS_NEBULA = `
    precision highp float;
    varying vec2 vQ; uniform mat3 uInv; uniform float uTan, uAspect;
    ${GLSL_NOISE}
    void main(){
      vec3 dir = normalize(uInv * vec3(vQ.x * uTan * uAspect, vQ.y * uTan, -1.0));
      vec3 q = dir * 1.7;
      float w = fbm(q * 1.15 + vec3(2.0, 7.0, 1.0));
      float n1 = fbm(q * 2.1 + w * 1.6);
      float region = smoothstep(0.18, 0.7, fbm4(q * 0.55 + vec3(5.0)));
      float mask = smoothstep(0.36, 0.82, n1) * region;
      vec3 neb = mix(vec3(0.035, 0.08, 0.2), vec3(0.24, 0.07, 0.24), smoothstep(0.38, 0.85, w));
      neb = mix(neb, vec3(0.58, 0.24, 0.08), smoothstep(0.7, 0.96, n1) * 0.55);
      vec3 col = vec3(0.004, 0.006, 0.016) + neb * mask * 1.05;
      float dust = smoothstep(0.52, 0.74, fbm4(q * 3.4 + vec3(9.0)));
      col *= 1.0 - dust * 0.55 * mask;
      float band = exp(-pow(dot(dir, normalize(vec3(0.25, 1.0, 0.4))) * 3.0, 2.0));
      col += vec3(0.045, 0.05, 0.065) * band * fbm4(q * 5.0);
      gl_FragColor = vec4(col, 1.0);
    }`;
  const FS_COPY = `precision mediump float; varying vec2 vQ; uniform sampler2D uTex;
    void main(){ gl_FragColor = texture2D(uTex, vQ * 0.5 + 0.5); }`;

  const VS_STARS = `
    attribute vec4 aStar;   // xyz = direction or position, w = size
    attribute vec3 aCol;
    uniform mat4 uVP; uniform float uFar, uDpr, uTime;
    varying vec3 vCol; varying float vTw;
    void main(){
      vec4 p = uVP * vec4(aStar.xyz, uFar > 0.5 ? 0.0 : 1.0);   // w = 0: direction at infinity
      gl_Position = vec4(p.xy, 0.0, p.w);                          // no depth test; keep inside the clip volume
      float tw = 0.82 + 0.18 * sin(uTime * (0.6 + fract(aStar.w * 13.7)) + aStar.w * 40.0);
      vTw = tw; vCol = aCol;
      gl_PointSize = aStar.w * uDpr * (uFar > 0.5 ? 1.0 : clamp(28.0 / max(p.w, 1.0), 0.6, 2.4));
    }`;
  const FS_STARS = `precision mediump float; varying vec3 vCol; varying float vTw;
    void main(){ vec2 c = gl_PointCoord - 0.5; float d = dot(c, c); float a = smoothstep(0.25, 0.0, d);
      gl_FragColor = vec4(vCol * a * vTw, a * vTw); }`;

  function compile(type, src) {
    const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  function program(vs, fs) {
    const p = gl.createProgram();
    gl.attachShader(p, compile(gl.VERTEX_SHADER, vs)); gl.attachShader(p, compile(gl.FRAGMENT_SHADER, fs));
    gl.bindAttribLocation(p, 0, "aPos"); gl.bindAttribLocation(p, 0, "aStar"); gl.bindAttribLocation(p, 1, "aCol");
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    const u = {}; const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (let i = 0; i < n; i++) { const info = gl.getActiveUniform(p, i); u[info.name.replace(/\[0\]$/, "")] = gl.getUniformLocation(p, info.name); }
    return { p, u };
  }

  let P = {}, quadBuf = null, starBufFar = null, starBufNear = null, starCount = { far: 0, near: 0 };
  let neb = { fb: null, tex: null, w: 0, h: 0, key: "" };

  function initGL() {
    cv = document.createElement("canvas");
    cv.id = "universe"; cv.setAttribute("aria-hidden", "true");
    document.body.prepend(cv);
    const attrs = { alpha: true, antialias: false, premultipliedAlpha: true, preserveDrawingBuffer: false, powerPreference: "low-power" };
    gl = cv.getContext("webgl", attrs) || cv.getContext("experimental-webgl", attrs);
    if (!gl) throw new Error("no webgl");
    P.planet = program(VS_QUAD, FS_PLANET);
    P.star = program(VS_QUAD, FS_STAR);
    P.nebula = program(VS_FULL, FS_NEBULA);
    P.copy = program(VS_FULL, FS_COPY);
    P.stars = program(VS_STARS, FS_STARS);
    quadBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, quadBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    buildStars();
    cv.addEventListener("webglcontextlost", (e) => { e.preventDefault(); U.mode = "lost"; });
    cv.addEventListener("webglcontextrestored", () => { try { P = {}; initPrograms(); } catch (err) { fallback2D(); } });
  }
  function initPrograms() {
    P.planet = program(VS_QUAD, FS_PLANET); P.star = program(VS_QUAD, FS_STAR); P.nebula = program(VS_FULL, FS_NEBULA);
    P.copy = program(VS_FULL, FS_COPY); P.stars = program(VS_STARS, FS_STARS);
    quadBuf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, quadBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    buildStars(); neb.key = ""; U.mode = "webgl"; requestFrame();
  }

  // Deterministic random numbers so the sky is the same on every visit.
  function rng(seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
  function starColor(t) { // t 0 cool red .. 1 hot blue
    return t < 0.15 ? [1, 0.72, 0.55] : t < 0.4 ? [1, 0.88, 0.75] : t < 0.8 ? [0.95, 0.95, 1] : [0.72, 0.82, 1];
  }
  function buildStars() {
    const r = rng(7), far = [], near = [];
    for (let i = 0; i < 2600; i++) {
      const z = r() * 2 - 1, a = r() * TAU, s = Math.sqrt(1 - z * z);
      const big = r(); const size = big > 0.995 ? 3.2 : big > 0.96 ? 2.1 : 1.0 + r() * 0.7;
      const c = starColor(r()), b = 0.35 + r() * 0.65 * (size > 2 ? 1 : 0.8);
      far.push(s * Math.cos(a), z, s * Math.sin(a), size, c[0] * b, c[1] * b, c[2] * b);
    }
    for (let i = 0; i < 520; i++) {
      const p = [(r() - 0.5) * 160, (r() - 0.5) * 70, (r() - 0.5) * 160], size = 1 + r() * 1.6, b = 0.25 + r() * 0.5;
      near.push(p[0], p[1], p[2], size, 0.8 * b, 0.86 * b, b);
    }
    const mk = (arr) => { const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(arr), gl.STATIC_DRAW); return buf; };
    starBufFar = mk(far); starBufNear = mk(near); starCount = { far: far.length / 7, near: near.length / 7 };
  }

  // ------------------------------------------------------------------ frame state
  let raf = 0, last = 0, time = 0, frameMs = [], drift = 0, running = false;
  function requestFrame() { if (!raf && U.mode !== "off") raf = requestAnimationFrame(frame); }
  U.requestFrame = requestFrame;

  function resize() {
    W = window.innerWidth; H = window.innerHeight;
    dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    const retro = U.isRetro();
    scale = retro ? 0.34 : dpr * quality;
    if (cv) {
      cv.width = Math.max(1, Math.round(W * scale)); cv.height = Math.max(1, Math.round(H * scale));
      cv.classList.toggle("retro", retro);
    }
    if (ui) { const s = Math.min(window.devicePixelRatio || 1, 2); ui.width = Math.round(W * s); ui.height = Math.round(H * s); uiCtx.setTransform(s, 0, 0, s, 0, 0); }
    neb.key = "";
    requestFrame();
  }

  const FOV = 40 * Math.PI / 180;
  let viewB = null, eyeNow = [0, 0, 0];
  /** Project a world point to CSS pixels. depth = distance along the view axis. */
  function project(p) {
    if (!viewB) return { x: -1e4, y: -1e4, depth: -1, visible: false, k: 0 };
    const d = v3.sub(p, eyeNow);
    const z = v3.dot(d, viewB.f);
    const k = (H / 2) / Math.tan(FOV / 2) / Math.max(z, 1e-3);
    const x = W / 2 + v3.dot(d, viewB.r) * k, y = H / 2 - v3.dot(d, viewB.u) * k;
    return { x, y, depth: z, k, visible: z > 0.3 && x > -W * 0.5 && x < W * 1.5 && y > -H * 0.5 && y < H * 1.5 };
  }
  U.project = project;
  U.projectBody = (id) => { const b = byId.get(id); if (!b) return null; const p = project(b.pos); p.r = b.r * p.k; p.body = b; return p; };

  function updateCamera(now, dt) {
    const reduced = reduceMotion();
    if (!reduced) { drift += dt; view.ptrX += (view.ptrTX - view.ptrX) * Math.min(1, dt * 2.2); view.ptrY += (view.ptrTY - view.ptrY) * Math.min(1, dt * 2.2); }
    else { view.ptrX = view.ptrY = 0; }
    let want = sceneFn();
    if (tween) {
      const k = clamp((now - tween.t0) / tween.dur, 0, 1), e = ease(k);
      want = { eye: v3.lerp(tween.from.eye, want.eye, e), target: v3.lerp(tween.from.target, want.target, e) };
      if (k >= 0.86 && tween.resolve) { tween.resolve(); tween.resolve = null; }
      if (k >= 1) tween = null;
    }
    cam = want;
    // calm drift + pointer parallax, proportional to the distance to the target
    const dist = v3.len(v3.sub(cam.eye, cam.target));
    const b0 = basis(cam.eye, cam.target);
    const sway = reduced ? [0, 0] : [Math.sin(drift * 0.11) * 0.012 + view.ptrX * 0.035, Math.sin(drift * 0.083 + 1.3) * 0.008 - view.ptrY * 0.022];
    eyeNow = v3.add(cam.eye, v3.add(v3.mul(b0.r, sway[0] * dist), v3.mul(b0.u, sway[1] * dist)));
    viewB = basis(eyeNow, cam.target);
  }

  function updateBodies(dt) {
    const reduced = reduceMotion();
    const orbiting = U.scene === "map" && !reduced && !U.state.orbitsPaused && !U.state.hover && !U.state.focusLock;
    if (orbiting) { for (const b of bodies) if (b.kind === "planet") b.theta += dt * b.orbit.speed; }
    if (!reduced) { orbitClock += dt; for (const b of bodies) b.spin += dt * b.spinSpeed; }
    placeBodies();
    // visibility of experiment moons: only around the focused world, faint on the map
    for (const b of bodies) if (b.kind === "moon") {
      const focus = (U.scene === "world" && U.sceneOpts && U.sceneOpts.id === b.parent.id) || U.state.hover === b.parent.id;
      const want = focus ? 1 : U.scene === "map" ? 0.55 : 0;
      b.alpha += (want - b.alpha) * Math.min(1, dt * 3);
    }
  }

  // ------------------------------------------------------------------ drawing (WebGL)
  function mat4VP() {
    const f = 1 / Math.tan(FOV / 2), aspect = W / H, n = 0.1, fa = 800;
    const { r, u, f: fw } = viewB, e = eyeNow;
    const V = [r[0], u[0], -fw[0], 0, r[1], u[1], -fw[1], 0, r[2], u[2], -fw[2], 0, -v3.dot(r, e), -v3.dot(u, e), v3.dot(fw, e), 1];
    const Pm = [f / aspect, 0, 0, 0, 0, f, 0, 0, 0, 0, (fa + n) / (n - fa), -1, 0, 0, (2 * fa * n) / (n - fa), 0];
    const out = new Float32Array(16);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { let s = 0; for (let k = 0; k < 4; k++) s += Pm[k * 4 + j] * V[i * 4 + k]; out[i * 4 + j] = s; }
    return { VP: out };
  }

  function bindQuad(prog) { gl.useProgram(prog.p); gl.bindBuffer(gl.ARRAY_BUFFER, quadBuf); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0); gl.disableVertexAttribArray(1); }

  function drawNebula(retro) {
    if (retro) return;
    const w = Math.max(64, Math.round(cv.width * 0.34)), h = Math.max(48, Math.round(cv.height * 0.34));
    if (!neb.tex || neb.w !== w || neb.h !== h) {
      if (neb.tex) { gl.deleteTexture(neb.tex); gl.deleteFramebuffer(neb.fb); }
      neb.tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, neb.tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      neb.fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, neb.fb);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, neb.tex, 0);
      neb.w = w; neb.h = h; neb.key = "";
    }
    // Re-render the nebula only when the view direction changed noticeably.
    const key = viewB.f.map((x) => x.toFixed(3)).join(",") + "|" + viewB.u[1].toFixed(3) + "|" + W + "x" + H;
    if (key !== neb.key) {
      gl.bindFramebuffer(gl.FRAMEBUFFER, neb.fb); gl.viewport(0, 0, w, h); gl.disable(gl.BLEND);
      bindQuad(P.nebula);
      const { r, u, f } = viewB;
      gl.uniformMatrix3fv(P.nebula.u.uInv, false, new Float32Array([r[0], r[1], r[2], u[0], u[1], u[2], -f[0], -f[1], -f[2]]));
      gl.uniform1f(P.nebula.u.uTan, Math.tan(FOV / 2)); gl.uniform1f(P.nebula.u.uAspect, W / H);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null); neb.key = key;
    }
    gl.viewport(0, 0, cv.width, cv.height);
    bindQuad(P.copy); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, neb.tex); gl.uniform1i(P.copy.u.uTex, 0);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }

  function drawStars(m, retro) {
    if (retro) return;                       // Retro mode keeps the original pixel starfield behind
    gl.useProgram(P.stars.p);
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
    const draw = (buf, count, far) => {
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 4, gl.FLOAT, false, 28, 0);
      gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 28, 16);
      gl.uniformMatrix4fv(P.stars.u.uVP, false, m.VP);
      gl.uniform1f(P.stars.u.uFar, far ? 1 : 0); gl.uniform1f(P.stars.u.uDpr, retro ? 1 : scale); gl.uniform1f(P.stars.u.uTime, reduceMotion() ? 0 : time);
      gl.drawArrays(gl.POINTS, 0, count);
    };
    draw(starBufFar, starCount.far, true);
    draw(starBufNear, starCount.near, false);
    gl.disableVertexAttribArray(1);
  }

  function rotationFor(b) {
    // body rotation R = Rz(tilt) * Ry(spin); uM maps view-space normals into body space: R^T * V^T
    const cs = Math.cos(b.spin), ss = Math.sin(b.spin), ct = Math.cos(b.tilt), st = Math.sin(b.tilt);
    // R columns
    const Ry = [[cs, 0, -ss], [0, 1, 0], [ss, 0, cs]];
    const Rz = [[ct, st, 0], [-st, ct, 0], [0, 0, 1]];
    const R = [0, 1, 2].map((i) => [0, 1, 2].map((j) => Rz[0][j] * Ry[i][0] + Rz[1][j] * Ry[i][1] + Rz[2][j] * Ry[i][2])); // R[i] = column i
    // view basis rows: r, u, -f (camera space = rows of V)
    const Vt = [viewB.r, viewB.u, v3.mul(viewB.f, -1)];
    // world normal = sum_k n_k * Vt[k]; body normal component i = dot(world, R column i)
    const M = new Float32Array(9);
    for (let i = 0; i < 3; i++) for (let k = 0; k < 3; k++) M[k * 3 + i] = v3.dot(Vt[k], R[i]);
    return M;
  }

  function drawBodies(retro) {
    gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
    const list = [];
    for (const b of bodies) {
      if (b.alpha < 0.02) continue;
      const pr = project(b.pos);
      if (pr.depth < 0.3) continue;
      const rpx = b.r * pr.k, ext = b.kind === "star" ? 3.6 : b.atmK > 0 ? 1.32 : 1.04;
      if (rpx < 0.4 || pr.x + rpx * ext < 0 || pr.x - rpx * ext > W || pr.y + rpx * ext < 0 || pr.y - rpx * ext > H) continue;
      list.push({ b, pr, rpx, ext });
    }
    list.sort((a, c) => c.pr.depth - a.pr.depth);
    for (const { b, pr, rpx, ext } of list) {
      const prog = b.kind === "star" ? P.star : P.planet;
      bindQuad(prog);
      const cx = (pr.x / W) * 2 - 1, cy = 1 - (pr.y / H) * 2;
      gl.uniform2f(prog.u.uCenter, cx, cy);
      gl.uniform2f(prog.u.uHalf, (rpx * ext) / W * 2, (rpx * ext) / H * 2);
      gl.uniform1f(prog.u.uQ, ext);
      gl.uniform1f(prog.u.uPx, Math.max(1, rpx * (retro ? 0.34 : scale)));
      gl.uniform1f(prog.u.uTime, time);
      gl.uniform1f(prog.u.uAlpha, b.alpha * (U.state.dimOthers && U.state.dimOthers !== b.id && b.kind === "planet" ? 0.55 : 1));
      gl.uniform1f(prog.u.uRetro, retro ? 1 : 0);
      if (b.kind === "star") { gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4); continue; }
      const L = v3.norm(v3.sub(SUN.pos, b.pos));
      gl.uniform3f(prog.u.uL, v3.dot(L, viewB.r), v3.dot(L, viewB.u), -v3.dot(L, viewB.f));
      gl.uniformMatrix3fv(prog.u.uM, false, rotationFor(b));
      gl.uniform1f(prog.u.uType, b.type); gl.uniform1f(prog.u.uSeed, b.seed);
      gl.uniform3fv(prog.u.uA, b.pal[0]); gl.uniform3fv(prog.u.uB, b.pal[1]); gl.uniform3fv(prog.u.uC, b.pal[2]);
      gl.uniform3fv(prog.u.uAtm, b.atm); gl.uniform1f(prog.u.uAtmK, b.atmK);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    }
  }

  function renderGL() {
    const retro = U.isRetro();
    const wantScale = retro ? 0.34 : dpr * quality;
    if (Math.abs(wantScale - scale) > 0.01 || cv.width !== Math.round(W * wantScale)) resize();
    gl.viewport(0, 0, cv.width, cv.height);
    gl.clearColor(0, 0, 0, retro ? 0 : 1); gl.clear(gl.COLOR_BUFFER_BIT);
    const m = mat4VP();
    gl.disable(gl.BLEND);
    drawNebula(retro);
    drawStars(m, retro);
    drawBodies(retro);
  }

  // ------------------------------------------------------------------ 2D fallback
  let ctx2 = null, fallbackPlanets = new Map(), fallbackStars = [];
  function fallback2D() {
    U.mode = "2d";
    if (cv) cv.remove();
    cv = document.createElement("canvas"); cv.id = "universe"; cv.className = "fallback"; cv.setAttribute("aria-hidden", "true");
    document.body.prepend(cv);
    ctx2 = cv.getContext("2d");
    const r = rng(11); fallbackStars = Array.from({ length: 420 }, () => ({ x: r(), y: r(), z: 0.2 + r() * 0.8, b: 0.3 + r() * 0.7 }));
    resize();
  }
  function render2D() {
    if (!ctx2) return;
    const s = cv.width / W, g = ctx2; g.setTransform(s, 0, 0, s, 0, 0);
    const retro = U.isRetro();
    g.clearRect(0, 0, W, H);
    if (!retro) {
      g.fillStyle = "#02040b"; g.fillRect(0, 0, W, H);
      [[0.3, 0.6, 0.55, "rgba(30,50,110,.35)"], [0.75, 0.3, 0.45, "rgba(70,25,80,.28)"], [0.55, 0.8, 0.35, "rgba(120,50,20,.18)"]].forEach(([x, y, rr, c]) => {
        const gr = g.createRadialGradient(W * x, H * y, 0, W * x, H * y, W * rr); gr.addColorStop(0, c); gr.addColorStop(1, "transparent"); g.fillStyle = gr; g.fillRect(0, 0, W, H); });
      for (const st of fallbackStars) {
        const x = ((st.x - view.ptrX * 0.01 * st.z) % 1 + 1) % 1 * W, y = ((st.y + view.ptrY * 0.01 * st.z) % 1 + 1) % 1 * H;
        g.globalAlpha = st.b * 0.7; g.fillStyle = "#dfe8ff"; g.fillRect(x, y, st.z > 0.8 ? 1.6 : 1, st.z > 0.8 ? 1.6 : 1);
      }
      g.globalAlpha = 1;
    }
    const list = bodies.filter((b) => b.alpha > 0.05 && b.kind !== "moon").map((b) => ({ b, pr: project(b.pos) })).filter((o) => o.pr.depth > 0.3).sort((a, c) => c.pr.depth - a.pr.depth);
    for (const { b, pr } of list) {
      const rpx = b.r * pr.k;
      if (rpx < 1) continue;
      if (b.kind === "star") {
        const gr = g.createRadialGradient(pr.x, pr.y, 0, pr.x, pr.y, rpx * 3.4);
        gr.addColorStop(0, "#fff3d6"); gr.addColorStop(0.28, "#ffcf8a"); gr.addColorStop(0.32, "rgba(255,150,70,.35)"); gr.addColorStop(1, "transparent");
        g.fillStyle = gr; g.beginPath(); g.arc(pr.x, pr.y, rpx * 3.4, 0, TAU); g.fill(); continue;
      }
      let entry = fallbackPlanets.get(b.id);
      if (!entry && F.createPlanet) { const c = document.createElement("canvas"); entry = { c, p: F.createPlanet(c, b.index, { size: 160 }), at: -1 }; fallbackPlanets.set(b.id, entry); }
      if (!entry) continue;
      if (Math.abs(entry.at - b.spin) > 0.02) { entry.p.draw(b.spin); entry.at = b.spin; }
      const size = rpx / 0.405 * 2;
      g.globalAlpha = b.alpha; g.drawImage(entry.c, pr.x - size / 2, pr.y - size / 2, size, size); g.globalAlpha = 1;
    }
  }

  // ------------------------------------------------------------------ main loop
  function frame(now) {
    raf = 0;
    if (U.mode === "off" || U.mode === "lost") return;
    const dt = Math.min(0.1, last ? (now - last) / 1000 : 0.016); last = now;
    const reduced = reduceMotion();
    if (!reduced) time += dt;
    updateBodies(dt);
    updateCamera(now, dt);
    const t0 = performance.now();
    try { if (U.mode === "webgl") renderGL(); else render2D(); } catch (e) { console.warn("universe render failed", e); fallback2D(); }
    if (ui) {
      uiCtx.clearRect(0, 0, W, H);
      listeners.forEach((fn) => { try { fn(uiCtx, { W, H, dt, now, reduced }); } catch (e) { console.warn(e); } });
    } else listeners.forEach((fn) => { try { fn(null, { W, H, dt, now, reduced }); } catch (e) { console.warn(e); } });
    adaptQuality(performance.now() - t0, now);
    // Keep running while animated; with reduced motion only while a tween is pending.
    const animate = !document.hidden && (!reduced || tween);
    if (animate) requestFrame();
  }

  // Lower the render resolution when frames are slow (integrated GPUs, software GL).
  function adaptQuality(ms, now) {
    if (U.mode !== "webgl" || U.isRetro()) return;
    frameMs.push(ms); if (frameMs.length < 40) return;
    const avg = frameMs.reduce((a, b) => a + b, 0) / frameMs.length; frameMs = [];
    const before = quality;
    if (avg > 22 && quality > 0.5) quality = Math.max(0.5, quality - 0.15);
    else if (avg < 9 && quality < 1) quality = Math.min(1, quality + 0.1);
    if (before !== quality) resize();
  }
  U.quality = () => quality;

  // ------------------------------------------------------------------ input
  function onPointer(e) {
    if (e.pointerType === "touch") return;
    view.ptrTX = e.clientX / Math.max(1, W) - 0.5; view.ptrTY = e.clientY / Math.max(1, H) - 0.5;
    if (reduceMotion()) return;
    requestFrame();
  }
  function onScroll() {
    const max = Math.max(1, document.documentElement.scrollHeight - window.innerHeight);
    view.scroll = clamp(window.scrollY / max, 0, 1);
    if (U.scene !== "home") requestFrame();
  }
  U.setHomeProgress = (k) => { U.state.homeK = k; requestFrame(); };

  // ------------------------------------------------------------------ boot
  function boot() {
    buildBodies();
    ui = document.createElement("canvas"); ui.id = "universe-ui"; ui.setAttribute("aria-hidden", "true");
    uiCtx = ui.getContext("2d");
    if (!uiCtx) ui = null;
    try { initGL(); U.mode = "webgl"; } catch (e) { console.info("WebGL unavailable, using 2D universe", e && e.message); fallback2D(); }
    if (ui) cv.after(ui);
    resize();
    U.setScene("deep", { duration: 0 });
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onPointer, { passive: true });
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("visibilitychange", () => { last = 0; requestFrame(); });
    document.addEventListener("fif:settings", () => { last = 0; requestFrame(); });
    media.addEventListener && media.addEventListener("change", requestFrame);
    U.ready = true;
    U._debug = { worldShot, homeKey, basis, scenes, FOV };   // used by tests/universe.test.cjs
    document.dispatchEvent(new CustomEvent("fif:universe"));
  }
  U.refresh = () => { resize(); requestFrame(); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
