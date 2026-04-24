# 05 · v1 10-walker production (SCANCELLED)

First attempt at 10-walker production. Submitted 2026-04-24 ~09:00 as SLURM array 45558834 on `volta-gpu`, scancelled at 22:05 after both PM and Codex flagged an FP-030 homogeneous-start violation.

## Files

| File | What it is |
|---|---|
| `submit_walkers.sh` | SLURM array script, 10 walkers. |
| `materialize_walkers.py` | Seed-materialization script for v1 — extracts 10 frames from 500 ns Ain cMD at `t = 50, 100, ..., 500 ns`. |

## Why scancelled

The 500 ns Ain classical MD trajectory had long equilibrated to the Open basin (`s ≈ 1`). So the "diverse" seeds at `t = 50, 100, …, 500 ns` all collapsed to the same CV region. Shared-HILLS MetaD requires walker distribution across CV space; otherwise it degenerates into "single walker × 10" and the parallelisation benefit is lost (FP-030 in the failure-pattern registry).

**Lesson**: time-diverse seeds are not the same as CV-diverse seeds. Sampling a biased CV space for seeds requires a biased trajectory (pilot COLVAR, not unbiased cMD), which is how v2 was designed — see `06_v2_10walker_crashed/`.

## Surviving data

v1 walkers did produce ~5000 COLVAR rows each (~1 ns/walker) before the scancel at ~45 min wall-clock. The data is scientifically suspect for reasons above; it is NOT used in the Week-7 FES figure.

HILLS and COLVAR files are kept on Longleaf at `/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers/` for audit purposes only.
