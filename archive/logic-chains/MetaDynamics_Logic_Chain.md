# MetaDynamics × TrpB：完整逻辑链

> 适合读者：有 LiGaMD / 增强采样经验的人，想搞清楚"为什么在 TrpB 上用 MetaDynamics，以及它在整个 pipeline 里起什么作用"。

---

## 一句话版本

**MetaDynamics 是在告诉你：这个酶，在没有任何底物的帮助下，自己能不能打开和关闭活性口袋。能做到的，才可能是好酶。**

---

## 第一部分：为什么要做模拟？为什么不直接做实验？

### 1.1 实验的瓶颈

你拿到一批 AI 设计的 TrpB 候选序列——可能有几百个甚至几千个。每一个都要表达、纯化、测活性，实验成本是每个候选 1–2 周时间 + 数百美元。全测不现实。

计算筛选的目的是**把候选集从几百个压缩到几个**，然后再送实验。

但为什么不能直接用 AlphaFold 预测结构然后看活性位点就完了？

### 1.2 静态结构不够用

AlphaFold 给你的是一个**静态的原子坐标**——酶在某个特定状态下的样子。但酶催化不是发生在一个固定构象上的，而是发生在一个**动态构象转换的过程**中。

TrpB 的催化依赖 COMM domain 的 Open→Closed 转换。这个转换是：
- 不发生在纳秒级（传统 MD 可以采样的时间尺度）
- 是微秒到毫秒级的慢运动

换句话说：**如果直接跑普通 MD，等不到这个转换发生，你什么也看不到。**

> 这和你在 Miao Lab 跑 LiGaMD 的动机是完全一样的：配体结合/解离也是慢过程，标准 MD 采样不到，所以才用增强采样。

### 1.3 所以必须用增强采样

增强采样的核心思路：**人为地给系统加一个偏置势能（bias），帮助它越过能垒，探索原本需要等几毫秒才能到达的构象**。

完成后，把 bias 移除（或数学上校正），就能还原出**真实的自由能面（Free Energy Landscape, FEL）**。

MetaDynamics 是目前最成熟、在酶动力学研究里使用最广的增强采样方法之一。

---

## 第二部分：MetaDynamics 是什么，物理上在做什么？

### 2.1 核心想法

标准 MD 里，系统被困在能量最低点附近，越不过能垒。MetaDynamics 的做法是：

**每隔一段时间，在系统当前位置"垫一块砖头"——往 CV 空间里存放一个 Gaussian 势能包（hill）。**

砖头越积越多，把原来的能量最低点逐渐填平。系统就会被逼着爬出去、探索新的区域。最终，当所有的能量谷都被填平，系统就能自由地跑遍整个构象空间。

这时候，你把所有"垫进去的砖头"加起来取反号，就是原始的自由能面。

```
              原始 FEL                 被 Gaussian 填平后
能量 ↑         ___                         ___________
              |   |                       |           |
         ____|   |___               ______|           |______
        |              |           ↑ 高 Gaussian 填充
  Open  |     能垒     |  Closed       → 系统可以自由穿越
        |_______________|
              CV（COMM 闭合程度）
```

### 2.2 Well-Tempered MetaDynamics：不是普通 MetaD，而是更聪明的版本

普通 MetaDynamics 有个问题：砖头越加越多，FEL 会过度填平，结果不收敛。

**Well-Tempered（良温 MetaDynamics）** 的改进：随着模拟推进，每次新加的 Gaussian 高度会**逐渐减小**。加得越多的地方，新砖头越矮。系统探索新区域时砖头高，探索过的区域砖头低。最终会收敛到一个稳定的 FEL。

控制这个"降温速率"的参数叫做 **bias factor（γ = 10）**。

> γ 越大 → 砖头降温越慢 → 探索越激进 → 适合能垒大的系统
> γ 越小 → 降温越快 → 保守但精确 → 适合能垒小的系统
> **原文用 γ = 10** — 对应 COMM domain 这种 ~6 kcal/mol 能垒，选择合理。

### 2.3 Gaussian 参数的物理意义

| 参数 | 原文值 | 物理意义 |
|------|--------|---------|
| Height | 0.15 kcal/mol | 每块砖头的"高度"。太高→不精确；太低→填平太慢 |
| Pace | 每 2 ps | 多久加一块砖头。2 ps = 1000 MD steps（2 fs timestep）|
| Adaptive Gaussian width | 自适应 | 砖头的宽度根据局部 FEL 曲率自动调整，平坦区域宽，陡峭区域窄 |
| Bias factor γ | 10 | 控制砖头高度的衰减速率 |

---

## 第三部分：为什么用 Path CV？而不是普通 RMSD？

### 3.1 COMM domain 的运动不是简单的"开"和"关"

如果只用一个 RMSD（COMM domain 对参考闭合态的 RMSD），你只能知道"离闭合态有多远"。但 COMM domain 的转换是一个**多维空间中的运动**，可能有很多条路径，有些是生物学相关的，有些是随机的偏离。

**Path Collective Variable（路径 CV）** 的解决方案：

先用 X-ray 数据给出一条参考路径（15 个构象帧，从 Open 到 Closed 的 Cα 线性插值），然后定义两个 CV：

```
s(R) = 路径进度（1 = Open, 15 = Closed）
         → 告诉你系统在路径上走到哪了

z(R) = 到路径的均方偏差（MSD）
         → 告诉你系统偏离了这条参考路径多少
```

二维 FEL 就是 s 和 z 组成的平面上的自由能地图。

```
z ↑  偏离路径
    |
2.5 |    O basin
2.0 |         \
1.5 |          PC basin
1.0 |              \
0.5 |               C basin
    |________________________→ s（路径进度）
     1   5   10   15
```

**为什么这比单 RMSD 好？**
- 它描述的是"沿着一条有生物学意义的轨迹的进度"，而不只是"离某个参考态有多远"
- z 轴告诉你系统是否在生物学相关路径附近（z 小）还是随机乱晃（z 大）
- 能区分 O、PC、C 三个状态，而不只是"开"和"关"

### 3.2 参考路径怎么来的？

1WDW（PfTrpS 晶体结构，COMM Open）→ 3CEP（StTrpS 晶体结构，COMM Closed） 之间的 Cα 原子做**线性插值**，得到 15 个中间构象。

使用的原子：
- COMM domain: 残基 97–184（Cα）
- Base region: 残基 282–305（Cα）

λ 参数（控制路径 CV 的分辨率）= 2.3 / MSD_between_frames，其中相邻帧的 MSD = 80。

---

## 第四部分：MetaDynamics 在这个项目里具体干什么？

### 4.1 输入是什么

- 一个经过充分平衡的 TrpB 结构（500 ns 普通 MD 之后的快照）
- GROMACS topology + 坐标文件
- PLUMED 输入文件（定义 Path CV + Well-tempered MetaD）

### 4.2 输出是什么

一张 **2D 自由能地图（FEL）**：

```
z (Å) ↑                              ΔG (kcal/mol)
2.5   |  · · · · · · · · · · · ·   ■ -6 ~ -4  深蓝（最稳定）
2.0   | [O]  · · ·                  □ -2 ~ 0
1.5   |       · ·                   □  0 ~ 2
1.0   |        [PC] · ·             □  2 ~ 4   红（高能量）
0.5   |              · [C]
      |__________________→ s(R)
         1  3  5  7  9  11  13  15
```

从这张图读出来的信息：
- **O 位置的能量深不深？** → TrpB 在 Ain 中间体时，O state 稳定，这是正常的
- **C 位置有没有能量井？** → 如果在 Q₂ 中间体时，C state 有深的能量井，说明这个酶能有效闭合
- **PC→C 的能垒是多少？** → 原文中 PfTrpS(Q₂) 的 PC→C 能垒 ~6 kcal/mol，PfTrpB⁰ᴮ²(Q₂) 只有 ~2 kcal/mol
- **结合 K82-Q₂ 距离** → 闭合态下 K82 和 Q₂ 中间体的质子转移距离 ≤ 3.6 Å，说明活性位点预组织好了

### 4.3 判断一个候选 TrpB "好不好"的标准

| 指标 | 好候选 | 坏候选 |
|------|--------|--------|
| Q₂ 时 C state 能量 | 有深的能量井（≤ -2 kcal/mol relative） | 没有 C 极小值，或极浅 |
| PC→C 能垒 | ≤ 5 kcal/mol | > 8 kcal/mol（无法越过） |
| K82-Q₂ 距离 | ≤ 3.6 Å 在 C state | > 5 Å（活性位点不对） |
| FEL 覆盖性 | 采样到 O、PC、C | 只采样到 O 附近（收敛不足或太僵硬） |

---

## 第五部分：整个项目的逻辑链

```
【aNima Lab 产出的 AI 设计 TrpB 序列】
              ↓
【AlphaFold2 结构预测（tAF2，reduced MSA）】
   → 筛选掉结构折叠明显错的候选
              ↓
【普通 MD（500 ns, AMBER ff14SB, 350 K）】
   → 平衡体系；初步看 COMM 是否卡死
              ↓
【Well-tempered MetaDynamics（GROMACS + PLUMED2）】   ← 你现在要复刻的步骤
   → 重建 FEL；量化 O/PC/C 稳定性
   → 每个候选产出一张 2D 自由能图
              ↓
【筛选：FEL 指标通过的候选送实验】
   → 预计从几十个候选中留下 3-10 个
              ↓
【湿实验室验证（大肠杆菌表达 + HPLC）】
```

**你现在复刻的不是终点——是"筛选步骤"本身**。一旦这个步骤跑通，它就变成一个可以批量应用的工具，用来评估任何 AI 设计出来的 TrpB 候选序列。

---

## 第六部分：为什么 MetaDynamics 能预测催化活性？

这是最核心的科学假设，也是 Osuna Lab 这一系列论文的根本贡献。

### 6.1 Population Shift Paradigm（构象群体转移范式）

酶不是在一个固定构象下工作的。它在溶液中持续采样一个构象系综（ensemble）。关键在于：**催化活性正比于催化活性构象在系综中的占比**。

用自由能语言说：某个构象的 Boltzmann 占比 ∝ exp(-ΔG / kT)。

如果 Closed state 的自由能比 Open state 低 4 kcal/mol，那么在 350 K 下：

```
Population(C) / Population(O) = exp(4 / (0.001987 × 350)) ≈ exp(5.75) ≈ 313x
```

闭合态的占比是开放态的 300 多倍。这个酶会很活跃。

反过来，如果 Closed state 根本没有稳定的能量井，酶很少采样到闭合构象，K82 和 Q₂ 就凑不到一起，催化效率极低。

### 6.2 为什么不用 docking 或 QM/MM？

- **Docking** 只看静态活性位点，完全忽略 COMM domain 动力学
- **QM/MM** 可以算化学步骤的能垒，但极度昂贵，且无法采样慢构象转换
- **MetaDynamics FEL** 直接量化构象动力学，计算成本适中，且与实验 kcat 有很强的相关性（Osuna 2019 Fig 3, 2021 Table S1 验证了这一点）

---

## 第七部分：你的 LiGaMD 经验在这里的映射

你在 Miao Lab 跑过 LiGaMD。两者对比：

| 方面 | LiGaMD（Miao Lab） | MetaDynamics（这个项目） |
|------|-------------------|-----------------------|
| 增强采样目标 | 配体结合/解离（ligand binding） | COMM domain 开关（conformational） |
| 偏置施加的位置 | 配体势能（整体加速） | 选定 CV 方向（定向偏置） |
| 输出 | 结合/解离路径 + ΔG | FEL 能量图 + 各态稳定性 |
| CV 设计 | 不需要预设 CV | 必须精心定义 Path CV |
| 软件 | AMBER + GaMD模块 | GROMACS + PLUMED2 |
| 校正方法 | Reweighting（cumulant expansion） | Sum_hills 积分 |

**核心相似点**：你已经理解了"为什么普通 MD 不够用"、"偏置势能的作用"和"如何从增强采样还原真实自由能"。MetaDynamics 在这些方面的物理直觉和 LiGaMD 是完全一致的。

---

## 快速参考：本项目 MetaDynamics 核心参数

```
软件:        GROMACS 5.1.2 + PLUMED 2
力场:        ff14SB（蛋白）+ GAFF+RESP（PLP 辅酶）
水模型:      TIP3P，cubic box，10 Å buffer
温度:        350 K（嗜热古菌 Pyrococcus furiosus）

Gaussian height:  0.15 kcal/mol
Gaussian width:   自适应（adaptive，根据 FEL 局部曲率）
Deposition pace:  每 2 ps 加一个
Bias factor γ:    10

Path CV:
  帧数: 15（Open 到 Closed 线性插值）
  Open  endpoint: PDB 1WDW（PfTrpS 开放态）
  Closed endpoint: PDB 3CEP（StTrpS 闭合态，Q analogue）
  原子选择: Cα of residues 97–184（COMM）+ 282–305（base）
  λ = 2.3 / 80 ≈ 0.029

Multiple walkers:
  10 个 replica，每个 50–100 ns
  每个系统总采样量: 500–1000 ns（~7 μs 等效壁钟时间）

系统: 3 × 4 = 12 个系统
  3 变体（PfTrpS, PfTrpB WT, PfTrpB⁰ᴮ²）× 4 中间体（Ain, Aex1, A-A, Q₂）
```

---

*文档位置: project-guide/MetaDynamics_Logic_Chain.md*
*最后更新: 2026-03-27*
