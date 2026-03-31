# TrpB × MetaDynamics 项目深度研究与计划
**整理时间：2026年3月18日** | 作者：基于今日项目会议整理

---

## 一、项目背景：你在做什么？

### 1.1 整体目标

你所加入的这个项目的核心科学问题是：**能不能设计（或改造）TrpB 酶，使其主要合成 D-型色氨酸（D-Trp）而非自然界普遍产生的 L-型色氨酸（L-Trp）？**

这是一个横跨计算结构生物学、酶工程和 AI 蛋白质设计的前沿课题。

### 1.2 TrpB 是什么？

**色氨酸合酶（Tryptophan Synthase, TrpS）** 是一个经典的异源二聚体酶复合物，由 TrpA 和 TrpB 两个亚基组成（αββα 构型）。

- **TrpA**（α 亚基）：催化吲哚-3-甘油磷酸（IGP）→ 吲哚 + G3P
- **TrpB**（β 亚基）：催化吲哚 + L-丝氨酸 → **L-色氨酸**（通过 PLP 辅因子介导的 C–C 键形成）

两个亚基之间存在**别构调控（Allosteric Regulation）**：TrpA 的存在会激活 TrpB，通过"隧道"将吲哚直接传递给 TrpB，避免吲哚在水溶液中的稀释。当 TrpB 单独存在时（standalone），活性大幅降低。

**你们 focus 的是 TrpB 这一段**，因为它是最终合成色氨酸（包括各种非天然氨基酸）的关键催化单元。

### 1.3 为什么 D-Trp 很难？

L-Trp 和 D-Trp 是对映异构体，化学性质基本相同，但在生物系统中的功能大相径庭。自然界中：

- **L-Trp** 是蛋白质合成的标准氨基酸，TrpB 的天然产物
- **D-Trp** 在自然界极少出现（少数特殊次级代谢途径），没有通用、高效的天然酶能直接合成它

改造 TrpB 合成 D-Trp 的核心难点在于**对活性位点的立体化学控制**——L-Ser 进入 TrpB 活性位点的取向、PLP（磷酸吡哆醛）的反应几何，都锁死了 L-构型产物的形成。要翻转这个选择性，需要**深度重塑活性位点附近的构象空间**。

---

## 二、Sílvia Osuna 的工作：MetaDynamics + TrpB

### 2.1 Osuna Lab 是谁？

[Sílvia Osuna](https://scholar.google.com/citations?user=rHtokY4AAAAJ) 是西班牙赫罗纳大学 / ICREA 的计算化学教授，全球最顶尖的**酶构象动力学与计算酶设计**专家之一。她的核心工具就是：**MetaDynamics + Shortest Path Map (SPM)**。

会议中提到的 "Oso"/"奥苏奈" 就是她。

### 2.2 Osuna Lab 的核心逻辑

**核心观点（Osuna 学派的中心思想）**：

> 酶的催化效率不只取决于活性位点的静态结构，更取决于它的**构象系综（Conformational Ensemble）**——即酶在热力学平衡下能访问哪些构象，各构象的稳定性如何。

换言之：**催化活性的关键，是活性构象在自由能景观（FEL）中的相对稳定性。**

MetaDynamics 的作用：通过向集体变量（CV）空间添加高斯势垒来"填平"自由能景观，从而加速构象转变的采样，**重建 FEL**。这在常规 MD 中是无法做到的（常规 MD 只能在纳秒尺度上看到局部弛豫，无法越过微秒-毫秒级的能垒）。

### 2.3 关键论文详解

#### 📄 论文一（必读，核心）
**"Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution"**
- Maria-Solano, Iglesias-Fernández & Osuna | *JACS* 2019 | [链接](https://pubs.acs.org/doi/abs/10.1021/jacs.9b03646)

**核心发现**：
- 研究对象：古细菌 *Pyrococcus furiosus* 的 TrpS（PfTrpS），以及它的祖先序列 LBCA-TrpB
- 关键结构：TrpB 的 **COMM domain**（Communication domain）是一个活动的 loop，在催化过程中要经历 **Open → Partially Closed → Closed** 的构象转变
- MetaDynamics 的用法：以 COMM domain 的构象变化作为集体变量（CV），计算 open-to-closed 过渡的自由能景观（FEL）
- 发现：LBCA-TrpB 之所以具有高 standalone 活性，是因为它的 FEL 中**闭合态（closed state）更稳定**——而大多数野生型 TrpB 在没有 TrpA 的情况下，闭合态的稳定性不足
- 结论：**恢复 COMM domain 闭合态的稳定性是提高 standalone TrpB 活性的关键**

**对你的项目的意义**：这套逻辑可以直接迁移到 D-Trp 合成的问题上——产生 D-Trp 所需的过渡态构象，可能对应 FEL 上的一个特殊构象（能量较高的稀有态）；MetaDynamics 可以让你采样到这个构象，并分析哪些突变能使其稳定化。

#### 📄 论文二（方法论）
**"In Silico Identification and Experimental Validation of Distal Activity-Enhancing Mutations in Tryptophan Synthase"**
- Maria-Solano, Kinateder, Iglesias-Fernández, Sterner & Osuna | *ACS Catalysis* 2021 | [链接](https://pubs.acs.org/doi/10.1021/acscatal.1c03950)

**核心内容**：
- 开发了 **Shortest Path Map (SPM)** 方法：基于 MD 轨迹中残基间的距离关联（Correlated Motions），构建残基通信图，找出远离活性位点但对构象动力学关键的"远端突变位点"
- 实验验证：SPM 预测的远端突变（distal mutations）在实验中真实提升了 standalone TrpB 的活性，效果与多轮定向进化相当
- MetaDynamics 在此用于基准验证：确认突变后 FEL 的变化符合预期

**对你的项目**：这是 "可以产生 impact 的工具" 的最佳例子——如果你能把 SPM 逻辑 + MetaDynamics FEL 信息整合进 reward function，你就在做真正有价值的贡献。

#### 📄 论文三（最新，AlphaFold2 整合）
**"Estimating conformational heterogeneity of tryptophan synthase with a template-based AlphaFold2 approach"**
- Casadevall, Duran, Estévez-Gay & Osuna | *Protein Science* 2022 | [链接](https://pmc.ncbi.nlm.nih.gov/articles/PMC9601780/)

**核心内容**：
- AlphaFold2 生成静态结构，但酶的功能需要理解构象分布
- 用 MetaDynamics 生成的 FEL 作为 ground truth，评估 tAF2（模板引导 AF2）+ 短 MD 方法预测构象异质性的能力
- 结论：tAF2-MD 可以快速估计构象景观，大幅降低计算成本

**对你的项目**：这说明 MetaDynamics 的 FEL 是 "ground truth"，而 ML 方法只是在尝试近似它——**你的 MetaDynamics 结果本身就很有价值，不只是作为训练数据**。

#### 📄 论文四（2024，最新工具）
**"Harnessing Conformational Dynamics in Enzyme Catalysis: The Shortest Path Map Tool for Computational Enzyme Design"**
- Duran, Casadevall & Osuna | *Faraday Discussions* 2024 | [链接](https://pubmed.ncbi.nlm.nih.gov/38910409/)

这篇是 SPM 方法的最新 review/extension，建议作为 SPM 方法学的主要参考。

#### 📄 论文五（2024，TrpA 方向）
**"Altering Active-Site Loop Dynamics Enhances Standalone Activity of the Tryptophan Synthase Alpha Subunit"**
- Duran, Kinateder, Hiefinger, Sterner & Osuna | *ACS Catalysis* 2024

延伸到 TrpA 亚基，展示了同样的逻辑（loop dynamics → standalone activity）在 α 亚基上的应用。

---

## 三、当前项目的具体工作流程

### 3.1 你们的 De Novo 设计流程

根据会议记录，你的老板（JP/project lead）描述了以下流程：

```
自然 TrpB 结构
    ↓
提取活性位点 → 构建"cell-zyme"模型（活性位点支架）
    ↓
RFDiffusion → 生成围绕该活性位点的新蛋白质骨架
    ↓
序列设计（ProteinMPNN 等）
    ↓
实验合成 + 筛选（White Lab）
```

这个流程已基本完成，接下来一个月左右会送去实验室测试。

### 3.2 MetaDynamics 的潜在切入点

会议中明确说了：**"我们还没想好 MetaDynamics 怎么接进来"**。这是你的机会。

以下是几个具体的可能整合方式：

#### 切入点 A：验证与优化设计的蛋白质构象 ⭐⭐⭐（推荐优先）
- 对 RFDiffusion 生成的新酶结构跑 MetaDynamics
- 检验新设计结构中，"D-Trp 过渡态所需构象" 在 FEL 上的稳定性
- 如果某个设计的 FEL 显示该构象被深度占据 → 好设计；否则需要改
- **价值**：为实验筛选提供一个额外的计算层过滤，减少实验成本

#### 切入点 B：为 reward function 提供物理学约束 ⭐⭐⭐
- RFDiffusion 的 de novo 设计依赖 reward/score function
- MetaDynamics FEL 可以提供以下 terms：
  - 闭合态 vs. 开放态的自由能差（ΔG_open→closed）
  - 与 D-Trp 立体化学相关的 CV 的自由能梯度
  - 过渡态的稳定化程度
- 将这些作为 reward function 的额外 term，引导 RFDiffusion/ProteinMPNN 偏向生成 "动力学上更利于 D-Trp 产生的构象"
- **价值**：这是 impact 最大的方向，直接影响设计质量

#### 切入点 C：理解野生型 TrpB 的立体化学机制 ⭐⭐
- 先用 MetaDynamics 精确重建野生型 TrpB 产生 L-Trp 时的 FEL
- 识别"D-Trp 形成所需的构象"（可能是 FEL 上的局部极小值或过渡态）
- 用 SPM 方法找出能稳定化该构象的远端突变位点
- **价值**：为整个项目建立机制基础，类似 Osuna lab 2019 年的工作

---

## 四、技术学习路线（具体操作）

### 4.1 第一阶段：理解 MetaDynamics 原理（第 1–2 周）

**必读论文**（按顺序）：

1. **Laio & Parrinello (2002)** — 原始 MetaDynamics 论文（了解原理）
2. **Barducci et al. (2008)** — Well-tempered MetaDynamics（这是 Osuna 组用的版本）
3. **Valsson et al. (2020)** — "Using MetaDynamics to explore complex free-energy landscapes" *Nature Reviews Physics* — [链接](https://www.nature.com/articles/s42254-020-0153-0)（最好的综述）
4. **Osuna JACS 2019** — 上面已详细介绍

**关键概念清单**（必须掌握）：
- 集体变量（Collective Variables, CVs）的选择逻辑
- 高斯势垒的堆积机制（Gaussian hills deposition）
- Well-tempered 变体的收敛保证
- 自由能景观（FEL）的重建方法（sum_hills）
- 多 walker MetaDynamics（multiple walkers）提高采样效率

### 4.2 第二阶段：MetaDynamics 软件实操（第 2–4 周）

**核心软件栈**（Osuna 组的标准）：
- **GROMACS**（MD 引擎）+ **PLUMED**（MetaDynamics 插件）

**学习资源**：
- PLUMED 官方 Master ISDD 2024 Tutorial：[链接](https://www.plumed.org/doc-v2.9/user-doc/html/master-_i_s_d_d-2.html)
- PLUMED Belfast Tutorial（MetaDynamics 专项）：[链接](https://www.plumed.org/doc-v2.9/user-doc/html/belfast-6.html)
- Towards Data Science MetaDynamics 入门系列：[链接](https://towardsdatascience.com/unveiling-metadynamics-a-beginners-guide-to-mastering-plumed-part-1-of-3-0442e1196abb/)

**操作检查单**：

```
[ ] 能用 GROMACS 从 PDB 文件建立 TrpB 系统并跑常规 MD
[ ] 能写 PLUMED 的 input 文件（定义 CV、METAD、PRINT）
[ ] 理解 SIGMA、HEIGHT、PACE 参数的物理含义和如何设置
[ ] 能跑一个简单体系（如 alanine dipeptide）的 MetaDynamics 并重建 FEL
[ ] 能用 plumed sum_hills 重建自由能景观
[ ] 了解如何定义 TrpB COMM domain 的构象变量（如 RMSD 或 dihedral CVs）
```

### 4.3 第三阶段：复现 Osuna 的 TrpB 计算（第 4–6 周）

**目标**：能复现 JACS 2019 中 COMM domain 的 open-to-closed 自由能景观

**具体步骤**：

1. 从 PDB 下载 LBCA-TrpB 结构（或相关结构）
2. 用 GROMACS 进行系统准备（加 H、溶剂化、平衡化）
3. 定义 COMM domain 相关的 CV（例如 COMM loop 质心到活性位点的距离，或特定二面角）
4. 运行 well-tempered MetaDynamics
5. 重建 FEL，与文献结果对比
6. **写入 weekly update**：描述 setup 参数、运行结果、FEL 形状

> **注意**：MD 的结果有随机性，不要求完全复现，但 FEL 的拓扑结构（哪些极小值、相对深度）应该大致一致。

### 4.4 第四阶段：整合进 reward function（第 6–10 周）

这是最难也最有创意的部分，下一节详细讨论。

---

## 五、如何展现你的价值（核心！）

你的老板说得很清楚：**"需要非常 impactful 的工作，而不是 incremental 的。"** 一个模型接着一个模型地调参不是他想要的——他需要新角度和新思路。

### 5.1 你的独特优势

你在 Miao Lab 做过的 **LiGaMD3** 和你在 Poplov Lab 做的 **HPC 自动化 + ML** 恰好可以组合成一个别人没有做过的方向：

> **"将 enhanced sampling（MetaDynamics/LiGaMD）的 FEL 数据转化为可驱动 de novo 设计的物理约束 reward signal"**

这是一个桥梁工作：把 Osuna 组的物理学 → 接进 Baker 组式的 de novo 设计流程。

### 5.2 具体的"展现价值"切入点

#### 角度一：FEL-informed Reward Function Design（最 impactful）

**你能做的**：
- 跑多组 TrpB 变体（wildtype + 已知 D-Trp 倾向突变）的 MetaDynamics
- 提取 FEL 中"D-Trp 过渡态相关构象"的自由能值作为特征
- 用你的 XGBoost / ML 经验，建立一个简单的模型：
  - 输入：MetaDynamics FEL 特征（ΔG、势垒高度、CV 分布）
  - 输出：预测的 D-Trp 选择性（ee 值 或 kcat/Km 比值）
- 将这个模型的输出作为 RFDiffusion 设计的 reward term

**为什么 impactful**：目前没有人在 TrpB de novo 设计中显式地把 MetaDynamics FEL 接进 reward function。这是一个真正的空白。

#### 角度二：基于 Conformational Clustering 的设计筛选

**你能做的**：
- 对 RFDiffusion 生成的一批设计结构跑短 MetaDynamics（或 GaMD），快速估计构象景观
- 用 PCA / K-Means 对构象进行聚类（你在 Miao Lab 做过这个）
- 找出哪些设计"天然地倾向 D-Trp 所需构象"
- 这些优先推荐给湿实验验证

**为什么 impactful**：等于给实验筛选加了一个"计算预筛选"层，提升命中率。

#### 角度三：利用你的 LiGaMD 背景做 benchmark 比较

**你能做的**：
- 同时用 MetaDynamics（Osuna 组方法）和 LiGaMD3（你熟悉的方法）模拟同一个 TrpB 构象转变
- 量化两种方法的 FEL 是否一致、效率差异、计算成本差异
- 写成一个系统性比较

**为什么有价值**：
- 这直接 leverage 你的独特背景（别人没有 LiGaMD 经验）
- 如果你能证明 LiGaMD3 在某些场景下更高效或更准确，就是一个新的 methodological contribution
- 同时让你老板看到你不是在简单地"抄作业"，而是在带来新工具

---

## 六、Weekly Update 写作框架

你老板说每周六晚要发 update，以下是建议格式：

```markdown
## Week X Update — [你的名字]

**本周完成**
- 读完了 XXX 论文，核心发现：...（用自己的话）
- 在本地/HPC 上 setup 了 GROMACS + PLUMED，成功运行了 alanine dipeptide 的 MetaDynamics

**技术细节**
MetaDynamics 参数设置：
- CV: backbone dihedral φ, ψ of Ala
- HEIGHT = 0.3 kJ/mol, SIGMA = 0.35, PACE = 500
- 运行时长: 50 ns（4 walkers × 12.5 ns）
- 收敛判断: 最后 10 ns 的 FEL 与前 10 ns 差异 < 0.5 kJ/mol

**FEL 结果**
（图）... 两个极小值对应 α-helix 和 β-sheet 构象，与文献一致。

**问题 / 下周计划**
- 问题 A: COMM domain 的 CV 怎么定义更合理？考虑用 RMSD vs. dihedral，有什么建议？
- 下周: 开始对 LBCA-TrpB PDB 结构进行 system prep
```

---

## 七、关键文献清单（优先级排序）

### 🔴 必须首先读（第 1–2 周）

| 论文 | 期刊/年 | 优先级 | 要点 |
|------|---------|--------|------|
| Maria-Solano et al. 2019 | JACS | ⭐⭐⭐⭐⭐ | MetaDynamics + TrpB COMM domain FEL，项目核心 |
| Barducci et al. 2008 | PRL | ⭐⭐⭐⭐⭐ | Well-tempered MetaDynamics 原理 |
| Valsson & Parrinello 2020 | Nature Reviews Physics | ⭐⭐⭐⭐ | MetaDynamics 最佳综述 |

### 🟡 第 2–4 周读

| 论文 | 期刊/年 | 优先级 | 要点 |
|------|---------|--------|------|
| Maria-Solano et al. 2021 | ACS Catal | ⭐⭐⭐⭐ | SPM 方法 + 远端突变验证 |
| Casadevall et al. 2022 | Protein Sci | ⭐⭐⭐ | tAF2 + MetaDynamics 比较 |
| Duran et al. 2024 | Faraday Discuss | ⭐⭐⭐ | SPM 最新版本 |

### 🟢 背景了解（有时间读）

| 论文 | 期刊/年 | 要点 |
|------|---------|------|
| Buller et al. 2015 | PNAS | TrpB standalone 定向进化经典 |
| Herger et al. 2016 | JACS | TrpB β-branched 氨基酸合成 |
| RFDiffusion Paper (Watson et al.) 2023 | Nature | de novo 设计背景知识 |
| RFDiffusion2 (Lauko et al.) 2025 | Nature Methods | 最新版本 |
| Casadevall & Osuna 2023 | JACS Au | AlphaFold2 + 酶设计综述 |

---

## 八、时间线规划（10 周）

```
Week 1–2:  文献精读阶段
           □ Osuna JACS 2019（必须逐段精读，做笔记）
           □ MetaDynamics 原理论文（Barducci 2008 + Valsson 2020）
           □ 安装 GROMACS + PLUMED，跑 alanine dipeptide 测试

Week 3–4:  MetaDynamics 基础操作
           □ 完成 PLUMED 官方 tutorial（alanine dipeptide + 蛋白质案例）
           □ 准备 TrpB 的 GROMACS 系统（PDB → 加H → solvation → 平衡）
           □ 讨论 COMM domain CV 的定义策略

Week 5–6:  复现 Osuna 2019 实验
           □ 对 LBCA-TrpB 跑 MetaDynamics（重建 COMM domain FEL）
           □ 比较 open/closed 态稳定性，与文献对比
           □ 尝试 multiple walkers 方法提升效率

Week 7–8:  整合进项目
           □ 对 RFDiffusion 设计的候选结构跑 MetaDynamics
           □ 提取 FEL 特征，讨论与 D-Trp 选择性的关联
           □ 与老板/组内讨论 reward function 设计方向

Week 9–10: 产出与总结
           □ 整理所有 MetaDynamics 结果
           □ 提出 reward function 的具体公式/设计方案
           □ 如有时间：LiGaMD vs MetaDynamics benchmark 比较
```

---

## 九、潜在风险与应对

| 风险 | 说明 | 应对方案 |
|------|------|----------|
| MetaDynamics 不收敛 | CV 选择不当，FEL 无法收敛 | 参考 Osuna 2019 的 CV 选择，多 walker 方案 |
| TrpB 系统太大，计算成本高 | 全酶 MetaDynamics 可能需要大量 GPU 时间 | 先用截断活性位点（QM/MM 方法），或争取 HPC 资源 |
| D-Trp 相关构象在 FEL 上不明显 | 找不到对应的局部极小值 | 参考 2025 年 TrpB-IRED 级联的机制，考虑不同底物类似物 |
| "NeuroMD" 已经做了类似工作 | 老板提到 Dec 2024 的论文 | 仔细读那篇文章，找差异点——你的角度是 FEL → reward，而非 neural potential |

---

## 十、一句话总结：你的核心价值主张

> "我有 enhanced sampling 的实操经验（LiGaMD3 + HPC 大规模计算），也有 ML 建模的经验（XGBoost/LSTM/深度学习）。我可以做别人做不到的事：把 MetaDynamics FEL 的物理学信号转化成可量化的 reward signal，驱动 de novo 酶设计向 D-Trp 合成方向收敛。这不是工具的简单应用，而是两个领域之间的真正桥梁。"

这就是你在这个组里不可替代的位置。

---

*参考来源综合自：Osuna Lab 官方网站、PLUMED 官方文档、PubMed、Nature Communications、JACS、ACS Catalysis 等*
