"""Global 'Neon Stadium' design system injected into Streamlit."""

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@400;600;800;900&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

:root{
  --bg:#05070F; --bg2:#0A0F22; --ink:#E9F0FF; --mute:#8B97B8;
  --lime:#C6FF3D; --cyan:#3DF5FF; --pink:#FF3DAE; --violet:#9D7BFF; --amber:#FFB13D;
  --glass:rgba(14,20,44,.55); --stroke:rgba(255,255,255,.09);
  --r:22px;
}
@property --a{syntax:'<angle>';initial-value:0deg;inherits:false}
@property --n{syntax:'<integer>';initial-value:0;inherits:false}

html{background:var(--bg)!important}body{background:transparent!important}
.stApp{background:
  radial-gradient(1200px 600px at 10% -10%,rgba(157,123,255,.18),transparent 60%),
  radial-gradient(900px 500px at 100% 0%,rgba(61,245,255,.12),transparent 60%),
  radial-gradient(800px 600px at 50% 120%,rgba(198,255,61,.08),transparent 60%),
  transparent!important;color:var(--ink);font-family:'Space Grotesk',Inter,sans-serif}
.stApp::after{content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.07;mix-blend-mode:overlay;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='3'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");}
[data-testid="stHeader"]{background:transparent!important;backdrop-filter:none}
[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:transparent!important}
.block-container{padding-top:2.2rem!important;max-width:1320px!important;position:relative;z-index:2}
h1,h2,h3,h4{font-family:'Unbounded',sans-serif!important;letter-spacing:-.02em;color:var(--ink)!important}
p,li,label,span,div{font-family:'Space Grotesk',Inter,sans-serif}
code,pre{font-family:'JetBrains Mono',monospace!important}
::selection{background:var(--lime);color:#000}
::-webkit-scrollbar{width:10px;height:10px}::-webkit-scrollbar-track{background:#05070F}
::-webkit-scrollbar-thumb{background:linear-gradient(var(--cyan),var(--violet));border-radius:10px}

/* hide 0-height FX iframes */
.element-container:has(> iframe[height="0"]),.stElementContainer:has(iframe[height="0"]),
.stElementContainer:has(> .stHtml .cb-fx){position:absolute!important;height:0!important;overflow:hidden!important;margin:0!important}

/* ── Sidebar ───────────────────────────── */
[data-testid="stSidebar"]{background:linear-gradient(180deg,rgba(10,14,34,.92),rgba(5,7,15,.96))!important;
  border-right:1px solid transparent;border-image:linear-gradient(180deg,var(--lime),var(--violet),transparent) 1;
  backdrop-filter:blur(18px)}
[data-testid="stSidebar"] *{color:var(--ink)}
[data-testid="stSidebar"] h3{font-size:.8rem!important;letter-spacing:.18em;text-transform:uppercase;color:var(--lime)!important;margin-top:.6rem}
.cb-logo{display:flex;align-items:center;gap:.8rem;margin:.2rem 0 1rem}
.cb-logo-orb{width:46px;height:46px;border-radius:14px;position:relative;
  background:conic-gradient(from var(--a),var(--lime),var(--cyan),var(--violet),var(--pink),var(--lime));
  animation:spin 4s linear infinite;box-shadow:0 0 30px rgba(198,255,61,.35)}
.cb-logo-orb::after{content:"⚡";position:absolute;inset:3px;border-radius:11px;background:#070A18;display:grid;place-items:center;font-size:1.3rem}
.cb-logo b{font-family:'Unbounded';font-size:1.15rem;letter-spacing:-.02em;display:block}
.cb-logo small{font-family:'JetBrains Mono';font-size:.62rem;letter-spacing:.2em;color:var(--mute)}
@keyframes spin{to{--a:360deg}}

/* XP / level card */
.cb-xp{padding:14px 16px;border-radius:18px;background:var(--glass);border:1px solid var(--stroke);margin-bottom:.6rem;position:relative;overflow:hidden}
.cb-xp-top{display:flex;justify-content:space-between;align-items:baseline;font-family:'JetBrains Mono';font-size:.72rem;color:var(--mute)}
.cb-xp-top b{font-family:'Unbounded';font-size:1.05rem;color:var(--lime)}
.cb-xp-bar{height:10px;border-radius:99px;background:rgba(255,255,255,.07);margin-top:9px;overflow:hidden}
.cb-xp-bar i{display:block;height:100%;border-radius:99px;
  background:repeating-linear-gradient(45deg,var(--lime) 0 10px,#9BE01E 10px 20px);background-size:28px 28px;
  animation:stripes 1s linear infinite,grow 1.2s cubic-bezier(.2,.9,.2,1) both;box-shadow:0 0 18px var(--lime)}
.cb-badges{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.cb-badge{font-size:1.05rem;width:32px;height:32px;display:grid;place-items:center;border-radius:10px;
  background:rgba(255,255,255,.05);border:1px solid var(--stroke);filter:grayscale(1) opacity(.35);transition:.3s}
.cb-badge.on{filter:none;border-color:rgba(198,255,61,.5);box-shadow:0 0 14px rgba(198,255,61,.35);animation:pop .6s both}
@keyframes stripes{to{background-position:28px 0}}
@keyframes grow{from{width:0}}
@keyframes pop{0%{transform:scale(.3)}70%{transform:scale(1.2)}100%{transform:scale(1)}}

/* ── Inputs ───────────────────────────── */
.stTextInput input,.stNumberInput input,.stTextArea textarea,[data-baseweb="select"]>div,[data-baseweb="input"]{
  background:rgba(8,12,30,.7)!important;border:1px solid var(--stroke)!important;border-radius:14px!important;color:var(--ink)!important;transition:.25s}
.stTextInput input:focus,.stTextArea textarea:focus,[data-baseweb="select"]>div:focus-within{
  border-color:var(--cyan)!important;box-shadow:0 0 0 3px rgba(61,245,255,.15),0 0 24px rgba(61,245,255,.2)!important}
[data-baseweb="tag"]{background:linear-gradient(90deg,rgba(198,255,61,.2),rgba(61,245,255,.2))!important;border:1px solid rgba(198,255,61,.4)!important}
[data-baseweb="popover"] ul{background:#0B1124!important}
[data-testid="stSlider"] [role="slider"]{background:var(--lime)!important;box-shadow:0 0 0 6px rgba(198,255,61,.18),0 0 18px var(--lime)}
[data-testid="stExpander"]{background:var(--glass);border:1px solid var(--stroke)!important;border-radius:16px!important}

/* ── Buttons ──────────────────────────── */
.stButton>button,.stDownloadButton>button,.stFormSubmitButton>button{
  border-radius:14px!important;font-family:'Space Grotesk'!important;font-weight:700!important;letter-spacing:.02em;
  background:rgba(255,255,255,.04)!important;border:1px solid var(--stroke)!important;color:var(--ink)!important;
  position:relative;overflow:hidden;transition:transform .2s,box-shadow .3s,border-color .3s}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--cyan)!important;box-shadow:0 0 24px rgba(61,245,255,.25);transform:translateY(-2px)}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primary"],button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(110deg,var(--lime),#7CFFB2 45%,var(--cyan))!important;color:#03060E!important;border:none!important;
  box-shadow:0 10px 40px -10px rgba(198,255,61,.65)}
.stButton>button[kind="primary"]::after,button[data-testid="stBaseButton-primary"]::after{content:"";position:absolute;inset:0;
  background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,.75) 50%,transparent 70%);transform:translateX(-120%);animation:shine 2.8s infinite}
.stButton>button[kind="primary"] p,button[data-testid="stBaseButton-primary"] p{color:#03060E!important;font-weight:800}
@keyframes shine{60%,100%{transform:translateX(120%)}}

/* ── Tabs (Streamlit ≥1.60 react-aria markup + legacy baseweb) ── */
.stTabs [role="tablist"]{gap:6px;background:rgba(8,12,30,.6);padding:6px;border-radius:18px;border:1px solid var(--stroke);
  backdrop-filter:blur(14px);width:fit-content;max-width:100%;overflow-x:auto;margin-bottom:1rem}
.stTabs [role="tab"]{border-radius:13px!important;padding:10px 18px!important;height:auto!important;background:transparent;transition:.25s;cursor:pointer}
.stTabs [role="tab"] p{font-family:'Unbounded'!important;font-size:.78rem!important;letter-spacing:.02em;color:var(--mute)!important;white-space:nowrap}
.stTabs [role="tab"]:hover{background:rgba(255,255,255,.05)}
.stTabs [role="tab"]:hover p{color:var(--ink)!important}
.stTabs [role="tab"][aria-selected="true"]{background:linear-gradient(110deg,var(--lime),var(--cyan))!important;box-shadow:0 6px 30px -6px rgba(198,255,61,.6)}
.stTabs [role="tab"][aria-selected="true"] p{color:#03060E!important;font-weight:800}
.stTabs .react-aria-SelectionIndicator,.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none!important}

/* segmented control / pills */
[data-testid="stButtonGroup"] button{border-radius:12px!important;background:rgba(255,255,255,.04)!important;border:1px solid var(--stroke)!important}
[data-testid="stButtonGroup"] button[aria-checked="true"],[data-testid="stButtonGroup"] button[kind*="Active"]{
  background:linear-gradient(110deg,rgba(198,255,61,.25),rgba(61,245,255,.25))!important;border-color:var(--lime)!important;box-shadow:0 0 18px rgba(198,255,61,.3)}

/* metrics, dataframes, alerts */
[data-testid="stMetric"]{background:var(--glass);border:1px solid var(--stroke);border-radius:18px;padding:14px 18px}
[data-testid="stMetricValue"]{font-family:'Unbounded'!important;color:var(--lime)!important}
[data-testid="stDataFrame"]{border-radius:16px;overflow:hidden;border:1px solid var(--stroke)}
[data-testid="stAlert"]{border-radius:16px!important;backdrop-filter:blur(10px)}
[data-testid="stPlotlyChart"]{background:var(--glass);border:1px solid var(--stroke);border-radius:var(--r);padding:6px;backdrop-filter:blur(10px)}

/* ── Typography helpers ───────────────── */
.cb-kicker{font-family:'JetBrains Mono';font-size:.72rem;letter-spacing:.28em;text-transform:uppercase;color:var(--lime);
  display:inline-flex;align-items:center;gap:.6rem}
.cb-kicker::before{content:"";width:28px;height:2px;background:var(--lime);box-shadow:0 0 10px var(--lime)}
.cb-h{font-family:'Unbounded';font-weight:900;font-size:clamp(1.8rem,3.6vw,3.2rem);line-height:1.02;letter-spacing:-.04em;margin:.4rem 0 .6rem;
  background:linear-gradient(100deg,#fff 0%,#fff 35%,var(--lime) 50%,#fff 65%,#fff 100%);background-size:250% 100%;
  -webkit-background-clip:text;background-clip:text;color:transparent;animation:sheen 6s ease-in-out infinite}
.cb-sub{color:var(--mute);font-size:1.05rem;max-width:720px}
@keyframes sheen{0%,100%{background-position:100% 0}50%{background-position:0 0}}

/* ── Cards ────────────────────────────── */
.cb-card{position:relative;border-radius:var(--r);padding:22px;background:var(--glass);border:1px solid var(--stroke);
  backdrop-filter:blur(16px);overflow:hidden;isolation:isolate}
.cb-beam::before{content:"";position:absolute;inset:-1px;border-radius:inherit;padding:1.5px;z-index:-1;
  background:conic-gradient(from var(--a),transparent 0 70%,var(--c,var(--lime)) 80%,transparent 90%);
  -webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;
  animation:spin 5s linear infinite}
.cb-tilt{transform-style:preserve-3d;transition:transform .25s cubic-bezier(.2,.9,.2,1),box-shadow .3s;will-change:transform}
.cb-tilt::after{content:"";position:absolute;inset:0;border-radius:inherit;pointer-events:none;opacity:0;transition:opacity .3s;
  background:radial-gradient(420px circle at var(--mx,50%) var(--my,50%),rgba(255,255,255,.13),transparent 45%)}
.cb-tilt:hover::after{opacity:1}
.cb-tilt:hover{box-shadow:0 30px 80px -30px var(--c,rgba(198,255,61,.5))}

.cb-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin:1rem 0 2rem}
.cb-feat{min-height:190px;display:flex;flex-direction:column;gap:8px;animation:rise .8s cubic-bezier(.2,.9,.2,1) both}
.cb-feat .e{font-size:2rem;width:58px;height:58px;display:grid;place-items:center;border-radius:16px;
  background:radial-gradient(circle at 30% 30%,color-mix(in srgb,var(--c) 45%,transparent),transparent 70%),rgba(255,255,255,.04);
  border:1px solid color-mix(in srgb,var(--c) 40%,transparent);transform:translateZ(40px)}
.cb-feat h4{font-size:1rem!important;margin:6px 0 0!important;transform:translateZ(30px)}
.cb-feat p{color:var(--mute);font-size:.9rem;margin:0;transform:translateZ(20px)}
.cb-feat .tag{margin-top:auto;font-family:'JetBrains Mono';font-size:.66rem;letter-spacing:.14em;color:var(--c);display:flex;justify-content:space-between}
@keyframes rise{from{opacity:0;transform:translateY(40px) scale(.96)}to{opacity:1;transform:none}}

/* stat tickers */
.cb-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:1.2rem 0}
.cb-stat{padding:18px 20px}
.cb-stat .v{font-family:'Unbounded';font-weight:800;font-size:2.3rem;color:var(--c,var(--lime));counter-reset:n var(--n);
  animation:count 2.4s cubic-bezier(.2,.9,.2,1) forwards;text-shadow:0 0 30px color-mix(in srgb,var(--c,var(--lime)) 60%,transparent)}
.cb-stat .v::before{content:counter(n)}
.cb-stat .l{color:var(--mute);font-size:.82rem;font-family:'JetBrains Mono';letter-spacing:.08em;text-transform:uppercase}
@keyframes count{from{--n:0}to{--n:var(--to)}}

/* marquee */
.cb-marquee{overflow:hidden;border-block:1px solid var(--stroke);padding:14px 0;margin:1.5rem 0;
  mask-image:linear-gradient(90deg,transparent,#000 10%,#000 90%,transparent)}
.cb-marquee .t{display:flex;gap:48px;width:max-content;animation:marq 38s linear infinite}
.cb-marquee span{font-family:'Unbounded';font-weight:800;font-size:1.6rem;white-space:nowrap;color:transparent;-webkit-text-stroke:1px rgba(233,240,255,.35)}
.cb-marquee span:nth-child(3n){color:var(--lime);-webkit-text-stroke:0;text-shadow:0 0 20px rgba(198,255,61,.5)}
@keyframes marq{to{transform:translateX(-50%)}}

/* pipeline */
.cb-flow{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:1rem 0 2rem;position:relative}
.cb-step{padding:18px;text-align:left}
.cb-step .n{font-family:'JetBrains Mono';color:var(--c);font-size:.75rem;letter-spacing:.2em}
.cb-step b{display:block;font-family:'Unbounded';font-size:.95rem;margin:.4rem 0}
.cb-step small{color:var(--mute)}
.cb-step .bar{height:3px;border-radius:3px;margin-top:12px;background:linear-gradient(90deg,var(--c),transparent);background-size:200% 100%;animation:flow 2s linear infinite}
@keyframes flow{from{background-position:200% 0}to{background-position:0 0}}

/* feature header in coach tab */
.cb-fhead{display:flex;gap:18px;align-items:center;padding:20px 24px;margin:.4rem 0 1rem}
.cb-fhead .e{font-size:2.6rem;filter:drop-shadow(0 0 16px var(--c))}
.cb-fhead h3{margin:0!important;font-size:1.4rem!important}
.cb-fhead p{margin:.2rem 0 0;color:var(--mute)}
.cb-chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:.6rem}
.cb-chip{font-family:'JetBrains Mono';font-size:.7rem;padding:5px 10px;border-radius:99px;border:1px solid var(--stroke);background:rgba(255,255,255,.04);color:var(--ink)}
.cb-chip.hot{border-color:var(--c);color:var(--c)}

/* ── Result rendering ─────────────────── */
.cb-result-hero{padding:30px 32px;margin:1rem 0;animation:rise .9s both}
.cb-result-hero h2{font-size:clamp(1.4rem,2.6vw,2.2rem)!important;margin:.4rem 0!important;
  background:linear-gradient(100deg,var(--lime),var(--cyan) 50%,var(--violet));-webkit-background-clip:text;background-clip:text;color:transparent!important}
.cb-result-hero p{color:#C9D3EE;font-size:1.05rem;margin:0}
.cb-status{font-family:'JetBrains Mono';font-size:.68rem;letter-spacing:.2em;padding:5px 11px;border-radius:99px;display:inline-block}
.cb-status.live{background:rgba(198,255,61,.12);color:var(--lime);border:1px solid rgba(198,255,61,.4)}
.cb-status.demo{background:rgba(61,245,255,.1);color:var(--cyan);border:1px solid rgba(61,245,255,.35)}
.cb-secs{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin:.6rem 0 1rem}
.cb-sec{animation:rise .8s both}
.cb-sec h4{font-size:.95rem!important;display:flex;gap:10px;align-items:center;margin:0 0 .6rem!important}
.cb-sec h4 span{font-size:1.4rem}
.cb-sec ul{margin:0;padding-left:0;list-style:none}
.cb-sec li{position:relative;padding:7px 0 7px 22px;color:#D3DBF2;font-size:.93rem;border-bottom:1px dashed rgba(255,255,255,.06)}
.cb-sec li:last-child{border-bottom:none}
.cb-sec li::before{content:"";position:absolute;left:2px;top:14px;width:8px;height:8px;border-radius:2px;transform:rotate(45deg);background:var(--c);box-shadow:0 0 10px var(--c)}
.cb-coach{display:flex;gap:16px;align-items:center;padding:18px 22px;margin:1rem 0;animation:rise 1s .3s both}
.cb-coach .av{width:54px;height:54px;flex:none;border-radius:50%;display:grid;place-items:center;font-size:1.6rem;
  background:conic-gradient(from var(--a),var(--lime),var(--cyan),var(--pink),var(--lime));animation:spin 3s linear infinite;position:relative}
.cb-coach .av::after{content:"🤖";position:absolute;inset:3px;border-radius:50%;background:#070A18;display:grid;place-items:center}
.cb-coach q{font-family:'Unbounded';font-size:1.05rem;quotes:"“" "”"}
.cb-safety{border-left:3px solid var(--amber);padding:16px 20px;margin:1rem 0;background:linear-gradient(90deg,rgba(255,177,61,.08),transparent)}
.cb-safety b{color:var(--amber);font-family:'Unbounded';font-size:.85rem;letter-spacing:.06em}
.cb-safety li{color:#E8DCC6;font-size:.9rem;margin:.25rem 0}
.cb-block{padding:28px;text-align:center;border:1px solid rgba(255,61,110,.5);background:radial-gradient(circle at 50% 0,rgba(255,61,110,.18),transparent 70%),var(--glass)}
.cb-block h3{color:#FF8FB0!important}

/* loader */
.cb-loader{display:flex;flex-direction:column;align-items:center;gap:18px;padding:40px}
.cb-loader .rings{width:90px;height:90px;position:relative}
.cb-loader .rings i{position:absolute;inset:0;border-radius:50%;border:3px solid transparent;border-top-color:var(--lime);animation:rot 1s linear infinite}
.cb-loader .rings i:nth-child(2){inset:12px;border-top-color:var(--cyan);animation-duration:1.4s;animation-direction:reverse}
.cb-loader .rings i:nth-child(3){inset:24px;border-top-color:var(--pink);animation-duration:.8s}
.cb-loader span{font-family:'JetBrains Mono';letter-spacing:.25em;font-size:.75rem;color:var(--mute);animation:blink 1.2s infinite}
@keyframes rot{to{transform:rotate(360deg)}}
@keyframes blink{50%{opacity:.35}}

/* prompt viewer */
.cb-code{font-family:'JetBrains Mono';font-size:.78rem;white-space:pre-wrap;color:#B9C6EA;background:rgba(3,5,12,.8);
  border:1px solid var(--stroke);border-radius:14px;padding:16px;max-height:380px;overflow:auto}
.cb-ver{display:flex;gap:12px;align-items:flex-start;padding:10px 0;border-bottom:1px dashed var(--stroke)}
.cb-ver b{font-family:'JetBrains Mono';color:var(--lime);min-width:34px}
.cb-ver span{color:#C9D3EE;font-size:.9rem}

.cb-foot{margin-top:3rem;padding:22px;text-align:center;color:var(--mute);font-size:.8rem;font-family:'JetBrains Mono';border-top:1px solid var(--stroke)}

@media (max-width:768px){
  .block-container{padding:1.2rem .8rem!important}
  .stTabs [role="tab"]{padding:8px 11px!important}
  .stTabs [role="tab"] p{font-size:.66rem!important}
  .cb-stat .v{font-size:1.7rem}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""
