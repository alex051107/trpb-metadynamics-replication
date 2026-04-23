# Meeting Prep — Zhenpeng × Amin, Wed 4/23 2pm CT

**Format**: 30 min · 1-on-1 re-align · Zhenpeng brings this one-pager, Amin steers
**Preceded by**: v4 email (sent ~Apr 18 night EDT), Slack DM to Yu (2 min after email)
**Synthesis of**: Claude + Codex + ChatGPT Pro + Slack fact-check (4/18)

---

## What I've shipped (past 6 weeks)

- **MetaD production run** — Job 44008381 on Longleaf, GROMACS 2026 + PLUMED 2.9.2, 45/50 ns, max s(R) ≈ 4.1 (O→C transition partially sampled). Path: `/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/`
- **Conventional MD baseline** — Job 40806029, 500 ns production (71.55 hrs, 22 GB trajectory) for unbiased vs biased comparison.
- **PLP ligand parameterization** — `Ain_gaff.mol2` + `Ain.frcmod` via GAFF + RESP; charge = −2 verified against literature; protonation state resolved after 3 iterations.
- **Path CV** — 15-frame O→C reference (112 Cα, λ = 379.77 nm⁻², PATHMSD). Numerically matches Osuna 2019 SI. 6-PDB projection audit + 4HPX cross-species check.
- **System build** — tleap pipeline, 39,268 atoms, charge-neutral, ff14SB + TIP3P.
- **Failure-pattern library** — 7 reproducible debug docs (FP-020 → FP-027) in `replication/validations/failure-patterns.md`.
- **Bilingual tutorial** — ~2000 lines EN + CN at `project-guide/TrpB_Replication_Tutorial_{EN,CN}.md`.
- **Author correspondence** — emails to Maria-Solano (Apr 17) + Iglesias-Fernández (Apr 18) re: unresolved SI gaps (SIGMA values + path alignment); no reply yet from Osuna group.

---

## My read on role

After six weeks of hands-on metadynamics + force-field work, and after reviewing the recent STAR-MD discussion and the 4/11 Slack context on Mori-Zwanzig / memory kernel, my read right now is that my best contribution for me to own is **metadynamics + chemistry-to-ML bridge**, not model architecture.

Concretely, either:

- **(1) I own the TrpB MetaD benchmark pack** — reproducible pipeline + FES + representative substates + state labels + evaluation schema. This serves two audiences at once: (a) strengthening the TrpB design pipeline Yu described on 3/21, and (b) usable as validation ground truth for whatever the dynamics line converges to; **or**
- **(2) I own one defined model-side task with a clear validation target**, under you and Yu.

Either works. I just want it decided by one of us, in this meeting, rather than inferred again.

---

## Top 4 questions I want to align on

1. **What is the one primary deliverable you want me to own through the summer?** — single source of truth. Prevents repeating the 6-week miss.
2. **If metaD-side: which exact artifact — reproducible pipeline, FES, state labels, representative snapshots, or an evaluation script?** — each is a different 2-week scope. I'd rather pick the right one than build all five thinly.
3. **After the STAR-MD paper, what question do you see as still open for the protein-dynamics line?** — so my work plugs into your framing, not mine or ChatGPT's.
4. **Weekly check-in cadence — you, Yu, or both together?** — removes the structural ambiguity that caused the Slack-visibility gap in the first place.

*(Optional 5th if time: Is the 3/6 `#genslm` "protein dynamic benchmark for the SURF student" mine to own, or is there a second SURF student on that thread?)*

---

## Objective constraints

UNC finals through Fri 4/25 (~60% capacity this week, full 4/26 onward); Osuna-group SI clarification emails still unanswered as of 4/18; summer availability starts immediately after 4/25 per SURF contract.

---

## Proposed next step

Within 48 h of this meeting, I send you + Yu a one-paragraph recap of what we decided, plus a single-sentence deliverable I commit to by end of May.

---

## Speaker notes (not part of printed page — for Zhenpeng only)

**Opener (paraphrase, do not recite):**
> Something like: "Thanks for making time. Before we dig in — I reviewed the recent STAR-MD discussion and Slack context because I realized I'd mostly been interacting through Yu and didn't have a complete picture of the current project direction. My read right now is that the best contribution for me to own is the metadynamics + chemistry-to-ML bridge side, but I don't want to guess wrong, so I'd like to align on the one primary deliverable you want me to own through the summer."

**Do NOT say**:
- "I don't know what I'm supposed to do." → hypothesis-free = red flag
- "Do you want me to improve your model?" → pushes conversation to most ambiguous place
- "STAR-MD basically killed our project." → inaccurate + premature
- "Most of the blockers weren't my fault." → defensive
- "I thought Yu was the only one I needed to talk to." → true but not useful to say out loud

**Meeting outcome you actually want to leave with**:
1. One written-down primary deliverable (one sentence).
2. One explicit primary + one explicit secondary (you ask: "what should I explicitly deprioritize?").
3. One success criterion (X artifact by Y date).
4. One check-in owner + cadence.

**Critical nuance flagged by fact-check**: Yu on 3/21 framed metaD as **strengthening the existing MD pipeline** ("if OpenMM can reproduce, we can modify our current MD code to strengthen the existing pipeline"). Don't push "metaD = RNO ground truth" too hard as if that's the only direction — metaD's value is bi-directional (design pipeline + dynamics-line validation). If Amin leans one direction, follow his lead.
