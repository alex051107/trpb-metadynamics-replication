# Team Lead — Independent Anchor (pre-team)

Read by lead before agents return. Used to spot agreement/disagreement and avoid rubber-stamping.

## Paper at a glance
- **STAR-MD**: Shoghi, Liu, Shen, Brekelmans, Li, Gu — ByteDance Seed, arXiv 2602.02128v2 (Feb 12 2026), 49 pp.
- Same-group lineage: ConfRover (Shen et al., NeurIPS 2025) → STAR-MD. Y.S. = Yuning Shen on both. Project page lives under `/ConfRover/starmd`.
- Architecture: causal (autoregressive) SE(3) diffusion transformer over backbone rigids (T∈R³, R∈SO(3)); IPA + joint spatio-temporal (S×T) attention + EdgeTransition + MLP backbone update; 2D-RoPE on (residue, frame).
- Training: 4 diffusion blocks (1 IPA + 2 S×T each), hidden 256, 8 heads, Adam 5e-5, **context L=8 frames**, batch 8, 8×H100, DeepSpeed Stage 2 (§G).
- Inference (Table 4, p. 22):
  - 100 ns → 80 frames @ 1.2 ns
  - 240 ns → 200 frames @ 1.2 ns
  - 1 μs   → 400 frames @ 2.5 ns
  - **Up to 50× training context length at inference** — extrapolation, not interpolation.
- Forward diffusion: T uses Gaussian (Eq 1), R uses IGSO3 (Eq 2). Score-matching, ε-style noise prediction.

## Key engineering tricks (real)
1. **Block-causal teacher-forcing** training (concat clean+noisy, special attention pattern) — borrowed from Block-Diffusion (Arriola ICLR 2025) and Diffusion Forcing.
2. **Contextual noise perturbation** τ ∼ U[0, 0.1] applied at both train AND inference time — cures distribution shift, mitigates compounding errors.
3. **Continuous-time Δt conditioning** Δt ∼ LogUniform[10⁻², 10¹] ns via AdaLN — decouples physical duration from frame count. THIS is the actual "extrapolation" mechanism; the model never trained on long absolute time, just on diverse strides.
4. **KV cache reduction** O(NL) vs ConfRover's O((N+N²)L) → 196× reduction at N=200,L=32 (§B.4 calc on p. 21).
5. **2D-RoPE** for joint (residue, frame) positional embedding → length extrapolation.

## "Theory" — Mori-Zwanzig (§3.4 + Appendix A.2)
- Proposition 1 (Memory Inflation): `K̃⁽²⁾(p) = K̃ss⁽¹⁾ + (Ωsz + K̃sz⁽¹⁾)(pI − Ωzz − K̃zz⁽¹⁾)⁻¹(Ωzs + K̃zs⁽¹⁾)`.
- This is **a standard Schur-complement projection**, not a new theorem. Mathematically correct.
- It proves: removing pair features → richer, non-separable memory kernel.
- It does **NOT** prove: joint S×T attention is required. That's an inference / architectural heuristic. Factored attention with enough depth is also a universal approximator.
- The memory kernel is **never measured, learned, or explicitly modeled** — it's only invoked as motivation.
- Verdict: MZ is dressing, not derivation. Honest framing should say "MZ motivates non-Markovian temporal modeling" — but the paper says "directly motivates our architecture: joint spatio-temporal attention" (p. 5/p. 18) which over-claims.

## Empirics — what the tables actually show

### 100 ns benchmark (Table 1, p. 7)
- STAR-MD JSD 0.43, Rec 0.54, tICA 0.17, CA+AA 85.29% — clear SOTA over MDGen / AlphaFolding / ConfRover.
- Oracle MD: JSD 0.31, Rec 0.67, CA+AA 96.43% — **gap to oracle is still substantial** (12 pts validity, 24% relative recall gap).
- AlphaFolding's 0.11% all-atom validity is **shockingly low** — strongly suggests baseline misuse, not legitimate failure of the method as designed.

### 240 ns / 1 μs (Table 2, p. 9)
- STAR-MD on 1 μs: JSD 0.46, Rec 0.61, CA+AA 79.93%. Oracle: JSD 0.23, Rec 0.91, CA+AA 82.75%.
- ConfRover-W (windowed) JSD 0.55, Rec 0.45, CA+AA 36.91% on 1 μs.
- Sample sizes: 240 ns = 32 proteins, 1 μs = **8 proteins**. 1 μs claim is on tiny set.
- ConfRover full version excluded due to OOM → ConfRover-W is a degraded baseline. Author acknowledges; still uncomfortable for headline "catastrophic failure" framing.

### Ablations (Table 3, p. 10)
- Joint S×T vs separable (`w/ Sep Attn`): JSD 0.46→0.42 (joint better), tICA 0.17 (tied), RMSD 0.09 (tied), CA% 87.95→86.62 (separable actually slightly better!), AutoCor 0.05→0.02 (joint better).
- The dynamic-fidelity gains from joint attention are **modest and not uniform**. The big win is **conformational coverage** (JSD/Recall), not dynamics per se.
- This undercuts the MZ-derived "joint attention is necessary for dynamics" framing.
- `w/o Noise`: validity drops 85→76%. Confirms contextual noise is the load-bearing trick for stability.

## Baselines fairness (§F, p. 26)
- AlphaFolding: 10 ps native, sub-sampled. Block size 16 frames. Long horizons require running the recommended `run_eval_extrapolation.sh` for very many blocks. Not what it was tuned for.
- MDGen: 100 ns per rollout, 400 ps stride. Discards memory between rollouts (paper acknowledges).
- ConfRover-W: windowed attention size=14, 2 attention sinks (Xiao 2024 StreamingLLM). Validated at 100 ns to lose ~6.3 pts CA+AA validity vs full ConfRover (Table 6, p. 27) — modest degradation.
- **Most damning fairness issue**: training context for STAR-MD (L=8) was small, but Δt conditioning gave it stride diversity that baselines may not have had in their training. Need to check whether MDGen/ConfRover were trained with stride randomization.

## Reproducibility status
- No code/checkpoint release mentioned in main text or appendix sections I've read.
- Uses official AlphaFolding & MDGen code+weights for baselines (URLs in §F).
- Hyperparameters in Tables 7–10 (§G) — appears reasonably complete.

## My initial top vulnerabilities (lead's view)
1. **MZ "theoretical justification" is window-dressing.** Proposition 1 is true, but the architectural conclusion (joint S×T attention) is not derived — and the ablation only weakly supports it.
2. **Long-horizon claim rests on 8 proteins** for the headline 1 μs number. No functional / experimental ground truth — only structural validity + tICA correlation as a *proxy* for dynamics fidelity.
3. **Same-group baseline (ConfRover)** + degraded variant for the long-horizon comparison. Conflict-of-interest risk.
4. **"Microsecond extrapolation"** — model never trained on long absolute durations. Trained context = 8 frames; inference = 50× that. The success is impressive engineering but is fundamentally about architectural extrapolation (RoPE + Δt conditioning + contextual noise), not about learning microsecond physics from data.
5. **AlphaFolding's 0.11% validity** screams misuse, but is featured prominently as evidence baselines fail. Suspect.
6. **No sequence-conditioning ablation** — can't tell what fraction of performance comes from frozen OpenFold features vs the diffusion learning.
7. **Validity metrics are derived from oracle MD's 99th-percentile thresholds** (§D, Table 5). A model that just regurgitates near-equilibrium folded structures will score well on validity. This metric does not reward genuine dynamics, only structural plausibility.

## Where the paper is genuinely strong
- Real engineering wins: 196× KV reduction, contextual noise stability, length extrapolation via 2D-RoPE.
- Continuous-time Δt conditioning is elegant.
- Most thorough long-horizon evaluation in this niche to date.
- Honest about ConfRover-W substitution (didn't hide it).
- Ablations cover the main design choices.

## Lab-relevance signal (for the user)
- **Remaining opening**: paper does not address (a) sequence-conditioned dynamics for engineered proteins (e.g. enzyme variants with directed mutations), (b) cross-family transfer (only ATLAS-style globular proteins tested), (c) functional/experimental validation (no comparison to NMR S², MFPTs from spectroscopy, etc.), (d) ligand-bound dynamics, (e) anything close to the TrpB-style allosteric coupling between domains.
- For Caltech project: TrpB-style "MetaDynamics-replacement via learned model" is wide open — STAR-MD is unconditional dynamics on a globular protein benchmark, not a replacement for enhanced sampling on a functional question.
