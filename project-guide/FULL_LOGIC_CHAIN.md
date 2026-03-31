# 从零理解整个项目：TrpB MetaDynamics 全景逻辑链

> **这是什么文档？** 这份文档假设你什么都不知道，从最基础的概念开始，一步一步把整个项目的逻辑链讲清楚。每个概念第一次出现时都会解释。读完之后，你应该能回答："我在做什么？为什么要做？每一步的逻辑是什么？"
>
> **读这份文档需要多久？** 大约 30–40 分钟。建议一口气读完，中间不要跳。

---

## 第一章：这个项目到底在干什么

### 1.1 一句话版本

你要复刻一种叫 MetaDynamics 的计算方法，用它来评估 AI 生成的蛋白质是否具有催化活性。

### 1.2 三句话版本

Caltech 的 aNima Lab 用一种叫 GenSLM 的 AI 模型生成了大量新的 TrpB 酶序列。但是"AI 说这个序列好"不够——你需要用物理学层面的模拟来验证这些序列对应的蛋白质是否真的能工作。西班牙 Osuna 实验室发表了一套方法（MetaDynamics + 自由能景观分析），能从蛋白质的三维结构出发，预测它有没有催化活性。你的任务就是先复刻 Osuna 的方法，确认你能得到和她一样的结果，然后把这个方法应用到 aNima Lab 生成的新序列上。

### 1.3 为什么你在做这个

你即将去 Caltech 的 aNima Lab（Anima Anandkumar 教授）做暑期研究。这个项目是你在那边的工作内容。你现在在 UNC 提前开始准备，目标是到了 Caltech 就能直接上手跑模拟，而不是到了再从零学起。

---

## 第二章：TrpB 是什么——从酶开始讲

### 2.1 什么是酶

酶是蛋白质的一种，专门负责催化化学反应。催化的意思是：让一个本来很慢（可能要几百年）的化学反应在几毫秒内完成。酶本身不被消耗，只是提供一个"场地"让反应发生。

### 2.2 什么是 TrpB

TrpB 全名叫 **Tryptophan Synthase β-subunit**（色氨酸合酶β亚基）。它催化的反应是：

```
吲哚 (Indole) + L-丝氨酸 (L-Serine) → L-色氨酸 (L-Tryptophan)
```

色氨酸是 20 种天然氨基酸之一，是人体必需的营养成分。自然界中，TrpB 是所有生物合成色氨酸的关键酶。

### 2.3 TrpB 的"搭档"问题

在自然界中，TrpB 不是独立工作的。它和另一个亚基 **TrpA** 组成一个复合体叫 **Tryptophan Synthase (TrpS)**。TrpA 和 TrpB 之间有"别构通讯"——TrpA 的存在会让 TrpB 的催化活性大幅提升。

> **别构通讯 (Allosteric communication)**：蛋白质一个位置发生的变化，通过内部的结构传导，影响了另一个远处位置的行为。就像你按了门铃（一个位置），屋里的灯亮了（另一个位置）——中间通过电线（结构传导）连接。

如果你把 TrpB 从 TrpS 复合体中拿出来单独使用（"isolated TrpB"），它的活性会大幅下降。这是一个核心问题：**为什么 TrpB 离开 TrpA 就不好用了？**

### 2.4 PLP——TrpB 的辅因子

TrpB 的催化活性依赖一个叫 **PLP (Pyridoxal 5'-Phosphate, 磷酸吡哆醛)** 的小分子。PLP 不是蛋白质的一部分，它是一个"辅因子"——就像工人手里的工具。没有 PLP，TrpB 什么都催化不了。

PLP 通过一种叫 **Schiff base (席夫碱)** 的化学键共价连接到 TrpB 上的第 82 号赖氨酸残基（**K82**）。在催化过程中，PLP 依次和不同的底物形成中间体：

| 催化阶段 | 化学物种 | 缩写 | 发生了什么 |
|---------|---------|------|-----------|
| 第 1 步 | Internal aldimine | **E(Ain)** | PLP 和 K82 连着，等待底物进来 |
| 第 2 步 | External aldimine | **E(Aex1)** | L-丝氨酸挤走 K82，自己和 PLP 连上 |
| 第 3 步 | Aminoacrylate | **E(A-A)** | 丝氨酸脱水，形成高活性中间体 |
| 第 4 步 | Quinonoid | **E(Q₂)** | 吲哚进攻 A-A，形成新的 C-C 键——色氨酸即将诞生 |
| 第 5 步 | Product release | **E(Trp)** | L-色氨酸释放，PLP 回到和 K82 连接的状态 |

> **为什么要知道这些中间体？** 因为蛋白质在每个中间体阶段的形状（构象）是不一样的。你做 MetaDynamics 模拟的时候，需要分别在每个中间体阶段跑模拟，看蛋白质在那个阶段的形状偏好。

---

## 第三章：COMM domain——整个故事的核心

### 3.1 什么是 COMM domain

TrpB 上有一段大约 88 个氨基酸的区域（第 97–184 号残基），叫 **COMM domain (Communication domain, 通信结构域)**。这段区域是一个可以活动的"盖子"——它可以打开（Open），也可以关闭（Closed）。

想象一个饭盒：饭盒盖子打开的时候，你可以往里放东西（底物进入）；盖子关上的时候，里面的东西被封住（催化反应发生）；做完饭，盖子再打开，产物出来。

### 3.2 三种构象状态

COMM domain 不是只有"开"和"关"两个状态，它有三种：

| 状态 | 英文 | 缩写 | 含义 |
|------|-----|------|------|
| 打开 | Open | **O** | 盖子完全打开，底物可以进出 |
| 半关 | Partially Closed | **PC** | 盖子半开半关，过渡状态 |
| 关闭 | Closed | **C** | 盖子完全关上，催化反应正在发生 |

### 3.3 为什么 COMM domain 这么重要

Osuna 实验室的核心发现是：

> **TrpB 变体的催化活性，取决于它的 COMM domain 能不能稳定地处于 Closed 状态。**

更具体地说：

- 如果一个 TrpB 变体的 COMM domain **容易关上、关上之后很稳定**（能量低），那它的催化活性就高。
- 如果 COMM domain **关不上、或者关上之后不稳定**（能量高），那催化活性就低。

这就是所谓的 **"population shift" (群体偏移) 范式**：催化活性不是由某个单一的结构特征决定的，而是由蛋白质在不同构象之间的**分布（population）**决定的。Closed 构象占的比例越大，活性越高。

### 3.4 "Productive" 和 "Unproductive" Closure

还有一个重要的细节：不是所有的"关闭"都是好的关闭。

- **Productive closure（生产性关闭）**：COMM domain 关上之后，活性位点的关键残基（K82、E104 等）恰好对准了底物，催化反应可以进行。判断标准：COMM domain 结构和已知的活性关闭结构（PDB 3CEP）的偏差 < 1.5 Å，并且 K82 到 Q₂ 中间体的距离 ≤ 3.6 Å。
- **Unproductive closure（非生产性关闭）**：COMM domain 虽然关上了，但关得不对——关键残基没对准，催化反应做不了。偏差 > 1.5 Å 或 K82-Q₂ 距离太远。

> **类比**：就像你关门的时候没对准门框，门虽然"关上了"，但其实没锁好，风一吹就开了——这就是 unproductive closure。

---

## 第四章：为什么需要计算机模拟

### 4.1 实验的局限

你可能会想：直接做实验不就行了？把蛋白质放在试管里测一下活性不就知道了？

问题在于：

1. **实验慢且贵**：合成一个新蛋白质需要几天到几周，测活性又要花时间。如果 AI 一次生成了 100,000 个候选序列，你不可能每个都做实验。
2. **实验告诉你"是什么"，不告诉你"为什么"**：实验能测出一个变体的活性是 2.9 s⁻¹，但不能告诉你为什么它活性高——是因为 COMM domain 更容易关闭？还是因为底物结合更紧？实验看不到蛋白质在原子层面的运动。

### 4.2 分子动力学模拟 (MD)

**分子动力学模拟 (Molecular Dynamics, MD)** 是一种用计算机模拟蛋白质运动的方法。基本原理很直观：

1. 给蛋白质中每个原子一个初始位置和速度
2. 用牛顿第二定律（F = ma）计算每个原子受到的力
3. 更新每个原子的位置和速度
4. 重复 2-3 步，每次前进一小步（通常 2 飞秒 = 0.000000000000002 秒）

这样你就可以"看到"蛋白质在溶液中的运动——哪些部分在抖动、哪些部分很稳定、COMM domain 有没有打开或关闭的趋势。

### 4.3 常规 MD 的局限——"罕见事件"问题

问题来了：COMM domain 从 Open 到 Closed 的完整转变，在真实时间尺度上大约需要几微秒到几毫秒。而一次 MD 模拟，即使在最快的 GPU 上跑一天，也只能模拟几百纳秒（1 微秒 = 1000 纳秒）。

这意味着：你跑了 500 纳秒的 MD，可能从头到尾 COMM domain 都停留在 Open 状态，一次都没有转到 Closed——不是因为它不会转，而是因为你的模拟时间不够长，没有等到那个"罕见事件"发生。

> **类比**：你想知道一个人一生中会不会搬家。但你只观察了他 3 天——3 天里他当然没搬家，但你不能因此说他永远不会搬。

这就是为什么需要"增强采样"方法——**MetaDynamics** 就是其中一种。

---

## 第五章：MetaDynamics——让蛋白质"加速探索"

### 5.1 基本思想

MetaDynamics 的核心思想非常简单：**往蛋白质已经待过的地方加"惩罚能量"，迫使它去探索新地方。**

想象你在一个有很多山谷的地形上行走。你自然会停在最深的谷底（最稳定的构象）。普通 MD 就是让你在这个地形上自由行走——你大部分时间都会困在谷底出不来。

MetaDynamics 做的事情是：每隔一段时间，在你当前位置放一块"砖头"（一个小的高斯能量丘）。砖头越堆越多，谷底被慢慢填平，最终你被"推"出谷底，翻过山脊，滑到旁边的另一个谷底。

这样，通过逐渐堆砖头，蛋白质就能在模拟时间内完成从 Open 到 Closed 的完整转变——这在普通 MD 中可能需要几十倍甚至几百倍的时间。

### 5.2 集体变量 (Collective Variable, CV)——"往哪个方向看"

MetaDynamics 不是在三维空间的每个位置都放砖头（那样维度太高了，做不了）。它是在一个**降维后的坐标空间**里放砖头。这个降维后的坐标叫 **集体变量 (Collective Variable, CV)**。

CV 是你定义的一个或多个"反应坐标"，用来描述你关心的那个运动。对于 TrpB 来说：

- 你关心的运动是 **COMM domain 从 Open 到 Closed 的转变**
- 所以你需要一个 CV 能够量化"COMM domain 现在是打开的还是关上的"

### 5.3 Path Collective Variable——为什么不用简单的 RMSD

最简单的想法是用 RMSD（均方根偏差）作为 CV：测量当前 COMM domain 的结构和 Open 状态结构的 RMSD——RMSD 小说明接近 Open，RMSD 大说明远离 Open。

但这有个问题：RMSD 只告诉你"离 Open 有多远"，不告诉你"你到底去了哪里"。你可能远离了 Open，但不是走向 Closed，而是走到了一个完全无关的方向。就像你知道"离北京 1000 公里"——你可能在上海，也可能在蒙古，RMSD 区分不了。

所以 Osuna 使用了 **Path Collective Variable（路径集体变量）**，它由两个分量组成：

| 分量 | 符号 | 含义 | 类比 |
|------|------|------|------|
| 进展 | **s(R)** | 沿着 O→C 参考路径走了多远 | GPS 上的"距目的地还有多少公里" |
| 偏离 | **z(R)** | 偏离参考路径有多远 | "你偏离了高速公路多远" |

**参考路径**是怎么来的？取两个已知的晶体结构：
- **1WDW**：Open 状态的 TrpB（起点）
- **3CEP**：Closed 状态的 TrpB（终点）

在这两个结构之间做线性插值，生成 **15 个中间帧**，组成一条从 Open 到 Closed 的"参考高速公路"。

然后 MetaDynamics 在 s(R) 和 z(R) 这两个维度上放砖头。s 从 1 到 15（1 = Open，15 = Closed），z 越小越好（说明你在路径附近，没有跑偏）。

### 5.4 Well-Tempered MetaDynamics——砖头越放越小

普通 MetaDynamics 有一个问题：砖头的大小是固定的。填平一个深谷需要很多砖头，但填平之后如果继续放同样大的砖头，能量面就被"过度填充"了——结果不再准确。

**Well-Tempered MetaDynamics** 解决了这个问题：砖头的高度不是固定的，而是随着时间递减。已经填过的地方，后续放的砖头越来越小，最终收敛到一个稳定的自由能面。

控制递减速度的参数叫 **bias factor (偏差因子, γ)**。Osuna 用的是 **γ = 10**。γ 越大，探索越充分但收敛越慢；γ 越小，收敛越快但可能探索不够。

### 5.5 Multiple Walker——多人同时探索

为了让探索更充分，Osuna 使用了 **Multiple Walker MetaDynamics**：同时启动 10 个平行的模拟（10 个 "walker"），它们共享砖头信息。就像 10 个人同时在不同位置探索一个地图，每个人发现的地形信息实时共享给其他人。

每个 walker 跑 50–100 ns，10 个 walker 加起来就是 500–1000 ns 的总采样时间。

### 5.6 具体参数一览

| 参数 | 值 | 含义 |
|------|---|------|
| 初始高斯高度 | 0.15 kcal/mol | 每块"砖头"的初始高度 |
| 高斯沉积间隔 | 2 ps | 每隔多久放一块砖头 |
| 偏差因子 γ | 10 | 砖头衰减速率 |
| 高斯宽度 | 自适应 (Adaptive) | 砖头的"宽度"根据局部地形自动调整 |
| Walker 数量 | 10 | 平行探索的模拟数量 |
| 每个 Walker 时长 | 50–100 ns | 每个平行模拟跑多久 |
| 温度 | 350 K (≈77°C) | 因为 PfTrpB 来自嗜热古菌 *P. furiosus* |
| MetaDynamics 软件 | PLUMED 2 + GROMACS | PLUMED 是加砖头的引擎，GROMACS 是跑 MD 的引擎 |

---

## 第六章：自由能景观 (FEL)——MetaDynamics 的输出

### 6.1 什么是自由能

先解释"自由能"。自由能（Gibbs Free Energy, G）是热力学中衡量一个状态"多稳定"的量。自由能越低的状态越稳定——系统自然会倾向于待在自由能低的地方。

> **类比**：球在碗底是稳定的（势能最低），你把球推到碗壁上它会滚回去。自由能就是这个"碗"的深度。

### 6.2 什么是自由能景观 (Free Energy Landscape, FEL)

当你用 MetaDynamics 在 s(R) 和 z(R) 两个 CV 维度上填完所有的砖头后，把堆积的砖头"反过来"，就得到了这两个维度上的自由能面——这就是 **FEL**。

FEL 是一张二维的"地形图"：
- **x 轴**：s(R)，从 Open (左) 到 Closed (右)
- **y 轴**：z(R)，偏离参考路径的程度
- **颜色/高度**：自由能的值。深蓝色 = 自由能很低 = 蛋白质喜欢待在这里。红色 = 自由能很高 = 蛋白质不太愿意去这里。

### 6.3 怎么读 FEL

FEL 上你需要关注这些东西：

**1. 能量盆（Energy Basin / Minimum）——"谷底"**

FEL 上的蓝色区域就是能量盆。每个能量盆对应一种蛋白质喜欢待的构象。

- 如果在 s ≈ 1–5 的位置有一个深蓝色的盆，说明蛋白质喜欢待在 Open 状态。
- 如果在 s ≈ 10–15 的位置有一个深蓝色的盆，说明蛋白质喜欢待在 Closed 状态。
- 如果两个盆都有，说明蛋白质可以在 Open 和 Closed 之间切换。

**2. 能垒（Energy Barrier）——"山脊"**

两个盆之间的最高点就是能垒。能垒越高，蛋白质从一个状态转到另一个状态就越难（需要更多能量）。

**3. ΔG(closed)——Closed 态有多稳定**

ΔG(closed) = G(closed) − G(open)。如果 ΔG 是负数（比如 −3 kcal/mol），说明 Closed 比 Open 更稳定——蛋白质大部分时间在 Closed 状态。这意味着催化活性高。

### 6.4 不同 TrpB 变体的 FEL 长什么样

Osuna 的 JACS 2019 论文比较了三种 TrpB 在 Q₂ 中间体阶段的 FEL：

| 变体 | FEL 特征 | 催化活性 (kcat) |
|------|---------|----------------|
| **PfTrpS (αβ复合体)** | Open 和 PC 都有能量盆，C 态较高但可达 | 1.0 s⁻¹ |
| **PfTrpB (isolated, 孤立)** | 只有一个能量盆，C 态不可达或为 unproductive | 0.31 s⁻¹ |
| **PfTrpB0B2 (进化变体)** | O/PC/C 都可达，能垒仅 ~2 kcal/mol，C 态是 productive | 2.9 s⁻¹ |

看到了吗？PfTrpB0B2 的活性最高（2.9 s⁻¹），恰好对应它的 FEL 上 Closed 态最容易达到、最稳定。而孤立的 PfTrpB 活性最低，因为它的 FEL 显示它根本到不了 productive Closed 状态。

**这就是 FEL 作为"筛选工具"的科学基础：FEL 上 Closed 态的深度 ≈ 催化活性。**

---

## 第七章：GenSLM 和 aNima Lab——序列从哪来

### 7.1 定向进化的局限

传统上，如果你想要一个更好的酶，你用 **定向进化 (Directed Evolution, DE)**：随机突变→测活性→挑最好的→再随机突变→循环。Frances Arnold 因此获得了 2018 年诺贝尔化学奖。

但定向进化有两个问题：
1. 每轮只能探索已有序列附近的小范围突变（通常只改 1-2 个氨基酸）
2. 需要大量实验，每轮筛选成千上万个突变体

### 7.2 GenSLM——用 AI 生成全新序列

**GenSLM** 是一种在 DNA 序列（密码子级别）上训练的语言模型。它学习了大量基因组数据中的序列规律，然后可以**生成全新的蛋白质序列**——不是在已有序列上做小修改，而是从头生成。

aNima Lab（Anandkumar）和 Arnold Lab 合作，用 GenSLM 生成了大约 100,000 个 TrpB 候选序列。其中一些序列和已知的 TrpB 只有 70-90% 的序列相似度——这意味着它们是自然界中从未存在过的全新蛋白质。

### 7.3 实验验证了什么

Lambert et al. 2026 (Nature Communications) 对其中一部分候选进行了实验测试：

- 许多 GenSLM-TrpB 确实能表达、折叠、并具有催化活性
- **GenSLM-230** 这个变体特别突出：活性超过了 Arnold 实验室通过定向进化得到的 PfTrpB0B2
- 更惊人的是：一些 GenSLM-TrpB 对**非天然底物**（比如 D-丝氨酸）也有活性——这是定向进化的变体做不到的

### 7.4 但是——实验不够

虽然实验证明了一部分 GenSLM-TrpB 有活性，但：
1. 不可能对全部 100,000 个候选都做实验
2. 实验只告诉你"这个有活性 / 没活性"，不告诉你**为什么**
3. 如果你想改进 GenSLM（让它生成更好的序列），你需要一个**定量的评分标准**——不是"有活性/没活性"的二分法，而是一个连续的数值

这就是 MetaDynamics 的用武之地。

---

## 第八章：MetaDynamics 作为筛选工具和 Reward Function

### 8.1 筛选逻辑

把前面的知识串起来：

1. Osuna 发现：**FEL 上 Closed 态的稳定性 ≈ 催化活性**
2. GenSLM 生成了 100,000 个 TrpB 序列
3. 不可能对每个都做实验
4. **但可以对每个都跑 MetaDynamics**（虽然也很费计算资源，但比实验快得多）
5. 跑完之后看 FEL → 提取 ΔG(closed) → 排序 → 挑最好的去做实验

这就是 MetaDynamics 作为"筛选工具"的运作方式。

### 8.2 Reward Function——从筛选到优化

更进一步，如果你不只是想筛选，而是想**指导 GenSLM 生成更好的序列**，你需要一个 **reward function（奖励函数）**。

Reward function 的意思是：给每个候选序列一个"分数"。分数高的序列 = 好的设计，分数低的 = 差的设计。然后把这个分数反馈给 GenSLM，让它学会"生成分数高的序列"。

从 MetaDynamics 的 FEL 中可以提取三个关键指标：

| 指标 | 含义 | "好"的标准 |
|------|------|-----------|
| **ΔG(closed)** | Closed 态比 Open 态低多少 kcal/mol | < −2 kcal/mol |
| **Barrier height** | 从 Open 翻到 Closed 要多少能量 | < 5 kcal/mol |
| **K82-Q₂ distance < 3.6 Å 的比例** | 活性位点几何正确的时间占比 | > 30% |

把这三个数组合成一个 scalar score（比如加权求和），就得到了 reward function。

### 8.3 闭环设计循环

完整的闭环是这样的：

```
GenSLM 生成序列
       ↓
同源建模（把序列变成 3D 结构）
       ↓
MetaDynamics 模拟
       ↓
提取 FEL → 计算 reward score
       ↓
score 反馈给 GenSLM → GenSLM 学会生成更好的序列
       ↓
（循环）
```

你现在做的是**第一步**：确保你能正确地跑 MetaDynamics 并从 FEL 中提取出可靠的 score。如果这一步不成功，后面的闭环就无从谈起。

---

## 第九章：你具体要做什么——完整步骤

### 9.1 Phase 1：复刻 Osuna 的结果（验证方法正确性）

你不能直接就去跑 GenSLM 的新序列。你必须先在已知体系上复刻 Osuna 的结果，证明你的方法是对的。如果你在已知体系上都得不到正确的 FEL，那你在新序列上得到的结果就不可信。

**复刻目标**：对 PfTrpS (αβ复合体) 在 E(Ain) 阶段跑 MetaDynamics，得到的 FEL 应该显示 Open 态是主要稳定态——和 Osuna JACS 2019 Figure 2a 一致。

**具体步骤**：

| Step | 做什么 | 用什么工具 | 在哪里做 |
|------|--------|-----------|---------|
| 1 | PLP 辅因子参数化 | antechamber (AMBER) + Gaussian09 | Longleaf (Claude Code Terminal) |
| 2 | 构建 15 帧 O→C 参考路径 | Python (MDAnalysis/ProDy)，1WDW→3CEP Cα 线性插值 | Longleaf |
| 3 | 准备 PfTrpS(Ain) 体系 | AMBER (tleap): solvate + minimize + heat + equilibrate | Longleaf |
| 4 | 500 ns 常规 MD | AMBER pmemd.cuda (GPU) | Longleaf GPU 节点 |
| 5 | 转换到 GROMACS 格式 | amb2gro_top_gro.py 或 ParmEd | Longleaf |
| 6 | Well-tempered MetaD (10 walkers) | GROMACS + PLUMED2 | Longleaf GPU 节点 |
| 7 | 提取 FEL | `plumed sum_hills` → Python matplotlib 画图 | Longleaf + Cowork |
| 8 | 比较 FEL 与 Osuna 发表的结果 | 肉眼对比 + 定量指标 | Cowork |

### 9.2 Phase 2：应用到 GenSLM-TrpB

复刻成功后，对 GenSLM-230（和其他候选）做同样的流程。比较它们的 FEL 和已知体系的 FEL：

- GenSLM-230 的 Closed 态是不是更稳定？（应该是，因为实验显示它活性很高）
- 它对 D-丝氨酸底物的 FEL 和 L-丝氨酸底物有什么不同？
- 哪些 GenSLM-TrpB 变体的 FEL 最好看？推荐实验验证。

### 9.3 Phase 3：构建 Reward Function（如果时间允许）

写一个 Python 脚本，自动从 FEL 中提取 ΔG(closed)、barrier height、K82-Q₂ distance 比例，计算出一个 scalar score，输出排名表。

---

## 第十章：当前进度和剩余工作

### 已完成 ✅

| 事项 | 说明 |
|------|------|
| Paper 阅读材料准备 | 5 篇核心论文的 reading notes + deep annotation HTML 全部生成 |
| MetaDynamics 参数提取 | 从 JACS 2019 SI 提取了所有参数，写入了参数表，fact-checked |
| HPC 环境配置 | Longleaf 上 AMBER 24p3、PLUMED 2.9、GROMACS 2026.0 (conda, PLUMED patch) 全部装好 |
| 项目文件体系 | CLAUDE.md、RULES.md、GLOSSARY.md、CHANGELOG.md、PROTOCOL.md、6-stage pipeline 全部就绪 |
| PDB 结构下载 | 5DVZ、5DW0、5DW3、1WDW、3CEP、4HPX、5IXJ 已下载并验证 |
| **Alanine dipeptide toy test** | GROMACS+PLUMED2 工具链验证通过。6.1 ns well-tempered MetaD, 6088 hills, FES 显示预期的 Ramachandran 能量盆 (alpha_R at phi=-53, psi=-32)。4 个脚本 bug 在执行中发现并修复（见 failure-patterns.md FP-003/004/006/007）。结论：工具链可用，可以进入 TrpB 正式 campaign。 |
| 全项目 fact-check | 5 个 parallel agent 验证了参数表、逻辑链、术语表、阅读笔记、项目状态。修正了 7 个文档错误，0 个 AI 幻觉 |
| Gaussian/ORCA 可用性 | Longleaf 有 Gaussian 16c02 和 ORCA 6.0/6.1，PLP RESP 参数化可行 |

### 未完成 ❌

| 事项 | 需要做什么 | 依赖什么 |
|------|-----------|---------|
| **读论文** | 打开 HTML 标注文件，通读 JACS 2019 和 GenSLM 2026 | 你的时间和注意力 |
| **PLP 参数化** | 用 antechamber + Gaussian16 生成 PLP Ain 中间体的 GAFF+RESP 参数 | AMBER 环境 + Gaussian (已就绪) |
| **O→C 参考路径** | 从 1WDW 和 3CEP 提取 Cα 坐标，线性插值 15 帧 | Python + PDB 文件 (已下载) |
| **PfTrpS(Ain) 体系准备** | Solvation, minimization, heating, equilibration | PLP 参数 |
| **500 ns 常规 MD** | 在 Longleaf GPU 上跑 | 体系准备完成 |
| **Well-tempered MetaD** | 10 walkers × 50-100 ns | 常规 MD + 参考路径 |

---

## 第十一章：核心概念速查

读到这里，你应该已经理解了所有核心概念。以下是一张快速对照表，方便你以后随时查：

| 概念 | 一句话解释 |
|------|-----------|
| **TrpB** | 催化"吲哚 + 丝氨酸 → 色氨酸"的酶 |
| **COMM domain** | TrpB 上一段可以开关的"盖子"（残基 97-184），开关状态决定催化活性 |
| **O / PC / C** | COMM domain 的三种状态：Open / Partially Closed / Closed |
| **PLP** | 辅因子（工具），共价连在 K82 上，催化必需 |
| **Ain, Aex1, A-A, Q₂** | 催化过程中 PLP 和底物形成的不同中间体 |
| **MD (分子动力学)** | 用牛顿力学模拟蛋白质原子运动的方法 |
| **MetaDynamics** | 往蛋白质待过的地方加"砖头"，迫使它探索新构象的增强采样方法 |
| **Well-Tempered MetaD** | 砖头越放越小的改进版 MetaDynamics，结果更准确 |
| **Path CV (s, z)** | 两个集体变量：s = 沿 O→C 路径走了多远，z = 偏离路径多远 |
| **FEL (自由能景观)** | MetaDynamics 的最终输出：一张"地形图"，颜色深 = 蛋白质喜欢待 |
| **ΔG(closed)** | Closed 态比 Open 态低多少 kcal/mol，越负 = 活性越高 |
| **GenSLM** | AI 语言模型，能生成全新的 TrpB 序列 |
| **Reward function** | 从 FEL 提取的评分标准，用于反馈给 GenSLM 指导设计 |
| **Population shift** | Osuna 的核心范式：催化活性 = Closed 构象的群体占比 |
| **SPM (Shortest Path Map)** | 从 MD 轨迹中识别别构通讯路径的分析方法 |
| **Productive closure** | COMM domain 关得正确（K82-Q₂ ≤ 3.6 Å，RMSD < 1.5 Å from path） |
| **ff14SB** | 蛋白质力场——描述原子间相互作用的数学模型 |
| **GROMACS** | 跑 MD 的开源软件（本项目中用于 MetaDynamics） |
| **PLUMED** | MetaDynamics 插件，装在 GROMACS 上面 |
| **AMBER** | 另一个跑 MD 的软件（本项目中用于常规 MD 和体系准备） |
| **Longleaf** | UNC 的 HPC 集群，你跑所有模拟的地方 |

---

## 第十二章：逻辑链总图

把整个故事串成一条线：

```
TrpB 是催化色氨酸合成的酶
    ↓
它的催化活性取决于 COMM domain 能不能正确关闭
    ↓
Osuna 用 MetaDynamics 证明了这一点：
FEL 上 Closed 态越稳定 → 活性越高
    ↓
aNima Lab 用 GenSLM 生成了 100,000 个新的 TrpB 序列
    ↓
需要一种方法来筛选哪些序列真的好用
    ↓
MetaDynamics FEL 就是这个筛选方法：
跑 MetaD → 得到 FEL → 看 Closed 态有多稳定 → 排名
    ↓
你的工作：
(1) 先复刻 Osuna 的结果，验证方法正确
(2) 再应用到 GenSLM-TrpB 上，筛选最好的候选
(3) 把 FEL 指标做成 reward function，反馈给 GenSLM
```

这就是你整个项目的完整逻辑链。每一步都有因果关系，没有一步是可以跳过的。

---

> **最后一句话**：你现在处于"复刻 Osuna 结果"的 Phase 1 中期。基础设施全部搭好，工具链通过 alanine dipeptide 验证（GROMACS+PLUMED2 能正确跑 well-tempered MetaD 并生成 FES）。下一步是：(1) 读论文，(2) PLP 参数化，(3) 生成 15-frame O→C 参考路径，(4) 准备 PfTrpS(Ain) 体系开始正式模拟。
