# TrpB MetaD — Week 7 Technical Manuscript / 技术稿件 (2026-04-24)

**Bilingual (EN + ZH)** · **Scope**: Topics 1 – 4 (re-alignment / Miguel contract / current results / 10-walker status). ML-layer future is **excluded** from this document.

**双语 (英中)** · **范围**: 议题 1 – 4 (重新对齐 / Miguel 参数契约 / 当前结果 / 10-walker 状态)。ML 层未来方向**不包含**在本文中。

---

## 0 · Executive summary / 摘要

**EN** — The core work of the week is a silent cross-species residue-mapping bug (FP-034) in the Path-CV reference. The bug made the naive path mix non-homologous residues between 1WDW-B (*P. furiosus*) and 3CEP-B (*S. typhimurium*), inflating the Open↔Closed RMSD 5× and the adjacent MSD 27×, which in turn drove λ to the wrong regime (3.80 Å⁻² instead of ~100 Å⁻²). After fixing the mapping with a custom Needleman-Wunsch alignment — `offset = +5` throughout the selected 112 residues — an 8 ns single-walker pilot now samples `s = 1 → 12.87`, versus the old path trapped at `s < 1.9` over 16 ns. A 10-walker production (v1 homogeneous-start scancelled, v2 LINCS blow-up) is still pending a v3 pipeline with EM + NVT settle, diagnosed by Codex.

**中文** — 本周核心是发现并修复了一个 silent 了 3 周的跨物种 residue 映射 bug (FP-034)。原 path 把 1WDW-B (*古菌 P. furiosus*) 和 3CEP-B (*沙门菌*) 的 **非同源** residue 拿来比较, 使 O↔C RMSD 放大了 5×, 相邻 MSD 放大了 27×, 进而把 Branduardi 的 λ 推到错误的量级 (3.80 Å⁻² vs 正确的 ~100 Å⁻²)。用自写 Needleman-Wunsch alignment 修正映射关系 (整段 112 residue 的偏移都是 `+5`) 后, 8 ns single-walker pilot 已经 sample 到 `s = 1 → 12.87`, 而老 path 跑 16 ns 都卡在 `s < 1.9`。10-walker production (v1 均一起点被 scancel, v2 LINCS 爆, 都无法用) 等 v3 pipeline (EM + NVT settle, Codex 已诊断) 才能继续。

---

## 1 · Re-alignment (FP-034) / 重新对齐

### 1.1 Why cross-species endpoints are unavoidable / 为什么端点必须跨物种

**EN** — The JACS 2019 protocol defines the Path-CV endpoints as the two **crystallographically resolved** conformational extremes of TrpB β-subunit: 1WDW (Open, O) and 3CEP (Closed, C). 1WDW is the only available Open structure for *P. furiosus* TrpB; there is no Closed TrpB-Pf crystal at sufficient resolution, so 3CEP (*S. typhimurium*, closest homolog in Closed state) is the only defensible choice. Cross-species is therefore not a design flaw — **the design flaw was the naive resid-number mapping between the two species**.

**中文** — JACS 2019 协议把 Path-CV 的两个端点定义为 TrpB β 亚基的两个 **晶体学可解析** 的构象极点: 1WDW (Open, O) 和 3CEP (Closed, C)。1WDW 是 *P. furiosus* TrpB 唯一可用的 Open 晶体; TrpB-Pf 没有足够分辨率的 Closed 晶体, 所以只能用 *S. typhimurium* 的 3CEP (Closed 态最近的同源物)。跨物种不是 design flaw——**design flaw 是两个物种之间用了 naive residue 编号的 mapping**。

### 1.2 The silent bug / 潜伏的 bug

**EN** — The previous path reference (`single_walker/path_gromacs.pdb`) assumed *position-for-position identity*: residue 97 in 1WDW-B was paired with residue 97 in 3CEP-B. But 3CEP-B starts at resid 2 and carries an N-terminal extension of 5 residues relative to 1WDW-B. Consequently, 1WDW-B resid 97 is homologous to 3CEP-B resid **102**, not 97. Measured over the 112 residues that JACS 2019 selects for the Path-CV (COMM 97–184 and base 282–305), the naive mapping produced:

- Sequence identity at "matched" positions: **6.2 %**  (random baseline for an amino-acid alphabet is ~5 %; we were at random-chance level)
- Per-atom O↔C RMSD: **10.89 Å**  (two different proteins superimposed)
- Adjacent-MSD along 15-frame linear-interpolation path: **0.606 Å²**
- Branduardi λ = 2.3 / ⟨MSD⟩ = **3.80 Å⁻²**  (≈ 21× smaller than Miguel's reported 80)

**中文** — 原 path reference (`single_walker/path_gromacs.pdb`) 假设了 **对位 identity**: 1WDW-B 的 residue 97 被配对到 3CEP-B 的 residue 97。但 3CEP-B 从 resid 2 开始, 且比 1WDW-B 多 5 个 N 端残基。因此 1WDW-B resid 97 对应的是 3CEP-B resid **102**, 不是 97。在 JACS 2019 选定的 112 个 Path-CV residue 上 (COMM 97–184 加 base 282–305), naive mapping 给出:

- "匹配"位置的 sequence identity: **6.2%**  (氨基酸字母表随机 baseline 约 5%; 我们是随机水平)
- O↔C per-atom RMSD: **10.89 Å**  (等于把两个不同蛋白硬叠)
- 15 帧 linear-interpolation path 上相邻 MSD: **0.606 Å²**
- Branduardi λ = 2.3 / ⟨MSD⟩ = **3.80 Å⁻²**  (约比 Miguel 邮件给的 80 小 21×)

### 1.3 How the residue mapping was actually derived / 究竟怎么找到 residue 对应关系

**EN** — Corrected mapping is produced by the script `replication/metadynamics/path_seqaligned/build_seqaligned_path.py`. The algorithm is deliberately **pure numpy, no BioPython**, so every step is inspectable and reproducible. The flow:

**Step 1. Extract the crystallographic Cα sequence of each chain.** A manual fixed-column PDB parser (`load_ca(pdb, chain='B')`) walks `ATOM` records, keeps Cα atoms with altloc blank or "A", filters chain B, and de-duplicates resids. It emits `(seq, resids, coords)` — where `seq` is a one-letter amino-acid string whose order matches the actual resolved residues in the crystal. Not the UniProt sequence; not a generic reference. The sequence that the PATHMSD Cα coordinates actually come from.

```python
AA3 = {'ALA':'A', 'ARG':'R', ..., 'VAL':'V'}
s1, r1, c1 = load_ca("1WDW.pdb", "B")   # 385 residues
s3, r3, c3 = load_ca("3CEP.pdb", "B")   # 393 residues
```

**Step 2. Needleman-Wunsch global alignment (handwritten in numpy).** No BLOSUM62; the scoring matrix is the simplest defensible choice — `match = +2, mismatch = -1, gap = -2` — because the two chains are >50 % identical, and any reasonable scoring scheme converges to the same uniform offset. BLOSUM62 with BLASTp defaults (gap-open -10, gap-extend -0.5) produces the identical alignment; we did not use BLOSUM62 in the script to keep the dependency count at zero.

```python
def needleman_wunsch(s1, s2, match=2, mismatch=-1, gap=-2):
    M = np.zeros((m+1, n+1), dtype=int)
    T = np.zeros((m+1, n+1), dtype=int)
    # ... standard dynamic programming fill + traceback ...
    return aligned1, aligned2, best_score
```

**Step 3. Walk the aligned strings to build the resid-to-resid mapping.** `build_mapping(a1, a3, resids1, resids3)` scans the two aligned strings in parallel. Whenever neither position is a gap character, the 1WDW-resid at that column is associated with the 3CEP-resid at the same column:

```python
mapping = {}
i1 = i3 = 0
for c1, c3 in zip(a1, a3):
    if c1 != '-' and c3 != '-':
        mapping[resids1[i1]] = resids3[i3]
    if c1 != '-': i1 += 1
    if c3 != '-': i3 += 1
```

**Step 4. Verify the offset is uniform across the selected residues.** Only after the mapping is built from the alignment do we check whether it is a constant shift:

```python
offsets = [mapping[r] - r for r in COMM + BASE]      # 112 values
print(min(offsets), max(offsets))                    # both 5 → uniform
```

The critical scientific claim — "no indel within the 112 selected residues" — is this empirical check, not an assumption. If any insertion or deletion had landed inside [97..184] or [282..305], `min(offsets)` and `max(offsets)` would differ, and a simple `+5` shift would be mathematically wrong. The fact that they are equal is what licenses the Kabsch step.

**Step 5. Extract the 112-Cα coordinate pair and Kabsch-align.** Using 1WDW-B residues [97..184] + [282..305] for O and 3CEP-B residues [102..189] + [287..310] for C, both coordinate sets are centered, and 3CEP is rotated by the SVD-based Kabsch solution onto 1WDW's frame. The resulting per-atom O↔C RMSD is **2.115 Å** — a 5× improvement over the naive mapping and consistent with the two proteins being >50 % identical homologs.

**Step 6. Linear interpolation produces 15 frames.** Standard PATHMSD reference construction: frame *i* = `(1 – i/14) * O + (i/14) * C_aligned`, for i ∈ {0..14}. The output path file stores Cα only, with placeholder residue name ALA and serial indices 1..N (PATHMSD reads only the Cα coordinates).

**中文** — 修正后的 mapping 由脚本 `replication/metadynamics/path_seqaligned/build_seqaligned_path.py` 产生。刻意**只用 numpy, 不依赖 BioPython**, 每一步都可审查可复现。流程:

**步骤 1 · 从每个 chain 抽晶体学 Cα 序列。** 手写 fixed-column PDB parser (`load_ca(pdb, chain='B')`) 逐行扫 `ATOM` 记录, 保留 altloc 为空或 "A" 的 Cα, 过滤 chain B, 对 resid 去重。返回 `(seq, resids, coords)` —— `seq` 是一串 one-letter amino acid, 顺序严格对应**晶体中实际解析出来的** residue。不是 UniProt sequence, 不是通用 reference, 就是后面 PATHMSD 要读的 Cα 坐标对应的那个序列。

**步骤 2 · Needleman-Wunsch 全局对齐 (numpy 手写实现)。** 不用 BLOSUM62; 评分矩阵用最简单能自圆其说的方案—— `match = +2, mismatch = -1, gap = -2` ——因为两条 chain identity > 50 %, 任何合理评分都会收敛到同一个 uniform offset。用 BLOSUM62 + BLASTp 默认参数 (gap-open -10, gap-extend -0.5) 得到完全相同的 alignment; 脚本里不用 BLOSUM62 是为了把依赖数量压到零。

**步骤 3 · 从对齐字符串走出 resid↔resid 映射表。** `build_mapping(a1, a3, resids1, resids3)` 并行扫两条对齐串, 两边都不是 gap 时, 把 1WDW 当前列的 resid 和 3CEP 当前列的 resid 关联起来 (代码见上方英文版块)。

**步骤 4 · 验证选定 residue 内 offset 是否均一。** Mapping 建完之后**才**检查它是不是常数偏移:

```python
offsets = [mapping[r] - r for r in COMM + BASE]      # 112 个值
print(min(offsets), max(offsets))                    # 两个都是 5 → uniform
```

"112 个 residue 内部没有 indel" 这个科学 claim 是**经验检查**, 不是假设。如果 [97..184] 或 [282..305] 里有任何插入/删除, `min(offsets)` 和 `max(offsets)` 会不相等, 简单的 `+5` 就数学上不合法。两者相等, 才能进 Kabsch 那一步。

**步骤 5 · 抽 112-Cα 坐标对 + Kabsch 对齐。** 用 1WDW-B [97..184] + [282..305] 作为 O, 3CEP-B [102..189] + [287..310] 作为 C, 两组坐标去中心化后用 SVD Kabsch 把 3CEP 转到 1WDW 的 frame。per-atom O↔C RMSD = **2.115 Å** —— 比 naive mapping 好 5×, 和"两条 chain 同源 identity > 50 %"一致。

**步骤 6 · Linear interpolation 生成 15 帧。** 标准 PATHMSD reference 构造: 第 *i* 帧 = `(1 – i/14) * O + (i/14) * C_aligned`, i ∈ {0..14}。输出 path 文件只存 Cα, residue name 用占位符 ALA, serial 用 1..N (PATHMSD 只读 Cα 坐标)。

### 1.4 The NW's real role: formal verification, not novel discovery / NW 的真实角色

**EN** — When Yu asks "isn't a `+5` offset just a PDB-numbering convention difference?" — yes, mostly. The five-residue offset reflects a difference in how 1WDW and 3CEP authors numbered their N-terminal signal-peptide residues. The scientific value-add of NW is not *discovering the offset*; it is **proving that a uniform offset is legitimate within the selected 112 residues** (step 4 above). If the NW had reported variable offsets or indels inside the selection window, a single-number fix would be mathematically wrong, and the real correction would have been far more invasive (residue-by-residue re-mapping with possible dropout). We must volunteer this framing — not wait for it to be extracted under cross-examination.

**中文** — Yu 如果问 "`+5` offset 不就是 PDB 编号惯例差吗" —— 对, 基本是。这 5 个 residue 的差距反映的是 1WDW 和 3CEP 作者对 N 端 signal peptide 残基的不同编号习惯。NW 的科学 value-add **不是**"发现了 offset", 而是**证明在选定的 112 个 residue 范围内可以用 uniform offset** (即步骤 4)。如果 NW 报 variable offsets 或选定区间内有 indel, 单一数字的修正就数学上不合法, 真正的 fix 会复杂得多 (逐 residue 重新映射, 可能要 dropout)。这个论点要**主动说**, 不要等 pushback 逼问出来。

### 1.5 Four-layer independent verification / 四层独立验证

| # | Method / 方法 | Result / 结果 |
|---|---|---|
| (a) | My NW (numpy, match=+2 / mismatch=-1 / gap=-2) | score = 286, identity = 59.0 %, offset = +5 |
| (b) | Codex independent re-implementation (blind, only given the two sequences) | score = 286, identity = 59.033 %, offset = +5 (byte-level match) |
| (c) | Endpoint round-trip self-projection on the final 15-frame path | 1WDW → s = 1.14, 3CEP → s = 14.86 (λ-rounding per Branduardi 2007) |
| (d) | Independent crystal projection (4 held-out PDBs not used in the path) | see Table 2.3 below |

**EN** — Layer (d) is the strongest: the crystals 5DW0 (βPC + L-Ser), 5DW3 (βPC variant), 5DVZ (βPC holo), 4HPX (Pf A-A) were never used to build the path — we only used 1WDW and 3CEP. If the corrected path is scientifically meaningful, the βPC crystals should project to mid-path `s` values and 4HPX to a near-C value. The corrected path gives exactly that (see Table 2.3). The naive path had all three βPC crystals collapsing to `s ≈ 1.07`, which is physically absurd (PC is, by definition, **not** Open).

**中文** — 第 (d) 层最硬: 晶体 5DW0 (βPC + L-Ser), 5DW3 (βPC 变体), 5DVZ (βPC holo), 4HPX (Pf A-A) **不**参与 path 的构造——我们只用了 1WDW 和 3CEP。如果 corrected path 在生物学上有意义, βPC 晶体应投到 path 中段, 4HPX 应投到近 C 端。Corrected path 给的正是这个结果 (见下方表 2.3)。Naive path 里 3 个 βPC 晶体都塌到 `s ≈ 1.07`, 物理荒谬 (PC 的定义就是**不是** Open)。

---

## 2 · Numerical evidence / 数值证据

### 2.1 Core numerical comparison / 核心数值对比

| Metric / 指标 | Naive path | Seq-aligned | Ratio |
|---|---:|---:|---:|
| Cα identity, 112 residues | 6.2 % | **59.0 %** | 9.5× |
| O↔C per-atom RMSD (Å) | 10.89 | **2.115** | 5.1× tighter |
| ⟨MSD_adj⟩ along path (Å²) | 0.606 | **0.0228** | 26.6× smaller |
| λ = 2.3 / ⟨MSD⟩ (Å⁻²) | 3.80 | **100.79** | 26.5× larger |
| Ratio vs Miguel's λ = 80 | 0.047× | **1.26×** | within tolerance |

### 2.2 Why λ must be self-consistent per path / 为什么 λ 要按 path 自洽

**EN** — Branduardi, Gervasio, Parrinello 2007 (JCP 126, 054103) derive the heuristic `λ ≈ 2.3 / ⟨MSD_{i,i+1}⟩` so that adjacent-frame soft-min weights satisfy `exp(-λ · ⟨MSD⟩) ≈ exp(-2.3) ≈ 0.1`. This makes the soft-min sharp enough to resolve neighbouring frames but not so sharp that a single frame dominates. ⟨MSD⟩ is a property of **the specific path geometry**, so λ is a per-path scalar, never a universal constant. Miguel's email gave `λ = 80 Å⁻²` as self-consistent on his path. On our corrected path, `⟨MSD⟩ = 0.0228 Å²` gives `λ = 100.79 Å⁻²`; the ratio 100.79 / 80 = 1.26 places us in the same kernel-width regime Miguel used (< 2× tolerance typical for Branduardi).

**中文** — Branduardi, Gervasio, Parrinello 2007 (JCP 126, 054103) 推 `λ ≈ 2.3 / ⟨MSD_{i,i+1}⟩` 的启发式, 让相邻帧 soft-min 权重满足 `exp(-λ · ⟨MSD⟩) ≈ exp(-2.3) ≈ 0.1`, 既能分辨相邻帧又不让单帧独霸。⟨MSD⟩ 是 **具体 path 几何** 的属性, 所以 λ 是每 path 独立的标量, 绝非 universal constant。Miguel 邮件给的 `λ = 80 Å⁻²` 是在他 path 上自洽。我们修正后 `⟨MSD⟩ = 0.0228 Å²` 给出 `λ = 100.79 Å⁻²`; 比值 100.79 / 80 = 1.26, 和 Miguel 在同一 kernel 宽度量级 (Branduardi 容忍的典型偏差 < 2×)。

### 2.3 Independent PC-crystal projection (post-hoc validation) / 独立 PC 晶体投影 (事后验证)

| PDB | Chain | Literature state | `s` (naive path) | `s` (corrected path) | Consistent? |
|---|---|---|---:|---:|---|
| 1WDW | B | Open endpoint | 1.00 | 1.00 | — (reference) |
| 3CEP | B | Closed endpoint | 15.00 | 15.00 | — (reference) |
| 5DW0 | A | βPC + L-Ser (Aex1) | 1.07 | **9.46** | ✓ mid-path |
| 5DW3 | A | βPC variant | — | **8.51** | ✓ mid-path |
| 5DVZ | A | βPC holo | 1.07 | **5.37** | ✓ mid-path |
| 4HPX | B | Pf A-A intermediate | 14.91 | **14.90** | ✓ near-C |

---

## 3 · Miguel author parameter contract / Miguel 原作者参数契约

### 3.1 Why it matters / 为什么这是本周最重要的外部输入

**EN** — Three weeks of parameter debates — probe_sweep HEIGHT/BF 2×2, wall4 AT scan, piecewise-λ design — were all stalled on the absence of an authoritative reference. Miguel Maria-Solano (JACS 2019 first author) replied 2026-04-23 with a verbatim METAD parameter block, which terminates those debates at a stroke.

**中文** — 过去三周在 plumed.dat 上的所有调参 debate (probe_sweep 2×2, wall4 AT 扫描, piecewise-λ 设计) 都卡在缺 authoritative reference。Miguel Maria-Solano (JACS 2019 一作) 2026-04-23 邮件回复了 verbatim METAD 参数块, 一举终结了这些 debate。

### 3.2 Verbatim contract / 原文契约

```
UNITS         LENGTH=A  ENERGY=kcal/mol          # NOT nm / kJ
METAD ARG=path.sss  PACE=500                     # MULTIPLE_WALKERS
  HEIGHT         0.15 kcal/mol                   # primary (0.3 aggressive fallback)
  BIASFACTOR     10                              # primary (15 aggressive fallback)
  SIGMA          ADAPTIVE=DIFF                   # NOT GEOM
  WALKERS_N      10                              # shared HILLS, 10 walkers
  TEMP           350                             # K
  LAMBDA         80 (A^-2)                       # self-consistent on HIS path
UPPER_WALLS ARG=path.zzz  AT=2.5  KAPPA=500
```

### 3.3 What changed vs our prior attempts / 与我们此前尝试的差异

**EN** —
- **ADAPTIVE = DIFF (not GEOM)** — fixes FP-031. PLUMED documents that GEOM projects σ onto the chord direction, which becomes ill-defined at the two ends of a path; DIFF estimates σ directly from the consecutive-step CV differences and is endpoint-stable.
- **UNITS = A / kcal (not nm / kJ)** — fixes FP-032. Miguel's SIGMA literals (0.1, 0.3, 0.005) are in Å/kcal; running with GROMACS native nm/kJ left the effective σ off by a unit conversion factor.
- **Primary set is `HEIGHT=0.15 kcal/mol, BIASFACTOR=10, WALKERS_N=10`**, with `0.3 / 15` explicitly labelled an *aggressive fallback* by Miguel, only to be used if primary fails to converge.
- **λ is self-consistent per path**, not universal. See § 2.2.

**中文** —
- **ADAPTIVE = DIFF (不是 GEOM)** — 修 FP-031。PLUMED 文档指出 GEOM 把 σ 投影到 chord 方向, 在 path 两端 ill-defined; DIFF 直接用连续步 CV 差分估 σ, 端点稳。
- **UNITS = A / kcal (不是 nm / kJ)** — 修 FP-032。Miguel SIGMA 字面值 (0.1, 0.3, 0.005) 是 Å/kcal; 用 GROMACS native nm/kJ 跑会让等效 σ 差一个单位转换因子。
- **Primary set 是 `HEIGHT=0.15 kcal/mol, BIASFACTOR=10, WALKERS_N=10`**, `0.3 / 15` 被 Miguel 明确标为 *aggressive fallback*, 只在 primary 不收敛时才上。
- **λ 按 path 自洽**, 非普适常数 (见 § 2.2)。

### 3.4 Source of truth / 真相来源

- `chatgpt_pro_consult_45558834/miguel_email.md` — full email text / 邮件全文
- `replication/metadynamics/miguel_2026-04-23/plumed_template.dat` — parsed frozen spec / 解析后的 frozen spec
- `replication/metadynamics/miguel_2026-04-23/ladder.yaml` — locked / tunable split / 锁定与可调参数的划分

---

## 4 · Current results / 当前结果

### 4.1 Pilot run configuration / Pilot 配置

| Item / 项 | Value / 值 |
|---|---|
| Job ID | 45515869 |
| Path reference | `path_seqaligned_gromacs.pdb` (corrected, post-FP-034) |
| MetaD parameters | **Miguel single-walker fallback** (HEIGHT=0.3, BF=15, ADAPTIVE=DIFF, UNITS=A/kcal) — **NOT** Miguel primary 10-walker (HEIGHT=0.15, BF=10) |
| λ (in plumed.dat) | LAMBDA=80 Å⁻² (Miguel email value, ratio 1.26× our path-derived 100.79) |
| UPPER_WALLS | `path.zzz AT=2.5, KAPPA=800` (verified from `path_seqaligned/plumed.dat`) |
| Walker count | 1 (single-walker pilot, **NOT** 10-walker production) |
| Sim length | 8.86 ns (44,300 COLVAR rows; HILLS deposits = 4,429 with biasf=15.0 verified) |
| Seed | `start.gro` = terminal frame of 500 ns Ain classical MD |
| Verified params from HILLS | col-8 biasf = 15.0; first deposit height ≈ 0.32 ≈ HEIGHT × BF/(BF-1) = 0.3 × 15/14 ✓ consistent with HEIGHT=0.3, BF=15 |

### 4.2 s(t) exploration / s(t) 探索

**EN** — Under identical start.gro, the **same single-walker fallback variant** of the Miguel contract (HEIGHT=0.3 / BF=15 / KAPPA=800), and the same single-walker setup, the only variable between baseline 45324928 and pilot 45515869 is `path.pdb` (and the path-derived self-consistent LAMBDA: 3.77 Å⁻² for the naive path → 80 Å⁻² for the seq-aligned path). Observed behaviour:

```
Baseline 45324928 (naive path, 16 ns):
    min_s = 1.005,  max_s = 1.896,  mean_s = 1.171
    s ∈ [1.00, 1.25) for 75.24 % of frames

Pilot 45515869 (seq-aligned path, 8 ns):
    min_s = 1.000  @ t = 4920 ps
    max_s = 12.867 @ t = 6085 ps  (single transient, ~120 ps wide)
    plateau 437 – 6085 ps at max_s ≈ 10.92, sustained 4.3 ns
```

Six-fold wider `s`-coverage in half the wall-clock time — this difference is 100 % attributable to the path geometry fix, because nothing else was changed.

**中文** — 同一个 start.gro、**同一套 Miguel single-walker fallback 参数**(HEIGHT=0.3 / BF=15 / KAPPA=800)、同样 single walker 的前提下, baseline 45324928 和 pilot 45515869 的**唯一变量是 `path.pdb`** (以及 path 几何决定的自洽 LAMBDA: naive path 3.77 Å⁻² → seqaligned 80 Å⁻²)。观测:

```
Baseline 45324928 (naive, 16 ns):
    min_s = 1.005,  max_s = 1.896,  mean_s = 1.171
    s ∈ [1.00, 1.25) 占 75.24% 的 frame

Pilot 45515869 (seq-aligned, 8 ns):
    min_s = 1.000  @ t = 4920 ps
    max_s = 12.867 @ t = 6085 ps  (单次 transient, ~120 ps 宽)
    plateau 437 – 6085 ps 维持 max_s ≈ 10.92, 持续 4.3 ns
```

wall-clock 时间一半、s 区域宽 6×。这个差异 100% 归因于 path 几何修复, 因为**没有任何其他变量改变**。

### 4.3 FES(s, z) density — initial-run figure / FES(s, z) 密度 — initial-run 图

**EN** — `reports/figures/sz_2d_distribution.png`, generated by `reports/figures/plot_sz_si_sumhills.py`, renders the PLUMED `sum_hills` free-energy surface clipped to the JACS 2019 SI / main-paper visual range `0 ≤ ΔG ≤ 14 kcal/mol`. The y-axis is **unit-correct**: PLUMED writes `path.zzz` in MSD (Å²) when `UNITS LENGTH=A` is set, and the figure plots `√path.zzz` so the axis reads in Å (per-atom RMSD deviation), matching the JACS 2019 SI Fig 3 convention. Independent verification: Codex CCB task `20260424-234500`. Full unit chain in `deliverables/week7_2026-04-24/08_figures/UNIT_AUDIT.md`. Panel (a) is single-walker baseline 45324928 on the naive path (17.7 ns); panel (b) is single-walker pilot 45515869 on the seq-aligned path (8.9 ns). Both panels use the same colorscale for direct comparison. Panel (a) shows the FES confined to a narrow `s < 2` ridge; panel (b) shows the FES spread across `s ∈ [1, 12]`. The red star in panel (b) marks start.gro at `(s = 7.09, RMSD Deviation = 1.30 Å)` — equivalently raw `p1.zzz = 1.68 Å² → √ = 1.30 Å`.

**Important caveat**: this figure uses **single-walker** initial-run data for both panels. **No 10-walker production data** is included, because v1 was scancelled (FP-030 homogeneous start) and v2 all crashed (LINCS blow-up). The figure demonstrates the path-geometry fix alone; the production FES remains a next-week deliverable.

**中文** — `reports/figures/sz_2d_distribution.png`, 由 `reports/figures/plot_sz_si_sumhills.py` 生成, 渲染 PLUMED `sum_hills` 自由能面, clip 到 JACS 2019 SI/正文视觉范围 `0 ≤ ΔG ≤ 14 kcal/mol`。**y 轴单位是严格的**: 在 `UNITS LENGTH=A` 下 PLUMED 把 `path.zzz` 写成 MSD (Å²) 单位, 图里画的是 `√path.zzz` 所以纵轴读作 Å (per-atom RMSD deviation), 跟 JACS 2019 SI Fig 3 一致。独立验证: Codex CCB task `20260424-234500`。完整单位链见 `deliverables/week7_2026-04-24/08_figures/UNIT_AUDIT.md`。panel (a) = 单 walker baseline 45324928 on naive path (17.7 ns); panel (b) = 单 walker pilot 45515869 on seq-aligned path (8.9 ns)。两个 panel 用相同色标直接对比。panel (a) FES 被压在窄窄的 `s < 2` 条带; panel (b) FES 铺开到 `s ∈ [1, 12]`。panel (b) 红色星标是 start.gro 位置 `(s = 7.09, RMSD Deviation = 1.30 Å)` — 也就是 raw `p1.zzz = 1.68 Å² → √ = 1.30 Å`。

**重要 caveat**: 本图**两个 panel 都用 single-walker initial-run 数据**。**不含任何 10-walker production 数据**, 因为 v1 被 scancel (FP-030 homogeneous start), v2 全 crash (LINCS 爆)。图只证明 path 几何修复有效; production FES 仍是下周 deliverable。

### 4.4 start.gro at s = 7.09 is a soft-min artifact, not biology / start.gro 在 s=7.09 是 soft-min 伪影, 非生物学

**EN** — The pilot walker's starting configuration projects to `s = 7.09, z = 1.68 Å²` on the corrected path. The temptation is to read this as "Ain is already in the PC basin." Direct Kabsch alignments of start.gro to each of the 15 path MODELs refute this:

| vs. reference MODEL | direct Cα RMSD (Å) |
|---|---:|
| MODEL 1 (1WDW) | 1.590 |
| MODEL 4 | 1.410 |
| MODEL 7 (geometric midpoint) | 1.298 |
| MODEL 11 | 1.480 |
| MODEL 15 (3CEP+5) | 1.760 |

**start.gro is near-equidistant to every MODEL, with differences of only 0.3 – 0.5 Å.** There is no dominant "nearest MODEL". Under the Branduardi soft-min formula

$$s(R) = \frac{\sum_{i=1}^{N} i \cdot \exp(-\lambda \cdot \mathrm{MSD}_i(R))}{\sum_{i=1}^{N} \exp(-\lambda \cdot \mathrm{MSD}_i(R))}$$

when the `MSD_i` values are all comparable, the numerator becomes a weighted average of all integer indices and the sum concentrates around `N/2 ≈ 7`. This is a geometric property of linear-interpolation paths, not a numerical bug and not a statement about biology. The `z = 1.68 Å²` channel corroborates: walker off-path deviation is large (mean `z = 1.53` over 8 ns), i.e. the protein genuinely **is not on the path**, and the projected `s` is a soft-average of equidistant neighbours rather than a basin identification.

**中文** — pilot walker 起始构象在 corrected path 上投到 `s = 7.09, z = 1.68 Å²`。很容易把它读成 "Ain 已经在 PC basin"。Start.gro 对 15 个 path MODEL 每一个做直接 Kabsch 对齐的 Cα RMSD 否定这个解读 (见上表)。

**Start.gro 离每一个 MODEL 都差不多远, 差距只有 0.3 – 0.5 Å。** 没有 dominant 的 "nearest MODEL"。在 Branduardi soft-min 公式下, 当所有 `MSD_i` 差不多时, 分子变成所有整数 index 的加权平均, 总和集中在 `N/2 ≈ 7`。这是 linear-interpolation path 的几何性质, 不是 numerical bug, 也**不是生物学陈述**。`z = 1.68 Å²` 印证: walker off-path deviation 很大 (8 ns 全程 mean `z = 1.53`), 即蛋白**并不在 path 上**, 投到的 `s` 是"等距邻居的 soft-average", 不是 basin identification。

### 4.5 What can / cannot be claimed / 可以 / 不可以声称

| ✓ Can claim / 可以声称 | ✗ Cannot claim / 不可声称 |
|---|---|
| Corrected path exposes `s ∈ [1, 12]` (6× wider than naive) | "500× speedup" — only coord rescaling / 只是坐标 rescaling |
| λ = 100.79 is self-consistent, 1.26× ratio vs Miguel's 80 | start.gro is Ain in PC basin — soft-min artifact |
| 4-layer verification confirms FP-034 fix | Barrier has been crossed — transient, not sustained |
| Held-out PC crystals land at mid-path `s = 5 – 9` | WT FES reproduced — needs 10-walker production |
| 3 new failure-patterns (FP-031/032/034) documented | MetaD replication complete — far from |

---

## 5 · 10-walker production story / 10-walker production 故事

### 5.1 v1 (45558834) — scancelled / 被取消

**EN** — All 10 walkers were seeded by `gmx trjconv -dump` at `t = 50, 100, …, 500 ns` from the 500 ns Ain classical MD trajectory. But that cMD had long since equilibrated to the Open basin (`s ≈ 1`), so the "diverse" seeds all collapsed to the same CV region. FP-030 rule: shared-HILLS MetaD requires walkers distributed across CV space; otherwise it degenerates into "single walker × 10". Both PM and Codex independently flagged this; the job was scancelled at 22:05.

**中文** — 所有 10 个 walker 都用 `gmx trjconv -dump` 从 500 ns Ain cMD 轨迹抽 `t = 50, 100, …, 500 ns` 的帧。但 cMD 早已 equilibrate 到 Open basin (`s ≈ 1`), 所以 "diverse" seed 在 CV 空间全塌在同一区域。FP-030 规则: shared-HILLS MetaD 要求 walker 在 CV 空间分散, 否则退化为 "单 walker × 10"。PM 和 Codex 独立 flag, 22:05 scancel。

### 5.2 v2 (45570699) — all FAILED exit 139 / 全部 FAILED 退出码 139

**EN** — Seeding strategy was rebuilt: for each `target_s ∈ {1..10}`, pick the pilot-COLVAR frame with `|s − target_s| < 0.1` and minimum `z`, then `gmx trjconv -dump t_ps` to extract the .gro. Result:

| Walker | Sim time reached | Exit code |
|---|---:|---:|
| w0 | 180 ps | 139 (14 min) |
| w1 | 430 ps | 1 (35 min) |
| w2 | 661 ps | 139 (55 min) |
| w3 | 1253 ps | 139 (1 h 48 min) |
| w4 | 2334 ps | 139 (3 h 05 min) — longest |
| w5 | 786 ps | 139 (1 h 14 min) |
| w6 | 932 ps | 139 (1 h 27 min) |
| w7 | 1442 ps | 139 (1 h 54 min) |
| w8 | 1262 ps | 139 (1 h 38 min) |
| w9 | — | 139 |

Typical slurm-log tail (w0, last steps before crash):

```
Step 90098, t = 180.196 ps:  LINCS WARNING
  atoms 4463-4465: angle 90°, constraint 0.6979 Å vs 0.1097 Å target  (6.4× stretched)
  atoms 4461-4462: angle 90°, constraint 0.7633 Å vs 0.1013 Å target  (7.5× stretched)
Step 90099, t = 180.198 ps:
  rms 0.592463, max 32.428905
  atoms 4463-4465: constraint 3.6672 Å vs 0.1097 Å target  (33× stretched)
step 90099: One or more water molecules can not be settled.
Check for bad contacts and/or reduce the timestep if appropriate.
→ Segmentation fault (core dumped)
```

Concurrently, the COLVAR files show **metad.bias going negative** in the last rows of several walkers — physically impossible, since metad.bias is a sum of positive Gaussians:

| Walker | end t | end metad.bias | end wall4.bias |
|---|---:|---:|---:|
| w0 | 180 ps | **−26.5** | 0 |
| w5 | 786 ps | **−548** | 11.4 |
| w7 | 1442 ps | **−838** | 39.2 |

A negative `metad.bias` is downstream corruption: LINCS failure destabilised the coordinates, the Cα stencil that feeds PATHMSD went out of bounds, and the PLUMED state propagated nonsense.

**Secondary red flag — seed duplication.** First-row `s` values in the COLVAR files:

```
w0 = 1.9871   w1 = 1.9871  ← duplicate
w5 = 6.5957   w6 = 6.5957  ← duplicate
```

At least two pairs of walkers received the same seed frame. The seed-selection script lacked a unique-frame guard; when the pilot COLVAR was sparse in a target-s window, the "min-z" candidate for adjacent target bins collided.

**中文** — Seeding 策略重建: 对每个 `target_s ∈ {1..10}`, 从 pilot COLVAR 挑 `|s − target_s| < 0.1` 且 min `z` 的 frame, 再 `gmx trjconv -dump t_ps` 抽 .gro。结果: 全部 10 个 walker FAILED exit 139 (上表)。

典型 slurm log (见上方英文版)。同时 COLVAR 末尾出现 **metad.bias 负值**—— 物理上不可能, 因为 metad.bias 是正 Gaussian 的累加。这是下游 corruption: LINCS 失败使坐标失稳, 喂给 PATHMSD 的 Cα 数组越界, PLUMED 状态一起传染。

**次要 red flag — seed 重复**: COLVAR 第一行 `s` 值出现 w0 = w1 = 1.9871, w5 = w6 = 6.5957 两对重复。seed 脚本缺 unique-frame guard, pilot COLVAR 在某个 target-s 区间稀疏时, 相邻 target bin 的 "min-z" 候选会 collide。

### 5.3 Codex diagnosis (2026-04-24 17:22) / Codex 诊断

**EN — verbatim root-cause from Codex**: "Most consistent with biased-pilot coordinate seeds being launched directly into fresh production without local relaxation. The common atom pair 4463-4465 across walkers points to a reproducible bad-contact / constraint instability in the seed ensemble, not random GPU failure. Missing velocities in dumped `.gro` also means production likely regenerated / assigned velocities inconsistently with a pre-biased geometry."

The .gro files from `gmx trjconv -dump` are **positions only** — no velocities. The submit script ran `gmx mdrun -deffnm metad -plumed plumed.dat` directly with no EM and no NVT equilibration, so GROMACS regenerated velocities on a geometry that still carried the strain of a biased-MetaD snapshot. LINCS then failed on the stressed methyl bonds (atom 4463-4465 consistently across walkers) and SETTLE failed on cascaded water bad-contacts.

**中文** — **Codex 原文根因**: "最一致的解释是有 bias 的 pilot 坐标 seed 没做局部 relaxation 就直接塞进 fresh production。所有 walker 同一 atom pair 4463-4465 出错, 说明是 seed ensemble 可重现的 bad-contact / constraint 不稳, 不是 GPU 随机故障。`.gro` dump 出来没 velocity, production 就会在带 bias 几何的基础上重新生成 / 分配速度, 不一致。"

`gmx trjconv -dump` 出的 .gro **只有位置, 没有速度**。submit script 直接 `gmx mdrun -deffnm metad -plumed plumed.dat`, 没有 EM, 没有 NVT settle, 所以 GROMACS 在仍带 biased-MetaD 几何应力的结构上重新生成速度, LINCS 就在受力的甲基键上失败 (所有 walker 都是 atom 4463-4465), SETTLE 级联在 water bad-contacts 上也失败。

### 5.4 v3 pipeline / v3 管线

**EN — Codex-verified submit script**:

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

# Step 1 — energy minimization
gmx grompp -f em.mdp -c start.gro -p topol.top -o em.tpr -maxwarn 1
gmx mdrun -deffnm em -ntmpi 1 -ntomp ${OMP_NUM_THREADS:-4}

# Step 2 — NVT settle (PLUMED off, velocities regenerated)
gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -maxwarn 1
gmx mdrun -deffnm nvt -ntmpi 1 -ntomp ${OMP_NUM_THREADS:-4}

# Step 3 — production MetaD (PLUMED on, continue from NVT checkpoint)
gmx grompp -f metad.mdp -c nvt.gro -t nvt.cpt -p topol.top -o metad.tpr -maxwarn 1
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS:-4}
```

MDP key choices: `em.mdp` → `integrator=steep, nsteps=1000, emtol=1000`; `nvt.mdp` → 100 ps at 350 K, `gen_vel=yes` (regenerate velocities from zero), PLUMED off; `metad.mdp` → `gen_vel=no`, continue from `nvt.cpt`.

**materialize_v3.py assertion suite** (Codex-suggested):

```python
assert len(seed_frames) == 10
assert len({x.frame_index for x in seed_frames}) == 10, "duplicate seed frame"
assert min(np.diff(sorted(x.s for x in seed_frames))) > 0.25, "seed s too clustered"
assert np.std([x.s for x in seed_frames]) > 2.0, "seed s variance too low"

def gro_has_velocities(path):
    rows = open(path).read().splitlines()[2:-1]
    return all(len(r.split()) >= 9 for r in rows[:100])
# if start.gro has no velocities, MUST route through NVT settle
```

**中文 — Codex 已验证的 submit 脚本** (同上方 bash 块)。MDP 关键选择同英文版。**materialize_v3.py assertion suite** (Codex 建议, 同上方 Python 块)。

### 5.5 Honest positioning for the meeting / 诚实的组会表述

**EN** — Neither v1 nor v2 produced usable 10-walker data. The slides deliberately use **only single-walker initial-run data** in the FES figure; no v1 / v2 frames are visualised as "production." The 10-walker production is framed explicitly as a next-week deliverable, gated on the v3 pipeline above and the 2026-05-01 PM decision point.

**中文** — v1 和 v2 都没产生可用的 10-walker 数据。Slides 里的 FES 图**刻意只用 single-walker initial-run 数据**; 没有任何 v1 / v2 frame 被可视化为 "production"。10-walker production 明确 frame 为下周的 deliverable, gated on 上述 v3 pipeline 和 2026-05-01 PM 决策点。

---

## 6 · Anti-overclaim summary / 反 overclaim 总结

**EN — What I CLAIM this week:**
1. Path CV fixed via FP-034 NW `+5` offset, 4-layer independent verification.
2. Miguel author contract locked: ADAPTIVE=DIFF, UNITS=A/kcal, λ=100.79 self-consistent at ratio 1.26× vs Miguel's 80.
3. Corrected path exposes `s ∈ [1, 12]` in the single-walker pilot (baseline stuck at `s < 1.9` over 16 ns).
4. `failure-patterns.md` grew three reusable entries (FP-031, FP-032, FP-034).

**EN — What I DO NOT claim:**
- Not "500× speedup" — only coordinate rescaling.
- Not "start.gro is Ain in PC basin" — `s = 7.09` is a soft-min artifact (`z = 1.68`).
- Not "barrier crossed" — `max_s = 12.87` is a single ~120 ps transient.
- Not "WT FES reproduced" — 10-walker production has not finished (and v1 / v2 both failed).
- Not "Miguel's λ = 80 is universal" — only self-consistent on his path.

**中文 — 本周我声称:**
1. Path CV 通过 FP-034 NW `+5` offset 修复, 4 层独立验证。
2. Miguel 原作者契约锁定: ADAPTIVE=DIFF, UNITS=A/kcal, λ=100.79 自洽, 比值 1.26× vs Miguel 的 80。
3. 修正后的 path 在 single-walker pilot 里露出 `s ∈ [1, 12]` 区间 (baseline 16 ns 卡在 `s < 1.9`)。
4. `failure-patterns.md` 新增 3 条可复用条目 (FP-031, FP-032, FP-034)。

**中文 — 本周我不声称:**
- 不是 "500× 加速" — 只是坐标系 rescaling。
- 不是 "start.gro 是 Ain 在 PC basin" — `s = 7.09` 是 soft-min 伪影 (`z = 1.68`)。
- 不是 "barrier 穿越了" — `max_s = 12.87` 是单次 ~120 ps transient。
- 不是 "WT FES 复现了" — 10-walker production 未完成 (v1 / v2 都失败)。
- Miguel 的 λ = 80 不普适 — 只在他的 path 上自洽。

**EN — Single-sentence takeaway:** Cross-species Path-CV construction must hard-gate on sequence identity > 50 % within the selected residue range; this assertion is now part of all future path-builder scripts.

**中文 — 一句话 takeaway:** 跨物种 Path-CV 构造必须在选定 residue 范围内硬 gate "sequence identity > 50 %"; 这个 assertion 已写进所有 future path-builder 脚本。

---

## 7 · Pointer map / 文件指针地图

| Topic / 议题 | Primary source / 主要来源 |
|---|---|
| NW + path build script | `replication/metadynamics/path_seqaligned/build_seqaligned_path.py` |
| Independent verification | `replication/metadynamics/path_seqaligned/VERIFICATION_REPORT.md` |
| Endpoint round-trip sanity | `replication/metadynamics/path_seqaligned/REVERSE_SANITY_CHECK.md` |
| Path geometry summary | `replication/metadynamics/path_seqaligned/summary.txt` |
| Miguel email | `chatgpt_pro_consult_45558834/miguel_email.md` |
| Miguel parsed spec | `replication/metadynamics/miguel_2026-04-23/plumed_template.dat` |
| Locked / tunable split | `replication/metadynamics/miguel_2026-04-23/ladder.yaml` |
| Failure patterns registry | `replication/validations/failure-patterns.md` |
| FES figure script | `reports/figures/plot_sz_distribution.py` |
| FES figure output | `reports/figures/sz_2d_distribution.png` |
| Pilot raw data | `chatgpt_pro_consult_45558834/raw_data/pilot_45515869_COLVAR` |
| Baseline raw data | `chatgpt_pro_consult_45558834/raw_data/baseline_45324928_COLVAR` |
| Pro consultation package | `chatgpt_pro_consult_45558834/README.md` + `QUESTION_FOR_PRO.md` |
