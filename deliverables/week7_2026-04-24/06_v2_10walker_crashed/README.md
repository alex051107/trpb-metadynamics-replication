# 06 · v2 10-walker production (ALL FAILED exit 139)

Second attempt. Submitted 2026-04-24 ~10:00 as SLURM array 45570699 on `volta-gpu`. Seed frames were CV-diverse this time (one frame per `target_s ∈ {1..10}` from the pilot COLVAR, `|s - target_s| < 0.1`, minimum `z`). All 10 walkers crashed within 14 min to 3 h 05 min with LINCS blow-up on the same atom pair 4463–4465. Root cause diagnosed by Codex: missing local relaxation (no EM, no NVT) between seed extraction and production.

## Files

| File | What it is |
|---|---|
| `sacct_exit_codes.txt` | SLURM accounting output — job state, elapsed, exit code per walker. |
| `slurm_crash_tail_w00.txt` | Last 60 lines of `slurm-seqaligned_v2-45570699_0.out`, showing the LINCS blow-up progression. |
| `colvar_blowup_evidence.txt` | Last 3 rows of each walker's COLVAR showing negative `metad.bias`. |
| `seed_duplication_evidence.txt` | First-row `path.s` of each walker showing that w0/w1 and w5/w6 collided on the same seed frame. |
| `codex_root_cause.md` | Full text of Codex's diagnosis plus our response-plan outline. |

## Failure summary

```
sacct -j 45570699 --format=JobID,State,ExitCode,Elapsed

45570699_0   FAILED   139:0   00:13:56
45570699_1   FAILED     1:0   00:35:35
45570699_2   FAILED   139:0   00:55:40
45570699_3   FAILED   139:0   01:48:41
45570699_4   FAILED   139:0   03:05:39   ← longest before crash
45570699_5   FAILED   139:0   01:14:20
45570699_6   FAILED   139:0   01:27:10
45570699_7   FAILED   139:0   01:54:19
45570699_8   FAILED   139:0   01:38:43
45570699_9   FAILED   139:0   — (log tail unavailable)
```

## LINCS blow-up signature (walker 0, last visible steps)

```
Step 90093, t = 180.186 ps:  LINCS WARNING on atoms 4463-4465  (CH3 methyl, angle 39°)
Step 90098, t = 180.196 ps:  LINCS WARNING, rms 0.154, max 6.535
  atoms 4463-4465: constraint 0.6979 Å vs 0.1097 Å target  (6.4× stretched)
  atoms 4461-4462: constraint 0.7633 Å vs 0.1013 Å target  (7.5× stretched)
Step 90099, t = 180.198 ps:  rms 0.592, max 32.429
  atoms 4463-4465: constraint 3.6672 Å vs 0.1097 Å target   (33× stretched)
step 90099: One or more water molecules can not be settled.
→ Segmentation fault (core dumped)
```

## COLVAR corruption signatures

`metad.bias` is a sum of positive Gaussians and must be ≥ 0. The last rows of several walkers show deep negative values, which is downstream corruption after LINCS destabilises the coordinates and the Cα stencil that feeds PATHMSD falls out of bounds:

```
w0 end (180 ps)  : metad.bias = -26.5
w5 end (786 ps)  : metad.bias = -548,  wall4.bias = 11.4
w7 end (1442 ps) : metad.bias = -838,  wall4.bias = 39.2, wall_s = 125508
```

## Seed-selection bug

First-row `path.s` values from each walker's COLVAR:

```
w0 = 1.9871   w1 = 1.9871  ← duplicate seed frame
w2 = 2.8015
w3 = 3.5621
w4 = 4.3168
w5 = 6.5957   w6 = 6.5957  ← duplicate seed frame
w7 = 8.1723
w8 = 8.4764
```

At least two pairs of walkers received identical seed frames. The materialize script lacked a unique-frame guard; when the pilot COLVAR was sparse in a target-s window, the "min-z" candidate for adjacent target bins collided.

## Codex root-cause (verbatim)

> "Most consistent with biased-pilot coordinate seeds being launched directly into fresh production without local relaxation. The common atom pair 4463-4465 across walkers points to a reproducible bad-contact / constraint instability in the seed ensemble, not random GPU failure. Missing velocities in dumped `.gro` also means production likely regenerated / assigned velocities inconsistently with a pre-biased geometry."

The `.gro` files from `gmx trjconv -dump` contain **positions only**, no velocities. The v2 submit script ran `gmx mdrun -deffnm metad -plumed plumed.dat` directly with no EM and no NVT equilibration, so GROMACS regenerated velocities on a geometry still carrying the strain of a biased-MetaD snapshot. LINCS then failed on the stressed methyl bonds (atom 4463-4465 consistently across walkers) and SETTLE cascaded on water bad-contacts.

See `07_v3_pipeline_plan/` for the fix.
