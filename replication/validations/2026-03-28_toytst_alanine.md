# Skeptic Validation Note — Alanine Dipeptide Toy Test

> **Campaign**: 工具链验证（非科学 campaign）
> **目的**: 验证 GROMACS 2026.0 + PLUMED 2.9 工具链在 Longleaf 上能正确跑 well-tempered MetaDynamics

---

## 验证范围

| 阶段 | 预期结果 | 实际结果 | 状态 |
|------|---------|---------|------|
| PDB 生成 | 正确的 ACE-ALA-NME 22 原子 | 第一次失败（FP-003），修复后 ✅ | ✅ |
| pdb2gmx | ff14SB 拓扑，charge 0.000 | 22 atoms, charge 0.000 ✅ | ✅ |
| solvate | TIP3P 水盒子 | 成功 ✅ | ✅ |
| energy minimize | Fmax 收敛 | 成功 ✅ | ✅ |
| NVT heating | 350 K 稳定 | 成功 ✅ | ✅ |
| NPT equilibration | 密度稳定 | 成功 ✅ | ✅ |
| MetaDynamics run | HILLS + COLVAR 文件生成 | Job 39960327 提交，HILLS 正在写入 | ⏳ |
| FES analysis | φ/ψ FES 与文献吻合 | 待 job 完成 | ⏳ |

---

## 发现的脚本 bug（Cowork 生成 → Longleaf 执行时暴露）

| Bug | 对应 FP | 修复方式 |
|-----|---------|---------|
| ACE 残基有 N 原子 | FP-003 | 重写 PDB，去掉 N |
| PLUMED 索引 4,5,6,7 | FP-004 | 从 .gro 确认正确索引 5,7,9,15 |
| conda 路径硬编码 | — | 改为 source activate |
| OMP_NUM_THREADS 冲突 | — | 显式 export OMP_NUM_THREADS=4 |

---

## 结论

工具链本身（GROMACS + PLUMED）可以正常工作。问题全部出在 **Cowork 远程生成脚本时对力场细节和拓扑输出的假设**。

**教训**：Cowork 生成的脚本必须包含 validation step（`validate_setup.sh`），Claude Code Terminal 在执行前先跑验证脚本。
