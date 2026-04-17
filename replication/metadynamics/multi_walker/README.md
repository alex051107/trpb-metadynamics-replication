# 10-walker MetaDynamics (Phase 2) — multi_walker/

> **Status**: script bundle ready; awaiting single_walker Phase 1 completion
> (Job 44008381 spans s(R) = 1..15) + manual PyMOL visual QA before launch.

---

## 1. SI 原文 (Osuna et al., JACS 2019, SI p.S3-S4)

> "After an initial metadynamics run, we extracted ten snapshots for each
> system covering approximately all the conformational space available.
> Then, multiple-walkers metadynamics simulations with 10 replicas were
> computed. Each replica was run for 50-100 ns, giving a total of 500-1000 ns
> of simulation time per system."

This bundle reproduces exactly that protocol. Every physics parameter
(LAMBDA, SIGMA, HEIGHT, PACE, BIASFACTOR, TEMP, ADAPTIVE=GEOM) is identical
to `single_walker/plumed.dat`; only the walker-synchronisation block differs.

---

## 2. 参数合理性

| Parameter | Value | Source | 理由 |
|-----------|-------|--------|------|
| `WALKERS_N` | `10` | SI-quote | "10 replicas" (p.S3-S4) |
| Per-walker length | `50-100 ns` | SI-quote | "Each replica was run for 50-100 ns" |
| `WALKERS_DIR` | `../` | Our-choice | Shared HILLS lives in `multi_walker/`; each walker reads HILLS from parent |
| `WALKERS_RSTRIDE` | `1000` | Our-choice (SI silent) | 1000 PLUMED steps × 2 fs/step = 2 ns HILLS sync cadence. Shorter = tighter coupling but more filesystem thrash; longer = walkers drift. 2 ns is PLUMED tutorial convention. |
| `WALKERS_ID` | `0..9` | PLUMED spec | Baked in per walker via sed (robust across MPI ranks) |
| `LAMBDA` | `379.77 nm⁻²` | SI-derived | See `replication/parameters/PARAMETER_PROVENANCE.md` |
| `SIGMA / SIGMA_MIN / SIGMA_MAX` | `0.1 / 0.3,0.005 / 1.0,0.05` | FP-024 fix | ADAPTIVE=GEOM requires per-CV floor/ceiling in CV units |
| `HEIGHT / PACE / BIASFACTOR / TEMP` | `0.628 / 1000 / 10 / 350` | SI-quote | Identical to single_walker |

---

## 3. 前置条件 (prerequisites)

Before launching `submit_array.sh`:

1. **Initial single-walker MetaD complete**. Required outputs from `single_walker/`:
   - `metad.tpr` (topology + parameters)
   - `traj_comp.xtc` (compressed trajectory covering s(R) ∈ [1, 15])
   - `COLVAR` (plain-text s/z trace; passed to `setup_walkers.sh` for KMeans)
   - `topol.top`, `metad.mdp` (copied per walker)
2. **Yu Zhang 2026-04-09 L2859 directive**: the 10 starting snapshots MUST be
   picked by human eye in PyMOL. KMeans proposes candidates; a human confirms.
   This is NON-NEGOTIABLE — the SI's phrase "covering approximately all the
   conformational space available" is qualitative.
3. **`path_gromacs.pdb` present in `multi_walker/`** — each walker reads it as
   `../path_gromacs.pdb` (symlink from `single_walker/` or copy).
4. **PLUMED source-compiled build** (`$PLUMED_KERNEL` env var set to
   `/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so`). Conda-forge
   kernel is broken for PATHMSD (FP-020).

---

## 4. 启动流程 (numbered steps)

### Step 1 — KMeans candidate proposal
```bash
cd replication/metadynamics/multi_walker/
bash setup_walkers.sh ../single_walker/COLVAR
# produces candidate_frames.csv with 10 (time_ps, s, z, frame_idx) rows
```

### Step 2 — PyMOL visual QA (MANDATORY, Yu L2859)
For each candidate time:
```bash
gmx trjconv -s ../single_walker/metad.tpr \
            -f ../single_walker/traj_comp.xtc \
            -dump <time_ps> -o probe_<cid>.gro
pymol probe_0.gro probe_1.gro ... probe_9.gro
```
Inspect the COMM loop (residues 97-184). Confirm that the 10 frames cover
the full O → PC → C conformational range. Replace any cluster whose
representative looks redundant.

### Step 3 — Commit confirmed times
```bash
bash setup_walkers.sh --commit-frames t0,t1,t2,...,t9
# populates walker_0/..walker_9/ with start.gro + topol + mdp + plumed.dat (sed'd)
```

### Step 4 — Submit to Slurm
```bash
sbatch submit_array.sh
# 10 MPI ranks, 10 GPUs, up to 72 h wall
```

### Step 5 — Monitor
```bash
squeue -u $USER
# Inside the job:
tail -f multi_walker-<jobid>.out
wc -l HILLS.*
# Per-walker s(R) trace:
awk 'NR>5{print $2}' walker_0/COLVAR | head
```

---

## 5. 收敛判据 (convergence)

Osuna 2019 judges convergence by ΔG(O vs C) plateauing over simulation time
(SI Figures S4-S5 style). Our equivalent check:

```bash
plumed sum_hills --hills HILLS.0 --stride 2500 --mintozero --kt 2.908
# produces fes_<t>.dat at multiple times; plot ΔG_C - ΔG_O vs t
```

Convergence criteria:
- ΔG(O vs C) fluctuation < 1 kcal/mol over the last 100 ns (aggregate)
- All 10 walkers have visited s(R) ∈ [1, 15] at least once
- 2D FES (s, z) has no isolated pixel-scale bias cells (mean bias per
  Gaussian ≈ HEIGHT × e^(−bias/(BIASFACTOR−1)kT))

---

## 6. 中止判据 (abort triggers)

Kill the job immediately and investigate if any of:

| Condition | Meaning | Action |
|-----------|---------|--------|
| Any walker's COLVAR shows NaN | numerical blow-up | `scancel`, check `metad.log` for LINCS warnings |
| Two walkers' s(R) trajectories overlap > 80% of the time | bias sync broken / duplicate seeds | `scancel`, re-run `setup_walkers.sh --commit-frames` with more spread |
| HILLS.* sigma column < 0.3 on s-axis | FP-024 recurrence (Gaussian collapse) | `scancel`, check SIGMA_MIN=0.3 took effect |
| `bck.*.HILLS` appears in any walker dir | FP-026 recurrence (unsafe restart) | `scancel`, never restart without `convert-tpr -extend` + `RESTART` |
| Walker wall-time > 72 h with < 50 ns completed | GPU starved / launcher bug | `scancel`, check `-multidir` MPI layout |

---

## 7. 与 single_walker 对照表

| Item | single_walker | multi_walker | 说明 |
|------|---------------|--------------|------|
| `plumed.dat` | 1 file | 10 files (per walker, sed'd) | WALKERS_ID baked in per walker |
| `path_gromacs.pdb` | 1 copy in single_walker/ | 1 copy in multi_walker/ (each walker reads `../`) | shared reference |
| `HILLS` | written locally | written to `../HILLS.<id>`, all walkers see `../HILLS.*` | shared bias |
| `topol.top` | 1 | per walker (same file, copied for grompp isolation) | — |
| `metad.tpr` | 1 | per walker, grompp'd from per-walker `start.gro` | each walker has unique starting coords |
| `start.gro` | 1 (post-equilibration) | per walker, dumped from single_walker trajectory | different points along s(R) |
| `COLVAR` | 1 | per walker | analyse individually then aggregate |
| Walker bias coupling | — | `WALKERS_N=10, WALKERS_RSTRIDE=1000` | new parameters, SI-quoted and our-choice |
| Physics params (SIGMA, LAMBDA, HEIGHT, PACE, BIASFACTOR, TEMP, ADAPTIVE) | same | same | VERIFY via `diff` in verification block below |

---

## 8. FAQ

**Q: 为什么不自动选初始 10 帧（e.g. 每 5 ns 一帧）?**
A: Yu Zhang 2026-04-09 directive (L2859). SI says "covering approximately
all the conformational space available" which is a qualitative criterion.
Every-N-frames picks by simulation time, not by conformational diversity;
KMeans on (s, z) is closer to the spirit of the SI, but a human eye must
still verify the candidates don't collapse onto a single basin.

**Q: 10 walkers 能否扩展到 15 或 20?**
A: Possible in principle (PLUMED has no hard cap). But SI says "10 replicas"
so strict replication says stay at 10. Scaling up also changes the per-walker
convergence profile: 15 walkers share bias 50% faster but each walker sees
more "competing" Gaussians, which can slow free-diffusion exploration.
Re-run convergence analysis if you scale.

**Q: 出现 `bck.*.HILLS` 怎么办?**
A: FP-026 recurrence. PLUMED created a backup because HILLS already exists
and `RESTART` was not specified — meaning 10-100 ns of bias is about to be
silently discarded. `scancel` immediately; never restart without
`gmx convert-tpr -extend <ps>` + `plumed_restart.dat` (first line `RESTART`).

**Q: `mpirun -np 10 gmx_mpi mdrun -multidir` 要不要手动分配 GPU?**
A: With `#SBATCH --gres=gpu:10` on one node, GROMACS 2026 auto-distributes
rank → GPU 1:1 via `CUDA_VISIBLE_DEVICES`. If you run on 2 nodes × 5 GPUs,
add `-gpu_id 0123401234` explicitly. On Longleaf's `volta-gpu` partition,
single-node-10-GPU jobs are currently routed only to the Tesla V100 nodes.

**Q: Why not use the shell `export WALKER_ID=$i` approach from the task brief?**
A: Because PLUMED reads plumed.dat inside the GROMACS mdrun subprocess, and
env-var propagation across MPI ranks in multidir mode is unreliable (PLUMED
parses plumed.dat once per rank but in each rank's working dir). The
baked-in per-walker plumed.dat (sed substitution at setup time) eliminates
this class of bug entirely. The setup_walkers.sh sanity-checks that the
`__WALKER_ID__` sentinel is gone and the correct integer is present.

---

## 9. Verification commands

```bash
cd replication/metadynamics/multi_walker/

# Syntax check
bash -n setup_walkers.sh
bash -n submit_array.sh

# Physics-params parity vs single_walker (only WALKERS_* should differ)
diff <(grep -v '^#' plumed.dat | grep -v '^$') \
     <(grep -v '^#' ../single_walker/plumed.dat | grep -v '^$')
# Expected diff: PATH REFERENCE line (../path_gromacs.pdb vs path_gromacs.pdb),
# METAD FILE (../HILLS vs HILLS), plus WALKERS_N/ID/DIR/RSTRIDE additions.
# No SIGMA/HEIGHT/PACE/BIASFACTOR/TEMP/LAMBDA change.
```

---

## 10. File manifest

| File | Purpose | Lines |
|------|---------|-------|
| `plumed.dat` | MetaD input template with `__WALKER_ID__` sentinel | ~50 |
| `setup_walkers.sh` | Two-phase bootstrap: KMeans candidates → PyMOL QA → commit | ~180 |
| `submit_array.sh` | Slurm job, 10 MPI ranks, `gmx mdrun -multidir`, pre+post asserts | ~110 |
| `README.md` | This file | ~220 |

To be produced at runtime:
- `candidate_frames.csv` (Phase 1 output)
- `walker_0/..walker_9/` subdirs (Phase 2 output)
- `HILLS.0..HILLS.9` (shared bias, written by PLUMED during production)
- `multi_walker-<jobid>.out/err` (Slurm logs)

---

## 11. Ambiguity log (for Codex second-review)

The SI does not specify:
- **WALKERS_RSTRIDE**: we chose 1000 steps = 2 ns (PLUMED tutorial convention).
  Alternatives: 500 (tighter coupling, 2× filesystem load) or 5000 (looser).
- **Snapshot selection criterion**: SI says "covering approximately all the
  conformational space available" — we implement this as KMeans on (s, z)
  followed by mandatory human PyMOL QA.
- **Per-walker exact length**: SI gives the range "50-100 ns". We default to
  the `-maxh 71.5` wall-time cap which, at ~30-50 ns/day per V100, gives
  each walker 80-100 ns — middle-to-upper of the SI range.
- **GPU topology**: SI does not specify single-node vs multi-node; we default
  to single-node 10-GPU (`--nodes=1 --gres=gpu:10`) for NVLink bandwidth and
  to avoid inter-node MPI overhead during HILLS sync.

None of these change the physics; they are operational choices that should
be revisited if convergence fails.
