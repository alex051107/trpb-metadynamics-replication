# Chapter 00 — TL;DR: What You Need to Know by Wed 4/23 2pm CT

**Audience**: You (Zhenpeng). The Amin meeting is 30 minutes. This is the one-page reference you re-read the morning of the meeting.

**Single highest-priority rule**: If you only internalize one thing from this knowledge map, internalize Chapter 03 §3.4 (quinonoid chirality loss) and Chapter 05 §2 (STAR-MD limitations). Those two topics cover ~80% of what can come up technically. Everything else supports those two.

---

## 1. The three things Amin most plausibly wants to see you know

### (a) STAR-MD's honest limitations
- SE(3) diffusion trained on ATLAS (100 ns, apo, small proteins, no ligands).
- No ligand atoms in training → PLP + substrate + water chains = out-of-distribution.
- Δt-conditioning assumes Markovian statistics → tension with Amin's own 4/11 Mori-Zwanzig note.
- Paper's own Conclusion flags "extend to complexes and small-molecule interactions" as future work.

### (b) Mori-Zwanzig / memory kernels in practical terms
- Coarse-graining → non-Markovian → need memory kernel in generalized Langevin equation.
- Extracting a memory kernel from finite MD data is **data-hungry** (Vroylandt 2022, Ayaz 2021) — this is the bottleneck, not the theory.
- Amin's 4/11 note is him **exploring**, not declaring a solution. You can contribute **ground truth data** (MetaD + unbiased MD on TrpB) that makes memory-kernel estimation tractable.

### (c) Your unique angle: chemistry-aware evaluation
- Standard ML-dynamics metrics (JSD, Recall, AA%, tICA) miss enzyme chemistry entirely.
- PLP Dunathan angle distribution, reprotonation-face geometry, lid-closure occupancy — none of these are in ATLAS.
- TrpB is the perfect test case because the chemistry is sharp (planar quinonoid → face-specificity).
- Proposing a benchmark pack (TrpB MetaD ground truth + chemistry-aware metrics suite) lets **anyone on the dynamics-ML line validate on a real enzyme**.

---

## 2. The one-sentence role pitch

> "My best contribution for me to own is the **metadynamics + chemistry-to-ML bridge** — a reproducible TrpB benchmark pack with chemistry-aware metrics that (a) strengthens the design pipeline Yu and Raswanth built and (b) serves as validation ground truth for whatever ML-dynamics direction you and Anima converge on."

Memorize this sentence. Say it once. Then let Amin respond.

---

## 3. Six-week deliverable snapshot (for when he asks what you've done)

- MetaD Job 44008381 at 45/50 ns; max s(R) ≈ 4.1 (O→C transition partially sampled).
- 500 ns conventional MD (Job 40806029) as unbiased reference.
- PLP parameterization (Ain_gaff.mol2 + Ain.frcmod) verified charge=−2.
- 15-frame O→C path CV (PATHMSD, λ = 379.77 nm⁻²) numerically matching Osuna SI.
- tleap system: 39,268 atoms, ff14SB + TIP3P, neutral.
- 7 reproducible debug docs (FP-020 to FP-027).
- Bilingual 2000-line tutorial (EN + CN).
- Osuna-group author emails sent 4/17 + 4/18 (no reply yet).

**Do not read this as a list in the meeting.** Have it ready for specific questions. Amin cares about the **role decision**, not the retrospective.

---

## 4. The four questions you want decisions on (ordered)

1. What is the **one primary deliverable** you want me to own through the summer? (single source of truth; prevents repeating the 6-week miss)
2. If metaD-side: which exact artifact — reproducible pipeline, FES, state labels, representative snapshots, or an evaluation script? (each is a different 2-week scope)
3. After the STAR-MD paper, what question do you see as still open for the protein-dynamics line? (so my work plugs into your framing, not mine or ChatGPT's)
4. Weekly check-in cadence — you, Yu, or both together?

Optional 5th: Is the 3/6 `#genslm` "protein dynamic benchmark for the SURF student" mine to own, or is there a second SURF student on that thread?

---

## 5. Topics you should be able to sketch in 30 seconds each

| If Amin raises... | You say... |
|-------------------|------------|
| RFdiffusion / RFD3 | "Watson et al. Nature 2023, denoising diffusion over backbone frames; Baker lab. RFAA adds ligand awareness (Krishna 2024). Raswanth uses this for theozyme scaffolding." |
| LigandMPNN | "Dauparas 2025, inverse folding with explicit ligand context — critical for TrpB because PLP is in the pocket. Standard MPNN would miss the cofactor." |
| GRPO | "Group Relative Policy Optimization, Shao 2024 (DeepSeek). On-policy RL with group-wise advantage estimation. Raswanth uses it for F0-level reward. F1/F2 are kept off-gradient via MFBO to avoid reward hacking." |
| Boltzmann generators | "Noé 2019, normalizing flow trained to sample equilibrium from energy. Doesn't scale to large proteins directly. Ancestor of BioEmu / MDGen / STAR-MD." |
| BioEmu | "Microsoft's diffusion model for protein ensembles. Sequence-conditioned. Closest living relative to STAR-MD in the apo-protein space." |
| OPES | "On-the-fly Probability Enhanced Sampling (Invernizzi 2020). Arguably better convergence than well-tempered MetaD. We used WTMetaD to replicate Osuna." |
| Markov state model | "Rigorous kinetic framework. If a generative model's trajectories recover MSM rates, it has captured kinetics, not just statics. The standard we should hold ML-dynamics to." |
| Dunathan hypothesis | "C(α)–H ⊥ PLP plane for α-abstraction. Would show up as a dihedral-angle distribution over an MD trajectory — concrete chemistry-aware metric." |
| Weighted ensemble | "WESTPA (Zwier/Chong). Unbiased rare-event sampling. Unlike MetaD, recovers rate constants directly. Viable alternative if we care about kinetics not FES." |
| tICA / VAMP-2 | "Slow-mode identification from time-lagged correlations (Pérez-Hernández 2013) / principled Koopman scoring (Noé 2018). Both used as ML-dynamics evaluation proxies." |

---

## 6. Things you should **not** say

From your meeting one-pager speaker notes (verbatim):
- ❌ "I don't know what I'm supposed to do." → hypothesis-free = red flag
- ❌ "Do you want me to improve your model?" → pushes conversation to most ambiguous place
- ❌ "STAR-MD basically killed our project." → inaccurate + premature
- ❌ "Most of the blockers weren't my fault." → defensive
- ❌ "I thought Yu was the only one I needed to talk to." → true but not useful to say out loud
- ❌ "Mori-Zwanzig for 400-residue proteins is standard." → false; it's an open research problem

---

## 7. Meeting outcome you actually want to leave with

1. One written-down **primary deliverable** (one sentence).
2. One explicit primary + one explicit secondary (ask: "what should I explicitly deprioritize?").
3. One **success criterion** (X artifact by Y date).
4. One **check-in owner** + cadence.

Nothing else.

---

## 8. Critical nuance (from your fact-check agent)

Yu on 3/21 framed metaD as **strengthening the existing MD pipeline** ("if OpenMM can reproduce, we can modify our current MD code to strengthen the existing pipeline"). Do NOT push "metaD = RNO ground truth" too hard as if that's the only direction — metaD's value is **bi-directional**:
- (a) strengthening the TrpB design pipeline Yu described on 3/21, and
- (b) usable as validation ground truth for whatever the dynamics line converges to

If Amin leans direction (a), follow his lead. If he leans direction (b), follow that. Don't commit to one until he signals.

---

## 9. Where to find the detailed arguments

If mid-meeting you realize you need depth on a specific topic, the chapters in this knowledge map are:

- **Ch 01** — MD foundations + why your software stack (AMBER/GROMACS/PLUMED) is defensible
- **Ch 02** — Enhanced sampling taxonomy (OPES vs WTMetaD, WESTPA, REMD, etc.)
- **Ch 03** — PLP chemistry, Dunathan, quinonoid chirality, D/L selectivity problem
- **Ch 04** — Protein design ML (RFdiffusion, MPNN/LigandMPNN, GenSLM, GRPO, MFBO)
- **Ch 05** — STAR-MD deep dive + BioEmu + MDGen + Boltzmann generators + flow matching
- **Ch 06** — Mori-Zwanzig, memory kernels, neural operators (RNO)
- **Ch 07** — Evaluation metrics — generic + chemistry-aware precedents + proposed TrpB metrics
- **Ch 08** — Consolidated pros/cons matrix (all methods, one table)
- **Ch 09** — Improvement levers — where independent judgment would change the project

The master index (`TECHNICAL_KNOWLEDGE_MAP.md`) has a "find X here" lookup table.

---

## 10. Mental model for the Amin meeting

**You are not defending your 6 weeks.** You are asking for a decision and proposing a role that serves multiple stakeholders. The 6 weeks of MetaD work is **evidence of capability**, not a deliverable to justify. Don't let the conversation drift into "did you do enough" territory — steer it back to "what's my role going forward".

**Amin is not grading you.** He is allocating a SURF student's summer. He needs to be able to tell Anima "Zhenpeng owns X by Y". Help him get there.

**Yu is not being bypassed.** Your Slack DM to Yu after sending the Amin email (Codex's fact-check prescribed this) means Yu knows you're re-aligning. If Amin asks, say "Yu knows I'm here; I'm trying to get clarity on who owns what so I don't duplicate or miss things going forward".

---

**You've got this.** Breathe. 30 minutes. One decision. Recap in 48 hours.
