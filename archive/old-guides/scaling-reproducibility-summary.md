# Scaling Reproducibility 论文与 TrpB 项目

## 论文核心观点

论文题目：*Scaling Reproducibility: An AI-Assisted Workflow for Large-Scale Reanalysis*

**一句话总结**：复杂科学工作流可以规模化，当且仅当：
1. 研究问题冻结成明确的模板
2. 执行分解成模块化的阶段
3. 反复出现的问题被记录为可重用的规则

## 为什么对 TrpB 项目重要

现有风险：
- 论文笔记 → 假设 → 筛选规则，步步放大不确定性
- Benchmark 校准 vs 下游管道集成，界线模糊
- 失败模式反复出现但未被系统记录

论文解决方案：
- **冻结边界**：明确区分"科学模板"、"执行"、"下游使用"
- **模块化阶段**：每个阶段有明确的输入输出和失败检查
- **知识积累**：每次解决问题，记录通用修复方案

## 6 阶段管道映射

| 阶段 | 输入 | 输出 | 关键约束 |
|---|---|---|---|
| **1-Profiler** | 论文、周报、笔记 | frozen campaign manifest | 明确事实 vs 假设 vs 未解决 |
| **2-Librarian** | DOI、PDB IDs、补充资料 | 资源清单（已有/缺失/受限） | 权威来源优先 |
| **3-Janitor** | 散乱的工作目录 | 标准化的 campaign 目录树 | 输入输出分离 |
| **4-Runner** | frozen manifest | 可执行命令、日志、工件 | 验证梯（toy→benchmark→对比→筛选） |
| **5-Skeptic** | 运行输出 | 操作/科学/集成状态报告 | 区分三种"成功" |
| **6-Journalist** | 所有上述工件 | campaign 报告、交接说明 | 事实、具体、可验证 |

## 关键区分：三种"成功"

1. **操作成功**：文件存在，无错误 ✓ 但可能科学有问题
2. **科学成功**：结果与 frozen campaign 一致 ✓ 但可能下游无法用
3. **集成就绪**：导出特征可追溯，下游声明有根据 ✓ 真的可以用

## 对 TrpB 项目的直接适用

现在可以自动化：
- Profiler：论文 → manifest
- Librarian：清点 PDB、论文补充资料
- Janitor：组织 campaign 目录
- Runner：生成命令计划（即使 HPC 不可用）
- Journalist：写活动报告

不应该自动化（需人工判断）：
- Profiler 的"这是假设还是事实"判断
- Skeptic 的"这个 CV 是否真的捕捉生物学"判断
- Journalist 的"下游声明是否正当"判断

## 最重要的教训

**不是"让 AI 做一切"，而是"建立科学、执行、使用之间的版本化边界"。**

这对 TrpB 项目至关重要，因为主要风险不是运行时失败，而是从 benchmark 校准悄悄滑入缺乏根据的筛选声明。
