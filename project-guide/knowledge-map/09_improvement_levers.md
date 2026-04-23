# Chapter 09 — Independent Judgment: Where the TrpB Project Can Be Improved

**Purpose**: This is the chapter that answers the user's original ask — "have independent aesthetic to judge the improvement plans." It enumerates concrete improvement levers across the whole project stack, ranked by (a) expected impact and (b) what you could actually own as a SURF student.

**Source discipline**: Every lever below is grounded in a specific method claim made in Chapters 01–08. If a claim here is not backed by a chapter citation, flag it explicitly.

---

## 9.1 How to read this chapter

Each lever entry has:
- **Status quo**: what the lab does now
- **Proposed change**: the improvement
- **Evidence base**: citation to a specific chapter + external paper
- **Expected impact**: quantitative if possible
- **Implementation cost**: days/weeks
- **Your ownership potential**: 1 (not yours to own) to 5 (perfect SURF scope)
- **Risk**: what could go wrong

---

## 9.2 Enzyme-design-pipeline levers

### Lever D1 — Upgrade MPNN → LigandMPNN
- **Status quo**: Raswanth runs the RFD3 → MPNN → RF3 pipeline. Uncertain whether current MPNN is vanilla or ligand-aware.
- **Proposed change**: Confirm with Raswanth; if vanilla, upgrade to LigandMPNN (Dauparas 2025 *Nat Methods* 22:717).
- **Evidence base**: Ch 04 §4; Ch 08 §8.8. At ligand-contact positions, LigandMPNN's NSR is ~63% vs MPNN's ~50%. For TrpB-PLP, 15-20 pocket residues get 13% better sequence-recovery signal.
- **Expected impact**: Higher fraction of designed sequences retain catalytic geometry. Reduces downstream MD filter attrition.
- **Cost**: 2-3 days (drop-in replacement + re-run on 12 theozymes).
- **Ownership potential**: 1 — this is Raswanth's call. You surface it as a question in the meeting.
- **Risk**: None significant; LigandMPNN is well-validated.

### Lever D2 — Chemistry-aware F0 reward beyond PLACER
- **Status quo**: F0 = PLACER geometric score. Feeds GRPO. Does not explicitly check D/L-selectivity-relevant geometry.
- **Proposed change**: Add a **reprotonation-face geometry term** to F0 — score how well the putative acid/base residue aligns with the si face of the Cα carbanion in the quinonoid state.
- **Evidence base**: Ch 03 §3.4 (quinonoid chirality loss); Ch 04 §7 (GRPO scope). Raswanth's 4/4 Slack concern about planar-intermediate chirality is exactly this.
- **Expected impact**: Prevents GRPO from converging on high-PLACER-score sequences that bind D-Ser but still produce L-Trp.
- **Cost**: 1 week to define + implement + validate on known substrates.
- **Ownership potential**: 3 — defensible contribution if Raswanth welcomes collaboration.
- **Risk**: Reward design can hack itself. Validate on both L- and D-producing known variants before deploying.

### Lever D3 — MFBO acquisition function tuning
- **Status quo**: Raswanth pivoted 4/4 to MFBO for F1/F2 (MD/MMPBSA). Default acquisition likely Expected Improvement.
- **Proposed change**: Switch to Knowledge Gradient or Multi-Fidelity Expected Improvement (Wu 2020) for better expensive-fidelity allocation.
- **Evidence base**: Ch 04 §7; Lin 2025 *ACS Cent Sci* benchmarks MFBO for drug discovery.
- **Expected impact**: 20-30% reduction in total MD budget for same final-ranking accuracy (literature benchmark).
- **Cost**: 1 week if using BoTorch/Ax.
- **Ownership potential**: 1 — Raswanth's domain. Mention as informed question.
- **Risk**: Requires careful fidelity-cost calibration.

---

## 9.3 Metadynamics / sampling levers

### Lever M1 — Evaluate OPES vs WTMetaD for convergence
- **Status quo**: WTMetaD with PATHMSD (what you ran).
- **Proposed change**: Run the same O→C system with OPES (Invernizzi 2020) for 50 ns; compare convergence rate and final FES shape to WTMetaD.
- **Evidence base**: Ch 02; OPES documentation; Invernizzi-Parrinello *J Phys Chem Lett* 2020.
- **Expected impact**: OPES often converges 2x faster; cleaner bias-factor interpretation. If it holds on TrpB, 50 ns becomes 25 ns effective — big for the 10-walker phase.
- **Cost**: 1 week (PLUMED input is minor rewrite).
- **Ownership potential**: 4 — perfect SURF scope, self-contained, publishable as method comparison.
- **Risk**: Comparison on single system is weak benchmark; need at least 3 systems for generality claims.

### Lever M2 — ML-learned CV (DeepTDA) for follow-up variants
- **Status quo**: Hand-designed PATHMSD over 15 reference frames.
- **Proposed change**: For 12 new theozymes where O→C path may differ structurally, use DeepTDA (Bonati 2021) to discover system-specific CV.
- **Evidence base**: Ch 02; Luigi Bonati group publications.
- **Expected impact**: Avoids false transferability assumption; catches cases where mutants have different pathways.
- **Cost**: 2 weeks per variant (including validation).
- **Ownership potential**: 4 — directly useful for the design campaign.
- **Risk**: ML CVs can be uninterpretable; always cross-check against PATHMSD reference.

### Lever M3 — Rate-constant recovery via weighted ensemble
- **Status quo**: WTMetaD gives FES but not rates directly. Reweighting to rates is indirect and noisy.
- **Proposed change**: Run a parallel WESTPA weighted-ensemble simulation to directly measure k_O→C forward rate for native TrpB vs 2-3 key variants.
- **Evidence base**: Ch 02 §7; Zwier-Chong WESTPA papers.
- **Expected impact**: Rigorous rate measurements become the "chemistry-aware kinetic metric" in the benchmark pack.
- **Cost**: 3-4 weeks (WESTPA learning curve).
- **Ownership potential**: 3 — high-value but long tail.
- **Risk**: WESTPA setup is fiddly; progress coordinate choice affects results.

---

## 9.4 Validation / benchmark levers (your proposed owned contribution)

### Lever V1 — TrpB MetaD Benchmark Pack (the primary deliverable)
- **Status quo**: No single public resource for ligand-bound enzyme dynamics benchmark. STAR-MD, BioEmu, MDGen train and evaluate on ATLAS (apo).
- **Proposed change**: Package your MetaD ground truth + chemistry-aware metrics suite into a versioned, open-source benchmark:
  - MetaD-reweighted ensemble on TrpB-PLP-AEX (native)
  - Reference distributions for: Dunathan angle, lid-closure, PLP SASA, water occupancy, s(R)/z(R) FES
  - Scoring script (Python, minimal deps)
  - YAML config for frame/atom indices
  - Pre-registered failure thresholds
- **Evidence base**: Ch 07 (the whole chapter); Ch 03 for chemistry grounding.
- **Expected impact**: Gives the dynamics-ML line a concrete test target; fills a literature gap; cite-able deliverable.
- **Cost**: 4-6 weeks (the bulk of summer SURF).
- **Ownership potential**: 5 — this is exactly the "chemistry-to-ML bridge" role.
- **Risk**: Single-system benchmark may face criticism for generality. Mitigate by including 4HPX cross-species as secondary target.

### Lever V2 — Quantify STAR-MD failure on TrpB-PLP explicitly
- **Status quo**: STAR-MD's Conclusion acknowledges ligand-dynamics is future work, but no one has quantified the gap.
- **Proposed change**: Run STAR-MD (if Amin has access) on TrpB-apo and TrpB-PLP-AEX frames; measure JSD degradation with ligand present. Publish as single figure + 1-page note.
- **Evidence base**: Ch 05 §9; Ch 07 §3; STAR-MD Table 1.
- **Expected impact**: Concrete number for the gap. Strengthens case for ligand-aware dynamics ML.
- **Cost**: 2 weeks (including STAR-MD setup).
- **Ownership potential**: 4 — ideal SURF scope, self-contained, publishable.
- **Risk**: STAR-MD inference code may not be easily accessible outside the ByteDance team.

### Lever V3 — Markovianity diagnostic on TrpB O→C
- **Status quo**: Nobody has measured whether O→C dynamics on the path coordinate are Markovian or not.
- **Proposed change**: From your unbiased 500 ns MD, compute the memory kernel K(t) on s(R) via the Volterra iteration or likelihood method (Vroylandt 2022). Report the non-Markovianity timescale.
- **Evidence base**: Ch 06 §3; Berezhkovskii-Makarov 2018 diagnostic.
- **Expected impact**: Gives Amin a data point for his 4/11 Mori-Zwanzig thinking. If memory decays fast (<50 ps), ordinary Langevin is fine. If slow (>1 ns), non-Markovian modeling is required.
- **Cost**: 1-2 weeks (use existing GLE_AnalysisEM or MEMnets packages).
- **Ownership potential**: 5 — directly plugs into Amin's current curiosity, self-contained, genuine new data point.
- **Risk**: 500 ns may be too short to converge kernel; explicit fallback is "upper bound on memory timescale".

---

## 9.5 Force-field / parameterization levers

### Lever F1 — OpenFF 2.0 for PLP
- **Status quo**: GAFF + RESP for PLP-AEX.
- **Proposed change**: Re-parameterize PLP-AEX with OpenFF Sage 2.0; compare Dunathan angle distributions over 50 ns MD.
- **Evidence base**: Ch 01 §1.2; Ch 03 §3.7.
- **Expected impact**: If Dunathan distribution differs >5%, the current GAFF-based metric baseline has systematic error. Changes quantitative interpretation of benchmark.
- **Cost**: 1 week (OpenFF has tutorials).
- **Ownership potential**: 3 — small, useful, publishable as a "parameterization uncertainty" note.
- **Risk**: Small-scope change may not justify switching the replication pipeline.

### Lever F2 — Explicit polarization (AMOEBA or Drude) for active-site
- **Status quo**: Fixed-charge ff14SB + GAFF.
- **Proposed change**: QM/MM-accurate region around PLP via AMOEBA (Ren-Ponder 2002) or Drude particle (Lemkul 2017) polarization.
- **Evidence base**: Ch 01 §1.10 (honest limitations).
- **Expected impact**: Better Schiff base geometry; marginal improvement on conformational timescale.
- **Cost**: 2-3 months (steep learning curve).
- **Ownership potential**: 1 — outside SURF scope.
- **Risk**: Overkill for conformational-change study.

---

## 9.6 Methodological integration levers

### Lever I1 — Chemistry-aware terms in GRPO reward (careful)
- **Status quo**: F0 PLACER → GRPO. F1/F2 MD/MMPBSA → MFBO (off-gradient).
- **Proposed change**: Add chemistry-aware geometric terms (Dunathan angle, reprotonation face) to F0. Keep MD/MMPBSA firmly off-gradient as Raswanth does.
- **Evidence base**: Ch 04 §7 (why MFBO vs GRPO); Ch 03 §3.4 (chemistry).
- **Expected impact**: Reward shape now respects chirality logic; fewer L-producing "false positive" D-Ser binders.
- **Cost**: 2 weeks collaborative work with Raswanth.
- **Ownership potential**: 3 — good joint project.
- **Risk**: Reward hacking. Need held-out validation set with known L vs D producers.

### Lever I2 — Coupled MetaD + GenSLM screening loop
- **Status quo**: Design stack produces 5k sequences; downstream MD/MMPBSA filters. No feedback from MetaD to sequence generation.
- **Proposed change**: Use MetaD-derived chemistry-aware score to re-weight sequence generation (active learning loop).
- **Evidence base**: Ch 04 §7 (MFBO precedents); Ch 07 (metrics).
- **Expected impact**: Faster convergence to catalytically competent variants.
- **Cost**: Long; 2+ months infrastructure.
- **Ownership potential**: 2 — infrastructure-heavy.
- **Risk**: Premature integration; need to validate individual pieces first.

---

## 9.7 ML-model-architecture levers (for the dynamics line)

**Important framing**: These levers are for the Anandkumar-line (Amin + collaborators). You are unlikely to own any, but you should recognize them so you can contribute informed questions.

### Lever A1 — Ligand-aware extension of STAR-MD
- **Status quo**: STAR-MD ingests backbone + sequence; no small-molecule tokens.
- **Proposed change**: Add ligand atom track (like RFAA does for structure prediction) to the SE(3) diffusion.
- **Evidence base**: Ch 05 §2 (STAR-MD architecture limitations).
- **Expected impact**: Principled fix for the TrpB-PLP gap. Probably a year-scale effort with retraining.
- **Ownership potential**: 1 — this is a senior ML researcher's project.

### Lever A2 — Memory-aware neural operator (MemNO-style) for protein dynamics
- **Status quo**: No published protein-dynamics application of MemNO / memory-augmented FNO yet.
- **Proposed change**: Port MemNO (Buitrago Ruiz et al. 2024, arXiv:2409.02313) to protein configurations.
- **Evidence base**: Ch 06 §4-5.
- **Expected impact**: Explicit memory kernel in the generative model. If it works, publishable as first demonstration on biomolecular system.
- **Ownership potential**: 1 — PhD-level ML.

### Lever A3 — MSM / VAMP-2 as evaluation baseline
- **Status quo**: STAR-MD evaluates vs MD ensemble directly.
- **Proposed change**: Compare STAR-MD-generated trajectories to a reference MSM built from the same MD ensemble. Report ITS (implied timescales) matching.
- **Evidence base**: Ch 05 §7; Ch 07 §2.
- **Expected impact**: Stronger kinetic claim; reveals whether STAR-MD just samples statics or actually preserves slow modes.
- **Ownership potential**: 3 — you could run the MSM side if Amin has STAR-MD inference access.

---

## 9.8 Data-pipeline / engineering levers

### Lever E1 — Make MetaD pipeline fully reproducible (containerized)
- **Status quo**: Pipeline runs on Longleaf with conda envs + source-built PLUMED. Reproducibility is documented but container-less.
- **Proposed change**: Build a Singularity/Docker container with exact MD + PLUMED versions. Publish with benchmark.
- **Evidence base**: Ch 01 §1.7 (software ecosystem); your own FP-020 incident.
- **Expected impact**: Benchmark pack becomes usable by anyone without matching Longleaf setup.
- **Cost**: 1-2 weeks.
- **Ownership potential**: 5 — necessary complement to Lever V1.
- **Risk**: Small, well-trod path.

### Lever E2 — Shared analysis pipeline with Yu's MD infrastructure
- **Status quo**: Your MetaD + Yu's conventional MD have separate analysis stacks.
- **Proposed change**: Unify analysis on MDAnalysis + PLUMED driver post-hoc; Yu's MD outputs become comparable to MetaD ensemble automatically.
- **Evidence base**: Ch 01 §1.9.
- **Expected impact**: Yu's 100+ simulations become available as training/validation data for the benchmark pack.
- **Cost**: 2-3 weeks collaborative work with Yu.
- **Ownership potential**: 4 — scoring points with Yu's line too.

---

## 9.9 Prioritization — top 5 levers by SURF-relevance

Ranked by: (ownership potential × expected impact / cost):

1. **Lever V1** (TrpB MetaD Benchmark Pack) — the anchor deliverable.
2. **Lever V3** (Markovianity diagnostic) — directly answers Amin's 4/11 curiosity.
3. **Lever V2** (Quantify STAR-MD failure on TrpB-PLP) — fills a specific literature gap.
4. **Lever M1** (OPES vs WTMetaD benchmark) — methods-paper potential.
5. **Lever E1** (Containerized reproducibility) — necessary for V1 to have impact.

**These five, bundled, can be the summer's deliverable.** V1 is the shape, V2–V3 are concrete uses of V1, M1 is the methods-adjacent side bet, E1 is the packaging.

---

## 9.10 Anti-levers (things NOT to propose)

**Do not pitch** these in the Amin meeting, even though they might seem sensible:

- ❌ "Let me build a better STAR-MD architecture" — you cannot. Too big, wrong background.
- ❌ "Let me implement MemNO for proteins" — ML-PhD territory.
- ❌ "Let me train a new protein dynamics model from scratch" — same.
- ❌ "Let me switch the whole lab to OpenMM for MetaD" — infrastructure disruption, low value.
- ❌ "Let me do QM/MM on the α-abstraction step" — out of scope for SURF timeline.
- ❌ "Let me redesign the GRPO reward from scratch" — Raswanth's territory; offer collaboration only.

These are real levers but wrong scope.

---

## 9.11 What if the lab's direction changes mid-summer?

Contingency table:

| Scenario | Your pivot |
|----------|------------|
| Amin wants you on model architecture | Decline politely, offer V3 (Markovianity diagnostic) as informed adjacent help |
| Anima wants a demo on TrpB specifically for a grant | Accelerate V1 to MVP in 4 weeks |
| Raswanth asks for help on reward design | Offer Lever D2 (chemistry-aware F0 term) as co-owned |
| Yu asks for help on MD analysis | Offer Lever E2 (shared pipeline) |
| STAR-MD group wants collaboration | Offer V2 (failure quantification) as contribution |

**Default rule**: your primary is V1 (benchmark pack); everything else is secondary and should not compete with V1 unless explicitly instructed.

---

## 9.12 Self-assessment — where this chapter could be wrong

- **Ranking biased toward metaD side**: You have 6 weeks of MetaD depth. Your confident levers skew there.
- **Ownership estimates optimistic**: SURF is 10 weeks. V1 alone may fill it. V2+V3 at a pinch.
- **Impact numbers are literature extrapolations**: "20-30% reduction in budget" for MFBO is from other fields; actual number on TrpB unknown.
- **External dependencies underweighted**: STAR-MD inference access (V2), Raswanth's willingness (D2/I1), Yu's collaboration bandwidth (E2) all gate execution.

Acknowledge these in the meeting. Honest uncertainty is stronger than overclaimed confidence.

---

**Next**: Read the master index (`TECHNICAL_KNOWLEDGE_MAP.md`) for reading-order guidance.
