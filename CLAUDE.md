# Memory

> **AI Agent 强制启动序列（按顺序执行，不准跳过）**：
> 1. 本文件 `CLAUDE.md` — **唯一 entry point**，所有强制规则都在这里
> 2. **检查 pipeline stage**：运行 `python3 scripts/pipeline_guard.py --check`
> 3. `replication/validations/failure-patterns.md` — **已知错误模式，生成任何新文件前必读**
> 4. `NEXT_ACTIONS.md` — 当前任务队列
> 5. 遇到不认识的术语查 `GLOSSARY.md`
>
> **如果你跳过了第 2 步就开始生成文件，你就会重复已知的错误。这在本项目中已经发生过多次。**
>
> **Pipeline 已通过 pre-tool-call hook 强制执行。** 如果你在错误的 stage 尝试运行执行命令（antechamber, sbatch, gmx 等），命令会被系统自动拦截。这不是建议，是硬性限制。

## Me
Zhenpeng Liu, undergraduate at UNC Chapel Hill (liualex@ad.unc.edu). Preparing for Caltech/Anima Lab summer research position. Building a TrpB MetaDynamics replication project to demonstrate computational biology skills.

## Project Status (last updated: 2026-04-09 PATHMSD pivot)

| Milestone | Status | Notes |
|-----------|--------|-------|
| Paper reading (5 papers) | **speed-brief-ready** | JACS2019 speed brief generated; need to actually read |
| Resource inventory | done | All downloaded |
| MetaDynamics parameters extraction | done | From SI, fact-checked 2026-03-28 |
| SI protocol extraction | **done** | Full 5-phase protocol; 10 gaps identified |
| PLP parameterization (GAFF+RESP) | **done** | Ain_gaff.mol2 + Ain.frcmod generated; charge=-2 confirmed |
| PDB residue name verification | **done** | 5DVZ=LLP, 5DW0=PLS, 4HPX=0JO |
| O→C reference path (15 frames) | **done** | path.pdb, 112 Cα; λ = 379.77 nm⁻² (PATHMSD, matches SI) |
| System build (tleap) | **done** | 39,268 atoms, charge neutral, 4 Na⁺ |
| Toy MetaD test (alanine dipeptide) | **done** | GROMACS+PLUMED2 validated |
| Conventional MD (500 ns) | **done** | Job 40806029, 71.55 hrs, 22 GB trajectory |
| AMBER→GROMACS conversion | **done** | ParmEd, 39,268 atoms verified |
| PLUMED source build | **done** | PLUMED 2.9.2 from source (conda 版 libplumedKernel.so 残缺) |
| **PATHMSD verification** | **done** | 2026-04-09 plumed driver test: PATHMSD works with source-compiled PLUMED; FP-020 re-diagnosed; switched back from FUNCPATHMSD workaround |
| **Well-tempered MetaD initial run** | **❌ FAILED → PATHMSD fix ready** | Job 41514529: 46.3/50 ns then walltime; broken by FP-022 (later switched back to PATHMSD 2026-04-09). **Resubmit with new plumed.dat pending.** |
| Tutorial (EN+CN) | **done** | project-guide/TrpB_Replication_Tutorial_EN/CN.md (~2000 lines each) |
| Weekly report (Week 4) | **done** | reports/WeeklyReport_Week4_2026-04-04.docx |
| Pipeline research (9 papers) | **done** | PDFs + reading notes + annotation HTMLs |
| Logic Chain expansion (ch.19-23) | **done** | Pipeline 全景/RFD/GRPO+MFBO/SE3/角色重定位 |
| 10-walker MetaD scripts | **ready** | feature/10-walker-metad branch, WALKERS_DIR 方案 |
| MetaD visualization | **done** | 6-panel interactive HTML, 2 rounds review |

## Key Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| MetaD engine | **GROMACS + PLUMED2** (strict replication) | Original paper used GROMACS 5.1.2 + PLUMED2; we replicate exactly |
| Force field | ff14SB | From SI |
| Water model | TIP3P | From SI |
| Temperature | 350 K | Thermophilic enzyme (P. furiosus) |
| Conventional MD engine | AMBER 24p3 (pmemd.cuda) | For system prep + 500 ns production |

---

## Collaboration Architecture

> 基于 arXiv 2602 (Scaling Reproducibility) 三层分离架构设计。

| Role | Provider | 做什么 |
|------|----------|--------|
| PM | Zhenpeng | 科学决策、优先级、审批。动嘴不动手 |
| Designer | Claude | 规划、协调、分发任务给 Codex、review 产出 |
| Executor | Codex | 写脚本、改文件、生成命令、产出 artifacts |
| Debate | Claude+Codex | Bug/分歧 → `.ccb/debate-protocol.md` 直到共识 |

**正常流程**：PM 下指令 → Claude 分解任务 → `/ask codex` 执行 → Claude review → PM 确认
**异常流程**：发现 bug → debate protocol → 共识后报告 PM

### Codex Dispatch 格式
Claude 发给 Codex 时必须包含：
1. 当前 pipeline stage（从 `PIPELINE_STATE.json`）
2. 具体任务描述 + 期望输出
3. Codex 需要先读的文件路径
4. Stop conditions（什么需要人决策）
5. **Skeptical requirements（强制）**：
   - 所有数值计算必须写成函数，函数必须有 assertion
   - Assertion 包括：物理范围检查、单位一致性检查
   - 函数名必须与返回值语义一致
   - 不确定的地方标 UNVERIFIED，不要假装确定
   - 中间变量要 print 出来，让 skeptic 能看到计算过程

### Codex 启动文件（每次 session 必读）
```
CLAUDE.md → PIPELINE_STATE.json → failure-patterns.md → NEXT_ACTIONS.md → frozen manifest
```

---

## 强制规则（从 RULES.md + PROTOCOL.md 提取的核心内容）

> 以下规则必须遵守。完整细节见 `PROTOCOL.md`（pipeline 详细说明）。工作风格规则的原始版本见 `archive/RULES.md`。

### 核心原则

> **分离三种决策**：科学决策（测什么、为什么）、执行决策（怎么跑软件）、下游集成声明（结果对 pipeline 意味着什么）。三者不能混为一谈。

### Pipeline Enforcement（HARD GATE）

> **当前 stage 由 `PIPELINE_STATE.json` 控制，pre-tool-call hook 自动执行。**
> 你不需要"记住"自己在哪个 stage——hook 会阻止你在错误 stage 运行执行命令。

**检查当前 stage：**
```bash
python3 scripts/pipeline_guard.py --check
```

**完成当前 stage 后推进：**
```bash
python3 scripts/pipeline_guard.py --advance
```

**被 hook 拦截时：** 不要绕过。读 `PIPELINE_STATE.json`，完成当前 stage 的工作，推进后再执行。

**Human override（紧急情况）：**
```bash
python3 scripts/pipeline_guard.py --force 3
```

### 6-Stage Pipeline（参考表 — 实际执行由上面的 hook 控制）

| # | Stage | 干什么 | 什么时候停下等人审批 |
|---|-------|--------|---------------------|
| 0 | Profiler | 论文 → frozen manifest | **必须停。Manifest 需要人签字。** |
| 1 | Librarian | 盘点资源，找缺失 | 缺资源或无权限时 |
| 2 | Janitor | 整理目录结构 | 路径冲突时 |
| 3 | Runner | 生成脚本 / 提交作业 | 参数不确定时 |
| 4 | Skeptic | 验证运行结果 | 科学有效性不确定时 |
| 5 | Journalist | 写 campaign report | 不需要停 |

详细的 stage 说明在 `project-guide/stages/` 下。

### 脚本化原则（Runner stage 强制，FP-015 教训）

> **任何出现在 production 文件里的数值，必须是脚本输出，不是人工输入。**
>
> 脚本必须包含：
> 1. 物理范围 assertion（如 `assert 0.01 < lambda < 0.1`）
> 2. 单位标注（MSD 单位是 A^2，RMSD 单位是 A，不能混用）
> 3. 中间值打印（让 skeptic 能看到计算过程）
> 4. 与参考值比较（JACS 2019 SI 的对应值，偏差超过 10% 必须解释）
>
> **如果 AI 手动计算一个数字然后写进文件，这本身就是 violation。**
> **函数名必须与返回值语义一致：`calculate_msd` 返回 MSD (A^2)，不是 RMSD (A)。**

### 独立复核原则（Skeptic 自动触发）

> **每次 Runner 产出新 artifact 后，必须起独立 subagent 验证。不需要人提醒。**
> Skeptic 不接收 Claude/Codex 的讨论上下文，只看最终文件。
> 验证清单：数值追溯来源、assertion 存在、函数名语义一致、物理范围合理、与 JACS 2019 对比。

### 错误处理规则（Skeptic 强制触发）

> **任何时候发现事实错误、脚本 bug、参数不匹配，必须做以下三件事，缺一不可：**

1. **修源文件**：在出错的文件里直接修正
2. **追加 failure-patterns.md**：在 `replication/validations/failure-patterns.md` 追加 FP-XXX 条目（首次发现、发现者、错误描述、正确事实、根因、防范措施）
3. **写 validation note**：在 `replication/validations/` 创建 `YYYY-MM-DD_[context].md`，记录 pass/fail 结果

**光改 CHANGELOG.md 不算完成。** CHANGELOG 记"发生了什么"，failure-patterns 记"怎么防止再发"，validation note 记"验证结论"。

### 工作风格

1. 中英文混用。中文写说明，英文写技术术语和命令
2. 不要 overwhelming，给清晰的 entry point
3. 每一步都要有"为什么"（用 `> blockquote`）
4. 参数变化必须标注（表格说清楚哪些要重新算）
5. 代码块直接给命令，不描述
6. 文件要 portable，不锁定 AI vendor
7. 不给虚假进度：没做就标 NOT STARTED

### 严格复刻原则

**MetaDynamics 必须用 GROMACS + PLUMED2**（原文 GROMACS 5.1.2 + PLUMED2），不用 AMBER 做 MetaD。
**常规 MD 可以用 AMBER 24p3**（pmemd.cuda），力场层面与 AMBER16 等价。

---

## Current Campaigns

| Campaign | Manifest | Status |
|----------|---------|--------|
| JACS 2019 benchmark reproduction | `replication/manifests/osuna2019_benchmark_manifest.yaml` | Librarian done (2026-03-30) — Janitor stage next |
| GenSLM-230 vs NdTrpB comparison | `replication/manifests/genslm230_vs_ndtrpb_manifest.yaml` | Blocked on benchmark + lab assets |

---

## HPC (UNC Longleaf)

| Item | Value |
|------|-------|
| Username | liualex |
| Home | /nas/longleaf/home/liualex (50 GB, near full!) |
| Work | /work/users/l/i/liualex (10 TB) |
| **Project dir** | **/work/users/l/i/liualex/AnimaLab/** |
| Conda envs | /work/users/l/i/liualex/conda/envs/ |
| AMBER | module load amber/24p3 (GPU: pmemd.cuda) |
| PLUMED | conda activate trpb-md → plumed 2.9 |
| GROMACS (system) | module load gromacs/2026.0 — **无 PLUMED 支持** |
| GROMACS (conda) | conda activate trpb-md → gmx 2026.0 (PLUMED 支持 ✓) |
| SSH from Mac | ControlMaster via `ssh longleaf`（需保持一个 Terminal 窗口连着）|

### AnimaLab 目录结构 (on Longleaf)

```
/work/users/l/i/liualex/AnimaLab/
├── structures/              ← PDB 原始文件
├── parameterization/ain/    ← PLP RESP 参数化
├── system_build/            ← tleap 产出 (parm7, inpcrd)
├── classical_md/            ← AMBER 经典 MD (inputs/ slurm/ output/)
├── metadynamics/            ← GROMACS+PLUMED MetaD
│   ├── conversion/          (AMBER→GROMACS)
│   ├── path_cv/             (15-frame path.pdb)
│   ├── plumed/              (plumed.dat, metad.mdp)
│   └── single_walker/       (当前运行)
├── analysis/                ← FES 分析
├── archive/                 ← 旧文件
└── logs/                    ← Slurm 日志
```

## Key Files

| File | What |
|------|------|
| **NEXT_ACTIONS.md** | **共享任务队列 — 所有 agent 都先读这个再干活** |
| **scripts/pipeline_guard.py** | **统一 pipeline 执行器（hook + CLI + stage verification）** |
| **PIPELINE_STATE.json** | **Pipeline 状态 + 每个 stage 的 artifact verification spec (schema v2)** |
| PROTOCOL.md | 详细参考：6-stage pipeline 完整说明 |
| project-guide/PROJECT_OVERVIEW.md | Full project overview |
| project-guide/FULL_LOGIC_CHAIN.md | 12 章从零开始的项目逻辑链 |
| **project-guide/PLP_SYSTEM_SETUP_LOGIC_CHAIN.md** | **12 章 PLP 参数化 + 体系搭建逻辑链（从 PDB 到 MetaD-ready）** |
| project-guide/briefs/ | 概念指南、中英文 briefing 文档 |
| papers/reading-notes/ | 5 篇论文的结构化阅读笔记 + JACS2019 速读 brief |
| papers/annotations/ | Deep annotation HTML（dual-column, browser-viewable） |
| replication/manifests/ | Frozen campaign manifests |
| replication/parameters/ | MetaD params from SI (fact-checked) |
| replication/validations/failure-patterns.md | **已知错误模式 — 生成新文件前必读** |
| .ccb/debate-protocol.md | **Claude+Codex debate 规则** |
| .ccb/debates/ | Debate transcripts + index.json |
| docs/superpowers/plans/ | Implementation plans |
| docs/superpowers/specs/ | Architecture design docs |

## Terms

| Term | Meaning |
|------|---------|
| COMM domain | Communication domain, residues 97-184 of TrpB; O/PC/C states |
| Path CV | s(R) = progress along O→C path; z(R) = deviation from path |
| O/PC/C | Open / Partially Closed / Closed conformations |
| FEL | Free Energy Landscape |
| SPM | Shortest Path Map (correlation-based tool) |
| PLP | Pyridoxal phosphate cofactor |
| Ain, Aex1, A-A, Q₂ | Reaction intermediates along TrpB catalytic cycle |
| 6-stage pipeline | Profiler→Librarian→Janitor→Runner→Skeptic→Journalist |

## Agent Sessions

| Agent | Role | Entry Point | 特点 |
|-------|------|-------------|------|
| Claude (Cowork) | designer | 本文件 CLAUDE.md | Research, planning, web search |
| Claude (Terminal) | designer | 本文件 CLAUDE.md | SSH, HPC, install, submit jobs |
| Codex (CCB) | executor | `openai.yaml` → CLAUDE.md | 写脚本、改文件、生成命令 |

所有 agent 共享本文件作为上下文注入入口。
Pipeline enforcement: Claude 通过 `.claude/settings.json` hook 强制，Codex 通过 `openai.yaml` default_prompt 注入。
Debate protocol: `.ccb/debate-protocol.md`。

## Preferences
- 信息不要太 overwhelming，给清晰的 entry point
- Weekly reports 要去 AI 化（banned phrases in weekly-report skill）
- 文件要 portable，不锁定在某个 AI vendor
- 中英文混用 OK
