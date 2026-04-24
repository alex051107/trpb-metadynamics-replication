# 10-walker production on sequence-aligned path (Ain system)

## Status (2026-04-23)

Prepared but NOT yet launched. Awaiting pilot 45515869 gate:
- max_s > 12 on corrected path → promote this to production
- max_s stalls < 5 → diagnose before launching 10-walker

## Design

- **System**: Ain (PLP internal aldimine), same 39,268-atom solvated box as
  all prior runs (single_walker/ and initial_seqaligned/).
- **Path**: `path_seqaligned_gromacs.pdb` (FP-034-corrected, Needleman-Wunsch
  sequence-aligned 1WDW-B vs 3CEP-B, uniform +5 offset; independently
  verified by Codex 7/8 PASS in `../path_seqaligned/VERIFICATION_REPORT.md`).
- **LAMBDA**: 80 Å⁻² — Miguel's email-quoted value, now self-consistent
  with our path (Branduardi λ = 100.79 Å⁻², ratio 1.26×).
- **MetaD recipe**: Miguel PRIMARY contract (not fallback):
  - ADAPTIVE=DIFF, SIGMA=1000 steps (= 2 ps window)
  - HEIGHT=**0.15** kcal/mol (primary, vs fallback 0.3)
  - BIASFACTOR=**10.0** (primary, vs fallback 15)
  - TEMP=350 K
  - UPPER_WALLS on p1.zzz AT=2.5 KAPPA=800
  - GRID_MIN=0.5,0.0 GRID_MAX=15.5,2.8 GRID_BIN=300,100
  - WALKERS_N=10, shared HILLS via `WALKERS_DIR=../HILLS_DIR`,
    `WALKERS_RSTRIDE=3000`
- **Seeding**: 10 snapshots from 500 ns Ain cMD trajectory at t = 50,
  100, 150, ..., 500 ns (uniformly spaced). On corrected path, these
  snapshots span s ≈ 5-10 (mid-path), giving natural diversity for
  exploration.

## Files

- `plumed_template.dat` — Miguel primary contract + seqaligned path +
  LAMBDA=80; `__WALKERS_ID__` placeholder for walker index
- `materialize_seqaligned_walkers.py` — stamps walker_00..walker_09 from
  template + extracts 10 snapshots from 500 ns Ain cMD + builds 10 TPRs
- `submit_array.sh` — SLURM array script (0-9), volta-gpu a100-gpu
- `HILLS_DIR/` (created by materialize) — shared bias directory

## Launch procedure (when pilot 45515869 clears gate)

On Longleaf:
```bash
cd /work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers
python3 materialize_seqaligned_walkers.py   # creates walker_00..09/
sbatch submit_array.sh                       # 10-way SLURM array
```

Each walker runs 5-10 ns independently; HILLS shared every 6 ps
(RSTRIDE=3000 × 2 fs). Total ~50-100 GPU-h.

## Post-run deliverable

- COLVAR_all.csv (concatenated 10-walker s,z trajectories)
- FES reweight via `plumed sum_hills` on combined HILLS
- 2D (s,z) FES plot vs Osuna 2019 Figure 3 baseline
- Methods-critique writeup citing FP-034 and the PMSD path-recipe
  reconstruction

## NOT in scope here

- Running on OLD (naive-mapped) path — that was for 45324928 / 45448011
  and is archived.
- Mixing ADAPTIVE=GEOM or other schemes — Miguel email pins DIFF.
- Extending to Aex1 — 45186335 cMD still in progress; Aex1 MetaD
  blocked on cMD completion (task #17).
