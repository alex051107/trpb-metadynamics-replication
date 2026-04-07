# Next Actions

> **这个文件是 Cowork 和 Claude Code Terminal 共享的任务队列。**
> 两边都应该在开始工作前先读这个文件，结束工作后更新它。
> 规则：谁完成了一项就打 ✅ 并注明日期和工具；谁新增了一项就写清楚在哪里做。

---

## 当前阶段：Phase 1 — 复刻 Osuna 结果

**一句话目标**：在 Longleaf 上成功跑通 GROMACS+PLUMED2 MetaDynamics，对 PfTrpS(Ain) 复刻出和 JACS 2019 Figure 2a 一致的 FEL。

---

## 🔴 Blocked（做不了，等依赖）

_目前无_

---

## 🟡 Ready to Do（可以立刻动手）

### 你自己做的（不需要 AI）

- [ ] **先读 Critical Thinking 框架**（5 min）
  - 打开 `project-guide/CRITICAL_THINKING_PROMPTS.md`
  - 以后每次读论文都要用里面的 5 层拆解表
  - **不读这个就去读论文 = 白读**

- [ ] **读 JACS 2019 正文**（~30 min，有速读 brief 辅助）
  - **先读** `papers/reading-notes/JACS2019_SpeedBrief.md`（10 min 浏览关键点）
  - 再打开 `papers/annotations/JACS2019_DeepAnnotation_v2.html`
  - 重点：Figure 2 (FEL), Figure 3 (K82-Q2 距离对比), productive vs unproductive closure
  - 读完标准：能回答 SpeedBrief 末尾的 5 个 checklist 问题
  - **读完后追加 5 层拆解表到 reading notes 末尾**（模板在 CRITICAL_THINKING_PROMPTS.md）
  - 🧠 强制思考：Figure 2 的 FEL 上，PC 态在 Ain 和 Q2 的能量差是多少？这个差值靠什么证据？你信吗？

- [ ] **读 PLP + 体系搭建 Logic Chain**（~35 min）
  - 打开 `project-guide/PLP_SYSTEM_SETUP_LOGIC_CHAIN.md`
  - 重点：第 5 章（质子化状态）、第 11 章（PI meeting 议题）
  - 这是和 PI 开会的核心参考文档
  - 🧠 强制思考：第 5 章说 charge = -2，但这个文档是 AI 写的。你现在知道实验证据在哪了（Caulkins 2014 NMR）。如果没有那篇 NMR 论文，你有别的方式验证 charge 吗？

- [ ] **读 GenSLM TrpB Nature Comms**（~15 min）
  - 打开 `papers/annotations/NatCommun2026_DeepAnnotation.html`
  - 重点：GenSLM 怎么生成序列、为什么需要 MetaDynamics 筛选
  - 读完标准：能回答"GenSLM 生成的序列为什么需要 MetaDynamics 来筛选"
  - **读完后追加 5 层拆解表**
  - 🧠 强制思考：GenSLM 生成的序列真的需要 MetaD 筛选吗？有没有更快的方式判断一个突变体好不好？MetaD 筛选的假设是"构象动态决定活性"——这个假设靠谱吗？

- [ ] **填领域地图表**（15 min，PI meeting 前必须完成）
  - 模板在 `project-guide/CRITICAL_THINKING_PROMPTS.md` 最后
  - 填完保存到 `project-guide/MY_FIELD_MAP.md`
  - 带这张表去 PI meeting

### 在 Claude Code Terminal 做的

> **PI 反馈 (2026-03-30)**: Follow Osuna SI protocol exactly. PLP parameterization is straightforward:
> Gaussian charges → FF parameters. Gaussian09→16 会有微小差异。搞清楚完整流程后约 meeting review。
>
> **PLP 参数化脚本已重写（2026-03-30），修复了残基名、提取逻辑、capping。**
> 质子化状态已通过 Caulkins 2014 NMR 数据确认（charge=-2）。
> ✅ ACE/NME capping 已确认必须（2026-03-31，Codex 分析 + Claude review）。
> ✅ Gaussian Job 40533504 已完成（Normal termination，88 步优化，2026-03-31）。
> ✅ Codex review 完成：修复了 6 个文件中的 iop(6/50=1) 残留 + Slurm OMP 问题（2026-03-31）。

- [x] **Production MD submitted** ✅ (2026-04-01)
  - Job `40806029` RUNNING
  - Production script: `replication/scripts/amber_md/submit_production.sh`

- [x] **Codex 脚本交付** ✅ (2026-04-01)
  - `convert_amber_to_gromacs.py`
  - `plumed_trpb_metad.dat` / `plumed_trpb_metad_single.dat` 更新
  - `replication/scripts/gromacs_metad/`
  - `replication/scripts/analysis/`

- [x] **独立参数验证** ✅ (2026-04-01)
  - `31/41 PASS`

- [x] **PLP 参数化 Ain — RESP 电荷提取** ✅ (2026-03-31)
  - Ain_gaff.mol2（42 atoms, charge=-2, backbone retyped to ff14SB）
  - Ain.frcmod（无 ATTN warnings）
  - FP-015 修复（lambda 从 3.798 → 0.034）

- [x] **tleap 体系搭建** ✅ (2026-03-31)
  - 39,268 atoms, box 76.4×88.1×73.2 Å, 4 Na+, 11,092 WAT
  - K82 sidechain retyped to ff14SB (C8/HC/HP); NZ stays GAFF (nh)
  - Skeptic 6/6 PASS

- [x] **生成 15-frame O→C 参考路径** ✅ (2026-03-31)
  - λ(total SD) = 0.0339 (JACS ~0.029, ratio 1.17×)
  - FP-015 修复 + assertions 添加

- [x] **Pipeline Cycle 1 完成** ✅ (2026-03-31)
  - 全 6 stages PASS，campaign report 已写

- [x] **常规 MD 500 ns — production 已提交** ✅ (2026-04-01)
  - Prep pipeline job `40709153` submitted on 2026-03-31
  - Production job `40806029` RUNNING
  - 脚本：`replication/scripts/amber_md/run_md_pipeline.sh` → `submit_production.sh`
  - 输出目录：`/work/.../AnimaLab/replication/runs/pftrps_ain_md/`
  - UNVERIFIED: heating ref coords (用 min2.rst7), 72h walltime chunking

### 需要和 PI 讨论的

- [x] **PLP 质子化状态确认** ✅ (2026-03-30, 文献 review)
  - 磷酸基团：dianionic (-2) — Caulkins 2014 ³¹P NMR
  - 酚羟基 O3：deprotonated (-1) — Caulkins 2014 ¹³C shifts
  - 吡啶 N1：**deprotonated (0)** — Caulkins 2014 ¹⁵N δ=294.7 ppm
  - Schiff base N：protonated (+1) — Caulkins 2014 ¹⁵N δ=202.3 ppm
  - **总电荷 = -2**
  - 详见 `replication/validations/2026-03-30_plp_protonation_literature_review.md`
- [ ] **K82 Schiff base capping 策略**：ACE/NME 还是更大的 cap？（Codex 调查中）
- [ ] **4HPX (A-A) chain 选择**：哪条链是 beta subunit？
- [ ] **PI 的 PLP tutorial**：PI 说会找 tutorial，follow up
- [ ] **约 PI meeting**：PI 要求搞清楚完整流程后 meet 一起 review

---

## 🟢 Done（已完成）

| 事项 | 完成日期 | 工具 |
|------|---------|------|
| GROMACS conda 安装 | 2026-03-28 | Claude Code Terminal |
| PLUMED 2.9 安装 | 2026-03-26 | Claude Code Terminal |
| AMBER 24p3 验证 | 2026-03-28 | Claude Code Terminal |
| MetaDynamics 参数提取 (SI) | 2026-03-27 | Cowork |
| 4 篇论文 reading notes + HTML | 2026-03-28 | Cowork |
| CLAUDE.md / RULES.md / GLOSSARY.md | 2026-03-27 | Cowork |
| AnimaLab 目录创建 | 2026-03-28 | Claude Code Terminal |
| Full Logic Chain 文档 | 2026-03-28 | Cowork |
| Peer review (JACS 2019) | 2026-03-28 | Claude Code Terminal |
| SI 参数 fact-check（逐项对照 SI PDF） | 2026-03-28 | Cowork |
| Toy alanine 全套脚本（10 文件） | 2026-03-28 | Cowork |
| Toy alanine MetaD 执行 + FES 验证 | 2026-03-28 | Claude Code Terminal |
| O→C 参考路径生成脚本 | 2026-03-28 | Cowork |
| PLUMED MetaD 输入模板（单 walker + 多 walker） | 2026-03-28 | Cowork |
| PLP 参数化工作流脚本 v1 | 2026-03-28 | Cowork |
| 1WDW + 3CEP + 4HPX PDB 下载 | 2026-03-28 | Claude Code Terminal |
| Gaussian 16c02 可用性确认 | 2026-03-28 | Claude Code Terminal |
| CLAUDE_CODE_TODO.md（给 Terminal 的执行指令） | 2026-03-28 | Cowork |
| NEXT_ACTIONS.md 共享任务队列 | 2026-03-28 | Cowork |
| **SI protocol 完整提取（5-phase, 10 gaps）** | 2026-03-30 | Claude Code Terminal |
| **PDB 残基名验证（LLP/PLS/0JO）** | 2026-03-30 | Claude Code Terminal |
| **parameterize_plp.sh 重写 v2（754 行）** | 2026-03-30 | Claude Code Terminal |
| **PLP + 体系搭建 Logic Chain（1248 行，12 章）** | 2026-03-30 | Claude Code Terminal |
| **JACS 2019 速读 Brief** | 2026-03-30 | Claude Code Terminal |
| **Coordinator Agent 创建** | 2026-03-30 | Claude Code Terminal |
| **Claude+Codex 协作架构搭建** | 2026-03-30 | Claude + Codex |
| **Pipeline enforcement 统一 (pipeline_guard.py)** | 2026-03-30 | Codex |
| **Debate protocol 创建 (.ccb/)** | 2026-03-30 | Claude + Codex |
| **PLP 质子化态文献 review (4 sources)** | 2026-03-30 | Claude (Zotero+Web) |
| **PROTOCOL.md 更新（PLP sources section）** | 2026-03-30 | Claude |
| **RESP 电荷提取 + backbone/sidechain retype** | 2026-03-31 | Claude + Codex |
| **FP-015 lambda bug 修复（130× 错误）** | 2026-03-31 | Claude + Codex |
| **tleap 体系搭建（39,268 atoms）** | 2026-03-31 | Claude + Codex |
| **Pipeline Cycle 1 全 6 stages PASS** | 2026-03-31 | Claude |
| **AMBER MD input files (12 files)** | 2026-03-31 | Codex |
| **Prep pipeline submitted (Job 40709153)** | 2026-03-31 | Claude Code Terminal |

---

## 🟡 本周待做（2026-04-07 起）

> **MetaD Job 41514529 预计 ~8h 后完成（84%, 42.1/50 ns）**

### Phase B: MetaD 完成后 FES 分析流程

- [ ] **B1. 确认正常完成**：`squeue` 检查 job 状态，`wc -l HILLS COLVAR`，`grep error metad.log`
- [ ] **B2. COLVAR 时间序列**：统计 O(s<5) / PC(5<s<10) / C(s>10) 各有多少帧。如果 O+C = 0 → 跳到 10-walker
- [ ] **B3. FES 重构** ⚠️ 必须加 `--kt 2.908`（GROMACS 用 kJ/mol，不是 kcal/mol，见 FP-021）
  ```
  plumed sum_hills --hills HILLS --outfile fes.dat --mintozero --kt 2.908
  ```
- [ ] **B4. 分段收敛**：截断 HILLS（`head -n $((ns*500+HEADER))`），分别重构 10/20/30/40 ns 的 FES
- [ ] **B5. FES sanity check**：范围 0-30 kJ/mol（合理），不平坦（max-min > 5 kJ/mol）
- [ ] **B6. 运行分析脚本**：`analyze_fes.py --fes fes.dat` + `check_convergence.py --fes-pattern "fes_*ns.dat"`
- [ ] **B7. 决策**（见下方决策矩阵）
- [x] **FP-021 已记录** ✅ 2026-04-07（--kt 单位，Codex review 发现）

### FES 决策矩阵

| FES 结果 | 下一步 |
|---------|--------|
| 3-basin + 收敛 + ΔG≈5 kcal/mol | merge 10-walker branch → 生产运行 |
| 3-basin 但未收敛 | 直接上 10-walker（SI 用 500-1000 ns 总采样） |
| 只有 PC 区域采样 | 直接上 10-walker（单 walker HILLS 可 warm-start） |
| 只有 2 个 basin | 不一定错（独立 TrpB 的 O 态可能不稳定），对照 JACS 2019 对应体系 |
| 严重偏差 | 检查 LAMBDA、path frames Cα (res 97-184 + 282-305)、FUNCPATHMSD atom indexing |

---

## ✅ 本周已完成（2026-04-04 ~ 04-07）

| 事项 | 日期 | 备注 |
|------|------|------|
| 500 ns production MD 完成 | 04-04 | Job 40806029, 71.55 hrs, 22 GB |
| AMBER→GROMACS 转换 | 04-04 | ParmEd, 39268 atoms 验证 |
| MetaD pipeline 调试 | 04-04 | FP-018/019/020 |
| PLUMED 源码编译 | 04-04 | 2.9.2 from source |
| Single-walker MetaD 提交 | 04-04 | Job 41514529, FUNCPATHMSD + ADAPTIVE=GEOM |
| Tutorial 文档 (EN+CN) | 04-04 | ~2000 行/版 |
| Weekly Report Week 4 | 04-04 | docx |
| 目录重组 | 04-04 | 本地+Longleaf 对齐 |
| 组会纪要 | 04-02 | MeetingNotes_2026-04-02 |
| 参数文件注释 PDF | 04-04 | 6 页彩色 |
| **9 篇论文 PDF 下载** | 04-05 | GenSLM/RFD/GRPO/MFBO/STAR-MD/DeepTDA/LigandMPNN |
| **4 组 reading notes** | 04-05 | GenSLM/RFD+LMPNN/GRPO+MFBO/SE3+DeepTDA |
| **5 个 annotation HTML** | 04-05 | dual-column 中文标注 |
| **Logic Chain ch.19-23** | 04-05 | Pipeline 全景/RFD/GRPO+MFBO/SE3/角色重定位 |
| **10-walker 脚本** | 04-06 | feature/10-walker-metad branch, 含 README |
| **MetaD visualization HTML** | 04-07 | 6 面板交互动画（2 轮 review 修正） |
| **Git commit + push** | 04-06 | master + feature branch |
| **Codex plan review** | 04-07 | 3 CRITICAL 修正（--kt/--stride） |

---

## 📋 Backlog（以后做，现在不急）

- [ ] Cross-verify reading notes（verifier agent）
- [ ] SPM 分析 — 等 MetaD 轨迹
- [ ] GenSLM-230 同源建模 + MetaD — Phase 2
- [ ] Reward function Python 模块 — Phase 3
