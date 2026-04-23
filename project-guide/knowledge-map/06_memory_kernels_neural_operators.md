# Chapter 06 — Memory Kernels, Mori-Zwanzig, and Neural Operators

> Target reader: me (Zhenpeng), preparing for the 2026-04-23 meeting with Amin Tavakoli (Caltech/Argonne, Anandkumar group).
> Trigger: Amin's 4/11 Slack note — "protein dynamics are not Markovian if the protein representation is not all-atom (coarse grain). This is related to Mori-Zwanzig formalism… I am trying to study more and potentially find efficient ways to model this."
> Goal: hold my own in a 30-min conversation. Not pretend to be an expert. Know enough to ask good questions.

---

## 06.1 Why non-Markovian dynamics matter for coarse-grained proteins

### Intuition first

An all-atom MD simulation is Markovian by construction. Given positions and velocities of every atom at time `t`, Newton's equations tell you exactly what happens at `t + dt`. No history needed. That's the definition of a Markov process on phase space.

Now imagine you project the system onto one coordinate — say the Cα RMSD between the open (O) and closed (C) states of the TrpB COMM domain, or a path CV `s(R)` as in my current replication. You have thrown away roughly 39,000 of the 39,268 degrees of freedom. The ones you threw away (side-chain torsions, water dipoles, PLP cofactor vibrations) are still moving. They still exchange energy with `s(R)`. But you don't see them.

From the point of view of `s(R)` alone, those hidden DOFs look like a colored noise source plus a time-delayed restoring force. If the closed state fluctuates and nudges `s(R)`, the push does not arrive instantaneously as white noise — it carries the imprint of however long it took for that fluctuation to propagate back. That is memory.

One-line statement: **coarse-graining is equivalent to tracing out hidden variables, and tracing out hidden variables generically produces memory.**

The Markovian approximation for a CG coordinate holds only when the "hidden" DOFs relax much faster than the CG coordinate you care about. For small peptides sampled at nanosecond resolution this is often OK. For backbone-only or residue-level representations of a 400-residue enzyme like TrpB, with PLP, water, and ligand all contributing to the effective friction, it almost certainly is not.

Ayaz, Tepper, Brünig, Kappler, Daldrop, and Netz (2021, PNAS) showed this explicitly for an α-helix-forming peptide: the Markovian model cannot simultaneously reproduce folding AND unfolding times from MD, but the generalized Langevin equation (GLE) with an extracted memory kernel can (https://www.pnas.org/doi/10.1073/pnas.2023856118).

### Math (one layer deeper)

Let `q(t)` be a coarse variable (CV) and `p(t)` its conjugate momentum. Under Mori-Zwanzig projection, the exact equation of motion is

```
dp/dt = -dV_eff/dq  -  ∫_0^t K(t - s) p(s) ds  +  η(t)
```

Three terms:
1. Conservative mean force from an effective potential `V_eff(q)` (the PMF / free-energy surface).
2. A **memory kernel convolution** with past momenta — this is the history-dependent friction.
3. A **random force** `η(t)` related to `K(t)` through the second fluctuation-dissipation theorem: `⟨η(t)η(s)⟩ = k_B T · K(t − s)`.

If `K(t) = 2γδ(t)`, the convolution collapses to `-γp` and you recover ordinary Langevin. But in general `K(t)` is a non-trivial decaying function whose tail encodes how long the hidden bath remembers past kicks.

---

## 06.2 The Mori-Zwanzig formalism — what it actually is

Mori-Zwanzig is a projection-operator scheme. You pick a projector `P` onto a subspace of observables you care about (e.g. functions of `q`, or `{q, p}`). Let `Q = 1 − P`. Starting from the full Liouville equation `dA/dt = iLA`, you can formally derive

```
dA(t)/dt  =  Ω · A(t)  +  ∫_0^t K(t − s) A(s) ds  +  F(t)
```

where:
- `Ω = PiLP` — the "streaming" / Markovian part (mean-force dynamics on the resolved variables).
- `K(τ) = PiLe^{τQiL}QiLP` — the memory kernel, expressed through the "orthogonal" dynamics that live in the complement of your projector.
- `F(t) = e^{tQiL}QiLA(0)` — the "random" force, orthogonal by construction to `PA`.

The identity is exact for any projector. Everything you did by coarse-graining is bookkept. Nothing was "approximated away" — it was moved into `K(τ)` and `F(t)`. The cost is that `K(τ)` now carries all the complexity you avoided.

Why this matters: any statement like "let's replace all-atom MD with an ML surrogate on 100 backbone CVs" is, whether you like it or not, a claim about your ability to reproduce `V_eff`, `K(τ)`, and the statistics of `F(t)`. If your surrogate ignores `K(τ)`, you are making the Markovian approximation, and Ayaz/Dalton/Netz's data say that's quantitatively wrong for protein folding timescales.

A useful modern review on the machinery is Jung, Hanke, and Schmid on the generalized Langevin equation and the Mori projection operator technique (arXiv:2503.20457, 2025). For data-driven learning of MZ operators, see Lin and Lu's SIAM Journal on Applied Dynamical Systems paper (2021, arXiv:2101.05873) and the Chorin-Stinis line on Wiener projections.

---

## 06.3 Memory kernel estimation from MD data

This is where feasibility becomes concrete. Three representative lines of work:

### Vroylandt et al. 2022 (PNAS) — likelihood-based GLE

Vroylandt, Goudenège, Monmarché, Pietrucci, Rotenberg (2022), "Likelihood-based non-Markovian models from molecular dynamics", PNAS 119(13), e2117586119. Parameterizes `K(τ)` via hidden auxiliary variables (finite exponentials — an extended Markov embedding) and fits by **maximum likelihood** of the observed trajectory rather than by Volterra inversion of correlation functions (brittle at long times). Recovers kernel and noise statistics jointly. Code: HadrienNU/GLE_AnalysisEM.

Companion paper, Vroylandt & Monmarché (2022, J. Chem. Phys. 156:244105, arXiv:2201.02457): position-dependent memory kernels via Volterra equations. Code: HadrienNU/VolterraBasis. This matters because real protein kernels depend on position — friction near the transition state differs from friction in the wells.

### Ayaz 2021 and Dalton 2023 (PNAS) — protein folding with memory

Ayaz, Tepper, Brünig, Kappler, Daldrop, Netz (2021), PNAS 118(31), e2023856118:
- α-helix-forming polypeptide, explicit-water MD.
- Extracts `U_eff(q)` and `Γ(t)` by direct GLE inversion.
- Memory decay time **hundreds of ps to ns**, comparable to folding time itself.
- Non-Markov GLE reproduces folding AND unfolding times; Markov cannot fit both.

Dalton, Ayaz, Kiefer, Klimek, Tepper, Netz (2023), PNAS 120(31), e2220068120:
- Eight fast-folding proteins, 10–80 residues (chignolin, α3D, Trp-cage, villin HP35, WW, λ-repressor, …).
- Data: **DE Shaw Anton trajectories, 100 μs – 3 ms per protein.**
- Memory-induced acceleration reduces folding times by up to 10× vs. Markov prediction.
- Headline: for fast folders, memory-dependent friction matters more than barrier height. Striking, non-obvious — worth flagging to Amin.

Follow-on: Dalton et al. (2025), "Hierarchical friction memory leads to subdiffusive configurational dynamics" — kernel has power-law / multi-timescale structure, so single-exponential fits fail. Kiefer/Netz JCTC 2024 (https://pubs.acs.org/doi/10.1021/acs.jctc.3c01289) gives practical numerics for sparse-framed trajectories.

### Data-driven closure / MZ learning

Lei, Baker, Li (2016, PNAS, https://www.pnas.org/doi/10.1073/pnas.1609587113) — early GLE parameterization on model systems. Lin & Lu (2021, SIAM JADS, arXiv:2101.05873) — unifies MZ with Koopman operator learning; relevant because Koopman + VAMPnets is already the Noé-group ML-for-MD pipeline. Ma/Wang/Li data-driven non-Markovian closures (Physica D 2015, Chorin-Stinis lineage) — historical recipe: observe coarse trajectory, fit `K(τ)` and random-force statistics, validate against full simulation.

### How much data do you actually need?

Honest answer: a lot, and it depends strongly on the memory time vs. the dwell time of the CV.

- Ayaz 2021: single trajectory around 1 μs of explicit-water MD was sufficient for a 20-residue peptide, for a 1D CV.
- Dalton 2023: used pre-existing DE Shaw runs of 100 μs–3 ms per protein. You need many folding/unfolding events to get kernel statistics, especially in the transition region.
- Vroylandt 2022 shows the likelihood method is more sample-efficient than Volterra inversion, but still requires enough transitions to cover phase space.
- For a TrpB-sized enzyme (~400 residues) with ligand binding and a ~10 kcal/mol barrier between O and C, you almost certainly need enhanced sampling. A single 500-ns conventional MD is not enough. That's exactly why we're using metadynamics — to get many crossings.

**Feasibility rule of thumb I'd use in the meeting:** if you have `N_cross` independent barrier crossings and the memory time `τ_mem` is much less than the dwell time `τ_dwell`, you can estimate a 1D kernel reliably. If `τ_mem ~ τ_dwell`, you need `N_cross >> 100` plus very careful treatment of stationarity. Scaling up to 2D or position-dependent kernels squares the data requirement. This is the rate-limiting factor.

---

## 06.4 Neural operators 101

### NN vs. NO

A neural network learns `R^n → R^m` between finite-dimensional vectors. A **neural operator** learns `G: A → U` between function spaces — input is a function `a(x)` (initial condition, forcing, BC), output is another function `u(x, t)`. The practical consequence is **discretization invariance**: train on a 64×64 grid, evaluate on 256×256, get consistent answers. A vanilla CNN cannot because its parameters are tied to grid size. Kovachki, Li, Liu, Azizzadenesheli, Bhattacharya, Stuart, Anandkumar (2021/2023, arXiv:2108.08481) is the canonical theory paper and proves a universal approximation theorem for operators.

### Fourier Neural Operator (FNO)

Li, Kovachki, Azizzadenesheli et al. (2020, arXiv:2010.08895). Signature move: parameterize the integral kernel in **Fourier space**. Each layer does `v → σ(W·v + F^{-1}[R_θ · F[v]])` — truncate to `k_max` modes, learn a linear transform on them, invert. Cheap (FFT is O(N log N)), global receptive field. FNO claimed 1000× speedup over traditional PDE solvers on turbulent Navier-Stokes. Anandkumar lab's flagship paper; the reason operators are on Amin's radar.

### DeepONet

Lu, Jin, Pang, Zhang, Karniadakis (Nat. Mach. Intell. 2021, arXiv:1910.03193). Two-network architecture: **branch net** encodes input function at fixed sensors, **trunk net** encodes output query points, output is a dot product. Theoretically grounded in Chen & Chen's 1995 universal approximation for operators. FNO and DeepONet are the two default starting points for operator learning.

### Graph Neural Operator

Predecessor to FNO. Integral kernel parameterized as message passing on a graph. More natural than FNO for irregular geometry — e.g. atom-level protein graphs.

### Why Anandkumar pushes this framing

Two reasons from her talks. First, discretization invariance is philosophically clean — the physics lives in function space, not on a grid. Second, many physics problems ARE operator problems (IC → trajectory, source → solution), so the infinite-dimensional structure is real. For multiscale problems — turbulence, protein dynamics, weather — operators offer hope of better sample efficiency and out-of-distribution generalization than plain NNs.

---

## 06.5 Recurrent Neural Operator and the memory angle

Honest flag: "Recurrent Neural Operator" is not a single canonical paper from the Anandkumar group as of April 2026. It is a family of closely related works.

Closest canonical Anandkumar-group paper on long-time dynamics: **Markov Neural Operator** (Li, Liu, Azizzadenesheli, Bhattacharya, Stuart, Anandkumar 2021, https://github.com/neuraloperator/markov_neural_operator). Learns a one-step operator for dissipative chaotic PDEs and iterates autoregressively; reproduces long-time statistics of turbulent Kolmogorov flow. Implicit assumption: single-step is enough — Markov on the chosen state. For a snapshot of a PDE often fine; for a low-dimensional CV projection of MD, exactly the Markov assumption Amin flags as problematic.

Work that explicitly adds memory:
- **Memory Neural Operator (MemNO)**, Buitrago Ruiz / Marwah / Gu / Risteski (2024, arXiv:2409.02313). Combines S4 (structured state-space) with FNO. Motivation is **explicitly Mori-Zwanzig**. Proves examples where memory-augmented is arbitrarily better than Markov, shows up to 6× error reduction on low-res/noisy PDE benchmarks. The paper that directly answers "why memory in a neural operator?"
- Recurrent-FNO / RNN hybrids for long-time integration (Michałowska, Goswami et al. 2023, arXiv:2303.02243).
- Implicit U-Net FNO (IU-FNO) for turbulence long-horizon stability, 2023.
- Memory-efficient Kernel Neural Operators (KNO), 2024 (arXiv:2407.00809).

Parallel line outside the Anandkumar group:
- Wang/Ren/Li et al. (2020), RNN closure of parametric POD-Galerkin ROMs based on MZ — explicit MZ-inspired RNN closure for fluid ROMs.
- Koren et al. (2025, arXiv:2507.23428), "Merging Memory and Space" — continues the MemNO direction.

**Meeting one-liner:** the canonical "Markov Neural Operator" from Anandkumar is explicitly Markovian; the MZ-aware successor (MemNO) is from another group, cites MZ directly, and is the natural reference if Amin wants to move in that direction.

---

## 06.6 Feasibility table for TrpB-sized systems

| Approach | Idea | Rigor | Data cost | Works today for ~400 AA + ligand? |
|----------|------|-------|-----------|-------------------------------|
| **GLE + learned memory kernel** (Ayaz/Netz, Vroylandt) | Fit `V_eff(q)` and `K(τ)` from MD | Rigorous (MZ exact in the limit) | 100 μs – ms trajectories per system; Anton-class | Demonstrated for <100 AA peptides. Extending to TrpB is believable for 1D path CV, but nobody has published it for a ligand-bound 400-AA enzyme. |
| **Direct seq→traj ML** (STAR-MD, DiffMD, TimeWarp, Bio-Emu) | Ignore explicit memory; train a big enough model to match trajectory statistics | No rigorous MZ guarantee; relies on capacity | Huge (DE Shaw-scale pretraining) | Scales to proteins but gives ensembles, not calibrated kinetics. Memory is absorbed implicitly. |
| **Coupled: NO parameterizes memory kernel** | Use a neural operator to output `K(τ)` (or latent-state dynamics with memory) and integrate GLE | Best of both — rigorous form, expressive parameterization | Moderate — need data for the operator, not for every system | Largely speculative. MemNO + GLE would be the template. No published protein paper yet to my knowledge. **This is very possibly what Amin is angling toward.** |
| **MSM / VAMPnet / VAMP2** (Noé group) | Discretize state space, fit transition matrix at lag `τ` | Markovian by construction — chooses `τ` large enough that it looks Markov | Moderate | Standard pipeline. But the "choose `τ` large enough" is an ad-hoc way of hiding the memory. |
| **MEMnets** (Huang group, 2024, https://www.nature.com/articles/s43588-025-00815-8) | CV discovery by minimizing time-integrated memory kernel via NN encoders | Partially rigorous — uses generalized master equation formalism | Moderate — fits within existing MD data | Demonstrated on FIP35 WW + RNA polymerase clamp opening. Could plausibly be tried on TrpB O→C directly. |

For TrpB specifically my honest read: doing end-to-end GLE extraction on a 400-residue ligand-bound enzyme is a research project in itself, not a plug-in. The likely tractable subtasks are (i) a 1D kernel along the path CV `s(R)`, and (ii) a Markovianity diagnostic (autocorrelation vs. transition-path time distribution) on the metadynamics trajectory. Both are feasible with what we already have.

---

## 06.7 What I can actually contribute

Honest inventory. I'm a UNC undergrad with one TrpB replication under my belt. I am not going to train a new neural operator architecture between now and September. What I can do:

1. **Provide ground-truth metadynamics data** on TrpB O→C at a resolution useful for memory-kernel extraction. The well-tempered MetaD I'm debugging gives biased trajectories; unbiased reweighted histories along `s(R)` are usable input for GLE fitting (see Vroylandt 2022 methods).
2. **Quantify autocorrelation decay and TPT distributions** for `s(R)` and `z(R)` in the conventional-MD trajectory. This is the Markovianity diagnostic Hummer's group formalized (Berezhkovskii and Makarov, JPCL 2018, https://pubs.acs.org/doi/10.1021/acs.jpclett.8b00956). It gives a number — is TrpB's conformational coordinate Markov or not? — that would go straight into any downstream coarse-graining decision.
3. **Benchmark existing memory-kernel tools** (VolterraBasis, GLE_AnalysisEM, MEMnets) on TrpB data. I can install, run, and report. This is genuinely useful: most of these codes have only been tested on peptides.
4. **Literature mapping** — exactly what this chapter is. Knowing the space matters for an undergrad who's joining a research group.

What I should NOT claim I can do: train a new NO, propose a new architecture, or make clean theoretical claims about Mori-Zwanzig for large enzymes. Flagging this honestly in the meeting is better than overstating.

---

## 06.8 Videos and tutorials

Lengths are approximate. If a URL breaks, YouTube-search the exact title.

**Neural operators (Anandkumar-sphere)**
- Anandkumar, "Neural operator: A new paradigm for learning PDEs", March 2021, ~60 min — https://www.youtube.com/watch?v=Bd4KvlmGbY4. Best single intro to FNO and function-space framing in her own voice. Watch first.
- Anandkumar, "AI Accelerating Science: Neural Operators on Function Spaces", April 2023, ~50 min — https://www.youtube.com/watch?v=xgVbWVOAHTY. More recent, covers weather/fluids applications.
- Anandkumar talks playlist — https://www.youtube.com/playlist?list=PLVNifWxslHCDBMTlTpZlHymOhPtchk9mz.

**DeepONet perspective**
- Karniadakis / Lu, "DeepONet: Learning nonlinear operators…", MIT CBMM 2020, ~70 min — https://www.youtube.com/watch?v=1bS0q0RkoH0. Good for contrasting theory lineage (Chen & Chen 1995 vs. Anandkumar integral-operator approach).

**Mori-Zwanzig / ROM**
- I could not pin down a single definitive YouTube lecture. Search YouTube for "Panos Stinis Mori Zwanzig operator learning" — Stinis (PNNL) leads the operator-learning thrust of SEA-CROGS and ties MZ to DeepONet explicitly. Textbook: Chorin & Hald, *Stochastic Tools in Mathematics and Science* (2013), ch. 6 — no YouTube substitute.

**ML for molecular dynamics**
- Frank Noé, "Advancing molecular simulation with deep learning", IPAM Jan 2023, ~60 min — https://www.youtube.com/watch?v=JZjeFBH0Jl4. VAMPnets, deep MSMs, Boltzmann generators. The ML-for-MD baseline; clarifies where Markov is still the default assumption.

**Amin's own context**
- Tavakoli's "Capturing Protein Dynamics" (abstract at amintavakol.github.io) — sequence → dynamic-aware representation → design. Non-Markovian memory fits naturally if the representation is a time-history embedding.
- Arnold/Anandkumar tryptophan synthase paper, Nat. Comm. 2026 (https://www.nature.com/articles/s41467-026-68384-6) — likely why TrpB is on the lab's radar.

**Suggested prep order (~4 hours)**: Anandkumar 2021 FNO talk → Karniadakis DeepONet talk → Noé IPAM 2023 → Ayaz 2021 + Dalton 2023 abstracts+figures → MemNO abstract+intro.

---

## 06.9 If someone asks me X, I say Y

**Q: "Why is protein dynamics non-Markovian?"**
A: Coarse-graining traces out hidden DOFs. By Mori-Zwanzig, any projection of a Markov system generically produces a GLE with a non-trivial memory kernel. All-atom MD on a small peptide: memory time can be sub-ps. Folding coordinates of chignolin / λ-repressor (Dalton 2023): memory time runs into ns and changes folding rates by up to 10×.

**Q: "So is a Markovian model just wrong?"**
A: Depends on the question. For equilibrium structure, MSMs work — you only need the stationary distribution. For kinetics (rates, transition paths), Ayaz data say memory is required to fit both folding AND unfolding times; one Markov model cannot.

**Q: "How do people estimate the kernel from MD?"**
A: Two families. (1) Volterra inversion of correlation functions (Vroylandt-Monmarché 2022) — robust, careful discretization. (2) Max-likelihood with hidden auxiliary variables (Vroylandt PNAS 2022) — sample-efficient, code is GLE_AnalysisEM. Ayaz/Netz use direct GLE inversion on long Anton trajectories.

**Q: "How much data does it take?"**
A: 1D CV on a peptide: ~1 μs explicit-water. Fast folders (Dalton 2023): 100 μs – 3 ms on Anton. A 400-AA ligand-bound enzyme with a 10 kcal/mol barrier: not done. Requires enhanced sampling — exactly why metadynamics is a natural input pipeline.

**Q: "What's a neural operator, why does Anima care?"**
A: A NN generalized to map between function spaces. Signature property: discretization invariance. FNO parameterizes the integral kernel in Fourier space (Li/Kovachki/Anandkumar 2020, arXiv:2010.08895). Matters because PDEs, parametric PDEs, and dynamical systems are intrinsically infinite-dimensional — the function-space framing makes that explicit.

**Q: "How does that connect to MZ?"**
A: The MZ memory term is an integral operator on the history of the coarse variable. Exactly what a neural operator parameterizes. MemNO (Buitrago Ruiz/Marwah/Gu/Risteski 2024, arXiv:2409.02313) combines FNO with a state-space model (S4) for time-dependent PDEs with memory and cites MZ explicitly. Translating the idea to protein CVs — NO-parameterized `K(τ)` along a reaction coordinate, then integrate the GLE — is a logical next step. As far as I can tell, not yet published for proteins.

**Q: "Is this what you'd work on for SURF?"**
A: I'd aim for what I can finish. Plan: (i) clean metadynamics trajectories on TrpB suitable for GLE extraction; (ii) Markovianity diagnostic (autocorrelation + TPT distribution, Berezhkovskii-Makarov 2018) to quantify how non-Markov TrpB's O→C coordinate is; (iii) benchmark VolterraBasis / GLE_AnalysisEM / MEMnets on that data. Doable by a motivated undergrad. Training a new Memory Neural Operator is not — I'd be upfront.

**Q: "Why TrpB vs. chignolin?"**
A: TrpB has a ligand (PLP) and an experimentally meaningful conformational switch (COMM O→C) tied to catalysis. Interesting for combining dynamics with design (Arnold-Anandkumar TrpB paper, Nat. Comm. 2026). Chignolin is solved — memory kernels already characterized. TrpB would be harder, more scientifically useful.

**Q: "What would break?"**
A: Most likely failure: `s(R)` isn't a good reaction coordinate for TrpB in the Markov sense because COMM closure couples to PLP state and ligand rearrangements not captured by 112 Cα atoms. Memory kernel on `s(R)` alone would inherit those missing DOFs as colored noise. Fix: 2D `(s, z)` kernel, or add ligand CVs in PLUMED — doubles the data cost.

---

## Sources

Papers:
- Vroylandt et al. 2022, PNAS — https://www.pnas.org/doi/10.1073/pnas.2117586119
- Vroylandt & Monmarché 2022, J. Chem. Phys. — https://arxiv.org/abs/2201.02457
- Ayaz et al. 2021, PNAS — https://www.pnas.org/doi/10.1073/pnas.2023856118
- Dalton et al. 2023, PNAS — https://www.pnas.org/doi/10.1073/pnas.2220068120
- Dalton et al. 2025, PNAS (hierarchical friction) — https://www.pnas.org/doi/abs/10.1073/pnas.2516506123
- Kiefer/Netz JCTC 2024 (accurate kernel extraction) — https://pubs.acs.org/doi/10.1021/acs.jctc.3c01289
- Berezhkovskii & Makarov JPCL 2018 (Markovianity test) — https://pubs.acs.org/doi/10.1021/acs.jpclett.8b00956
- Li et al. FNO 2020 — https://arxiv.org/abs/2010.08895
- Kovachki et al. Neural Operator 2021 — https://arxiv.org/abs/2108.08481
- Lu et al. DeepONet 2021 — https://www.nature.com/articles/s42256-021-00302-5
- Li et al. Markov Neural Operator — https://github.com/neuraloperator/markov_neural_operator
- Buitrago Ruiz et al. MemNO 2024 — https://arxiv.org/abs/2409.02313
- Lin & Lu, SIAM J. Appl. Dyn. Sys. 2021 — https://epubs.siam.org/doi/10.1137/21M1401759
- Lei/Baker/Li PNAS 2016 — https://www.pnas.org/doi/10.1073/pnas.1609587113
- MEMnets, Nature Comput. Sci. 2025 — https://www.nature.com/articles/s43588-025-00815-8
- Jung/Hanke/Schmid MZ review — https://arxiv.org/html/2503.20457v2

Code:
- GLE_AnalysisEM — https://github.com/HadrienNU (Zenodo DOI 10.5281/zenodo.5536561)
- VolterraBasis — https://github.com/HadrienNU/VolterraBasis
- MEMnets — https://github.com/xuhuihuang/memnets
- neuraloperator — https://github.com/neuraloperator/neuraloperator
- DeepONet — https://github.com/lululxvi/deeponet

Videos (search YouTube if URL breaks):
- Anandkumar 2021 FNO talk — https://www.youtube.com/watch?v=Bd4KvlmGbY4
- Anandkumar 2023 AI for Science — https://www.youtube.com/watch?v=xgVbWVOAHTY
- Karniadakis/Lu DeepONet CBMM 2020 — https://www.youtube.com/watch?v=1bS0q0RkoH0
- Frank Noé IPAM 2023 — https://www.youtube.com/watch?v=JZjeFBH0Jl4
