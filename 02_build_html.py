"""
02_build_html.py
Reads the synthetic CSVs, assembles a JSON payload, injects it into a single
self-contained, noindex, mobile-responsive index.html (vanilla JS + hand-rolled SVG).
No external assets, no identifying business context.
"""
import pandas as pd, json, os

OUT = os.path.dirname(os.path.abspath(__file__))
cells = pd.read_csv(f"{OUT}/cells.csv")
cat   = pd.read_csv(f"{OUT}/category.csv")
brands= pd.read_csv(f"{OUT}/brands.csv")
drv   = pd.read_csv(f"{OUT}/drivers.csv")
media = pd.read_csv(f"{OUT}/media.csv")
copies= pd.read_csv(f"{OUT}/copies.csv")
dist  = pd.read_csv(f"{OUT}/distribution.csv")
vpm   = pd.read_csv(f"{OUT}/vpm.csv")
eras  = pd.read_csv(f"{OUT}/eras.csv")

years = cat.year.tolist()
CELLS = ['BS','BB','PS','PB']
cell_label = {'BS':'Base · Small','BB':'Base · Big','PS':'Premium · Small','PB':'Premium · Big'}

# value share per cell per year (for mix area)
cell_vshare = {c: [] for c in CELLS}
for y in years:
    tot = cells[cells.year==y].value.sum()
    for c in CELLS:
        v = cells[(cells.year==y)&(cells.cell==c)].value.iloc[0]
        cell_vshare[c].append(round(v/tot*100,2))

BRANDS = ['Auria','Nello','Pavo','Mercato PL']
brand_share = {b: brands[brands.brand==b].sort_values('year').value_share.tolist() for b in BRANDS}

BENEFITS = ["Value & Longevity","Everyday Performance","Hygiene & Protection","Premium Care","Smart Value"]
gyears = sorted(media.year.unique().tolist())
media_share = {bs: [] for bs in BENEFITS}
for y in gyears:
    for bs in BENEFITS:
        row = media[(media.year==y)&(media.benefit_space==bs)]
        media_share[bs].append(int(row.share.iloc[0]) if len(row) else 0)
grp_total = [int(media[media.year==y].grp.sum()) for y in gyears]

# era-level leader contribution vs fair share
catval = {y: cat[cat.year==y].value.iloc[0] for y in years}
aur = {y: brands[(brands.brand=='Auria')&(brands.year==y)].value.iloc[0] for y in years}
aur_sh = {y: brand_share['Auria'][years.index(y)] for y in years}
era_fair = []
for _,r in eras.iterrows():
    s,e = int(r.start), int(r.end)
    dcat = catval[e]-catval[s-1]
    daur = aur[e]-aur[s-1]
    contrib = round(daur/dcat*100,1) if dcat else 0
    avgshare = round(sum(aur_sh[y] for y in range(s,e+1))/(e-s+1),1)
    era_fair.append(dict(era=r.era,label=r.label,contrib=contrib,share=avgshare,gap=round(contrib-avgshare,1)))

DATA = dict(
    years=years, gyears=gyears,
    category=dict(
        units=cat.units.tolist(), value=cat.value.round(0).tolist(),
        value_index=[round(v/cat.value.iloc[0]*100,1) for v in cat.value],
        vol_index=[round(u/cat.units.iloc[0]*100,1) for u in cat.units],
        price_index=cat.price_index.tolist(), cpi_index=cat.cpi_index.round(1).tolist(),
        units_mult=round(cat.units.iloc[-1]/cat.units.iloc[0],1),
    ),
    cells=dict(order=CELLS, label=cell_label, vshare=cell_vshare),
    brands=dict(order=BRANDS, share=brand_share),
    drivers=dict(penetration=drv.penetration.tolist(), consumption=drv.consumption.tolist(),
                 premiumization=drv.premiumization.tolist()),
    media=dict(benefits=BENEFITS, share=media_share, grp_total=grp_total),
    distribution=dict(nd=dist.numeric_distribution.tolist(), tdp=dist.tdp_index.tolist()),
    vpm=vpm.to_dict('records'),
    eras=eras.to_dict('records'),
    era_fair=era_fair,
)

# ---- per-era vector evidence (why E2 fired across all five) ----
def yv(yrs, vals): return {int(y): v for y, v in zip(yrs, vals)}
port_y = yv(years, drv.portfolio_breadth.tolist())
grp_y  = yv(gyears, grp_total)
tdp_y  = yv(years, dist.tdp_index.tolist())
vl_y   = yv(gyears, media_share['Value & Longevity'])
def cagr(d, s, e):
    s = max(s, min(d)); e = min(e, max(d))
    return round(((d[e]/d[s])**(1/(e-s))-1)*100, 1)
vec = dict(portfolio=[], media=[], distribution=[], comms=[], pricing=[])
for r in eras.itertuples():
    s, e = int(r.start), int(r.end)
    vec['portfolio'].append(cagr(port_y, s, e))
    vec['media'].append(cagr(grp_y, s, e))
    vec['distribution'].append(cagr(tdp_y, s, e))
    yy = [y for y in gyears if s <= y <= e]
    vec['comms'].append(round(sum(vl_y[y] for y in yy)/len(yy)))
vec['pricing'] = [v['price_vs_inflation'] for v in vpm.to_dict('records')]
DATA['portfolio'] = drv.portfolio_breadth.tolist()
DATA['skus'] = dict(entry=drv.entry_skus.tolist(), premium=drv.premium_skus.tolist())
DATA['vectors'] = vec

TPL = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Category Growth Codification Console</title>
<style>
:root{
  --ink:#15171C; --paper:#FFFFFF; --panel:#F2F4F7; --line:#E3E6EC; --muted:#6B7280;
  --teal:#0E7C66; --teal-l:#5EAD9B; --indigo:#4338CA; --indigo-l:#8E97E8;
  --slate:#64748B; --clay:#C2410C; --gold:#B45309;
  --maxw:1080px;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--panel);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.5;-webkit-font-smoothing:antialiased}
.mono{font-family:"SF Mono",ui-monospace,"JetBrains Mono",Menlo,Consolas,monospace;
  font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 20px}

header.top{background:var(--ink);color:#fff;padding:26px 0 0}
.eyebrow{font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:#9aa3b2;font-weight:600}
header.top h1{font-size:26px;font-weight:700;letter-spacing:-.02em;margin:6px 0 4px}
header.top p.sub{margin:0 0 18px;color:#c5ccd8;font-size:13.5px;max-width:640px}
nav.tabs{display:flex;gap:0;flex-wrap:wrap;border-top:1px solid #2a2e38}
nav.tabs button{flex:1 1 auto;min-width:150px;background:none;border:none;color:#9aa3b2;cursor:pointer;
  padding:14px 12px;font-size:13px;font-weight:600;border-bottom:2px solid transparent;text-align:left;
  font-family:inherit;transition:color .15s}
nav.tabs button .n{font-size:10px;letter-spacing:.18em;display:block;color:#5f6776;margin-bottom:3px}
nav.tabs button:hover{color:#dfe4ec}
nav.tabs button[aria-selected=true]{color:#fff;border-bottom-color:var(--teal-l)}
nav.tabs button[aria-selected=true] .n{color:var(--teal-l)}

main{padding:28px 0 64px}
.panelpage{display:none;animation:fade .25s ease}
.panelpage.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.lead{font-size:15px;color:#3b3f48;max-width:680px;margin:0 0 22px}
.lead b{color:var(--ink)}

.eras-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:0 0 24px}
.era-card{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:13px 14px}
.era-card .tag{font-size:10px;letter-spacing:.14em;font-weight:700;text-transform:uppercase;color:var(--muted)}
.era-card .yr{font-size:11px;color:var(--muted);margin-top:1px}
.era-card .lbl{font-size:13px;font-weight:650;margin:7px 0 8px;min-height:34px}
.era-card .cagr{font-size:23px;font-weight:700;letter-spacing:-.02em}
.era-card .cagr small{font-size:11px;font-weight:600;color:var(--muted);letter-spacing:0}
.era-card .vol{font-size:11px;color:var(--muted);margin-top:2px}

.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}
.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.card.full{grid-column:1 / -1}
.card h3{margin:0 0 2px;font-size:14.5px;font-weight:650}
.card .cap{margin:0 0 12px;font-size:12px;color:var(--muted)}
.legend{display:flex;flex-wrap:wrap;gap:12px;margin-top:10px;font-size:11.5px;color:#3b3f48}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{width:11px;height:11px;border-radius:3px;display:inline-block}
.legend i.ln{height:3px;width:16px;border-radius:2px}
svg{width:100%;height:auto;display:block}
text{font-family:"SF Mono",ui-monospace,Menlo,Consolas,monospace}

.callout{background:#0E7C661a;border:1px solid #0E7C6644;border-left:4px solid var(--teal);
  border-radius:10px;padding:14px 16px;margin-top:4px}
.callout.warn{background:#C2410C14;border-color:#C2410C44;border-left-color:var(--clay)}
.callout .k{font-size:10px;letter-spacing:.16em;text-transform:uppercase;font-weight:700;color:var(--teal)}
.callout.warn .k{color:var(--clay)}
.callout p{margin:5px 0 0;font-size:13.5px;color:#26303a}
.callout.warn p{color:#3a2820}

.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}
.kpi{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:13px 14px}
.kpi .v{font-size:24px;font-weight:700;letter-spacing:-.02em}
.kpi .v.dn{color:var(--clay)} .kpi .v.up{color:var(--teal)}
.kpi .l{font-size:11px;color:var(--muted);margin-top:3px;line-height:1.35}

.vecgrid{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin-top:6px}
.vec .h{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;font-weight:700;color:var(--ink)}
.vec .d{font-size:11px;color:var(--muted);line-height:1.4;margin-top:7px}
@media(max-width:980px){.vecgrid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:560px){.vecgrid{grid-template-columns:repeat(2,1fr)}}

.recos{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px}
.reco{background:var(--paper);border:1px solid var(--line);border-radius:11px;padding:14px 16px;display:flex;gap:13px}
.reco .num{font-family:"SF Mono",ui-monospace,Menlo,monospace;font-size:12px;font-weight:700;color:var(--teal);
  border:1.5px solid var(--teal);border-radius:7px;width:30px;height:30px;display:flex;align-items:center;
  justify-content:center;flex:none}
.reco .vlab{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:700}
.reco h4{margin:3px 0 4px;font-size:13.5px}
.reco p{margin:0;font-size:12.5px;color:#3b3f48;line-height:1.45}

.compare{width:100%;border-collapse:collapse;margin-top:4px;font-size:13px}
.compare th{text-align:left;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);
  font-weight:700;padding:8px 10px;border-bottom:1px solid var(--line)}
.compare td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.compare td.who{font-weight:650}
.pill{display:inline-block;font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:20px}
.pill.up{background:#0E7C661a;color:var(--teal)} .pill.dn{background:#C2410C1a;color:var(--clay)}
.pill.fl{background:#64748b1a;color:var(--slate)}

footer{border-top:1px solid var(--line);padding:18px 0 40px;color:var(--muted);font-size:11.5px}
@media(max-width:760px){
  .grid{grid-template-columns:1fr}
  .eras-strip{grid-template-columns:1fr 1fr}
  .kpis{grid-template-columns:1fr 1fr}
  .vectors{grid-template-columns:1fr 1fr}
  .recos{grid-template-columns:1fr}
  .era-card .lbl{min-height:0}
}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <div class="eyebrow">P20Y Category Growth &middot; Decomposition Instrument</div>
  <h1>Category Growth Codification Console</h1>
  <p class="sub">Twenty years of an FMCG category, decomposed into growth eras, the volume/price/mix that built them, the demand vectors behind them, and where the landscape leaves the leader now. Synthetic illustrative data.</p>
  <nav class="tabs" role="tablist">
    <button role="tab" aria-selected="true" data-t="0"><span class="n">01 · WHAT HAPPENED</span>Category Growth</button>
    <button role="tab" aria-selected="false" data-t="1"><span class="n">02 · WHY IT WON</span>Growth Vectors</button>
    <button role="tab" aria-selected="false" data-t="2"><span class="n">03 · WHO WON</span>Share &amp; Contribution</button>
    <button role="tab" aria-selected="false" data-t="3"><span class="n">04 · SO WHAT</span>Now &amp; Outlook</button>
  </nav>
</div></header>

<main class="wrap">
  <!-- TAB 0 -->
  <section class="panelpage active" id="p0">
    <p class="lead">The category grew <b id="mult"></b> in volume over twenty years, but not evenly. Four eras tell different stories &mdash; and the volume/price/mix split reveals which growth was real demand versus inflation.</p>
    <div class="eras-strip" id="eraStrip"></div>
    <div class="grid">
      <div class="card full"><h3>Category trajectory &amp; growth eras</h3><p class="cap">Indexed to base year = 100. Volume vs value.</p><div id="c_traj"></div>
        <div class="legend"><span><i class="ln" style="background:var(--teal)"></i>Volume index</span><span><i class="ln" style="background:var(--indigo)"></i>Value index</span></div></div>
      <div class="card"><h3>Volume / price / mix by era</h3><p class="cap">Points of value CAGR. Bars sum to the era's value growth; the marker is total value CAGR.</p><div id="c_vpm"></div>
        <div class="legend"><span><i style="background:var(--teal)"></i>Volume</span><span><i style="background:var(--slate)"></i>Price</span><span><i style="background:var(--indigo)"></i>Mix</span><span><i style="background:var(--ink)"></i>Value CAGR</span></div></div>
      <div class="card"><h3>Pricing vs inflation</h3><p class="cap">Category price index against CPI. Gap below CPI = real accessibility.</p><div id="c_infl"></div>
        <div class="legend"><span><i class="ln" style="background:var(--clay)"></i>Category price</span><span><i class="ln" style="background:var(--muted)"></i>CPI</span></div></div>
    </div>
    <div class="callout"><span class="k">Read</span><p id="read0"></p></div>
  </section>

  <!-- TAB 1 -->
  <section class="panelpage" id="p1">
    <p class="lead">High-growth eras were <b>volume-led</b>, and that volume came from <b>penetration &mdash; new category users</b> &mdash; not from existing buyers spending more. Penetration was won by five vectors firing together.</p>
    <div class="grid">
      <div class="card"><h3>Demand driver tree</h3><p class="cap">Penetration, consumption per buyer, premiumization. Indexed to base = 100.</p><div id="c_drv"></div>
        <div class="legend"><span><i class="ln" style="background:var(--teal)"></i>Penetration</span><span><i class="ln" style="background:var(--indigo)"></i>Consumption/buyer</span><span><i class="ln" style="background:var(--gold)"></i>Premiumization</span></div></div>
      <div class="card"><h3>Tier &times; pack mix shift</h3><p class="cap">Value share of the four cells over time.</p><div id="c_mix"></div>
        <div class="legend" id="mixleg"></div></div>
    </div>
    <div style="margin:6px 0 12px"><h3 style="margin:0 0 3px;font-size:15px">How each vector moved &mdash; and how differently, era to era</h3>
      <p class="cap" style="font-size:12.5px">The actual in-process metric behind each vector across twenty years. Era bands carry each era's rate of change, so you see the shift in what was being done, not just the result. E2's band is tinted.</p></div>
    <div class="grid" id="vectors"></div>
    <div class="grid"><div class="card full"><h3>Comms vector &middot; benefit-space map</h3><p class="cap">The fifth vector, in process: share of media weight by benefit space, by year. Concentrated on one conversion message through E2, fragmented across spaces after.</p><div id="c_media"></div>
      <div class="legend" id="medleg"></div></div></div>
    <div class="callout"><span class="k">Read</span><p id="read1"></p></div>
  </section>

  <!-- TAB 2 -->
  <section class="panelpage" id="p2">
    <p class="lead">The leader <b>Auria</b> didn't just ride the category &mdash; it drove a disproportionate share of growth, pulling share from <b>46% to a 66% peak</b>. Then the curve turned.</p>
    <div class="grid">
      <div class="card full"><h3>Manufacturer value share</h3><p class="cap">Annual value share, four players.</p><div id="c_share"></div>
        <div class="legend" id="brleg"></div></div>
      <div class="card full"><h3>Contribution to growth vs fair share</h3><p class="cap">By era: Auria's share of category growth (bar) against its average market share (marker). Above the marker = winning more than its fair share.</p><div id="c_fair"></div>
        <div class="legend"><span><i style="background:var(--teal)"></i>Contribution to growth</span><span><i style="background:var(--ink)"></i>Avg market share (fair share)</span></div></div>
    </div>
    <div class="callout"><span class="k">Read</span><p id="read2"></p></div>
  </section>

  <!-- TAB 3 -->
  <section class="panelpage" id="p3">
    <p class="lead">Today the engine that built the category &mdash; penetration of the core tier &mdash; has <b>saturated</b>. Growth has cooled to low single digits, buyers are down-tiering, and the value entrant is back. Here's the contrast and what to do.</p>
    <div class="kpis" id="nowkpis"></div>
    <div class="grid">
      <div class="card"><h3>What changed</h3><p class="cap">The vectors that won, now turning.</p>
        <ul style="margin:6px 0 0;padding-left:18px;font-size:13px;color:#3b3f48;line-height:1.7" id="changed"></ul></div>
      <div class="card"><h3>Competitive read &mdash; now</h3><p class="cap">Where each player is pressing.</p>
        <table class="compare"><thead><tr><th>Player</th><th>Move</th><th>Trajectory</th></tr></thead><tbody id="comprows"></tbody></table></div>
    </div>
    <div class="card full" style="margin-bottom:16px"><h3>Recommendations to stay competitive</h3><p class="cap">Mapped to the five vectors, anchored to where the data turned.</p>
      <div class="recos" id="recos"></div></div>
    <div class="callout warn"><span class="k">Bottom line</span><p id="read3"></p></div>
  </section>
</main>

<footer class="wrap">Synthetic, illustrative dataset &mdash; no real brand, category, or figure. Built as a portfolio demonstration of category-growth decomposition. Tier (Base/Premium) &times; pack (Small/Big), four manufacturers, twenty years.</footer>

<script>
const D = /*__DATA__*/;
const C = {teal:'#0E7C66',tealL:'#5EAD9B',indigo:'#4338CA',indigoL:'#8E97E8',slate:'#64748B',clay:'#C2410C',gold:'#B45309',ink:'#15171C',muted:'#6B7280',line:'#E3E6EC'};
const CELLCOL={BS:C.teal,BB:C.tealL,PS:C.indigo,PB:C.indigoL};
const BRCOL={'Auria':C.teal,'Nello':C.slate,'Pavo':C.indigo,'Mercato PL':C.clay};
const BENCOL=[C.teal,C.tealL,C.slate,C.indigo,C.clay];
const Y=D.years, Y0=Y[0], Y1=Y[Y.length-1];

// ---- svg helpers ----
const W=760,H=380,M={l:54,r:18,t:26,b:34};
const IW=W-M.l-M.r, IH=H-M.t-M.b;
function sx(y){return M.l + (y-Y0)/(Y1-Y0)*IW;}
function svg(extra){return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="xMidYMid meet">${extra}</svg>`;}
function eraBands(){
  let s='';
  D.eras.forEach((e,i)=>{
    const x0=sx(e.start-0.5), x1=sx(e.end+0.5);
    s+=`<rect x="${x0}" y="${M.t}" width="${x1-x0}" height="${IH}" fill="${i%2?'#0E7C66':'#4338CA'}" opacity="0.04"/>`;
    s+=`<text x="${(x0+x1)/2}" y="${M.t-9}" text-anchor="middle" font-size="10" font-weight="700" fill="${C.muted}">${e.era}</text>`;
  });
  return s;
}
function xAxis(yPix){
  let s=`<line x1="${M.l}" y1="${yPix}" x2="${W-M.r}" y2="${yPix}" stroke="${C.line}"/>`;
  [2002,2007,2012,2017,2022].forEach(y=>{
    s+=`<text x="${sx(y)}" y="${yPix+15}" text-anchor="middle" font-size="10" fill="${C.muted}">'${String(y).slice(2)}</text>`;
  });
  return s;
}
function yGrid(vmin,vmax,yScale,fmt){
  let s='';const steps=4;
  for(let i=0;i<=steps;i++){
    const v=vmin+(vmax-vmin)*i/steps, yp=yScale(v);
    s+=`<line x1="${M.l}" y1="${yp}" x2="${W-M.r}" y2="${yp}" stroke="${C.line}" stroke-dasharray="2 3"/>`;
    s+=`<text x="${M.l-8}" y="${yp+3}" text-anchor="end" font-size="10" fill="${C.muted}">${fmt(v)}</text>`;
  }
  return s;
}
function linePath(vals,yScale){
  return vals.map((v,i)=>`${i?'L':'M'}${sx(Y[i]).toFixed(1)},${yScale(v).toFixed(1)}`).join(' ');
}

// ---- TAB 0 ----
function eraStrip(){
  document.getElementById('mult').textContent = D.category.units_mult+'x';
  document.getElementById('eraStrip').innerHTML = D.vpm.map(v=>`
    <div class="era-card"><div class="tag">${v.era} · ${v.label}</div><div class="yr">${v.start}–${v.end}</div>
    <div class="lbl">${v.label}</div>
    <div class="cagr">${v.value_cagr}%<small> value CAGR</small></div>
    <div class="vol">${v.volume_cagr}% volume · ${v.price_vs_inflation>=0?'+':''}${v.price_vs_inflation}pt vs CPI</div></div>`).join('');
}
function chartTraj(){
  const a=D.category.vol_index, b=D.category.value_index;
  const vmax=Math.max(...a,...b)*1.05, vmin=80;
  const ys=v=>M.t+IH-(v-vmin)/(vmax-vmin)*IH;
  let g=eraBands()+yGrid(vmin,vmax,ys,v=>Math.round(v));
  g+=`<path d="${linePath(a,ys)}" fill="none" stroke="${C.teal}" stroke-width="2.4"/>`;
  g+=`<path d="${linePath(b,ys)}" fill="none" stroke="${C.indigo}" stroke-width="2.4" stroke-dasharray="1 0"/>`;
  g+=xAxis(M.t+IH);
  document.getElementById('c_traj').innerHTML=svg(g);
}
function chartVPM(){
  const eras=D.vpm, n=eras.length, comps=[['volume_pts',C.teal],['price_pts',C.slate],['mix_pts',C.indigo]];
  let vmax=0,vmin=0;
  eras.forEach(e=>comps.forEach(([k])=>{vmax=Math.max(vmax,e[k],e.value_cagr);vmin=Math.min(vmin,e[k]);}));
  vmax=Math.ceil(vmax+1);vmin=Math.floor(vmin-0.5);
  const L=M.l,R=W-M.r,plotW=R-L, ys=v=>M.t+IH-(v-vmin)/(vmax-vmin)*IH;
  const gw=plotW/n, bw=gw*0.2;
  let g=yGrid(vmin,vmax,ys,v=>v.toFixed(0));
  g+=`<line x1="${L}" y1="${ys(0)}" x2="${R}" y2="${ys(0)}" stroke="${C.muted}"/>`;
  eras.forEach((e,i)=>{
    const cx=L+gw*(i+0.5);
    comps.forEach(([k,col],j)=>{
      const v=e[k], x=cx+(j-1)*bw-bw/2, y0=ys(0), y1=ys(v);
      g+=`<rect x="${x}" y="${Math.min(y0,y1)}" width="${bw}" height="${Math.abs(y1-y0)}" fill="${col}" rx="1.5"/>`;
    });
    g+=`<circle cx="${cx}" cy="${ys(e.value_cagr)}" r="4" fill="${C.ink}"/>`;
    g+=`<text x="${cx}" y="${ys(e.value_cagr)-9}" text-anchor="middle" font-size="10" font-weight="700" fill="${C.ink}">${e.value_cagr}</text>`;
    g+=`<text x="${cx}" y="${M.t+IH+15}" text-anchor="middle" font-size="10" fill="${C.muted}">${e.era}</text>`;
  });
  document.getElementById('c_vpm').innerHTML=svg(g);
}
function chartInfl(){
  const a=D.category.price_index, b=D.category.cpi_index;
  const vmax=Math.max(...a,...b)*1.04, vmin=95;
  const ys=v=>M.t+IH-(v-vmin)/(vmax-vmin)*IH;
  let g=eraBands()+yGrid(vmin,vmax,ys,v=>Math.round(v));
  g+=`<path d="${linePath(b,ys)}" fill="none" stroke="${C.muted}" stroke-width="2" stroke-dasharray="5 4"/>`;
  g+=`<path d="${linePath(a,ys)}" fill="none" stroke="${C.clay}" stroke-width="2.4"/>`;
  g+=xAxis(M.t+IH);
  document.getElementById('c_infl').innerHTML=svg(g);
}

// ---- TAB 1 ----
function chartDrv(){
  const ks=[['penetration',C.teal],['consumption',C.indigo],['premiumization',C.gold]];
  let all=[];ks.forEach(([k])=>all=all.concat(D.drivers[k]));
  const vmax=Math.max(...all)*1.04, vmin=Math.min(...all)*0.97;
  const ys=v=>M.t+IH-(v-vmin)/(vmax-vmin)*IH;
  let g=eraBands()+yGrid(vmin,vmax,ys,v=>Math.round(v));
  ks.forEach(([k,col])=>g+=`<path d="${linePath(D.drivers[k],ys)}" fill="none" stroke="${col}" stroke-width="2.4"/>`);
  g+=xAxis(M.t+IH);
  document.getElementById('c_drv').innerHTML=svg(g);
}
function chartMix(){
  const order=D.cells.order, ys=v=>M.t+IH-v/100*IH;
  let cum=Y.map(()=>0), g=yGrid(0,100,ys,v=>v+'%');
  order.forEach(c=>{
    const top=cum.map((b,i)=>b+D.cells.vshare[c][i]);
    let path=`M${sx(Y0)},${ys(cum[0])}`;
    Y.forEach((y,i)=>path+=`L${sx(y).toFixed(1)},${ys(top[i]).toFixed(1)}`);
    for(let i=Y.length-1;i>=0;i--)path+=`L${sx(Y[i]).toFixed(1)},${ys(cum[i]).toFixed(1)}`;
    path+='Z';
    g+=`<path d="${path}" fill="${CELLCOL[c]}" opacity="0.88"/>`;
    cum=top;
  });
  g+=xAxis(M.t+IH);
  document.getElementById('c_mix').innerHTML=svg(g);
  document.getElementById('mixleg').innerHTML=order.map(c=>`<span><i style="background:${CELLCOL[c]}"></i>${D.cells.label[c]}</span>`).join('');
}
function trendChart(o){
  const w=400,h=240,m={l:46,r:14,t:30,b:28}, iw=w-m.l-m.r, ih=h-m.t-m.b;
  const xs=y=>m.l+(y-Y0)/(Y1-Y0)*iw;
  const ys=v=>m.t+ih-(v-o.yMin)/(o.yMax-o.yMin)*ih;
  let g='';
  D.eras.forEach((e,i)=>{
    const x0=xs(e.start-0.5), x1=xs(e.end+0.5), isE2=i===1;
    g+=`<rect x="${x0}" y="${m.t}" width="${x1-x0}" height="${ih}" fill="${isE2?C.teal:'#94a3b8'}" opacity="${isE2?0.10:0.05}"/>`;
    g+=`<text x="${(x0+x1)/2}" y="${m.t-15}" text-anchor="middle" font-size="9.5" font-weight="700" fill="${isE2?C.teal:C.muted}">${e.era}</text>`;
    g+=`<text x="${(x0+x1)/2}" y="${m.t-4}" text-anchor="middle" font-size="10" font-weight="700" fill="${isE2?C.teal:C.slate}">${o.eraLabels[i]}</text>`;
  });
  for(let k=0;k<=3;k++){const v=o.yMin+(o.yMax-o.yMin)*k/3, yp=ys(v);
    g+=`<line x1="${m.l}" y1="${yp}" x2="${w-m.r}" y2="${yp}" stroke="${C.line}" stroke-dasharray="2 3"/>`;
    g+=`<text x="${m.l-6}" y="${yp+3}" text-anchor="end" font-size="9.5" fill="${C.muted}">${o.yFmt(v)}</text>`;}
  if(o.zeroLine){const yp=ys(0);g+=`<line x1="${m.l}" y1="${yp}" x2="${w-m.r}" y2="${yp}" stroke="${C.muted}" stroke-width="1"/>`;}
  [2002,2012,2022].forEach(y=>g+=`<text x="${xs(y)}" y="${h-8}" text-anchor="middle" font-size="9.5" fill="${C.muted}">'${String(y).slice(2)}</text>`);
  o.series.forEach(s=>{
    const pts=s.x.map((xx,i)=>[xs(xx),ys(s.y[i])]);
    if(s.fillToZero){let d=`M${pts[0][0].toFixed(1)},${ys(0)}`;pts.forEach(p=>d+=`L${p[0].toFixed(1)},${p[1].toFixed(1)}`);d+=`L${pts[pts.length-1][0].toFixed(1)},${ys(0)}Z`;
      g+=`<path d="${d}" fill="${s.color}" opacity="0.14"/>`;}
    g+=`<path d="${pts.map((p,i)=>`${i?'L':'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ')}" fill="none" stroke="${s.color}" stroke-width="${s.width||2.4}"${s.dash?` stroke-dasharray="${s.dash}"`:''}/>`;
  });
  return `<svg viewBox="0 0 ${w} ${h}" style="width:100%">${g}</svg>`;
}
function vectors(){
  const V=D.vectors, Y=D.years, GY=D.gyears, pe=a=>a.map(v=>(v>0?'+':'')+Math.round(v)+'%');
  const mx=a=>Math.max(...a), legrow=(arr)=>`<div class="legend">${arr.map(([c,t,ln])=>`<span><i class="${ln?'ln':''}" style="background:${c};${ln?'height:3px;width:16px':''}"></i>${t}</span>`).join('')}</div>`;
  // PORTFOLIO — entry vs premium SKUs actually in market
  const eS=D.skus.entry, pS=D.skus.premium, smax=mx(eS.concat(pS))*1.25;
  const port=trendChart({yMin:0,yMax:smax,yFmt:v=>Math.round(v),eraLabels:pe(V.portfolio),zeroLine:false,
    series:[{x:Y,y:eS,color:C.gold,width:2.6},{x:Y,y:pS,color:C.indigo,width:2.6}]});
  // MEDIA — GRP level
  const grp=D.media.grp_total;
  const media=trendChart({yMin:0,yMax:mx(grp)*1.12,yFmt:v=>Math.round(v/1000)+'k',eraLabels:pe(V.media),
    series:[{x:GY,y:grp,color:C.indigo,width:2.6,fillToZero:true}]});
  // PRICING — price index vs CPI, the gap is the story
  const pi=D.category.price_index, cpi=D.category.cpi_index, pmin=95, pmax=mx(pi.concat(cpi))*1.03;
  const pricing=trendChart({yMin:pmin,yMax:pmax,yFmt:v=>Math.round(v),
    eraLabels:V.pricing.map(v=>(v>0?'+':'')+v.toFixed(1)+'pt'),
    series:[{x:Y,y:cpi,color:C.muted,width:2,dash:'5 4'},{x:Y,y:pi,color:C.clay,width:2.6}]});
  // DISTRIBUTION — reach (ND) and shelf points (TDP), indexed to base
  const nd=D.distribution.nd, tdp=D.distribution.tdp, nd0=nd[0];
  const ndi=nd.map(v=>v/nd0*100);
  const dist=trendChart({yMin:90,yMax:mx(ndi.concat(tdp))*1.08,yFmt:v=>Math.round(v),eraLabels:pe(V.distribution),
    series:[{x:Y,y:ndi,color:C.teal,width:2.6},{x:Y,y:tdp,color:C.tealL,width:2.6,dash:'1 0'}]});
  const cards=[
    ['Portfolio','SKUs in market &mdash; entry vs premium',port,
      [[C.gold,'Entry (Base) packs',0],[C.indigo,'Premium packs',0]],
      'Entry packs were added fast in E2 to recruit new users; premium packs only multiplied in E3. The range you fielded was different in every era.'],
    ['Media','Media weight &mdash; GRP per year',media,[[C.indigo,'GRP',true]],
      'Spend sat low and flat through E1, then stepped up roughly 3x to carry the recruitment message in E2, plateaued in E3 and was pulled back in E4.'],
    ['Pricing','Category price index vs CPI',pricing,[[C.clay,'Category price',true],[C.muted,'CPI',true]],
      'Price tracked under inflation only in E2 &mdash; the lines split &mdash; keeping the category accessible during recruitment. From E3 price runs at or above CPI.'],
    ['Distribution','Reach vs shelf points (indexed)',dist,[[C.teal,'Numeric distribution',true],[C.tealL,'Shelf points (TDP)',true]],
      'Both reach and shelf points climbed steeply in E2; shelf points outran reach as pack-sizes multiplied. By E3 reach hit its ceiling and the curve flattens.'],
  ];
  document.getElementById('vectors').innerHTML=cards.map(([h,sub,svg,leg,d])=>`
    <div class="card"><h3>${h}</h3><p class="cap">${sub}</p>${svg}${legrow(leg)}<p class="d" style="font-size:11.5px;color:var(--muted);line-height:1.45;margin:10px 0 0">${d}</p></div>`).join('');
}
function chartMedia(){
  const gy=D.gyears, bens=D.media.benefits, n=gy.length;
  const L=M.l,R=W-M.r,plotW=R-L, ys=v=>M.t+IH-v/100*IH;
  const bw=plotW/n*0.74, step=plotW/n;
  let g=yGrid(0,100,ys,v=>v+'%');
  gy.forEach((y,i)=>{
    let base=0; const x=L+step*i+(step-bw)/2;
    bens.forEach((b,j)=>{
      const v=D.media.share[b][i], y1=ys(base+v), y0=ys(base);
      g+=`<rect x="${x}" y="${y1}" width="${bw}" height="${y0-y1}" fill="${BENCOL[j]}" opacity="0.9"/>`;
      base+=v;
    });
    if(i%3===0||i===n-1)g+=`<text x="${x+bw/2}" y="${M.t+IH+15}" text-anchor="middle" font-size="9" fill="${C.muted}">'${String(y).slice(2)}</text>`;
  });
  document.getElementById('c_media').innerHTML=svg(g);
  document.getElementById('medleg').innerHTML=bens.map((b,j)=>`<span><i style="background:${BENCOL[j]}"></i>${b}</span>`).join('');
}

// ---- TAB 2 ----
function chartShare(){
  const ord=D.brands.order;
  let all=[];ord.forEach(b=>all=all.concat(D.brands.share[b]));
  const vmax=Math.max(...all)*1.05, vmin=0;
  const ys=v=>M.t+IH-(v-vmin)/(vmax-vmin)*IH;
  let g=eraBands()+yGrid(vmin,vmax,ys,v=>Math.round(v)+'%');
  ord.forEach(b=>{
    g+=`<path d="${linePath(D.brands.share[b],ys)}" fill="none" stroke="${BRCOL[b]}" stroke-width="${b==='Auria'?3:2}"/>`;
  });
  g+=xAxis(M.t+IH);
  document.getElementById('c_share').innerHTML=svg(g);
  document.getElementById('brleg').innerHTML=ord.map(b=>`<span><i class="ln" style="background:${BRCOL[b]}"></i>${b}</span>`).join('');
}
function chartFair(){
  const ef=D.era_fair, n=ef.length;
  const vmax=Math.max(...ef.map(e=>Math.max(e.contrib,e.share)))*1.12;
  const L=M.l,R=W-M.r,plotW=R-L, ys=v=>M.t+IH-v/vmax*IH;
  const gw=plotW/n, bw=gw*0.4;
  let g=yGrid(0,vmax,ys,v=>Math.round(v)+'%');
  ef.forEach((e,i)=>{
    const cx=L+gw*(i+0.5), x=cx-bw/2, above=e.contrib>=e.share;
    g+=`<rect x="${x}" y="${ys(e.contrib)}" width="${bw}" height="${M.t+IH-ys(e.contrib)}" fill="${above?C.teal:C.clay}" rx="2"/>`;
    g+=`<text x="${cx}" y="${ys(e.contrib)-7}" text-anchor="middle" font-size="11" font-weight="700" fill="${above?C.teal:C.clay}">${e.contrib}%</text>`;
    // fair share marker
    g+=`<line x1="${x-6}" y1="${ys(e.share)}" x2="${x+bw+6}" y2="${ys(e.share)}" stroke="${C.ink}" stroke-width="2.4"/>`;
    g+=`<text x="${cx}" y="${M.t+IH+15}" text-anchor="middle" font-size="10" fill="${C.muted}">${e.era}</text>`;
  });
  document.getElementById('c_fair').innerHTML=svg(g);
}

// ---- TAB 3 ----
function nowTab(){
  const pen=D.drivers.penetration, sh=D.brands.share, mer=sh['Mercato PL'], aur=sh['Auria'];
  const lastE=D.vpm[3], penPeak=Math.max(...pen), penPeakYr=Y[pen.indexOf(penPeak)];
  const aurPeak=Math.max(...aur), aurNow=aur[aur.length-1];
  const merTrough=Math.min(...mer), merNow=mer[mer.length-1];
  document.getElementById('nowkpis').innerHTML=`
    <div class="kpi"><div class="v dn">${lastE.value_cagr}%</div><div class="l">Value CAGR now (E4) vs ${D.vpm[1].value_cagr}% at peak (E2)</div></div>
    <div class="kpi"><div class="v dn">${aurNow}%</div><div class="l">Leader share, down from ${aurPeak}% peak</div></div>
    <div class="kpi"><div class="v up">${merNow}%</div><div class="l">Value entrant share, recovered from ${merTrough}% trough</div></div>
    <div class="kpi"><div class="v">${lastE.volume_cagr}%</div><div class="l">Volume CAGR now &mdash; growth is price, not demand</div></div>`;
  document.getElementById('changed').innerHTML=[
    `Penetration <b>saturated</b> &mdash; peaked ~${penPeakYr} and has since slipped, so the new-user engine that built E2 is spent.`,
    `Buyers are <b>down-tiering</b>: Base/Small value share rebounded in E4 after the premium run.`,
    `The <b>value entrant returned</b> (${merTrough}% &rarr; ${merNow}%), taking incremental growth the leader used to own.`,
    `Growth is now <b>price-led</b> (${lastE.volume_cagr}% volume of ${lastE.value_cagr}% value), and price has caught back up to inflation.`,
  ].map(t=>`<li>${t}</li>`).join('');
  document.getElementById('comprows').innerHTML=[
    ['Value entrant','Re-pricing into reopened entry tiers','up','Gaining'],
    ['Premium niche','Holding premium/big-pack buyers','fl','Stable'],
    ['Mainstream rival','Defensive, ceding share','dn','Slipping'],
    ['Leader (you)','Over-indexed on a saturated vector','dn','At risk'],
  ].map(([w,m,t,lab])=>`<tr><td class="who">${w}</td><td>${m}</td><td><span class="pill ${t}">${lab}</span></td></tr>`).join('');
  const recos=[
    ['Portfolio','Re-open the entry door','Barbell the range: refresh accessible Base/Small trial packs to restart penetration, while defending the Premium/Big ceiling that drove E3 value.'],
    ['Media','Rebalance benefit spaces','Weight was over-rotated to Value &amp; Longevity for a decade. Shift toward Smart Value and Hygiene &amp; Protection to meet the value entrant where it is winning.'],
    ['Pricing','Protect entry price points','E4 pricing ran ahead of volume. Hold price-pack entry to slow down-tiering rather than harvest price into a softening category.'],
    ['Distribution','Defend the shelf','Numeric distribution has plateaued near its ceiling; the next point comes from TDP &mdash; more pack-sizes per store &mdash; not new stores, especially against value-entrant listings.'],
    ['Comms','Shift conversion to retention','The job moved from trading new users in to keeping them from trading down. Lead on superiority versus the value alternatives, not versus the legacy form that has already gone.'],
  ];
  document.getElementById('recos').innerHTML=recos.map((r,i)=>`
    <div class="reco"><div class="num">${String(i+1).padStart(2,'0')}</div>
    <div><div class="vlab">${r[0]}</div><h4>${r[1]}</h4><p>${r[2]}</p></div></div>`).join('');
  document.getElementById('read3').textContent=
    `The category was built on penetration, and penetration is done. Defending the ${aurNow}% share means re-opening new-user access and meeting the value entrant on price-pack and message — not harvesting price out of a category growing only ${lastE.volume_cagr}% in real volume.`;
}

function reads(){
  document.getElementById('read0').innerHTML=`The high-growth era (E2, ${D.vpm[1].value_cagr}% value CAGR) was overwhelmingly <b>volume-led</b> — ${D.vpm[1].volume_pts} of ${D.vpm[1].value_cagr} points came from volume, with pricing held ${Math.abs(D.vpm[1].price_vs_inflation)}pt below inflation. The category never bought its way to growth; it recruited users. E4 inverts this: thin volume, price doing the work.`;
  document.getElementById('read1').innerHTML=`Penetration is the lead line through E2 — new buyers entering the category — while consumption and premiumization only take over in E3. Underneath sits five vectors moving together: an accessible portfolio, 3x media weight on a single conversion message, pricing below inflation, distribution reaching from ${D.distribution.nd[0]}% to ${D.distribution.nd[D.distribution.nd.length-1]}% of stores, and comms concentrated on Value &amp; Longevity.`;
  document.getElementById('read2').innerHTML=`In E2–E3 Auria's contribution to growth ran far above its fair share — it captured more of every incremental point than its size entitled it to. In E4 that flips: contribution falls toward and below fair share as the value entrant takes the marginal growth.`;
}

// ---- tabs ----
let built=[false,false,false,false];
function build(t){
  if(built[t])return; built[t]=true;
  if(t===0){eraStrip();chartTraj();chartVPM();chartInfl();}
  if(t===1){chartDrv();chartMix();vectors();chartMedia();}
  if(t===2){chartShare();chartFair();}
  if(t===3){nowTab();}
  if(t===0)reads(); if(t===1)reads(); if(t===2)reads();
}
document.querySelectorAll('nav.tabs button').forEach(b=>{
  b.addEventListener('click',()=>{
    const t=+b.dataset.t;
    document.querySelectorAll('nav.tabs button').forEach(x=>x.setAttribute('aria-selected',x===b));
    document.querySelectorAll('.panelpage').forEach((p,i)=>p.classList.toggle('active',i===t));
    build(t);
  });
});
reads(); build(0);
</script>
</body>
</html>"""

html = TPL.replace("/*__DATA__*/", json.dumps(DATA))
with open(f"{OUT}/index.html","w") as f:
    f.write(html)
print("index.html written:", len(html), "bytes")
