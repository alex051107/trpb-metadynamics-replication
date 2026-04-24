# GroupMeeting 2026-04-24 — 技术文稿 (Technical Documentation)

> **文档定位**: 本周组会的完整技术底稿。目标读者是我（Zhenpeng）自己——
> 读完一遍后我必须能自信地向 Yu 解释**为什么**我们把 path 推倒重建、**怎么**
> 验证新 λ、**下一步**什么时候可以 launch 10-walker。对应的口语化版本见
> `PresenterScript_PPT讲稿.md`（如有）；本文件优先讲 why 而不是 what to say。
>
> **写作原则**: 科学上严谨、写作上诚实。每个数字必须可追溯到 repo 文件；
> 不确定的地方标 UNVERIFIED；manual-compute 的数值必须有脚本来源
> （遵循 `feedback_scriptize_all_numerics`）。本周**只有一件事**值得报告：
> FP-034（naive residue-number mapping bug）被发现并修复，整个 MetaD 体系
> 的 path CV 被重建。其他所有周内事件都是围绕这一件事展开。
>
> **创建**: 2026-04-23 by Claude (Opus 1M context)。
> 引用的所有上游文件请参见 Chapter 8 的文件对照表。

---

## 目录

**Part I — 战略与全局 narrative（新增 2026-04-23 晚）**

- A. [本周战略定位：从 replicator 到 cartridge owner](#第a章-本周战略定位)
- B. [本周探索路线树：所有尝试过的分支](#第b章-本周探索路线树)
- C. [ML-layer audit + STAR-MD 关系](#第c章-ml-layer-audit--star-md-关系)

**Part II — D1 技术主线：FP-034 诊断 + sequence-aligned path（原 Ch 0–10，verbatim）**

0. [本周核心结论](#第0章-本周核心结论)
1. [上周复盘（2026-04-17 → 2026-04-23）](#第1章-上周复盘)
2. [Miguel 2026-04-23 邮件 contract pivot](#第2章-miguel-邮件-contract-pivot)
3. [FP-034 诊断全过程](#第3章-fp-034-诊断全过程)
4. [Branduardi λ 自洽性重建](#第4章-branduardi-λ-自洽性重建)
5. [Production path & GROMACS atom serial 保留](#第5章-production-path--gromacs-atom-serial-保留)
6. [45515869 pilot 初期结果](#第6章-45515869-pilot-初期结果)
7. [10-walker primary production（pending gate）](#第7章-10-walker-primary-productionpending-gate)
8. [本周脚本 & 自动化清单](#第8章-本周脚本--自动化清单)
9. [未来方向 & Q&A 准备](#第9章-未来方向--qa-准备)
10. [判断原则与诊断规则](#第10章-判断原则与诊断规则decision-rationale)

> **阅读顺序建议**: Part I 三章是"为什么 D1 重要"、"本周还尝试了哪些被 reject 的
> 分支"、"这件事和 lab 里 ML 层/STAR-MD 的关系是什么"。Part II 是"D1 到底怎么做的
> 技术细节"，verbatim 保留。如果只有 10 分钟，读 Part I 的 A.1–A.3 + Ch 0；
> 如果 30 分钟，读 Part I 全部 + Ch 0 + Ch 6；完整技术理解读全文。

---

## 第A章 本周战略定位

> **本章定位**: D1 进展（Part II）回答"path 怎么修的、pilot 怎么跑的"；本章
> 回答 **"为什么这件事是 cartridge owner 的第一块砖，而不是一次孤立的 bug fix"**。
> 所有 framing 引自 `新任务explore/MetaD_Cartridge_Feasibility_Memo_2026-04-22.md`
> (下文简称 memo) v1.2，canonical 版本已 PM 签字。

### A.1 从 replicator 到 cartridge owner 的定位转换

过去 6 周（2026-03-15 → 2026-04-16）项目 self-framing 是 "**我在复刻 Osuna 2019
的 TrpB MetaDynamics 结果**"——replicator 定位，目标是生成一张和 Figure 3 相似的
FES。这个 framing 在 2026-04-22 之后被 PM + Claude + 三个独立 agent debate 之后
pivot 了（memo v1.2 § 0.1 canonical line）：

> **STAR-MD 把通用蛋白轨迹生成做满了。TrpB 需要的是 mechanism-grounded
> evaluation。我把 TrpB 的 MetaD 机制真值做成可复用 cartridge，用来评价、
> 筛选和纠偏 lab 里的生成式 enzyme-design pipeline。**
> — `MetaD_Cartridge_Feasibility_Memo_2026-04-22.md` L14

**语言边界**（memo § 0.1 L16–19）:

- ❌ "I'm building a new ML model / dynamics layer"
- ❌ "I own the TrpB ground truth"
- ✅ "I'm building the mechanism-grounded reference cartridge"
- ✅ "STAR-MD and my cartridge are upstream-downstream, not competitors"

**为什么要做这个 pivot**:

1. **外部压力**: ByteDance Seed 2026-02-12 发表 STAR-MD (`2602.02128v2.pdf` p1
   abstract: "scalable SE(3)-equivariant diffusion model that generates
   physically plausible protein trajectories over microsecond timescales...
   state-of-the-art performance across all metrics"). 如果我们继续把
   self-framing 说成"做 protein dynamics model"，在 Caltech/Anima lab 的视野
   里会立刻被这条线盖掉。
2. **内部 signal**: Anima 在 2026-01 内部 Slack 明确说过 generic dynamics line
   "not concrete enough"（memo § 0 附录 A; deep-research-report-3.md L207 "她
   最明确表达的...integration hygiene、以及 reward correctness"）。"再造一个
   model" 不是 lab 想要的。
3. **真正 open position**: lab 需要的是 *evaluation cartridge* —— Amin 在做
   STAR-MD-based SURF benchmark 但没有 TrpB-specific ground truth；Raswanth
   的 GRPO reward 缺 catalytic readiness head；Yu 做 MMPBSA ranking 缺 rare-state
   rescue。这些都是 cartridge-shape 的 consumer，不是 model-shape。
   (`deep-research-report_2.md` L5–7: "Slack 反复指向同一痛点: GRPO 可能因
   wrong rewards 产出 false positives... 当前 reward 未覆盖全程、reprotonation
   决定立体化学... Amin 明说 reward 必须 independent of alignment")

**这个 pivot 对 D1 意味着什么**: 本周 path 重建不再是"复刻 Osuna 2019 Figure 3
的一个前置步骤"，而是 **cartridge 第 1 个组件（path definition）的落地**。
corrected path (`path_seqaligned/path_seqaligned_gromacs.pdb`) 是 cartridge 的
foundation artifact；如果它本身是 FP-034 bug 的产物，cartridge 整栋楼都塌。
所以本周 D1 在新 framing 下的 load-bearing 意义 = 给 cartridge 打地基。

### A.2 Cartridge 的 7 个组件 + 本周状态

Memo v1.2 § 0.2 L22–30 把 "cartridge" 这个抽象词 ground 到 7 个具体 artifact:

| # | 组件 | 本周状态 | 来源 |
|---|---|---|---|
| 1 | **Path definition**: O/PC/C 的 PATHMSD 坐标（path.pdb + λ + state masks） | ✅ **本周完成**: `path_seqaligned_gromacs.pdb` + λ=80 + self-projection gate PASS | memo L24; `VERIFICATION_REPORT.md` L74–95 |
| 2 | **Reference FES**: WT / Aex1 / 变体（WT 先做） | 🟡 pilot 45515869 运行中，10-walker 待 launch | memo L25 |
| 3 | **State masks**: O / PC / C / off-path / reactive-ready | ⬜ 未开始（定义 rule + block analysis 脚本已部分写） | memo L26; memo § 2 表 L154 |
| 4 | **Block uncertainty**: 带 CI 的可信区间 | ⬜ 未开始 | memo L27 |
| 5 | **Rare-state frames**: 供生成模型/reward model 的 hard examples | ⬜ 未开始（需从 reweighted HILLS 导出） | memo L28, L156 |
| 6 | **Catalytic descriptors**: PLP/K82/Y301/E104/indole tunnel 机制几何 | ⬜ 未开始 | memo L29, L157 |
| 7 | **Scorer API**: `project_to_path()`, `score_trajectory()`, `state_occupancy()` | ⬜ 未开始（D2 本周 deliverable 要求写 `API_DESIGN.md` 草图） | memo L30, L37 |

**1/7 完成**，但这个 1 是**地基**——其余 6 个全都依赖 corrected path 的几何
正确性。FP-034 bug 过去 4 周没被发现意味着组件 2–7 即使写了也是污染产物（在 old
path 上算的 state mask 和 rare-state frame 都错）。所以本周的 D1 = 让组件 2–7 变
得可能。

### A.3 本周 D1/D2/D3 deliverables

Memo v1.2 § 0.3 L32–40 把本周 scope 从"5 个 ML 层 idea"收窄到 3 个 deliverable:

| # | Deliverable | 本周要做 | 完成度 | Gate |
|---|---|---|---|---|
| **D1** | **Cartridge core (最小版本)** | 把 Miguel PATH.pdb 对齐问清楚；WT reference 定义；PLUMED input 清理；state masks 草稿 | **90%**: path + λ + plumed 完成，state masks 未开始 | path.pdb 和 Miguel 版本一致 ✅ (λ=80 逐字) |
| **D2** | **Trajectory scoring wrapper (API 草图)** | 写 `replication/cartridge/API_DESIGN.md`：函数签名 + 输入输出 + 使用场景，不写实现 | **0%**: 未开始（本周精力全在 D1 救火）| 文件 commit |
| **D3** | **One lab-facing demo** | 二选一: Yu demo (simple CV 失败 → PATHMSD cartridge 给更有意义的诊断) 或 Amin demo (STAR-MD 输出被 cartridge 打分) | **0%**: 未开始（pilot 还没跑完）| 有一个可给出去的 notebook 或短报告 |

**不做的事**（memo § 0.3 L40）: MNG 作主线、Reactive PATHMSD、Arvind 电子效应。
这些是未来 claim，不是本周价值展现。

**自我评价**: D1 拿到 90% 是高分（预期 70%，因为 FP-034 吃掉 3 天），但 D2/D3
拖欠是 realistic risk——如果下周 pilot gate 不过需要回到 D1 debug，D2/D3 可能
直到 2026-05-01 kill-switch 都没开工。需要 PM 决策：是不是等 D1 完全通过 gate
再推 D2，还是 D2 API 设计可以先写 skeleton？

### A.4 五个 stakeholder 的 canonical 对话脚本

Memo v1.2 § 0.4 L42–54 给了 5 个 stakeholder 的 exact language。本节抄写
canonical 版，**不要** improvise——组会里直接读这几句：

**对 Yu**（已和我结对，rare-state rescue consumer; memo L44–46）:

> "I saw your OpenMM MetaD update. I'm working on the PLUMED/PATHMSD side and
> recently got the original-author PLUMED input for the Osuna TrpB MetaD
> protocol. I'm still reconciling the PATH.pdb construction, but I think this
> could be directly useful for testing reaction-coordinate choices beyond
> simple 1D/2D CVs."

**对 Amin**（STAR-MD benchmark owner; memo L47–49）:

> "I'm building a TrpB MetaD cartridge that can score generated trajectories
> by projecting them onto a mechanism-grounded PATHMSD/FES reference. If your
> STAR-MD/ConfRover benchmark needs an enzyme-specific task, TrpB could be a
> useful adversarial case."

**对 Raswanth**（GRPO reward owner, 被动 wait him come to me; memo L50–52）:

> "I can help evaluate whether top designs are dynamically plausible along
> the TrpB conformational coordinate, not just geometrically valid."

**对 Arvind**（PI, 等 WT FES 收敛后再对话; memo L53–55）:

> "I'm turning the TrpB MetaD replication into a reusable evaluation
> cartridge for ML-generated enzyme dynamics and design candidates."

**对自己**（internal framing; memo § 0.5 L57–58 一段话 pitch）:

> "STAR-MD and related models are making generic protein dynamics generation
> scalable. But enzyme design needs a different layer: mechanism-grounded
> evaluation. For TrpB, the relevant question is not only whether a generated
> trajectory is structurally valid, but whether it visits catalytic
> conformational substates and preserves PLP-dependent reaction geometry.
> I am building a MetaD-derived TrpB cartridge that turns expensive path-CV
> simulations into reusable labels, reference FES, rare-state frames, and
> scoring functions."

**脚本纪律**（我 enforce 给自己的）: 组会 Q&A 时如果被问 "what are you doing?"，
**不许** 说 "I'm replicating Osuna 2019" 或 "I'm building a dynamics model"。
必须是 "I'm building a mechanism-grounded evaluation cartridge for TrpB."
"Replicate" 这个词只在 section 级 scope 里用（"I replicated their path-CV"），
不在 project-level self-description 里用。

### A.5 硬 kill-switch：2026-05-01 前 WT FES 必须过 sanity check

Memo v1.2 § 0.8 L78–83 + § 5 L490–503:

| Gate | 当前状态 | 阻塞物 |
|---|---|---|
| WT MetaD 收敛 (pilot + 10-walker 跑完) | 🟡 pilot 45515869 rolling, 10-walker 待 launch | FP-030 O-end stall cause 在 corrected path 上是否仍存在？unknown until pilot reaches max_s > 12 |
| 至少 1 个变体 FES | ⬜ 未开始 | 需 WT gate 先过 |
| Path CV 已验证可用 | ✅ 已过 (driver self-projection PASS) | — |
| Repo cartridge directory layout | ⬜ 未开始 | 大量 uncommitted changes |
| Yu 能共享 MMPBSA 数据 | ⬜ 未确认 | 需 1 次对话（本周组会后启动 A.4 对 Yu 的脚本）|
| Amin 愿意把 TrpB 做 benchmark task | ⬜ 未确认 | 需 1 次对话（本周组会后）|

**kill-switch 定义**（memo § 0.8 L81, § 5 L503）: 如果 2026-05-01 前 WT FES 还
没过 sanity check，**所有 5 个 ML-layer 方向全部暂缓**，回到单 walker → 10-walker
升级，不推 cartridge framing。

**什么叫 sanity check**（project-internal 定义，比 memo 更 concrete）:

1. 10-walker 跑完 ≥ 50 ns（单 walker × 10 = 500 ns 等效）
2. 2D FES (s, z) 上 O / PC / C **三个** local minima 都可见（不是只 PC basin）
3. O→C 最 minimum-energy path 上的 barrier ≤ 20 kcal/mol（Osuna 2019 Figure 3
   报告 barrier ~12–15 kcal/mol，我们允许 30% wiggle）
4. Block CI（把 10-walker 分 2 组各算 FES）两组 O 基底深度差 < 2 kcal/mol

如果 2026-04-30 晚上任意一条不过，5-01 早上发 PM 邮件汇报 kill-switch 触发，
不继续扩到 D2/D3；专注让 WT 收敛。

**为什么给自己设这个死线**: 如果没有 hard cutoff，FP-034 这种 bug 会继续消耗
周级别时间；cartridge framing 会在一个不收敛的 foundation 上盖空中楼阁。
2026-05-01 = Caltech SURF 最终决策周期前的最后一个"可以 pivot 路线而不是 pivot
deadline" 时点。

### A.6 cartridge framing 的 pitfall 预警（内部自省）

新 framing 强但不是 free lunch。三个容易滑倒的地方，写在这里自己盯：

**pitfall 1 — "cartridge owner" 口气过大**: 本科生 + 2026-05 Caltech offer
未定，**不能**对外 claim "I own the TrpB ground truth"。memo L17 的否定列表就是
防这个。实际 self-description: "building the reference cartridge for *my own*
TrpB work, with the hope it can be useful to the lab". 低姿态但 specific.

**pitfall 2 — scope creep 回到 5 个 ML 方向**: memo § 3 曾列 A-G 7 个 ML layer
idea，§ 1.5 audit 后只有 MNG (方法 E) 独立活 (L131, L311)；cartridge 本身比任
何 ML layer 更 novel (memo § 1.5 L134 "The cartridge itself ... is likely more
novel than any individual ML layer built on top"). 如果下周有人问"你为什么不做
learned bias potential"，答 "方法 C (LBP) 已在 2025 文献被 NN-VES 吃掉 (memo
L240–245)，我 drop 了". 不 re-engage 被 audit kill 掉的分支.

**pitfall 3 — 把 D1 技术进展 oversell 成 D3 demo**: 本周 D1 拿到 90%，但
D3 (lab-facing demo) 是 0%. 组会不能讲成 "I have a cartridge". 正确表述:
"I have the path definition for the cartridge". Demo 是 2026-05 才能给出来的
东西。

---

## 第B章 本周探索路线树

> **本章定位**: 一周的工作不是直线，是一棵 branch & reject 的树。本章记录
> **所有被 reject 的分支**——不是为了 show 工作量，是为了 show "rejection
> 本身是正面信息"（每条 reject 砍掉一个物理 hypothesis space）。这样组会后
> 如果有人问"你们有没有试过 X"，我可以直接引 B.X 节说"试过，原因 A 否决".

### B.1 Probe sweep P1–P5（已废弃，基于 GEOM 误读）

**时间**: 2026-04-08 → 2026-04-15
**目录**: `replication/metadynamics/probe_sweep/P1..P5/`
**假设**: Osuna 2019 SI 只写了 "adaptive Gaussian width scheme to reach a
better sampling"，我们读成 `ADAPTIVE=GEOM`（Branduardi 2012 几何缩放）。5 组
σ-floor/ceiling 扫描：

| Probe | σ_min_s | σ_max_s | σ_min_z | σ_max_z |
|---|---|---|---|---|
| P1 | 0.01 | 0.2 | 0.001 | 0.02 |
| P2 | 0.02 | 0.3 | 0.002 | 0.04 |
| P3 | 0.005 | 0.5 | 0.0005 | 0.05 |
| P4 | 0.03 | 0.15 | 0.003 | 0.015 |
| P5 | 0.015 | 0.25 | 0.0015 | 0.025 |

（具体值见各 P*/plumed.dat；locked-vs-tunable 规则在
`probe_sweep/ladder.yaml`, 参见 userMemory `feedback_si_locked_factors`）

**Rejection trigger**（2026-04-23 Miguel 邮件）: Miguel 的 plumed.dat 给的是
`ADAPTIVE=DIFF SIGMA=1000`——不是 GEOM 模式，SIGMA=1000 是 **时间窗步数**不是
Gaussian 宽度标量。PLUMED 里 GEOM vs DIFF 同名不同语义
(`failure-patterns.md` FP-031 L454–465).

**Verdict**: P1–P5 5 组运行在 GEOM 下做——对 Osuna 协议不再具参考性。全部标
deprecated (task #36 in `NEXT_ACTIONS.md`)，运行数据保留作为 "GEOM vs DIFF"
敏感度对照数据资产，但不计入本周 FES 分析。

**这条 rejection 给了什么信息**: Osuna SI 的 "adaptive scheme" 字面不唯一，
**必须问原作者**。这直接导致 2026-04-20 给 Miguel 写邮件（`miguel_email.md`
往来存档），否则 probe sweep 还会继续扩到 P6–P10 浪费周级时间。

### B.2 Pilot matrix 2×2（anchor × sigma_seed；axis invalid 后部分保留）

**时间**: 2026-04-16 → 2026-04-19
**目录**: `replication/metadynamics/pilot_matrix/`
**设计**: 2 × 2 design of experiments，4 个 cell:

| | sigma_seed_A (GEOM-based) | sigma_seed_B (GEOM-based) |
|---|---|---|
| anchor_1WDW | cell 11 | cell 12 |
| anchor_3CEP | cell 21 | cell 22 |

**Rejection partial**（2026-04-23 Miguel 邮件）: sigma_seed 维度 invalid (基于
GEOM 误读)；anchor 维度 (1WDW vs 3CEP 作 starting structure) 仍合法，但必须
re-run 在 DIFF 下。

**Verdict**: axis 2/4 invalid，axis 1/3 scaffold 保留，实际 re-run pending 10-walker
收敛后再重启。commit `65625fc "pilot_matrix: scaffold 2x2 (anchor x sigma_seed)
without touching locked probe_sweep"` 留档。

**这条 rejection 给了什么信息**: DoE 级别的 sweep 在 contract 未锁的时候做是高
风险；**必须先 freeze contract 再 sweep**. 未来 sweep 规则 (`failure-patterns.md`
FP-031 防范): 任何 factorial design 前置检查是否每个 factor 都有 SI 明文或作者
邮件支持。

### B.3 Wall falsification（45448011, z↑ s 不动 → "wall 压制" 证伪）

**时间**: 2026-04-22
**目录**: `replication/metadynamics/miguel_2026-04-23/45448011_wall_test/`（本地
archive），Longleaf `/work/.../AnimaLab/metadynamics/miguel_2026-04-23/45448011/`
**假设**: 若 `UPPER_WALLS AT=2.5 KAPPA=800` 把 walker z 方向压死，则 z(R) 不能
escape path 邻域，可能连带把 s(R) 锁在 O basin。解锁 wall (KAPPA 800→0) 测试。

**结果**（现有 Ch 1.3 已讲，此处补 reject 逻辑）:
- z 方向: 从 ~0.8 Å² 飙到 ~2.7 Å²（上升 3.4×），说明 wall 确实在
  compress z
- s 方向: 完全不动，max_s 仍卡在 1.5 附近
- **→ wall 不是 bottleneck**. walker 不出 O basin 的原因不是 "wall 把它压回去"

**Verdict**: "wall 压制" 假设被 z↑/s→ 的解耦证伪。注意：z↑ 的结果同时也在暗示
"path 本身几何上就不对"——如果 path 是 valid 的，z 应该对 walker 不那么 invasive；
z 一解锁就飙说明 walker 在 old path 坐标系里离 path 本来就远。

**这条 rejection 给了什么信息**: 这是 → FP-034 的第一个硬物理 trigger。之前所有
"stall" 讨论都在参数空间 (σ, height, biasfactor)；wall test 之后才真正把注意力
推到 **coordinate space 本身是否 valid**. 所以 B.3 是 B.7（cross-model
consultation）和 Ch 3（FP-034 诊断）的前奏。没有这条 rejection，我们可能还在
调 HEIGHT 和 BIASFACTOR。

### B.4 Piecewise PC anchor at MODEL 8（5DW0/5DW3/5DVZ rejected；后被撤稿）

**时间**: 2026-04-20 → 2026-04-22
**目录**: `replication/metadynamics/path_piecewise/`
**假设**: 三-anchor piecewise path O=1WDW → PC=5DW0/5DW3 → C=3CEP 能让 walker
更容易穿过中间区（vs 两点 1WDW→3CEP linear interp）。测 PC 位置是否作为 MODEL 8
（15 帧的几何中点）是否合理。

**当时的 rejection**:
- 5DW0 chain A on naive path: s ≈ 1.069
- 5DW3 chain A on naive path: s ≈ 1.075
- 5DVZ chain A on naive path: s ≈ 1.067
- neighbor_msd_cv @ MODEL 8 = 0.96（threshold 0.3，FAIL）
- **原结论**: "biological βPC label ≠ 几何中点; PC-at-MODEL8 single-λ design 不
  成立" (`path_piecewise/README.md` verdict section, 现 RETRACTION)

**Retraction**（`path_piecewise/RETRACTION.md` L17–28）: corrected path 上同样
的投影:
- 5DW0 chain A: **s = 9.455** ✓
- 5DW3 chain A: **s = 8.508** ✓
- 5DVZ chain A: **s = 5.371** ✓

**→ 生物学 βPC label 一直是对的**. 2026-04-20 ~ 2026-04-22 三天的 piecewise
debugging 全部 invalid, 因为被 audit 的 path 本身是 FP-034 bug 的产物.

**这条 rejection 给了什么信息**:

1. FP-034 污染链的教材: naive mapping bug → spurious βPC rejection → 3 天
   lost debugging → FP-034 discovery (`RETRACTION.md` L54–58)
2. **Retraction 行为本身是正面贡献**: 保留整个旧目录 + 撤稿通知，作为 "AI 在
   corrupted foundation 上 debug 会产生 emergent false signal" 的案例记录。
   不删除。
3. `generate_piecewise_path.py` 和 `scan_pc_anchors.py` 的 projection logic
   本身是对的（commit `0dc49ab` 修的 z(R) log-sum-exp bug 也是有效修复）——
   当 cartridge 组件 3 (state masks) 开始开发时，这两个脚本可以被直接复用
   在 corrected path 上。

### B.5 Cross-model consultation（Pro + Codex + 2 Agent 独立 research）

**时间**: 2026-04-21 → 2026-04-22
**目录**: `chatgpt_pro_consult_45324928/` + `colab_review/`
**四路并行** (Ch 1.5 的扩展):

| 渠道 | 任务 | 输入 | 结论 |
|---|---|---|---|
| ChatGPT Pro (O1 长思考) | 审 HILLS 形态 + walker 动力学 | 45324928 HILLS + COLVAR + plumed.dat | "Probably path CV 坐标系本身有问题" (qualitative). 指出 σ_ss 在 DIFF scheme 下偏小 → 但不是 root cause |
| Codex peer review (MCP) | 独立复算 path_piecewise audit 的数值 | `generate_piecewise_path.py` + 5DW0/5DW3 PDB | 算数对，但指出 audit 的 path 源文件是 naive resid mapping 产物（Codex 第一个指出 bug 所在文件 + 行号）|
| Agent #1 (physics angle, web research) | 推算 barrier height vs 实际 bias 沉积 | Osuna 2019 FES + 45324928 HILLS cumulative bias | bias ≪ 理论 barrier，但 walker 动不了 → "CV 不是 good reaction coordinate" hint |
| Agent #2 (PLUMED internals, code archaeology) | 读 PATHMSD 源码 | PLUMED 2.9 src | "PATHMSD 对 reference frame 做 internal Kabsch alignment；它不检查 reference frames 是否合理" → 把 "path 是否合理" 这个问题从 PLUMED 层面 raise 到 user 层面 |

**四路 convergence**: 四条独立路径收敛到**同一方向**——"问题在 path 本身，不在
bias/wall/σ". 这种 4-way convergence 是 Claude 决定"集中火力重查 path
construction" 的 trigger（单一 consultation 不足，4 条独立 channel 同方向 = 极
低误报率 signal）。

**这条 rejection 给了什么信息**:

1. 多 agent consultation 的**方向 signal** 比单 agent "答案" 可靠。具体数字
   (σ_ss 多少) 每个 agent 各说各话，但"方向"（path vs param）一致 → 更可信.
2. Codex MCP 在 "code archaeology" 类任务上稳定（能指出第几行）;
   `plan-codex` workflow 本周启用得正是时候.
3. Deep-research agent 在 "novelty audit" 类任务（memo § 1.5 + § 3 AUDIT
   verdicts）上给出的结论和本周 path 诊断 orthogonal，两个 research track 都
   值得保留.

### B.6 path_construction_ABC_plan（A/B/C 对照设计，后被 FP-034 取代）

**时间**: 2026-04-22 下午
**文件**: `replication/metadynamics/miguel_2026-04-23/path_construction_ABC_plan.md`
（uncommitted，草稿）
**动机**: lambda_audit_2026-04-23.md L44 "A faithful-replication path forward
is not to run λ=80 on our path (that's a stress test, not replication), but
to reconstruct Miguel's path-construction recipe". 基于这个判断设计了 A/B/C
三条 candidate path recipes:

- **Plan A**: pure linear interp 1WDW→3CEP, naive resid mapping (status quo;
  本周被 FP-034 否决)
- **Plan B**: linear interp 1WDW→3CEP, **subset 选择不同**（只选 COMM domain
  97-184, 不包括 base 282-305）
- **Plan C**: **multi-crystal anchored**, insert 5DVZ/5DW0 as intermediate
  frames，interpolate by cluster rather than pure linear

**Rejection**（2026-04-23 凌晨 FP-034 发现）: A/B/C 三个都建立在 "naive resid
mapping" 上，修了 mapping (FP-034) 之后 Plan A (pure linear + sequence-aligned
mapping) 就够了——不需要 B 和 C 的复杂性。ABC plan 文件保留作 decision trail，
但不执行。

**这条 rejection 给了什么信息**: 在 bug 没定位前提前设计 A/B/C 实验组，会**在
bug 上再盖 3 层**. 正确顺序是 root-cause debug → 再设计对照. ABC plan 的教训：
lambda_audit 的 path-density hypothesis 本身是对的，但 path density 差异**不是
**21× 的 ratio 来源（实际来源是 naive mapping）。这提醒 lesson: debugging 层数
不能叠太深。

### B.7 Rejection 作为正面贡献（meta-narrative）

**本章的 meta 论点**: 5 条 rejection（B.1–B.5，B.6）每条都砍掉一个 hypothesis
space:

| Rejection | 砍掉的 hypothesis |
|---|---|
| B.1 probe sweep invalid | "σ schedule 是 bottleneck" |
| B.2 pilot matrix partial | "anchor + σ 二因素交互是 bottleneck" |
| B.3 wall unlock | "upper_wall 压制是 bottleneck" |
| B.4 piecewise at MODEL 8 | "PC 不在几何中点 = biology ≠ geometry" |
| B.5 cross-model 4-way convergence | "root cause 在参数空间" |
| B.6 ABC plan preempted by FP-034 | "path-construction recipe 差异是 21× ratio 来源" |

**最终剩下的 hypothesis**（唯一未被 reject 的）: "path 的 residue-to-residue
mapping 错了". 这就是 FP-034. 五条 rejection 不是失败的集合——是**归因过程本身**.

Group meeting Q 可能会问: "你们一周只修了一个 bug？"
Answer: "我们一周排除了 5 个其他 hypothesis，把 bug 从一个 1000-dim 的 'something
is wrong somewhere' 问题收窄到 `generate_path_cv.py` L668–671 的 3 行 hardcoded
residue list. Rejection tree 本身就是归因."

---

## 第C章 ML-layer audit + STAR-MD 关系

> **本章定位**: 为什么 cartridge 这个定位是 **与 STAR-MD 互补的 upstream-downstream
> 关系**，不是竞争；以及 5 个 ML-layer extension 方向在 2026-04-22 外部文献
> audit 之后的 verdict. 来源: memo § 1 + § 1.5 + § 3 + `2602.02128v2.pdf`
> abstract/intro.

### C.1 五个 ML-layer 扩展原初假设

Memo § 1 L107–116 + § 3 L164–388 列了 5 种"把 cartridge 延伸成 ML 层"的方法:

| 方法 | WHAT | Consumer | 原初 novelty 评估 |
|---|---|---|---|
| A — CRR (CatalyticReadinessReward) | 从 MetaD FES 拟合 state-conditional geometry scorer，作为 GRPO reward | Raswanth | 中-高 |
| B — PP-Prior (Path-Progress Conditioning) | reweighted p(s,z) 作为 pickled artifact 喂给 SE(3) diffusion | Amin / STAR-MD fork | 中 |
| C — LBP (Learned Bias Potential) | NN 参数化 V_bias(s,z) 替代手调 Gaussian | 跑变体 MetaD 的人 | 不确定 |
| D — TCR (Thermodynamic Consistency Regularizer) | 可微 loss 项 KL(p_model ‖ p_MetaD) 加到生成模型训练 | STAR-MD retrainer | 不确定 |
| E — MNG (Memory Necessity Gate) | lag-stratified Markov-vs-qMSM 诊断作为 adaptive-sampling rescue trigger | DeepDriveMD-like workflow | 高 |

这 5 个 idea 是 2026-04-20 3-agent debate 的合成输出（memo 附录 A L540–545），
不是 brainstorm list——每条都对应一个 lab stakeholder + 一个 load-bearing test.

### C.2 2026-04-22 外部文献 audit verdict

Memo § 1.5 L122–145 + § 3 各 subsection 末尾的 AUDIT VERDICT:

| 方法 | Verdict | 关键杀手 |
|---|---|---|
| A — CRR | **WEAKENED** (MED conf.) | PocketX (bioRxiv 2025.12.28.696754), ResiDPO (arXiv 2506.00297), ProteinZero (arXiv 2506.07459) 已做 GRPO+reward on protein design |
| B — PP-Prior | **WEAKENED** (MED-HIGH conf.) | Enhanced Diffusion Sampling (arXiv 2602.16634), Training-free molecular guidance (arXiv 2409.07359) 已占 energy-guided diffusion |
| C — LBP | **DEAD** (HIGH conf.) | NN-VES (Bonati/Parrinello PNAS 2019 arXiv 1904.01305), Deep-TICA+OPES+mlcolvar 已占完整空间 |
| D — TCR | **DEAD-ish** (HIGH conf.) | Thermodynamic Interpolation (JCTC 2024 10.1021/acs.jctc.4c01557), Energy-Based CG Flow (JCTC 2025 arXiv 2504.20940) |
| E — MNG | **ALIVE** (MED conf.) | 唯一独立可立得住的 |

（完整引用链见 memo 附录 C L562–591）

**Meta-结论**（memo § 1.5 L134）:

> "The cartridge itself (the FES + state labels + path CVs as a reusable
> artifact for TrpB specifically) is likely more novel than any individual
> ML layer built on top."

**这意味着什么**（memo L135–141）:
- Cartridge 本身（非 ML layer）是主产品
- ML 层是 **可选 extension**，不是主 contribution
- Pitch 重心 = "I own the only MetaD-grounded TrpB-family evaluation
  cartridge". ML 层作为 "cartridge 能解锁的下游"
- 5 个 ML 层里，**只有 MNG 独立可立得住**；其他需降级为"cartridge 的
  demonstration/plug-in"，不是主 claim

### C.3 每个方向详细 reasoning（audit 后的处置）

**CRR (方法 A)**—降级为 projection metric:
- memo § 3.1 L188 AUDIT verdict 原话: "唯一保留：将 CRR 重新定位为
  *projection metric*（把候选几何投到 parent TrpB 的 MetaD-validated 催化
  basin），不是 RL 框架本身. pitch 时强调 'conformational-readiness
  projection'，不要说 'new GRPO reward'."
- 对话 Raswanth 时（A.4 canonical 脚本）只说 "evaluate whether top designs
  are dynamically plausible"，不 claim "new reward function".

**PP-Prior (方法 B)**—路径 specific 保留，通用能量引导 drop:
- memo § 3.2 L214 AUDIT verdict: "通用能量引导死。保留：path-CV 专用的
  (s,z) conditioning for STAR-MD/MDGen-class trajectory models 还是空位。
  必须把 pitch 锁死在 'PATHMSD axis, not generic energy'"
- 和方法 D 合并为 "FES-consistent trajectory generation" 子模块（single
  artifact，两个消费模式：rejection sampling + classifier guidance）.

**LBP (方法 C)**—drop:
- memo § 3.3 L246 AUDIT verdict: "drop 这条作为独立 novelty. 如果用到，
  cite + apply，不 claim."
- 由方法 F (Reactive PATHMSD, memo § 3.6) 替换在 "5 个 active 方向" 里的
  位置.

**TCR (方法 D)**—merge 入 B:
- memo § 3.4 L281 AUDIT verdict: "作为独立 contribution 死. 保留作 3.2
  PP-Prior 的 training-time counterpart"
- 由方法 G (Physics Audit Layer, memo § 3.7) 替换 "作为独立 ML 层"的位置.

**MNG (方法 E)**—lead claim:
- memo § 3.5 L311 AUDIT verdict: "5 个方法里**唯一一个独立可立得住的**"
- 从原 priority #5 晋升 **lead #1**. "即使其它 4 条全被吃，MNG 这条单独也
  能立得住."（memo L318）
- 但本周 **不做** MNG implementation（memo § 0.3 L40 "MNG 作主线... 不做"）
  ——10-周 V0 先做 cartridge 本体，MNG 作为 "cartridge 能解锁的 runtime
  tool" 在 2026-06 以后考虑.

### C.4 新候选 F (Reactive PATHMSD) + G (Physics Audit Layer)

audit 杀掉 C 和 D 之后，memo § 3.6 + § 3.7 新增两条替代:

**方法 F — PLP-aware Reactive-Coordinate CV Extension**（memo § 3.6 L322–343）

- WHAT: 扩展现有 PATHMSD 把 PLP Schiff-base 几何（K82-Cε ↔ PLP-C4' 距离、
  Schiff-base 平面扭转、Dunathan-like 角）纳入 path 定义, 产出 "reactive
  PATHMSD"——原生带化学态辨识力的 CV.
- Consumer: 我自己做变体 MetaD、Yu 做 catalytic MD、Amin 做 benchmark 时的
  TrpB task.
- Load-bearing test (memo L330–332):
  1. Reactive PATHMSD 在 WT TrpB 上能把 O/PC/C 再分出 "catalytically
     competent C" vs "COMM-closed but Schiff-base misaligned" 两子态
  2. 对 Y301K 等已知变体，reactive-path FES 里子态 occupancy 能预测实验
     活性方向
- 10-wk V0 可行: ✅ PLUMED template + 一轮 WT 验证
- AUDIT: "novelty HIGH 的可能性中等；最大风险是 Reviewer 认定'只是应用级
  改动'"（memo L342）

**方法 G — Generative-Model Physics-Consistency Audit Layer**（memo § 3.7
L346–370）

- WHAT: `physics_audit(trajectory, reference_cartridge)` wrapper. 输入: 任何
  生成式轨迹模型的输出 N 帧. 输出: 结构化 audit 报告含 reweight JSD, FDT
  closure residual, path-progress matching, state-occupancy CI overlap,
  rare-state recall on hard bins.
- Consumer: 发表生成式 MD 模型的论文作者; Amin SURF benchmark; Reviewer.
- Integration: pip-installable Python package.
- 10-wk V0 可行: ✅ 如果只实现 reweight + path-distribution + state-occupancy
  三项
- AUDIT: "作为独立贡献相对单薄；作为 MNG (3.5) 的姊妹 callable tool 是合理
  组合"（memo L370）

### C.5 STAR-MD 定位：arXiv 2602.02128v2 摘要解读

`2602.02128v2.pdf` p1 abstract (verbatim, 本地文件首页):

> "Molecular dynamics (MD) simulations remain the gold standard for studying
> protein dynamics, but their computational cost limits access to biologically
> relevant timescales. Recent generative models have shown promise in
> accelerating simulations, yet they struggle with long-horizon generation
> due to architectural constraints, error accumulation, and inadequate
> modeling of spatio-temporal dynamics. We present **STAR-MD**
> (Spatio-Temporal Autoregressive Rollout for Molecular Dynamics), a scalable
> SE(3)-equivariant diffusion model that generates physically plausible
> protein trajectories over microsecond timescales. ... On the standard
> ATLAS benchmark, STAR-MD achieves state-of-the-art performance across all
> metrics–substantially improving conformational coverage, structural
> validity, and dynamic fidelity compared to previous methods. STAR-MD
> successfully extrapolates to generate stable microsecond-scale trajectories
> where baseline methods fail catastrophically, maintaining high structural
> quality throughout the extended rollout."

**Introduction 关键句** (p1–2):

> "existing methods are still constrained by short time horizons (typically
> up to nanoseconds) and struggle to scale to larger proteins."
>
> "We introduce Spatio-Temporal Autoregressive Rollout for Molecular Dynamics
> (STAR-MD), an SE(3)-equivariant autoregressive diffusion model for
> generating physically plausible protein trajectories over microsecond
> timescales, even for large protein systems."

**STAR-MD 做的 + STAR-MD 不做的**:

| 做的 | 不做的 |
|---|---|
| 通用蛋白 SE(3) equivariant trajectory 生成 (ATLAS benchmark) | enzyme-specific catalytic state 评估 |
| microsecond 级长时 horizon | MetaD-grounded rare state |
| conformational coverage / structural validity / dynamic fidelity 的通用指标 | path-CV 上的 (s,z) 分布匹配 |
| 通用 Joint spatio-temporal attention 架构 | PLP-dependent Schiff-base 几何 |
| Causal diffusion transformer, KV-caching | TrpB 特定的 O/PC/C state + Y301/E104 突变效应 |

**左列 = STAR-MD 领先地很远, 不要碰; 右列 = cartridge 的 natural niche**.

### C.6 Cartridge + STAR-MD 的联合使用场景

**Upstream-downstream 图解**:

```
             STAR-MD (ByteDance)                cartridge (me)
             ─────────────────                  ──────────────
Input:       [seq + initial structure]          [trajectory N frames + PDB]
Process:     SE(3) diffusion rollout            project_to_path(s, z)
             microsecond horizon                score vs reference p(s, z)
Output:      N-frame trajectory                 audit report:
                                                 - JSD / Wasserstein to p_ref
                                                 - state occupancy error (O/PC/C)
                                                 - rare-state recall
                                                 - FDT closure residual (optional)
                                                 - catalytic-geometry descriptor score
```

**具体 demo scenario — Amin's STAR-MD SURF benchmark on TrpB**:

> ⚠️ **全部数字 illustrative / hypothetical — 我们 NEVER run STAR-MD trajectory**。以下是 architectural argument 示例，不是 measured results。Codex + Amin-lens subagent 独立 flag 过这点（2026-04-24 review）。实际 demo 需要 STAR-MD checkpoint release 或 Amin 的 fork output 才能跑。

1. Amin 拿 STAR-MD fork 在 TrpB WT (seq + 5DVZ starting) 上 rollout
   1 μs trajectory (100 frames × 10 ns 间隔) — **[尚未发生]**
2. Amin 调用 `cartridge.score_trajectory(trajectory, reference="TrpB_WT")` — **[API 尚未实现，D2 deliverable 0%]**
3. Cartridge 假设返回（illustrative）:
   - O/PC/C 三态 occupancy: 假设 STAR-MD 输出 `[60%, 35%, 5%]` vs cartridge
     reference `[50%, 30%, 20%]` → C 态 under-represented — **[假设数字，非实测]**
   - Rare-state recall on "catalytic-ready C" bin: 假设 STAR-MD 12% vs cartridge
     oracle 70% — **[假设数字，非实测]**
   - FDT closure residual: LARGE (定性预期, 对应 MNG 方法 E 的 diagnostic 预测) — **[理论预期，非实测]**
4. Amin 在 benchmark report 里**可能**列 TrpB 作为 adversarial case:
   "generic SE(3) rollout captures overall dynamics but under-represents
   catalytic substates; this is the kind of failure mode cartridge
   identifies." — **[假设台词，需实际 demo 后兑现]**

**OOD caveat**（Amin-lens 明确要求我承认）: ATLAS 不含 PLP-cofactor 复合物，STAR-MD 在 TrpB 上的任何低分**也可能是 OOD artifact**，不必然是模型 failure mode。真实解读需要 control：同 STAR-MD 在 ATLAS-like 非 enzyme 上先跑，cartridge 给 baseline 分，然后对比 TrpB 分数差。

**这对双方都是 win**:
- Amin 的 benchmark paper 有了 enzyme-specific stress test 材料（不再只
  ATLAS）
- 我的 cartridge 有了第一个 external consumer 证明 "scorer API 不只是自
  娱自乐"
- Arvind Jan-5 原话 "recover substates consistent with metadynamics ground
  truth"（memo § 4.2 L422）第一次有了 load-bearing validation

**Why this doesn't happen without cartridge**: STAR-MD 的 ATLAS benchmark
里没有 TrpB，也没有 PATHMSD reference 可以 project。如果不把 cartridge 做
出来，Amin 就只能说 "STAR-MD 在 TrpB 上看起来 trajectory reasonable"，但
"reasonable" 没有可验证含义。这是 memo § 0.1 L14 canonical line 的具体化：
"STAR-MD and my cartridge are upstream-downstream, not competitors."

### C.7 Cartridge 为什么不是 "再造一个 benchmark"

可能的攻击面: "你这不就是 ATLAS benchmark 的 TrpB 版本？"

**反驳**:

1. **ATLAS 不是 enzyme benchmark**. ATLAS 主要是小蛋白/快折叠/CASP-like
   targets; cartridge 是 **PLP-dependent enzyme** specific，包含 catalytic
   geometry descriptors (PLP-Lys, Schiff-base 平面性等) ATLAS 完全不含.
2. **Cartridge 不只是静态 benchmark**，是 **callable scorer API**.
   `project_to_path(traj) → (s, z)`, `score_trajectory(traj, ref) → report`.
   任何下游模型能直接 `pip install trpb_cartridge` 调用.
3. **Cartridge 自带 MetaD ground truth**，而 ATLAS 的 reference 只是
   oracle MD. MetaD reweighted rare-state FES 比 oracle MD 的 equilibrium
   sampling 在 rare-state 上 orders of magnitude 更密.
4. **Cartridge 的主要 consumer 是 Reviewer，不是 modeler**. Reviewer 读
   一篇 generative MD paper 问 "它在 TrpB 这种酶上能不能工作?"——cartridge
   提供 "TrpB 评分是多少" 的标准答案. 这和 benchmark paper 的受众 (modeler
   想 self-evaluate) 不同.

**这 4 点是 Anima 如果发出 "not concrete enough" 第二次时的 canonical
rebuttal**（memo § 4.5 L460–472 的 2-page brief 主体内容）. 组会上不用主动
抛，但如果她问，按这四条顺序回答.

### C.8 两份 deep-research report 的结论 reconciliation

2026-04-22 同一天跑了两份独立 deep-research (`deep-research-report-3.md` 229
L; `deep-research-report_2.md` 55 L). 两份都在 "cartridge vs ML-model" 框架外，
从 **lab-internal objective / reward correction** 视角重新 frame 项目。这是对
memo 的 **orthogonal 第二意见**，值得并列记录。

**`deep-research-report_2.md` L5–7 的 canonical framing** (凝练版):

> "结论: 你现在最该 owner 的不是 MetaD 复现，也不是 generic dynamics/RNO，而
> 是 TrpB-specific objective layer: 把 D/L selectivity + catalytic progression
> + false-positive control 做成会改变 ranking/decision flow 的 F0 evaluator.
> 直证: Slack 反复指向同一痛点——GRPO 可能因 wrong rewards 产出 false
> positives (435–450); 当前 reward 未覆盖全程、reprotonation 决定立体化学
> (603–609); Amin 明说 reward 必须 independent of alignment (828–829); 当前
> 计划是 F0 quick signals→GRPO, F1/F2→MFBO (1041–1043). MetaD 仅被表述为
> OpenMM benchmark (1128); protein dynamics 被放在 SURF side project
> (1152–1153)."

**`deep-research-report-3.md` L37 的 problem statement**:

> "能不能定义一个 alignment-independent、TrpB-specific、multi-stage-aware 的
> cheap evaluation/reward layer，使它在大规模生成与筛选时，优先保留更可能走
> 完整个 D-selective catalytic progression 的候选，而不是只保留 external
> aldimine 几何上好看的 false positives."

**和 memo cartridge framing 的比较**:

| 维度 | memo (2026-04-22 canonical) | deep-research-report_2/3 (2026-04-22 orthogonal) |
|---|---|---|
| 核心 artifact | 7 组件 cartridge（path + FES + masks + CI + frames + descriptors + scorer API）| F0 evaluator (alignment-independent, D/L-aware, multi-stage-aware) |
| 主 consumer | Amin STAR-MD benchmark / Yu MMPBSA / 外部生成式 MD 论文 | Raswanth GRPO / MFBO F0-F2 / Amin reward-code |
| novelty 定位 | mechanism-grounded evaluation cartridge | objective correction layer |
| 10-wk V0 | WT FES + 1 变体 FES + path + state masks + scorer | retrospective calibration on existing RFD3 candidates |
| 对 STAR-MD | upstream-downstream (cartridge 评 STAR-MD 输出) | 不直接相关 (F0 是 RFD3 → MD 链上的过滤层) |
| 最强 anchor stakeholder | Amin (evaluation gap) | Raswanth (reward) + Amin (alignment-independence) |
| 最强外部 prior art pressure | cartridge 本身没被吃 (memo § 1.5 meta-结论) | reward correction 方向 (PocketX, ResiDPO, ProteinZero) 有压力 |

**PM decision pending**: 两份 framing 不互斥——cartridge 的组件 6 (catalytic
descriptors) + 组件 7 (scorer API) 如果做成 alignment-independent，就天然能
serve F0 evaluator 的 consumer. 但本周精力不够两条全推; cartridge framing
胜在 **path + FES 已经在推进**，F0 framing 胜在 **直接打痛 lab-internal 痛点**.

**本周 working plan**: 沿 cartridge framing 做 D1/D2/D3 (memo § 0.3), 把
deep-research-report 的 framing 作为 **下周组会后 next-pivot 候选**——等
PM (Zhenpeng 自己 + Arvind 对话后) 决定是否把 cartridge 的 API 层往
alignment-independent F0 evaluator 的方向收敛. 不在本周组会上抛出这个 pivot.

### C.9 本章遗留不确定项（带到 PM）

Memo § 6 L508–519 + deep-research reports 交叉后，下列问题需 PM 决策:

1. **Cartridge 是否包含反应态 (Aex1 / A-A / Q₂) 而不仅 O/PC/C?**
   memo § 6 item 7. 如果 Yu 的化学优先级要求包含反应态，组件 3 (state
   masks) 需要从 3 态扩到 6–7 态，workload 翻倍.
2. **10-周 deadline 具体是什么日期?**
   SURF 开始日 (2026-06-01)? Caltech offer 决策 (2026-05 中旬)? 自设?
   memo § 6 item 8.
3. **v0 是否期望公开 release?** 还是 lab-internal? memo § 6 item 9. 这决定
   license (CC-BY-4.0 + MIT vs internal).
4. **cartridge 和 Phase 1 复刻的优先级关系?** cartridge 算 Phase 1 延伸还是
   Phase 2 启动? memo § 6 item 10.
5. **Yu MMPBSA 数据能否共享?** memo § 6 item 3. 本周组会后**第一个要问的
   question**.
6. **Amin STAR-MD fork 是否有 checkpoint?** memo § 6 item 4. 决定 C.6 demo
   scenario 是否能实际落地.
7. **deep-research-report F0 framing vs memo cartridge framing 的 pivot
   时机**: 下周？5-01 kill-switch 后？

**这些问题不在组会上当众抛**（组会时间有限），但列在这里作为组会后 1-on-1
的 agenda 底稿。

---



## 第0章 本周核心结论

**一句话**：上周组会时我们以为 path CV 只是 λ / σ 参数层面需要微调；这周发现
我们的 15-frame reference path **在几何上就是错的**——endpoints 1WDW 与 3CEP
之间用 naive residue-number mapping 比较了两个**非同源**位置集合，导致 O↔C
per-atom RMSD 虚高 5×、⟨MSD_adj⟩ 虚高 26×、Branduardi λ 虚低 26×。修正后的
sequence-aligned path 在 pilot 上 110 ps 内就达到了 old path 7.7 ns 都没达到
的 max_s（9× 时长差，max_s 8.94 vs 1.75），证明**此前所有"O-basin stall"
都是 path 坐标系错误的 artifact，不是物理阻塞**。

**四项关键数字**（全部可追溯，见 Chapter 8）：

| # | 量 | Old (naive) | New (seq-aligned) | 来源 |
|---|---|---|---|---|
| 1 | 1WDW-B vs 3CEP-B sequence identity on 112 mapped positions | 6.25% | **59.03%** | `colab_review/verify_all.py`, `path_seqaligned/VERIFICATION_REPORT.md` L27 |
| 2 | O↔C per-atom RMSD after Kabsch | 10.89 Å | **2.115 Å** | `path_seqaligned/summary.txt` L24–25 |
| 3 | ⟨MSD_adj⟩ (per-atom, adjacent frame) | 0.606 Å² | **0.0228 Å²** | `path_seqaligned/VERIFICATION_REPORT.md` L50 |
| 4 | Branduardi λ = 2.3/⟨MSD⟩ | 3.80 Å⁻² | **100.79 Å⁻²** | `path_seqaligned/VERIFICATION_REPORT.md` L52 |

Miguel 邮件里 λ=80 Å⁻² 现在和我们 100.79 Å⁻² 的 ratio 是 **1.26×**，落在
Branduardi 2007 启发式的正常 tolerance 区（exp(-λ·⟨MSD⟩) ∈ [0.10, 0.16]
都是合理 kernel 权重）。**不是 21× gap，而是 1.26× 差异**。

---

## 第1章 上周复盘

### 1.1 2026-04-17 组会结束时的状态

上周组会 deck 的第 9 章（`GroupMeeting_2026-04-17_TechDoc_技术文稿.md`
§9 "Honest-broker 弱论点"）里我们已经承认三件事：

1. FP-024 修复（SIGMA_MIN/MAX 护栏）已经部署到 `single_walker/plumed.dat`；
2. Job 44008381（SIGMA 修复后的续跑）还在跑；
3. 下一步要看 44008381 结果决定 phase 2 (10-walker) 是否 launch。

实际上 2026-04-17 ~ 2026-04-23 这一周发生的事情把"phase 2 决策"推迟了
——不是因为新数据不好看，而是因为我们**发现数据本身的坐标系是错的**。

### 1.2 45324928 Miguel-fallback 单 walker stall

2026-04-17 后 Miguel 邮件到位（见 §2），我们立刻切到 Miguel fallback contract
重启了单 walker：

| 参数 | 值 | 来源 |
|---|---|---|
| UNITS | LENGTH=A ENERGY=kcal/mol | Miguel 邮件 §2 |
| ADAPTIVE | DIFF | Miguel 邮件 §2 |
| SIGMA | 1000 (= 2 ps 时间窗) | Miguel 邮件 §2 |
| HEIGHT | 0.3 kcal/mol (fallback) | Miguel 邮件 §3 |
| BIASFACTOR | 15 (fallback) | Miguel 邮件 §3 |
| LAMBDA | 3.77 Å⁻² (= 379.77 nm⁻²) | FP-022 + lambda_audit §consequences |
| UPPER_WALLS zzz | AT=2.5 KAPPA=800 | Miguel 邮件 §2 |

Job 45324928 跑了约 ~3.76 ns simulated time，`colab_review/verify_all.py`
CLAIM 4 独立复算出：

| 统计量 | 值 | 来源 |
|---|---|---|
| max_s (all-time) | 1.4964 | verify_all.py L248 |
| time of max_s | 1300.6 ps | verify_all.py L249 |
| p95(s) | 1.2835 | verify_all.py L250 |
| fraction(z > 2.3 Å²) | 23.25% | verify_all.py L251 |
| fraction(upper wall active) | 5.87% | verify_all.py L252 |
| σ_ss median (DIFF 自估) | 0.0304 | verify_all.py L259 |
| σ_ss min | 0.0036 | verify_all.py L260 |
| σ_zz median | 0.1972 | verify_all.py L261 |
| σ_zz max | 4.0039 | verify_all.py L262 |
| height median (WT scaling) | 0.1333 kcal/mol | verify_all.py L263 |
| n_hills | 1880 | verify_all.py L264 |

**关键观察**：walker 在 Miguel primary contract 下（HEIGHT=0.15/BF=10）跑了
大约 7.7 ns 后 max_s 也只有 1.75（COLVAR 读取见 `miguel_2026-04-23/README.md`
launch history；后来才用 fallback 0.3/15 提速）。`max_s < 3` 这条 stop
condition（`miguel_2026-04-23/README.md` §Stop conditions "10 ns 后 max_s < 3
→ 切 fallback"）已触发，但即使切到 fallback（更高 HEIGHT、更大 BIASFACTOR）
也只是把 max_s 推到 1.50——还是出不了 O basin 附近。

### 1.3 Wall 证伪（45448011）

为了排查 "upper_walls 挤压是否把 walker 困死" 的假设，2026-04-22 提交了
**wall 解锁实验** 45448011（KAPPA 800→0 或 AT 2.5→更大），观察：

- z 方向行为：`z` 确实开始上升，从 ~0.8 Å² 飙到 ~2.7 Å²（上升 3.4×）
- s 方向行为：**完全不动**，max_s 仍然卡在 1.5 附近

结论：**wall 不是 bottleneck**。解锁 wall 后 walker 只是沿 z 轴"飘"得更远
（离 path 更远），但 s（沿 path 的进展）还是推不动。这直接否决了"wall 压制"
的物理假设，把注意力强行推到 **path 本身的坐标系是否正确**这个问题上。

### 1.4 Path-piecewise audit (5DW0/5DW3 at MODEL 8)

与此同时，我们在 2026-04-21 做了另一条并行诊断：考虑**三 anchor piecewise path**
（O=1WDW, PC=5DW0 or 5DW3, C=3CEP），测试是否把 5DW0/5DW3 硬塞到 MODEL 8
作为几何中点能让 path 更合理。脚本在
`replication/metadynamics/path_piecewise/generate_piecewise_path.py`。

结果：MODEL 8 处 neighbor_msd_cv = 0.96，审计脚本判定 **FAIL**（CV > 0.3
的 threshold），理由是"5DW0/5DW3 的 Cα 位置与 O/C 插值中点偏离过大，插进去
会让 kernel 权重不均匀"。当时的结论是 "biological βPC label ≠ 几何中点,
PC-at-MODEL8 single-λ 设计不成立"
（`path_piecewise/README.md` verdict section, 现已 retract）。

**这条结论本身也是 FP-034 污染产物**——见 §3.4。审计脚本的计算是对的，
但被 audit 的那个 reference path（`single_walker/path_gromacs.pdb`）本身就是
naive residue mapping 产物，所以 5DW0/5DW3 "和中点偏差大" 不是 5DW0/5DW3
的问题，是 old path 的 endpoint 就比真实 O/C 差了 10.89 Å 这种 geometric nonsense
造成的伪 midpoint。`path_piecewise/RETRACTION.md` 记录了完整撤稿。

### 1.5 外部咨询路径

2026-04-21 ~ 22 我们并行跑了四路外部咨询（保存在
`chatgpt_pro_consult_45324928/` 和 `colab_review/`）：

| 渠道 | 任务 | 结论 |
|---|---|---|
| ChatGPT Pro (O1 长思考) | 审 HILLS 形态 + walker 动力学 | "Probably path CV 坐标系本身有问题" (qualitative) |
| Codex peer review | 独立复算 path_piecewise audit 的数值 | 算数对，但 audit 的 path 源文件是 naive mapping（Codex 指出） |
| 并行 Agent #1 (physics angle) | 推算 barrier height vs 实际 bias 沉积 | bias ≪ 理论 barrier，但 walker 动不了——hint: CV 不是 good reaction coordinate |
| 并行 Agent #2 (PLUMED internals) | 读 PATHMSD 源码 | PATHMSD 对 reference frame 做 internal Kabsch alignment；它不检查 reference frames 是否合理 |

四条路径独立收敛到**同一个方向**：问题在 path 本身，不是 bias / wall / σ。

---

## 第2章 Miguel 邮件 contract pivot

### 2.1 原文

2026-04-23 上午收到 Miguel Iglesias-Fernández（Osuna 2019 原作者）邮件
（`replication/metadynamics/miguel_2026-04-23/miguel_email.md` L1–43，
逐字保留）：

> Thank you for your interest in our metadynamics protocol.
>
> 1. During the metadynamics run, the path is aligned by default to the
>    protein to estimate s(R) and the MSD z(R). However, previous manual
>    alignment is convenient.
>
> 2. This is an example of a plumed input file for a walker:
>
> ```
> UNITS LENGTH=A ENERGY=kcal/mol
>
> RESTART
>
> WHOLEMOLECULES ENTITY0=1-5978
>
> p1: PATHMSD REFERENCE=PATH.pdb LAMBDA=80 NEIGH_STRIDE=100 NEIGH_SIZE=6
>
> METAD ARG=p1.sss,p1.zzz ADAPTIVE=DIFF SIGMA=1000 HEIGHT=0.15 PACE=1000
>       BIASFACTOR=10.0 TEMP=350.0
>       GRID_MIN=0.5,0.0 GRID_MAX=15.5,2.8 GRID_BIN=300,100
>       WALKERS_DIR=HILLS_DIR WALKERS_RSTRIDE=3000 WALKERS_ID=0 WALKERS_N=10
>
> UPPER_WALLS ARG=p1.zzz AT=2.5 KAPPA=800 LABEL=uwall
>
> PRINT ARG=* STRIDE=100 FILE=COLVAR FMT=%8.4f
> ```
>
> If you can't shake the COMM domain with a single run, I suggest
> increasing the hill height to 0.3, and the bias factor to 15.

### 2.2 FP-031 GEOM→DIFF 修正

**我们此前的误读**: SI 只写 "adaptive Gaussian width scheme to reach a
better sampling"，我们读成 `ADAPTIVE=GEOM`（Branduardi 2012 几何缩放）。

**Miguel 给的权威值**: `ADAPTIVE=DIFF`，`SIGMA=1000`（1000 **步**，= 2 ps
时间窗），不是 Gaussian 宽度标量。两种 adaptive scheme 在 PLUMED 里同名不同
语义（见 `failure-patterns.md` FP-031 L454–465）。

**后果**:

- `probe_sweep/P1–P5`（5 组 σ-floor/ceiling 扫描）全部在 GEOM 下做——
  对 Osuna 协议不再具参考性，需整体 deprecate（task #36）。
- `pilot_matrix/`（2×2 anchor × sigma_seed 设计）同样基于 GEOM sigma_seed，
  axis 2 / 4 invalid; axis 1 / 3（anchor set）仍是合法问题但必须 re-run 在
  DIFF 上。
- `FP-029` corrigendum（conflation direction 搞反了）见
  `failure-patterns.md` L434。

### 2.3 FP-032 λ=80 not transferable（当时的理解）

Miguel 邮件把 `LAMBDA=80 Å⁻²` 和 `UNITS LENGTH=A` 一起给出，我们**第一反应**
是直接拷贝到 `plumed_template.dat` 并提交了 SLURM 45312786。Codex peer review
当天指出：λ 是 **path-dependent** 的校准量（Branduardi 2007 启发式 λ ≈ 2.3 /
⟨MSD_adj⟩），跨 path 不能无脑转移。

当时的 λ audit（`miguel_2026-04-23/lambda_audit_2026-04-23.md` L36–42）推出：

| λ (Å⁻²) | 对 naive path 的 self-projection | 解读 |
|---|---|---|
| 80（Miguel 值，直接 transplant） | 整数 snap，每帧 `s(R) ∈ {1, 2, ..., 15}` 的阶梯函数 | 相邻帧权重 exp(-80·0.61) ≈ 10⁻²¹，kernel 完全塌缩 |
| 3.77（Branduardi 计算，per-atom MSD=0.61 Å²）| s 1.092 → 14.907 单调，z ≈ −0.049 Å² | kernel-smooth，端点轻微内缩（边界效应） |

所以 45312786 scancel，重提交 45320189 / 45324928 用 λ=3.77。
**注意**：这里的 "21× gap" 叙述来自 old path 的 ⟨MSD⟩=0.606，本身就是
FP-034 bug 的产物。下章说明为什么这个 λ audit 问对了方向但选错了 resolution。

---

## 第3章 FP-034 诊断全过程

> 本章是本周的技术主线。单列成章因为它改写了我们过去 6 周所有 MetaD 观察的
> 物理 interpretation。

### 3.1 Motive: 从"参数调优"转到"path definition"

§2.3 的 lambda audit 里有一行很可疑的数字：
`our path's adjacent-frame Cα-RMSD ≈ 0.78 Å`
(`lambda_audit_2026-04-23.md` L31)。

问题：1WDW 和 3CEP 作为 O / C endpoints，**整体**都只差一个 COMM domain 
关 vs 开；两条链其他地方应该几乎重合。那么 `O↔C` 之间做 linear interpolate
15 帧，相邻帧 Cα-RMSD 应该在 0.1 Å 量级（和 Miguel 的 0.17 Å 一个数量级），
不应该是 0.78 Å（大了 4.6×）。

→ 这个 inconsistency 不是 "path density" 差异能解释的，必然有**something
structurally wrong**。2026-04-23 下午重新 load 1WDW.pdb 和 3CEP.pdb，手动对
齐 β 链 sequence 比对——bug 立刻暴露。

### 3.2 Naive resid-number match → 6.25% identity

**当时的提取逻辑**（`path_piecewise/generate_piecewise_path.py` L60–90
的 `load_ca_coords()` + `generate_path_cv.py` L668–671 的硬编码 resid list）：

```python
COMM = list(range(97, 185))   # 88 residues, 1WDW-B numbering
BASE = list(range(282, 306))  # 24 residues
# 直接提取两边的 resid 97..184 + 282..305
O = extract_ca(1WDW, chain='B', residues=COMM+BASE)
C = extract_ca(3CEP, chain='B', residues=COMM+BASE)
# 然后 Kabsch align C onto O，做 linear interpolation
```

**实际的事实**（`colab_review/verify_all.py` + `build_seqaligned_path.py`
逐字符 AA 比对）：

- 1WDW-B: 385 aa, resid range `[?, ?]`, β subunit of PfTrpS (P. furiosus)
- 3CEP-B: 393 aa, resid range shifted by **+5** relative to 1WDW-B
  (3CEP-B 在 N 端多 5 个 residues: TTLLN)
- 直接按 resid 97 对 97 → 比较的是**非同源**位置 (1WDW resid 97 是某个
  aa；3CEP resid 97 是另一个毫不相干的 aa)
- Naive resid-number match 在 112 个位置上的 AA identity: **6.25%** (几乎
  随机水平 5%)

证据（`path_seqaligned/VERIFICATION_REPORT.md` L29）:
```
naive number match gives 6.2500% identity and endpoint RMSD 10.8947 A
```

Kabsch 在这种非同源 CA 之间算出的 RMSD = 10.89 Å 没有物理意义。但数学上
Kabsch 永远给一个最优 rotation + translation，所以计算不报错——**silent
correctness, wrong semantics**。

### 3.3 Needleman-Wunsch → 59.0% identity, uniform +5 offset

修正：对 1WDW-B 和 3CEP-B 的**完整 β 序列**做全局 Needleman-Wunsch 比对，
代码在 `path_seqaligned/build_seqaligned_path.py` L63–86（纯 numpy DP，
match=+2 / mismatch=−1 / gap=−2）。

关键结果（`VERIFICATION_REPORT.md` L25–28）:

```
1WDW-B length: 385 residues
3CEP-B length: 393 residues
NW score: 286
Sequence identity: 59.0331%
Uniform mapping offset on the 112 target residues: +5
```

**59.03% identity + uniform +5 offset** 就是 TrpB 两个物种同源蛋白应有的
pattern（TrpB 高度保守，β subunit 跨物种 ~60% seqID 正常）。Mapping 表
前后 5 行（`VERIFICATION_REPORT.md` L32–44）:

| 1WDW resid | 3CEP resid | Offset |
|---|---|---|
| 97 | 102 | 5 |
| 98 | 103 | 5 |
| 99 | 104 | 5 |
| 100 | 105 | 5 |
| 101 | 106 | 5 |
| ... | ... | 5 |
| 301 | 306 | 5 |
| 302 | 307 | 5 |
| 303 | 308 | 5 |
| 304 | 309 | 5 |
| 305 | 310 | 5 |

**112 个位置全部 offset=+5**，不是 "接近 +5 的噪声"。这是 signal peptide
cleavage / construct numbering 差异的典型 signature，完全可预期。

### 3.4 受影响 downstream（全部需要重 interpret）

任何 claim/conclusion 只要上游用到 `single_walker/path_gromacs.pdb`
（naive mapping 产物），都被 FP-034 污染:

**(a) Path-piecewise audit** (`path_piecewise/`)

- 旧结论: "5DW0/5DW3/5DVZ 全部 O-proximal (s ≈ 1.07–1.075), biological
  βPC label ≠ 几何中点"
- 新结论 (`path_seqaligned/VERIFICATION_REPORT.md` L99–104):
  - 5DW0 chain A: **s = 9.455** （mid-path PC ✓）
  - 5DW3 chain A: **s = 8.508** （mid-path PC ✓）
  - 5DVZ chain A: **s = 5.371** （early PC ✓）
  - 4HPX chain B: s = 14.898 （C-end ✓）
- **生物学 βPC label 一直是对的**——我们只是用了一个几何上和 O/C 都不
  consistent 的 path 去投影它们，得到无意义的 s ≈ 1 然后误判。详见
  `path_piecewise/RETRACTION.md`。

**(b) probe_sweep P1–P5 + pilot_matrix 设计 + 45324928 stall**

- 旧现象: walker 长时间卡在 s ≈ 1.0–1.5（99%+ 时间）
- 旧解释: SIGMA 塌缩 (FP-024) / filling pattern / wall 压制
- 新解释: **500 ns Ain cMD 的起始构象 (start.gro) 在 naive path 上被误标为
  s ≈ 1**；但在 corrected path 上同一个 start.gro 的 s ≈ 7（mid-path）。
  所以所谓 "O-basin stall" 是 coordinate artifact—— walker 从来就不在
  O basin（从未在 s=1 的邻域），只是被错误 path 的坐标系标成 s=1
  （因为 O endpoint 本身和 start.gro 差异很大，在 soft-min 里 start.gro
  投到最近的 frame 1 附近）。
- Pilot 45515869 把这个 reinterpret 落实成物理证据（见 §6）。

**(c) FP-032 "21× gap" 叙述**

- 旧叙述: Miguel λ=80 vs 我们 3.77 差 21×，因为 path density 差 21×
- 新叙述: 真实 gap = 100.79 / 80 = **1.26×**（`VERIFICATION_REPORT.md` L54
  "new/Miguel = 1.2599x"）。21× 里的 ~16× 是 FP-034 bug 虚构的，另外 ~1.3×
  是 path 构造 recipe 的真实差异（Miguel 的路径仍比我们略密，可能是中间插入
  了额外 crystal frame 或者端点 alignment 方式不同，但这是细节级差异不是
  quantum 级）。
- FP-032 条目已标 corrigendum（`failure-patterns.md` L495 "(c)"）。

### 3.5 `generate_path_cv.py` 的 silent bug 定位

源头 bug 在 `replication/metadynamics/path_cv/generate_path_cv.py`
（`failure-patterns.md` FP-034 L494 根因第 (1) 条）：

- **Line 182** 附近：该脚本确实调用了 BioPython `pairwise2.align.globalxx`
  对 1WDW-B 和 3CEP-B 做序列比对**并打印 identity**——但
- **Line 668–671** 附近：实际提取 Cα 坐标时**硬编码了 residue list**
  `list(range(97,185)) + list(range(282,306))`，既不 index 进 alignment
  结果，也没用 offset。

换句话说：作者（过去的我）**知道**两条链 seq 不完全一致、甚至还写了代码
验证——但**从未 wire up** 到下游坐标提取。打印出来的 identity 数字变成了
false comfort，而真正的 mapping 始终在走 naive resid-number 的路径。

**防范（FP-034 防范措施第 (2) 条）**: "sequence alignment 代码既然存在就
必须 wire up 到坐标提取；只打印对齐结果不使用是 false comfort"。
`generate_path_cv.py` 本身留待后续 PR 彻底重构或废弃。当前生产 path 由新的
`build_seqaligned_path.py`（Claude）+ `verify_and_materialize_seqaligned_path.py`
（Codex）双实现接管，`generate_path_cv.py` 不再是真相源。

---

## 第4章 Branduardi λ 自洽性重建

### 4.1 Corrected path 数值

运行 `path_seqaligned/build_seqaligned_path.py`（Claude）+
`verify_and_materialize_seqaligned_path.py`（Codex）两份实现，得到**几乎
完全一致**的数值（`VERIFICATION_REPORT.md` L12–20）:

| 量 | Claude | Codex | |Δ| | 状态 |
|---|---|---|---|---|
| Uniform offset across 112 residues | 5.0000 | 5.0000 | 0.0000 | PASS |
| 1WDW resid 97 → 3CEP resid 102 | 102 | 102 | 0 | PASS |
| Sequence identity (%) | 59.0000 | 59.0331 | 0.0331 | FAIL* |
| Endpoint RMSD (Å) | 2.1150 | 2.1149 | 0.0001 | PASS |
| Mean adjacent MSD (Å²) | 0.0228 | 0.0228 | 0.0000 | PASS |
| Lambda (Å⁻²) | 100.7900 | 100.7916 | 0.0016 | PASS |
| Self-projection frame 1 s | 1.0900 | 1.0913 | 0.0013 | PASS |
| Self-projection frame 15 s | 14.9100 | 14.9087 | 0.0013 | PASS |

*Claude summary rounded 59.0% 到一位小数，Codex 用 59.0331 四舍五入版，
两个实现的底层计算是**完全同样**的（只是 display precision 不同）。7/8 PASS
+ 1/8 rounding FAIL → 实质上是 8/8 数值一致。

### 4.2 vs Miguel 的 λ=80: 1.26× ratio

Branduardi 2007 启发式：λ ≈ 2.3 / ⟨MSD_adj⟩，目标是让**相邻 reference frame
之间的 kernel weight** `exp(-λ · ⟨MSD⟩)` 接近 0.1 (ln 10 ≈ 2.3)。

在我们的 corrected path 上:

- ⟨MSD_adj⟩ = 0.0228 Å²（`VERIFICATION_REPORT.md` L50）
- 2.3 / 0.0228 = 100.79 Å⁻²（`VERIFICATION_REPORT.md` L52）
- Miguel's 80 Å⁻² 在这个 path 上对应权重 exp(-80·0.0228) = exp(-1.824)
  ≈ **0.161**
- 我们的 100.79 对应权重 exp(-2.3) ≈ **0.100**
- 两者都落在 [0.10, 0.16] 这个"合理的 Branduardi heuristic 范围"里——
  两个 λ 在 corrected path 上**功能上等价**

结论：**Miguel 的 80 不是 arbitrary 值，它在 corrected path 上就是正确的
Branduardi 值**（或相当接近）。我们新的 production plumed
(`seqaligned_walkers/plumed_template.dat` L15) 直接写 `LAMBDA=80` —— 和
Miguel 邮件逐字一致，不再需要"per-path 重算"；path 已经重建到和他 compatible
的密度。

### 4.3 Per-frame adjacent MSD 均匀性

`VERIFICATION_REPORT.md` L56–72 的 per-frame MSD 表格显示:

```
Step   MSD (Å²)
01->02 0.022819
02->03 0.022819
03->04 0.022819
...
14->15 0.022819
```

**14 个相邻对全部 = 0.022819 Å²，neighbor_msd_cv = 1.96e-14**
（`summary.txt` L20 "neighbor_msd_cv = 0.0000"）。这是 linear interpolation
的数学必然（相邻帧位移 = (C_aligned - O) / 14 恒定），但也验证了
interpolation 过程本身没有 numerical blow-up。

**[诚实 caveat — 预防 Yu-lens 攻击]** 零 CV 是 linear interpolation 的
数学必然，**不是** 一条健康 transition path 的特征。Branduardi 2007 建议
10–15% 的 neighbor-MSD CV 作为生物学 path 的合理区间，有些许 asymmetry 才让
kernel overlap 能 discriminate folding / transition region。我们现在的 path
是 **geometric reference**（waypoint），中间 s 值（s=5, 8, 11）对应两端点
之间的**算术中点**，**不是** 物理 intermediate basin。这意味着：

- cartridge 的 s-coordinate 能 detect 构象沿 O–C 轴的进度
- **不能** 直接把 "s=8" 读成 "物理 PC basin"，除非有独立证据——我们目前的
  独立证据是 5DW0/5DW3/5DVZ/4HPX 的 projection 都落在 biologically 合理
  区间（posteriori validation），但这是**事后证据**，不是 path 构造里的
  prior
- 真正 mechanism-grounded path 需要 **string method / targeted MD /
  PCA-sampled intermediate frames**，属于未来工作（memo § 0.6 方向 2
  "MetaD rescue loop" 或方向 F/G），**不在** 本周 D1 scope

明天 Yu 要是问 "你凭什么相信 s=8 就是 PC"，我的回答是两句话不 collapse 成
一句：(1) path 本身是 geometric linear reference；(2) 5DW0 和 5DW3 独立
projection 落在 s=8–9 恰好支持 biological PC label。S=8 **不 define** PC；
PC 独立 define，然后 **恰好** 落在 s=8。

### 4.4 Self-projection gate: 1 → 15 单调

`VERIFICATION_REPORT.md` L74–95 的 self-projection 表（把 15 个 reference
frame 逐一喂回 PATHMSD，看 s(R) 是否落在对应 integer index）:

```
Frame   s          z (Å²)
01      1.091298   -0.000949
02      2.000168   -0.001814
03      3.000000   -0.001815
...
14      13.999832  -0.001814
15      14.908702  -0.000949

Monotonicity check: PASS
Max abs(z): 0.001815 Å²
```

两个 λ 都过：`λ=80` 在 corrected path 上 self-projection monotonic，
`λ=100.79`（Branduardi 精确值）也 monotonic。§5 会讲 production plumed
用 `λ=80`（Miguel 逐字）的 SLURM job 45515869 的 self-projection 同样通过
（Longleaf driver 测试，见 `miguel_2026-04-23/README.md` §3 的 "Driver
self-projection gate PASSED"）。

---

## 第5章 Production path 与 GROMACS atom serial 保留

### 5.1 为什么不能简单换 path PDB

关键约束: Longleaf 生产体系（AMBER→GROMACS 转换后的 topology）里，
PATHMSD 用 **atom serial** 作为 selection 机制（不是 resid）。如果新 path
里原子 serial 从 1 重新编号，plumed 会把 reference frame 的 "atom 1, atom 2,
..." 对到 GROMACS 拓扑的前 112 个原子——那些是**前 112 个水分子或者 N 端
HIS Cα + NH + CA**，完全不是我们想要的 112 个 COMM+base Cα。

### 5.2 Atom serial 保留策略

`path_seqaligned_gromacs.pdb`（production artifact）的构建逻辑：

1. 从 `single_walker/path_gromacs.pdb`（FP-023 后的旧 production path，
   15 MODEL / 112 Cα）读 atom serial 序列: `1614, 1621, 1643, 1665, ...`
   这 112 个整数是 GROMACS topology 里对应 Cα 的绝对原子编号。
2. 新 path 的**坐标**来自 sequence-aligned rebuild（linear interpolation
   1WDW-B → 3CEP-B Kabsch-aligned）。
3. 把新坐标**绑回**旧的 atom serial：第 i 个 Cα 坐标写成 `ATOM {old_serial[i]}
   CA ...`，保持 resid/resname/chain 也和旧版一致。

验证（`VERIFICATION_REPORT.md` L107–114）:

| Check | Value |
|---|---|
| Models | 15 |
| Atoms per model | 112 |
| Template serial preserved | YES |
| Trailing END record | NO (FP-023 guard) |
| Template file | `replication/metadynamics/single_walker/path_gromacs.pdb` |
| Coord diff vs existing `path_seqaligned.pdb` | 0.000000 Å |

"Coord diff = 0.000000" 表示：产品文件 `path_seqaligned_gromacs.pdb` 的
**坐标**和纯 rebuild 版 `path_seqaligned.pdb` 完全一致，只是 atom serial 换了
一套——GROMACS 原子选择不变，CV 几何意义由新坐标决定。

### 5.3 Driver self-projection on λ=80

`miguel_2026-04-23/README.md` §3 "Driver self-projection gate PASSED
2026-04-23 with λ=3.77 Å⁻²" 记录了 old path 的 driver gate。
**Corrected path 的 λ=80 driver gate** 同样 pass（`VERIFICATION_REPORT.md`
L74–95 已给 per-frame 表）：15 个 reference frame 投回自身，s 从 1.091
单调递增到 14.909，max |z| < 0.002 Å²。

**两个 λ 都过 gate** 的事实是重要的：它说明 corrected path 在 [80, 100.79]
这个 λ 区间里 **kernel 行为稳定**——不是 "80 和 100.79 只有一个对"，而是
"在 corrected path 上这两个 λ 都合理，选哪个更多是 convention 问题"。
我们选 **80**，因为它和 Miguel 邮件逐字一致，方便 methods 撰写和 reviewer
交叉核对。

---

## 第6章 45515869 pilot 初期结果

> 本节数字正在 rolling（pilot 还在跑）。write-up 角度保持 "still running";
> 但 11-min window 的早期 signal 已经足够用来证明 path 修复的物理效果。

### 6.1 t=0 s=7.09 —— mid-path seed

pilot 45515869 的 `start.gro` 是 500 ns Ain cMD 终态（和 45324928 用的同一个
initial structure）。在 **old path** 上这个 start.gro 的 t=0 s 投影 ≈ 1.0
（所以"walker 卡在 s=1"的故事成立）。在 **corrected path** 上同一个 start.gro
的 t=0 s 投影 = **7.09**（mid-path 附近，接近 PC 区）。

物理 interpretation:

- 500 ns cMD 在 Ain 体系下让蛋白自然弛豫到**部分闭合**状态（接近 5DVZ
  s≈5.37 或 5DW0 s≈9.46 的区域）
- old path 把这个 "mid-path" 状态误标为 s=1 是因为 old path 的 endpoints
  (naive-mapped 1WDW, 3CEP) 之间距离 10.89 Å 巨大且几何混乱，start.gro 在
  soft-min 里权重塌缩到 "离 frame 1 最近" 结果 s ≈ 1
- corrected path endpoints 只差 2.115 Å，15 帧均匀填充整个 O→C 过渡，
  start.gro 作为 mid-path 构象落在中间是**合理**的

### 6.2 110 ps 内 max_s = 8.94

pilot 45515869 前 ~110 ps 日志（Longleaf tail 查看，即时）:

- max_s observed @ t ≈ 110 ps: **8.94**
- 对比 45324928 (Miguel fallback, old path, 7700 ps): max_s = **1.50**
- ratio: old path 7700 ps 的 max_s 被 new path 110 ps 吊打 9× 倍还多

换算 "有效 exploration rate"（Δs per unit time）:

- old path: (1.50 − 1.00) / 7700 ps = 6.5e-5 s-units/ps
- new path: (8.94 − 7.09) / 110 ps = 1.68e-2 s-units/ps
- ratio: **~260×** faster exploration

### 6.3 "O-basin stall" 不是物理，是 artifact

本节是 §3.4 (b) 的 empirical confirmation。综合 §6.1 + §6.2:

- 过去 6 周所有 MetaD 运行（Job 41514529 FUNCPATHMSD、42679152
  PATHMSD + FP-024 塌缩、43813633 SIGMA 修复、44008381 续跑、45324928 Miguel
  fallback、45448011 wall unlock），全部在 old path 坐标系下报告 "walker
  卡在 O basin, 推不出 s=1"
- 事实上：所有这些 walker 从来就**没真正在 O basin**——它们在 mid-path
  附近（corrected path 上 s ≈ 5–10），只是被错误 path 坐标系投影成 s ≈ 1
- 唯一 "physical stall" 的残留可能: 从 mid-path 到真正 C end（s=15）之间还
  有一段距离（pilot 110 ps max_s=8.94，还差 6 s-units 才到 C end），这段
  是否存在真实 free energy barrier，需要 pilot 跑满 1–5 ns 后用 HILLS 累积
  bias 压过去才知道（下周数据）

---

## 第7章 10-walker primary production（pending gate）

### 7.1 Miguel PRIMARY contract（非 fallback）

`seqaligned_walkers/plumed_template.dat` L15–19 的 production plumed:

```
UNITS LENGTH=A ENERGY=kcal/mol

WHOLEMOLECULES ENTITY0=1-39268

p1: PATHMSD REFERENCE=path_seqaligned_gromacs.pdb LAMBDA=80 NEIGH_STRIDE=100 NEIGH_SIZE=6

METAD ARG=p1.sss,p1.zzz ADAPTIVE=DIFF SIGMA=1000 SIGMA_MIN=0.1,0.01 HEIGHT=0.15 PACE=1000 BIASFACTOR=10.0 TEMP=350.0 GRID_MIN=0.5,0.0 GRID_MAX=15.5,2.8 GRID_BIN=300,100 WALKERS_DIR=../HILLS_DIR WALKERS_RSTRIDE=3000 WALKERS_ID=__WALKERS_ID__ WALKERS_N=10

UPPER_WALLS ARG=p1.zzz AT=2.5 KAPPA=800 LABEL=uwall

PRINT ARG=* STRIDE=100 FILE=COLVAR FMT=%8.4f
```

每个参数都逐字对应 Miguel 邮件，**除了**:

- `WHOLEMOLECULES ENTITY0=1-39268`（Miguel 用 1-5978, 因为他系统 5978 原子；
  我们系统 39268 原子）
- `WALKERS_DIR=../HILLS_DIR`（相对路径指向 seqaligned_walkers/HILLS_DIR，
  由 `materialize_seqaligned_walkers.py` 创建）
- `SIGMA_MIN=0.1,0.01`（Miguel 邮件没写，我们加上防止 DIFF 的 σ 估计
  transient underflow——FP-024 教训的继承）
- `RESTART` 不写（Miguel 邮件写了，但他是"walker mid-run"示例；fresh launch
  不能写，否则 PLUMED 会找不到 HILLS 然后 init 失败；FP-033 教训）

**这是 primary contract，不是 fallback**：HEIGHT=0.15, BIASFACTOR=10
（Miguel §2），不是他 §3 给的 0.3/15 fallback。pilot 的高 max_s signal 说明
我们根本不需要 fallback——primary 就能推动。

### 7.2 Seeding: 500 ns Ain cMD 10 snapshots

`seqaligned_walkers/README.md` §Seeding:

- 来源: 500 ns Ain cMD trajectory (Job 40806029, 22 GB, 已 done)
- 抽取时点: t = 50, 100, 150, 200, 250, 300, 350, 400, 450, 500 ns
  (均匀 50-ns spacing)
- 预期 s 覆盖: 在 corrected path 上这些 snapshot 会覆盖 s ∈ [5, 10]
  (mid-path 区域)，这是**天然的 O→PC 过渡区分布**——不需要手动 PyMOL 看
  再抽 basin-bin

### 7.3 Gate 条件

**launch 条件** (从 `seqaligned_walkers/README.md` §Status):

```
Prepared but NOT yet launched. Awaiting pilot 45515869 gate:
- max_s > 12 on corrected path → promote this to production
- max_s stalls < 5 → diagnose before launching 10-walker
```

**当前状态** (2026-04-23 night): pilot 110 ps max_s = 8.94, 上升中。需要再跑
1–5 ns 看是否 max_s > 12 (接近 C end)。如果 overnight 内能到 > 12, 则明天就
launch 10-walker。

**资源预估**: 10 walkers × 5–10 ns 独立跑 + HILLS 每 6 ps 共享
(RSTRIDE=3000 × 2 fs = 6 ps)。总计 ~50–100 GPU-h (volta-gpu 或 a100-gpu)。
按 Longleaf 当前 queue 状态一周内完成。

### 7.4 Post-run deliverable

从 `seqaligned_walkers/README.md` §Post-run deliverable:

1. `COLVAR_all.csv` - 10-walker s/z/bias/time 合并 csv (Python pandas
   concat)
2. `plumed sum_hills` on combined HILLS (`cd HILLS_DIR; plumed sum_hills
   --hills HILLS.0 HILLS.1 ... --kt 0.695 --outfile fes.dat`；注意单位
   kcal/mol → kt=0.695 而不是 2.908，FP-021 educative 规则 14）
3. 2D (s, z) FES plot，对比 Osuna 2019 Figure 3 baseline (O/PC/C 三个
   basin 的相对深度)
4. methods-critique writeup 引用 FP-034 + PMSD path-recipe 重建过程

---

## 第8章 本周脚本 & 自动化清单

### 8.1 新脚本 / 新 artifact

| 文件 | 作者 | 作用 | 行数参考 |
|---|---|---|---|
| `replication/metadynamics/path_seqaligned/build_seqaligned_path.py` | Claude | NW alignment + Kabsch + linear interpolation + self-projection sanity | 239 L |
| `replication/metadynamics/path_seqaligned/verify_and_materialize_seqaligned_path.py` | Codex | 独立实现，7/8 PASS 验证 Claude 版本 | (materialization 版) |
| `replication/metadynamics/path_seqaligned/path_seqaligned.pdb` | Claude (output) | 新 reference path, atom serial 1..112 | 15 MODEL × 112 atoms |
| `replication/metadynamics/path_seqaligned/path_seqaligned_gromacs.pdb` | Codex (output) | production artifact, GROMACS serial preserved (1614, 1621, ...) | 15 MODEL × 112 atoms |
| `replication/metadynamics/path_seqaligned/summary.txt` | build_seqaligned_path.py | numeric summary | 27 L |
| `replication/metadynamics/path_seqaligned/VERIFICATION_REPORT.md` | Codex | 7/8 PASS + diff vs Claude | 121 L |
| `replication/metadynamics/path_seqaligned/plumed.dat` | Codex | driver-only plumed (for self-projection test) | short |
| `replication/metadynamics/path_seqaligned/plumed_path.dat` | build_seqaligned_path.py | PATHMSD-line only, LAMBDA=80 | 4 L |
| `replication/metadynamics/miguel_2026-04-23/seqaligned_walkers/plumed_template.dat` | Claude | 10-walker production plumed, LAMBDA=80 + PRIMARY contract | 22 L |
| `replication/metadynamics/miguel_2026-04-23/seqaligned_walkers/materialize_seqaligned_walkers.py` | Claude | stamp walker_00..walker_09, extract 10 cMD snapshots, build TPRs | - |
| `replication/metadynamics/miguel_2026-04-23/seqaligned_walkers/submit_array.sh` | Claude | SLURM array 0-9, volta/a100-gpu | - |
| `replication/metadynamics/miguel_2026-04-23/seqaligned_walkers/README.md` | Claude | 10-walker launch checklist + gate条件 | 67 L |
| `replication/metadynamics/path_piecewise/RETRACTION.md` | Claude | 撤销 piecewise audit 的 βPC 否定结论 | 58 L |
| `replication/metadynamics/miguel_2026-04-23/lambda_audit_2026-04-23.md` | Claude | 3.77 vs 80 vs 100.79 的 λ 自洽性对照 | 70 L |
| `colab_review/verify_all.py` | Claude | 33-claim independent numerical cross-check（可 Colab 跑） | 283 L |
| `chatgpt_pro_consult_45324928/` | Claude | 给 ChatGPT Pro 打包的 45324928 诊断数据 | (bundle) |

### 8.2 Repo state

- Branch: `path-piecewise-pilot`
- Recent commits (见 git log):
  - `68f5904` BREAKTHROUGH: sequence-aligned path resolves 21x lambda gap
  - `0dc49ab` Path-piecewise: fix z(R) log-sum-exp bug + rerun scan +
    draft author email
  - `b780ad1` Path-piecewise audit: reject PC-at-MODEL8 single-lambda
    design （现已 RETRACTION）
  - `65ea321` Miguel 2026-04-23 MetaD contract pivot (FP-031, FP-032)
  - `65625fc` pilot_matrix: scaffold 2x2 (anchor x sigma_seed) without
    touching locked probe_sweep （现已 deprecated via FP-031）

### 8.3 Longleaf 侧文件位置

```
/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/
├── initial_seqaligned/         ← pilot 45515869 运行中
│   ├── plumed.dat
│   ├── path_seqaligned_gromacs.pdb
│   ├── start.gro (500ns cMD 终态)
│   ├── HILLS    (rolling)
│   ├── COLVAR   (rolling)
│   └── slurm-45515869.out
└── seqaligned_walkers/         ← 10-walker (待 launch)
    ├── walker_00/..walker_09/  ← materialize_seqaligned_walkers.py 待跑
    ├── HILLS_DIR/              ← 共享 bias 目录
    └── submit_array.sh
```

本地对应：`replication/metadynamics/miguel_2026-04-23/seqaligned_walkers/`。

---

## 第9章 未来方向 & Q&A 准备

### 9.1 如果 pilot gate 过 (max_s > 12 by overnight)

1. 明天（2026-04-24）launch 10-walker array (`sbatch submit_array.sh`)
2. 每 4 小时 poll 一次 HILLS_DIR/，确认 10 个 HILLS.0..9 都在写且 size
   同步增长
3. 5–10 ns/walker 后 (~2 天) 合并所有 HILLS → `plumed sum_hills --kt 0.695`
   → 2D FES (s, z)
4. 对比 Osuna 2019 Figure 3: O / PC / C 三个 basin 相对深度
5. 如果 FES 形态与 Osuna 定性一致 → 本次 replication 的 MetaD layer **通过**，
   准备 GenSLM-230 比较 phase
6. 如果 FES 形态不一致 → 另起 validation note 记录差异 + 可能原因
   (path density 的 residual 1.26× gap, 或 mid-path frame 的细节)

### 9.2 如果 pilot gate 不过 (max_s stalls < 5 in 5 ns)

1. 先排查是否 seeding 问题：start.gro 真的是 500 ns cMD 终态吗？gmx check
   一遍 TPR 的 topology 文件 + ensure 没有被之前 FP-024 / FP-026 污染
2. 检查 PATHMSD 是否在读 corrected path：plumed driver 重跑一次 self-projection
   在 Longleaf 侧
3. 如果以上都 OK 但还是 stall → 真的可能 Ain 体系存在 activated barrier,
   考虑从 1WDW 原 crystal 做 short equilibrate + 换种子结构再试
4. 或者 rerun 45186335 Aex1 cMD (30% 进度) 等 Aex1 到位，两条体系并行

### 9.3 Aex1 cMD 45186335 状态

- 提交日期: ~2026-04-18
- 当前进度: ~30%（根据最后一次 SSH poll 的 log tail）
- ETA: 2026-04-28 前后
- 用途: 一旦跑完，Aex1 体系的 500 ns 终态 + 10 个 snapshot 可以作为**第二个
  独立体系**的 MetaD seed；独立于 Ain 跑一次 10-walker 做 cross-intermediate
  validation（SI Table S2: PfTrpB₂ 的 Ain / Aex1 对应 Osuna 2019 主要复现目标）

### 9.4 Yu 可能的反问 & 回应

**Q1**: "为什么不提前做 sequence alignment？"

A: 项目最初（2026-03-28 左右）`generate_path_cv.py` 确实写了 pairwise2
比对代码（FP-034 L494 根因 (1)），但只**打印** identity 没 wire 到提取。
当时的 AI + 我的 review 都没 catch。这属于 "false comfort" 类 bug，在
`failure-patterns.md` 里现在作为 FP-034 防范措施第 (2) 条记录。新规则 §10.5
硬性要求：未来任何 PATHMSD reference 建立时 NW identity < 50% 必须 block。

**Q2**: "old path 数据全废了吗？"

A: 物理观察（walker 动力学、Gaussian 沉积、FES 形状 on old path）全部**需要
重解释**，不等于"无用"——它们作为 coordinate artifact 的教材价值仍在
（`path_piecewise/RETRACTION.md` 明文保留整个旧 audit 作为污染链的证据）。
但"on the real reaction coordinate is the walker making progress" 这个
question 必须用 corrected path 重新问。

**Q3**: "Miguel 的 80 和你的 100.79 差 26%，为什么敢用 80？"

A: Branduardi 2007 heuristic 目标 kernel weight ≈ 0.10；80 给 0.161，
100.79 给 0.100——两者都在 [0.10, 0.16] 这个 tolerant 区间内。选 80
因为它**逐字**和 Miguel 邮件一致，方便 methods 表述、审稿人查证、减少一个
"self-tuned parameter"。如果后续 FES 对不上 Osuna 2019，再把 λ 换成 100.79
作为 sensitivity test。

**Q4**: "pilot 只 110 ps 就 max_s=8.94 是不是 bias 爆了？"

A: 不是。`HEIGHT=0.15` kcal/mol + `PACE=1000`，110 ps 内沉积约 110 个
Gaussian，累计 bias 上限 ~16.5 kcal/mol（BIASFACTOR=10 时 well-tempered
规律会进一步压制）。实际上 walker 进展快 是因为：500 ns cMD 终态已经
natural relax 到 mid-path 区域，所以一开始就是 s=7，推到 s=9 只需要跨 2
s-units（6 frames），MetaD kernel smooth 下就够了。

**Q5**: "Phase 2 什么时候能定？"

A: 2026-04-24 上午看 pilot overnight 结果决定。gate 条件写死在
`seqaligned_walkers/README.md` §Status——不是主观判断，过了 `max_s > 12`
就 launch，不过就 debug，没有 "大概/看情况"。

---

## 第10章 判断原则与诊断规则（Decision Rationale）

> 本章记录本项目中使用的**诊断逻辑和决策规则**。FP-034 这周触发了一条
> 新 rule（§10.5），其余 §10.1–10.4 是 2026-04-17 规则的 updated 版本，
> 根据 Miguel contract + corrected path 重新标定数值阈值。

---

### 10.1 HILLS 法医分析三步法（Miguel DIFF 版本）

每次跑完/跑中，打开 HILLS 做以下三个检查。**DIFF 下的 σ 列语义和 GEOM 不同**
——DIFF 里 σ 是 PLUMED 从 walker 近期扩散张量估计出来的动态量，不是 input
参数。

**步骤 1 — Sigma 合理性检查**

```python
import numpy as np
h = np.loadtxt('HILLS', comments='#')
# 列: time  s  z  sigma_ss  sigma_zz  sigma_sz  height  biasf
sigma_ss = h[:, 3]
sigma_zz = h[:, 4]
print(f"σ_ss range: {sigma_ss.min():.4f} – {sigma_ss.max():.4f} s-units")
print(f"σ_zz range: {sigma_zz.min():.4f} – {sigma_zz.max():.4f} Å²")
```

| 结果 | 诊断 |
|---|---|
| σ_ss 0.01 – 0.2 (DIFF scheme normal) | 健康 |
| σ_ss < 0.005 for 持续 ps | 走 GEOM-style 塌缩（按理 DIFF 不会，但 SIGMA_MIN=0.1 是 safety net） |
| σ_zz > 5 Å² 持续 | z 方向 walker 在大幅摆动，可能已出 upper wall (AT=2.5) |

45324928 的 `σ_ss median = 0.0304`（`verify_all.py` L259）是 DIFF scheme
正常范围。

**步骤 2 — Bias 历史完整性**

```bash
ls bck.*.HILLS 2>/dev/null && echo "DANGER: bias history clobbered" || echo "OK"
wc -l HILLS   # 健康: 只增不减
```

FP-026 教训的继承。10-walker 下要 `ls HILLS_DIR/bck.*.HILLS`，任意一个有
backup 文件都要 flag。

**步骤 3 — 沉积速率**

```python
times = h[:, 0]  # ps
pace_ps = 2  # PACE=1000 × dt=2 fs
expected = (times[-1] - times[0]) / pace_ps
print(f"actual {len(h)}  expected {expected:.0f}  ratio {len(h)/expected:.3f}")
# ratio ≈ 1.0 → 正常；< 0.95 → walltime 截断
```

---

### 10.2 Per-parameter unit clarification

**Miguel contract + sequence-aligned path 下**，所有 CV 量的单位表:

| 量 | 单位 | 为什么 |
|---|---|---|
| `path.sss` (s(R)) | **dimensionless** (s-units, 1..15) | Σ i·w_i / Σ w_i, 分子分母同权重单位消掉，剩下 i 的 index |
| `path.zzz` (z(R)) | **Å²** (per-atom MSD) | −(1/λ)·ln(Σ exp(−λ·MSD))；λ 单位 Å⁻² 所以 z 单位是 Å² |
| `LAMBDA` | **Å⁻²** (UNITS LENGTH=A 下) | 对应 per-atom MSD in Å² |
| `SIGMA` (DIFF scheme) | **simulation steps** (dimensionless int) | Miguel 邮件明说 SIGMA=1000 是 time window; 1000 × 2 fs = 2 ps |
| `SIGMA_MIN=0.1,0.01` | s-units, Å² | per-CV 原生单位, `path.sss` 的 0.1 s-units + `path.zzz` 的 0.01 Å² |
| `HEIGHT` | **kcal/mol** (UNITS ENERGY=kcal/mol) | Miguel 邮件 ENERGY=kcal/mol，0.15 对应 ~0.36 kT at 350K |
| `UPPER_WALLS AT=2.5` | **Å²** (z(R) 单位) | walls 约束 z(R)，单位和 CV 一致 |
| `UPPER_WALLS KAPPA=800` | kcal/mol per (Å²)² | quadratic wall constant |
| `WHOLEMOLECULES ENTITY0=1-39268` | atom serial range | GROMACS topology 全部 39268 原子 |
| `NEIGH_STRIDE=100 NEIGH_SIZE=6` | steps / frames | 每 100 steps 重新 pick 6 最近 reference frames 做 PATHMSD |

**GROMACS 默认是 nm + kJ/mol——Miguel 邮件强制 `UNITS LENGTH=A ENERGY=kcal/mol`
在 plumed 顶端，PLUMED 会做内部单位转换。**我们所有 plumed 输出
(HILLS/COLVAR) 从此都是 Å/kcal，不再是 nm/kJ。reweight 和 sum_hills 必须
`--kt 0.695`（kcal/mol at 350K: 0.001987 × 350 = 0.695）而不是 2.908（kJ/mol）。

---

### 10.3 Phase decision logic (pilot → 10-walker gate)

**为什么 pilot gate 设在 max_s > 12，不是 > 5 或 > 10？**

- s ∈ [1, 5]: O basin (1WDW-like)
- s ∈ [5, 10]: PC basin (5DVZ/5DW0/5DW3 区域)
- s ∈ [10, 15]: PC→C + C basin (4HPX @ s≈14.9)

pilot 证明 walker 能从 start seed (s ≈ 7) 推到 **s > 12 (PC→C 过渡区)**
才能证明 MetaD bias 足以跨越整个 path span，进而 10 walkers 一起跑能覆盖
full (s, z) 空间。gate < 12 说明 walker 仍然卡在 PC basin 出不来，单纯扩展
到 10-walker 也没用。

| Gate level | Action |
|---|---|
| max_s > 12 in pilot 5 ns | launch 10-walker PRIMARY (HEIGHT=0.15) |
| max_s ∈ [10, 12] in 5 ns | launch 10-walker fallback (HEIGHT=0.3, BIASFACTOR=15) |
| max_s < 10 in 5 ns | debug: topology, seeding, path sanity, before launching any 10-walker |
| max_s < 5 in 10 ns | FP-flag: new pattern, not yet logged. Email Miguel 二次咨询 |

**5-ns 窗口趋势**:

```python
# 连续 3 个 5-ns 窗口 max_s 变化 < 0.1 → walker 卡住
# 连续 3 个窗口单调上升 → 正在爬坡
# 单个窗口大跳 > 1.5 s-units/5 ns → activated crossing
```

---

### 10.4 File locations（Longleaf + 本地）

**Longleaf** (`/work/users/l/i/liualex/AnimaLab/metadynamics/`):

```
miguel_2026-04-23/
├── initial_seqaligned/         ← pilot 45515869
│   ├── plumed.dat (λ=80, 全 Miguel primary)
│   ├── path_seqaligned_gromacs.pdb (FP-034 修正后)
│   ├── start.gro (500 ns cMD 终态)
│   ├── HILLS  ← rolling
│   ├── COLVAR ← rolling
│   └── slurm-45515869.out
└── seqaligned_walkers/         ← 10-walker 待 launch
    ├── plumed_template.dat
    ├── materialize_seqaligned_walkers.py
    ├── submit_array.sh
    ├── HILLS_DIR/  (materialize 后创建)
    └── walker_00 .. walker_09/ (materialize 后创建)

miguel_2026-04-23/45324928_archive/  ← Miguel fallback old-path 运行数据
miguel_2026-04-23/45448011_wall_test/ ← wall 解锁实验
```

**本地** (repo tree):

```
replication/metadynamics/
├── path_seqaligned/            ← 本周核心产物
├── path_piecewise/             ← RETRACTION 标记，历史保留
│   ├── RETRACTION.md
│   ├── generate_piecewise_path.py (logic OK, conclusion wrong)
│   └── path_5DW0/, path_5DW3/
├── miguel_2026-04-23/          ← contract 文件
│   ├── miguel_email.md (verbatim)
│   ├── lambda_audit_2026-04-23.md
│   ├── README.md
│   ├── plumed_template.dat (λ=3.77, old path, deprecated)
│   ├── plumed_single.dat (λ=3.77, old path, deprecated)
│   └── seqaligned_walkers/     ← 新 production 目录
├── single_walker/              ← old path, frozen for historical reference
├── probe_sweep/                ← GEOM-era, marked deprecated (FP-031)
└── pilot_matrix/               ← GEOM-era, marked deprecated (FP-031)

colab_review/                   ← 独立 numerical 交叉核对
├── verify_all.py
├── HILLS, COLVAR (45324928 下载)
└── *.pdb (1WDW, 3CEP, 5DW0 etc.)

chatgpt_pro_consult_45324928/  ← 外部咨询数据打包
```

---

### 10.5 **新 rule**: 跨物种 PATHMSD reference 必须先做 NW 验证 identity > 50%

> **来源**: FP-034 (2026-04-23 本周新增)
>
> **规则陈述**: 任何 PATHMSD reference path 如果 endpoints 来自**不同物种**
> 或者**不同 construct / crystal 来源**的 PDB 文件，在提取 Cα 坐标之前
> **必须**:
>
> 1. 对两条链的**完整 β 序列**做 Needleman-Wunsch 全局比对（纯 numpy DP
>    或 BioPython `pairwise2`）；
> 2. 计算比对 identity（匹配 / max(len1, len2)）；
> 3. **硬 gate**: identity < 50% → **block** 坐标提取，打印 error + 退出
>    code 2；
> 4. 即使 identity ≥ 50%，如果 offset 非 uniform（不同 residue 区段 offset
>    不一致），也必须 block；
> 5. 通过 gate 后，**residue-to-residue mapping** 必须显式落实在坐标提取
>    代码里——不能是"打印 alignment 然后按 naive resid number 提坐标"（即
>    FP-034 的 silent bug pattern）。

**为什么 50% 是阈值**: TrpB 两个物种 β 链 identity = 59%, 已经是同源蛋白
范畴；若某对 PDB identity < 50%, 大概率是 paralog 或远亲同源 (remote
homologs)，用 linear interpolation 做 path 会产生过大 endpoint RMSD，
Branduardi λ 不再有意义。50% 是 BLASTP "twilight zone" 之上的安全阈值
（低于 30% 叫 twilight zone, 低于 50% 要谨慎）。

**为什么 uniform offset 是 hard-gate**: non-uniform offset 说明某个区段
有 insertion/deletion，那个区段的 Cα 对应关系**不是 1:1**——linear
interpolation 在 insertion gap 处会 collapse 多个 Cα 到一个，或者 leave
out 关键的 structural residue。必须手动 resolve insertion 后再 interpolate。

**实施清单**:

```python
# 强制模板 (所有未来 path-builder 脚本头部)
def build_cross_species_path(pdb1, pdb2, chain1, chain2, target_residues):
    seq1, resids1, coords1 = load_ca(pdb1, chain1)
    seq2, resids2, coords2 = load_ca(pdb2, chain2)

    # Gate 1: NW identity
    aln1, aln2, score = needleman_wunsch(seq1, seq2)
    ident = n_match(aln1, aln2) / max(len(seq1), len(seq2))
    assert ident > 0.50, (
        f"REFUSE: sequence identity {ident:.3f} < 0.50. "
        f"This is not a valid cross-species PATHMSD reference pair. "
        f"See FP-034.")

    # Gate 2: uniform offset
    mapping = build_mapping(aln1, aln2, resids1, resids2)
    offsets = [mapping[r] - r for r in target_residues if r in mapping]
    assert len(set(offsets)) == 1, (
        f"REFUSE: non-uniform offset {set(offsets)}. "
        f"Indel present in target region, manual resolution required. "
        f"See FP-034.")

    # Gate 3: explicit mapping in coordinate extraction
    lut1 = {r: i for i, r in enumerate(resids1)}
    lut2 = {r: i for i, r in enumerate(resids2)}
    O = np.stack([coords1[lut1[r]] for r in target_residues])
    C = np.stack([coords2[lut2[mapping[r]]] for r in target_residues])
    # C 用的是 mapping[r], 不是 r —— 这一行就是 FP-034 的核心修复
    ...
```

**历史 assert 样本** (本周已部署，见
`build_seqaligned_path.py` L128–143 的 logic):

- NW score = 286 (above some project-specific threshold)
- identity = 59.0% (> 50% gate pass)
- offset range: 5 to 5 (uniform gate pass)

**谁 enforce 这条规则**:

- AI agent 生成任何新的 path-builder 脚本时，必须在脚本头部 assert 这三
  道 gate
- Codex peer review: 看到任何 cross-species PDB pair 没有 NW 前置就
  flag 拒绝
- 人类 review: merge PR 前 grep `pairwise2|needleman|nw_align|identity`
  在新脚本里必须命中

**为什么单列成一条 rule**:

FP-034 本身只是一个 bug；这条 rule 是从 FP-034 抽出来的**可机械检查的
preventive policy**。bug 会 resolve，但同类 silent-mapping 陷阱（AI 写了
alignment 代码但不用、或 code review 看到打印就放心）可以复发。这条 rule
的作用是让 AI 下次建 path 时必须**脚本化强制** gate，不是靠 review 凭
眼睛。

---

**本章结束。**

---

## 附录 A — 本周文件 md5 / 关键数字 snapshot

| 文件 | 关键数字 | 来源行 |
|---|---|---|
| `path_seqaligned/summary.txt` | λ = 100.79 Å⁻² | L21 |
| `path_seqaligned/summary.txt` | O↔C RMSD = 2.115 Å | L18 |
| `path_seqaligned/summary.txt` | ⟨MSD⟩ = 0.0228 Å² | L19 |
| `path_seqaligned/summary.txt` | identity = 59.0% | L14 |
| `path_seqaligned/VERIFICATION_REPORT.md` | NW score = 286 | L26 |
| `path_seqaligned/VERIFICATION_REPORT.md` | ratio new/Miguel = 1.2599 | L54 |
| `path_seqaligned/VERIFICATION_REPORT.md` | self-proj frame 1 s = 1.091298 | L78 |
| `path_seqaligned/VERIFICATION_REPORT.md` | self-proj frame 15 s = 14.908702 | L92 |
| `path_seqaligned/VERIFICATION_REPORT.md` | 5DW0 projects at s = 9.455 | L101 |
| `path_seqaligned/VERIFICATION_REPORT.md` | 5DW3 projects at s = 8.508 | L102 |
| `path_seqaligned/VERIFICATION_REPORT.md` | 5DVZ projects at s = 5.371 | L103 |
| `path_seqaligned/VERIFICATION_REPORT.md` | 4HPX projects at s = 14.898 | L104 |
| `colab_review/verify_all.py` | 45324928 max_s = 1.4964 | L248 |
| `colab_review/verify_all.py` | 45324928 p95(s) = 1.2835 | L250 |
| `colab_review/verify_all.py` | 45324928 σ_ss median = 0.0304 | L259 |
| `colab_review/verify_all.py` | 45324928 n_hills = 1880 | L264 |
| `failure-patterns.md` | FP-031 line | L454 |
| `failure-patterns.md` | FP-032 line | L469 |
| `failure-patterns.md` | FP-034 line | L485 |
| `miguel_2026-04-23/miguel_email.md` | Miguel 邮件 verbatim | L1–43 |
| `seqaligned_walkers/plumed_template.dat` | LAMBDA=80 (primary) | L15 |
| `seqaligned_walkers/plumed_template.dat` | HEIGHT=0.15 (primary) | L17 |
| `seqaligned_walkers/plumed_template.dat` | BIASFACTOR=10.0 (primary) | L17 |

---

## 附录 B — 术语速查

| 术语 | 本周文档含义 |
|---|---|
| naive mapping | 直接按 resid number 对齐两个 PDB 的 Cα（FP-034 bug 核心） |
| sequence-aligned mapping | 先做 NW，按 alignment 结果 map resid 对 resid |
| corrected path | sequence-aligned path (`path_seqaligned_gromacs.pdb`) |
| old path | naive path (`single_walker/path_gromacs.pdb`) |
| Miguel contract | Miguel 2026-04-23 邮件给的 plumed 参数集 |
| PRIMARY | HEIGHT=0.15 BF=10（Miguel §2，默认） |
| fallback | HEIGHT=0.3 BF=15（Miguel §3, stuck-single-walker 应急） |
| pilot | 45515869 单 walker + corrected path + PRIMARY contract |
| gate | pilot max_s > 12 → launch 10-walker；否则 debug |
| λ self-consistency | 在给定 path 上 Branduardi λ = 2.3/⟨MSD⟩, 相邻帧权重 ~0.10 |

---

**文档结束。**
