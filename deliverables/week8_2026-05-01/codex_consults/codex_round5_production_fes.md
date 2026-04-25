# Codex Round 5 — Production health monitoring + early FES rendering + convergence criterion (2026-04-25)

CCB task: `20260425-161301-106-13057`
Reviewer: Codex
Context: A3 10-walker production launched as SLURM 45784112 at 16:08; PM asks (1) is it actually running, (2) when can we render the production FES for weekly report, (3) what's the convergence PASS criterion.

## Reply summary (verbatim sections in Codex_R5_full.md)

### Q1: Production health PASS/FAIL signatures by timepoint

| Timepoint | PASS signature | FAIL action |
|---|---|---|
| ~5 min | All active walkers have `em.gro`, most have `nvt.log`; no `LINCS WARNING`/`Fatal error`/`Segmentation fault`; PD-status walkers waiting on resources are OK | If active walker has EM/NVT fatal: `scancel 45784112`, preserve logs |
| ~30 min | `nvt.cpt` exists for active walkers, `metad.log` exists, `HILLS.N` files growing in shared `HILLS_DIR/`. After 1 ns MetaD: ~500 hill rows/walker. COLVAR finite, `p1.zzz` < 2.8 mostly, `uwall.bias` not exploding (walker_09 at z=2.00 starting OK; fail only on sustained z>2.8 or wall bias > ~50 kcal/mol) | Missing `HILLS.N` after MetaD started: stop, shared-HILLS config wrong |
| ~3 hr | All 10 walkers have HILLS files; HILLS growth = 1 hill/2 ps = 500 hills/ns ≈ 2500/walker at 5 ns; COLVAR rows = 5000/ns ≈ 25,000/walker at 5 ns; all `plumed.dat` show `WALKERS_DIR=../HILLS_DIR WALKERS_N=10` and unique `WALKERS_ID` | Any walker isolated with local HILLS dir or missing parent `HILLS.N`: stop; shared bias invalid |
| ~10 hr | HILLS rows ~12,500/walker at 25 ns; COLVAR ~125,000/walker; no negative bias, no LINCS/SETTLE; all 10 walkers still advancing | One walker crashed after shared-HILLS production started: stop and mark non-production-grade unless documented censor/restart policy |

### Q2: Earliest honest FES render

| Per-walker time | Description |
|---|---|
| 5 ns | "early 10-walker fingerprint", no basin-depth claims |
| **10 ns** | **MINIMUM for weekly deck (~5000 hills/walker)** |
| 25 ns | first semi-quantitative snapshot, still PROVISIONAL |
| 50 ns | SI-scale production endpoint for this launch |

### Q2b: PLUMED sum_hills command (compute node, snapshot copy)

```bash
ssh longleaf "srun -N1 -n1 -t 00:20:00 --mem=8G bash -lc '
module purge
module load anaconda/2024.02
source \$(conda info --base)/etc/profile.d/conda.sh
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
BASE=/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_production_2026-04-25
SNAP=\$BASE/fes_snapshots/snap_\$(date +%Y%m%d_%H%M%S)
mkdir -p \$SNAP
cp \$BASE/HILLS_DIR/HILLS.{0..9} \$SNAP/
cd \$SNAP
HILLS=\$(printf \"HILLS.%s,\" {0..9}); HILLS=\${HILLS%,}
plumed sum_hills --hills \"\$HILLS\" --outfile fes_sumhills.dat --mintozero --kt 0.695 --min 0.5,0.0 --max 15.5,2.8 --bin 300,100
echo \$SNAP/fes_sumhills.dat
'"
```

(`--kt 0.695` = kBT at 350 K in kcal/mol; `--mintozero` = zero baseline)

### Q2c: matplotlib pseudocode (production FES contour)

See `plot_production_fes_snapshot.py` (templated for auto-render once HILLS hit 10 ns/walker).

### Q3: Convergence PASS criterion (SI gave no numeric; defensible thresholds)

| Criterion | PASS | PROVISIONAL | FAIL |
|---|---|---|---|
| All 10 walkers contributed | ≥45 ns each | ≥30 ns each | <30 ns or any walker crashed |
| `\|ΔG_PC−O(50ns) − ΔG_PC−O(40ns)\|` | ≤ 0.5 kcal/mol | 0.5–1.0 kcal/mol | > 1.0 kcal/mol |
| `\|ΔG_C−PC(50ns) − ΔG_C−PC(40ns)\|` | ≤ 0.5 kcal/mol | 0.5–1.0 kcal/mol | > 1.0 kcal/mol |
| Leave-one-walker-out jackknife half-width | ≤ 1.0 kcal/mol | 1.0–1.5 kcal/mol | > 1.5 kcal/mol |
| Basin minimum s shift over last 20 ns | < 0.5 | 0.5–1.0 | > 1.0 |

### Q3c: PROVISIONAL ship language for 2026-05-01

If status=PROVISIONAL by deadline:
- Frame as "10-walker production FES snapshot, not converged thermodynamic label"
- `label_grade = EVAL_ONLY` (NOT TRAIN)
- Use ONLY for L0/L1: path coverage, basin locations, qualitative O/PC/C sampling
- Do NOT report `P_O`, `P_PC`, `P_C` as populations or ΔG labels
- State drift number explicitly: "ΔG_PC−O still drifting >1 kcal/mol over final 10 ns; convergence_grade=PROVISIONAL"
