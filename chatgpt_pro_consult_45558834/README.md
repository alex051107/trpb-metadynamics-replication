# TrpB Metadynamics Replication — Pro Consultation Package

**Date**: 2026-04-24
**Context**: 今天下午和 PI (Yu Chen) 1-on-1 group meeting。需要 Pro 就 FP-034 path fix 的 validity + 10-walker seeding 策略 + pilot 45515869 结果的解读给 verdict。

---

## 最关键的一条数据（30 秒读懂）

我的 MD 系统 start.gro（= 500 ns Ain cMD 终末帧）和 1WDW 晶体的 **直接 Kabsch RMSD = 1.590 Å/atom (112 Cα)**。

- 距 **1WDW (path MODEL 1)**: RMSD = 1.590 Å
- 距 **3CEP(+5) (path MODEL 15)**: RMSD = 1.760 Å
- **距 MODEL 7 (path 中点)**: RMSD = 1.298 Å ← MIN
- PATHMSD 用 λ=80 soft-min 算出 **s = 7.09, z = 1.68 Å²**

**PM 的困惑是**：500 ns Ain cMD 按 JACS 2019 应 equilibrate 到 Open (s=1)。但 start.gro 投到 s=7。是 path fix 错了吗？

**我的解释**（等 Pro verdict）：
- start.gro 物理上**更像 1WDW** (RMSD 1.59 vs 1.76)
- 但 linear interp path 的**中点 MODEL 7 几何上更 soft-min 友好**（三角不等式）
- PATHMSD 报 s=7 **math 没 bug**，但不能直接读成"protein 在 PC basin"
- 这是 linear-interp path 的**已知局限**（neighbor_msd_cv=0，Belfast 教程提过）

---

## 包里 5 个核心问题（见 QUESTION_FOR_PRO.md）

**Q1**: FP-034 +5 offset 对吗？
**Q2**: start.gro 投 s=7 是正确 observation 还是 path fix 仍有 bug？
**Q3**: Pilot max_s=12.87 near-wall (z=2.04) 算不算 "path 通路 confirm"?
**Q4**: 10-walker seeding 该怎么选？（A 从 pilot 挑 s=1-12 frames / B 加 cMD 转换补 s<7 / C 重 equilibrate）
**Q5**: 明天 meeting narrative 该怎么软化？

---

## 包里文件索引

### 核心 analysis docs
- `QUESTION_FOR_PRO.md` — 5 个 specific questions 给 Pro
- `VERIFICATION_REPORT.md` — Codex 独立验证 7/8 PASS（FP-034 fix 的 sanity check）
- `REVERSE_SANITY_CHECK.md` — endpoint self-projection + 独立 PC candidate 投影
- `summary.txt` — 数值 snapshot（⟨MSD⟩, λ, identity %）
- `JACS2019_ReadingNotes.md` — 原论文笔记（"Ain 平衡态在 Open" 的来源）
- `miguel_email.md` — Miguel 作者原邮件 PLUMED contract
- `plumed_template.dat` — 10-walker production plumed input

### Path + system artifacts
- `path_seqaligned_gromacs.pdb` — **corrected path** (FP-034 fix 后 production 用的；15 MODEL × 112 Cα)

### Raw data (under raw_data/)
- `pilot_45515869_COLVAR` — 8 ns MetaD (corrected path) 的完整 s(t) / z(t)，40193 rows
- `pilot_45515869_HILLS` — Gaussian deposition history
- `baseline_45324928_COLVAR` — 老 path (naive mapping, pre-FP-034) 的 16 ns baseline 对照，81479 rows
- `start.gro` — 2.6 MB GROMACS 格式 MD start structure (39268 atoms, 500 ns Ain cMD 终末帧)

---

## Pilot 45515869 的完整 s 分布（独立于 10-walker 讨论）

Pilot 单 walker 8 ns sim 的 s histogram:
```
s=[ 1,  2):   6631 frames (16.50%) ████████
s=[ 2,  3):   4105 frames (10.21%) █████
s=[ 3,  4):   4303 frames (10.71%) █████
s=[ 4,  5):   5006 frames (12.45%) ██████
s=[ 5,  6):   4744 frames (11.80%) █████
s=[ 6,  7):   4539 frames (11.29%) █████
s=[ 7,  8):   3743 frames ( 9.31%) ████
s=[ 8,  9):   2654 frames ( 6.60%) ███
s=[ 9, 10):   2085 frames ( 5.19%) ██
s=[10, 11):   1758 frames ( 4.37%) ██
s=[11, 12):    608 frames ( 1.51%)
s=[12, 13):     17 frames ( 0.04%)
```

- **min_s = 1.000** at t = 4920.2 ps（walker 到过 s=1）
- **max_s = 12.867** at t = 6085 ps（transient，near wall z=2.04）
- **mean_z = 1.530 Å²**（walker 通常 off-path 1.53 Å²）
- fraction(s<3) = 26.71%
- fraction(s>10) = 3.0%

**这说明什么（请 Pro verify）**：
- pilot 实际 sample 了 s=1 到 s=12 整段 path ✓
- 但 mean_z=1.53 意味着 walker 大部分时间**并不在 path 上**，是 soft-min 投影后被 assign 到不同 s 值
- walker 自己穿越 s=1 到 s=12 所用 sim 时间 ~5 ns ← 这是实际 exploration speedup 的 evidence
- 不需要 10-walker 就能 sample 全 path？还是 shared bias 仍然加速 convergence？

---

## Baseline 45324928 对照（老 path, pre-FP-034）

```
16 ns sim:
  min_s = 1.005, max_s = 1.896, mean_s = 1.171
  s=[1.00, 1.25): 75.24%  ← walker 卡在 naive-path s=1 领域
```

**关键对比**：同一个 start.gro + 同一个 MetaD 参数，
- 老 path 16 ns 只 sample s=1-1.9 （窄）
- 新 path 8 ns sample s=1-12.87 （宽 6x）

→ FP-034 fix **在 exploration 能力上有肯定的正面效应**，即使对 start.gro 投影点的解读有争议。

---

## 当前 Longleaf 运行状态

| Job | State | 备注 |
|---|---|---|
| 45186335 | RUNNING 1d+13h | Aex1 500ns cMD（独立线，不相关）|
| 45324928 | RUNNING 21h+ | 老 path 对照（有用，不动）|
| 45515869 | RUNNING 8h+ | **pilot，corrected path，已 sample s=1-12** |
| 45558834_[0-9] | RUNNING 45min+ | **10-walker production，seeding 有争议，待 PM 批准 scancel 或继续** |

---

## PM 需要 Pro 回答的最紧迫决策

1. **现在要不要 scancel 45558834**?（seeding 全用 same start.gro，被 Codex + internal subagent + PM 3 方 flag）
2. **如果 re-seed**，从 pilot xtc 挑 s-diverse frames 合理吗？
3. **明天 meeting slide 9 "gate cleared"** 的 claim 要软化到什么程度？（given z=2.04 near-wall 问题）
4. **linear-interp path 的 s=middle 偏置 (soft-min bias)** 要不要写进 TechDoc 作为 known limitation？

**回复 format**: 5 段，每段回答一个 Q，≤200 字。最后一段 "most likely Yu attack vector tomorrow"。
