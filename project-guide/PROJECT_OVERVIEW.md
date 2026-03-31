# TrpB MetaDynamics Project — 总览

> 最后更新：2026-03-26 · 这份文档是整个项目的唯一入口。
> 面试回顾、AI 工具调用、日常推进都从这里开始。

---

## 一句话概括

用 MetaDynamics（增强采样）作为物理层，解释和筛选 TrpB 生成式设计 pipeline 产出的候选序列。

---

## 我在做什么

Anima Lab（Caltech, Frances Arnold 组）用大语言模型（GenSLM）生成了大量 TrpB 变体序列。其中一个叫 GenSLM-230 的候选，预测结构和天然同源物 NdTrpB 几乎一样（backbone RMSD 0.36 Å），但活性完全不同。

静态结构解释不了这个差异。**我的假设是：差异来自构象动力学**——具体来说是 COMM 结构域（残基 97–184）从 Open 到 Closed 的构象转变。MetaDynamics 可以算出这个转变的自由能景观，从而解释哪些序列能"生产性关闭"（productive closure），哪些不能。

长远目标是把 MetaDynamics 的输出变成一个可量化的筛选标准（conformational filter），集成进生成式 pipeline。

---

## 项目路线图

```
阶段 0: 读论文，理解方法     ← 你现在在这里
   ↓
阶段 1: 复刻 Osuna 2019 benchmark（验证工具链能跑通）
   ↓
阶段 2: GenSLM-230 vs NdTrpB 比较（回答科学问题）
   ↓
阶段 3: D-Trp conformational filter 设计（应用到 pipeline）
   ↓
阶段 4: 导出特征给代理模型（规模化）
```

每个阶段的详细说明见 `project-guide/stages/` 文件夹。

---

## 论文阅读通路

按顺序读。每篇论文回答一个具体问题，读完产出一份 reading note。

### 必读（按顺序）

| # | 论文 | 读完得到什么 | 为什么需要 | 对 pipeline 的作用 |
|---|------|------------|-----------|-------------------|
| 1 | **JACS 2019** — Maria-Solano et al., "Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution" | MetaDynamics 在 TrpB 上的完整实现：path CV 定义（s-axis/z-axis）、productive closure 判据（RMSD < 1.5 Å, K82-Q2 ≤ 3.6 Å）、FEL 的解读方式 | **这是你要复刻的那篇。** 不读这篇，后面所有工作都没有基础 | 提供 benchmark 的全部参数和成功判据 |
| 2 | **ACS Catal 2021** — Maria-Solano et al., "In Silico Identification and Experimental Validation of Distal Activity-Enhancing Mutations" | SPM（Shortest Path Map）分析、定向进化位点预测、突变如何改变 COMM 动力学 | 理解"动力学信息怎么指导序列设计"——这正是你的 pipeline 要做的事 | 验证 MetaDynamics → 序列设计 这条路是可行的 |

### 选读（按需要）

| # | 论文 | 什么时候读 | 得到什么 |
|---|------|----------|---------|
| 3 | **NatComm 2026** — Lambert, Tavakoli et al. | 需要理解 GenSLM pipeline 整体时 | 生成式 pipeline 的完整架构、230 vs NdTrpB 的实验数据 |
| 4 | **Protein Science 2025** — Kinateder et al. | 需要理解独立 TrpB 的别构通讯时 | 不依赖 TrpA 的 TrpB 的构象行为 |
| 5 | **WIREs 2020** — MetaDynamics 方法综述 | 需要补方法论基础时 | well-tempered MetaDynamics、path CV、bias factor 的原理 |

### 论文阅读产出

每篇论文读完后，在 `papers/reading-notes/` 里写一份 .md 文件，格式固定：

```markdown
# [论文简称] Reading Notes

## 这篇讲了什么（3 句话）
## 关键方法和数字
## 对我的项目意味着什么
## 还不确定的地方
```

深度标注（HTML 格式）放在 `papers/annotations/`，用 paper-annotation skill 生成。

---

## 复刻体系：六阶段流水线

这套体系来自 *Scaling Reproducibility*（arXiv 2602.16733）的架构，核心原则：

> **科学决定、执行决定、下游集成声明，三件事必须分开。**

为什么要分开？因为 MetaDynamics 最大的风险不是"跑不起来"，而是"跑起来了但结论不可信"——参数是猜的、成功判据是主观的、CV 定义是借的、然后结果就直接被拿去筛序列。

### 流水线总览

```
┌─────────────────────────────────────────────────────┐
│  Profiler                                           │
│  输入：论文 + 周报 + 笔记                              │
│  输出：campaign_manifest.yaml（冻结所有科学决定）        │
│  规则：manifest 冻结后，run 期间不能改                   │
│  详见：project-guide/stages/1-profiler.md             │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Librarian                                          │
│  输入：DOI、PDB ID、SI 链接                            │
│  输出：资源清单（有什么、缺什么、去哪里拿）                 │
│  规则：缺就写缺，不猜不跳过                              │
│  详见：project-guide/stages/2-librarian.md            │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Janitor                                            │
│  输入：下载的文件 + 现有目录                             │
│  输出：标准化工作目录、changelog                         │
│  规则：原始输入、生成 artifact、导出特征分开放             │
│  详见：project-guide/stages/3-janitor.md              │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Runner                                             │
│  输入：冻结的 manifest + 整理好的工作目录                 │
│  输出：命令列表、Slurm 脚本、运行日志                     │
│  规则：按 validation ladder 走——                       │
│        toy → benchmark → comparison → filter          │
│        不能跳步，没有磁盘 artifact 不算成功               │
│  详见：project-guide/stages/4-runner.md               │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Skeptic                                            │
│  输入：运行输出 + manifest                              │
│  输出：验证报告                                        │
│  规则：区分三种"成功"——                                 │
│        环境成功 ≠ 科学成功 ≠ 可以往下游传                 │
│  详见：project-guide/stages/5-skeptic.md              │
└──────────────────────┬──────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────┐
│  Journalist                                         │
│  输入：验证报告 + manifest                              │
│  输出：campaign 总结报告                                │
│  规则：每次结束都有可追踪的书面记录                        │
│  详见：project-guide/stages/6-journalist.md           │
└─────────────────────────────────────────────────────┘
```

### 什么时候用哪个阶段

| 你在做的事 | 用哪个阶段 |
|-----------|----------|
| 读完论文，想把参数整理成可执行计划 | Profiler |
| 确认 PDB 文件、SI、参数文件在不在 | Librarian |
| 准备开跑之前，整理目录结构 | Janitor |
| 写 Slurm 脚本、生成命令 | Runner |
| 跑完了，检查结果是否可信 | Skeptic |
| 写这次 campaign 的总结 | Journalist |

### Campaign Manifest（冻结文件）

每次开始新的 campaign 之前，必须先冻结一份 manifest，写清楚：

1. campaign 模式（benchmark / comparison / filter / surrogate）
2. 研究问题
3. 跑哪些系统
4. CV 定义
5. 软件栈（AMBER 版本、PLUMED 版本、力场）
6. 期望看到的 readouts
7. 成功判据
8. 结果给谁用
9. 已知 blockers

已有的 manifest 草稿在 `replication/manifests/`。

---

## 当前 Blockers（按优先级）

| # | Blocker | 状态 | 怎么解决 |
|---|---------|------|---------|
| 1 | JACS 2019 SI（PLUMED 输入文件） | 未下载 | 从 ACS 网站下载 SI，确认 PLUMED 文件完整 |
| 2 | PLP cofactor AMBER 参数 | 来源未确认 | 可能在 SI，否则联系 Osuna 组 |
| 3 | GenSLM-230 / NdTrpB 结构资产 | 等 Anima Lab | 阶段 2 才需要，暂不阻塞 |
| 4 | D-Trp 几何判据定义 | 未定 | 阶段 3 才需要 |

已解决：
- ✅ HPC：UNC Longleaf 账号可用

---

## 文件夹结构

```
tryp B project/
├── project-guide/          ← 你现在在看的这个文件夹
│   ├── PROJECT_OVERVIEW.md ← 这份文档（唯一入口）
│   ├── stages/             ← 六阶段的详细说明
│   └── templates/          ← manifest 模板、报告模板
│
├── papers/                 ← 论文相关
│   ├── annotations/        ← HTML 深度标注
│   └── reading-notes/      ← .md 阅读笔记（简明版）
│
├── replication/            ← 具体复刻工作
│   ├── manifests/          ← campaign manifest（冻结文件）
│   ├── inventories/        ← 资源清单
│   ├── runs/               ← 运行目录
│   ├── validations/        ← 验证报告
│   └── campaign-reports/   ← campaign 总结
│
├── reports/                ← 周报
├── 研究进展日志.md          ← 个人中文进展日志
└── archive/                ← 旧文件
```

---

## 工具使用指南

| 任务 | 用什么工具/skill |
|-----|----------------|
| 深度标注一篇论文（HTML 双栏格式） | paper-annotation skill |
| 快速理解一篇论文（tutor 模式） | paper-reading skill |
| 把论文信息整理成 campaign manifest | Profiler 阶段（见 stages/1-profiler.md） |
| 查 Zotero 里的论文 | Zotero MCP connector |
| 生成周报 | weekly-report skill（待创建） |
| 文献综述 | literature-review skill |

---

## 关键术语速查

| 术语 | 含义 |
|-----|------|
| COMM domain | TrpB 残基 97–184，控制底物通道开关的构象域 |
| O / PC / C | Open / Partially Closed / Closed，COMM 的三种构象状态 |
| Path CV | 路径集变量，s-axis 是沿 O→C 路径的进度，z-axis 是偏离路径的程度 |
| Productive closure | COMM RMSD < 1.5 Å（偏离参考路径）且 K82-Q2 ≤ 3.6 Å |
| FEL | Free Energy Landscape，MetaDynamics 算出的自由能面 |
| PLP | 磷酸吡哆醛，TrpB 的辅因子 |
| SPM | Shortest Path Map，从 FEL 提取的关键残基网络 |
| E(Ain) → E(Trp) | TrpB 催化循环的五个中间态 |
| Campaign manifest | 冻结所有科学决定的 YAML 文件，run 期间不能改 |
| Validation ladder | toy → benchmark → comparison → filter，必须按顺序走 |
