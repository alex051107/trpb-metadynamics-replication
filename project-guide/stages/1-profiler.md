# 阶段 1：Profiler（分析器）

## 功能

把论文、周报、项目笔记转换成结构化的 campaign manifest（活动方案定义）。

## 何时使用

- 有新的论文或参考资料需要转换成可执行的计划
- 需要从非结构化的笔记中提取科学要点
- 需要明确区分"明确事实"、"推断"、"假设"、"未解决的问题"

## 输入

- 论文 PDF 或摘要
- 周报 / weekly reports
- MetaDynamics_Setup_Notes.md
- 项目规划文档或流程图

## 输出

选择以下之一：
- 更新的 campaign manifest (YAML)
- metric specification note（指标定义说明）
- fact-vs-hypothesis note（事实 vs 假设清单）
- comparison brief（对比方案简述）

## 关键规则

1. **分离显式事实和推断**：不要将猜测的参数升级为确认的参数
2. **保留不确定性标签**：每项事实标记为：explicit（明确）/ inferred（推断）/ hypothesis（假设）/ unresolved（未解决）
3. **记录冲突**：多个本地文档有矛盾时要明确指出
4. **命名下游消费者**：不只是问科学问题，要说明"谁会使用这个结果"
5. **人工审查必需**：输出必须经过人工验证

## 工作流程

1. 阅读源材料
2. 提取关键信息：
   - campaign mode（活动模式：benchmark_reproduction / mechanism_comparison / physics_filter / surrogate_bootstrap）
   - research question（研究问题）
   - systems under study（被研究的体系）
   - reference structures（参考结构）
   - CV design（CV设计）
   - software stack（软件栈）
   - measurable readouts（可测指标）
   - validation criteria（验证标准）
   - downstream consumer（下游使用者）
3. 对每项内容标记来源（明确/推断/假设/未解决）
4. 写入 manifest 或活动笔记
