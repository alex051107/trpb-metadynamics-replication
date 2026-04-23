# TrpB MetaDynamics 复刻项目：完整技术指南

> **⚠️ 2026-04-23 Miguel Iglesias-Fernández 直接确认 MetaD 方案**：原文作者邮件给出权威版本。若本文其余章节（尤其 §MetaDynamics 参数、Path CV λ、`ADAPTIVE=GEOM`、`SIGMA_MIN/MAX`、single-walker 50 ns）与以下合同矛盾，**以 Miguel 合同为准**：
>
> - `UNITS LENGTH=A ENERGY=kcal/mol`（SI 数值本就是 Å + kcal/mol，不要再乘 100 或 4.184）
> - `ADAPTIVE=DIFF SIGMA=1000`（1000 **步** 的时间窗，≈ 2 ps；不是 Gaussian 宽度）
> - `HEIGHT=0.15 kcal/mol`、`BIASFACTOR=10`、`PACE=1000`、`TEMP=350`
> - `WALKERS_N=10` 并行（SI 原文即 10 walker，single-walker 只是 fallback）
> - `UPPER_WALLS ARG=p1.zzz AT=2.5 KAPPA=800`（Å, kcal/mol）
> - `WHOLEMOLECULES ENTITY0=1-39268` 每步重拼
> - `PATHMSD LAMBDA=3.77 Å⁻²`（= 379.77 nm⁻²，基于我们 15 帧路径的 ⟨MSD⟩ ≈ 0.61 Å² 所得。Miguel 自己的 `LAMBDA=80 Å⁻²` 是给他更密集路径用的，不能照搬。）
>
> 权威来源：`replication/metadynamics/miguel_2026-04-23/miguel_email.md` + FP-031 + FP-032（`replication/validations/failure-patterns.md`）。所有旧版 `ADAPTIVE=GEOM / SIGMA_MIN,MAX` 叙述都是基于 SI 含糊措辞的误读，已记录为 failure pattern 不再展开。

这份文档回答一个核心问题：如果你现在加入这个项目，如何从科学背景一路走到可以在 Longleaf 上提交 TrpB 的 MetaDynamics 复刻任务。本文以仓库内已经确认的 `Runner` 阶段事实为准，特别是 Ain/LLP 的 `RESP` 参数化、`Path CV` 定义和 `Longleaf` 实操约束。

本文默认读者具备基础的物理化学、蛋白质结构和命令行能力，但不预设你已经做过 `MD` 或 `MetaDynamics`。中文负责解释逻辑与化学原因，英文负责技术术语、命令、文件名与引用。

---

## 第一部分：科学背景

这一部分回答两个问题：TrpB 到底是个什么酶，以及为什么它的构象变化值得用增强采样去研究。如果不先把催化化学和构象动力学连起来，后面的参数、脚本和 HPC 流程只会变成机械操作。

### 1.1 TrpB 是什么

本节回答两个问题：TrpB 在催化什么反应，`PLP` 为什么会成为整个体系的化学核心。理解这一点后，你才会知道为什么一个辅因子的电荷和质子化态足以卡住整个 pipeline。

`TrpB` 是 `tryptophan synthase beta subunit`，属于色氨酸合酶复合体的 `β` 亚基。它催化的最终化学事件是把 `indole` 与 `L-serine` 衍生的活化中间体偶联，生成 `L-tryptophan`。在天然体系中，`TrpA` 负责上游底物裂解并通过通道输送 `indole`，`TrpB` 负责完成 `PLP` 依赖的偶联与产物形成。

`PLP` 的角色不是“被动辅因子”，而是一个真正参与成键与断键的电子汇。它通过 `Schiff base chemistry` 与底物或赖氨酸形成亚胺键，在不同中间体之间切换电子结构，稳定高能中间态并重排反应坐标。

从教学角度，可以把 TrpB 催化循环粗略理解成下面这条主线：

| 中间体                   | 化学含义               | 关键化学事件                          | 本项目中的地位                   | 来源                                                             |
| ------------------------ | ---------------------- | ------------------------------------- | -------------------------------- | ---------------------------------------------------------------- |
| `Ain`                  | internal aldimine      | `PLP` 与 `Lys82` 形成 Schiff base | 当前参数化起点                   | `FULL_LOGIC_CHAIN.md`; JACS 2019, DOI `10.1021/jacs.9b03646` |
| `Aex1`                 | external aldimine      | 底物取代 `Lys82` 与 `PLP` 成键    | 论文复刻目标之一                 | 同上                                                             |
| `A-A`                  | aminoacrylate          | 脱水后形成活化中间体                  | 关闭态最关键预反应构型之一       | 同上                                                             |
| `Q1/Q2/Q3`             | quinonoid-like family  | 偶联后的高能电子重排区间              | `Q2` 是 JACS 2019 的重点分析态 | `FULL_LOGIC_CHAIN.md`; JACS 2019                               |
| `Aex2` / product state | 后期外醛亚胺与产物释放 | 走向 `L-Trp` 释放                   | 不在当前 benchmark 的首要范围内  | `FULL_LOGIC_CHAIN.md`                                          |

为什么研究它？因为 TrpB 是一个同时具有基础科学价值和工程价值的酶体系。

- 对基础科学，它是 `allostery`、`PLP chemistry` 与蛋白质构象门控耦合的经典模型体系。
- 对工业酶工程，它能参与非天然氨基酸与取代色氨酸衍生物的生物合成，是可编程生物催化的重要平台。
- 对本项目，它是把 `Generative AI` 提案落到“有物理可解释性 reward”上的理想测试床，见 Lambert et al. 2026, *Nature Communications*, DOI `10.1038/s41467-026-68384-6`。

### 1.2 COMM domain 与构象变化

本节回答的问题是：TrpB 的“开合”到底在说什么，为什么论文会把 `Closed` 态当成催化能力的代理指标。只有先理解这个结构问题，`Figure 2-3`、`Path CV` 和 `productive closure` 的定义才有意义。

TrpB 最重要的慢构象变化来自 `COMM domain`。在本项目中，沿用 JACS 2019 的定义，`Path CV` 使用的是 `Cα` 原子集合：残基 `97–184` 加上基底区域 `282–305`。这不是随便挑的一段结构，而是论文中用来表征 `Open -> Partially Closed -> Closed` 转换的实际工作坐标。

这三种状态可以这样理解：

| 构象状态             | 结构特征                                     | 功能含义                             | 来源                 |
| -------------------- | -------------------------------------------- | ------------------------------------ | -------------------- |
| `Open`             | active site 暴露，COMM domain 远离催化位点   | 更利于底物进入，但通常不利于高效催化 | JACS 2019 Figure 2   |
| `Partially Closed` | COMM domain 开始靠近，但尚未形成完整催化几何 | 过渡态附近的可采样 basin             | JACS 2019 Figure 2   |
| `Closed`           | active site 更封闭，关键催化原子间距离收紧   | 更接近 productive chemistry          | JACS 2019 Figure 2-3 |

为什么 `Closed` 态重要？因为在 TrpB 里，闭合不是“形状好看”，而是把催化所需的电荷环境、几何关系和底物定位同时推到正确区域。JACS 2019 用自由能景观和结构分析给出了一条可操作的经验判断：真正有催化意义的 `productive closure` 不只看一个 `RMSD`，还要看关键化学距离是否到位。

本项目沿用的 `productive` 定义是：

- `COMM-domain RMSD < 1.5 Å`，相对于 `Closed` 参考态。
- `K82-Q2 distance <= 3.6 Å`，表示赖氨酸/辅因子附近的催化几何进入 productive 区间。

这两个量的角色不同，不能混为一谈：

- `s(R)` 和 `z(R)` 是真正被加偏置的 `collective variables`。
- `COMM RMSD` 与 `K82-Q2 distance` 是后验分析指标，用来判断“这个 basin 像不像 productive closed state”。

这是仓库里 `FP-001` 明确要求避免的概念混淆。

从本地论文笔记提取的关键证据如下：

| 证据                    | 结论                                                                                               | 对本项目的意义                                  | 来源                                                     |
| ----------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------- |
| JACS 2019 Figure 2      | `PfTrpS(Q2)` 存在 `O/PC/C` 多 basin；孤立 `PfTrpB(Q2)` 的 `C-like` 区域高能且不 productive | 说明闭合自由能景观与活性相关                    | `JACS2019_SpeedBrief.md`; DOI `10.1021/jacs.9b03646` |
| JACS 2019 Figure 3      | `PfTrpS` 与 `PfTrpB0B2` 的 `K82-Q2` 距离更接近 `~3.6 Å`；孤立 `PfTrpB` 更偏离           | 说明不是任何 closed-looking 结构都 productive   | 同上                                                     |
| FULL_LOGIC_CHAIN 的总结 | 论文要解释的是构象 ensemble，而不是单一静态结构                                                    | 直接决定我们后面为什么不用普通结构比对做 reward | `FULL_LOGIC_CHAIN.md`                                  |

### 1.3 为什么需要计算模拟

本节回答的问题是：既然有很多晶体结构，为什么还要折腾 `MD` 和 `MetaDynamics`。短答案是，实验给的是静态快照，而我们真正关心的是慢时间尺度上的构象分布与转移概率。

`X-ray crystallography`、`NMR` 和 `cryo-EM` 都能告诉你“哪些状态存在”，但很难直接给出“这些状态之间怎样互相转换、哪个 basin 更稳、跨越势垒要付出多少自由能代价”。TrpB 的关键问题恰恰就是后者。

对于 TrpB 这种 `allosteric enzyme`，很多最重要的事件发生在 `μs-ms` 量级。常规 `MD` 能做的事情主要有两类：

- 在局部 basin 内放松结构、检查稳定性、生成初始 ensemble。
- 为后续增强采样提供合理起点、坐标、速度与溶剂环境。

但常规 `MD` 往往不足以在可承受时间内反复跨越 `Open/PC/Closed` 之间的自由能势垒。因此需要 `enhanced sampling`。JACS 2019 选择的是 `Well-Tempered MetaDynamics` 配合 `Path CV`，本项目严格复刻这条路线，而不是在方法学上另起炉灶。

### 读完检查

1. 为什么说 `Closed` 态在 TrpB 里不是单纯的几何描述，而是和 catalytic productivity 直接相关？
2. `COMM RMSD` 与 `K82-Q2 distance` 各自扮演什么角色，为什么它们不能替代 `s(R)` 与 `z(R)`？
3. 如果只有晶体结构而没有增强采样，你会错过哪些关于 TrpB 的关键信息？

---

## 第二部分：计算方法论

这一部分回答的方法学问题是：我们到底用什么数学模型描述体系，又为什么选这套模型而不是更“简单”的替代品。重点不是背参数，而是知道每一个参数在物理上买来了什么能力。

### 2.1 分子动力学基础

本节回答的问题是：`MD` 在本项目里究竟模拟了什么，以及 `force field`、水模型和时间步长这些设置分别控制什么误差。只有知道这些近似的边界，后面谈 MetaDynamics 才不会失真。

经典 `MD` 的核心思想，是用经验势能函数近似原子间相互作用，然后通过牛顿方程推进体系随时间演化。对 TrpB 这样的蛋白体系，势能通常拆成键长、键角、二面角、`van der Waals` 和静电项。

本项目严格复刻 JACS 2019 的参数框架：

| 模块           | 选择       | 为什么                                                             | 来源                                                |
| -------------- | ---------- | ------------------------------------------------------------------ | --------------------------------------------------- |
| 蛋白力场       | `ff14SB` | 为蛋白 backbone/side chain 提供经过校准的 bonded 与 nonbonded 参数 | JACS 2019 SI `p.S2`, DOI `10.1021/jacs.9b03646` |
| 非标准残基力场 | `GAFF`   | 给 `PLP`、底物和非标准中间体提供原子类型与 bonded 模板           | JACS 2019 SI `p.S2`                               |
| 电荷模型       | `RESP`   | 用量子化学 `ESP` 拟合部分电荷，比 `AM1-BCC` 更适合催化位点     | JACS 2019 SI `p.S2`; `FP-009`                   |
| 水模型         | `TIP3P`  | 与原论文一致，且和 AMBER 生态兼容性最好                            | JACS 2019 SI `p.S2`                               |
| 时间步长       | `2 fs`   | 在 `SHAKE` 约束下兼顾数值稳定与效率                              | JACS 2019 SI `p.S2`                               |
| 长程静电       | `PME`    | 避免截断库仑势带来的系统误差                                       | JACS 2019 SI `p.S2`                               |

`SHAKE` 在这里的作用也必须说清楚。它不是“固定氢键角度”，而是把高速振动的键长自由度约束掉，尤其是水分子的 `O-H` 键与 `H-O-H` 几何，从而允许把时间步长从 `1 fs` 扩到 `2 fs`。这正是 `FP-002` 强调的表述规范。

### 2.2 Well-Tempered MetaDynamics

本节回答的问题是：`MetaDynamics` 到底在做什么，`well-tempered` 又比原始版本多了什么稳定性。理解这一层后，你才会知道 `height`、`pace` 和 `bias factor` 这些数字为什么不是随手填的。

标准 `MetaDynamics` 的思路，是在选定的 `CV` 空间中定期沉积 Gaussian hills，把系统从已经访问过的 basin 里“推开”。这样做的结果是，体系会不断探索新的构象区域，最终让偏置势近似抵消真实自由能面。

`Well-Tempered MetaDynamics` 的关键改进来自 Barducci et al. 2008：随着采样进行，后续 hills 的有效高度会逐渐衰减，因此偏置不会无限制把自由能面填平，而是更平滑、更稳定地逼近自由能景观。对蛋白质大尺度构象变化来说，这比原始 `MetaDynamics` 更容易收敛，也更不容易过度填坑。

本项目沿用 JACS 2019 的关键参数：

| 参数               | 值                                   | 物理含义                                           | 来源                  |
| ------------------ | ------------------------------------ | -------------------------------------------------- | --------------------- |
| `height`         | `0.15 kcal/mol` (`0.628 kJ/mol`) | 单次沉积 hill 的初始强度                           | JACS 2019 SI `p.S3` |
| `pace`           | 每 `2 ps` 一次                     | 沉积频率，太快会过偏置，太慢会低效                 | 同上                  |
| `bias factor`    | `10`                               | 控制 bias tempering 强度，等效提高 CV 空间探索能力 | 同上                  |
| `temperature`    | `350 K`                            | 与生产模拟保持一致                                 | 同上                  |
| `Gaussian width` | `adaptive`                         | 根据局部地形自动调节 hill 宽度                     | 同上                  |

收敛不是“跑够时间就算收敛”。在本项目中，更合理的收敛判据包括：

- `O` 与 `C` basin 的相对自由能差随时间趋于平台。
- 不同 walkers 合并后的 `FES` 不再出现持续漂移的大 basin 重排。
- 后验指标如 `K82-Q2 distance`、`COMM RMSD` 的 basin 归属与 `FES` 解释保持一致。

### 2.3 Path Collective Variables

本节回答的问题是：为什么不直接用一个 `RMSD` 做偏置，而要用 `Path CV`。这是整个 MetaDynamics 设计里最容易“看起来复杂、其实必要”的一环。

简单 `RMSD` 的问题在于，它把两种本来应该分开的信息压成了一个标量：

- 体系在正确反应路径上走到了哪里。
- 体系有没有偏离这条路径，跑到奇怪但 `RMSD` 也不大的 off-path 结构。

`Path CV` 正好把这两件事分开：

| CV       | 数学/物理含义       | 直觉解释                                       | 来源         |
| -------- | ------------------- | ---------------------------------------------- | ------------ |
| `s(R)` | progress along path | 体系沿 `Open -> Closed` 参考路径走到了第几段 | JACS 2019 SI |
| `z(R)` | deviation from path | 体系离参考路径本身有多远                       | 同上         |

这就是为什么 `Path CV` 比单独一个 `RMSD` 更适合 TrpB：COMM domain 的闭合不是一维平移，而是一条带有方向性的集体运动。你需要同时知道“前进了多少”和“有没有跑偏”。

参考路径的构建也不是拍脑袋：

| 项目             | 选择                                    | 为什么                                                   | 来源                  |
| ---------------- | --------------------------------------- | -------------------------------------------------------- | --------------------- |
| Open reference   | `1WDW`                                | 论文使用的 open 参考结构                                 | JACS 2019 SI `p.S3` |
| Closed reference | `3CEP`                                | 论文使用的 closed 参考结构                               | 同上                  |
| 路径帧数         | `15`                                  | 在分辨率与数值稳定之间折中                               | 同上                  |
| 原子集合         | `Cα` of `97–184` and `282–305` | 聚焦 COMM domain 与基底区域的主构象变化                  | 同上                  |
| `lambda`       | `2.3 × (1/MSD) ≈ 0.029`             | 用相邻参考帧平均 `MSD ≈ 80 Å²` 归一化 path 距离尺度 | 同上                  |

这里特别值得强调：`lambda` 不是“可有可无的调参常数”，它决定了 `s,z` 对参考路径帧间距的敏感度。如果 `lambda` 太小，路径分辨率会塌；如果太大，局部噪声会被过分放大。

### 2.4 Multiple Walker 策略

本节回答的问题是：为什么论文不用一条超长轨迹，而要用 `10 walkers` 共享偏置。答案和并行效率、自由能收敛速度、以及初始构象多样性都有关。

`Multiple Walker MetaDynamics` 的核心思想是：让多个独立模拟并行探索同一个 `CV` 空间，并共享 `HILLS` 偏置历史。这样每个 walker 都能站在其他 walkers 已经“填过”的坑上继续探索，而不是各自从头爬山。

JACS 2019 的设置是：

| 参数           | 值                                       | 解释                                 | 来源         |
| -------------- | ---------------------------------------- | ------------------------------------ | ------------ |
| walkers 数     | `10`                                   | 10 条并行 replica                    | JACS 2019 SI |
| 单 walker 时长 | `50–100 ns`                           | 取决于体系与收敛情况                 | 同上         |
| 总采样         | `500–1000 ns`                         | 共享偏置后的总有效采样量             | 同上         |
| 初始构象来源   | 初步 MetaD 或常规 MD 提取的多样 snapshot | 保证 walkers 不全从同一个 basin 出发 | 同上         |

为什么这通常比一条单长轨迹高效？

- 并行 wall-clock 更友好，适合 HPC。
- 更容易跨越多个 basin，不会被某一个初始构象长期困住。
- 对慢变量体系，多个 walker 能更快把 bias 撒到整个重要区域。

### 读完检查

1. `RESP` 相比 `AM1-BCC` 为什么更适合 TrpB 里这种参与催化的 `PLP` 中间体？
2. 为什么 `Path CV` 的两个坐标 `s(R)` 和 `z(R)` 比一个 `RMSD` 更有解释力？
3. `bias factor = 10` 和 `multiple walker` 分别在收敛上解决了什么问题？

---

## 第三部分：复刻流程（Complete Workflow）

这一部分回答实践问题：如果你现在从零开始复刻 Osuna 2019 的 TrpB MetaDynamics，需要按什么顺序把结构、参数、体系、轨迹和增强采样串起来。重点不是“把命令跑通”，而是知道每一步为什么放在这里，以及哪里最容易出科学错误。

### 3.1 起始结构准备

本节回答的问题是：复刻的起点结构从哪里来，残基名称为什么不能靠记忆写。这里一旦搞错，后面所有参数文件都会在错误的化学对象上工作。

当前项目使用的关键 `PDB` 起始结构是：

| 结构     | 中间体/用途              | 备注                                                            | 来源                                  |
| -------- | ------------------------ | --------------------------------------------------------------- | ------------------------------------- |
| `5DVZ` | `Ain`                  | `chain A`, residue `82 = LLP`，对应 `PLP-K82 Schiff base` | `PROJECT_OVERVIEW.md`; `5DVZ.pdb` |
| `5DW0` | `Aex1`                 | 外醛亚胺前期结构来源                                            | `PLP_SYSTEM_SETUP_LOGIC_CHAIN.md`   |
| `4HPX` | `A-A`                  | `aminoacrylate` 相关结构来源                                  | 同上                                  |
| `1WDW` | Path CV open reference   | JACS 2019 使用的 open 参考                                      | JACS 2019 SI                          |
| `3CEP` | Path CV closed reference | JACS 2019 使用的 closed 参考                                    | 同上                                  |

对 Ain，最重要的一个命名事实是：

- `LLP` 不是“随便起的 ligand name”，而是 `5DVZ` 里已经存在的聚合物连接残基名。
- 它表示的是与 `Lys82` 成 `Schiff base` 的 `PLP` 派生态。
- 因为它是 `polymer-linked residue`，所以你不能把它当作脱离蛋白骨架的普通小分子直接去 `RESP`。

如果要构建突变体，原则上应在经过验证的实验 scaffold 上引入点突变，并在参数化前保持辅因子与 active-site 化学对象不变。JACS 2019 中 `PfTrpB0B2` 的突变是用 `RosettaDesign` 引入；本项目当前 `Runner` 阶段的首要目标不是设计新突变，而是先把野生型 benchmark 跑对。

### 3.2 PLP 参数化（当前 blocker，重点展开）

本节回答的问题是：为什么 `LLP` 会成为整个复刻流程的瓶颈，以及怎样把一个蛋白链内共价连接的辅因子中间体，转成可用于 `ff14SB + GAFF` 的参数文件。这里也是当前 pipeline 最不能偷懒的一段。

#### 3.2.1 为什么需要参数化

这一小节回答一个最基础的问题：为什么 `PLP` 不能直接靠标准蛋白力场“自动识别”。答案是，标准力场只认识标准氨基酸，而不认识处在特定反应中间体状态、还和蛋白共价相连的 `LLP`。

对 Ain/LLP，至少有三类信息需要补齐：

| 需要补齐的内容                      | 工具/来源                   | 作用                                                               |
| ----------------------------------- | --------------------------- | ------------------------------------------------------------------ |
| 原子类型 (`atom types`)           | `antechamber -at gaff`    | 决定 bonded / nonbonded 参数模板                                   |
| 部分电荷 (`partial charges`)      | `RESP` on Gaussian output | 决定静电相互作用，尤其是 active site 里的 H-bond 与 electrostatics |
| 缺失参数 (`missing bonded terms`) | `parmchk2`                | 补齐 GAFF 库中未覆盖的键角/二面角                                  |

为什么当前项目明确禁止直接用 `BCC`？

- `FP-009` 已经把结论写死：Osuna 2019 用的是 `RESP`，不是 `AM1-BCC`。
- `FP-010` 进一步说明，对无氢的 `PDB` 直接跑 `antechamber` 会把芳香体系类型分错，尤其会把吡啶环与共轭体系错误分类。
- TrpB 的 `PLP` 中间体正好是最不该用粗略电荷近似的对象，因为它既承载离域电子结构，又直接处在催化核心。

#### 3.2.2 质子化态确定

这一小节回答的问题是：Ain 里的 `LLP` 到底该带什么电荷，为什么最后是 `-2` 而不是很多人直觉会写的 `-1`。这是整个参数化中最关键的化学判断。

当前仓库已经把 Ain 的四个 `pH-sensitive` 位点通过文献和项目验证统一起来：

| 位点               | 结论                                | 电荷贡献 | 证据                           | 来源                                                     |
| ------------------ | ----------------------------------- | -------- | ------------------------------ | -------------------------------------------------------- |
| phosphate          | `dianionic`                       | `-2`   | `31P NMR` 指向二阴离子磷酸   | Caulkins et al. 2014,*JACS*, DOI `10.1021/ja506267d` |
| phenolic `O3`    | `deprotonated`                    | `-1`   | `13C` 化学位移支持 phenolate | 同上                                                     |
| pyridine `N1`    | `deprotonated` / neutral acceptor | `0`    | `15N δ = 294.7 ppm`         | 同上                                                     |
| Schiff base `NZ` | `protonated`                      | `+1`   | `15N δ = 202.3 ppm`         | 同上                                                     |

总电荷因此是：

```text
phosphate (-2) + O3 (-1) + N1 (0) + NZ (+1) = -2
```

为什么不是 `-1`？因为要得到 `-1`，你通常得额外给 phosphate 加一个质子，或者把 `O3` 变回中性酚。前者会直接破坏 `Caulkins 2014` 的 `31P NMR` 证据，后者又和 `13C` 及后续 `MD` 验证不一致。换句话说，`-1` 不是“另一个也说得通的选择”，而是与当前最佳证据链冲突。

四来源交叉验证可以总结如下：

| 来源                                                                 | 类型               | 提供了什么信息                                      | 对最终结论的权重 |
| -------------------------------------------------------------------- | ------------------ | --------------------------------------------------- | ---------------- |
| Caulkins et al. 2014,*JACS*, DOI `10.1021/ja506267d`             | 直接实验 `ssNMR` | 给出 Ain 中 `PLP` 位点级质子化证据                | 最高，决定性     |
| Huang et al. 2016,*Protein Science*, DOI `10.1002/pro.2709`      | `MD` 方案比较    | 比较 17 套质子化方案，NMR-consistent 模型表现最好   | 高，交叉验证     |
| Maria-Solano et al. 2019,*JACS*, DOI `10.1021/jacs.9b03646`      | 原 benchmark 方法  | 明确对 Ain 等中间体做 `RESP @ HF/6-31G(d)`        | 中，提供方法框架 |
| Kinateder et al. 2025,*Protein Science*, DOI `10.1002/pro.70103` | Osuna 组后续工作   | 继续沿用基于文献约束的 `PLP` 化学与 `RESP` 思路 | 中，现代交叉验证 |

#### 3.2.3 ACE/NME Capping

这一小节回答的问题是：为什么不能把 `LLP` 从 `PDB` 里硬截出来就拿去做 `Gaussian`。因为 Ain 里的 `LLP` 不是自由小分子，而是嵌在蛋白主链里的共价连接残基。

仓库里的 `5DVZ.pdb` 明确存在两条聚合物连接：

- `HIS81 C -> LLP82 N`
- `LLP82 C -> THR83 N`

这意味着如果你直接截取 residue `82`，就会在两端留下不物理的“裸露肽键边界”。这种边界会污染 `ESP` 分布，使 RESP 电荷在残基首尾处出现不应有的极化。

因此，本项目当前确认的做法是把 Ain 作为 `ACE-LLP-NME` capped fragment 做 `RESP`：

| cap     | 锚点原子         | 作用                        | 电荷  |
| ------- | ---------------- | --------------------------- | ----- |
| `ACE` | `HIS81 CA/C/O` | 模拟 LLP N 端前一个肽键环境 | `0` |
| `NME` | `THR83 N/CA`   | 模拟 LLP C 端后一个肽键环境 | `0` |

当前已验证的 capped fragment 统计为：

| 项目             | 数值                         | 来源                                            |
| ---------------- | ---------------------------- | ----------------------------------------------- |
| LLP heavy atoms  | `24`                       | `5DVZ.pdb` + `build_llp_ain_capped_resp.py` |
| caps heavy atoms | `5` (`ACE=3`, `NME=2`) | `2026-03-30_capping_analysis.md`              |
| 总 heavy atoms   | `29`                       | 同上                                            |
| 总 H             | `25`                       | 同上                                            |
| 总原子数         | `54`                       | `FP-012` 修复后结论                           |
| 总电荷           | `-2`                       | protonation review + capping analysis           |
| multiplicity     | `1`                        | electron parity check                           |

电子数检查也必须显式做：

```text
Z_total = 226
electrons = 226 - (-2) = 228
228 为偶数，因此 singlet (multiplicity = 1) 合法
```

这正是 `FP-012` 所修复的问题：旧版本误生成 `55` 原子，导致奇电子 singlet，Gaussian 直接报错。

#### 3.2.4 Gaussian RESP 计算

这一小节回答的问题是：在当前项目中，什么样的 `Gaussian` 输入才算既符合 RESP 目的、又能在 `Gaussian16` 上稳定运行。这里要同时满足化学正确、软件兼容和后续 `antechamber` 可读性。

首先要澄清一个术语：`HF/6-31G(d)` 与 `HF/6-31G*` 在这个语境下是同一个标准 `RESP` 层级，只是写法不同。JACS 2019 说的是 `HF/6-31G(d)`；当前 Longleaf validated run file 写成 `6-31G*`，两者等价。

当前项目验证通过、且已经用于 Job `40533504` 的 route 是：

```gaussian
%chk=LLP_ain_resp_capped.chk
%nprocshared=8
%mem=8GB
#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt

LLP Ain RESP fitting with ACE/NME caps

-2 1
```

为什么是这条 route，而不是旧版脚本里的那条？

- `Pop=MK`：要求 Gaussian 生成 `Merz-Kollman` 型 `ESP` 采样，供 RESP 拟合。
- `SCF=tight`：让自洽场收敛更严格，减少电荷拟合中的数值噪声。
- `opt`：先把 capped fragment 放松到量化学层级的局部稳定构型，再在优化后的几何上输出 `ESP`。
- `iop(6/33=2)` 与 `iop(6/42=6)`：采用当前仓库已经在 `Gaussian16 + antechamber` 工作流中验证可读取的 `MK ESP` 采样设置。

与旧历史相比，最重要的兼容性结论是：

- 不要使用 `iop(6/50=1)`。
- `FP-013` 已确认这是 `Gaussian16` 上的失败点，而 `antechamber -fi gout` 也不需要额外的 `.gesp` 文件。

当前项目对这两个 `iop` 的实践性理解如下：

| 关键词          | 当前项目中的作用                                                 | 说明                                                   |
| --------------- | ---------------------------------------------------------------- | ------------------------------------------------------ |
| `iop(6/33=2)` | 让 `Gaussian` 以 AmberTools 兼容的方式输出 `MK ESP` 相关信息 | 目的是保证 `.log` 能被 `antechamber -fi gout` 读取 |
| `iop(6/42=6)` | 提高 `ESP` 采样密度                                            | 在仓库文档中按 `6 points/A^2` 使用                   |

这里故意不再引入额外未出现在 run file 里的 `IOP` 变体。原因很简单：JACS 2019 只给了 `RESP @ HF/6-31G(d)` 的方法框架，当前项目真正要执行的是“已在本地验证可运行”的 Gaussian16 输入，而不是再拼装一套未经测试的教程配方。

可复制的生成命令如下：

```bash
python3 scripts/build_llp_ain_capped_resp.py \
  --output replication/parameters/resp_charges/ain/LLP_ain_resp_capped.gcrt
```

#### 3.2.5 antechamber 提取电荷

这一小节回答的问题是：`Gaussian` 跑完之后，如何把 `ESP` 拟合结果转成 AMBER 能读的 `mol2`，以及为什么 capped fragment 不能直接原封不动塞回蛋白系统里。

标准提取命令是：

```bash
antechamber \
  -i LLP_ain_resp_capped.log -fi gout \
  -o Ain_capped_resp.mol2 -fo mol2 \
  -c resp -at gaff
```

这一步会得到一个带 `GAFF atom types` 和 `RESP charges` 的 `mol2`。但要注意，最终要装回蛋白里的不是 `ACE-LLP-NME` 三残基复合物，而是 `LLP` 这个非标准残基本体。因此后处理必须做一轮人工审计：

| 审计点                  | 为什么要查                                              | 实务建议                                   |
| ----------------------- | ------------------------------------------------------- | ------------------------------------------ |
| atom order / atom names | 后续 `prep/mol2/lib` 对名称敏感                       | 保持与 `5DVZ` 的 `LLP` 原子名一致      |
| LLP-only charge sum     | 删掉 caps 后总电荷不能漂移                              | 目标仍应回到 `-2`                        |
| boundary atoms          | 首尾原子要与蛋白主链拼接兼容                            | 不要把 cap 人为极化带入主链边界            |
| cap removal strategy    | capped fragment 只是 QM 边界近似，不是最终 residue 定义 | 删除 `ACE/NME` 原子，再检查/重整边界电荷 |

这里要诚实说明一个工程事实：`cap` 原子删掉之后，边界电荷如何重新分配，不是一个可以盲目自动化的“机械删除”步骤。最稳妥的做法是：

1. 先从 capped `mol2` 读取全体 RESP 电荷。
2. 提取 `LLP` 本体原子并检查剩余电荷和是否接近 `-2`。
3. 对首尾边界原子做人工审计，确保其电荷与 `ff14SB` 主链拼接不出现明显不连续。

如果这一步不做检查，你得到的不是“严格参数化”，而只是“把 Gaussian 跑过了”。

#### 3.2.6 parmchk2 补缺参数

这一小节回答的问题是：为什么有了 `GAFF atom types + RESP charges` 还不够。原因是 `GAFF` 是通用力场，遇到罕见连接模式时仍可能缺少显式参数，需要 `parmchk2` 给出补丁。

标准命令：

```bash
parmchk2 -i Ain_resp.mol2 -f mol2 -o Ain.frcmod
```

输出文件 `Ain.frcmod` 会列出缺失的 bond/angle/dihedral/nonbond 参数。这里最重要的人工检查点不是“文件有没有生成”，而是：

- 有没有 `ATTN` 或类似提示，表示参数来自经验估算而不是直接命中库。
- 缺失项是否集中出现在 `PLP` 共轭体系、phosphate 或 Schiff base 周围。
- 参数量级是否物理合理，没有明显离谱的 force constant 或平衡键长。

### 3.3 体系搭建（tleap）

本节回答的问题是：参数文件拿到以后，如何把蛋白、辅因子、水和离子真正组装成可模拟体系。这里的关键是“让不同来源的参数在同一个 topology 里和平共处”。

最小可工作的 `tleap` 模板如下：

```tcl
source leaprc.protein.ff14SB
source leaprc.gaff
source leaprc.water.tip3p

AIN = loadmol2 Ain_resp.mol2
loadamberparams Ain.frcmod

prot = loadpdb 5DVZ_prepared_with_LLP.pdb
check prot

solvatebox prot TIP3PBOX 10.0
addions prot Na+ 0

saveamberparm prot pftrps_ain.parm7 pftrps_ain.inpcrd
savepdb prot pftrps_ain_leap.pdb
quit
```

这里每一行都对应一个明确目标：

- `ff14SB` 负责标准蛋白部分。
- `GAFF` 与 `Ain.frcmod` 负责 `LLP`。
- `TIP3PBOX 10.0` 复刻论文的 `10 Å` 溶剂缓冲。
- `addions ... 0` 保证体系整体中和。

最终输出的关键文件是：

| 文件                    | 作用                     |
| ----------------------- | ------------------------ |
| `pftrps_ain.parm7`    | AMBER topology           |
| `pftrps_ain.inpcrd`   | 初始坐标与 box           |
| `pftrps_ain_leap.pdb` | 便于人工检查的组装后结构 |

### 3.4 最小化 → 加热 → 平衡

本节回答的问题是：一个新组装好的蛋白体系为什么不能直接开跑生产 `MD`。原因是初始结构里一定存在局部坏接触、溶剂未放松和温度/压力未达稳态的问题。

这里以仓库中的 `JACS2019_MetaDynamics_Parameters.md` 为准，而不是引用二手摘要。关键阶段如下：

| 阶段                 | 论文/项目采用值                                                    | 目的                             | 来源         |
| -------------------- | ------------------------------------------------------------------ | -------------------------------- | ------------ |
| minimization stage 1 | 仅最小化 solvent + ions；solute restraints `500 kcal/mol·Å^-2` | 先消除溶剂坏接触，不扭曲蛋白主体 | JACS 2019 SI |
| minimization stage 2 | 全体系无约束最小化                                                 | 释放整体局部应力                 | 同上         |
| heating              | `7 × 50 ps`, `NVT`, `0 -> 350 K`, `1 fs`                  | 平稳升温，避免一次性热冲击       | 同上         |
| heating restraints   | 从 `210` 递减到 `10 kcal/mol·Å^-2`                           | 逐步放开结构自由度               | 同上         |
| bond constraints     | `SHAKE` on water geometry                                        | 支持后续 `2 fs`                | 同上         |
| equilibration        | `2 ns`, `NPT`, `350 K`, `1 atm`, `2 fs`                  | 稳定密度、体积与溶剂分布         | 同上         |

为什么这里的 `equilibration` 是 `2 ns`，而不是很多口头流程里常见的“几百 ps 就够”？因为本文明确以 JACS 2019 SI 提取值为准。复刻 benchmark 的第一原则不是自作聪明地缩短流程，而是先把原始 protocol 做对。

一个典型的 `heating` 输入会包含：

- `Langevin thermostat`
- 周期性边界条件
- 渐进释放 restraints
- `1 fs` 时间步长

而到了平衡与生产阶段，再切到 `2 fs`。

### 3.5 常规 MD（500 ns, AMBER）

本节回答的问题是：为什么 MetaDynamics 之前还要先跑一段长常规 `MD`，以及为什么这一段用 `AMBER pmemd.cuda` 而不是直接切到 `GROMACS`。答案是，JACS 2019 本来就是这么做的，而且这一步的目标是获得稳定、可转换、可抽样的平衡 ensemble。

JACS 2019 的生产 `MD` 设定是：

| 参数           | 值                    | 来源         |
| -------------- | --------------------- | ------------ |
| 软件           | `AMBER16`           | JACS 2019 SI |
| 时长           | `500 ns` per system | 同上         |
| ensemble       | `NVT`               | 同上         |
| 温度           | `350 K`             | 同上         |
| 时间步长       | `2 fs`              | 同上         |
| electrostatics | `PME`               | 同上         |
| cutoff         | `8 Å`              | 同上         |

推荐的运行方式是分段续跑，而不是一次性提交一个超长单任务。核心命令形式如下：

```bash
pmemd.cuda -O \
  -i prod_nvt.in \
  -o prod_nvt.out \
  -p pftrps_ain.parm7 \
  -c equil_final.rst7 \
  -r prod_nvt.rst7 \
  -x prod_nvt.nc \
  -inf prod_nvt.info
```

为什么这里坚持 `AMBER`？

- 严格复刻层面：原论文的 conventional `MD` 用的是 `AMBER16`。
- 工程层面：`pmemd.cuda` 在这类蛋白体系上通常非常高效。
- 数据流层面：我们的 `ff14SB + GAFF + RESP` 参数首先在 AMBER 生态里最自然。

常规 `MD` 的主要验收指标包括：

- 蛋白整体 `RMSD` 没有持续发散。
- active site 关键 H-bond 网络不出现明显崩坏。
- 溶剂盒尺寸、温度、势能进入稳定平台。

### 3.6 格式转换（AMBER → GROMACS）

本节回答的问题是：既然前面用的是 `AMBER`，为什么后面还要转成 `GROMACS`。短答案是：因为本项目追求的是对 Osuna 2019 `MetaDynamics` 实现的严格复刻，而原文的 MetaD 引擎就是 `GROMACS 5.1.2 + PLUMED2`。

推荐的转换工具是 `ParmEd`：

```bash
python -c "
import parmed as pmd
a = pmd.load_file('pftrps_ain.parm7', 'pftrps_ain_equil_last.rst7')
a.save('pftrps_ain.top')
a.save('pftrps_ain.gro')
"
```

为什么不直接全程用 `AMBER + PLUMED`？

- 技术上可以，但那已经不是“严格复刻 JACS 2019”。
- 仓库当前 benchmark 目标是先复现论文的 `FES`，不是先做方法学变体比较。

转换后必须做 `energy consistency check`：

```bash
gmx grompp -f energy_check.mdp \
  -c pftrps_ain.gro \
  -p pftrps_ain.top \
  -o energy_check.tpr

gmx mdrun -s energy_check.tpr -nsteps 0 -rerun pftrps_ain.gro
```

要比较的不是总能量一个数字，而是分项能量是否同量级一致：

- bond
- angle
- dihedral
- `van der Waals`
- electrostatics

小差异是允许的；如果差异大到 `> 10 kcal/mol` 量级，优先怀疑转换或非标准残基处理出了问题。

### 3.7 Well-Tempered MetaDynamics（GROMACS + PLUMED2）

本节回答的问题是：前面准备好的平衡体系，如何真正进入论文里的 `WT-MetaD` 生产阶段。这里的重点是把 `Path CV`、`METAD` 参数和 `multiple walkers` 组合到一个可以在 HPC 上执行的输入体系里。

当前仓库 `plumed_trpb_metad.dat` 的逻辑可简化为三部分：

1. 定义 `s`、`z` 两个 `Path CV`。
2. 定义只用于监测、不用于 bias 的辅助指标，如 `K82_Q2_DIST`、`E104_Q2_DIST`、`COMM_RMSD`。
3. 用 `METAD` 对 `s,z` 施加 `well-tempered bias`。

一个精简后的 `PLUMED` 片段如下：

```plumed
PATHMSD ...
  LAMBDA=0.029
  REFERENCE=path_reference.pdb
  LABEL=path
... PATHMSD

METAD ...
  ARG=path.s,path.z
  PACE=1000
  HEIGHT=0.628
  BIASFACTOR=10
  TEMP=350
  ADAPTIVE=GEOM
  SIGMA=0.1
  SIGMA_MIN=0.3,0.005   # per-CV (s, z) in CV units; FP-024
  SIGMA_MAX=1.0,0.05    # per-CV (s, z) in CV units; FP-024
  FILE=HILLS
  STRIDE=500
... METAD

PRINT ARG=path.s,path.z,K82_Q2_DIST,E104_Q2_DIST,COMM_RMSD FILE=COLVAR STRIDE=500
```

关键参数表如下：

| 参数           | 值        | 单位/解释                                    | 来源                                     |
| -------------- | --------- | -------------------------------------------- | ---------------------------------------- |
| `LAMBDA`     | `0.029` | path 缩放参数                                | JACS 2019 SI                             |
| `HEIGHT`     | `0.628` | `kJ/mol`, 即 `0.15 kcal/mol`             | 仓库 `plumed_trpb_metad.dat` + JACS SI |
| `PACE`       | `1000`  | `dt = 0.002 ps` 时等于每 `2 ps` 沉积一次 | 同上                                     |
| `BIASFACTOR` | `10`    | well-tempered factor                         | JACS 2019 SI                             |
| `TEMP`       | `350`   | K                                            | 同上                                     |
| `ADAPTIVE`   | `GEOM`  | 自适应 Gaussian 宽度                         | 同上                                     |
| walkers        | `10`    | shared bias                                  | 同上                                     |

当前项目特别强调一点：`K82_Q2_DIST` 和 `COMM_RMSD` 是分析变量，不是偏置变量。这一点必须始终和 `FP-001` 保持一致。

一个最小可复制的 `GROMACS` 运行命令是：

```bash
gmx mdrun \
  -deffnm metad \
  -plumed plumed_trpb_metad.dat \
  -ntmpi 1 \
  -ntomp ${SLURM_CPUS_PER_TASK}
```

对于 `multiple walkers`，当前 Longleaf 更实用的方案是用 `job array` 或 `-multidir` 组织多个 walker 目录，并让它们共享 `HILLS` 信息。关键不在于哪一种 shell 技巧，而在于：

- 10 个 walkers 使用不同初始 snapshot。
- 每个 walker 的 `PLUMED` 都指向同一 walker 协议。
- 输出目录与重启文件命名要一致，否则很容易在恢复运行时混乱。

### 3.8 分析

本节回答的问题是：MetaDynamics 跑完以后，什么样的分析才算真正回答了科学问题。仅仅画一张彩色热图不够，你需要把 `FES`、构象 basin 和化学可解释指标连起来。

最基础的后处理是重建 `free energy surface`：

```bash
plumed sum_hills --hills HILLS --outfile fes.dat
```

之后至少要做三类分析：

| 分析任务                | 要回答的问题                                | 工具/指标                          |
| ----------------------- | ------------------------------------------- | ---------------------------------- |
| `FES` 重建            | `O/PC/C` basin 是否出现，势垒位置是否合理 | `sum_hills`, `s-z` contour     |
| 收敛检查                | basin 相对自由能是否趋于稳定                | 分时间窗重建 `FES`               |
| productive closure 判定 | `Closed` basin 是否真 productive          | `COMM RMSD`, `K82-Q2 distance` |

与 JACS 2019 Figure 2 对比时，不要只看“有没有三个颜色块”，而要看：

- basin 的相对位置是否与 `Open/PC/Closed` 解释一致。
- `Closed-like` 区域的 `z` 是否较低，说明不是偏离路径的假闭合。
- 后验距离指标是否支持 productive chemistry，而不是只有几何上“看起来关了”。

### 读完检查

1. 为什么 Ain/LLP 的参数化必须从 `ACE-LLP-NME` capped fragment 开始，而不是直接把 `LLP` 当自由小分子？
2. 为什么常规 `MD` 用 `AMBER`，而 `MetaDynamics` 又要切到 `GROMACS + PLUMED2`？
3. 如果你最终看到一个 `Closed-like` basin，为什么还必须再去检查 `K82-Q2 distance`？

---

## 第四部分：HPC 实操

这一部分回答的问题是：上面的科学流程怎样在 Longleaf 上变成稳定、可恢复、可审计的实际作业。这里重点不是“会写 Slurm”，而是知道哪些小错误会在共享 HPC 上迅速放大成浪费计算资源的大故障。

### 4.1 Longleaf 环境

本节回答的问题是：在 Longleaf 上跑这个项目，到底需要哪些模块、环境和目录约定。环境不统一，后面的脚本模板再漂亮也没意义。

当前仓库记录的核心环境如下：

| 模块/环境                          | 用途                                                  | 当前建议                                                   | 来源                                      |
| ---------------------------------- | ----------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------- |
| `amber/24p3`                     | 常规 `MD`、`antechamber`、`parmchk2`、`tleap` | `module load amber/24p3`                                 | `resource_inventory.md`                 |
| `gaussian/16c02`                 | RESP 的 `Gaussian16` 任务                           | `module load gaussian/16c02`                             | 同上                                      |
| `anaconda/2024.02` + `trpb-md` | `GROMACS + PLUMED`                                  | `module load anaconda/2024.02 && conda activate trpb-md` | `FP-007`                                |
| 工作目录                           | Longleaf project root                                 | `/work/users/l/i/liualex/AnimaLab/`                      | `PROJECT_OVERVIEW.md`; scripts comments |

建议进入节点后的检查命令：

```bash
module load amber/24p3
module load anaconda/2024.02
conda activate trpb-md

which antechamber
which parmchk2
which tleap
gmx --version
plumed --version
```

### 4.2 Slurm 脚本模板

本节回答的问题是：Gaussian、AMBER 和 GROMACS 任务分别应该怎样写 `Slurm`，才能尽量避免仓库已经踩过的坑。下面的模板都偏保守，但保守在共享 HPC 上通常是优点。

#### Gaussian RESP job 模板

```bash
#!/bin/bash
#SBATCH --job-name=llp_ain_resp
#SBATCH --partition=general
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=24:00:00
#SBATCH --output=llp_ain_resp_%j.out

set -euo pipefail

module purge
module load gaussian/16c02
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

INPUT_GCRT="${1:-LLP_ain_resp_capped.gcrt}"
SCRATCH_DIR="${TMPDIR:-/tmp}/${USER}/gaussian/${SLURM_JOB_ID}"
mkdir -p "${SCRATCH_DIR}"
trap 'rm -rf ${SCRATCH_DIR}' EXIT
export GAUSS_SCRDIR="${SCRATCH_DIR}"

cd "${SLURM_SUBMIT_DIR}"
g16 "${INPUT_GCRT}"
```

这个模板里最关键的不是 `SBATCH` 数字，而是两件小事：

- 显式设置 `OMP_NUM_THREADS`。
- 给 scratch 目录加 `cleanup trap`。

#### AMBER production job 模板

```bash
#!/bin/bash
#SBATCH --job-name=trpb_md
#SBATCH --partition=<gpu-partition>
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=48:00:00
#SBATCH --output=trpb_md_%j.out

set -euo pipefail

module purge
module load amber/24p3

cd "${SLURM_SUBMIT_DIR}"

pmemd.cuda -O \
  -i prod_nvt.in \
  -o prod_nvt.out \
  -p pftrps_ain.parm7 \
  -c prod_prev.rst7 \
  -r prod_next.rst7 \
  -x prod_next.nc \
  -inf prod_next.info
```

这里把 GPU 分区写成占位符，是因为仓库当前验证的是软件环境与 protocol，而不是某一个固定的 Longleaf GPU queue 名。真正提交前应替换成实验室当前可用的 GPU partition。

#### GROMACS + PLUMED MetaD job 模板

```bash
#!/bin/bash
#SBATCH --job-name=trpb_metad
#SBATCH --partition=general
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=48:00:00
#SBATCH --output=trpb_metad_%A_%a.out
#SBATCH --array=0-9

set -euo pipefail

module purge
module load anaconda/2024.02
conda activate trpb-md
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK

WALKER_ID=${SLURM_ARRAY_TASK_ID}
cd "${SLURM_SUBMIT_DIR}/walker_${WALKER_ID}"

gmx grompp -f run_metad.mdp -c start.gro -p topol.top -o metad.tpr

gmx mdrun \
  -deffnm metad \
  -plumed ../plumed_trpb_metad.dat \
  -ntmpi 1 \
  -ntomp ${SLURM_CPUS_PER_TASK}
```

这个模板直接吸收了 `FP-006` 和 `FP-007` 的教训：`OMP_NUM_THREADS` 要和 `-ntomp` 一致，`conda` 要按 Longleaf 的模块方式加载，不要硬编码本地路径。

### 4.3 常见问题与解决

本节回答的问题是：这个项目最常见的失败模式是什么，以及看到某种错误时你应该先怀疑哪里。这里直接基于 `failure-patterns.md`，按“症状 -> 原因 -> 修复”组织，而不是写成事后复盘散文。

| 分类              | FP         | 症状                                            | 原因                                     | 一句话修复                                                                                   |
| ----------------- | ---------- | ----------------------------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------- |
| 概念混淆          | `FP-001` | 把 `K82-Q2` 当成被加偏置的 CV                 | 混淆 analysis metric 与 bias CV          | 只对 `s,z` 加 bias，`K82-Q2` 与 `COMM RMSD` 只做分析                                   |
| 概念混淆          | `FP-002` | 把 `SHAKE` 写成“约束氢键角”                 | 误解约束对象                             | 写成“约束水分子几何或高频键振动”                                                           |
| 力场/参数错误     | `FP-003` | cap 原子名、残基连接写错，`pdb2gmx`/拓扑报错  | 凭记忆发明原子名                         | 所有 atom names 只从 `PDB` 与 force-field template 读出                                    |
| Pipeline 操作错误 | `FP-004` | PLUMED 索引对不上真实拓扑                       | 直接拿输入 `PDB` 编号当 GROMACS 原子号 | 只从最终 `.gro/.tpr` 提取 index                                                            |
| 力场/参数错误     | `FP-005` | 参数表把不同体系/中间体混在一行                 | `(system, intermediate)` 配对混乱      | 每行只描述唯一体系与唯一中间体                                                               |
| Slurm/HPC 错误    | `FP-006` | `gmx mdrun` 报 OMP 与 `-ntomp` 冲突         | 没显式导出 `OMP_NUM_THREADS`           | 在 `conda activate` 之后、`mdrun` 之前设 `export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK` |
| Slurm/HPC 错误    | `FP-007` | `conda activate` 失败或找不到环境             | Longleaf conda 路径被硬编码错            | 用 `module load anaconda/2024.02 && conda activate trpb-md`                                |
| 概念混淆          | `FP-008` | 报告里写的参数和真实运行文件不一致              | 用记忆或摘要替代 run file                | 只从当前 `.mdp/.slurm/.dat/.gcrt` 提取报告参数                                             |
| 力场/参数错误     | `FP-009` | PLP 电荷模型偏粗糙，复刻偏离论文                | 偷懒用了 `BCC`                         | `PLP` 一律走 `RESP`                                                                      |
| 力场/参数错误     | `FP-010` | `antechamber` 把芳香体系类型分错              | 对无氢 `PDB` 直接 typing               | 先补氢，再做 `GAFF` typing                                                                 |
| Pipeline 操作错误 | `FP-011` | 前后步骤打乱，产物不可追溯                      | 不遵守 6-stage pipeline                  | 按 `Profiler -> Librarian -> Janitor -> Runner -> Skeptic -> Journalist` 顺序推进          |
| Gaussian 输入错误 | `FP-012` | Gaussian 报 electron parity / multiplicity 错误 | capped fragment 原子数与电荷不一致       | Ain capped fragment 固定为 `54 atoms`, `charge=-2`, `mult=1`                           |
| Gaussian 输入错误 | `FP-013` | Gaussian16 route 失败或 `.gesp` 方案多余      | 使用 `iop(6/50=1)` 老配方              | route 改为 `#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt`                       |

### 读完检查

1. 在 Longleaf 上跑 `GROMACS + PLUMED` 时，为什么 `OMP_NUM_THREADS` 不是“可设可不设”的小细节？
2. 如果 `Gaussian` 报 multiplicity 和 electron count 不可能，你第一反应应该去检查哪三件事？
3. 为什么说 `FP-008` 其实是科研可追溯性问题，而不只是“文档写错了”？

---

## 第五部分：关键决策汇总表

这一部分回答的问题是：到目前为止，这个项目到底有哪些关键技术决策已经定了，分别依据什么定。它的用途不是教学，而是给后续执行者和审稿者一个可以快速核对的 decision ledger。

| 决策                        | 选择                                                        | 来源                                    | DOI                                          | 为什么                                             |
| --------------------------- | ----------------------------------------------------------- | --------------------------------------- | -------------------------------------------- | -------------------------------------------------- |
| 蛋白力场                    | `ff14SB`                                                  | JACS 2019 SI; manifest                  | `10.1021/jacs.9b03646`                     | 严格复刻原 benchmark                               |
| 非标准残基力场              | `GAFF`                                                    | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 原论文对 cofactors/ligands 的选择                  |
| 水模型                      | `TIP3P`                                                   | JACS 2019 SI; manifest                  | `10.1021/jacs.9b03646`                     | 与原文和 AMBER 生态保持一致                        |
| 溶剂盒                      | cubic box,`10 Å` buffer                                  | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 直接复刻体系尺寸设置                               |
| PLP 电荷模型                | `RESP`                                                    | JACS 2019 SI;`FP-009`                 | `10.1021/jacs.9b03646`                     | active-site electrostatics 不能用粗略 `BCC` 替代 |
| RESP QM 层级                | `HF/6-31G(d)` = `6-31G*`                                | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 标准 AMBER/RESP 层级                               |
| Ain 总电荷                  | `-2`                                                      | protonation literature review           | `10.1021/ja506267d`; `10.1002/pro.70103` | `ssNMR` 与后续文献共同支持                       |
| Ain protonation             | phosphate `-2`, `O3 -1`, `N1 0`, `NZ +1`            | same as above                           | `10.1021/ja506267d`                        | 位点级证据最强                                     |
| Ain RESP 片段边界           | `ACE-LLP-NME` capped fragment                             | capping analysis;`FP-012`             | `N/A`                                      | LLP 是 polymer-linked residue，不能裸截断          |
| Ain capped fragment 规模    | `54 atoms`, `29 heavy + 25 H`                           | capping analysis; failure patterns      | `N/A`                                      | 满足 electron parity 且与当前 run file 一致        |
| Gaussian route              | `#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt` | validated `.gcrt`; `FP-013`         | `N/A`                                      | 这是当前在 Gaussian16 上已验证可运行的实现         |
| 常规 MD 引擎                | `AMBER pmemd.cuda`                                        | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 原文如此，且 GPU 性能优秀                          |
| MetaD 引擎                  | `GROMACS 5.1.2 + PLUMED2`                                 | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 严格复刻原始增强采样实现                           |
| 生产 MD 温度                | `350 K`                                                   | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 论文设定                                           |
| 生产 MD ensemble            | `NVT`                                                     | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 与论文生产阶段一致                                 |
| Path CV references          | `1WDW -> 3CEP`                                            | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 直接来自论文方法                                   |
| Path CV 帧数                | `15`                                                      | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 平衡路径分辨率与平滑性                             |
| Path atom set               | `Cα` of `97–184` and `282–305`                     | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 聚焦 COMM domain 主构象变化                        |
| `lambda`                  | `0.029`                                                   | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 由相邻路径帧 `MSD ≈ 80 Å²` 推得               |
| productive closure 判据     | `COMM RMSD < 1.5 Å` and `K82-Q2 <= 3.6 Å`             | manifest + JACS main-text reading notes | `10.1021/jacs.9b03646`                     | 同时要求全局闭合与局部催化几何到位                 |
| Multiple walkers            | `10`                                                      | JACS 2019 SI                            | `10.1021/jacs.9b03646`                     | 提高采样效率与收敛速度                             |
| Longleaf GROMACS conda 规范 | `module load anaconda/2024.02 && conda activate trpb-md`  | `FP-007`                              | `N/A`                                      | 避免环境路径硬编码失败                             |
| Slurm 线程规范              | `export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK`             | `FP-006`                              | `N/A`                                      | 避免 `GROMACS` 线程冲突                          |

### 读完检查

1. 在所有决策里，哪些是直接来自论文，哪些是项目为了在 Gaussian16/Longleaf 上稳定执行而增加的实现决策？
2. 为什么 `Ain charge = -2` 这个决策同时属于化学决策和工程决策？
3. 如果以后你想把 `GAFF` 换成 `GAFF2`，哪些表项会被连带影响？

---

## 第六部分：技术发展与批判性思考

这一部分不是在讲"我们用了什么"，而是在讲"为什么整个领域走到了这里，我们站在什么位置，前面还有什么没解决"。读完之后你应该能做到两件事：一是向任何人解释这条技术路线的历史合理性，二是指出它每一层的核心假设和已知弱点。

### 6.1 酶工程的五个时代

本节回答的问题是：从 directed evolution 到 GenSLM，酶工程的方法论经历了哪些范式转移，每一次转移解决了什么、又留下了什么。我们的项目处在第五个时代的入口。

酶工程的第一个时代始于 Frances Arnold 在 1990 年代建立的 directed evolution 框架（Nobel Chemistry 2018）。核心思路极其简洁：随机突变、高通量筛选、挑出赢家、重复。Arnold 的实验室用这套方法产出了数百种工程化酶，其中就包括 stand-alone TrpB 变体（Buller et al., *PNAS* 2015）。那项工作的一个关键发现是：60% 的激活突变位于 COMM domain 或 alpha/beta 界面区域——这直接把"构象动态"与"催化活性"联系在了一起。但 directed evolution 的根本瓶颈是组合爆炸：100 个残基的蛋白有 1,900 个单突变和超过 150 万个双突变，而典型实验室每轮只能筛选 10^3 到 10^4 个变体。

第二个时代是 rational/computational design，以 Rosetta（Baker Lab）和 FoldX 为代表。这些工具用能量函数预测哪些突变会改善稳定性或活性，从而把筛选空间从百万级压缩到几十个候选。2023 年 RFdiffusion 的出现（Watson et al., *Nature* 2023, DOI: 10.1038/s41586-023-06415-8）将 de novo 蛋白设计推到了皮摩尔级亲和力。然而这类方法的核心假设是静态结构：它们认为突变只在局部影响蛋白构型，不会改变大尺度构象动态。对 TrpB 来说这个假设是致命的——Osuna 2019 的整个论文都在说明 O/PC/C 构象转换是催化的关键，而 Rosetta-ddG 完全无法捕获这种运动。现有基准测试显示，静态方法的 Matthews correlation coefficient 在 0.3-0.5 之间，成功率约 15-40%。

第三个时代是 sequence-level machine learning（2019-2023），以 UniRep（Church Lab, 2019, DOI: 10.1038/s41592-019-0598-1）、ESM-2（Lin et al., *Science* 2023, DOI: 10.1126/science.ade2574）和 ProtTrans 为代表。这些模型在数百万条蛋白序列上训练，学到了进化共变模式并产生了编码生物物理性质的嵌入。但它们学到的是统计相关性，不是物理机制。它们无法告诉你一个突变为什么有效——只能告诉你它"看起来像"已知的功能序列。对于缺乏同源物的全新序列，zero-shot 性能会显著下降。

第四个时代是 generative protein language models（2022-至今）：ProtGPT2、ProGen2、EvoDiff（Microsoft, 2023）和 GenSLM（Argonne/NVIDIA, 2022, DOI: 10.1177/10943420231201154）。GenSLM 的独特之处在于它在 codon 层级（DNA）而非氨基酸层级工作，训练数据覆盖 1.1 亿条原核基因序列，最大规模达 250 亿参数。Lambert et al.（*Nature Communications* 2026, DOI: 10.1038/s41467-026-68384-6）用 GenSLM 为 TrpB 生成了 60,000 条新序列，实验验证显示许多序列不仅具有催化活性，还展现出超越天然酶的底物杂泛性。但关键问题是：他们的 in silico 过滤全部基于序列特征（ESM scores、同源性过滤），没有任何物理验证。他们知道这些酶有活性，但不知道为什么。

第五个时代——也是我们项目的定位——是 physics-informed generative design。核心思路是：用生成模型产出候选序列，然后用增强采样模拟（MetaDynamics）计算每个候选的构象自由能景观，将 FEL 特征作为 conformational filter 或 reward signal。这条路线同时利用了第四时代的生成能力和第二/三部分介绍的物理模拟精度。

> **批判性思考**：为什么不直接用 AlphaFold 验证生成的序列？因为 AlphaFold 预测的是单一静态结构，不是构象分布。Lane（2023）指出 AF2 "likely does not learn the energy landscapes underpinning protein folding and function"。对 TrpB 来说，COMM domain 的 O→C 转换涉及残基 102-189 的大规模集体运动——这恰好是 AlphaFold 无法表征的。
>
> **假设检验**："conformational dynamics → catalytic activity" 这个假设对 TrpB 有多可靠？答案是非常可靠。Buller 2015 发现 60% 的激活突变影响构象动态区域；Osuna JACS 2019 直接用 FEL 证明实验室进化变体将平衡态移向 Closed；Osuna ACS Catal. 2021（DOI: 10.1021/acscatal.1c03950）用 SPM 工具成功预测并实验验证了远端增强突变。这不是假说——这是被多个独立研究组验证过的结论。

### 6.2 增强采样方法演进

本节回答的问题是：从 umbrella sampling 到 OPES，增强采样方法的每一代解决了什么问题、又引入了什么新假设。理解这条演进线之后，你才能判断 well-tempered MetaDynamics 在 2019 年为什么是正确选择，以及今天有什么更好的替代。

Umbrella sampling（Torrie & Valleau, 1977, DOI: 10.1016/0021-9991(77)90121-8）是增强采样的起点。它的核心思路是沿预定义反应坐标放置一系列 harmonic biasing windows，分别模拟后用 WHAM 拼接出自由能面。这个方法有效但僵硬：你必须事先知道正确的反应坐标，窗口数量随维度指数增长，且没有自适应探索能力。

2002 年 Laio 和 Parrinello 提出标准 MetaDynamics（*PNAS* 99, 12562-12566, DOI: 10.1073/pnas.202427399），用一个优雅的思路替代了固定窗口：在 CV 空间当前位置定期沉积 Gaussian hills，让系统不断从已访问的 basin 被"推走"。这消除了预设窗口的需要，但引入了一个新问题——overfilling：由于 hill 高度恒定，偏置势永远不会收敛，而是在真实 FES 附近振荡。你无法确定什么时候应该停止模拟。

Well-tempered MetaDynamics（Barducci, Bussi & Parrinello, 2008, *Phys. Rev. Lett.* 100, 020603, DOI: 10.1103/PhysRevLett.100.020603）通过一个简单修改解决了 overfilling：让 hill 高度随已积累的偏置势衰减，衰减速度由 bias factor γ 控制。当 γ→∞ 时退化为标准 MetaD，当 γ=1 时退化为无偏模拟。这给了 WT-MetaD 平滑收敛的性质——偏置势最终收敛到 -(1-1/γ)F(s)。这正是我们项目使用的方法，也是 Osuna 2019 的选择。

但 WT-MetaD 有一个根本性弱点，是当前领域对它最强的批评：**orthogonal slow degrees of freedom 问题**。如果你选的 CV 捕获了 O→C 的主运动，但遗漏了一个耦合的慢运动（比如某个 loop 的重排或 side chain 的 rotamer 翻转），那么得到的 FES 会偏向最先被采样的 basin。Yang et al.（*Nature Communications* 2025, DOI: 10.1038/s41467-025-55983-y）直接证明了"biased trajectories from empirical collective variables display non-physical features"。此外，WT-MetaD 的实际 CV 维度上限约为 3——对涉及多域耦合运动的大蛋白构象变化来说，这可能不够。

2020 年 Invernizzi 和 Parrinello 提出 OPES（On-the-fly Probability Enhanced Sampling, *J. Phys. Chem. Lett.* 11, 2731-2736），从根本上重新思考了偏置构建方式：不再堆叠 Gaussian hills，而是用核密度估计直接估算 CV 空间的概率分布，再施加偏置使分布变为目标分布（通常是均匀分布）。OPES 收敛更快、参数更少更鲁棒、对次优 CV 的容忍度更高。它现已在 PLUMED 2.8+ 中实现，并逐渐成为 Parrinello 组推荐的 WT-MetaD 替代品。OneOPES（Rizzi et al., *JCTC* 2023, 19(17):5731-5742）进一步将多个 OPES 变体整合到 replica exchange 框架中。

另一条重要路线是 Gaussian Accelerated MD（Miao et al., 2015, *JCTC* 11, 3584-3595, DOI: 10.1021/acs.jctc.5b00436）——它完全不需要 CV，而是直接在总势能上加 boost potential。这对探索性研究特别有价值（你不知道哪些自由度是慢的），但它均匀降低所有势垒，无法聚焦到特定构象变化，因此自由能精度通常低于充分收敛的 MetaD。值得一提的是，GaMD 的开发者 Miao 实验室就在 UNC。

> **批判性思考**：Osuna 2019 选 WT-MetaD 对吗？在 2019 年完全正确——OPES 尚未发表，GaMD 对特定大尺度构象变化的聚焦加速不够，REST2 不给 FES。但如果今天（2025-2026）一个新组做同样的问题，大概率会选 OPES 或 OneOPES，配合 ML-learned CV 而非手工 Path CV。
>
> **核心假设审查**：WT-MetaD 的收敛依赖于 CV 的质量——如果 CV 遗漏了关键慢自由度，得到的 FES 可能定性上就是错的，而不只是"不够精确"。对我们的项目来说，Path CV 只描述了沿 O→C 路径的投影，任何正交于这条路径的慢运动都被忽略了。这不是可以通过增加模拟时间解决的问题。

### 6.3 集体变量设计演进

本节回答的问题是：为什么 Path CV 在 2007 年是一个突破，它的核心假设是什么，以及 ML-learned CV 为什么正在取代手工 CV。

Path CV 由 Branduardi, Gervasio 和 Parrinello 于 2007 年提出（*J. Chem. Phys.* 126, 054103, DOI: 10.1063/1.2432340），解决了一个长期困扰增强采样的问题：如何用少数几个变量描述复杂的多残基构象变化。它的巧妙之处在于把两种本应分开的信息显式分开——s(R) 描述"沿路径走到了哪里"，z(R) 描述"偏离路径多远"。这比单一 RMSD 更有信息量，因为 RMSD 会把"到达了目标但走了不同路线"和"到达了完全不同的状态"混为一谈。

然而 Path CV 有几个已知弱点，其中最关键的是对参考路径质量的依赖。在我们的项目中，参考路径是从 1WDW（Open）到 3CEP（Closed）的 Cα 线性插值，共 15 帧。这里的问题是：笛卡尔空间的线性插值不尊重构象能量面的曲率，可能产生不物理的中间构型——比如空间碰撞或不现实的骨架几何。而且 1WDW 是 PfTrpS（含 TrpA 亚基），3CEP 是 StTrpS（不同物种），两个端点来自不同生物体和不同寡聚态，它们是否真的代表同一酶在溶液中的 O 和 C 态 basin，是一个合理的疑问。

Felts et al.（*J. Phys. Chem. B* 2023, DOI: 10.1021/acs.jpcb.3c02028）指出了另一个具体问题：Cα-only Path CV 会漏掉侧链贡献。骨架可能已经到达了目标构型，但关键侧链仍然被困在旧 rotamer 中——给出一种"假阳性"的成功转换印象。

从 2020 年开始，Parrinello 组推出了 Deep-LDA 和 Deep-TDA（Bonati et al., *J. Phys. Chem. Lett.* 11, 2998-3004, 2020; Bonati et al., *PNAS* 118, e2113533118, 2021），用神经网络从短期无偏模拟数据中学习 CV。Deep-TDA 的训练目标是让不同亚稳态在投影空间中的分布匹配预设的 Gaussian target，使得学到的 CV 可以直接用于增强采样。2024 年 Frohlking et al. 进一步提出 Deep-LNE（*J. Chem. Phys.* 160, 174109），学习类似 Path CV 的路径坐标但完全从数据驱动，不需要手工选取 landmark 帧。

另一条路线是 VAMPnets（Mardt et al., *Nature Communications* 9, 5, 2018），用 variational score 学习动力学最慢的自由度。它和 TICA（Schwantes & Pande, 2013）的思路一脉相承——找最慢的模式——但用神经网络突破了 TICA 的线性限制。这些方法最初是为 MSM 分析设计的，但现在越来越多地被用作增强采样的 CV。

当前的 state-of-the-art 是将 ML CV 与 OPES 结合：用短期无偏模拟训练 Deep-TDA，用学到的 CV 驱动 OPES 采样，收集新数据后重新训练 CV，迭代直到收敛（arXiv:2410.18019, 2024 tutorial）。这解决了 CV 设计的 chicken-and-egg 问题——你需要好的 CV 来采样稀有事件，但你需要稀有事件的数据来学好的 CV。

> **批判性思考**：在我们的项目中，没有人做过 TrpB 的 Path CV 与 ML CV 对比。如果复刻完成后能做这个对比，将是一个有意义的 novel contribution。具体问题是：Deep-TDA 学到的 CV 会不会发现 Path CV 遗漏的构象通道？如果会，这将直接质疑 Osuna 2019 FEL 的完整性。
>
> **假设检验**：Path CV 假设真实的构象转换近似地沿着参考路径发生。如果真实路径有大曲率——比如先 loop closure 再 helix rotation 再 domain compaction——那么一个单一的 Path CV 会把这些序贯步骤压成一条模糊的投影，产生人为平滑的自由能面。

### 6.4 力场与电荷方法演进

本节回答的问题是：GAFF + RESP 作为非标准残基参数化的"标准流程"，它的物理假设有多强，以及现在有什么更好的替代。

GAFF（Wang et al., *J. Comput. Chem.* 25, 1157-1174, 2004）用 33 种基本原子类型覆盖 H/C/N/O/S/P 化学空间，设计初衷是与 AMBER 蛋白力场兼容。它对药物分子大小的有机物表现良好，但对 PLP 这样同时包含磷酸基团、吡啶环和 Schiff base 共轭体系的分子，torsion 参数来自有限的 QM 训练集，准确性存疑。Markthaler et al.（2019）发现所有四大通用力场（GAFF、GAFF2、CGenFF、OPLS-AA）对嘌呤衍生物的渗透压系数预测都很差，暗示芳香杂环参数存在系统性问题。

GAFF2（随 AmberTools 增量发布，从约 2015 年开始）改进了 van der Waals 参数和 torsion 参数，Kinateder 2025 的 TrpB 工作已使用 GAFF2。但 GAFF2 从未以单篇论文形式正式发表。更激进的变革来自 Open Force Field Initiative（2019 至今）：SMIRNOFF 格式用 SMIRKS pattern 直接感知化学环境，跳过了传统的 atom type 分类步骤。BespokeFit 可以为特定分子自动优化 torsion 参数——对 PLP 这种通用参数覆盖不佳的分子特别有价值。Espaloma-0.3（Takaba et al., 2024）走得更远，用图神经网络在超过 110 万条 QM 计算上训练，可以自洽地参数化蛋白和配体。

在电荷方面，RESP（Bayly et al., *J. Phys. Chem.* 97, 10269-10280, 1993）的核心假设是 HF/6-31G(d) 气相计算的系统性过极化近似模拟了凝聚相自极化效应。这个"trick"对中性药物分子校准过，但对 PLP 这样带 -2 电荷的磷酸化杂环辅因子，气相 ESP 是否仍然可靠是一个开放问题。Schauperl et al.（*Commun. Chem.* 3, 44, 2020）提出了 RESP2，混合 60% 水相和 40% 气相 QM 电荷，部分解决了这个问题，但尚未集成到标准 antechamber 工作流中。

机器学习势（ANI、MACE、NequIP）在 2024-2025 年取得了巨大进展——MACE-OFF（Batatia et al., *JACS* 2024, DOI: 10.1021/jacs.4c07099）对有机分子达到了接近 DFT 的精度，甚至成功模拟了 crambin 在显式水中的折叠（18,000 原子）。但对于我们的 500 ns MetaDynamics + 50,000 原子体系，ML 势比经典力场慢 100-1000 倍，目前不可行。不过 Delta-MLP QM/MM 方案（2025）已经展示了在酶催化反应中的可转移性——如果未来的问题是 PLP 的化学步骤而非 COMM domain 动态，QM/MM + MetaD 将是正确选择。

> **批判性思考**：GAFF 是整个参数化链中最弱的一环。PLP 吡啶环周围的 torsion profile、Schiff base C4'-NZ 键的旋转势垒、磷酸酯基团的构象偏好——这些都是 GAFF 通用参数只能近似覆盖的。我们的 FP-010 已经证明 antechamber 会在缺氢时错误分配原子类型。即使类型分配正确，参数本身的准确度也只是"大致合理"。
>
> **假设检验**：对于 COMM domain 构象动态来说，PLP 电荷的精确值可能不是决定性因素——驱动大尺度骨架运动的主要力来自氢键网络、盐桥和疏水接触，这些由 ff14SB 良好描述。因此 GAFF+RESP 对 PLP 的近似在当前科学问题（构象动态，非化学反应）的语境下是 defensible 的。但如果将来要研究 PLP 的催化化学步骤，就必须升级到 QM/MM。

### 6.5 我们的定位：GenSLM + MetaDynamics Pipeline

本节回答的问题是：把所有技术线汇合起来，我们的项目到底在整个领域里处于什么位置，填了什么 gap。

Lambert et al. 2026 用 GenSLM 生成了 60,000 条 TrpB 序列并实验验证了催化活性和底物杂泛性——但没有使用任何物理模拟。他们的 in silico 过滤完全基于序列特征。与此同时，METL（*Nature Methods* 2025, DOI: 10.1038/s41592-025-02776-2）在 Rosetta 模拟数据上预训练 transformer 后，仅用 64 个实验数据点就能准确预测突变效应。SeqDance（*PNAS* 2026, DOI: 10.1073/pnas.2530466123）在超过 64,000 个蛋白的 MD 动力学数据上训练 PLM，显示动力学信息显著提升突变效应预测。REINVENT+ESMACS（*JCTC* 2024, DOI: 10.1021/acs.jctc.4c00576）在 Frontier 百亿亿次计算机上对小分子实现了 generative AI + 结合自由能模拟的闭环设计。

但关键事实是：**没有人对蛋白质构象动态做过 generate → simulate → retrain 的闭环。** 这是我们项目的 novelty claim。

具体而言，我们的 pipeline 设想是：

1. GenSLM 生成 TrpB 候选序列（~1000 条）
2. 快速预筛：SPM + 短 MD（每个突变体数小时，筛掉 ~950 条）
3. 精细验证：Well-tempered MetaDynamics 计算 top 50 候选的 FEL
4. 从 FEL 提取 reward signal：O→C 势垒高度、C 态相对稳定性、productive closure 概率
5. 用 reward 反馈 GenSLM 微调（或训练 ML surrogate 作为快速 reward proxy）

这条路线之所以对 TrpB 有独特的合理性，是因为"构象动态→催化活性"的因果链在这个体系中已被反复验证：Osuna JACS 2019 和 ACS Catal. 2021 的工作直接证明了 FEL 特征与实验活性的对应关系。TrpB 不是一个需要假设动态-活性关联的体系——它是一个已经被证明了这种关联的体系。

关于速度瓶颈：全原子 WT-MetaD 对 TrpB 单个突变体需要 3-7 天（4 个 walker，1 个 GPU）。如果要筛选 1000 个候选，直接全做需要约 14 GPU-年。但用分层策略——SPM 预筛（1 小时/突变体）→ MetaD 精筛（top 50）——总墙钟时间约一周，在中等规模 HPC 上完全可行。

> **批判性思考**：这个 pipeline 最弱的环节是什么？是 reward signal 的设计。我们知道 O→C 势垒和 C 态稳定性与活性相关，但这种相关是定性的，不是定量的。Osuna 的工作说明了"FEL shifted toward Closed = more active"，但没有给出 ΔF → Δk_cat 的定量关系。建立这种定量关系将是一个显著的科学贡献。
>
> **假设检验**：整个 pipeline 的核心假设是"序列→构象动态→催化活性"可以用来做 reward。如果某些突变体的活性提升主要来自化学步骤（键的断裂与形成）而非构象变化呢？那么 MetaDynamics 的 conformational filter 就会漏掉它们。这个假设在 TrpB 的 COMM domain 控制型催化中是合理的，但不应不加验证地推广到所有酶体系。

### 6.6 未解决的问题与研究机会

本节回答的问题是：在这条技术路线上，哪些问题目前没有人解决过？

**Reward signal design。** FEL 的哪些具体特征最能预测催化活性？势垒高度、basin 相对深度、路径保真度、productive closure 的概率——这些特征的预测权重从未被系统比较过。

**构象 filter 的可推广性。** 现有的所有基于动力学的酶设计研究都是 case-specific 的（TrpB、adenylate kinase 等）。没有通用框架告诉你"这个酶需要什么类型的动态特征作为 filter"。

**速度-精度的 Pareto frontier。** 从秒级的 SeqDance zero-shot 预测到周级的全原子 MetaD，中间存在巨大的精度-速度谱系。最优的折中点在哪里？在什么近似水平上你会失去预测能力？

**多目标优化。** 酶需要同时具备稳定性、活性、可表达性和选择性。如何将 MetaDynamics 构象数据与稳定性/溶解度预测整合到一个优化目标中？

**构象空间中的 epistasis。** 多个突变如何协同影响 FEL？DCIasym GNN（*PNAS* 2025, DOI: 10.1073/pnas.2502444122）展示了用 MD 衍生特征建模 epistatic 效应的可行性，但没人将其应用于 generative design。

**Data-efficient MetaDynamics。** 当前的 MetaD 协议假设每个突变体都要从头做。如果能在相似突变体之间转移已收敛的偏置势（bias transfer），收敛时间可能大幅缩短。这在概念上类似于 transfer learning，但技术实现尚未被验证。

**Path CV vs ML CV for TrpB。** 如前所述，没有人做过这个直接对比。如果在复刻完成后用 Deep-TDA 学习 CV 并与 Path CV 的 FEL 比较，将是一个明确的 novel contribution——它可以回答"Osuna 2019 的 FEL 有多完整"。

### 读完检查

1. Lambert 2026 生成了 60,000 条 TrpB 序列但没做物理验证——如果你来填这个 gap，你会怎么设计 pipeline？
2. WT-MetaD 最被诟病的弱点是 orthogonal DOF 问题。在 TrpB 的 COMM domain 运动中，你能想到哪些可能被 Path CV 遗漏的耦合慢运动？
3. GAFF+RESP 对 PLP 的参数化是 defensible 的——但只在"我们研究的是构象动态而非化学反应"的前提下。如果研究问题变成 PLP 催化机制，你需要升级什么？
4. 如果今天（2026）一个新组要做和 Osuna 2019 相同的科学问题，他们最可能用的方法栈是什么？（提示：OPES + ML CV + 什么预筛策略？）
5. "没有人对蛋白质构象动态做过 generate → simulate → retrain 的闭环"——你觉得技术上最大的 bottleneck 是什么？

---

## 附录

### A. 术语表


|                        |                                |                                                    |
| ---------------------- | ------------------------------ | -------------------------------------------------- |
|                        |                                | 论文与当前复刻使用的显式水模型                     |
| `PME`                | Particle-Mesh Ewald            | 周期性边界下的长程静电处理方法                     |
| `SHAKE`              | bond constraint algorithm      | 这里主要用于约束水分子几何与高速键振动             |
| `walker`             | 并行采样副本                   | Multiple-walker MetaD 中共享 bias 的一个独立轨迹   |
| `HILLS`              | MetaD bias history file        | 记录 Gaussian hills，供 `sum_hills` 重建 `FES` |
| `COLVAR`             | collective variable trajectory | 记录 `s,z` 与监测量随时间变化                    |
| `productive closure` | productive 的闭合构象          | 同时满足全局 closed-like 与局部催化几何条件的状态  |

### B. 文献引用列表

这一节回答的问题是：本文依赖了哪些核心文献，每篇文献分别提供了什么不可替代的信息。这里只列对当前 benchmark 直接有用的 references。

| 文献                                                           | DOI                            | 一句话说明                                                                                                                  |
| -------------------------------------------------------------- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Maria-Solano MA, Iglesias-Fernández J, Osuna S. 2019,*JACS* | `10.1021/jacs.9b03646`       | 本项目的主 benchmark 文献，提供 `ff14SB + GAFF + RESP`、`Path CV`、`WT-MetaD` 和 `multiple walkers` 的核心 protocol |
| Caulkins BG et al. 2014,*JACS*                               | `10.1021/ja506267d`          | 用 `ssNMR` 给出 TrpS Ain 中 `PLP` 位点级质子化证据，是 `charge = -2` 的决定性来源                                     |
| Huang et al. 2016,*Protein Science*                          | `10.1002/pro.2709`           | 比较多套 `PLP` 质子化方案，说明 NMR-consistent 模型在动力学上最合理                                                       |
| Kinateder et al. 2025,*Protein Science*                      | `10.1002/pro.70103`          | Osuna 组后续 TrpB 工作，说明 `RESP @ HF/6-31G(d)` 与 `PLP` 化学建模仍是主流做法                                         |
| Lambert T et al. 2026,*Nature Communications*                | `10.1038/s41467-026-68384-6` | 给出本项目上游的生成式酶设计背景，解释为什么需要把 MetaDynamics 变成 reward-bearing physics layer                           |
| Maria-Solano et al. 2021,*ACS Catalysis*                     | `10.1021/acscatal.1c03950`   | 展示 Osuna 路线如何把构象动力学与远端突变设计联系起来，对后续扩展任务有参考价值                                             |

### C. 文件索引

这一节回答的问题是：项目里最重要的文件分别在哪里，应该在什么时候看它们。它相当于一个面向执行者的本地地图。

| 文件                                                | 位置                                         | 用途                                              |
| --------------------------------------------------- | -------------------------------------------- | ------------------------------------------------- |
| `FULL_LOGIC_CHAIN.md`                             | `project-guide/`                           | 给出整个项目的科学逻辑主线                        |
| `PLP_SYSTEM_SETUP_LOGIC_CHAIN.md`                 | `project-guide/`                           | 记录 PLP 参数化与系统搭建的实现细节与历史推理     |
| `PROJECT_OVERVIEW.md`                             | `project-guide/`                           | 高层目标、阶段划分、项目定位                      |
| `PROTOCOL.md`                                     | repo root                                    | 六阶段 pipeline 规则与当前 campaign 状态          |
| `JACS2019_MetaDynamics_Parameters.md`             | `replication/parameters/`                  | 从 SI 提取的论文计算参数总表                      |
| `2026-03-30_plp_protonation_literature_review.md` | `replication/validations/`                 | Ain/LLP `charge = -2` 的文献证据汇总            |
| `2026-03-30_capping_analysis.md`                  | `replication/validations/`                 | 为什么 Ain RESP 必须 `ACE/NME` capping          |
| `failure-patterns.md`                             | `replication/validations/`                 | 已踩过的 13 类错误模式及修复规范                  |
| `osuna2019_benchmark_manifest.yaml`               | `replication/manifests/`                   | 当前 benchmark 的 machine-readable 决策摘要       |
| `5DVZ.pdb`                                        | `replication/structures/`                  | Ain 的源结构，`chain A residue 82 = LLP`        |
| `build_llp_ain_capped_resp.py`                    | `scripts/`                                 | 从 `5DVZ` 生成 Ain capped Gaussian input 的脚本 |
| `LLP_ain_resp_capped.gcrt`                        | `replication/parameters/resp_charges/ain/` | 当前实际运行的 Ain Gaussian input                 |
| `submit_gaussian_capped.slurm`                    | `replication/parameters/resp_charges/ain/` | 当前 Ain Gaussian Slurm 模板                      |
| `parameterize_plp.sh`                             | `replication/scripts/`                     | 参数化流程脚本化尝试与自动化入口                  |
| `plumed_trpb_metad.dat`                           | `replication/scripts/`                     | 当前 TrpB MetaD 的 PLUMED 模板                    |
| `resource_inventory.md`                           | `replication/inventories/`                 | 软件、文献、环境、资产的本地盘点                  |
| `README_plp_param.md`                             | `replication/scripts/`                     | 参数化工作流说明，但部分内容已落后于当前 Ain 结论 |
| `GLOSSARY.md`                                     | repo root                                    | 术语速查表                                        |
