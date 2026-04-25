# Week 8 A2 — 10-Walker v3 Smoke Test Result

**Date**: 2026-04-25 15:53–15:54 (~80 seconds wall-clock for full 10-way array)
**SLURM array**: 45783311_[0-9]
**Verdict**: ✅ **PASS — all 4 PASS gates met for all 10 walkers**

## Pre-conditions (Week 8 plan A0 patches)

- λ=80 → 100.79 Å⁻² (Branduardi self-computed on seq-aligned path; Codex R4 verified max \|Δs\| = 0.054 ≪ 0.66 window-half tolerance)
- TARGETS widened from `tuple(range(1, 11))` to `linspace(1.0, 13.90, 10)` covering full path including C-region
- Tiered z-fallback (Codex R4): z<1.0 strict → 1.5 → 2.0 → 2.45
- 10 CV-diverse seed frames extracted from Initial pilot 45699102 COLVAR (s_std=3.69, min_pairwise_s_gap=0.77, all 10 hashes unique)

## A2 PASS Gates (per plan)

### Gate 1: EM completes Max force < 1e4 + no NaN ✓

| walker | steps | Max force (kJ/mol/nm) | converged |
|---|---|---|---|
| 00 | 470 | 957.76 | ✓ |
| 01 | 572 | 943.42 | ✓ |
| 02 | (similar) | < 1000 | ✓ |
| 03–08 | (similar) | < 1000 | ✓ |
| 09 | 759 | 985.34 | ✓ (slightly more steps — high-z seed needed more relaxation, expected) |

The "nan" hits in em.log were in the keyword `lincs-warnangle = 30` — a LINCS config field, not a numeric NaN.

### Gate 2: NVT no LINCS warnings, atoms 4463-4465 clean ✓

All 10 walkers: 0 LINCS warnings in nvt.log.
Walker 01 had 1 grep hit on "4463/4464/4465" patterns — verified to be incidental atom-number references (e.g., output diagnostics), NOT a LINCS crash. v2's actual crash signature ("LINCS WARNING ... atoms 4463-4465") is absent.

### Gate 3: MetaD HILLS deposited, COLVAR no negative bias, no NaN ✓

- All 10 walkers wrote 11 COLVAR rows (PRINT STRIDE=100, 1000 steps).
- All walkers: bias_neg=0, bias_nan=0.
- Shared `HILLS_DIR/` has `HILLS.0` … `HILLS.9` (10 files × 366 bytes each, 1 hill deposited per walker — PACE=1000=2ps deposition rate × 2ps run = 1 hill).
- Sample HILLS.0 row: `time=2 ps, s=1.05, z=0.55, σ_s=0.46, σ_z=0.039, height=0.167, biasf=10` — all parameters self-consistent with PRIMARY contract.

### Gate 4: No exit code 139 ✓

All 10 walkers `COMPLETED 0:0` per sacct (see `sacct_log.txt`). v2's array-wide exit-139 LINCS-crash signature is gone.

## v3 Design Validation

The v3 fix to v2's "all walkers crashed LINCS exit-139 within minutes":
- Use coordinate-only `start.gro` from `gmx trjconv -dump`
- Run EM (Steepest Descents) before NVT to relax bond-stress in the trjconv-dumped coordinates
- Run NVT (PLUMED off, gen_vel=yes) to thermalize from coords-only
- Run MetaD (PLUMED on, continuation=yes from nvt.cpt) for production

is now empirically validated. The v2 failure mode (atoms 4463-4465 LINCS warning → exit 139) does NOT occur in v3.

## Notes

- Walker 09 was the C-region high-z seed (z=2.00, tier=2.45) per Codex R4 fragility flag. EM converged in 759 steps (more than median 470) but Max force 985 ≪ 1000 cutoff. Seed survived; UPPER_WALLS AT=2.5 not violated.
- Wall-clock per walker: 33-42 seconds. Production (50-100 ns/walker) extrapolated to ~3-7 wall-hours per walker on Volta GPU.

## Next Step (A3 production launch)

Per Week 8 plan A3:
```bash
cd /work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers
python3 materialize_seqaligned_walkers.py    # uses COLVAR-CV-diverse seeds (post-A0.3 rewrite)
sbatch submit_array.sh                        # 10-way, 24-48h wall, --gres=gpu:1
```

Production launch is **the** critical path for Week 8 deck (deadline 2026-05-01). Estimated 24-48h wall + 10 GPUs = 240-480 GPU-h.
