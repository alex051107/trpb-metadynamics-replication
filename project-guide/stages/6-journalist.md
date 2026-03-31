# 阶段 6：Journalist（记者）

## 功能

写 campaign 报告：把工作流状态转换成清晰、可重用的研究记录。

## 何时使用

- campaign 需要总结
- 干运行或实际运行结束
- 需要为下一步记录阻碍
- 需要与团队或未来的自己共享进展

## 输入

- campaign manifest（frozen）
- run logs and outputs
- validation report from Skeptic
- progress notes

## 输出

选择以下之一（使用 campaign_report.template.md）：
- run report（运行报告）
- campaign report（活动报告）
- short status memo（简短状态备忘）
- weekly research note update（周报更新）
- reproducibility handoff note（可重现性交接说明）

## 关键规则

1. **分离计划和实际**：说清楚"计划做什么"和"实际发生了什么"
2. **具体引用工件**：提到具体的文件路径和输出
3. **明确标记阻碍**：哪些步骤完成了，哪些被卡住了
4. **记录即时后续行动**：下一步是什么
5. **失败模式学习**：如果学到新的失败模式，是否添加到知识库
6. **说明解释边界**：此证据支持什么声明，不支持什么

## 报告结构

按 campaign_report.template.md 组织：
1. Campaign Identity（ID、日期、模式）
2. Systems and Inputs（系统、manifest、软件栈）
3. Stage Reached（当前阶段、已执行的命令、生成的工件）
4. Validation（操作/科学/集成状态）
5. Interpretation Boundary（支持的声明、不支持的、未解决的假设）
6. Failure Analysis（根本原因、是否是反复出现的问题）
7. Next Action（下一步是什么）

## 语气

- 事实、简洁、操作向
- 避免猜测性语言
- 聚焦可验证的工件

## 非目标

- 不要创建虚假的完成感
- 不要隐藏失败或不确定性
