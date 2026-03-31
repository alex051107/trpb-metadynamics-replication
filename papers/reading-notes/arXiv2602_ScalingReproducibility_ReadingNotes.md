# arXiv 2602.16733 Reading Notes
> Xu & Yang, arXiv 2602.16733v2 (Feb 2026, revised Mar 2026)
> "Scaling Reproducibility: An AI-Assisted Workflow for Large-Scale Replication and Reanalysis"

## 这篇讲了什么（3 句话）
作者开发了一套自动化工作流，用于大规模验证学术论文的计算可重复性。他们测试了 384 篇政治学论文（2010-2025），包含 3,382 个回归模型，发现有数据存档要求后可重复率从 29.6% 升至 79.8%。核心架构是三层分离：协调层（LLM 调度）、技能层（结构化输入输出）、执行层（确定性计算）。

## 关键架构

### 三层设计
| 层 | 做什么 | 关键原则 |
|---|---|---|
| **Layer 1: 协调** | LLM 调度任务、解释错误 | 自适应但不做数值计算 |
| **Layer 2: 技能** | 定义输入输出契约，记录已解决的失败模式 | 结构化、可重用 |
| **Layer 3: 执行** | 文件操作、统计脚本、回归捕获 | 确定性，不参与数值估计 |

### 三阶段执行流程
| Phase | 做什么 | 产出 |
|---|---|---|
| **A: 获取与执行** | 从 PDF 提取元数据 → 下载复刻包 → 修路径 → 跑代码 | 运行日志、回归输出 |
| **B: 可重复性验证** | 提取系数 → 精度感知匹配 → 分类 | fully/largely/partially/not reproducible |
| **C: 诊断评估** | 识别研究设计 → 应用诊断模板（如 IV 的 F-stat, Anderson-Rubin） | 标准化诊断报告 |

### 三个分离原则（最重要的设计思想）
1. **自适应协调 ≠ 固定计算**：LLM 调度，但不做数学
2. **科学推理 ≠ 执行**：跑通代码 ≠ 重现结果
3. **执行 ≠ 验证**：代码运行成功 ≠ 论文可重复

> "Running an author's code successfully does not by itself establish that the paper's reported results have been reproduced."

## 关键数字

### 可重复性测试（384 篇论文）
| 指标 | 数值 |
|------|------|
| 测试论文总数 | 384 篇（APSR, AJPS, JOP, 2010-2025） |
| 回归模型数 | 3,382 个 |
| 执行脚本数 | 2,012 个 |
| 有复刻包 | 275/384 (71.6%) |
| 数据可访问 | 251/384 (65.4%) |
| 完全可重复（数据可用时）| 237/251 (**94.4%**) |
| DA-RT 前可重复率 | 29.6% [95% CI: 22.1%-37.0%] |
| DA-RT 后可重复率 | 79.8% [95% CI: 74.6%-84.9%] |

### 运行性能
| 场景 | 时间 |
|------|------|
| 无复刻包 | <2 min（中位数）|
| 完整执行（下载+运行+提取+匹配）| <10 min |
| 最复杂代码库 | ~1 hour |

### IV 诊断扩展（92 篇论文，215 个 IV specification）
- 自主成功率：82%（55/67 篇原始论文）
- 条件成功率（数据可用时）：**100%**
- 2SLS/OLS 比值中位数：**3.0x**（2SLS 系统性放大 OLS 估计）

## 失败模式分布
| 失败原因 | 论文数 |
|----------|--------|
| 缺失复刻包 | 109 |
| 数据受限/不可访问 | 24 |
| 代码执行失败 | 14 |
| 可修复的编码错误 | 10（被系统自动修复）|

## 失败编码机制
> "When a recurring failure pattern is identified, it is encoded as a generalized rule in the execution layer and version-controlled between runs."

这就是"知识积累"：每次遇到新的失败模式（比如"路径用了 Windows 反斜杠"），修复后记录为通用规则，下次自动避免。

## 精度感知匹配方法
- 将代码输出的系数四舍五入到论文报告的相同小数位数
- 使用最优一对一分配（optimal assignment）匹配每个报告值
- 比简单的"差值 < 阈值"更严格但更公平

## 对我项目的映射

| 论文概念 | 我的 TrpB 项目等价物 |
|----------|---------------------|
| PDF 元数据提取 | **Profiler**: 从 JACS 2019 提取 MetaD 参数 |
| 下载复刻包 | **Librarian**: 下载 PDB、SI、检查资源 |
| 修路径和环境 | **Janitor**: 整理 AnimaLab 目录 |
| 执行代码 | **Runner**: 提交 Slurm 作业到 Longleaf |
| 精度感知匹配 | **Skeptic**: FEL 能垒 ±1.5 kcal/mol 验证 |
| 诊断报告 | **Journalist**: Campaign report |
| 失败编码 | CHANGELOG.md 里的"遇到的问题"表 |
| 三种分离 | Manifest（科学）→ Script（执行）→ Validation（验证）|

## 跟 TrpB 项目的关键区别

1. **论文处理的是统计代码**（R/Stata），我处理的是**分子动力学模拟**（GROMACS/AMBER/PLUMED）
2. **论文的验证是精确数值匹配**，我的验证是**物理量趋势匹配**（能垒高低、basin 位置）
3. **论文可以全自动跑完**（<10 min/论文），我的**一次模拟就需要几天到几周**
4. **论文的失败是代码级别的**（路径错、包缺失），我的失败可能是**物理级别的**（CV 选错、采样不足）

## 最重要的 takeaway

> **版本化边界**：科学决策（manifest）、执行决策（scripts）、下游声明（validation）必须分开管理、分开版本控制。

这不是"让 AI 做一切"，而是"让 AI 在明确边界内执行，人类在边界处审批"。
