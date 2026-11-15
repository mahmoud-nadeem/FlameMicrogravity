const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const root = path.join(__dirname, "..");
const context = {window:{},document:{addEventListener(){},querySelectorAll:()=>[]},localStorage:{getItem(){return null;}},URLSearchParams,setInterval(){return 0;},clearInterval(){},setTimeout(){return 0;},clearTimeout(){}};
context.window.matchMedia=()=>({matches:false});
vm.createContext(context);
for(const file of ["data/site-data.js","assets/js/util.js","assets/js/sprites.js","assets/js/dialog.js","assets/js/planet-renderer.js","assets/js/pages.js","assets/js/lab-config.js","assets/js/lab.js","data/shorts.js","assets/js/expedition.js","assets/js/orbital-explore.js","assets/js/chat-visuals.js"]){
  vm.runInContext(fs.readFileSync(path.join(root,file),"utf8"),context,{filename:file});
}
const F=context.window.FIF;
// Conservation of a unit pulse, transport of its centre, and increasing dispersion.
for(const u of [0,2,8]) for(const t of [0,10,60]){
  let mass=0,moment=0;
  for(let x=-200;x<700;x+=.05){const c=F.transport(x,t,u,1)*.05;mass+=c;moment+=x*c;}
  assert.ok(Math.abs(mass-1)<1e-6);
  assert.ok(Math.abs(moment-u*t)<1e-5);
}
assert.ok(F.transport(0,10,0,5)<F.transport(0,10,0,1));
assert.equal(F.transport(-5,10,0,1),F.transport(5,10,0,1));
assert.match(F.pages.lab("PSI-101").html,/EDUCATIONAL MODEL/);
assert.match(F.pages.lab("unknown").html,/unavailable/);
assert.match(F.pages.profile("nadeem").html,/BACK TO EXPLORE/);
assert.match(F.pages.record("PSI-101").html,/LAUNCH SIMULATION/);
assert.match(F.pages.shorts().html,/DISCOVERY VIEWPORT/);
assert.match(F.pages.explore().html,/CHOOSE A WORLD/);
assert.equal((F.pages.explore().html.match(/class="map-node"/g)||[]).length,6);
assert.match(F.pages.explore().html,/CREW DIRECTORY/);
assert.equal((F.pages.home().html.match(/class="story-sec world-sec"/g)||[]).length,6);
assert.match(F.pages.lab("PSI-101").html,/MODEL CARD/);
assert.match(F.pages.lab("PSI-101").html,/Not calibrated/);
for(const f of ["assets/vendor/pdfjs/pdf.min.mjs","assets/vendor/pdfjs/pdf.worker.min.mjs","assets/vendor/pdfjs/LICENSE"])assert.ok(fs.existsSync(path.join(root,f)),f);
assert.doesNotMatch(fs.readFileSync(path.join(root,"assets/js/expedition.js"),"utf8"),/cdn\.jsdelivr/,"PDF.js is bundled, not loaded from a CDN");
for(const item of context.window.FIF_SHORTS){
  const bytes=fs.readFileSync(path.join(root,item.url));
  assert.equal(bytes.subarray(0,4).toString(),"%PDF");
}
const html=fs.readFileSync(path.join(root,"index.html"),"utf8");
for(const [,src] of html.matchAll(/(?:src|href)="([^"#]+\.(?:js|css))"/g))assert.ok(fs.existsSync(path.join(root,src)),src);
console.log("Passed: transport conservation/centroid/dispersion, route rendering, PDF signatures, local asset references.");
