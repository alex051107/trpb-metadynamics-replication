# MetaD Cartridge Feasibility Memo (v1.2, 2026-04-22) — **SUPERSEDED 2026-04-24**

> ⚠️ **THIS MEMO IS SUPERSEDED**. 
> See `Convergence_Memo_v2_2026-04-24.md` for the current recommendation.
> 
> **What changed**: Codex (via CCB, 4-24) and earlier Reports 1/2/3 (4-20) both concluded that "Cartridge as product" is the wrong framing. The correct framing is **F0+PathGate Evaluator** — MetaD is escalation infrastructure, not the headline. This v1.2 kept cartridge at the center; v2.0 demotes cartridge to an internal `pathgate/cartridge/` folder inside the evaluator package.
> 
> v1.2 is retained below as audit trail of the thinking that led to v2.0. The ByteDance analysis and stakeholder scripts in §0.4 are still valid; the cartridge-as-headline positioning is not.

---

> 作者：Claude（Zhenpeng 的 designer agent）
> 状态：**v1.2 — PM (Zhenpeng) 二次审阅完成；framing 已收敛** [SUPERSEDED]
> v1.1 分析保留在下半部分作为 decision trail。
> 顶部 §0 是 canonical 版本，往下是支撑材料。

---

## 0. CANONICAL DECISION (v1.2 PM-ratified, 2026-04-22)

### 0.1 一句话定位

> **STAR-MD 把通用蛋白轨迹生成做满了。TrpB 需要的是 mechanism-grounded evaluation。我把 TrpB 的 MetaD 机制真值做成可复用 cartridge，用来评价、筛选和纠偏 lab 里的生成式 enzyme-design pipeline。**

**关键语言边界**：
- ❌ "I'm building a new ML model / dynamics layer"
- ❌ "I own the TrpB ground truth"  
- ✅ "I'm building the mechanism-grounded reference cartridge"
- ✅ "STAR-MD and my cartridge are upstream-downstream, not competitors"

### 0.2 Cartridge = 这 7 件东西，不是抽象的"ground truth"

1. **path definition**：O/PC/C 的 PATHMSD 坐标（现在 path.pdb 正在和 Miguel 对齐）
2. **reference FES**：WT / Aex1 / 变体（WT 先做）
3. **state masks**：O、PC、C、off-path、reactive-ready
4. **block uncertainty**：带 CI 的可信区间，不是一张漂亮图
5. **rare-state frames**：供生成模型/reward model 的 hard examples
6. **catalytic descriptors**：PLP/K82/Y301/E104/indole tunnel 机制几何
7. **scorer API**：`project_to_path()`, `score_trajectory()`, `state_occupancy()`

### 0.3 本周 3 个 Deliverables（不再做 5 个）

| # | Deliverable | 本周要做 | Gate |
|---|---|---|---|
| D1 | **Cartridge core（最小版本）** | 把 Miguel PATH.pdb 对齐问清楚；WT reference 定义；PLUMED input 清理；state masks 草稿 | path.pdb 和 Miguel 版本一致 |
| D2 | **Trajectory scoring wrapper（API 草图）** | 写 `replication/cartridge/API_DESIGN.md`：函数签名 + 输入输出 + 使用场景，不写实现 | 文件 commit |
| D3 | **One lab-facing demo** | 二选一：**Yu demo**（simple CV 失败 → PATHMSD cartridge 给更有意义的 state 诊断）或 **Amin demo**（STAR-MD 输出被 cartridge 打分）。Amin 没有模型输出就先做 Yu。 | 有一个可给出去的 Jupyter notebook 或短报告 |

**不做**：MNG 作主线、Reactive PATHMSD、Arvind 电子效应。这些都是未来 claim，不是本周的价值展现。

### 0.4 对不同人怎么说（canonical 脚本）

**对 Yu**：
> "I saw your OpenMM MetaD update. I'm working on the PLUMED/PATHMSD side and recently got the original-author PLUMED input for the Osuna TrpB MetaD protocol. I'm still reconciling the PATH.pdb construction, but I think this could be directly useful for testing reaction-coordinate choices beyond simple 1D/2D CVs."

**对 Amin**：
> "I'm building a TrpB MetaD cartridge that can score generated trajectories by projecting them onto a mechanism-grounded PATHMSD/FES reference. If your STAR-MD/ConfRover benchmark needs an enzyme-specific task, TrpB could be a useful adversarial case."

**对 Raswanth**（等他有 designs 之后，不主动 pitch）：
> "I can help evaluate whether top designs are dynamically plausible along the TrpB conformational coordinate, not just geometrically valid."

**对 Arvind**（等 Miguel path + WT baseline 更稳后再说）：
> "I'm turning the TrpB MetaD replication into a reusable evaluation cartridge for ML-generated enzyme dynamics and design candidates."

### 0.5 Meta pitch（一段话完整版 — 英文）

> STAR-MD and related models are making generic protein dynamics generation scalable. But enzyme design needs a different layer: mechanism-grounded evaluation. For TrpB, the relevant question is not only whether a generated trajectory is structurally valid, but whether it visits catalytic conformational substates and preserves PLP-dependent reaction geometry. I am building a MetaD-derived TrpB cartridge that turns expensive path-CV simulations into reusable labels, reference FES, rare-state frames, and scoring functions. This can be used to evaluate STAR-MD/ConfRover outputs, filter RFD3/MPNN candidates, and trigger targeted MetaD rescue where ML dynamics misses rare catalytic states.

### 0.6 在 ByteDance 背景下可以 involve 的 5 个方向（但本周只做 D1-D3）

保留作未来扩展，**优先级顺序**：

1. **TrpB adversarial benchmark for STAR-MD/ConfRover/MDGen** — D3 Amin demo 的自然延伸。最稳。
2. **MetaD rescue loop** — 有野心版：ML model propose, MetaD repair. 是 MNG 的落地形态。
3. **MetaD-derived rare-event corpus** — 数据资产。需要 WT + 变体都收敛后再谈。
4. **Path-CV conditioning layer** — 不要 claim 通用 method；只 claim "TrpB PATHMSD/FES-conditioned evaluation wrapper"。
5. **Dynamics-aware design filter** — 对 Raswanth/Yu 直接有用。进 GRPO 是远景。

### 0.7 Deep-research 三问的 v1.2 结论

| 问题 | 结论 | 保留行动 |
|---|---|---|
| PLaTITO/ConfRover/STAR-MD 是否已处理 enzyme-specific dynamics？ | **没有**。它们是 generic protein dynamics / Cα CG / sequence-conditioned trajectory 模型 | enzyme cartridge 方向活 |
| MetaD-biased trajectory corpus 作训练数据？ | 材料/MLIP 方向有，**enzyme+PLP MetaD corpus 没有直接等价** | 方向 3 的空位活 |
| SE(3) diffusion + path-CV conditioning 吃掉没？ | 通用 guided generation 已挤；**path-CV+enzyme mechanism 作为 evaluation target 没吃掉** | 不 claim 通用 method，只 claim evaluation wrapper |

### 0.8 硬 gate 不变

- WT MetaD 收敛（Job 44008381 / Phase 2 10-walker）
- path.pdb 和 Miguel 版本 reconciled
- 2026-05-01 kill-switch：如果 WT FES 还没过 sanity check，所有 5 方向都暂缓，回到单 walker → 10-walker 升级

---

**以下是 v1 / v1.1 分析材料，保留作 decision trail。canonical 版本到此结束。**

---

# 附（v1.1 支撑材料 — PM 审阅前的原始分析）
> 前置阅读：`新任务explore/TrpB 锚定的序列条件动力学贡献设计书.md`、`真正卡点与可行性判断.md`、`papers/reviews/starmd_team_review_2026-04-17/round4_synthesis.md`、`reports/tools/slack_history.md`

---

## 0. 这份文档是什么、不是什么

**是什么**：在"3-agent debate 结束 → 用户要我把 cartridge 想法做 deep research + 五 × 五"这一节点上，把所有可能的 ML-layer 形态和下一步贡献动作铺开成可决策选项，附可证伪测试与不确定清单。

**不是什么**：
- 不是实施计划（user 还没批准任何一条）
- 不是论文大纲（没到那一步）
- 不是已通过 PI/Arvind/Amin 的提议（内部分析）

---

## 1. TL;DR

**核心定位**（来自 3-agent 合成）：把自己定位成 "**TrpB MetaD Ground-Truth Cartridge Owner**"，而不是"做模型的人"。cartridge = WT + 变体 FES（带 block CI）+ state labels + path CV 定义 + rare-state pack + 化学几何 descriptors。

**为什么这个定位不和 lab 内任何人正面冲突**：
- Amin 已占 STAR-MD benchmark codebase → 你给他 TrpB **evaluation cartridge**，他的 benchmark 因此能测到 Arvind Jan-5 原话要的"metadynamics substates"
- Raswanth 已占 GRPO reward → 你给他 **optional catalytic-readiness reward head**，但前置已和 Yu 的 MMPBSA 排名共验证，不是空讲
- Yu 已在和你结对 → cartridge 反哺她对 MMPBSA winners 做 rare-state rescue
- Anima 否决了 generic RNO → 你不 claim 架构；你 claim "没我这块 ground truth，别人的架构没法被检验"

**五种把 cartridge 扩展成 ML 层的方法**（第 3 节）与**五种下一步贡献方法**（第 4 节）按 stakeholder/时间顺序排列。每条都附可证伪测试与 10-周可行性。

---

## 1.5 AUDIT 结论摘要（v1.1 新增 — 关键）

> 2026-04-22 外部文献核查（2024–2026 arXiv/Nature/JCTC/PNAS/bioRxiv）完成。
> **五种 ML 层方法里有两条 DEAD、两条 WEAKENED、一条 ALIVE。**

| 方法 | 原初评估 | 审计后 verdict | 主要杀手 |
|---|---|---|---|
| A. CRR | 中-高 | **WEAKENED** | PocketX, ResiDPO, ProteinZero 已经做 "GRPO+reward on protein design"；唯一剩下的新意是 "MetaD-validated closed-basin 作为 projection 指标"，不是 RL 框架 |
| B. PP-Prior | 中 | **WEAKENED** | Enhanced Diffusion Sampling (arXiv 2602.16634), training-free guidance (2409.07359) 已占 energy-guided diffusion；path-CV (s,z) 专门版本还是薄但活的 |
| C. LBP | 不确定 | **DEAD** | NN-VES (Bonati/Parrinello PNAS 2019), Deep-TICA + OPES + mlcolvar 已占完整空间。只有"应用到 TrpB PATHMSD"这种 engineering-level 剩余 |
| D. TCR | 不确定 | **DEAD-ish** | Thermodynamic Interpolation (JCTC 2024), Energy-Based CG Flow (JCTC 2025), Experiment-Directed MetaD 已占；唯一保留是"作为 PP-Prior 的 training-time 对偶"—— 与 B 合并 |
| E. MNG | 高 | **ALIVE** | MEMnets (Nature Comput Sci 2025) 是 CV 发现，不是 runtime gate；qMSM / active-learning VAMPnets 不用来触发 MetaD rescue。定位最独特 |

**真正的 meta-结论（来自审计 agent 原话）**：
> *"The cartridge itself (the FES + state labels + path CVs as a reusable artifact for TrpB specifically) is likely more novel than any individual ML layer built on top."*

**这意味着什么**：
- Cartridge 本身（非 ML layer）是你的主产品
- ML 层是 **可选的 extension**，不是主 contribution
- 你的 pitch 重心应该是 "I own the only MetaD-grounded TrpB-family evaluation cartridge"，ML 层作为"这是它能解锁的下游"
- 5 个 ML 层里，**只有 MNG 是独立可立得住的**；其他需要降级成"cartridge 的 demonstration/plug-in"，不是主 claim

**替换候选**（审计后为保持 5 个活选项新增，见 3.6 / 3.7）：
- 方法 F — PLP-aware reactive-coordinate extension of PATHMSD (替换 C)
- 方法 G — Generative-model physics-consistency audit layer (替换 D 独立性)

---

## 2. Cartridge 的精简定义

| 组件 | 内容 | 状态 |
|---|---|---|
| WT FES on unified PATHMSD grid | Job 44008381 应产出，或 phase 2 10-walker 产出 | **进行中** |
| 2–3 个公开 TrpB 变体 FES（同坐标系） | 0B2 + 1–2 个文献变体 | 未开始 |
| State masks (O / PC / C) + block CI | 需定义 rule + block analysis 脚本 | 脚本已写部分 |
| Path CV 定义 + path.pdb | 已产出，λ ≈ 0.034 | **已完成** |
| Rare-state pack (frames + weights + ESS + CI) | 从 reweighted HILLS 导出 | 未开始 |
| Chemistry-geometry descriptors（state-conditional） | PLP-Lys 几何、Dunathan-like 角、tunnel gate | 未开始 |
| 公开 license + scorer scripts | CC-BY-4.0 + MIT | 未开始 |

**cartridge 的最小可交付版本 = WT FES + 1 个变体 FES + path.pdb + state masks + 一个 scorer script**。这是所有下游 ML 层的共同地基。

---

## 3. 五种把 MetaD 变成 ML 层的方法

> **Novelty 警告**：本节所有结论基于内部推理，外部文献核查 agent 正在跑。等它回来后会在每条下补"外部 verdict"。目前暂标 **〔pending〕**。

### 3.1 方法 A — CRR (CatalyticReadinessReward)

**WHAT**：从 WT + 变体 MetaD FES 拟合一个轻量 state-conditional geometry scorer（B2 的延伸）。输入：RFD3 或 MPNN 生成的候选结构。输出：标量 reward = "此 pocket 几何投射到 parent TrpB 的催化就绪 basin 的概率"。

**CONSUMER**：Raswanth 的 GRPO reward function（F0 或新增 F3 tier）。

**INTEGRATION HOOK**：GRPO 内循环 per-step 调用，&lt;100 ms inference。

**LOAD-BEARING TEST**：
1. CRR 对 Yu Zhang 的 MMPBSA ranking 的 Spearman ρ &gt; 0.5（随机 baseline ≈ 0）
2. CRR 对 JACS 2019 / Duran 2024 已知高活性 vs 低活性 TrpB 变体分得开（AUC &gt; 0.75）

**10-WEEK V0 可行**：✅ 数据 pipeline + scorer + Yu 数据对照
**10-WEEK V0 不可行**：❌ 接入 Raswanth 的 GRPO 主循环（那是他的代码基）

**不确定项**：
- 不确定 Yu 能否及时提供 MMPBSA ranking 的可共享版本（需和她确认）
- 不确定 Raswanth 的 F0 reward 当前 ρ 是多少 —— 如果 F0 本身已和活性高度相关，CRR 的增量价值会很小
- 不确定 chemistry descriptors 在 ff14SB/TIP3P 下是否足够稳健作为 reward

**AUDIT VERDICT (v1.1)**: **WEAKENED (MED confidence)**. PocketX (bioRxiv 2025.12.28.696754), ResiDPO (arXiv 2506.00297), ProteinZero (arXiv 2506.07459) 已经做 "GRPO + binding/designability reward on protein design"。**独立 novelty 死**。唯一保留：将 CRR 重新定位为 *projection metric*（把候选几何投到 parent TrpB 的 MetaD-validated 催化 basin），不是 RL 框架本身。pitch 时强调 "conformational-readiness projection"，不要说 "new GRPO reward"。

---

### 3.2 方法 B — PP-Prior (Path-Progress Conditioning)

**WHAT**：reweighted p(s,z) 作为 pickled artifact，被 SE(3) diffusion 模型（STAR-MD / ConfRover）消费。两种消费模式：
- **Mode 1 — Rejection sampling**：模型生成 N 帧，按 p_ref(s,z)/p_proposal(s,z) 权重重采样
- **Mode 2 — Classifier guidance**：冻结模型，外加一个 s,z classifier head，在 reverse diffusion 每步 nudge 朝目标 s,z 移动

**CONSUMER**：Amin 的 STAR-MD-based SURF benchmark；外部 PLaTITO / ConfRover checkpoint。

**INTEGRATION HOOK**：包装器脚本，不改模型权重。

**LOAD-BEARING TEST**：
1. PP-conditioned ConfRover 在 TrpB WT 轨迹上的 O→C transition recall 相比 unconditional 明显提升
2. rejection-sampled p(s,z) 的 Wasserstein 距离到 MetaD 参考 &lt; 一个公认阈值

**10-WEEK V0 可行**：✅ rejection sampler + 在一个 open checkpoint 上 demo
**10-WEEK V0 不可行**：❌ 训练 classifier guidance（需 gradient access）

**不确定项**：
- 不确定 ConfRover 是否有 public checkpoint（STAR-MD review 说"no code/checkpoint release"）；若 Amin 的 fork 不能分享，这条 dead
- 不确定 SE(3) diffusion model 在 TrpB 规模（~39k atoms, ~400 residues）下的推理成本是否允许在 10 周做完
- 不确定 classifier guidance 在 SE(3) backbone 几何上的数学正确性（Riemannian 条件）

**AUDIT VERDICT (v1.1)**: **WEAKENED (MED-HIGH confidence)**. "Enhanced Diffusion Sampling for rare events" (arXiv 2602.16634), "Breaking the Timescale Barrier" (arXiv 2510.24979), training-free molecular guidance (arXiv 2409.07359) 已占 "energy-guided diffusion"。**通用能量引导死**。保留：**path-CV 专用的 (s,z) conditioning for STAR-MD/MDGen-class trajectory models** 还是空位。必须把 pitch 锁死在 "PATHMSD axis, not generic energy"。**建议吸收 3.4 TCR 作为它的 training-time 对偶**，合并成一个 "FES-consistent trajectory generation" 模块。

---

### 3.3 方法 C — Learned Bias Potential (LBP)

**WHAT**：用 NN 参数化 V_bias(s,z) 替代 MetaDynamics 手调 Gaussian hills。训练目标：使 reweighted trajectory 的 ∫p(s,z) 在 target region 上接近 uniform（well-tempered 等价）。输出：一个"学习出来的 MetaD 偏置势"，在新变体上微调后可加速 convergence。

**CONSUMER**：任何跑 TrpB 变体 MetaD 的人（Yu 的 workflow、你的 workflow、未来 RFD3 输出变体的 follow-up MD）。

**INTEGRATION HOOK**：PLUMED 的 PYTORCH_MODEL bias collective（PLUMED 2.9 支持）。

**LOAD-BEARING TEST**：
1. LBP 初始化的 MetaD 在 TrpB 变体上收敛时间相比标准 well-tempered MetaD 缩短 ≥ 30%
2. Final FES 在 block CI 内一致

**10-WEEK V0 可行**：⚠️ 存疑 —— 训练 LBP 需要已有 reference FES，这在 10 周内只能有 WT；测试变体会受时间挤压
**10-WEEK V0 不可行**：❌ 跨家族迁移

**不确定项**：
- 不确定 PLUMED 2.9 的 PYTORCH_MODEL 对 PATHMSD 的兼容性（FP-020 曾发现 conda 版 libplumedKernel 残缺；LBP 可能撞到类似问题）
- 不确定 NN-parameterized bias 的训练稳定性（reweight 可能出现数值爆炸）
- 不确定这个方向**是否已被 2025 文献吃掉** —— VES (Variationally Enhanced Sampling) + NN、OPES + NN 都是邻近空间。**这是外部 novelty 核查的最高优先项**
- 不确定 Anima 或 Arvind 会不会觉得"你在发明轮子"

**AUDIT VERDICT (v1.1)**: **DEAD (HIGH confidence)**. 杀手证据：
- NN-VES (Bonati, Zhang, Parrinello, PNAS 2019, arXiv 1904.01305) —— bias potential 本身就是一个 NN 用 variational loss 训练
- "Accelerated Sampling of Rare Events using a NN Bias Potential" (arXiv 2401.06936)
- Deep-TICA + OPES (arXiv 2410.18019) + mlcolvar 库已提供端到端 learned CV + adaptive bias
- Enhanced Sampling in the Age of ML (Chem Rev 2025) 综述已覆盖

**结论**：**drop 这条作为独立 novelty**。如果用到，cite + apply，不 claim。由 **方法 F (3.6)** 替换。

---

### 3.4 方法 D — TCR (Thermodynamic Consistency Regularizer)

**WHAT**：一个可微 loss 项，附加到任何生成式轨迹模型的训练：

```
L_TCR = KL( p_model(s,z) || p_MetaD(s,z) )
```

**不是** inference-time guidance（那是 PP-Prior），而是 **training-time inductive bias**。强迫模型在训练时就学会匹配 MetaD FES 的边缘分布。

**CONSUMER**：任何 retraining 或 finetuning SE(3) diffusion 的团队（Amin 的 STAR-MD fork、PLaTITO 的下一代）。

**INTEGRATION HOOK**：一行 loss 追加；需要模型暴露 s,z 可微投影。

**LOAD-BEARING TEST**：
1. TCR-trained model 在 held-out TrpB 变体上的 rare-state recall 明显优于无 TCR baseline
2. TCR 训练不伤原 validity 指标（trade-off 可控）

**10-WEEK V0 可行**：❌ 需要 retrain 一个 SE(3) diffusion model，你没有这个算力和工程栈
**10-WEEK V0 可行降级版本**：只把 TCR 写成 "paper proposal + 小合成体系（alanine dipeptide 或 toy tetrapeptide）demo"

**不确定项**：
- 不确定可微 s,z 投影（PATHMSD on backbone rigids）在 SE(3) 表示下的数值稳定性
- 不确定 "training-time FES matching" 是否已被 flow-matching + Boltzmann-generator 线 吃掉
- **不确定 v0 是否脱离 toy 级别**就做不出来

**AUDIT VERDICT (v1.1)**: **DEAD-ish (HIGH confidence)**. 杀手证据：
- Thermodynamic Interpolation (JCTC 2024, doi 10.1021/acs.jctc.4c01557)
- Energy-Based Coarse-Graining Flow (JCTC 2025, arXiv 2504.20940) — 显式最小化 reverse-KL to target Boltzmann
- Experiment-Directed Metadynamics (EDM) 已经做"shape MD to match target FES"
- Thermodynamically Informed Multimodal Learning (arXiv 2405.19386)

**结论**：作为独立 contribution 死。保留作 3.2 PP-Prior 的 training-time counterpart（合并命名："FES-consistent trajectory generation"）。由 **方法 G (3.7)** 替换为新的独立 ML 层候选。

---

### 3.5 方法 E — MNG (Memory Necessity Gate)

**WHAT**：lag-stratified Markov-vs-qMSM 诊断（D1 in 设计书）封装成一个 callable：
```
mng_score = MemoryNecessityGate(short_trajectory, observables)
if mng_score > threshold:
    trigger_metad_rescue(region)
```
用作 adaptive-sampling loop 的 runtime check。

**CONSUMER**：任何跑 DeepDriveMD-style adaptive sampling 的 workflow；或 Raswanth 的未来 closed-loop design 流程。

**INTEGRATION HOOK**：一个 Python 包 + CLI。

**LOAD-BEARING TEST**：
1. 在 TrpB WT 的 hold-out 轨迹片段上，MNG-triggered MetaD rescue 能恢复 surrogate 模型 miss 的 substates，代价 &lt; full-MetaD cost 的 20%
2. 不同 observables 子集下 MNG 结果一致

**10-WEEK V0 可行**：✅ 诊断 + 单 rescue episode demo
**10-WEEK V0 不可行**：❌ 嵌入完整 DeepDriveMD 循环（lab 目前不跑这个）

**不确定项**：
- 不确定 lab 里有没有 consumer —— DeepDriveMD 是 Arvind 早年工作，但 Slack 里当前 pipeline 没看到在跑
- 不确定 MNG 在 short trajectory 下的统计功效（block 数少会噪）
- 不确定是否和 Amin 的 xTB/CREST pathway verification tool 功能重叠

**AUDIT VERDICT (v1.1)**: **ALIVE (MED confidence, could be LOW if a 2026 NeurIPS/ICLR preprint surfaces)**. 5 个方法里**唯一一个独立可立得住的**。近邻：
- MEMnets (Nature Comput Sci 2025) 是 *CV discovery*，不是 runtime gate
- qMSM literature (Huang lab) 形式化非马尔可夫，不驱动 MetaD rescue
- Active-learning VAMPnets (JCTC 2023) 用 uncertainty 触发采样，不用 Markovianity-deficit

**剩下的独占地**：*lag-stratified Markov-vs-qMSM 不一致作为 runtime trigger，驱动 MetaD rescue in ML-surrogate adaptive-sampling loops*。

**战略地位**：应该是你 5 个 ML 层里的 **lead claim**，从原来的 #5 晋升 #1。即使其它 4 条全被吃，MNG 这条单独也能立得住。

---

### 3.6 方法 F — PLP-aware Reactive-Coordinate CV Extension（LBP 的替换）

**WHAT**：扩展现有 PATHMSD 把 PLP Schiff-base 几何（K82-Cε ↔ PLP-C4' 距离、Schiff-base 平面扭转、Dunathan-like 角）纳入 path 定义，产出 **"reactive PATHMSD"** —— 一个原生带化学态辨识力的 CV。封装成 PLUMED input template + Python post-processing，供变体 MetaD 直接调用。

**CONSUMER**：你自己做变体 MetaD、Yu 做 catalytic MD、Amin 做 benchmark 时的 TrpB task。

**INTEGRATION HOOK**：PLUMED input template + 一个 `reactive_path.py` 工具库。

**LOAD-BEARING TEST**：
1. Reactive PATHMSD 在 WT TrpB 上能把 O/PC/C 三态再分出 "catalytically competent C" vs "COMM-closed but Schiff-base misaligned" 两个子态（纯几何 path CV 做不到）
2. 对 Y301K 等已知变体，reactive-path FES 里子态 occupancy 能预测实验活性方向

**10-WEEK V0 可行**：✅ PLUMED template + 一轮 WT 验证（是现有 cartridge infra 的扩展）
**10-WEEK V0 不可行**：❌ 整套变体谱全跑

**不确定项**：
- 不确定 Schiff-base 扭转在 ff14SB + GAFF 下的数值稳定性
- 不确定 Reviewer 会不会说"你就是加了几个距离到 PATHMSD"
- 不确定是否和 B2（catalytic readiness descriptors）本质重复

**AUDIT VERDICT**: **不确定 — 未独立核查**。近邻 prior art（PLUMED PATH + chemistry CVs）常见但没有专门针对 PLP 的定式化。**novelty HIGH 的可能性中等**；最大风险是 Reviewer 认定"只是应用级改动"。

---

### 3.7 方法 G — Generative-Model Physics-Consistency Audit Layer（TCR 的替换）

**WHAT**：一个 `physics_audit(trajectory, reference_cartridge)` wrapper。输入：任何生成式轨迹模型（STAR-MD / ConfRover / MDGen / PLaTITO）的输出 N 帧。输出：一个结构化 audit 报告，含：
- Reweight-to-MetaD-FES 的 JSD / Wasserstein 差
- FDT closure residual（D2 from 设计书）
- Path-progress distribution matching score（A2 from 设计书）
- State-occupancy CI overlap
- Rare-state recall on cartridge-provided hard bins

**CONSUMER**：任何发表生成式 MD 模型的论文作者；Amin 的 SURF benchmark；Reviewer 判定"这个模型是不是 physics-consistent"。

**INTEGRATION HOOK**：pip-installable Python package，输入一个 `.pdb` trajectory + 一个 cartridge handle。

**LOAD-BEARING TEST**：
1. 能把已知"structurally valid but physics-inconsistent"的生成轨迹（比如 STAR-MD 公开输出 on TrpB / ATLAS 某蛋白）和 oracle MD 区分出来
2. 对 MNG 阳性的区域给出 actionable 诊断（"模型在 barrier region 明显低估 memory kernel"）

**10-WEEK V0 可行**：✅ 如果只实现 reweight + path-distribution + state-occupancy 三项
**10-WEEK V0 不可行**：❌ FDT closure 需要长 trajectory 和 correlation function，可能超出预算

**不确定项**：
- 不确定能否拿到 STAR-MD / ConfRover 的公开输出做 case study（review 说没 checkpoint release；需和 Amin 要他 fork 的输出）
- 不确定 Reviewer 会不会说"这不就是 Catalytic Path Fidelity Suite (E2) 的另一种包装"—— 的确是，但包装成 **pip-installable callable** vs **benchmark paper** 是定位不同

**AUDIT VERDICT**: **ALIVE (推理级，未独立核查)**。近邻是原设计书 E2 Catalytic Path Fidelity Suite，novelty 继承自其子 component（A2, B2, C2, D2）。**作为独立贡献相对单薄；作为 MNG (3.5) 的姊妹 callable tool 是合理组合**。

---

### 3.× 汇总表（AUDIT 后）

| 方法 | 独立 novelty | Lab 内 consumer | 10-wk 可交付 | 撞 Raswanth/Amin 风险 | 建议定位 |
|---|---|---|---|---|---|
| **E. MNG** | ALIVE | 无短期 | 中 | 低 | **LEAD** (#1) |
| 3.7 G. Physics Audit | ALIVE（推理） | Amin, 外部 | 中 | 低 | MNG 姊妹工具 |
| 3.6 F. Reactive PATHMSD | 不确定 | Yu, 你, Amin | 高 | 低 | Cartridge 的化学扩展 |
| B. PP-Prior (+ D 合并) | WEAKENED | Amin（条件） | 中 | 中 | "FES-consistent generation" submodule |
| A. CRR | WEAKENED | Raswanth（条件） | 高 | 高 | **降级** 为 projection metric，不 claim RL 新方法 |
| C. LBP | **DEAD** | — | — | — | **Drop**；用则 cite NN-VES |
| D. TCR | **DEAD-ish** | — | — | — | **Merge** 入 B |

**一句话重构**：你不是"5 个 ML product 的 shipping 者"，是"**1 个 cartridge** + 2 个 alive ML tool (MNG + Physics Audit) + 2 个 weakened 降级后的 callable (PP-Prior, CRR-projection) + 1 个 cartridge 化学扩展 (Reactive PATHMSD)"。

---

## 4. 五种下一步贡献方法（按 stakeholder 组织）

每条都对应一个 **具体可去的人** 和 **可以交给他 / 她的具体物件**，不是虚空的研究方向。

### 4.1 For Yu Zhang — Rare-state rescue on her MMPBSA winners

**WHAT 你给她**：拿她跑出来的 MMPBSA top-N 变体 → 各做一个短 MetaD（10-20 ns 探针）沿 TrpB path CV → 返回每个变体的"是否到达 PC/C basin"+ barrier height 估计。

**为什么找她**：她是你已确认的 teammate；Slack line 1123-1128 她已提议和你合作做 MetaD。风险最低、心理成本最低。

**LOAD-BEARING TEST**：她的 top-N 里，MetaD 诊断把"binding affinity 好但 kinetically dead"的假阳性挑出来 ≥ 1 个。

**不确定项**：
- 不确定她当前 top-N 有多少候选
- 不确定 10 ns 探针能否在现在的 TrpB 系统上产生有意义信号（WT 单 walker 都还没过 50 ns）

---

### 4.2 For Amin — Evaluation cartridge 喂给他的 STAR-MD SURF benchmark

**WHAT 你给他**：一个 `trpb_cartridge.py` package，暴露 API：
```python
from trpb_cartridge import load_reference_fes, project_to_path_cv, score_trajectory
p_ref = load_reference_fes("WT")  # 返回 p(s,z)
s, z = project_to_path_cv(predicted_trajectory)
report = score_trajectory(s, z, p_ref)  # 返回 JSD, state occupancy error, rare-state recall
```
加一份 "how to evaluate your STAR-MD fork on TrpB" 2 页说明。

**为什么找他**：他明说在给 SURF student 准备 STAR-MD dynamics benchmark (Slack 1023)；Arvind Jan-5 原话直接要"recover substates consistent with metadynamics ground truth"，但 Amin 目前只有 **架构**，没有 **ground truth**。你就是那块 ground truth。

**LOAD-BEARING TEST**：Amin 在他的 benchmark report 里把你的 cartridge 当成一个官方 evaluation module 调用（哪怕只是一个 task）。

**不确定项**：
- 不确定 Amin 是否愿意把 TrpB 设为 benchmark task（他可能选通用 ATLAS 蛋白以保通用性）
- 不确定 cartridge 的 API 设计会不会被他嫌"过于 TrpB-specific"

---

### 4.3 For Raswanth — CRR prototype，但只在内部验证通过后送

**WHAT 你给他**：一个 `catalytic_readiness_reward.py`，输入 RFD3/MPNN backbone 结构，输出 [0, 1] 分数。**先不申请接入 GRPO**；先给他一张表："我拿你已经生成的 100 个 backbones + Yu 的 MMPBSA ranking，CRR vs motif-RMSD 的 ROC-AUC 分别是 X 和 Y"。

**为什么找他，但谨慎**：Slack line 10 他明说 catalysis metrics 不在 pipeline 里；Arvind Jan-5 直接点名要多 level reward。你有合法 opening。**但他是 reward owner**，需要先证明价值再提议接入，不能空手去。

**LOAD-BEARING TEST**：CRR ROC-AUC 比 motif-RMSD 高 ≥ 0.1 在同样验证集上。

**不确定项**：
- 不确定 100 个 backbone + 30 个 MMPBSA 样本是否够统计功效
- 不确定 Raswanth 是不是更倾向自己做（他已经在 PLACER/EVB 上投入）
- 不确定他的 F0 当前基线有多强；可能已经很好，CRR 没有 lift

---

### 4.4 For Arvind — Electronic-effect + MetaD energy-scale 分析 on RFD3 outputs

**WHAT 你给他**：Slack line 201-205 他原话问"analyze the rfd3 results... take into account electronic effects on the step"，**无人交付**。你做：从 Yu 的 DFT theozyme 能量 + 你的 MetaD FES 能量尺度构建一张 "each RFD3 variant's predicted ΔG along the reaction coordinate" 图。用 xTB (Amin 的工具) + MetaD barrier 合成。

**为什么找他**：这是 PI 亲自点名但无人领的任务。如果你能哪怕部分回答，就能直接进 Arvind 的视野，不通过中间人。

**LOAD-BEARING TEST**：对 Yu 已经跑完的 Y301K 变体 + 至少 2 个对照变体，给出 ΔG(external aldimine → quinonoid) 的 MetaD 估计值，并和 DFT / 实验文献比较。

**不确定项**：
- **这条风险最高**：你目前 WT FES 都没收敛，谈电子效应会显得不自量力
- 不确定 xTB 对 PLP-Schiff-base 的参数化质量
- 不确定能否拿到 Yu 的 DFT 原始数据（她说了能共享，但没签字）

---

### 4.5 For Anima — 2-page technical note 直面她的"not concrete"否决

**WHAT 你给她**：一份 2 页的 technical brief，标题例：**"TrpB MetaD Cartridge: What STAR-MD, PLaTITO, and MDGen Structurally Cannot Evaluate, and Why This Matters for the Lab's RFD3 Pipeline."** 内容：
- 第 1 页：quadrant 图 x 轴 = structural validity, y 轴 = catalytic/kinetic fidelity。把 STAR-MD/PLaTITO/MDGen 放在右下。把你的 cartridge 放在右上（评价 y 轴的工具）。
- 第 2 页：列 3 个 load-bearing test（GRPO reward 提升、STAR-MD benchmark 的 TrpB task、Arvind Jan-5 substates）对应哪种模型配哪种 metric 才能回答。

**为什么找她**：她 Codex line 239-240 明说"not concrete enough"。这份 brief 是**直接针对她那句话的回答**。不是 pitching 架构，是 pitching evaluation gap。

**LOAD-BEARING TEST**：她不再说"not concrete"；具体表现是她问一个跟进问题而不是再次否决。

**不确定项**：
- 不确定她愿不愿意读一个 undergrad 写的 brief
- 不确定"quadrant 图 + evaluation gap"是否真的是她心里想要的 concreteness（她可能想要的是 architecture concreteness 而不是 evaluation concreteness）
- 不确定谁递给她合适（PI 链路 Arvind 还是直接？）

---

### 4.× 贡献方法汇总

| # | 找谁 | 给什么 | 门槛 | 风险 |
|---|---|---|---|---|
| 4.1 | Yu | rare-state rescue 诊断 | 低（她主动邀请） | 低 |
| 4.2 | Amin | cartridge API + docs | 中（需他接受） | 中 |
| 4.3 | Raswanth | CRR 预验证报告 | 中-高（需 Yu 数据 + 统计功效） | 中 |
| 4.4 | Arvind | 电子效应 + MetaD 合成分析 | **高**（需先出 WT FES） | 高 |
| 4.5 | Anima | 2-page brief | 低（纯写作） | 中（她可能仍不买账） |

**建议顺序**：4.1 → 4.2 → 4.5 → 4.3 → 4.4。先拿低风险高合作的 4.1/4.2 建立 "Zhenpeng has shippable artifacts" 声誉；然后 4.5 给 Anima；4.3/4.4 在 cartridge 成熟后再推。

---

## 5. 硬前置与 gate

无论走哪一条，下面这些必须先通过：

| Gate | 状态 | 阻塞物 |
|---|---|---|
| WT MetaD 收敛（Job 44008381 跑完 + sanity check PASS） | 🟡 进行中 | FP-030 O-end stall cause still open |
| 至少 1 个变体 FES | ⬜ 未开始 | 需先过 WT gate |
| Path CV 已验证可用 | ✅ 已过 | PATHMSD fix 后 driver 自检通过 |
| Repo 已清理 + cartridge directory layout | ⬜ 未开始 | 一堆 uncommitted changes |
| Yu 能共享 MMPBSA 数据 | ⬜ 未确认 | 需 1 次对话 |
| Amin 愿意把 TrpB 做 benchmark task | ⬜ 未确认 | 需 1 次对话 |

**Kill-switch**：如果 2026-05-01 前 WT FES 还没过 sanity check，所有 5×5 都不要推；focus 回到单 walker → 10-walker 升级。

---

## 6. 不确定清单（汇总 — 用户需要帮我确认的事）

1. ~~方法 C (LBP) 的 novelty~~ — **已查：DEAD**（NN-VES/Deep-TICA/OPES 已占）
2. ~~方法 B (PP-Prior) 的 novelty~~ — **已查：WEAKENED**（path-CV 专版仍活，通用能量引导死）
3. **Yu 的 MMPBSA 数据能否共享** —— 用户需要和 Yu 确认。
4. **Amin 的 STAR-MD fork 是否有 checkpoint 可对接** —— 用户需要和 Amin 确认。
5. **Raswanth F0 reward 的当前 ρ/ROC-AUC 基线** —— 用户需要查或问。
6. **Anima 具体要什么样的"concrete"** —— 是 evaluation gap 还是 architecture claim？用户可能需要试探。
7. **cartridge 是否需要包含反应态（external aldimine / quinonoid）而不仅是 O/PC/C** —— 用户需要向 Yu 确认化学相关性优先级。
8. **10 周 deadline 具体是什么日期** —— SURF 开始日？Caltech offer 决策日？还是自设？
9. **是否期望 v0 就公开 release** —— 还是先 lab-internal？
10. **和 Phase 1 复刻的优先级关系** —— cartridge 算 Phase 1 的延伸，还是 Phase 2 的启动？

---

## 7. 需要你（Zhenpeng）做的决策

**今天 / 这周需要决策**：
- [ ] 这个 "cartridge owner" 定位你认不认？（不认请指出哪里不对）
- [ ] 第 4 节的 5 个贡献路径，按 4.1 → 4.2 → 4.5 → 4.3 → 4.4 顺序可不可以？
- [ ] 硬前置 gate 你同意吗？尤其是 2026-05-01 kill-switch

**等 deep-research agent 返回后**：
- [ ] 如果方法 C (LBP) 被 2025 文献吃掉，你想补哪一条替换？
- [ ] 如果方法 B (PP-Prior) 已有前例，是否降级为"我们 TrpB-specialized"版？

**等你和 Yu / Amin 对谈后**：
- [ ] cartridge 的具体 schema（是否含反应态、变体数量、rare-state pack 标准）
- [ ] 时间盒（WT FES 收敛 deadline）

---

## 附录 A — 3-agent debate 主要引用

- Agent A (STAR-MD auditor) 原话："the live novelty directions are (a) state/CV-conditional diffusion, (b) PLP/substrate-aware parameter injection, and (c) learned bias potentials... Direction (c) is the sharpest."
- Agent B (Slack mapper) 原话（redundancy risk）："Amin is explicitly building a protein-dynamics benchmark using STAR-MD... Raswanth already explored 'cheap mechanistic signals for GRPO'..."
- Agent B 原话（真开口）："Arvind's redirect (Codex line 242–249) is the actual opening: sequence-conditioned memory kernel + MetaD-consistent substates across families. Nobody owns this."
- Agent C (strategist) 原话："CRR reuses the same MetaD infrastructure but ships a callable rather than a paper. That reframes the 10-week deliverable from 'benchmark artifact' to 'pipeline component Raswanth imports on Monday.'"

## 附录 B — 修订历史

- v1 (2026-04-22 上午, Claude): 初始草稿，pending novelty
- **v1.1 (2026-04-22 下午, Claude)**: 整合外部 novelty audit。关键变化：
  - 方法 C (LBP) 判定 DEAD，drop
  - 方法 D (TCR) 判定 DEAD-ish，merge 入 B
  - 方法 A (CRR) 降级为 projection metric
  - 方法 B (PP-Prior) 收窄到 path-CV specific
  - 方法 E (MNG) 从 #5 晋升 lead #1
  - 新增 方法 F (Reactive PATHMSD) 替换 C 的位置
  - 新增 方法 G (Physics Audit) 替换 D 独立性
  - **meta-结论**：cartridge 本身比任何单独 ML layer 更有 novelty
- v1.2 (待定)：用户反馈后修订

## 附录 C — Novelty Audit 引用链（2026-04-22 查）

**关键杀手引用（按方法分组）**：

方法 C (DEAD) 的杀手：
- NN-VES: Bonati, Zhang, Parrinello, PNAS 2019, arXiv 1904.01305
- Accelerated Sampling via NN Bias Potential: arXiv 2401.06936
- OPES + ML CVs with PLUMED: arXiv 2410.18019
- Enhanced Sampling in the Age of ML (Chem Rev 2025)
- mlcolvar library (Deep-TICA)

方法 D (DEAD-ish) 的杀手：
- Thermodynamic Interpolation, JCTC 2024, doi 10.1021/acs.jctc.4c01557
- Energy-Based Coarse-Graining Flow, JCTC 2025, arXiv 2504.20940
- Thermodynamically Informed Multimodal Learning, arXiv 2405.19386

方法 B (WEAKENED) 的杀手：
- Enhanced Diffusion Sampling for rare events, arXiv 2602.16634
- Breaking the Timescale Barrier, arXiv 2510.24979
- Training-Free Guidance for Discrete Diffusion / Molecular Generation, arXiv 2409.07359

方法 A (WEAKENED) 的杀手：
- PocketX: bioRxiv 2025.12.28.696754
- ResiDPO: arXiv 2506.00297
- ProteinZero: arXiv 2506.07459

方法 E (ALIVE) 的近邻（未杀死）：
- MEMnets, Nature Comput Sci 2025, s43588-025-00815-8 (CV 发现，不是 runtime gate)
- qMSM (Huang lab) 系列
- Active-learning VAMPnets, JCTC 2023

**注**：上述链接由 web-research agent 在 2026-04-22 生成；用户二次审阅时应抽查 2-3 条以防幻觉引用。
