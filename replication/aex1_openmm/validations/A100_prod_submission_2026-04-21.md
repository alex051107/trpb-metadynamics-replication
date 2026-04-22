# Aex1 A100 production submission — 2026-04-21

## Scope

- Goal: launch the 500 ns Aex1 OpenMM cMD production run on Longleaf A100 after the post-fix smoke validations.
- Branch: `aex1-openmm-parallel`
- Submission job ID: `44955655`
- Partition: `a100-gpu`
- Walltime: `48:00:00`
- Run dir: `/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm/prod`

## State reuse decision

- Reused the validated A100 smoke equilibration from `/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm/smoke_a100`.
- Seeded `prod/` with:
  - `nvt_final_state.xml`
  - `npt_final_state.xml`
  - `nvt_final.pdb`
  - `npt_final.pdb`
- Cleared any stale production files in `prod/` before submission:
  - `prod_progress.json`
  - `prod_state.xml`
  - `prod_final_state.xml`
  - `prod.log`
  - `prod.dcd`
  - `prod_final.pdb`
  - `run_summary.json`

> Why: `run_aex1_cmd.py` skips NVT/NPT when `nvt_final_state.xml` and `npt_final_state.xml` already exist in the target workdir. This preserves the smoke-validated starting state and avoids redoing the first 1 ns.

## Submission command shape

- Script: `replication/aex1_openmm/slurm/aex1_cmd_prod.sbatch`
- Runtime overrides:
  - `MODE=production`
  - `PROD_NS=500`
  - `RUN_DIR=/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm/prod`
  - `ENV_PREFIX=/work/users/l/i/liualex/conda/envs/md_setup_trpb`

## Scheduler state at submission time

- `squeue`: `PENDING`
- `squeue --start`: no ETA assigned yet at submission-time poll

## Expected runtime

- A100 smoke production segment measured `278.273 ns/day`.
- Simple throughput estimate for `500 ns`:
  - `500 / 278.273 = 1.797 days`
  - `≈ 43.1 hours`
- Requested walltime `48 h` therefore leaves about `4.9 h` overhead margin.
