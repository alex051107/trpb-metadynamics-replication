# TrpB MetaDynamics Replication — Project Context

> **读取顺序 / Reading Order**:
> 1. **本文件** → 项目概览、当前状态、工作规则
> 2. `PIPELINE_STATE.json` → 当前处于哪个 pipeline 阶段
> 3. `failure-patterns.md` → 已知错误模式（**生成任何新文件前必读**）
> 4. `NEXT_ACTIONS.md` → 当前任务队列
> 5. `GLOSSARY.md` → 不认识的术语查这里
> 6. `PREFERENCES.md` → 用户的工作风格偏好

---

## 项目信息 / Project Info

**负责人**: Zhenpeng Liu, UNC Chapel Hill undergraduate (liualex@ad.unc.edu)
**目标**: 复刻 Osuna 组 JACS 2019 (DOI: 10.1021/jacs.9b03646) 中 TrpB 酶的 well-tempered MetaDynamics 模拟，展示计算生物学能力，准备 Caltech/Anima Lab 暑研
**SI 来源**: ja9b03646_si_001.pdf

---

## 当前状态 / Current Status (last updated: 2026-04-05)

| Milestone | Status | Notes |
|-----------|--------|-------|
| Paper reading (5 papers) | speed-brief-ready | JACS2019 speed brief generated |
| Resource inventory | **done** | All downloaded |
| MetaDynamics parameters extraction | **done** | From SI, fact-checked 2026-03-28 |
| SI protocol extraction | **done** | Full 5-phase protocol; 10 gaps identified |
| PLP parameterization (GAFF+RESP) | **done** | Ain_gaff.mol2 + Ain.frcmod, charge=-2 |
| System build (tleap) | **done** | 39,268 atoms, charge neutral, 4 Na⁺ |
| PDB residue verification | **done** | 5DVZ=LLP, 5DW0=PLS, 4HPX=0JO |
| O→C reference path (15 frames) | **done** | λ=3.39 nm⁻² (=0.034 Å⁻², vs SI 0.029) |
| Conventional MD (500 ns) | **done** | Job 40806029, 71.55 hrs, 22 GB |
| AMBER→GROMACS conversion | **done** | ParmEd, 39,268 atoms verified |
| PLUMED source build | **done** | 2.9.2 (conda 版残缺，从源码编译) |
| **Well-tempered MetaD** | **running** | Job 41514529, FUNCPATHMSD, ADAPTIVE=GEOM |
| FES reconstruction | NOT STARTED | After MetaD completes |

---

## 关键决策 / Key Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| MetaD engine | **GROMACS + PLUMED2** | SI used GROMACS 5.1.2 + PLUMED2; strict replication |
| Classical MD engine | **AMBER 24p3** (pmemd.cuda) | GPU acceleration; ff14SB equivalent to AMBER16 |
| Force field | ff14SB (protein) + GAFF (cofactor) | From SI p.S2 |
| Water model | TIP3P | From SI p.S2 |
| Temperature | 350 K | Thermophilic P. furiosus enzyme |
| Charge method | RESP @ HF/6-31G(d) | SI p.S2; AM1-BCC fails for PLP (FP-009) |

---

## HPC 环境 / HPC Setup (UNC Longleaf)

| Item | Value |
|------|-------|
| Username | liualex |
| Project dir | `/work/users/l/i/liualex/AnimaLab/` |
| AMBER | `module load amber/24p3` (GPU: pmemd.cuda) |
| PLUMED | `conda activate trpb-md` → PLUMED 2.9 |
| GROMACS | `conda activate trpb-md` → gmx 2026.0 (PLUMED patched ✓) |
| Gaussian | `module load gaussian/16c02` |

### Longleaf 目录结构

```
AnimaLab/
├── structures/              ← PDB 原始文件
├── parameterization/ain/    ← PLP RESP 参数化
├── system_build/            ← tleap 产出 (parm7, inpcrd)
├── classical_md/            ← AMBER 经典 MD
│   ├── inputs/              (.in 文件)
│   ├── slurm/               (提交脚本)
│   └── output/              (轨迹, 22GB prod_500ns.nc)
├── metadynamics/            ← GROMACS + PLUMED MetaD
│   ├── conversion/          (AMBER→GROMACS)
│   ├── path_cv/             (15-frame path.pdb)
│   ├── plumed/              (PLUMED 输入)
│   ├── single_walker/       (测试)
│   └── multi_walker/        (10-walker 生产)
├── analysis/                ← FES 分析
├── archive/                 ← 旧文件
└── logs/                    ← Slurm 日志
```

---

## 强制规则 / Mandatory Rules

### 1. Pipeline 阶段控制

项目分 6 个阶段，当前阶段由 `PIPELINE_STATE.json` 控制：

| # | Stage | 干什么 | 停下等审批的条件 |
|---|-------|--------|-----------------|
| 0 | Profiler | 论文 → frozen manifest | Manifest 需要人签字 |
| 1 | Librarian | 盘点资源 | 缺资源或无权限 |
| 2 | Janitor | 整理目录 | 路径冲突 |
| 3 | Runner | 生成脚本/提交作业 | 参数不确定 |
| 4 | Skeptic | 验证结果 | 科学有效性不确定 |
| 5 | Journalist | 写 report | 不需要停 |

检查当前阶段：`python3 pipeline_guard.py --check`
推进到下一阶段：`python3 pipeline_guard.py --advance`

### 2. 脚本化原则

> **任何 production 文件里的数值，必须是脚本输出，不是手工输入。**

脚本必须包含：
- 物理范围 assertion（如 `assert 0.01 < lambda < 0.1`）
- 单位标注（MSD 是 Å², RMSD 是 Å）
- 中间值打印（让 skeptic 能看到计算过程）
- 与 JACS 2019 SI 对应值的比较（偏差超过 10% 必须解释）

### 3. 独立复核

每次 Runner 产出新 artifact，必须独立验证（不接收之前的讨论上下文）。验证清单：数值来源追溯、assertion 存在、物理范围合理、与 SI 对比。

### 4. 错误处理三步曲

发现错误时，三件事缺一不可：
1. **修源文件**
2. **追加 failure-patterns.md**（FP-XXX 条目）
3. **写 validation note**（`replication/validations/YYYY-MM-DD_context.md`）

### 5. 严格复刻

- MetaDynamics: 必须用 **GROMACS + PLUMED2**（不用 AMBER 做 MetaD）
- 经典 MD: 可以用 **AMBER 24p3**

---

## 决策分离原则

三种决策不能混为一谈：
1. **科学决策**（测什么、为什么）→ PM（Zhenpeng）负责
2. **执行决策**（怎么跑软件）→ AI / 执行者负责
3. **下游集成声明**（结果对 pipeline 意味着什么）→ 需要明确讨论

---

## 关键文件索引 / Key Files

| File | Purpose |
|------|---------|
| `PIPELINE_STATE.json` | Pipeline 状态机 + artifact 验证规范 |
| `NEXT_ACTIONS.md` | 共享任务队列 |
| `PROTOCOL.md` | 6-stage pipeline 详细参考手册 |
| `GLOSSARY.md` | 所有术语定义 |
| `failure-patterns.md` | 17+ 个已知错误模式 |
| `PREFERENCES.md` | 用户工作风格偏好 |
| `osuna2019_benchmark_manifest.yaml` | 当前 campaign 冻结参数 |
| `JACS2019_MetaDynamics_Parameters.md` | SI 参数逐项对照表 |
| `pipeline_guard.py` | Pipeline 强制执行脚本 |
| `CHANGELOG.md` | 完整变更记录 |

---

## 术语速查 / Quick Terms

| Term | Meaning |
|------|---------|
| COMM domain | Communication domain, residues 97-184 of TrpB |
| Path CV | s(R) = progress along O→C path; z(R) = deviation from path |
| O / PC / C | Open / Partially Closed / Closed conformations |
| FEL | Free Energy Landscape |
| PLP | Pyridoxal phosphate cofactor |
| LLP | PDB name for PLP covalently linked to Lys82 (Ain intermediate) |
| AIN | Internal residue name (= LLP, just renamed for tleap compatibility) |
| Ain, Aex1, A-A, Q₂ | Four reaction intermediates in TrpB catalytic cycle |
