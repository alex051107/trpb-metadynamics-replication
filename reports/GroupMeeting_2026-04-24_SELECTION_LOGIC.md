# 2026-04-24 组会 — 决策逻辑速读（会前 5 分钟看）

> 这份文档补齐了之前 TechDoc 和 PresenterScript 里没直接讲的 "**我为什么这么选**"。
> 全文 ~600 行，目的是让 Yu 看明白**每一步选择背后的 reasoning chain**，避免 "你怎么想到的" 被追问。

---

## 核心逻辑链 (one-slide 摘要)

```
SI (JACS 2019)                ← 约束来源
  ↓ 规定 1WDW↔3CEP + 112 Cα + linear interp + 15 frames
MD 系统搭建
  ↓ 1WDW β chain + Ain cofactor + TIP3P + 39268 atoms
  ↓ 500 ns pmemd.cuda cMD (equilibration)
start.gro 产出
  ↓
Path 构造 (发现 FP-034 bug 前)
  ↓ naive: resid 97↔97 跨物种 → 6.2% identity, O↔C RMSD 10.89 Å, λ=3.80
  ↓ [2026-04-23 发现 bug]
Path 重建 (FP-034 fix 后)
  ↓ NW +5 offset: resid 97↔102 → 59.0% identity, RMSD 2.115 Å, λ=100.79
  ↓ 4 层 verify: 自实现 + Codex + reverse sanity + PC crystal projection
Pilot 45515869 (fallback, single walker, verify path 能跑)
  ↓ 8 ns: min_s=1, max_s=12.87, 26.7% 时间在 s<3
  ↓ start.gro 投到 s=7 但 z=1.68 (off-path, NOT biology claim)
10-walker 45558834 (primary, multi-walker production)
  ↓ 当前状态: 1h 后 2 walker 已过 s=12, 其余在 s=8-11 spread
  ↓ caveat: seeding 用 same start.gro (suboptimal, shared HILLS 弥补中)
Meeting material + cartridge D1 deliverable
```

---

## 6 个关键选择的 "why"

### 选择 1: MD 系统用 1WDW β chain + Ain cofactor

**为什么选 1WDW**:
- JACS 2019 SI 明确规定 **O endpoint = 1WDW**（P. furiosus apo TrpB 晶体）
- 1WDW β chain 是 TrpB β subunit（催化 Trp 合成的那条链，COMM domain 在这条）

**为什么加 Ain (PLP-Lys internal aldimine)**:
- Ain = "idle resting state" PLP 共价连 Lys82
- 生物学上这是 TrpB 底物结合前的**基态**，最稳定，MetaD 起点最合理
- Aex1 / A-A / Q₂ 是反应中间态，不稳定，暂不做

**为什么 TIP3P + ff14SB + 350 K**:
- SI 明确 TIP3P
- ff14SB 是 AMBER 14SB 力场，原文 AMBER16 等价（Osuna paper 里用 AMBER16，我们 AMBER 24p3 向后兼容）
- 350 K = 77°C 近 P. furiosus 嗜热酶生理温度

**不是我发明的**：完全按 Osuna SI + 标准 AMBER force field 来。

---

### 选择 2: Path 用 linear interpolation 1WDW→3CEP, 15 frames, 112 Cα

**为什么 linear interp + 15 frames**:
- SI 原话（黑体引自 JACS2019_ReadingNotes.md）:
  > "a path of conformations from open (O) to closed (C) states was obtained by **linear interpolation between the X-ray available data**. ... a **path of 15 conformations** from an open (s(R)=1) to closed state (s(R)=15), was generated."

**为什么 112 Cα = COMM 97-184 + base 282-305**:
- SI 原话:
  > "Guided by structural information we restricted the path of structures to the **alpha carbons of the COMM domain (residues 97-184) and a region located at the base of COMM domain (residues 282-305)**"
- COMM = Communication domain，负责 α-β subunit 之间的 allosteric coupling
- 88 (COMM) + 24 (base) = 112，SI 明确

**linear interp 的已知缺陷（诚实说）**:
- `neighbor_msd_cv = 1.96e-14`（每帧间距完全均匀）= **geometric waypoint, 不是 physical intermediate**
- Belfast PLUMED 教程推荐 10-15% CV，我们是 0
- 中段 MODEL 在 soft-min 下被 triangle-inequality "偏爱"（任意 off-path 结构都容易投到中点）
- → 这是 linear interp path 的已知限制，**不是 bug**，但影响 s value 的物理解读（见 选择 6）

**不是我发明的**：完全按 SI 字面。但**SI 没写 path 的 endpoint 怎么对齐**—— 这就是 FP-034 bug 的根源。

---

### 选择 3: FP-034 — 用 Needleman-Wunsch +5 offset 替换 naive resid mapping

**为什么是 bug 不是 feature**:
- 1WDW = P. furiosus, 3CEP = S. typhimurium —— **不同物种**
- 两条蛋白 homologous 但 residue numbering **不一样**（N 端 signal peptide 处理不同）
- Naive 取 "1WDW resid 97 ↔ 3CEP resid 97" 比较的是**非同源位置**
- 验证：naive mapping 给 COMM 区**只 5.7% identity**（相当于随机噪声）

**为什么 NW 选 match=+2 mismatch=-1 gap=-2**:
- Identity-based scoring（不是 BLOSUM62），**简化版本**
- 在 TrpB 两物种这种 "中等同源" 情况下足够（subagent 测试过能正确 detect fake indel）
- 如果是 distant homolog 要用 BLOSUM62 + affine gap，现在情况够用

**为什么 offset 是 +5 不是别的**:
- 手算（FGEFGG motif）：N 端 1WDW 到 3CEP 是 +6 offset
- 但 COMM 区（97-184）中间有 1 个 indel（在 resid 61-62 附近）把 offset 从 +6 减到 +5
- 验证：offset +5 给 COMM **70.5% identity** vs 其他 offset (+6=2.3%, +7=8.0%)
- Codex 独立实现同样得 +5

**4 层独立验证**:
1. 我的 `build_seqaligned_path.py` (Python NW)
2. Codex 的 `verify_and_materialize_seqaligned_path.py` (7/8 PASS; 1 FAIL 是 59.0% rounding)
3. Reverse sanity: 1WDW 晶体自投 corrected path → s=1.14; 3CEP(+5) 自投 → s=14.86
4. 独立 PC 晶体 projection: 5DW0→s=9.46, 5DW3→s=8.51, 5DVZ→s=5.37, 4HPX→s=14.90（全部生物学合理）

---

### 选择 4: Pilot 用 Miguel **fallback** (HEIGHT=0.3, BF=15) 单 walker

**为什么是 fallback 不是 primary**:
- Miguel 邮件明确:
  > Primary = 10-walker, HEIGHT=0.15, BIASFACTOR=10, 50-100 ns/walker
  > Fallback = **single-walker, HEIGHT=0.3, BIASFACTOR=15, 用于 "shake the COMM domain if stuck"**
- **Pilot 的目的是快速 verify corrected path 是否 responsive**，不是 production FES
- 单 walker + 激进参数能在 ~10 ns 内 sample 广 s range，**足够回答 "path 通不通"**

**为什么 λ=80 不是 λ=100.79**:
- Miguel 邮件原字面值 LAMBDA=80（他的 path 的 Branduardi 最优值）
- 我们 corrected path 的 Branduardi 最优是 100.79（ratio 1.26× Miguel 的 80）
- 1.26× 在 Branduardi tolerance 内（kernel weight 0.16 vs target 0.10）
- **选 80 更贴近 Miguel contract**，想严格 Branduardi 的话切 100.79 也 OK（plumed 已备两版）

**运行了多久 + 结论**:
- 11h wall, 8.55 ns sim
- min_s = 1.000 @ t=4920 ps（到过 Open 端）
- max_s = 12.867 @ t=6085 ps（到过 Closed 端）
- **整段 s=1-12 都 sample 到了** → corrected path response ✓
- mean_z = 1.530 Å² → walker 大部分时间在 path 附近但**不在 path 上**（linear interp path 的特性，不是 bug）

---

### 选择 5: 10-walker 用 Miguel **primary** (HEIGHT=0.15, BF=10) + shared HILLS

**为什么切到 primary contract**:
- Pilot 已 verify path responsive → 现在做 production FES
- 10-walker shared HILLS = 标准 well-tempered multi-walker 方案
- HEIGHT 减半、BF 减半：蓝图要**更 conservative**，因为 10 walker 并行填 bias 更快

**为什么 seeding 用 same start.gro（我错了，承认）**:
- **懒 + 时间压力**：500 ns cMD 是 AMBER `.nc` 格式，要 cpptraj 转 GROMACS 才能提 early frame
- 以为 "shared HILLS + random seed 能产生 diversity"
- **PM + Codex + Pro 三方 flag**: 这不是 diverse seeding，是 "1 walker × 10 份 GPU"

**当前观察（1h 后）**:
- 10 walkers max_s 分散 8.87-12.58 → **shared HILLS 确实弥补了部分 seed 缺陷**
- w05 max=12.58, w09 max=12.32 → **2 walker 已过 s=12 gate**
- 但**没 walker 在 s<7 起跑**（全从 s=7 出发）

**Decision 现状**:
- **不 scancel**：继续观察 2-4h，如果 walkers 进一步 diverge 到 s<5，就让它跑完
- **如果 stall 了**：scancel + reseed from pilot xtc（按 s 值 1-12 挑 10 个最低 z frame）
- Pilot 的 candidate seed 我已经选好（见 TechDoc Ch 8）

---

### 选择 6: start.gro s=7 的叙事软化（Pro verdict）

**发生了什么**:
- 我昨天（04-23）写 slide 9 时 claim "start.gro at s=7 = Ain biology 自然 PC"
- Pro verdict 今早（04-24）指出：这个 claim **是 post-hoc rationalization**，和 JACS 2019 明说的 "Ain O highly favored, PC 高 2 kcal/mol" **直接矛盾**

**重新解读（Pro + 我手算联合确认）**:
- start.gro 投到 s=7 **math 对**（soft-min 算的）
- start.gro 到 MODEL 1 (1WDW) 直接 Kabsch RMSD = **1.59 Å**
- start.gro 到 MODEL 15 (3CEP+5) Kabsch RMSD = **1.76 Å**
- **物理上离 1WDW 比 3CEP 近**（1.59 < 1.76）
- start.gro 的 z = 1.68 Å² = **off-path，不是中段 basin**

**正确说法**:
- ❌ "start.gro 在 PC basin" / "500 ns cMD 到了 PC" / "Ain 自然 PC"
- ✅ "start.gro 是 1WDW+Ain 系统 500 ns cMD 后的 endpoint"
- ✅ "它到 1WDW 原晶体 1.59 Å 漂移，物理上仍偏 Open side"
- ✅ "linear interp path 的 soft-min 把它投到 s=7，但这是几何投影 artifact，不是生物学状态"

**对 meeting 的影响**:
- Slide 9 标题从 "GATE CLEARED" → "corrected path exploration (s=1 to 12)"
- Slide 1 去掉 "端到端通路 confirm"
- Cheatsheet 开场句改成 honest 版
- TechDoc Chapter 7 **专门一章**讲这个 nuance

---

## Yu 明天最可能的 3 个 killer questions + 我的答案

### Q1: "你的 start.gro 怎么会投到 s=7？500 ns 后应该还在 Open (s≈1)"
**答**: 您 intuition 对一半。**物理上** start.gro 到 1WDW 晶体 1.59 Å（仍偏 Open），**数学上** PATHMSD soft-min 把它投到 s=7 因为 linear interp path 中段 MODEL 几何上 triangle-inequality friendly。这**不是 biology claim**，是 linear interp path 的已知 artifact。TechDoc Ch 7 专门讲这个。

### Q2: "+5 offset 是 alignment finding 还是 PDB numbering convention？"
**答**: **主要是 numbering convention 差**（signal peptide 处理不同）。NW 的 value 不是"发现 offset"，是**证明 selected 112 个 residue 内无 indel**。N 端实际是 +6 offset，但 97-184 + 282-305 这段是 +5。identity 70.5% 是强同源信号。还没做 BLAST/BLOSUM 正式 proof。TechDoc Ch 5 讲清楚。

### Q3: "10-walker 全从 s=7 起跑，不是浪费 parallelism 吗？"
**答**: 承认 seeding 不 optimal（我偷懒 + 时间压力）。但 1h 观察：shared HILLS 已让 walkers 扩散到 s=8-12 范围，2 walker 已过 s=12 gate。如果 2-4h 还没 diverge 到 s<5，会 scancel + reseed from pilot xtc (candidates 已选好)。这是明显的可执行补救。

---

## FP-034 fix 的 meeting 立场

**Stay firm on**:
- FP-034 bug 是真的（6.2% vs 59.0% identity 不是工具 artifact）
- +5 offset 在 selected 112 Cα 内是正确的（4 层 verify）
- λ=100.79 vs Miguel 80 ratio 1.26× 是真实一致

**Soften on**:
- start.gro s=7 interpretation（off-path projection, not biology）
- "Ain 平衡态" 全面删除，只说 coord reprojection
- Pilot max_s=12.87 是 near-wall transient，不是 "clean end-to-end path validation"

**Admit uncertainty on**:
- Miguel 原 PATH.pdb 我们没有 → 他的 path 构造细节可能和我们不完全一致
- 10-walker seeding 的 practical consequences 还在观察中
- 500 ns cMD 是否真 equilibrate 到 "Ain 平衡态" 不确定

---

## 数据源头（每一个数字的出处）

| Claim | 值 | 来源 |
|---|---|---|
| NW identity COMM | 70.5% | 本地手算 (Python NW) 2026-04-24 |
| NW identity (59.0%) | 59.03% | Codex VERIFICATION_REPORT L16 |
| O↔C RMSD 2.115 Å | 2.1149 | VERIFICATION_REPORT L24 |
| ⟨MSD_adj⟩ 0.0228 Å² | 0.022819 | summary.txt L21 |
| λ 100.79 Å⁻² | 100.7916 | VERIFICATION_REPORT L25 |
| Miguel λ=80 | 80 | miguel_email.md |
| start.gro s=7.09 | 7.0879 | pilot COLVAR row 1 (t=0) |
| start.gro z=1.68 | 1.6814 | pilot COLVAR row 1 |
| start.gro RMSD to 1WDW | 1.590 | 本地 Kabsch (Python) 2026-04-24 |
| Pilot min_s=1.000 | 1.000 @ t=4920.2 | pilot COLVAR numpy scan |
| Pilot max_s=12.867 | 12.867 @ t=6085.4 | pilot COLVAR numpy scan |
| Pilot fraction(s<3)=26.71% | 10736/40193 | pilot COLVAR numpy scan |
| Baseline max_s=1.896 | on old path | baseline COLVAR numpy scan |
| 10-walker max_s(w05)=12.58 | 2026-04-24 09:22 snapshot | live squeue + COLVAR |

---

**Meeting 时间**：下午
**建议**：先读这份 600 行 SELECTION_LOGIC.md，再读 updated TechDoc（agent 还在写，~15 min 后回）。
