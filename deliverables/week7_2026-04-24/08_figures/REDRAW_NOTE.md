# Canonical FES figure - design note (2026-04-25)

Script: `reports/figures/plot_canonical_fes.py`
Outputs: `reports/figures/sz_2d_distribution.{png,pdf}` (300 dpi, 10.5 x 4.8 in)

## What changed
Previous figures painted unsampled bins with the colorbar max, producing a uniform "red wall." This version masks every FES cell where fewer than 3 effective COLVAR frames landed (sigma=1.2 histogram smoothing, then 5x5 closing) and paints those cells WHITE via `cmap.set_bad`. Also fixed grid orientation: PLUMED `sum_hills` writes z as the slow axis, so `reshape(Nz, Ns)` is correct (the prior `reshape(Ns, Nz).T` was scrambling the surface).

## Colormap choice
`viridis_r` over rainbow / cmocean dense / cmocean deep. The brief required low DG = dark, high DG = yellow-light — exactly viridis-reversed. cmocean.dense ends in white and would blend with the mask; rainbow/turbo is forbidden. Viridis_r is colorblind-safe and prints to grayscale gracefully.

## Basin annotations
Auto-detection runs on the unsmoothed masked FES: 1-D local minima of F(s)=min over y, threshold F<1.5 kcal/mol, >=1.5 s-separation. Three basins emerge: Open (s=1.00, F=0.74), Mid (2.90, F=0.60), PC (4.65, F=0.00). Each gets a white-filled marker plus a white-on-black tag `Label  (F = X.XX)` — F-value inline so the reviewer doesn't re-count colorbar steps. Tags use 8 compass placements; Open and PC top-right, Mid below, breaking the vertical overlap. Naive panel stays unannotated so the reviewer reads the empty-Open story from the s=1.00-1.90 footer.
