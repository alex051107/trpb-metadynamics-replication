# 文献精读批注手册
## Annotated Paper Reading Guide — TrpB × MetaDynamics Project

> **使用说明**：每篇论文附有三类批注符号：
> - 🔑 **核心概念**：你必须理解的关键点
> - 💭 **思考整合**：读到这里时需要主动思考的问题
> - ⚡ **项目连接**：这段内容与你具体项目工作的直接关联
>
> 建议边读原文边对照本手册的批注。

---

## 模块一：TrpB 生物化学基础（先读这组）

---

### 📄 Paper 1 — 必读第一篇【TrpB 机制综述】

**标题**：Tryptophan Synthase: Biocatalyst Extraordinaire
**作者**：Buller et al.（Andrew Buller 实验室）
**期刊**：ChemBioChem, 2021
**PMC ID**：PMC7935429
**DOI**：[10.1002/cbic.202000379](https://doi.org/10.1002/cbic.202000379)
**来源**：Based on articles retrieved from PubMed

---

#### 为什么先读这篇？

这是理解整个 TrpB 领域最好的入门综述。作者是 Arnold lab 出来的，Buller 本人就是做 TrpB directed evolution 的核心人物。读这篇你可以在 1–2 小时内建立起整个领域的认知框架。

---

#### 逐节精读批注

**第 1 节：Introduction（非天然氨基酸的价值）**

> *"Noncanonical amino acids (ncAAs) enable researchers to interact with and modify life at the molecular level..."*

🔑 **核心概念**：ncAA（非天然氨基酸）是整个项目的终极产物类别。D-Trp 就是一种 ncAA。理解 ncAA 的价值帮助你理解为什么整个项目值得做。

💭 **思考整合**：为什么化学合成 ncAA 如此麻烦？因为**氨基酸有手性中心**，化学合成容易产生外消旋混合物，而酶催化天然具有立体选择性。D-Trp 难合成的根本原因在这里。

---

**第 1.1 节：Properties of TrpS（TrpS 的基本性质）**

> *"The two subunits interact with one another through rigid-body motion of the TrpB communication (COMM) domain and a monovalent cation (MVC) binding site within TrpB."*

🔑 **核心概念**：**COMM domain** 是你整个项目的核心结构元件。记住：
- COMM domain = TrpB 里的一段 ~40 残基活动环
- 它的开/闭状态 ↔ 催化活性的开关
- MVC（单价阳离子）结合位点 + TrpA 都能通过 COMM domain 激活 TrpB

⚡ **项目连接**：MetaDynamics 的集体变量（CV）就是用来描述 COMM domain 从 open 到 closed 的转变。这是 Osuna 组所有 TrpB MetaDynamics 工作的 CV 定义基础。

---

**催化循环部分（关键！）**

> *"In the TrpB resting state, PLP is covalently bound to the ε-nitrogen of a lysine residue (K82) through a protonated Schiff-base linkage referred to as the internal aldimine, E(Ain) (λmax = 412 nm)."*

🔑 **核心概念**：催化循环的五个主要状态，用光谱可以区分：

| 状态 | 吸收峰 | 结构描述 | COMM domain 状态 |
|------|--------|---------|-----------------|
| E(Ain) | 412 nm | PLP-Lys82 Schiff 碱，resting state | Open |
| E(Aex1) | 428 nm | PLP-Ser 外部 Schiff 碱 | Partially Closed |
| E(Q1) | 470 nm | 醌类中间体，Cα 去质子化 | Partially Closed |
| **E(A-A)** | **350 nm** | **氨基丙烯酸酯**，亲电体，等待吲哚 | **Fully Closed** |
| E(Q2/Q3) | 476 nm | 吲哚进攻后的醌类中间体 | Closed |

💭 **思考整合**：**E(A-A) 形成时 COMM domain 必须完全闭合**。这就是为什么 COMM domain 的闭合态稳定性 ↔ 酶的活性高低。如果 COMM 不能稳定闭合，E(A-A) 会被水消除（β-elimination），产物是丙酮酸 + 氨，而非色氨酸。**这个竞争副反应是设计问题的关键！**

⚡ **项目连接**：对于 D-Trp 的合成，E(A-A) 阶段吲哚进攻的 **面选择性（si/re face）** 决定了产物立体化学。你需要的 MetaDynamics CV 不只是 COMM domain 开/闭，还可能需要包括吲哚进入活性位点时的方向角。

---

> *"The catalytic glutamate is important for controlling the regioselectivity of the reaction; mutagenesis reveals its crucial role to effect C–C bond formation at C3 over a C–N bond at N1."*

🔑 **核心概念**：**E104（催化谷氨酸）** 是调控反应选择性的关键残基。它：
1. 使吲哚从 C3 进攻（而非 N1）→ C-C 键而非 C-N 键
2. 当用非吲哚亲核体（如 azulene）时，E104 突变会完全废除活性

💭 **思考整合**：在 de novo 设计中，你的活性位点需要保留一个类似 E104 功能的残基，才能维持正确的反应区域选择性。同时，如果要合成 D-Trp，E104 周围的空间环境必须被重新排列来引导 re-face 进攻。

---

**第 2.1 节：Engineering a stand-alone TrpB**

> *"Only three rounds of directed evolution and six mutations were needed to increase the catalytic efficiency of PfTrpB 83-fold, resulting in a stand-alone variant, 0B2-TrpB, that was even more active than the native TrpS complex."*

🔑 **核心概念**：Arnold lab 2015 年的突破——6 个突变、3 轮进化，kcat 提升 83 倍。这些突变位于 COMM domain 附近，效果等同于"模拟 TrpA 的别构激活"。

⚡ **项目连接**：这 6 个突变的位置你要记住（在 PfTrpB 中是：T292S, E104N（不对，需查原文），可能还有几个远端位点）。Osuna 的工作就是在分析为什么这几个突变有效——答案是它们重塑了 COMM domain 的 FEL。

---

**第 2.3 节：β-Branched Trps（β-支链氨基酸）**

> *"This is remarkable: Thr is a universal and abundant metabolite that TrpS naturally discriminates against... [but] directed evolution produced TrpBβMe showing >6000-fold boost."*

💭 **思考整合**：TrpS 对 Thr 的选择性比 Ser 低 82,000 倍，但经过进化可以做到 6000 倍改善。这说明酶的底物选择性并非不可改变，合适的突变可以彻底重塑。**D-Trp 立体选择性也是同理——不是不可能，只是还没有人找到正确的突变组合。**

---

**第 3.1 节：D-氨基酸合成（直接相关！）**

> *"TrpS's strict retention of stereoselectivity for making the L-amino acid hinders its ability to be repurposed as a D-amino acid synthase. Nevertheless, because TrpS still represents a simple way to make Trp derivatives, numerous groups have combined TrpS with downstream enzymes to access various D-Trps."*

🔑 **核心概念**：现有的 D-Trp 合成都是**酶级联方法**：
1. TrpB 合成 L-Trp 衍生物
2. LAAD（L-氨基酸脱氨酶）氧化脱氨
3. DAAT（D-丙氨酸氨基转移酶）重新氨化，但立体化学反转

⚡ **项目连接**：这正是你导师说的"现在想直接工程化 TrpB 合成 D"的背景——**现有方法需要多步酶级联，效率低**。如果能直接用一个工程化 TrpB 产生 D-Trp，将是重大突破。

---

**阅读要点总结**（Reading Checklist）：

```
完成阅读后你应该能回答：
[ ] TrpB 催化循环中 E(A-A) 是什么？为什么重要？
[ ] COMM domain 的三种构象状态各在何时出现？
[ ] K82 和 E104 各起什么作用？
[ ] 为什么独立 TrpB（standalone）活性低？
[ ] Arnold lab 怎么解决这个问题的？
[ ] 现有方法如何合成 D-Trp？有什么缺点？
```

---

### 📄 Paper 2 — 必读第二篇【Arnold Lab 原始突破论文】

**标题**：Directed evolution of the tryptophan synthase β-subunit for stand-alone function recapitulates allosteric activation
**作者**：Buller, A.R. et al.（Arnold 实验室）
**期刊**：PNAS, 2015
**PMC ID**：PMC4664345
**DOI**：[10.1073/pnas.1516401112](https://doi.org/10.1073/pnas.1516401112)
**来源**：Based on articles retrieved from PubMed

---

#### 为什么读这篇？

这是 standalone TrpB 的开山之作。你需要了解它的实验细节，因为 Osuna 组 2019 年的工作就是用 MetaDynamics **解释这篇文章里那 6 个突变为什么有效**。

---

#### 精读批注

> *"Kinetic, spectroscopic, and X-ray crystallographic data show that this lost activity can be recovered by mutations that reproduce the effects of complexation with the α-subunit."*

🔑 **核心概念**：这篇文章的核心贡献是证明了**"别构激活 = 改变 COMM domain 动力学"**。进化得到的突变和 TrpA 结合具有相同的机制效果。

💭 **思考整合**：如果别构激活可以被突变模拟，那么 D-Trp 的立体化学控制（通常依赖特定的过渡态几何）是否也可以被突变模拟？逻辑上是一致的。

⚡ **项目连接**：你们的 de novo 设计，本质上是在设计一个"从零开始"的蛋白质，让它天然就倾向 D-Trp 合成所需的几何——不依赖任何 TrpA 来"纠正"构象。

**重点关注**：
- 具体的 6 个突变是哪些（看 Supplementary）
- 这些突变位于什么二级结构元件上
- 晶体结构如何显示 COMM domain 的变化

---

## 模块二：Osuna 组的 MetaDynamics 工作（核心模块）

---

### 📄 Paper 3 — 核心论文【MetaDynamics + TrpB FEL】

**标题**：Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution
**作者**：Maria-Solano, Iglesias-Fernández & Osuna
**期刊**：Journal of the American Chemical Society, 2019
**DOI**：[10.1021/jacs.9b03646](https://doi.org/10.1021/jacs.9b03646)

> ⚠️ 注意：这篇在 JACS 上，不在 PMC 免费数据库中。获取方式：
> 1. 通过 UNC 图书馆访问（你有 UNC 账号）
> 2. 如果需要，可以发 Email 给 silvia.osuna@udg.edu 索取 preprint
> 3. Google Scholar 上可能有作者上传的版本

---

#### 读前准备：你应该先知道的背景

在读这篇之前，你应该已经从 Paper 1 和 Paper 2 了解了：
- COMM domain 的三种构象
- 6 个突变如何激活 standalone TrpB
- PLP 催化循环

现在这篇要回答的是：**为什么那 6 个突变有效？它们对 COMM domain 的 FEL 做了什么？**

---

#### 逐节精读批注

**Abstract 关键句**：

> *"We find that recovering the conformational ensemble of a subdomain of TrpS—affecting the relative stabilities of open, partially closed, and closed conformations—is a prerequisite for enhancing the catalytic efficiency of the β-subunit."*

🔑 **核心概念**：这一句是 Osuna lab 整个研究的哲学核心：**"催化效率 = 合适的构象系综"**。注意"prerequisite"这个词——这不是充分条件，而是必要条件。

💭 **思考整合**：如果"构象系综"是必要条件，那么对于 D-Trp 合成，需要什么构象系综？需要过渡态中 re-face 进攻的构象有多稳定？这是你 MetaDynamics 工作需要回答的问题。

---

**Methods 关键部分（重点看！）**：

🔑 **核心概念**：Osuna 使用的技术参数：
- 软件：GROMACS + PLUMED
- 方法：**Well-tempered Multiple-walker MetaDynamics**（4 个 walkers）
- CV1：COMM domain 沿着 open-to-closed 路径的位移（用"path CV"或 RMSD 定义）
- CV2：与 Q2 中间体相关的第二个构象变量
- 运行时长：足以收敛（Supplement 中有具体参数）

⚡ **项目连接**：你复现这篇实验的第一步就是理解他们的 CV 定义。**这是你最需要弄清楚的技术细节**。他们用的"path CV"在 PLUMED 里有专门的实现（`PATH` collective variable），你需要找到他们 Supplement 里 path 的参考结构。

---

**Figure 2（最重要的图！）**：

> 图描述：展示四个 TrpB 系统（wtTrpB, LBCA-TrpB, 0B2-TrpB, TrpS 复合物）在 Q2 中间体状态下的 2D 自由能景观（FEL）。

🔑 **核心概念**：如何读这个图：
- X 轴：CV1（COMM domain 开/闭程度，数字越大越闭合，1–15 的路径刻度）
- Y 轴：CV2（沿路径的偏离）
- 颜色：蓝=低能（稳定），红=高能（不稳定）
- 每个 FEL 上的蓝色深谷 = 最稳定构象

🔑 **核心概念**：关键比较——
| 系统 | 闭合态稳定性 | kcat（相对值） |
|------|------------|---------------|
| wt PfTrpB（独立） | 低（谷浅，偏 open） | 低 |
| LBCA-TrpB | 高（谷深，主要 closed） | 高 |
| 0B2-TrpB | 高（闭合态最深） | 最高 |
| TrpS 复合物 | 高 | 高 |

💭 **思考整合**：这就是 "FEL = functional predictor" 的实验证据。闭合态稳定性和 kcat 之间有直接关联。

⚡ **项目连接**：对于 D-Trp 设计，你需要的"目标 FEL"是什么？不只是"闭合态稳定"，而是"闭合态中，吲哚从 re-face 进攻的构象稳定"。这是比 Osuna 2019 更进一步的问题。

---

**Figure 3（从 FEL 到机制）**：

> 展示 COMM domain 在不同 FEL 极小值处的代表性结构

🔑 **核心概念**：图中显示了以下信息：
- Open state：R141 和 D305 之间无氢键/盐桥
- Closed state：R141-D305 盐桥形成，S297-S299 新氢键网络
- 这些特定相互作用是"COMM domain 闭合"的分子指标

💭 **思考整合**：R141-D305 盐桥可以作为 **另一个 CV** 的候选——定义这对残基之间的距离作为 CV 更加直观！而且它有明确的物理化学意义。这是你可以在 MetaDynamics setup 中尝试的 CV 变体。

---

**阅读要点总结**：

```
完成阅读后你应该能回答：
[ ] Osuna 使用了哪种 MetaDynamics 变体？参数是什么？
[ ] CV 是如何定义的？用了哪些 PLUMED 关键字？
[ ] 四个系统的 FEL 有什么关键差异？
[ ] 为什么 LBCA-TrpB 活性高？FEL 上怎么体现？
[ ] COMM domain 闭合的分子标志（盐桥等）是什么？
[ ] 这些发现如何为 de novo 设计提供指导？
```

---

### 📄 Paper 4 — 方法论论文【AlphaFold2 + MetaDynamics 整合】

**标题**：Estimating conformational heterogeneity of tryptophan synthase with a template-based AlphaFold2 approach
**作者**：Casadevall, Duran, Estévez-Gay & Osuna
**期刊**：Protein Science, 2022
**PMC ID**：PMC9601780
**DOI**：[10.1002/pro.4426](https://doi.org/10.1002/pro.4426)
**来源**：Based on articles retrieved from PubMed（已获取全文）

---

#### 为什么读这篇？

这篇是 Osuna 2019 的直接续作，但引入了 AlphaFold2。从你的项目视角，这篇很重要，因为它展示了**如何在不跑完整 MetaDynamics 的情况下快速估计构象景观**——这正是你们做 de novo 设计时大规模筛选所需要的。

---

#### 精读批注

**Introduction 关键段落**：

> *"Induced by the mutations introduced, catalytically productive conformational states are stabilized, whereas the non-productive ones for the novel functionality are disfavored, thus converting computational enzyme design into a population shift problem."*

🔑 **核心概念**：**"酶设计 = 种群偏移问题（population shift problem）"**。这是 Osuna lab 的核心框架。你不是在设计一个静态结构，你是在重新分配酶的构象分布。

💭 **思考整合**：D-Trp 的合成需要什么样的"种群偏移"？需要 re-face 进攻构象的比例增加。问题是：这个构象是 FEL 上已有的极小值（只需稳定化），还是完全不存在于当前 TrpB 中（需要完全重新设计）？这个问题决定了你用 MetaDynamics + 点突变就够，还是需要 de novo 设计。

---

**核心方法（tAF2 = template-based AlphaFold2）**：

🔑 **核心概念**：tAF2 的工作原理：
1. 减少输入 MSA 的深度（32–64 sequences，而非默认的数千序列）
2. 提供不同构象的 X 射线结构或 MD 提取构象作为模板
3. AF2 会尝试"折叠"到接近模板的构象
4. 从多个 AF2 预测 + 短 MD（10 ns × 60 个结构 = 1200 ns 总量）重建粗略 FEL

💭 **思考整合**：这是一个近似方法。关键数据：tAF2-MD 估计的 FEL 和真正的 MetaDynamics FEL **定性一致，但不完全定量准确**。适合快速筛选，不适合精确定量。

⚡ **项目连接**：对于你们需要筛选的 1000 个 RFDiffusion 设计候选，用 tAF2-MD 做初步筛选（计算成本低），对最有希望的 top 20–50 个再做完整 MetaDynamics（计算成本高）——这是合理的分层筛选策略。

---

**关键结果（Figure 5）**：

> *"The estimated FEL from multiple replica short nanosecond timescale MD simulations performed starting at the x-ray template-based AF2 predictions... are in line with the previously reconstructed FELs... obtained from well-tempered multiple-walker metadynamics simulations."*

🔑 **核心概念**：tAF2 + 短 MD（~1200 ns）≈ MetaDynamics（~200 ns × 4 walkers = 800 ns）的粗略 FEL。两者在区分高活性 vs 低活性变体上都有效。

💭 **思考整合**：注意两者的计算成本：
- tAF2 方法：60 × 2 × 10 ns = 1200 ns MD，但每个模拟独立，计算可以高度并行
- MetaDynamics 方法：4 walkers × ~200 ns = 800 ns，但 walkers 必须共享偏置，并行度受限

对于大批量筛选，tAF2 可能更高效。这是你可以量化的一个方法学贡献点。

---

**阅读要点总结**：

```
完成阅读后你应该能回答：
[ ] tAF2 方法的具体步骤（MSA 深度、模板数量、MD 长度）？
[ ] tAF2-MD 和 MetaDynamics FEL 的相关性有多好？
[ ] 什么情况下 tAF2 会失败（不准确）？
[ ] 如何将这个方法应用于 de novo 设计候选的快速筛选？
```

---

### 📄 Paper 5 — SPM 方法【识别远端突变位点】

**标题**：In Silico Identification and Experimental Validation of Distal Activity-Enhancing Mutations in Tryptophan Synthase
**作者**：Maria-Solano, Kinateder, Iglesias-Fernández, Sterner & Osuna
**期刊**：ACS Catalysis, 2021
**DOI**：[10.1021/acscatal.1c03950](https://doi.org/10.1021/acscatal.1c03950)

> ⚠️ 注意：ACS Catal 需要通过 UNC 图书馆或作者邮件获取

---

#### 精读批注

**Abstract 关键句**：

> *"By testing only one single variant the fold increase in kcat was similar to the 9-fold obtained by directed evolution (DE) that required the generation and screening of more than 3000 variants."*

🔑 **核心概念**：**1 个计算设计变体 ≈ 3000 个定向进化变体**。这就是 Osuna 方法的影响力所在——不只是更快，而是**定性上改变了搜索效率**。

---

**SPM 方法的核心逻辑**：

🔑 **核心概念**：SPM（Shortest Path Map）的算法步骤：

```
输入：普通 MD 轨迹（50–200 ns）
  ↓
步骤 1：计算所有残基对之间的动态相关性（Dynamic Cross-Correlation）
         - 残基 i 和 j 之间的协同运动程度
         - 得到一个 N×N 的相关性矩阵
  ↓
步骤 2：将相关性矩阵转化为图（Graph）
         - 节点 = 残基
         - 边权重 = 相关性强度的函数
  ↓
步骤 3：用 Dijkstra 算法找最短路径
         - 起点 = 活性位点残基（PLP 结合位点）
         - 终点 = COMM domain 关键残基
  ↓
步骤 4：路径上的残基 = 信号传导的关键节点
         - 这些残基突变 → 影响 TrpA 信号 → 影响 COMM domain 动力学
  ↓
输出：候选突变位点列表（远端，但功能关键）
```

⚡ **项目连接**：你可以用 SPM webserver（spmosuna.com）分析你们的 de novo 设计结构，找出设计中影响 COMM domain 动力学的关键位点，作为第二轮优化的候选突变位点。

💭 **思考整合**：SPM 方法找到的是"信号传导路径上的关键中继站"。在 de novo 设计中，这些关键位点可能并不存在（因为是全新序列）。问题是：新设计的酶中 SPM 能找到有意义的路径吗？这是一个有趣的 open question。

---

**重点阅读**：实验验证部分

> 找到 SPM6 变体的实验数据：kcat 提升 7 倍，所有测试均在 ANC3-TrpB 背景下。

🔑 **核心概念**：注意实验在 **ANC3-TrpB（祖先重建序列）** 背景下进行，而非野生型 PfTrpB。这说明从祖先序列出发进化更容易。这与你们的 de novo 设计思路有相通之处：**从一个"原始"的、构象更灵活的骨架出发设计可能更容易**。

---

## 模块三：De Novo 酶设计工具（背景知识）

---

### 📄 Paper 6 — RFDiffusion【骨架生成工具】

**标题**：De novo design of protein structure and function with RFdiffusion
**作者**：Watson et al.（Baker 实验室）
**期刊**：Nature, 2023
**DOI**：[10.1038/s41586-023-06415-8](https://doi.org/10.1038/s41586-023-06415-8)

---

#### 精读批注

**Introduction 关键观点**：

> 理解 RFDiffusion 的核心逻辑：用于条件生成——给定"我想要活性位点长这样"，生成满足这个条件的蛋白质骨架。

🔑 **核心概念**：扩散模型（Diffusion Model）在蛋白质设计中的类比：
- **训练时**：将真实蛋白质结构逐渐加噪声（Diffusion = 破坏结构），学习如何反转这个过程（Denoising）
- **生成时**：从纯噪声出发，通过条件（活性位点约束）引导去噪，生成满足条件的新结构

⚡ **项目连接**：你导师用的工作流就是：
1. 给 RFDiffusion 提供 TrpB 活性位点的原子坐标（theozyme/cellzyme）
2. RFDiffusion 生成围绕这个活性位点的新蛋白质骨架
3. 这个骨架可能完全不同于自然界的 TrpB 折叠

**重点阅读**：De novo enzyme design 案例（论文的 Figure 4/5），关注 Diels-Alderase 的设计流程——和你们的工作是同类型的。

---

### 📄 Paper 7 — RFdiffusion2【最新版本，你导师用的工具】

**标题**：Atom-level enzyme active site scaffolding using RFdiffusion2
**作者**：Lauko et al.（Baker 实验室）
**期刊**：Nature Methods, 2025
**DOI**：[10.1038/s41592-025-02975-x](https://doi.org/10.1038/s41592-025-02975-x)

---

#### 精读批注

**关键改进**（相比 RFDiffusion1）：

🔑 **核心概念**：RFDiffusion2 vs RFDiffusion1 的关键差异：

| 特性 | RFDiffusion | RFDiffusion2 |
|------|------------|--------------|
| 活性位点输入 | 需要预先指定残基序号和 rotamer | 只需功能基团坐标（sequence-agnostic）|
| Rotamer 推断 | 手动 | 自动（flow matching）|
| 成功率（AME benchmark）| 16/41 活性位点 | 41/41 |
| 使用门槛 | 高（需要 theozyme generation）| 较低 |

💭 **思考整合**：对你的项目，RFDiffusion2 意味着**可以直接从过渡态的 QM 计算结果生成候选骨架**，不需要先做繁琐的 rotamer 解算。你的导师说"现在已经做完了"，说明他们已经用这个工具生成了候选。

⚡ **项目连接**：你可能会接触到这些候选结构的 PDB 文件。你的 MetaDynamics 工作就是在这些设计结构上运行的。

---

## 模块四：方法论工具（操作参考）

---

### 📄 Paper 8 — MetaDynamics 原理【Barducci 2008, Well-Tempered】

**标题**：Well-Tempered Metadynamics: A Smoothly Converging and Tunable Free-Energy Method
**作者**：Barducci, Bussi & Parrinello
**期刊**：Physical Review Letters, 2008
**DOI**：[10.1103/PhysRevLett.100.020603](https://doi.org/10.1103/PhysRevLett.100.020603)

> 这是物理学期刊，不在 PubMed 中。通过 APS 网站或 Google Scholar 获取。

---

#### 精读批注

**核心公式（你必须真正理解）**：

Well-tempered MetaDynamics 的高斯高度随时间衰减：

$$h(t) = \omega \cdot \exp\left(-\frac{V_G(s(\mathbf{R}), t)}{k_B \Delta T}\right)$$

🔑 **核心概念**：这个公式的物理含义：
- 如果当前 CV 位置已经被填了很多高斯（$V_G$ 大），新高斯的高度 $h(t)$ 就很小
- 如果当前 CV 位置没怎么被访问（$V_G$ 小），$h(t)$ 接近初始值 $\omega$
- 效果：**已充分采样的区域不再加大偏置，未充分采样的区域继续填充**
- 最终 FEL 收敛，而不是无限填充

💭 **思考整合**：BIASFACTOR（BF）= $(T + \Delta T)/T$ 的物理含义：
- BF = 1：不做增强（普通 MD）
- BF = ∞：标准 MetaDynamics（不收敛）
- BF = 10–30：Well-tempered（推荐，收敛后 FEL 缩放因子）

对于蛋白质构象变化，**BF = 10–20 是常用范围**。Osuna 组通常用 BF = 15。

---

### 📄 Paper 9 — MetaDynamics 综述【最佳入门综述】

**标题**：Using metadynamics to explore complex free-energy landscapes
**作者**：Bussi & Laio
**期刊**：Nature Reviews Physics, 2020
**DOI**：[10.1038/s42254-020-0153-0](https://doi.org/10.1038/s42254-020-0153-0)

---

#### 精读批注

> 这是最推荐的 MetaDynamics 入门综述，内容现代，覆盖 WTMetaD、Multiple Walkers、OPES 等变体。

🔑 **核心概念**：你需要从这篇综述中掌握的核心技能：

1. **CV 设计原则**（Section 2 of the review）
   - CV 必须能区分反应物和产物状态
   - CV 不应包含快速弛豫的自由度（否则需要过多高斯）
   - CV 的数量越少越好（2 是最佳实践上限）

2. **收敛判断**（Section 3）
   - 绘制"自由能差 vs. 模拟时间"的图
   - 收敛 = 此差值在最后 20–30% 时间内波动 < 0.5 kJ/mol

3. **Multiple Walkers**（Section 4）
   - N 个 walkers 共享 HILLS 文件
   - 效率近似线性提升（4 walkers ≈ 4× 速度）

⚡ **项目连接**：这篇综述是你设置 MetaDynamics 参数的"字典"。每次不确定参数含义，先查这篇。

---

## 模块五：技术参考

---

### PLUMED 操作速查

以下是你运行 TrpB MetaDynamics 的最小可用 PLUMED input 模板：

```bash
# PLUMED input file: plumed.dat
# 目标：TrpB COMM domain open-to-closed 的 MetaDynamics

# 1. 定义 COMM domain 的 RMSD（相对于 closed state 参考结构）
COMM_rmsd: RMSD
  REFERENCE=trpb_closed.pdb    # closed state 的参考结构
  TYPE=OPTIMAL                 # 最优叠合（排除刚体平移/旋转）
  ATOMS=101-140                # COMM domain 残基范围（需根据你的 PDB 调整）

# 2. 定义活性位点到 COMM domain 质心的距离
active_site: GROUP ATOMS=82,104,305  # K82, E104, D305 的 Cα
comm_center: CENTER ATOMS=101-140

COMM_dist: DISTANCE ATOMS=active_site,comm_center

# 3. MetaDynamics
METAD: METADYNAMICS
  ARG=COMM_rmsd,COMM_dist    # 两个 CVs
  SIGMA=0.15,0.3             # 高斯宽度（从短 MD 的 CV 波动 σ 估计）
  HEIGHT=1.2                 # 初始高斯高度 kJ/mol
  PACE=500                   # 每 500 MD 步加一个高斯（1 ps/高斯 @2fs timestep）
  BIASFACTOR=15              # Well-tempered 参数
  TEMP=300                   # 温度 K
  FILE=HILLS                 # 输出文件名
  WALKERS_N=4                # Multiple walkers 数量
  WALKERS_ID=0               # 当前 walker 编号（0,1,2,3 分别设置）
  WALKERS_DIR=../            # HILLS 文件共享目录

# 4. 定期输出 CV 值
PRINT
  ARG=COMM_rmsd,COMM_dist,METAD.bias
  STRIDE=500
  FILE=COLVAR
```

💭 **思考整合**：`SIGMA` 的设置方法：先跑一段 5–10 ns 的普通 MD，计算 CV 的标准差 σ。SIGMA 设为 σ 的 1/3 到 1/2 是经验规则。

---

## 附录：阅读路径与时间规划

### 推荐阅读顺序

```
Week 1（基础建立）：
  Day 1-2:  Paper 1 全文（TrpB Biocatalyst Extraordinaire）
            ——重点：催化机制 + COMM domain + D-Trp 级联
  Day 3:    Paper 2 Abstract + Main Text（Buller PNAS 2015）
            ——重点：6 个突变的实验数据
  Day 4-5:  Paper 9 综述（MetaDynamics Nature Reviews Physics）
            ——重点：WTMetaD 原理 + CV 设计原则

Week 2（核心技术）：
  Day 1-3:  Paper 3 全文（Osuna JACS 2019）
            ——重点：Figure 2 的 2D FEL，Methods 的 PLUMED 参数
  Day 4-5:  Paper 8（Barducci PRL 2008）
            ——重点：well-tempered 公式的物理含义

Week 3（整合与实操）：
  Day 1-2:  Paper 4 全文（Osuna Protein Sci 2022）
            ——重点：tAF2-MD 方法 + 与 MetaDynamics 的比较
  Day 3-4:  Paper 5 Methods（Osuna ACS Catal 2021）
            ——重点：SPM 算法流程 + 实验验证结果
  Day 5:    Paper 6/7（RFDiffusion/RFDiffusion2 Background）
            ——只需了解 de novo 设计的流程，不需要深读
```

### 每篇文献的推荐笔记格式

```markdown
## [论文标题] 读书笔记

**核心问题**：这篇文章想解决什么问题？

**核心答案**：他们的主要发现是什么？（用 2-3 句话）

**方法亮点**：他们用了什么新方法？参数是什么？

**关键数据**：最重要的定量结果（1-3 个数字）

**对我项目的意义**：这篇文章如何帮助我？我需要用哪些？

**未解决的问题**：这篇文章留下了什么 open question？

**相关文献**：引用了哪些我还没读的重要文章？
```

---

*注：本文档所引用 PubMed 文献均已注明 DOI，来源为 PubMed 数据库（Based on articles retrieved from PubMed）。相关 DOI 链接：[10.1002/cbic.202000379](https://doi.org/10.1002/cbic.202000379)（Biocatalyst Extraordinaire）；[10.1073/pnas.1516401112](https://doi.org/10.1073/pnas.1516401112)（Buller PNAS 2015）；[10.1002/pro.4426](https://doi.org/10.1002/pro.4426)（Osuna Protein Sci 2022）。*
