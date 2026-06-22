# Category Growth Codification Console

A self-contained, interactive decomposition of twenty years of an FMCG category. It takes a long-run growth series apart into eras, the volume/price/mix that built each one, the demand vectors behind them, the share story, and a forward competitive read. Built as a portfolio demonstration of category-growth analysis.

**All data is synthetic and product-agnostic.** No real brand, category, figure, or business context. The dataset is engineered to carry a specific, realistic analytical narrative so the method is visible end to end.

---

## The four acts

1. **Category Growth** — the 20-year trajectory split into four growth eras, a volume/price/mix bridge per era (bars reconcile exactly to each era's value CAGR), and pricing tracked against inflation.
2. **Growth Vectors** — why it won. A demand driver tree (penetration / consumption / premiumization), the tier x pack mix shift, and the five enabling vectors shown as in-process metric *trajectories* over the full timeline, each era's rate of change annotated on the band, plus the comms benefit-space map.
3. **Share & Contribution** — manufacturer value share over time, and contribution-to-growth vs fair share by era (above the marker = winning more than your size entitles you to).
4. **Now & Outlook** — current-state KPIs, what changed, a competitive read, and five recommendations mapped one-to-one to the vectors and anchored to where the data turned.

## The engineered narrative

- **E1 (2003–2008) Stable Base Growth** — ~4% volume CAGR, base-led, low penetration.
- **E2 (2009–2015) Penetration Explosion** — ~15% volume CAGR, new-user led. All five vectors fire together: entry packs added, GRP ~3x, pricing held below inflation, distribution expands, comms concentrated on one conversion benefit.
- **E3 (2016–2018) Premiumization & Big Pack** — consumption and premium tier grow; price moves up.
- **E4 (2019–2022) Saturation & Competitive Shift** — penetration saturates, buyers down-tier, the value entrant rebounds, growth turns price-led, leader contribution slips below fair share.

The leader (Auria) climbs from 46% to a 66% peak then erodes to 59%; the value entrant (Mercato PL) collapses from 18% to 6% then recovers to 12%.

---

## Build pipeline

Two scripts, run in order. Same convention as the other consoles: script 01 generates the engineered synthetic data, script 02 produces a single self-contained HTML by injecting the data as JSON.

```bash
python 01_generate_data.py    # writes the CSVs
python 02_build_html.py        # reads CSVs -> index.html
```

### `01_generate_data.py`
Generates the synthetic data with the era dynamics described above and writes nine CSVs. Volume/price/mix is decomposed exactly (an assertion checks that volume + price + mix reconciles to value CAGR per era before anything is written).

### `02_build_html.py`
Reads the CSVs, assembles a single JSON payload, derives the per-era vector evidence and the era-level contribution-vs-fair-share, and injects everything into `index.html`. The page is vanilla JS with hand-rolled SVG charts — no external assets, no libraries, no network calls. `noindex`, mobile-responsive.

## Data files

| File | Grain | Contents |
|---|---|---|
| `category.csv` | year | category units, value, avg price, price index, CPI index |
| `cells.csv` | year x tier x pack | units, price, value for the four cells |
| `brands.csv` | year x brand | value, value share, contribution to growth |
| `drivers.csv` | year | penetration / consumption / premiumization indices; portfolio breadth; entry & premium SKU counts |
| `media.csv` | year x benefit space | GRP and share of weight |
| `copies.csv` | year | copies per month, active benefit spaces |
| `distribution.csv` | year | numeric distribution %, TDP index |
| `vpm.csv` | era | value/volume CAGR, volume/price/mix points, price vs inflation |
| `eras.csv` | era | era boundaries and labels |

## Segmentation

- **Tier:** Base / Premium
- **Pack:** Small Pack / Big Pack
- **Manufacturers:** Auria (leader), Nello (mainstream), Pavo (premium niche), Mercato PL (value / private label)
- **Benefit spaces:** Value & Longevity, Everyday Performance, Hygiene & Protection, Premium Care, Smart Value

## Notes

- To re-skin: brand names, the category framing, benefit-space labels, and era titles are all data, not logic. Change them in `01_generate_data.py` (or the label maps in `02`) and rebuild.
- To re-shape the narrative: adjust the era YoY growth, the mix anchors, the price-vs-CPI settings, and the brand share anchors in `01_generate_data.py`. The decomposition and all charts recompute.
