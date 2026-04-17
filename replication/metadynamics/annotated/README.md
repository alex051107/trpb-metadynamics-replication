# `metadynamics/annotated/` — MetaD stage reference package

## 两个版本各装什么（快速查阅）

| View | File | Contains |
|------|------|----------|
| Clean production | `plumed.dat` | PLUMED directives only (byte-identical to `single_walker/plumed.dat`) |
| Teaching | `plumed_annotated.dat` | Directives + Source + sensitivity (每个数值参数带 Source 标签 + "调大 2× / 调小 2×" 影响) |

Use **clean** to see exactly what is running; use **teaching** to understand
why each parameter was chosen and what happens if it drifts.

---

This folder holds two views of the same WT-MetaD setup used for Job 42679152
on Longleaf (`/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/`):

1. **Annotated (teaching) versions** — heavily commented walkthroughs of each
   file. Useful for understanding *what* every parameter means and *why* it was
   picked. All annotated files are kept in sync with the PATHMSD pivot:
   strip every comment + blank line from an `_annotated` file and you get back
   the corresponding production file line-for-line.
2. **Clean (production) versions** — byte-identical copies of the files
   currently running on Longleaf under the PATHMSD pivot (2026-04-09). Use
   these if you want to see *exactly* what the running simulation is using.

## File layout

| Purpose | Annotated (教学版) | Clean (生产版, byte-identical to `single_walker/`) | Annotated action lines match Clean? |
|---|---|---|---|
| PLUMED input | `plumed_annotated.dat` (12.8 KB, 2026-04-09 rewrite for PATHMSD) | `plumed.dat` (2.1 KB) | ✅ |
| GROMACS MDP | `metad_annotated.mdp` (15.5 KB, unchanged since 2026-04-04) | `metad.mdp` (1.6 KB) | ✅ |
| Slurm submit | `submit_annotated.sh` (12.6 KB, LAMBDA echo + input-file notes patched 2026-04-09) | `submit.sh` (0.9 KB) | ✅ |
| Path CV reference | — | `path_gromacs.pdb` (130 KB, 15 frames × 112 Cα, in Å, no trailing `END`) | — |
| LaTeX parameter reference | `parameter_reference.{tex,pdf}` | — | — |

**Important naming convention**: files with the `_annotated` suffix are the
teaching versions. Files without that suffix are the current production
snapshots.

## 干净版 vs 教学版

这个文件夹里每个 PLUMED/Slurm/MDP 文件都有两个形态：

- **`plumed.dat`（clean / 干净版）**：byte-identical 到
  `single_walker/plumed.dat`（也就是 Longleaf 上跑的那一份）。只有 PLUMED
  directive 行，没有 `Source:` 标签，没有敏感性分析。作用是给 `gmx grompp`
  读、给 diff-verification 用。
- **`plumed_annotated.dat`（teaching / 教学版）**：和 clean 版有完全一样
  的 directive 行，外加 `#` 注释块：
  1. 每个数值参数前一个 `# ─── PARAM = value ───` 教学块
  2. `Source:` 标签（SI-quote / SI-derived / Our-choice / PLUMED-default /
     Legacy-bug — 语义见 `replication/parameters/PARAMETER_PROVENANCE.md`
     顶部的 Source legend）
  3. "调大 2×" 和 "调小 2×" 各自后果
  4. 推荐区间（来自 PLUMED docs / SI / 文献）

用户阅读教学版的核心目的是回答两个问题：
「每个参数变大变小后会怎样？」+「Source 来源是否可信？」

### 验证两版同步（empty output = 同步）

编辑完 `plumed_annotated.dat` 后必须跑这条，**输出必须是空**：

```bash
cd replication/metadynamics/annotated
diff <(grep -v '^#' plumed_annotated.dat | grep -v '^$') plumed.dat
# expected: empty output = in sync
```

如果 `plumed.dat` 本身也带 header 注释（现在是这样），用双向剥离版本：

```bash
diff <(grep -v '^#' plumed_annotated.dat | grep -v '^$') \
     <(grep -v '^#' plumed.dat          | grep -v '^$')
# expected: empty output = directives in sync
```

非空 = 你的注释块不小心破坏了 action 行（例如把 `path: PATHMSD ...`
吞进注释里了）。立刻修复，不要 commit。

---

## MD5 parity (verified 2026-04-17, post FP-024 fix)

```
aca3f0c4d23ee4d2f8cb6dcb14383908  plumed.dat        (2026-04-15, FP-024 SIGMA floor/ceiling)
83cedc03842d23352cff347d205c8331  metad.mdp         (unchanged since 2026-04-04)
edf6c00ebaef9300bd35df9c936153af  submit.sh         (unchanged since 2026-04-09)
cbc88225f516d11f07b78d312c9cdfdb  path_gromacs.pdb  (unchanged since 2026-04-09)
```

These four files match `replication/metadynamics/single_walker/` and
`/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/` on Longleaf
bit-for-bit. (Pre-FP-024 plumed.dat md5 was `ba2dbd89...`, archived at
`replication/metadynamics/archive_pre_2026-04-15/single_walker__plumed.dat.bak_2026-04-15`.)

## Edit history

| Date | File | Change |
|---|---|---|
| 2026-04-04 | `metad_annotated.mdp`, `submit_annotated.sh` | First authored (heavy Chinese teaching comments) |
| 2026-04-08 | (now deleted) old `plumed_annotated.dat` | Authored for the intermediate `FUNCPATHMSD + SQUARED` fix (FP-022) |
| 2026-04-09 | **new** `plumed_annotated.dat` | **Rewritten from scratch** for the current PATHMSD pivot (FP-020 re-diagnosis). Old FUNCPATHMSD version deleted. |
| 2026-04-09 | `submit_annotated.sh` | Patched: LAMBDA echo 3.3910 → 379.77, input-file description `frames/` → `path_gromacs.pdb` |
| 2026-04-09 | `plumed.dat`, `metad.mdp`, `submit.sh`, `path_gromacs.pdb` | Added as byte-identical clean copies of `single_walker/` |

**All annotated files now describe the same PATHMSD setup as the clean
production files in this folder.** Specifically:

- `plumed_annotated.dat` → strip every `#` comment and blank line → the 3
  resulting action lines are **byte-identical** to `plumed.dat`
- `submit_annotated.sh` → strip every `#` comment and blank line → the
  resulting directives are **byte-identical** to `submit.sh`
- `metad_annotated.mdp` → strip every `;` comment and blank line → the
  resulting parameter lines have the **same set of `key = value` pairs**
  as `metad.mdp`. Two pairs (`pme-order`, `fourier-spacing`) appear in a
  different order for teaching reasons (the annotated version groups them
  under the "PME electrostatics" section, whereas the clean version keeps
  GROMACS's own emit order). GROMACS `.mdp` parsing is order-insensitive,
  so both files produce identical `metad.tpr` after `gmx grompp`.

Independent verification (run from this folder):

```bash
diff <(grep -v '^#' plumed_annotated.dat | grep -v '^$') \
     <(grep -v '^#' plumed.dat          | grep -v '^$')        # empty = match

diff <(sed 's|#.*||' submit_annotated.sh | sed 's/[[:space:]]*$//' | grep -v '^$') \
     <(sed 's|#.*||' submit.sh          | sed 's/[[:space:]]*$//' | grep -v '^$') # empty = match

strip_mdp() { sed 's/;.*//' "$1" | sed 's/[[:space:]]*$//' | grep -v '^$' | sort; }
diff <(strip_mdp metad_annotated.mdp) <(strip_mdp metad.mdp)    # empty = match (after sort)
```

See `replication/validations/failure-patterns.md` (FP-020, FP-022, FP-023)
and `reports/TechWalkthrough_2026-04-09.md` Section 5-6 for the full bug
history that led to this final state.

## What is *not* in this folder

To actually run `submit.sh` you need two more files that live in
`single_walker/` on Longleaf but are **not** tracked in git because they are
large binaries derived from AMBER output:

- `start.gro` (≈ 2.7 MB) — GROMACS-format starting coordinates, converted from
  `classical_md/output/prod_500ns.rst7` via
  `replication/metadynamics/conversion/convert_amber_to_gromacs.py`
- `topol.top` (≈ 3.3 MB) — GROMACS-format topology, same conversion step

If you need to reproduce a run from this folder, either:

1. **Recommended**: copy these four files (`plumed.dat`, `metad.mdp`,
   `submit.sh`, `path_gromacs.pdb`) into a fresh workspace that already has
   `start.gro` + `topol.top`, then `sbatch submit.sh` there; or
2. Re-run `convert_amber_to_gromacs.py` on Longleaf to regenerate
   `start.gro` + `topol.top`.

## Not runnable in place

`sbatch submit.sh` directly from `annotated/` will **fail** at the `gmx grompp`
step because `start.gro` and `topol.top` are not present here. That is
intentional: this folder is a documentation reference, not a working directory.
The real working directory is
`/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/` on Longleaf,
where Job 42679152 is currently running (see
`reports/TechWalkthrough_2026-04-09.md` §10).
