# JACS 2019 Reading Notes
> Maria-Solano et al., JACS 2019, 141(33), 13049-13056
> DOI: 10.1021/jacs.9b03646 | Zotero key: JKPAIETQ

## 这篇讲了什么（3 句话）
通过 MetaDynamics 模拟分析了野生型 TrpB (PfTrpS αβ复合体、孤立 PfTrpB) 与进化出来的独立活性变体 (PfTrpB0B2) 在催化过程中的构象动力学差异。PfTrpB0B2 通过 6 个 DE 突变恢复了 COMM 域的构象灵活性，使其能够有效关闭并完成产物转移。SPM 方法成功预测了关键功能突变位点，说明可以从动力学轨迹中直接识别功能性残基。

## 关键方法和数字

### 研究体系
- 3 个蛋白体系：PfTrpS (αβ complex)、PfTrpB (wild-type, isolated)、PfTrpB0B2 (evolved stand-alone)
- 4 个催化中间体：E(Ain)、E(Aex1)、E(A-A)、E(Q2)
- 总计 12 次 MetaDynamics 运行 (3 系统 × 4 中间体)

### COMM 域 (residues 97-184)
- 三种构象：Open (O)、Partially Closed (PC)、Closed (C)
- α-helix H6 (residues 164-174) 与吲哚直接相互作用

### MetaDynamics 自由能景观 (FEL)
**PfTrpS(Ain):**
- O 高度有利，PC ~2 kcal/mol 较高，O→PC 势垒 ~3 kcal/mol

**PfTrpS(Q2):**
- O 和 PC 稳定性接近，C ~5 kcal/mol 较高，PC→C 势垒 ~6 kcal/mol

**PfTrpB(Q2) - 孤立后异常**
- 限制景观，每阶段单一能量最小值
- C 态"非生产性"(RMSD > 1.5 Å from reference path)
- K82-Q2 距离 = 3.9±0.3 Å (过长)

**PfTrpB0B2(Q2) - 进化变体恢复能力**
- 恢复 O/PC/C 异质性
- O→PC→C 势垒仅 ~2 kcal/mol
- C 态与 PfTrpS productive closure 很好对齐
- K82-Q2 ≈ 3.6 Å (与 PfTrpS 可比)

### 生产性关闭定义
- COMM 域 RMSD < 1.5 Å from O→C conformational path
- K82-Q2 质子转移距离 ≤ 3.6 Å
- E104-Q2 距离也被追踪

### Shortest Path Map (SPM) 分析
- 应用于 PfTrpS(Q2) MetaDynamics 轨迹
- PfTrpB0B2 含 6 个 DE 突变：P12L, E17G, I68V, T292S, F274S, T321A
- SPM 直接预测：P12L、E17G (2/6)
- SPM 与以下相互作用：I68V、F274S、T292S (3/6)
- 未捕获：T321A (1/6)
- 总命中率：5/6

### kcat 数据
| 体系 | kcat (s⁻¹) |
|------|-----------|
| PfTrpB0B2 | 2.9 |
| PfTrpS complex | 1.0 |
| PfTrpB isolated | 0.31 |
| PfTrpB0B2 + PfTrpA | 0.04 |

### PDB 结构坐标
- 5DVZ: holo TrpB, PfTrpB (Ain, Open)
- 5DW0: TrpB with L-Ser external aldimine (Aex1, PC)
- 5DW3: TrpB with L-Trp product (E(Trp), PC, pre-release)
- 4HN4, 3CEP: Closed states post E(A-A)
- 1V8Z: Resting state (Ain, Open)

## 对我的项目意味着什么

**Benchmark 复刻**
- 这个工作是 TrpB 构象动力学研究的标准参考。需要复现这 12 次 MetaDynamics 运行，确认 PfTrpB0B2 的 FEL 确实比 PfTrpB 更有利。

**构象过滤标准**
- Productive closure 的两个准则（RMSD < 1.5 Å from reference path + K82-Q2 ≤ 3.6 Å）将成为评估生成序列的核心过滤器。所有新序列都需要通过这两个标准才能算"功能性"。

**生成模型评分函数**
- SPM 方法证明可以从 MD 轨迹中直接识别功能残基，不需要序列对齐。这对 TrpB generative pipeline 的打分机制很重要：可能可以用动力学签名而不仅仅依赖序列相似度。

**突变策略参考**
- PfTrpB0B2 的 6 个突变位点可作为参考，看看是否有通用的"恢复 COMM 柔性"的突变模式。

## 还不确定的地方

- **MetaDynamics 技术细节**：主文本未给出 PLUMED 输入文件、偏差因子、Gaussian 高度、采样速率。都在 SI 里，需要单独下载。
- **PLP 参数化**：蛋白质中含有共价结合的吡哆醇，参数化细节在 SI，不确定是否使用标准 AMBER 参数或自定义力场。
- **CV 路径定义**：z-variable (reference O→C path) 的确切定义需要 SI 确认。是从平均结构导出的？还是从 ensemble 提取的？
- **力场版本**：AMBER 版本、具体力场版本 (ff14SB?) 在 SI。
- **SPM 方法细节**：引用 Romero-Rivera et al., ACS Catal 2017 (ref 12)，原始论文需要查看以理解SPM算法逻辑。

## 复刻所需的具体材料

### PDB 坐标
- ✓ 5DVZ, 5DW0, 5DW3, 4HN4, 3CEP, 1V8Z (公开可得)

### 模拟软件 & 参数
- [ ] SI 文件：exact PLUMED 输入、AMBER 版本、force field 参数、PLP 参数化
- [ ] AMBER 16+ 或 GROMACS (需要 SI 确认)
- [ ] PLUMED 2.x (exact version in SI)

### 参考论文
- [ ] Romero-Rivera et al., ACS Catal 2017, ref 12 (SPM 方法细节)

### 已确认的参数
- ✓ 12 个 MetaDynamics 运行配置 (3 系统 × 4 中间体)
- ✓ 2 个 Path CV：s(R) = 沿 O→C 路径进度 (1=open, 15=closed)，z(R) = 偏离参考路径的均方偏差
- ⚠️ K82-Q2 distance 和 E104-Q2 distance 是**监测指标**，不是 MetaD 偏置的 CV
- ✓ Productive closure 阈值：RMSD < 1.5 Å from O→C path, K82-Q2 ≤ 3.6 Å

### 待查项
- [ ] 是否有公开发布的 PLUMED 输入、拓扑文件、力场参数文件？(需要写信给作者或查看补充数据库)
- [ ] PfTrpB0B2 的准确序列与 wild-type PfTrpB 的突变位点确认 (可能在 SI Table)
