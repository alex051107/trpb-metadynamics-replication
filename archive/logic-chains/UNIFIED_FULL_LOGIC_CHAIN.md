# TrpB MetaDynamics 项目统一逻辑链
# Unified Full Logic Chain

> **这是什么文档？** 这是整个 TrpB MetaDynamics 复刻项目的**唯一完整参考文档**。它合并了所有已有的逻辑链、论文笔记、参数表、失败记录和代码，形成一个从零开始、不需要任何前置知识就能理解整个项目的完整技术蓝图。
>
> **受众**：你自己（Zhenpeng Liu），以及审阅这份材料的 PI。
>
> **阅读时间**：完整通读约 90-120 分钟。建议分 Part 阅读，每个 Part 可独立查阅。
>
> **最后更新**：2026-03-30

---

# Part I: 理论与背景 -- Why Are We Doing This?

---

## 第一章：TrpB 是什么，为什么研究它

### 1.1 从酶说起

酶是蛋白质的一种，专门负责催化化学反应。催化的意思是：让一个本来很慢（可能要几百年）的化学反应在几毫秒内完成。酶本身不被消耗，只是提供一个"场地"让反应发生。

### 1.2 TrpB 催化什么反应

TrpB 全名叫 **Tryptophan Synthase beta-subunit**（色氨酸合酶 beta 亚基）。它催化的反应是：

```
吲哚 (Indole) + L-丝氨酸 (L-Serine) --> L-色氨酸 (L-Tryptophan)
```

色氨酸是 20 种天然氨基酸之一，是人体必需的营养成分。自然界中，TrpB 是所有生物合成色氨酸的关键酶。

### 1.3 TrpB 的"搭档"问题

在自然界中，TrpB 不是独立工作的。它和另一个亚基 **TrpA** 组成一个复合体叫 **Tryptophan Synthase (TrpS)**。TrpA 和 TrpB 之间有"别构通讯" -- TrpA 的存在会让 TrpB 的催化活性大幅提升。

> **别构通讯 (Allosteric communication)**：蛋白质一个位置发生的变化，通过内部的结构传导，影响了另一个远处位置的行为。类比：你按了门铃（一个位置），屋里的灯亮了（另一个位置），中间通过电线（结构传导）连接。

如果你把 TrpB 从 TrpS 复合体中拿出来单独使用（"isolated TrpB"），它的活性会大幅下降。这是核心问题：**为什么 TrpB 离开 TrpA 就不好用了？**

### 1.4 PLP -- TrpB 的辅因子

TrpB 的催化活性依赖一个叫 **PLP (Pyridoxal 5'-Phosphate, 磷酸吡哆醛)** 的小分子辅因子。没有 PLP，TrpB 什么都催化不了。

PLP 通过一种叫 **Schiff base (席夫碱)** 的化学键共价连接到 TrpB 上的第 82 号赖氨酸残基（**K82**）。在催化过程中，PLP 依次和不同的底物形成中间体：

| 催化阶段 | 化学物种 | 缩写 | 发生了什么 |
|---------|---------|------|-----------|
| 第 1 步 | Internal aldimine | **E(Ain)** | PLP 和 K82 连着，等待底物进来 |
| 第 2 步 | External aldimine | **E(Aex1)** | L-丝氨酸挤走 K82，自己和 PLP 连上 |
| 第 3 步 | Aminoacrylate | **E(A-A)** | 丝氨酸脱水，形成高活性中间体 |
| 第 4 步 | Quinonoid | **E(Q2)** | 吲哚进攻 A-A，形成新的 C-C 键 |
| 第 5 步 | Product release | **E(Trp)** | L-色氨酸释放，PLP 回到和 K82 连接的状态 |

> **为什么要知道这些中间体？** 因为蛋白质在每个中间体阶段的形状（构象）是不一样的。做 MetaDynamics 模拟的时候，需要分别在每个中间体阶段跑模拟，看蛋白质在那个阶段的形状偏好。

### 1.5 COMM domain -- 整个故事的核心

TrpB 上有一段大约 88 个氨基酸的区域（第 97-184 号残基），叫 **COMM domain (Communication domain, 通信结构域)**。这段区域是一个可以活动的"盖子" -- 它可以打开（Open），也可以关闭（Closed）。

> **类比**：想象一个饭盒。盖子打开的时候，你可以往里放东西（底物进入）；盖子关上的时候，里面的东西被封住（催化反应发生）；做完饭，盖子再打开，产物出来。

COMM domain 有三种构象状态：

| 状态 | 英文 | 缩写 | 含义 |
|------|-----|------|------|
| 打开 | Open | **O** | 盖子完全打开，底物可以进出 |
| 半关 | Partially Closed | **PC** | 盖子半开半关，过渡状态 |
| 关闭 | Closed | **C** | 盖子完全关上，催化反应正在发生 |

### 1.6 Productive vs Unproductive Closure

不是所有的"关闭"都是好的关闭：

- **Productive closure（生产性关闭）**：COMM domain 关上之后，活性位点的关键残基（K82、E104 等）恰好对准了底物，催化反应可以进行。
  - 判断标准 1：COMM domain 结构和已知的活性关闭结构（PDB 3CEP）的偏差 **< 1.5 A**
  - 判断标准 2：K82 到 Q2 中间体的距离 **<= 3.6 A**
- **Unproductive closure（非生产性关闭）**：COMM domain 虽然关上了，但关得不对 -- 关键残基没对准，催化反应做不了。偏差 > 1.5 A 或 K82-Q2 距离太远（如 3.9 A）。

> **类比**：关门的时候没对准门框，门虽然"关上了"，但其实没锁好，风一吹就开了 -- 这就是 unproductive closure。

### 1.7 三个 TrpB 变体的活性对比

| 变体 | 英文 | kcat (s^-1) | 特点 |
|------|------|------------|------|
| PfTrpS (alpha-beta 复合体) | Wild-type complex | 1.0 | 有 TrpA 帮忙，正常水平 |
| PfTrpB (孤立野生型) | Isolated WT | 0.31 | 没有 TrpA，活性大降 |
| PfTrpB0B2 (进化变体) | Evolved stand-alone | **2.9** | 6 个定向进化突变恢复活性，甚至超过复合体 |

**PfTrpB0B2 的 6 个定向进化突变**：P12L, E17G, I68V, T292S, F274S, T321A。这些突变恢复了 COMM domain 的构象灵活性，使其能够沿着正确的路径关闭。

---

## 第二章：定向进化与计算的结合 -- Osuna 的 JACS 2019 论文做了什么

> 论文引用：Maria-Solano, Iglesias-Fernandez & Osuna, JACS 2019, 141(33), 13049-13056
> DOI: 10.1021/jacs.9b03646

### 2.1 论文的核心发现

**一句话总结**：COMM domain "能关上"和"关对了"是两码事。

孤立的 PfTrpB 并不是 COMM domain 完全关不上。MetaDynamics 显示它确实能到达 closed-like 的构象。但问题在于，它关上的"姿势"不对 -- COMM domain 的位置偏离了参考路径超过 1.5 A，导致 K82 离 Q2 中间体有 3.9 A（正常应该 <= 3.6 A）。

这 0.3 A 的差距意味着 K82 没法有效地参与质子转移，催化反应就卡住了。

PfTrpB0B2 的 6 个突变恢复了 COMM domain 的 conformational flexibility，使它能沿着正确的路径关闭，K82 精准到位。

### 2.2 三个体系的 Free Energy Landscape (FEL) 对比

Osuna 比较了三种 TrpB 在 Q2 中间体阶段的 FEL（本文最核心的图，Figure 2）：

| 变体 | FEL 特征 | 催化活性 (kcat) |
|------|---------|----------------|
| **PfTrpS (alpha-beta 复合体)** | Open 和 PC 都有能量盆，C 态可达但能垒较高（约 6 kcal/mol） | 1.0 s^-1 |
| **PfTrpB (isolated, 孤立)** | 景观很单调，只有一个能量盆。C 态区域偏离参考路径（z 值大），属于 unproductive closure | 0.31 s^-1 |
| **PfTrpB0B2 (进化变体)** | 恢复了 O/PC/C 三个能量盆的异质性，O 到 C 能垒仅约 2 kcal/mol，C 态与 PfTrpS 的 productive closure 对齐 | 2.9 s^-1 |

**核心逻辑**：PfTrpB0B2 的活性最高，恰好对应它的 FEL 上 Closed 态最容易达到、最稳定。而孤立的 PfTrpB 活性最低，因为它根本到不了 productive Closed 状态。

### 2.3 Productive Closure 的结构证据（Figure 3）

三个体系到达 closed state 后的结构叠合：

| 体系 | K82-Q2 距离 | 判定 |
|------|------------|------|
| PfTrpS | 约 3.6 A | Productive -- 质子转移可以发生 |
| PfTrpB | 3.9 +/- 0.3 A | **Unproductive** -- 太远了 |
| PfTrpB0B2 | 约 3.6 A | Productive -- 恢复到和复合体一样 |

### 2.4 SPM 分析（Figure 4）

**Shortest Path Map (SPM)**：从 MetaDynamics 轨迹中识别关键的 residue-residue correlation。基于 Calpha 相关性的 Dijkstra 最短路径算法。

关键结果：SPM 命中了 PfTrpB0B2 的 5/6 个突变位点（83% 命中率）。唯一没捕获的是 T321A。

> **为什么这很重要？** 证明"从 MD 轨迹挖功能信息"这条路走得通。对我们项目的评分函数设计有启发。

### 2.5 论文的方法论弱点

1. 每个条件只跑了一次 MetaDynamics，没有独立重复，FEL 上没有 error bars
2. 收敛性检查只是 qualitative（看能量差趋势图），没有 block analysis
3. PLP 用 GAFF + RESP (HF/6-31G*) 参数化，对共价辅酶的描述能力有限
4. 定性趋势可能可靠，但具体数值的误差不确定

### 2.6 我们项目的位置

这篇论文建立了一个关键范式：**FEL 上 Closed 态的稳定性 ≈ 催化活性**。我们的工作是：

1. **Phase 1**：复刻 Osuna 的结果，验证方法正确性
2. **Phase 2**：将方法应用到 Caltech aNima Lab 的 GenSLM 生成序列上
3. **Phase 3**（如果时间允许）：构建基于 FEL 的 Reward Function，反馈给 GenSLM

---

## 第三章：MetaDynamics 是什么 -- 从 MD 基础到增强采样

### 3.1 分子动力学模拟 (Molecular Dynamics, MD)

**MD** 是一种用计算机模拟蛋白质运动的方法。基本原理：

1. 给蛋白质中每个原子一个初始位置和速度
2. 用牛顿第二定律（F = ma）计算每个原子受到的力
3. 更新每个原子的位置和速度
4. 重复 2-3 步，每次前进一小步（通常 2 飞秒 = 0.000000000000002 秒）

### 3.2 力场 (Force Field) -- 力从哪里来

力场是一套数学公式 + 参数的集合，描述原子之间的相互作用力：

- 两个碳原子之间的化学键长应该是 1.53 A，弹簧常数是 317 kcal/mol/A^2
- 三个原子组成的键角应该是 109.5 度
- 两个不成键的原子之间有 van der Waals 作用力和静电作用力

> **类比**：力场像一本"说明书"，告诉计算机每种原子对之间的弹簧有多硬、弹簧的自然长度是多少。

我们使用的力场：

| 力场 | 管什么 | 版本 |
|------|--------|------|
| **ff14SB** | 蛋白质的 20 种标准氨基酸 | AMBER 力场家族 |
| **GAFF** (General AMBER Force Field) | 非标准小分子（如 PLP） | 注意是 GAFF 不是 GAFF2，与 SI 一致 |
| **TIP3P** | 水分子 | 三点水模型 |

### 3.3 常规 MD 的局限 -- "罕见事件"问题

COMM domain 从 Open 到 Closed 的完整转变，在真实时间尺度上大约需要几微秒到几毫秒。而一次 MD 模拟，即使在最快的 GPU 上跑一天，也只能模拟几百纳秒。

> **类比**：你想知道一个人一生中会不会搬家。但你只观察了他 3 天 -- 3 天里他当然没搬家，但你不能因此说他永远不会搬。

这就是为什么需要"增强采样" -- **MetaDynamics** 就是其中一种。

### 3.4 MetaDynamics 的核心思想

**往蛋白质已经待过的地方加"惩罚能量"，迫使它去探索新地方。**

> **类比**：想象你在一个有很多山谷的地形上行走。你自然会停在最深的谷底。MetaDynamics 每隔一段时间在你当前位置放一块"砖头"（一个小的高斯能量丘）。砖头越堆越多，谷底被慢慢填平，最终你被"推"出谷底，翻过山脊，到达另一个谷底。

### 3.5 集体变量 (Collective Variable, CV) -- "往哪个方向看"

MetaDynamics 不是在三维空间的每个位置都放砖头（维度太高）。它是在一个**降维后的坐标空间**里放砖头。这个坐标叫 **集体变量 (CV)**。

对于 TrpB：
- 你关心的运动是 COMM domain 从 Open 到 Closed 的转变
- 所以你需要一个 CV 能够量化"COMM domain 现在是打开的还是关上的"

### 3.6 Well-Tempered MetaDynamics -- 砖头越放越小

普通 MetaDynamics 的砖头大小是固定的。填平一个深谷后如果继续放同样大的砖头，能量面就被"过度填充"了。

**Well-Tempered MetaDynamics** 解决了这个问题：砖头的高度随时间递减。已经填过的地方，后续放的砖头越来越小，最终收敛到稳定的自由能面。

控制递减速度的参数叫 **bias factor (偏差因子, gamma)**。Osuna 用的是 **gamma = 10**。

### 3.7 Multiple Walker -- 多人同时探索

同时启动 10 个平行的模拟（10 个 "walker"），共享砖头信息。

> **类比**：10 个人同时在不同位置探索一个地图，每个人发现的地形信息实时共享给其他人。

每个 walker 跑 50-100 ns，10 个 walker 加起来就是 500-1000 ns 的总采样时间。

---

## 第四章：Path CV -- 怎么定义构象变化的"进度条"

### 4.1 为什么不用简单的 RMSD

最简单的想法是用 RMSD（均方根偏差）作为 CV：测量当前 COMM domain 和 Open 状态结构的 RMSD。RMSD 小说明接近 Open，RMSD 大说明远离 Open。

问题：RMSD 只告诉你"离 Open 有多远"，不告诉你"到底去了哪里"。你可能远离了 Open，但不是走向 Closed，而是走到了一个完全无关的方向。

> **类比**：你知道"离北京 1000 公里" -- 你可能在上海，也可能在蒙古，RMSD 区分不了。

### 4.2 Path CV 的两个分量

Osuna 使用了 **Path Collective Variable（路径集体变量）**，由两个分量组成：

| 分量 | 符号 | 含义 | 类比 |
|------|------|------|------|
| 进展 | **s(R)** | 沿着 O-->C 参考路径走了多远 | GPS 上的"距目的地还有多少公里" |
| 偏离 | **z(R)** | 偏离参考路径有多远 | "你偏离了高速公路多远" |

### 4.3 参考路径怎么来的

取两个已知的晶体结构：
- **1WDW**：Open 状态的 TrpB（起点）
- **3CEP**：Closed 状态的 TrpB（终点，来自 *S. typhimurium* TrpS 的 Q analogue）

在这两个结构之间做 Calpha 线性插值，生成 **15 个中间帧**，组成从 Open 到 Closed 的"参考高速公路"。

### 4.4 Path CV 的数学参数

| 参数 | 值 | 含义 |
|------|---|------|
| 路径帧数 | 15 | O-->C 被离散化为 15 步 |
| 使用的原子 | COMM domain (残基 97-184) + base region (残基 282-305) 的 Calpha | 定义"结构"的原子集 |
| lambda 参数 | 2.3 x (1/80) ≈ 0.029 | 路径平滑因子，2.3 x (1/mean square displacement between successive frames) |

### 4.5 s(R) 的状态定义

| 状态 | s(R) 范围 |
|------|----------|
| Open (O) | 1-5 |
| Partially Closed (PC) | 5-10 |
| Closed (C) | 10-15 |

> **关键理解**：s = 1 对应完全 Open，s = 15 对应完全 Closed。z 越小越好（说明在参考路径附近，没跑偏）。Productive closure 要求 z 小（在路径上）且 s 大（接近 Closed）。

---

## 第五章：Free Energy Landscape (FEL) -- 我们最终要得到什么

### 5.1 什么是自由能

自由能（Gibbs Free Energy, G）是热力学中衡量一个状态"多稳定"的量。自由能越低的状态越稳定。

> **类比**：球在碗底是稳定的（势能最低），你把球推到碗壁上它会滚回去。自由能就是这个"碗"的深度。

### 5.2 什么是 FEL

当 MetaDynamics 在 s(R) 和 z(R) 两个 CV 维度上填完所有的砖头后，把堆积的砖头"反过来"，就得到了自由能面 -- 即 **FEL (Free Energy Landscape)**。

FEL 是一张二维的"地形图"：
- **x 轴**：s(R)，从 Open (左) 到 Closed (右)
- **y 轴**：z(R)，偏离参考路径的程度
- **颜色/高度**：自由能的值。深蓝色 = 自由能很低 = 蛋白质喜欢待在这里。红色 = 自由能很高。

### 5.3 怎么读 FEL

**能量盆 (Energy Basin / Minimum)**：FEL 上的深色区域。每个能量盆对应蛋白质喜欢待的一种构象。

**能垒 (Energy Barrier)**：两个盆之间的最高点。能垒越高，从一个状态转到另一个状态越难。

**Delta-G(closed)**：G(closed) - G(open)。如果是负数，说明 Closed 比 Open 更稳定，催化活性高。

### 5.4 从 FEL 提取的三个关键指标

| 指标 | 含义 | "好"的标准 |
|------|------|-----------|
| **Delta-G(closed)** | Closed 态比 Open 态低多少 kcal/mol | < -2 kcal/mol |
| **Barrier height** | 从 Open 翻到 Closed 要多少能量 | < 5 kcal/mol |
| **K82-Q2 distance < 3.6 A 的比例** | 活性位点几何正确的时间占比 | > 30% |

> **FEL 作为"筛选工具"的科学基础：FEL 上 Closed 态的深度 ≈ 催化活性。**

### 5.5 FEL 重构方法

使用 PLUMED 的 `sum_hills` 工具：

```bash
plumed sum_hills --hills HILLS --outfile fes.dat --mintozero
```

输出的 `fes.dat` 是一个二维网格，每行包含 `s z FreeEnergy`。可以用 Python (matplotlib) 画出二维等高线图。

### 5.6 收敛性检查

- 监测 Open 和 Closed 局部最小值之间的能量差随模拟时间的变化
- 理想情况：该差值在模拟后期趋于稳定
- 原文的检查方式是 qualitative（Figure S4/S5），没有做 block analysis

---

# Part II: 从 PDB 到 Simulation-Ready System (体系搭建)

---

## 第六章：PDB 结构准备 -- 从 RCSB 下载到可用输入

### 6.1 所有需要的 PDB 结构

| PDB | 分辨率 | 描述 | 在项目中的用途 | 状态 |
|-----|--------|------|---------------|------|
| **1WDW** | 2.0 A | Open PfTrpS (alpha-beta) | 起始结构 + Path CV 的 Open 端点 | 已下载 |
| **3CEP** | 1.9 A | Closed StTrpS (Q analogue) | Path CV 的 Closed 端点 | 已下载 |
| **5DVZ** | 1.5 A | Holo PfTrpB (Ain, Open) | LLP 残基提取；RMSD 参考 | 已下载 |
| **5DW0** | 1.9 A | PfTrpB + L-Ser (Aex1, PC) | PLS 残基提取 | 已下载 |
| **5DW3** | -- | PfTrpB + L-Trp (product, PC) | 参考 | 已下载 |
| **4HPX** | -- | StTrpS closed (A-A) | 0JO 残基；结构模板 | 已下载 |
| **5IXJ** | -- | PfTrpB (Ain, L-Thr) | 辅助参考 | 已下载 |
| **4HN4** | -- | StTrpS closed (A-A) | 额外 Closed 参考 | 未下载 |

### 6.2 PDB 文件里的非标准残基

PLP 在 PDB 文件中以特殊残基名记录，**不是** "PLP" 这个名字：

| PDB | 中间体 | PDB 残基名 | 全称 | 重原子数 | 化学含义 |
|-----|--------|-----------|------|---------|---------|
| 5DVZ | Ain | **LLP** | N6-(pyridoxal phosphate)-L-lysine-5'-monophosphate | 24 | PLP-K82 Schiff base (共价连接) |
| 5DW0 | Aex1 | **PLS** | Pyridoxal-5'-phosphate-L-serine | 22 | 外部醛亚胺 (K82 游离) |
| 4HPX | A-A | **0JO** | Aminoacrylate-PLP adduct | 21 | 来自 S. typhimurium，仅作模板 |
| -- | Q2 | **未知** | Quinonoid intermediate | -- | 无晶体结构，需要建模 |

> **这些名字是从实际 PDB 文件中验证的（2026-03-30），不是从记忆中写的。** 参见 failure-patterns.md FP-003。

### 6.3 LLP 残基的原子组成（5DVZ, 24 个重原子）

LLP 包含两部分：

**PLP 吡啶环 + 磷酸基团（15 个原子）**：N1, C2, C2', C3, O3, C4, C4', C5, C6, C5', OP4, P, OP1, OP2, OP3

**K82 主链 + 侧链（9 个原子）**：N, CA, CB, CG, CD, CE, NZ, C, O

关键连接：

```
K82-NZ = C4'（PLP 的醛基碳）
     ^
   这就是 Schiff base 键（C=N 双键）
```

PDB 中的 LINK 记录证实 LLP 残基 82 通过肽键连接到前后残基：
```
LINK     C   HIS A  81           N   LLP A  82
LINK     C   LLP A  82           N   THR A  83
```

> **关键理解**：LLP 不是一个"外来的配体"。它是蛋白质多肽链的一部分（残基 82），只是这个残基包含了 PLP 辅因子。

### 6.4 PLS 残基与 LLP 的区别

| 区别 | LLP (Ain) | PLS (Aex1) |
|------|-----------|------------|
| Schiff base 连接对象 | K82 的 NZ | L-丝氨酸的 N |
| K82 | **包含在残基内** | **不包含**（K82 变回普通 Lys） |
| PDB 中位置 | 残基 82（取代 Lys82） | HETATM 401（独立配体） |
| 总重原子数 | 24 | 22 |

> **注意命名变化**：5DVZ (LLP) 和 5DW0 (PLS) 对相同的 PLP 原子使用了不同的名字（C4' vs C4A, C2' vs C2A 等）。这是 PDB 命名惯例的差异，不代表化学结构不同。

---

## 第七章：PLP 参数化 -- 完整 GAFF+RESP 工作流

### 7.1 为什么 PLP 是第一个 blocker

ff14SB 的"说明书"里没有 PLP 的条目。计算机不知道 PLP 的吡啶环上原子之间用多大的弹簧常数，不知道磷酸基团的氧原子应该带多少电荷。

> **类比**：你去一个餐厅点菜，菜单上有 20 道标准菜（标准氨基酸），但你带了一道自己做的菜（PLP）要求厨房加热。厨房说："这道菜的烹饪温度是多少？用什么火候？"你得自己提供这些信息。这就是"参数化"。

而且 PLP 通过 Schiff base 共价连接到 K82，不能单独处理：

```
PLP 参数 --> tleap 建模 --> 最小化 --> 加热 --> 平衡 --> 500ns MD --> GROMACS 转换 --> MetaDynamics
```

如果第一步做不出来，后面全部被 block。

### 7.2 PDB 里的残基名 (LLP/PLS/0JO) -- 怎么发现的，什么意思

最初以为 PDB 中 PLP 残基名就是 "PLP"，但实际检查 PDB 文件后发现不是（参见 resource_inventory.md 的 "PLP Residue Names" 部分）。

**发现过程**：在 Longleaf 上执行 `grep '^HETATM' 5DVZ.pdb | awk '{print $4}' | sort -u` 得到实际残基名 `LLP`。

**原因**：PDB 对共价修饰的标准氨基酸使用特定的三字母代码（CCD, Chemical Component Dictionary），而不是辅因子本身的名字。LLP 代表"N6-pyridoxyl-lysine"，是 lysine 被 PLP 修饰后的产物。

### 7.3 antechamber + Gaussian RESP 完整流程

完整 Pipeline 图：

```
PDB 文件（5DVZ）
    |
    |-- 1. 提取 PLP-K82 单元（grep HETATM/ATOM + residue name）
    |
    |-- 2. 加氢（reduce）+ ACE/NME capping（封住断键）
    |
    |-- 3. antechamber：分配 GAFF 原子类型
    |     命令：antechamber -fi pdb -fo mol2 -c gas -at gaff
    |
    |-- 4. Gaussian 16 计算：几何优化 + ESP
    |     关键词：#p HF/6-31G(d) Opt Pop=MK iop(6/33=2,6/42=6,6/50=1)
    |
    |-- 5. antechamber -c resp：从 Gaussian ESP 拟合 RESP 电荷
    |     输入：Gaussian .log --> 输出：带 RESP 电荷的 mol2
    |
    |-- 6. parmchk2：检查并补充缺失的 GAFF 参数
    |     输入：mol2 --> 输出：frcmod
    |
    |-- 7. tleap：组装完整体系
          加载 ff14SB + GAFF + TIP3P + mol2 + frcmod
          输出：parm7（拓扑）+ inpcrd（坐标）
```

**每一步详解：**

**Step 1: 提取修饰残基**

```bash
# 在 Longleaf 上
module load amber/24p3

# 从 5DVZ 提取 chain A 的 LLP 残基
grep -E "^(HETATM|ATOM  )" 5DVZ.pdb \
    | awk '{rn=substr($0,18,3); gsub(/ /,"",rn); cid=substr($0,22,1);
            if(rn=="LLP" && cid=="A") print}' \
    > LLP_chainA.pdb

# 验证：应该有 24 行
wc -l LLP_chainA.pdb
```

**Step 2: 加氢**

```bash
# 用 AmberTools 的 reduce 加氢
reduce LLP_chainA.pdb > LLP_chainA_H.pdb

# 验证：从 24 个重原子变成约 42 个原子（含氢）
wc -l LLP_chainA_H.pdb
```

> **为什么 PDB 没有氢原子？** X-ray 晶体学的分辨率通常不够看到氢原子（氢只有 1 个电子，散射能力太弱）。量子化学计算需要氢原子才能正确计算电子分布。

**Step 2b: ACE/NME Capping -- 封住断键**

LLP 残基的主链 N 和 C 各有一个断键（从肽链上切下来的地方）。如果直接拿"断键"的分子做量子化学计算，电子分布会严重失真。

| 位置 | Cap | 全称 | 化学结构 | 做什么 |
|------|-----|------|---------|--------|
| N-端 | **ACE** | Acetyl | CH3-CO- | 封住主链 N 的断键 |
| C-端 | **NME** | N-methylamide | -NH-CH3 | 封住主链 C 的断键 |

加了 capping 之后：

```
ACE -- [LLP 残基] -- NME
```

> **类比**：你要测量一段铁路的重量。你把它从完整的铁路线上切下来，但切口处钢轨是扭曲变形的。你需要在切口处做处理（加 cap），才能准确称量。

> **Osuna 做了什么？** SI 没有提到 capping 策略。但根据计算化学标准做法，几乎可以确定使用了 ACE/NME capping。这是 SI gap 之一。

推荐 capping 方式：在 PyMOL 或 Chimera 中手动添加 ACE/NME，然后 reduce 加氢。

**Step 3: antechamber 原子类型分配**

antechamber 给每个原子分配 GAFF 原子类型（比如 `ca` = 芳香碳，`os` = 醚氧，`p5` = 五价磷）：

```bash
# 注意：这里用 -c gas (Gasteiger) 只是为了原子类型分配
# 最终电荷将由 RESP 给出
antechamber -i LLP_chainA_H.pdb -fi pdb \
    -o LLP_ain_gas.mol2 -fo mol2 \
    -c gas -at gaff -rn LLP -nc -2

# 注意：用 -at gaff 而不是 -at gaff2（SI 指定 GAFF）
```

| 参数 | 含义 |
|------|------|
| `-fi pdb` | 输入格式是 PDB |
| `-fo mol2` | 输出格式是 mol2 |
| `-c gas` | Gasteiger 电荷（仅供原子类型分配，不作为最终电荷） |
| `-at gaff` | 使用 **GAFF**（不是 GAFF2）原子类型，与 SI 一致 |
| `-rn LLP` | 残基名 |
| `-nc -2` | 净电荷 `[待 PI 确认]` |

**Step 4: Gaussian 量子化学计算**

这是计算量最大的一步。

```bash
# 加载 Gaussian
module load gaussian/16c02

# 用 antechamber 直接生成 Gaussian 输入文件
antechamber -i LLP_ain_gas.mol2 -fi mol2 \
    -o LLP_ain_resp.com -fo gcrt \
    -gv 1 -ge LLP_ain_resp.log \
    -nc -2 -m 1 -at gaff
```

> **如果 antechamber 生成的 .com 文件缺少关键词**，需要手动检查并补充 route line：

```
%chk=LLP_ain.chk
%mem=16GB
%nproc=16
#p HF/6-31G(d) Opt Pop=MK iop(6/33=2,6/42=6,6/50=1)

LLP Ain internal aldimine - RESP charge calculation

-2 1
 N     -42.317  -74.558  -61.909
 C     -42.792  -73.582  -61.102
 ...
```

Gaussian 关键词详解：

| 关键词 | 含义 | 为什么用 |
|--------|------|---------|
| `HF` | Hartree-Fock 方法 | AMBER 标准；RESP 电荷的标配 |
| `6-31G(d)` | 基组，中等大小 | AMBER 标准；和力场其他参数匹配 |
| `Opt` | 几何优化 | 找到最低能量构型再计算 ESP |
| `Pop=MK` | Merz-Kollman ESP 计算方案 | RESP 需要 ESP 数据 |
| `iop(6/33=2)` | 多层 ESP 网格 | 提高 RESP 拟合质量 |
| `iop(6/42=6)` | ESP 网格点密度 | 每个壳层 6 个点/A^2 |
| `iop(6/50=1)` | 输出 ESP 到 .log 文件 | antechamber 需要读取 |

> **为什么是 HF/6-31G(d) 而不是更高级的方法？** AMBER 力场的所有标准电荷都是用 HF/6-31G(d) 计算的。用更高级的方法（如 B3LYP）得到的电荷和力场其他参数不匹配，反而降低精度。类比：配眼镜的镜片和镜框要匹配。

Slurm 提交脚本：

```bash
#!/bin/bash
#SBATCH --job-name=llp_resp
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --partition=general
#SBATCH --output=llp_resp_%j.out

module load gaussian/16c02
cd $SLURM_SUBMIT_DIR
g16 LLP_ain_resp.com
```

预计运行时间：LLP 约 50 个原子，HF/6-31G(d) + Opt，16 cores，约 **2-8 小时**。

**Step 5: RESP 电荷拟合**

```bash
# Gaussian 完成后，检查正常终止
grep 'Normal termination' LLP_ain_resp.log

# 从 Gaussian output 提取 RESP 电荷
antechamber -i LLP_ain_resp.log -fi gout \
    -o LLP_ain_resp.mol2 -fo mol2 \
    -c resp -at gaff -rn LLP -nc -2
```

> **RESP (Restrained Electrostatic Potential)** 的核心思想：
> 1. 用量子化学（HF/6-31G(d)）计算分子周围的静电势 (ESP)
> 2. 找一组原子点电荷，使其产生的静电势尽可能拟合 ESP
> 3. 加约束：化学等价的原子（如甲基的三个氢）有相同的电荷

**Step 6: parmchk2 检查缺失参数**

```bash
parmchk2 -i LLP_ain_resp.mol2 -f mol2 \
    -o LLP_ain.frcmod -a Y
```

> **frcmod 文件是什么？** Force field modification file，只包含 GAFF 数据库中缺失的参数。Schiff base 的 C=N 连接到 lysine 侧链这种组合可能不常见，某些二面角参数可能需要补充。

**Step 7: 验证检查清单**

| 检查项 | 通过标准 | 怎么检查 |
|--------|---------|---------|
| RESP 电荷总和 | 等于指定的净电荷 | 手动加总 mol2 中的电荷列 |
| 所有原子有 GAFF 类型 | 没有 `DU`（dummy）类型 | `grep "DU" *.mol2` |
| frcmod 无 "needs revision" | 无 ATTN 警告 | `grep "ATTN" *.frcmod` |
| 化学等价原子电荷合理 | 磷酸三个氧电荷相近 | 目视检查 |
| Schiff base 氮电荷 | 不应该太极端 (\|q\| < 1.0) | 检查 NZ 行 |

### 7.4 BCC 失败的经验教训（FP-009/010）

**我们踩过的坑**：

**FP-009: antechamber BCC (AM1-BCC) SCF 不收敛**

对 LLP 运行 `antechamber -c bcc` 时，SQM AM1 计算 SCF 不收敛（1000 steps 后 DeltaE = -10.5, DeltaP = 0.21）。charge=0 和 charge=-2 都不收敛。

根因：PLP 含磷酸基团（高电荷密度）+ 吡啶环 + Schiff base 共轭体系，AM1 半经验方法处理这类分子容易 SCF 发散。

> **教训：PLP 类分子不能用 BCC 电荷。必须走 RESP 路径（Gaussian HF/6-31G(d) --> antechamber -c resp）。这也正好是 SI 指定的方法。**

**FP-010: 无氢 PDB 的原子类型分配错误**

对仅含重原子的 `LLP_chainA.pdb`（24 atoms, no H）运行 antechamber 时，吡啶环原子被错误分配为 `c1`（sp）/ `c2`（sp2）而非 `ca`（aromatic）/ `nb`（aromatic N）。

根因：antechamber 需要氢原子来正确判断键级和芳香性。

> **教训：提取非标准残基后，必须先用 reduce 加氢再运行 antechamber。**

### 7.5 质子化状态：为什么这是最难的决策

质子化状态直接决定了：
1. 分子的总电荷
2. 原子的局部电子密度
3. RESP 电荷计算的输入（Gaussian 需要指定总电荷）
4. 力场中的相互作用

> **如果质子化状态选错了，得到的 RESP 电荷是错的，整个力场参数是错的，跑出来的模拟轨迹是错的，最终的 FEL 是错的。** 这不是一个"差不多就行"的决策。

**PLP 上 pH 敏感的基团（实验 pH 7.5）**：

| 基团 | pKa（文献值） | pH 7.5 下的状态 | 推理 |
|------|-------------|----------------|------|
| 磷酸 (-OPO3H2) | pKa1 约 1.6, pKa2 约 6.2 | **双阴离子** (-OPO3^2-) | pH 7.5 >> pKa2 = 6.2 |
| 酚羟基 (C3-OH) | 约 5.8（PLP 中因吡啶 N 吸电子效应降低） | **去质子化** (C3-O^-) | pH 7.5 >> pKa = 5.8 |
| 吡啶 N (N1) | 约 8.5（游离 PLP）；Schiff base 中可能变化 | **质子化** (N1-H+) | pH 7.5 < pKa 约 8.5 |

> **为什么吡啶 N 的 pKa 是 约 8.5 而不是通常的 约 5.2？** 游离吡啶的 pKa 是 5.2，但 PLP 中酚羟基的去质子化（O3^-）形成的分子内氢键稳定了 N1-H+ 形式，将 pKa 提高到约 8.5。

**K82 NZ 在不同中间体中的状态**：

| 中间体 | K82-NZ 状态 | 原因 |
|--------|------------|------|
| **Ain** | Schiff base (NZ=C4') | NZ 和 PLP 形成双键 |
| **Aex1** | 游离 Lys (NZ-H3+, pKa 约 10.5) | 底物取代了 K82 |
| **A-A** | 游离 Lys (NZ-H3+) | 同上 |
| **Q2** | 游离 Lys (NZ-H3+) | 同上 |

**各中间体的总电荷估算** `[待 PI 确认]`：

| 中间体 | 磷酸 | 酚 O3 | N1 | NZ/Schiff base | 预估总电荷 |
|--------|------|-------|-----|----------------|-----------|
| **Ain** (Schiff base 质子化) | -2 | -1 | +1 | +1 | **-1** |
| **Ain** (Schiff base 去质子化) | -2 | -1 | +1 | 0 | **-2** |
| **Aex1** | -2 | -1 | +1 | N/A | **-2** |

> **这是本文档中最大的不确定性**。总电荷取决于 Schiff base 氮的质子化状态，而 SI 没有给出答案。

**需要 PI 决策的问题（按优先级排序）**：

| 问题 | 选项 A | 选项 B | 推荐 |
|------|--------|--------|------|
| Ain Schiff base NZ 质子化？ | 是 (总电荷 -1) | 否 (总电荷 -2) | 选 A（文献主流，pKa 约 10-11） |
| 磷酸双阴离子？ | 是 (-2) | 单阴离子 (-1) | 选"是"（pH 7.5 >> pKa2 6.2） |
| 酚 O3 去质子化？ | 是 (-1) | 否 (0) | 选"是"（pH 7.5 >> pKa 5.8） |
| N1 质子化？ | 是 (+1) | 否 (0) | 选"是"（pH 7.5 < pKa 约 8.5） |

文献参考：
- Toney 2011, Arch Biochem Biophys: PLP 酶综述
- Casasnovas et al. 2014, JACS: PLP 的 pKa 计算
- Major & Gao 2006, JACS: QM/MM 研究 PLP Schiff base 质子化

### 7.6 Capping 策略

**为什么不能直接把 PLP-K82 丢进 Gaussian**：

LLP 残基包含 K82 的主链原子（N, CA, C, O）。当你把 LLP 从蛋白质多肽链中提取出来时，主链 N 和 C 各有一个断键。断键导致量子化学计算的电子分布严重失真。

解决方案：加 **ACE/NME capping groups**（见 Step 2b）。

Cap 原子的电荷在最终 MD 中被丢弃，只保留 LLP 残基本身的原子电荷。但 cap 的存在影响了 LLP 主链原子的电荷分布，使其更接近真实的蛋白质环境。

**Osuna 的 SI 没有提到 capping 策略**（SI gap #2），但这是 AMBER 社区的标准操作。

---

## 第八章：tleap 体系组装

### 8.1 tleap 是什么

tleap 是 AmberTools 的体系构建程序。它的工作是：

1. 读取蛋白质的 PDB 文件
2. 给每个标准残基分配 ff14SB 参数
3. 给 PLP 分配你计算好的 GAFF + RESP 参数
4. 加水（溶剂化）
5. 加离子（中和电荷）
6. 输出 topology (parm7) 和 coordinate (inpcrd) 文件

### 8.2 处理 PLP-K82 共价键

LLP 残基通过肽键连接到 His81 和 Thr83。推荐方法是使用 AMBER library (.lib) 文件：

```bash
# 先在 tleap 中从 mol2 创建 lib 文件
tleap -f - <<EOF
source leaprc.gaff
LLP = loadmol2 LLP_ain_resp.mol2
set LLP head LLP.1.N        # head atom = 主链 N（连接前一个残基）
set LLP tail LLP.1.C        # tail atom = 主链 C（连接后一个残基）
set LLP.1 connect0 LLP.1.N
set LLP.1 connect1 LLP.1.C
saveoff LLP LLP_ain.lib
quit
EOF
```

> **为什么 head 是 N, tail 是 C？** 蛋白质是 N-->C 方向合成的。前一个残基的 C 连接到 LLP 的 N（head），LLP 的 C 连接到下一个残基的 N（tail）。

### 8.3 完整的 tleap 脚本

```bash
tleap -f - <<EOF
# 1. 加载力场
source leaprc.protein.ff14SB      # 蛋白质力场
source leaprc.gaff                # 小分子力场（注意是 gaff 不是 gaff2）
source leaprc.water.tip3p         # 水模型

# 2. 加载 PLP 参数
loadamberparams LLP_ain.frcmod    # 缺失参数补充
loadoff LLP_ain.lib               # LLP 残基定义

# 3. 加载蛋白质
mol = loadpdb pftrps_ain_prepared.pdb

# 4. 检查
check mol

# 5. 溶剂化（TIP3P 水，立方体 box，10 A buffer）
solvatebox mol TIP3PBOX 10.0

# 6. 加离子中和电荷
addions mol Na+ 0
addions mol Cl- 0

# 7. 再次检查
check mol

# 8. 保存
saveamberparm mol pftrps_ain.parm7 pftrps_ain.inpcrd
savepdb mol pftrps_ain_solvated.pdb

quit
EOF
```

> **为什么是 `solvatebox`（立方体）而不是 `solvateoct`（截断八面体）？** SI 说 "pre-equilibrated cubic box"。立方体 box 浪费更多水分子（角落里的水其实不太需要），但和 SI 一致。

> **为什么只中和电荷不加额外盐？** SI 只说 "explicit counterions (Na+ or Cl-)"，没有提到额外的离子浓度。`addions mol Na+ 0` 的 `0` 意味着"加到体系变成电中性为止"。

### 8.4 输出文件

| 文件 | 格式 | 包含什么 | 后续用途 |
|------|------|---------|---------|
| `pftrps_ain.parm7` | AMBER topology | 所有原子的类型、电荷、键连接、力场参数 | AMBER MD |
| `pftrps_ain.inpcrd` | AMBER coordinates | 所有原子的初始坐标 + box 尺寸 | AMBER MD |
| `pftrps_ain_solvated.pdb` | PDB | 可视化检查用 | VMD/PyMOL |

> **parm7 + inpcrd 的关系**：parm7 描述"这个体系有哪些原子、它们之间有什么相互作用"，inpcrd 描述"每个原子现在在哪里"。类比：地图（parm7）和 GPS 坐标（inpcrd）。

---

## 第九章：Conventional MD -- 最小化 --> 加热 --> 平衡 --> 生产

### 9.1 为什么要先跑常规 MD

MetaDynamics 不是直接在晶体结构上跑的。你需要先：

1. **最小化**：消除原子碰撞
2. **加热**：从 0 K 慢慢升温到 350 K
3. **平衡**：让体系的密度、能量稳定
4. **产出 MD**：跑 500 ns，采集数据

> **类比**：你要让一个人跑马拉松（MetaDynamics）。你不能直接把他从冰柜（0 K）里拿出来就开跑。你得先解冻（加热），然后做热身（平衡），确认身体状态正常后，再开始正式比赛。

### 9.2 两阶段最小化

**Stage 1：约束溶质，只最小化溶剂**

```
Minimization Stage 1: solvent relaxation
 &cntrl
  imin=1,
  maxcyc=10000,
  ncyc=5000,
  ntb=1,
  ntr=1,
  restraint_wt=500.0,
  restraintmask='!@H= & !:WAT & !:Na+ & !:Cl-',
 /
```

| 参数 | SI 值 | 含义 |
|------|-------|------|
| `restraint_wt` | 500 kcal/mol/A^2 | 把蛋白质"钉死"在原位 |
| `ncyc` | 5000 | 前半最速下降，后半共轭梯度 |

**Stage 2：无约束最小化**

```
Minimization Stage 2: full system
 &cntrl
  imin=1,
  maxcyc=10000,
  ncyc=5000,
  ntb=1,
  ntr=0,
 /
```

### 9.3 七步加热 (0 --> 350 K)

SI："Seven 50-ps steps (0-->350 K, 50 K increments), NVT, 1 fs timestep, decreasing harmonic restraints."

| Step | 温度 (K) | 约束力常数 (kcal/mol/A^2) | 时间 (ps) | 系综 |
|------|---------|--------------------------|----------|------|
| 1 | 0 --> 50 | 210 | 50 | NVT |
| 2 | 50 --> 100 | 165 | 50 | NVT |
| 3 | 100 --> 150 | 125 | 50 | NVT |
| 4 | 150 --> 200 | 85 | 50 | NVT |
| 5 | 200 --> 250 | 45 | 50 | NVT |
| 6 | 250 --> 300 | 10 | 50 | NVT |
| 7 | 300 --> 350 | 10 (或 0) | 50 | NVT |

示例 AMBER 输入文件（step 1）：

```
Heating step 1: 0-50 K
 &cntrl
  imin=0,
  irest=0,
  ntx=1,
  nstlim=50000,
  dt=0.001,
  ntc=2,
  ntf=2,
  ntt=3,
  gamma_ln=1.0,
  tempi=0.0,
  temp0=50.0,
  ntb=1,
  ntp=0,
  ntr=1,
  restraint_wt=210.0,
  restraintmask='!@H= & !:WAT & !:Na+ & !:Cl-',
  ntpr=500,
  ntwx=500,
  ntwr=5000,
 /
```

> **为什么加热用 NVT 不用 NPT？** 温度剧烈变化时，压力控制器和恒温器可能"打架"，导致 box 尺寸剧烈波动。
>
> **为什么约束力递减？** 开始时强力约束蛋白质在晶体结构位置，只让水适应新温度。随着温度升高，逐渐放松，让蛋白质也自由运动。

### 9.4 NPT 平衡 (2 ns)

```
NPT Equilibration: 2 ns at 350 K, 1 atm
 &cntrl
  imin=0,
  irest=1,
  ntx=5,
  nstlim=1000000,
  dt=0.002,
  ntc=2,
  ntf=2,
  ntt=3,
  gamma_ln=1.0,
  temp0=350.0,
  ntb=2,
  ntp=1,
  barostat=2,
  pres0=1.0,
  ntr=0,
  ntpr=1000,
  ntwx=1000,
  ntwr=50000,
 /
```

> **为什么平衡用 NPT？** 晶体结构放进水 box 后，水的密度不一定是 1 g/cm^3。NPT 允许 box 尺寸自动调整到内部压力等于 1 atm。

### 9.5 NVT 产出 MD (500 ns)

```
Production MD: 500 ns NVT at 350 K
 &cntrl
  imin=0,
  irest=1,
  ntx=5,
  nstlim=250000000,
  dt=0.002,
  ntc=2,
  ntf=2,
  ntt=3,
  gamma_ln=1.0,
  temp0=350.0,
  ntb=1,
  ntp=0,
  cut=8.0,
  ntr=0,
  ntpr=5000,
  ntwx=5000,
  ntwr=250000,
 /
```

| SI 参数 | 值 | 备注 |
|---------|---|------|
| 时间 | 500 ns | 每个体系 |
| 系综 | NVT | 用 NPT 平衡后确定的 box 尺寸 |
| cutoff | 8 A | LJ + 实空间静电截断 |
| 静电 | PME | Particle-Mesh Ewald |
| 温度 | **350 K** | *P. furiosus* 最适温度 |

### 9.6 在 Longleaf 上的运行时间估计

| 体系 (原子数) | GPU 速度 (ns/day, V100) | 500 ns 需要 |
|--------------|------------------------|-------------|
| PfTrpS alpha-beta + 水 (约 60,000) | 80-120 | 4-6 天 |
| PfTrpB 单体 + 水 (约 40,000) | 120-180 | 3-4 天 |

---

# Part III: MetaDynamics Execution (增强采样)

---

## 第十章：AMBER --> GROMACS 转换

### 10.1 为什么需要转换

Osuna 的工作流程：

```
AMBER (ff14SB) --> 常规 MD 500 ns --> [转换] --> GROMACS + PLUMED2 --> MetaDynamics
```

- 常规 MD 用 AMBER：GPU 加速 (pmemd.cuda) 性能极好
- MetaDynamics 用 GROMACS + PLUMED2：原文做法，PLUMED2 和 GROMACS 集成最成熟

> **能不能全用 AMBER？** 技术上可以（AMBER 也能和 PLUMED2 接口），但不是原文做法，严格复刻应该用 GROMACS。

### 10.2 ParmEd 转换

```python
import parmed as pmd

# 读取 AMBER 文件
amber = pmd.load_file('pftrps_ain.parm7', 'pftrps_ain_equil_last.rst7')

# 保存为 GROMACS 格式
amber.save('pftrps_ain.top')      # GROMACS topology
amber.save('pftrps_ain.gro')      # GROMACS coordinates
```

### 10.3 能量验证（转换后必做）

```bash
# GROMACS 单点能量计算
gmx grompp -f energy_check.mdp -c pftrps_ain.gro -p pftrps_ain.top -o energy_check.tpr
gmx mdrun -s energy_check.tpr -nsteps 0 -rerun pftrps_ain.gro
```

比较 AMBER 和 GROMACS 的键能、角能、van der Waals 能、静电能。

预期差异：由于 1-4 相互作用处理方式略有不同，总能量可能有 约 0.1-1.0 kcal/mol 的差异。如果差异 > 10 kcal/mol，说明转换有问题。

### 10.4 非标准残基的已知痛点

| 问题 | 表现 | 解决方案 |
|------|------|---------|
| 原子类型映射失败 | GROMACS 拓扑中出现未知原子类型 | 手动检查 .top 中的 [ atomtypes ] |
| 1-4 scaling factor 不一致 | 能量差异大 | AMBER ff14SB: 1-4 EE = 1/1.2, 1-4 VDW = 1/2.0；确认 GROMACS top 一致 |
| 残基名识别问题 | GROMACS 不认识 LLP | 确认 ParmEd 正确处理了 |

---

## 第十一章：PLUMED 输入文件解读

### 11.1 PLUMED 是什么

PLUMED 是一个增强采样插件，"装在" GROMACS 上面。GROMACS 负责跑基础的 MD（算力、更新位置），PLUMED 负责在 CV 空间里"放砖头"（加偏置势）。

### 11.2 PLUMED 输入文件结构

```
# plumed.dat -- TrpB Well-Tempered MetaDynamics

# 1. 定义原子组
COMM: GROUP ATOMS=...        # COMM domain Calpha atoms (res 97-184)
BASE: GROUP ATOMS=...        # Base region Calpha atoms (res 282-305)
ALLCA: GROUP ATOMS=COMM,BASE # 所有用于 Path CV 的原子

# 2. 定义 Path CV
path: PATHMSD ...
   REFERENCE=reference_path.pdb  # 15 帧 O-->C 路径
   LAMBDA=0.029                  # 平滑因子
   NEIGH_SIZE=-1                 # 使用所有参考帧
   NEIGH_STRIDE=-1

# 3. 定义 MetaDynamics 偏置
METAD ...
   LABEL=metad
   ARG=path.sss,path.zzz       # 偏置的 CV：s(R) 和 z(R)
   SIGMA=0.5,0.05               # 高斯宽度（自适应时为初始值）
   HEIGHT=0.15                   # 初始高斯高度 (kcal/mol)
   PACE=1000                     # 每 1000 步 = 每 2 ps 放一个高斯
   BIASFACTOR=10                 # bias factor gamma = 10
   TEMP=350                      # 温度 350 K
   FILE=HILLS                    # 输出文件
... METAD

# 4. 输出监测量
PRINT ARG=path.sss,path.zzz,metad.bias STRIDE=500 FILE=COLVAR
```

> **FP-001 教训**：MetaD 只偏置 2 个 Path CV: s(R) 和 z(R)。K82-Q2 距离和 E104-Q2 距离是**监测指标**，不参与偏置。不要混淆 METAD 里的 ARG（被偏置的 CV）和 PRINT 里的 ARG（被记录的监测量）。

### 11.3 关键参数对照

| PLUMED 关键词 | SI 值 | 含义 |
|--------------|-------|------|
| `HEIGHT` | 0.15 kcal/mol | 初始高斯高度 |
| `PACE` | 1000 (步) | 每 2 ps 放一个高斯 (dt=2 fs, 1000*2fs=2ps) |
| `BIASFACTOR` | 10 | Well-tempered 参数 gamma |
| `TEMP` | 350 (K) | 模拟温度 |
| `SIGMA` | adaptive | 高斯宽度（自适应调整） |

---

## 第十二章：Well-Tempered MetaDynamics 设置

### 12.1 Gaussian 参数详解

| 参数 | 值 | 含义 | 类比 |
|------|---|------|------|
| 初始高斯高度 | 0.15 kcal/mol | 每块"砖头"的初始高度 | 砖头的厚度 |
| 高斯沉积间隔 | 2 ps | 每隔多久放一块砖头 | 放砖头的频率 |
| 偏差因子 gamma | 10 | 砖头衰减速率 | gamma 越大，探索越充分但收敛越慢 |
| 高斯宽度 | Adaptive | 根据局部 FES 自动调整 | 砖头的"面积" |
| 温度 | 350 K | *P. furiosus* 的生理温度 | -- |

### 12.2 GROMACS MDP 参数

```
; md.mdp for MetaDynamics run (GROMACS)
integrator               = md
dt                       = 0.002        ; 2 fs timestep
nsteps                   = 50000000     ; 100 ns per walker
nstxout-compressed       = 5000         ; save every 10 ps

; Temperature coupling
tcoupl                   = v-rescale
tc-grps                  = Protein Non-Protein
tau_t                    = 0.1 0.1
ref_t                    = 350 350

; Pressure (NVT for production MetaD)
pcoupl                   = no

; Electrostatics
coulombtype              = PME
rcoulomb                 = 0.8          ; 8 A cutoff (matching SI)
rvdw                     = 0.8

; Constraints
constraints              = h-bonds
constraint-algorithm     = LINCS

; PBC
pbc                      = xyz
```

### 12.3 运行命令

```bash
# 在 Longleaf 上
module load anaconda/2024.02
conda activate trpb-md

# GROMACS 预处理
gmx grompp -f md.mdp -c pftrps_ain.gro -p pftrps_ain.top -o metad.tpr

# 运行（带 PLUMED）
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK   # FP-006 教训
gmx mdrun -s metad.tpr -plumed plumed.dat -ntomp $OMP_NUM_THREADS
```

> **FP-006 教训**：Longleaf Slurm 默认 `OMP_NUM_THREADS=1`。GROMACS `-ntomp N` 要求 OMP=N，不一致时 fatal error。所有 Slurm 脚本必须包含 `export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK`。

---

## 第十三章：多 Walker MetaDynamics

### 13.1 起始构象选取

10 个 walker 需要 10 个不同的起始构象。获取方式：
1. 先跑一次短的单 walker MetaDynamics
2. 从中提取 10 个 snapshot，覆盖 O/PC/C 整个构象空间
3. 每个 snapshot 作为一个 walker 的起始结构

### 13.2 Multi-Walker 技术实现

PLUMED 通过 `WALKERS_MPI` 或 `WALKERS_DIR` 机制实现多 walker 通信：

```
# plumed.dat for multi-walker
METAD ...
   LABEL=metad
   ARG=path.sss,path.zzz
   SIGMA=0.5,0.05
   HEIGHT=0.15
   PACE=1000
   BIASFACTOR=10
   TEMP=350
   FILE=HILLS
   WALKERS_DIR=../          # 所有 walker 共享 HILLS 文件
   WALKERS_N=10             # 总共 10 个 walker
   WALKERS_ID=0             # 当前 walker 的 ID (0-9)
... METAD
```

### 13.3 运行规模

| 参数 | 值 |
|------|---|
| Walker 数量 | 10 |
| 每个 Walker 时长 | 50-100 ns |
| 总采样时间 | 500-1000 ns per system |
| 累积 wall-clock 等效 | 约 7 microseconds per system |

---

# Part IV: 分析与验证 (Analysis & Validation)

---

## 第十四章：FES 重构

### 14.1 从 HILLS 到 FES

所有 walker 的 HILLS 文件（记录每个高斯的位置、高度、宽度）被汇总，然后用 PLUMED `sum_hills` 重构 FES：

```bash
plumed sum_hills --hills HILLS.0,HILLS.1,...,HILLS.9 \
    --outfile fes.dat \
    --mintozero \
    --bin 100,100
```

### 14.2 Python 可视化

```python
import numpy as np
import matplotlib.pyplot as plt

# 读取 FES 数据
data = np.loadtxt('fes.dat')
s = data[:, 0]
z = data[:, 1]
fes = data[:, 2]

# 转换为网格
n = int(np.sqrt(len(s)))
S = s.reshape(n, n)
Z = z.reshape(n, n)
FES = fes.reshape(n, n)

# 画图
fig, ax = plt.subplots(figsize=(8, 6))
contour = ax.contourf(S, Z, FES, levels=20, cmap='RdYlBu_r')
plt.colorbar(contour, label='Free Energy (kcal/mol)')
ax.set_xlabel('s(R) [Progress: 1=Open, 15=Closed]')
ax.set_ylabel('z(R) [Deviation from reference path]')
ax.set_title('Free Energy Landscape - PfTrpS(Ain) at 350 K')
plt.savefig('fes_trpb.png', dpi=300)
```

---

## 第十五章：Productive vs Unproductive Closure 判断标准

### 15.1 两个判据

| 判据 | 阈值 | 怎么测量 |
|------|------|---------|
| COMM domain RMSD from reference path | **< 1.5 A** | 将 closed 构象和 3CEP 做 RMSD |
| K82 到 Q2 中间体的距离 | **<= 3.6 A** | 测量 NZ 到 Q2 的距离 |

两个条件**同时满足**才算 productive closure。

### 15.2 三个体系的对比标准

| 体系 | K82-Q2 距离 | RMSD from path | 判定 |
|------|------------|----------------|------|
| PfTrpS | 约 3.6 A | < 1.5 A | Productive |
| PfTrpB | 3.9 +/- 0.3 A | > 1.5 A | **Unproductive** |
| PfTrpB0B2 | 约 3.6 A | < 1.5 A | Productive |

> **0.3 A 的差距听起来很小，但在催化化学中是决定性的**：质子转移反应对距离极度敏感，3.6 A 可以发生但 3.9 A 不行。

---

## 第十六章：收敛性检查

### 16.1 原文的做法

- 监测 Open 和 Closed 局部最小值之间的能量差随模拟时间的变化（Figure S4/S5）
- 对于只有单一能量最小值的体系，比较最小值和高能区域的能量差
- Qualitative assessment：能量差在后期趋于平稳即认为收敛

### 16.2 我们应该做的（更严格）

1. **Block analysis**：将轨迹分成若干块，每块独立重构 FES，看 block 间的方差
2. **时间演化图**：画 Delta-G vs simulation time 的曲线，确认后半段平稳
3. **多 walker 一致性**：检查不同 walker 是否探索了相同的构象空间

### 16.3 复刻容差

| 指标 | 容差 | 说明 |
|------|------|------|
| 能垒高度差异 | **< 1.5 kcal/mol** | Well-tempered MetaD 的典型统计误差 |
| 能量盆位置 s(R) | **< 1 单位** | 15-frame path 的分辨率 |
| O/PC/C 相对稳定性 | 定性一致 | 必须一致 |

---

# Part V: 流程管控 (Pipeline & Quality Control)

---

## 第十七章：6-Stage Pipeline 详解

### 17.1 核心原则

> **分离三种决策**：科学决策（测什么、为什么）、执行决策（怎么跑软件）、下游集成声明（结果对 pipeline 意味着什么）。三者不能混为一谈。

### 17.2 Pipeline 总览

| # | Stage | 做什么 | 什么时候停下等人审批 |
|---|-------|--------|---------------------|
| 0 | **Profiler** | 论文 --> frozen manifest | **必须停。Manifest 需要人签字** |
| 1 | **Librarian** | 盘点资源，找缺失 | 缺资源或无权限时 |
| 2 | **Janitor** | 整理目录结构 | 路径冲突时 |
| 3 | **Runner** | 生成脚本 / 提交作业 | 参数不确定时 |
| 4 | **Skeptic** | 验证运行结果 | 科学有效性不确定时 |
| 5 | **Journalist** | 写 campaign report | 不需要停 |

### 17.3 当前 Campaign 状态

| Campaign | Status | Next Stage |
|----------|--------|------------|
| JACS 2019 benchmark reproduction | Librarian done (2026-03-30) | Janitor |
| GenSLM-230 vs NdTrpB comparison | Blocked on benchmark | -- |

### 17.4 Frozen Manifest 必须包含

1. Campaign mode (benchmark_reproduction / mechanism_comparison / etc.)
2. Research question（一句话）
3. Systems under study
4. CV definition
5. Software stack
6. Readouts to measure
7. Success criteria（具体数字）
8. Downstream consumer
9. Known blockers

### 17.5 错误处理规则

> **发现事实错误、脚本 bug、参数不匹配，必须做三件事：**
>
> 1. **修源文件**
> 2. **追加 failure-patterns.md**（FP-XXX 条目）
> 3. **写 validation note**（在 replication/validations/ 下）

---

## 第十八章：已知错误模式 (Failure Patterns)

以下是项目中已经发生过的错误，汇总为经验教训：

| FP # | 错误 | 根因 | 防范措施 |
|------|------|------|---------|
| FP-001 | 混淆 biased CV 和 monitoring metric | AI 没区分"偏置"和"监测" | 明确区分 METAD ARG 和 PRINT ARG |
| FP-002 | SHAKE/SETTLE 约束描述不精确 | 不精确的 shorthand | 写全：SHAKE constrains bonds involving H; SETTLE constrains water geometry |
| FP-003 | PDB 原子名不匹配力场定义 | 凭记忆写 PDB 坐标 | **永远不要凭记忆写 PDB 原子名** |
| FP-004 | PLUMED 原子索引与拓扑不匹配 | 基于原始 PDB 写索引 | **PLUMED 索引必须从 pdb2gmx 输出的 .gro 确定** |
| FP-005 | 体系-中间体分配错误 | 混淆了不同体系的中间体 | 每行对应唯一的 (system, intermediate) pair |
| FP-006 | OMP_NUM_THREADS 与 GROMACS -ntomp 冲突 | Slurm 默认 OMP=1 | **所有 Slurm 脚本必须 export OMP_NUM_THREADS** |
| FP-007 | conda 激活路径硬编码错误 | 不知道 Longleaf 的加载方式 | 统一用 `module load anaconda/2024.02 && conda activate trpb-md` |
| FP-008 | 报告温度标注与实际运行温度不符 | 从项目级别推断而非从 MDP 读取 | **参数必须从实际运行文件读取** |
| FP-009 | **BCC 对 PLP SCF 不收敛** | AM1 处理不了磷酸+共轭体系 | **PLP 不能用 BCC，必须走 RESP** |
| FP-010 | **无氢 PDB 的原子类型错误** | antechamber 需要氢来判断芳香性 | **先 reduce 加氢再运行 antechamber** |
| FP-011 | 跳过 pipeline stage 直接执行 | 急于推进进度 | **Librarian --> Janitor --> Runner 不能跳过** |

**通用规则**：

1. 写任何文件前，先读 failure-patterns.md
2. 区分"看到的"和"确认的"：标注信息来源
3. 不要凭记忆写结构数据
4. 索引类数据必须从实际输出确认
5. 报告中的参数必须从运行文件读取

---

## 第十九章：所有 SI 参数汇总表

### 19.1 System Preparation

| Item | Value | Source |
|------|-------|--------|
| Starting structure | PDB 1WDW (open PfTrpS) | SI p.S2 |
| Complex | alpha-beta heterodimer | SI p.S2 |
| Isolated TrpB | Manually remove TrpA | SI p.S2 |
| PfTrpB0B2 mutations | Introduced with RosettaDesign | SI p.S2 |
| Intermediates | Ain, Aex1, A-A, Q2 | SI p.S2 |

### 19.2 Ligand Parameterization

| Item | Value | Source |
|------|-------|--------|
| Software | Antechamber (AMBER16) | SI p.S2 |
| Force field | **GAFF** | SI p.S2 |
| Charge method | RESP | SI p.S2 |
| QM level | HF/6-31G(d) | SI p.S2 |
| QM software | Gaussian09 (we use Gaussian 16c02) | SI p.S2 |

### 19.3 Conventional MD

| Parameter | Value | Source |
|-----------|-------|--------|
| Software | AMBER16 (we use AMBER 24p3) | SI p.S2 |
| Protein force field | **ff14SB** | SI p.S2 |
| Water model | **TIP3P** | SI p.S2 |
| Box type | **Cubic** (solvatebox, not solvateoct) | SI p.S2 |
| Buffer distance | **10 A** | SI p.S2 |
| Approximate water molecules | approximately 15,000 | SI p.S2 |
| Neutralization | Explicit counterions (Na+ or Cl-) | SI p.S2 |

**Minimization**

| Stage | Description | Source |
|-------|-------------|--------|
| 1 | Solvent + ions minimized; protein restrained at 500 kcal/mol/A^2 | SI p.S2 |
| 2 | Unrestrained full system | SI p.S2 |

**Heating**

| Parameter | Value | Source |
|-----------|-------|--------|
| Steps | 7 x 50 ps (0-->350 K, 50 K increments) | SI p.S2 |
| Ensemble | NVT | SI p.S2 |
| Timestep | 1 fs | SI p.S2 |
| Restraints | Decreasing: 210, 165, 125, 85, 45, 10 kcal/mol/A^2 | SI p.S2 |
| Thermostat | Langevin | SI p.S2 |

**Equilibration**

| Parameter | Value | Source |
|-----------|-------|--------|
| Duration | 2 ns | SI p.S2 |
| Ensemble | NPT | SI p.S2 |
| Pressure | 1 atm | SI p.S2 |
| Temperature | **350 K** | SI p.S2 |
| Timestep | 2 fs | SI p.S2 |

**Production**

| Parameter | Value | Source |
|-----------|-------|--------|
| Duration | 500 ns per system | SI p.S2-S3 |
| Ensemble | NVT | SI p.S2-S3 |
| Timestep | 2 fs | SI p.S2-S3 |
| Temperature | **350 K** | SI p.S2-S3 |
| Electrostatics | PME | SI p.S2-S3 |
| Cutoff | 8 A | SI p.S2-S3 |

### 19.4 Well-Tempered MetaDynamics

| Parameter | Value | Source |
|-----------|-------|--------|
| CV type | Path CV: s(R) and z(R) | SI p.S3 |
| Reference path | 15 frames, 1WDW (Open) --> 3CEP (Closed) | SI p.S3 |
| Atoms for path | Calpha of COMM (97-184) + base (282-305) | SI p.S3 |
| Lambda | 2.3 x (1/MSD between frames) ≈ 0.029 | SI p.S3 |
| MetaDynamics software | **PLUMED 2 + GROMACS 5.1.2** | SI p.S3 |
| Initial Gaussian height | **0.15 kcal/mol** | SI p.S3 |
| Deposition pace | **Every 2 ps** | SI p.S3 |
| Bias factor (gamma) | **10** | SI p.S3 |
| Gaussian width | **Adaptive** | SI p.S3 |
| Number of walkers | **10** | SI p.S3 |
| Time per walker | **50-100 ns** | SI p.S3 |
| Total sampling per system | **500-1000 ns** | SI p.S3 |

### 19.5 SI Gaps Identified

| Gap | Severity | Status |
|-----|----------|--------|
| Protonation states (K82, PLP, His) | **HIGH** | `[待 PI 确认]` |
| PLP-K82 covalent bond treatment during RESP | **HIGH** | `[待 PI 确认]` |
| AMBER-->GROMACS conversion method | HIGH | Plan to use ParmEd |
| Missing residues in 1WDW | MEDIUM | Need to check PDB REMARK 465 |
| 7 heating steps vs 6 restraint values | LOW | 7th step uses last value (10) |
| Minimization step counts | LOW | Use 5000/10000 (standard) |
| Barostat type | LOW | Berendsen (AMBER default) |
| Capping strategy (ACE/NME) | MEDIUM | Standard practice, assume used |
| Gaussian optimization: freeze backbone? | MEDIUM | Usually not frozen |

---

## 第二十章：待决事项与 PI Meeting 议题

### 20.1 需要 PI 决策的问题（按优先级）

**Priority 1: 必须在开始 Gaussian 计算前确定**

| # | 问题 | 推荐 | 备选 |
|---|------|------|------|
| 1 | Ain 中间体的总电荷是 -1 还是 -2？ | **-1**（Schiff base 质子化） | -2（去质子化） |
| 2 | 磷酸是 -1 还是 -2？ | **-2**（pH 7.5 下双阴离子） | -1 |
| 3 | Phase 1 只做 Ain 还是同时做 Aex1？ | **先只做 Ain** | 同时做 |

**Priority 2: 可以在计算过程中决定**

| # | 问题 | 推荐 | 备选 |
|---|------|------|------|
| 4 | 用 GAFF 还是 GAFF2？ | **GAFF**（严格复刻，SI 说 GAFF） | GAFF2 |
| 5 | Gaussian 几何优化后做 frequency check？ | 做 | 不做 |
| 6 | RESP 电荷不合理怎么办？ | 调整质子化状态重算 | 联系 Osuna 组 |

### 20.2 可以通过文献检索解决的问题

| 问题 | 推荐文献 | 预计结论 |
|------|---------|---------|
| PLP Schiff base 质子化态 | Toney 2011; Casasnovas 2014 | Internal aldimine Schiff base N 质子化 (pKa 约 10) |
| PLP 磷酸 pKa | Metzler & Snell; Eliot & Kirsch 2004 | 双阴离子 at pH 7.5 |
| RESP 电荷 PLP 的先例 | 搜索 "PLP RESP AMBER parameterization" | 可能找到已发表的参数 |

### 20.3 推荐 PI 会议议程

1. **5 min**：项目进度概述（alanine dipeptide 验证通过，PLP 参数化是下一步）
2. **10 min**：PLP 质子化状态讨论（第七章 7.5 节，需要 PI 决策）
3. **5 min**：Phase 1 范围确认（只做 Ain？）
4. **5 min**：时间线讨论
5. **5 min**：其他 SI gaps 的处理策略

### 20.4 当前项目状态总览

| Milestone | Status |
|-----------|--------|
| Paper reading materials | Speed-brief ready |
| Resource inventory (PDBs, PDFs, SI) | Done |
| MetaDynamics parameters extraction | Done |
| SI protocol extraction | Done |
| Full Logic Chain document | Done |
| PLP + System Setup Logic Chain | Done |
| Longleaf HPC setup (AMBER, GROMACS, PLUMED) | Done |
| PDB residue name verification | Done |
| Alanine dipeptide toy test | **Done** -- GROMACS+PLUMED2 validated |
| PLP parameterization (GAFF+RESP) | **Script ready, not executed** |
| O-->C reference path (15 frames) | NOT STARTED |
| Conventional MD (500 ns) | NOT STARTED |
| Well-tempered MetaD | NOT STARTED |

### 20.5 预计时间线

| 任务 | 前置条件 | 预计耗时 | 累计 |
|------|---------|---------|------|
| PI 确认质子化状态 | 本文档 | 1 次会议 | Day 0 |
| 提取 LLP + 加氢 + capping | PI 决策 | 2-3 小时 | Day 1 |
| antechamber + Gaussian | 上一步 | 等 2-8 小时 | Day 1-2 |
| RESP 电荷 + parmchk2 + 验证 | Gaussian 完成 | 1-2 小时 | Day 2 |
| tleap 体系组装 | mol2 + frcmod | 2-3 小时 | Day 2-3 |
| 最小化 + 加热 + 平衡 | parm7 + inpcrd | 等约 2 小时 | Day 3 |
| 500 ns 产出 MD | 平衡完成 | **4-6 天** (GPU) | Day 4-10 |
| AMBER --> GROMACS 转换 + 验证 | MD 完成 | 2-3 小时 | Day 10 |
| **总计（乐观）** | | **约 10 天** | |
| **总计（保守）** | | **2-3 周** | |

> 保守估计原因：tleap 报错、电荷不平衡、能量验证不通过等问题可能让每一步多花 1-2 天。

---

# 附录

---

## 附录 A：Software Stack 对照

| Component | Paper version | Our version | Status | Longleaf command |
|-----------|-------------|-------------|--------|-----------------|
| AMBER | AMBER16 | **AMBER 24p3** | Verified | `module load amber/24p3` |
| GROMACS | GROMACS 5.1.2 | **GROMACS 2026.0** | Verified (PLUMED-patched) | `conda activate trpb-md` |
| PLUMED | PLUMED 2 | **PLUMED 2.9** | Verified | `conda activate trpb-md` |
| Gaussian | Gaussian09 | **Gaussian 16c02** | Verified | `module load gaussian/16c02` |
| antechamber | AmberTools 16 | **AmberTools 24p3** | Verified | Included in amber/24p3 |
| parmchk2 | AmberTools 16 | **AmberTools 24p3** | Verified | Included in amber/24p3 |
| tleap | AmberTools 16 | **AmberTools 24p3** | Verified | Included in amber/24p3 |

## 附录 B：PDB 结构清单

| PDB | Description | Role | Status |
|-----|------------|------|--------|
| 1WDW | Open PfTrpS | Starting structure + Path CV Open endpoint | Downloaded |
| 3CEP | Closed StTrpS | Path CV Closed endpoint | Downloaded |
| 5DVZ | PfTrpB (Ain, Open) | LLP extraction; RMSD reference | Downloaded |
| 5DW0 | PfTrpB (Aex1, PC) | PLS extraction | Downloaded |
| 5DW3 | PfTrpB (product, PC) | Reference | Downloaded |
| 4HPX | StTrpS (A-A) | 0JO extraction; structural template | Downloaded |
| 5IXJ | PfTrpB (Ain, L-Thr) | Reference | Downloaded |
| 4HN4 | StTrpS closed | Additional C reference | **Not downloaded** |

## 附录 C：核心概念速查表

| 概念 | 一句话解释 |
|------|-----------|
| **TrpB** | 催化"吲哚 + 丝氨酸 --> 色氨酸"的酶 |
| **COMM domain** | TrpB 上可以开关的"盖子"（残基 97-184） |
| **O / PC / C** | Open / Partially Closed / Closed |
| **PLP** | 辅因子，共价连在 K82 上 |
| **Ain, Aex1, A-A, Q2** | PLP 与底物形成的不同催化中间体 |
| **MD** | 用牛顿力学模拟蛋白质原子运动 |
| **MetaDynamics** | 往蛋白质待过的地方加"砖头"的增强采样方法 |
| **Well-Tempered MetaD** | 砖头越放越小的改进版 MetaDynamics |
| **Path CV (s, z)** | s = 沿 O-->C 路径走了多远，z = 偏离路径多远 |
| **FEL** | MetaDynamics 的最终输出：自由能"地形图" |
| **Delta-G(closed)** | Closed 态比 Open 态低多少 kcal/mol |
| **Population shift** | 催化活性 = Closed 构象的群体占比 |
| **Productive closure** | COMM domain 关得正确（K82-Q2 <= 3.6 A + RMSD < 1.5 A） |
| **GAFF** | 非标准小分子力场（用于 PLP） |
| **RESP** | 从量子化学 ESP 拟合原子电荷的方法 |
| **ff14SB** | 蛋白质力场 |
| **GROMACS** | 跑 MD 的软件（用于 MetaDynamics） |
| **PLUMED** | MetaDynamics 插件，装在 GROMACS 上 |
| **AMBER** | 另一个跑 MD 的软件（用于常规 MD 和体系准备） |
| **SPM** | Shortest Path Map，从 MD 轨迹识别别构通讯路径 |
| **GenSLM** | AI 语言模型，生成全新 TrpB 序列 |
| **Longleaf** | UNC 的 HPC 集群 |

## 附录 D：完整 Pipeline 依赖图

```
质子化状态决策 ------+
                     |
PDB (5DVZ) --------- +---> Gaussian RESP --> mol2 + frcmod --+
                     |                                        |
ACE/NME capping ----+                                        |
                                                              |
ff14SB -----------------------------------------------+       |
TIP3P ------------------------------------------------+       |
PDB (1WDW, chain A+B) --------------------------------+       |
                                                       +---> tleap --> parm7 + inpcrd
mol2 + frcmod (from RESP) ----------------------------+
                                                                  |
                                                                  v
                                                        AMBER MD (500 ns)
                                                                  |
                                                                  v
                                                        ParmEd --> GROMACS
                                                                  |
                                                                  v
15-frame path (1WDW --> 3CEP) -----------------------> MetaDynamics (10 walkers)
                                                                  |
                                                                  v
                                                               FEL --> Score
```

## 附录 E：逻辑链总图

```
TrpB 是催化色氨酸合成的酶
    |
    v
它的催化活性取决于 COMM domain 能不能正确关闭
    |
    v
Osuna 用 MetaDynamics 证明了这一点：
FEL 上 Closed 态越稳定 --> 活性越高
    |
    v
aNima Lab 用 GenSLM 生成了 100,000 个新的 TrpB 序列
    |
    v
需要一种方法来筛选哪些序列真的好用
    |
    v
MetaDynamics FEL 就是这个筛选方法：
跑 MetaD --> 得到 FEL --> 看 Closed 态有多稳定 --> 排名
    |
    v
你的工作：
(1) 先复刻 Osuna 的结果，验证方法正确
(2) 再应用到 GenSLM-TrpB 上，筛选最好的候选
(3) 把 FEL 指标做成 reward function，反馈给 GenSLM
```

---

> **最后一句话**：这份文档是整个 TrpB MetaDynamics 复刻项目的完整技术蓝图。最大的不确定性是 PLP 的质子化状态（第七章 7.5 节），需要 PI 确认。一旦质子化状态确定，后续步骤都是标准操作，可以按本文档的代码执行。当前处于"复刻 Osuna 结果"的 Phase 1 中期：基础设施全部搭好，工具链通过 alanine dipeptide 验证，下一步是 PLP 参数化。
