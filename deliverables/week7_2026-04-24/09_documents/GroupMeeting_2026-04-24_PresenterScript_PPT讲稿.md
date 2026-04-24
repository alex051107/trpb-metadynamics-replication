# GroupMeeting 2026-04-24 · Bilingual Page-by-Page Presenter Script
# 中英对照逐页讲稿 · 对齐当前 12-slide deck

> **Deck**: `reports/GroupMeeting_2026-04-24.pptx` (12 slides, 5-topic structure)
> **Meeting**: 1-on-1 with Yu Chen · ~28–30 min talk + 10–15 min Q&A
> **Format**: each slide block has **EN** (English phrasing for practice/reference) then **中文** (read aloud at meeting)
> **Side binders**: `CHEATSHEET.md` · `TechDoc_Bilingual.md` open in side windows

---

## Slide 1 / 12 — Title (30 s)

Slide content: "TrpB MetaD Week 7 — Path realignment + Miguel parameters + pilot results".

**EN**: "The headline of this week: I found and fixed a silent cross-species residue-mapping bug in the Path-CV — FP-034. After the fix, an 8 ns single-walker pilot samples `s = 1 → 12.87`; the old path was trapped at `s < 1.9` over 16 ns. The 10-walker production failed twice and the v3 pipeline is waiting for your approval. I will cover five topics across the next 11 slides in about 28 minutes."

**中文**: "这周的核心进展是**发现并修复了 path CV 的一个跨物种 residue mapping bug——FP-034**。修完后, 8 ns 单 walker pilot 已经 sample 到 `s = 1 到 12.87`, 老 path 跑 16 ns 都卡在 `s < 1.9`。10-walker production 前两次都 fail, v3 pipeline 已经设计好等您 approve。我按 5 个 topic 讲, 接下来 11 张 slide 大概 28 分钟。"

---

## Slide 2 / 12 — Roadmap · 本周 5 个重点 (1 min)

Slide content: 5 topic bullets previewing the deck.

**EN** — walk through the 5 topics without expanding, ~10 s each:
1. **Re-alignment (FP-034)** — cross-species residue-mapping bug, Needleman-Wunsch `+5` offset, 4-layer verification.
2. **Miguel author contract** — JACS 2019 first author emailed the verbatim MetaD parameters, closing 3 weeks of internal debate.
3. **Current results** — pilot 8 ns vs baseline 16 ns, s(t) trace and (s,z) 2D density; `start.gro = (7.09, 1.68)` is off-path.
4. **10-walker seeding story** — v1 scancelled for FP-030 homogeneous start, v2 all FAILED exit 139 (LINCS + seed-dup), v3 pipeline pending.
5. **ML-layer future** — external prior-art audit narrowed 5 directions to MNG-lead; 2026-05-01 hard gate.

**中文** — 逐条点出, 不展开, ~10 秒一条:
1. **Re-alignment (FP-034)** — "cross-species residue mapping bug, Needleman-Wunsch 修复 +5 offset, 4 层独立验证。"
2. **Miguel author contract** — "原文一作邮件给了 verbatim MetaD 参数, 一次性终结 3 周调参 debate。"
3. **Current results** — "pilot 8 ns vs baseline 16 ns, s(t) trace 和 (s,z) 2D 密度; `start.gro=(7.09, 1.68)` 是 off-path。"
4. **10-walker 故事** — "v1 因 FP-030 均一起点 scancel, v2 全 FAILED exit 139 (LINCS + seed-dup), v3 pipeline 待批。"
5. **ML 层未来** — "外部 prior-art 审计 5 条收窄到 MNG-lead, 2026-05-01 hard gate。"

**Transition**: "Topic 1 要多花时间, 这是本周 main result。"

---

## Slide 3 / 12 — Topic 1 (1/3) · FP-034 Root Cause (3 min)

Slide content: dual-box "Naive path" vs "Sequence-aligned path" + root-cause bullets.

**EN**: "1WDW-B is *P. furiosus* TrpB β-subunit in the Open state — 385 residues. 3CEP-B is *S. typhimurium* TrpB β in the Closed state — 393 residues. They differ by a +5 N-terminal offset (3CEP has additional signal-peptide residues that 1WDW does not). So 1WDW resid 97 is homologous to **3CEP resid 102**, not resid 97. Our original `generate_path_cv.py` had `aln_offset` computed at line 182 but never consumed it at line 670 — it used raw residue numbers throughout. Result: the naive path paired non-homologous residues. Across the 112 selected residues (COMM 97–184 plus base 282–305), sequence identity was 6.2 %, per-atom O↔C RMSD was 10.89 Å, and Branduardi λ landed at 3.80 Å⁻² — 21× smaller than Miguel's reported 80. After the fix with a uniform `+5` NW-derived offset: identity 59.0 % (9.5×), RMSD 2.115 Å (5.1× tighter), λ = 100.79 Å⁻². Ratio vs Miguel = 1.26×. Same kernel-width regime."

**EN — key line, pause 1 s**: "This bug was silent for three weeks. The code ran without error, `path.pdb` looked syntactically valid, and `plumed driver` accepted the file. The only downstream symptom was walker trapping at `s ≈ 1`."

**中文**: "1WDW 是嗜热菌 *P. furiosus* 的 TrpB β 亚基, Open 态, 385 aa。3CEP 是沙门菌 *S. typhimurium* 的 TrpB β, Closed 态, 393 aa。两条 chain 相差一个 **+5 N 端 offset** (3CEP 多 5 个 signal peptide residue)。"

"所以 1WDW resid 97 的真正同源 residue 是 **3CEP resid 102, 不是 97**。但我们的 `generate_path_cv.py` 在 182 行**算**了 NW alignment, 在 670 行**没 consume** 这个 offset, 直接用 residue number 配对——等于把两个不同蛋白的 backbone 硬叠。"

**数字 hit (指 slide 两个 box)**:
- "naive: 112 个 residue identity 6.2%, O↔C RMSD 10.89 Å, λ = 3.80 Å⁻² —— 比 Miguel 的 80 小 21×"
- "seq-aligned: identity 59.0% (9.5× 提升), RMSD 2.115 Å (5.1× 紧), λ = 100.79 Å⁻² —— 跟 Miguel 比值 1.26×, 同 kernel 宽度量级"

**中文 — 关键 line, pause 1 秒**: "**这个 bug silent 了 3 周**。代码跑不报错, `path.pdb` 长得正常, `plumed driver` 也接受。问题只在下游表现为 'walker 卡在 s=1'。"

**防守预案**:
- Yu: "为什么早没发现?" → "因为 Codex 和我都没 cross-check alignment identity。FP-034 已经加进 `failure-patterns.md`, 以后所有 future path-builder 脚本头部必须 `assert identity > 50%`。"

**Transition**: "修复之后的生物学 sanity 下一页看。"

---

## Slide 4 / 12 — Topic 1 (2/3) · Numerical + Biological Sanity (3 min)

Slide content: large table with 10 rows (metric comparison + independent PC crystal projection).

**EN — numerical block (top half)**: "Nine-and-a-half-fold identity gain, 5× tighter RMSD, 26× smaller adjacent-MSD, 26× larger λ. The `ratio vs Miguel = 1.26×` line is what matters — our λ is self-consistent on our path, and 1.26 is inside the Branduardi < 2× tolerance."

**EN — biological sanity (bottom half)**: "This is an **independent** post-hoc validation. The four crystals 5DW0, 5DW3, 5DVZ, and 4HPX were **not** used to build the path — only 1WDW and 3CEP were. On the naive path, the three βPC crystals all collapsed to `s ≈ 1.07`, indistinguishable from Open, which is physically absurd because PC is by literature definition not Open. On the corrected path, the three βPC crystals spread across `s = 5.4 – 9.5` — expected partial-closure geometry. 4HPX, the Pf A-A intermediate near Closed, sits at `s ≈ 14.9` on both paths because it is close to the C endpoint and insensitive to the path fix."

**EN — NW algorithm detail if Yu asks**: "NW is handwritten in numpy; no BioPython. Scoring match=+2, mismatch=-1, gap=-2 — simplest defensible scheme. Both chains are > 50 % identical, so any reasonable scoring converges. Codex's blind reimplementation produced score 286, identity 59.0331 %, uniform offset +5 — byte-level match. The NW's real value-add is **not** discovering the offset (mostly a PDB-numbering convention); it is **proving** that a uniform offset is mathematically legal across the selected 112 residues by checking `min == max` on `[mapping[r] - r]`."

**中文 — 数值块**: "9.5× identity 提升, 5× RMSD 紧, 26× MSD 小, 26× λ 大。最后一行 '比 Miguel 80 是 1.26×' —— 我们的 λ 在我们的 path 上自洽, 1.26× 在 Branduardi 2007 tolerance (< 2×) 内。"

**中文 — 生物学 sanity**: "下半张表是**独立** sanity check——这 4 个晶体**没**参与 path 构造, 我们只用了 1WDW 和 3CEP。"

指表逐行:
- "5DW0 是文献标注的 βPC + L-Ser (Aex1 intermediate)。naive path s≈1.07 (等同 Open, 物理荒谬), corrected path s=9.46 (path 中段, 合理 partial closure)。"
- "5DW3 / 5DVZ 另外两个 βPC 晶体, corrected path 上 s=8.51 / 5.37, 都落在 mid-path。"
- "4HPX 是 Pf A-A 中间体, 接近 Closed, 两种 path 都 s≈14.9 —— 它本就接近 C 端点, 对 path 修正不敏感。"

**中文 — 关键 line**: "3 个 βPC 晶体在 naive path 上**全塌到 s≈1**, 在 corrected path 上散布 s=5.4–9.5。这是 path 修复有效的硬证据。"

**中文 — 如果被追问 NW 算法**: "NW 是 numpy 手写的, 不用 BioPython。评分 match=+2, mismatch=-1, gap=-2, 最简 scheme, 因为 identity>50% 任何合理评分都收敛。Codex 独立实现跑 score 286, identity 59.0331%, offset +5, 跟我 byte-level 一致。NW 的 value-add **不是发现** offset (大部分是 PDB 编号惯例差), 而是**证明** 112 residue 内 uniform offset 合法——检查 `min([mapping[r]-r]) == max([mapping[r]-r])`。"

**Transition**: "下一页是视觉证据。"

---

## Slide 5 / 12 — Topic 1 (3/3) · Visual Proof + start.gro Soft-Min (3 min)

Slide content: `sz_2d_distribution.png` (side-by-side FES) + bullets explaining how figure made + start.gro rationale.

**EN — the figure**: "This is the single most important figure of the week. Panel a — baseline on the naive path, 16 ns, 81 479 single-walker frames; density compressed into the narrow `s < 2` ridge. Panel b — pilot on the sequence-aligned path, 8 ns, 40 193 single-walker frames; density spread across `s = 1 – 12`. The **only** variable between the two panels is `path.pdb` — same start.gro, same Miguel parameters, same single-walker protocol. Half the wall-clock time, 6.8× wider s-coverage."

**EN — how the figure was made**: "Left is 2D gaussian KDE of baseline COLVAR, right is the same KDE of pilot COLVAR, both converted to `F(s,z) = -kT ln(p/p_max)` at T = 350 K, clipped at 6 kcal/mol, identical grid and colorscale. Script is `reports/figures/plot_sz_distribution.py`, reproducible from raw COLVAR."

**EN — start.gro preempt**: "The red star on panel b marks `start.gro` at `(s = 7.09, z = 1.68)`. Someone will ask: 'does this mean Ain is in the PC basin?' I will argue no. Direct Kabsch RMSD of start.gro against each of the 15 MODELs is 1.30 – 1.76 Å — spread of only 0.3 – 0.5 Å. start.gro is **near-equidistant** to every MODEL; there is no dominant 'nearest'. Under the Branduardi soft-min, near-equidistant `MSD_i` values make the numerator a weighted average of all integer indices, concentrating at `N/2 = 7`. This is a known geometric property of linear-interpolation paths, not a numerical bug and not a biological claim. The `z = 1.68` corroborates — mean_z across the 8 ns pilot is 1.53, so the walker is generally off-path; `s = 7` is a soft-average artifact, not a PC-basin identification."

**中文 — 图讲解**: "这是本周最重要的一张图。panel a 是 naive path baseline, 16 ns, 81479 frames, 密度压在窄窄 `s<2` 条带; panel b 是 corrected path pilot, 8 ns, 40193 frames, 密度铺开到 `s=1-12`。**两个 panel 唯一变量是 path.pdb, 其他完全一样**。时间一半, s 宽度 6.8 倍。"

**中文 — 图怎么做的**: "左右都是 COLVAR 的 2D gaussian KDE 转成 `F(s,z) = -kT ln(p/p_max)`, T=350 K, clip 在 6 kcal/mol, 相同 grid 相同色标。脚本 `reports/figures/plot_sz_distribution.py`, 从 raw COLVAR 完全 reproducible。"

**中文 — start.gro 这点必须 preempt**: "右图红色星星是 start.gro, 投到 `(s=7.09, z=1.68)`。有人会问 '这不就说明 Ain 在 PC basin 吗' —— **我不这么读, 是 overclaim**。"

**中文 — soft-min 解释**: "start.gro 对 path 每个 MODEL 做直接 Kabsch, RMSD 都在 1.30-1.76 Å, **差距只有 0.3-0.5 Å**。start.gro **离每个 MODEL 都差不多近**, 没有 dominant 'nearest MODEL'。Branduardi soft-min 公式下, 当所有 MSD_i 差不多时, 分子变成整数 index 的加权平均, 自然集中到 `N/2 ≈ 7`。这是 **linear-interp path 的已知几何性质**, 不是 numerical bug, **也不是生物学陈述**。`z=1.68` 也佐证: 8 ns 全程 mean_z=1.53, walker 本来就不在 path 上, `s=7` 是 soft-average 伪影, 不是 basin identification。"

**Transition**: "Topic 1 讲完——bug 找到, fix 对, 视觉也看见。下一个讲最重要的外部输入, Miguel 的 email。"

---

## Slide 6 / 12 — Topic 2 · Miguel Author Parameter Contract (3 min)

Slide content: verbatim PLUMED code block + 4 bullets on what changed + why it matters.

**EN**: "Miguel Maria-Solano, first author of the JACS 2019 paper, replied to my parameter request on 2026-04-23 with a verbatim PLUMED parameter block. This single email terminated three weeks of internal debate — probe_sweep HEIGHT/BIASFACTOR 2×2, wall4 AT-scan, piecewise-λ design, all stalled on lack of an authoritative reference. The four corrections are:"

1. **ADAPTIVE = DIFF, not GEOM** — closes FP-031. PLUMED documentation explicitly states that GEOM projects σ onto the chord direction, which becomes ill-defined at path endpoints; DIFF estimates σ from consecutive-step CV differences and is endpoint-stable.
2. **UNITS = A / kcal, not nm / kJ** — closes FP-032. Miguel's SIGMA literals (0.1, 0.3, 0.005) are Å/kcal; running with GROMACS native nm/kJ left the effective σ off by a unit-conversion factor.
3. **Primary set = HEIGHT=0.15 kcal/mol, BIASFACTOR=10, WALKERS_N=10**; the alternate `0.3 / 15` is explicitly an aggressive fallback only, to be used if primary fails to converge.
4. **λ is self-consistent per path, not universal.** Miguel's 80 is his value on his path. Our corrected path gives 100.79, ratio 1.26× — same regime.

**中文**: "Miguel Maria-Solano 是原文一作。2026-04-23 回复我一个 verbatim PLUMED 参数块。这封 email **一次性终结 3 周的内部 debate** —— probe_sweep HEIGHT/BF 2×2, wall4 AT 扫描, piecewise-λ 设计, 都卡在缺 authoritative reference。4 个修正:"

1. **ADAPTIVE = DIFF, 不是 GEOM** — "关闭 FP-031。PLUMED 文档明确说 GEOM 在 path 端点 ill-defined (chord 方向不稳); DIFF 用连续步 CV 差分直接估 σ, 端点稳。"
2. **UNITS = A / kcal, 不是 nm / kJ** — "关闭 FP-032。Miguel 的 SIGMA 字面值 (0.1, 0.3, 0.005) 是 Å/kcal; GROMACS native nm/kJ 跑, 等效 σ 差一个单位转换因子。"
3. **Primary = HEIGHT=0.15, BF=10, WALKERS_N=10** — "不是 0.3 / 15。后者是 Miguel 邮件里标的 aggressive fallback, primary 不收敛才上。"
4. **λ 按 path 自洽, 不普适** — "Miguel 的 80 是他的 path 上自洽。我们 100.79, 比值 1.26×, 同 regime。"

**Transition**: "对的 path + 对的参数, pilot 结果下一页讲。"

---

## Slide 7 / 12 — Topic 3 (1/2) · s(t) Trace (2 min)

Slide content: `s_trend_slide.png` on left + bullets describing pilot / baseline / interpretation on right.

**EN**: "Blue line is baseline 45324928, naive path, 16 ns — trapped at `s < 1.9`, 75.24 % of frames at `s < 1.25`. Orange line is pilot 45515869, corrected path, 8 ns — min(s) = 1.000 at t = 4920 ps (walker genuinely visited the Open endpoint), max(s) = 12.867 at t = 6085 ps (single ~120 ps transient). From t = 437 ps to 6085 ps there is a ~4.3 ns plateau at `max(s) ≈ 10.92`."

**EN — caveat**: "This is **not** a 500× speedup. The kernel λ went from 3.80 to 100.79, so the coordinate resolution is different. Real sampling efficiency can only be measured against a converged FES under identical sampling budget — requires 10-walker production."

**中文**: "蓝线是 baseline 45324928, naive path, 16 ns, 卡在 s<1.9, 75.24% frames 在 s<1.25。橙线是 pilot 45515869, corrected path, 8 ns: min(s)=1.000 at t=4920 ps (walker 确实到过 O 端点), max(s)=12.867 at t=6085 ps (单次 ~120 ps transient)。t=437 ps 到 6085 ps 有 ~4.3 ns plateau, max_s ≈ 10.92。"

**中文 — caveat 必须说**: "这**不是** '500× speedup'。kernel λ 从 3.80 变成 100.79, 坐标分辨率不同。真采样效率要等 converged FES 做同等预算对比才能测——需要 10-walker production。"

**Transition**: "2D 分布下一页。"

---

## Slide 8 / 12 — Topic 3 (2/2) · (s, z) 2D Density (2 min)

Slide content: `sz_2d_pilot_jacs_style.png` (single panel, JACS Fig 3 analog) + bullets.

**EN**: "This is the pilot walker's (s, z) density in JACS-2019-Fig3 style, single panel. Density spread across `s = 1 → 12`, highest occupancy at `s = 1 – 7` (walker starts near Open, drifts toward Closed). The red star marks start.gro at `(7.09, 1.68)` — **not** in the highest-density region, because `z = 1.68` is elevated vs `mean_z = 1.53`, confirming start.gro is off-path. Tail at `z > 2` near `s = 12` corresponds to the `max(s) = 12.87` transient that approached the `UPPER_WALLS z = 2.5` cap."

**EN — caveat**: "WT FES is **not** reproduced here. A single walker over 8 ns does not give uniform s-space coverage; FES reconstruction requires 10-walker production plus `sum_hills.py`."

**中文**: "pilot 单 walker 的 (s, z) 2D 密度, JACS 2019 Fig 3 风格, 单面板。密度 s=1 到 12 都有, 最高在 s=1-7 (walker 从 Open 出发往 Closed 漂)。红色星星 start.gro (7.09, 1.68) **不**在最高密度区, 因为 z=1.68 比 mean_z=1.53 高, 说明 start.gro 偏离 path。右上 z>2 的尾巴对应 max_s=12.87 那次 transient, 到了 UPPER_WALLS z=2.5 附近。"

**中文 — 关键 line**: "**WT FES 没复现**。单 walker 8 ns 在 s 空间采样**不均匀**, FES 重建需要 10-walker production 加 sum_hills 才算数。"

**Transition**: "说到 10-walker, 这是本周最郁闷的——"

---

## Slide 9 / 12 — Topic 4 · 10-Walker v1 / v2 / v3 Story (4 min)

Slide content: 4-row table (v1 / v2 / v3) + v3 pipeline bullets + assertion suite bullets.

**EN** — "I ran 10-walker production twice this week. Both unusable."

**EN — v1 (45558834)**: "Seeds were 10 frames from 500 ns Ain cMD at `t = 50, 100, ..., 500 ns`. But that cMD had long equilibrated to the Open basin, so the time-diverse seeds all collapsed in CV space to `s ≈ 1`. Violates FP-030 — shared-HILLS needs walkers distributed across CV space, otherwise it degenerates into 'single walker × 10'. PM and Codex independently flagged; I scancelled at 22:05."

**EN — v2 (45570699)**: "Seeds rebuilt from pilot COLVAR — for each target_s ∈ {1..10}, pick the frame with `|s − target_s| < 0.1` and minimum z. CV space was diverse this time. But **all 10 walkers FAILED exit 139 SEGV**, elapsed 14 min to 3 h 05 min. Crash signature identical across walkers: LINCS blows up at atoms 4463–4465 (a CH3 methyl bond) with the constraint stretching from 0.11 nm to 3.67 nm (33× over target), then SETTLE fails on cascaded water bad-contacts. Concurrently, `metad.bias` in COLVAR goes deeply negative — physically impossible, since metad.bias is a sum of positive Gaussians. This is downstream corruption after LINCS destabilises the coordinates fed to PATHMSD."

**EN — Codex diagnosis**: "I handed the full crash log to Codex. Root cause: seeds from `gmx trjconv -dump` contain positions only, no velocities. v2 submit script ran `gmx mdrun -plumed` directly with no EM and no NVT, so GROMACS regenerated velocities on a geometry still carrying the strain of a biased-MetaD snapshot. LINCS failed on the stressed methyl bonds (reproducibly at the same atom pair across walkers); segfault followed."

**EN — v3 pipeline**: "Codex-verified fix, three stages: (1) EM 1000 steps with `emtol = 1000 kJ/mol/nm` — eliminate bad contacts; (2) NVT 100 ps at 350 K with PLUMED **off** and `gen_vel = yes` — regenerate MB velocity distribution on relaxed geometry; (3) continue from nvt.cpt into production MetaD with PLUMED on. Plus three assertions in the materialize script: unique-frame guard, `std(seed_s) > 2.0` diversity, velocity-presence check on start.gro. The submit template is in `deliverables/.../07_v3_pipeline_plan/submit_v3_template.sh`, awaiting your approval before I sbatch."

**EN — honest line**: "Because v1 and v2 are both unusable, **every figure in this deck uses single-walker data only**. No v1 / v2 frame appears as 'production'. 10-walker FES is next week's deliverable, not this week's."

**中文** — "10-walker production 跑了两次, 两次都不能用。"

**v1 (45558834)** — "从 500 ns Ain cMD 抽 t=50/100/.../500 ns 做 seed。但 cMD 早 equilibrate 到 Open basin, 10 个 time-diverse seed 在 CV 空间**全塌在 s≈1**。违反 FP-030 (shared-HILLS 需要 CV 分散)。PM 和 Codex 独立 flag, 22:05 scancel。"

**v2 (45570699)** — "seed 改从 pilot COLVAR 挑, 每个 target_s=1..10 挑 |s-target|<0.1 且 min z。CV 分散了——但**所有 10 个 walker 全 FAILED exit 139 SEGV**, 14 分钟到 3h05 不等。crash 都是同一个 pattern: LINCS 在 atom 4463-4465 (一个 CH3 methyl 键) 爆炸, 约束从 0.11 nm 拉到 3.67 nm (33× stretched), 然后 SETTLE 级联在 water bad-contacts, GROMACS segfault。COLVAR 末尾 **metad.bias 负值** (物理不可能, 累加高斯必须 ≥ 0)——是下游 corruption, LINCS 失败后坐标越界污染 PATHMSD 和 PLUMED 状态。"

**Codex 诊断** — "我把完整 crash log 丢给 Codex。根因: `gmx trjconv -dump` 出的 seed .gro **只有位置没速度**, v2 submit 直接跑 `gmx mdrun -plumed`, **没 EM, 没 NVT**, GROMACS 在 biased 几何上重新生成速度, LINCS 第一步就在 methyl 键上 fail (所有 walker 同一 atom pair, 可重现)。"

**v3 pipeline** — "Codex 验证过的三段式: (1) EM 1000 步, emtol=1000 kJ/mol/nm 去 bad contacts; (2) NVT 100 ps at 350 K, PLUMED **off**, gen_vel=yes 在 relaxed 几何上重新生成 MB 速度; (3) 从 nvt.cpt 继续 production MetaD, PLUMED on。另加 3 条 assertion: unique-frame guard, `std(seed_s) > 2.0` 多样性, start.gro velocity 检查。submit 模板在 `deliverables/.../07_v3_pipeline_plan/submit_v3_template.sh`, 等您 approve 再 sbatch。"

**中文 — 诚实 line 必须说**: "v1 v2 都不能用, 所以**本 deck 所有图都只用 single-walker 数据**, 没有任何 v1 / v2 frame 冒充 production。10-walker FES 是下周的 deliverable, 不是这周的。"

**Transition**: "接下来讲 ML 层——先说结论: **2026-05-01 前 10-walker FES 不通过 sanity, 所有 ML 扩展全暂停**。"

---

## Slide 10 / 12 — Topic 5 (1/2) · ML-Layer Audit + v2.0 Pivot (3 min)

Slide content: 2-column layout — left column "5 original extensions + 2026 verdict", right column "v1.2 → v2.0 pivot + hard gate".

**EN — audit (left column, ~10 s per row)**: "The v1.2 cartridge memo listed 5 ML-layer directions. I audited them against 2024–2026 arXiv / Nature / JCTC this week."
- **A · CRR (catalytic-readiness reward for GRPO)** — WEAKENED (PocketX, ResiDPO, ProteinZero already do similar reward heads).
- **B · PP-Prior (path-CV energy-guided diffusion)** — WEAKENED (Enhanced Diffusion Sampling arXiv 2602.16634).
- **C · LBP (learned bias potential)** — DEAD (NN-VES, Deep-TICA, OPES+mlcolvar saturate this space).
- **D · TCR (FES-matching training loss)** — DEAD-ish (Thermodynamic Interpolation JCTC 2024).
- **E · MNG (Memory Necessity Gate)** — ALIVE, the lead. MEMnets does CV discovery, not runtime rescue gate.

**EN — meta conclusion (critical line)**: "The cartridge artifact itself is likely more novel than any individual ML layer on top of it. v1.2 → v2.0 pivot: reposition from 'ML algorithm innovator' to '**F0 PathGate evaluator** as a pip-installable Python wrapper' — a concrete deliverable for Yu, Amin, and Raswanth. New directions F (PLP-aware reactive PATHMSD, Dunathan angle) and G (generative-model physics-consistency audit) replace the C / D independence claims."

**中文 — audit (左栏)** — "v1.2 cartridge memo 列了 5 条 ML 方向, 本周对 2024-2026 arXiv / Nature / JCTC 做 prior art 审计:"
- "A · CRR — PocketX / ResiDPO / ProteinZero 已经做了 reward head → **weakened**"
- "B · PP-Prior — Enhanced Diffusion Sampling 2602.16634 → **weakened**"
- "C · LBP — NN-VES / Deep-TICA / OPES+mlcolvar → **dead**"
- "D · TCR — Thermodynamic Interpolation JCTC 2024 → **dead-ish**"
- "E · MNG — MEMnets 是 CV discovery 不是 runtime gate, **alive, lead**"

**中文 — Meta 结论 (关键 line)**: "审计 meta 结论: **cartridge 这个 artifact 本身可能比任何单层 ML 更 novel**。v1.2 → v2.0 pivot: 从 'ML 算法创新者' 变成 '**F0 PathGate evaluator** 的 pip-installable wrapper 作者' —— 给 Yu / Amin / Raswanth 用的具体 deliverable。新方向 F (PLP-aware 反应 PATHMSD, Dunathan angle) 和 G (生成模型物理一致性 audit) 替代 C/D 的独立 novelty claim。"

**Transition**: "具体 deliverable 下一页。"

---

## Slide 11 / 12 — Topic 5 (2/2) · Deliverables + 2026-05-01 Hard Gate (3 min)

Slide content: bullets for this-week D2/D3, next-week 10-walker v3, 2026-05-01 gate criteria.

**EN — this week (D2 + D3)**: "D2 is the API design document `replication/cartridge/API_DESIGN.md` — function signatures, I/O types, one example call, no implementation. D3 is a lab-facing demo. Preferred option: a Yu-facing demo that shows a simple 1D/2D CV failing to distinguish PC from O, then PATHMSD cartridge recovering the state diagnosis. Alternative: score a STAR-MD or ConfRover public trajectory through the cartridge. Deliverable is 1 Jupyter notebook or 2-page write-up."

**EN — next week (10-walker v3 production)**: "v3 pipeline produces 10 walkers × 30 – 50 ns each, FES(s, z) compared against JACS-2019 Fig 2a, at least two PC crystals projected onto the 2D occupancy (5DW0, 5DW3), block-analysis CI reported however wide."

**EN — 2026-05-01 hard gate (binary, three criteria)**:
1. WT MetaD 10-walker FES shows O / PC / C basins.
2. Block-analysis CI defined.
3. ≥ 2 PC crystals projected on 2D.

"**Gate FAILS → all 5 ML directions SUSPEND.** Focus reverts to WT debugging. No pitch to Amin / Raswanth / Arvind until WT is defensible."

"**Gate PASSES → D2 freezes, D3 runs on real cartridge, Aex1 variant becomes next target, MNG moves from memo to scoping doc.**"

**中文 — 本周 (D2 + D3)**: "D2 是 API 设计文档 `replication/cartridge/API_DESIGN.md` — 签名 + I/O + 一个 example call, 不写 implementation。D3 是 lab-facing demo: 优先做 Yu 方向, 展示简单 1D/2D CV 不能区分 PC 和 O, 然后 PATHMSD cartridge 给 meaningful state diagnosis。备选: 给 STAR-MD / ConfRover 公开轨迹打分。交付是 1 个 Jupyter notebook 或 2 页 write-up。"

**中文 — 下周 (v3 10-walker)**: "v3 pipeline 跑出 10 walker × 30-50 ns, FES(s, z), 跟 JACS 2019 Fig 2a 比, 至少 2 个 PC 晶体投影到 2D occupancy (5DW0, 5DW3), block-analysis CI 即使宽也要标出来。"

**中文 — 2026-05-01 硬 gate (binary, 三条)**:
1. "WT 10-walker FES 出现 O / PC / C 三个 basin"
2. "Block CI defined"
3. "≥ 2 个 PC 晶体 2D 投影"

"**Gate FAIL → 5 个 ML 方向全暂停。** 回到 WT 单 walker → 10 walker 的 debug。不对 Amin / Raswanth / Arvind 做 pitch, 因为 WT 自己都没 defensible。"

"**Gate PASS → D2 freeze, D3 run, Aex1 variant 作为下一个 target, MNG 从 memo 升级到 scoping doc。**"

**Transition**: "最后一页总结。"

---

## Slide 12 / 12 — Summary · Q & A (2 min)

Slide content: can-claim / cannot-claim two-column, last-line takeaway.

**EN — what I CLAIM this week**:
1. Path CV fixed via FP-034 NW `+5` offset, 4-layer independent verification.
2. Miguel parameter contract locked (ADAPTIVE=DIFF, UNITS A/kcal, λ=100.79 self-consistent).
3. Corrected path opens `s = 1 – 12` region in a single-walker 8 ns pilot (baseline stuck at `s < 1.9` over 16 ns).
4. `failure-patterns.md` gained 3 reusable entries (FP-031 / 032 / 034).

**EN — what I DO NOT claim**:
- Not "500× speedup" — only coordinate rescaling.
- Not "start.gro is Ain in PC basin" — soft-min artifact (z = 1.68 off-path).
- Not "barrier crossed" — `max(s) = 12.87` is a single ~120 ps transient.
- Not "WT FES reproduced" — 10-walker production has not completed.
- Not "Miguel's λ = 80 is universal" — self-consistent on his path only.

**EN — single-sentence takeaway (the line of the meeting)**: "Cross-species Path-CV construction must hard-gate on sequence identity > 50 % within the selected residue range. This assertion is now in every future path-builder script header. This is what elevates the week's work from *fixing a bug* to *establishing a rule*."

**中文 — 能 claim 的 (指 slide 左列)**:
1. "Path CV 通过 FP-034 NW +5 offset 修复, 4 层独立验证。"
2. "Miguel 参数契约锁定 (ADAPTIVE=DIFF, UNITS A/kcal, λ=100.79 自洽)。"
3. "Corrected path 让 single walker 8 ns 暴露 s=1-12 区间 (baseline 16 ns 卡在 s<1.9)。"
4. "`failure-patterns.md` 新增 3 条可复用条目 (FP-031/032/034)。"

**中文 — 不能 claim 的 (指 slide 右列)**:
- "❌ 500× speedup — 只是坐标 rescaling"
- "❌ start.gro 在 PC basin — soft-min 伪影 (z=1.68 off-path)"
- "❌ barrier crossed — max_s=12.87 是单次 ~120 ps transient"
- "❌ WT FES 复现了 — 10-walker 没完"
- "❌ Miguel 的 λ=80 普适 — 只在他 path 上自洽"

**中文 — 最终 takeaway (整个 meeting 最重要一句)**:
> "**Cross-species PATH-CV construction 必须在选定 residue 范围内硬 gate: sequence identity > 50%。这条写进 failure-patterns.md FP-034, 所有 future path-builder 脚本头部必须 assert。**"

> "这句话的意义是: 从**修一个 bug**升级到**建了一条规则**。Yu, 我觉得这是本周最重要的 takeaway, 不是 pilot 的 s=12。"

---

## Q & A Preparation / 问答预案

### Q1 · "+5 offset is just a PDB-numbering convention difference" / "不就是 PDB 编号惯例差"

**EN**: Yes, largely — it reflects a signal-peptide numbering difference between 1WDW and 3CEP authors. But the NW's value-add is **not discovering** the offset; it is **proving** that a uniform offset is mathematically legal within the 112 selected residues. If any indel existed inside [97..184] ∪ [282..305], a single-number fix would be illegal and a per-residue remap (possibly with dropout) would be required.

**中文**: "对, 大部分是编号惯例差。NW 的 value-add 不是**发现** offset, 是**证明 112 residue 内部没有 indel**, 所以 uniform +5 合法。如果有 indel, 单一数字的 fix 数学上不可能。"

### Q2 · "zero neighbor_msd_cv = no physical intermediate, why does s=8 mean PC?" / "s=8 凭什么代表 PC?"

**EN (two sentences, do not merge)**:
1. The path itself is a geometric reference — `s = 8` does **not define** PC.
2. 5DW0 / 5DW3 are **independent** biological PC crystals, and their projection happens to land at `s = 8 – 9`. This is a **post-hoc validation**, not a prior. A mechanistically meaningful path requires string method or TMD — future work.

**中文**: (分两句, 不合并)
1. "Path 本身是 geometric reference, `s=8` **不 define** PC。"
2. "5DW0 / 5DW3 是**独立**的 biological PC 晶体, projection 恰好落 s=8-9, 是**事后 validation 不是 prior**。真 mechanistic path 需要 string method 或 TMD, future work。"

### Q3 · "Is the 500 ns cMD analysis also contaminated?" / "cMD 分析污染了吗?"

**EN**: cMD itself is **not contaminated** — unbiased Cartesian coordinates, never used `path.zzz`. What is contaminated is downstream `project_to_path.py` output that referenced the naive path. TechDoc § 3.4 lists three downstream items to rerun: (a) path_piecewise audit retracted, (b) probe_sweep stall reinterpreted, (c) FP-032 21× anomaly corrected to 1.26×.

**中文**: "cMD trajectory 本身**没污染** (unbiased Cartesian, 没用 path CV)。污染的只是**用老 path 做过的 project_to_path.py 产出**。TechDoc § 3.4 列了 3 条 downstream 要重跑。"

### Q4 · "MNG needs qMSM — do you know it?" / "qMSM 你会吗?"

**EN (be honest)**: No. This is the key technical risk for next month. Mitigation: Huang Lab qMSM tutorial + PyEMMA / Deeptime reference implementations. If after one month I judge this is not learnable within the budget, I will escalate and hand it to a future graduate student rather than over-promise.

**中文 (坦白)**: "不会, 这是下个月关键技术风险。mitigation: Huang lab 教程 + PyEMMA / Deeptime 现成实现。1 个月判断学不动就 drop 给未来 grad student。"

### Q5 · "Which parts are Claude/Codex vs you?" / "哪些是 Claude / Codex 写的"

**EN**: `build_seqaligned_path.py` (NW + Kabsch) — me, pure numpy. `verify_and_materialize_seqaligned_path.py` — Codex, blind re-implementation for cross-verification (byte-level match). v3 submit template — Codex, based on its crash-log diagnosis. Slides and TechDoc prose — Claude, my review + edits. **Every number in the deck is a script output, not hand-calculated**.

**中文**: "`build_seqaligned_path.py` (NW + Kabsch) 是我写的, 纯 numpy。`verify_and_materialize_seqaligned_path.py` 是 Codex 独立实现交叉验证 (byte-level 一致)。v3 submit template 是 Codex 基于 crash log 诊断写的。Slides 和 TechDoc prose 是 Claude 写的, 我 review + 改。**每个数字都是脚本输出, 不是手算**。"

### Q6 · Why MSD not RMSD in path CV? / 为什么 path CV 用 MSD 不用 RMSD?

**EN**: RMSD is what structural biologists use in PyMOL / VMD / papers because it is in Å — directly interpretable. But PATHMSD (and any path-CV meant to drive metadynamics forces) must be differentiable everywhere in atomic coordinates. `z = RMSD = √MSD` has `∂z/∂Δr = Δr / RMSD`; at `RMSD = 0` (walker sits exactly on the path) the denominator blows up and the derivative is undefined — GROMACS hits NaN and segfaults. Using MSD (squared) gives `∂z/∂Δr = 2·Δr`, smooth everywhere including `MSD = 0`. So Branduardi 2007 was forced into MSD by the requirement that MetaD can compute forces. The reason our figure axis reads `Å²` is exactly this — when you want an interpretable "distance per Cα", take `√z`: for start.gro `z = 1.68 Å²` → `√z ≈ 1.3 Å` per Cα.

**中文**: 结构生物学里大家确实用 RMSD (PyMOL / VMD / paper figure 都是), 因为 Å 直觉好。但 PATHMSD 要驱动 MetaD 的力, **必须处处可微**。`z = RMSD = √MSD` 的导数 `∂z/∂Δr = Δr / RMSD`, 在 RMSD=0 (walker 正好踩 path 上) 时分母爆 0 → NaN → GROMACS segfault。换成 MSD (平方), 导数 `2·Δr` 在 0 处也平滑, MetaD 能稳定积分。所以 Branduardi 2007 **被迫**选 MSD, 不是 MSD 更好, 是 RMSD 根本跑不起来。我们 2D 图 y 轴是 Å² 正是这个原因; 想要"每个 Cα 平均偏几 Å"的直觉, `√z` 一下就行 —— start.gro `z=1.68 Å² → √z ≈ 1.3 Å per Cα`。

### Downgrade phrase / 临时降级话术

**EN**: "My hot-path answer may be inaccurate. TechDoc § X and VERIFICATION_REPORT have the full traceback; let me circle back after the meeting."

**中文**: "这个 hot-path 答不对可能犯错。**TechDoc § X** / **VERIFICATION_REPORT** 都有完整溯源, 会后过一遍。"

---

## Pre-meeting 30-second self-check / 上场前 30 秒自检

- [ ] `pptx` opened to slide 1, full-screen
- [ ] `CHEATSHEET.md` + `TechDoc_Bilingual.md` + `SELECTION_LOGIC.md` open in side windows
- [ ] Laptop battery > 50 %
- [ ] One sip of water
- [ ] Deep breath — you did the right work

---

## Mindset / 心态

**EN — your three real contributions this week**:
1. Found a silent bug no one had caught in 3 weeks.
2. Ran independent Claude + Codex cross-verification.
3. Honestly reported the 10-walker failures — did not overclaim.

Yu's pushback exists to protect you, not attack you. Stay grounded. Be honest. Acknowledge limitations. That is enough to win.

**中文 — 你本周的三件真实贡献**:
1. 发现一个 silent 3 周没人发现的 bug
2. 独立 + Codex 双实现 cross-verification
3. 诚实承认 10-walker failed, 不 overclaim

Yu 的 pushback 是保护你, 不是针对你。**稳住, 诚实, 承认 limitation, 就赢了**。
