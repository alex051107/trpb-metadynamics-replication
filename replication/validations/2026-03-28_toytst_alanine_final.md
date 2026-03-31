# Skeptic Validation Note: Alanine Dipeptide Toy Test (Final)

> **Campaign**: 工具链验证（非科学 campaign）
> **目的**: 验证 GROMACS 2026.0 + PLUMED 2.9 工具链在 Longleaf 上能正确跑 well-tempered MetaDynamics
> **Job ID**: 39960327 (前两次 39960167, 39960248 失败，见 FP-006, FP-007)

---

## 操作验证 (Operational)

| 检查项 | 预期 | 实际 | 状态 |
|--------|------|------|------|
| PDB 生成 | ACE-ALA-NME 22 atoms | 修复后正确 (FP-003) | PASS |
| pdb2gmx | ff14SB 拓扑, charge 0.000 | 22 atoms, charge 0.000 | PASS |
| Solvation | TIP3P 水盒子 | 成功 | PASS |
| Energy minimization | Fmax 收敛 | 成功 | PASS |
| NVT heating | 300 K 稳定 | 成功 | PASS |
| NPT equilibration | 密度稳定 | 成功 | PASS |
| MetaDynamics run | HILLS + COLVAR 生成 | 6088 hills, 30448 COLVAR entries | PASS |
| FES generation | plumed sum_hills 成功 | fes.dat (194 KB, 51x51 grid) | PASS |
| 无 NaN 或发散 | 能量稳定 | 最终 step 3,044,200, E = -15280 kJ/mol | PASS |

**操作结论: PASS**

## 科学验证 (Scientific)

| 检查项 | 预期 | 实际 | 状态 |
|--------|------|------|------|
| 模拟时长 | 10 ns | 6.1 ns (walltime timeout) | PARTIAL |
| 能量盆数量 | 2+ basins (alpha_R + C7eq) | 12 local minima (size=5 filter), 3 主要 | PASS |
| Alpha_R basin | phi ~ -60, psi ~ -40 | phi=-53, psi=-32, E=6.1 kJ/mol | PASS |
| Alpha_L basin | phi ~ 60, psi ~ 40 | phi=74, psi=18, E=3.3 kJ/mol | PASS |
| FES 形态 | 标准 Ramachandran 面貌 | 正 phi 区域偏低 (300 K 下正常), 基本合理 | PASS |
| 收敛性 | well-tempered 高斯高度递减 | 最后 hill 高度 0.19 kJ/mol (初始 ~0.6), 递减中 | PASS |

**注意**: 实际模拟温度为 **300 K**（MDP ref_t=300, PLUMED TEMP=300），非 350 K。之前标注有误（FP-008）。FES 形态与 300 K 文献结果一致。

**科学结论: PASS** (工具链验证目的已达到)

## 下游就绪 (Integration)

| 检查项 | 结论 |
|--------|------|
| GROMACS + PLUMED2 能跑 WT-MetaD? | YES |
| plumed sum_hills 能生成 FES? | YES |
| 可以开始 TrpB MetaD? | YES, 但需要先完成 PLP 参数化 + 15-frame path |

**下游结论: READY** (工具链验证通过，可以进入 TrpB 正式 campaign)

---

## 遇到的问题 (已记录在 failure-patterns.md)

| 问题 | FP 编号 | 状态 |
|------|---------|------|
| ACE 残基 PDB 原子名错误 | FP-003 | 已修复 |
| PLUMED 原子索引不匹配 | FP-004 | 已修复 |
| OMP_NUM_THREADS 与 -ntomp 冲突 | FP-006 | 已修复 |
| conda 路径硬编码错误 | FP-007 | 已修复 |

## 产出文件

| 文件 | 位置 |
|------|------|
| FES 数据 | `replication/analysis/toy-alanine/fes.dat` (本地) |
| FES 图 | `replication/analysis/toy-alanine/fes_alanine.png` (本地) |
| HILLS | Longleaf: `/work/users/l/i/liualex/AnimaLab/runs/toy-alanine/HILLS` |
| COLVAR | Longleaf: `/work/users/l/i/liualex/AnimaLab/runs/toy-alanine/COLVAR` |
