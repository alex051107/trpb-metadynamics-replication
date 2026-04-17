# Job 42679152 — FP-024 SIGMA Collapse (Archived 2026-04-15)

**Status**: FAILED (physically stuck, mechanically complete)
**Run date**: 2026-04-09 → 2026-04-12 (50 ns)
**Failure mode**: FP-024 — SIGMA_MIN missing under ADAPTIVE=GEOM

## What happened

- 50 ns completed, 25,003 Gaussians deposited, 48 kJ/mol accumulated bias, 0 NaN
- s(R) stuck in [1.00, 1.63] for full 50 ns (O basin; never left)
- HILLS column 4 (sigma_path.sss): 0.011–0.072 s-units → 0.07–0.5% of 14-unit path axis
- All Gaussians piled at s≈1.05, forming a deep narrow well with ~zero gradient outside

## Root cause

`SIGMA=0.05 ADAPTIVE=GEOM` with no SIGMA_MIN: PLUMED 2.9 METAD "Sigma is one number 
that has distance units" (Cartesian nm scalar). Adaptive algorithm projects this seed 
onto each CV and adjusts to local curvature. Without SIGMA_MIN, per-CV σ_s collapsed 
to needle-thin Gaussians that exert zero gradient on the walker.

## Fix deployed 2026-04-15

```
SIGMA=0.1 ADAPTIVE=GEOM SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05
```

## Diagnostic use

Read `HILLS` column 4 (`sigma_path.sss_path.sss`) to confirm FP-024 signature:
```python
import numpy as np
h = np.loadtxt('HILLS', comments='#')
print(f"sigma_sss range: {h[:,3].min():.4f} – {h[:,3].max():.4f} s-units")
# FP-024: max < 0.1; healthy: min > 0.3
```
