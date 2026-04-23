# Next Actions

> **这个文件是 Cowork 和 Claude Code Terminal 共享的任务队列。**
> 两边都应该在开始工作前先读这个文件，结束工作后更新它。
> 规则：谁完成了一项就打 ✅ 并注明日期和工具；谁新增了一项就写清楚在哪里做。

---

## 当前阶段：Phase 1 — 复刻 Osuna 结果

**一句话目标**：在 Longleaf 上成功跑通 GROMACS+PLUMED2 MetaDynamics，对 PfTrpS(Ain) 复刻出和 JACS 2019 Figure 2a 一致的 FEL。

---

## Current (2026-04-22)

### Phase A landed
Path CV diagnostic package committed (`e2f19f4`). Self-projection PASS, PATHMSD↔FUNCPATHMSD PASS, O-endpoint tangent OFF-TANGENT signal (21/21 frames). Rules out technical bugs at PATHMSD / λ / metric. λ=379.77 is FP-022-settled. VERDICT at `replication/metadynamics/path_cv/diagnostics/VERDICT_2026-04-21.md`.

### Probe sweep (σ floor/ceiling ladder) — CLOSED
All 5 probes (P1–P5) stalled with max_s ≤ 1.64 through ≥ 5 ns. **SIGMA_MIN/MAX axis does not rescue.** Decision: stop scanning this axis.
- P3 extension 44956161 TIMEOUT at 15h (run logged but no rescue)
- P5 44956006 COMPLETED 6:28, same stall pattern
- `replication/metadynamics/probe_sweep/ladder.yaml` is the source of truth

### Aex1 cMD — running
Job 45186335 on a100-gpu, 18 ns / 500 ns (3.9 %), 273 ns/day, ETA ~44 h. This is the chemistry-control line: 5DW0 chain A (PLS external aldimine) on same PATHMSD + λ + plumed.dat. 5DW0 → s ≈ 1.07 on current path.
- Load-state stale-XML bug fixed by preflight diff (ChatGPT Pro spec, Codex-applied)
- FP-028 (openmm CUDA PTX) resolved on prod branch; CPU fallback not needed
- Post-cMD plan: Aex1 MetaD 5–10 ns on same path to discriminate chemistry-specific vs path-local stall

### Next strategic framing (ChatGPT Pro 2026-04-22)
The probe sweep ruling out SIGMA_MIN/MAX narrows the remaining hypotheses to two **separable** variables:
- **H1 — anchor set**: direct 1WDW→3CEP linear interpolation may be globally OK but locally poor at O-end; PC-state anchor (5DW0) not used in current path
- **H2 — initial SIGMA=0.1**: the initial Gaussian seed is UNVERIFIED (SI silent); probe sweep varied floor/ceiling only, never the seed

Rather than launching 10 parallel walkers (same CV, falsification-only, no causal signal), Pro's plan is a **2×2 pilot matrix** holding ff/λ/bias/pace constant and varying only {anchor set, initial SIGMA}:

| Pilot | Path | SIGMA | Purpose |
|---|---|---|---|
| P1 (baseline) | 1WDW→3CEP | 0.1 | have |
| P2 | 1WDW→3CEP | 0.3 | isolates seed axis |
| P3 | 1WDW→5DW0 | 0.1 | isolates anchor axis |
| P4 | 1WDW→5DW0 | 0.3 | interaction |

Each pilot runs 3 ns; only winner extends to 10 ns. Read {max_s, p95(s), p95(z), (s,z) occupied bins, HILLS center spread}.

## Next 48 hours

1. **Cheap O-end diagnostic first** — project existing unbiased Ain 500 ns cMD onto current path, plot z vs t. ~30 min with existing traj. If thermal alone saturates z while s pinned, Pilot 3/4 (anchor change) is predicted to be the winner before GPU burn. (Unblocks once `path_cv/attribution/project_to_path.py` window-NaN is fixed — cap 2 h.)
2. **Pilot 2 launch** — `ladder.yaml` add P6 with SIGMA=0.3, floor/ceiling unchanged. Cheapest of the 4; launches tonight. Gate read at 3 ns.
3. **1WDW→5DW0 path build** — extract 5DW0 chain A 112 Cα, renumber to Ain convention, re-run `generate_path_cv.py`, **re-run self-projection + re-derive λ for new anchor geometry** (do NOT assume λ=379.77 transfers). Multi-hour task. Gate: self-projection must PASS before Pilots 3/4 launch.
4. **Aex1 cMD monitor** (hourly cron) — flag on completion or wall-clock drift; post-cMD MetaD prep is queue-able once this crosses 50 ns.
5. **Osuna group email** (Iglesias-Fernández) — draft at `reports/osuna_email_draft_2026-04-18_iglesias.md`, send on user confirmation.

### Will NOT do now (Pro-deprioritized)
- **10 parallel walkers** — same CV, no causal signal until 2×2 returns. Defer until 2×2 matrix has a winner or Pilots 3/4 confirm anchor set is the axis.
- **Full piecewise O→PC→C path** — Pro's sequencing: first-round local pilot is "keep 15 frames, 112 Cα, λ=379.77, only change terminal anchor", not production-grade piecewise. Upgrade to piecewise only after Pilots 3/4 show rescue on the simpler local-anchor swap.

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

## 🟡 本周待做（2026-04-15 更新：SIGMA floor fix）

> **⚠️ 2026-04-15 最新状态**：Job 42679152（2026-04-12 跑完）50 ns 全程 walker 卡在 s(R)=1.0-1.6（O basin），**SIGMA 太窄导致 Gaussian 塌成针尖**（FP-024）。从 PLUMED 2.9 官方 METAD 文档逐字验证 + 4 agent 并行调查得出修复：加 SIGMA_MIN=0.3,0.005 + SIGMA_MAX=1.0,0.05，SIGMA 0.05→0.1 nm。已部署到 Longleaf，**探针 Job 43813633 (10 ns) PENDING**（分区 hov，walltime 14h）。5 ns 决策点：max s>3 → 扩到 50-100 ns full initial；max s<2 → path CV 本身可能要重建。详见 FP-024/025。
>
> **历史脉络**：
> - ❌ Job 41514529（FUNCPATHMSD）：FP-022 LAMBDA 112× bug
> - ❌ Job 42679152（PATHMSD + SIGMA=0.05）：FP-024 Gaussian 过窄
> - ⏳ Job 43813633（PATHMSD + SIGMA_MIN/MAX 修复）：探针中

### Phase A (更新 2026-04-09 evening — deployment complete)：部署 PATHMSD 修复 + 重跑 initial run

- [ ] **A1. Commit 当前改动**（PATHMSD plumed.dat、FP-020 更正、FP-023、PIPELINE_STATE、PPT、annotated/ 重写、TechWalkthrough、bilingual script、submit.sh echo 更新）并 push
  - ⚠️ 仍未完成 — 本地仍有 uncommitted changes 等组会后一起 commit
- [x] **A2. 同步修复后的文件到 Longleaf** ✅ 2026-04-09
  - `scp plumed.dat submit.sh longleaf:...single_walker/`
  - md5 两边一致：plumed.dat=`ba2dbd89...`，submit.sh=`edf6c00e...`
- [x] **A3. 备份旧 Job 41514529 数据** ✅ 2026-04-09
  - 归档目录：`single_walker/archive_FP022_broken_2026-04-09/`
  - 已归档文件：HILLS, COLVAR, metad.{xtc,log,edr,cpt,tpr}, mdout.mdp, PLUMED.OUT, path_fixed.pdb, 所有 #metad* 备份, 所有 bck.*.PLUMED.OUT, 6 个旧 slurm 日志
- [x] **A4. PLUMED driver 离线验证** ✅ 2026-04-09（其实在部署前就已经做过）
  - `rerun/plumed_pathmsd_test.dat` + `rerun/COLVAR_pathmsd`
  - 结果：0 NaN，s(R) ≈ 1.02-1.06，z ≈ 0.02-0.03 nm²
- [x] **A5. 重提交 50 ns initial run with PATHMSD plumed.dat** ✅ 2026-04-09 ~17:00
  - **Job 42679152** submitted
  - 2026-04-09 ~17:25 切到 **RUNNING** 状态（partition=hov，node=c0301）
  - 起步 CV 健康度验证：PATHMSD kernel loaded，`path.sss ≈ 1.04`（匹配 offline rerun 预测），`metad.bias` 从 0 爬到 ~0.9 kJ/mol（正常累积），COLVAR FIELDS = `time path.sss path.zzz metad.bias`（PATHMSD 特征命名）
- [ ] **A6. 等待 ~3 天 — IN PROGRESS**
  - Job 42679152 started 2026-04-09 ~17:25
  - ETA ~2026-04-12（50 ns × walltime 72 h）
  - 监控命令：`ssh longleaf "squeue -u liualex -j 42679152 && tail -3 /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/COLVAR"`

### Phase B: MetaD 重跑完成后 FES 分析流程（沿用之前的 B1-B7）

> 所有命令在 Longleaf 的 `single_walker/` 目录执行：
> `cd /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker`
> `conda activate trpb-md && export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so`

- [ ] **B1. 确认正常完成**（Job 42679152，ETA ~2026-04-12）
  ```bash
  squeue -u liualex | grep 42679152       # 应该不在了（跑完后才能做 Phase B）
  wc -l HILLS COLVAR                      # HILLS ~25000, COLVAR ~50000
  grep -i "error\|fatal\|nan" metad.log | head -5
  tail -5 slurm-trpb_metad-42679152.out   # 检查 === Done === 诊断块
  ```

- [ ] **B2. COLVAR 时间序列**
  ```bash
  python3 -c "
  import numpy as np; d=np.loadtxt('COLVAR',comments='#')
  s=d[:,1]; print(f'O(s<5):{(s<5).sum()} PC(5-10):{((s>5)&(s<10)).sum()} C(s>10):{(s>10).sum()}')
  "
  ```
  如果 O+C = 0 → 跳到 Phase C（10-walker）

- [ ] **B3. FES 重构** ⚠️ `--kt 2.908`（kJ/mol, FP-021）
  ```bash
  plumed sum_hills --hills HILLS --outfile fes.dat --mintozero --kt 2.908
  ```

- [ ] **B4. 分段收敛**（截断 HILLS 文件，不是 --stride）
  ```bash
  HEADER=$(grep -c "^#" HILLS)
  for ns in 10 20 30 40; do
    head -n $((ns * 500 + HEADER)) HILLS > HILLS_${ns}ns
    plumed sum_hills --hills HILLS_${ns}ns --outfile fes_${ns}ns.dat --mintozero --kt 2.908
  done
  cp fes.dat fes_50ns.dat
  ```

- [ ] **B5. FES sanity check**（⚠️ 如果 FAIL，先检查 --kt 是否用了 2.908 而非 0.695）
  ```bash
  python3 -c "
  import numpy as np; d=np.loadtxt('fes.dat',comments='#'); f=d[:,2]
  fmax_kj=f.max(); fmax_kcal=fmax_kj/4.184
  print(f'Range: {f.min():.1f}-{fmax_kj:.1f} kJ/mol ({f.min()/4.184:.1f}-{fmax_kcal:.1f} kcal/mol)')
  print('FLAT_CHECK:', 'FAIL - FES is flat, bias not working' if fmax_kj-f.min()<1 else 'PASS')
  print('RANGE_CHECK:', 'PASS' if fmax_kj<80 else 'FAIL - FES max %.1f kJ/mol > 80, likely --kt unit error (FP-021)' % fmax_kj)
  # FP-021 detector: if --kt was 0.695 instead of 2.908, FES is ~4.18x too large
  # Expected max ~20-30 kJ/mol. If >80 kJ/mol, almost certainly wrong --kt.
  "
  ```

- [ ] **B6. 运行分析脚本**
  ```bash
  # 上传脚本（如果还没传）
  # scp replication/analysis/analyze_fes.py longleaf:.../single_walker/
  # scp replication/analysis/check_convergence.py longleaf:.../single_walker/
  python3 analyze_fes.py --fes fes.dat
  python3 check_convergence.py --fes-glob "fes_*ns.dat"
  ```
  输出：`fes_plot.png`, `fes_report.json`, `fes_convergence_plot.png`, `fes_convergence_report.json`

- [ ] **B7. 决策**（见下方决策矩阵）
- [x] **FP-021 已记录** ✅ 2026-04-07

### FES 决策矩阵

> analyze_fes.py 输出两个 JACS 对比指标：
> - `C relative to lowest(O,PC)` — 参考值 ~5 kcal/mol (±2)
> - `PC → C barrier` — 参考值 ~6 kcal/mol (±2)

| analyze_fes.py 输出 | 含义 | 下一步 |
|---------|--------|--------|
| 两项 PASS + 收敛 | benchmark 复刻成功 | merge 10-walker branch → 生产运行 |
| 两项 PASS 但未收敛 | basin 对但采样不够 | 直接上 10-walker（SI 用 500-1000 ns） |
| COLVAR 只在 PC 区域 | 单 walker 采样不足 | 直接上 10-walker（HILLS 可 warm-start） |
| 只有 2 个 basin | 不一定错（独立 TrpB O 态可能不稳定） | 对照 JACS 2019 对应体系再判断 |
| FAIL：数值偏差 >2 kcal/mol | 参数或 CV 可能有误 | 检查 LAMBDA, path Cα (97-184 + 282-305), atom indexing |
| sum_hills 失败或 fes.dat 空/corrupt | 命令错误 | 检查 --kt 单位、HILLS 文件完整性 |

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
| **FP-022 path CV LAMBDA bug 诊断 + 修复** | 04-08 | branch fix/path-cv-repair, 三步曲完成 |
| **PLUMED driver 离线验证** | 04-08 | 用修复后 plumed.dat 重算 metad.xtc，PLUMED 自检通过 |
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
