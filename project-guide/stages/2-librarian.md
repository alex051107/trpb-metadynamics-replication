# 阶段 2：Librarian（资源管理员）

## 功能

搜集和审计外部资源（PDB 结构、论文补充资料、候选资产、实验室参考资源）。

## 何时使用

- 需要下载 PDB 结构或论文补充信息
- 需要清点当前项目拥有的所有资源
- 需要确定哪些资源缺失或受限
- 需要为 benchmark 或对比活动构建资源清单

## 输入

- DOI 或论文标题
- PDB IDs
- supplementary URLs（补充资料链接）
- 实验室引用或资源清单

## 输出

选择以下之一：
- resource inventory note（资源清单说明）
- status table of available vs missing（可获得 vs 缺失状态表）
- explicit local file paths（明确的本地文件路径）
- provenance record（出处记录）

## 关键规则

1. **优先使用权威来源**：论文原始数据优于次级引用
2. **明确记录缺失**：不要猜测，直接说明"无法获取"
3. **优先级顺序**：paper → DOI → official databases
4. **区分可用性**：
   - 本地已有
   - 远程可获得
   - 无法获得或受限
5. **记录使用目的**：每项资源说明在当前活动中的具体作用

## 优先资源

对于 benchmark 活动：
- RCSB PDB entries
- 论文 supplementary methods
- Osuna lab pages
- PLUMED documentation

对于对比或筛选活动：
- lab 提供的序列/结构资产
- GenSLM-230、NdTrpB、候选蛋白的精确标识符
- assay summaries（实验总结）
- prior preparation scripts（前序脚本）

## 好的输出示例

- "这些结构已在本地；这些仍然缺失"
- "SI 链接存在但参数提取尚未确认"
- "此对比可以框架化，但候选特定资产仍缺失"
