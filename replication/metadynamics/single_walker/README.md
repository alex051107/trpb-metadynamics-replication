# `single_walker/` — 当前生产目录

This folder holds the four files currently driving the active well-tempered
metadynamics run on Longleaf. It is the authoritative *clean* copy; the
*annotated* teaching versions live in `../annotated/` and must stay
byte-identical after comment stripping (see `../annotated/README.md`).

## 状态 (2026-04-17)

- **Longleaf Job 44008381** running in
  `/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/`.
- Started 2026-04-16 as a 10 ns probe; extended to 50 ns via
  `../../../.worktrees/probe-extension/replication/metadynamics/single_walker/extend_to_50ns.sh`.
- Latest pull (2026-04-17 12:33): **25.56 ns simulated, max s(R) = 2.794**.

## 文件 (MD5 verified 2026-04-17)

| 文件 | MD5 | 最后修改 | 用途 |
|---|---|---|---|
| `plumed.dat` | `aca3f0c4d23ee4d2f8cb6dcb14383908` | 2026-04-15 | PLUMED 输入, FP-024 修复版 (adaptive sigma + floor/ceiling) |
| `metad.mdp` | `83cedc03842d23352cff347d205c8331` | 2026-04-09 | GROMACS MD 参数 (350 K, 2 fs, NPT, 50 ns stop) |
| `submit.sh` | `edf6c00ebaef9300bd35df9c936153af` | 2026-04-09 | Slurm 提交脚本 (Longleaf volta-gpu) |
| `path_gromacs.pdb` | `cbc88225f516d11f07b78d312c9cdfdb` | 2026-04-09 | 15 帧 O→C 路径参考 (112 Cα, Å, no trailing END) |

Re-compute with:

```bash
cd replication/metadynamics/single_walker
md5 plumed.dat metad.mdp submit.sh path_gromacs.pdb
```

## 运行前提

To actually `sbatch submit.sh` you need two more files that are **not** in
this folder (large binaries derived from AMBER, excluded from git):

- `start.gro` (≈ 2.7 MB) — converted from `prod_500ns.rst7` via
  `../conversion/convert_amber_to_gromacs.py`.
- `topol.top` (≈ 3.3 MB) — same conversion step.

Both live on Longleaf in
`/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/`.

## 参数一眼看

| Parameter | Value | Source |
|---|---|---|
| λ (LAMBDA) | 379.77 nm⁻² | SI-derived via `path_cv/generate_path_cv.py`, FP-022 修正 |
| SIGMA (initial) | 0.1 nm | Our-choice, 2026-04-15 post-FP-024 |
| SIGMA_MIN | 0.3, 0.005 | Our-choice (FP-024 floor, s/z respectively) |
| SIGMA_MAX | 1.0, 0.05 | Our-choice (FP-024 ceiling, s/z respectively) |
| HEIGHT | 0.628 kJ/mol (0.15 kcal/mol) | SI-quote |
| PACE | 1000 steps | SI-quote |
| BIASFACTOR | 10 | SI-quote |
| TEMP | 350 K | SI-quote (thermophile, *P. furiosus*) |

Full per-parameter Source tags + sensitivity annotations: `../annotated/plumed_annotated.dat`.
Parameter provenance matrix: `../../parameters/JACS2019_MetaDynamics_Parameters.md`.

## 相关

- SSH inspection checklist (pull HILLS / COLVAR / log from Longleaf):
  `./SSH_INSPECTION_CHECKLIST.md` (Track G 产出, pending).
- 50 ns timeline + decision gate log:
  `../../validations/2026-04-17_single_walker_timeline.md` (being drafted).
- Known failure patterns that touch this folder: FP-020, FP-022, FP-023,
  FP-024 (see `../../validations/failure-patterns.md`).

## Edit protocol

Never hand-edit a file here. The workflow is:

1. Change `../annotated/<file>_annotated.*` with a justification comment.
2. Strip comments + blanks → compare byte-for-byte with this folder (see
   `../annotated/README.md` for the exact `diff` invocation).
3. Copy the regenerated clean file into this folder.
4. Re-hash MD5 and update the table above *plus* `../annotated/README.md`.
5. Push to Longleaf and verify MD5 parity before `sbatch`.
