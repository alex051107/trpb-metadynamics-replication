---
name: round2_cross_examination
description: Round 2 cross-examination across the 4 Round-1 memos. Catalogs consensus, verified disagreements (against the paper text), and questions to escalate to Round 3.
type: review
---

# Round 2 — Cross-Examination

Read order: 00_lead_anchor → round1_engineer → round1_adversary → round1_context → round1_tutor → THIS DOC.

This round does NOT produce new claims. It only does three things:
1. Catalog **strong consensus** across agents (high confidence — multiple independent reads landed on the same point).
2. Catalog **disagreements** and resolve those that can be resolved against the paper text *now*.
3. List **unresolved questions** to escalate to Round 3 (external verification / Codex hostile probe).

Page numbers refer to arXiv 2602.02128v2 (Feb 12 2026).

---

## A. Strong Consensus (≥3 agents independently)

| # | Claim | Confidence | Backed by |
|---|-------|------------|-----------|
| C1 | The Mori–Zwanzig appeal is **motivation, not derivation**. Proposition 1 is a true Schur-complement identity but it does **not** uniquely imply joint S×T attention; factored-with-depth is also a universal approximator. | High | Lead, Adversary, Context, Tutor |
| C2 | The real engineering win is the **singles-only KV cache** (O(NL) vs O((N+N²)L), §B.4 p. 21) plus continuous-time Δt conditioning + 2D-RoPE. Together they enable length and stride extrapolation cheaply. | High | Lead, Engineer, Tutor |
| C3 | **Contextual noise perturbation τ ∼ U[0, 0.1]** at both train and inference is the load-bearing stability trick (Table 3 `w/o Noise`: validity 85→76%, p. 10). | High | Lead, Engineer, Adversary, Tutor |
| C4 | **ConfRover-W is a degraded baseline** for the long-horizon comparison; full ConfRover is excluded due to OOM. Paper acknowledges (§F + Table 6 ≈ 6.3-pt CA+AA validity gap at 100 ns), but the headline framing of "catastrophic failure" of ConfRover-W on 1 μs is partly an artifact of windowing + same-group origin. | High | Lead, Adversary, Context |
| C5 | **No code or checkpoint release** is mentioned in the main text or appendix sections read. Reproduction blockers are non-trivial: hyperparameter conflicts, undescribed loss form, missing pre-training spec for FrameEncoder/OpenFold features. | High | Engineer, Adversary |
| C6 | **Validity metrics are derived from oracle-MD 99th-percentile thresholds (§D, Table 5)** — they reward *structural plausibility near equilibrium*, not *dynamics fidelity*. A model that emits near-equilibrium folded structures will look good. | High | Lead, Adversary, Tutor |
| C7 | **Long-horizon claim rests on tiny n.** 1 μs benchmark = 8 proteins; 240 ns = 32. No functional / experimental ground truth (no NMR S², no MFPT-from-spectroscopy, no kinetic comparison), only structural validity + tICA correlation as a *proxy*. | High | Lead, Adversary |

---

## B. Verified Disagreements (resolved against paper text)

### D1 — Does separable attention beat joint on validity?

- **Adversary claim**: "w/ Sep Attn" beats joint STAR-MD on CA% / AA% / CA+AA% in the 1 μs ablation (Table 13).
- **Engineer / Tutor framing**: Joint attention is the design highlight; gains in JSD/Recall/AutoCor/VAMP-2 justify it.
- **Direct paper check**:
  - **Table 3 (100 ns ablation, p. 10)**: `STAR-MD 0.42 0.57 0.17 0.09 0.02 0.12 86.62 98.28 85.18` vs `w/ Sep Attn 0.46 0.46 0.17 0.09 0.05 0.49 87.95 98.34 86.70`. **Separable wins on CA%, AA%, CA+AA% even at 100 ns.**
  - **Table 13 (1 μs ablation)**: `w/ Sep Attn` CA% 93.12 vs STAR-MD 91.00 — **separable wins again**.
- **Resolution**: Adversary is correct. The joint-vs-separable trade-off is **JSD/Recall/AutoCor/VAMP-2 ↑ for joint**, **MolProbity-style validity ↑ for separable**. Paper foregrounds the wins, omits the validity loss when discussing joint. This weakens the "joint S×T is necessary for dynamics" framing because (a) the validity-loss is consistent across horizons and (b) the dynamic-fidelity gains are modest.
- **Status**: Verified disagreement → **Adversary upheld**. Goes into "vulnerable claims" deliverable.

### D2 — Is "microsecond extrapolation" actually novel?

- **Adversary claim**: ITO (2023), Timewarp (2023), implicit transfer operators have already discussed microsecond-scale dynamics inference.
- **Context claim**: STAR-MD's real novelty is **protein size at ATLAS scale** (full ATLAS chains up to ~700 residues), not the temporal axis per se.
- **Lead view**: Trained context = 8 frames; inference = 50× context length is **architectural extrapolation**, not microsecond physics learned from data.
- **Resolution**: All three framings are compatible. The paper conflates two things:
  1. **Architectural length extrapolation** (real, demonstrated, ~14× in physical duration if max train stride ≈ 10 ns).
  2. **Long-horizon dynamics fidelity** (claimed, but n=8 and only structural-validity proxies).
  Genuine novelty axis: **scaling causal SE(3) diffusion to ATLAS-size proteins with a singles-only cache**. The "microsecond" framing is salesmanship.
- **Status**: Resolved. Treat as a **framing critique**, not a factual error. Goes into "overstated framing" deliverable.

### D3 — How damaging is the BioEmu CATH1 result?

- **Adversary claim**: BioEmu beats STAR-MD on the CATH1 free-energy benchmark (§J.1).
- **Direct paper check**: §J.1 (p. 45) explicitly says: *"BioEmu achieves higher accuracy with lower error and higher coverage."* Paper hedges with the **STAR-MD-iid** experiment (drop temporal context, train on iid frames) showing ~similar performance to STAR-MD, then concludes the gap "likely arises from factors other than the trajectory-generation architecture" — i.e., training data / pretraining differences.
- **Resolution**: Adversary is factually correct. The hedge is *plausible but unproven* — the iid experiment shows that *removing temporal context doesn't hurt much on this benchmark*, but that itself is a problem: it suggests the temporal-context machinery is not contributing where it should.
- **Status**: Verified. Use as: *"on the one head-to-head equilibrium-distribution benchmark with a stronger non-same-group baseline, STAR-MD loses, and the paper's defense is a self-ablation that arguably weakens the case for joint S×T further."*

### D4 — Hyperparameter contradictions in Appendix G

- **Engineer claim**: Table 7 (batch 1) vs §G text (batch 8); Table 10 (LR 2e-4) vs §G text (LR 5e-5).
- **Resolution**: Confirmed by Engineer's direct table reads. These are real contradictions, not transcription errors on Engineer's side. Without code, a reader cannot tell which is the actual training config used to produce Tables 1/2/3.
- **Status**: Verified. Reproduction blocker.

---

## C. Unresolved — escalate to Round 3

| ID | Question | Why it matters | How to resolve |
|----|----------|----------------|----------------|
| U1 | Are MDGen / ConfRover trained with comparable **stride randomization** to STAR-MD's Δt LogUniform? If not, the long-horizon comparison is structurally unfair (STAR-MD uniquely engineered for stride extrapolation). | Decides whether the long-horizon "win" is architecture or training-data engineering. | Codex hostile probe + check MDGen/ConfRover papers for stride-augmentation details. |
| U2 | Is there published prior art on **memory-kernel parameterization for biomolecular dynamics** (Ayaz / Dalton / Netz, PNAS 2021, 2023; Dietrich Frankenbach 2023) that STAR-MD should have cited? Context flagged this. | If memory-kernel literature is cited, the MZ rhetoric is more honest; if not, MZ is pure dressing borrowed from a community whose actual machinery the paper ignores. | Web verification of Ayaz et al. PNAS 2021/2023; check whether STAR-MD references them. |
| U3 | Does **frozen-OpenFold-features ablation** exist anywhere in the paper? Without it we can't tell what fraction of performance is the diffusion learning vs the OpenFold prior. | A large OpenFold contribution would mean the joint S×T gains are riding on a strong static prior, not learning dynamics. | Search appendix for "OpenFold ablation" / "FrameEncoder ablation". |
| U4 | What is the **actual loss function** form? Engineer flagged it is never written out (only "score matching, ε-prediction"). | Reproduction blocker; also a tell about whether reweighting / dynamics-aware loss terms exist. | Codex direct probe of paper. |
| U5 | The MZ claim is presented as motivation — but is there any **measured memory-kernel trace** from oracle MD shown in the paper or supplement, even as a sanity check? | If yes, MZ has empirical content here. If no (likely), it is pure rhetoric. | Direct paper search for "memory kernel" in figures/tables beyond §3.4. |
| U6 | The **AlphaFolding 0.11% all-atom validity** number on 100 ns (Table 1) — is this consistent with what AlphaFolding reports in its own paper, or is this a baseline-misuse artifact? | If misuse, the headline framing ("baselines fail catastrophically") collapses for one of the three baselines. | Check AlphaFolding paper / repo for native horizon and reported validity. |

---

## D. Confidence levels going into Round 3

- **Very high**: C1, C2, C3, C5, C6 (multi-agent + paper-text verified)
- **High**: C4, C7, D1, D3, D4 (paper-text verified)
- **Medium**: D2 (verified factually but framing-dependent)
- **Open**: U1–U6

Round 3 will use Codex as a hostile second reader on U1/U4/U5 (probe paper directly, no charity), and web verification on U2/U6.
