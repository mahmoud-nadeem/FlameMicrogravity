const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm"),path=require("node:path");
const root=path.join(__dirname,"..");
const load=(ctx,file)=>vm.runInContext(fs.readFileSync(path.join(root,"assets/js",file),"utf8"),ctx,{filename:file});
const flush=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
async function testQueue(){
  const ctx=vm.createContext({window:{FIF:{}}});load(ctx,"conversation-queue.js");
  const q=ctx.window.FIF.createConversationQueue(),events=[];let release;
  const first=q.add(async()=>{events.push("start A");await new Promise(r=>release=r);events.push("end A");});
  const second=q.add(async()=>{events.push("start B");throw Error("network failed");}).catch(e=>events.push(e.message));
  const third=q.add(async()=>events.push("C"));
  assert.deepEqual(events,["start A"]);release();await Promise.all([first,second,third]);
  assert.deepEqual(events.filter(e=>e!=="network failed"),["start A","end A","start B","C"]);
  assert.ok(events.includes("network failed"));
}
async function testChat(){
  class El {
    constructor(){this.children=[];this.handlers={};this.dataset={};this.value="";this.isConnected=true;this.classList={add(){},remove(){}};}
    insertAdjacentHTML(){}
    set innerHTML(value){this.html=value;this.nodes={canvas:new El(),".bubble":new El(),".t":new El()};}
    get innerHTML(){return this.html;}
    appendChild(e){this.children.push(e);return e;}
    append(e){this.appendChild(e);}
    querySelector(q){return this.nodes?.[q]||new El();}
    setAttribute(){}
    addEventListener(name,fn){this.handlers[name]=fn;}
    insertBefore(e){this.appendChild(e);}
    after(){}
    focus(){}
  }
  const elements=new Map();const $=id=>{if(!elements.has(id))elements.set(id,new El());return elements.get(id);};
  const chars=[{id:"guide",name:"Guide",greeting:"Guide greeting",track:"T0"},{id:"a",name:"Scientist A",greeting:"A greeting",track:"T1"},{id:"b",name:"Scientist B",greeting:"B greeting",track:"T2"}];
  let currentTyping=0,maxTyping=0;const turns=[],finish=[];
  const F={data:{chat:{api_url:""},faq:{items:[]},tracks:[],records:{},questions:[],findings:[]},
    characters:chars,character:id=>chars.find(c=>c.id===id),characterForTrack:()=>null,
    $,$$:()=>[],esc:String,spriteHTML:()=>"<canvas></canvas>",paintSprites(){},drawSprite(){},
    typeText(el,text,sprites,id){currentTyping++;maxTyping=Math.max(maxTyping,currentTyping);turns.push({id,text});return new Promise(r=>finish.push(()=>{currentTyping--;r();}));}
  };
  const ctx=vm.createContext({window:{FIF:F},document:{createElement:()=>new El()},console});
  load(ctx,"conversation-queue.js");load(ctx,"chat.js");F.initChat();
  F.openChat("a");F.openChat("b");assert.equal(turns.length,1);
  finish.shift()();await flush();assert.deepEqual(turns.map(t=>t.id),["a","b"]);
  finish.shift()();await flush();
  // Submit to B and switch to A before that turn finishes: B retains attribution.
  $("#chat-input").value="question outside the dataset";
  $("#chat-form").handlers.submit({preventDefault(){}});
  F.openChat("a");await flush();assert.equal(turns[2].id,"b");
  finish.shift()();await flush();assert.equal(turns[3].id,"a");
  finish.shift()();await flush();assert.equal(maxTyping,1);
}
async function testTypewriter(){
  const callbacks=new Map();let timer=0;
  const F={settings:{reduceMotion:false},drawSprite(){},blip(){}};
  const ctx=vm.createContext({window:{FIF:F},setInterval(fn){callbacks.set(++timer,fn);return timer;},clearInterval(id){callbacks.delete(id);},setTimeout(){return 0;},clearTimeout(){}});
  load(ctx,"dialog.js");
  const el={textContent:"",isConnected:true},sprite={classList:{add(){},remove(){}},dataset:{}};
  const a=F.typeText(el,"first message",[sprite]);const b=F.typeText(el,"replacement",[sprite]);
  await a;assert.equal(callbacks.size,1);el._finishTyping();await b;
  assert.equal(callbacks.size,0);assert.equal(el.textContent,"replacement");
  const c=F.typeText(el,"detached",[sprite]);el.isConnected=false;[...callbacks.values()][0]();await c;assert.equal(callbacks.size,0);
}
(async()=>{await testQueue();await testChat();await testTypewriter();console.log("Passed: FIFO, failure recovery, rapid crew switching, speaker attribution, single active typer, skip and detach cleanup.");})().catch(e=>{console.error(e);process.exitCode=1;});
