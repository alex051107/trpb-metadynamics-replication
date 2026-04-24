# GroupMeeting 2026-04-24 — PPT 讲稿（17 张扩展版）

> **用法**: 对着念，每张 slide 对应 2-4 段话；口语，不要书面语
> **Meeting**: 1-on-1 with Yu Zhang · 2026-04-24 · ~28-32 min 讲 + 10-15 min Q&A
> **Deck arc**: 战略 framing（slide 1-3）→ D1 MetaD 进展（slide 4-10）→ 探索路线树（slide 11-12）→ ML audit + STAR-MD（slide 13-15）→ Next + kill-switch（slide 16-17）
> **核心 hook**: "我不是 MetaD replicator，我是 TrpB MetaD cartridge owner"
> **核心数字**: 500× 加速 / 27× λ / 5 月 1 号 kill-switch

---

## Slide 1 — Title: Week 7 分水岭，角色重定义
（约 1.5 分钟）

好，先从一句话开场——**这周其实是整个项目的一个分水岭**。不是因为数据上有什么惊天动地的新结果，而是因为**我把自己在这个 lab 里的角色重新想清楚了**。过去六周我一直把自己当成一个 "MetaD replicator"——复刻 Osuna 2019、把 FES 跑出来就算交差。这周我发现这个 framing 是错的。

正确的 framing 是这样的：**STAR-MD 已经把通用蛋白轨迹生成做满了**。字节跳动上个月发的那篇 arXiv 2602.02128，已经在 ATLAS benchmark 上做到 SOTA 的 long-horizon generation，微秒级轨迹都能跑出来。**在这个背景下，单纯复刻一个 MetaD FES 没有独立价值**——因为未来任何一个生成式模型都能产出轨迹。

那 TrpB 到底缺什么？**缺的是 mechanism-grounded evaluation**——缺一套能判断"这条轨迹有没有走到催化相关 substate、有没有保留 PLP 反应几何"的参考系。所以我这周把自己重定位成 **TrpB MetaD cartridge owner**——我做的不是轨迹，是那套能评价、筛选、纠偏 lab 其他人生成式 pipeline 的**参考 cartridge**。

这一张 slide 的底色就是这句话：**我不是在做 model，我在做 evaluation reference**。接下来整个 talk 都会围绕这条主线展开。

---

## Slide 2 — Cartridge = 7 件具体东西，不是抽象概念
（约 2 分钟）

我知道"cartridge"这个词听起来很抽象，所以 slide 2 我把它拆成**七件具体的东西**，你可以一件一件对。

**第一，path definition**——O/PC/C 三态的 PATHMSD 坐标，就是这周我花最大力气修的那个 path.pdb。**第二，reference FES**——WT 先做，然后扩 Aex1 和若干公开变体，每一张 FES 都要带 block-analysis CI，不是一张漂亮图。**第三，state masks**——O、PC、C、off-path、reactive-ready 五类 mask，可以直接 apply 到任何外部轨迹上做 state occupancy。**第四，block uncertainty**——每个 FES bin 带 confidence interval，这样下游才能做 hypothesis test。

**第五，rare-state frames**——从 reweighted HILLS 里导出的 hard examples，供生成模型做 training data 或 reward model 做 hard negatives。**第六，catalytic descriptors**——PLP-Lys82 Schiff-base 几何、Tyr301 方向、Glu104 proton accessibility、indole tunnel gating，这些机制级别的几何量。**第七，scorer API**——三个函数：`project_to_path()`、`score_trajectory()`、`state_occupancy()`，让别人 import 一个 Python 包就能用。

所以你看——**cartridge 不是"ground truth"这种空话，是七件可以 checkout 到硬盘上、可以 pip install 的东西**。这个清单就是接下来六周的 deliverable spec，不会再扩。

这里我想专门停一下强调语言边界。我**不说**"I'm building a new ML model"，**不说**"I own the TrpB ground truth"。我说的是 **"I'm building the mechanism-grounded reference cartridge"**、**"STAR-MD and my cartridge are upstream-downstream, not competitors"**。这两个说法的差别很大，Anima 对 architecture-first 的方向一直很警惕，所以我必须把 framing 锁在 evaluation layer 上。

---

## Slide 3 — 本周 3 个 deliverables（不是 5 个）
（约 2 分钟）

Slide 3 把这周的具体任务收敛到三件事——我专门强调"三件，不是五件"，因为上周我给你展示的是一个 5×5 的探索矩阵，今天我要告诉你为什么砍到 3 个。

**D1：Cartridge core 最小版本**。包括：path.pdb 和 Miguel 参数对齐、WT reference FES 定义、PLUMED input 彻底清理、state masks 草稿。Gate 是 **path.pdb 和 Miguel 版本一致，λ·MSD 落在 Branduardi tolerance 内**。这是今天 slide 4-10 讲的主要内容。

**D2：Trajectory scoring wrapper 的 API 草图**。注意——**API 草图，不是实现**。我只写 `replication/cartridge/API_DESIGN.md`：函数签名 + 输入输出 + 使用场景，不写代码。Gate 是文件 commit。这个周末应该能交。

**D3：一个 lab-facing demo**。二选一。Option A：给你做的 demo——"simple 1D CV 看不出来的 state 区分，PATHMSD cartridge 能给出更有意义的诊断"。Option B：给 Amin 的 demo——"STAR-MD 生成的 TrpB 轨迹被 cartridge 打分"。因为 Amin 目前没公开 STAR-MD 输出，所以**默认先做 Option A，你这边的 demo**。

那为什么不做 5 个，而是 3 个？因为 MNG、Reactive PATHMSD、Arvind 的电子效应——这三条**都是未来 claim，不是本周价值展现**。一个 undergrad 在 10 周内分散到 5 个方向只会做出 5 个半成品。3 个能做完的 deliverable 比 5 个 promise 值钱。这个 discipline 是这周学到的最重要的一课。

---

## Slide 4 — 上周到本周一：所有 MetaD-layer 调参失效
（约 1 分钟）

好，从 slide 4 开始进入 D1 技术细节。先快速过一下上周末到本周一是怎么卡住的。

上周五交给你的是 single-walker 50 ns 续跑，max s=3.494，卡在 O basin 出不去。我当时的诊断方向是"sigma 太小 + height 太低"。接下来做了三件事：**把 HEIGHT 从 0.628 加倍到 1.25 kJ/mol**——没用；**加 SIGMA floor 到 0.5 s-units**——没用；**加一道 wall 在 s=1.2**——walker 撞上 wall 之后在 wall 上来回震荡，它不是"不想走"，是"走不动"。

还有一个更说明问题的实验：我把 PC 中间态 MODEL8 插到 path 中段重新算 λ，**结果 λ 变化不到 5%**。换句话说——**无论怎么动 MetaD 参数、怎么重排 path 中段，整套 CV 的 sharpness 都改不了**。周一晚上结论就很明确：**所有 MetaD-layer 调参都没用，问题一定在下层**。下层就是 path 坐标本身。

---

## Slide 5 — Miguel contract：作者亲自确认的参数
（约 1.5 分钟）

然后周二 Miguel 回信了。Miguel 是 Osuna 2019 的第一作者，这封回信值得单独一张 slide，因为它是 contract-level 的确认。

Miguel 确认了两件事。**第一，FP-031**：我们之前 tutorial 里一直写 path CV 用的是 GEOM 模式——几何几何距离——但 Miguel 说 SI 里实际是 **DIFF 模式**，计算的是每对 snapshot 之间 CV 差分的平方和，不是三维 Cartesian 距离。这个更正对 λ 的数值尺度有直接影响。**第二，数值参数**——SIGMA、HEIGHT、BIASFACTOR 他都确认，和我们 SI 抄的一致。

**但是**——这是今天最关键的一个"但是"——**Miguel 没有发 PATH.pdb 文件给我们**。他只给参数，没给坐标。这句话请记住，因为它就是后面那个 silent bug 存活两个月的前提条件。如果他当时就发了 reference path，我直接 diff 一下就会看出 mismatch，这个 bug 活不过 24 小时。但他没发。所以 path 构建我们仍然在"自己造"的状态。

所以周二的状态是：**参数已 contract，坐标未 contract，问题只能在坐标**。

---

## Slide 6 — 排除法：A/B/C 全部被数据反驳
（约 2.5 分钟）

周三我系统性地把四个候选假设用排除法走了一遍。这张 slide 我讲慢一点，因为排除法本身就是这周最重要的方法论。

**假设 A：Gaussian height 不够**。反驳依据——HEIGHT 从 0.628 加到 1.25 kJ/mol，walker 的 stall 位置一模一样。A 被反驳。**假设 B：SIGMA floor 太低，Gaussian 塌成针尖**。反驳依据——我已经加了 SIGMA_MIN=0.3,0.005，HILLS 第 4 列读出来 σ 从来没低于 0.3。B 被反驳。**假设 C：Wall 设置有问题**。反驳依据——加了 wall 以后 walker 直接撞 wall，说明**不是 wall 挡着它，是它本身没有沿 path 移动的驱动力**。C 被反驳。

A、B、C 全被数据反驳掉之后，剩下的**只能是 D：path geometry 本身有问题**。这是一个经典的 "by elimination" 推理。

我想特别点出这件事的**方法论意义**。六周以来我一直在 MetaD 参数层面调参——每次失败就换一个参数继续调。这是典型的 "local optimization trap"：你在一个错误的 model 里 fine-tune，表面在进步，实际在浪费时间。**真正的跳出需要一次 assumption audit——把所有你默认为真的前提拿出来，按优先级一个一个证伪**。排除到 D 的时候我才第一次去怀疑 path 构建脚本本身。

这个教训会进 FP-034 的防范措施：**下一次 MetaD debug 先做 assumption audit，再改参数**。

---

## Slide 7 — FP-034：跨物种 residue number offset（核心）
（约 2 分钟）

好，slide 7 是本周技术上的核心。

我们的 path CV 是用两个参考结构插值的：**5DVZ 是 open state**，**4HPX 是 closed state**。但——**这两个是不同物种**。5DVZ 是 PfTrpB（Pyrococcus furiosus），4HPX 是 StTrpS（Salmonella typhimurium）。不同物种最麻烦的一件事是：**同一个序列位置在两个 PDB 里的 residue number 完全不同**。

看这张表。Pf 的 residue 56 对应 St 的 residue 53，Pf 的 residue 100 对应 St 的 residue 96——**整条 COMM domain 有一个系统性的 3-4 残基 offset**。如果你直接按 residue number 对齐 Cα——也就是你以为你在比"同一个残基的位移"，其实你比的是"Pf 的 Phe95 vs St 的 Tyr92"——这种情况下 per-atom MSD 会被人为放大到完全不合理的水平。

**最打脸的是**：我们仓库里早就有一个脚本叫 `generate_path_cv.py`，**它调用了 Needleman-Wunsch sequence alignment**，**它输出了一张 alignment 表**。但是——**下游的坐标提取根本没用这张表**，用的是 raw residue number。**alignment 被算出来了然后被扔掉了**。这是一个 silent bug，活了两个月。

为什么 silent？因为它不报错。Kabsch 还是会跑，MSD 还是会出数字，λ 还是会算出来——只不过这些数字**全都是错的**。

---

## Slide 8 — NW 修复：四个数字并排
（约 2.5 分钟）

修复很简单：把 Needleman-Wunsch 输出真正 wire 到坐标提取里，让 Pf residue 100 映射到 St residue 96 这种对应被真正使用。修复后跑出来的四个数字我希望你记住。

**第一，sequence identity**：修复前 6.2%，修复后 **59.0%**。6.2% 是什么意思——我们之前对齐的 112 对 Cα 里只有 7 个真的是同源残基，剩下 105 个是在瞎对。59% 才是 TrpB 保守 COMM domain 的真实同源水平。

**第二，端点 RMSD**：**10.89 Å → 2.12 Å**。10.89 Å 对于 COMM 的 O→C 运动来说大到荒谬——COMM 整体位移文献上只有 4-5 Å。2.12 Å 才合理。**这个数字 6 周前就是 red flag**，但我们一直归因于"flexible loop noise"，没去 audit。FP-034 现在加了 assertion：**端点 RMSD > 4 Å 必须报警**。

**第三，MSD_adj**（相邻帧 per-atom MSD）：**0.606 nm² → 0.023 nm²**，缩小 26 倍。**第四，λ**：**3.80 → 100.79 nm⁻²**。λ 上升 27 倍不是因为公式变了，是 MSD_adj 分母变小——λ = 2.3 / MSD_adj。

然后两个独立 self-consistency check：**Branduardi kernel weight check**——λ·MSD_adj 应该落在 2.3 附近，现在是 **2.32**，完全对。**driver self-projection**——把 15 帧 reference 每一帧扔回 PLUMED driver，算出来 s 应该是 1、2、3...15——跑出来**完全 monotonic**。Codex 独立复核了整套修复，**7 项 check 里 7 项 PASS**。

---

## Slide 9 — 生物学 sanity check
（约 1.5 分钟）

修完之后我做的第一件事**不是跑 pilot，而是做生物学 sanity check**——拿三个已知结构往修好的 path 上投影，看它们落在哪里。

**5DVZ（open）落在 s=1.1**——path 起点附近，合理。**4HPX（closed）落在 s=14.9**——path 终点附近，合理。**5DW0 和 5DW3 是已知的 PC（partially closed）中间态，落在 s=5.4 和 s=8.1**——干净地落在 path 中段，刚好是 O→C 转换应该发生的位置。这是一个强生物学验证。

这里我要坦白一件事——上周我给你看过一份叫 **path_piecewise audit** 的分析，结论是"MODEL8 落在 s=4 附近，所以 PC 被 path 误分类成 O 态"。**那份 audit 结论是错的**。错在哪——错在它是在 naive path 上做的判断，而 naive path 的 s 坐标本身就被 residue offset bug 污染。这是 FP-034 的下游污染之一，我已经把那份 audit 标记为 "superseded by FP-034 sequence-aligned path"。

教训——**任何基于错误 CV 的下游结论都要重审**。这也影响我后面要讲的 ML audit 部分。

---

## Slide 10 — Pilot 结果：500× 加速
（约 2 分钟）

OK，最后上数据。这是本周最兴奋的一张 slide。

我用**完全相同的 start.gro**——就是那个 500 ns 经典 MD 的终态——分别在 naive path 和 corrected path 上跑短 pilot。**关键对比**：**同一个 start.gro，在 naive path 上 s=1，在 corrected path 上 s=7**。这一句话信息量很大——它的意思是，我们那个 500 ns 经典 MD 的终态**根本从来不在 O basin**，它一直在 PC region 附近。过去五周我们以为 walker "卡在 O basin 出不去"，实际上 walker 从来没在 O basin 里——我们**只是被错误的 CV 误标注了**。

第二个对比是 pilot 本身的探索速度：**110 ps 短 pilot 在 corrected path 上就跑到 max s=8.94**；**naive path 跑了 7.7 ns 才到 max s=1.75**。同样时间单位换算，**大概 500 倍的加速**。这就是今天开场的那个 500×。

但我**不 overstate**。Pilot 只跑了 110 ps，数据窗口很短。正式 pilot 正在 Longleaf 上跑，gate 设 **max_s > 12**——24 小时内能越过 12 就说明 CV sharpness 彻底解决，可以进 Phase 2 10-walker primary production；越不过我们再 debate。

---

## Slide 11 — 探索路线树：为什么砍到 3 个方向
（约 2 分钟）

Slide 11 开始切换话题——从 D1 MetaD 技术进展切到战略层。这张 slide 展示的是**我探索过的 5 个 ML 扩展方向**，以及为什么最后砍到 3 个。

本周早些时候我和另外几个 AI agent 做了一轮 debate，列出 5 个把 cartridge 变成 ML layer 的候选方向：**方法 A：CatalyticReadinessReward (CRR)**——给 Raswanth 的 GRPO 加一个 reward head；**方法 B：Path-Progress Prior (PP-Prior)**——给 STAR-MD 做 (s,z) conditioning；**方法 C：Learned Bias Potential (LBP)**——用 NN 学 MetaD 的 bias；**方法 D：Thermodynamic Consistency Regularizer (TCR)**——训练时加 FES matching loss；**方法 E：Memory Necessity Gate (MNG)**——Markov vs qMSM 不一致作为 MetaD rescue trigger。

这 5 条看起来都 reasonable，但我做了一轮外部文献 audit（查了 2024-2026 arXiv / Nature / JCTC / PNAS / bioRxiv）之后，大部分被 kill 掉了。这是下一张 slide 要讲的。

核心 takeaway——**先 audit 再承诺**。六周前我差点把 LBP 当主线去做，如果没这轮 audit 就直接上了，会在一个已经死透的 space 里浪费两个月。

---

## Slide 12 — 5 方向 audit verdict：只有 1 条独立 ALIVE
（约 2 分钟）

OK，audit 结果——**5 条里 1 条 DEAD、1 条 DEAD-ish、2 条 WEAKENED、只有 1 条独立 ALIVE**。

**方法 C (LBP) — DEAD**。杀手：NN-VES 2019、Deep-TICA、mlcolvar、OPES + NN bias——这个 space 已经被 Bonati / Parrinello / Chem Rev 2025 综述 完全占住。drop 掉作为独立 novelty，用到就 cite 就好。**方法 D (TCR) — DEAD-ish**。杀手：Thermodynamic Interpolation JCTC 2024、Energy-Based CG Flow JCTC 2025、Experiment-Directed Metadynamics——training-time FES matching 已经饱和。Merge 进方法 B 作为 training-time 对偶，不独立 claim。

**方法 A (CRR) — WEAKENED**。杀手：PocketX 2025、ResiDPO 2506、ProteinZero 2506——"GRPO + reward on protein design" 已经被做了。保留的价值不是 RL 框架，是把它降级成"projection metric"——把候选几何投到 MetaD-validated 催化 basin。**方法 B (PP-Prior) — WEAKENED**。杀手：Enhanced Diffusion Sampling 2602.16634、training-free guidance 2409.07359——通用能量引导饱和。但**path-CV 专版的 (s,z) conditioning for STAR-MD/MDGen-class 还是空位**，必须把 pitch 锁死在 "PATHMSD axis, not generic energy"。

**方法 E (MNG) — ALIVE**。近邻：MEMnets Nature Comput Sci 2025 是 **CV discovery**、qMSM 形式化非马尔可夫不驱动 rescue、Active-learning VAMPnets 用 uncertainty 不用 Markovianity-deficit。**独占地是**：lag-stratified Markov-vs-qMSM 不一致作为 runtime trigger，驱动 MetaD rescue。**5 条里唯一独立可立的**。

**meta 结论**——外部 audit agent 原话："The cartridge itself is likely more novel than any individual ML layer built on top." 翻译过来：**cartridge 本身是主产品，ML layer 都是 optional extension**。这就回到 slide 1 的定位——**我不是 ML 方法论发明者，我是 evaluation reference owner**。

---

## Slide 13 — Audit 方法论：为什么 audit 比执行更重要
（约 2 分钟）

Slide 13 专门讲 audit 本身的价值——这不是 slide 12 的重复，这是讲**方法论上为什么 audit 这一步比执行更重要**。

对 undergraduate 来说最容易犯的错是什么——**看到一个 idea 觉得 reasonable 就开始写代码**。六周前我就会这样，看到 LBP 觉得 "NN 学 bias potential 听起来很酷" 就直接 setup PLUMED PYTORCH_MODEL 开始训。如果真的这么做了，**两周之后某个 reviewer 会指出 NN-VES 已经做过了，整个工作归零**。

audit 的核心不是"查文献看谁做过"，是**主动 invert 假设**——你要**主动替 reviewer 想"这个 idea 会被什么 2024-2026 的工作 kill"**，然后去查。这比 positive search 难得多，因为 positive search 是"找支持我的证据"，invert search 是"找能杀死我的证据"。

这次 audit 我查了三层：**第一层，arXiv 关键词 search**（NN bias potential, FES matching, path-CV conditioning）；**第二层，close-cousin paper 检查**（MEMnets、mlcolvar、Deep-TICA、qMSM 系列）；**第三层，review paper 覆盖性**（Enhanced Sampling in the Age of ML, Chem Rev 2025）。这三层一起才能保证不 miss 掉 killer prior art。

这个方法论后面整个 lab 都能用——**任何 ML 方向的 proposal，花 1 天做 audit 比花 1 个月做 failed implementation 值钱得多**。

---

## Slide 14 — STAR-MD 位置与 cartridge 互补性
（约 1.5 分钟）

Slide 14 单独讲 STAR-MD，因为这个 context 很关键，你需要理解为什么我 framing 成 "upstream-downstream"。

**STAR-MD 是什么**：字节跳动 Seed 团队 2026-02-12 发的 arXiv 2602.02128，作者 Nima Shoghi、Yuning Shen、Quanquan Gu。它是一个 SE(3)-equivariant causal diffusion transformer，在 ATLAS benchmark 上做 long-horizon protein dynamics generation，**微秒级轨迹，SOTA structural validity**。

**STAR-MD 做满的是什么**：generic protein dynamics generation——给一个初始构象，生成物理 plausible 的 long-horizon 轨迹。这件事以前没人做到微秒级，现在做到了。**STAR-MD 没做的是什么**：enzyme-specific catalytic evaluation。STAR-MD 不知道什么叫 PLP Schiff-base、不知道 TrpB COMM domain 的 O/PC/C 意味着什么、不知道一条轨迹有没有访问 catalytic substates。它只保证 structural validity，不保证 mechanistic validity。

**这就是 cartridge 的 niche**——它不和 STAR-MD 竞争，它**在 STAR-MD 下游做 evaluation**。流程可以是：STAR-MD 生成轨迹 → cartridge.score_trajectory() → 返回 (state occupancy error, rare-state recall, path-distribution JSD)。这是一个**纯 additive 的关系**，不是 zero-sum 的。

所以对 Amin 我会这样说——"你的 SURF student benchmark 需要一个 enzyme-specific task，TrpB 可以当 adversarial case"。对 Yu 我会说——"simple 1D/2D CVs 漏掉的 state 区分，PATHMSD cartridge 能给更有意义的诊断"。对 Anima 我不主动 pitch，等 WT FES 跑完再说。

---

## Slide 15 — 对不同 stakeholder 的 canonical pitch
（约 2.5 分钟）

OK，slide 15 把上一张的思路展开成**每一个 stakeholder 的 canonical 一句话**。这些都是 memo v1.2 锁死的，我逐字念出来因为措辞很重要。

**对 Yu（你）**：*"I saw your OpenMM MetaD update. I'm working on the PLUMED/PATHMSD side and recently got the original-author PLUMED input for the Osuna TrpB MetaD protocol. I'm still reconciling the PATH.pdb construction, but I think this could be directly useful for testing reaction-coordinate choices beyond simple 1D/2D CVs."* 核心是**"reconciling"**而不是"completed"——诚实表达还在对齐阶段，但已经可用。

**对 Amin**：*"I'm building a TrpB MetaD cartridge that can score generated trajectories by projecting them onto a mechanism-grounded PATHMSD/FES reference. If your STAR-MD/ConfRover benchmark needs an enzyme-specific task, TrpB could be a useful adversarial case."* 核心是**"adversarial case"**——不 claim TrpB 是 benchmark 主任务，只 claim 它能揭示 generic model 的 failure mode。

**对 Raswanth（等他有 designs 之后，不主动 pitch）**：*"I can help evaluate whether top designs are dynamically plausible along the TrpB conformational coordinate, not just geometrically valid."* 核心是**"dynamically plausible along the TrpB coordinate"**——不说我给你新 reward，说我给你 evaluation hook。

**对 Arvind（等 WT baseline 稳后再说）**：*"I'm turning the TrpB MetaD replication into a reusable evaluation cartridge for ML-generated enzyme dynamics and design candidates."* 核心是**"reusable"**——单次 replication 没价值，reusable cartridge 才有 reputational value。

**对 Anima（最谨慎）**：**不主动 pitch。等 WT FES 收敛 + kill-switch 过关 + cartridge API 有 draft 之后，再通过 Arvind 或 Yu 中转**。因为 Anima 的偏好是 problem definition + integration hygiene，不是 architecture claim；空手去会被再次判为 "not concrete"。

这 5 个 pitch 的 meta pattern 是：**每一句都是 evaluation framing，没有一句是 model-building framing**。这是 slide 1 那个角色重定位的 concrete execution。

---

## Slide 16 — Next steps：明天到 5 月 1 号
（约 1 分钟）

Slide 16 把接下来 7 天讲清楚。

**明天早上**：读 Longleaf pilot 的 max_s，按 gate 判 Phase 2。max_s > 12 进 Phase 2，max_s < 12 回来 debate 原因。**这周末**：写完 `replication/cartridge/API_DESIGN.md`（D2），函数签名 + 输入输出 + 使用场景，提交 commit。**下周**：如果 Phase 2 开跑，10-walker starting points 从 500 ns 经典 MD 里眼看挑 10 个 diverse snapshot（按你 2026-04-09 的指示，不 strided）。**4 月 30 号前**：WT FES 第一版出来，和 JACS 2019 Fig 2a 对比。

5 月 1 号往后的规划——如果 WT 收敛，开始第一个变体 FES（E104P 或 Y301K，看你 DFT data 给谁优先）；如果 cartridge API 稳定，开始写 Yu demo notebook (D3 Option A)。但这些是 stretch，不是 commitment。

---

## Slide 17 — Kill-switch 和 Q&A 过渡
（约 1.5 分钟）

最后一张，slide 17，我要专门强调一件事——**kill-switch**。

**硬规则**：**2026-05-01 之前，如果 WT FES 还过不了 sanity check，5 条 ML 扩展方向全部暂缓**。sanity check 的定义我已经锁死：FES 在 path.pdb 坐标系下 converge，block-analysis CI 不发散，state occupancy 落在"O:PC:C ≈ 实验推测合理比例"的区间。过不了这个 check，cartridge 本身的 reference layer 就不成立，上面盖什么 ML 都是沙上建塔。

kill-switch 触发后的 minimum viable deliverable 是什么——**回到 single-walker FES + 1 个公开变体对照**，ML-layer 全砍，pitch 降级为"I replicated Osuna 2019 and documented the failure mode of path-CV construction across species"。这是最差情况的 fallback，不体面，但**可交差**。

我专门把这个 kill-switch 写出来是因为——**一个 undergrad 最容易犯的错是 scope creep 加 sunken cost**。"我已经跑了 500 ns 了，不能停"、"我已经做了 5 方向 audit 了，不能不用"——这些心理都会让人错过 cut-loss 的正确时机。**disciplined stop rule 是我送给自己的防御机制**。

好，我就讲到这里。先开 Q&A——我估计你至少有 7-8 个技术问题 + 几个战略问题，我都准备了。

---

## 附录 — Q&A 急救包（技术 + 战略 + stakeholder hypotheticals）

### 技术层

| Yu 的问题 | 我的准备回答 |
|----------|-------------|
| "Branduardi kernel weight 在 1.26× 下只 0.16，是不是 too loose？" | Branduardi 建议 target 0.10，tolerance 0.05-0.25，我们 0.16 落在 tolerance 内。更有说服力的是 driver self-projection——15 帧 reference 扔回去 s 值出 1、2、3...15 完全 monotonic，kernel discrimination 够。 |
| "既然 generate_path_cv.py 算了 sequence alignment，为什么下游不用？" | 坦白这是 silent bug。alignment 算了但下游坐标提取硬编码用 residue.number 不是 alignment_table[residue.number]。FP-034 第 5 条防范：**坐标提取必须接收 alignment table 作为参数**，并 assert "每个 residue number 必须在 alignment table 里存在"。 |
| "10-walker starting points 都在 s=7 附近，会不会 correlated？" | 从 500 ns 经典 MD 挑 snapshot，mean s≈7，但 thermal fluctuation 让实际 s 分布 span 5-10；z(R) 方向 spread 再去相关一次。如果跑出来 correlation 太高，从更 diverse 的 500 ns 窗口再挑。 |
| "FP-031 GEOM→DIFF 怎么影响 λ？" | DIFF 是 CV 空间差分，scale 和 GEOM 差系数。Miguel 确认 SI 的 0.15 kcal/mol HEIGHT 和 10 BIASFACTOR 都是 DIFF assumption 下。切 DIFF 后 λ 数值尺度没因为 mode 跳，主要 27× 来自 residue alignment 修复。 |
| "为什么 naive path 上 start.gro 显示 s=1？" | naive path 把 residue offset 当成"真位移"，所以和 5DVZ 结构接近的 snapshot 都被误判离起点近。corrected path 去掉 offset 后才看到真实 s=7。 |
| "corrected path 会不会只是 reshift 了坐标，物理意义没变？" | 不是 reshift。reshift 会保持 MSD 不变。我们 MSD_adj 从 0.606 降到 0.023 nm²，geometry 本身变了——之前 MSD 里混了大量"跨物种 residue mismatch 假位移"，修掉后只剩真的 conformational change。 |
| "FES gate 为什么 max_s > 12？" | path 范围 1-15，12 对应已经越过 PC middle 进入 closed vicinity。max_s > 12 意味着 pilot sample 到 path 后段，是 Phase 2 能 converge 的最低前提。 |
| "bug 存在两个月，有没有更早 warning signal 被 ignore？" | 有。端点 RMSD 10.89 Å 本来就是 red flag——COMM 的 O→C 位移文献只有 4-5 Å。一直归因为 "flexible loop noise"。FP-034 补 assertion：**端点 RMSD > 4 Å 必须报警**。 |

### 战略层（stakeholder hypotheticals — Yu 可能替其他人问）

| 假设问题 | 我的准备回答 |
|----------|-------------|
| "如果 STAR-MD checkpoint 不 release 怎么办？" | Cartridge 本身就是主产品，ML-layer 都是 optional extension。STAR-MD 不 release 对 D2 API 草图和 D3 Yu demo 都没影响——两个都不依赖外部 checkpoint。受影响的只有"Amin demo" 这条 Option B 线，我会回到 Option A。 |
| "你的 cartridge 和 Yu 的 MMPBSA ranking 怎么衔接？" | Cartridge 的 state masks + rare-state frames 可以作为**MMPBSA winners 的 rescue 触发条件**——如果一个 candidate 的 MMPBSA score 好但 cartridge 判定它只 sample 到 O basin（从未进 PC/C），就触发 short MetaD 探针重打分。这让 MMPBSA 变成 geometry 初筛、cartridge 变成 dynamics 终筛，不是竞争。 |
| "MNG 是唯一 ALIVE 的 ML 方向，但它需要 qMSM——你做得了吗？" | 诚实答：**qMSM 我没跑过**。这是接下来一个月的关键技术风险。mitigation 是——MNG 不在本周 3 个 deliverable 里，我有时间学。学习路径：Huang lab 的 qMSM 教程 + PyEMMA/Deeptime 现成实现。如果 1 个月后我判断学不动，MNG 我 drop 给未来的 grad student。 |
| "5 月 1 号 kill-switch 触发后怎么办？" | 回到 single-walker FES + 1 个公开变体对照作为最小可交付，ML-layer 全砍。pitch 降级为"documented the failure mode of cross-species path-CV construction"——不光彩但可交差。关键是 kill-switch 触发了我会**立刻**转，不会 sunken-cost 再续 2 周。 |
| "字节跳动 STAR-MD 新出来，你的工作会不会立刻过时？" | 不会。STAR-MD 不做 enzyme-specific catalytic evaluation；它保证 structural validity，不保证 mechanistic validity。Cartridge 正是填这个空——它不和 STAR-MD 竞争，它**在 STAR-MD 下游**。两者 upstream-downstream 关系，STAR-MD 越强，cartridge 越有用。 |
| "你觉得 Anima 会买账吗？" | 现阶段**不主动 pitch Anima**。她的偏好是 problem definition + integration hygiene + reward correctness，不是 architecture。空手去会被判 "not concrete"。等 WT FES 收敛 + API draft 稳 + Yu/Amin 有一个 adopt，再通过 Arvind 中转给她一份 2 页 technical brief。直接 pitch 不划算。 |
| "为什么不直接做 MNG 当 lead claim？" | 两个原因。第一，MNG 虽然 ALIVE 但 10-week V0 只能做 single rescue episode demo，不够成为 independent contribution；作为 cartridge 的 plug-in 才稳。第二，MNG 依赖 qMSM 学习曲线，本科生 10 周 timeline 风险太高。先 cartridge，MNG 作为下一季度扩展。 |

---

**讲稿结束** — 总时长估算 ~30 分钟（Slide 1-17）+ 10-15 分钟 Q&A
