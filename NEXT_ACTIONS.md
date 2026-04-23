# Next Actions

> **这个文件是 Cowork 和 Claude Code Terminal 共享的任务队列。**
> 两边都应该在开始工作前先读这个文件，结束工作后更新它。
> 规则：谁完成了一项就打 ✅ 并注明日期和工具；谁新增了一项就写清楚在哪里做。

---

## 当前阶段：Phase 1 — 复刻 Osuna 结果

**一句话目标**：在 Longleaf 上成功跑通 GROMACS+PLUMED2 MetaDynamics，对 PfTrpS(Ain) 复刻出和 JACS 2019 Figure 2a 一致的 FEL。

---

## Current (2026-04-23 — Miguel pivot)

### Miguel Iglesias-Fernández email 2026-04-23 — ground-truth contract
Original Osuna 2019 author clarified the MetaD recipe directly. Paper contract (authoritative, supersedes SI re-read):
- `UNITS LENGTH=A ENERGY=kcal/mol` (SI values are Å / kcal·mol⁻¹, not nm / kJ·mol⁻¹)
- `ADAPTIVE=DIFF SIGMA=1000` — time window in integrator steps (≈ 2 ps), NOT a geometry Gaussian width
- `HEIGHT=0.15 kcal/mol` BIASFACTOR=10 PACE=1000 TEMP=350
- 10 parallel walkers, not single-walker
- `UPPER_WALLS ARG=p1.zzz AT=2.5 KAPPA=800` (Å, kcal/mol)
- `WHOLEMOLECULES ENTITY0=1-39268` every step
- Email + annotated template at `replication/metadynamics/miguel_2026-04-23/miguel_email.md`

### λ=3.77 Å⁻² (= 379.77 nm⁻²) — Codex-confirmed
Miguel's `LAMBDA=80` is correct for HIS denser path (adjacent MSD ~0.03 Å²); our 15-frame path has adjacent MSD ~0.61 Å², so Branduardi textbook λ = 2.3 / 0.61 ≈ 3.77 Å⁻². Miguel's 80 would be 21× too sharp for our path (neighbor weight 10⁻²¹, integer-snap artifact). FP-022 was CORRECT all along; FP-027 re-opening was the error. See FP-032 + `replication/metadynamics/miguel_2026-04-23/lambda_audit_2026-04-23.md`.

### Initial 10-walker production — LAUNCHED 2026-04-23
**Job `45320189` (array 0-9) RUNNING** on volta-gpu, 10-walker WALKERS_DIR sync, path_gromacs.pdb 15 frames, all-PATHMSD-atoms λ=3.77 Å⁻². 3-day walltime; ETA depends on convergence, not hard wall.
- Driver self-projection gate PASS under UNITS=A + λ=3.77 (s: 1.092 → 14.907 monotonic, z ≈ −0.049 Å²).
- COLVAR / HILLS shared via `HILLS_DIR/`; per-walker provenance.txt records Miguel-email source + λ contract.
- Monitor cadence: every 2 h (per user request). Metrics: max_s per walker, HILLS σ columns (verify DIFF populates non-zero), first COLVAR s seed ≈ 1, wall-clock progress.

### Superseded directories (DEPRECATED, do not launch from)
- `replication/metadynamics/probe_sweep/` — P1–P5 were GEOM scans, invalidated by DIFF. `DEPRECATED.md` points at Miguel dir.
- `replication/metadynamics/pilot_matrix/` — 2×2 (anchor × SIGMA seed) scaffold built on GEOM assumption. Nothing launched. `DEPRECATED.md` points at Miguel dir.
- Anchor-set question (1WDW→3CEP vs 1WDW→5DW0) is still scientifically legitimate but must be re-posed under the Miguel contract, not inside the old 2×2 scaffold.

### Aex1 cMD — running (parallel, not Miguel-gated)
Job `45186335` on a100-gpu, ~13 h / 500 ns target, ~273 ns/day. Chemistry-control line: 5DW0 chain A (PLS external aldimine), unbiased. Not affected by Miguel pivot (no MetaD contract in cMD phase).
- stale-XML preflight bug fixed; FP-028 (openmm CUDA PTX) resolved.
- Post-cMD Aex1 MetaD prep will use Miguel contract (UNITS=A, DIFF SIGMA=1000, WALKERS_N=10, λ per Aex1 path density) once cMD completes.

## Next 48 hours

1. **Monitor 45320189 at 2 h cadence** — log max_s, σ-column population (DIFF sanity), s-seed (~1), wall-clock; first checkpoint at first HILLS row (~1 ps). If all walkers stall <s=2 through 10 ns under Miguel contract → anchor-set / piecewise-path becomes the surviving live hypothesis. If any walker crosses s>3 → Miguel contract vindicates and the whole GEOM/σ-ladder story was the wrong axis.
2. **Docs sweep** — tutorials, MASTER_TECHNICAL_GUIDE, TrpB_MetaDynamics_Complete_Workflow, JACS2019 parameters doc all still quote old (GEOM, SIGMA=0.1 nm, 50 ns single-walker, λ=3.798 nm⁻²) contract. Replace with Miguel contract. Do NOT rewrite failure-patterns.md (FP-031/032 already land the correction in place).
3. **Aex1 cMD monitor** — hourly cron; post-cMD Aex1 MetaD prep (path-CV self-projection + λ derivation on 5DW0-seeded path) queue-able once cMD crosses 50 ns.
4. **Miguel reply draft** — acknowledge contract, report our λ path-density derivation (so Miguel knows we did not blindly copy his 80), attach 45320189 first 10 ns COLVAR when available.
5. **Commit + push Miguel pivot** — single commit covering plumed.dat/plumed_template/single/materialize_walkers/submit/provenance + FP-031/FP-032/FP-022 corrigendum + DEPRECATED.md × 2 + this NEXT_ACTIONS rewrite + tutorial doc sweep. Author `alex051107 <2476939435@qq.com>`, NO Claude attribution. Target `trpb-metadynamics-replication.git` branch `new_idea_explore`; update PR #2.

### Will NOT do now
- **Revisit λ scheme** — FP-022 + FP-032 + Codex λ audit all landed. Not re-opening.
- **1WDW→5DW0 path build** — legitimate but contingent on Miguel-contract initial run's verdict. If 45320189 escapes, anchor change is not the pivot. If it stalls, anchor build becomes B-priority.
- **Launch piecewise path** — same reasoning; defer until Miguel initial returns a verdict.

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
