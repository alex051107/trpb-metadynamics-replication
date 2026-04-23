---
name: round5_codex_rebuttal
description: Round 5 — hostile second-pass from Codex against our R4 synthesis. Records where Codex forced us to downgrade / reframe and where our critique survived.
type: review
---

# Round 5 — Codex Hostile Pass

We (Claude, R1–R4) asked Codex to steelman the paper against our four hardest critiques. Codex returned a focused rebuttal. Below: what survives, what we must soften, what we were wrong about.

---

## Critique 1 — "MZ is decoration, not derivation"

**Codex pushback**: The paper's real architectural argument is about **efficient inductive bias**, not unique derivation. Once pair-temporal state is dropped from the cache, the kernel over singles is genuinely non-separable; under STAR-MD's compute budget, a single low-depth joint operator is the natural cheap representation. Our "factored attention + depth is universal" counter is mathematically correct but practically evasive — universality ignores depth/width/FLOP cost.

**Our survival**: Paper's Remark 2 text ("cannot be factorized into independent spatial and temporal components, requiring models that capture non-separable coupling") is still too strong as written. That's an impossibility framing, not an efficiency framing.

**Revised claim**: *MZ motivates a practical preference for joint S×T attention under the singles-only constraint, not a necessity. The paper's Remark 2 wording overreaches but the underlying efficiency argument is defensible.*

**Confidence**: HIGH (Codex agrees the wording is too strong; we withdraw the stronger "decoration" framing).

---

## Critique 2 — "Joint attention loses validity to separable (Tables 3 + 13)"

**Codex pushback (severe)**: We over-interpret a +1–2 point delta on n=32 (100 ns) / **n=8** (1 μs) with **no error bars** reported. Our "rare conformation" defense for joint's lower validity is weak — MolProbity outliers are stereochemical pathology, not signatures of productive rare states. Real story is a **coverage-validity tradeoff**: separable trades exploration for local conservatism.

**Our survival**: Paper's selective discussion — foregrounding coverage wins, silent on validity losses — is still a framing critique that holds.

**Revised claim**: *Tables 3 + 13 suggest a coverage-validity tradeoff rather than a clean joint win. The validity deltas are small, uncertain on n=8, and the paper's failure to acknowledge the tradeoff is a discussion-quality issue, not a scientific refutation.*

**Confidence**: MED (downgraded from HIGH). This is our most significant concession. The "separable beats joint" framing in R2/R3/R4 was overconfident.

---

## Critique 3 — "Baselines are structurally disadvantaged by fixed-stride training"

**Codex pushback**: We conflated two statements. Our strong line — *"the comparison is unfair"* — is sloppy because §F is transparent about baseline stride handling and evaluating checkpoints in their canonical form is normal practice. Our weaker line — *"headline gains are partly attributable to stride-conditioning rather than architecture"* — is fine.

**Our survival**: The missing control (stride-randomized MDGen retrained with matched compute) is still missing, and the paper still attributes gains to joint S×T / MZ reasoning rather than to the concrete `Δt` LogUniform advantage.

**Revised claim**: *Headline long-horizon gains are partly attributable to STAR-MD's stride-conditioning training, which baselines do not have. This is not "unfair" — it is a real contribution — but the paper credits the wrong mechanism (joint attention / MZ) rather than the actual one (continuous-time Δt + LogUniform sampling).*

**Confidence**: MED-HIGH. Refined, not withdrawn.

---

## Critique 4 — "Ayaz/Dalton PNAS uncited prior art"

**Codex pushback (severe)**: This is our weakest attack. Ayaz/Dalton/Netz study memory-dependent friction along a **1D folding coordinate** (Q, fraction of native contacts). STAR-MD models **high-dimensional backbone-rigid autoregressive dynamics**. Different MZ object, different projection, different task. Citing Mori 1965 + Zwanzig 1961 originals is adequate for the generic formalism.

**Our survival**: A modern biomolecular MZ citation would still improve the paper. But characterizing the omission as a "major omission" / "reviewer ammunition" overreaches.

**Revised claim**: *Modern biomolecular MZ literature (e.g., Ayaz et al. PNAS 2021, Dalton et al. PNAS 2023) would strengthen the motivation section, but the MZ objects studied there (1D folding-coordinate memory kernels) are not direct prior art for STAR-MD's backbone-rigid autoregressive formulation. "Nice-to-have citation" is the defensible version; "major omission" is overreach.*

**Confidence**: HIGH (we accept Codex's reframing; withdraw the "reviewer ammunition" framing).

---

## Net effect on R4 deliverables

| Deliverable | Change |
|-------------|--------|
| D2 claim/evidence table, row #4 (MZ derivation) | Soften: "non-unique derivation" → "efficiency motivation overreached to necessity in Remark 2" |
| D3 Proven vs Suggested, joint-attention line | Reframe as "coverage-validity tradeoff"; drop "separable wins on validity" as clean claim |
| D6 Vulnerable Claims V1 | Sharpen the specific sentence in Remark 2 as the target, not the whole MZ argument |
| D6 V2 | Downgrade: present as discussion-quality issue, not scientific failure |
| D6 V3 | Reword: "stride-conditioning is the unacknowledged mechanism" (drop "unfair") |
| D6 V8 (Ayaz/Dalton uncited) | Downgrade from "reviewer ammunition" to "strengthen motivation" |
| D9 Rebuttal Kit, Q3 | Keep — now aligned with refined V3 |
| D9 Rebuttal Kit, Q5 | Soften the MZ-literature phrasing |

---

## Meta-note

Codex forced two real concessions (validity tradeoff framing, Ayaz citation severity) and sharpened two claims (MZ efficiency vs necessity, stride-conditioning attribution). No critique was fully withdrawn, but the tone and specificity tightened across the board. This is the right use of a hostile second reader.
