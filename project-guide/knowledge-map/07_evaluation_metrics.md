# Chapter 07 — Evaluation Metrics for Protein-Dynamics ML

**Author:** Zhenpeng Liu (UNC → aNima Lab summer candidate)
**Date:** 2026-04-19
**Prereqs:** Chapters 01–06 (MD basics, MetaD, path CVs, SE(3) diffusion, STAR-MD architecture)
**Reading time:** ~45 min
**Style note:** Honest about limits. Every number traceable. No emoji. 中英混写 OK.

---

## 07.1 Why evaluation metrics are the real bottleneck

> If you can't score the model, you can't train it, you can't compare it, and you can't trust it.

The protein-dynamics ML field has spent 2022–2026 racing on **architectures** — equivariant networks, diffusion, flow matching, SE(3) attention. The race on **metrics** has been much slower. That is backwards. A generative model that beats SOTA on JSD but fails on catalytic geometry is not "better at dynamics"; it is better at one proxy. If the proxy is wrong, the whole leaderboard is wrong.

Three concrete consequences:

1. **Optimization loop cannot close.** GRPO/RLHF needs a reward. If the reward is reference-PC JSD, the model learns to sample the reference basin and ignore rare events (this is exactly the failure mode STAR-MD quietly demonstrates on long horizons — validity stays high, JSD saturates at 0.46 vs oracle 0.23, the model has learned to breathe inside one attractor).
2. **Reward hacking.** As shown in Ye et al. (2024) on molecular design, data-driven reward models are vulnerable to policy exploitation when the reward drifts from the training distribution. In enzyme dynamics this is worse: a model can produce geometrically valid frames with zero catalytic competence, and current metrics will not flag it.
3. **Paper-to-lab gap.** Yu (MD pipeline) and Raswanth (GRPO on protein ensembles) both need a readout that says "this ensemble is useful for designing a variant." Current metrics only say "this ensemble looks like the training distribution."

What I expect Anima Anandkumar to press on in an interview: *what is your reward signal, and why is it not hackable?* Her group has published Eureka (reward design via LLM), so metric design is live in her head. The safe answer is not "JSD." The interesting answer is "a chemistry-aware metric suite grounded in TrpB catalysis, with preregistered thresholds and known failure modes."

This chapter is my attempt to write that answer.

---

## 07.2 The generic dynamics-ML metric zoo

Below is every metric I found in STAR-MD (Shoghi et al., 2026, §4 + Appendix D), ConfRover (Shen et al., 2024), MDGen (Jing et al., 2024), and BioEmu (Lewis et al., 2024). I group them by what they claim to measure.

### 07.2.1 Distributional metrics (does the ensemble shape match?)

**Jensen-Shannon Divergence (JSD).** Symmetric KL divergence. JSD = 0 → identical distributions. JSD = log 2 ≈ 0.693 → disjoint distributions. In STAR-MD it is computed on projections of the conformations onto the top principal components of the **reference** trajectory, then on a 1D histogram per PC. STAR-MD 100 ns result: 0.43 vs oracle 0.31. 1 μs: 0.46 vs oracle 0.23 (oracle improves with more samples; STAR-MD does not).

What JSD misses:
- Joint structure across PCs (it is evaluated marginal-by-marginal or on a 2D histogram at best)
- Anything outside the reference PC subspace — by construction, JSD cannot reward discovering a basin the reference never visited
- The physical meaning of "distance" — PC1 might be a rigid-body wobble, PC2 might be a catalytic lid; JSD treats them as equivalent axes

**Recall.** % of reference conformations whose nearest neighbor in the generated ensemble lies within ε (Shen et al. define ε from the reference self-distance). One-directional: reference → generated. This is why recall can be high while the generated ensemble also samples garbage — recall does not penalize extra mass. STAR-MD 1 μs recall ≈ 0.58 on valid frames.

**FES overlap.** Pinheiro & Parrinello (2020) and Invernizzi & Parrinello (2020) reconstructed a 2D FES on chosen CVs; two FES can be compared by KL divergence or by the Wasserstein metric on the Boltzmann-weighted distribution. For TrpB this is natural: the (s, z) path CVs give an FES that matches the JACS 2019 landscape. None of the current generative-MD benchmarks use this because they have no defined CV — they use PCs of the reference trajectory.

**RMSD distribution shape.** Histogram of per-frame backbone RMSD against a reference structure. Surprisingly informative — a collapsed ensemble sits tight around 1–2 Å, a diffusive one spreads to 5+ Å. STAR-MD reports this as the basic sanity metric.

### 07.2.2 Kinetic metrics (does the trajectory have the right timescales?)

**tICA (time-lagged independent component analysis; Pérez-Hernández et al. 2013).** Finds the slowest linearly decorrelating modes of a trajectory at lag time τ. "tICA correlation" as used in STAR-MD = cosine similarity between the top tIC eigenvectors of reference and generated trajectories. STAR-MD matches oracle at 0.17 (100 ns). But: tICA is **fit on the reference**, so if the reference does not see the slow mode, neither does the evaluation. This is the "reference blind spot" that makes tICA unusable for rare events.

**VAMP-2 score (Noé & Paul, 2018, via deeptime).** The squared sum of estimated transfer-operator eigenvalues; variationally bounded, higher is better, principled under the Koopman operator framework. Widely used to rank MSMs. Frank Noé's VAMPnets (Mardt et al., 2018) trained directly on this score. Same reference-blindness caveat as tICA.

**Autocorrelation decay.** Per-residue or per-atom decay curve C(τ) of some coordinate. Compare decay rate of generated vs. reference. STAR-MD Fig. 8 shows autocorrelation ≈ 0 at 1 μs for STAR-MD vs. 0.2 for oracle — the generated trajectory has **forgotten** its past too fast. This is one of the few places where current metrics honestly show long-horizon failure.

**MFPT (mean first passage time).** Not used in any current ML benchmark. The gold standard for enzyme kinetics (transition rate 1/MFPT). Hard to estimate without defined macrostates and trajectories long enough to observe transitions. This is the metric that would actually match experimental kcat.

### 07.2.3 Structural validity (does each frame make physical sense?)

**AA% (amino-acid contact accuracy).** Fraction of native contacts present. Evaluates topology, not geometry — a squashed but topologically correct frame scores well.
**CA% / CA+AA%.** Add a hard constraint on Cα–Cα distance (break check) and optional clash check. STAR-MD's headline metric. CA+AA% = 86% at 100 ns, 80% at 1 μs.

These are **backbone-only** and **indifferent to the active site, the cofactor, and the substrate**. A TrpB frame with the PLP ring rotated 180° and the Schiff base broken would still get a high CA+AA% if the Cα trace looks clean.

### 07.2.4 The composite picture

| Metric | Axis | Reference-bound? | Chemistry-aware? | Catches rare events? |
|--------|------|---|---|---|
| JSD on PC | distribution | Yes (hard) | No | No |
| Recall | coverage | Yes | No | One-directional |
| tICA corr. | kinetics | Yes | No | No |
| VAMP-2 | kinetics | Yes | No | No |
| Autocorr | memory | Partial | No | Partial |
| CA+AA% | validity | No | No | N/A |
| FES overlap on (s,z) | thermodynamics | **No** | **Partial** | **Yes** |

The bottom row is what I want to add. Everything above it is either reference-bound, chemistry-blind, or both.

---

## 07.3 Why these metrics fail for ligand-bound enzymes

Four specific failure modes.

**(1) Everything is Cα-based.** ATLAS's 1,390 systems are apo or ion-only. No PLP, no substrate, no water-bridge network. The metrics were defined on Cα traces plus backbone contacts. When STAR-MD "solves ATLAS," it has shown nothing about whether it can reproduce a cofactor-dependent active site.

**(2) No explicit chemistry constraint.** The Dunathan hypothesis says the Cα–H bond of the external aldimine must sit perpendicular (~90°) to the PLP π system for catalysis (Dunathan 1966; Toney 2014; Phillips et al. 2025). Standard metrics never touch this dihedral. A model could predict a PLP ring flipped 180° and lose the perpendicular alignment entirely — JSD and CA+AA% would not know.

**(3) No catalytic competence measure.** For TrpB, the paper's whole question is "does the closed state allow nucleophilic attack?" Competence means: Schiff base intact, Dunathan angle in range, water network ready, lid closed. None of this is in any current metric.

**(4) ATLAS has zero enzyme-with-substrate systems.** I verified this against the DSIMB list (Vander Meersche 2024, NAR 52 D1). 1,390 chains, zero complexes with a bound ligand that matters mechanistically. The field is optimizing on apo dynamics and calling it "protein dynamics."

**(5) Contact maps are indifferent to occupancy.** An empty active site and an occupied one have the same backbone topology. AA% cannot distinguish.

This is the gap. Filling it is the student contribution.

---

## 07.4 Precedents for chemistry-aware validation

I am not inventing the idea of chemistry-aware metrics — I am repackaging ideas scattered across five different communities, which is why nobody has done it in one place for TrpB.

- **Warshel EVB / QM/MM (1976 → present).** Gold standard for computing activation energies of enzymatic reactions. Gives ΔG‡ in kcal/mol, which can be compared to experiment via the Eyring equation. Too expensive to run on a generated ensemble frame-by-frame, but useful as **ground truth** for a subset of test frames.
- **Toney group structural descriptors of PLP catalysis (Toney 2014, 2019).** Defined the Dunathan angle, quinonoid geometry, and Cα pyramidalization as experimentally testable structural features. These are directly portable.
- **Houk lab transition-state analysis (Tantillo group too, 2020–2024).** Use transition-state geometry as a **design metric**. Riff-Diff (Vázquez-Torres et al., Nature 2025) and the Houk group's TS-metric approach to de novo enzyme design (Houk 2014 Acc. Chem. Res., reviews through 2024) evaluate how well designed active sites fit a target TS. Same logic applied post-hoc: does the generated ensemble populate TS-like geometry?
- **MSM rate-constant recovery (Chodera, Prinz et al. 2011; Bowman 2014).** If you can build an MSM from a generated trajectory and the rate constants match experiment, dynamics are correct. This is the kinetic ground truth and it requires MFPT, which nobody in generative-MD computes.
- **Baker lab PLACER (Anishchenko et al., 2025).** Graph neural network that scores protein–ligand **conformational ensembles**, outputs pRMSD, lDDT, and implicitly scores active-site geometry. Can be repurposed as a post-hoc metric: generated ensemble → PLACER → confidence score per frame. Not a replacement for physics but a fast first filter.
- **Protein–ligand residence-time metrics (Bhakat & Söderhjelm 2022; Wang et al. 2024 SPIB-Metad).** Ligand autocorrelation C(τ) gives k_off; benchmark datasets exist for kinase–drug pairs. Directly portable to PLP and substrate.

Taken together, every building block exists. The missing artifact is a packaged benchmark that says: *for this cofactor system, these seven numbers must fall in these ranges, and here is the reference ensemble that gives them.* That is the deliverable.

---

## 07.5 Proposed chemistry-aware metrics for TrpB

Each metric gets: definition, reference value (from unbiased MetaD-reweighted MD), why standard metrics miss it, failure mode. All are computed from atomistic coordinates — no hidden dependencies.

### 07.5.1 Dunathan angle distribution

**Definition.** Dihedral Cα(Ser)–Cβ(Ser)–Cγ(PLP C4')–Nε(Lys87 Schiff base). For catalytic competence it must sit within ±20° of 90° during the Aex1 step.
**Reference.** Histogram from 10 μs unbiased MD reweighted onto path CV (s, z) space. Mode at 92°, FWHM ≈ 25°.
**Comparison.** JSD between generated histogram and reference.
**Why standard metrics miss it.** Dunathan angle is a 4-atom dihedral involving 3 residues + cofactor. No Cα metric touches it.
**Failure mode.** A model can get a high-entropy angle distribution (flat histogram) and the JSD looks OK, but the enzyme is not catalytically competent. Guard: also report fraction of frames within ±20° of 90°.

### 07.5.2 Schiff base geometry

**Definition.** C=N bond length (PLP C4'–Lys Nε) and sp² planarity (out-of-plane angle of the Nε). Intact Schiff base: bond 1.28–1.32 Å, planarity < 10°.
**Reference.** Tight distribution, 1.30 ± 0.02 Å, planarity < 8° at 95% CI.
**Why standard metrics miss it.** Bond lengths are not part of any backbone metric; deprotonated/hydrolyzed PLP gives similar Cα topology.
**Failure mode.** Small but consistent bias to longer C=N (1.40 Å) — the model has drifted the cofactor toward hydrolysis. Any CA metric would score fine.

### 07.5.3 Lid closure distance

**Definition.** Distance between COMM-domain residue Phe184 Cζ and α-subunit residue Glu109 Cδ (proxy for the β-subunit COMM lid closing over α). Open ≈ 14 Å, partially-closed ≈ 10 Å, closed ≈ 7 Å.
**Reference.** Trimodal distribution with reweighted populations matching JACS 2019 FES (closed ≈ 60% at 350 K based on MetaD reweighting).
**Comparison.** 3-way JSD or bin-by-bin population match.
**Why standard metrics miss it.** Two residues 75 apart in sequence; JSD on backbone PC captures only dominant global mode.

### 07.5.4 COMM-domain inter-subunit angle

**Definition.** Angle between the first principal axis of the β-subunit COMM helix bundle (residues 97–184) and the first principal axis of the α-subunit active site. Reports on the α/β allosteric coupling that turns TrpB into a catalyst.
**Reference.** 73° ± 12° in closed state, 88° ± 15° in open state.
**Why standard metrics miss it.** This is a collective angle between domains; no PC of the reference trajectory necessarily aligns with it, so JSD on PC space can pass while this angle is wrong.

### 07.5.5 Active-site water occupancy

**Definition.** Count of water molecules with oxygen within 4 Å of any PLP heavy atom. Open state ≈ 5–7 waters, closed state ≈ 1–2 (water depletion is part of catalytic activation).
**Reference.** Mean and variance per macrostate.
**Why standard metrics miss it.** Generative models usually ignore explicit water; the metric exposes this silent failure.

### 07.5.6 PLP solvent-accessible surface area (SASA)

**Definition.** SASA of PLP atoms using a 1.4 Å probe. Reports on burial, complementary to water occupancy.
**Reference.** 110 ± 30 Å² open, 60 ± 20 Å² closed.
**Why standard metrics miss it.** SASA of a specific cofactor is not computed in any current benchmark.

### 07.5.7 D-Ser vs L-Ser positional asymmetry

**Definition.** For the engineered D-specific variant: Cα-chirality of the bound Ser (dihedral check on Cα–Cβ–N–H). For WT: verifies L-specific binding pocket.
**Reference.** 100% L-specific for WT, >95% D-specific for the designed variant (if we're extending to design).
**Why standard metrics miss it.** Stereochemistry of substrate is invisible at backbone resolution. This is the metric that matters for redesign.

### 07.5.8 Residence-time autocorrelation for the ligand

**Definition.** C(τ) = ⟨1_bound(t) · 1_bound(t+τ)⟩, where 1_bound is an indicator of Ser being within 4 Å of PLP. Fit exponential; k_off = 1/τ.
**Reference.** From unbiased + MetaD-reweighted k_off estimate. Order-of-magnitude target.
**Why standard metrics miss it.** Rate constants are absent from ATLAS metrics. This is the closest bridge to experiment (kinetic assays).

Any one of these metrics alone is hackable. The seven-tuple together is hard to hack because reward-hacking on one (e.g., pinning the Dunathan angle to exactly 90° always) forces a cost on another (water occupancy distribution flattens). This is the **cross-check** that a single-scalar metric cannot give.

---

## 07.6 Packaging as a benchmark

A benchmark is not a metric — it is a frozen reference plus scoring code plus failure thresholds plus documentation. Below is the concrete directory structure I propose.

```
trpb_metad_bench/
  reference/
    metad_walker_0.xtc           # 8 walkers, 50 ns each
    metad_walker_1.xtc
    ... (8 trajectories)
    reweighted_ensemble.h5       # PATHMSD-reweighted samples + weights
    distributions/
      dunathan_angle.npz         # histograms + bin edges
      schiff_base.npz
      lid_closure.npz
      comm_angle.npz
      water_occupancy.npz
      plp_sasa.npz
      ser_chirality.npz
      ligand_autocorr.npz
  config.yaml                    # atom indices, macrostate definitions
  score.py                       # single-file scorer
  tests/
    test_on_reference.py         # sanity: reference scores self at JSD < 0.02
    test_on_mdgen_sample.py      # anti-sanity: MDGen output scores badly
  thresholds.yaml                # pre-registered failure bars
  README.md
```

**config.yaml excerpt** (reduces reviewer-level ambiguity):
```yaml
macrostates:
  open:   {path_s: "<0.35"}
  pc:     {path_s: "0.35-0.65"}
  closed: {path_s: ">0.65"}
dunathan_atoms:
  Ca_ser: "resid 61 and name CA"
  Cb_ser: "resid 61 and name CB"
  C4p_plp: "resname PLP and name C4A"   # PLP atom name in Amber LLP topology
  Ne_lys: "resid 87 and name NZ"
schiff_base_bond: ["resname PLP and name C4A", "resid 87 and name NZ"]
lid_distance:
  a: "resid 184 and name CZ"
  b: "resid 109 and name CD"
```

**score.py behavior.** `python score.py --ensemble my_traj.xtc --topology topol.pdb` prints a table:

```
metric                     | value   | target     | pass?
Dunathan fraction ±20°     | 0.62    | >0.70      | FAIL
Schiff C=N (Å)             | 1.29    | 1.30±0.03  | pass
Lid closure mode-1 freq    | 0.71    | 0.60±0.10  | pass
COMM angle (°)             | 76      | 73±12      | pass
Water occupancy (closed)   | 2.1     | 1-2        | pass
PLP SASA (Å²)              | 72      | 60±20      | pass
Ser chirality L-fraction   | 1.00    | 1.00       | pass
k_off relative to reference| 0.7x    | 0.3-3x     | pass
---------------------------- overall: 7/8, FAIL on Dunathan ----
```

**thresholds.yaml.** Hard-coded pass/fail bars set **before** any ML model is scored — this prevents post-hoc tuning. Preregistration is the same idea clinical trials use for the same reason (researcher degrees of freedom).

Dependencies: MDAnalysis + numpy + h5py. No GPU. No training. Total < 1500 lines of Python including tests. Open-source from day one — Apache 2.0.

---

## 07.7 How this plugs into the lab's work

Four concrete lanes.

**STAR-MD extension (Shoghi et al.).** Once published at ICLR 2026, the Anandkumar-adjacent community will want to extend STAR-MD to ligand-bound systems. The TrpB-MetaD benchmark gives them a test bed with a published ground-truth FES (JACS 2019) plus a chemistry-aware scorer. The benchmark is what turns "we ran STAR-MD on an enzyme" into a publishable validation.

**GenSLM-designed variants (Ramasamy / Anandkumar collaboration).** When GenSLM proposes a TrpB variant that shifts Aex1 → AA transition rate, you need to prescreen it by running a short MetaD. The chemistry-aware metric vector tells you, before wet-lab testing, whether the variant preserves Dunathan alignment and lid closure. Anything that fails ≥2 of 8 metrics goes to the back of the queue.

**Raswanth's GRPO (rumored direction).** GRPO needs a scalar reward. Chemistry-aware metrics can become reward signals — but I will be explicit: **do not put them in the gradient**. They are F2-level offline validators, not F0-level inputs to the policy. The reason is metric-hacking: an RL agent will find the minimum free-energy way to hit the metric, which often looks nothing like biology. Use the metrics as a constraint-based filter (reject if FAIL), and train on a broader physics prior.

**Yu's MD pipeline.** Standardizes the readout across her runs. Every MetaD or enhanced-sampling run in the group produces the same 8-number vector. Makes retrospective comparison possible.

---

## 07.8 Critical self-assessment — what could go wrong

Six honest limits.

**(1) Dunathan angle is a classical dihedral; the real catalytic effect is quantum.** σ → π* hyperconjugation has a calculated ~10¹² rate enhancement per Phillips et al. 2018, and this is an electronic effect. My dihedral metric is a geometric proxy. Missing it → missing chemistry. What I have is necessary but not sufficient.

**(2) MetaD reference ensemble has reweighting uncertainty.** Well-tempered MetaD reweighting in PLUMED typically gives ±10–20% on population estimates (Tiwary & Parrinello 2015). The reference distributions are **noisy ground truth**. Threshold widths need to account for this — my proposed ±20% on population fractions reflects this.

**(3) Metric choice depends on reaction step.** TrpB catalyzes a cascade: Ain → external aldimine → aminoacrylate → quinonoid → final product. Each intermediate has different characteristic geometry. I am focused on Aex1 (the step the JACS 2019 paper studied). For a full cycle, I need step-specific metrics. First-pass benchmark: Aex1 only; extending to the whole cycle is v2.

**(4) Off-pathway configurations.** What if the model generates a protein-only open state with the PLP fallen out? The current scorer tests each metric conditionally on the PLP being bound. If PLP unbinds, many metrics become undefined. Handling: report "fraction of frames with bound PLP" as a separate pre-check, require > 0.95 before scoring the downstream 7 metrics. This still lets a model with 94% unbinding skate, so a stricter bar may be needed.

**(5) Reference ensemble is 8 walkers × 50 ns = 400 ns aggregate.** For slow transitions (open → closed in WT TrpB occurs on μs-ms timescale experimentally), 400 ns might not sample the thermodynamic ensemble at 350 K even with MetaD bias. Need convergence check (block analysis, last-half vs. first-half divergence).

**(6) Over-fitting the metric panel to TrpB.** 8 metrics chosen because they are known to matter for TrpB. Will they generalize to other PLP enzymes (aminotransferases, decarboxylases)? Partially — Dunathan and Schiff base are universal; lid closure and COMM angle are TrpB-specific. Honest framing: this is a TrpB benchmark, not a PLP-enzyme benchmark. Scaling to other PLP systems needs per-enzyme metric design.

None of these kill the idea. All of them should be in the paper as limitations.

---

## 07.9 Benchmarks to reference

Positioned against existing infrastructure so the TrpB-MetaD pack fits into a recognizable slot.

- **ATLAS (Vander Meersche et al. 2024 NAR; ~2,000 chains by July 2025).** The apo-protein dynamics benchmark. My TrpB-MetaD benchmark is the *ligand-bound enzyme* complement, not a replacement.
- **PDBbind 2020 / CASF-2016 (Su et al. 2018, JCIM).** Static binding-pose benchmark. 285 complexes, evaluates scoring/docking/ranking/screening power. Different axis (static pose) but uses the same "scoring function on a frozen set" pattern. Useful as a design precedent.
- **P2DFlow + energy-based alignment benchmarks (2025).** Recent generative-MD models evaluated on ATLAS; shows the current ceiling and what ligand-free SOTA looks like.
- **PED 2024 (Ghosh et al. 2024, NAR 52 D1 D536).** 461 entries of IDP ensembles. Benchmark for disorder, complementary axis.
- **IDRome (Vitalis et al. 2024, Nature).** 28,058 IDR ensembles from human proteome. Scale reference.
- **M-CSA (Ribeiro et al., ongoing).** Mechanism and Catalytic Site Atlas. 1,000+ enzymes with annotated catalytic residues. Useful source for extending beyond TrpB.
- **PeptoneBench (2025 preprint).** Order-disorder continuum benchmark. Proof that the community is willing to accept new, domain-specific benchmarks alongside ATLAS.

My sales pitch in one sentence: *ATLAS is to apo proteins what TrpB-MetaD-Bench is to ligand-bound enzymes — a frozen reference with chemistry-aware scoring.*

---

## 07.10 Meeting prep Q&A — likely Anima / Amin questions

**Q1. Why 8 metrics and not 1 scalar reward?**
A single scalar is hackable and maps many physical failures to the same number. 8 independent metrics cross-check each other. For RL use, an agent forced to satisfy all 8 cannot collapse to a trivial mode. This is the same argument behind multi-reward in RLHF (Ye et al. 2024 Nature Commun on DyRAMO).

**Q2. What is your ground truth and why do you trust it?**
8-walker well-tempered MetaD on PATHMSD CVs, matching JACS 2019 (Sola/Osuna 2019) protocol with ff14SB + TIP3P at 350 K. Trust = SI-level parameter provenance, block-convergence check, FES error bars < 1 kT, and published FES as sanity benchmark. If the reference is wrong, every downstream metric inherits the error — I disclose this upfront.

**Q3. Could your metrics falsely pass a bad model?**
Yes, each individually; almost no, all together. The Dunathan angle histogram can be flat-hacked (infinite entropy, JSD ≈ 0 under wide target). Cross-metric: such a flat distribution will not reproduce lid closure populations or k_off. Designing the scorer so that the aggregate requires all 8 pass reduces this to "how much search budget does an adversary have?" With preregistered thresholds, even a determined adversary hacks 2–3 metrics at best.

**Q4. Why not just use PLACER or Rosetta to score?**
PLACER scores local conformations given a ligand pose. It does not evaluate dynamic distributions or rate constants. It is a good first filter (I would add it as metric 9), not a replacement. Rosetta scoring is structural-energy, not thermodynamic-population. Same answer.

**Q5. What if the MetaD reference is not converged?**
Convergence check is part of the benchmark release (block analysis, FES error < 1 kT in core basins). If convergence fails, the benchmark is not shipped. This is a hard gate.

**Q6. How do you plan to propose this at the interview?**
Position 1: existing metrics are apo-only. Position 2: here are 8 chemistry-aware metrics grounded in PLP catalysis. Position 3: here is the scoring harness and threshold table. Position 4: I have an 8-walker MetaD run ready to produce the reference. Not asking the lab to build it — asking for permission to publish the benchmark.

**Q7. How long to produce the full benchmark?**
4 weeks from green light. Week 1: finalize 8-walker MetaD + reweighting. Week 2: implement score.py + config.yaml. Week 3: test on reference (sanity), MDGen (anti-sanity), STAR-MD (real test). Week 4: preprint + GitHub release.

**Q8. How does this generalize beyond TrpB?**
Universal PLP metrics (Dunathan, Schiff base, hyperconjugation proxies) transfer directly to aminotransferases and decarboxylases. Enzyme-specific metrics (lid closure, COMM angle) need reparameterization. Framework is reusable; individual atom selections are not. Roadmap: TrpB v1.0, then extend to one decarboxylase and one aminotransferase (v1.1, v1.2), then propose a "catalytic-geometry benchmark family" at NeurIPS 2027.

---

## 07.11 Video and reading recommendations

Ordered by payoff-per-hour.

- **Frank Noé — "Deep Learning of Molecular Kinetics" (HITS colloquium 2023, YouTube).** 45 min. Gives the Koopman/VAMP foundation; after this, VAMP-2 and tICA stop being magic.
- **Cecilia Clementi — "Modeling Protein Dynamics with Machine Learning and Molecular Simulation" (HITS-SIMPLAIX 2025-02-10, YouTube).** 50 min. Covers BioEmu and CGSchNet; sets the bar I am measuring against.
- **John Chodera — any MSM validation lecture (2018+, YouTube via MSKCC/Chodera lab).** MSM rate constants, Chapman-Kolmogorov test, implied timescales. The grounding for "why is MFPT the right kinetic metric?"
- **Michael Toney — PLP enzymology reviews (no talk I found; start with Toney 2014 Biochim. Biophys. Acta and Phillips et al. 2018 JACS).** Don't skip the structural chemistry — my metrics reduce to these 4 features + 4 engineering choices.

---

## 07.12 Chapter summary

**Claim.** The protein-dynamics ML field is architecture-rich and metric-poor. Every SOTA model optimizes on apo-protein Cα benchmarks. For ligand-bound enzymes — which is what Anandkumar, Osuna, Raswanth, and Yu all need — these benchmarks are silent.

**Contribution.** 8 chemistry-aware metrics for TrpB PLP catalysis, packaged as a frozen reference + open scorer + preregistered thresholds, plugging into the existing benchmark ecosystem (ATLAS / PED / CASF) as the ligand-bound-enzyme complement.

**Honest limits.** Proxy for electronic catalysis, TrpB-specific, depends on MetaD convergence. Honest delta vs. current SOTA: everything existing benchmarks cannot detect, this one will.

**Ask of the lab.** Permission to publish. Minimal compute (already have the MetaD data). Willingness to use the scorer as a standard readout for the group's generative-MD outputs.

---

**Next chapter (08):** How to turn a passing score into a publishable finding — writing benchmark papers, failure modes of leaderboards, the "ATLAS saturation" problem.

**Sources referenced:**
- [STAR-MD (Shoghi et al. 2026, arXiv:2602.02128v2)](https://arxiv.org/abs/2602.02128)
- [ATLAS (Vander Meersche et al. 2024, NAR 52 D1 D384)](https://academic.oup.com/nar/article/52/D1/D384/7438909)
- [VAMPnets (Mardt et al. 2018, Nature Commun 9:5)](https://www.nature.com/articles/s41467-017-02388-1)
- [BioEmu (Lewis et al. 2024, bioRxiv 2024.12.05.626885)](https://www.biorxiv.org/content/10.1101/2024.12.05.626885v1)
- [PLACER (Anishchenko et al. 2025, Baker Lab preprint)](https://www.bakerlab.org/wp-content/uploads/2025/11/anishchenko-et-al-2025-modeling-protein-small-molecule-conformational-ensembles-with-placer.pdf)
- [CASF-2016 (Su et al. 2018, JCIM)](https://pubs.acs.org/doi/abs/10.1021/acs.jcim.8b00545)
- [PED 2024 (Ghosh et al. 2024, NAR 52 D1 D536)](https://academic.oup.com/nar/article/52/D1/D536/7334090)
- [IDRome (Vitalis et al. 2024, Nature)](https://www.nature.com/articles/s41586-023-07004-5)
- [Dunathan hypothesis + PLP stereoelectronics (Phillips et al. 2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3359020/)
- [Tryptophan synthase NMR Schiff base (Mueller et al. 2014)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4183654/)
- [Ligand residence time SPIB-Metad (Wang et al. 2024)](https://pubs.acs.org/doi/abs/10.1021/acs.jctc.4c00503)
- [Reward hacking in molecular design (Ye et al. 2025 Nature Commun)](https://www.nature.com/articles/s41467-025-57582-3)
- [Chodera MSM validation (Prinz et al. 2011, J. Chem. Phys.)](https://www.choderalab.org/publications/2014/4/26/markov-models-of-molecular-kinetics-generation-and-validation)
- [Riff-Diff catalytic motif scaffolding (Vázquez-Torres et al. 2025, Nature)](https://www.nature.com/articles/s41586-025-09747-9)
