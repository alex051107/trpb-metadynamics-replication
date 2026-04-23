# Adversarial Review — STAR-MD (Shoghi et al., arXiv 2602.02128v2, Feb 2026)

**Reviewer stance:** hostile NeurIPS/ICML external reviewer. I read the paper looking for leverage points where the claims outrun the evidence.

---

## 1. Theory → Architecture Leap: Mori–Zwanzig as Rhetoric, Not Derivation

The paper spends Section 3.4 (p. 5) and all of Appendix A (pp. 16–19) justifying its architecture via the Mori–Zwanzig (MZ) formalism. On close reading this is **motivation dressed as derivation**.

- Section 3.4 (p. 5): *"We show that removing explicit spatial correlations 'inflates' the memory kernel for the remaining residues, necessitating a significantly richer temporal history to compensate. Crucially, this inflated kernel exhibits non-separable spatio-temporal coupling (Remark 2), meaning spatial and temporal modes cannot be factorized. This theoretical insight directly motivates our architecture."*
- Proposition 1 (p. 17, Eq. 8) gives an explicit inflation formula under **linearization** — this is a linear-response/Laplace-domain identity, not a theorem about the actual nonlinear protein dynamics or about attention expressivity.
- Remark 2 (p. 18, Eq. 18) shows the kernel is non-separable in a product-form sense `K_ij(t-τ) ≠ u_ij · v(t-τ)`.

**Where the leap lies:**
1. The memory kernel is never **learned, measured, or even estimated** anywhere in the paper. Attention weights are not shown to approximate K̃⁽²⁾(p). There is no connection between the learned attention pattern and the alleged non-separable kernel — e.g., no SVD of attention maps showing rank > 1 in time-space, no comparison against a separable-parameterization baseline's *kernel* (only its *metrics*).
2. Non-separability of an integral operator does not uniquely imply "joint attention over (residue, frame) tokens" — a stack of alternating spatial and temporal layers (which the paper calls "factorized") also produces non-separable functions via composition. The "factorized attention cannot capture non-separable kernels" claim on p. 19 (Section A.3.3, item 1) is **false as stated**: composition of linear separable maps can yield non-separable outputs; with nonlinearities between blocks it is universal. So the MZ argument at most motivates *having* temporal memory, not the *specific* joint-attention design.
3. The paper concedes as much in Section 3.4 (p. 5): *"Our work makes this connection explicit, providing the theoretical justification underlying recent temporal architectures in trajectory modeling [6, 13, 26]."* — i.e., the same MZ story justifies ConfRover/MDGen/AlphaFolding equally well. It is therefore not discriminative evidence for STAR-MD.

**Verdict:** MZ is a rhetorical hook. The architecture is defensible on pure engineering grounds (cheaper KV cache, flashattention-friendly) and should have been sold that way. The "theoretical justification" subsection is load-bearing for the paper's novelty narrative but is vacuous on inspection.

---

## 2. Long-Horizon Claims: Structural Validity ≠ Physical Dynamics

The abstract (p. 1): *"STAR-MD successfully extrapolates to generate stable microsecond-scale trajectories where baseline methods fail catastrophically, maintaining high structural quality throughout the extended rollout."* Concl. (p. 11): *"our model successfully extrapolates to generate stable, high-fidelity trajectories up to the microsecond regime."*

Reading Section 4.3–4.4 and Table 2 (p. 9) carefully, the claim decomposes as:

| Claim type | What the paper shows | What is missing |
|---|---|---|
| (a) Structural validity | Fig. 3 (p. 9), Table 2: CA+AA% ≈ 80–83% at 240 ns and 1 μs | MolProbity checks are **99th-percentile thresholds of 100 ns oracle** (Table 5, p. 24) — so the threshold is absolute and not designed for long-horizon ensembles. Side-chain placement validity at μs scale is almost surely dominated by memorized rotamer libraries rather than physically evolved side chains. |
| (b) Stable rollout | Fig. 3/Fig. 4/Fig. 24 show flat validity curves | No energy conservation, no potential-energy time series, no solvent. The "stability" shown is *structural plausibility* not *dynamical stability*. |
| (c) Correct slow modes / free-energy basins | tICA PC1/PC2 Pearson r ≈ 0.17–0.18 (Table 11, p. 30); VAMP-2 deviation 0.10 at 100 ns (Table 1) | PC1/PC2 *correlation* is weak (|r| ≈ 0.18) and is barely above MDGen (0.13) and ConfRover (0.16) at 100 ns. The paper reports no transition rates, no MFPTs, no MSM validation. "Slow modes captured" is not demonstrated — only "top-2 tICA modes weakly correlate". |
| (d) Functional/experimental agreement | Appendix J.2 (pp. 48–49): cryptic-pocket binding, Abl kinase active↔inactive | Anecdotal, cherry-picked, no statistics. Best-RMSD is reported — a **min-over-samples** metric that inevitably shrinks with more samples. No experimental validation of populations or rates. |

**Conflation to flag:** Fig. 3 (p. 9) is labeled "long-horizon stability and error accumulation" but measures only Cα + All-Atom validity percentage over time. The reader infers "physical stability"; the axis measures "percent of frames that don't have backbone clashes or rotamer outliers." A model that produces a random i.i.d. valid conformation per frame would also appear "stable" under this metric, while being physically nonsensical. **The core μs-claim rests on this single conflation.**

---

## 3. Baseline Fairness: Degraded Baselines, Changed Rules

Several concrete problems:

1. **ConfRover-W is a knee-capped ConfRover.** Section 4.3 p. 8: *"ConfRover could not be evaluated on either 240 ns or 1 μs generation tasks … even with CPU offloading of the KV cache, ConfRover's memory requirements exceeded our hardware limits (1869 GB CPU RAM, 8× H100 GPUs)."* The paper then substitutes a **windowed attention variant (ConfRover-W)** with sliding window size 14 and 2 attention sinks (Appendix F, p. 26). So the μs "catastrophic failure" of ConfRover is actually failure of an architecture that **explicitly threw away its memory**. This is precisely the mechanism (memory break) the paper said ConfRover avoided (Section 2, p. 2). The 1 μs comparison is therefore not ConfRover vs STAR-MD; it is *stream-LLM-hacked ConfRover* vs STAR-MD.
2. **MDGen's block-extension is adversarial to MDGen.** Appendix F (p. 26): *"For 240 ns and 1 μs trajectories, we extended generation by setting num_rollouts to the required number of sequential blocks."* MDGen is explicitly designed for joint 100 ns generation with no autoregressive conditioning (Section 2, p. 2). Repeated-block rollout of MDGen is the *paper's* choice, not MDGen's method — and of course it degrades. The "catastrophic failure" language is unfair here.
3. **AlphaFolding is dropped from 4 largest proteins.** Footnote 1 (p. 7) and Section 4.2: *"AlphaFolding results are evaluated on 78/82 proteins due to out-of-memory error for 4 large proteins."* The aggregate AlphaFolding numbers in Tables 1 and 2 are therefore on an easier subset than STAR-MD's — a systematic bias in AlphaFolding's favor for coverage, yet it still looks bad. But it means no head-to-head on the harder proteins.
4. **Inference protocol differs.** Section 4.1 (p. 6): *"Trajectories from fixed-stride models (AlphaFolding, MDGen) are first generated at their native resolution and then subsampled."* Subsampling alters power spectra and autocorrelations; direct-stride models (STAR-MD, ConfRover) are not subsampled. So kinetic-fidelity comparisons (autocorrelation, tICA, VAMP-2) are not apples-to-apples.
5. **Same-seed ensemble size unspecified.** Tables 1–2 report "±" across 5 seeds for STAR-MD but some baselines show no variance (e.g., AlphaFolding 1 μs tICA N/A, MDGen only 1 seed in some rows?). Need explicit seed count per cell.

---

## 4. Benchmark Leakage / Overfitting

Appendix C (p. 22): *"we adopt a time-based split for ATLAS. Specifically, the train/validation/test sets are divided based on the release date of each protein, using cutoff dates of May 1, 2018 and May 1, 2019."*

- Time-based splits are **weaker than sequence/cluster-based splits** for measuring generalization. A protein deposited after 2019 can have 80%+ sequence identity to a 2017 training protein (the very problem noted in Appendix H.3.2, p. 37: 7buy_A and 7e2s_A have >80% identity to training set). The paper acknowledges this but only removes **2 proteins** (Table 19, p. 37) — the threshold "80%" is extremely permissive; homologs at 30–70% identity are still in the test set and those are exactly where memorization-via-structure-prior shows up.
- OpenFold embeddings are frozen (Section 3.2, p. 4; Appendix E, p. 25) and provide sequence-level structural priors trained on the entire PDB including post-2019 entries. **This is a structural leak.** Any test-time protein with a homolog in PDB gets a strong prior. The single-and-pair OpenFold features essentially supply the answer to the "which fold" question before dynamics modeling starts. The paper never controls for this.
- MolProbity thresholds are calibrated on the *oracle* (ATLAS MD) itself (Table 5, p. 24). A model that memorizes ATLAS-style side-chain conformations will trivially pass its own validity filter. This is a **self-referential validity metric**.
- No ECOD/CATH-disjoint or fold-disjoint split is reported. The only "generalization" stress test in the main paper is Table 19 (removes 2 sequences). That is not a held-out-fold evaluation.

---

## 5. Ablations: Missing The Ones That Matter

Table 3 (p. 10) ablates: (a) contextual noise, (b) separable vs joint attention, (c) S×T placement inside vs outside diffusion block. Notably **not** ablated:

- **Param-matched separable baseline.** The "w/ Sep Attn" row is not reported at matched parameter count. Joint S×T has tokens of size N·L; factored attention operates on smaller token sets and can compensate with more layers/channels. Without a FLOP- or param-matched comparison, "joint > separable" conflates capacity with architecture.
- **No-causality ablation.** Is causality actually necessary, or would bidirectional attention within a fixed window plus rollout perform the same? Never tested.
- **No-OpenFold-prior ablation.** How much of STAR-MD's gain is from the frozen OpenFold single/pair features (which encode a huge amount of the ATLAS answer) vs from the dynamics architecture? Never tested.
- **Context length L.** Training uses L=8 (Table 7, p. 28). The "memory" story demands longer context. Why does L=8 suffice? Is the memory kernel actually being used, or is the model essentially 1-step Markovian with a shallow context buffer? A context-length ablation is conspicuously absent.
- **Continuous-time Δt conditioning.** The paper claims (Section 3.3, p. 5) that LogUniform Δt sampling enables μs extrapolation. Never ablated against fixed-stride training.
- **Contextual-noise level τ ∈ U[0, 0.1].** Never swept. Is 0.1 a magic number?

In ablation Table 13 (p. 35, 1 μs), "w/ Sep Attn" and "w/ Preproc Attn" **beat** STAR-MD on some validity metrics (CA% 93.12 and 94.12 vs 91.00) and match/beat on CA+AA%. This significantly weakens the "joint S×T is necessary" claim at the headline horizon.

---

## 6. "Catastrophic Failure" of Baselines: Training-Horizon Mismatch

Abstract p. 1 and Section 4.3 (p. 7): *"baseline methods fail catastrophically."* Unpacking:

- **AlphaFolding** was trained for 16-frame blocks at 10 ps stride (Appendix F, p. 26). Asking it to roll out 1 μs is **100,000× its native horizon**. Of course it fails — that is not "STAR-MD is better," that is "you asked the wrong model the wrong question."
- **MDGen** trained on 250-frame × 400 ps = 100 ns blocks. 1 μs = 10× its native block, extended by naive block concatenation. Not designed for this either.
- **ConfRover** could not be evaluated natively due to memory (see §3). The windowed proxy ConfRover-W is a different model.
- **STAR-MD's continuous-Δt training** (Section 3.3) *explicitly* trains on strides up to 10 ns. Its 2.5 ns stride at 1 μs is very close to its training range. So STAR-MD is evaluated near its training regime while baselines are evaluated far outside theirs. **Apples to oranges.**

The fair headline would read: *"When asked to extrapolate 100× past their training horizon, baseline models degrade; STAR-MD — which was trained for this — does not."* That is a much weaker statement than "catastrophic failure."

---

## 7. Metrics Gaming: What Would a Memorizer Score?

A model that memorizes ATLAS-style valid frames and outputs random permutations thereof would score:
- **CA/AA validity high** — all output frames are valid by construction (thresholds set from ATLAS itself, Table 5).
- **Recall moderate** — i.i.d. sampling from a memorized bank covers most bins of PC1–PC2 (Appendix D, p. 22). JSD punishes distribution shape but 10-bin PCA is coarse.
- **Autocorrelation** — for a random permutation, autocorrelation ≈ 0 for all lags. STAR-MD's autocorrelation-difference metric at 1 μs is 0.10 (Table 2). An i.i.d. memorizer would score ≈ 0.0–0.2 depending on the reference. **Near-zero autocorrelation is consistent with both "perfect dynamics" and "no dynamics."** The paper does not disambiguate.
- **RMSD difference** — low for an i.i.d. sampler from the correct ensemble (since RMSD-lag plateaus at the equilibrium value). STAR-MD scores 0.07 at 100 ns and 0.13 at 1 μs (Table 2). Ambiguous.
- **tICA correlation** 0.17–0.18 is **weak** (|r| ≈ 0.18 explains ~3% of variance). Oracle MD itself only scores 0.17 (Table 1). That the "oracle" replicates itself with correlation 0.17 strongly suggests the tICA metric has a low ceiling and noise floor — any model hitting ≈ 0.17 is indistinguishable from "draws from equilibrium with no temporal structure."

**The metric suite is weakly diagnostic of dynamics.** An equilibrium ensemble emulator (BioEmu, cited in Appendix J.1) would likely match most of these numbers. Indeed, Appendix J.1 shows BioEmu **outperforms** STAR-MD on the CATH1 free-energy benchmark (Fig. 25, p. 46) — which is the test that actually measures free-energy fidelity. The paper frames this as BioEmu being "overly diverse" but it is more honestly read as: **on the benchmark that isolates thermodynamic accuracy, STAR-MD loses.**

---

## 8. Cherry-Picking: Per-Protein and Per-Scale

- **Sequence-length breakdown (Tables 14–18, pp. 36–37)** shows STAR-MD's advantage is **uneven**. For 150–225 AA (11 chains), JSD 0.37 vs ConfRover 0.47 — good. For 100–150 AA (16 chains), JSD 0.49 vs ConfRover 0.53 — thin margin. Variances are large; bucket sizes 11–23 chains mean confidence intervals overlap heavily. No significance testing reported.
- **Per-protein coverage plots (Figs. 13–22, pp. 38–42):** on several proteins STAR-MD's recall is comparable to or worse than MD itself's inter-replica recall (MD-to-MD recall in Fig. 2(b) p. 8 shows MD replicas only agree at R≈0.65 — the metric has a hard ceiling that varies per protein). The paper cherry-picks Fig. 2(b) showing two-mode coverage for 6XB3-H but Fig. 22 (6tly_A) shows STAR-MD missing modes seen in all three MD references.
- **10 μs extreme-horizon (Appendix I.2, Table 20, p. 44):** CA+AA validity drops to 77.28%. The paper calls this "stable" but the comparison drops 8–10 percentage points from the 1 μs number (83.15% at 240 ns → 79.93% at 1 μs → 77.28% at 10 μs). This is slow but clear error accumulation; the Fig. 24 curve shows a descending trend that the text does not discuss.
- **Abl kinase case (Appendix J.2.2, pp. 48–49):** best core-RMSD 2.00–2.60 Å reported from 500 samples. Min-over-samples is a free parameter — **more samples → better min-RMSD**. Not a population or rate claim, just "the model can produce *some* frame that looks vaguely like the other state." No statement about whether the transition happened in a single trajectory, whether the intermediates are on-path, or whether the ratio of active-to-inactive populations is correct.

---

## 9. Missing Reproduction Details

- Batch size conflict: Table 7 (p. 28) says "Global batch size 1" but main text Section 3.3 area implies batch size 8. Which is correct? Critical for reproducibility.
- Learning rate conflict: text p. 28 says "5 × 10⁻⁵" but Table 10 (p. 29) says "0.0002." Direct contradiction.
- OpenFold checkpoint hash/version not specified (Appendix E, p. 25).
- Training compute budget (GPU-hours, wall clock, total tokens) not reported.
- Random seed handling for "±" metrics — how seeds are drawn, how shared across models.
- MD oracle for 240 ns and 1 μs: Appendix F says "Gromacs 2023.2, V100, same ATLAS protocol" — but what force field version (CHARMM36m? Amber14SB?), water model, ion concentration, thermostat? The paper delegates to Vander Meersche et al. [30] without explicitly restating. These are the reference for **every kinetic-fidelity claim at long horizons**.
- Number of 240 ns / 1 μs proteins: 32 and 8 respectively (Section 4.3, p. 7). Which 32 and 8? Selection criteria? Selection on ease?
- Inference sampling: Table 8 gives 200 diffusion steps, Euler SDE — no ablation on solver fidelity or step count.

---

## 10. Overstated Claims — Direct Quotes

1. **Abstract, p. 1:** *"state-of-the-art performance across all metrics"* — Table 1 shows STAR-MD ties or loses to the MD oracle on every metric by construction, and Appendix J.1 (p. 46) shows BioEmu beats STAR-MD on CATH1 free-energy. "All metrics" excludes any metric that isolates thermodynamic accuracy.
2. **Abstract, p. 1:** *"baseline methods fail catastrophically"* — see §6. Baselines were pushed 10×–100× past their training horizons. "Catastrophic" framing is unfair given the apples-to-oranges comparison.
3. **Section 1, p. 2:** *"STAR-MD … generates physically plausible protein trajectories over microsecond timescales."* — "Physically plausible" is a strong claim. The paper demonstrates *MolProbity-plausible single frames*; it does not demonstrate correct free energies, correct transition rates, or energy conservation. "Structurally valid frames stitched together" is weaker than "physically plausible dynamics."
4. **Section 3.4, p. 5:** *"This theoretical insight directly motivates our architecture."* — Overstated: the MZ result motivates *some* form of non-separable temporal modeling, not the specific joint-token attention. Many architectures satisfy the same constraint (see §1).
5. **Section 4.4, p. 8:** *"STAR-MD exhibits controlled error accumulation."* — True in the limited sense of validity-% over time. The 10 μs experiment (Table 20) shows clear validity erosion that contradicts "controlled" when viewed across scales (96% → 83% → 77% from 240 ns → 1 μs → 10 μs, though not same proteins).
6. **Section 4.5, p. 10:** *"These ablation studies demonstrate that each component of STAR-MD addresses a specific challenge."* — Table 13 (1 μs) shows "w/ Sep Attn" *beating* STAR-MD on CA% (93.12 vs 91.00). This weakens the "joint attention is necessary" claim at the headline horizon the paper markets.
7. **Conclusion, p. 11:** *"paves the way for accelerated exploration of complex biological processes"* — aspirational language unsupported by experimental validation against any measured biological process (binding affinities, rates, populations).

---

## My Top-3 Vulnerabilities

The three **weakest load-bearing claims** that could sink the paper under serious review:

### 1. The μs-stability claim is built on a metric (CA+AA validity %) that does not distinguish "memorization of valid frames" from "correct dynamics."
Evidence: Table 5 (p. 24) derives validity thresholds from the ATLAS oracle itself — self-referential; Fig. 3 (p. 9) conflates "structural plausibility" with "dynamical stability"; autocorrelation at long lags (Fig. 8 p. 31, Table 2) near zero is consistent with both perfect dynamics and random-permutation-of-valid-frames. **An equilibrium-ensemble baseline (BioEmu-style) run at μs would likely score similarly on these metrics, and in fact does beat STAR-MD on the CATH1 free-energy benchmark (Fig. 25, p. 46).** Without a thermodynamic/kinetic check that discriminates these regimes, the headline claim is unsupported.

### 2. The "catastrophic baseline failure" at μs is a training-horizon artifact, not an architectural failure.
Evidence: AlphaFolding trained on 16-frame × 10 ps = 160 ps windows (Appendix F, p. 26); MDGen on 100 ns blocks; ConfRover natively cannot fit in 8×H100+1.9 TB RAM and was replaced by a memory-crippled variant (ConfRover-W, Section 4.3 p. 8). STAR-MD trained with Δt up to 10 ns (Section 3.3 p. 5) — within a factor of 4 of the 1 μs stride (2.5 ns). **STAR-MD is evaluated inside its training regime; baselines are evaluated 10×–100× outside theirs.** The comparison does not isolate architectural quality from training-data-horizon matching.

### 3. The Mori–Zwanzig theoretical justification (Section 3.4, Appendix A) does not derive the architecture — it is post-hoc narrative.
Evidence: Proposition 1 (p. 17) is a linear-response identity; nothing in the paper measures, learns, or parameterizes the memory kernel K̃⁽²⁾(p). Remark 2's "non-separability" (p. 18) does not uniquely select joint-token attention — any sufficiently deep factorized model with nonlinearities produces non-separable operators. The claim in Section A.3.3 item 1 (p. 19) that "factorized attention cannot capture non-separable coupling" is **false as an architectural theorem**. Since the paper's contribution narrative ("theoretically justified joint S×T attention") depends on this argument, and ablation Table 13 (p. 35) shows separable attention outperforming joint on CA% at 1 μs, the contribution reduces to: "we moved pairformer out and saved memory, which lets us train longer context." That is an engineering paper, not a theory-grounded one — and it should be sold as such.
