"""
01_generate_data.py
Generates a synthetic, product-agnostic FMCG category dataset engineered to carry
a specific analytical narrative across 20 years (2002 base, 2003-2022 growth):

  E1 2003-2008  Stable Base Growth         (~4% CAGR)
  E2 2009-2015  Penetration Explosion      (~15% CAGR, new-user led, all vectors firing)
  E3 2016-2018  Premiumization & Big Pack  (~9% CAGR, consumption/premium led)
  E4 2019-2022  Saturation & Competitive   (~2% CAGR, down-tiering, value entrant rebounds)

Segmentation axes (fully abstracted):
  Tier = Base / Premium
  Pack = Small Pack / Big Pack
Manufacturers: Auria (leader/protagonist), Nello (mainstream), Pavo (premium niche),
               Mercato PL (value / private label entrant).

All numbers are invented and internally consistent. No real brand, category, or figure.
"""
import numpy as np, pandas as pd, os

np.random.seed(7)
OUT = os.path.dirname(os.path.abspath(__file__))

YEARS = list(range(2002, 2023))           # 2002 = base year
GROWTH_YEARS = list(range(2003, 2023))

ERAS = [
    ("E1", 2003, 2008, "Stable Base Growth"),
    ("E2", 2009, 2015, "Penetration Explosion"),
    ("E3", 2016, 2018, "Premiumization & Big Pack"),
    ("E4", 2019, 2022, "Saturation & Competitive Shift"),
]

def interp(anchors):
    """anchors: dict year->value -> per-year linear interpolation across YEARS."""
    ays = sorted(anchors)
    out = {}
    for y in YEARS:
        if y <= ays[0]:
            out[y] = anchors[ays[0]]
        elif y >= ays[-1]:
            out[y] = anchors[ays[-1]]
        else:
            lo = max(a for a in ays if a <= y)
            hi = min(a for a in ays if a >= y)
            if lo == hi:
                out[y] = anchors[lo]
            else:
                f = (y - lo) / (hi - lo)
                out[y] = anchors[lo] + f * (anchors[hi] - anchors[lo])
    return out

# ----------------------------------------------------------------------------- 
# 1. Category total volume (index MSU), engineered YoY growth by era
# ----------------------------------------------------------------------------- 
yoy = {
    2003:0.04,2004:0.03,2005:0.04,2006:0.05,2007:0.04,2008:0.03,            # E1 ~4%
    2009:0.16,2010:0.14,2011:0.17,2012:0.13,2013:0.15,2014:0.16,2015:0.14,  # E2 ~15%
    2016:0.10,2017:0.08,2018:0.09,                                          # E3 ~9%
    2019:0.05,2020:-0.03,2021:0.04,2022:0.03,                               # E4 ~2%
}
units = {2002: 1000.0}
for y in GROWTH_YEARS:
    units[y] = units[y-1] * (1 + yoy[y])

# ----------------------------------------------------------------------------- 
# 2. Tier x Pack volume-share mix (sums to 100 each year) + per-unit prices
#    Cells: BS Base/Small, BB Base/Big, PS Premium/Small, PB Premium/Big
# ----------------------------------------------------------------------------- 
mix_anchor = {  # volume share %
    'BS': {2002:55,2008:52,2015:50,2018:44,2022:47},
    'BB': {2002:18,2008:20,2015:22,2018:24,2022:22},
    'PS': {2002:20,2008:19,2015:17,2018:16,2022:15},
    'PB': {2002:7 ,2008:9 ,2015:11,2018:16,2022:16},
}
mix = {c: interp(a) for c, a in mix_anchor.items()}
# normalise to 100
for y in YEARS:
    s = sum(mix[c][y] for c in mix)
    for c in mix: mix[c][y] = mix[c][y] / s * 100

base_price = {'BS':10.0,'BB':8.0,'PS':16.0,'PB':13.0}   # per-unit; big pack cheaper/unit
price_yoy_by_era = {'E1':0.035,'E2':0.015,'E3':0.045,'E4':0.045}  # E2 below CPI, E3/E4 above
def era_of(y):
    for e,s,en,_ in ERAS:
        if s <= y <= en: return e
    return 'E1'
price = {c:{2002:base_price[c]} for c in base_price}
for c in base_price:
    for y in GROWTH_YEARS:
        price[c][y] = price[c][y-1] * (1 + price_yoy_by_era[era_of(y)])

# CPI index (inflation) ~4%/yr
cpi = {2002:100.0}
cpi_yoy = {y:(0.030 if 2009<=y<=2015 else 0.040) for y in GROWTH_YEARS}
for y in GROWTH_YEARS: cpi[y] = cpi[y-1]*(1+cpi_yoy[y])

# cell-level fact table
cell_rows = []
for y in YEARS:
    for c in mix:
        u = units[y]*mix[c][y]/100.0
        p = price[c][y]
        tier = 'Premium' if c[0]=='P' else 'Base'
        pack = 'Big Pack' if c[1]=='B' else 'Small Pack'
        cell_rows.append(dict(year=y, cell=c, tier=tier, pack=pack,
                              units=round(u,2), price=round(p,3), value=round(u*p,2)))
cells = pd.DataFrame(cell_rows)

# category totals + price index
cat_rows = []
for y in YEARS:
    val = cells[cells.year==y].value.sum()
    u   = cells[cells.year==y].units.sum()
    cat_rows.append(dict(year=y, units=round(u,2), value=round(val,2),
                         avg_price=round(val/u,4), cpi_index=round(cpi[y],2)))
cat = pd.DataFrame(cat_rows)
p0 = cat.avg_price.iloc[0]
cat['price_index'] = (cat.avg_price/p0*100).round(2)

# ----------------------------------------------------------------------------- 
# 3. Brand / manufacturer value share + contribution to growth
# ----------------------------------------------------------------------------- 
brand_anchor = {  # value share %
    'Auria'      : {2002:46,2008:44,2015:62,2018:66,2022:59},
    'Nello'      : {2002:24,2008:25,2015:18,2018:16,2022:17},
    'Pavo'       : {2002:12,2008:13,2015:12,2018:12,2022:12},
    'Mercato PL' : {2002:18,2008:18,2015:8 ,2018:6 ,2022:12},
}
bshare = {b: interp(a) for b,a in brand_anchor.items()}
for y in YEARS:
    s = sum(bshare[b][y] for b in bshare)
    for b in bshare: bshare[b][y] = bshare[b][y]/s*100

brand_rows = []
catval = {y: cat[cat.year==y].value.iloc[0] for y in YEARS}
for y in YEARS:
    for b in bshare:
        bv = catval[y]*bshare[b][y]/100.0
        brand_rows.append(dict(year=y, brand=b, value=round(bv,2),
                               value_share=round(bshare[b][y],2)))
brands = pd.DataFrame(brand_rows)
# contribution to category growth (yoy) per brand
brands['contrib_to_growth'] = np.nan
for b in bshare:
    sub = brands[brands.brand==b].sort_values('year')
    for i in range(1,len(sub)):
        y = sub.year.iloc[i]
        dcat = catval[y]-catval[y-1]
        dbr  = sub.value.iloc[i]-sub.value.iloc[i-1]
        contrib = (dbr/dcat*100) if dcat!=0 else np.nan
        brands.loc[(brands.brand==b)&(brands.year==y),'contrib_to_growth']=round(contrib,1)

# ----------------------------------------------------------------------------- 
# 4. Demand driver tree: penetration / consumption / premiumization (index 2002=100)
# ----------------------------------------------------------------------------- 
drivers = pd.DataFrame({'year':YEARS})
drivers['penetration']    = [round(interp({2002:100,2008:108,2015:150,2018:158,2022:152})[y],1) for y in YEARS]
drivers['consumption']    = [round(interp({2002:100,2008:103,2015:118,2018:130,2022:128})[y],1) for y in YEARS]
drivers['premiumization'] = [round(interp({2002:100,2008:106,2015:112,2018:140,2022:138})[y],1) for y in YEARS]
# portfolio breadth (range/SKU proxy): entry packs recruit in E2, premium extensions in E3
drivers['portfolio_breadth'] = [round(interp({2002:100,2008:108,2015:165,2018:195,2022:198})[y],1) for y in YEARS]
# what portfolio was actually in market: entry (Base) vs premium SKU counts
drivers['entry_skus']   = [round(interp({2002:6,2008:8 ,2015:15,2018:16,2022:16})[y]) for y in YEARS]
drivers['premium_skus'] = [round(interp({2002:3,2008:4 ,2015:6 ,2018:12,2022:12})[y]) for y in YEARS]

# ----------------------------------------------------------------------------- 
# 5. Media (leader Auria): GRP by benefit space + copies/month
# ----------------------------------------------------------------------------- 
grp_total = {2003:11000,2004:12000,2005:13000,2006:14000,2007:16000,2008:18000,
             2009:24000,2010:30000,2011:38000,2012:42000,2013:46000,2014:52000,2015:55000,
             2016:58000,2017:60000,2018:50000,2019:48000,2020:38000,2021:42000,2022:40000}
BENEFITS = ["Value & Longevity","Everyday Performance","Hygiene & Protection","Premium Care","Smart Value"]
alloc_by_era = {  # % of GRP per benefit space
 'E1':[35,40,15,5,5],
 'E2':[50,25,15,7,3],
 'E3':[25,20,15,35,5],
 'E4':[18,17,22,23,20],
}
media_rows=[]
for y in GROWTH_YEARS:
    a = alloc_by_era[era_of(y)]
    for bs,share in zip(BENEFITS,a):
        media_rows.append(dict(year=y, benefit_space=bs,
                               grp=round(grp_total[y]*share/100.0),
                               share=share))
media = pd.DataFrame(media_rows)
copies = pd.DataFrame({'year':GROWTH_YEARS,
   'copies_per_month':[round(interp({2003:3,2009:4,2015:3,2018:3,2022:3})[y]) for y in GROWTH_YEARS],
   'active_benefit_spaces':[sum(1 for s in alloc_by_era[era_of(y)] if s>=15) for y in GROWTH_YEARS]})

# ----------------------------------------------------------------------------- 
# 6. Distribution: numeric distribution (% stores) + TDP index
# ----------------------------------------------------------------------------- 
dist = pd.DataFrame({'year':YEARS})
dist['numeric_distribution'] = [round(interp({2002:48,2008:55,2015:78,2018:84,2022:80})[y],1) for y in YEARS]
dist['tdp_index']            = [round(interp({2002:100,2008:120,2015:210,2018:240,2022:225})[y],1) for y in YEARS]

# ----------------------------------------------------------------------------- 
# 7. Volume / Price / Mix decomposition per era (exact, then -> CAGR points)
# ----------------------------------------------------------------------------- 
def cell_state(y):
    sub = cells[cells.year==y]
    U = sub.units.sum()
    s = {r.cell: r.units/U for r in sub.itertuples()}
    p = {r.cell: r.price for r in sub.itertuples()}
    return U, s, p

vpm_rows=[]
for e,s_y,e_y,label in ERAS:
    y0, y1 = s_y-1, e_y          # decompose from era-start-1 to era-end
    U0,s0,p0d = cell_state(y0)
    U1,s1,p1d = cell_state(y1)
    Pbar0 = sum(s0[c]*p0d[c] for c in s0)
    Pbar1 = sum(s1[c]*p1d[c] for c in s1)
    V0, V1 = U0*Pbar0, U1*Pbar1
    Volume = (U1-U0)*Pbar0
    Mix    = U1*sum((s1[c]-s0[c])*p0d[c] for c in s0)
    Price  = U1*sum(s1[c]*(p1d[c]-p0d[c]) for c in s0)
    dV = V1-V0
    n = y1-y0
    val_cagr = (V1/V0)**(1/n)-1
    vol_cagr = (U1/U0)**(1/n)-1
    # split CAGR proportionally to each component's share of dV (sums to val_cagr)
    def pts(x): return round((x/dV)*val_cagr*100,2) if dV!=0 else 0.0
    price_idx_growth = (cat[cat.year==y1].price_index.iloc[0]/cat[cat.year==y0].price_index.iloc[0])**(1/n)-1
    cpi_growth       = (cpi[y1]/cpi[y0])**(1/n)-1
    vpm_rows.append(dict(era=e, label=label, start=s_y, end=e_y,
        value_cagr=round(val_cagr*100,2), volume_cagr=round(vol_cagr*100,2),
        volume_pts=pts(Volume), price_pts=pts(Price), mix_pts=pts(Mix),
        price_growth=round(price_idx_growth*100,2), cpi_growth=round(cpi_growth*100,2),
        price_vs_inflation=round((price_idx_growth-cpi_growth)*100,2)))
vpm = pd.DataFrame(vpm_rows)
# sanity check
chk = (vpm.volume_pts+vpm.price_pts+vpm.mix_pts) - vpm.value_cagr
assert chk.abs().max() < 0.05, f"VPM does not reconcile: {chk.tolist()}"

# ----------------------------------------------------------------------------- 
# write
# ----------------------------------------------------------------------------- 
cells.to_csv(f"{OUT}/cells.csv",index=False)
cat.to_csv(f"{OUT}/category.csv",index=False)
brands.to_csv(f"{OUT}/brands.csv",index=False)
drivers.to_csv(f"{OUT}/drivers.csv",index=False)
media.to_csv(f"{OUT}/media.csv",index=False)
copies.to_csv(f"{OUT}/copies.csv",index=False)
dist.to_csv(f"{OUT}/distribution.csv",index=False)
vpm.to_csv(f"{OUT}/vpm.csv",index=False)
pd.DataFrame(ERAS,columns=['era','start','end','label']).to_csv(f"{OUT}/eras.csv",index=False)

print("VPM reconciliation OK. Era summary:")
print(vpm[['era','label','value_cagr','volume_cagr','volume_pts','price_pts','mix_pts','price_vs_inflation']].to_string(index=False))
print("\nLeader (Auria) share:", [round(bshare['Auria'][y],1) for y in [2002,2008,2015,2018,2022]])
print("Mercato PL share:", [round(bshare['Mercato PL'][y],1) for y in [2002,2008,2015,2018,2022]])
print("Category units 2002->2022:", round(units[2002]), "->", round(units[2022]),
      f"({units[2022]/units[2002]:.1f}x)")
