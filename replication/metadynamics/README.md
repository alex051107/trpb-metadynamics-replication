# `replication/metadynamics/` — MetaD 相关文件总目录

This directory collects every artifact tied to the well-tempered metadynamics
(WT-MetaD) stage of the TrpB replication: production inputs, the one-off path
CV + AMBER→GROMACS conversion assets, teaching annotations, and archived
pre-2026-04-15 attempts. If you just walked in cold, read this file first.

## 当前状态 (2026-04-17)

- **Single-walker production run**: Longleaf **Job 44008381** is running
  (started 2026-04-16 after `extend_to_50ns.sh` extended the 10 ns probe to
  50 ns). Latest pull (2026-04-17 12:33): **25.56 ns simulated, max s(R) = 2.794**.
- **Next decision gate**: once the 50 ns single-walker completes, decide
  whether to launch Phase 2 (10-walker, `multi_walker/`) or jump to Phase 3
  (FES analysis). The decision criterion is documented in
  `replication/validations/2026-04-08_path_cv_lambda_bug.md` and updated in
  `NEXT_ACTIONS.md`.
- **Current production `plumed.dat`**: `single_walker/plumed.dat` — the
  2026-04-15 FP-024 fix (adaptive sigma with floor + ceiling). Older attempts
  live in `archive_pre_2026-04-15/`.

## 子目录用途

| 目录 | 用途 | 是否当前活跃 |
|---|---|---|
| `single_walker/` | 现在跑的单 walker 生产文件 (`plumed.dat`, `metad.mdp`, `submit.sh`, `path_gromacs.pdb`) | ✅ 活跃 |
| `annotated/` | 教学版: 每参数都带 Source + sensitivity 注释; 干净版是 `single_walker/` 字节相同拷贝 | ✅ 活跃 |
| `multi_walker/` | 10-walker 协议 (SI p.S3-S4); Phase 2 触发后使用 | ⏸ ready but not yet launched |
| `path_cv/` | 一次性: O→C 15 帧路径生成 (`generate_path_cv.py`, `path.pdb`, `summary.txt`) | ✅ 已完成 |
| `conversion/` | 一次性: AMBER→GROMACS 坐标转换 (`convert_amber_to_gromacs.py`) | ✅ 已完成 |
| `archive_pre_2026-04-15/` | 历史与 `.bak_*` 文件 (FUNCPATHMSD 旧方案, 旧 `plumed_trpb_metad*.dat` 命名, Apr 1 stale `metad.mdp`) | 🗄 归档 |

`extract_snapshots.sh` (top-level) is a one-off helper for pulling frames out
of the AMBER trajectory; it is not part of any active pipeline step.

## 关键文件 — 当前生产 MD5 (2026-04-17)

Verified from `replication/metadynamics/single_walker/` on this commit:

```
aca3f0c4d23ee4d2f8cb6dcb14383908  plumed.dat
83cedc03842d23352cff347d205c8331  metad.mdp
edf6c00ebaef9300bd35df9c936153af  submit.sh
cbc88225f516d11f07b78d312c9cdfdb  path_gromacs.pdb
```

Authoritative docs:

- Teaching reference (per-parameter Source + sensitivity): `annotated/README.md`,
  `annotated/plumed_annotated.dat`, `annotated/metad_annotated.mdp`,
  `annotated/submit_annotated.sh`, `annotated/parameter_reference.pdf`.
- Parameter provenance table (what comes from SI vs. our-choice):
  `replication/parameters/JACS2019_MetaDynamics_Parameters.md`.
- Campaign manifest: `replication/manifests/osuna2019_benchmark_manifest.yaml`.

## 相关脚本 (外部)

- `/.worktrees/probe-extension/replication/metadynamics/single_walker/extend_to_50ns.sh`
  — Slurm script that extended Job 44008381 from 10 ns to 50 ns (used
  `gmx convert-tpr -until 50000` + PLUMED `RESTART`).
- `/.worktrees/cv-audit/project_structures.py` — audits PATHMSD projections on
  reference frames; used before every rebuild of `path_gromacs.pdb`.

## 最近失败模式 (必读 before editing plumed.dat)

See `replication/validations/failure-patterns.md`:

- **FP-020** — `libplumedKernel.so` from conda is truncated; must build PLUMED
  2.9.2 from source. Fixed 2026-04-09.
- **FP-022** — `PATH` CV with `TYPE=OPTIMAL-FAST` requires λ in **nm⁻²**
  (379.77), not Å⁻² (3.39). Re-diagnosed 2026-04-09 (PATHMSD pivot).
- **FP-023** — `annotated/` must stay byte-identical to `single_walker/` after
  comment stripping.
- **FP-024** — Adaptive sigma needs both a floor (`SIGMA_MIN`) and ceiling
  (`SIGMA_MAX`) to keep hill widths in a physical range. Added 2026-04-15.
- **FP-025 / FP-026 / FP-027** — Recent parameter-provenance tracking gaps;
  see `replication/parameters/JACS2019_MetaDynamics_Parameters.md`.

## Ground rule

**Never edit `single_walker/*` directly.** Change `annotated/*_annotated.*`
first with the justification comment, regenerate the clean file by comment
stripping (see `annotated/README.md` for the exact `diff` invocations), then
copy it to `single_walker/` and re-verify MD5 parity on Longleaf before
resubmitting.
