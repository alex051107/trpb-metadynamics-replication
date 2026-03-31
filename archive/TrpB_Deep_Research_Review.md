# TrpB × MetaDynamics × De Novo Enzyme Design
## 深度研究综述 | Deep Research Review

**整理日期：2026年3月18日** | 适用读者：项目新成员快速上手

---

> **读前指引**：这份文档的目标是让你在开始真正操作之前，对整个项目的科学背景形成完整认知。建议按章节顺序阅读，每一节都对应了你需要 hands-on 之前必须掌握的一块知识。

---

## 第一章：色氨酸合酶 β 亚基（TrpB）——你需要知道的所有事

### 1.1 TrpB 是什么？从生物化学基础说起

**色氨酸合酶（Tryptophan Synthase, TrpS）** 是存在于细菌、真菌和植物中的一个模块化双功能酶复合物，负责合成必需氨基酸 **L-色氨酸（L-Trp）**。它由两种亚基组成：

```
TrpA (α-亚基):  吲哚-3-甘油磷酸（IGP）  →  吲哚 + 3-磷酸甘油醛（G3P）
                      [裂解反应，产生吲哚作为中间体]

TrpB (β-亚基):  吲哚 + L-丝氨酸（L-Ser）  →  L-色氨酸（L-Trp）
                      [β-置换反应，PLP 依赖，C–C 键形成]
```

这两个亚基在天然状态下以 **αββα 四聚体** 形式排布。关键在于：TrpA 产生的吲哚不会扩散到溶液中，而是通过一条约 25 Å 的 **疏水隧道（hydrophobic tunnel）** 直接传递给 TrpB。这种"底物通道传递"（substrate channeling）是酶复合物高效工作的核心机制。

**你的项目聚焦在 TrpB 这一段**，因为它是最终催化 C–C 键形成、决定氨基酸骨架结构的关键步骤。

---

### 1.2 TrpB 的催化机制：PLP 化学的核心

TrpB 是典型的 **PLP（磷酸吡哆醛，pyridoxal 5'-phosphate）依赖酶**。PLP 是这类酶的通用辅酶，其功能是通过形成 Schiff 碱（亚胺键）稳定氨基酸底物并激活其 Cα 位置。

TrpB 的催化循环分为两个阶段，涉及多个光谱上可区分的中间体：

#### 阶段一：L-Ser 活化（形成亲电体）

| 中间体 | 缩写 | 吸收峰 | 描述 |
|--------|------|--------|------|
| 内部醛亚胺（resting state） | E(Ain) | 412 nm | PLP 通过 Schiff 碱与 Lys82 共价连接 |
| 外部醛亚胺 1 | E(Aex1) | 428 nm | L-Ser 的氨基取代 Lys82，与 PLP 形成新 Schiff 碱 |
| 醌类中间体 1 | E(Q1) | 470 nm | Cα 去质子化，形成醌类负离子 |
| **氨基丙烯酸酯中间体** | **E(A-A)** | **350 nm** | **消除 OH⁻，形成亲电的 α,β-不饱和亚胺** |

这个 **E(A-A) 中间体**是整个催化循环的关键节点：它是一个高度亲电的物种，等待吲哚（亲核试剂）来进攻。

#### 阶段二：吲哚亲核进攻，C–C 键形成

```
E(A-A)  +  吲哚  →  E(Q2/Q3)  →  E(Aex2)  →  L-Trp + E(Ain)
              ↑
         吲哚 C3 进攻亚胺双键
         形成新的 C–C 键
         这一步决定立体化学！
```

**催化关键残基**：
- **E104（谷氨酸）**：控制反应区域选择性。它引导吲哚的亲核进攻发生在 C3（形成 C-C 键），而不是 N1（否则会形成 C-N 键）。
- **K82（赖氨酸）**：PLP 的共价锚定位点，参与所有 transimination 步骤。
- **R141、D305（精氨酸和天冬氨酸）**：COMM domain 闭合时形成盐桥，稳定过渡态。

---

### 1.3 COMM Domain：动力学的核心

这是你理解 MetaDynamics 如何与 TrpB 结合的最关键知识点。

**COMM domain（Communication Domain，通信结构域）** 是 TrpB 中一段大约 40 个残基的活动环区（residues ~100–150，依物种不同有差异），在催化循环中经历明确的构象转变。

#### 构象状态定义

```
开放态（Open）  ←→  半闭合态（Partially Closed）  ←→  闭合态（Closed）
                                                              ↑
                                                    催化活性构象
```

**各状态对应的催化事件**：
- **开放态**：E(Ain) 阶段，活性位点开放，允许 L-Ser 进入
- **半闭合态**：E(Aex1) 和 E(Q1) 阶段，L-Ser 结合触发 COMM domain 向内移动；Asp300 与 L-Ser 羟基形成氢键
- **闭合态**：E(A-A) 形成后，COMM 完全闭合；R141 与 D305 之间形成关键盐桥；活性位点密封，吲哚通道打开以接受来自 TrpA 的吲哚

**为什么这个闭合转变如此重要**：

如果 COMM domain 无法高效达到闭合态，酶的催化效率极低。这正是独立 TrpB（没有 TrpA）催化效率低下的根本原因：**TrpA 的别构激活作用，实质上是帮助 COMM domain 稳定闭合态**。

Osuna 实验室的核心发现：**闭合态在自由能景观（FEL）上的相对稳定性，是预测 TrpB 催化效率的最佳指标**。

---

### 1.4 别构调控与独立（Standalone）TrpB

天然 TrpB **单独存在时活性极低**（kcat 降低 100 倍以上），必须与 TrpA 结合才能高效工作。原因：

1. TrpA 的结合通过接触 COMM domain，物理上推动它向闭合态移动
2. TrpB 内部存在一个 **一价阳离子结合位点（Monovalent Cation Binding Site, MCS）**，Na⁺ 或 K⁺ 的结合也能稳定闭合态
3. 两种效应协同，将 COMM domain FEL 上的闭合态稳定约 2–4 kcal/mol

**Arnold lab（Caltech）的突破**（2015, PNAS）：
通过对嗜热古细菌 *Pyrococcus furiosus* 的 TrpB（PfTrpB）进行定向进化，仅需 **3 轮进化、6 个突变**，就使独立 TrpB 的 kcat 提升了 83 倍。这些突变中大多数位于 COMM domain 附近或远端调控位点，本质上是通过突变"模拟"了 TrpA 的别构激活效果。

**Osuna lab（2021, ACS Catalysis）的计算突破**：
通过 MetaDynamics FEL 分析 + SPM 方法，从一次计算出发，预测了可将独立 TrpB 的 kcat 提升 **7 倍**的突变（SPM6-TrpB 变体），仅需测试 1 个变体，效果媲美定向进化中筛选 3000+ 变体的结果。

---

### 1.5 TrpB 的生物催化价值：底物多样性

一旦从 TrpA 依赖中解放，工程化 TrpB 展现出惊人的底物宽容性：

**可接受的吲哚类底物**：
- 卤代吲哚（F/Cl/Br/I 位于 4、5、6、7 位）
- 氰基、硝基、甲氧基取代吲哚
- 氮杂吲哚（aza-indoles）、苯并呋喃、苯并噻吩

**可替代 L-Ser 的亲核体**：
- β-甲基丝氨酸（→ β-甲基色氨酸）
- 各种 β-支链丝氨酸类似物

**非天然亲核试剂（非吲哚体系）**：
- 硝基烷烃、氧吲哚（oxindole）、砜类化合物 → 形成**季碳手性中心（quaternary stereocenters）**

目前 TrpB 的工程变体已可合成超过 **70 种非天然氨基酸（non-canonical amino acids, ncAAs）**。

---

## 第二章：为什么要合成 D-型色氨酸？——关于立体化学目标的深度解析

### 2.1 L-Trp vs D-Trp：镜像世界的差异

L-色氨酸和 D-色氨酸互为对映体（enantiomers），化学式完全相同（C₁₁H₁₂N₂O₂），但在三维空间中的排布完全相反：

```
L-Trp：                    D-Trp：
  NH₂                        NH₂
   |                           |
  Cα—H           ←→          H—Cα
   |                           |
  COOH                       COOH
  (S 构型)                   (R 构型)
```

你的 PI 在会议中说"合成 D 而不是 L"——这里需要厘清一个关键概念：

> **L/D 命名（Fischer 约定）与 R/S 命名（IUPAC CIP 规则）在色氨酸上是一致的：L-Trp = S 构型，D-Trp = R 构型。**

天然 TrpB 产生的是 **L-Trp（S 构型）**，你们的目标是工程化得到主要产生 **D-Trp（R 构型）** 的酶。

---

### 2.2 D-Trp 的重要性：为什么值得去做？

#### 2.2.1 天然存在与稀缺性

D-氨基酸在自然界中远比 L-氨基酸稀少。D-Trp 主要存在于：
- **细菌细胞壁肽聚糖**的修饰形式
- **某些多肽类天然产物**（如 telomycin 类抗生素的片段）
- **肠道微生物代谢产物**（在宿主-微生物互作中被检测到）
- **牛奶中微量存在**

由于缺乏高效合成D-氨基酸的天然酶系统，D-Trp 的化学合成成本远高于 L-Trp，严重限制了其研究和应用。

#### 2.2.2 药物和生物活性价值（近年研究）

近年来的研究（2024 Frontiers in Microbiology，系统综述 865 篇文献）揭示了 D-Trp 的多种生物活性：

**免疫调节**：
- 在哮喘小鼠模型中，D-Trp 增加肺部和肠道的调节性 T 细胞（Treg），降低 Th2 应答，减轻过敏性气道炎症
- 通过与树突状细胞相互作用影响 IDO（吲哚胺-2,3-双加氧酶）通路

**抗菌与抗生物膜**：
- 40 mM D-Trp 对多种食源性致病菌（沙门氏菌、金黄色葡萄球菌等）表现出显著抑菌效果
- 抑制假单胞菌（Pseudomonas）和葡萄球菌（Staphylococcus）的生物膜形成

**医疗应用**：
- 作为抗肿瘤药物的合成前体
- 抗结核治疗
- 抗动脉粥样硬化和骨质疏松研究

**作为手性构建块**：
- 合成多种含 D-Trp 骨架的生物活性肽（如 D-Trp 类似物的神经肽、生长激素类似物）
- 非营养性甜味剂（D-色氨酸的甜度约为蔗糖的 35 倍）

#### 2.2.3 为什么要通过工程化 TrpB 来做？

现有的 D-Trp 合成途径：
1. **化学不对称合成**：步骤繁多，ee 值不稳定，成本高
2. **DL-Trp 化学拆分**：浪费一半原料，效率低
3. **酶级联（TrpB + 化学/生物转化）**：可以，但步骤多，原子经济性差

**直接工程化 TrpB 产生 D-Trp** 是最优雅的路径：一步反应，高 ee 值，生物可持续。这也是为什么你导师认为这是值得做的工作。

---

### 2.3 立体化学反转的核心挑战

TrpB 产生 L-Trp 的立体化学来源于 **E(A-A) 阶段吲哚进攻时的空间约束**：

1. PLP 与底物形成的 Schiff 碱平面（平面型中间体）决定了吲哚从哪一侧接近
2. 活性位点的空间排布（K82 的位置、周围残基的手性环境）固定了过渡态的立体化学
3. 吲哚只能从 **si 面**（对应产生 L 构型）进攻亲电亚胺

要产生 D-Trp，需要吲哚从 **re 面**进攻，这要求**整体重塑活性位点几何结构**——这不是几个点突变能做到的，需要重新设计活性位点空间。

这正是为什么你的导师采用 **de novo 设计**而非简单定向进化的原因。

---

## 第三章：Sílvia Osuna 的工作——MetaDynamics 如何驾驭 TrpB

### 3.1 Osuna 实验室的核心哲学

Osuna 实验室（西班牙赫罗纳大学 / ICREA）的中心主张：

> **酶的催化能力不仅由活性位点的静态几何决定，更由其动态构象系综（conformational ensemble）决定。促进正确构象分布，就能提升催化效率。**

这与传统的"lock-and-key"或甚至"induced-fit"模型不同，更接近"**conformational selection**"范式：酶始终在构象空间中波动，活性构象的出现概率直接影响表观活性。

---

### 3.2 方法论：MetaDynamics 在 Osuna 组的使用方式

Osuna 组使用的具体技术栈：

```
MD 引擎:   GROMACS / AMBER
MetaDynamics 插件:  PLUMED 2.x（开源，与 GROMACS 无缝集成）
变种:    Well-tempered MetaDynamics（WTMetaD）+ Multiple Walkers
后处理:   plumed sum_hills（重建 FEL）
可视化:   WESTPA / VMD / Python matplotlib
```

#### 集体变量（Collective Variables, CVs）的选择

Osuna 在 TrpB 研究中主要用以下 CV：

**CV1：COMM domain 的开/闭程度**
- 通常定义为 COMM domain 质心与活性位点特定残基之间的距离
- 或者 COMM domain 相关残基相对于参考结构的 RMSD
- 反映 open-to-closed 的宏观构象变化

**CV2（辅助 CV）：底物/配体姿态**
- 如 E(A-A) 中间体相对于催化位点的朝向（某个二面角）
- 在研究立体化学时尤为重要

**Well-tempered MetaDynamics（WTMetaD）的参数范例**（参考 Osuna 2019 JACS 的 SI）：

```
# PLUMED input 示例（简化）
COMM_dist: DISTANCE ATOMS=@COMM_center,@active_site_center
COMM_rmsd: RMSD REFERENCE=closed_structure.pdb TYPE=OPTIMAL

METAD: METADYNAMICS ARG=COMM_dist,COMM_rmsd
       SIGMA=0.2,0.3        # 高斯宽度
       HEIGHT=0.5           # 初始高斯高度 (kJ/mol)
       PACE=500             # 每 500 步加一个高斯
       BIASFACTOR=15        # Well-tempered 参数（越大越接近标准 MetaD）
       TEMP=300             # 温度(K)
       FILE=HILLS

PRINT ARG=COMM_dist,COMM_rmsd,METAD.bias STRIDE=500 FILE=COLVAR
```

---

### 3.3 Osuna 关键成果一览

#### 📄 Osuna et al., JACS 2019（核心论文）

**完整引用**：Maria-Solano, M.A.; Iglesias-Fernández, J.; Osuna, S. "Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution." *J. Am. Chem. Soc.* 2019, 141(33), 13049–13056.

**关键图片理解**：
- 该论文中的核心图是 **COMM domain 的二维自由能景观（2D FEL）**，横轴是一个 CV，纵轴是另一个 CV，颜色深度代表自由能（蓝色=低能/稳定，红色=高能/不稳定）
- 野生型 TrpB（独立）：FEL 上闭合态浅，开放态深 → 偏向开放，催化效率低
- LBCA-TrpB（6 突变进化体）：FEL 上闭合态变深，开放/闭合能差缩小 → 高效催化

**核心结论**：突变通过重塑 FEL 来改变酶的行为，而非直接改变活性位点几何。

#### 📄 Osuna et al., ACS Catalysis 2021（SPM 方法）

**工作流程**：

```
步骤 1: 对 TrpB 跑 50-200 ns 普通 MD（获取构象轨迹）
    ↓
步骤 2: 计算残基间的动态相关性矩阵（Cross-correlation matrix）
        - 基于原子间距离波动
    ↓
步骤 3: 将相关性矩阵转化为图（Graph）
        - 节点 = 残基，边 = 相关性强度
    ↓
步骤 4: 用 Dijkstra 算法找最短路径（Shortest Path）
        - 连接活性位点残基 → COMM domain → 潜在远端调控位点
    ↓
步骤 5: SPM 路径上的残基 = 候选突变位点
        - 这些位点突变后会影响信号从底物结合到 COMM 闭合的传导
    ↓
步骤 6: MetaDynamics 验证 → 确认突变后 FEL 的闭合态稳定化
    ↓
步骤 7: 实验测试（少量突变体，7 倍提升 kcat）
```

**关键数据**：SPM6-TrpB 变体（6 个远端突变）kcat 提升 7 倍；定向进化筛 3000 变体才能达到 9 倍。

#### 📄 Casadevall et al., Protein Science 2022（AlphaFold2 整合）

- 用 MetaDynamics FEL 作为 "ground truth"
- 评估 template-based AlphaFold2（tAF2）+ 短 10ns MD 能否快速近似构象景观
- 结论：tAF2-MD 可以初步筛选，但精确 FEL 仍需 MetaDynamics

---

### 3.4 SPM Webserver（可直接使用！）

Osuna 组已将 SPM 方法部署为公开 Web 服务器：
- **网址**：https://spmosuna.com/
- **输入**：蛋白质 PDB + MD 轨迹
- **输出**：关键残基列表、通信网络可视化
- 这是你未来可以直接用来帮助项目的工具之一

---

## 第四章：MetaDynamics——原理到实操

### 4.1 为什么普通 MD 不够用？

常规分子动力学（Molecular Dynamics, MD）的核心限制：

**时间尺度问题**：
- MD 模拟时步约 2 fs（飞秒，10⁻¹⁵ s）
- 实际能跑到的极限：几十到几百 ns（纳秒）
- 但生物学上重要的构象转变（如 COMM domain 开→闭）发生在 **微秒到毫秒（μs–ms）时间尺度**
- 结论：**普通 MD 根本采样不到 COMM domain 的完整开→闭→开循环**

**能垒问题**：
- COMM domain 的 open→closed 转变有显著能垒（通常 5–15 kcal/mol）
- 在 300K 条件下，系统翻越这个能垒的概率极低
- 即使跑几十微秒，也可能只看到单一构象

---

### 4.2 MetaDynamics 的核心思想

MetaDynamics（由 Parrinello 和 Laio 于 2002 年提出）的思路极其优雅：

**核心操作：在集体变量（CV）空间中持续添加高斯型排斥势（Gaussian hills）**

```
在 CV 空间中的当前位置：添加一个高斯势垒
                         ↓
下次访问同一位置：能垒更高，系统被"推走"
                         ↓
重复此操作：慢慢"填平"自由能景观
                         ↓
最终：系统均匀探索整个 CV 空间
     堆积的高斯总和 ≈ 负的真实自由能（取反后即 FEL）
```

**数学表达**：

$$V_G(s, t) = \sum_{t' < t} h \cdot \exp\left(-\frac{(s - s(t'))^2}{2\sigma^2}\right)$$

其中：
- `s`：集体变量（CV）的当前值
- `h`：高斯高度（HEIGHT 参数）
- `σ`：高斯宽度（SIGMA 参数）
- `t'`：之前添加高斯的时间步

**Well-tempered MetaDynamics（WTMetaD）的改进**（Barducci et al., 2008）：

普通 MetaDynamics 的问题：高斯不断堆积，永远不会收敛。

WTMetaD 的解决方案：让高斯高度随时间**指数衰减**：

$$h(t) = h_0 \cdot \exp\left(-\frac{V_G(s, t)}{k_B \Delta T}\right)$$

其中 `ΔT` 是一个"bias temperature"参数，实际操作中用 `BIASFACTOR = (T + ΔT) / T` 来设置。BIASFACTOR 越大，越接近标准 MetaD；BIASFACTOR = ∞ 等价于标准 MetaD。

**WTMetaD 的优势**：FEL 估计会平滑收敛，不会过填充。

---

### 4.3 集体变量（CV）的选择：艺术与科学

CV 的选择是 MetaDynamics 中最需要经验判断的部分，它必须：

1. **捕获关键的构象自由度**：必须包含你关心的过渡（COMM domain 开/闭）
2. **不过度简化系统**：如果重要的构象变化没被 CV 捕获，FEL 不可信
3. **维数不能太高**：2–3 个 CV 是实际可行的上限（多 CV 采样效率指数下降）

**对 TrpB COMM domain 的 CV 设计选项**：

| CV 类型 | 定义 | 优势 | 劣势 |
|---------|------|------|------|
| 质心距离 (DISTANCE) | COMM 质心 到 活性位点残基距离 | 直观，易定义 | 对具体构象不够敏感 |
| RMSD | COMM domain 对 closed/open 参考结构的 RMSD | 直接衡量闭合程度 | 需要高质量参考结构 |
| 二面角 (TORSION) | 关键 loop 残基的骨架二面角 | 原子级精度 | 需要先识别哪些二面角重要 |
| 接触数 (COORDINATION) | COMM domain 与活性位点的残基接触数 | 自然描述开/闭 | 计算代价稍高 |
| AlphaFold-based CV | 基于 AF2 输出的线性组合 | 数据驱动，自动化 | 需要多个 AF2 结构 |

**Osuna 实验室的实践**：通常使用 RMSD（相对于 closed state 的参考结构）+ 距离（COMM 质心到特定活性位点残基）的组合，以 2D FEL 的形式展示结果。

---

### 4.4 Multiple Walkers MetaDynamics：提升采样效率

对于大型蛋白质体系（TrpB 全酶约 300 个残基），单 walker MetaDynamics 可能需要极长时间才能收敛。

**Multiple Walkers**（Raiteri et al.）的思路：
- 同时运行 N 个独立的模拟（walkers）
- 所有 walkers **共享同一个高斯偏置势**（共享 HILLS 文件）
- 每个 walker 独立探索 CV 空间，但偏置来自全部 walkers 的积累

效果：近似线性加速（4 个 walkers ≈ 4× 速度提升），计算成本可控。

```
# PLUMED multiple walkers 示例
METAD: METADYNAMICS ARG=cv1,cv2
       ...
       WALKERS_N=4          # 总 walker 数
       WALKERS_ID=0         # 当前 walker 的编号（0,1,2,3）
       WALKERS_DIR=../      # 共享 HILLS 文件目录
```

---

### 4.5 FEL 重建和分析

运行完 MetaDynamics 后，用 `plumed sum_hills` 重建自由能景观：

```bash
plumed sum_hills --hills HILLS --outfile fes.dat --stride 500 --mintozero
```

- `--stride`：每隔多少个高斯检查一次收敛
- `--mintozero`：将最低点归零（只有相对值有意义）

**收敛判断**：

```python
# 将 FEL 分成前半段和后半段，比较差异
fes_first_half = load_fes("fes_000.dat")
fes_second_half = load_fes("fes_final.dat")
if max(abs(fes_first_half - fes_second_half)) < 0.5:  # kJ/mol
    print("收敛！")
```

**分析重点**：
- 开放态（open）和闭合态（closed）的自由能差 ΔG = G(closed) - G(open)
- 能垒高度（关系到转变速率）
- 是否存在中间态（partially closed）

---

## 第五章：De Novo 酶设计工作流程——从零开始造一个新酶

### 5.1 整体思路：为什么不直接改造 TrpB？

你的导师说的流程是"de novo 设计"，而非"定向进化 TrpB"。原因：

**定向进化的局限**：
- 从野生型 TrpB 出发，只能在自然存在的序列空间中做局部优化
- 要实现立体化学完全反转（L→D），所需突变可能过多，超出进化搜索的可达范围
- 序列空间太大，盲目搜索成本极高

**De Novo 设计的优势**：
- 从头开始，活性位点几何由你来指定（不受天然 TrpB 结构约束）
- 可以专门针对 D-Trp 合成所需的 **re-face 进攻**几何来设计活性位点
- 现有 AI 工具（RFDiffusion）已经能做到这一步

---

### 5.2 完整的 De Novo 酶设计流程（你导师的工作流）

#### Step 1：定义催化性活性位点（Theozyme / Catalytic Motif）

```
输入：
  - TrpB 催化机制（PLP 化学，关键残基 K82, E104 等）
  - 目标立体化学（D-Trp，re-face 进攻几何）
  - 过渡态计算（QM 或 QM/MM 给出原子坐标）

输出：
  - "Theozyme"：一组催化残基（3–8 个）及其精确空间坐标
  - 即：K82（PLP 锚定）+ E104（区域选择性控制）+
         其他氢键供体/受体 + 新设计的 re-face 引导残基
  - 关键：这些残基的相对几何固定，但不规定它们在序列上的位置
```

**"Cellzyme" 概念（你导师提到的词）**：本质上是"从已知酶中提取活性位点"的催化性模块（catalytic module），类似 theozyme，强调对现有酶功能位点的直接迁移和重新利用。

---

#### Step 2：RFDiffusion / RFDiffusion2——活性位点支架化（Scaffolding）

```
输入：
  - Theozyme（活性位点的原子级坐标）
  - 不需要预先知道催化残基在序列中的位置！
  - 可以加约束（如蛋白质总长度、二级结构偏好）

过程：
  - RFDiffusion2 是一个扩散模型（Diffusion Model）
  - 从随机噪声开始，逐步去噪生成蛋白质骨架
  - 去噪过程被"锁定"在满足 theozyme 几何约束的空间中
  - 同时生成 backbone coordinates + 推断催化残基的 rotamer

输出：
  - 多个候选蛋白质骨架（通常生成 1000–10000 个）
  - 每个骨架都正确地包含了活性位点几何
```

**RFDiffusion2 相较 RFDiffusion1 的关键改进**（Nature Methods 2025）：
- RFD1 需要预先指定催化残基在序列中的位置和 rotamer
- RFD2 直接从功能基团坐标出发，自动推断序列位置和 rotamer
- 基准测试：41 个活性位点全部成功支架化（RFD1 只能做 16/41）

---

#### Step 3：ProteinMPNN——序列设计

```
输入：
  - RFDiffusion 生成的蛋白质骨架（backbone only）
  - 活性位点残基固定（不设计这些位置）

过程：
  - ProteinMPNN 是一个图神经网络（GNN）
  - 基于骨架的几何特征（残基间距离、方向）预测最佳氨基酸序列
  - 对每个骨架生成多个序列候选（通常 100–1000 条序列/骨架）

输出：
  - 完整的蛋白质序列（每个位置的氨基酸类型）
  - 每个序列会给出一个 log-likelihood 打分
```

---

#### Step 4：计算过滤（Computational Filtering）

这是最关键的筛选步骤，目的是从海量候选中筛出最可能成功的设计：

```
过滤层 1：AlphaFold2 自洽检验
  - 用 AlphaFold2 重新预测每个设计的结构
  - 检验预测结构与 RFDiffusion 设计结构是否一致
  - 指标：pLDDT（>80 为良好）、RMSD（<1.5 Å 为一致）
  - 作用：过滤掉序列和骨架不匹配的设计
  - 通常淘汰 80–90%

过滤层 2：Rosetta 能量打分
  - 计算 Rosetta REF2015 能量函数打分
  - 排除不稳定设计
  - 通常保留 top 10–20%

过滤层 3：活性位点几何验证
  - 检查催化残基是否保持正确的空间位置
  - 检查过渡态类似物在活性位点的对接姿态
  - 通常保留 top 5–10%

过滤层 4：MD 稳定性筛选（可选，耗时，但更准确）
  - 对最终候选进行短 MD 模拟（10–50 ns）
  - 检查活性位点在热运动下是否保持稳定
  - 通常保留 top 1–5%
```

**最终送实验**：通常每个设计活动提交 **48–200 个候选**去 wet lab。

---

#### Step 5：湿实验验证（Wet Lab）

你导师提到他们会送去 **White Lab**（可能是具体的合作实验室）进行实验测试：

```
Step 5a：基因合成 + 蛋白质表达
  - 将设计序列委托合成 DNA
  - 在大肠杆菌（E. coli）或酵母中表达
  - His-tag 亲和纯化

Step 5b：酶活性初筛
  - 用 HPLC 或质谱检测反应产物
  - 底物：吲哚 + L-Ser（检测是否有 Trp 产物）
  - 如果有活性，测定 kcat 和 Km

Step 5c：手性分析（最关键！）
  - 用手性柱 HPLC 或手性质谱区分 L-Trp 和 D-Trp
  - 计算 ee 值（enantiomeric excess = (D-D_frac - L_frac) / (D_frac + L_frac) × 100%）
  - 目标：ee > 90%（D-形式）

Step 5d：命中后优化
  - 对活性/立体选择性最好的变体进行进一步工程化
  - 可结合定向进化 + 计算预测
```

---

### 5.3 MetaDynamics 在这个流程中可能的位置

目前，**你的导师说 MetaDynamics 怎么整合进来还没想好**。以下是三个具体可行的接入点：

#### 接入点 A：过滤层 4 的增强版（最自然的切入）

在当前的 MD 稳定性筛选基础上，改用 MetaDynamics：

```
传统方法：跑 10-50 ns 常规 MD，看 RMSD 稳定性
MetaDynamics 升级：跑 WTMetaD，采样构象系综，计算 FEL

具体操作：
  - 对每个候选设计，跑 COMM domain 的 MetaDynamics
  - 计算 D-Trp 过渡态构象的 ΔG（相对于 L-Trp 过渡态）
  - 优先筛选 ΔG(D-TS) 更低的设计
```

这是最直接的做法，不改变现有流程，只是把一个步骤做得更好。

#### 接入点 B：Reward Function 的物理学项

在 RFDiffusion 的设计过程中，直接将 MetaDynamics FEL 信息编码为额外的打分项：

```
当前 reward function:
  Score = AF2_pLDDT + Rosetta_energy + active_site_geometry

MetaDynamics 增强版:
  Score = AF2_pLDDT + Rosetta_energy + active_site_geometry
        + λ × ΔG(D-TS)  ← MetaDynamics 提供的项

其中 ΔG(D-TS) 从一个小型 MetaDynamics 数据库学习：
  - 对已知的 TrpB 变体跑 MetaDynamics
  - 建立 "结构特征 → ΔG(D-TS)" 的 ML 模型
  - 用这个模型快速预测新设计的 ΔG(D-TS)
```

这是你导师讲话中 "reward function 的 term 很重要，想让 MetaDynamics contribute 进来" 的具体实现。

#### 接入点 C：理解机制，反推设计规则

先用 MetaDynamics 深入研究野生型 TrpB 的 FEL：
- 找到"D-Trp 产物所需的过渡态构象"对应的 FEL 高能点
- 用 SPM 方法找到哪些残基对这个高能态的稳定化贡献最大
- 将这些残基位置作为 RFDiffusion 设计时的额外约束

---

## 第六章：现有方法全景——知己知彼

### 6.1 方法论谱系图

TrpB 相关研究和非天然氨基酸合成的现有方法可以大致分为以下几类：

```
                          [D-Trp 合成目标]
                               ↓
        ┌──────────────────────┼───────────────────────┐
        ▼                      ▼                       ▼
   化学合成方法           生物催化方法               AI 辅助设计
        ↓                      ↓                       ↓
  不对称合成/拆分        酶级联/定向进化            de novo / 半理性
```

---

### 6.2 定向进化方法（Arnold Lab 路线）

**核心工具**：
- 随机突变（epPCR）+ 高通量筛选
- 半理性设计（SmArts Library）+ 筛选
- 最近：**AI 辅助定向进化（active learning-assisted DE）**（Nature Communications, 2025）

**代表工作**：
- Arnold lab 对 PfTrpB 的进化（PNAS 2015）：3 轮，6 突变，83× 活性提升
- TrpB Pfquat（JACS 2019）：6 轮定向进化，合成季碳手性中心，400× 活性提升
- Active learning-assisted DE（2025）：将 ML 预测与实验迭代结合，大幅减少筛选轮数

**局限**：
- 对于立体化学完全反转（L→D），需要改变的突变位点太多，定向进化搜索空间不足
- 每轮需要实验筛选，时间和成本高

---

### 6.3 半理性设计 + MetaDynamics（Osuna Lab 路线）

**核心工具**：
- MetaDynamics（FEL 重建）
- SPM（识别关键远端位点）
- AlphaFold2 + short MD（快速估计）

**代表工作（已在第三章详述）**：
- JACS 2019：FEL 解析 TrpB 别构调控
- ACS Catal 2021：SPM 方法，7× 活性提升，测试 1 个变体
- Protein Sci 2022：tAF2-MD 快速筛选方案
- GenSLM TrpB（Nature Commun 2026）：语言模型设计新型 TrpB

**局限**：
- 仍基于改造现有 TrpB，受天然序列约束
- FEL 计算成本较高（需要 100–500 ns MetaDynamics per 变体）
- 对立体化学翻转问题尚无直接解决方案

---

### 6.4 De Novo 酶设计方法（Baker Lab + 最新进展）

**核心工具**：
- RFDiffusion（2023, Nature）：蛋白质骨架生成
- ProteinMPNN（2022）：序列设计
- AlphaFold2（2021）：结构验证
- RFDiffusion2（2025, Nature Methods）：原子级活性位点支架化

**代表工作**：
- RFDiffusion（Watson et al., 2023）：包含 de novo 酶设计案例（Diels-Alderase）
- RFDiffusion2（Lauko et al., 2025）：retroaldolase + cysteine hydrolase + zinc hydrolase
- Riff-Diff（Nature 2025）：retro-aldol 和 MBH 反应的 de novo 酶
- GRACE workflow（2024）：针对碳酸酐酶，10,000 候选 → 2 功能酶

**局限**：
- 活性通常比自然酶低 1–3 个数量级，需要后续进化
- 对于需要 PLP 辅因子的复杂反应（如 TrpB），设计难度更高
- 立体化学控制仍是挑战

---

### 6.5 神经网络辅助 MD（NeuroMD / 你导师提到的"老方法"问题）

会议中提到的 "NeuroMD" 和 "neuroplexor" 是指 **机器学习势（ML Potential）** 领域的工作：

**NeuroPlex / Neural MD 系列**：
- 用神经网络学习量子力学势能面（代替传统力场如 AMBER/CHARMM）
- 更准确描述化学键形成/断裂（可以处理催化机制本身）
- 代表工作：ANI（2017）、NequIP（2022）、MACE（2022）、DeePMD（2018）

**你导师否定 neuroplexor 的原因**（根据会议记录分析）：
- 有一篇相似的工作（2024 年 12 月 31 日发表，可能是某个组的 neuro-MD + TrpB 工作）
- 重新训练 ML potential 需要大量 QM/MM 数据，工程量巨大
- 你导师认为这条路已经被做掉或者不够 impactful

**对你的启示**：你做的 MetaDynamics 用的是传统力场（AMBER/CHARMM），这与 Neural MD 是不同的工具，没有冲突。

---

## 第七章：你的独特价值——如何在这个项目中脱颖而出

### 7.1 你拥有的独特组合

你的背景恰好横跨了当前项目的所有关键技术：

| 你的背景 | 项目需要 | 连接方式 |
|---------|---------|---------|
| LiGaMD3（enhanced sampling） | MetaDynamics 操作 | 两者都是增强采样，原理相通，操作可迁移 |
| XGBoost/LSTM/ML 建模 | FEL → reward function | 直接迁移，建立 structure-FEL-activity 模型 |
| PCA/K-Means 构象分析 | 设计候选筛选 | 用聚类分析构象多样性 |
| HPC/Slurm 自动化 | 大规模 MD 计算 | 你比任何人都更快 setup 计算流程 |
| LSTM 时序收敛预测 | MetaDynamics 收敛判断 | 这个没人做过！可以做成创新点 |

### 7.2 具体的 Impact 方向（你可以主动提议）

#### 提议一：建立 FEL-to-Function 数据库（第 6–8 周提议）

```
计划：
  - 对 Osuna 文献中已知的 TrpB 变体（wildtype, LBCA, SPM6, 等 10–20 个）
    跑统一的 MetaDynamics 计算
  - 提取每个变体的 FEL 特征向量（ΔG, 能垒高度, closed state 深度等）
  - 与已知的活性数据（kcat, ee 值）关联
  - 建立 XGBoost/Random Forest 模型：FEL 特征 → 预测催化性能

价值：
  - 这是一个"FEL 特征作为 scoring function"的可量化实现
  - 如果模型预测精度够高，就可以快速筛选 RFDiffusion 的候选设计
  - 是你可以在 2–3 个月内完成并拿出结果的工作
```

#### 提议二：LiGaMD vs MetaDynamics 基准对比（第 4–6 周提议）

```
你的独特优势：你同时懂两种方法

计划：
  - 在相同的 TrpB 系统上，平行运行 LiGaMD3 和 WTMetaDynamics
  - 比较：FEL 的形状一致性、计算成本、采样效率
  - 如果 LiGaMD3 更快或更准，就有 methodological contribution

价值：
  - 这是别人做不到的比较（没有人同时有两种增强采样的经验）
  - 即使结论是 "两者一致"，也是有价值的 benchmark
  - 这直接 showcase 你的背景
```

#### 提议三：ML-assisted MetaDynamics 收敛检测（最创新，较长期）

```
你的 LSTM 时序预测经验 + MetaDynamics 收敛问题 = 有趣的组合

MetaDynamics 的收敛判断目前主要靠人工：
  - 把 HILLS 文件分成几段，比较 FEL 形状
  - 很耗时，依赖经验判断

你的想法：
  - 用你在 Miao Lab 做的时序 ML 方法
  - 输入：COLVAR 文件（CV 随时间的轨迹）
  - 输出：预测模拟何时收敛，提前终止不必要的计算
  - 可以节省大量 GPU 时间

价值：
  - 这是一个真正新颖的工具，Osuna 组自己都没有
  - 一旦能用，整个组都会受益
  - 投 JACS/ACS Catal 都有足够分量
```

---

## 第八章：行动清单——从今天到第一个月

### 本周（第 1 周）

```
[ ] 读 Osuna JACS 2019（精读，做笔记，重点看 Figure 1-3 的 FEL）
[ ] 安装 GROMACS（最新稳定版，2023 或 2024）+ PLUMED（2.9.x）
[ ] 完成 PLUMED 官方 alanine dipeptide MetaDynamics tutorial
[ ] 读 Barducci et al. 2008（PRL，well-tempered MetaDynamics 原始论文）
[ ] 从 RCSB 下载 PfTrpB 的 PDB 结构（推荐 PDB: 5DW3 或 1K8Z）
```

### 第 2 周

```
[ ] 读 Osuna ACS Catal 2021（SPM 方法）
[ ] 为 TrpB 系统做 GROMACS 的 system preparation
    - 加氢原子（protonation state，pH 7.4）
    - 溶剂化（TIP3P water box）
    - 加 NaCl（150 mM）
    - 能量最小化 + NVT + NPT 平衡
[ ] 访问 SPM webserver（spmosuna.com），了解 TrpB 的通信网络
```

### 第 3–4 周

```
[ ] 定义 TrpB COMM domain 的 CV（RMSD + distance 两个 CV）
[ ] 运行 WTMetaD（建议 4 walkers × 50 ns = 200 ns 总时间）
[ ] 重建 FEL，检查 open/closed 能差是否合理（应在 2-8 kcal/mol 范围）
[ ] 写第一篇 weekly update（详细描述你的 MetaDynamics setup 参数）
```

### 第 5–8 周

```
[ ] 开始对 RFDiffusion 生成的候选结构做 MetaDynamics
[ ] 与导师讨论 reward function 具体设计
[ ] 如有余力：开始 LiGaMD3 vs MetaDynamics 的基准比较
```

---

## 附录：关键资源汇总

### 必读论文（按优先级）

1. **Osuna JACS 2019** — TrpB MetaDynamics core paper
2. **Barducci et al. PRL 2008** — Well-tempered MetaDynamics 原理
3. **Osuna ACS Catal 2021** — SPM 方法
4. **Watson et al. Nature 2023** — RFDiffusion
5. **Buller et al. PNAS 2015** — TrpB standalone directed evolution
6. **Toney, PMC 2021** — TrpB Biocatalyst Extraordinaire（机制综述）
7. **Lauko et al. Nature Methods 2025** — RFDiffusion2

### 软件工具

| 工具 | 用途 | 网址/来源 |
|------|------|---------|
| GROMACS | MD 引擎 | gromacs.org |
| PLUMED | MetaDynamics 插件 | plumed.org |
| ProteinMPNN | 序列设计 | GitHub: dauparas/ProteinMPNN |
| RFDiffusion | 骨架生成 | GitHub: RosettaCommons/RFdiffusion |
| AlphaFold2 | 结构预测/验证 | GitHub: google-deepmind/alphafold |
| SPM Webserver | 通信网络分析 | spmosuna.com |
| Rosetta | 能量打分 | rosettacommons.org |
| VMD | 可视化 | ks.uiuc.edu/Research/vmd |

### PDB 结构建议

| PDB ID | 物种 | 状态 | 用途 |
|--------|------|------|------|
| 5DW3 | PfTrpB（Pyrococcus furiosus） | Standalone, open | MetaDynamics 起始结构 |
| 1K8Z | StTrpB（Salmonella） | In complex with TrpA | 参考结构 |
| 5T5K | PfTrpB with inhibitor | Semi-closed | Closed state 参考结构 |

---

*本综述整合自：Osuna Lab 官方文献、PLUMED 官方文档、RFDiffusion2 论文（Nature Methods 2025）、TrpB Biocatalyst Review（PMC 2021）、D-Tryptophan Frontiers 综述（2024）及相关领域一手文献。*

*引用文献（部分）：*
- *[Osuna JACS 2019](https://pubs.acs.org/doi/abs/10.1021/jacs.9b03646)*
- *[Osuna ACS Catal 2021](https://pubs.acs.org/doi/10.1021/acscatal.1c03950)*
- *[TrpB Biocatalyst Review](https://pmc.ncbi.nlm.nih.gov/articles/PMC7935429/)*
- *[RFDiffusion2 biorxiv](https://www.biorxiv.org/content/10.1101/2025.04.09.648075v1)*
- *[D-Trp Frontiers 2024](https://www.frontiersin.org/journals/microbiology/articles/10.3389/fmicb.2024.1455540/full)*
- *[MetaDynamics Nature Rev Physics](https://www.nature.com/articles/s42254-020-0153-0)*
- *[PLUMED Belfast Tutorial](https://www.plumed.org/doc-v2.9/user-doc/html/belfast-6.html)*
- *[SPM Webserver](https://spmosuna.com/)*
