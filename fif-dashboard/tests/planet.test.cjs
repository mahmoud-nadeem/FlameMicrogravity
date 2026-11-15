const fs=require("node:fs"),vm=require("node:vm"),path=require("node:path"),assert=require("node:assert/strict");
let rendered;
function context(){return {createImageData(w,h){return {data:new Uint8ClampedArray(w*h*4)};},putImageData(image){rendered=new Uint8ClampedArray(image.data);},clearRect(){},fillRect(){},drawImage(){},createRadialGradient(){return {addColorStop(){}};}};}
const ctx=vm.createContext({window:{FIF:{}},document:{createElement(){return {getContext:context};}},Uint8ClampedArray});
vm.runInContext(fs.readFileSync(path.join(__dirname,"../assets/js/planet-renderer.js"),"utf8"),ctx);
const canvas={getContext:context},renderer=ctx.window.FIF.createPlanet(canvas,0,{size:80});
renderer.draw(0);const a=rendered;renderer.draw(.5);const b=rendered;
assert.ok(a.some((v,i)=>i%4!==3&&v!==b[i]),"axial rotation changes surface texture");
assert.equal(a[3],0,"space outside the globe remains transparent");
assert.ok(a[(40*80+40)*4+3]===255,"globe centre opaque");
let left=0,right=0;for(let y=30;y<50;y++){left+=a[(y*80+20)*4];right+=a[(y*80+60)*4];}
assert.ok(left>right,"fixed directional light produces a day/night terminator");
renderer.dispose();assert.equal(canvas.width,1);
console.log("Passed: rotating texture, transparent exterior, opaque sphere, directional lighting, disposal.");
