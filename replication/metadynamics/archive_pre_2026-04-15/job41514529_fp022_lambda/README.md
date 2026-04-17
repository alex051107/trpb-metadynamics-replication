# Job 41514529 — FP-022 Wrong λ (Archived 2026-04-09)

**Status**: FAILED (wrong λ, pre-PATHMSD pivot)
**Run date**: 2026-04-04 → 2026-04-07 (~40 ns)
**Failure mode**: FP-022 — λ = 3.3910 nm⁻² (RMSD-based, off by 112×)

## What happened

- λ should be 379.77 nm⁻² (2.3 / per-atom MSD_adj where MSD_adj = 0.006056 nm²)
- Actual λ used: 3.3910 nm⁻² (derived from RMSD 0.825 Å using wrong formula)
- Additionally, this run used FUNCPATHMSD (workaround for conda PLUMED bug)
  → HILLS fields named `path.s` / `path.z` (not `path.sss` / `path.zzz`)
- Path CV values not physically meaningful; run discarded

## Note on HILLS format

Column headers differ from current production:
- Old (this run): `path.s`, `path.z`
- Current (Job 44008381): `path.sss`, `path.zzz`

This is a naming difference from FUNCPATHMSD vs PATHMSD, not a data format difference.

## Fix deployed 2026-04-09

1. λ recalculated: 2.3 / 0.006056 nm² = 379.77 nm⁻² (per-atom MSD, not RMSD)
2. Switched from FUNCPATHMSD back to PATHMSD (PLUMED 2.9.2 source-compiled, 
   libplumedKernel.so present and working)
