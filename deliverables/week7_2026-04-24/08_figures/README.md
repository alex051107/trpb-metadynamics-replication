# 08 · Figures

Reproducible figures for the Week-7 deliverable.

## Files

| File | What it is |
|---|---|
| `plot_sz_si_sumhills.py` | Current SI-style script. Reads PLUMED `sum_hills` grids from Longleaf HILLS, uses SI-like axes and colorbar. |
| `plot_sz_distribution.py` | Older diagnostic script. Reads pilot + baseline COLVAR and builds a 2D KDE occupancy surface, not the SI `sum_hills` FEL. |
| `sz_2d_distribution.png` | Headline figure: SI-literal FEL(s, z) naive vs sequence-aligned, generated from HILLS via `plumed sum_hills`. |
| `s_trend_slide.png` | 1D s(t) trace, pilot vs baseline overlay (used on slide 6). |
| `sz_2d_pilot_jacs_style.png` | Pilot-only 2D density in JACS-2019-Fig3 style (used on slide 7). |

## Reproduction

```bash
# First generate the FES grids on Longleaf with PLUMED 2.9.2:
plumed sum_hills --hills ../initial_single/HILLS \
  --outfile fes_initial_single.dat --min 0.5,0.0 --max 15.5,2.8 \
  --bin 300,140 --mintozero

plumed sum_hills --hills ../initial_seqaligned/HILLS \
  --outfile fes_initial_seqaligned.dat --min 0.5,0.0 --max 15.5,2.8 \
  --bin 300,140 --mintozero

# Then render locally:
python3 plot_sz_si_sumhills.py
```

The Longleaf grids were generated in:
`/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/analysis_si_style_figures/`.

## Design choices

- **PLUMED `sum_hills`, not COLVAR KDE** — matches the SI caption language that FELs are estimated by summing deposited Gaussian potentials.
- **SI-literal y-axis** — raw `p1.zzz` is plotted with the paper's `RMSD Deviation (Å)` label to match the original visual convention.
- **Colorbar 0-14 kcal/mol** — matches the SI/main-paper scale.
- **`start.gro` marked with a red star on panel b** — with explicit `(s, z)` annotation so viewers know where the seed lives.
- **`UPPER_WALLS z = 2.5` dashed line** — documents the bias cap that appears in the pilot data.
