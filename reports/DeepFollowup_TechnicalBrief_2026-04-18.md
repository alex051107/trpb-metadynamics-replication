# Deep Follow-up 技术文稿

> **文档定位**: 这是对 `chatgpt_pro问题回答.docx` 的第二轮“深入展开版”，不是新 summary。
> 目标读者是我（Zhenpeng）自己。读完后，我应该能：
> 1. 讲清楚前一轮 5 个 ideas 各自到底是什么；
> 2. 解释它们为什么和 TrpB / MetaDynamics / STAR-MD 有关；
> 3. 判断哪些 ideas 适合我 before summer 主动提给 Amin；
> 4. 带着更像“技术判断”而不是“模糊求助”的姿态去开会。
>
> **写作原则**:
> - 科学上严谨，写作上诚实。
> - 只把材料直接支持的内容写成 `事实`。
> - 基于材料的项目判断写成 `推断/建议`。
> - 现在无法锁死的内容写成 `未知`。
> - 优先解释“为什么”，其次才是“怎么做”。

---

## 目录

1. [先给结论](#先给结论)
2. [共同事实基线](#共同事实基线)
3. [Idea 1: TrpB MetaDynamics Benchmark Pack](#idea-1-trpb-metadynamics-benchmark-pack)
4. [Idea 2: Multi-start Rare-State Evaluation](#idea-2-multi-start-rare-state-evaluation)
5. [Idea 3: Mutation-conditioned TrpB Mini-Dataset](#idea-3-mutation-conditioned-trpb-mini-dataset)
6. [Idea 4: Reward Sanity Study](#idea-4-reward-sanity-study)
7. [Idea 5: TrpB-specific Extension of Amin's Benchmark](#idea-5-trpb-specific-extension-of-amins-benchmark)
8. [横向比较](#横向比较)
9. [最稳妥的 meeting framing](#最稳妥的-meeting-framing)
10. [第三轮追问树](#第三轮追问树)

---

## 先给结论

1. `事实`
   只看 Slack history，你被明确放进去的位置是 `proposal + metadynamics + method benchmark`，不是 model owner。
2. `事实`
   STAR-MD 确实会削弱“做一个 generic long-horizon coarse-grained protein dynamics model”这层 story，但并没有把 TrpB-specific、ligand-aware、metadynamics-grounded 的任务做完。
3. `推断/建议`
   所以现在最强的打法不是“我要去发明一个新 architecture”，而是把你手上的 chemistry / MetaDynamics 线升级成 ML 侧能直接消费的 benchmark、evaluation、或 data asset。
4. `推断/建议`
   5 个 ideas 里，最值得优先深挖的是：
   - `Idea 1: Benchmark Pack`
   - `Idea 2: Rare-State Evaluation`
   - `Idea 4: Reward Sanity Study`
5. `推断/建议`
   如果你马上要和 Amin 开会，最稳的 framing 不是“我该不该改模型”，而是：
   `我现在最可能贡献的，是把 MetaDynamics 这条线变成一个 first usable benchmark / evaluation asset；如果你更希望我接 model-side task，请帮我把 scope 明确到一个可执行的交付物。`

---

## 共同事实基线

### A. 项目主线和支线

- `事实`
  Slack 主线一直是 TrpB design loop：RFD3 / sequence generation / docking / MD / reward / filtering。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:1) 和 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:12)。
- `事实`
  protein dynamics 是后面长出来的 SURF 支线，Amin 明确说过自己做了 `protein dynamic benchmark for the SURF student`。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:1022)。

### B. 你的角色

- `事实`
  Yu 明确说你愿意帮 proposal 和 metadynamics。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:817)。
- `事实`
  更具体的说法是：Yu 和你一起做 metadynamics setup，探索 OpenMM/openmm-plumed 是否能复现 Osuna 式结果，作为 method benchmark。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:1123)。
- `推断/建议`
  这意味着你最自然的升级方向不是“直接拥有模型”，而是 `benchmark / chemistry-to-ML bridge`。

### C. STAR-MD 的边界

- `事实`
  STAR-MD 的主任务是 generic long-horizon protein dynamics generation，主 benchmark 是 ATLAS，主卖点是 joint spatio-temporal attention、microsecond-scale rollout、Mori-Zwanzig 对 coarse-graining + temporal history 的理论支撑。
  见 [STAR-MD_arXiv2602.02128.pdf](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/papers/STAR-MD_arXiv2602.02128.pdf:1)。
- `事实`
  它自己的 limitation 里把 `protein complexes` 和 `small-molecule interactions` 写成 future work。
  见 [STAR-MD_arXiv2602.02128.pdf](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/papers/STAR-MD_arXiv2602.02128.pdf:11)。
- `推断/建议`
  所以它并没有把 `TrpB mutant + ligand/cofactor + metadynamics-ground-truth` 这类问题空间彻底吃掉。

---

## Idea 1: TrpB MetaDynamics Benchmark Pack

### 1. 一层人话

`推断/建议`
这个 idea 的意思不是“继续跑 MetaD”，而是把你跑出来的东西变成一套别人能直接用的标准资产。

如果用最朴素的话说：
- 现在你的工作像是一堆 chemistry 结果和复现过程；
- Benchmark Pack 的目标，是把它整理成“可复现、可比较、可给 ML 使用”的完整包。

它至少应包含：
- 可重复的输入和参数说明
- FES / FEL 结果
- O / PC / C 这类状态定义
- 代表性结构 seeds
- 对 ML 友好的 metadata / schema

### 2. 为什么它和我们项目强相关

- `事实`
  你们项目已经把 MetaDynamics 放在 generative TrpB pipeline 的 physics layer 里。
  见 [PROTOCOL.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/PROTOCOL.md:10)。
- `事实`
  4 月 9 日的组会脚本把 FES 明确写成下游输入，服务 dynamics benchmark、reward、variant screening。
  见 [GroupMeeting_2026-04-09_Script_Bilingual.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/GroupMeeting_2026-04-09_Script_Bilingual.md:21)。
- `推断/建议`
  这说明 MetaDynamics 不是一个孤立的 side quest。它本来就应该成为后面 ML 线可消费的 ground truth。

### 3. 为什么 STAR-MD 没做完这件事

- `事实`
  STAR-MD 的 benchmark 不是 TrpB-specific metadynamics benchmark，它没有给你 O/PC/C basins、productive closure labels、path-CV minima 这种资产。
- `事实`
  内部 review 明确把 `metadynamics-ground-truth benchmarking` 视为剩余空间。
  见 [round4_synthesis.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/papers/reviews/starmd_team_review_2026-04-17/round4_synthesis.md:132)。
- `推断/建议`
  所以 Benchmark Pack 的意义，不是跟 STAR-MD 比谁模型强，而是补它缺少的任务真值层。

### 4. 工作流

`推断/建议`

1. 冻结最小 scope
   - 输入：当前复现状态、已有脚本、当前 blockers
   - 输出：v0 benchmark 的边界定义
   - 为什么必须有：否则会无限扩成“完美复现整篇 Osuna paper”

2. 先打通单体系/单状态链路
   - 输入：path CV、single-walker / available runs
   - 输出：第一版可用 FES + state separation
   - 为什么必须有：没有可信的第一版，后面的 state labels 都会漂

3. 导出标准资产
   - 输入：trajectory、HILLS/COLVAR、FES
   - 输出：FES 文件、state labels、representative seeds、README
   - 为什么必须有：ML 侧不能直接消费一堆原始 trajectory

4. 做 ML-facing schema
   - 输入：上述资产
   - 输出：统一字段、文件命名、使用说明
   - 为什么必须有：否则 asset 只对你自己可用

### 5. 核心术语

- `path CV`
  - 最简单定义：沿参考路径前进了多少、偏离路径多远
  - 在这里：用 `s(R)` 和 `z(R)` 描述 TrpB COMM domain 的构象位置
  - 为什么重要：MetaD bias 是加在这两个量上的
  - 不是：普通 RMSD 或单一距离

- `FES / FEL`
  - 最简单定义：自由能地形图
  - 在这里：不是一条轨迹，而是全局构象空间的地图
  - 为什么重要：它比“某一帧长什么样”更接近功能相关 truth

- `state label`
  - 最简单定义：给一个结构打上它属于哪个 basin / state 的标签
  - 在这里：至少是 O / PC / C，可能再加 productive / non-productive
  - 为什么重要：没有标签，ML 侧没法做 state-aware evaluation

- `seed bank`
  - 最简单定义：一组代表性起始结构
  - 在这里：用来给 downstream model/evaluation 多起点启动
  - 为什么重要：这是你从 chemistry 向 dynamics benchmark 传递的关键接口

### 6. 背后原理

`推断/建议`
Benchmark 的真正价值不是“堆文件”，而是定义问题。

如果没有 benchmark pack，ML 侧会遇到两个根本问题：
1. 不知道什么算“学到了 TrpB 相关 dynamics”
2. 不知道应该和哪种 chemistry truth 对齐

所以这个 idea 的原理很简单：
- MetaDynamics 给你的是 rare-event / state-landscape truth
- 机器学习要消费它，需要离散化、结构化、可复现化
- Benchmark Pack 正是在做这个翻译

### 7. 可交付物

`推断/建议`

- 最小可用版
  - manifest
  - reproducible input notes
  - first usable FES/FEL
  - O/PC/C labels
  - representative seed pack
  - evaluation README

- 稍强版
  - 加 productive / non-productive closure labels
  - 加 OpenMM compatibility note
  - 加 baseline visualization

- 时间尺度
  - 1 周：先交 v0 schema + first usable artifact list
  - 2 周：交 first usable pack
  - 1 个月：交更稳的 state labels + first baseline comparison

### 8. 对你本人是否现实

`推断/建议`
现实，而且比“发明新模型”现实得多。

你真正需要强的是：
- 复现链路
- 资产整理
- 术语和 state 定义
- 和 Yu / Amin 对齐接口

不现实的版本是：
- 你一个人同时做全套 chemistry truth、12 组复刻、完整模型 benchmarking

### 9. 依赖与 blockers

- `事实`
  single-walker 仍然是关键 blocker。
  见 [failure-patterns.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/validations/failure-patterns.md:325)。
- `事实`
  Osuna SI 没给完整 SIGMA 数值，某些参数仍是 informed choice。
  见 [JACS2019_MetaDynamics_Parameters.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/parameters/JACS2019_MetaDynamics_Parameters.md:220)。
- `推断/建议`
  管理性 blocker 是：你要先让 Amin 明确他想要的是哪一类 artifact。

### 10. 失败模式

- 科学失败：state 定义不稳，FES 不可信
- 技术失败：restart / CV / adaptive hill 处理错误
- 沟通失败：你做成 chemistry archive，但 Amin 不知道怎么用
- scope 失败：把 v0 benchmark 写成“完美 Osuna 复刻”

### 11. 如何 pitch 给 Amin

- 2 句话版本
  - `I think the most concrete contribution I can make is to turn the TrpB metadynamics work into a first usable benchmark pack.`
  - `That would mean reproducible setup, FES/state labels, representative seeds, and an evaluation-ready schema for the model side.`

- 5 句话版本
  - `Rather than guessing at a new model direction, I think I can first make the metadynamics side more useful to the team by packaging it into a benchmark asset.`
  - `My idea is not just to run MetaD, but to produce a first usable pack with reproducible setup, FES, state labels, representative seeds, and usage notes.`
  - `That would give the ML side something chemistry-grounded to evaluate against.`
  - `It also seems like a more realistic before-summer deliverable for me than trying to define a new architecture.`
  - `If that is useful, I’d like to confirm what exact artifacts you would want in that pack.`

---

## Idea 2: Multi-start Rare-State Evaluation

### 1. 一层人话

`推断/建议`
这个 idea 想解决的问题是：
“一个 dynamics model 就算能生成很平滑的轨迹，也不代表它真的懂 TrpB 重要的 rare states。”

所以 multi-start evaluation 的重点是：
- 不只从一个 open state 开始
- 而是从多个 metaD-derived states 开始
- 看模型能不能保持合理 basin topology、恢复关键 rare states、区分 productive / non-productive behavior

### 2. 为什么它和我们项目强相关

- `事实`
  Osuna/JACS 关心的不是一个静态结构，而是 ensemble heterogeneity、O/PC/C 状态和 productive closure。
  见 [JACS2019_ReadingNotes.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/papers/reading-notes/JACS2019_ReadingNotes.md:19)。
- `事实`
  Amin 自己的 protein-dynamics 线已经在关心 metadynamics-like behavior 和 non-Markovian dynamics。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:1152)。
- `推断/建议`
  所以这个 idea 能把 generic benchmark 拉成真正 TrpB-specific 的 evaluation layer。

### 3. 为什么 STAR-MD 没做完这件事

- `事实`
  STAR-MD 的主 benchmark 仍然是 ATLAS-style long-horizon rollout。
- `事实`
  它有功能相关案例，但没有把 “from multiple metaD-derived basins, recover TrpB-relevant rare states” 设计成核心 benchmark。
- `推断/建议`
  所以 STAR-MD 证明了 rollout 可以很强，但没有证明模型已经学会 TrpB-specific rare-state dynamics。

### 4. 工作流

`推断/建议`

1. 从 Benchmark Pack 里挑 canonical states
   - 输入：O/PC/C + productive labels
   - 输出：state seed bank

2. 设计 multi-start protocol
   - 输入：seed bank、固定 horizon、replicates
   - 输出：统一评估协议

3. 定义 metrics
   - 输入：rollout trajectories
   - 输出：state retention、rare-state recall、productive closure rate、occupancy consistency

4. 输出 comparison matrix
   - 输入：不同 model / baseline 的结果
   - 输出：谁只是“稳”，谁真的“懂 TrpB”

### 5. 核心术语

- `multi-start`
  - 最简单定义：从多个不同起点重复评估
  - 在这里：不是只从一个 open conformation 出发
  - 为什么重要：防止模型把所有轨迹平均化

- `rare-state recovery`
  - 最简单定义：模型能不能回到稀有但重要的状态
  - 在这里：重点不是轨迹好看，而是 rare substates 是否被保留
  - 为什么重要：TrpB 功能相关变化很多不是最常见状态

- `occupancy`
  - 最简单定义：轨迹在各状态里待多久
  - 在这里：判断模型是否把状态分布学歪了
  - 为什么重要：仅有 single-frame accuracy 不够

### 6. 背后原理

`推断/建议`
rare-state evaluation 的难点在于：
- rare states 本来就少
- 普通 dynamics model 很容易学到“安全平均轨迹”
- 如果只看结构 validity，你会误以为模型很好

所以这个 idea 的原理是：
- 把真正有科学意义的状态作为 benchmark 单元
- 让模型从多个 basin 出发
- 看它是否保留功能相关 state topology，而不是只会平滑 rollout

### 7. 可交付物

- 最小可用版
  - state seed bank
  - state classifier
  - metric spec
  - one baseline results table

- 稍强版
  - visualization dashboard
  - generic vs TrpB-specific benchmark comparison note

- 时间尺度
  - 1 周：metric draft + seed definition
  - 2 周：first evaluator
  - 1 个月：full comparison protocol

### 8. 对你本人是否现实

`推断/建议`
中等偏高，前提是你做 evaluation，不做 architecture。

这件事适合本科生的原因在于：
- 它要求你把科学问题说清楚
- 把 state 和 metrics 说清楚
- 而不是从零 owner 一个新模型

### 9. 依赖与 blockers

- `事实`
  没有稳定 Benchmark Pack，这个 idea 会漂。
- `事实`
  还依赖 Amin 的 benchmark/rollout 接口。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:1023)。
- `未知`
  目前不知道 Amin 的 working version 支持什么输入输出格式。

### 10. 失败模式

- state labels 自己就不稳
- seeds 太单一，multi-start 退化成 single-start
- metrics 又回到 generic validity
- benchmark leakage
- 过度把 occupancy difference 解释成 kinetics fidelity

### 11. 如何 pitch 给 Amin

- 2 句话版本
  - `I think a useful extension would be a TrpB-specific multi-start rare-state evaluation.`
  - `Instead of only checking smooth rollouts, we could ask whether the model preserves basin topology and recovers productive closure from metadynamics-derived seeds.`

- 5 句话版本
  - `One way I could contribute without jumping directly into architecture work is to define a TrpB-specific evaluation layer for the dynamics benchmark.`
  - `The idea would be to start from multiple metadynamics-derived states rather than a single initial structure.`
  - `Then we could test whether the model preserves the correct basin structure, recovers rare states, and distinguishes productive from non-productive closure.`
  - `That would give us a more meaningful task than just checking validity or smoothness.`
  - `If that direction is useful, I’d want to align on what outputs your current benchmark already supports.`

---

## Idea 3: Mutation-conditioned TrpB Mini-Dataset

### 1. 一层人话

`推断/建议`
这不是“大模型训练集”，而是把现在散在 mutation / docking / MD / MMPBSA 里的结果整理成一个小但干净的数据资产。

直观理解：
- 现在组里的 mutation 结果像很多零散表格和讨论
- Mini-Dataset 的目标，是把它们变成一个清晰、可查询、可复用的结构化表

### 2. 为什么它和我们项目强相关

- `事实`
  104 / 298 / 301、D/L discrimination、MD stability、binding energy 已经是主线问题，不是你额外引入的。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:398)。
- `推断/建议`
  这个 asset 会直接服务 reward、analysis、wet-lab triage。

### 3. 为什么 STAR-MD 没做完这件事

- `事实`
  STAR-MD 不是 mutation-specific enzyme dataset，也不做 chirality/selectivity。
- `推断/建议`
  所以这块是你们项目内部才有的 task/data layer。

### 4. 工作流

1. 定义样本主键
   - variant + handedness + theozyme context
2. 汇总 raw tables
   - Amin 的 docking/mutation 结果
   - Yu 的 MD/MMPBSA/geometry 结果
3. 统一 schema
4. 加 derived features
5. 形成 clean data card + baseline notebook

### 5. 核心术语

- `mutation-conditioned`
  - 最简单定义：把突变信息当输入条件
  - 在这里：不是 generic protein，而是特定 mutation patterns

- `descriptor`
  - 最简单定义：可计算的特征
  - 在这里：active-site distances、lysine placement 等

- `label`
  - 最简单定义：想预测或分析的结果
  - 在这里：D 优于 L、MD 稳定、MMPBSA 排名等

### 6. 背后原理

`推断/建议`
小样本数据资产的价值，不在于训练大模型，而在于：
- 统一语言
- 让 reward / analysis / filtering 不再每次从头对齐
- 明确哪些信号真的和 promising variants 同向

### 7. 可交付物

- clean CSV/Parquet
- data schema
- feature dictionary
- data card
- one simple baseline notebook

### 8. 对你本人是否现实

`推断/建议`
中等偏高。难点主要是数据清洗和对齐，不是模型创新。

### 9. 依赖与 blockers

- 依赖 Amin 给 mutation/docking 表
- 依赖 Yu 给 MD/MMPBSA/geometry 结果
- blocker 常常是命名不统一、版本混乱、标签定义不一致

### 10. 失败模式

- 样本太少
- 标签噪声高
- train/test 泄漏
- 把 binding 好误当 catalysis 好

### 11. 如何 pitch 给 Amin

`I think one concrete way I could help is to organize the current mutation and validation results into a clean TrpB mini-dataset. That would make the reward and evaluation side more systematic rather than relying on scattered tables and informal comparisons.`

---

## Idea 4: Reward Sanity Study

### 1. 一层人话

`推断/建议`
这项工作的核心不是“重新发明 reward”，而是先搞清楚：
`哪些便宜信号真的有用，哪些只是看起来合理？`

### 2. 为什么它和我们项目强相关

- `事实`
  组里已经在反复担心 geometry-only reward、wrong reward、cheap proxy 是否会误导优化。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:500)。
- `推断/建议`
  所以这是贴着主线走的，不是边缘问题。

### 3. 为什么 STAR-MD 没做完这件事

- `事实`
  STAR-MD 解决的是 dynamics generation，不是 enzyme reward design。
- `推断/建议`
  这个问题完全还在你们自己手里。

### 4. 工作流

1. 定义 downstream target
   - promising candidate / D-L selectivity / MD stability 等
2. 列出 cheap signals
   - motif RMSD、docking、lysine placement、active-site distances 等
3. 做单变量 sanity
4. 做小规模组合
5. 生成 tiered reward/filtering schema

### 5. 核心术语

- `cheap signal`
  - 低成本 proxy
- `sanity study`
  - 先验证 proxy 有没有信息，再决定要不要放进 reward
- `tiered reward`
  - 便宜信号先筛，贵信号后验验证

### 6. 背后原理

`推断/建议`
reward 是优化目标，不是中立观察者。
如果 reward 错了，GRPO/RLHF 只会把错误更系统化。
所以 sanity study 的本质，是先问“proxy 和真实目标同不同向”，再问“优化怎么做”。

### 7. 可交付物

- signal inventory
- sanity matrix
- useful vs harmful signals list
- v1 tiered reward schema
- negative findings note

### 8. 对你本人是否现实

`推断/建议`
高。因为它更像严谨评估研究，而不是开放式 model project。

### 9. 依赖与 blockers

- 依赖统一 candidate 表
- 依赖大家认可 downstream target 定义
- blocker 主要是标签定义，而不是算力

### 10. 失败模式

- 样本量太小
- batch 不可比
- confounding 强
- 所有 cheap signals 都弱

最后一种不一定是坏事，它反而能阻止后续在错 reward 上浪费时间。

### 11. 如何 pitch 给 Amin

`I think a useful contribution would be a reward sanity study: before optimizing harder, I want to check which cheap signals actually correlate with promising downstream candidates and which ones are misleading.`

---

## Idea 5: TrpB-specific Extension of Amin's Benchmark

### 1. 一层人话

`推断/建议`
这件事不是去改 Amin 的 dynamics architecture，而是在他已有 benchmark 外面再加一层 `TrpB-specific task layer`。

也就是：
- generic benchmark 可能只看 validity / smoothness / coverage
- 你要加的是：TrpB 相关 states、active-pocket geometry、rare-state recovery

### 2. 为什么它和我们项目强相关

- `事实`
  Amin 已经说过他做了 protein dynamic benchmark working version。
  见 [slack_history.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/tools/slack_history.md:1023)。
- `推断/建议`
  如果你能把 MetaD 产物接到这个 benchmark 上，你和 Amin 的线才真正连上。

### 3. 为什么 STAR-MD 没做完这件事

- `事实`
  STAR-MD 没有 TrpB-specific benchmark，也不替代 metadynamics 沿 CV 的 rare-event truth。
- `推断/建议`
  所以它留下了 task-definition 和 evaluation 层的空间。

### 4. 工作流

1. 先定义 TrpB task，不先碰模型
2. 从 MetaD/FES 提取 seeds 和 states
3. 设计 TrpB-specific metrics
4. 先做 benchmark spec 和 scorer
5. 再看是否接 Amin 的模型输出

### 5. 核心术语

- `task layer`
  - 在 generic benchmark 上再加一个具体科学问题
- `state seed`
  - 某个 basin 的代表性起始结构
- `active-pocket geometry consistency`
  - 模型轨迹是否保住关键几何约束

### 6. 背后原理

`推断/建议`
一个 benchmark 是否“有用”，取决于它有没有问对问题。
generic benchmark 能告诉你模型稳不稳；
TrpB-specific benchmark 才能告诉你模型有没有学到你们真正关心的 dynamics。

### 7. 可交付物

- benchmark spec
- state seed pack
- metric script
- TrpB task README
- one baseline report

### 8. 对你本人是否现实

`推断/建议`
中等偏低，但不是不能做。
前提是 scope 要锁在 `evaluation/task layer`，不能变成“半个 model project”。

### 9. 依赖与 blockers

- 强依赖 Amin 分享 benchmark working version
- 依赖你这边先有 usable seeds / labels
- 如果 MetaD artifact 还不稳，metric 也会漂

### 10. 失败模式

- scope 爆炸成 model project
- TrpB 状态定义本身不稳
- metric 太多却没人真正用
- 形式感很强，但没有实际决策价值

### 11. 如何 pitch 给 Amin

`I am not proposing to redesign the dynamics model itself. What I could do is define a TrpB-specific task layer on top of your current benchmark, using metadynamics-derived states and metrics to test whether the model captures functionally relevant dynamics rather than only smooth rollouts.`

---

## 横向比较

### 按 feasibility

1. Reward Sanity Study
2. Benchmark Pack
3. Mutation-conditioned Mini-Dataset
4. Multi-start Rare-State Evaluation
5. TrpB-specific Extension of Amin's Benchmark

### 按和你当前工作最顺的连接程度

1. Benchmark Pack
2. Multi-start Rare-State Evaluation
3. Reward Sanity Study
4. TrpB-specific Benchmark Extension
5. Mutation-conditioned Mini-Dataset

### 按 novelty

1. Multi-start Rare-State Evaluation
2. TrpB-specific Benchmark Extension
3. Benchmark Pack
4. Reward Sanity Study
5. Mutation-conditioned Mini-Dataset

### 我的综合判断

- `最稳妥`
  Benchmark Pack
- `最平衡`
  Benchmark Pack + Rare-State Evaluation
- `最激进`
  TrpB-specific Extension of Amin's Benchmark

---

## 最稳妥的 meeting framing

最不容易出错的说法不是：

`Do you want me to improve the model?`

而是：

`My current working hypothesis is that the most useful contribution I can make is to turn the TrpB metadynamics side into a first usable benchmark / evaluation asset for the dynamics side. If you would prefer a model-side task instead, I think I would be most effective if that scope is defined explicitly.`

这句话的好处是：
- 你给出自己的判断
- 你没有装成已经知道全部答案
- 你没有把 conversation 一脚踢进“开放式 model innovation”

---

## 第三轮追问树

### 应该问 Amin

1. `Before summer, what is the one primary deliverable you want me to own?`
2. `Do you want me primarily on the metadynamics / benchmark side, or on a scoped model-side task?`
3. `If the metadynamics side is useful, what exact artifact do you want: FES, state labels, seeds, evaluator, or a benchmark pack?`
4. `What part of the protein-dynamics question do you still think remains open after STAR-MD?`

### 应该问 Yu

1. `For the metadynamics work, what is the minimum scientifically credible artifact we can hand off before summer?`
2. `Which states / structures would you trust enough to become seeds or labels for downstream evaluation?`
3. `If I package this for ML, what chemistry distinctions are most important not to lose?`

### 应该问自己

1. 我现在最顺手的产出是什么，不依赖大量新权限？
2. 我最怕的 scope explosion 是哪一类？
3. 哪个 deliverable 最能让我在 meeting 后 1 周内交出第一版？

### 项目自己还没回答的问题

1. protein-dynamics 支线的核心 research question 现在到底是什么？
2. MetaDynamics 对 dynamics benchmark 的接口，是 evaluation truth 还是 training signal？
3. project 里到底谁对你的 weekly deliverable 说了算，是 Amin、Yu，还是两人共同？

