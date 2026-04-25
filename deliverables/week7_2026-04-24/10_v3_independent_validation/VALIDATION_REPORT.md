# v3 Independent 10-Walker Validation Report

Date: 2026-04-24

Remote directory:

```text
/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_v3_validation
```

## What Was Validated

- v2 failure precondition confirmed: production was launched directly from
  coordinate-only `start.gro` files with `continuation = no` and `gen_vel = yes`.
- v3 validation bundle materialized in a separate directory; no production files
  were overwritten.
- 10 fresh seed frames were selected from `initial_seqaligned/COLVAR` using
  non-overlapping `s` windows, `z < 2.5`, `min_time_gap_ps = 100`, and
  `min_s_gap = 0.25`.
- All 10 extracted `start.gro` files are coordinate-only, as expected from
  `trjconv -dump`; this is explicitly handled by the NVT stage with
  `gen_vel = yes`.
- All 10 coordinate hashes are unique.
- `walker_00` EM `grompp` succeeded and wrote `em.tpr`.
- Slurm syntax/resource check passed with `sbatch --test-only`; no job remained
  in the queue.

## Seed Set

```text
walker_id target_s time_ps s z
00  1   5142.4  1.1243  0.2787
01  2   4947.2  1.5423  0.3042
02  3   3728.4  2.8249  0.3328
03  4   5243.8  4.2594  0.3967
04  5   8081.2  5.2769  0.3874
05  6   7918.6  5.8621  0.4021
06  7    563.2  6.6367  0.4169
07  8    332.2  7.6622  0.5561
08  9    462.2  8.6826  0.5878
09 10   6211.0  9.5739  0.8596
```

Seed assertions:

```text
manifest_seeds 10 s_std 2.7593 min_s_gap 0.4180
unique_start_hashes 10 of 10
ASSERTIONS_PASS
```

## Handoff Logic

Each walker has:

```text
start.gro  -> em.mdp    -> em.tpr
em.gro     -> nvt.mdp   -> nvt.tpr   # PLUMED off, gen_vel=yes
nvt.gro+cpt -> metad.mdp -> metad.tpr # PLUMED on, continuation=yes, gen_vel=no
```

This tests the proposed solution to the 10-walker failure without reusing v2's
unsafe direct-production launch.

## Remaining Action

The only validation step not run here is the actual short smoke job:

```bash
cd /work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_v3_validation
sbatch submit_v3_validation.sh
```

That command was intentionally not submitted automatically.
