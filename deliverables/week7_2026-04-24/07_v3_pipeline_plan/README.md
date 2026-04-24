# 07 · v3 10-walker pipeline plan

Design for the third and (hopefully) final 10-walker production attempt. Built on Codex's root-cause diagnosis of v2 (see `../06_v2_10walker_crashed/codex_root_cause.md`): seed frames from a biased pilot xtc must go through EM + NVT before production MetaD, and the seed-selection script must guard against duplicate frames.

**Status**: scripts and assertion suite are drafted below and in `submit_v3_template.sh` / `assertion_suite.py`. Awaiting PI sign-off before actually submitting.

## Files

| File | What it is |
|---|---|
| `submit_v3_template.sh` | Three-stage SLURM script (EM → NVT → production MetaD). Array job; one walker per array task. |
| `assertion_suite.py` | Guard clauses to be added to `materialize_walkers_v3.py` before seeds are handed to grompp. |
| `mdp_templates.md` | Key MDP parameters for each stage. |

## Pipeline in three sentences

1. For each of 10 seed frames (pilot COLVAR, one per target_s ∈ {1..10}, minimum z, **unique frame enforced**): run 1000-step steepest-descent EM to eliminate bad contacts carried from the biased pilot geometry.
2. Run 100 ps NVT at 350 K with PLUMED **off**, `gen_vel=yes`, so a proper Maxwell-Boltzmann velocity distribution is regenerated on a relaxed geometry.
3. Continue from the NVT checkpoint into production MetaD with Miguel's primary parameter contract (PLUMED on, shared HILLS_DIR, `WALKERS_N=10`).

## Why this closes the v2 failure mode

| v2 failure | How v3 addresses it |
|---|---|
| Biased-pilot seed has constraint-stretched methyl bonds (4463-4465) | EM relaxes to `fmax < 1000 kJ/mol/nm` — bad contacts vanish |
| No velocities in `.gro` from `trjconv -dump` | NVT with `gen_vel=yes` regenerates MB distribution on relaxed geometry |
| LINCS immediately fails on production step 1 | NVT 100 ps ensures LINCS has converged stable constraints before bias begins |
| Two pairs of walkers got identical seeds | `assertion_suite.py` enforces unique seed frames + `std(s) > 2.0` diversity |

## Launch gate

Before `sbatch submit_v3_template.sh`:
1. PI approves (2026-05-01 decision or earlier).
2. All assertions in `assertion_suite.py` pass on the materialized seed set.
3. Dry-run `gmx mdrun -deffnm em -ntmpi 1` succeeds on walker_00's `em.tpr` as a 1-walker sanity check.
4. Probe-sweep archive cleanup (delete `seqaligned_walkers_v2/walker_NN/metad*` from Longleaf to avoid path confusion).

## Expected deliverable

After 12 – 24 h of wall-clock (array parallel on 10 × A100), we should have:
- `HILLS_DIR/HILLS.0 … HILLS.9` — shared bias deposition.
- 10 × `metad.xtc` of ~50 ns each (Miguel PACE=500 + BIASFACTOR=10 gives ~500 ns aggregate).
- Block-analysis error bars on `sum_hills.py` output.
- PC crystal 2D occupancy projection (5DW0, 5DW3 at least).

If `max(s) > 12` is not reached in aggregate, the WT FES is not converged and we return to PI for priority call.
