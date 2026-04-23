---
name: round3_external_verification
description: Round 3 external verification — direct paper grep + web search to resolve U1–U6 unresolved questions from Round 2.
type: review
---

# Round 3 — External Verification

Method: targeted grep on `.zotero-ft-cache` (full paper text) + web search for prior art. No charity to the paper — adversarial reading.

---

## U1 — Are baselines trained with stride randomization?

**Resolved: NO.**

From §F (lines 621–622 of cache):
- **AlphaFolding**: *"fixed time step of 10 ps, which differs from our model's variable stride capability. Generated trajectories were sub-sampled to match the frame rates required for evaluation."*
- **MDGen**: *"trained on ATLAS trajectories preprocessed with 400 ps intervals (stride 40 with base interval 10 ps)"* — **single fixed stride.**

**Implication**: STAR-MD's Δt ∼ LogUniform[10⁻², 10¹] ns gives it a unique structural advantage when the evaluation requires arbitrary stride. AlphaFolding has to iterate at 10 ps to reach 100 ns (10⁴ steps); MDGen is locked at 400 ps. Both accumulate compounding error precisely because their training never exposed them to the strides at which they are evaluated.

**This is the single most damaging fairness finding of the whole review.** It does not mean STAR-MD is wrong; it means the comparison numbers in Tables 1, 2 are partly an artifact of training-distribution coverage, not architectural superiority. The honest framing would be: *"variable-stride training is the architectural advantage; baselines without this property cannot be expected to match."* The paper does not frame it this way.

---

## U2 — Memory-kernel literature on proteins (uncited prior art)

**Resolved: Major uncited prior art exists.**

Verified via web search (PubMed / PNAS):
- **Ayaz, Scalfi, Dalton, Netz, "Non-Markovian modeling of protein folding," PNAS 118 e2023856118 (2021)** — directly **extracts memory kernels from MD** for 8 fast-folding proteins along the Q (native-contact fraction) reaction coordinate. Concludes friction (memory-dependent) is more influential than free-energy barriers in folding rates.
- **Dalton, Ayaz, Netz, "Fast protein folding is governed by memory-dependent friction," PNAS 120 e2220068120 (2023)**.
- Related: position-dependent memory kernels (PRE 2022), nonlinear PMF + memory friction (PRE 2022).

STAR-MD's bibliography (cache lines 222, 240) cites only:
- Mori, *Prog. Theor. Phys.* 33, 423 (1965) — original MZ formalism.
- Zwanzig, *Phys. Rev.* 124, 983 (1961) — original memory-effects paper.

**No citation to the actual protein-dynamics MZ literature.** This is striking because:
1. The paper invokes MZ specifically as motivation *for protein-structure prediction*.
2. There is a directly-relevant body of work (Netz group, ~5 years, multiple PNAS papers) that **measures** the memory kernel they hand-wave about.
3. Citing Ayaz/Dalton would force the paper to confront that the memory kernel is *measurable* — and they never measure it.

**Adversarial interpretation**: omitting this literature lets the paper use MZ as decoration without engaging with the field that has done the work. This is reviewer ammunition.

---

## U3 — Is the OpenFold contribution ablated?

**Resolved: NO ablation found.**

From cache lines 57, 609:
- *"frozen OpenFold FoldingModule for sequence-level single-residue and pairwise features s, z = {si, zij}"*
- *"STAR-MD takes as input the pre-trained pairwise features from a frozen OpenFold model. Then, it employs a FrameEncoder module Shen et al. [26] which incorporates pairwise geometric information into the pair features."*

The FrameEncoder itself is borrowed from Shen et al. 2025 (ConfRover, same group). No experiment isolates how much of STAR-MD's accuracy comes from:
- the frozen OpenFold prior,
- the borrowed FrameEncoder,
- vs. the new joint S×T diffusion blocks.

**Implication**: any "joint S×T attention is necessary" claim is co-mingled with a strong static structural prior the paper doesn't disentangle. A separable-attention model **on the same OpenFold prior** still scores 86–88% CA validity (Table 3). The marginal contribution of the joint attention to validity is *negative*; to dynamics-coverage metrics it is positive but modest.

---

## U4 — Actual loss function

**Resolved: 7-term composite loss, not pure score-matching.**

Table 10 (cache line 676) lists the loss weights:

| Term | Weight | Active when |
|------|--------|-------------|
| Rotation score loss | 0.5 | always |
| Translation score loss | 1.0 | always |
| Torsion loss | 0.5 | always |
| Backbone FAPE loss | 0.5 | always |
| Sidechain FAPE loss | 0.5 | always |
| Backbone coordinates loss | 0.25 | diffusion t ≤ 0.25 |
| Backbone distance map loss | 0.25 | diffusion t ≤ 0.25 |

**This is consequential.** Pure score-matching would be the rotation/translation score terms only. The remaining five terms — FAPE × 2, torsion, coordinates, distance map — are **AlphaFold-style auxiliary structural-fidelity losses** that strongly bias the model toward emitting native-like geometry. The coordinates/distance-map terms are even gated to fire only at low diffusion noise (t ≤ 0.25), i.e., near the clean structure.

**Implication**: the validity numbers (Tables 1, 2, 3) are partly the *direct consequence of the loss design*. The model is explicitly trained to emit AlphaFold-quality structures at every step. The "dynamics fidelity" claims live on top of a static-fidelity scaffold the paper doesn't credit.

This also reframes the AlphaFolding baseline comparison: STAR-MD inherits five of AlphaFold's loss terms; AlphaFolding is by construction operating in the same regime. The validity gap is partly *which auxiliary losses survive what evaluation horizon*, not architecture per se.

---

## U5 — Is the memory kernel ever measured?

**Resolved: NO.**

Grep across cache for `memory kernel|memory function|GLE|generalized Langevin|Mori|Zwanzig` returns:
- §3.4 main text (motivation paragraphs)
- §A.2 appendix (Proposition 1 + proof)
- Bibliography entries

**No empirical measurement** of the memory kernel from oracle MD trajectories, anywhere. No fit. No sanity-check that the architecture's effective memory matches what MZ predicts. The kernel is invoked, projected (Schur complement), shown to inflate, then dropped.

**Combined with U2**: the paper invokes a formalism whose protein-specific empirical literature it does not cite, and never instantiates the central object (the kernel) of that formalism.

---

## U6 — AlphaFolding's 0.11% all-atom validity at 100 ns

**Partial — likely a compounding-error artifact.**

§F states AlphaFolding has a 10 ps native step and sub-sampled to match evaluation cadence. For a 100 ns benchmark this is on the order of **10⁴ autoregressive steps** vs. the model's 16-frame block-size training context (which Adversary's R1 memo flagged). Models trained with limited block size and no contextual-noise stability trick (which is STAR-MD's specific innovation) can compounding-error their way to near-zero validity. This is consistent with the 0.11% number being a *predictable extrapolation failure*, not a fundamental limit of AlphaFolding's design.

The honest framing would be: "AlphaFolding is not designed for this horizon — running it here illustrates the problem we tackle, not a benchmark of its architectural ceiling." The paper presents the number without that caveat.

**Status**: leave at MEDIUM confidence; not a smoking gun, but consistent with baseline-misuse pattern.

---

## Bonus finding — 10 μs experiment exists in supplement

Cache lines 1144–1145: *"To probe the limits of STAR-MD's stability, we generated trajectories using the maximum training stride (∼10 ns) for 1000 steps, resulting in a total simulation time of approximately 10 μs. Table 20 reports the structural validity metrics averaged over the full 10 μs trajectory…"*

So the actual extrapolation extreme is 10 μs, not 1 μs. Importantly, this is **stability-only** — only structural validity, no JSD/Recall/dynamics metrics. This is an honest framing: the model stays stable far past its training horizon, which is a genuine engineering result. It does **not** support a claim that the dynamics at 10 μs are physically meaningful.

---

## Summary of Round 3 evidence shifts

| Round-2 ID | Status after R3 | Severity for paper |
|-----|-----|-----|
| U1 baselines stride | Confirmed unfair | **Critical** — undercuts headline comparison |
| U2 Ayaz/Netz uncited | Confirmed major omission | High — easy reviewer hit |
| U3 OpenFold ablation | Confirmed missing | High — confounds joint-attn claim |
| U4 loss form | Confirmed multi-term | **Critical** — reframes validity claims |
| U5 kernel measurement | Confirmed absent | High — confirms MZ is decoration |
| U6 AlphaFolding 0.11% | Likely artifact | Medium |

Combined effect: the paper's strongest engineering claims (singles-only KV cache, contextual noise, length extrapolation via 2D-RoPE + Δt conditioning) **survive** scrutiny. The paper's *theoretical framing* (MZ → joint S×T attention) and *competitive framing* (catastrophic baseline failure) are substantially weakened.
