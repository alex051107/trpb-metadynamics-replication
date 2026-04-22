# A100 smoke validation — 2026-04-21

## Scope

- Goal: confirm that the post-FP-028 `md_setup_trpb` env runs the Aex1 OpenMM smoke cleanly on Longleaf A100 after the CUDA 12.4 repin.
- Job ID: `44952881`
- Partition: `a100-gpu`
- Node: `g141602`
- State: `COMPLETED`
- Exit code: `0:0`
- Elapsed: `00:11:51`
- Run dir: `/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm/smoke_a100`

## Environment

- Env prefix: `/work/users/l/i/liualex/conda/envs/md_setup_trpb`
- GPU: `NVIDIA A100-PCIE-40GB`
- Driver: `590.48.01`
- `openmm`: `8.2.0`
- `openmm-plumed`: `2.1`
- `cuda-version`: `12.4`
- `cuda-nvrtc`: `12.4.127`

## Gates

- CUDA probe: `PASS`
  - `CUDA_PLATFORM_OK`
  - `cuda_platform CUDA`
  - `cuda_device_index 0`
  - `cuda_precision mixed`
- System total charge after solvation: `-0.000000 e`
- Minimize max force: `2665.139413 kJ/mol/nm`
- Full smoke MD: `PASS`

## Performance

- NVT `0.5 ns`: `386.997 ns/day`
- NPT `0.5 ns`: `276.614 ns/day`
- Production `1.0 ns`: `278.273 ns/day`

## Build / parameterization checks

- `ligand_code=PLS`
- `pls_heavy_atom_count=22`
- `pls_formal_charge=-2.000000`
- `pls_partial_charge_sum=-2.000000`
- `na_added=3`
- `atom_count_post_solvation=47385`
- `selected_small_molecule_forcefield=gaff-2.11`

## Interpretation

- The post-fix CUDA 12.4 env is validated on both Longleaf GPU families now:
  - V100 smoke `44951229` completed cleanly
  - A100 smoke `44952881` completed cleanly
- FP-028 is closed for the current `md_setup_trpb` env and Aex1 OpenMM smoke path.
- No new blocker was observed for proceeding to the 500 ns A100 production submission.
