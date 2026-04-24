# 08 · Figures

Reproducible figures for the Week-7 deliverable.

## Files

| File | What it is |
|---|---|
| `plot_sz_distribution.py` | Primary script. Reads pilot + baseline COLVAR, builds FES via 2D gaussian KDE at T = 350 K, produces side-by-side figure. |
| `sz_2d_distribution.png` | Headline figure: FES(s, z) naive vs sequence-aligned. The one figure that summarises the week. |
| `s_trend_slide.png` | 1D s(t) trace, pilot vs baseline overlay (used on slide 6). |
| `sz_2d_pilot_jacs_style.png` | Pilot-only 2D density in JACS-2019-Fig3 style (used on slide 7). |

## Reproduction

```bash
# Requires numpy, scipy, matplotlib
python3 plot_sz_distribution.py
```

The script expects COLVAR files at:
```
../../../chatgpt_pro_consult_45558834/raw_data/pilot_45515869_COLVAR
../../../chatgpt_pro_consult_45558834/raw_data/baseline_45324928_COLVAR
```
(relative to this subdirectory inside the deliverable package).

## Design choices

- **Viridis_r colormap** (yellow = populated, dark = unvisited) — colorblind-safe, perceptually uniform.
- **`F = -kT ln(p / p_max)` clipped at 6 kcal/mol** — single-walker data is not a converged FES; 6 kcal/mol is low enough to show occupancy structure without implying barrier heights.
- **Panel captions below each panel, not inside** — prevents overlap with the 2D density.
- **`start.gro` marked with a red star on panel b** — with explicit `(s, z)` annotation so viewers know where the seed lives.
- **`UPPER_WALLS z = 2.5` dashed line** — documents the bias cap that appears in the pilot data.
