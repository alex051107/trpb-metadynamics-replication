# GroupMeeting 2026-05-01 · Bilingual Page-by-Page Presenter Script
# 中英对照逐页讲稿 · 对齐 12-slide deck

> **Deck**: `reports/GroupMeeting_2026-05-01.pptx` (12 slides; 5-topic structure per `clever-tickling-sparrow.md` §C1)
> **Meeting**: Yu Chen / PI 1-on-1 · ~28-30 min talk + 10-15 min Q&A
> **Format**: each slide block has **EN** (phrasing for practice/reference) then **中文** (read aloud at meeting)
> **Side binders**: `GroupMeeting_2026-05-01_TechDoc_Bilingual.md` open in side window for live deep-dives

---

## Slide 1 / 12 — Title (30 s)

Slide content: "TrpB MetaD Week 8 — SI-faithful 10-walker production launched + ML cartridge V1 contract".

**EN**: "Two big movements this week. First, the 10-walker SI-literal production launched — v1 was scancelled for homogeneous starts, v2 crashed exit-139 LINCS, v3 with EM+NVT pre-equilibration validated 10/10 walkers PASS in smoke and is running now as SLURM 45784112. Second, the ML cartridge V1 contract is now redteamed across 8 rounds of Codex audit plus an independent sub-agent second-pass that found ten more software-debt issues — all fixed via rewording. I will cover five topics across the next 11 slides in about 28 minutes."

**中文**: "这周两个大动作。第一, **10-walker SI-literal production 终于跑起来了** —— v1 被 scancel 了同质起点, v2 LINCS exit-139 全崩, v3 加了 EM+NVT pre-equilibration, smoke 10/10 walker PASS, 现在 production 已经在 SLURM 45784112 上跑。第二, **ML cartridge V1 contract** 经过 8 轮 Codex audit 加一个独立 sub-agent second-pass, 又找出 10 个 software-debt issue, 全部 reworded 修好了。我按 5 个 topic 讲, 接下来 11 张 slide 大概 28 分钟。"

---

## Slide 2 / 12 — Roadmap · 本周 5 个重点 (1 min)

Slide content: 5 topic bullets previewing the deck.

**EN** — walk through the 5 topics without expanding, ~10 s each:
1. **Topic 1 wrap** — Initial Run + UNIT_AUDIT (Week 7 carried, no new work, 1 slide).
2. **Topic 2 production推进** — v1/v2 fail recap → v3 design → smoke PASS → production launched (4 slides).
3. **Topic 3 ML 转化 demo** — three MetaD-unique descriptors that ANin GenSLM and Yu MMPBSA cannot produce (3 slides).
4. **SI-faithfulness audit chain** — 8 rounds of Codex + sub-agent second-pass (1 slide).
5. **Cross-lab dataflow + 2026-05-01 kill-switch state + Week 9 ask** (2 slides).

**中文** — 逐条点出, 不展开, ~10 秒一条:
1. **Topic 1 wrap** —— Initial Run + UNIT_AUDIT 是 Week 7 已完成, 1 张 slide 复述 conclusion.
2. **Topic 2 10-walker 推进** —— v1/v2 失败回顾 → v3 设计 → smoke PASS → production launched (4 slides).
3. **Topic 3 ML 转化 demo** —— 三个 MetaD 专有 descriptor, ANin 的 GenSLM 和 Yu 的 MMPBSA 都做不出 (3 slides).
4. **SI-faithfulness 8 轮 audit chain + sub-agent second-pass** (1 slide).
5. **Cross-lab dataflow + 2026-05-01 kill-switch + Week 9 ask** (2 slides).

**Transition**: "Topic 1 一句话过, Topic 2 是本周 main result, 多花时间。"

---

## Slide 3 / 12 — Topic 1 deck-main · Initial Run (24 ns, post-FP-034) (2 min)

Slide content: `reports/figures/initial_pilot_latest_fes.png` — single 2D contour, x=s (dim), y=z_RMSD (Å), color=ΔG (kcal/mol), 24.03 ns / max_s=14.05 / 12,015 Gaussians.

**EN**: "This is the latest Initial pilot FES — 24 nanoseconds of single-walker MetaD on the FP-034-corrected path, frozen this afternoon. Y-axis is z RMSD in Angstrom, x-axis is the path coordinate s dimensionless from 0.5 to 15.5, color is ΔG in kcal per mol. You can see clear O / PC / C basins separated along the path. Note: this is the FALLBACK contract — HEIGHT 0.3, BIASFACTOR 15 — the seed-discovery stage in the SI protocol, NOT the production FES yet."

**EN — before vs after framing**: "Before the FP-034 fix, the same path-CV stuck at s less than 1.9 over 16 nanoseconds — basically trapped at the Open endpoint. After the path realignment (NW alignment, 9.5× identity gain), the pilot now explores the full O-to-Closed path in 24 nanoseconds. The realignment is the single largest delta this campaign."

**EN — why differs from SI**: "SI Fig S2 and S3 are 10-walker × 50 nanoseconds × shared HILLS — about 500 nanoseconds aggregate sampling on the PRIMARY contract HEIGHT 0.15 BIASFACTOR 10. What we're showing is the upstream Initial pilot — one walker, FALLBACK contract, 24 nanoseconds. The 10-walker production launched this morning (45784112), running now, and will produce the SI-comparable figure once 10 nanoseconds per walker accumulates — ETA tomorrow morning. The deck main figure will swap then."

**中文**: "这张是 Initial pilot 最新的 FES——FP-034 修复后的 path 上跑了 **24 ns 单 walker**, 今下午 frozen 出来的。**y 轴是 z 的 RMSD (Å), x 轴是 path coordinate s (无量纲, 0.5 到 15.5), color 是 ΔG (kcal/mol)**。可以清楚看到 **O / PC / C 三个 basin 沿 path 分开**。注意: 这是 **FALLBACK 合约**——HEIGHT=0.3, BIASFACTOR=15——SI 协议里的 **seed-discovery 阶段**, 不是 production FES。"

**中文 — before vs after**: "FP-034 修复**之前**, 同一个 path-CV **跑 16 ns 卡在 s < 1.9** —— 基本困在 Open 端出不去。修复**之后** (NW alignment, identity 提升 9.5×), pilot 在 **24 ns 内 explore 完整 O→Closed path**。**这次 campaign 最大的单点 delta 就是 path realignment。**"

**中文 — 为什么跟 SI 不一样**: "**SI Fig S2/S3 是 10-walker × 50 ns × shared HILLS, 大约 500 ns aggregate sampling, PRIMARY 合约 HEIGHT=0.15 BIASFACTOR=10**。我们这张是上游 **Initial pilot —— 单 walker, FALLBACK 合约, 24 ns**。**10-walker production 今早已经启动 (45784112), 正在跑, 等每个 walker 累积到 10 ns 就能出 SI-comparable 的图——ETA 明早**, deck 主图到时候 swap 过去。"

**Transition**: "下一页讲 Topic 2 production 怎么从 v1/v2 失败一路修到 v3 PASS 的。"

---

## Slide 4 / 12 — Topic 2 (1/4) · v1 + v2 失败回顾 (3 min)

Slide content: 2-row table — v1 / v2 failure mode with 1-sentence root cause + FP code.

**EN — v1 row**: "v1 SLURM 45558834 launched 2026-04-23. Scancelled after 1 hour 28 minutes. Root cause FP-030: all 10 walkers were seeded from the same equilibrated frame from cMD output, so all 10 stuck at s≈1 — the homogeneous-start failure mode."

**EN — v2 row**: "v2 SLURM 45570699 launched 2026-04-24. All 10 walkers crashed within 12 minutes, exit code 139. Root cause: production launched directly from coordinate-only `start.gro` files with `continuation=no, gen_vel=yes` AND PLUMED on simultaneously. Un-thermalized atoms hit the path-CV bias before the velocities equilibrated; LINCS bond-stress on atoms 4463-4465 (the v2 crash signature) overflowed."

**EN — quick line**: "Both failures were on COLVAR-extraction-as-seed materializer that I wrote, NOT the SI protocol. v1 was wrong about WHICH frames to extract; v2 was wrong about HOW to start them. The SI was right both times."

**中文 — v1 row**: "v1 SLURM 45558834, 2026-04-23 启动, 1h28min 后 scancel。根因 **FP-030: 10 个 walker 全用同一个 cMD equilibrated frame 起点, 全卡在 s≈1**—— 同质起点 failure mode."

**中文 — v2 row**: "v2 SLURM 45570699, 2026-04-24 启动, 12 分钟内 10 个 walker 全 crash, exit code 139. 根因: **production 直接从 coordinate-only start.gro 起跑, continuation=no + gen_vel=yes + PLUMED on 同时**, 速度还没热化, path-CV bias 已经压上来, **LINCS bond-stress 在 atoms 4463-4465** (v2 crash signature) 直接 overflow."

**中文 — 关键线**: "**两次失败都是我写的 materializer 出问题, 不是 SI 协议错。** v1 错在抽哪些 frame, v2 错在怎么启动它们。SI 两次都是对的。"

**防守预案**:
- Yu: "你怎么确认 v3 不会再炸?" → "见下一张, 3-stage 设计 + smoke 10/10 PASS。"

---

## Slide 5 / 12 — Topic 2 (2/4) · v3 design + smoke PASS (3 min)

Slide content: 3-box flow diagram (`start.gro → EM → em.gro → NVT → nvt.gro+cpt → MetaD → metad.xtc + COLVAR + HILLS`) with PASS gates.

**EN — design**: "Three stages per walker. Stage 1: EM 1000 steps, no PLUMED, gives `em.gro` with `Maximum force < 1000 kJ/mol/nm`. Stage 2: NVT 100 ps, PLUMED still off, `gen_vel=yes` to initialize Maxwell-Boltzmann velocities at 350 K, gives `nvt.gro + nvt.cpt`. Stage 3: MetaD 50 ns, PLUMED on, `continuation=yes` reads `nvt.cpt` so velocities are inherited from NVT — no double thermalization. Each stage's output feeds the next stage's input as a coordinate file plus a checkpoint where applicable."

**EN — smoke PASS**: "Smoke 45783311, 2026-04-25 morning, 10-way array, 30-min wall, 1000+1000+1000 steps. ALL 10 walkers PASS. EM Max force range 938-986 (well under 1000), 0 LINCS warnings, 0 atoms 4463-4465 errors, HILLS deposited 1 hill / 2 ps per walker, 0 exit 139, all walkers COMPLETED 0:0. Took 24 min wall."

**中文 — 设计**: "每个 walker 三阶段。阶段一: **EM 1000 steps, PLUMED off**, 输出 `em.gro`, Maximum force < 1000 kJ/mol/nm。阶段二: **NVT 100 ps, PLUMED 还是 off, gen_vel=yes** 在 350 K 初始化 Maxwell-Boltzmann 速度, 输出 `nvt.gro + nvt.cpt`。阶段三: **MetaD 50 ns, PLUMED on, continuation=yes 读 nvt.cpt**, 速度从 NVT 继承, 不会双重热化。每一阶段的输出是下一阶段的输入坐标 + checkpoint."

**中文 — smoke PASS**: "**Smoke 45783311** (2026-04-25 上午, 10-way array, 30 min wall, 1000+1000+1000 步): **10/10 PASS**。EM Max force 938-986 (低于 1000 阈值), **0 LINCS warning, 0 atoms 4463-4465 错误**, HILLS deposit 1 hill / 2 ps, 0 exit 139, 全 walker COMPLETED 0:0。24 min wall 跑完。"

---

## Slide 6 / 12 — Topic 2 (3/4) · SI-faithful seed selection + walker_09 caveat (2 min)

Slide content: 10-row seed table from VALIDATION_REPORT (target_s, time_ps, s, z, rule).

**EN**: "Seeds = 10 CV-diverse snapshots from Initial MetaD trajectory at the time-points `materialize_v3_validation.py:select_seeds()` selects via window-min-z. Targets are `linspace(1.0, max_s_observed, 10)` so the 10 seeds cover the full path including the C-region. Selection rule: in each `[target-Δ/2, target+Δ/2)` window, pick the row with minimum `z=path.zzz` to start farthest from the upper wall. Hard cap `seed.z < 2.5` rejects upper-wall starts."

**EN — walker_09 caveat**: "Walker 09 starts at s=13.29, z=2.01 — close to the wall. Pilot has very few low-z frames in the high-s region; this is a pilot-undersampling issue, not a selection-rule issue. NVT pre-equilibration (PLUMED off, 100 ps) gives the upper wall time to relax z before MetaD wall takes effect. Smoke walker 09 EM converged in 759 steps without UPPER_WALLS violation, so the design works. If walker 09 collapses in production, fallback action is documented: extend pilot to 30 ns and re-materialize."

**中文**: "**Seeds 来自 Initial MetaD 轨迹的 10 个 CV-diverse 快照**。Target = `linspace(1.0, max_s_observed, 10)`, 覆盖完整 path 包括 C 段。选择规则: 每个 `[target-Δ/2, target+Δ/2)` 窗口里选 `z=path.zzz` 最小的那一帧 (离上壁最远)。Hard cap `seed.z < 2.5` 拒绝上壁起点。"

**中文 — walker_09 caveat**: "**walker_09 起点 s=13.29, z=2.01, 靠 wall**。Pilot 在高 s 区低 z frame 很少, **这是 pilot 欠采样问题, 不是选择规则问题**。NVT pre-equilibration (PLUMED off 100 ps) 给 walker 时间让 z 先 relax 再开 MetaD wall。Smoke walker 09 EM 759 steps 收敛, 没碰 UPPER_WALLS, 设计生效。production 如果 walker 09 还是塌, fallback 已经文档化: pilot 延到 30 ns 重新 materialize。"

**Transition**: "下一页讲 production 当前状态。"

---

## Slide 7 / 12 — Topic 2 (4/4) · Production state + Codex R8 verdicts (3 min)

Slide content: Production health table (10 walkers × HILLS row count + s-range) + 2 R8 verdicts.

**EN — health**: "Production SLURM 45784112 launched 2026-04-25 16:08 EDT. As of meeting time, all 10 walkers RUNNING, HILLS rows 200-310 per walker, walker advancement: walker_06 reached s=10.86, walker_08 reached s=10.91, walker_07 reached 9.30 — three walkers crossed into C-region. 0 LINCS warnings, 0 fatal errors. The shared-HILLS Multiple-Walkers MetaD is confirmed working: one HILLS file per walker in shared `WALKERS_DIR=../HILLS_DIR`, all 10 walkers reading the same accumulated bias."

**EN — R8 Q1**: "Codex Round 8 verified the SI quote: production FES is built from 10-walker production HILLS only; do NOT combine initial pilot HILLS into the sum. The pilot uses FALLBACK contract (HEIGHT=0.3, BIASFACTOR=15) and production uses PRIMARY (0.15, 10) — WT-MetaD theorem requires single biasfactor."

**EN — R8 Q2**: "Codex Round 8 also verified the seed strategy. PM proposed window-min-z (no z ceiling). Codex independently recomputed seeds: byte-identical to the v1 tiered output on the current pilot (every window already has low-z candidates). Conclusion: do NOT scancel 45784112, current run is essentially equivalent to PM v2. Conceptual clean-up patch applied to materialize_v3_validation.py for future re-materializations."

**中文 — health**: "Production SLURM 45784112, 2026-04-25 16:08 EDT 启动. 开会时刻全 10 walker RUNNING, HILLS 200-310 rows per walker, walker_06 s=10.86, walker_08 s=10.91, walker_07 s=9.30 —— **三个 walker 已经跨过 C-region**。0 LINCS warning, 0 fatal error. **shared-HILLS Multiple-Walkers MetaD 工作正常**: 每 walker 一个 HILLS 文件存在共享 `WALKERS_DIR=../HILLS_DIR`, 10 个 walker 共享累积 bias。"

**中文 — R8 Q1**: "**Codex Round 8 verbatim 引了 SI 原文: production FES 只用 10-walker production HILLS, 不要把 initial pilot HILLS 合进去。** 我们 pilot 用的是 FALLBACK 合约 (HEIGHT=0.3, BIASFACTOR=15), production 用 PRIMARY (0.15, 10), WT-MetaD 理论要求单一 biasfactor, 混不可。"

**中文 — R8 Q2**: "**Codex R8 同时审了 seed 策略**。PM 提议 window-min-z (无 z 上限)。Codex 独立重算了 seed: **跟当前 v1 tiered 输出 byte-identical** (每个 window 都已经有低 z 候选, fallback 没启用)。结论: **45784112 不需要 scancel, 当前 run 实质就是 PM v2 等价**。概念清理 patch 已经打到 materialize_v3_validation.py, 给未来 re-materialize 用。"

**防守预案**:
- Yu/PI: "production FES 几张图能放deck?" → "目标今晚 10 ns/walker (=5000 HILLS rows 各 walker) 时由 watcher 自动渲染, R5 Codex pseudocode + R7 Codex 渲染 skill 都已就位。"

---

## Slide 8 / 12 — Topic 3 (1/3) · ML 转化 4-tier 整体思路 + descriptor framing (2 min)

Slide content: 4-row tier table (L0/L1/L2/L3) on top + 3-row descriptor framing on bottom.

**EN — 4-tier framework (15 s setup)**: "I split the MetaD-to-ML conversion into four tiers — each one feeds a different role in the general training pipeline. Tier zero is descriptors — input features. Tier one is state pseudo-labels — classification target. Tier two is free energy values — supervised regression target. Tier three is candidate ranking — final output. Tiers zero and one are always available because they're descriptive. Tiers two and three are gate-controlled — they only populate when convergence and activity proxy gates pass. If gates fail, the system degrades to F0-only research mode by design — that is the kill-switch wiring from Red Team Section 8."

**EN — descriptor framing**: "For tier 0 specifically, three descriptors that the upstream sequence ML lab and the downstream binding-score lab cannot produce. P(state) — fraction of frames in O / PC / C; needs biased sampling, not docking pose. Mean z RMSD per state — per-state geometric stability; needs trajectory, not single-frame energy. Sigma_s of t — adaptive bias deposition shape; proxies sampling difficulty per region. None derivable from sequence embedding or single MMPBSA score."

**EN — anti-overclaim**: "Critical caveat: V1 ships RAW frame counts, not Boltzmann-reweighted populations. Tiwary-Parrinello c-of-t reweighting is a NotImplementedError stub, deferred to V2 once production FES converges. V1 acceptance criteria do NOT apply to reweighted values."

**中文 — 4-tier 框架**: "**MetaD 到 ML 的转化我切成 4 层, 每一层在 general training pipeline 里承担不同的 role**: **L0 描述符 → input feature, L1 状态标签 → classification target, L2 自由能 → supervised regression target, L3 候选排序 → final output**。L0/L1 任何时候都能给(描述性), L2/L3 是 **gate-controlled** —— convergence 和 activity proxy gate 不 PASS 就不开。Gate fail → 整套退化到 F0-only research mode, 这就是 RED_TEAM §8 三个 kill-switch 的 wiring。"

**中文 — descriptor framing**: "**L0 这一层我具体演示三个 descriptor**, 上游 ANin (sequence) 和下游 Yu (单帧 binding) **都做不出**。P(state): 每个状态下的 frame 占比, 需要 biased sampling, 不是 docking pose。⟨z_RMSD⟩|state: 状态内几何稳定性, 需要轨迹, 不是单帧能量。σ_s(t): adaptive bias deposit 形状, 表征每区域 sampling 难度。三个都**不能从 sequence embedding 或 MMPBSA 单帧打分推出**——这是 MetaD 的不可替代价值。"

**中文 — anti-overclaim**: "**关键 caveat: V1 ships 的是 raw frame count, 不是 Boltzmann-reweighted population**。Tiwary-Parrinello c(t) reweighting 是 NotImplementedError stub, 延到 V2 (production FES converged 后)。V1 验收标准**不适用于** reweighted value, V2 要单独验收。"

**Slide table reference (4-tier)**:

| 层 | 在 pipeline 里的 role | 输入 | 现在能给? |
|---|---|---|---|
| L0 | input feature | COLVAR | ✅ |
| L1 | classification target | COLVAR + state mask | ✅ |
| L2 | regression target | HILLS + sum_hills + ESS | ❌ gate convergence PASS |
| L3 | final output | L2 + activity proxy + seq embed | ❌ gate L2 + PM Q1 |

---

## Slide 9 / 12 — Topic 3 (2/3) · 3-panel descriptor figure (2 min)

Slide content: `reports/figures/metad_unique_descriptors.png` (P(state) bar + ⟨z⟩|state strip + σ_s(t) line, pilot 19.83 ns).

**EN — read off numbers**: "Panel left: P(O)=18.67%, P(PC)=22.50%, P(C)=6.16%, P(off-path)=52.67%. PC is most populated of the three states because pilot started near s=7 and walker explored backward to O before pushing forward. Panel center: ⟨z_RMSD⟩|O = 1.04 Å, ⟨z_RMSD⟩|PC = 1.08 Å, ⟨z_RMSD⟩|C = 1.28 Å — C state has the highest off-path deviation, expected because path endpoint geometry is sparser than O endpoint. Panel right: σ_s(t) ranges [0.003, 1.401] over 19.8 ns — adaptive sigma inflated when walker entered unexplored basin, deflates when basin filled."

**EN — when production lands**: "Tonight's auto-render will swap pilot data with 10-walker production data. Same script, same axis units, same caveats; only data path changes."

**中文 — 读数**: "**左 panel**: P(O)=18.67%, P(PC)=22.50%, P(C)=6.16%, P(off-path)=52.67%. PC 占比最高, 因为 pilot 从 s=7 起跑, 先 explore 回 O 再推到 C。**中 panel**: ⟨z_RMSD⟩|O = 1.04 Å, ⟨z_RMSD⟩|PC = 1.08 Å, ⟨z_RMSD⟩|C = 1.28 Å —— C state off-path 最大, 符合预期 (path 终点几何比起点稀疏)。**右 panel**: σ_s(t) 在 19.8 ns 内 [0.003, 1.401] 区间; **adaptive sigma 在 walker 进未探索 basin 时膨胀, basin 填满后收缩** —— 这是 MetaD 独有的 sampling difficulty proxy。"

**中文 — production 替换**: "今晚 watcher 自动渲染 production 版本, **同 script 同坐标轴单位同 caveat, 只改数据路径**。"

---

## Slide 10 / 12 — Topic 3 (3/3) · ML cartridge V1 contract + sub-agent audit (2 min)

Slide content: ML V1 ship target 2026-07-18 + 8-round audit chain table + sub-agent finding count.

**EN — V1 contract**: "Demo command `evaluator score-fasta GenSLM230.fasta --against WT_PfTrpB_FES_v1.npz` outputs CSV with columns sequence_id, F0_score, pathgate_score, combined_rank, confidence_band. PathGate column populated only if `convergence_grade.status == PASS`; otherwise EVAL_ONLY tag and excluded from combined_rank. Three kill-switches wired: D-Trp blindness, MMPBSA-truth recursion (3-tier 0.6/0.75 threshold), PathGate-MMPBSA disjoint."

**EN — audit chain**: "Eight rounds of Codex audit (R0, R0.5, R1, R2, R4, R5, R7, R8) plus an independent sub-agent second-pass found 10 software-debt issues that all 8 Codex rounds missed: cross-doc threshold inconsistencies, silent assumption gaps, kill-switch unsatisfiable preconditions when activity_proxy=MMPBSA, knife-edge defaults. All 10 fixed via rewording — no design churn. PM Q2 (GenSLM populated/null) reframed as informed default not theater. Q1 split into Q1a (proxy choice) + Q1b (n>=12 commitment)."

**EN — pending PM decisions**: "Five PM decisions still pending and gating L2/L3 supervised labels: (1) activity proxy MMPBSA/k_cat/bins, (2) GenSLM populate or null, (3) L2 scope WT-Ain only / 3-variant, (4) reweight estimator, (5) burn-in policy. The audit just lowered the cost of getting these wrong by making the cascades visible."

**中文 — V1 合约**: "Demo command 输出 CSV, 列 sequence_id, F0_score, pathgate_score, combined_rank, confidence_band。**pathgate_score 只在 convergence_grade.status==PASS 时填充**; 否则 EVAL_ONLY tag, 不进 combined_rank。**三个 kill-switch wired**: D-Trp blindness / MMPBSA-truth recursion (3-tier 0.6/0.75 阈值) / PathGate-MMPBSA disjoint。"

**中文 — audit chain**: "**8 轮 Codex audit (R0/R0.5/R1/R2/R4/R5/R7/R8) + 独立 sub-agent second-pass** 又找出 10 个 software-debt issue, 8 轮都漏了: 跨文档阈值不一致、silent assumption 漏洞、kill-switch 在 activity_proxy=MMPBSA 时 unsatisfiable, knife-edge 默认。**全 10 个 fixable via rewording, 无 design churn**。PM Q2 (GenSLM populated/null) 重写成 informed default 不是 theater。Q1 拆成 Q1a (proxy choice) + Q1b (n≥12 commitment)。"

**中文 — pending decisions**: "**5 个 PM 决策仍 pending**, 阻塞 L2/L3 supervised label: (1) activity proxy MMPBSA/k_cat/bins, (2) GenSLM populate or null, (3) L2 scope WT-Ain only / 3-variant, (4) reweight estimator, (5) burn-in policy。这次 audit 把 cascade 暴露出来, 决策错的代价降低。"

---

## Slide 11 / 12 — Cross-lab dataflow + 2026-05-01 kill-switch state (1.5 min)

Slide content: 3-lane dataflow diagram (ANin GenSLM → joint_features.parquet ← Yu MMPBSA-30 / Cartridge L0/L1) + kill-switch status check.

**EN — dataflow**: "Three lanes feed `joint_features.parquet`. ANin's GenSLM-25M sequence embeddings: column `genslm_embed = null` in V1 since `d_model` and pooling rule are BLOCKED #1+#2 — V1 ships F0+state-pseudo only, GenSLM populates in V2. Yu's MMPBSA-30 set: feeds activity_proxy column once PM picks (MMPBSA / k_cat / bins). My MetaD cartridge: feeds L0 (s, z, time) + L1 (state_pseudo) from production COLVAR; L2 (FES values + state masks) populates only on convergence PASS."

**EN — kill-switch state**: "Today is 2026-05-01 — the kill-switch deadline per Convergence_Memo §7. Status: WT-Ain v3 production launched but NOT YET converged — 0.3 ns/walker as of meeting; PASS gate is ≥45 ns/walker with `|ΔΔG_PC-O(50ns) - ΔΔG_PC-O(40ns)| ≤ 0.5` per Codex R5. So convergence_grade.status = PROVISIONAL, F0+PathGate Evaluator degrades to F0-only research-mode if not PASS by next checkpoint. Kill-switch fires correctly."

**中文 — dataflow**: "**三条 lane 喂 joint_features.parquet**。ANin GenSLM-25M sequence embeddings: V1 中 `genslm_embed = null` (BLOCKED #1+#2 d_model + pooling rule), V1 ships F0+state-pseudo only, GenSLM 等 V2。Yu MMPBSA-30: PM 选定 activity proxy 后填 activity_proxy 列。我的 MetaD cartridge: L0 (s, z, time) + L1 (state_pseudo) 从 production COLVAR 来; L2 (FES values + state mask) **只在 convergence PASS 时才 populate**。"

**中文 — kill-switch state**: "**今天 2026-05-01, 是 Convergence_Memo §7 的 kill-switch 死线**。状态: **WT-Ain v3 production 已启动但未收敛** —— 开会时 0.3 ns/walker, PASS gate 是 ≥45 ns/walker + `|ΔΔG_PC-O(50 ns) - ΔΔG_PC-O(40 ns)| ≤ 0.5` (Codex R5)。所以 **convergence_grade.status = PROVISIONAL**, F0+PathGate Evaluator 按设计降级到 F0-only research-mode (RED_TEAM §8)。kill-switch 按预设触发, V1 contract 不破。"

---

## Slide 12 / 12 — Week 9 ask + open questions (1 min)

Slide content: 3-bullet PI ask + 3-bullet open Q.

**EN — Week 9 ask**:
1. **PM activity-proxy decision** (Q1a + Q1b) — without this, L2/L3 supervised label is undefined; blocks V1 demo end-to-end.
2. **Wall-clock budget for production** — 24h gives ~20 ns/walker; need ~50 ns/walker for PASS. Approve extension to 72h or accept PROVISIONAL ship?
3. **GenSLM populate decision** (Q2) — null is the working assumption; if PI wants populated, V1 ship slips ~3 weeks.

**EN — open questions**:
1. Is 8 rounds of Codex audit + sub-agent second-pass enough rigor for V1 ship, or should we add a third independent reviewer (different model)?
2. Should V2 (with reweighting) ship under same V1 PR/FAQ acceptance criteria, or a separate criteria set per Sub-agent finding #10?
3. Walker_09 high-z caveat — if production walker_09 collapses against UPPER_WALLS in next 24h, is the documented fallback (extend pilot to 30 ns) acceptable, or is there a shorter-loop fallback?

**中文 — Week 9 ask**:
1. **PM activity-proxy 决策 (Q1a + Q1b)** —— 没这个 L2/L3 supervised label 不定, 阻塞 V1 demo end-to-end。
2. **Production wall-clock 预算** —— 24h 大概 20 ns/walker, 需要 50 ns/walker 才 PASS。是延到 72h 还是接受 PROVISIONAL ship?
3. **GenSLM populate 决策 (Q2)** —— null 是 working assumption, PI 要 populated 的话 V1 ship 推迟 3 周左右。

**中文 — open questions**:
1. **8 轮 Codex + sub-agent second-pass 够 V1 ship 严谨度吗?** 还是再加一个第三方独立 reviewer (不同 model)?
2. **V2 (带 reweighting) 该跟 V1 同一套 PR/FAQ 验收标准, 还是按 Sub-agent finding #10 单独验收?**
3. **walker_09 高 z caveat** —— production 24h 内 walker_09 撞 UPPER_WALLS 塌了, 文档化的 fallback (pilot 延到 30 ns) 可接受吗, 还是有更短的 short-loop?

---

## Q&A 防守预案 (PI/Yu likely asks)

| 问题 | 答 |
|------|----|
| "production FES 图怎么没?" | "10 ns/walker watcher 自动渲染, 大概今晚 19:00-20:00 EDT。watcher 已 armed, 用 Codex R5 sum_hills + R7 RMSD-axis renderer。" |
| "v3 EM+NVT pre-equil 是 SI 写的还是你加的?" | "**SI 没明说, 我加的**, 因为 v2 LINCS exit-139 必须 NVT 热化才能开 PLUMED。anti-overclaim 标 author-clarified, 在 plumed_template.dat 注释。" |
| "λ=100.79 跟 Miguel 80 差 26%, 谁错?" | "都对, 都是 self-consistent 的 Branduardi 真值, **是 path 不一样**。Miguel 用了 PfTrpS+PfTrpB+PfTrpB0B2 的 path; 我们 only PfTrpB Open→Closed seq-aligned 1WDW-3CEP path。Codex R4 验证: 26% λ 改变, max\|Δs\|=0.054, 远小于窗 half-window 0.66, seed 不受影响。" |
| "kill-switch 真的触发降级, 还是你 sandbagging?" | "**RED_TEAM §8 + Codex R0/R2/R4 都验证过 wiring**。Sub-agent second-pass 又抓了一个 unsatisfiable precondition (kill-switch #3 在 activity_proxy=MMPBSA 时永远 trip), 已 fixed。降级是 fail-safe, 不 sandbag。" |
| "Yu 看到 MMPBSA 跟 PathGate disjoint 怎么办?" | "**kill-switch #3 已重写**: 需要 PM week 2 前 pre-register secondary activity adjudication source (literature k_cat 或 hand-bins). 没 pre-register, kill-switch 不能 waive, V1 = F0-only。" |
| "Sub-agent audit vs Codex 谁 more authoritative?" | "**Codex 抓 schema bug 跟 unit, sub-agent 抓 cross-doc 一致性 + silent assumption**。两者互补, 都是文档证据。下次 audit 链建议: 先 Codex schema, 再 sub-agent narrative, 最后第三方独立 review。" |

---

## 时间预算

| Slides | EN+中文读完 | 累计 |
|---|---|---|
| 1-2 (Title + Roadmap) | 1.5 min | 1.5 |
| 3 (Topic 1 wrap) | 1 min | 2.5 |
| 4-7 (Topic 2 production) | 11 min | 13.5 |
| 8-10 (Topic 3 ML) | 5.5 min | 19 |
| 11-12 (closeout) | 2.5 min | 21.5 |
| Q&A buffer | — | ~21-23 min talk + 7-9 min Q&A |

总 ~30 min talk + 10 min Q&A, 落在 PI 1-on-1 预算内。
