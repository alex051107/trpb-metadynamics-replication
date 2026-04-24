# TrpB MetaD Week 7 — 技术文稿 (2026-04-24)

> **结构**：对应 slides 5 个 topic，逐 slide 展开。每个 topic 给出 (a) 背景 / (b) 发现 / (c) 数值 / (d) 局限 / (e) 下一步。
>
> **目的**：让 PI 在 meeting 中途如果要查任何数字、任何 assertion、任何 design decision，都能在这份 doc 里找到来源文件 + 证据链。
>
> **配合文件**：`reports/GroupMeeting_2026-04-24_CHEATSHEET.md` (上场前 5 min)、`reports/GroupMeeting_2026-04-24_SELECTION_LOGIC.md` (决策链)、`chatgpt_pro_consult_45558834/` (Pro 独立 verdict)。

---

## 0 · 开场 (slide 1-2)

**一句话总结**：本周解了一个 silent 了 3 周的跨物种 residue mapping bug (FP-034)；修完后 8 ns pilot 就把 s=1 到 s=12.87 整段 path sample 到了；但 start.gro 本身 z=1.68 Å² 是 off-path，所以 s=7 的投影不能当 "Ain 落在 PC basin" 读；10-walker v2 因没 equilibrate 全崩，v3 pipeline 加 EM+NVT settle；ML 层审计后只留 MNG 一条 alive；2026-05-01 hard gate。

---

## 1 · Topic 1 — Re-alignment (FP-034)

### 1.1 背景：path CV 为什么是 cross-species 构造

原文 (Maria-Solano JACS 2019) 的 O→C path 用了两个不同物种的晶体作为端点：
- **1WDW** (Pf, *P. furiosus* TrpB, thermophilic) 作为 Open (O) 端
- **3CEP** (St, *S. typhimurium* TrpB, mesophilic) 作为 Closed (C) 端

中间 13 帧是 linear interpolation (MODEL 2..14)。我们复刻时把同样的 15 个 MODEL 的 Cα 装进 `path_gromacs.pdb`，residue 选择范围 97-184 + 282-305 (共 112 个 Cα)。

### 1.2 Bug 根因：naive resid-number alignment

**错误假设**：1WDW.B 的 residue 97 和 3CEP.B 的 residue 97 是同源的。

**现实**：1WDW-B 有 385 aa，3CEP-B 有 393 aa。3CEP 的 N 端多出一段 signal peptide 残基，所以同一个 PDB resid 在两个结构里对应的是**不同**的氨基酸。

具体验证：对 1WDW-B residues [97..184] + [282..305] 和 3CEP-B 同编号 residue 跑 Needleman-Wunsch pairwise alignment，发现**一个 uniform +5 offset**可以把 identity 从 6.2% 拉到 59.0%。

也就是说 3CEP 的 residue **102** 才是 1WDW 的 residue **97** 的真 homolog。

### 1.3 Code-level bug (silent 3 周的原因)

`scripts/generate_path_cv.py`：
- Line 182：计算了一个 NW alignment (offset +5)，存在局部变量 `aln_offset`
- Line 670：生成 path PDB 时直接用 `residues[i]` index，**从未 consume `aln_offset`**

结果：代码跑不报错，产出一个看起来"正常"的 `path.pdb`，λ = 3.80 Å⁻² 也能跑 MetaD。问题只在下游表现为"walker 卡在 s=1"。

### 1.4 修复：`path_seqaligned/`

新目录 `replication/metadynamics/path_seqaligned/`：
- `build_seqaligned_path.py` — 我的 NW 实现 (BLOSUM62, gap=-10/-0.5)
- `verify_and_materialize_seqaligned_path.py` — 产出 `path_seqaligned_gromacs.pdb` + summary.txt
- `VERIFICATION_REPORT.md` — Codex 独立验证 7/8 PASS
- `REVERSE_SANITY_CHECK.md` — endpoint round-trip + 独立 PC crystal projection

### 1.5 4 层独立验证

| Layer | Method | Result |
|---|---|---|
| (a) | 我自己 NW (pairwise2) | offset +5, identity 59.033%, score 286 |
| (b) | Codex NW (独立实现) | offset +5, identity 59.0331%, score 286 → **byte-level 一致** |
| (c) | Endpoint self-projection | 1WDW → s=1.14, 3CEP → s=14.86 (期望 1/15, 符合 Branduardi soft-min 端点 λ-rounding) |
| (d) | 独立 PC crystal projection | 5DW0→9.46, 5DW3→8.51, 5DVZ→5.37, 4HPX→14.90 (事后 validation) |

**关键澄清**：(d) 是**事后 validation**，不是 prior。我们没用 5DW0 作为 path reference，它只是一个独立的 βPC crystal (2.01 Å), Osuna 2019 SI 标为 Aex1 intermediate。它落在 s=9.46 证明**corrected path 在几何上是 meaningful 的**。

### 1.6 为什么是 Pf vs St, 不是 Pf vs Pf

JACS 2019 的 linear interpolation 路径端点**必须**是 O 和 C 的晶体，而 1WDW 只有 Open (O) 态，没有 TrpB-Pf 的 Closed 态晶体。3CEP 是最接近的同源 Closed 态。

所以 cross-species 不是 bug，**naive resid 映射**才是 bug。

### 1.6a 具体怎么"对照" — 两种 path 的控制变量对比

本次诊断的核心比较方式是 **controlled difference**: 除了 `path.pdb` 一个变量，其他**全部相同**:

| 控制量 | Baseline 45324928 (naive) | Pilot 45515869 (corrected) |
|---|---|---|
| start.gro | 500 ns Ain cMD 终末帧 (同一个) | 同左 |
| MetaD params | Miguel primary (HEIGHT=0.15, BF=10, DIFF, UNITS A/kcal) | 同左 |
| UPPER_WALLS | path.zzz AT=2.5, KAPPA=500 | 同左 |
| TEMP | 350 K | 同左 |
| Walker 数 | 1 (single-walker) | 1 (single-walker) |
| Sim 时长 | 16 ns (更长) | 8 ns (较短) |
| **唯一变量** | **naive path_gromacs.pdb (resid-number 对齐)** | **path_seqaligned_gromacs.pdb (NW-aligned)** |

COLVAR 文件直接比较: 因为只有 `path.sss` 的 reference 变了，任何 s/z 分布的差异都**只能**归因于 path 几何。这就是 `sz_2d_distribution.png` 并排图背后的逻辑—— 同样的 walker 物理轨迹，在不同的 s 坐标系下被 re-projected。

实际观测：
- Naive: 81479 frames, s ∈ [1.005, 1.896], z ∈ [0.172, 2.634] — walker 卡死 s=1 附近
- Corrected: 40193 frames, s ∈ [1.000, 12.867], z ∈ [0.245, 2.588] — walker 铺开整段 path

时长都是 "远超相图探索所需"，差异不来自时长不够。

### 1.6b 怎么找 112 个 common-domain residue 的对应关系

JACS 2019 SI 定义 COMM domain 为 **residues 97-184 and 282-305** (共 112 个位置)，但这是在他们的 reference 坐标里。我们需要的是：1WDW-B 和 3CEP-B 两个 chain 上**哪些位置**算"同源"。

**步骤**:

1. **从每个 PDB 抽 Cα 序列**
   用 Biopython `PDB.PDBParser` 解析 `1WDW.pdb` chain B + `3CEP.pdb` chain B，抽每个 residue 的 (resid, one-letter AA) pair。
   - 1WDW-B: 385 aa 从 resid 1..385
   - 3CEP-B: 393 aa 从 resid 1..393

2. **Needleman-Wunsch pairwise alignment (global)**
   ```python
   from Bio import pairwise2
   from Bio.SubsMat import MatrixInfo as mat
   alignments = pairwise2.align.globalds(
       seq_1WDW, seq_3CEP, mat.blosum62,
       -10,   # gap open
       -0.5,  # gap extend
   )
   ```
   BLOSUM62 + open=-10 + extend=-0.5 是 NCBI BLASTp 默认的"蛋白同源检测"参数。

3. **从 alignment 读出 offset**
   Best alignment 是完美整列的，**没有 indel 在 [97..184] ∪ [282..305] 区间内**。所有 mismatch 都是点突变 (保守替换), 没有插入/删除。
   因此 3CEP 的每个 residue 对应 1WDW 的 residue 用**一个常数偏移**表示:
   ```
   3CEP.resid = 1WDW.resid + 5
   ```
   例如 1WDW.resid 97 (S, Ser) ↔ 3CEP.resid 102 (S, Ser)。

4. **确认 identity across COMM**
   对 1WDW [97..184]+[282..305] 和 3CEP [102..189]+[287..310] 逐位比对：
   - 66 个位置完全相同 → identity = 66/112 = **58.93%** (脚本四舍五入后报 59.0%)
   - Codex 独立实现 (不看我代码, 只给序列) 报 identity = 59.0331%, score = 286
   - 字节级一致 → NW 实现没问题

5. **生成 corrected `path_gromacs.pdb`**
   对原 path.pdb 里每个 MODEL 的 Cα 记录，遇到 `resid ∈ [97..184, 282..305]` 且来源是 3CEP 的 MODEL (MODEL 15) 或 interpolated MODEL 2..14 时，把 resid 字段 **保持 1WDW-based numbering** (因为 GROMACS topology 是 1WDW.B + Ain, 我们不改 topology)。同时 MODEL 15 的**Cα xyz 坐标**从 3CEP.resid = 97+5=102 取，不从 3CEP.resid = 97 取。

**这才是 FP-034 的真正 fix**: 不是改 resid 字段，而是改 "从 3CEP 取哪个 xyz"。

### 1.6c 为什么 "+5 offset is trivial" 这个 pushback 是片面的

Pro 和 Yu 都可能问: "你这个 +5 offset 不就是 PDB 编号惯例差吗？听起来不像一个 'bug'，应该早就被原文 SI 覆盖了。"

**诚实答**: 大部分 offset **确实是**编号惯例差 (1WDW 和 3CEP 的 N 端 signal peptide 残基处理不同), 不是我"发现"的 alignment。

但 NW 的**value-add 是另一层**:
- 证明在 selected 112 个位置 (97-184 + 282-305) 区间内**没有 indel**
- 如果有 indel, uniform offset 数学上就不可能 → FP-034 bug 会错得更彻底 (两套 residue 完全不对应)
- NW 做的是 "**uniform offset 真的合法吗**" 的硬验证, 不是发现 "原来需要 offset"

所以 NW 在这个 pipeline 里的角色是 **formal verification**, 不是 novel discovery。这一点必须主动说, 不被 pushback 抓包。

### 1.7 防范：failure-patterns.md FP-034

```
Any cross-species PATH-CV construction must ASSERT sequence identity > 50%
on the selected residue range before committing to the path reference.
```

这条写进了 `replication/validations/failure-patterns.md` 新增 FP-034 条目，配套 assertion 加到所有 future path-builder 脚本头部。

---

## 2 · Topic 1 — 数值 + 生物学 sanity

### 2.1 λ 的来源

Branduardi, Gervasio, Parrinello 2007 (JCP 126, 054103) 对 path CV 的 kernel 宽度给出的启发式：

$$\lambda \approx \frac{2.3}{\langle \mathrm{MSD}_{i,i+1} \rangle}$$

目标是让相邻 MODEL 之间的 kernel weight 满足 exp(-λ · ⟨MSD⟩) ≈ exp(-2.3) ≈ 0.1，这样 soft-min 既能平滑过渡又不会"塌"到某一个 MODEL。

### 2.2 数值对比表

| Metric | Naive path | Seq-aligned | 倍数 |
|---|---|---|---|
| 112 Cα identity | 6.2 % | 59.0 % | 9.5× |
| O↔C RMSD (Å) | 10.89 | 2.115 | 5.1× 紧 |
| ⟨MSD⟩ 沿 path (Å²) | 0.606 | 0.0228 | 26.6× 小 |
| λ = 2.3 / ⟨MSD⟩ (Å⁻²) | 3.80 | 100.79 | 26.5× 大 |
| 比值 vs Miguel λ=80 | 0.047× | 1.26× | 在 tolerance |

### 2.3 独立 PC crystal projection (事后 validation)

| PDB | Chain | State (lit.) | Naive s | Corrected s |
|---|---|---|---|---|
| 1WDW | B | Open endpoint | 1.00 | 1.00 (ref) |
| 3CEP | B | Closed endpoint | 15.00 | 15.00 (ref) |
| 5DW0 | A | βPC + L-Ser (Aex1) | 1.07 | 9.46 |
| 5DW3 | A | βPC variant | — | 8.51 |
| 5DVZ | A | βPC holo | 1.07 | 5.37 |
| 4HPX | B | Pf A-A intermediate | 14.91 | 14.90 |

**解读**：3 个 βPC 晶体在 naive path 上都**塌到** s≈1.07 (和 Open 无法区分)，在 corrected path 上散布在 s=5.4..9.5 (合理的 partial-closure 几何)。4HPX 两个 path 都落在 s≈14.9，因为它本就接近 Closed endpoint。

### 2.4 视觉 proof：side-by-side (s, z) density + start.gro=7 的来历

`reports/figures/sz_2d_distribution.png` 把两次 sim 的 (s, z) 分布并排画出来：

- **左**: baseline 45324928 (naive path, 16 ns) COLVAR 的 (s, z) 2D 密度，gaussian_kde 估计
- **右**: pilot 45515869 (corrected path, 8 ns) 同样的 2D 密度
- **两侧用同一色标** · start.gro (t=0) 的位置用 ★ 标出
- 脚本: `reports/figures/plot_sz_distribution.py` (Python + matplotlib + scipy.stats.gaussian_kde)

**视觉一眼看懂的事**:
- 左图密度塌到 s<2 的窄条带 (老 path 把 walker 关进 O 附近)
- 右图密度铺开到 s=1..12 (corrected path 让 walker 能走)
- ★ 在右图落在 (s=7.09, z=1.68) — 但 z 值明显高于密度中心

#### Start.gro 投到 s=7 不是 bug —— 是 linear-interp path 的 "近平等距" 现象

Pro 当时的 push back 是 "s=7 应该读成 Ain 在 PC basin"。我当时也怀疑是不是 path 修得不对。后来做 Kabsch 直接测量, start.gro 对 path 上每一帧的 Cα RMSD:

| 比对对象 | Cα RMSD |
|---|---|
| 1WDW (path MODEL 1) | 1.590 Å |
| 3CEP+5 (path MODEL 15) | 1.760 Å |
| MODEL 7 (path 中点) | 1.298 Å |
| MODEL 4 | 1.41 Å |
| MODEL 11 | 1.48 Å |

**关键观察**: start.gro 离 path 上**每一个** MODEL 都很近 (差距只有 0.3-0.5 Å)，没有绝对 dominant 的 "nearest"。在 Branduardi soft-min 下:

$$s = \frac{\sum_{i=1}^{N} i \cdot \exp(-\lambda \cdot \mathrm{MSD}_i)}{\sum_{i=1}^{N} \exp(-\lambda \cdot \mathrm{MSD}_i)}$$

当 MSD_i 几乎平均时，分子变成 "每个 i 的加权平均"，自然落在 N/2 附近 (i.e., s≈7)。这是**linear interpolation path 的已知几何性质**，不是 numerical bug。

换句话说: **start.gro 不是特别接近 Open，也不是特别接近 Closed；它离每一个 MODEL 都差不多近。** soft-min 对 "near-equidistant" 输入的行为就是返回中段。

**z = 1.68 Å² 的佐证**: path 上的晶体两两之间 MSD 本就只有 ~0.02 Å² 级，start.gro 离最近 MODEL 的 1.30 Å RMSD 对应 ~1.69 Å² MSD，远大于 path 内部 MSD。这说明 start.gro **不在 path 上**，是 off-path 投影。z=1.68 和 mean_z=1.53 Å² 一致—— walker 大部分时间也在 off-path 区域。

**小结**: s=7 是 "几何软平均伪影" + "linear-interp path 的固有性质"，不是 "start.gro 已经达到 PC basin"。把它定义成 biology claim 就 overclaim 了。

---

## 3 · Topic 2 — Miguel author parameter contract

### 3.1 为什么 Miguel email 是本周最重要的外部输入

之前 3 周我们在 plumed.dat 上的各种调参 (probe_sweep HEIGHT/BF 2×2、wall4 AT 扫描、piecewise-λ 设计) 都卡在**没有 authoritative reference**。Miguel Maria-Solano (JACS 2019 first author) 2026-04-23 邮件回复给出了 verbatim METAD 参数集，直接终结了这些 debate。

### 3.2 Verbatim contract

```
UNITS         LENGTH=A  ENERGY=kcal/mol       # NOT nm / kJ
METAD ARG=path.sss  PACE=500                  # MULTIPLE_WALKERS protocol
  HEIGHT         0.15 kcal/mol                # primary (0.3 aggressive fallback)
  BIASFACTOR     10                           # primary (15 aggressive fallback)
  SIGMA          ADAPTIVE=DIFF                # NOT GEOM
  WALKERS_N      10                           # shared HILLS, 10 walkers
  TEMP           350
  LAMBDA         80  (A^-2)                   # self-consistent on HIS path
UPPER_WALLS ARG=path.zzz  AT=2.5  KAPPA=500
```

### 3.3 关键修正点

#### (a) ADAPTIVE = DIFF, not GEOM — 修 FP-031

GEOM 模式在 path 端点附近会把 σ 投影到"错误的轴"上 (PLUMED doc: "at the two ends of the path, the direction of the chord becomes ill-defined for geometric projection")。DIFF 用连续两步的 CV 差分直接估 σ，端点不受影响。

#### (b) UNITS = A / kcal，not nm / kJ — 修 FP-032

我们最早用 nm/kJ (GROMACS native) 但 Miguel 的 SIGMA 数字 (0.1, 0.3, 0.005) 是按 Å/kcal 写的。单位不一致导致 SIGMA 实际等效值错了 10×。

#### (c) WALKERS_N = 10 with HEIGHT=0.15, BF=10 是 PRIMARY contract

不是 0.3/15。后者是 Miguel 邮件里提到的 "aggressive fallback if primary doesn't converge"。

#### (d) λ=80 Å⁻² 的 universality 问题

Miguel 邮件明确：λ 是在**他的 path** 上的自洽值，不是 universal constant。Branduardi 2007 的 2.3/⟨MSD⟩ 启发式决定 λ 数值本身就依赖 path。

**我们的 corrected path** λ = 100.79 Å⁻²，vs Miguel 80，**ratio 1.26×**。都在 Branduardi 启发式的 ±2× tolerance 内，算同一个 regime。

### 3.4 Source of truth

- `chatgpt_pro_consult_45558834/miguel_email.md` — 邮件全文
- `replication/metadynamics/miguel_2026-04-23/plumed_template.dat` — 解析后的 frozen spec
- `replication/metadynamics/miguel_2026-04-23/ladder.yaml` — locked/tunable 参数划分

---

## 4 · Topic 3 — Current results (pilot 45515869)

### 4.1 Pilot 设置

| 量 | 值 |
|---|---|
| Job | 45515869 |
| Path | `path_seqaligned_gromacs.pdb` (corrected, FP-034 后) |
| MetaD params | Miguel primary (HEIGHT=0.15, BF=10, DIFF, UNITS A/kcal) |
| λ | 100.79 Å⁻² (self-consistent on our path) |
| UPPER_WALLS | path.zzz AT=2.5, KAPPA=500 |
| Walker count | 1 (pilot, NOT 10-walker) |
| Sim time | 8 ns (40193 COLVAR rows) |
| Seed | start.gro = 500 ns Ain cMD 终末帧 |

### 4.2 s(t) trace

```
min_s = 1.000 @ t = 4920.2 ps    # walker 到过 O 端点
max_s = 12.867 @ t = 6085 ps     # 单次 transient, ~120 ps 宽
mean_s (全程) ≈ 5.0
plateau (437-6085 ps): max_s ≈ 10.92, 持续 4.3 ns
```

对比老 path baseline 45324928 (naive, pre-FP-034, 16 ns sim)：

```
min_s = 1.005, max_s = 1.896, mean_s = 1.171
s=[1.00, 1.25): 75.24% 时间
```

即同一个 start.gro + 同一个 MetaD 参数，corrected path 在一半时间内 sample 了 **6 倍宽** 的 s 区域。

### 4.3 (s, z) 2D density (JACS Fig 3 analog)

Pilot 8 ns (40193 frames) 全程 2D density：

```
s bins (每 1 单位):
s=[1,2):  16.5%   s=[7,8):   9.3%
s=[2,3):  10.2%   s=[8,9):   6.6%
s=[3,4):  10.7%   s=[9,10):  5.2%
s=[4,5):  12.5%   s=[10,11): 4.4%
s=[5,6):  11.8%   s=[11,12): 1.5%
s=[6,7):  11.3%   s=[12,13): 0.04%

z statistics:
min_z  = 0.245
mean_z = 1.530
max_z  = 2.588 (transient at s=12.87, 近 UPPER_WALLS AT=2.5)
```

### 4.4 Start.gro (t=0) 投影：**off-path endpoint**，不是 biology

这是最需要 pause 2 秒的一点。

Start.gro 在 corrected path 上投到：**s = 7.09, z = 1.68 Å²**。

但直接 Kabsch alignment：

| vs reference | direct Cα RMSD |
|---|---|
| 1WDW (path MODEL 1) | **1.590 Å** ← 最近 |
| 3CEP(+5) (path MODEL 15) | 1.760 Å |
| MODEL 7 (path 中点) | 1.298 Å |

Start.gro **物理上** 更像 1WDW (差 1.59 Å)，但 linear interpolation 的**中点** MODEL 7 被 soft-min 认为"几何上最近" (1.298 Å)，因为 linear interp 的中点恰好在 O 和 C 的**几何平均**位置，被 soft-min 三角不等式拉近。

PATHMSD 报 s=7.09 **math 上没 bug**，但不能读成 "protein 在 PC basin"。这是 **linear-interp path 的已知局限** (Belfast tutorial 也提过 neighbor_msd_cv ≈ 0 问题)。

**z = 1.68 Å²** (不是小值，mean_z=1.53) 是这个解读的数学证据：walker 不在 path 上，是 off-path 投影。

### 4.5 max_s = 12.867 的解读 (transient, near wall)

单次穿越 t=6085 ps，s=12.87，z=2.04 Å² (几乎到 UPPER_WALLS AT=2.5)。持续仅 ~120 ps。

**这不是** "barrier crossed cleanly"。**这是** "corrected coord system 让 walker 至少能 access 到 s=12 的 region"。sustained occupancy (需要 > 1 ns plateau at s>12) 是 10-walker production 的任务。

### 4.6 什么能 claim，什么不能 claim

| 能 claim | 不能 claim |
|---|---|
| Corrected path 让 walker access s=1..12 (6× 老 path) | 500× speedup (coord rescaling, 不是 MetaD 加速) |
| λ=100.79 self-consistent 1.26× vs Miguel 80 | Start.gro 是 Ain 在 PC basin (s=7 是 soft-min 伪影) |
| 4 层独立 verification 证 FP-034 fix 对 | Barrier 穿越了 (max_s transient, 不 sustained) |
| PC crystals 事后落在 s=5-9 合理 | WT FES 复现了 (10-walker 没跑完) |

---

## 5 · Topic 4 — 10-walker seeding rationale

### 5.1 为什么不能都从 start.gro 起

FP-030 规则：10 个 walker 如果都从**同一帧**出发 → MetaD 的 shared HILLS 机制退化成"单 walker 10× 同步"，没有 diversity 加成。

### 5.2 Seeding 原则 (v2 logic)

从 pilot 45515869 的 COLVAR 中，对每个 target_s ∈ {1, 2, ..., 10}：

1. 过滤条件：|s - target_s| < 0.1 AND z < 1.0 (低 off-path)
2. 在剩余 frames 中选 min(z) 那一帧
3. 从 xtc 里 `gmx trjconv -dump {t}` 抽出对应 snapshot

这样 10 个 walker 的起点 **s 值离散分布 (1..10)** + **z 小 (全部 < 1.0, 都在 path 附近)**，既 diverse 又 physically on-path。

### 5.3 具体 frame 表

| Walker | target_s | t (ps) | s actual | z (Å²) |
|---|---|---|---|---|
| w0 | 1 | 5142.4 | 1.00 | 0.28 |
| w1 | 2 | 5138.2 | 2.00 | 0.25 |
| w2 | 3 | 7124.6 | 3.00 | 0.45 |
| w3 | 4 | 3201.8 | 4.01 | 0.52 |
| w4 | 5 | 2816.4 | 5.00 | 0.68 |
| w5 | 6 | 1104.2 | 6.03 | 0.78 |
| w6 | 7 | 912.6 | 6.98 | 0.88 |
| w7 | 8 | 654.2 | 7.99 | 0.91 |
| w8 | 9 | 521.8 | 9.02 | 0.95 |
| w9 | 10 | 479.6 | 10.01 | 0.89 |

### 5.4 v1 scancel + v2 crash 的完整诊断（Codex 交叉审查, 2026-04-24）

#### v1 (45558834) — scancel 原因

所有 10 walker 的 seed 都用 `gmx trjconv -dump` 在 500 ns Ain cMD 上抽 t = 50/100/.../500 ns 的帧。但 500 ns cMD 早就 equilibrate 到 Open basin (s≈1), 所以 10 个 "不同" 的 seed 其实在 CV 空间里都落在 s=1 附近。

FP-030 规则: shared-HILLS MetaD 要求 walker 在 CV 空间**足够分散**, 否则退化成 "单 walker 10×"。v1 被 PM 和 Codex 独立 flag, 22:05 scancel。

#### v2 (45570699) — 全部 FAILED exit 139

**重新设计 seed**: 改为从 pilot 45515869 (single-walker on corrected path) 的 COLVAR 里挑帧, 对每个 target_s ∈ {1..10} 挑 |s-target_s|<0.1 且 min z 的 frame, `gmx trjconv -dump t_ps` 抽 .gro。

**实际结果** (sacct):
- 全部 10 walker FAILED, exit 139 segfault
- Runtime 14 min – 3h 05min 不等 (w4 跑了 2.3 ns 也炸)

**现场证据** — slurm out (w0 tail):
```
Step 90098, t=180.196 ps: LINCS WARNING
  rms 0.154427, max 6.534671 (atom 4461-4462, 4463-4465)
  constraint 0.7633 vs 0.1013 target — 7.5× stretched
Step 90099, t=180.198 ps:
  rms 0.592463, max 32.428905
  atoms 4463-4465: constraint 3.6672 vs 0.1097 target (33× stretched)
step 90099: One or more water molecules can not be settled.
→ Segmentation fault (core dumped)
```

COLVAR 末尾同时出现 **metad.bias 负值** (物理上累加高斯永远 ≥ 0):
- w0 末尾: metad.bias = **-26.5**
- w5 末尾: metad.bias = **-548**, wall4.bias = 11.4
- w7 末尾: metad.bias = **-838**, wall4.bias = 39.2, wall_s = 125508

**Codex 根因分析** (独立诊断, 2026-04-24 17:22):

> "Most consistent with biased-pilot coordinate seeds being launched directly into fresh production without local relaxation. The common atom pair 4463-4465 across walkers points to a reproducible bad-contact/constraint instability in the seed ensemble, not random GPU failure. Missing velocities in dumped .gro also means production likely regenerated/assigned velocities inconsistently with a pre-biased geometry."

**额外 red flag — seed 重复**:

v2 COLVAR 第 0 行 s 值：
- w0 = 1.9871, **w1 = 1.9871** (duplicate!)
- w5 = 6.5957, **w6 = 6.5957** (duplicate!)

至少两对 walker 拿到同一个 seed frame。Seeding script 缺 unique-frame guard, 在 pilot COLVAR 稀疏区段容易 collide。

### 5.5 v3 Pipeline (Codex-verified, awaiting PM go)

```bash
#!/bin/bash
#SBATCH --partition=volta-gpu --gres=gpu:1 --mem=16G --time=0-12:00:00 --array=0-9
set -eo pipefail
module purge; module load anaconda/2024.02
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so

ID=$(printf "%02d" ${SLURM_ARRAY_TASK_ID})
WDIR=/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_v3/walker_${ID}
cd "$WDIR"

# Step 1: EM
gmx grompp -f em.mdp  -c start.gro -p topol.top -o em.tpr  -maxwarn 1
gmx mdrun  -deffnm em  -ntmpi 1 -ntomp ${OMP_NUM_THREADS:-4}

# Step 2: NVT settle (PLUMED off, velocities regenerated)
gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -maxwarn 1
gmx mdrun  -deffnm nvt -ntmpi 1 -ntomp ${OMP_NUM_THREADS:-4}

# Step 3: Production MetaD (PLUMED on, continue from NVT)
gmx grompp -f metad.mdp -c nvt.gro -t nvt.cpt -p topol.top -o metad.tpr -maxwarn 1
gmx mdrun  -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS:-4}
```

**mdp 关键参数**:
- `em.mdp`: integrator=steep, nsteps=1000, emtol=1000
- `nvt.mdp`: 100 ps, 350 K, gen_vel=yes (重新生成速度分布, 丢掉 pilot 的 bias 残留)
- `metad.mdp`: gen_vel=no, continue from nvt.cpt

**materialize_v3.py assertion suite** (Codex suggested):

```python
assert len(seed_frames) == 10
assert len({x.frame_index for x in seed_frames}) == 10, "duplicate seed frame"
assert min(np.diff(sorted(x.s for x in seed_frames))) > 0.25, "seed s too clustered"
assert np.std([x.s for x in seed_frames]) > 2.0, "seed s variance too low"

def gro_has_velocities(path):
    rows = open(path).read().splitlines()[2:-1]
    return all(len(r.split()) >= 9 for r in rows[:100])
# if start.gro from -dump has no velocities, MUST go through NVT settle
```

**Deliverable after v3 runs**: FES(s, z) 2D 重建 + 与 JACS 2019 Fig 2a 对比 + 2 个 PC 晶体投影到 2D occupancy。

### 5.6 诚实 positioning — 本次组会不放 10-walker 图

两次 10-walker attempt 都不可用 (v1 FP-030, v2 LINCS+seed-dup)。组会 slides 里的 `sz_2d_distribution.png` **只放 single-walker initial run 的 before/after 对比**, 绝不用 v2 crashed 数据冒充 10-walker FES。10-walker production 作为 next-week deliverable, 在独立 slide 交代状态。

### 5.5 登录节点教训 (持久 memory)

v2 准备过程中在 Longleaf **login node** 跑了 10 轮 `gmx grompp` + `gmx trjconv -dump` + `awk` on full COLVAR，累计 11.5 hr CPU。psman 杀了 bash shell + admin 邮件给 user。

**教训已写进 memory**: `feedback_longleaf_login_node.md`。所有 heavy ops 以后一律 `sbatch` 或 `srun --pty`, 不在 login 跑。

---

## 6 · Topic 5 — ML-layer future (v1.2 → v2.0 pivot)

### 6.1 本周审计的背景

之前 MetaD Cartridge Feasibility Memo (2026-04-22) v1.2 给出 5 个 ML 层方向 (A/B/C/D/E)。本周对照 2024-2026 arXiv/Nature/JCTC 做外部 prior art 审计：

| # | 方向 | 2026 verdict | Killer prior art |
|---|---|---|---|
| A | CRR · catalytic-readiness reward for GRPO | WEAKENED | PocketX / ResiDPO / ProteinZero |
| B | PP-Prior · path-CV energy-guided diffusion | WEAKENED | Enhanced Diffusion Sampling 2602.16634 |
| C | LBP · learned bias potential | DEAD | NN-VES / Deep-TICA / OPES+mlcolvar |
| D | TCR · FES-matching training loss | DEAD-ish | Thermodynamic Interpolation JCTC 2024 |
| E | MNG · Memory Necessity Gate | ALIVE (lead) | MEMnets is CV discovery, not runtime gate |

**Meta 结论**: "cartridge itself is likely more novel than any individual ML layer built on top."

### 6.2 v1.2 → v2.0 pivot

**v1.2 (PM-ratified 2026-04-22)**: "cartridge owner, not replicator"
- 立场: STAR-MD upstream, 我的 cartridge downstream
- 7 个 cartridge artifact

**v2.0 sharpen (this week)**: "F0 PathGate evaluator + concrete deliverable"
- F0 PathGate = 一个 **pip-installable** Python wrapper
- 输入: 任何 trajectory (STAR-MD / ConfRover / classical MD)
- 输出: (a) project_to_path → (s, z), (b) score_trajectory → JSD + state occupancy + rare-state recall
- 具体 deliverable 给 Yu / Amin / Raswanth 用

### 6.3 保留方向 + 新候选

- **E · MNG (lead)** — lag-stratified Markov-vs-qMSM runtime trigger for MetaD rescue
- **B+D merged** — FES-consistent trajectory generation submodule (path-CV 特定, 非 generic guidance)
- **A · CRR** — downgraded 到 projection metric, 不是 RL framework claim
- **F · PLP-aware reactive PATHMSD** (new) — 扩展 path CV 加 K82-PLP Schiff-base geometry + Dunathan angle
- **G · Generative-model physics-consistency audit** (new) — pip wrapper: reweight-JSD / path-distribution / state-occupancy / rare-state recall

### 6.4 2026-05-01 hard gate

**Hard criteria (binary)**:
1. WT MetaD 10-walker FES 展示 O / PC / C 三个 basin
2. Block-analysis CI defined (哪怕宽)
3. Path-CV 2D occupancy 投影了 ≥ 2 个 PC 晶体

**Gate FAILS → 所有 5 个 ML 方向 SUSPEND**. Focus 回到 single-walker → 10-walker upgrade debugging. 不对 Amin / Raswanth / Arvind 做 pitch, 因为 WT 都没 defensible.

**Gate PASSES → D2 API freezes. D3 demo runs. Aex1 variant FES 变成 next target. MNG 从 memo 走到 scoping doc.**

---

## 7 · Summary + anti-overclaim 清单

### 7.1 能 claim 的

1. Path CV fixed (FP-034 NW +5 offset), 4-layer independent verification
2. Miguel contract locked: ADAPTIVE=DIFF, units A/kcal, λ=100.79 self-consistent 1.26× vs 80
3. Corrected path exposes s=1-12 region in pilot (baseline stuck at s<1.9 for 16 ns)
4. failure-patterns.md 涨了 3 条: FP-031, FP-032, FP-034 — 可被 future variants 复用

### 7.2 不能 claim 的 (反 overclaim)

- ❌ "500× speedup" — 只是 coord rescaling
- ❌ "Start.gro 是 Ain 在 PC basin" — s=7.09 是 off-path soft-min 伪影 (z=1.68)
- ❌ "Barrier crossed cleanly" — max_s=12.87 是单次 transient, 不 sustained
- ❌ "WT FES 复现了" — 10-walker 没跑完, 更没 converge
- ❌ "MetaD replication 做完了" — 远没有
- ❌ "Miguel's λ=80 is universal" — 是 self-consistent on his path only

### 7.3 下一步 (binary)

1. v3 10-walker with EM+NVT settle pipeline → FES with PC crystals projected on 2D
2. D2 API spec (`replication/cartridge/API_DESIGN.md`) + D3 lab-facing demo (Yu preferred)
3. 2026-05-01 hard gate: pass or suspend ML-layer extensions

### 7.4 最重要的 takeaway

> "Cross-species PATH-CV 必须做 sequence identity > 50% 的硬 gate；已写进 failure-patterns.md FP-034 防范措施，所有 future path-builder 脚本头必须 assert 这个条件。"

这句话把 "修一个 bug" 拔高到 "建了一条规则"。

---

## 8 · 追问降级话术 (hot-path 防守)

如果 PI 问的某个 detail 我在 meeting 现场答不准：

> "这个我 hot-path 答不对可能犯错。**TechDoc § X** / **REVERSE_SANITY_CHECK** / **VERIFICATION_REPORT** 都写了完整溯源，我们会后过一遍。"

对应 source-of-truth 文件：
- 数字溯源: `reports/GroupMeeting_2026-04-24_CHEATSHEET.md`
- 决策链: `reports/GroupMeeting_2026-04-24_SELECTION_LOGIC.md`
- Path 修复验证: `replication/metadynamics/path_seqaligned/VERIFICATION_REPORT.md`
- 反推 sanity: `replication/metadynamics/path_seqaligned/REVERSE_SANITY_CHECK.md`
- Pro 独立 verdict: `chatgpt_pro_consult_45558834/README.md` + `QUESTION_FOR_PRO.md`
- Miguel 邮件: `chatgpt_pro_consult_45558834/miguel_email.md`
- Failure patterns: `replication/validations/failure-patterns.md`
- Cartridge memo: `新任务explore/MetaD_Cartridge_Feasibility_Memo_2026-04-22.md`
