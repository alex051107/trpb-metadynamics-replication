# Reading Notes: SE3 Diffusion (STAR-MD) + Deep-TDA

**Prepared for:** TrpB MetaDynamics replication project — Amin benchmark context
**Date:** 2026-04-05
**Relevance:** Amin (Ramanathan Lab) is setting up a benchmark comparing AI-predicted dynamics (STAR-MD) with physics-based simulation (MetaDynamics). These are the two key methods.

---

## Paper 1: STAR-MD

### Paper Info

| Field | Value |
|-------|-------|
| Title | Scalable Spatio-Temporal SE(3) Diffusion for Long-Horizon Protein Dynamics |
| arXiv | 2602.02128 |
| Authors | Nima Shoghi, Yuxuan Liu, Yuning Shen, Rob Brekelmans, Pan Li, Quanquan Gu |
| Venue | ICLR 2026 (accepted) |
| Date | February 2026 |

---

### What Problem Does It Solve?

Conventional MD cannot reach microsecond timescales for most proteins — it is computationally too expensive. Prior generative models for protein dynamics (e.g., FrameDiff, MDGen, ConfRover) either:
- Produce structurally invalid trajectories at long timescales
- Have O(N³L) memory scaling (Pairformer-based), making them impractical for longer sequences or longer trajectories
- "Fail catastrophically" when rolled out beyond their training horizon (~100 ns)

STAR-MD is designed specifically for **long-horizon generation**: producing physically realistic protein trajectories at 240 ns to 1 μs scales, where previous methods collapse.

---

### How Does It Work?

#### SE(3) Equivariance

The model maintains rotational and translational symmetry of molecular systems throughout the diffusion process. Two separate processes are used:

- **Translations:** Standard Gaussian diffusion (Eq. 1 in paper)
- **Rotations:** Isotropic Gaussian on SO(3) — IGSO₃ diffusion (Eq. 2 in paper)

This ensures that rotating the entire protein does not change predicted dynamics — a fundamental physical requirement.

#### Causal Diffusion Transformer

The key architectural innovation is a **joint spatio-temporal attention mechanism**:

- Residue features at each frame attend to residue features from *previous frames*
- Causal masking ensures the model is autoregressive in time
- Complexity: O(N²L²) where N = protein length (residues), L = trajectory frames
- vs. ConfRover's O(N³L + N²L²) — the Pairformer-based competitor

**Memory efficiency at N=200, L=32:**
- STAR-MD: ~6.6 MB per attention layer
- ConfRover: ~1.3 GB per attention layer
- **196× reduction in KV cache memory**

#### Autoregressive Rollout

Trajectories are generated sequentially: each block of frames conditions on all previous frames. A key training trick is **contextual noise injection**: during training, diffusion noise τ ~ U[0, 0.1] is applied to historical context, preventing the model from overfitting to exact atomic positions in the conditioning window.

#### Training Data

- **ATLAS dataset:** 1,390 proteins, each with 100 ns all-atom MD trajectories
- **Training split:** 1,080 proteins (excluded proteins >384 residues)
- **Test split:** 82 proteins (time-based split to prevent data leakage)
- Extended evaluation set: custom 250 ns and 1 μs MD simulations

---

### Key Results and Benchmarks

#### ATLAS Benchmark (100 ns generation)

| Metric | STAR-MD | ConfRover | MDGen | AlphaFold |
|--------|---------|-----------|-------|-----------|
| Conformational recall | **0.54** | 0.36 | 0.28 | — |
| Combined structural validity | **86.81%** | 52.06% | — | 0.47% |
| tICA correlation | **0.17** | — | — | — (MD oracle: 0.17) |
| RMSD deviation | **0.07 ± 0.02** | 0.20 | — | — |
| Autocorrelation error | **0.02 ± 0.00** | 0.08 | — | — |

> Note: AlphaFold achieves near-0 structural validity despite appearing competitive on raw metrics — it cannot generate dynamically valid trajectories.

#### Long-Horizon Extrapolation

| Timescale | STAR-MD recall | ConfRover-W recall | STAR-MD validity | ConfRover-W validity |
|-----------|---------------|-------------------|-----------------|---------------------|
| 240 ns | **0.59** | 0.42 | **83.15%** | 36.51% |
| 1 μs | **0.61** | 0.45 | **79.93%** | 36.91% |

Notably, STAR-MD's recall *improves* from 100 ns → 1 μs (0.54 → 0.61), indicating better conformational exploration over longer timescales. ConfRover-W degrades in validity but keeps marginal recall improvement.

---

### Limitations

1. **Training distribution:** ATLAS contains mostly globular, soluble proteins. Membrane proteins, intrinsically disordered regions, and multimeric enzymes are likely out-of-distribution.
2. **No free energy:** STAR-MD generates *kinetically plausible* trajectories, but does not output free energy values. Recall measures which conformations are visited, not their thermodynamic probability.
3. **Force field independence:** The model learns from ATLAS MD data, so it inherits whatever force field biases ATLAS simulations contain (likely CHARMM36m + TIP3P).
4. **No explicit biasing:** Unlike MetaDynamics, STAR-MD cannot be targeted to a rare event. It explores stochastically.

---

### Relation to TrpB MetaDynamics Project

TrpB (from *P. furiosus*) is not in ATLAS — ATLAS covers 1,390 proteins but focuses on well-characterized, mostly mesophilic globular proteins. Key questions for the Amin benchmark:

1. **Out-of-distribution generalization:** Can STAR-MD generate the O→PC→C conformational transition of TrpB's COMM domain when it has never seen this protein during training?
2. **Path CV comparison:** Our MetaDynamics uses a hand-crafted 15-frame path CV (FUNCPATHMSD) defining the O→C reaction coordinate. STAR-MD generates trajectories without any such prior — does it spontaneously visit the same pathway?
3. **Timescale gap:** TrpB catalytic conformational change is on the μs timescale. Our MetaDynamics uses well-tempered biasing to accelerate this. STAR-MD claims μs-scale generation — but whether it can capture rare-event barrier crossing vs. simply generating diverse structures is unclear.

---

## Paper 2: Deep-TDA

### Paper Info

| Field | Value |
|-------|-------|
| Title | Effective data-driven collective variables for free energy calculations from metadynamics of paths |
| DOI | 10.1093/pnasnexus/pgae159 |
| Authors | Lukas Müllender, Andrea Rizzi, Michele Parrinello, Paolo Carloni, Davide Mandelli |
| Journal | PNAS Nexus, Vol. 3, Issue 4, April 2024 |
| Group | Parrinello group (ETH Zurich / IIT) |

---

### What Problem Does It Solve?

MetaDynamics requires a **collective variable (CV)** that captures the slow degrees of freedom of a conformational transition. Choosing a bad CV leads to:
- Slow convergence
- Missing intermediate states (hidden metastable basins)
- Free energy surfaces that don't correspond to the true thermodynamics

Hand-crafted CVs (e.g., our FUNCPATHMSD path CV) require expert knowledge about the transition and may miss intermediate states not known a priori. Deep-TDA addresses two related problems:
1. Learning CVs from data without prior knowledge of intermediates
2. Discovering hidden intermediate metastable states automatically via **Metadynamics of Paths (MoP)**

---

### How Does It Work?

#### Deep Targeted Discriminant Analysis (DeepTDA)

A supervised neural network trained to discriminate between known metastable states by projecting configurations into a well-separated latent space.

**Architecture:** Feed-forward network
- 3 hidden layers: {24, 12, 1} nodes
- Activation: ReLU
- Output: 1D CV value (scalar per configuration)
- Optimizer: ADAM, learning rate = 10⁻³
- L2 regularization: λ = 10⁻⁵
- Loss hyperparameters: α = 1, β = 250
- Training stopping: early stopping, patience = 15 epochs

**Training data:** MD configurations from known endpoint states (e.g., Open and Closed conformations)

The network learns a mapping s(R) → scalar such that configurations from different states are maximally separated, while configurations within each state are clustered. This is equivalent to linear discriminant analysis but nonlinear via the neural network.

#### Metadynamics of Paths (MoP)

The key innovation for discovering unknown intermediates. MoP operates in **trajectory space** rather than configuration space:

- Uses an isomorphism between path probability distributions and Boltzmann distributions of elastic polymers
- A trajectory {R₁, R₂, ..., R_N} is treated as a "polymer" where the trajectory CV S({Rₙ}) = s(R_N) − s(R₁) measures the end-to-end progress
- Biasing in trajectory space drives the system to explore reactive pathways including transition states
- "Crumpled polymer" configurations (low |S|) identify hidden intermediate basins

**MoP simulation parameters (alanine dipeptide):**
- Polymer beads: N = 512
- Simulation length: 4 × 10⁶ steps
- Timestep: 0.5 fs (config space), 1.0 fs (trajectory space)
- Damping: 500 fs (config), 1,000 (trajectory)

#### Iterative Protocol

```
1. Run unbiased MD from endpoint states (A and C)
2. Train initial 2-state DeepTDA CV on {A, C} configurations
3. Run MoP with this initial CV → discover reactive pathways + hidden basins
4. Cluster MoP trajectories → identify new intermediate states B
5. Retrain DeepTDA as n-state CV including {A, B, C, ...}
6. Run MoP again with refined CV → repeat until full A→C transitions achieved
7. Use final CV for production MetaDynamics/OPES to compute FES
```

The power of this approach: step 3 automatically discovers intermediate states that the user did not know about, without requiring prior knowledge.

---

### Key Results and Benchmarks

#### 2D Model Potential (Müller-Brown)

- System: 3 metastable basins A, B, C; highest barrier ≈ 120 k_BT
- **Problem:** Initial 2-state CV (trained on A and C only) failed to distinguish intermediate B from final state C
- **After iterative refinement to 4-state CV:** free energy difference converged to analytical value of **12.15 k_BT** with "excellent agreement"
- Reactive trajectories aligned with minimum free energy pathways

#### Alanine Dipeptide

- System: 3 conformational states C5, C7eq, Cax; simulation at 300 K in Amber99-SB force field
- **2-state CV (initial):** showed **0.2 k_BT discrepancy** vs. reference dihedral angle method after 5 ns
- **3-state refined CV:** "improved convergence speed and smaller statistical fluctuations," matched reference (explicit φ, ψ dihedrals) with no free parameter tuning
- Training data: 4,000 configurations per state

#### Comparison with Hand-Crafted CVs

| CV Approach | System | Result |
|------------|--------|--------|
| Explicit dihedral angles (hand-crafted) | Ala dipeptide | Reference standard |
| DeepTDA 2-state (initial) | Ala dipeptide | 0.2 k_BT discrepancy at 5 ns |
| DeepTDA 3-state (refined with MoP) | Ala dipeptide | Matches reference, faster convergence |
| DeepTDA 4-state (refined with MoP) | 2D model | Matches analytical value (12.15 k_BT) |

The refined DeepTDA CV matches or exceeds hand-crafted CV performance while requiring no prior knowledge of intermediates.

---

### Could Deep-TDA Improve Our Path CV?

**Current approach (Path CV / FUNCPATHMSD):**
- 15-frame path constructed from known O and C crystal structures (5DVZ, 5DW0)
- Uses Cα-based MSD to define s(R) and z(R)
- λ = 3.39 nm⁻² (= 0.034 Å⁻²) calibrated from average Cα displacement
- Known limitation: if the true O→C pathway goes through an intermediate not captured by the 15 linear interpolation frames, the CV will mis-estimate the free energy barrier

**What Deep-TDA would offer:**
1. **Automatic discovery of intermediates:** MoP would find the PC (Partially Closed) state without requiring us to know about it in advance — we currently include PC implicitly in the path frames, but cannot verify this
2. **Better CV quality:** The learned CV could separate O, PC, and C states more cleanly than the geometric Cα MSD
3. **Validation of our path:** If we ran Deep-TDA on TrpB and it converged to the same pathway, that would validate our FUNCPATHMSD approach

**Practical challenges for TrpB:**
- Requires unbiased MD data from endpoint states — we have 500 ns conventional MD (Job 40806029), which provides the O-state ensemble; C-state data would require either the 5DW0 structure or MetaDynamics output
- NN training is cheap (minutes), but the MoP simulations require significant additional compute
- PLUMED supports DeepTDA via the `pytorch` module and `PYTORCH_MODEL` CV — but this requires recompiling PLUMED with libtorch (not currently in our setup)

**Verdict:** Deep-TDA is a legitimate upgrade path for our Path CV, but is a post-replication extension, not a prerequisite.

---

## Cross-Paper Analysis: SE3 Diffusion vs. MetaDynamics

### What Each Method Provides

| Capability | STAR-MD (SE3 Diffusion) | MetaDynamics (our TrpB pipeline) |
|-----------|------------------------|----------------------------------|
| **Output** | Trajectory ensemble (coordinates over time) | Free Energy Surface F(s, z) in kcal/mol |
| **Thermodynamics** | No — cannot compute ΔG or ΔF | Yes — primary output is quantitative FEL |
| **Kinetics** | Qualitative — which states are visited | Qualitative — relative barriers, but absolute rates require long simulation |
| **Rare event sampling** | Stochastic — no guarantee of barrier crossing | Explicit — bias drives system over barriers |
| **Prior knowledge required** | None — learns from ATLAS data | CV design requires knowledge of endpoints |
| **Physical accuracy** | Depends on training data quality | Force field limited, but physically grounded |
| **Computational cost** | Minutes (GPU inference) | Days to weeks (HPC, ongoing) |
| **New protein generalization** | Unknown — TrpB is out of ATLAS distribution | Always applicable with any protein |

### Key Scientific Question for the Amin Benchmark

> **Can STAR-MD identify the O→PC→C conformational landscape of TrpB without any physics-based simulation?**

If yes: STAR-MD could be used as a cheap prior for CV design or hypothesis generation.
If no: MetaDynamics remains the only way to get thermodynamically rigorous FES for TrpB.

The two methods are **complementary, not competing:**
- MetaDynamics answers: "What is the free energy barrier between O and C?"
- STAR-MD answers: "What conformations does TrpB visit on the μs timescale?"
- Deep-TDA answers: "Can we learn a better CV from TrpB trajectory data?"

### Benchmark Design Recommendation

For the Amin comparison, the most scientifically informative benchmark would be:

1. Run STAR-MD inference on TrpB (5DVZ as starting structure)
2. Project STAR-MD trajectories onto our Path CV (s, z coordinates)
3. Compare STAR-MD-visited conformational space with MetaDynamics FES
4. Specific checks:
   - Does STAR-MD visit the C-state region (s ≈ 1)?
   - Does STAR-MD sample the PC intermediate (s ≈ 0.5)?
   - Does STAR-MD trajectory density correlate with MetaDynamics probability (exp(−F/kT))?

---

## Summary for Project Context

| Paper | Key Takeaway for TrpB Project |
|-------|-------------------------------|
| STAR-MD (arXiv 2602.02128) | Benchmark comparison target — AI generates trajectories, we provide ground truth FES. STAR-MD cannot compute free energy; MetaDynamics can. |
| Deep-TDA (PNAS Nexus 2024) | Post-replication upgrade path: replace hand-crafted FUNCPATHMSD with ML-learned CV. Would require PLUMED+libtorch setup and C-state MD data. Not blocking. |
