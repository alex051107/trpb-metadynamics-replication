# Chapter 05 — ML for Protein Dynamics: Landscape, STAR-MD Deep Dive, and TrpB Failure Modes

> **Reader**: Zhenpeng Liu. **Purpose**: walk into the 2026-04-23 meeting with Amin Tavakoli able to defend or attack every technical claim in STAR-MD (Shoghi et al., arXiv:2602.02128v2), locate it inside the broader ML-for-dynamics field, and propose concrete experiments where TrpB metadynamics data exposes the model's blind spots.
>
> **Style**: no fluff, no marketing. Every citation has author + year. Numbers come from the paper tables or cited sources.

---

## 1. The ML-for-protein-dynamics landscape in 2026

The field exists because classical MD has a speed/accuracy wall: the fastest GPU-MD codes (OpenMM, AMBER pmemd.cuda, GROMACS) run ~100–500 ns/day for a 40 k atom system. A functional event like enzyme turnover (ms) or allosteric transition (μs–ms) costs weeks of GPU time per event observed, with no variance reduction. Every ML-for-dynamics method is an attempt to short-circuit that cost by learning a surrogate for some piece of the dynamics.

### 1.1 Historical tree (compact)

```
                        Physical MD (1970s–present, Karplus/Levitt/Warshel)
                                         |
                        Markov State Models (Noé, Pande, Chodera ~2007–2014)
                                         |
                                         |  — learned discretization —
                                         v
                        VAMPnets (Mardt 2018)         Time-lagged AE (Wehmeyer 2018)
                                         |
                                         |  — replace histogram with density model —
                                         v
        Boltzmann Generators (Noé et al., Science 2019)      ← grandparent; normalizing flows
                                         |
                                         |  — replace NFs with continuous-time generative models —
                                         v
        Diffusion (Ho 2020)    Flow Matching (Lipman 2022)    Rectified Flow (Liu 2022)
                                         |
              +---------------------------+---------------------------+
              |                           |                           |
    Ensemble generators          Trajectory generators        Coarse-grained emulators
    (time-independent)           (time-dependent)             (Timewarp, CGnet)
              |                           |
   AlphaFlow / ESMFlow          MDGen (Jing 2024, flow matching)
   (Jing 2024)                  ConfRover (Shen 2025, AR + KV-cache)
   BioEmu (Lewis 2024/2025)     STAR-MD (Shoghi 2026, AR + SE(3) diffusion + joint S×T)
```

Three branches matter for the 4/23 conversation:

| Branch | Question it answers | Canonical example |
|---|---|---|
| Ensemble generators | "What conformations does this sequence visit at equilibrium?" | BioEmu, AlphaFlow |
| Trajectory generators | "What does the next 100 ns / 1 μs look like given the current frame?" | MDGen, ConfRover, STAR-MD |
| Kinetic learners | "What are the rate constants between metastable states?" | MSM + VAMPnets |

STAR-MD is firmly in branch 2. Amin's group is publishing heavily in branches 1 and 2 — chapter-06 memory-kernel work is where branch 2 meets physical rigor.

### 1.2 Why the field migrated diffusion → flow matching → autoregressive diffusion

Each generation fixed a specific pain point of the previous. Boltzmann generators (Noé 2019) used invertible normalizing flows for one-shot equilibrium sampling, but exact Jacobian determinants don't scale past ~1000 atoms. Diffusion (Ho 2020) gave up invertibility for simulation-free training via denoising score matching; inference is slow (100–1000 steps). Flow matching (Lipman et al., ICLR 2023) and Rectified Flow (Liu et al., ICLR 2023) defined straight probability paths between noise and data — one-step regression, faster inference; adopted by AlphaFlow (Jing 2024) and MDGen (Jing 2024). Autoregressive diffusion (STAR-MD 2026) combines diffusion stability with causal structure via block-diffusion training (Arriola et al., ICLR 2025).

None of these has solved the **ligand-aware, rate-accurate, chemically-reactive** regime. That is where TrpB metadynamics lives.

---

## 2. STAR-MD deep dive

Full citation: Nima Shoghi, Yuxuan Liu, Yuning Shen, Rob Brekelmans, Pan Li, Quanquan Gu. *Scalable Spatio-Temporal SE(3) Diffusion for Long-Horizon Protein Dynamics*. arXiv:2602.02128v2, 2026. ByteDance Seed team; Pan Li (Georgia Tech) on author list.

### 2.1 What it actually does

Factorize a trajectory as `p(x₁:L) = ∏_ℓ p(x_ℓ | x_{<ℓ}, Δt_ℓ)`. For each new frame:

1. Start from Gaussian backbone coordinates in SE(3).
2. Denoise with a score network conditioned on the full history of clean past frames, the current noisy frame, the diffusion time τ, and the physical time gap Δt.
3. Output backbone frames (translation + rotation, per residue). Side chains are reconstructed post-hoc by an OpenFold-style structure module — they are **not** in the diffusion loss.

### 2.2 Architecture details (what Amin will actually quiz you on)

| Component | What it is | Why it exists |
|---|---|---|
| SE(3)-equivariant diffusion | Score network output covariant under 3D rotation + translation | Physical symmetry — trajectory shouldn't depend on lab frame |
| Joint spatio-temporal (S×T) attention | One attention operator over (residue i, frame ℓ) jointly, not sequential | Ablation: separable attention costs JSD 0.42 → 0.46 on 100 ns (Table 3) |
| Singles-only KV-cache, O(NL) | Caches only single-residue (not pair) embeddings across time | ConfRover caches pair embeddings → O(N²L); KV-cache blows past 256 GB GPU cap at N=500 (Fig. 5) |
| 2D-RoPE | Rotary positional embedding on (residue index i, frame index ℓ) simultaneously | Matches the 2D nature of the (i, ℓ) grid |
| Contextual noise τ ∼ U[0, 0.1] | During training, noise is added to the historical "clean" context frames | Prevents error accumulation at inference — without it, validity falls off (Table 3: 86.6 → 77.8) |
| Δt ∼ LogUniform[10⁻², 10¹] ns | Training samples at 4 decades of physical time stride | Enables inference at arbitrary stride without retraining |

### 2.3 Training data

- Dataset: ATLAS (Vander Meersche et al., NAR 2024), 1390 proteins × 100 ns × 3 replicas.
- Filter: chains ≤ 384 AA → 1080 train / 82 test split, ECOD-balanced.
- Force field: ff14SB + TIP3P (matches the TrpB setup exactly; this matters for section 9).
- **No ligands, no cofactors, no covalent modifications in the training set.**

### 2.4 Evaluation metrics

Six numbers are reported (Table 2 of the paper):

| Metric | Meaning | What failure looks like |
|---|---|---|
| Coverage JSD ↓ | Jensen-Shannon divergence between generated and oracle distributions projected onto reference PCA space | Rare basin missed |
| Recall ↑ | Fraction of oracle conformations reproduced | Mode collapse |
| tICA correlation ↑ | Match on slow collective variables | Fast modes right, slow modes wrong |
| RMSD ↓ | Positional deviation from oracle (self-pairs, not cross) | Integration drift |
| AutoCorrelation ↓ | Decorrelation of frame similarity over time | Static "frozen" trajectory |
| CA / AA validity ↑ | Stereochemical validity (% frames passing MolProbity-style thresholds) | Bond/clash errors |

### 2.5 Headline numbers from Table 2 (pp. 9–10 of the PDF)

| Metric (1 μs, stride 2.5 ns) | MD oracle | STAR-MD | MDGen | AlphaFolding | ConfRover-W |
|---|---|---|---|---|---|
| JSD ↓ | 0.23 | **0.46** | 0.56 | 0.65 | 0.55 |
| RMSD ↓ | 0.00 | 0.13 | 0.37 | 0.78 | 0.33 |
| CA+AA Validity % ↑ | 82.75 | **79.93** | 24.81 | 0.06 | 36.91 |
| AutoCor ↓ | 0.00 | 0.10 | 0.39 | 0.04 | 0.38 |

On 240 ns the corresponding JSD is 0.44 (STAR-MD) vs 0.26 (oracle) vs 0.52 (MDGen) vs 0.57 (AlphaFolding) vs 0.51 (ConfRover-W). The paper's prose claims ~0.43 which rounds this.

**Honest reading**: STAR-MD's headline is *structural validity over 1 μs*, not *distribution matching*. On validity it is within 3 points of the oracle. On JSD the gap to oracle is ~2× (0.46 vs 0.23) and is **not improved by longer horizons** — it's slightly worse at 1 μs than at 240 ns. In ATLAS language STAR-MD produces trajectories that look locally like MD but whose long-time distribution remains visibly off.

### 2.6 Strengths — what STAR-MD uniquely delivers

1. **Long-horizon stability.** All prior trajectory generators (MDGen, AlphaFolding, ConfRover) collapse at 240 ns and become unphysical at 1 μs (Fig. 3, validity curves). STAR-MD holds 80–86% validity across 1 μs. This is a real engineering win driven almost entirely by contextual noise + block diffusion.
2. **Memory scaling.** Singles-only KV-cache keeps 500-residue, 1000-frame inference inside a single 256 GB node. ConfRover would need ~2 TB for the same config (Fig. 5). AlphaFolding OOMs at 400+ residues (Table 18).
3. **Variable-stride inference without retraining.** Thanks to continuous-time Δt conditioning, a single model emits 0.01–10 ns stride trajectories. The 2.5 ns and 1.2 ns strides in Fig. 4 are both inside the training distribution.

### 2.7 Honest limitations (this is the critical part)

The authors acknowledge three in the Conclusion (p. 11):

> "While STAR-MD represents a significant step forward, there are avenues for future improvement. The temporal consistency of the generated trajectories, while strong, does not yet perfectly match that of oracle MD simulations. The model's performance could be further enhanced by training on larger and more diverse MD simulation datasets, such as MDCATH. Additionally, **a promising direction for future work is to extend the model's capabilities to simulate the dynamics of protein complexes or their interactions with small molecules, which are crucial for understanding biological processes and drug design.**"

That last sentence is the TrpB-PLP gap, in the authors' own words.

Additional structural limitations — some stated, some latent:

1. **No ligand atoms in training.** ATLAS is apo protein only. Binding pockets in STAR-MD are geometric voids, not chemical environments. PLP, PLP-Lys87 Schiff base, substrate indole — all out-of-distribution.
2. **Backbone-only diffusion loss.** Side chains reconstructed post-hoc. Catalytic residue positions (Lys87, Glu104 in TrpB) are not targets of the generative loss. Side chain dynamics under the covalent PLP linker are unconstrained.
3. **100 ns training horizon.** The model learns to extrapolate from 8-frame context to 1000-frame rollout (12×–125× OOD in history length). Events rarer than ~100 ns in the training basins are not expected to be reproducible, and the 1 μs results confirm this: the model holds validity but the distribution does not expand to cover slow modes — the J.1 benchmark admission is the authors' own phrasing, "STAR-MD concentrates around the low energy basins."
4. **Markov-style Δt conditioning.** Δt is injected via AdaLN into a model that, despite attending the full history, still conditions on a single scalar gap. Continuous-time conditioning assumes the history-to-next-frame map is a smooth function of Δt alone. For non-Markovian partially-observed dynamics (Mori-Zwanzig, see chapter 06), the true propagator has a memory kernel K(t−τ) that is not a scalar function of Δt. STAR-MD's mention of "non-Markovian properties often present in partially observed systems" is acknowledgment without a mechanism.
5. **Small proteins only.** ≤384 AA in training means multi-domain (e.g., TrpAB heterodimer ~680 AA per protomer) and oligomeric (TrpB₂ dimer, full α₂β₂ tetramer) dynamics are under-sampled.
6. **ATLAS sparse-data regime.** 1080 proteins is small compared to AlphaFold's 100M sequences. Generalization to a thermophilic P. furiosus enzyme with unusual packing is unquantified.
7. **Oracle-relative metrics.** Validity thresholds are drawn from ATLAS oracle 99-percentile (Table 5). A model that perfectly reproduces an ATLAS force-field artifact scores well. True physical correctness is not measured.
8. **On CATH1 ensemble benchmark (Appendix J.1), STAR-MD loses to BioEmu.** The paper's own wording: "STAR-MD concentrates around the low energy basins." This is a latent rare-event deficit.

---

## 3. BioEmu (Lewis et al., Microsoft Research 2024 → *Science* 2025)

Lewis et al. *Scalable emulation of protein equilibrium ensembles with generative deep learning.* bioRxiv 2024.12.05.626885; *Science* 389, 2025. DOI: 10.1126/science.adv9817. github.com/microsoft/bioemu.

Deep-learning ensemble emulator: sequence in, thousands of i.i.d. all-atom conformations out, approximating the Boltzmann distribution. Does **not** produce ordered trajectories.

Training data is the differentiator: AlphaFold prior over ~100M sequences; ~200 ms aggregated explicit-solvent MD (46 ms on 1100 CATH domains alone); ~500 k experimental ΔG measurements.

Key numbers: 0.91 kcal/mol MAE on free energies vs experiment + ms-MD ground truth on 17 CATH systems. ~10⁴–10⁵× wall-clock speedup vs explicit MD. Captures cryptic-pocket formation, local unfolding, domain rearrangements.

| Axis | STAR-MD | BioEmu |
|---|---|---|
| Output | Ordered trajectory | i.i.d. equilibrium ensemble |
| Training MD | 1390 × 100 ns ≈ 0.4 ms | 46 ms (CATH) + ~200 ms total |
| Ligand-aware | No | No (monomer only) |
| Free-energy calibrated | Not directly | Yes (~1 kcal/mol) |
| Kinetics | Autocorrelation / tICA attempt | None — pure equilibrium |

Weakness: BioEmu gives populations, not rates. For "fraction of time COMM domain sits closed" it answers; for "MFPT from open to closed" it is silent. STAR-MD's Appendix J.1 compares against BioEmu on a CATH1 ensemble benchmark and loses — the authors don't put this in the main text.

---

## 4. MDGen (Jing, Stärk, Jaakkola, Berger; NeurIPS 2024)

Jing et al. *Generative Modeling of Molecular Dynamics Trajectories.* NeurIPS 2024, arXiv:2409.17808. Flow-matching trajectory generator using a Scalable Interpolant Transformer (SiT) with stochastic interpolants to model a whole 250-frame window jointly (not autoregressively), strides ~400 ps.

Precursor to STAR-MD: established that direct generative modeling of MD trajectories is feasible, with ~180× speedup (60 GPU-seconds for 100 ns tetrapeptide vs 3 GPU-hours OpenMM).

Falls short vs STAR-MD: fixed-window block generation can't cheaply extend past training window. At 240 ns / 1 μs STAR-MD validity is 83–88%; MDGen's is 36–57% then collapses — the main empirical argument STAR-MD leans on. Beats STAR-MD on tetrapeptide transition path sampling and dynamics-conditioned design, neither of which STAR-MD has publicly demonstrated.

---

## 5. Boltzmann generators (Noé, Olsson, Köhler, Wu; *Science* 2019)

Noé et al. *Science* 365, eaaw1147, 2019 (arXiv:1812.01729). **Key insight**: learn an invertible normalizing flow `F: z → x` so that Gaussian `p(z)` maps to protein configurations with exact density via change-of-variables. Reweight by `exp(−U(x)/kT − log det J_F)` for unbiased Boltzmann samples in one shot — without sequentially simulating.

Demonstrated on BPTI (~900 atoms) capturing ms-timescale conformational change. Doesn't scale because: (1) exact Jacobian determinants cost O(N³) per sample; (2) free-energy reweighting has exponential variance when learned distribution is far from target; (3) training needs either MD data (defeats the purpose) or variational loss (mode collapse).

It's the intellectual grandparent of BioEmu, AlphaFlow, and STAR-MD. The field moved to diffusion / flow matching precisely to break the invertibility bottleneck.

---

## 6. Flow matching and continuous-time generative models

Lipman et al. (ICLR 2023 / arXiv:2210.02747) and Liu et al. (ICLR 2023 / arXiv:2209.03003, rectified flow) define a deterministic ODE velocity field `v_θ(x, t)` along straight probability paths between noise and data. Training is regression on `‖v_θ − u_target‖²` — simulation-free. Inference integrates `dx/dt = v_θ(x, t)`; straight paths mean few integration steps.

For proteins: faster inference (10–50 steps vs 200–1000 for diffusion), cleaner conditioning on both diffusion-time and physical-time separately (AlphaFlow, MDGen), and works natively on SE(3) (Chen & Lipman 2023, Riemannian flow matching).

STAR-MD chose diffusion over flow matching because (a) SE(3) diffusion (Yim 2023) had mature infrastructure for backbone generation, and (b) block-diffusion (Arriola 2025) gave a principled autoregressive/diffusion interpolation. The choice is defensible, not inevitable.

---

## 7. Classical alternatives that still matter

**Markov State Models (Pande ~2004, Noé ~2007, Chodera 2014).** Recipe: featurize trajectories (tICA of distances/torsions) → cluster into microstates → build transition matrix `T_ij = P(state_j at t+τ | state_i at t)` → eigendecompose for timescales and fluxes. Remain the rigor gold standard because: Perron-cluster gives certifiable metastable sets; implied timescales converge as τ → ∞ when Markov assumption holds; transition rates and MFPTs are first-class outputs; Chapman-Kolmogorov test lets you *reject* a bad MSM; rate predictions have been validated against single-molecule experiments. Limited by MD-data coverage requirement and no cross-sequence generalization.

**VAMPnets (Mardt et al., *Nature Commun.* 2018).** End-to-end neural version: coordinates → deep net → soft state assignment, trained to maximize VAMP-2 (variational upper bound on transfer-operator Frobenius norm). VAMP-2 is one of STAR-MD's Table 3 metrics; STAR-MD's full model scores 0.12 vs 1.22 for the "no-noise" ablation — but the no-noise model diverges structurally, showing VAMP-2 alone can be gamed.

**Time-lagged autoencoders (Wehmeyer & Noé, *JCP* 2018).** Neural tICA. Encoder compresses `x(t)`, decoder reconstructs `x(t+τ)`; latent space captures slow CVs. Feeds MSM/VAMPnet pipelines.

The 4/23 conversation will revolve around rates. STAR-MD does not explicitly compute rates. MSM + VAMPnet does. The honest reply to "is STAR-MD useful for enzyme kinetics" is: you could post-hoc build an MSM from STAR-MD trajectories, but nobody has shown that the resulting rates match MD-derived rates. Until that experiment exists, the rate claim is open.

---

## 8. Critical comparison table

| Method | Ligand-aware? | Learns rate constants? | Needs long MD training data? | Multi-domain allostery? | Rare-event sampling? | Benchmark where shown to work |
|---|---|---|---|---|---|---|
| Boltzmann Generator (Noé 2019) | No | No (equilibrium only) | No (can use variational loss) | No | Partial (with tempering) | BPTI ~900 atoms |
| MDGen (Jing 2024) | No | No (window-level) | Yes (ATLAS) | No | No | Tetrapeptides, ATLAS ≤100 ns |
| BioEmu (Lewis 2025) | No | No (equilibrium only) | Yes (~200 ms MD) | Partial | Some (cryptic pockets) | CATH 17 systems, ΔG ≈ 1 kcal/mol |
| STAR-MD (Shoghi 2026) | No | Implicit via trajectories | Yes (ATLAS 1390 × 100 ns) | Under-sampled | No (concentrates in low-E basins, J.1) | ATLAS 82 test, 240 ns / 1 μs |
| Markov State Model | If ligand in MD | Yes (explicit) | Yes (µs–ms MD) | Yes | Yes (with adaptive sampling) | Folding, kinase activation, GPCR |
| VAMPnet | If ligand in MD | Yes (via MSM) | Yes | Yes | Requires enhanced sampling | Small proteins, dialanine |
| Classical MetaD / PATHMSD | Yes (full atomistic) | Via reweighting | No (generates its own data) | Yes | Yes (by construction) | TrpB (Osuna *JACS* 2019), many enzymes |

Reading the table: on the five columns that matter for enzyme catalysis (ligand, rates, allostery, rare events), classical MetaD + MSM still dominates. ML methods own speed and generalization-across-sequences. The intersection — fast, ligand-aware, rate-accurate — is empty. That's the open problem.

---

## 9. Where TrpB metadynamics data can expose STAR-MD failures

The TrpB project already has the ingredients — 500 ns unbiased MD, GAFF+RESP parameterized PLP (charge = −2), 15-frame O→C path, PATHMSD CV, 350 K thermophilic enzyme, 39 268 atoms. The force field (ff14SB + TIP3P) matches ATLAS, which means the only OOD axis we introduce is the ligand. This is methodologically clean.

### 9.1 Experiment A — apo-TrpB → STAR-MD rollout (sanity check)

Strip PLP + substrate, equilibrate apo backbone under ff14SB, extract every 2.5 ns across 500 ns, feed 8-frame window into STAR-MD, rollout to 1 μs. **Expected**: validity ≈ 80% at 1 μs consistent with Table 2; JSD vs apo-unbiased-MD ~0.3–0.5 but no divergence. **Purpose**: baseline competence, so any subsequent failure is attributable to the ligand, not the protein being OOD.

### 9.2 Experiment B — holo-TrpB with PLP-AEX → STAR-MD

Same extraction but from the holo trajectory (PLP-Lys87 Schiff base + AEX substrate). STAR-MD consumes backbone-only (no ligand atoms). Compare STAR-MD backbone trajectory vs real holo MD. **Expected failure modes**: (1) Lys87 loop drifts toward apo-like conformations without the PLP tether — quantify as Lys87 Cα RMSD to holo MD; (2) COMM-domain closure mis-timed because STAR-MD can't see the ligand — quantify as KL divergence of `(s, z)` histogram vs metadynamics ground truth; (3) JSD vs holo MD ≥ 2× the apo gap from Experiment A. **Why**: directly occupies the "extending to small molecules is future work" admission — we show *how* it fails.

### 9.3 Experiment C — STAR-MD vs MetaD-reweighted FES on (s, z)

~100 μs of effective sampling via metadynamics on the `(s, z)` path CV gives us `F(s, z)`. Seed STAR-MD from multiple frames spanning O, PC, C; histogram on the same grid; compare free-energy surfaces. **Expected**: STAR-MD under-samples high-barrier regions (the "concentrates in low-E basins" admission). Quantify barrier-height error at O→PC saddle — a 3 kcal/mol vs 8 kcal/mol gap is 120× in Boltzmann population and equivalently off in rate. **Why**: first published benchmark pitting a trajectory generator against enhanced-sampling ground truth on a *functional* CV. Publishable whatever the outcome.

### 9.4 Experiment D — 12 TrpB variants as novel-sequence stress test

Run STAR-MD on 12 computationally designed TrpB variants (Iglesias-Fernández / Osuna lineage). Compare to (a) classical MD on the variants, (b) experimental k_cat / K_M. **Expected**: per-variant JSD correlates with sequence identity to nearest ATLAS training protein. Likely finding: STAR-MD cannot distinguish a 2-fold mutant from a 200-fold mutant on dynamics alone — a ceiling for enzyme-engineering use.

### 9.5 Summary of where we hit

| Experiment | Gap exposed | Metric | Expected outcome |
|---|---|---|---|
| A | Baseline apo | JSD, validity | Works ~as advertised |
| B | Ligand-blind holo | Lys87 drift, COMM timing, JSD | Fails; quantifies the future-work gap |
| C | Rare-event / barrier | FES mismatch on (s, z) | STAR-MD underestimates barriers |
| D | Novel-sequence generalization | Per-variant JSD vs k_cat | STAR-MD insensitive to catalytically distinguishing mutations |

Any one of B, C, D is a standalone contribution to the field.

---

## 10. Meeting prep Q&A

Ten questions Amin plausibly asks, with defensible answers.

**Q1. Single most important architectural trick?** Not joint S×T attention — Table 3 shows separable attention costs only 0.04 JSD. The dominant trick is **contextual noise during training**: without it, validity drops 86.6% → 77.8% and autocorrelation rises 0.02 → 0.11. The S×T story is marketing; the noise story is what makes long horizons work.

**Q2. Is the O(NL) KV-cache real or engineering spin?** Real. It's why STAR-MD fits 500-residue, 1000-frame rollouts in 256 GB (Fig. 5). ConfRover's pair KV-cache would need ~2 TB. Hard reason STAR-MD exists separately from ConfRover, not just a variant.

**Q3. Why diffusion not flow matching?** SE(3) diffusion (Yim 2023) had mature infrastructure; block-diffusion (Arriola 2025) gave a principled autoregressive/diffusion interpolation. Flow matching would be faster at inference; authors chose stability over speed.

**Q4. Compare to BioEmu?** Different tasks. STAR-MD: ordered trajectories (autocorrelation, tICA). BioEmu: equilibrium ensembles (calibrated free energies). On Appendix J.1 CATH1 ensemble benchmark STAR-MD loses — "concentrates around low energy basins." BioEmu for ΔG, STAR-MD for dynamics, neither for rate constants.

**Q5. Is the Mori-Zwanzig invocation in §4.6 principled?** Partially. They identify correctly that backbone coordinates are a coarse-grained subspace and MZ predicts a non-Markovian K(t−τ) + FDT-coupled random force. Attention is presented as implicitly learning this. But they never show the learned attention kernel has the analytic properties K(t−τ) should have — causality, positive-definite autocorrelation, FDT consistency. Handwave, not derivation. Most attackable theoretical move in the paper.

**Q6. Would STAR-MD work on TrpB-PLP?** No, three stacked reasons: (a) ATLAS has no ligands, PLP chemistry pure OOD; (b) backbone-only diffusion ignores Lys87-PLP covalent geometry; (c) on functional `(s, z)` CVs the "low-E basin" concentration dominates because transitions are rare. Experiments A–C operationalize this.

**Q7. What would a ligand-aware STAR-MD need?** Minimum: (a) ligand atom positions as a separate token stream in the attention; (b) training data with ligands — MDCATH is named but lacks curated holo coverage; (c) covalent-bond constraint layer for Schiff-base and other reactive linkages; (d) formal-charge-aware protonation handling. None are trivial.

**Q8. Relation to memory kernels (chapter 06)?** STAR-MD's scalar Δt is a collapsed version of what MZ propagator needs. A truly non-Markovian model would expose K(t−τ) as output and condition on integrated history convolution, not just 8 frames + Δt. Nobody has done this for proteins yet — plausibly where Amin's group pushes.

**Q9. Clearest OOD boundary?** Three bounds: (i) apo single-chain ≤ 384 AA, Δt ≤ 10 ns, horizon ≤ 1 μs — in-distribution; (ii) holo complexes, covalent modifications, oligomers — OOD; (iii) rate constants within 10× of experiment — not validated. Outside (i) you're extrapolating.

**Q10. One experiment on TrpB, which?** Experiment C — STAR-MD histograms on `(s, z)` path CV vs metadynamics-reweighted FES. Cleanest because: our MetaD is the best TrpB reference available; metric is physical (free energy); publishable either way; directly addresses the J.1 admission with a functional CV instead of ATLAS reference PCA.

---

## 11. Video / talk recommendations

Priority order for 4/23 prep:

1. **Frank Noé — *Deep Generative Learning for Physics Many-Body Systems*** (Machine Learning for Physics Workshop). youtube.com/watch?v=XhAP2VNPVhg — the canonical Boltzmann-generators talk.
2. **Tommi Jaakkola — *Generative modeling and physical processes*** (Big Data Conference). youtube.com/watch?v=GLEwQAWQ85E — sets up MDGen's flow-matching motivation.
3. **MIT News: *Toward video generative models of the molecular world*** (2025-01-23, news.mit.edu). Short press piece that gives the MDGen framing in Jaakkola's own words — useful for matching Amin's conceptual vocabulary.
4. **Sarah Lewis / Microsoft Research — *Scalable emulation of protein equilibrium ensembles with BioEmu*** (microsoft.com/en-us/research/video). For the ensemble-generator perspective.
5. Paper talk for STAR-MD itself: not released as of 2026-04-19. Check the OpenReview page (Q1JpRZkR3S) closer to meeting date for any ICLR/NeurIPS presentation video.

---

## 12. What to carry into the room on 4/23

Three claims you should be willing to defend cold.

1. **STAR-MD's headline innovation is long-horizon stability, and it's driven primarily by contextual noise — not by the joint S×T attention that the abstract foregrounds.**
2. **The ligand gap is acknowledged by the authors themselves in the Conclusion section, and the TrpB-PLP system is the cleanest proof-of-gap available in the academic community right now.**
3. **Rate constants remain the unsolved problem across the entire ML-for-dynamics field. STAR-MD doesn't solve it; BioEmu doesn't solve it; MDGen doesn't solve it. Classical MetaD + MSM still owns this column in the comparison table.**

If the conversation drifts toward "what could you contribute," lead with Experiment C (FES on (s, z) path CV). It's the best fusion of your existing TrpB infrastructure with a measurable attack on STAR-MD's weakest column.

---

## Sources

- [Shoghi et al., 2026 — STAR-MD, arXiv:2602.02128](https://arxiv.org/abs/2602.02128)
- [Shoghi et al., 2026 — STAR-MD OpenReview](https://openreview.net/forum?id=Q1JpRZkR3S)
- [Noé et al., 2019 — Boltzmann Generators, Science](https://www.science.org/doi/10.1126/science.aaw1147)
- [Noé et al., 2018 — Boltzmann Generators, arXiv:1812.01729](https://arxiv.org/abs/1812.01729)
- [Lipman et al., 2022 — Flow Matching, arXiv:2210.02747](https://arxiv.org/abs/2210.02747)
- [Liu et al., 2022 — Rectified Flow, arXiv:2209.03003](https://arxiv.org/abs/2209.03003)
- [Jing et al., 2024 — MDGen, NeurIPS](https://proceedings.neurips.cc/paper_files/paper/2024/file/478b06f60662d3cdc1d4f15d4587173a-Paper-Conference.pdf)
- [Jing et al., 2024 — MDGen arXiv:2409.17808](https://arxiv.org/html/2409.17808v1)
- [Jing et al., 2024 — AlphaFlow, arXiv:2402.04845](https://arxiv.org/abs/2402.04845)
- [Lewis et al., 2025 — BioEmu, Science](https://www.science.org/doi/10.1126/science.adv9817)
- [Lewis et al., 2024 — BioEmu bioRxiv](https://www.biorxiv.org/content/10.1101/2024.12.05.626885v1)
- [microsoft/bioemu GitHub repository](https://github.com/microsoft/bioemu)
- [Mardt et al., 2018 — VAMPnets, Nature Commun.](https://www.nature.com/articles/s41467-017-02388-1)
- [Wehmeyer & Noé, 2018 — Time-lagged autoencoders, JCP](https://pubs.aip.org/aip/jcp/article/148/24/241703/958887/Time-lagged-autoencoders-Deep-learning-of-slow)
- [Chodera & Noé, 2014 — MSM review, PMC4124001](https://pmc.ncbi.nlm.nih.gov/articles/PMC4124001/)
- [Frank Noé — Deep Generative Learning talk (YouTube)](https://www.youtube.com/watch?v=XhAP2VNPVhg)
- [Tommi Jaakkola — Generative modeling and physical processes (YouTube)](https://www.youtube.com/watch?v=GLEwQAWQ85E)
- [MIT News — Toward video generative models of the molecular world](https://news.mit.edu/2025/toward-video-generative-models-molecular-world-0123)
- [Microsoft Research — BioEmu talk](https://www.microsoft.com/en-us/research/video/scalable-emulation-of-protein-equilibrium-ensembles-with-bioemu-2/)
- [Shen et al., 2025 — ConfRover, arXiv:2505.17478](https://arxiv.org/abs/2505.17478)
- [Arriola et al., 2025 — Block Diffusion, ICLR](https://openreview.net/pdf?id=nTCF3QNsIN)
