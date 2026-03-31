# Skeptic Validation Note — Cowork 独立复审 Toy Test

> **Campaign**: 工具链验证（非科学 campaign）
> **复审者**: Cowork (独立于 Claude Code Terminal 的判断)
> **复审对象**: Claude Code Terminal 的 `2026-03-28_toytst_alanine_final.md` 及全部产出文件
> **方法**: 读 FES 数据 + HILLS 文件 + PLUMED 输入 + MDP + FES 图，用 sub-agent 独立分析

---

## 6-Stage Pipeline 逐层验证

### Stage 0 (Profiler): 是否需要 frozen manifest？

Toy test 是工具链验证，不是科学 campaign。Claude Code Terminal 正确标注了 `Campaign: 工具链验证（非科学 campaign）`。不需要 manifest。

**判断**: ✅ 正确处理

### Stage 1 (Librarian): 资源齐全？

| 资源 | 状态 |
|------|------|
| GROMACS 2026.0 (conda, PLUMED patched) | ✅ |
| PLUMED 2.9 | ✅ |
| ff14SB 力场 | ✅ |
| Alanine dipeptide PDB | ✅ (修复后) |

**判断**: ✅ PASS

### Stage 2 (Janitor): 目录结构？

| 产出 | 位置 | 正确？ |
|------|------|--------|
| 脚本 | `replication/scripts/toy-alanine/` | ✅ |
| FES 数据 | `replication/analysis/toy-alanine/` | ✅ |
| HILLS | `replication/analysis/toy-alanine/` | ✅ |
| FES 图 | `replication/analysis/toy-alanine/` | ✅ |
| Validation notes | `replication/validations/` | ✅ |

**判断**: ✅ PASS

### Stage 3 (Runner): 参数正确？

| 参数 | PLUMED 文件实际值 | MDP 实际值 | 合理？ |
|------|-------------------|-----------|--------|
| HEIGHT | 1.2 kJ/mol | — | ✅ 合理（alanine dipeptide 常用 0.5-2.0） |
| SIGMA | 0.35, 0.35 rad (~20°) | — | ✅ 标准值 |
| PACE | 500 steps = 1 ps | — | ✅ 合理 |
| BIASFACTOR | 10 | — | ✅ 与 TrpB campaign 一致 |
| TEMP (PLUMED) | **300 K** | — | ⚠️ 见下文 |
| TEMP (MDP) | — | **300 K** | ⚠️ 见下文 |
| dt | — | 0.002 ps | ✅ |
| nsteps | — | 5,000,000 (10 ns) | ✅ |
| integrator | — | md (leap-frog) | ✅ |
| constraints | — | h-bonds | ✅ |

**⚠️ 温度不一致**：

PLUMED 和 MDP 都写的 **300 K**，但项目的 Key Decision 表里写的是 **350 K**（P. furiosus 嗜热菌），Claude Code Terminal 的 final validation note 标题也写 "350 K"，FES 图标题也写 "350 K"。

**实际情况**：这个 toy test 是在 **300 K** 下跑的（MDP ref_t=300, PLUMED TEMP=300），不是 350 K。

但这**不是 bug**。理由：
- Toy test 的目的是验证工具链，不是复刻 TrpB 的物理条件
- Alanine dipeptide 在 300 K 跑是完全标准的
- 350 K 是给 TrpB 正式 campaign 用的
- **但 final validation note 和 FES 图里标的 "350 K" 是错的** — 实际跑的是 300 K

**这是一个新的 failure pattern**：Claude Code Terminal 在写 validation note 和绘图时，用了项目级别的温度（350 K）而不是实际 MDP 里的温度（300 K）。

**判断**: ⚠️ PARTIAL — 参数本身合理，但报告中的温度标注与实际不符

### Stage 4 (Skeptic): 操作验证

| 检查项 | 结果 |
|--------|------|
| HILLS 文件存在，6088 行 | ✅ |
| fes.dat 存在，2660 行，51×51 grid | ✅ |
| 无 NaN 或发散 | ✅ |
| HILLS 高度递减（初始 1.31 → 最终 0.19 kJ/mol, ~7× 衰减）| ✅ well-tempered 行为正确 |
| FES 图可读，等高线平滑 | ✅ |

**判断**: ✅ PASS

### Stage 4 (Skeptic): 科学验证

| 检查项 | 预期 | 实际 | 判断 |
|--------|------|------|------|
| alpha_R basin | φ~-60°, ψ~-40° | φ=-53°, ψ=-32°, ΔG=6.1 kJ/mol | ✅ 位置正确 |
| alpha_L basin | φ~60°, ψ~40° | φ=74°, ψ=18°, ΔG=3.3 kJ/mol | ✅ 位置基本正确 |
| C7eq basin | φ~-150°, ψ~150° | 图中可见（红色 → 浅色过渡区） | ✅ 存在 |
| Global min | C7ax 区域 | φ=67°, ψ=-152°, ΔG=0.0 | ⚠️ 见下文 |
| 模拟时长 | 10 ns | 6.1 ns (walltime) | ⚠️ 不完整但够用 |

**⚠️ Global minimum 位置**：

全局最低点在 φ=67°, ψ=-152°。在 300 K 文献中，alanine dipeptide 的全局最低点通常在 C7eq (φ~-80°, ψ~150°) 或 alpha_R 附近。这里 global min 在正 φ 区域（C7ax 附近），这是不常见的。

可能原因：
1. 6.1 ns 不够长，FES 还没完全收敛
2. ff14SB 力场在 alanine dipeptide 上已知有偏差（alpha_R 偏低的问题在 ff14SB 是 known issue）
3. 初始构象 + 有限采样导致

**对工具链验证的影响**：无。工具链验证只需要确认 "MetaD 能跑、FES 能出、basins 能看到"。全局最低点的定量位置不影响结论。

**判断**: ✅ PASS（工具链验证目的）/ ⚠️ PARTIAL（科学定量精度）

### Stage 5 (Journalist): 下游就绪？

| 问题 | 答案 |
|------|------|
| GROMACS + PLUMED 能跑 WT-MetaD？ | ✅ YES |
| plumed sum_hills 能生成 FES？ | ✅ YES |
| 可以开始 TrpB MetaD？ | ✅ YES（需先完成 PLP 参数化 + 15-frame path）|
| 是否有未解决的阻断性问题？ | ❌ NO |

**判断**: ✅ READY

---

## 发现的新问题

### 新 Failure Pattern: FP-008 温度标注与实际不符

| 字段 | 内容 |
|------|------|
| 首次发现 | 2026-03-28 |
| 发现者 | Cowork (Skeptic 独立复审) |
| 受影响文件 | `validations/2026-03-28_toytst_alanine_final.md`, `analysis/toy-alanine/fes_alanine.png` |
| 错误描述 | Final validation note 和 FES 图标题写 "350 K"，但 MDP ref_t=300 K，PLUMED TEMP=300 K。实际模拟温度是 300 K |
| 根因 | Claude Code Terminal 用了项目级别的温度设定（350 K, for TrpB）覆盖了 toy test 的实际参数 |
| 防范措施 | **报告中的参数必须从实际运行文件（MDP/PLUMED）读取，不能从项目级别的 Key Decisions 表推断** |
| 已修复 | ❌ 待修复 |

---

## 总结

| Stage | 判断 | 备注 |
|-------|------|------|
| 0 Profiler | ✅ N/A | 工具链测试，不需要 manifest |
| 1 Librarian | ✅ PASS | 资源齐全 |
| 2 Janitor | ✅ PASS | 目录正确 |
| 3 Runner | ⚠️ PARTIAL | 参数合理，但温度标注错误 (FP-008) |
| 4 Skeptic | ✅ PASS | 工具链验证通过；FES basins 定性正确 |
| 5 Journalist | ✅ READY | 可以进入 TrpB 正式 campaign |

**总体判断: PASS（工具链验证目的达成）**

唯一需要修的是 FP-008：final validation note 和 FES 图里的 "350 K" 应改为 "300 K"。
