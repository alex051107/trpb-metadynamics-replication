# STAR-MD — Round-1 Technical Reverse-Engineering Memo
**Reviewer role:** Technical Reverse Engineer
**Paper:** Shoghi, Liu, Shen, Brekelmans, Li, Gu. *Scalable Spatio-Temporal SE(3) Diffusion for Long-Horizon Protein Dynamics.* arXiv 2602.02128v2 (12 Feb 2026).
**Evidence:** text cache `.zotero-ft-cache`, line-indexed.

All statements below are tagged `[EXPLICIT, §/Table/p.]` when drawn verbatim from the paper, or `[INFERRED — reason]` when I am reconstructing. I deliberately do NOT smooth over missing numbers.

---

## 1. Architecture — block diagram in words

**Top-level pipeline (Fig. 1 + §3.2):** frame-by-frame autoregressive diffusion. For each frame `l`, the input to the main model is the *concatenation of clean history frames `x_{<l}`* (after small context noise perturbation, §3.3) *and the current noisy frame `x_l^τ`*, plus protein sequence features. The model outputs an updated backbone (T, R) that, at the final diffusion step, becomes the clean frame and is appended to history. [EXPLICIT §3.1–3.3]

**Input feature tensors (§3.2 "Input Module" + App. G Table 7):**
- A *frozen* OpenFold FoldingModule produces time-independent single `s ∈ R^{N×d_s}` and pair `z ∈ R^{N×N×d_z}` features from sequence (d_s = 384, d_z = 128 per Table 7). [EXPLICIT §3.2, App. E, Table 7 p.28]
- Per-frame, these are concatenated with amino-acid metadata and *pairwise Cβ distances* to produce time-dependent `s_l^init, z_l^init`. [EXPLICIT §3.2]
- Context length during training: `L = 8` frames, frame intervals sampled as `1…2^10 × 10 ps` snapshots (i.e., 10 ps–10.24 ns stride). [EXPLICIT Table 7 p.28]

**Main block stack ("diffusion blocks", §3.2).** Each block (there are 4 blocks, Table 9) contains:
1. **Invariant Point Attention (IPA) [Jumper 2021]** — 1 IPA layer per block, updates `s_l` using `z_l` and the noisy rigid frame `x_l^τ`. *This step is independent per frame* (no cross-time attention here). [EXPLICIT §3.2 item 1 + Table 9]
2. **Joint Spatio-Temporal Attention ("S×T")** — 2 layers per block (Table 9). This is the key novelty: attention over tokens indexed by `(residue i, frame l')` for all `l' ≤ l`, with 2D Rotary Position Embedding (2D-RoPE, Heo et al. 2024) encoding both residue index and frame index. [EXPLICIT §3.2, Table 9 p.29]
3. **EdgeTransition update to `z_l`** — local MLP `z_ij ← z_ij + MLP(s_i, s_j, z_ij)`, *not* triangular attention. This is Jumper et al.'s EdgeTransition layer. [EXPLICIT App. E p.25, eq. (33)]
4. **Backbone (rigid) update to `x_l^τ`** via an MLP that predicts translation and rotation updates from `s_l`. [EXPLICIT §3.2 item 3]

After stacking all blocks, the final coordinate update is used as the score-network output for denoising score matching. [EXPLICIT §3.2]

**"Joint" vs. "factored (S+T)" attention.** Factored variants do spatial attention across residues within each frame, then temporal attention across frames per channel (or vice versa); tokens are never mixed. STAR-MD's S×T flattens the (N·L) residue-frame tokens into a single attention layer, so any `(i, l)` token can attend to any `(j, l')` token with `l' ≤ l`. 2D-RoPE disambiguates residue vs. frame index. [EXPLICIT §3.2 "Joint Spatio-Temporal Attention", App. B.2.3]

**Where causality is enforced (§3.3 "Block-causal Attention"):** during training, clean history `x_{<l}` and noisy frames for *all* positions `l` are concatenated into one doubled-length sequence; a block-wise mask prevents noisy frames from being attended to by any earlier-or-equal-index clean frame. This mirrors block-diffusion language models [Arriola et al. 2025] and is how teacher-forcing is parallelized. At inference, the clean-frame KV cache is populated once per generated frame. [EXPLICIT §3.3]

**Input tensor shape at the S×T attention layer:** `[B, L_total, N, d=256]` where `L_total ≈ 2L` during training (clean||noisy concat) and `L_total = L_context + 1` at inference. [INFERRED from §3.3 "doubling the sequence length" + Table 9 hidden dim 256.]

---

## 2. Diffusion formulation

Translations and rotations are diffused *independently* on SE(3) [Yim 2023, Wang 2024] — eq. (1)–(2) §3.1 p.3:

```
T_τ = √α_τ · T_0 + √(1 − α_τ) · ε,    ε ~ N(0, I_{3N})     (eq. 1)
R_τ ~ IGSO3(R_0, σ_τ²)                                      (eq. 2)
```

- Translation: variance-preserving (VP) Gaussian noise with linear schedule `b_min/b_max = 0.1/20.0` (Table 8 p.28). Coordinate scaling factor 0.1 before diffusion.
- Rotation: isotropic Gaussian on SO(3) with *logarithmic* schedule `σ_min/σ_max = 0.1/1.5`. [EXPLICIT Table 8 p.28]

**Parametrization.** A denoising *score network* `s_θ = [s_θ^T, s_θ^R]` is trained by *denoising score matching* to predict the score (i.e., score-matching, **not** plain ε-prediction). [EXPLICIT §3.1 eq. 3 p.4] — the text says "trained via denoising score matching to predict the noise added to both components", which in the SE(3)-diffusion literature (Yim 2023) is equivalent to score prediction on T and ε-style noise on R via IGSO3. I read it as score-matching. [INFERRED — the paper does not write the loss equation explicitly.]

**Sampling.** Euler SDE reverse process, 200 diffusion steps, `t_max/t_min = 1.0/0.01`. [EXPLICIT Table 8 p.28]

**Loss (Table 10 p.29):** multi-term, with weights
- rotation score loss 0.5,
- translation score loss 1.0,
- torsion loss 0.5,
- backbone FAPE 0.5,
- sidechain FAPE 0.5,
- backbone-coordinate loss 0.25 (*only at diffusion t ≤ 0.25*),
- backbone distance-map loss 0.25 (*only at diffusion t ≤ 0.25*).

The exact closed-form of each term is *not reported* — the paper cites Shen et al. 2025 (ConfRover) for the loss setup. [EXPLICIT Table 10 but formulas NOT REPORTED in-text.]

**Context-noise training:** during every training step, history frames are perturbed with `τ ~ U[0, 0.1]` via the same forward process (eqs. 1–2) before serving as clean conditioning. Probability of sampling clean noise: 0.75 (Table 7 "Clean noise sampling prob"). At inference the *identical* perturbation is applied to every newly generated frame before it becomes history. [EXPLICIT §3.3 "Contextual Noise Perturbation", Table 7]

**Continuous-time physical conditioning:** the physical stride Δt is drawn `~ LogUniform[10⁻² , 10¹] ns` per training example, fed via AdaLN (Peebles & Xie 2023) jointly with diffusion progress τ. [EXPLICIT §3.3]

---

## 3. SE(3) equivariance

- **Frame-level representation:** each residue is a rigid backbone frame (T_i ∈ R³, R_i ∈ SO(3)) plus side-chain torsions. [EXPLICIT §3.1 + §4.1 "All models parametrize proteins using SE(3) backbone rigids with torsional angles for side-chain atoms."]
- **Where equivariance is enforced:** (a) IPA layers (Jumper 2021) inside each diffusion block — IPA is by construction SE(3)-invariant on singles while using rigid frames for geometric attention. [EXPLICIT §3.2 item 1.] (b) Diffusion on SE(3) with IGSO3 on SO(3). (c) Pair features encode *Cβ distance* (rotation/translation invariant). (d) The S×T attention operates on single-residue features which are invariant outputs of IPA; 2D-RoPE encodes only indices, not coordinates — so S×T is invariant. [INFERRED — the paper does NOT call S×T "equivariant"; it relies on IPA for all geometric equivariance, and S×T acts on scalar features.]
- No mention of tensor field networks, e3nn, frame-averaging, or explicit ITA. The equivariance machinery is exactly IPA + SO(3)-diffusion, i.e. same family as FrameDiff / ConfRover / AlphaFolding. [INFERRED from references §3.1 citing 26, 31, 36.]

---

## 4. Training pipeline

### Dataset
- **ATLAS** [Vander Meersche 2024]: 1390 proteins, triplicate 100 ns trajectories, snapshots every 10 ps. [EXPLICIT §4.1 + App. C p.22]
- Time-based split (cutoffs 1 May 2018 / 1 May 2019) following prior work [Jing 2024 / Shen 2025]. Training proteins > 384 AA are excluded → **1080 training proteins**. [EXPLICIT App. C]
- Validation/test counts NOT explicitly reported in main text; test set = 82 proteins (implied from Table 1 footnote "AlphaFolding results are evaluated on 78/82 proteins"). [INFERRED from Table 1 footnote 1, p.7.]
- **Extended benchmarks:** new MD runs (GROMACS 2023.2 on V100 40 GB, same ATLAS protocol) for 250 ns on 32 proteins and 1 μs on 8 proteins — for evaluation only, *not* training. [EXPLICIT §4.3 + App. F]

### Conditioning
- Protein sequence (frozen OpenFold FrameEncoder produces time-independent s, z). [EXPLICIT §3.2]
- Starting conformation x_0 at t=0 (Fig. 1, §3.1). [EXPLICIT Fig. 1]
- Physical stride Δt via AdaLN. [EXPLICIT §3.3]
- History frames `x_{<l}` (noise-perturbed) through S×T attention. [EXPLICIT §3.3]

### Batch construction
- Context length L = 8 frames per trajectory snippet. [EXPLICIT Table 7]
- Frame-interval sampling: pick uniform integer k ∈ {1,…,2^10}, then take every k-th 10 ps snapshot, giving physical strides 10 ps – 10.24 ns. [EXPLICIT Table 7]
- Global batch size = 1 per Table 7 "Global batch size 1", but §G opening text says "global batch size of 8". These contradict. [EXPLICIT — Table 7 says 1, narrative says 8. REPORTED INCONSISTENCY; cannot resolve without authors.]
- Frame-level noise sampling (prob 0.75 a random "clean noise magnitude ≤ 0.1" per frame). [EXPLICIT Table 7]

### Optimizer & schedule
- Adam. [EXPLICIT Table 10]
- LR = 2 × 10⁻⁴ (Table 10) — but §G body text says "5 × 10⁻⁵". These also contradict. [EXPLICIT INCONSISTENCY, Table 10 vs §G first paragraph p.28.]
- Linear warmup + cosine decay, 5 warmup epochs, 250 total epochs, warmup start LR factor 0.01, min LR factor 0.1, gradient-norm clip 1.0, BF16 mixed precision. [EXPLICIT Table 10]
- DeepSpeed Stage-2 ZeRO + gradient checkpointing. [EXPLICIT §G]

### Hardware & compute
- 8× NVIDIA H100 80 GB for training. [EXPLICIT §G]
- Inference eval on a single H100 80 GB (§App. F p.26 + Table 21 p.45).
- **Wall-clock training time / GPU-hours / FLOPs: NOT REPORTED.**

---

## 5. Inference / autoregressive rollout

### Frame generation
- For each new frame `l`: 200 Euler SDE denoising steps [Table 8] over the concat(history, x_l^τ) sequence; the final updated backbone is the clean `x_l`, then perturbed with τ ∈ U[0, 0.1] before being appended to history. [EXPLICIT §3.3]
- KV cache of *single-residue* features only (no pair-feature cache). [EXPLICIT §3.2 + §B.4]

### Task configurations (Table 4 p.22)
| Task | Stride | # frames |
|------|--------|----------|
| 100 ns | 1.2 ns | 80 |
| 240 ns | 1.2 ns | 200 |
| 1 μs   | 2.5 ns | 400 |

Plus a stress-test: 1 μs at 1.2 ns stride (~833 frames, §4.4 Fig. 4), and a 10 μs extreme-horizon test at ~10 ns stride for 1000 steps (App. I.2 Table 20).

### Forward passes per trajectory
- Each frame = 200 diffusion steps × number of frames = **16,000 forward passes for 100 ns**, **40,000 for 240 ns**, **80,000 for 1 μs @ 2.5 ns stride**, **200,000 for the 10 μs stress test**. [INFERRED: §3.2 + Table 8 give 200 steps; Table 4 gives frame counts.]
- Wall-clock (Table 21 p.45): 766 – 1381 s for 100 ns on a single H100 across 51–724 AA proteins, vs 6.3k – 78.5k s for OpenMM-implicit-solvent MD → speedup 8×–57×. NOT REPORTED: wall-clock for 240 ns, 1 μs, or 10 μs runs.

### Memory growth with horizon
- **Claim:** singles-only KV cache grows as `O(N·L·d)` bytes per layer. [EXPLICIT §B.4 p.20] At `N=200, L=32, d=256, 4 B/entry` → 6.6 MB per layer, vs ConfRover's `O((N+N²)·L·d) ≈ 1.3 GB`. [EXPLICIT §B.4 eqs. 24–29]
- Full KV cache in GPU memory, no CPU offload, no sliding window. [EXPLICIT §4.4 KV Cache Analysis + App. F "ConfRover-W"]
- KV cache size as function of L and N is plotted in Fig. 5 p.9 — STAR-MD stays below 10 GB out to L=800 frames and N=1000 residues. [EXPLICIT Fig. 5]

### How 240 ns / 1 μs rollouts are produced
- For variable-stride models (STAR-MD, ConfRover), trajectories are generated *directly* at the required stride; no re-splicing. [EXPLICIT §4.1]
- MDGen generates in blocks of 250 frames × 400 ps = 100 ns per rollout, then chained via `num_rollouts` → discards memory between blocks. [EXPLICIT §App. F]
- AlphaFolding: blocks of 16 frames @ 10 ps = 160 ps each, re-conditioned on the tail of the previous block. [EXPLICIT App. F]
- STAR-MD: *one continuous rollout* with KV-cache retention of all prior single-residue tokens. [EXPLICIT §2 "follows this approach [ConfRover] to avoid the 'memory break'", §4.4]

---

## 6. Complexity claims

- **Derived.** Complexity arguments are given formally in §B p.19–21 with explicit operation counts, not just asserted.
- Full S×T attention on singles: `O(N²L²)` per layer — derived from flattening (N·L) tokens into one attention map. [EXPLICIT §B.2.3 eq. and p.20]
- Full theoretical S×T on singles + pairs: `O(L²N⁴)` (prohibitive). [EXPLICIT §B.2.1 eq. 21]
- ConfRover: `O(N³L + (N+N²)L²)` total (Pairformer + channel-factorized temporal). [EXPLICIT §B.2.2]
- S+T on singles only (hypothetical baseline): `O(N³L + NL²)`. [EXPLICIT §B.3]
- Crossover `L ≈ N²/(N−1) ≈ N`, so for realistic N ≫ L STAR-MD wins via absence of cubic term. [EXPLICIT §B.3 eq. 22–23]
- **KV-cache memory:** singles only `O(N·L·d)` vs ConfRover `O((N+N²)·L·d)`. Ratio quoted at ~196× reduction at N=200, L=32. [EXPLICIT §B.4]

Comparison to claimed "memory bottlenecks": the bottleneck avoided is explicitly the *pair-feature KV cache* that forced ConfRover into CPU offload or windowing. [EXPLICIT §4.3, §4.4, Fig. 5] — this is consistent with their derivation.

The `O(N²L²)` is still quadratic in both N and L; the paper is honest that STAR-MD is *not* sub-quadratic. [EXPLICIT §B.5 p.21–22.]

---

## 7. Notation map (symbols introduced)

| Symbol | Definition | Intro page |
|--------|------------|------------|
| `x_{1:L}` | trajectory of L protein conformations | §3.1 p.3 |
| `Δt_l` | physical time interval between frame l and l−1 | §3.1 p.3 |
| `x = [T, R]` | SE(3) conformation: translations T ∈ R^{3N}, rotations R ∈ SO(3)^N | §3.1 p.3 |
| `N` | number of residues | §3.1 p.3 |
| `τ` (tau) | diffusion time | §3.1 p.4 |
| `α_τ` | VP noise schedule for translations | eq. 1 p.4 |
| `σ_τ²` | IGSO3 variance for rotations | eq. 2 p.4 |
| `ε` | Gaussian noise N(0, I_{3N}) | eq. 1 p.4 |
| `s_θ = [s_θ^T, s_θ^R]` | score network head | eq. 3 p.4 |
| `c` | conditioning input — here `c(x_{<l}^0, x_l^τ, τ)` | §3.1 p.4 |
| `s_l ∈ R^{N×d_s}` | per-residue ("singles") feature at frame l, d_s=384 | §3.2 p.4, Table 7 |
| `z_l ∈ R^{N×N×d_z}` | pairwise feature at frame l, d_z=128 | §3.2 p.4, Table 7 |
| `s_l^init, z_l^init` | initial time-dependent inputs after FrameEncoder | §3.2 p.4 |
| `L` | context / trajectory length in frames | §3.1 p.3 & §4.1 |
| `Γ(t)` | full-phase-space state in MZ formalism | §A.2.1 p.16 |
| `P` | projection operator | §A.2.1 p.16 |
| `A(t)` | projected (coarse-grained) state | §A.2.1 |
| `L` (calligraphic) | Liouville operator | eq. 4 p.16 |
| `K(t)` | memory kernel | eq. 5 p.16 |
| `F(t)` | random force term | eq. 5 p.16 |
| `Ω_{ss}, Ω_{sz}, Ω_{zs}, Ω_{zz}` | block-structured Markovian dynamics matrices | eq. 6 p.17 |
| `K̃^{(1)}, K̃^{(2)}` | Laplace-domain memory kernels for singles-and-pairs vs singles-only | §A.2.3 p.17 |
| `p` | Laplace variable | eq. 8 p.17 |
| `h` (used implicitly in Eq. (8)) | identity / grouping bracket | eq. 8 p.17 |
| `C_{00}, C_{0τ}, C_{ττ}` | instantaneous/lagged covariance matrices for VAMP-2 | eq. 32 p.23 |
| `M ∈ {0,1}^L` | validity mask for tICA | §D p.23 |
| `r_k` | per-PC tICA correlation | §D p.23 |

`h_l^i` (queried in the task brief) is **not introduced by the paper** — that is a canonical transformer hidden-state notation that the authors did not use; the closest thing is `s_l^{(i)}` (residue i at frame l), which I mark [INFERRED — reader convention, not paper].

---

## 8. Implementation status

From a careful read of the PDF, references, and acknowledgments:

- **Code:** *No repository URL is given in the paper.* The project page `https://bytedance-seed.github.io/ConfRover/starmd` is mentioned on p.1 (landing page, not a repo). [EXPLICIT p.1]
- **Model checkpoints:** Not mentioned.
- **Training configs:** Tables 7–10 (App. G) give hyperparameters but no `yaml`/`json` file; notable *internal contradictions* remain (batch size 1 vs 8; LR 2e-4 vs 5e-5). [EXPLICIT §G + Tables 7, 10]
- **Dataset-prep scripts:** Only ATLAS (public) and baseline scripts (MDGen, AlphaFolding, ConfRover repos linked in App. F footnotes).
- **GROMACS .tpr files for the extended 240 ns / 1 μs runs:** "using provided equilibrated structures and Gromacs .tpr files" (§App. F) — these come from ATLAS distribution, not the authors.

**Reproduction blockers:**
1. Loss function closed forms (deferred to Shen 2025 / ConfRover paper).
2. FrameEncoder architecture details (deferred to Shen 2025).
3. Exact OpenFold checkpoint and which layers are frozen.
4. AdaLN implementation for joint (τ, Δt) conditioning — parameter tying? separate MLPs?
5. 2D-RoPE application scheme: do queries/keys each get 2D rotation, or only the temporal axis? — not stated.
6. Batch size / LR contradictions.
7. Total epochs 250 — on what global batch size? training wall-clock?
8. Seeds, early-stopping criterion, validation-loss metric: not reported.
9. Block-causal attention mask construction — described only in prose, no formula.
10. Score-matching loss weights at which diffusion-time threshold: "t ≤ 0.25" for coord + distance-map losses (Table 10) — consistent with a low-noise auxiliary regression but implementation is unspecified.

---

## 9. Inferences vs explicit claims — summary index

Everything above is tagged inline; the purely *inferred* claims are:
- ε-prediction vs. score-matching: "score-matching via DSM" [INFERRED — paper writes "trained via denoising score matching to predict the noise added"; the exact objective is not written as an equation in-text].
- S×T tensor shape `[B, L_total, N, d=256]` [INFERRED].
- Test set = 82 proteins [INFERRED from Table 1 footnote on AlphaFolding 78/82].
- S×T attention equivariance is *invariant* because it acts on scalar IPA-outputs [INFERRED — not restated in §3.2].
- # forward passes per trajectory (16k / 40k / 80k / 200k) [INFERRED: 200 × frame count].
- Meaning of `h_l^i` [NOT IN PAPER — I refuse to invent a symbol].

Everything else is `[EXPLICIT]` with a citation.

---

## Open questions for the team

1. **Loss — exact form.** Does "translation score loss 1.0" refer to ε-MSE in coordinate space (after scaling 0.1) or to a VP-SDE score-matching term with the Yim 2023 time-dependent weighting? The paper never writes the loss equation. (Round-2 target: derive the implied loss from ConfRover's code.)
2. **Hyperparameter contradictions.** Table 7 says batch size 1 and Table 10 says LR 2×10⁻⁴, but the prose in §G says batch size 8 and LR 5×10⁻⁵. Which is correct? Did the authors train two different runs and merge tables?
3. **Context length L = 8 during training — how does that reconcile with Δt spanning 10 ps to 10 ns?** With L=8 and a 10.24 ns max stride, the maximum *physical* training window is ~72 ns. How then does the model learn to extrapolate to 1 μs (≈ 14× further)? Is the AdaLN(Δt) alone sufficient, or is there curriculum / long-context fine-tuning that is *not disclosed*?
4. **What is the actual inference wall-clock for the 1 μs and 10 μs rollouts?** Table 21 reports only 100 ns. At 200 diffusion steps × 400 frames × cost ≈ 80 000 denoiser calls, naive extrapolation says ~2.8 h per 1 μs rollout for N=50, ~5 h for N=700 — is this what is observed?
5. **SE(3) equivariance of S×T attention — is it actually equivariant, or only invariant?** IPA outputs invariant scalars, so S×T is trivially invariant. But the backbone update after S×T produces new frames — does the gradient flow through IPA preserve equivariance, given that the S×T layer mixes across time? Would like a formal statement.
6. **Pair-feature z_l is still updated per block (EdgeTransition).** How does this interact with autoregressive inference — are pair updates re-done per diffusion step or cached? §B.4 says *no pair KV cache*, but the EdgeTransition still requires `z_{l−1}` for the previous clean frames. Is `z_{<l}` recomputed from scratch on each new frame?
7. **Noise schedule on rotations is logarithmic (σ_min=0.1, σ_max=1.5) — why log, and does this match Yim 2023 or a modified version?** No derivation is given.
8. **Code / weight release.** Zero mention of a repo. Is this camera-ready or withheld for a later release? Does the project page host anything beyond visualizations?
9. **Downstream use for trpB-type allosteric-tunnel dynamics (our project-relevance question).** ATLAS excludes ligand / cofactor atoms — how would STAR-MD handle PLP-bound TrpB where the cofactor is part of the collective variable? The authors only note "extend to protein complexes or small molecules" as future work (§5 "Limitations").
10. **"Block-causal" mask formal definition.** Described in prose only (§3.3). Is this identical to Arriola et al. 2025 block-diffusion mask, or modified? No pseudocode.

---

*End of engineer memo — file path (absolute):*
`/Users/liuzhenpeng/Desktop/UNC/暑研 /Caltech Interview/tryp B project/papers/reviews/starmd_team_review_2026-04-17/round1_engineer.md`
