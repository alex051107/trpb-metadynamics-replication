# 阶段 5：Skeptic（验证器）

## 功能

验证运行输出。区分三种"成功"：操作成功、科学成功、下游集成就绪。

## 何时使用

- 运行完成或干运行结束
- 需要决定"这个失败是什么类型"
- 需要检查是否满足 frozen campaign 的要求
- 需要确定是否可以导出特征或下游使用

## 输入

- protocol manifest
- campaign manifest（frozen）
- run logs
- generated artifacts（HILLS、trajectory、FES、等）
- validation criteria

## 输出

选择以下之一：
- validation note（验证说明）
- pass/fail table（通过/失败表）
- root-cause statement（根本原因说明）

## 三种"成功"的区分

1. **操作成功**（Operationally valid）
   - 预期文件存在
   - 无 NaN 或致命运行时错误
   - HILLS 或偏置输出正常生成

2. **科学成功**（Scientifically valid）
   - readouts 与 frozen campaign 的问题一致
   - 被对比的体系在相同设置下可比
   - 解释与参考态逻辑一致

3. **下游就绪**（Integration-ready）
   - 下游消费者明确命名
   - 导出的特征表或决策规则可追溯到工件
   - 假设不被错误标记为生产筛选

## 典型检查项

- 预期文件是否存在
- 是否有 NaN 或明显发散
- CV 范围是否合理
- HILLS 沉积是否正常
- FES 输出是否存在且未损坏
- 对比体系确实可比吗
- 下游声明是否超出 frozen campaign 范围

## 关键规则

1. **先检查工件，再解释**
2. **"运行了"和"科学可接受"是不同的说法**
3. **标准未定义时要明确说明**
4. **把反复出现的验证失败记录在 failure-patterns.md**
5. **下游声明必须有明确的来源**

## 非目标

- 不要无理由为失败的结果开脱
- 不要创建虚假的"成功"来推进项目
