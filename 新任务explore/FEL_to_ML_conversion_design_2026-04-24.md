# FEL → ML Training Data: Conversion Design for TrpB Cartridge

> **Date**: 2026-04-24
> **Status**: v0.1 Claude's draft, pending external lit survey to confirm novelty. Research agent queried 2024-2026 protein-MD literature; updates will append as §7.
> **Purpose**: Answer the concrete question "how do I turn my MetaD output into ML training data?" with specific input/label/loss formulations rather than vague method names.

---

## 0. The framing that matters

MetaD produces four artifact types:
1. **Reweighted frame set** — (structure_i, weight_i, block_id_i) tuples
2. **FES on grid** — F(s, z) with block CI
3. **State masks** — which (s, z) bin belongs to O / PC / C / off-path
4. **Per-frame chemistry descriptors** — K82-PLP distance, Schiff-base tilt, etc.

"Turn FEL into training data" = decide which of these becomes **input**, which becomes **label**, which becomes **sample weight**. The 9 patterns below enumerate the defensible combinations.

---

## 1. Nine conversion patterns enumerated

### Pattern 1 — Frame-level state classifier (supervised)

| Slot | Content |
|---|---|
| Input | per-frame structure (backbone rigids, or active-site heavy atoms) |
| Label | discrete state ∈ {O, PC, C, off-path, reactive-ready} — from FES mask |
| Sample weight | MetaD reweight factor |
| Loss | weighted cross-entropy |
| Model | GNN on active-site atoms, or PointNet |
| Data needed | WT MetaD only (1 system) |
| 10-wk feasibility | ✅ high |
| Novelty bet | labels come from path-CV + FES, not naive RMSD clustering. Chemistry-grounded state definition. |

### Pattern 2 — Sequence → FES map regression

| Slot | Content |
|---|---|
| Input | sequence (one-hot or ESM2 embedding) |
| Label | 2D F(s, z) grid, block-averaged |
| Loss | MSE, weighted by inverse block-CI |
| Model | sequence transformer → flattened FES vector |
| Data needed | many variant FES (≥ 10 ideally, absolute minimum 5) |
| 10-wk feasibility | ❌ dead for 10 weeks — need too many variants |
| Novelty | high but depends on data we don't have |

### Pattern 3 — Mutation → per-state ΔΔG

| Slot | Content |
|---|---|
| Input | (WT sequence or structure, mutation specification) |
| Label | ΔG_state(mutant) − ΔG_state(WT), one scalar per state |
| Loss | MSE per state, summed |
| Model | small MLP or structure-aware delta-predictor |
| Data needed | ≥ 5 variant FES for training, 2 for test |
| 10-wk feasibility | ❌ same data constraint as Pattern 2 |
| Usefulness as **evaluation target** (zero-shot) | ✅ you can SCORE other models on this task without training your own |

### Pattern 4 — Rare-state contrastive / hard-example mining

| Slot | Content |
|---|---|
| Input | pairs (dominant-basin frame, rare-state frame) |
| Label | "which is rare" OR continuous rarity = −log(reweight_factor) |
| Loss | triplet / contrastive |
| Model | any structure encoder |
| Use | pretrain a representation that doesn't collapse rare states |
| Data needed | WT MetaD only |
| 10-wk feasibility | ✅ medium |
| Novelty bet | MetaD-derived hard-example pool for enzyme states — looks novel, confirm with lit |

### Pattern 5 — Descriptor → catalytic-readiness probability ⭐

| Slot | Content |
|---|---|
| Input | per-frame chemistry descriptors (5–8 features: K82-PLP dist, Dunathan angle, tunnel gate, etc.) |
| Label | binary or continuous "catalytic-ready" — derived from FES state mask + reaction-geometry threshold |
| Validation label | Yu's MMPBSA ranking on 30 variants |
| Loss | BCE or MSE |
| Model | gradient-boosted trees or 2-layer MLP |
| Data needed | WT MetaD + Yu's MMPBSA |
| 10-wk feasibility | ✅ highest — smallest data requirement, fastest training |
| **This is v2.0 memo's Layer 2 F0 composite scorer** |

### Pattern 6 — MetaD-reward RL for sequence generation ❌

Killed: this IS GRPO, already owned by Raswanth.

### Pattern 7 — FES-target Boltzmann Generator ❌

Killed by Nov-2024 novelty audit (Thermodynamic Interpolation JCTC 2024, Energy-Based CG Flow JCTC 2025 already occupy this space).

### Pattern 8 — MetaD reweight weights as sample importance (technique, not a standalone pattern)

Plug into Patterns 1, 4, 5 as a weighting scheme. No independent novelty.

### Pattern 9 — State-contrastive representation learning ⭐

| Slot | Content |
|---|---|
| Input | active-site structure embedding from pretrained GNN / ESM |
| Label | state tag, but used pairwise: "same state" vs "different state" |
| Loss | SimCLR-style contrastive or triplet |
| Model | small projection head on top of frozen encoder |
| Data needed | WT MetaD only, state labels |
| 10-wk feasibility | ✅ medium |
| Output | a **reusable embedding** where catalytic-ready states cluster tightly |
| Novelty bet | state-contrastive enzyme representation learning with FES-derived labels — needs lit check against VAMPnets/MEMnets |

---

## 2. Recommended stack for TrpB (concrete)

Given (a) WT MetaD is the only guaranteed data by week 6, (b) Yu's MMPBSA gives ~30 labels, (c) no guaranteed variant FES in 10 weeks:

### Primary — Pattern 5 (Readiness scorer)

**Because**: smallest data requirement, directly answers Raswanth's F0 gap, validated by Yu's ranking. Survives even if only WT FES ships.

Concrete spec:

```
Input features (per candidate structure, 5 ns short MD average):
  f1 = d(K82:NZ — PLS:C4')            # Schiff-base proximity, Å
  f2 = angle(K82:NZ-Cα-H, PLS ring)  # Dunathan-like, degrees
  f3 = d(E104:OE — PLS:O3)            # phenol H-bond
  f4 = d(Y301:OH — PLS:N1)            # pyridine N orientation
  f5 = d(indole tunnel gate residues) # substrate access
  f6 = <s>_frame                      # mean PATHMSD progress
  f7 = <z>_frame                      # mean off-path deviation
  f8 = state_entropy                  # Shannon H over state occupancy

Label (per candidate):
  L = f(MMPBSA rank bin)              # Yu gives us; binarize top-k vs bottom-k

Model:
  gradient-boosted trees, shallow (depth≤4), n_estimators ≤ 200
  OR 2-layer MLP w/ dropout, same feature input

Loss:
  BCE (binary top-k) or pairwise ranking (Lambda-rank style)

Training:
  stratified 5-fold CV on Yu's 30 candidates
  report Spearman ρ vs MMPBSA + AUROC on held-out fold

Shipping artifact:
  `trpb_function_evaluator/f0/readiness_model.pkl`
  + predict(pdb) API
  + ablation card showing which descriptor contributes most
```

### Secondary — Pattern 1 (State classifier) **as enabler of Pattern 5**

Pattern 5 needs state-occupancy feature `f8`. That feature comes from running a state classifier on candidate frames. So Pattern 1 is an **inside-Pattern-5 component**, not a separate product. Train on WT reweighted frames with FES-mask labels. Minimal scope.

### Stretch — Pattern 9 (State-contrastive pretraining) for Pattern 1

If Pattern 1 works well with ~1000 WT frames, stop. If Pattern 1 is underperforming (AUC < 0.75), pretrain the structure encoder with state-contrastive loss on a larger WT frame pool before training the classifier. This is the only "deep" ML piece in the stack.

### Zero-shot evaluation lane — Pattern 3 (ΔΔG per state) as BENCHMARK TASK, not trained

If any external group (PLaTITO, STAR-MD, BioEmu) wants to claim their model handles enzyme variants, you challenge them: "here's my 1 WT + 2 variant FES — predict ΔΔG(O→C) for each variant, scored against my reweighted ground truth." This costs you nothing extra and makes your cartridge a challenge benchmark, not just an internal tool.

---

## 3. What this stack actually **is** in ML terms

| Component | ML nature |
|---|---|
| F0 scripts (D/L docking gap, catalytic-lysine, geometry) | rule-based, not ML |
| State classifier (Pattern 1) | small supervised GNN |
| Catalytic-readiness scorer (Pattern 5) | small supervised GBM/MLP |
| State-contrastive encoder (Pattern 9, if needed) | self-supervised pretraining |
| Zero-shot ΔΔG task (Pattern 3) | **evaluation benchmark**, not trained by you |

The "ML layer" in v2.0 Layer 2 = Pattern 5 (lead) + Pattern 1 (inside) + Pattern 9 (stretch).

**All three models are small** (≪ 10M params, trainable on a laptop in hours). This is intentional: ByteDance has the 8×H100 lane; you have the "models that are small, specific, and validated against wet-lab proxy" lane.

---

## 4. How this deflects ByteDance

| Threat | Deflection |
|---|---|
| STAR-MD does long-horizon SE(3) diffusion | Your Pattern 5 is a 5-feature GBM. Apples vs oranges. |
| STAR-MD has more compute | Pattern 5 needs 30 labels + 5 features. Compute doesn't help them here. |
| STAR-MD claims universal dynamics | You claim specific catalytic-readiness. Anyone can test STAR-MD against your scorer; STAR-MD can't test against you without your data. |
| Large pretrained models have richer representations | Yours is grounded in wet-lab MMPBSA labels Yu painstakingly generated. Representation richness without grounding is unfalsifiable. |

**Your ML layer is deliberately small because the value is in the labels + the path CV infrastructure, not the model complexity.**

---

## 5. Input prep: what you actually need ready by week 4

1. **WT reweighted frame pool** (≥1000 frames post-block-analysis, each with weight + block-id + state label + descriptor vector)
2. **Per-candidate 5 ns short MD** for each of Yu's 30 MMPBSA candidates
3. **Descriptor computation pipeline** (`mdtraj` or equivalent, automated)
4. **Yu's MMPBSA rank table** (one CSV)
5. **State-mask json** derived from WT FES

Week-4 sanity check: can you produce the 8-feature vector for the WT trajectory in under 10 min of Python? If yes, you're ready to train Pattern 5.

---

## 6. Top 3 failure modes specific to this ML conversion

1. **Label noise dominates**: 30 MMPBSA labels with unknown experimental error may give ρ no better than random. Mitigation: test on JACS 2019 / Duran 2024 literature-known high- vs low-activity variants first as a sanity baseline.

2. **Feature collinearity**: f1-f8 might all correlate with "closed basin" and collapse to one effective dimension. Mitigation: run PCA; if > 90% variance in 1 PC, you need to add orthogonal features or admit this is a 1D problem.

3. **Short MD too short**: 5 ns may not equilibrate descriptors. Mitigation: check descriptor autocorrelation time on WT 500 ns reference; if > 5 ns, extend candidate MD to 20 ns or use MetaD-rescued states as proxy.

---

## 7. External novelty audit (completed 2026-04-24)

Research agent surveyed 2024-2026 protein-MD / enzyme-ML literature. Key findings below — full citations in §7.4.

### 7.1 What's CONFIRMED taken

| Recipe | Example | Status for us |
|---|---|---|
| Reweighted-frame ensemble as equilibrium samples | **BioEmu** (Science 2026, [doi:10.1126/science.adv9817]) uses 200 ms MD **MSM-reweighted** before training diffusion prior | Pattern canonical; we can **reuse it**, not claim it |
| MLIP training on MetaD-explored high-energy configs | [doi:10.1039/D5DD00261C], Yang 2024 [doi:10.1038/s41524-024-01481-6], Perego-Parrinello AdaptiveMLP | Reactive-chemistry / materials; **not our lane** |
| Iterative biased-data CV refinement | SPIB-BEMetaD [biorxiv 2023.07.24.550401], OPES-NN/ML-CV [arXiv:2410.18019] | Already dead for us (covered in earlier NN-VES audit) |

### 7.2 What's UNCLAIMED for enzymes — **confirmed whitespace**

Research agent's direct quote:
> *"I found **no 2024-2026 paper** that trains a downstream protein/variant-level ML model on MetaD-reweighted FES or PathCV frames specifically for PLP enzymes or allosteric catalytic states. Enzyme-ML work uses sequence/structure embeddings (ThermoMPNN, PLACER) or MLIP for QM. Pattern #2 for enzymes is unclaimed."*

Protein-specific check of the big models:
- **BioEmu**: uses MSM-reweighting of MD training data (yes)
- **MDGen** ([arXiv:2409.17808]): plain MD on tetrapeptides, **no MetaD**
- **STAR-MD** ([arXiv:2602.02128]): plain MD rollouts, **no MetaD** (unverified but consistent with paper text)
- **AlphaFlow** ([arXiv:2402.04845]): plain MD from ATLAS, **no MetaD**
- **Boltzmann Generators** (Noé line, [arXiv:2401.04246]): reweighting is core theory but applied to own flow samples, **MetaD-sourced frames rare**
- **PLaTITO** ([arXiv:2506.xxxxx]): unverified; closest hit LD-FPG [arXiv:2506.17064] trained on plain MD

### 7.3 IMPORTANT CORRECTION to Claude's §2

Research agent's Option A is **DIFFERENT from my Pattern 5**:

| | Claude's Pattern 5 (my draft) | Research's Option A |
|---|---|---|
| Input | per-frame chemistry descriptors | **FES-level scalar features** (ΔF_O→C, barrier height, z-width at TS, COMM-closure lifetime) |
| Label | MMPBSA rank | Experimental/MMPBSA activity scalar |
| Data required | 1 WT FES + 30 MMPBSA | **3-4 variant FES** + activities |
| Novelty | "MMPBSA with extra steps" (reviewer bait) | **"First PLP-enzyme FES→activity map"** — confirmed whitespace |

Research agent's verdict:
> *"Best novelty/feasibility: Option A — FES-descriptor → activity regression is genuinely whitespace for PLP/allosteric enzymes and fits 10-wk + 30-label budget [if 3-4 variant FES exist]."*
> *"Option C [my per-frame Pattern 5] is safest but reviewers will read it as 'MMPBSA with extra steps.'"*

**So my Pattern 5 is still fine as fallback, but the real novelty is FES-level features.** The difference matters: Pattern 5 pitches a small readiness predictor; Option A pitches the first FES→activity map for PLP.

### 7.4 Updated recommended stack (replaces §2)

**Upgrade path, conditional on variant FES availability:**

```
Fallback (WT-only)     ──→  Mid-tier (1 WT + ≥1 variant)  ──→  Full (WT + ≥3 variants)
Pattern 5 (per-frame)      Hybrid                              Option A (FES-scalar)
AUROC vs MMPBSA            ρ vs MMPBSA + 1 zero-shot variant   FES→activity map
"readiness scorer"          test (Pattern 3 benchmark)          PLP-enzyme first
```

Concrete features for Option A (replaces the 8-feature list in §2):

```
FES-level scalar descriptors (computed per system):
  g1 = ΔF(O → C)              global basin drop, kJ/mol
  g2 = ΔF‡ (PC → C)           barrier height, kJ/mol
  g3 = z-width at TS          off-path slack at barrier, nm²
  g4 = P(C | reweighted)      closed-state population
  g5 = MFPT_proxy             1/rate from FES shape (Eyring-like)
  g6 = p_state_entropy        H over O/PC/C occupancy
  g7 = state_conditional_catalytic_geometry_mean  per-state chemistry expectation (uses Pattern 5 as sub-module)

Target (per system):
  y = activity_proxy (MMPBSA | experimental k_cat if any | Yu ranking)

Model:
  GBM or small MLP (≪ 20 params given likely n=3-5 systems)
  
Training:
  leave-one-out CV given small n
  report per-system residual, not AUROC

Critical caveat:
  n=3-5 makes it closer to "curve fit" than ML. 
  Frame it as "first FES→activity regression for PLP", not "new ML method".
  The point is the MAP, not the model sophistication.
```

### 7.5 Three published pitfalls to dodge (from research)

1. **Reweighting variance blow-up / ESS collapse** — rare-state w_i dominated by few frames. Mitigate: block-analysis ESS check [doi:10.1021/acs.jctc.9b00867]
2. **CV-dependence of FES features** — g1, g2 depend on PathMSD s parameterization; swap CV → different label. Check CV-invariance before using FES scalars as ground truth.
3. **Unconverged biased trajectory treated as equilibrium** — BioEmu-style reweighting assumes FES filled. If our WT FES is truncated at 50ns and not converged, Option A labels are silently wrong. **This is the FP-030 / FP-034 risk showing up in ML form.**

### 7.6 Citations (verified by research agent 2026-04-24)

Core references:
- BioEmu: [doi:10.1126/science.adv9817]
- MDGen: [arXiv:2409.17808]
- STAR-MD: [arXiv:2602.02128]
- AlphaFlow: [arXiv:2402.04845]
- Boltzmann Generators (Noé): [arXiv:2401.04246]
- Active-learning MetaD MLIP: [doi:10.1039/D5DD00261C]
- Yang MLP catalysis: [doi:10.1038/s41524-024-01481-6]
- MetaD reweighting variance: [doi:10.1021/acs.jctc.9b00867]
- Enhanced Sampling + ML Chem Rev 2026: [doi:10.1021/acs.chemrev.5c00700]
- Iterated biased-data CV: [doi:10.1021/acs.jpcb.5c02164]
- SPIB-BEMetaD: [biorxiv:2023.07.24.550401]
- Enzyme-design review RSC: [doi:10.1039/D4CS00196F]
- LD-FPG: [arXiv:2506.17064]
- BioEmu accelerated sampling critique: [biorxiv:2026.01.07.698041]
- CV discovery hype vs reality: [PMC9437778]
- PLACER PNAS: [doi:10.1073/pnas.2427161122]
- ThermoMPNN PNAS: [doi:10.1073/pnas.2314853121]

**Novelty claim rigor note**: research agent flagged PLaTITO arXiv ID as unverified. If you cite PLaTITO anywhere, re-check arXiv number before PI meeting.

---

## 8. Open questions for Zhenpeng to confirm

1. Can Yu share the MMPBSA rank table? (30 candidates with scalar binding energies)
2. Is 5 ns short MD per candidate a reasonable compute budget? (30 × 5 ns ≈ 150 ns of short MD — needs ~a day on one A100, tractable)
3. Does Raswanth want the readiness scorer as a drop-in for his F0 reward, or as a separate post-hoc filter?
4. Should Pattern 1 state classifier use backbone rigids (STAR-MD style) or all-atom with PLP (more info but more to model)?

---

## Appendix — Relationship to v2.0 Convergence Memo

This document expands v2.0 §11 "ML Layer 2" from a single paragraph into a concrete design. If Zhenpeng approves, fold this into the evaluator package as `trpb_function_evaluator/f0/readiness_model_design.md`.

The FP-034 sequence-aligned path fix is a **prerequisite**, not a component: all frames must use consistent atom-map before being projected onto PATHMSD.
