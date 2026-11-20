"""WebGL / Three.js / canvas effects layered onto the Streamlit page."""

from __future__ import annotations

import json

# ── 1. Global FX: shader background, cursor glow, click sparks, tilt cards, confetti ──
# Runs once in the main document (st.html with JavaScript), guarded by window.__cbFX.
GLOBAL_FX_JS = r"""
(function(){
if (window.__cbFX) return; window.__cbFX = true;
const d = document;

/* ---------- WebGL aurora shader background ---------- */
const cv = d.createElement('canvas');
cv.id = 'cb-bg';
Object.assign(cv.style,{position:'fixed',inset:'0',width:'100vw',height:'100vh',zIndex:'-1',pointerEvents:'none'});
d.body.prepend(cv);
const gl = cv.getContext('webgl',{premultipliedAlpha:false,antialias:false});
if (gl){
  const vs = `attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}`;
  const fs = `precision highp float;uniform vec2 r;uniform float t;uniform vec2 m;
  float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
  float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
    return mix(mix(h(i),h(i+vec2(1,0)),f.x),mix(h(i+vec2(0,1)),h(i+vec2(1,1)),f.x),f.y);}
  float fbm(vec2 p){float v=0.,a=.5;for(int i=0;i<5;i++){v+=a*n(p);p*=2.02;a*=.5;}return v;}
  void main(){
    vec2 uv=gl_FragCoord.xy/r; vec2 q=uv; q.x*=r.x/r.y;
    float tt=t*.04;
    vec2 w=vec2(fbm(q*1.6+tt),fbm(q*1.6-tt+3.1));
    float f=fbm(q*2.2+w*1.8+vec2(tt*2.,-tt));
    vec3 base=vec3(.02,.027,.06);
    vec3 lime=vec3(.78,1.,.24), cyan=vec3(.24,.96,1.), vio=vec3(.62,.48,1.), pink=vec3(1.,.24,.68);
    vec3 col=base;
    col+=vio*smoothstep(.45,.95,f)*.22;
    col+=cyan*smoothstep(.55,1.,w.x*f*1.6)*.16;
    col+=lime*pow(smoothstep(.6,1.,w.y*f*1.5),2.)*.12;
    col+=pink*smoothstep(.75,1.,fbm(q*3.-tt*3.))*.05;
    float md=distance(uv,m); col+=cyan*.07*exp(-md*6.);
    /* perspective grid floor */
    vec2 g=uv; float y=1.-g.y; if(y>.55){float z=1./(y-.5+.0001); vec2 gp=vec2((g.x-.5)*z*2.,z+t*.6);
      float line=max(smoothstep(.96,1.,fract(gp.x)),smoothstep(.95,1.,fract(gp.y)));
      col+=lime*line*.06*smoothstep(.55,1.,y);}
    col*=1.-.55*pow(distance(uv,vec2(.5)),1.6);
    gl_FragColor=vec4(col,1.);
  }`;
  const sh=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);return s;};
  const pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,vs));gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,fs));
  gl.linkProgram(pr);gl.useProgram(pr);
  const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);
  gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,1,1]),gl.STATIC_DRAW);
  const loc=gl.getAttribLocation(pr,'p');gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,2,gl.FLOAT,false,0,0);
  const ur=gl.getUniformLocation(pr,'r'),ut=gl.getUniformLocation(pr,'t'),um=gl.getUniformLocation(pr,'m');
  let mx=.5,my=.5,tmx=.5,tmy=.5;
  addEventListener('pointermove',e=>{tmx=e.clientX/innerWidth;tmy=1.-e.clientY/innerHeight;});
  const DPR=Math.min(devicePixelRatio,1.25)*.6;
  const rs=()=>{cv.width=innerWidth*DPR;cv.height=innerHeight*DPR;gl.viewport(0,0,cv.width,cv.height);};
  addEventListener('resize',rs);rs();
  const t0=performance.now();
  (function loop(){mx+=(tmx-mx)*.05;my+=(tmy-my)*.05;
    gl.uniform2f(ur,cv.width,cv.height);gl.uniform1f(ut,(performance.now()-t0)/1000);gl.uniform2f(um,mx,my);
    gl.drawArrays(gl.TRIANGLE_STRIP,0,4);requestAnimationFrame(loop);})();
}
/* lift the app above the canvas */
const st=d.createElement('style');
st.textContent='#cb-glow{position:fixed;width:520px;height:520px;border-radius:50%;pointer-events:none;z-index:1;'+
 'background:radial-gradient(circle,rgba(61,245,255,.10),rgba(157,123,255,.06) 40%,transparent 70%);transform:translate(-50%,-50%);mix-blend-mode:screen;transition:opacity .4s}'+
 '#cb-spark{position:fixed;inset:0;pointer-events:none;z-index:9999}';
d.head.appendChild(st);

/* ---------- cursor glow ---------- */
const glow=d.createElement('div');glow.id='cb-glow';d.body.appendChild(glow);
let gx=innerWidth/2,gy=innerHeight/2,cx=gx,cy=gy;
addEventListener('pointermove',e=>{gx=e.clientX;gy=e.clientY;});
(function g(){cx+=(gx-cx)*.12;cy+=(gy-cy)*.12;glow.style.left=cx+'px';glow.style.top=cy+'px';requestAnimationFrame(g);})();

/* ---------- click sparks (game feel) ---------- */
const sp=d.createElement('canvas');sp.id='cb-spark';d.body.appendChild(sp);const sx=sp.getContext('2d');
const P=[];const rsz=()=>{sp.width=innerWidth;sp.height=innerHeight;};addEventListener('resize',rsz);rsz();
const COL=['#C6FF3D','#3DF5FF','#FF3DAE','#9D7BFF','#FFB13D'];
addEventListener('pointerdown',e=>{for(let i=0;i<18;i++){const a=Math.random()*Math.PI*2,s=2+Math.random()*5;
  P.push({x:e.clientX,y:e.clientY,vx:Math.cos(a)*s,vy:Math.sin(a)*s,l:1,c:COL[i%5],r:1.5+Math.random()*2.5});}});
(function s(){sx.clearRect(0,0,sp.width,sp.height);
  for(let i=P.length-1;i>=0;i--){const p=P[i];p.x+=p.vx;p.y+=p.vy;p.vy+=.12;p.vx*=.97;p.l-=.025;
    if(p.l<=0){P.splice(i,1);continue;}sx.globalAlpha=p.l;sx.fillStyle=p.c;sx.shadowBlur=12;sx.shadowColor=p.c;
    sx.beginPath();sx.arc(p.x,p.y,p.r,0,7);sx.fill();}
  requestAnimationFrame(s);})();

/* ---------- 3D tilt + spotlight for .cb-tilt ---------- */
d.addEventListener('pointermove',e=>{
  const el=e.target.closest&&e.target.closest('.cb-tilt');
  d.querySelectorAll('.cb-tilt[data-t]').forEach(x=>{if(x!==el){x.style.transform='';x.removeAttribute('data-t');}});
  if(!el)return; const r=el.getBoundingClientRect(),px=(e.clientX-r.left)/r.width,py=(e.clientY-r.top)/r.height;
  el.setAttribute('data-t','1');
  el.style.transform=`perspective(900px) rotateX(${(.5-py)*12}deg) rotateY(${(px-.5)*14}deg) translateZ(6px)`;
  el.style.setProperty('--mx',px*100+'%');el.style.setProperty('--my',py*100+'%');
});

/* ---------- confetti on demand ---------- */
const cs=d.createElement('script');cs.src='https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/dist/confetti.browser.min.js';d.head.appendChild(cs);
window.cbConfetti=function(){if(!window.confetti)return;const c=['#C6FF3D','#3DF5FF','#FF3DAE','#9D7BFF'];
  confetti({particleCount:120,spread:90,origin:{y:.65},colors:c,zIndex:10000});
  setTimeout(()=>confetti({particleCount:80,angle:60,spread:70,origin:{x:0},colors:c,zIndex:10000}),200);
  setTimeout(()=>confetti({particleCount:80,angle:120,spread:70,origin:{x:1},colors:c,zIndex:10000}),350);};
})();
"""

# Streamlit strips <script> from st.html, so a 0-height component iframe (same-origin)
# injects the code into the main document where it keeps running across reruns.
GLOBAL_FX = (
    "<script>(function(){const P=window.parent;if(!P||P.__cbFX)return;"
    "const s=P.document.createElement('script');s.textContent=" + json.dumps(GLOBAL_FX_JS) + ";"
    "P.document.head.appendChild(s);})();</script>"
)


def confetti_js(nonce: int) -> str:
    """Fire confetti once per generated plan (nonce makes each component unique)."""
    return (f"<script>/*{nonce}*/setTimeout(()=>{{try{{parent.cbConfetti&&parent.cbConfetti()}}catch(e){{}}}},250)</script>")


# ── 2. Three.js holographic stadium hero (inside an iframe) ────────────────────
HERO_TEMPLATE = r"""
<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@600;800;900&family=Space+Grotesk:wght@400;600&family=JetBrains+Mono&display=swap" rel="stylesheet">
<style>
*{margin:0;box-sizing:border-box}html,body{height:100%;background:transparent;overflow:hidden;font-family:'Space Grotesk',sans-serif;color:#E9F0FF}
#wrap{position:relative;height:100%;border-radius:28px;overflow:hidden;background:radial-gradient(ellipse at 70% 40%,#101a3a 0%,#060914 60%,#04060d 100%);
  border:1px solid rgba(255,255,255,.08)}
canvas{position:absolute;inset:0;display:block}
.ov{position:absolute;inset:0;padding:clamp(22px,4vw,56px);display:flex;flex-direction:column;justify-content:center;pointer-events:none;
  background:linear-gradient(90deg,rgba(4,6,13,.85) 0%,rgba(4,6,13,.35) 45%,transparent 70%)}
.k{font-family:'JetBrains Mono';font-size:12px;letter-spacing:.3em;color:#C6FF3D;display:flex;align-items:center;gap:10px;opacity:0;animation:in .8s .2s forwards}
.k i{width:8px;height:8px;border-radius:50%;background:#C6FF3D;box-shadow:0 0 12px #C6FF3D;animation:pulse 1.4s infinite}
h1{font-family:'Unbounded';font-weight:900;font-size:clamp(44px,8.4vw,118px);line-height:.88;letter-spacing:-.05em;margin:14px 0 10px}
h1 span{display:inline-block;opacity:0;transform:translateY(60px) rotateX(-80deg);animation:let .9s cubic-bezier(.2,.9,.2,1) forwards;
  background:linear-gradient(180deg,#fff 30%,#9fb0d9);-webkit-background-clip:text;background-clip:text;color:transparent}
h1 .ai{background:linear-gradient(100deg,#C6FF3D,#3DF5FF 60%,#9D7BFF);-webkit-background-clip:text;background-clip:text;filter:drop-shadow(0 0 24px rgba(198,255,61,.45))}
p.s{max-width:430px;color:#A9B6D6;font-size:clamp(14px,1.4vw,17px);line-height:1.5;opacity:0;animation:in .9s 1.1s forwards}
.cta{display:flex;gap:12px;margin-top:26px;pointer-events:auto;opacity:0;animation:in .9s 1.35s forwards;flex-wrap:wrap}
.btn{font-family:'Space Grotesk';font-weight:700;font-size:15px;border:none;border-radius:14px;padding:14px 22px;cursor:pointer;position:relative;overflow:hidden;transition:transform .2s}
.btn:hover{transform:translateY(-3px) scale(1.02)}
.b1{background:linear-gradient(110deg,#C6FF3D,#7CFFB2 45%,#3DF5FF);color:#03060E;box-shadow:0 14px 50px -12px rgba(198,255,61,.8)}
.b1::after{content:"";position:absolute;inset:0;background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,.8) 50%,transparent 70%);transform:translateX(-120%);animation:sh 2.6s infinite}
.b2{background:rgba(255,255,255,.06);color:#E9F0FF;border:1px solid rgba(255,255,255,.18);backdrop-filter:blur(10px)}
.chips{position:absolute;inset:0;pointer-events:none}
.chip{position:absolute;font-family:'JetBrains Mono';font-size:11px;letter-spacing:.08em;padding:8px 12px;border-radius:12px;
  background:rgba(8,12,30,.65);border:1px solid rgba(255,255,255,.12);backdrop-filter:blur(8px);white-space:nowrap;
  animation:float 6s ease-in-out infinite;opacity:0;transition:opacity .8s}
.chip b{color:var(--c)}
.stats{position:absolute;right:clamp(16px,3vw,40px);bottom:clamp(16px,3vw,32px);display:flex;gap:22px;pointer-events:none}
.stat{text-align:right}.stat b{font-family:'Unbounded';font-size:clamp(20px,2.4vw,32px);display:block;color:#fff}
.stat small{font-family:'JetBrains Mono';font-size:10px;letter-spacing:.2em;color:#8B97B8}
.scan{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(255,255,255,.025) 0 1px,transparent 1px 3px);mix-blend-mode:overlay}
@keyframes in{to{opacity:1;transform:none}}@keyframes let{to{opacity:1;transform:none}}
@keyframes pulse{50%{transform:scale(1.6);opacity:.4}}@keyframes sh{60%,100%{transform:translateX(120%)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-14px)}}
@media(max-width:700px){.chips,.stats{display:none}.ov{background:linear-gradient(180deg,rgba(4,6,13,.2),rgba(4,6,13,.85))}}
</style>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
"three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"}}</script>
</head><body><div id="wrap">
<div class="scan"></div>
<div class="chips" id="chips"></div>
<div class="ov">
  <div class="k"><i></i>NEXTGEN SPORTS LAB · POWERED BY GEMINI</div>
  <h1 id="title"></h1>
  <p class="s">__SUB__</p>
  <div class="cta"><button class="btn b1" onclick="go(1)">Start training ⚡</button><button class="btn b2" onclick="go(2)">Open Tuning Lab 🧪</button></div>
</div>
<div class="stats"><div class="stat"><b id="s1">0</b><small>AI FEATURES</small></div><div class="stat"><b id="s2">0</b><small>SPORTS</small></div><div class="stat"><b id="s3">0</b><small>POSITIONS</small></div></div>
</div>
<script>
const STATS=__STATS__;
function go(i){try{const P=parent,el=P.document.querySelectorAll('[role="tab"]')[i];if(!el)return;
  ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(t=>el.dispatchEvent(new (t.startsWith('pointer')?P.PointerEvent:P.MouseEvent)(t,
    {bubbles:true,cancelable:true,pointerId:1,isPrimary:true,button:0,pointerType:'mouse'})));
  P.scrollTo({top:0,behavior:'smooth'});}catch(e){}}
const words=[["COACH",""],["BOT",""],[" AI","ai"]];let h='',k=0;
words.forEach(([w,c])=>{for(const ch of w){h+=`<span class="${c}" style="animation-delay:${.35+k*.06}s">${ch===' '?'&nbsp;':ch}</span>`;k++;}if(w==='BOT')h+='<br>';});
document.getElementById('title').innerHTML=h;
const tick=(id,to)=>{let v=0;const el=document.getElementById(id);const s=performance.now();(function f(n){const p=Math.min(1,(n-s)/1800);v=Math.round(to*(1-Math.pow(1-p,3)));el.textContent=v;if(p<1)requestAnimationFrame(f);})(s);};
setTimeout(()=>{tick('s1',STATS[0]);tick('s2',STATS[1]);tick('s3',STATS[2]);},900);
const CH=[["🏋️ Position workouts","#C6FF3D",.57,.1],["🩹 Injury-safe plans","#3DF5FF",.76,.2],["🥗 7-day fuel","#FFB13D",.8,.47],
          ["🧠 Tactical IQ","#FF3DAE",.57,.7],["🧘 Tournament mindset","#9D7BFF",.73,.62]];
const chips=document.getElementById('chips');
CH.forEach(([t,c,x,y],i)=>{const e=document.createElement('div');e.className='chip';e.style.cssText=`left:${x*100}%;top:${y*100}%;--c:${c};animation-delay:${i*.7}s;border-color:${c}55`;
  e.innerHTML=`<b>●</b> ${t}`;chips.appendChild(e);setTimeout(()=>e.style.opacity=1,1400+i*180);});
</script>
<script type="module">
import * as THREE from 'three';
import {EffectComposer} from 'three/addons/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/addons/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/addons/postprocessing/UnrealBloomPass.js';
import {OutputPass} from 'three/addons/postprocessing/OutputPass.js';

const wrap=document.getElementById('wrap');
const R=new THREE.WebGLRenderer({antialias:true,alpha:false});
R.setPixelRatio(Math.min(devicePixelRatio,2));R.setClearColor(0x04060d,1);
wrap.prepend(R.domElement);
const S=new THREE.Scene();S.background=new THREE.Color(0x04060d);S.fog=new THREE.FogExp2(0x04060d,.045);
const C=new THREE.PerspectiveCamera(50,1,.1,200);C.position.set(0,1.2,9);
const root=new THREE.Group();S.add(root);
const off=()=>innerWidth>700?3.1:0; root.position.x=off();

/* holographic ball: wire icosahedron + fresnel core + vertex nodes */
const ico=new THREE.IcosahedronGeometry(1.7,1);
const wire=new THREE.LineSegments(new THREE.EdgesGeometry(ico),new THREE.LineBasicMaterial({color:0xC6FF3D,transparent:true,opacity:.9}));
root.add(wire);
const coreMat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,
  uniforms:{t:{value:0}},
  vertexShader:`varying vec3 vN;varying vec3 vV;void main(){vN=normalize(normalMatrix*normal);vec4 mv=modelViewMatrix*vec4(position,1.);vV=normalize(-mv.xyz);gl_Position=projectionMatrix*mv;}`,
  fragmentShader:`uniform float t;varying vec3 vN;varying vec3 vV;void main(){float f=pow(1.-max(dot(vN,vV),0.),2.4);
    vec3 c=mix(vec3(.24,.96,1.),vec3(.62,.48,1.),.5+.5*sin(t*.8+vN.y*3.));gl_FragColor=vec4(c*f*1.1,f*.85);}`});
const core=new THREE.Mesh(new THREE.SphereGeometry(1.55,64,64),coreMat);root.add(core);
const nodes=new THREE.Points(ico,new THREE.PointsMaterial({color:0xffffff,size:.09,transparent:true,opacity:.95}));root.add(nodes);
const inner=new THREE.Mesh(new THREE.IcosahedronGeometry(.75,0),new THREE.MeshBasicMaterial({color:0xFF3DAE,wireframe:true,transparent:true,opacity:.7}));
root.add(inner);

/* orbit rings with satellites */
const rings=[];const RC=[0x3DF5FF,0xFF3DAE,0x9D7BFF];
for(let i=0;i<3;i++){const g=new THREE.Group();
  const ring=new THREE.Mesh(new THREE.TorusGeometry(2.5+i*.55,.008,8,200),new THREE.MeshBasicMaterial({color:RC[i],transparent:true,opacity:.75}));
  g.add(ring);const sat=new THREE.Mesh(new THREE.SphereGeometry(.08,16,16),new THREE.MeshBasicMaterial({color:RC[i]}));
  sat.position.x=2.5+i*.55;g.add(sat);g.rotation.set(Math.PI/2+(i-1)*.5,i*.6,0);root.add(g);rings.push(g);}

/* galaxy particles */
const N=3200,pos=new Float32Array(N*3),col=new Float32Array(N*3);const cA=new THREE.Color(0xC6FF3D),cB=new THREE.Color(0x3DF5FF),cC=new THREE.Color(0x9D7BFF);
for(let i=0;i<N;i++){const r=3+Math.pow(Math.random(),1.6)*12,a=Math.random()*Math.PI*2+r*.35;
  pos[i*3]=Math.cos(a)*r;pos[i*3+1]=(Math.random()-.5)*(1.4+r*.12);pos[i*3+2]=Math.sin(a)*r;
  const c=(i%3===0?cA:i%3===1?cB:cC).clone().lerp(new THREE.Color(0xffffff),Math.random()*.3);col.set([c.r,c.g,c.b],i*3);}
const pg=new THREE.BufferGeometry();pg.setAttribute('position',new THREE.BufferAttribute(pos,3));pg.setAttribute('color',new THREE.BufferAttribute(col,3));
const galaxy=new THREE.Points(pg,new THREE.PointsMaterial({size:.045,vertexColors:true,transparent:true,opacity:.85,blending:THREE.AdditiveBlending,depthWrite:false}));
galaxy.rotation.x=.25;root.add(galaxy);

/* neon stadium floor: scrolling shader grid */
const floorMat=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{t:{value:0}},
  vertexShader:`varying vec2 vU;void main(){vU=uv;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
  fragmentShader:`uniform float t;varying vec2 vU;void main(){vec2 g=vU*vec2(40.,40.);g.y+=t*1.5;
    float l=max(smoothstep(.95,1.,fract(g.x)),smoothstep(.95,1.,fract(g.y)));
    float fade=smoothstep(.0,.5,vU.y)*smoothstep(1.,.55,vU.y)*(1.-abs(vU.x-.5)*1.6);
    vec3 c=mix(vec3(.78,1.,.24),vec3(.24,.96,1.),vU.x);gl_FragColor=vec4(c,l*fade*.55);}`});
const floor=new THREE.Mesh(new THREE.PlaneGeometry(60,60),floorMat);floor.rotation.x=-Math.PI/2;floor.position.y=-2.6;S.add(floor);

/* light streaks (running lanes) */
const streaks=[];for(let i=0;i<26;i++){const m=new THREE.Mesh(new THREE.BoxGeometry(.03,.03,1.6+Math.random()*2.5),
  new THREE.MeshBasicMaterial({color:[0xC6FF3D,0x3DF5FF,0xFF3DAE][i%3],transparent:true,opacity:.9}));
  m.position.set((Math.random()-.5)*26,-2.5+Math.random()*.2,-40+Math.random()*50);m.userData.v=.25+Math.random()*.5;S.add(m);streaks.push(m);}

/* shockwave on click */
const waves=[];wrap.addEventListener('pointerdown',()=>{const w=new THREE.Mesh(new THREE.RingGeometry(1.7,1.78,96),
  new THREE.MeshBasicMaterial({color:0xC6FF3D,transparent:true,opacity:1,side:THREE.DoubleSide}));
  w.lookAt(C.position);root.add(w);waves.push(w);core.scale.setScalar(1.25);});

const comp=new EffectComposer(R);comp.addPass(new RenderPass(S,C));
const bloom=new UnrealBloomPass(new THREE.Vector2(1,1),.8,.45,.2);comp.addPass(bloom);comp.addPass(new OutputPass());

let mx=0,my=0;addEventListener('pointermove',e=>{mx=e.clientX/innerWidth-.5;my=e.clientY/innerHeight-.5;});
function rs(){const w=wrap.clientWidth,h=wrap.clientHeight;R.setSize(w,h);comp.setSize(w,h);C.aspect=w/h;C.updateProjectionMatrix();root.position.x=off();}
addEventListener('resize',rs);rs();
const clk=new THREE.Clock();
(function loop(){const t=clk.getElapsedTime();
  coreMat.uniforms.t.value=t;floorMat.uniforms.t.value=t;
  wire.rotation.y=nodes.rotation.y=t*.25;wire.rotation.x=nodes.rotation.x=Math.sin(t*.3)*.3;
  inner.rotation.y=-t*.8;inner.rotation.z=t*.5;
  core.scale.lerp(new THREE.Vector3(1,1,1).multiplyScalar(1+Math.sin(t*2)*.02),.08);
  rings.forEach((g,i)=>g.rotation.z=t*(.3+i*.15)*(i%2?-1:1));
  galaxy.rotation.y=t*.03;
  streaks.forEach(s=>{s.position.z+=s.userData.v;if(s.position.z>12)s.position.z=-40;});
  for(let i=waves.length-1;i>=0;i--){const w=waves[i];w.scale.multiplyScalar(1.045);w.material.opacity*=.94;if(w.material.opacity<.02){root.remove(w);waves.splice(i,1);}}
  C.position.x+=(mx*2.2-C.position.x)*.04;C.position.y+=(1.2-my*1.4-C.position.y)*.04;C.lookAt(root.position.x*.55,0,0);
  comp.render();requestAnimationFrame(loop);})();
</script></body></html>
"""


def hero_html(subtitle: str, stats: tuple[int, int, int]) -> str:
    return HERO_TEMPLATE.replace("__SUB__", subtitle).replace("__STATS__", json.dumps(list(stats)))
