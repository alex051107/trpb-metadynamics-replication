# 阶段 4：Runner（执行器）

## 功能

从冻结的 campaign manifest 生成可执行的命令和分析步骤。

## 何时使用

- campaign 的科学模板已确定（frozen）
- 需要生成具体的命令列表或 Slurm 脚本
- 需要执行本地准备或分析步骤
- 需要收集实际运行的输出
- 需要导出特征表用于下游使用

## 输入

- frozen campaign manifest
- software stack specifications
- resource availability（本地/HPC）

## 输出

选择以下之一：
- staged command list（分阶段命令列表）
- Slurm job sketch（HPC 作业脚本）
- artifact checklist（工件检查清单）
- run folder with logs and outputs（包含日志和输出的运行文件夹）
- feature table with provenance（带来源的特征表）

## 验证阶梯（Validation Ladder）

按以下顺序执行，不要跳过：

1. toy 或 tutorial 增强采样验证
2. published TrpB benchmark 重现
3. pairwise comparison campaign
4. candidate-filter 或 surrogate-export batch

## 关键规则

1. **从 manifest 出发**：frozen campaign manifest 是真理来源
2. **具体化工件**：不要声称成功而不指出磁盘上的具体文件
3. **区分不同状态**：
   - command plan（计划）
   - dry run（干运行）
   - executed run（实际执行）
   - exported analysis product（导出产品）
4. **资源受限时**：HPC 不可用就生成计划，不要假装执行了
5. **保持可比性**：对比活动中不同体系的准备和分析应该一致

## 非目标

- 不要在执行阶段重新编写科学假设
- 不要混淆环境成功和科学成功
