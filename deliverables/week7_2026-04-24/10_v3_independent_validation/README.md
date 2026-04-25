# 10 · v3 Independent 10-Walker Validation

Purpose: validate the 10-walker fix in an isolated Longleaf directory before any
production resubmission.

The validation bundle deliberately separates three questions:

1. Seed selection: 10 unique pilot frames, non-overlapping `s` windows, `z < 2.5`,
   and `std(s) > 2.0`.
2. Relaxation chain: coordinate-only `start.gro` must go through EM, then NVT
   with PLUMED off and `gen_vel=yes`.
3. Production handoff: MetaD must start from `nvt.gro + nvt.cpt` with
   `continuation=yes` and `gen_vel=no`.

No script in this directory submits a production run.  The Slurm script is a
short smoke test with `nsteps=1000` for NVT and production unless regenerated
with longer MDPs.

Longleaf setup:

```bash
cd /work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23
python3 seqaligned_walkers_v3_validation/materialize_v3_validation.py
python3 seqaligned_walkers_v3_validation/materialize_v3_validation.py --write --extract
bash -n seqaligned_walkers_v3_validation/submit_v3_validation.sh
sbatch --test-only seqaligned_walkers_v3_validation/submit_v3_validation.sh
```

Only after that smoke-test script is explicitly approved should it be submitted.
