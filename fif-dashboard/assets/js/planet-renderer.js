/* Original procedural worlds. Canvas renderer; no remote textures or WebGL requirement. */
(function(){
  const F=window.FIF, TAU=Math.PI*2, cache=new Map();
  // One world per research track. `type` and `pal` drive the WebGL renderer (space-engine.js);
  // `kind`, `color` and `air` drive this Canvas fallback. Palettes are linear RGB 0..1.
  F.worlds=[
    {name:"EMBER",   theme:"volcanic world",  type:4,pal:[[.10,.08,.08],[.28,.22,.20],[1,.42,.10]],atm:[.9,.45,.2],atmK:.35,kind:"rock",color:[96,58,48],seed:3,air:[181,104,60]},
    {name:"IGNITION",theme:"desert world",    type:1,pal:[[.55,.27,.15],[.78,.52,.32],[.35,.20,.14]],atm:[.85,.6,.45],atmK:.45,kind:"rock",color:[185,104,67],seed:17,air:[200,140,100]},
    {name:"AEROSOL", theme:"ocean world",     type:0,pal:[[.04,.16,.34],[.26,.30,.16],[.55,.47,.35]],atm:[.35,.6,1],atmK:1,kind:"ocean",color:[93,158,151],seed:31,air:[72,135,211]},
    {name:"DROPLET", theme:"ice moon",        type:3,pal:[[.78,.84,.90],[.62,.72,.82],[.55,.32,.22]],atm:[.6,.75,1],atmK:.25,kind:"ice",color:[170,190,210],seed:53,air:[127,150,205]},
    {name:"PLASMA",  theme:"gas giant",       type:2,pal:[[.42,.55,.78],[.25,.32,.60],[.82,.88,.95]],atm:[.45,.6,1],atmK:.7,kind:"gas",color:[110,140,200],seed:71,air:[120,150,230]},
    {name:"SOOT",    theme:"cratered moon",   type:5,pal:[[.09,.09,.10],[.20,.19,.19],[.42,.40,.38]],atm:[.6,.6,.65],atmK:0,kind:"rock",color:[70,68,66],seed:97,air:[90,90,100]}
  ];
  function hash(x,y,s){const n=Math.sin(x*127.1+y*311.7+s*74.7)*43758.5453;return n-Math.floor(n);}
  function noise(x,y,s){
    const ix=Math.floor(x),iy=Math.floor(y),fx=x-ix,fy=y-iy,a=fx*fx*(3-2*fx),b=fy*fy*(3-2*fy);
    return (hash(ix,iy,s)*(1-a)+hash(ix+1,iy,s)*a)*(1-b)+(hash(ix,iy+1,s)*(1-a)+hash(ix+1,iy+1,s)*a)*b;
  }
  function fbm(x,y,s){let v=0,a=.54;for(let k=0;k<5;k++){v+=a*noise(x,y,s+k);x=x*2.03+7;y=y*2.03+3;a*=.48;}return v;}
  function texture(w){
    if(cache.has(w.seed))return cache.get(w.seed);
    const width=512,height=256,pixels=new Uint8ClampedArray(width*height*3);
    const craters=Array.from({length:32},(_,i)=>({x:hash(i,1,w.seed)*width,y:hash(i,2,w.seed)*height,r:3+hash(i,3,w.seed)*18}));
    for(let y=0;y<height;y++)for(let x=0;x<width;x++){
      const n=fbm(x/65,y/65,w.seed),fine=noise(x*.7,y*.7,w.seed)*.06;
      let c,light=.65+n*.6;
      if(w.kind==="ocean"){
        const land=n>.53;
        c=land?[105+n*55,102+n*50,67+n*45]:[16+n*25,42+n*55,65+n*85];
        const cloud=fbm(x/38+12*Math.sin(y/35),y/30,w.seed+20);
        const cover=Math.max(0,(cloud-.57)*4);
        c=c.map(v=>v*(1-cover)+220*cover);
      }else if(w.kind==="gas"){
        const bands=.5+.5*Math.sin(y*.21+noise(x/55,y/22,w.seed)*4+Math.sin(x*.025)*.5);
        c=w.color.map((v,k)=>v*(.55+.5*bands)+(k===2?15:5)*n);
      }else{
        let relief=0;
        for(const cr of craters){const dx=Math.min(Math.abs(x-cr.x),width-Math.abs(x-cr.x)),dy=y-cr.y,r=Math.hypot(dx,dy)/cr.r;
          if(r<1.2)relief+=r<.8?-.19*(1-r):.15*Math.sin((r-.8)/.4*Math.PI);
        }
        light+=relief;c=w.color.map((v,k)=>v*(light+fine)+(w.kind==="ice"?Math.max(0,.42-n)*220:0));
      }
      const polar=Math.max(0,(Math.abs(y/height-.5)-.40)*6)*(w.kind==="gas"?0:1);
      const index=(y*width+x)*3;for(let k=0;k<3;k++)pixels[index+k]=c[k]*(1-polar)+215*polar;
    }
    const t={width,height,pixels};cache.set(w.seed,t);return t;
  }
  F.createPlanet=function(canvas,index=0,options={}){
    const g=canvas.getContext("2d");if(!g)return {draw(){},dispose(){}};
    const size=options.size||240,world=F.worlds[index%F.worlds.length],tex=texture(world);
    const layer=document.createElement("canvas");layer.width=layer.height=size;
    const lg=layer.getContext("2d"),image=lg.createImageData(size,size),surface=[];
    const radius=size*.405,centre=size/2;
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){
      const nx=(x-centre)/radius,ny=(y-centre)/radius,r=nx*nx+ny*ny;if(r>1)continue;
      const nz=Math.sqrt(1-r),mu=-.67*nx-.28*ny+.687*nz;
      surface.push({i:(y*size+x)*4,u:(Math.atan2(nx,nz)/TAU+.5)*tex.width,v:Math.max(0,Math.min(tex.height-1,Math.floor((Math.asin(ny)/Math.PI+.5)*tex.height))),light:.012+Math.pow(Math.max(0,mu),.85)*1.1,rim:Math.pow(1-nz,3)*Math.max(0,mu+.25)*.55});
    }
    canvas.width=canvas.height=size;
    return {draw(rotation=0){
      const pixels=image.data,offset=rotation/TAU*tex.width;
      for(const p of surface){const u=((Math.floor(p.u+offset)%tex.width)+tex.width)%tex.width,t=(p.v*tex.width+u)*3;
        for(let k=0;k<3;k++)pixels[p.i+k]=Math.min(255,tex.pixels[t+k]*p.light+world.air[k]*p.rim);
        pixels[p.i+3]=255;
      }
      lg.putImageData(image,0,0);g.clearRect(0,0,size,size);
      const halo=g.createRadialGradient(centre,centre,radius*.94,centre,centre,radius*1.12);
      halo.addColorStop(0,"transparent");halo.addColorStop(.4,"rgba("+world.air.join(",")+",.12)");halo.addColorStop(1,"transparent");g.fillStyle=halo;g.fillRect(0,0,size,size);
      g.drawImage(layer,0,0);
    },dispose(){canvas.width=canvas.height=1;}};
  };
})();
