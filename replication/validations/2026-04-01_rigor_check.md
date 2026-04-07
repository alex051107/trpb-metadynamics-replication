# Independent Rigor Check: 14 Technical Claims

**Date**: 2026-04-01
**Reviewer**: Independent Skeptic Agent (science rigor auditor)
**Scope**: 14 specific claims from project-guide/FULL_LOGIC_CHAIN.md, project-guide/MASTER_TECHNICAL_GUIDE.md, and related files
**Method**: Each claim checked against primary literature DOIs, SI text, and internal cross-references

---

## Summary

| Verdict | Count |
|---------|-------|
| ACCURATE + SOURCED | 6 |
| ACCURATE + needs qualification | 4 |
| INACCURATE | 2 |
| UNVERIFIABLE (insufficient evidence in repo) | 2 |

---

## Claim-by-Claim Analysis

### Claim 1
> "TrpB 变体的催化活性取决于 COMM domain 能不能稳定地处于 Closed 状态"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE, with qualification** |
| **Source** | SOURCED — JACS 2019 (DOI: 10.1021/jacs.9b03646) Figures 2-3; ACS Catal. 2021 (DOI: 10.1021/acscatal.1c03950); Buller et al. PNAS 2015 |
| **Overclaim risk** | **MEDIUM**. The word "取决于" (depends on) is stronger than what the evidence supports. Osuna 2019 demonstrates a *correlation* between FEL-derived Closed-state stability and experimental kcat for 3 TrpB variants (PfTrpS, PfTrpB, PfTrpB0B2). Correlation over 3 data points is suggestive but not a proof of causal dependence. Additionally, productive closure requires specific catalytic geometry (K82-Q2 distance), not just COMM domain closure per se. |
| **Correction** | Replace "取决于" with "与...强相关" or add qualifier: "...取决于 COMM domain 能不能稳定地处于 **productive** Closed 状态（Osuna 2019 在 3 个变体上证明了这种相关性）". This maintains the message while being honest about evidence strength. |

---

### Claim 2
> "productive closure 的判据是 COMM RMSD < 1.5 A 且 K82-Q2 distance <= 3.6 A"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE** |
| **Source** | SOURCED — manifest `osuna2019_benchmark_manifest.yaml` lines 58-60 cite these as `explicit_from_literature`. MASTER_TECHNICAL_GUIDE.md section 1.2 explicitly attributes to JACS 2019 Figures 2-3. |
| **Overclaim risk** | **LOW**. However, a nuance: the < 1.5 A criterion is relative to a specific closed reference structure (3CEP alignment). The 3.6 A K82-Q2 distance is from structural clustering of metastable states in the JACS 2019 FEL analysis. These are operational thresholds from one paper, not universal constants. |
| **Correction** | None required, but recommend annotating that these thresholds are specific to the Osuna 2019 analysis framework and may differ if different reference structures or alignment methods are used. |

---

### Claim 3
> "GenSLM 生成了约 100,000 个 TrpB 候选序列"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **INACCURATE** |
| **Source** | The number is INCONSISTENT across the repo. `FULL_LOGIC_CHAIN.md` (lines 281, 295, 459) says "100,000". `MASTER_TECHNICAL_GUIDE.md` (line 870) says "60,000". The reading notes (`GenerativeDesign_LandscapeReview.md` line 177) also say "60,000". Lambert et al. 2026 (Nature Communications, DOI: 10.1038/s41467-026-68384-6) generated **60,000** TrpB sequences. Of these, 105 candidates were selected for experimental testing. |
| **Overclaim risk** | **HIGH**. The 100,000 figure appears to be a hallucination or confusion. It inflates the scale of the dataset by 67%. |
| **Correction** | Replace all instances of "100,000" with "60,000" in `FULL_LOGIC_CHAIN.md`. The correct pipeline: 30,000 training sequences -> GenSLM fine-tuning -> 60,000 generated sequences -> multi-stage filtering -> 105 candidates experimentally tested. Also add FP entry for this data error. |

---

### Claim 4
> "GenSLM-230 的活性超过了 PfTrpB0B2"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE, with qualification** |
| **Source** | SOURCED — Lambert et al. 2026, Nature Communications. FULL_LOGIC_CHAIN.md line 288; MASTER_TECHNICAL_GUIDE.md references this finding. The reading notes and deep annotations corroborate. |
| **Overclaim risk** | **MEDIUM**. The claim as stated is unqualified. "活性" (activity) needs specification: which assay conditions? L-Trp synthesis kcat? Total turnover? The project documents don't specify the exact metric or conditions under which GenSLM-230 outperforms PfTrpB0B2. Furthermore, this is from a single publication by the GenSLM team themselves. |
| **Correction** | Add specificity: "GenSLM-230 的 L-Trp 合成催化活性超过了 PfTrpB0B2 (Lambert et al. 2026, specific assay conditions: [TBD after reading paper in detail])". This is not wrong but needs the underlying numbers cited. |

---

### Claim 5
> "PLP 总电荷 = -2，基于 Caulkins 2014 NMR 数据"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE** |
| **Source** | SOURCED — Caulkins et al. 2014, JACS, 136, 12824 (DOI: 10.1021/ja506267d). Four-way cross-validation documented in MASTER_TECHNICAL_GUIDE.md section 3.2.2, PROTOCOL.md lines 152-158, and TECHNICAL_REASONING_LOG.md TR-001. The charge decomposition is: phosphate (-2) + O3 (-1) + N1 (0) + NZ (+1) = -2. |
| **Overclaim risk** | **LOW**. This is one of the best-sourced claims in the project. The NMR evidence is direct experimental measurement, cross-validated by Huang et al. 2016 MD comparison. |
| **Correction** | None. Exemplary sourcing. Note that this applies specifically to the Ain (internal aldimine) intermediate; other intermediates (Aex1, A-A, Q2) may have different protonation states and charges. The project already handles this correctly (PLP_SYSTEM_SETUP_LOGIC_CHAIN.md). |

---

### Claim 6
> "GAFF + RESP 对 PLP 的参数化在研究构象动态的语境下是 defensible 的"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE, with qualification** |
| **Source** | SOURCED — MASTER_TECHNICAL_GUIDE.md section 6.4 provides extensive literature context. JACS 2019 SI confirms GAFF+RESP was the method used by Osuna. The "defensible" qualifier is explicitly conditioned on the research question being conformational dynamics, not catalytic chemistry. |
| **Overclaim risk** | **LOW** (because the claim is already self-limiting). The document correctly states: "但只在'我们研究的是构象动态而非化学反应'的前提下。如果研究问题变成 PLP 催化机制，你需要升级什么？" This is honest and appropriate. |
| **Correction** | None required. The document already acknowledges GAFF's weaknesses: (1) torsion parameters for PLP pyridine ring from limited QM training sets, (2) Markthaler et al. 2019 showing poor performance for aromatic heterocycle derivatives, (3) FP-010 demonstrating atom typing failures. The reasoning -- that COMM domain motion is driven primarily by backbone H-bonds, salt bridges, and hydrophobic contacts (covered by ff14SB), not by PLP-specific torsions -- is physically reasonable. |

---

### Claim 7
> "没有人对蛋白质构象动态做过 generate -> simulate -> retrain 的闭环"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **UNVERIFIABLE from repo evidence alone** |
| **Source** | UNSOURCED — no literature search proving a negative. MASTER_TECHNICAL_GUIDE.md line 940 states this as a "novelty claim" but provides no systematic literature survey to support the negative assertion. |
| **Overclaim risk** | **HIGH**. This is the most dangerous claim in the project. Proving that something has "never been done" requires exhaustive search. The document does cite related work (REINVENT+ESMACS for small molecules, METL for Rosetta-based approach, SeqDance for dynamics-aware PLM) but none of these is a direct counterexample. However: (1) REINVENT+ESMACS (JCTC 2024) does do generate->simulate->retrain for *small molecule* binding, which is conceptually very close. (2) The distinction between "conformational dynamics" and "binding free energy" may be seen as splitting hairs by a reviewer. (3) There may be unpublished or very recent work doing exactly this. |
| **Correction** | Downgrade from a factual statement to a hypothesis/positioning: "据我们所知 (to the best of our knowledge)，尚无公开发表的工作将蛋白质构象动态 FEL 作为 reward signal 用于生成模型的闭环迭代。" Add "as of [date]" and cite the systematic landscape review that was done (`GenerativeDesign_LandscapeReview.md`). Also explicitly acknowledge REINVENT+ESMACS as a close analogue in the small-molecule domain. |

---

### Claim 8
> "Well-tempered MetaDynamics 在 2019 年是正确选择"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE** |
| **Source** | SOURCED — MASTER_TECHNICAL_GUIDE.md section 6.2 provides a detailed chronological analysis. Key facts: OPES not published until 2020 (Invernizzi & Parrinello, J. Phys. Chem. Lett. 11, 2731-2736); GaMD (2015) doesn't focus acceleration on specific conformational changes; REST2 doesn't yield FES. WT-MetaD (Barducci et al. 2008, Phys. Rev. Lett. 100, 020603) was the state-of-the-art for CV-based enhanced sampling in 2019. |
| **Overclaim risk** | **LOW**. The document appropriately qualifies: "在 2019 年完全正确" and then immediately states that today (2025-2026) one would likely choose OPES or OneOPES with ML-learned CVs. This is honest and well-reasoned. |
| **Correction** | None. The document also acknowledges WT-MetaD's principal weakness (orthogonal slow DOF problem, Yang et al. Nature Communications 2025). This is appropriately self-critical. |

---

### Claim 9
> "Path CV 假设真实转换近似沿参考路径发生"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE** |
| **Source** | SOURCED — Branduardi, Gervasio & Parrinello 2007, J. Chem. Phys. 126, 054103 (DOI: 10.1063/1.2432340). MASTER_TECHNICAL_GUIDE.md section 6.3 line 916 explicitly states this as a "假设检验" (hypothesis test). |
| **Overclaim risk** | **NONE** — this is a statement about a methodological assumption, not a result claim. The document correctly identifies this as a limitation and notes that if the real pathway has large curvature, the Path CV will produce artificially smoothed FES. It also cites Felts et al. 2023 (J. Phys. Chem. B) on the Calpha-only limitation. |
| **Correction** | None. This is an example of good scientific self-awareness. |

---

### Claim 10
> "Lambda = 2.3 / MSD, JACS 报告 MSD ~ 80 A^2 -> lambda ~ 0.029"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE** |
| **Source** | SOURCED — JACS 2019 SI p.S3 states lambda = 2.3 / MSD. JACS2019_MetaDynamics_Parameters.md line 114 records: "2.3 x (1/80) ~ 0.029". Manifest line 123 records: "lambda: 2.3 / mean_square_displacement_between_frames (MSD=80)". |
| **Overclaim risk** | **LOW**. The formula and values are correctly extracted from the SI. One note: the SI says "MSD" meaning average *mean square displacement* between consecutive reference frames. The exact definition (per-atom mean vs total sum over atoms) is ambiguous in the SI, as flagged by FP-015 and the independent verification report. |
| **Correction** | None for the claim itself. The ambiguity about per-atom vs total-sum convention should remain documented (it already is, in FP-015 and the verification report). |

---

### Claim 11
> "我们的 lambda = 0.034, 差异来自路径构建细节，不是代码 bug"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE, with qualification** |
| **Source** | PARTIALLY SOURCED — the lambda = 0.034 value is confirmed by `summary.txt` (Total SD = 67.826 A^2, lambda = 0.033910). The independent verification report (2026-04-01) confirms: "Discrepancy: ~15%, attributed to path construction details (alignment/residue mapping), not code bug." Campaign report line 84 concurs. FP-015 fix has been verified (sqrt bug removed). |
| **Overclaim risk** | **MEDIUM**. The attribution to "路径构建细节" (path construction details) is a *hypothesis*, not a verified conclusion. The 15-17% discrepancy (0.034 vs 0.029) could come from: (1) different structural alignment methods, (2) different atom selection (our code vs Osuna's code), (3) different handling of missing residues in 1WDW/3CEP, (4) the per-atom vs total-sum MSD convention difference. None of these has been systematically ruled in or out. Saying "not a code bug" is supported (FP-015 verified the code logic), but saying "comes from path construction details" is an educated guess. |
| **Correction** | Change to: "我们的 lambda = 0.034 (SD_total = 67.8 A^2), 与 JACS 值 0.029 (MSD~80 A^2) 有 ~17% 差异。FP-015 修复后代码逻辑已验证正确。差异可能来自路径构建细节（structural alignment, residue mapping, MSD convention），但具体原因尚未确定。" This is more honest. |

---

### Claim 12
> "AMBER -> GROMACS 转换改变的是程序，不是物理"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE as a design intent; UNVERIFIABLE as a factual statement** |
| **Source** | SOURCED as a principle — MASTER_TECHNICAL_GUIDE.md section 3.6 explicitly states: "转换后改变的应该是程序，不应该是物理。" This is correctly identified as a *requirement* to be verified, not a guaranteed outcome. |
| **Overclaim risk** | **MEDIUM**. The phrasing in FULL_LOGIC_CHAIN.md line 553 ("转换后改变的应该是程序，不应该是物理") correctly uses "应该" (should). However, in practice, AMBER/GROMACS differences in: (1) 1-4 scaling conventions, (2) GAFF atom type mapping, (3) PME implementation details, (4) thermostat/barostat implementations could introduce small but real physical differences. The conversion script includes energy consistency checks (convert_amber_to_gromacs.py, verified in parameter verification report), but this conversion has NOT YET BEEN EXECUTED (status: D-all UNVERIFIED in verification report). |
| **Correction** | Until the energy consistency check is actually run, this claim should be stated as: "AMBER -> GROMACS 转换的*目标*是只改变程序不改变物理。转换后必须通过分项能量对比确认这一点。当前转换尚未执行。" |

---

### Claim 13
> "AlphaFold 预测的是单一静态结构，不是构象分布"

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **ACCURATE as a first approximation, but OUTDATED as of 2025-2026** |
| **Source** | SOURCED — Lane (2023) is cited in MASTER_TECHNICAL_GUIDE.md line 874: "AF2 'likely does not learn the energy landscapes underpinning protein folding and function'". GenerativeDesign_LandscapeReview.md line 96: "AlphaFold2 predicts a single ground-state structure. It was NOT designed to predict conformational landscapes." |
| **Overclaim risk** | **MEDIUM-HIGH in the current landscape**. This was accurate for AlphaFold2 (2021-2024), but the field has moved: (1) AlphaFold3 (2024) predicts multiple conformations for some systems. (2) Osuna group's own tAF2-MD approach (cited in the repo's Modern_MD_Alternatives_Review.md) uses template-based AF2 to *generate diverse conformations*. (3) AF2 MSA subsampling has been shown to produce conformational diversity (Del Alamo et al., eLife 2022). (4) AlphaFlow and Distributional Graphormer (2024) are specifically designed to predict conformational distributions. Stating "AlphaFold predicts a single static structure" is a strawman in 2026. |
| **Correction** | Update to: "标准 AlphaFold2 的默认输出是单一（或少数高置信度的）静态结构预测，不直接给出 Boltzmann-weighted 的构象分布。虽然后续工作（tAF2-MD, MSA subsampling, AlphaFlow, AF3）已在一定程度上突破这一限制，但对于需要定量自由能面的问题（如 TrpB COMM domain 的 O/PC/C 转换势垒），增强采样 MD 仍然是不可替代的。" This is both more accurate and actually stronger as an argument. |

---

### Claim 14
> "MetaDynamics FEL 上 Closed 态的深度 ~ 催化活性"（第 6 章原话）

| Criterion | Assessment |
|-----------|------------|
| **Accuracy** | **INACCURATE as stated** |
| **Source** | FULL_LOGIC_CHAIN.md line 263: "FEL 上 Closed 态的深度 ≈ 催化活性". The "≈" symbol implies approximate quantitative equivalence, which is not what the evidence shows. |
| **Overclaim risk** | **HIGH**. This is the most scientifically dangerous overclaim in the project. The problems: |
| | (1) **Correlation != equality**: Osuna 2019 shows that variants with deeper Closed basins tend to have higher kcat. But "depth ≈ activity" implies a near-quantitative relationship, which was never established. The paper shows 3 data points (kcat = 0.31, 1.0, 2.9 s^-1) with qualitative FEL differences -- this is not a calibration curve. |
| | (2) **Confounding factors**: Catalytic activity depends on many things beyond COMM domain closure: substrate binding affinity, PLP chemistry, product release rate, active-site preorganization. The FEL only captures one dimension of the problem. |
| | (3) **Productive vs unproductive closure**: The document itself (section 3.4) explains that not all "closed" structures are catalytically productive. So the depth of the C basin in FEL space doesn't map directly to catalytic output -- you also need the closure to be productive (K82-Q2 < 3.6 A). |
| | (4) **Thermodynamic vs kinetic**: FEL depth is a thermodynamic quantity (free energy difference). Catalytic activity (kcat) is a kinetic quantity. The relationship between them is not straightforward -- a deep basin can be kinetically trapped. |
| **Correction** | Replace with: "FEL 上 Closed 态的相对自由能与催化活性定性相关（Osuna 2019 在 3 个 TrpB 变体上展示了这种趋势），但两者之间不存在简单的定量等价关系。Productive closure 还需要活性位点几何判据的配合。" In FULL_LOGIC_CHAIN.md line 263, change the "≈" to "定性相关于". |

---

## Cross-Cutting Findings

### Finding A: The 100,000 vs 60,000 discrepancy (Claim 3) is a data integrity issue.

`FULL_LOGIC_CHAIN.md` uses "100,000" in at least 3 places (lines 281, 295, 459), while `MASTER_TECHNICAL_GUIDE.md` and `GenerativeDesign_LandscapeReview.md` correctly say "60,000". This indicates the FULL_LOGIC_CHAIN was written or edited without cross-checking against the primary source. **This should be filed as a new failure pattern (FP-016).**

### Finding B: Novelty claims (Claim 7) need systematic evidence.

The "没有人做过" framing appears in a document that serves both as internal documentation and as potential interview/presentation material. Negative existence claims require citation of systematic reviews. The `GenerativeDesign_LandscapeReview.md` does survey the landscape but does not explicitly conclude "no one has done generate->simulate->retrain for conformational dynamics". The claim should be softened to "to the best of our knowledge".

### Finding C: FEL-activity relationship (Claims 1, 14) is the scientific backbone of the project but is systematically overclaimed.

The project correctly identifies the FEL->activity correlation as its foundational premise, but multiple documents state it more strongly than the evidence supports. A 3-point correlation from a single lab's work is a strong hypothesis, not a proven law. This matters because the entire reward function design (Chapter 8) depends on this relationship being quantitative, which it currently is not.

### Finding D: The project's self-critical apparatus is strong.

The failure-patterns.md system, the independent parameter verification, the "假设检验" and "批判性思考" prompts in MASTER_TECHNICAL_GUIDE.md, and the explicit UNVERIFIED labels all demonstrate a level of scientific rigor that is unusual and commendable. Most of the overclaims identified here exist in the earlier-written FULL_LOGIC_CHAIN.md and are already partially corrected in the later MASTER_TECHNICAL_GUIDE.md.

---

## Recommended Actions

| Priority | Action | Affected Files |
|----------|--------|----------------|
| **HIGH** | Fix 100,000 -> 60,000 everywhere; file FP-016 | `FULL_LOGIC_CHAIN.md` (3+ locations) |
| **HIGH** | Soften "FEL depth ≈ activity" to "FEL depth correlates qualitatively with activity" | `FULL_LOGIC_CHAIN.md` line 263 and Chapter 8 |
| **HIGH** | Add "to the best of our knowledge" to novelty claim | `MASTER_TECHNICAL_GUIDE.md` line 940 |
| **MEDIUM** | Update AlphaFold characterization to reflect AF3/tAF2-MD/AlphaFlow | `MASTER_TECHNICAL_GUIDE.md` line 874 |
| **MEDIUM** | Clarify lambda discrepancy as unresolved hypothesis | Campaign report, NEXT_ACTIONS |
| **LOW** | Add assay-specific details to GenSLM-230 activity claims | `FULL_LOGIC_CHAIN.md` line 288 |

---

*Reviewed: 2026-04-01 by Independent Skeptic Agent*
*Files examined: FULL_LOGIC_CHAIN.md, MASTER_TECHNICAL_GUIDE.md, JACS2019_MetaDynamics_Parameters.md, osuna2019_benchmark_manifest.yaml, failure-patterns.md, 2026-04-01_independent_parameter_verification.md, GenerativeDesign_LandscapeReview.md, PROTOCOL.md, TECHNICAL_REASONING_LOG.md, campaign reports, NEXT_ACTIONS.md*
