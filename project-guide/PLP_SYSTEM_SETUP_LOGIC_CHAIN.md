# PLP 参数化与体系搭建：从 PDB 到可跑 MetaDynamics 的完整逻辑链

> **这是什么文档？** 这份文档是 [FULL_LOGIC_CHAIN.md](FULL_LOGIC_CHAIN.md) 第九章 Step 1-5 的详细展开。它假设你什么都不知道，从"我手上有 PDB 文件"出发，一步一步讲到"我有一个溶剂化、平衡好的体系，可以开始跑 MetaDynamics"。每个概念第一次出现时都会解释。每个步骤都会说清楚"为什么要做这一步"。
>
> **读这份文档需要多久？** 大约 35-40 分钟。建议一口气读完。
>
> **这份文档的受众是谁？** 你自己（Zhenpeng），以及你和 PI 开会讨论时的参考材料。文档中标注了所有需要 PI 决策的地方。

---

## 第一章：为什么 PLP 参数化是第一个 Blocker

### 1.1 问题的本质

你想做的事情是：拿一个蛋白质的三维结构（PDB 文件），放进计算机里跑分子动力学模拟。但计算机不认识"原子"——它只认识数字。你需要告诉计算机：

1. 每个原子在哪里（坐标，从 PDB 文件读取）
2. 每个原子和周围原子之间的相互作用是什么（力场参数）

第 2 点就是 **力场 (Force Field)** 的工作。

### 1.2 什么是力场

力场是一套数学公式 + 参数的集合，描述原子之间的相互作用力。你可以把它想成一本"说明书"：

- 两个碳原子之间的化学键长应该是 1.53 A，弹簧常数是 317 kcal/mol/A^2
- 三个原子组成的键角应该是 109.5 度
- 四个原子组成的二面角偏好某些特定角度
- 两个不成键的原子之间有 van der Waals 作用力和静电作用力

对于蛋白质的 20 种标准氨基酸，力场（比如我们用的 **ff14SB**）已经提供了所有参数。你丢一个全是标准氨基酸的蛋白质进去，力场知道怎么处理每一个原子。

### 1.3 PLP 不是标准氨基酸

问题来了：**PLP (Pyridoxal 5'-Phosphate, 磷酸吡哆醛)** 不是 20 种标准氨基酸之一。它是一个辅因子 (cofactor)，通过共价键连接在 K82（第 82 号赖氨酸）上。

ff14SB 的"说明书"里没有 PLP 的条目。计算机不知道 PLP 的吡啶环上的原子之间应该用多大的弹簧常数，不知道磷酸基团的氧原子应该带多少电荷。

> **类比**：你去一个餐厅点菜，菜单上有 20 道标准菜（标准氨基酸），但你带了一道自己做的菜（PLP）要求厨房加热。厨房说："这道菜的烹饪温度是多少？用什么火候？"你得自己提供这些信息。这就是"参数化"。

### 1.4 Schiff Base 共价连接让事情更复杂

如果 PLP 只是一个独立的小分子"泡"在蛋白质旁边，参数化相对简单。但 PLP 通过一个叫 **Schiff base (席夫碱)** 的化学键共价连接到 K82 的侧链氨基上：

```
K82-NZ=C4'（PLP 的醛基碳）
     ↑
   这就是 Schiff base 键（C=N 双键）
```

这意味着 PLP 和 K82 不是两个独立的分子——它们在化学上是一体的。在 PDB 文件中，它被记录为一个特殊的残基类型 **LLP**（N6-pyridoxal-lysine），包含了 PLP 的原子 + K82 的主链和侧链原子。

> **为什么这让参数化更难？** 因为你不能单独给 PLP 算参数，也不能单独给 K82 算参数。Schiff base 键附近的原子的电荷分布、键参数都受到双方的影响。你必须把 PLP-K82 整体当作一个单元来参数化。

### 1.5 没有 PLP 参数，后面全部走不动

整个 pipeline 是严格线性依赖的：

```
PLP 参数 → tleap 建模 → 最小化 → 加热 → 平衡 → 500ns MD → GROMACS 转换 → MetaDynamics
```

如果第一步做不出来，后面全部被 block。这就是为什么 PLP 参数化是"第一个 blocker"。

---

## 第二章：PDB 文件里到底有什么

### 2.1 两个关键的 PDB 结构

我们需要参数化的中间体来自两个 PDB 结构：

| PDB ID | 分辨率 | 中间体 | 残基名 | 含义 |
|--------|--------|--------|--------|------|
| **5DVZ** | 1.5 A | E(Ain) — Internal aldimine | **LLP** | PLP 通过 Schiff base 连在 K82 上，等待底物 |
| **5DW0** | 1.9 A | E(Aex1) — External aldimine | **PLS** | L-丝氨酸挤走 K82，自己和 PLP 形成 Schiff base |

> **为什么是这两个？** 因为 Osuna 的论文研究了 4 个中间体（Ain, Aex1, A-A, Q2），每个都需要独立参数化。5DVZ 和 5DW0 是已有晶体结构的两个。A-A 和 Q2 没有 PfTrpB 的晶体结构，需要从其他物种的结构（如 4HPX, 3CEP）建模或通过化学修改生成。
>
> **我们的复刻只需要 Ain（因为 Phase 1 目标是 PfTrpS(Ain) 的 MetaDynamics）**，但理解所有中间体对后续工作很重要。

### 2.2 LLP 残基的原子组成（5DVZ, E(Ain), 24 个重原子）

从 PDB 文件直接读取（chain A, residue 82）：

```
FORMUL   1  LLP    4(C14 H22 N3 O7 P)
```

24 个重原子（不含氢）分属两部分：

**PLP 吡啶环 + 磷酸基团（15 个原子）：**

| 原子名 | 元素 | 属于什么基团 |
|--------|------|------------|
| N1 | N | 吡啶环氮 |
| C2 | C | 吡啶环碳 |
| C2' | C | 吡啶环 2 位甲基 |
| C3 | C | 吡啶环碳 |
| O3 | O | 酚羟基（3 位） |
| C4 | C | 吡啶环碳 |
| C4' | C | **Schiff base 碳（连接 NZ 的那个）** |
| C5 | C | 吡啶环碳 |
| C6 | C | 吡啶环碳 |
| C5' | C | 磷酸连接的亚甲基 |
| OP4 | O | 磷酸酯氧（桥接 C5'-P） |
| P | P | 磷原子 |
| OP1 | O | 磷酸氧 |
| OP2 | O | 磷酸氧 |
| OP3 | O | 磷酸氧 |

**K82 主链 + 侧链（9 个原子）：**

| 原子名 | 元素 | 属于什么基团 |
|--------|------|------------|
| N | N | K82 主链氨基 |
| CA | C | K82 主链 alpha 碳 |
| CB | C | K82 侧链 beta 碳 |
| CG | C | K82 侧链 gamma 碳 |
| CD | C | K82 侧链 delta 碳 |
| CE | C | K82 侧链 epsilon 碳 |
| NZ | N | **K82 侧链末端氮——Schiff base 的 N** |
| C | C | K82 主链羰基碳 |
| O | O | K82 主链羰基氧 |

PDB 中的 LINK 记录证实 LLP 残基 82 通过肽键连接到前后残基：
```
LINK         C   HIS A  81                 N   LLP A  82     （前一个残基 His81 的 C 连到 LLP 的 N）
LINK         C   LLP A  82                 N   THR A  83     （LLP 的 C 连到后一个残基 Thr83 的 N）
```

> **关键理解**：LLP 不是一个"外来的配体"。它是蛋白质多肽链的一部分（残基 82），只是这个残基恰好包含了 PLP 辅因子。在肽链中，它正常地通过肽键连接 His81 和 Thr83。

### 2.3 PLS 残基的原子组成（5DW0, E(Aex1), 22 个重原子）

```
FORMUL   5  PLS    4(C11 H17 N2 O8 P)
```

PLS 和 LLP 的关键区别：

| 区别 | LLP (Ain) | PLS (Aex1) |
|------|-----------|------------|
| Schiff base 连接对象 | K82 的 NZ | L-丝氨酸的 N |
| K82 | **包含在残基内** | **不包含**（K82 变回普通 Lys） |
| 底物 | 无 | L-丝氨酸 (Ser) 的主链 + OG |
| 总重原子数 | 24 | 22 |
| 分子式 | C14H22N3O7P | C11H17N2O8P |
| PDB 中位置 | 残基 82（取代 Lys82） | HETATM 401（独立配体） |

PLS 的独特原子（相比 LLP）：

| 原子名 | 元素 | 含义 |
|--------|------|------|
| N | N | Ser 主链氨基 |
| CA | C | Ser alpha 碳 |
| CB | C | Ser beta 碳 |
| OG | O | Ser 侧链羟基 |
| C | C | Ser 羰基碳 |
| O | O | Ser 羰基氧 |
| OXT | O | Ser 羧基另一个氧（C-末端形式） |
| C4A | C | **Schiff base 碳（原来的 C4'）——连接 Ser 的 N** |
| C2A | C | 吡啶环 2 位甲基（原来的 C2'，改了名） |
| C5A | C | 磷酸连接亚甲基（原来的 C5'） |
| O4P | O | 磷酸酯桥氧（原来的 OP4） |

> **注意命名变化**：5DVZ (LLP) 和 5DW0 (PLS) 对相同的 PLP 原子使用了不同的名字（C4' vs C4A, C2' vs C2A 等）。这是 PDB 命名惯例的差异，不代表化学结构不同。

### 2.4 四个中间体的化学差异总览

| 中间体 | 缩写 | PLP 连接对象 | PLP 环的变化 | K82 状态 | 需要参数化的总电荷 |
|--------|------|-------------|-------------|---------|------------------|
| Internal aldimine | **Ain** | K82-NZ | 无 | Schiff base (NZ=C4') | 需要计算 |
| External aldimine (Ser) | **Aex1** | Ser-N | 无 | 自由 Lys (NH3+) | 需要计算 |
| Aminoacrylate | **A-A** | 底物-N（脱水后） | 无 | 自由 Lys (NH3+) | 需要计算 |
| Quinonoid | **Q2** | Ind-Ser-N | 吡啶环共轭变化 | 自由 Lys (NH3+) | 需要计算 |

> **为什么要理解这些差异？** 每个中间体的化学结构不同，意味着原子间的电子密度分布不同，因此 RESP 电荷不同，力场参数也不同。**每个中间体需要独立走一遍完整的参数化流程。**

---

## 第三章：GAFF + RESP 工作流详解

### 3.1 整体思路

PLP 不在标准力场里，所以我们需要自己生成它的力场参数。这分两大块：

1. **键参数（bonds, angles, dihedrals）**：原子之间的弹簧常数、平衡距离等 -- 用 **GAFF** 自动分配
2. **原子电荷（partial charges）**：每个原子带多少电 -- 用 **RESP** 通过量子化学计算得到

### 3.2 GAFF 是什么

**GAFF (General AMBER Force Field)** 是 AMBER 提供的一个"通用"小分子力场。ff14SB 只管蛋白质的 20 种标准氨基酸，GAFF 管其他所有有机小分子。

GAFF 的工作方式是：看你给它的分子里有哪些原子类型（sp2 碳、sp3 碳、芳香氮、磷酸氧...），然后从它的参数数据库里查找对应的键长、键角、二面角参数。

> **类比**：ff14SB 像一本精装的"标准菜谱"，只收录 20 道经典菜。GAFF 像一本"万能调料表"——虽然没有每道菜的精确配方，但它有每种调料的基本用量规则，你可以用这些规则组合出任何菜的近似配方。
>
> GAFF 的精度不如为特定分子量身定制的参数，但对于 PLP 这类辅因子，它已经足够好了（尤其是当我们配合高质量的 RESP 电荷时）。

### 3.3 RESP 充电是什么

RESP 的全称是 **Restrained Electrostatic Potential**（约束静电势）充电方法。它的核心思想是：

1. 先用量子化学方法（HF/6-31G(d)）计算分子周围的静电势（electrostatic potential, ESP）
2. 然后找一组原子点电荷（partial charges），使得这些点电荷产生的静电势尽可能地拟合量子化学计算出的 ESP
3. 加一个"约束"（restraint）：尽量让化学等价的原子（比如甲基上的三个氢）有相同的电荷

> **为什么是 HF/6-31G(d)？** 这不是随便选的。AMBER 力场（包括 ff14SB 和 GAFF）的所有标准电荷都是用 HF/6-31G(d) 计算的。如果你用更高级的方法（比如 B3LYP 或 MP2），得到的电荷和力场的其他参数不匹配，反而会降低精度。
>
> **类比**：这就像配眼镜——镜片和镜框要匹配。用更"高级"的镜片配一个设计给低级镜片用的镜框，戴上反而看不清。HF/6-31G(d) 是 AMBER 力场体系的"标准镜框"，所有部件都是围绕它设计的。

### 3.4 完整 Pipeline 图

```
PDB 文件（5DVZ）
    │
    ├─ 1. 提取 PLP-K82 单元
    │     └─ 从 PDB 中取出 LLP 残基的坐标
    │
    ├─ 2. 加氢 + 加 capping groups（ACE/NME）
    │     └─ 量子化学计算需要完整的电子结构，PDB 没有氢原子
    │
    ├─ 3. antechamber：原子类型分配
    │     └─ 输入：mol2/PDB → 输出：带 GAFF 原子类型的 mol2
    │     └─ 命令：antechamber -fi pdb -fo mol2 -c bcc -at gaff2
    │
    ├─ 4. Gaussian 计算：优化几何 + ESP
    │     └─ 输入：Gaussian .com 文件
    │     └─ 关键词：#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt
    │     └─ 输出：.log 文件（含 ESP 数据）
    │
    ├─ 5. antechamber -c resp：从 ESP 拟合 RESP 电荷
    │     └─ 输入：Gaussian .log → 输出：带 RESP 电荷的 mol2
    │
    ├─ 6. parmchk2：检查缺失参数
    │     └─ 输入：mol2 → 输出：frcmod（补充缺失的力场参数）
    │
    └─ 7. tleap：组装完整体系
          └─ 加载 ff14SB + GAFF + TIP3P + mol2 + frcmod
          └─ 输出：parm7（拓扑）+ inpcrd（坐标）
```

### 3.5 每一步详解

**Step 1 & 2: 提取 + 加氢**

从 5DVZ.pdb 中提取 chain A 的 LLP 残基 82。PDB 文件只有重原子坐标（no hydrogens），但量子化学需要氢原子才能正确计算电子分布。

加氢的工具可以是：
- `reduce`（AmberTools 自带）
- PyMOL（`h_add` 命令）
- Open Babel

> **为什么 PDB 没有氢原子？** X-ray 晶体学的分辨率通常不够看到氢原子（氢只有 1 个电子，散射能力太弱）。所以 PDB 文件中几乎不含氢坐标。

**Step 3: antechamber 原子类型分配**

antechamber 是 AmberTools 的一个程序，专门处理小分子。它做两件事：
1. 给每个原子分配一个 GAFF 原子类型（比如 `ca` = 芳香碳，`os` = 醚氧，`p5` = 五价磷）
2. （可选）计算初步电荷（AM1-BCC 方法，快但不如 RESP 准确）

```bash
antechamber -i llp.pdb -fi pdb -o llp_gaff.mol2 -fo mol2 -c bcc -at gaff2 -rn LLP
```

| 参数 | 含义 |
|------|------|
| `-i` | 输入文件 |
| `-fi pdb` | 输入格式是 PDB |
| `-o` | 输出文件 |
| `-fo mol2` | 输出格式是 mol2 |
| `-c bcc` | 电荷方法（AM1-BCC，这里只是初步的） |
| `-at gaff2` | 使用 GAFF2 原子类型（比 GAFF 更新更准确） |
| `-rn LLP` | 残基名设为 LLP |

**Step 4: Gaussian 量子化学计算**

这是整个流程中计算量最大的一步。Gaussian 16 在 Longleaf 上可用（`module load gaussian/16c02`）。

输入文件（`.com`）示例：

```
%mem=8GB
%nproc=8
%chk=llp_resp.chk
#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt

LLP (PLP-K82 internal aldimine) geometry optimization and ESP

-2 1
 N     -42.317  -74.558  -61.909
 C     -42.792  -73.582  -61.102
 ...（所有原子坐标）
```

| 关键词 | 含义 |
|--------|------|
| `HF/6-31G(d)` | Hartree-Fock 方法，6-31G(d) 基组——AMBER 标准 |
| `Opt` | 先优化分子几何结构（找能量最低的构型） |
| `Pop=MK` | 用 Merz-Kollman 方案计算 ESP |
| `iop(6/33=2)` + `iop(6/42=6)` | 控制 ESP 网格点的层数和密度 |

电荷和自旋多重度行（`-2 1`）的含义将在第五章详细讨论。

**Step 5: RESP 电荷拟合**

Gaussian 计算完成后，用 antechamber 从输出文件中提取 ESP 数据并拟合 RESP 电荷：

```bash
antechamber -i llp_resp.log -fi gout -o llp_resp.mol2 -fo mol2 -c resp -at gaff2 -rn LLP
```

| 和 Step 3 的区别 | |
|-------------------|---|
| 输入 | 从 PDB 变成了 Gaussian 的 .log 输出 |
| `-fi gout` | 输入格式是 Gaussian output |
| `-c resp` | 电荷方法从 bcc 变成了 resp |

这一步输出的 mol2 文件中，每个原子的电荷就是最终的 RESP 电荷。

**Step 6: parmchk2 检查缺失参数**

```bash
parmchk2 -i llp_resp.mol2 -f mol2 -o llp.frcmod -a Y -at gaff2
```

parmchk2 做的事情是：检查 mol2 文件中所有的键、角、二面角组合，看 GAFF 数据库里有没有对应的参数。如果有，什么都不做。如果没有，就用类似的原子类型的参数来"估计"一个值，写进 frcmod 文件。

> **frcmod 文件是什么？** 全称 Force field modification file。它只包含 GAFF 数据库中缺失的参数。在 tleap 中加载 frcmod 后，这些参数就会补充到力场中。
>
> **什么时候会有缺失参数？** PLP 的吡啶环、磷酸基团都是常见的化学基团，GAFF 基本都有。但 Schiff base 的 C=N 连接到 lysine 侧链这种组合可能不常见，某些二面角参数可能需要补充。

**Step 7: tleap 组装**

在第八章详细讨论。

---

## 第四章：Capping 问题

### 4.1 为什么不能直接把整个 PLP-K82 丢进 Gaussian

LLP 残基包含 24 个重原子 + 氢原子，加氢后大约 45-50 个原子。这对 HF/6-31G(d) 来说计算量很小，不是问题。

真正的问题是 **断键**。

LLP 残基的主链氮 (N) 连接前一个残基 His81 的 C，主链 C 连接后一个残基 Thr83 的 N。当你把 LLP 单独提取出来时，这两个肽键被"切断"了——主链 N 和 C 各有一个不饱和的价键（dangling bond）。

如果你直接拿这个"断键"的分子去做量子化学计算，电子分布会因为断键的存在而严重失真，得到的 RESP 电荷完全不可靠。

> **类比**：你要测量一段铁路的重量。你把这段铁路从完整的铁路线上切下来，但切口处钢轨是扭曲变形的——这个变形不是铁路本身的特征，而是切割造成的。如果你连变形部分一起称，得到的重量不准确。你需要在切口处做处理。

### 4.2 ACE/NME Capping 是什么

解决方案是给断键的两端加上 **capping groups（封端基团）**：

| 位置 | Cap | 全称 | 化学结构 | 做什么 |
|------|-----|------|---------|--------|
| N-端（前面） | **ACE** | Acetyl | CH3-CO- | 封住主链 N 的断键 |
| C-端（后面） | **NME** | N-methylamide | -NH-CH3 | 封住主链 C 的断键 |

加了 capping 之后，分子变成：

```
ACE — [LLP 残基] — NME
```

这样所有的价键都饱和了，没有断键，量子化学计算得到的电子分布是合理的。

### 4.3 Capping 对 RESP 电荷的影响

加了 ACE/NME 后，分子总原子数增加了（ACE 加 6 个原子，NME 加 6 个原子，含氢）。RESP 会给所有原子（包括 cap 原子）分配电荷。

最终用于 MD 模拟时，你只需要 LLP 残基本身的原子电荷，cap 原子的电荷被丢弃。

> **但要注意**：cap 原子的存在影响了 LLP 原子的电荷。如果不加 cap，LLP 主链原子的电荷会因为断键而严重偏离。加了 cap 后，LLP 主链原子"以为"自己还在肽链里，电荷分布更接近真实情况。

### 4.4 Osuna 实验室做了什么（从 SI 推断）

SI 只说了：

> "Ligand parameters were obtained using the antechamber module of AMBER16 with GAFF and RESP charges at the HF/6-31G(d) level using Gaussian09."

没有提到 capping 策略。但根据计算化学的标准做法：

1. **几乎可以确定使用了 ACE/NME capping**——这是 AMBER 社区的标准操作，不做 capping 的 RESP 电荷是不合理的
2. **可能对磷酸基团做了特殊处理**——磷酸在 LLP 中远离肽链，可能不需要 capping 但需要正确处理质子化状态
3. **可能 RESP 电荷经过了手动检查**——确保总电荷是整数、化学等价原子电荷相同

> **这是一个 SI gap**：capping 策略没有被显式记录。在与 PI 的会议中，建议使用标准的 ACE/NME capping，除非 PI 有不同意见。

---

## 第五章：质子化状态——最难的决策

### 5.1 为什么质子化状态如此重要

"质子化状态"就是：一个基团上的氢原子有没有——具体说，可解离的氢（连在 O、N 上的氢）到底是"连着的"还是"离开了"。

质子化状态直接决定了：
1. **分子的总电荷**（每少一个 H+，总电荷减 1）
2. **原子的局部电子密度**（一个 -OH 和一个 -O^- 的电荷分布完全不同）
3. **RESP 电荷计算的输入**（Gaussian 需要你指定总电荷和自旋多重度）
4. **力场中的相互作用**（带电基团的静电作用力比中性基团强得多）

> **如果质子化状态选错了，得到的 RESP 电荷是错的，整个力场参数是错的，跑出来的模拟轨迹是错的，最终的 FEL 是错的。** 这不是一个"差不多就行"的决策。

### 5.2 PLP 上 pH 敏感的基团

PLP 有三个 pH 敏感基团。实验在 **pH 7.5** 下进行（*P. furiosus* 的最适 pH），所以我们需要判断在 pH 7.5 下每个基团的状态：

| 基团 | pKa（文献值） | pH 7.5 下的状态 | 推理 |
|------|-------------|----------------|------|
| **磷酸** (-OPO3H2) | pKa1 ~1.6, **pKa2 ~6.2** | **双阴离子** (-OPO3^2-) | pH 7.5 >> pKa2 = 6.2，第二个 H 也掉了 |
| **酚羟基** (C3-OH) | **~5.8** (在 PLP 中由于吡啶 N 的吸电子效应降低) | **去质子化** (C3-O^-) | pH 7.5 >> pKa = 5.8 |
| **吡啶 N** (N1) | **~8.5** (游离 PLP); 在 Schiff base 中可能变化 | **质子化** (N1-H+) | pH 7.5 < pKa ~8.5 |

> **为什么吡啶 N 的 pKa 是 ~8.5 而不是通常的 ~5.2？** 游离吡啶的 pKa 是 5.2，但 PLP 中酚羟基的去质子化（O3^-）形成的分子内氢键稳定了 N1-H+ 形式，将 pKa 提高到 ~8.5。这是 PLP 化学的一个经典特征。

### 5.3 K82 的 NZ 氮

K82 的侧链末端氮 (NZ) 在不同中间体中状态不同：

| 中间体 | K82-NZ 状态 | 原因 |
|--------|------------|------|
| **Ain** | **Schiff base** (NZ=C4', 不带额外 H) | NZ 和 PLP 形成双键，不能再质子化 |
| **Aex1** | **游离 Lys** (NZ-H3+, pKa ~10.5) | 底物取代了 K82，NZ 重新变成自由胺 |
| **A-A** | **游离 Lys** (NZ-H3+) | 同上 |
| **Q2** | **游离 Lys** (NZ-H3+) | 同上 |

> **Ain 中间体的 Schiff base 氮是否质子化？** 这是一个微妙的问题。Internal aldimine 的 Schiff base 氮在 pH 7.5 下通常是质子化的（pKa ~10-11），形成 -NZ(H)+=C4'-。这使得 Schiff base 上有一个正电荷。但在酶的微环境中（surrounded by charged residues），实际 pKa 可能偏移。
>
> **SI 没有说**。这是一个需要决策的点。

### 5.4 各中间体的总电荷估算

基于上述分析，在 pH 7.5 下：

| 中间体 | 磷酸 | 酚氧 | N1 | NZ / Schiff base | 其他 | 预估总电荷 |
|--------|------|------|-----|-------------------|------|-----------|
| **Ain (LLP, 含 capping)** | -2 | -1 | 0 | +1 (质子化 Schiff base) | 0 (cap 中性) | **-2** |
| **Ain (LLP, 去质子化 Schiff base)** | -2 | -1 | 0 | 0 | 0 | **-3** |
| **Aex1 (PLS, 含 capping)** | -2 | -1 | +1 | N/A (Ser 的 N 无额外电荷) | 0 | **-2** |

> **自旋多重度**：所有中间体都是闭壳层分子（所有电子配对），自旋多重度 = 1（singlet）。

> **这是本文档中最大的不确定性**：总电荷取决于 Schiff base 氮的质子化状态，而 SI 没有给出答案。错误的总电荷会导致 Gaussian 计算的 ESP 完全错误，进而所有 RESP 电荷都错。

### 5.5 文献中的参考

以下文献讨论了 PLP 在酶环境中的质子化状态：

- **Toney 2011, Arch Biochem Biophys**：PLP 酶综述，讨论了不同中间体的质子化态
- **Casasnovas et al. 2014, JACS**：PLP 的 pKa 计算
- **Major & Gao 2006, JACS**：QM/MM 研究 PLP 的 Schiff base 质子化

建议在 PI 会议前查阅这些文献，形成自己的判断。

### 5.6 需要 PI 决策的问题

| 问题 | 选项 A | 选项 B | 建议 |
|------|--------|--------|------|
| Ain Schiff base NZ 质子化？ | 是 (总电荷 -1) | 否 (总电荷 -2) | 选 A (文献主流) |
| 磷酸双阴离子？ | 是 (-2) | 单阴离子 (-1) | 选"是" (pH 7.5 >> pKa2 6.2) |
| 酚 O3 去质子化？ | 是 (-1) | 否 (0) | 选"是" (pH 7.5 >> pKa 5.8) |
| N1 质子化？ | 是 (+1) | 否 (0) | 选"是" (pH 7.5 < pKa ~8.5) |

---

## 第六章：Gaussian 计算细节

### 6.1 输入文件格式

Gaussian 的输入文件是 `.com`（或 `.gjf`）格式的纯文本文件。结构如下：

```
%mem=16GB                          ← 分配内存
%nproc=16                          ← 使用 CPU 核心数
%chk=llp_ain.chk                   ← checkpoint 文件（断点续算用）
#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt
                                   ← 空行（必须）
LLP Ain internal aldimine - RESP charge calculation
                                   ← 空行（必须）
-2 1                               ← 总电荷  自旋多重度
 N     -42.317  -74.558  -61.909   ← 原子坐标（element x y z）
 C     -42.792  -73.582  -61.102
 ...
                                   ← 空行（结束标志）
```

### 6.2 关键词详解

| 关键词 | 含义 | 为什么用 |
|--------|------|---------|
| `HF` | Hartree-Fock 方法 | AMBER 标准；RESP 电荷的标配 |
| `6-31G(d)` | 基组（basis set），中等大小 | AMBER 标准；和力场其他参数匹配 |
| `Opt` | 几何优化 | 找到分子的最低能量构型再计算 ESP |
| `Pop=MK` | Merz-Kollman ESP 计算方案 | RESP 需要 ESP 数据 |
| `iop(6/33=2)` | 多层 ESP 网格 | 提高 RESP 拟合质量 |
| `iop(6/42=6)` | ESP 网格点密度 | 每个壳层 6 个点/A^2 |
| `iop(6/33=2)` + `iop(6/42=6)` | 控制 MK ESP 网格层数和密度 | RESP 需要这些网格设置 |

### 6.3 各中间体的电荷和自旋多重度

| 中间体 | 总电荷 (推荐) | 自旋多重度 | 输入行 |
|--------|--------------|-----------|--------|
| **Ain** (ACE-LLP-NME, Schiff base 质子化) | -2 | 1 | `-2 1` |
| **Ain** (ACE-LLP-NME, Schiff base 去质子化) | -3 | 1 | `-3 1` |
| **Aex1** (ACE-PLS-NME) | -2 | 1 | `-2 1` |
| **A-A** (需要建模) | TBD | 1 | TBD |
| **Q2** (需要建模) | TBD | 1 | TBD |

> **自旋多重度为什么总是 1？** 自旋多重度 = 2S+1，S 是未配对电子总自旋量子数。PLP 中间体都是闭壳层分子（所有电子成对），S = 0，所以 2S+1 = 1。

### 6.4 Longleaf 上运行 Gaussian

```bash
# 加载 Gaussian
module load gaussian/16c02

# 提交作业（示例 Slurm 脚本）
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
g16 llp_ain.com
```

### 6.5 预计运行时间

LLP 有 24 个重原子，加氢 + ACE/NME 后大约 50-55 个原子。对于 HF/6-31G(d) + Opt：

| 原子数 | 基函数数 (approx) | 预计时间 (16 cores) |
|--------|-------------------|-------------------|
| ~50 | ~300 | **2-8 小时** |

> PLP 不是一个大分子。50 个原子的 HF/6-31G(d) 在现代 CPU 上很快。真正可能耗时的是几何优化的收敛（如果初始结构离最优构型很远，可能需要更多步）。

### 6.6 Gaussian 16 vs 09 的差异

SI 中 Osuna 使用的是 Gaussian 09。我们在 Longleaf 上有 Gaussian 16c02。

| 差异 | 影响 |
|------|------|
| 默认优化算法略有不同 | 收敛步数可能不同，但最终结构应该一样 |
| ESP 输出格式 | 完全兼容 |
| RESP 电荷结果 | 应该几乎完全一样（HF/6-31G(d) 的实现没有变化） |

> **结论**：Gaussian 16 和 09 在这个用例下可以互换，不影响复刻。

---

## 第七章：从 RESP 电荷到力场文件

### 7.1 antechamber -c resp 工作流

Gaussian 计算完成后，你有一个 `.log` 文件，里面包含了优化后的分子几何结构和 ESP 数据。下一步：

```bash
# Step 1: 从 Gaussian output 提取 RESP 电荷
antechamber -i llp_ain.log -fi gout -o llp_ain_resp.mol2 -fo mol2 \
    -c resp -at gaff2 -rn LLP -nc -1

# Step 2: 检查缺失参数
parmchk2 -i llp_ain_resp.mol2 -f mol2 -o llp_ain.frcmod -a Y -at gaff2
```

| 参数 | 含义 |
|------|------|
| `-nc -1` | 指定净电荷为 -1（必须和 Gaussian 中的一致） |
| `-a Y` | parmchk2 输出所有可能缺失的参数（而不只是完全缺失的） |

### 7.2 mol2 文件长什么样

mol2 是一种包含原子坐标、原子类型、键连接、**电荷**的文件格式。RESP 计算的核心输出就是这个文件：

```
@<TRIPOS>ATOM
      1 N1       -42.317  -74.558  -61.909 nb      1 LLP      -0.6314
      2 C2       -42.792  -73.582  -61.102 ca      1 LLP       0.3821
      3 C2'      -42.707  -73.742  -59.606 c3      1 LLP      -0.2176
      ...
@<TRIPOS>BOND
      1    1    2 ar
      2    2    3 1
      ...
```

每行原子的最后一列就是 RESP 电荷（例如 -0.6314）。中间的 `nb`、`ca`、`c3` 是 GAFF2 原子类型。

### 7.3 frcmod 文件长什么样

frcmod 是力场修改文件，只包含 GAFF 数据库中**缺失**的参数：

```
Remark line goes here
MASS
（缺失的原子类型质量——通常没有）

BOND
ca-nb  483.1   1.339    （芳香碳-芳香氮的键参数）

ANGLE
ca-ca-nb   67.2  122.10  （键角参数）

DIHE
X -ca-nb-X    2   9.60  180.0  2.0  （二面角参数）

IMPROPER
（不当二面角——维持平面性用）

NONBON
（非键参数——通常 GAFF 都有）
```

如果 frcmod 中某些参数被标记了 `ATTN: needs revision`，说明 parmchk2 找不到好的类比参数，用了比较粗糙的估计。这些参数需要你手动检查。

### 7.4 验证清单

在继续下一步之前，检查以下项目：

| 检查项 | 通过标准 | 怎么检查 |
|--------|---------|---------|
| **RESP 电荷总和** | 应该等于指定的净电荷（如 -1.000） | `grep "^@" llp_ain_resp.mol2` 或手动加总 |
| **所有原子都有 GAFF 类型** | 没有 `DU`（dummy）类型 | `grep "DU" llp_ain_resp.mol2` |
| **frcmod 无 "needs revision"** | 无 ATTN 警告 | `grep "ATTN" llp_ain.frcmod` |
| **化学等价原子电荷合理** | 磷酸三个氧电荷相近 | 目视检查 mol2 |
| **Schiff base 氮电荷合理** | NZ 电荷不应该太极端 (|q| < 1.0) | 检查 NZ 行 |
| **总原子数正确** | 和预期一致 | `wc -l` 统计 ATOM 行 |

---

## 第八章：体系组装 -- tleap

### 8.1 tleap 是什么

tleap 是 AmberTools 的体系构建程序。它的工作是：

1. 读取蛋白质的 PDB 文件
2. 给每个标准残基分配 ff14SB 参数
3. 给 PLP（LLP/PLS）分配你刚算好的 GAFF + RESP 参数
4. 加水（溶剂化）
5. 加离子（中和电荷）
6. 输出最终的 topology (parm7) 和 coordinate (inpcrd) 文件

### 8.2 处理 PLP-K82 共价键——最关键的一步

LLP 残基通过肽键连接到 His81 和 Thr83。在 tleap 中，有两种方式处理这种非标准残基：

**方法 A：使用 AMBER lib 文件（推荐）**

把 LLP 制作成一个 AMBER library (.lib) 文件，里面定义了：
- 所有原子的名字、类型、电荷
- 原子之间的键连接
- 残基的 head atom（连接前一个残基的 N）和 tail atom（连接后一个残基的 C）

```bash
# 在 tleap 中：
source leaprc.protein.ff14SB
source leaprc.gaff2
source leaprc.water.tip3p

# 加载 PLP 参数
loadamberparams llp_ain.frcmod
loadoff llp_ain.lib           # 包含 LLP 残基定义

# 加载蛋白质
mol = loadpdb protein_prepared.pdb
```

制作 lib 文件的方法：

```bash
# 先在 tleap 中从 mol2 创建
tleap -f - <<EOF
source leaprc.gaff2
LLP = loadmol2 llp_ain_resp.mol2
set LLP head LLP.1.N        # 设置 head atom = 主链 N
set LLP tail LLP.1.C        # 设置 tail atom = 主链 C
set LLP.1 connect0 LLP.1.N
set LLP.1 connect1 LLP.1.C
saveoff LLP llp_ain.lib
savepdb LLP llp_ain_check.pdb
quit
EOF
```

> **为什么 head 是 N, tail 是 C？** 因为 LLP 是多肽链的一部分。蛋白质是 N→C 方向合成的，所以前一个残基的 C 连接到 LLP 的 N（head），LLP 的 C 连接到下一个残基的 N（tail）。

**方法 B：使用 AMBER PREP 文件**

PREP 文件是 AMBER 的旧格式，功能和 lib 文件类似。一些旧教程会用这种格式。可以用但不推荐（lib 文件更直观）。

### 8.3 完整的 tleap 脚本

```bash
tleap -f - <<EOF
# 1. 加载力场
source leaprc.protein.ff14SB      # 蛋白质力场
source leaprc.gaff2               # 小分子力场
source leaprc.water.tip3p         # 水模型

# 2. 加载 PLP 参数
loadamberparams llp_ain.frcmod    # 缺失参数补充
loadoff llp_ain.lib               # LLP 残基定义

# 3. 加载蛋白质
mol = loadpdb pftrps_ain_prepared.pdb

# 4. 检查
check mol

# 5. 溶剂化（TIP3P 水，立方体 box，10 A buffer）
solvatebox mol TIP3PBOX 10.0

# 6. 加离子中和电荷
addions mol Na+ 0    # 加足够 Na+ 使体系中性
addions mol Cl- 0    # 如果需要额外 Cl-

# 7. 再次检查
check mol

# 8. 保存
saveamberparm mol pftrps_ain.parm7 pftrps_ain.inpcrd
savepdb mol pftrps_ain_solvated.pdb

quit
EOF
```

### 8.4 各步骤说明

**溶剂化 (Solvation)**

```
solvatebox mol TIP3PBOX 10.0
```

| 参数 | 含义 |
|------|------|
| `TIP3PBOX` | 使用预平衡的 TIP3P 水分子填充 |
| `10.0` | 蛋白质表面到 box 边界至少 10 A |

> **为什么是 10 A？** 这是 Osuna SI 中指定的值。10 A 的 buffer 大约对应 ~15,000 个水分子（对于 PfTrpS 这么大的复合体），足以避免蛋白质"看到"自己的周期性镜像。
>
> **为什么是立方体 (cubic) 而不是八面体 (truncated octahedron)?** SI 说 "pre-equilibrated cubic box"。立方体 box 浪费更多水分子（角落里的水其实不太需要），但和 SI 一致。

**离子中和 (Counterions)**

```
addions mol Na+ 0
addions mol Cl- 0
```

`0` 的意思是 "加到体系变成电中性为止"。如果蛋白质总电荷是 -8e，就加 8 个 Na+。

> **为什么要中和电荷？** MD 模拟使用周期性边界条件 + PME (Particle-Mesh Ewald) 处理长程静电。PME 要求体系总电荷为零，否则会有无穷大的能量发散。

SI 只说 "explicit counterions (Na+ or Cl-)"，没有提到额外的离子浓度（比如 150 mM NaCl）。所以我们只中和，不加额外盐。

### 8.5 输出文件

| 文件 | 格式 | 包含什么 | 后续用途 |
|------|------|---------|---------|
| `pftrps_ain.parm7` | AMBER topology | 所有原子的类型、电荷、键连接、力场参数 | AMBER MD 的输入 |
| `pftrps_ain.inpcrd` | AMBER coordinates | 所有原子的初始坐标 + box 尺寸 | AMBER MD 的输入 |
| `pftrps_ain_solvated.pdb` | PDB | 可视化检查用 | VMD/PyMOL 检查 |

> **parm7 + inpcrd 的关系**：parm7 描述了"这个体系有哪些原子、它们之间有什么相互作用"，inpcrd 描述了"每个原子现在在哪里"。就像一张地图（parm7）和一组 GPS 坐标（inpcrd）。MD 模拟需要两者才能运行。

---

## 第九章：常规 MD 协议 (AMBER)

### 9.1 为什么要先跑常规 MD

MetaDynamics 不是直接在晶体结构上跑的。你需要先：

1. **最小化 (Minimization)**：消除 PDB 结构中的原子碰撞（晶体学解析的原子位置不是精确的平衡位置）
2. **加热 (Heating)**：从 0 K 慢慢升温到 350 K（不能一步到位，蛋白质会"爆炸"）
3. **平衡 (Equilibration)**：在 350 K 下跑一段时间，让体系的密度、能量稳定下来
4. **产出 MD (Production)**：跑 500 ns，采集统计数据

只有经过这个过程，体系才处于物理上合理的状态，才能作为 MetaDynamics 的起始结构。

> **类比**：你要让一个人跑马拉松（MetaDynamics）。你不能直接把他从冰柜（0 K）里拿出来就开跑。你得先解冻（加热），然后做热身（平衡），确认身体状态正常后，再开始正式比赛。

### 9.2 两阶段最小化

**Stage 1：约束溶质，只最小化溶剂**

```
Minimization Stage 1: solvent relaxation
 &cntrl
  imin=1,           ! 最小化模式
  maxcyc=10000,     ! 最多 10000 步
  ncyc=5000,        ! 前 5000 步用最速下降法，后 5000 步用共轭梯度法
  ntb=1,            ! 周期性边界
  ntr=1,            ! 开启原子约束
  restraint_wt=500.0, ! 约束力常数 500 kcal/mol/A^2
  restraintmask='!@H= & !:WAT & !:Na+ & !:Cl-',  ! 约束蛋白质重原子
 /
```

| 参数 | SI 值 | 含义 |
|------|-------|------|
| `restraint_wt` | 500 kcal/mol/A^2 | 把蛋白质"钉死"在原位，只让水分子调整位置 |
| `ncyc` | 5000 | 前半用最速下降（大步快走），后半用共轭梯度（小步精调） |

> **为什么要分两种优化方法？** 最速下降法擅长快速消除大的原子碰撞，但到了接近最低点时效率很低。共轭梯度法在接近最低点时效率高，但如果初始结构碰撞严重，可能不收敛。先用最速下降处理大碰撞，再用共轭梯度精调，是标准做法。

**Stage 2：无约束最小化**

```
Minimization Stage 2: full system
 &cntrl
  imin=1,
  maxcyc=10000,
  ncyc=5000,
  ntb=1,
  ntr=0,           ! 无约束——所有原子都可以动
 /
```

### 9.3 七步加热 (0 → 350 K)

SI 描述："Seven 50-ps steps (0→350 K, 50 K increments), NVT, 1 fs timestep, decreasing harmonic restraints."

| Step | 温度 (K) | 约束力常数 (kcal/mol/A^2) | 时间 (ps) | 系综 |
|------|---------|--------------------------|----------|------|
| 1 | 0 → 50 | 210 | 50 | NVT |
| 2 | 50 → 100 | 165 | 50 | NVT |
| 3 | 100 → 150 | 125 | 50 | NVT |
| 4 | 150 → 200 | 85 | 50 | NVT |
| 5 | 200 → 250 | 45 | 50 | NVT |
| 6 | 250 → 300 | 10 | 50 | NVT |
| 7 | 300 → 350 | 10 (或 0) | 50 | NVT |

每个 step 的 AMBER 输入文件示例（以 step 1 为例）：

```
Heating step 1: 0-50 K
 &cntrl
  imin=0,            ! 动力学模式
  irest=0,           ! 全新启动（不是从 restart 文件继续）
  ntx=1,             ! 只读坐标（不读速度）
  nstlim=50000,      ! 50,000 步 × 1 fs = 50 ps
  dt=0.001,          ! 时间步长 1 fs
  ntc=2,             ! SHAKE 约束含 H 的键
  ntf=2,             ! 不计算含 H 键的力（因为 SHAKE 了）
  ntt=3,             ! Langevin 恒温器
  gamma_ln=1.0,      ! Langevin 碰撞频率
  tempi=0.0,         ! 初始温度
  temp0=50.0,        ! 目标温度
  ntb=1,             ! 常体积
  ntp=0,             ! 无压力控制 (NVT)
  ntr=1,             ! 原子约束
  restraint_wt=210.0,
  restraintmask='!@H= & !:WAT & !:Na+ & !:Cl-',
  ntpr=500,          ! 每 500 步输出能量
  ntwx=500,          ! 每 500 步写轨迹
  ntwr=5000,         ! 每 5000 步写 restart
 /
```

> **为什么是 NVT 而不是 NPT？** 加热阶段使用 NVT（恒温恒容），因为此时体系还没有达到平衡密度。如果用 NPT（恒温恒压），在温度剧烈变化时，压力控制器和恒温器可能会互相"打架"，导致 box 尺寸剧烈波动。
>
> **为什么约束力递减？** 开始时蛋白质被强力约束在晶体结构位置，只让水和氢原子适应新温度。随着温度升高，逐渐放松约束，让蛋白质也开始自由运动。如果一开始就不约束，低温下蛋白质可能因为初始碰撞而变形。

### 9.4 NPT 平衡

加热到 350 K 后，切换到 **NPT 系综**（恒温恒压），让体系找到正确的密度：

```
NPT Equilibration: 2 ns at 350 K, 1 atm
 &cntrl
  imin=0,
  irest=1,           ! 从加热的最后一步继续
  ntx=5,             ! 读坐标和速度
  nstlim=1000000,    ! 1,000,000 步 × 2 fs = 2 ns
  dt=0.002,          ! 时间步长 2 fs
  ntc=2,
  ntf=2,
  ntt=3,
  gamma_ln=1.0,
  temp0=350.0,
  ntb=2,             ! 恒压
  ntp=1,             ! 各向同性压力耦合
  barostat=2,        ! Monte Carlo barostat
  pres0=1.0,         ! 目标压力 1 atm
  ntr=0,             ! 无约束
  ntpr=1000,
  ntwx=1000,
  ntwr=50000,
 /
```

| SI 参数 | 值 | 含义 |
|---------|---|------|
| 时间 | 2 ns | 足够让密度稳定 |
| 系综 | NPT | 让 box 收缩/膨胀到正确密度 |
| 约束 | 无 | 蛋白质自由运动 |
| 时间步长 | 2 fs | 加热用 1 fs 是保守起见，平衡可以用 2 fs |

> **为什么平衡用 NPT？** 晶体结构放进水 box 后，水分子的密度不一定是 1 g/cm^3（因为 box 大小是随便选的 10 A buffer）。NPT 允许 box 尺寸自动调整，直到内部压力等于 1 atm，此时水的密度自然就是正确的 ~1 g/cm^3。

### 9.5 NVT 产出 MD (500 ns)

```
Production MD: 500 ns NVT at 350 K
 &cntrl
  imin=0,
  irest=1,
  ntx=5,
  nstlim=250000000,  ! 250,000,000 × 2 fs = 500 ns
  dt=0.002,
  ntc=2,
  ntf=2,
  ntt=3,
  gamma_ln=1.0,
  temp0=350.0,
  ntb=1,             ! 恒体积 (NVT)
  ntp=0,
  cut=8.0,           ! LJ + 静电 cutoff 8 A
  ntr=0,
  ntpr=5000,
  ntwx=5000,         ! 每 10 ps 写一帧
  ntwr=250000,
 /
```

| SI 参数 | 值 | 备注 |
|---------|---|------|
| 时间 | 500 ns | 每个体系跑 500 ns |
| 系综 | NVT | 用 NPT 平衡后确定的 box 尺寸 |
| cutoff | 8 A | LJ 和实空间静电的截断距离 |
| 静电 | PME | Particle-Mesh Ewald（长程静电） |
| 温度 | 350 K | *P. furiosus* 最适温度 |

> **为什么产出 MD 用 NVT 而不继续用 NPT？** 这是 AMBER 社区的常见做法。NPT 平衡后 box 尺寸已经稳定了，产出 MD 切到 NVT 可以避免 barostat 引入的体积波动对分析的干扰。此外，NVT 在 PLUMED/MetaDynamics 中更容易处理。

### 9.6 预计运行时间

在 Longleaf 的 GPU 节点上（NVIDIA V100/A100），AMBER pmemd.cuda 的速度大约是：

| 体系大小 (原子数) | 速度 (ns/day, V100) | 500 ns 需要 |
|------------------|--------------------|----|
| ~60,000 (PfTrpS αβ + 水) | ~80-120 | ~4-6 天 |
| ~40,000 (PfTrpB 单体 + 水) | ~120-180 | ~3-4 天 |

---

## 第十章：AMBER → GROMACS 转换

### 10.1 为什么需要转换

Osuna 的工作流程是：

```
AMBER (ff14SB) → 常规 MD 500 ns → [转换] → GROMACS + PLUMED2 → MetaDynamics
```

常规 MD 用 AMBER 是因为 AMBER 的 GPU 加速 (pmemd.cuda) 性能极好。MetaDynamics 用 GROMACS + PLUMED2 是因为原文就是用的这套组合，而且 PLUMED2 和 GROMACS 的集成最成熟。

> **能不能全用 AMBER？** 技术上可以。AMBER 也能和 PLUMED2 接口（通过 runtime patching）。但这不是 Osuna 原文的做法，严格复刻应该用 GROMACS。
>
> **能不能全用 GROMACS？** 也可以。但 AMBER 的 GPU 性能通常比 GROMACS 在小体系上更快（GROMACS 在大体系上更快）。而且我们的 ff14SB + GAFF 参数已经在 AMBER 格式下准备好了。

### 10.2 ParmEd 转换

**ParmEd** 是 AMBER 和 GROMACS 之间转换拓扑文件的标准工具。它是 AmberTools 的一部分：

```python
import parmed as pmd

# 读取 AMBER 文件
amber = pmd.load_file('pftrps_ain.parm7', 'pftrps_ain_equil_last.rst7')

# 保存为 GROMACS 格式
amber.save('pftrps_ain.top')      # GROMACS topology
amber.save('pftrps_ain.gro')      # GROMACS coordinates
```

或者用命令行：

```bash
python -c "
import parmed as pmd
a = pmd.load_file('pftrps_ain.parm7', 'pftrps_ain_equil_last.rst7')
a.save('pftrps_ain.top')
a.save('pftrps_ain.gro')
"
```

### 10.3 需要的输入文件

| 文件 | 来源 | 说明 |
|------|------|------|
| `pftrps_ain.parm7` | tleap 输出 | AMBER 拓扑 |
| `pftrps_ain_equil_last.rst7` | 500 ns 产出 MD 结束时的 restart 文件 | 平衡后的坐标 + box 信息 |

> **用 MD 结束的 restart 还是某个 snapshot？** 通常用最后一帧的 restart 文件，因为它代表了体系在 350 K 下平衡后的一个合理构象。如果要跑 multiple walkers，则需要 10 个不同的 snapshot（从 MD 轨迹中等间隔提取）。

### 10.4 能量验证

转换后**必须**验证 AMBER 和 GROMACS 给出的能量一致：

```bash
# GROMACS 单点能量
gmx grompp -f energy_check.mdp -c pftrps_ain.gro -p pftrps_ain.top -o energy_check.tpr
gmx mdrun -s energy_check.tpr -nsteps 0 -rerun pftrps_ain.gro
```

比较 AMBER 和 GROMACS 的：
- 键能 (bond energy)
- 角能 (angle energy)
- 二面角能 (dihedral energy)
- van der Waals 能
- 静电能

> **预期差异**：由于 AMBER 和 GROMACS 处理 1-4 相互作用的方式略有不同，总能量可能有 ~0.1-1.0 kcal/mol 的差异。这是正常的。如果差异 > 10 kcal/mol，说明转换有问题。

### 10.5 非标准残基的已知痛点

ParmEd 在处理非标准残基（如 LLP）时可能遇到的问题：

| 问题 | 表现 | 解决方案 |
|------|------|---------|
| **原子类型映射失败** | GROMACS 拓扑中出现未知原子类型 | 手动检查 .top 文件中的 `[ atomtypes ]` 部分 |
| **1-4 scaling factor 不一致** | 能量差异大 | AMBER ff14SB 的 1-4 EE scaling = 1/1.2, 1-4 VDW = 1/2.0，确认 GROMACS top 中一致 |
| **水模型不匹配** | 密度偏差 | 确保 GROMACS 用的是和 AMBER TIP3P 参数一致的水 |
| **残基名识别问题** | GROMACS 不认识 LLP | 在 .top 中手动定义或确认 ParmEd 正确处理了 |

---

## 第十一章：Gaps 与 PI 会议准备

### 11.1 SI 缺失信息汇总

| # | 缺失信息 | 严重性 | 影响什么 | 建议解决方案 |
|---|---------|--------|---------|-------------|
| 1 | **PLP 各中间体的质子化状态** | **Critical** | RESP 电荷、总电荷、整个力场 | 查 PLP 酶文献 (Toney 2011)；采用 pH 7.5 标准态；和 PI 确认 |
| 2 | **Capping 策略 (ACE/NME)** | High | RESP 电荷质量 | 使用标准 ACE/NME；几乎确定 Osuna 也是这么做的 |
| 3 | **总电荷和自旋多重度** | **Critical** | Gaussian 计算正确性 | 取决于质子化状态决策（见 #1） |
| 4 | **A-A 和 Q2 的初始结构来源** | High | 没有晶体结构怎么建模 | 可能从其他物种 PDB (4HPX) 修改；或者从 Aex1 手动脱水 |
| 5 | **AMBER → GROMACS 转换方法** | Medium | 能量一致性 | 用 ParmEd；标准做法但 SI 没说 |
| 6 | **mol2/frcmod 文件** | High | 无法直接复刻 | 自己计算；如果结果不确定，考虑联系 Osuna 组 |
| 7 | **PLP 在 tleap 中的处理方式** | Medium | 共价键连接 | lib 文件或 PREP 文件；标准 AMBER 做法 |
| 8 | **IGP/G3P 参数** | Low (Phase 1 不需要) | TrpA 的底物参数 | 同样的 GAFF+RESP 流程 |
| 9 | **Gaussian 优化是否冻结主链** | Medium | RESP 电荷 | 通常不冻结（cap 会限制主链变形）；但 SI 没说 |

### 11.2 需要 PI 决策的问题（按优先级排序）

**Priority 1: 必须在开始计算前确定**

| # | 问题 | 推荐答案 | 备选答案 | 需要 PI 说什么 |
|---|------|---------|---------|---------------|
| 1 | Ain 中间体的总电荷是 -1 还是 -2？ | -1（Schiff base 质子化） | -2（去质子化） | 同意/不同意/查文献 |
| 2 | 磷酸是 -1 还是 -2？ | -2（pH 7.5 下双阴离子） | -1（单阴离子） | 同意/不同意 |
| 3 | Phase 1 只做 Ain 还是同时做 Aex1？ | 先只做 Ain | 同时做 | 效率 vs 完整性 |

**Priority 2: 可以在计算过程中决定**

| # | 问题 | 推荐答案 | 备选答案 |
|---|------|---------|---------|
| 4 | 用 GAFF 还是 GAFF2？ | GAFF2（更新，但 SI 说 GAFF） | GAFF（严格复刻） |
| 5 | Gaussian 几何优化后是否做 frequency check？ | 做（确认是最低点不是鞍点） | 不做（省时间，LLP 应该没问题） |
| 6 | 如果 RESP 电荷不合理怎么办？ | 调整质子化状态重算 | 用 AM1-BCC 替代 |

**Priority 3: 信息类（不需要决策，但建议提及）**

| # | 信息 | 状态 |
|---|------|------|
| 7 | Gaussian 16 vs 09 兼容性 | 已确认无影响 |
| 8 | Longleaf 上 AMBER/Gaussian/GROMACS 全部可用 | 已确认 |
| 9 | Alanine dipeptide toy test 通过 | 已完成，GROMACS+PLUMED2 验证可用 |

### 11.3 可以通过文献检索解决的问题

| 问题 | 推荐文献 | 预计结论 |
|------|---------|---------|
| PLP Schiff base 质子化态 | Toney 2011, Arch Biochem Biophys; Casasnovas 2014, JACS | Internal aldimine Schiff base N 质子化 (pKa ~10) |
| PLP 磷酸 pKa | Metzler & Snell, various; Eliot & Kirsch 2004, Ann Rev Biochem | 双阴离子 at pH 7.5 |
| RESP 电荷 PLP 的先例 | 搜索 "PLP RESP AMBER parameterization" in PubMed | 可能找到已发表的 PLP 参数 |

### 11.4 推荐会议议程

1. **5 min**：项目进度概述（alanine dipeptide 验证通过，PLP 参数化是下一步）
2. **10 min**：PLP 质子化状态讨论（本文档第五章，需要 PI 决策）
3. **5 min**：Phase 1 范围确认（只做 Ain 还是同时做 Aex1？）
4. **5 min**：时间线讨论（第十二章）
5. **5 min**：其他 SI gaps 的处理策略

---

## 第十二章：逻辑链总图

### 12.1 完整 Pipeline 可视化

```
┌─────────────────────────────────────────────────────────┐
│                    Phase 0: 准备                         │
│  PDB 文件 (5DVZ, 5DW0)  ←  已下载 ✅                     │
│  SI 参数提取             ←  已完成 ✅                     │
│  工具链验证 (alanine)    ←  已通过 ✅                     │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│           Step 1: PLP 参数化 [本文档重点]                 │
│                                                         │
│  5DVZ.pdb                                               │
│     │                                                   │
│     ├─ 提取 LLP 残基                                     │
│     │                                                   │
│     ├─ 加氢 + ACE/NME capping                            │
│     │                                                   │
│     ├─ antechamber → GAFF2 原子类型                      │
│     │                                                   │
│     ├─ Gaussian 16: HF/6-31G(d) Opt + ESP    ← ⏳ 2-8h  │
│     │                   │                               │
│     │       ┌───────────┘                               │
│     │       ▼                                           │
│     ├─ antechamber -c resp → mol2 (RESP 电荷)            │
│     │                                                   │
│     ├─ parmchk2 → frcmod (缺失参数)                      │
│     │                                                   │
│     └─ 验证: 电荷总和、原子类型、frcmod 无警告             │
│                                                         │
│  ⚠️ BLOCKER: 质子化状态 → 决定总电荷 → 需要 PI 确认       │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│              Step 2: tleap 体系组装                       │
│                                                         │
│  ff14SB + GAFF2 + TIP3P                                 │
│  + mol2 + frcmod (from Step 1)                          │
│  + PDB (蛋白质 + PLP)                                    │
│     │                                                   │
│     ├─ 加载力场和 PLP 参数                                │
│     ├─ 创建 lib 文件 (共价键定义)                          │
│     ├─ 溶剂化: TIP3P, cubic box, 10 A buffer             │
│     ├─ 中和电荷: Na+/Cl-                                 │
│     │                                                   │
│     └─→ parm7 + inpcrd                                  │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│          Step 3: 常规 MD (AMBER pmemd.cuda)               │
│                                                         │
│  Minimization (2 stages)            ← ~30 min           │
│     │                                                   │
│     ▼                                                   │
│  Heating (7 × 50 ps, 0→350 K)      ← ~1 h              │
│     │                                                   │
│     ▼                                                   │
│  Equilibration (2 ns NPT)          ← ~30 min            │
│     │                                                   │
│     ▼                                                   │
│  Production (500 ns NVT, 350 K)     ← ~4-6 天 (GPU)     │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│          Step 4: AMBER → GROMACS 转换                    │
│                                                         │
│  ParmEd: parm7 + rst7 → .top + .gro                    │
│  能量验证: AMBER vs GROMACS 单点能差 < 1 kcal/mol        │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│          Step 5: 准备好，可以开始 MetaDynamics ✓          │
│                                                         │
│  输入文件:                                               │
│  - pftrps_ain.top (GROMACS topology)                    │
│  - pftrps_ain.gro (坐标)                                │
│  - plumed.dat (CV 定义, 来自 15-frame path)              │
│  - md.mdp (GROMACS MD 参数)                              │
│                                                         │
│  → Well-tempered MetaD, 10 walkers × 50-100 ns          │
└─────────────────────────────────────────────────────────┘
```

### 12.2 依赖图

```
质子化状态决策 ─────┐
                    │
PDB (5DVZ) ─────── ├──→ Gaussian RESP ──→ mol2 + frcmod ─┐
                    │                                      │
ACE/NME capping ───┘                                      │
                                                           │
ff14SB ──────────────────────────────────────────┐         │
TIP3P ───────────────────────────────────────────┤         │
PDB (1WDW, chain A+B) ──────────────────────────┤         │
                                                 ├──→ tleap → parm7 + inpcrd
mol2 + frcmod (from RESP) ──────────────────────┘
                                                               │
                                                               ▼
                                                     AMBER MD (500 ns)
                                                               │
                                                               ▼
                                                     ParmEd → GROMACS
                                                               │
                                                               ▼
15-frame path (1WDW → 3CEP) ─────────────────────→ MetaDynamics
```

### 12.3 预计时间线

| 任务 | 前置条件 | 预计耗时 | 累计 |
|------|---------|---------|------|
| PI 确认质子化状态 | 本文档 | 1 次会议 | Day 0 |
| 提取 LLP + 加氢 + capping | PI 决策 | 2-3 小时 (hands-on) | Day 1 |
| antechamber + Gaussian | 上一步 | 提交后等 2-8 小时 | Day 1-2 |
| RESP 电荷 + parmchk2 + 验证 | Gaussian 完成 | 1-2 小时 | Day 2 |
| tleap 体系组装 | mol2 + frcmod | 2-3 小时 | Day 2-3 |
| 最小化 + 加热 + 平衡 | parm7 + inpcrd | 提交后等 ~2 小时 | Day 3 |
| 500 ns 产出 MD | 平衡完成 | 4-6 天 (GPU) | Day 4-10 |
| AMBER → GROMACS 转换 + 验证 | MD 完成 | 2-3 小时 | Day 10 |
| **总计** | | **~10 天** (含 GPU 排队) | |

> **注意**：这是"一切顺利"的时间线。实际操作中，tleap 报错、电荷不平衡、能量验证不通过等问题可能让每一步多花 1-2 天。保守估计应该预留 **2-3 周**。

### 12.4 复刻容差

最终标准：我们的 MetaDynamics FEL 和 Osuna 发表的 FEL 相比：

| 指标 | 容差 | 来源 |
|------|------|------|
| 能垒高度差异 | **< 1.5 kcal/mol** | Well-tempered MetaD 的典型统计误差 |
| 能量盆位置 (s(R)) | **< 1 单位** | 15-frame path 的分辨率 |
| Open/PC/C 相对稳定性定性一致 | 必须一致 | 定性结论不能变 |

---

> **最后一句话**：这份文档覆盖了从 PDB 到 MetaDynamics-ready 体系的所有逻辑和细节。最大的不确定性是 PLP 的质子化状态（第五章），这需要 PI 确认。一旦质子化状态确定，后续步骤都是标准操作，可以按本文档的脚本执行。
