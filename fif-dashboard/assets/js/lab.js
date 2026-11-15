/* An analytical transport model, independent of the assistant and animation clock. */
(function () {
  const F = window.FIF, E = F.esc;
  // Unit-area Gaussian pulse on an unbounded 1-D axis. Units: cm, s, cm²/s.
  F.transport = (x, t, u, D, sigma0 = 2) => {
    const variance = sigma0 * sigma0 + 2 * D * t;
    return Math.exp(-Math.pow(x - u * t, 2) / (2 * variance)) / Math.sqrt(2 * Math.PI * variance);
  };
  const memories = {};
  F.pages.lab = function (id) {
    if (!["PSI-101","PSI-102","PSI-47"].includes(id)) return {html:'<h1>Lab unavailable</h1><a href="#/explore">Back to Explore</a>',mount(){}};
    return {
      html: `<a class="hud-btn profile-back" href="#/record/${E(id)}">&#9664; BACK TO EXPERIMENT</a>
      <p class="eyebrow">EXPERIMENT LAB · ${E(id)} · EDUCATIONAL MODEL</p><h1 class="page-title">FOLLOW THE SMOKE</h1>
      <p class="lede">Release a pulse of particles. Air carries its centre forward; mixing spreads it out. Change a setting and see the calculation respond.</p>
      <section class="exp-console"><div class="lab-grid"><div>
        <canvas class="lab-canvas" id="lab-plot" width="850" height="340" role="img" aria-label="Calculated particle concentration along a transport path"></canvas>
        <p id="lab-result" class="exp-status" aria-live="polite"></p>
        <div class="exp-toolbar"><button class="px-btn" id="lab-play">PLAY</button><button class="chip" id="lab-reset">RESET</button>
        <button class="chip" data-scenario="still">STILL AIR</button><button class="chip" data-scenario="gentle">GENTLE FLOW</button><button class="chip" data-scenario="fast">FAST FLOW</button></div>
      </div><div class="lab-controls">
        <label>Air speed <output id="u-out"></output><input aria-label="Air speed in centimetres per second" id="lab-u" type="range" min="0" max="8" step=".5" value="2"></label>
        <label>Effective mixing <output id="d-out"></output><input aria-label="Effective dispersion in square centimetres per second" id="lab-d" type="range" min=".1" max="5" step=".1" value="1"></label>
        <label>Sensor position <output id="l-out"></output><input aria-label="Sensor distance in centimetres" id="lab-l" type="range" min="10" max="100" step="5" value="50"></label>
        <label>Elapsed time <output id="t-out"></output><input aria-label="Time in seconds" id="lab-t" type="range" min="0" max="60" step=".1" value="0"></label>
        <p class="small muted">Mixing and sensor distance are illustrative inputs, not measured NASA apparatus parameters. No alarm threshold is assumed.</p>
      </div></div></section>
      <section class="panel"><h2>MISSION SCIENCE ASSISTANT</h2><p class="small">Offline command assistant. Try “increase air speed”, “set flow to 4”, “still air”, “why?”, or “explain mixing”. Results always come from the equation.</p>
      <form id="lab-form" class="exp-toolbar"><label class="sr-only" for="lab-prompt">Configure or ask about this experiment</label><input id="lab-prompt" class="lab-command" maxlength="300" placeholder="What happens if I increase air speed?"><button class="px-btn">ASK / APPLY</button></form>
      <div class="lab-crew-line">${F.spriteHTML("nadeem", "mid", "Mahmoud Nadeem, smoke track")}<p class="context-reaction" id="lab-reaction" role="status">You are at the controls. Change a parameter to investigate transport.</p></div>
      <p class="lab-answer" id="lab-answer" aria-live="polite">Choose a scenario, then press Play. The vertical marker is the sensor; the curve is the calculated particle distribution.</p>
      <button class="chip" id="lab-crew">ASK THE CREW ABOUT THE DATA</button></section>
      <section class="panel model-card" aria-labelledby="mc-title"><h2 id="mc-title">MODEL CARD</h2>
      <p class="kind-tag calc">CALCULATED &middot; NOT MEASURED &middot; NOT CALIBRATED</p>
      <div class="table-wrap"><table><tbody>
        <tr><th scope="row">Model</th><td>One-dimensional advection&ndash;diffusion of a released particle pulse, analytical Gaussian solution.</td></tr>
        <tr><th scope="row">Purpose</th><td>Show how air flow carries smoke and how mixing spreads it. A transport lesson, not a recreation of the flight apparatus.</td></tr>
        <tr><th scope="row">Parameters</th><td>${Object.entries({u:"Air speed",d:"Effective mixing",l:"Sensor position",t:"Elapsed time"}).map(([k,n])=>`${n}: ${F.labSchema[k].min}&ndash;${F.labSchema[k].max} ${F.labSchema[k].unit}`).join("; ")}; initial width &sigma;<sub>0</sub> = 2 cm (fixed).</td></tr>
        <tr><th scope="row">Equation</th><td>&part;c/&part;t + u &part;c/&part;x = D &part;&sup2;c/&part;x&sup2;; c(x,t) = exp[&minus;(x&minus;ut)&sup2;/(2&sigma;&sup2;)] / &radic;(2&pi;&sigma;&sup2;), &sigma;&sup2; = &sigma;<sub>0</sub>&sup2; + 2Dt.</td></tr>
        <tr><th scope="row">Assumptions</th><td>Constant flow and mixing; infinite 1-D path; Gaussian starting pulse; no walls, buoyancy, deposition, coagulation or chemistry.</td></tr>
        <tr><th scope="row">Limitations</th><td>Concentration is normalised per centimetre, not particles per cm&sup3;. It predicts no detector response, alarm time or particle growth.</td></tr>
        <tr><th scope="row">Calibration</th><td>Not calibrated against NASA measurements. The 0&ndash;8 cm/s air-speed range matches the inlet velocities listed in the SAME-R experimental table; mixing and sensor distance are illustrative.</td></tr>
        <tr><th scope="row">AI role</th><td>Typed commands are parsed into a bounded parameter patch and validated before the equation runs. No assistant produces numbers; every number on this page comes from the equation.</td></tr>
      </tbody></table></div></section>
      <details class="block panel" id="lab-details-${E(id)}"><summary>Research view: equations, assumptions and evidence</summary>
      <p>∂c/∂t + u ∂c/∂x = D ∂²c/∂x²; c(x,t) = exp[−(x−ut)²/(2σ²)] / √(2πσ²), with σ² = σ₀² + 2Dt and σ₀ = 2 cm. The pulse integrates to 1 over the infinite axis. Concentration here is normalised per centimetre, not particles/cm³.</p>
      <p>Assumes constant flow and dispersion, an infinite one-dimensional domain, a Gaussian initial pulse, and no walls, buoyancy, deposition, coagulation or chemical reactions. The centre reaches a sensor at L/u when u &gt; 0; this is not first arrival or an alarm time. This is a transport lesson, not a recreation or calibration of the flight apparatus.</p>
      <p>Source: <a href="https://ocw.mit.edu/courses/6-021j-quantitative-physiology-cells-and-tissues-fall-2004/b4b87eb17edb319471646bd01bbbdddc_manual5.pdf" target="_blank" rel="noopener">MIT: diffusion with convection</a>. Compare with <a href="#/research?q=F-T3-16">F-T3-16</a>: measured delays also include hardware transport. <a href="#/research?q=F-T3-1">Particle aging evidence</a> is separate from this transport equation.</p></details>`,
      mount(root) {
        const $ = s => root.querySelector(s), inputs = Object.fromEntries(["u","d","l","t"].map(k=>[k,$("#lab-"+k)]));
        let playing=false, raf=0, last=0, previous=0, dead=false, elapsed=0;
        const cv=$("#lab-plot"), g=cv.getContext("2d");
        const val=k=>+inputs[k].value;
        if(memories[id]) Object.entries(memories[id]).forEach(([k,v])=>inputs[k].value=v);
        const crewSprite=root.querySelector(".lab-crew-line canvas.sprite");
        // The scientist reacts to what you actually changed and gestures toward the plot.
        function react(message){$("#lab-reaction").textContent=F.settings.reactions===false?"Character reactions are off.":message;if(F.settings.reactions!==false&&F.setSpriteState)F.setSpriteState(crewSprite,{look:-1,gesture:"point"},1800);}

        function paint() {
          const u=val("u"), d=val("d"), l=val("l"), t=val("t");
          ["u","d","l","t"].forEach((k,i)=>$("#"+k+"-out").textContent=val(k).toFixed(k==="t"?1:1)+[" cm/s"," cm²/s"," cm"," s"][i]);
          const sigma=Math.sqrt(4+2*d*t), centre=u*t;
          $("#lab-result").textContent=`Centre: ${centre.toFixed(1)} cm · Spread σ: ${sigma.toFixed(1)} cm · At sensor: ${F.transport(l,t,u,d).toFixed(5)} cm⁻¹`;
          g.fillStyle="#050814";g.fillRect(0,0,850,340);
          g.strokeStyle="#2a3660";g.strokeRect(55,30,750,245);
          g.fillStyle="#8e97b3";g.font="14px monospace";g.fillText("Normalised concentration (cm⁻¹) · fixed scale 0–0.20",55,20);
          for(let x=0;x<=100;x+=20){g.fillText(x+" cm",55+x*7.5,300);}
          g.strokeStyle="#6da7ec";g.beginPath();
          for(let i=0;i<=750;i++){const y=275-F.transport(i/7.5,t,u,d)*1200;i?g.lineTo(55+i,y):g.moveTo(55+i,y);}g.stroke();
          g.strokeStyle="#f0b042";g.beginPath();g.moveTo(55+l*7.5,30);g.lineTo(55+l*7.5,275);g.stroke();
          g.fillStyle="#f0b042";g.fillText("SENSOR",Math.min(730,55+l*7.5),325);
          cv.setAttribute("aria-label",$("#lab-result").textContent);
        }
        function pause(){playing=false;cancelAnimationFrame(raf);$("#lab-play").textContent="PLAY";}
        function tick(now){if(dead||!playing)return;if(document.hidden){last=now;raf=requestAnimationFrame(tick);return;}const dt=Math.min((now-last)/1000,.1);last=now;elapsed=Math.min(60,elapsed+dt);inputs.t.value=elapsed;if(now-previous>80){paint();previous=now;}if(val("t")>=60){pause();paint();}else raf=requestAnimationFrame(tick);}
        $("#lab-play").onclick=()=>{if(playing)return pause();if(val("t")>=60)inputs.t.value=0;playing=true;elapsed=val("t");last=performance.now();$("#lab-play").textContent="PAUSE";raf=requestAnimationFrame(tick);};
        $("#lab-reset").onclick=()=>{pause();Object.entries({u:2,d:1,l:50,t:0}).forEach(([k,v])=>inputs[k].value=v);paint();$("#lab-answer").textContent="Reset to a 2 cm/s flow, 1 cm²/s mixing and a sensor 50 cm away.";};
        Object.entries(inputs).forEach(([key,input])=>input.oninput=()=>{pause();paint();explain();
          react(key==="u"?`You changed the airflow to ${val("u")} cm/s. Watch the pulse centre: it is now at ${(val("u")*val("t")).toFixed(1)} cm, speed × time.`:key==="d"?"You changed mixing. The pulse spreads without creating extra particles.":key==="l"?"You moved the sensor. We are sampling the same distribution at a different position.":"You moved the clock. The graph now shows the calculation at that time.");
        });
        root.querySelectorAll("[data-scenario]").forEach(b=>b.onclick=()=>{pause();inputs.u.value={still:0,gentle:2,fast:8}[b.dataset.scenario];inputs.t.value=0;paint();explain();});
        function explain(prefix=""){const u=val("u");$("#lab-answer").textContent=prefix+(u?`The pulse centre reaches ${val("l")} cm at ${(val("l")/u).toFixed(1)} s (distance ÷ speed). Increasing flow moves the centre faster. `:"With no airflow the centre stays at the release point; dispersion still spreads particles toward the sensor. ")+`Mixing widens the pulse: σ = ${Math.sqrt(4+2*val("d")*val("t")).toFixed(2)} cm at ${val("t")} s. This predicts transport, not detector sensitivity or particle growth.`;}
        $("#lab-form").onsubmit=e=>{e.preventDefault();pause();const q=$("#lab-prompt").value.toLowerCase().trim();if(!q)return;
          const current=Object.fromEntries(Object.keys(inputs).map(k=>[k,val(k)]));
          const command=F.parseLabCommand(q,current);
          if(command.error){$("#lab-answer").textContent=command.error;return;}
          Object.entries(command.patch).forEach(([k,v])=>inputs[k].value=v);
          react("You configured the model. The calculation below uses those validated parameters.");
          paint();explain("Calculated with your current settings. ");
        };
        $("#lab-crew").onclick=()=>F.openChat("nadeem");paint();
        return ()=>{memories[id]=Object.fromEntries(Object.keys(inputs).map(k=>[k,val(k)]));dead=true;pause();};
      }
    };
  };
})();
