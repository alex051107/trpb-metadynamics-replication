# MetaD-to-ML Cartridge for TrpB Sequence Design — 多代理深度研究报告

**Date**: 2026-04-24
**Author**: Multi-agent research team (Claude Opus 4.7 + 4 subagents)
**Scope**: 评估 "把 MetaD-derived FES 转成 ML labels 反馈到 sequence generation pipeline" 的可行性、新颖性、技术路线、与失败模式

---

## 1. Executive Verdict

**Partially novel, scientifically defensible，但成败 hinge 于两件超出学生控制的事**：(a) WT MetaD 在 10 周内能否 converge 到 strong-tier label；(b) Yu 是否真提供 1–2 个 variant 让你做 wet-lab correlation。

文献调研确认：MetaD/FES → generative sequence model 的闭环 **没有 EXACTLY TAKEN 的 prior art**。最近 prior 是 Osuna 自家的 SPM (Faraday Discuss. 2024，用 unbiased MD correlation 做 *人工* 设计) 和 METL (PMC12446067，用 *static* Rosetta 单点能 pre-train PLM)。BioEmu (Science 2025) 在 "MD→FES surrogate" 一段做了 generic protein 的 free-energy emulation，所以 defensible claim 必须收窄到 **"path-CV catalytic-cycle state populations + barriers as conditional reward for sequence-design generators"**。

可行的 v0 (2 周) = **schema + tooling + N=1 demo**，不承诺 scientific claim。可行的 v1 (10 周) = **internal lab tool + N=2-3 variant pilot**，stretch goal 是 workshop-paper draft (P~0.2-0.3)。Surrogate 走 GP+heteroscedastic NLL；feedback 顺序必须是 reranker → reward shaping (with σ-cap) → active learning，绝不能跳步。**最大 single point of failure 是 D-Trp vs L-Trp mechanism**——你和我都 UNCERTAIN，第 1 周必读 D-Trp primary literature (Hilvert / Buller lab)。

> **Go/no-go**: 概念值得做，但必须把 framing 从 "I will predict catalysis" 收窄到 "I provide mechanism-grounded evaluation infrastructure that is currently missing"。任何 over-promise 在 Anima/Arvind/PI 层都会被打 50% 折扣。

---

## 2. Prior-Art Table (浓缩版，详见 Part A 输出)

| Paper | Year | What sim produced | What ML consumed | Seq design? | Verdict |
|---|---|---|---|---|---|
| Maria-Solano & Osuna, JACS 2019 | 2019 | PATHMSD MetaD on TrpB COMM | none (manual) | no | RELATED ONLY (this is our replication target) |
| Duran et al., SPM, Faraday Discuss. 2024 | 2024 | unbiased MD correlations | hotspot graph | manual rational | CLOSE BUT DIFFERENT |
| METL, PMC12446067 | 2025 | Rosetta single-points | PLM pre-train | yes | CLOSE BUT DIFFERENT |
| ProtRL, arXiv:2412.12979 | 2024 | user-defined reward | DPO/GRPO on pLM | yes | RELATED ONLY |
| ProteinGuide, arXiv:2505.04823 | 2025 | any property scorer | guided generation | yes | RELATED ONLY (could *consume* our cartridge) |
| BioEmu, Science 2025 | 2025 | MD-derived equilibrium ensembles | pre-train | no | CLOSE BUT DIFFERENT (generic protein, not enzyme catalysis path-CV) |
| ConfRover, arXiv:2505.17478 | 2025 | unbiased MD trajectories | autoregressive ensembles | no | RELATED ONLY |
| MDGen, arXiv:2409.17808 | 2024 | unbiased MD (tetrapeptides) | generative trajectories | no | RELATED ONLY |
| RigidSSL, arXiv:2603.02406 | 2026 | MD frames (augmentation) | rigidity pre-train | yes | RELATED ONLY |
| EnzymeCAGE, Nat. Catal. 2026 | 2026 | static structures | retrieval | no | NOT RELEVANT (complementary) |
| **STAR-MD** | n/a | n/a | n/a | n/a | **NOT FOUND** — ask user for authors/DOI |
| **PLaTITO** | n/a | n/a | n/a | n/a | **NOT FOUND** — ask user for authors/DOI |

**Defensible novelty 句**: "Path-CV MetaDynamics-derived state-population and barrier labels for catalytic-cycle conformations, fed as conditional reward into sequence-design generators (RFdiffusion + MPNN + GRPO). Unlike BioEmu (generic ensemble emulation, no design loop) or ProteinGuide (guidance mechanism agnostic to label source), this provides the missing *enzyme-mechanism-grounded* label channel."

**Action**: 跟 PM 确认 STAR-MD / PLaTITO 的真实 paper/repo (是 Amin 内部代号还是已发表？)。在确认前不要在 paper 里跟它们对比。

---

## 3. Correct Technical Pipeline (Candidate sequence → MetaD label → ML feedback)

```
[1] Variant generation         → RFD3 / MPNN / GRPO / handcrafted
       │
[2] Structure prep             → AF2 fold + tleap (parm7/inpcrd) + GROMACS conversion
       │                          (reuse existing PLP-RESP frcmod, charge=-2)
[3] Path-CV definition         → path_seqaligned (post-FP-034) on COMM Cα,
       │                          15 frames, λ ≈ 379.77 nm⁻², SANITY CHECK:
       │                          1WDW frame → (s,z)≈(1,0); 3CEP → (15,0)
[4] WT-MetaD production        → 10-walker, BIASFACTOR=10, HEIGHT=0.15 kcal/mol,
       │                          ADAPTIVE=DIFF, UPPER_WALLS on z; cumulative target
       │                          gated by convergence (B4 tier policy)
[5] Convergence diagnostics    → block-FES (last ⅓ vs prior, std<0.3 kcal/mol),
       │                          walker-jackknife σ, re-crossing count, c(t) plateau
[6] Reweighting                → PLUMED REWEIGHT_BIAS → per-frame w_i
[7] FES → state population     → state masks (B2: SI windows + watershed sanity);
       │                          P_O, P_PC, P_C from ∑w_i / ∑w_total
[8] FES → ΔG and barriers      → 1D F(s) projection (primary) + 2D MFEP (sanity)
[9] Off-path & geometry        → Φ_off (z>z_thr); productive geom χ(R) per B5
       │                          (LOCKED to Ain intermediate for v0)
[10] Variant-row assembly      → variants.parquet row + label_tier classification
[11] Surrogate training        → GP-Matérn5/2 on ESM2-mean-pool (256-d PCA) + AS feats,
       │                          heteroscedastic NLL with per-sample CI as noise floor
[12] Feedback                  → reranker (v0) → GRPO reward with σ-cap (v1) →
                                  GP-UCB active learning (v1+)
```

**注意分层 (Layer 1/2/3 distinction)**：
- Layer 1 (descriptor): 任何结构都能算 (s, z, K82-PLP geom, H6 closure)。**不是 thermodynamic label**
- Layer 2 (FES label): 必须 MetaD + reweighting (P_state, ΔG, barrier, Φ_off)
- Layer 3 (ML feedback): 用 Layer 2 训 surrogate

绝不允许把 Layer 1 frame-level 数据当 Layer 2 thermodynamic label 直接喂 ML。

---

## 4. Data Schemas

### Frame-level `frames.parquet` (Layer 1，描述用，不直接训 ML)

| Column | dtype | unit | Notes |
|---|---|---|---|
| variant_id | str (FK) | — | |
| walker_id | uint8 | — | 0–9 |
| time_ns | float32 | ns | |
| s, z | float32 | dimensionless / nm² | post-FP-034 path |
| state_assignment | category {O, PC, C, off, transit} | — | |
| w_reweight | float32 | dimensionless | exp[(V−c(t))/kT] |
| K82_PLP_dist, H6_closure_d1/d2, chi1_F184, ... | float32 | Å / deg | 见 B5 表 |
| bias_V | float32 | kJ/mol | |
| block_id | uint16 | — | for jackknife/bootstrap |

### Trajectory-level `trajectories.parquet` (Layer 2 QC)

| Column | dtype | unit |
|---|---|---|
| variant_id (PK), walker_count, sim_time_ns_total | | |
| FES_convergence_score | float32 [0,1] | |
| P_O, P_PC, P_C, P_off | float32 [0,1] | |
| dG_PC_O, dG_C_O, barrier_O_PC, barrier_PC_C | float32 | kJ/mol |
| ESS, CI_*_lo, CI_*_hi | float32 | |
| label_tier | category {strong, medium, weak, reject} | |
| walker_diffusion, notes | | |

### Variant-level `variants.parquet` (Layer 3，ML 输入)

| Column | dtype |
|---|---|
| variant_id (PK), sequence, mutations_vs_WT, parent, generator | |
| n_mutations, seq_id_to_WT | |
| score, score_CI_width, confidence_weight, label_tier | |
| dG_PC_O, barrier_O_PC, P_PC, P_C, P_off (exposed for multi-task / Pareto) | |
| embedding_path, structure_path | |

Target size: v0 ≈ 10–20；v1 ≈ 50–100。

---

## 5. Label Construction (Formula sheet)

### Reweighted density (Tiwary–Parrinello 2015)

```math
w_i = \exp\!\Big[\frac{V(s_i,z_i;t_i) - c(t_i)}{k_B T}\Big],\quad
p(s,z) = \frac{\sum_i w_i\,\delta(s-s_i)\delta(z-z_i)}{\sum_i w_i}
```

### State occupancy & free energy

```math
P_{\text{state}} = \frac{\sum_{i\in\Omega_{\text{state}}} w_i}{\sum_i w_i},\quad
G_{\text{state}} = -k_B T \ln(P_{\text{state}}/P_{\text{ref}})
```

### Barrier (1D projection)

```math
F(s) = -k_B T \ln\!\Big[\sum_i w_i \delta(s-s_i)/\sum_i w_i\Big],\quad
\Delta F^{\ddagger}_{A\to B} = \max_{s\in[s_A,s_B]} F(s) - F(s_A)
```

### Off-path penalty

```math
\Phi_{\text{off}} = \frac{\int_{z>z_{thr}} F(s,z)\,p(s,z)\,ds\,dz}{\int_{z>z_{thr}} p(s,z)\,ds\,dz}
```

### Productive geometry

```math
\Pi_{\text{state}} = \frac{\sum_{i\in\Omega_{\text{state}}} w_i \chi(R_i)}{\sum_{i\in\Omega_{\text{state}}} w_i}
```

`χ(R) ∈ [0,1]` 由 rule-based gate 组合：K82-PLP < 1.7 Å (Schiff base intact) AND H6 closure within WT distribution AND active-site water count < threshold。**仅在 Ain intermediate 下定义**；Aex1/A-A/Q2 需重 parameterize PLP-substrate adduct (out of v0 scope)。

### Transition-accessibility scalar

```math
\text{score} = \alpha(-\Delta G_{PC\to O}) + \beta(-\Delta F^{\ddagger}_{O\to PC}) + \gamma P_{PC} + \delta P_C - \varepsilon P_{\text{off}} + \zeta\,\text{geom\_score} - \eta\,\text{CI\_width}
```

v0 默认: α=0.25, β=0.30, γ=0.15, δ=0.10, ε=0.30, ζ=0.15, η=0.10 (PM 签字后冻结)。

### Confidence-weighted training label (empirical-Bayes shrinkage)

```math
\tilde{\text{score}}_i = w_i\,\text{score}_i + (1-w_i)\,\text{score}_{\text{WT}},\quad
w_i = \min(1, \text{ESS}_i/500)\cdot \exp(-\text{CI\_width}_i/\sigma_{\text{ref}})
```

### Label tier policy (Skeptic gate)

| Tier | ESS/N | CI on ΔG | Sim length | Walker presence | Conv. std | ML use |
|---|---|---|---|---|---|---|
| strong | ≥10% | ≤0.5 kcal/mol | ≥50 ns/walker | ≥7/10 | <0.3 kcal/mol | supervised regression |
| medium | 1–10% | 0.5–1.5 | 30–50 | 4–6/10 | 0.3–0.8 | weighted training, ranking |
| weak | 0.1–1% | 1.5–3 | 20–30 | 2–3/10 | 0.8–1.5 | binary classifier |
| reject | <0.1% | >3 | <20 | ≤1/10 | not converged | active-learning trigger only |

**Refs**: Tiwary & Parrinello *JPCB* 2015; Branduardi et al. *JCP* 2007 (path-CV); Bonomi/Barducci/Parrinello *JCC* 2009 (block analysis); Barducci/Bussi/Parrinello *PRL* 2008 (well-tempered convergence).

---

## 6. ML Model Recommendation

### v0 (5–20 variants)
- **GP regression, Matérn-5/2 kernel, ARD lengthscales** over a 256-d PCA of ESM2-650M mean-pool + ~20-d handcrafted active-site features
- Heteroscedastic noise per-point set from `CI_width`
- Multi-output via independent GPs per head (or LMC if N≥15)
- Loss: heteroscedastic Gaussian NLL
- CV: leave-one-out with **mutation-cluster blocking** (group variants sharing ≥1 mutated position)
- 期望: Spearman ρ ≈ 0.3–0.55, R² ≈ 0.1–0.35 (诚实预期：仅作 top-K ranker, **不**作可靠 point predictor)
- **如果 ρ<0.3 → STOP**，labels 太 noisy 或 X 选错

### v1 (20–100 variants)
- Ensemble of GPs with different kernels + Bayesian ridge baseline
- Stack via inverse-variance averaging
- 添加 pairwise ranking loss (RankNet-style) for top-K selection
- 5-fold stratified CV by `n_mutations` AND `parent`，blocked Hamming<2

### 永远不做
- 端到端 GNN on full structure (overparameterized at N≤100)
- ESM full fine-tune (cost prohibitive, no data)
- Deep MLP without ensembling
- Tanimoto kernel on continuous embeddings (UNCERTAIN — 不适用)

**Refs**: Yang/Wu/Arnold *Nat Methods* 2019; Wittmann/Yang/Arnold *Cell Sys* 2021; Hie/Bryson/Berger 2020 (GP-UCB protein); Dallago et al. 2021 (FLIP splits); Notin et al. 2023 (ProteinGym).

---

## 7. Feedback into Sequence Generator

| Mode | Tech requirement | Risk | When | Integration |
|---|---|---|---|---|
| **Reranking** | trained surrogate; sort by μ−λσ (LCB) | miscalibration on top-K | **v0 first** | Post-hoc on top-200 RFD3+MPNN, submit top-10 to MetaD. No generator change. |
| **Reward shaping (GRPO)** | surrogate as reward channel; uncertainty-cap | **reward hacking** — generator finds OOD high-σ regions | After reranker validated (ρ≥0.5 held-out) | Add `r_surr = μ(x) − λσ(x)`, **cap when σ>σ_thr**. α ramp 0→0.3 over iterations. **UNCERTAIN**: HuggingFace TRL GRPO 是 scalar-only as of 2025 — 需确认 Raswanth 的 implementation |
| **Active learning** | surrogate + acquisition (UCB/qEI/Thompson); MetaD budget | cold start; GP scaling at N>200 | When budget allows 3+ rounds | BO outer loop: GP-UCB selects 5–10 → MetaD labels → retrain |

**关键顺序**：reranker → reward shaping with σ-cap → active learning。**绝不能跳到 reward shaping**——没 calibrated surrogate, GRPO 一个 iteration 就 reward-hack。

---

## 8. Stakeholder Fit

| Stakeholder (UNCERTAIN — 角色推断) | What helps | What resonates | Avoid |
|---|---|---|---|
| **Yu (wet lab)** | Variant table + dashboard 排序 | "在你跑 assay 前给 priority list, 省 wet-lab cycle" | "predicts kcat/KM" — 她有真数据立刻拆穿。说 "necessary but not sufficient for catalysis" |
| **Amin (STAR-MD/trajectory ML)** | reweighted FES + path-CV labeled frames as benchmark | "MetaD = thermodynamically grounded ground-truth distribution; STAR-MD 在上面 benchmark sampling fidelity" | "我的 MetaD 比你的 STAR-MD 好/快"。强调 **complementary**, 不是 replacement |
| **Raswanth (GRPO/reward)** | tabular reward function 接口 + σ-cap policy | "give you a mechanism-grounded reward channel beyond pLDDT/ESM-likelihood" | 别说 "替换你的 reward"。诚实说 throughput gap: MetaD/variant 几天 vs GRPO/step 一 variant — 用 surrogate 桥接 |
| **Arvind (mechanism reviewer)** | path-CV 选取理由 + JACS 2019 quantitative comparison + D-Trp vs L-Trp explicit handling | "FP-034 修复前后 ⟨MSD⟩ 差 26×, 我的 label reliability hinge on path-CV correctness" | 别用 PLUMED-tutorial 级 convergence 标准。不带 error bar 的 barrier 数字。把 PC 当 generic intermediate 不区分 D-Trp 机制 |
| **Anima (PI)** | one-page concept + minimum demo (即使 N=1) | "Most generative protein papers benchmark on static metrics. Catalysis 是 dynamic property — 我提供 evaluation infrastructure that bridges generative ML and enzyme catalysis" | "I will use ML to predict FES" (over-promise). "improve TrpB activity by X%". Generic "AI for science" framing |

**Anima 的"not generic" 要靠**:
1. Mechanism-anchored (not sequence-anchored) evaluation — TrpB COMM transition 有 wet-lab ground truth
2. MetaD 当 evaluation 不当 model — niche framing
3. Replicated published reference (JACS 2019) — baseline grounded, 差异 measurable

**Skeptic 警告**: 没有 ≥1 个 variant 的 wet-lab correlation 之前，"not generic" 是 *potential* 不是 demonstrated。

---

## 9. Failure Modes and Tests

| # | Failure | Prob | Damage | Test |
|---|---|---|---|---|
| 1 | **Unconverged FES used as label** | High (0.7) | Severe | `scripts/check_metad_convergence.py`: (a) block analysis ΔF<2 kJ/mol; (b) walker σ<1 kJ/mol per bin; (c) re-crossing ≥3; (d) HILLS τ extracted, sim ≥5τ. **Hard gate** on `label_tier=strong` |
| 2 | **Label not predictive of wet-lab activity** | Med-High (0.5–0.6) | Severe | **Wet-lab anchor test**: 选 Osuna/Hilvert paper 中已知 activity 的 3–5 mutants, compute Spearman ρ(score, log kcat/KM). \|ρ\|<0.4 with N≥3 → demote to "exploratory descriptor" |
| 3 | **Surrogate learns simulation artifact** | Med (0.4) | High | **Hyperparameter robustness sweep**: train with 2× (λ, bias_factor, walker_count), if RMSE_across>50% RMSE_within → refuse GRPO deploy |
| 4 | **No one in lab adopts the tool** | Med-High (0.5) | High | **Adoption metric** at week 5: ≥1 lab member 自主查 dashboard 1 次 (server log). 0 次 → pivot, 问对方"什么 format 你会用" |
| 5 | **Active-site descriptors mismatch D-Trp chemistry** | Med (0.3–0.4) | High | **Stereochemistry sanity test**: load D-Trp 与 L-Trp Aex1 mirror pair, assert chirality-sensitive descriptors give *opposite* sign |

**还要警惕但没列入 top 5**: FP-034 类 cross-species path bug 在 mutation 改 residue 数时复发；PLUMED 版本/source-build 漂移；学生身份给 senior 提建议被视为 over-step。

### 永远禁说的话

| 禁说 | 替换为 |
|---|---|
| "MetaD data is ground truth" | "best in-silico estimate conditional on (force field, CV choice, convergence)" |
| "We train a model to learn the transition state" | "committor-free barrier proxies along reaction-coordinate projection" |
| "This predicts catalytic activity" | "conformational accessibility score that *may correlate* — empirical validation pending (n=0)" |
| "50 ns single walker is enough" | "50 ns single walker is debug; production = 10-walker, cumulative target gated by block-analysis" |
| "Surrogate replaces MetaD" | "triage filter for prioritization; final ranking still requires MetaD on top-k" |
| "Cartridge generalizes to other enzymes" | "TrpB-specific; generalization requires re-deriving reaction-coordinate path" |
| "Path-CV s,z faithfully describes O→C" | "our chosen reaction-coordinate projection; alternative paths may give different barriers" |
| "State-of-the-art on TrpB design" | "no baseline exists; comparative benchmarking is future work" |

---

## 10. Papers to Read Next (Prioritized)

| # | Paper | Why |
|---|---|---|
| 1 | **D-Trp TrpB primary lit (Hilvert lab, Buller lab, possibly Bornscheuer 2019–2024)** | **Silent killer #0**: 你和我都 UNCERTAIN D-Trp vs L-Trp mechanism. L-Trp Osuna framework 不一定 transfer。第 1 周必读 |
| 2 | Tiwary & Parrinello, *JPCB* 2015, 119, 736 | Time-independent reweighting from WT-MetaD — **B1 公式直接来自这** |
| 3 | Branduardi/Gervasio/Parrinello, *JCP* 2007, 126, 054103 | Path-CV 原始 paper — λ 选取与 ⟨MSD⟩ 物理意义 |
| 4 | Barducci/Bussi/Parrinello, *PRL* 2008, 100, 020603 | Well-tempered convergence — Skeptic gate 标准 |
| 5 | Maria-Solano & Osuna, *JACS* 2019 (replicated) + 后续 ACS Catal. 2021/2022 | 你已经在复刻；后续 paper 涵盖 Aex1/A-A/Q2 — 给 v1 的 intermediate scope 路标 |
| 6 | Duran et al., SPM, *Faraday Discuss.* 2024 | 同 Osuna lab 的 mechanistic-feature → design pipeline，**最近的 prior art**，必须仔细区分 |
| 7 | METL, PMC12446067 (2025) | 最近的 simulation-labels-into-PLM paper — 区分 "static Rosetta vs dynamic MetaD" |
| 8 | BioEmu (Microsoft, *Science* 2025) + bioRxiv 2024.12.05.698041 | 最强 prior art for "MD→FES surrogate" — 你的 claim narrowing 必须建在区分上 |
| 9 | ProteinGuide, arXiv:2505.04823 | guidance mechanism — 你的 cartridge 可以是 ProteinGuide 的 reward provider，**reframe 工具不是竞争方** |
| 10 | Yang/Wu/Arnold *Nat Methods* 2019 + Wittmann/Yang/Arnold *Cell Sys* 2021 | Small-N protein ML — GP/baseline 的 sample-size 依据 |
| 11 | Hie/Bryson/Berger 2020 + ProteinGym (Notin 2023) | GP-UCB on protein + supervised low-N benchmarks |
| 12 | ConfRover (arXiv:2505.17478), MDGen (arXiv:2409.17808) | 你的 cartridge 可作为这俩的 evaluation harness — Amin-facing claim |
| 13 | Bonomi/Barducci/Parrinello *JCC* 2009 (block analysis); Pratyush Tiwary & Berne *PNAS* 2016 (time-derivative bias) | 实操 convergence diagnostic |
| 14 | (待 PM 确认) STAR-MD / PLaTITO 真实 paper | 否则无法 cite 或对比 |

---

## 11. Final Recommendation — 接下来 5 个工作日 Zhenpeng 该做什么

> **核心原则**: 不写新代码、不跑新 simulation，而是把"是否值得做"的事实基础打牢。代码生成全部走 Codex (per /Users/liuzhenpeng/.claude/CLAUDE.md role assignment)。

### Day 1 (周五)
1. **D-Trp vs L-Trp mechanism literature review** (silent killer #0)
   - Hilvert lab D-amino acid TrpB papers (2019–2024)
   - Buller lab β-replacement chemistry
   - 输出: `chatgpt_pro_consult_45558834/d_trp_mechanism_notes.md`，明确 "L-Trp Osuna framework 哪些 transfer / 哪些不 transfer"
2. **跟 PM 确认 STAR-MD / PLaTITO 是否真实存在**，要 authors/DOI/repo

### Day 2 (周一)
3. **跟 Yu / Raswanth / Amin 各发一封 5-行邮件** (用 cold-email-professor skill)
   - 不 propose cartridge，只问 "你现在的 input/output schema 是什么？我能不能把我的 MetaD 产出适配成你已有的接口？"
   - 目的：socially-validate stakeholder framing in D1 (现在全是我推断的 UNCERTAIN)

### Day 3 (周二)
4. **写 v0 schema (frame/trajectory/variant) 三张 parquet schema yaml**
   - Codex 任务: pydantic models + JSON schema export + unit test (WT round-trip)
   - 你 review 之后冻结成 `replication/cartridge/schema_v0.1/`

### Day 4 (周三)
5. **写 forbidden-claims policy + label-tier policy**
   - Markdown doc 放在 `replication/validations/cartridge_label_policy.md`
   - 每条 forbidden claim 配 safe alternative，每个 tier 配 hard-gate criterion
   - 给 Yu / Raswanth / Anima review

### Day 5 (周四)
6. **写 1-page concept memo for Anima** (不 send，先放 draft)
   - Framing = "Mechanism-grounded evaluation harness for generative protein design"
   - 引用 prior art 表 (BioEmu / ProteinGuide / METL) 并明确 narrow claim
   - 包含 minimum demo plan: WT 行 + 1 variant 行 (即使 weak tier)
   - 标注 known unknowns: D-Trp mechanism, STAR-MD identity, FES convergence timeline
7. **写 weekly report** (用 weekly-report skill) 总结这 5 天的 deliverable

### 5 天后的 checkpoint
- ✅ D-Trp lit review 完成 → 知道 cartridge 是否 fundamentally compatible with 项目目标
- ✅ Stakeholder schema 确认 → 知道 framing 是否站得住
- ✅ Schema/policy 冻结 → Codex 可以接手实现
- ❌ 不承诺任何 scientific result, 不跑新 simulation, 不训 surrogate

如果 D-Trp 文献显示 COMM dynamics 与 D-Trp 立体选择性 *无关*, **整个 cartridge 立即 pivot**——把 framing 改成 "TrpB COMM 替代 substrate 工程的 evaluation tool" 或者直接换 system。这是 5 天的最重要 finding。

---

**Hard rules compliance check**:
- ✅ Cited primary papers (Tiwary 2015, Branduardi 2007, Barducci 2008, JACS 2019, BioEmu Science 2025, etc.)
- ✅ Did not hallucinate exact novelty (STAR-MD/PLaTITO marked NOT FOUND)
- ✅ Marked UNCERTAIN explicitly (D-Trp mechanism, ESM3 availability, GRPO API, Tanimoto kernel, stakeholder roles)
- ✅ Separated descriptor (Layer 1) from MetaD-derived label (Layer 2)
- ✅ Separated frame-level (Table 1) from variant-level (Table 3)
- ✅ Did not recommend training large model from scratch (GP only at v0/v1)
- ✅ Did not recommend MetaD on every generated sequence (reranker → top-K only)
- ✅ Did not call unconverged biased trajectory equilibrium data (label_tier policy enforces)
- ✅ Did not confuse conformational transition with chemical TS (B3 explicitly distinguishes path-CV barrier from saddle/committor TS)
