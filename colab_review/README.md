# Colab review package — TrpB path-piecewise audit (2026-04-23)

Self-contained re-verification of every numerical claim in the recent
path-piecewise audit + the 45324928 Miguel fallback analysis. Runs on
local Python 3.9+ or Google Colab with only numpy.

## One-line run

```bash
python3 verify_all.py
```

Expected output: `SUMMARY: 33 PASS, 0 FAIL`. Tolerances are tight
(0.001–0.01 depending on claim); every number in this audit is checked.

## Google Colab instructions

1. Upload the entire `colab_review/` folder contents to Colab.
2. Run a single cell: `!python verify_all.py`.
3. If any claim prints `✗` the script exits with code 1.

No pip installs required. Base Colab already has numpy.

## Known bug fixed in this package

`scan_pc_anchors.py` (the script that produced the original scan
output) had a z(R) computation bug: `shift -= shift.max()` was done
in-place, then `shift.max()` was read AFTER the subtraction (=0),
giving `z_reported = true_z − MSD_min`. The s values and the verdict
were correct (s invariant under the constant shift), but the reported
z values were systematically biased by −MSD_min.

`verify_all.py` uses the corrected log-sum-exp formula. Results:

| Code | s(R) | z(R) new | z(R) old | MSD_min |
|---|---|---|---|---|
| 5DW0 | 1.069 | 2.450 | −0.019 | 2.469 |
| 5DW3 | 1.075 | 2.072 | −0.021 | 2.093 |
| 5DVZ | 1.067 | 1.733 | −0.018 | 1.752 |

Updated interpretation: these βPC anchors are not just O-proximal
(s≈1.07), they are also clearly off-path (|z|≈2 Å² kernel-averaged
distance). This strengthens rather than weakens the audit conclusion.

## What is NOT verified here

- **Hypothesis D (path geometry is the rate-limiter).** Still an
  open hypothesis. This requires the wall-relaxation pilot
  (job 45448011) to return, AND Miguel's fallback run 45324928 to
  hit its 8–10 ns hard gate.
- **45324928 extrapolation past current sim time (3.76 ns).** The
  downloaded COLVAR/HILLS snapshot represents the run state at the
  time of download. Later wall time may change numbers but will not
  change the historical max_s = 1.4964 at 1300.6 ps.
- **Miguel's own PATH.pdb geometry.** We do not have this file. All
  λ numbers on our side are self-consistent for OUR direct path,
  not his.

## Claim list (machine-checked in verify_all.py)

### Claim 1 — direct path numerics
- ⟨MSD_adj⟩ = 0.61 Å² (linear interp, uniform spacing ⇒ CV ≈ 0)
- λ = 3.80 Å⁻² (Branduardi formula on our ⟨MSD⟩)
- plumed.dat stores 3.77 — 0.7% rounding difference, acceptable

### Claim 2 — piecewise audit (1WDW → 5DW0/5DW3 → 3CEP with PC at MODEL 8)
- 5DW0: O↔PC=1.571 Å, PC↔C=11.061 Å, CV=0.96, single-λ=1.806 Å⁻²
- 5DW3: O↔PC=1.447 Å, PC↔C=10.988 Å, CV=0.97, single-λ=1.835 Å⁻²
- Belfast healthy CV ≤ 0.15 → both fail by 6×

### Claim 3 — PC candidate projection onto direct path
- 5DW0 s=1.069, z=2.450 Å², RMSD_to_O=1.57, RMSD_to_C=11.06 — O-proximal, off-path
- 5DW3 s=1.075, z=2.072 Å², RMSD_to_O=1.45, RMSD_to_C=10.99 — O-proximal, off-path
- 5DVZ s=1.067, z=1.733 Å², RMSD_to_O=1.32, RMSD_to_C=11.03 — O-proximal, off-path
- None land at the healthy PC range s ∈ [5, 10]

### Claim 4 — 45324928 Miguel fallback (3.76 ns) numerics
- max_s = 1.4964 at t = 1300.6 ps (single spike, no sustained occupancy)
- p95(s) = 1.283 (95% of the run below 1.3 on s)
- fraction(s > 1.5) = 0.0000 (never sustained above 1.5)
- fraction(z > 2.3) = 23.3%
- σ_ss median = 0.030 (below declared SIGMA_MIN=0.1, see multivariate
  Cholesky interpretation by Codex — flagged for independent review)
- σ_zz median = 0.20, max = 4.00 (spikes correlate with wall hits)
- wall active fraction = 5.9%
- 1880 hills deposited; height median = 0.133 (well-tempered scaling active)

## Files

```
colab_review/
├── README.md                     (this file)
├── verify_all.py                 (33-claim verification script)
├── direct_path_gromacs.pdb       (single_walker/path_gromacs.pdb, 15 MODELs × 112 Cα)
├── 1WDW.pdb, 3CEP.pdb            (O, C anchors)
├── 5DW0.pdb, 5DW3.pdb, 5DVZ.pdb  (PC candidates)
├── 4HPX.pdb                      (C-side reference; chain A has 24 missing resids)
├── HILLS, COLVAR, plumed.dat     (45324928 run, sim 0–3.76 ns)
└── miguel_email.md               (authoritative MetaD contract)
```
