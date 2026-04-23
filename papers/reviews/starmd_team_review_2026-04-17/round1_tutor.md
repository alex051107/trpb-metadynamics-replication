# STAR-MD — Tutor / Explainer Memo (Round 1)

**Paper**: Shoghi et al., *Scalable Spatio-Temporal SE(3) Diffusion for Long-Horizon Protein Dynamics* (STAR-MD), ByteDance Seed, arXiv 2602.02128v2, Feb 12 2026.
**Audience**: advanced undergrad entering protein-dynamics ML. Strong calculus, basic DL. Gaps: diffusion, equivariance, stat-mech.
**Goal**: make the hard parts *click* without lowering precision.

---

## 1. One-paragraph essence (p. 1–2)

Classical molecular dynamics (MD) resolves protein motion by integrating Newton's equations with ~1 fs time steps, which is honest physics but makes biologically relevant timescales (μs–ms) painfully expensive. Prior generative surrogates (MDGen, AlphaFolding, ConfRover) can sketch short trajectories (≤100 ns) but explode in memory, break their own context between chunks, or drift structurally at longer horizons. STAR-MD's **trick** is a *causal diffusion transformer* that (a) denoises one frame at a time conditioned on all previously generated frames via KV-cache (autoregression), (b) uses **joint** spatio-temporal attention on *singles-only* residue features instead of factored space-then-time attention over expensive *pair* features, and (c) injects small noise into the historical context at both train and inference to prevent compounding drift. The **result**: state-of-the-art on the ATLAS 100 ns benchmark (JSD 0.43 vs. 0.52 for ConfRover, validity 85.3% vs. 52.1%; Table 1, p. 7) and — more importantly — stable 1 μs rollouts where every baseline either runs out of memory or decays to nonsense (Table 2, p. 9).

---

## 2. Glossary (15 terms)

1. **SE(3) equivariance** — SE(3) = 3D rotations + translations. f is equivariant if f(Rx+t) = R·f(x)+t. Protein physics doesn't depend on lab-frame orientation (p. 3–4).
2. **Diffusion model (forward / reverse)** — Forward: add Gaussian noise to x₀ over τ∈[0,1] until pure noise. Reverse: learn to undo one step at a time. Eq. 1–2 on p. 4 give translations (Gaussian) and rotations (IGSO(3)).
3. **Score function** — ∇ₓ log p(xτ). Trained via denoising score matching: predict the noise ε, because for Gaussian forward process score = −ε/√(1−ᾱτ). STAR-MD's sθ outputs [sᵀθ, sᴿθ] (p. 4).
4. **ε-prediction** — Predict the noise ε instead of clean x₀. Equivalent up to loss reweighting; empirically better-conditioned because target norm is constant across τ.
5. **Noise schedule** — ᾱτ (translations) and στ (rotations): how much signal survives at diffusion time τ. Inherited from Yim et al. [36] / Shen et al. [26].
6. **Classifier-free guidance (CFG)** — Standard diffusion trick to amplify conditioning. TUTOR-UNCERTAIN whether STAR-MD uses it; main text conditions via AdaLN on (Δt, τ), not CFG dropout. Treat as "not used."
7. **IPA / frame representation** — Each residue is a rigid frame (Rᵢ ∈ SO(3), Tᵢ ∈ ℝ³). Invariant Point Attention (Jumper 2021) attends on 3D points expressed in local frames — scalars are SE(3)-invariant, coordinate updates are equivariant (p. 4).
8. **Autoregressive rollout** — p(x₁:L) = Πl p(xl | x<l, Δtl). Generate one frame given all prior frames, like LLM next-token (p. 3).
9. **KV cache** — Cache past-token Keys/Values so each new token costs O(L) not O(L²). STAR-MD caches *single* K/V only, not pairs — ~196× less memory than ConfRover (Fig. 5, p. 10).
10. **Joint vs factored attention** — Factored ("S+T"): alternate spatial attn (over residues) with temporal attn (over frames). Joint ("S×T"): flatten (i,l) tokens into length-NL sequence, one big attention matrix. Joint represents non-separable couplings; factored cannot in one layer (p. 4; p. 18 Remark 2).
11. **Mori-Zwanzig projection** — 1960s stat-mech recipe for eliminating DoFs from a Hamiltonian system. Price: reduced dynamics become non-Markovian with a history integral (p. 16, eq. 5).
12. **Memory kernel** K(t−τ) — weighting inside the MZ history integral. Zero kernel = Markov; fat kernel = long memory. STAR-MD's Proposition 1: K *inflates* when pair features are dropped (p. 17, eq. 8).
13. **TICA** — Time-lagged ICA: generalized eigenproblem Cτv = λC₀v. Top eigvecs are slowest linear collective modes — rare-transition coordinates (p. 23).
14. **MFPT** — Mean First-Passage Time. Direct kinetic observable. TUTOR-UNCERTAIN: *not* in STAR-MD's main metric tables; Tables 1–2 report JSD, recall, tICA corr., RMSD, autocorrelation, VAMP-2, validity.
15. **J-S divergence** — JSD(P‖Q) = ½KL(P‖M) + ½KL(Q‖M), M = (P+Q)/2. Symmetric, in [0, log 2]. Computed on binned PCA histograms (p. 22).

---

## 3. Diffusion math walk-through

Central forward process for translations (eq. 1, p. 4):

```
Tτ  =  √ᾱτ · T₀  +  √(1 − ᾱτ) · ε        ε ~ N(0, I₃N)
```

Decoding each symbol:

- **T₀** ∈ ℝ^(3N): the clean per-residue Cα translations of one frame (N residues × 3 coordinates).
- **τ** ∈ [0,1]: diffusion time (not physical simulation time; that's Δt). τ=0 is clean, τ=1 is pure noise.
- **ᾱτ**: cumulative signal-retention factor. ᾱ₀ = 1, ᾱ₁ ≈ 0. Encodes the noise schedule.
- **ε**: isotropic Gaussian noise, same shape as T₀.
- **Tτ**: the noised version actually fed to the network.

For rotations (eq. 2, p. 4):

```
Rτ  ~  IGSO₃(R₀, στ²)
```

Analogous construction on the SO(3) manifold: you can't just "add Gaussian noise" to a rotation matrix (it would leave SO(3)), so they use the **Isotropic Gaussian on SO(3)** — a wrapped heat kernel on the Lie group — with time-dependent variance στ² playing the role of (1−ᾱτ).

**Training loss (implicit, p. 4).** Denoising score matching:

```
L(θ) = E_{x₀, τ, ε} [  w(τ) · ‖ sθ(xτ, τ, c) − ε ‖²  ]
```

where `c = c(x₀<l, xτl, τ)` is the autoregressive conditioning (past clean frames + current noisy frame), and w(τ) is a schedule weighting. The rotation head uses the analogous IGSO(3) score.

**Why predict noise ε, not clean x₀?**

For a Gaussian forward process you can prove (Ho et al. 2020) that the conditional score is

```
∇ log p(xτ | x₀) = −(xτ − √ᾱτ x₀) / (1 − ᾱτ) = −ε / √(1 − ᾱτ)
```

So ε-prediction *is* score prediction up to a known multiplicative constant. Empirically ε has the same magnitude at every τ (it's N(0,I)), whereas x₀ has vanishing magnitude near τ=1 — so the learning target has well-behaved scale → better gradients. You *could* predict x₀ ("v-prediction" is yet another convex combination) and it's provably equivalent in expectation; the difference is optimization conditioning.

**Why does q(xτ | x₀) collapse to a single Gaussian?**

The forward process is a Markov chain: xτ = √(1−βτ) x_{τ−1} + √βτ · ε_τ. Iterating, the sum of independent Gaussians is Gaussian, and the recursion gives closed form

```
q(xτ | x₀) = N(xτ ; √ᾱτ x₀, (1−ᾱτ) I),   ᾱτ = Π_{s≤τ}(1 − βs)
```

So you *never* need to simulate the chain — sample τ, sample ε, form xτ in one line. This is what makes diffusion training parallel and cheap.

---

## 4. Joint spatio-temporal attention — walk-through

**Setup.** Protein has N residues, context has L frames. Each residue-frame pair (i, l) has a single-token embedding sᵢˡ ∈ ℝᵈ.

### Factored ("space-then-time"): what ConfRover / MDGen / AlphaFolding do

```
Layer k:
    for each frame l:                              # spatial
        s•ˡ ← SpatialAttn(s•ˡ)   cost N²L
    for each residue i:                            # temporal
        sᵢ• ← TemporalAttn(sᵢ•)  cost NL²
Total per layer: O(N²L + NL²)
```

Tensor shape throughout: [L, N, d]. The spatial block sees only one time slice; the temporal block sees only one residue's history. Space and time **never mix in a single softmax**.

### Joint ("S×T"): what STAR-MD does

```
Flatten: S ∈ ℝ^[L, N, d]  →  S̃ ∈ ℝ^[L·N, d]
         (with 2D-RoPE position embedding over (i, l))
S̃  ←  Softmax( Q K^T / √d ) V      over all L·N tokens
Total: O((NL)²) = O(N²L²)
```

ASCII picture of the attention matrix:

```
                        KEYS (residue, frame)
               (1,1) (2,1) ... (N,1) (1,2) ... (N,L)
             +----------------------------------------+
       (1,1) | ·     ·          ·     ·           ·   |
QUERIES(2,1) | ·     ·          ·     ·           ·   |
       ...   | ·     ·          ·     ·           ·   |
       (i,l) |  any query token can directly ask      |
       ...   |  any (i', l') key — no factored cage   |
       (N,L) | ·     ·          ·     ·           ·   |
             +----------------------------------------+
```

Block-causal mask: noisy-frame queries attend only to clean-history keys (p. 5, "Block-causal Attention").

### Why might this matter for non-Markovian dynamics?

If residue i at time l is *currently* flipping a loop, and that flip is *caused* by residue j's helix breathing *three frames ago*, the relevant coupling is a single element K[(i,l), (j, l−3)]. Factored attention has no direct path to this element: the spatial block can see (i,l)↔(j,l) but not across frames; the temporal block can see (j, l−3)↔(j, l) but not across residues. Joint attention sees it in one softmax.

### Where could this intuition be wrong?

- **Factored is not strictly less expressive**: if you stack enough factored layers with nonlinearities between them, you can in principle compose a spatial edge with a temporal edge and route information (i, l−3) → (j, l−3) → (j, l) → (i, l). The question is *sample efficiency*, not *representability*.
- **Joint attention with 2D-RoPE may still impose its own bias** (relative position encoding assumes translational symmetry in the (i, l) grid, which isn't strictly true for a protein).
- The paper's Mori-Zwanzig argument (§A.3) says non-separability is *provable* once pair features are dropped — but that's a linearized argument, and real proteins are nonlinear. TUTOR-UNCERTAIN how tight the theory actually binds in practice.

---

## 5. SE(3) equivariance in this paper

**What equivariance means.** For any rotation R ∈ SO(3) and translation t ∈ ℝ³, the network f satisfies

```
f( R·x + t ) = R · f(x) + t      (for coordinate outputs)
f( R·x + t ) = f(x)              (for scalar outputs — "invariance")
```

**Why it matters for proteins.** A protein's energy, forces, and physically meaningful predictions don't depend on how you oriented the PDB in the lab frame. If the network isn't equivariant, it has to *learn* this symmetry from data — wastes capacity, breaks out-of-distribution, and you get different predictions for the same molecule rotated 45°.

**Concrete machinery in STAR-MD (p. 4).**

- **Frame representation per residue**: Tᵢ ∈ ℝ³ (Cα translation), Rᵢ ∈ SO(3) (local orientation built from N–Cα–C atoms). Whole protein state x = [T, R] ∈ SE(3)^N.
- **Invariant Point Attention (IPA, Jumper 2021)**: expresses attention in terms of *distances* and *relative positions in each residue's local frame* — all of which are SE(3)-invariant scalars. Output point-updates are then re-expressed in the global frame, giving equivariant coordinate deltas.
- **Scalar single features sᵢ, pair features zᵢⱼ**: already invariant (they're learned scalars indexed by residue pairs).
- **IGSO(3) noise on rotations**: isotropic on the group, so the diffusion forward process itself is SO(3)-equivariant.
- **Backbone-update MLP**: produces ΔT in the *local* frame, then conjugates by Rᵢ to go global — equivariant by construction.

**What would break if removed?** If you replaced IPA with vanilla attention on raw Cartesian coordinates:
1. Same protein, different lab orientation → different predictions. Loss would fit the data distribution's orientation bias.
2. Long rollouts would drift rotationally — accumulated rotation errors wouldn't cancel.
3. Data augmentation by random rotation would be *mandatory* and still imperfect.
Equivariance is essentially free regularization: you bake in a symmetry the physics already has.

---

## 6. Metrics walk-through (Tables 1–2, p. 7, 9; App. D, p. 22–23)

### Structural validity (CA%, AA%, CA+AA%)

- **What**: fraction of generated frames where (a) no Cα–Cα clashes (too-close non-bonded atoms), (b) no chain breaks (consecutive Cα too far), (c) Ramachandran outliers ≤ 4.12%, (d) rotamer outliers ≤ 7.05%. Thresholds are the 99th percentile of the ATLAS oracle MD (Table 5, p. 24).
- **High = good** (more frames are physically plausible).
- **Blind spot**: this is a *per-frame stereochemistry* check, not a *thermodynamic plausibility* check. A frame can be locally valid but globally nonsense (wrong fold, buried hydrophilics). Also, a model that outputs the starting frame forever would score 100% validity.

### Conformational coverage — JSD, Recall, F1

- **What**: project every conformation onto the top PCs of the reference MD, bin into a 10× histogram, compute JSD between generated vs. reference distribution. Recall = fraction of reference bins the model also populates.
- **Low JSD = good**, **High recall = good**.
- **Blind spot**: PCA is learned from the reference, so it's a *reference-defined* yardstick — a model that finds a *real* but off-axis basin gets no credit. Also, coverage says nothing about *order* of visitation: you can shuffle frames and get identical JSD.

### Dynamic fidelity

- **tICA correlation** (higher = better): Pearson corr. between per-residue tICA contribution scores, generated vs. reference. *Blind spot*: linear; computed only on valid transitions (invalid frames silently dropped, inflates score).
- **RMSD vs lag-time** (lower |Δ| to oracle = better): average ‖xl+τ − xl‖ as a function of lag τ. *Blind spot*: amplitude-only, direction-blind.
- **Autocorrelation vs lag-time** (lower |Δ| = better): measures temporal memory in 32-PC space. *Blind spot*: a model that gets PC1 right but PC5 wrong still looks fine.
- **VAMP-2 score** (lower |Δ| = better): squared Frobenius norm of Koopman matrix — global summary of slow-mode variance captured. *Blind spot*: summary statistic, loses per-mode detail.

### MFPT / J-S divergence on TICA / contact-map agreement

TUTOR-UNCERTAIN. The **main-text metrics table** does not report MFPT or TICA-JSD explicitly. The user's prompt mentions these; they may be in the appendix (H.1) or expected as standard kinetic metrics. If present, their generic meanings:
- MFPT ratio (model vs oracle): <1 = kinetics too fast; >1 = too slow. Blind spot: huge variance with few transitions.
- Contact-map agreement: per-residue-pair contact frequency correlation. Blind spot: static in nature — a frozen wrong structure can score high if contacts match on average.

---

## 7. Long-horizon rollout — concrete walk-through (p. 7–9)

**Training.** STAR-MD is trained on ATLAS 100 ns trajectories (80 frames at 1.2 ns stride typically, though the physical stride Δt is *randomly* drawn from LogUniform[10⁻², 10¹] ns per training example — p. 5 "Continuous-time Conditioning"). Context windows during training are small (e.g. ≤80 frames, capped by GPU memory).

**Inference to 1 μs.** Paper config (Table 4, p. 22): stride 2.5 ns/frame, 400 frames total. Timeline:

```
physical time:  0 ──── 2.5ns ──── 5ns ──── 7.5ns ── ... ──── 1000ns (1 μs)
frame index:    x₁     x₂         x₃        x₄              x₄₀₀

Chunk-by-chunk, block-causal, diffusion:

Step 1 (generate x₂):
    inputs: clean history {x₁}
            + Gaussian noise x₂^(τ=1)
            + Δt = 2.5 ns (via AdaLN conditioning)
    run reverse diffusion τ=1 → τ=0 (K denoising steps, say 50)
    → x₂^(0) = clean frame x₂
    add small noise τ ~ U[0, 0.1]  →  x̃₂  (contextual noise trick, p. 5)
    append x̃₂ to KV cache

Step 2 (generate x₃):
    inputs: clean(ish) history {x₁, x̃₂}
            + noise x₃^(τ=1)
            + Δt = 2.5 ns
    reverse diffusion → x₃^(0)
    ...

Step l (generate xl):
    inputs: {x̃₁, ..., x̃_{l−1}}  (full history via KV cache)
            + noise xl^(τ=1)
    reverse diffusion → xl
    perturb → x̃l
    append
```

**Two tricks that make it not explode:**
1. **KV caching of single features only** — memory grows O(N·L·d) instead of O(N²·L·d). Fig. 5 (p. 10) shows ~196× reduction vs. ConfRover.
2. **Contextual noise perturbation** — when you re-use a generated frame as conditioning, add small noise to it. This matches the *training* distribution (training also perturbed history). Prevents the "my own outputs look subtly unlike training data → drift" failure mode (p. 5).

**Why doesn't context overflow training length?** Because Δt is continuous (AdaLN-conditioned) and randomized during training, the model sees relative time gaps spanning orders of magnitude even with short context windows. 2D-RoPE extrapolates frame indices past training length. The ablation "varying temporal resolution" (Fig. 4, p. 10) confirms they push 1.2 ns stride → ~833 frames > any training length.

---

## 8. Mori-Zwanzig in 200 words (p. 16–18)

Full-atom Hamiltonian dynamics are Markovian: the next microstate depends only on current positions + momenta. But we can only *afford* to track per-residue coordinates — a coarse subset. Mori-Zwanzig (Mori 1965 / Zwanzig 1961) gives the *exact* equation for what happens when you project onto a subspace A(t) via projection operator P. You get a **Generalized Langevin Equation** (eq. 5, p. 16):

```
dA/dt  =  P L A(t)         ← Markovian drift
       +  ∫₀ᵗ K(t−τ) A(τ) dτ   ← memory term
       +  F(t)              ← random force from eliminated DoFs
```

The memory kernel K encodes *everything* the eliminated coordinates would have done to A. Non-Markovianity is a mathematical consequence of coarse-graining, not a heuristic. STAR-MD's Proposition 1 (p. 17) goes further: if you drop *pair* features and keep only *singles*, K inflates to include the ghost of the pairs — and the inflation term is **non-separable** in space/time (Remark 2, p. 18), justifying joint attention.

**Brutally honest sentence.** STAR-MD does not *implement* Mori-Zwanzig — it cites it as a theoretical *motivation* for needing memory at all and for needing non-factored attention; the kernel K is never written down, fit, or imposed as a constraint. It's a physics-flavored justification for an engineering choice, not a derivation of the architecture.

---

## 9. Three "aha" insights

1. **"Temporal attention on singles is a Mori-Zwanzig memory kernel in disguise."** Dropping pair features doesn't make the problem easier — it shifts all the pair information into a fatter temporal memory. The architecture has to pay somewhere; the question is whether the *temporal* ledger (O(N²L²)) is cheaper than the *spatial* ledger (O(N³L)) for your regime. For N > L (realistic proteins), yes — and that's the whole pitch (p. 19–20).

2. **"Contextual noise perturbation ≈ scheduled sampling, but principled."** The long-standing autoregressive pain point is train-inference mismatch: train with teacher-forced clean history, infer with noisy self-generated history. STAR-MD aligns the two by perturbing history with the *same* forward diffusion operator during both phases. The student should notice this is *not* a hack — it's making training distribution = inference distribution, exactly.

3. **"ε-prediction + closed-form q(xτ|x₀) is why diffusion training parallelizes."** You don't simulate the forward chain, you jump directly to any τ in one Gaussian sample; the loss is one MSE. That's why diffusion training fits on GPUs at all. Without this trick, every gradient step would cost O(T_diff) simulation.

---

## 10. What to read next (5 references)

1. **Ho, Jain, Abbeel 2020 — DDPM** — arXiv:2006.11239. The canonical derivation of ε-prediction, ᾱτ, and the reverse process. Read §2–3 first; everything else builds on this.
2. **Yim et al. 2023 — SE(3) diffusion for protein backbones** — arXiv:2302.02277. The IGSO(3) rotation diffusion that STAR-MD uses verbatim.
3. **Jumper et al. 2021 — AlphaFold2** (Nature 596:583) — specifically the Supplementary for Invariant Point Attention. The frame representation + IPA are inherited wholesale.
4. **Shen et al. 2025 — ConfRover** (NeurIPS 2025). STAR-MD is basically "ConfRover but joint-attention + no pairs + contextual noise." Reading ConfRover makes every design choice in STAR-MD read as a targeted ablation.
5. **Chen et al. 2024 — Diffusion Forcing** (NeurIPS 37:24081). The "perturb your own history during training" idea that motivates STAR-MD's contextual noise. The math for why this stabilizes rollouts is cleaner here than in the STAR-MD paper itself.

**Bonus / for the Mori-Zwanzig gap**: Chorin & Hald, *Stochastic Tools in Mathematics and Science* (Springer), Ch. 6 — readable account of projection operators and memory kernels for a physics-leaning CS student.

---

*End of Round 1 tutor memo. Flags for other reviewers: §2 glossary items 6 (CFG) and 14 (MFPT) are TUTOR-UNCERTAIN and worth a skeptic pass. §4 "where the intuition could be wrong" and §8 brutal-honesty line are deliberate openings for the critic.*
