# 名词解释 / Glossary

> 本文件是项目内所有缩写、专有名词、软件名、PDB 编号的统一查阅表。
> 如果你是 AI agent 并且遇到不认识的术语，先来这里查。

---

## 酶和蛋白相关

| 术语 | 全称 | 一句话解释 |
|------|------|-----------|
| TrpS | Tryptophan Synthase | 色氨酸合酶全酶复合物，αββα 四聚体 |
| TrpA | α-subunit | 催化 IGP → 吲哚 + G3P 的裂解反应 |
| TrpB | β-subunit | 催化吲哚 + L-Ser → L-Trp 的缩合反应（PLP 依赖）|
| *Pf*TrpB | *Pyrococcus furiosus* TrpB | 嗜热古菌来源的 TrpB，本项目的主要研究对象 |
| *Pf*TrpB⁰ᴮ² | *Pf*TrpB 0B2 variant | Arnold 实验室定向进化得到的独立功能变体（6 个突变）|
| LBCA TrpB | Last Bacterial Common Ancestor TrpB | 祖先序列重建得到的 TrpB，具有天然独立功能 |
| ANC3 TrpB | Ancestral Node 3 TrpB | 系统发育树第三个节点，依赖 TrpA 变构激活 |
| SPM6 TrpB | SPM-designed 6-mutation variant | Osuna 实验室用 SPM+ASR 方法设计的 ANC3 变体 |
| COMM domain | Communication Domain | TrpB 残基 97–184（PfTrpB 编号，对应 StTrpB 102–189）；这是 JACS 2019 Path CV 的原子选择范围（含经典 COMM 域 + 相邻残基），经历 O→PC→C 构象转换 |
| H6 helix | α-helix H6 | COMM domain 中的关键螺旋（残基 164–174），参与吲哚结合 |
| PLP | Pyridoxal 5'-phosphate | 磷酸吡哆醛辅酶，通过 Schiff 碱共价连接 K82 |

## 反应中间体

| 缩写 | 全称 | COMM 状态 | 说明 |
|------|------|----------|------|
| E(Ain) | Internal aldimine | Open | PLP-K82 Schiff 碱，静息态 |
| E(Aex1) | External aldimine 1 | PC | L-Ser 取代 K82，形成新 Schiff 碱 |
| E(A-A) | Aminoacrylate | Closed | 消除水后的亲电中间体，等待吲哚进攻 |
| E(Q₂) | Quinonoid 2 | Closed | 吲哚偶联后的醌类中间体 |
| E(Trp) | Product complex | PC | L-Trp 产物释放前 |

## 构象状态

| 缩写 | 含义 | s(R) 范围 |
|------|------|----------|
| O | Open（开放态）| 1–5 |
| PC | Partially Closed（半闭合态）| 5–10 |
| C | Closed（闭合态）| 10–15 |

## 模拟方法

| 术语 | 全称 | 一句话解释 |
|------|------|-----------|
| MD | Molecular Dynamics | 分子动力学模拟 |
| MetaD / MetaDynamics | Metadynamics | 增强采样方法，用 Gaussian 偏置势填平能垒 |
| WT-MetaD | Well-Tempered MetaDynamics | 收敛版 MetaD，Gaussian 高度随时间衰减 |
| FEL / FES | Free Energy Landscape / Surface | 自由能面（s 和 z 组成的二维能量地图）|
| Path CV | Path Collective Variable | s(R) = 沿路径进度，z(R) = 偏离路径距离 |
| Bias factor (γ) | — | 控制 Gaussian 高度衰减速率的参数（本项目 γ=10）|
| Multiple walkers | — | 多个 replica 同时跑 MetaD 并共享 bias |
| SPM | Shortest Path Map | 基于相关性的变构通路识别工具（Dijkstra 算法）|
| LiGaMD | Ligand Gaussian Accelerated MD | Miao Lab 开发的配体增强采样方法（之前做过）|

## 力场和软件

| 术语 | 含义 |
|------|------|
| ff14SB | AMBER ff14SB 蛋白力场 |
| GAFF | General AMBER Force Field（小分子/辅酶）|
| RESP | Restrained Electrostatic Potential（电荷拟合方法）|
| TIP3P | 三位点水模型 |
| PME | Particle-Mesh Ewald（长程静电处理）|
| SHAKE | 固定含氢键长的约束算法 |
| AMBER | 分子动力学软件包 |
| GROMACS | 分子动力学软件包（本项目 MetaD 引擎）|
| PLUMED | 增强采样插件（接 GROMACS 使用）|
| antechamber | AmberTools 中生成小分子拓扑的工具 |
| cpptraj | AmberTools 中的轨迹分析工具 |
| CAVER | 隧道分析软件 |

## PDB 结构

| PDB ID | 内容 | 在项目中的角色 |
|--------|------|---------------|
| 1WDW | *Pf*TrpS（αβ 复合物，Open） | 起始结构 + Path CV Open 端点 |
| 3CEP | *St*TrpS（Q analogue，Closed） | Path CV Closed 端点 |
| 5DVZ | *Pf*TrpB（Ain，Open） | RMSD 参考 |
| 5DW0 | *Pf*TrpB（Aex1，PC） | 结构对比 |
| 5DW3 | *Pf*TrpB（L-Trp product，PC） | 结构对比 |
| 4HPX | *St*TrpS（A-A benzimidazole，Closed） | CAVER 分析参考 |
| 5IXJ | *Pf*TrpB（Ain，L-Thr） | Ser/Trp 初始构象来源 |

## Pipeline 阶段

| 阶段 | 角色 | 对应工具 |
|------|------|---------|
| Profiler | 定义研究问题、冻结 manifest | Cowork |
| Librarian | 收集资源、验证完整性 | Cowork |
| Janitor | 准备模拟输入文件 | Claude Code Terminal |
| Runner | 执行模拟 | Longleaf HPC |
| Skeptic | 验证结果 | Cowork / Terminal |
| Journalist | 写报告 | Cowork |

## 常见缩写

| 缩写 | 全称 |
|------|------|
| HPC | High-Performance Computing |
| Slurm | Simple Linux Utility for Resource Management |
| NVT | Canonical ensemble（恒温恒容）|
| NPT | Isothermal-isobaric ensemble（恒温恒压）|
| RMSD | Root Mean Square Deviation |
| MSD | Mean Square Displacement |
| SI | Supporting Information |
| DE | Directed Evolution |
| ASR | Ancestral Sequence Reconstruction |
| MSA | Multiple Sequence Alignment |
