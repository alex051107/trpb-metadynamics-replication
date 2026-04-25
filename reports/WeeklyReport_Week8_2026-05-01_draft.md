# Weekly Report — Week 8

| Field | Value |
|---|---|
| To | Prof. Anima Anandkumar; Dr. Yu Zhang |
| From | Zhenpeng Liu (liualex@ad.unc.edu) |
| Date | May 1, 2026 |
| Week | Week 8: Path realignment unblocks Initial pilot, 10-walker production launched |

## Project Context

I am replicating a MetaDynamics-based conformational analysis of the TrpB enzyme (an enhanced sampling method that pushes a system across rare-event barriers, applied to the open-to-closed motion of TrpB; Maria-Solano et al., JACS 2019). The goal is to validate the published method on the wild-type system, then design an ML "outer layer" that takes MetaDynamics-derived data and feeds it back into the GenSLM (a 25M-parameter generative protein language model from Lambert 2026) sequence-generation loop.

## Pipeline Overview

```
Phase 1: Replicate published results
  [1] Environment setup                 DONE
  [2] PLP cofactor parameterization     DONE
  [3] Reference path generation         DONE (path realignment landed this week)
  [4] System preparation                DONE
  [5] 500 ns conventional MD            DONE
  [6] Well-tempered MetaDynamics        IN PROGRESS  <-- here
  [7] Compare with published results    NEXT
Phase 2: Apply MetaDynamics output to score / fine-tune GenSLM
Phase 3: Closed-loop generation with MetaDynamics reward
```

## Summary

This week was about getting the Initial pilot to actually explore the open-to-closed conformational space, then launching the 10-walker production stage on top of that pilot. The Initial pilot now reaches s = 14.05 at 24 ns, covering the full path; the same setup before this week's path-builder fix was stuck at s less than 1.9 over 16 ns. The 10-walker production array (SLURM 45784112) launched this morning after a smoke test passed on all 10 walkers. The unresolved question is whether production will reach the published convergence threshold by the May 1 group meeting; with a 24-hour wall budget I expect about 20 ns per walker, well short of the 45 ns per walker the SI diagnostic asks for. I will ship the Initial pilot figure as the deck headline and present the 10-walker run as in-progress.

## Section 1: Work Done

| # | Task | Category | Status |
|---|---|---|---|
| 1 | Diagnosed v1 10-walker scancel: all 10 walkers used the same starting frame and stayed at the open conformation | Debug | Done |
| 2 | Diagnosed v2 10-walker exit code 139: LINCS bond-stress (the bond-constraint algorithm I use) on atoms 4463 to 4465 plus missing velocity initialization | Debug | Done |
| 3 | Designed v3 3-stage walker startup: energy minimization, then NVT 100 ps with PLUMED off and gen_vel=yes, then MetaDynamics with continuation=yes | Setup | Done |
| 4 | Smoke test 45783311: 10 of 10 walkers PASS, 24 minute wall, 0 LINCS warnings | Simulation | Done |
| 5 | Launched 10-walker production 45784112 with shared bias deposition | Simulation | Running |
| 6 | Rebuilt the reference path using a Needleman-Wunsch sequence alignment between 1WDW (P. furiosus, open) and 3CEP (S. typhimurium, closed) | Setup | Done |
| 7 | Self-computed the path-CV LAMBDA constant on the realigned path: 100.79 inverse Angstroms | Analysis | Done |
| 8 | Re-read JACS 2019 SI for the 10-walker protocol; corrected three drifts in our local replica (LAMBDA derivation, seed-target spacing, materializer source) | Documentation | Done |
| 9 | Rewrote the production materializer to extract walker seeds from the Initial pilot COLVAR file, not from the conventional MD trajectory | Setup | Done |
| 10 | Wrote select_seeds with a window-min-z rule that picks the frame closest to the path inside each target s-window | Setup | Done |
| 11 | Designed the MetaDynamics-to-GenSLM outer layer (kinetic-agility reward, LoRA adapter, DPO fine-tune); see Section 2.4 | Documentation | Draft |
| 12 | Wrote a 12-slide bilingual presenter script for the May 1 group meeting | Documentation | Done |
| 13 | Rendered the latest Initial pilot FES at 24 ns (Codex render via the lab's preferred plotting skill) | Analysis | Done |
| 14 | Rendered the before-vs-after path realignment trajectory comparison figure (Codex) | Analysis | Done |

## Section 2: What I Learned

### 1. Path realignment was the campaign's largest single-point delta this week

The published path coordinate uses 15 frames between an open structure (1WDW chain B, *P. furiosus* TrpB) and a closed structure (3CEP chain B, *S. typhimurium* TrpB). My original path-builder paired residues by raw residue number, so 1WDW residue 97 was paired with 3CEP residue 97. The two chains are not the same length: 3CEP carries five extra N-terminal signal-peptide residues, so 1WDW residue 97 is actually homologous to 3CEP residue 102. The naive pairing matched non-homologous residues across the 112 selected positions. Sequence identity dropped to 6.2 percent and the per-atom open-to-closed RMSD inflated to 10.89 A. The Branduardi formula `LAMBDA = 2.3 / mean MSD between adjacent frames` (Branduardi 2007) then collapsed LAMBDA to 3.80 inverse Angstroms, about 21 times smaller than what the published number implies.

I fixed this by writing a Needleman-Wunsch sequence alignment in numpy (match plus 2, mismatch minus 1, gap minus 2). The alignment recovers a uniform plus-5 offset across the 112 selected positions. After fixing the pairing, identity climbed to 59.0 percent, RMSD fell to 2.115 A, and LAMBDA settled at 100.79 inverse Angstroms. The bug was silent for three weeks because the path file syntax was valid and the simulation engine accepted it without complaint. The only downstream symptom was that the single-walker pilot stayed trapped at s less than 1.9 over 16 ns. After the realignment, the same pilot reaches s = 14.05 at 24 ns and explores the full open-to-closed path. **Figure 1 (before_after_fp034.png) shows the s-vs-time trajectory before and after the alignment fix.** The validation checklist now requires every future path-builder script to assert sequence identity above 50 percent before writing the path file.

### 2. Walker-startup design and why three stages were needed

The previous 10-walker attempt launched directly from coordinate-only `start.gro` files with `continuation=no`, `gen_vel=yes`, and PLUMED biasing turned on at the same time. All 10 walkers crashed inside 12 minutes with LINCS bond-stress on atoms 4463 through 4465. The root cause is that PLUMED started depositing path-CV bias before the velocities had Maxwell-Boltzmann thermalized at 350 K. Bond-stressed atoms cannot satisfy LINCS constraints under sudden bias; the integrator gives up with exit code 139.

The new walker startup splits into three stages. Stage 1 is energy minimization for 1000 steps with PLUMED off. Stage 2 is NVT for 100 ps with PLUMED still off and `gen_vel=yes`, which initializes velocities at 350 K. Stage 3 is MetaDynamics with `continuation=yes` so the velocities and box from `nvt.cpt` are inherited; PLUMED turns on for the first time at this stage. The smoke test ran 10 walkers for 1000+1000+1000 steps as a 30-minute sanity check. EM Maximum force fell into the 938 to 986 kJ/mol/nm range, no LINCS warnings, no atoms 4463 to 4465 errors, HILLS deposited at 1 Gaussian per 2 ps, no exit code 139. The production array launched immediately after the smoke pass.

### 3. The published FES uses production-only HILLS, not initial-plus-production

I considered combining the 22 ns of Initial pilot HILLS (the bias-deposit history) with the first 300 ps of the 10-walker production HILLS, on the assumption that more bias data is better. I asked for an SI re-read first.

The relevant lines on JACS 2019 SI p.S3-S4 are: "The free energy landscape associated with the metadynamics CVs is estimated by summing the Gaussian potentials deposited by all walker replicas as a function of the CVs values." And: "After an initial metadynamics run, we extracted ten snapshots ... Then, multiple-walkers metadynamics simulations with 10 replicas were computed."

The construction in the SI is production replicas only. Initial metadynamics is a seed-discovery stage; it is upstream of FES evidence. There is also a project-specific reason the merge would have been wrong: my Initial pilot uses a higher Gaussian height and biasfactor (height 0.3 kcal/mol, biasfactor 15) than the production run (0.15, 10). Well-tempered MetaDynamics theory requires a single biasfactor for one self-consistent FES estimate. Once production reaches 10 ns per walker, the FES is built only from the 10 production HILLS files. **Figure 2 (initial_pilot_latest_fes.png) shows the latest Initial pilot 2D FES with z RMSD on the y-axis and ΔG in kcal/mol on the color scale; the corresponding 10-walker production figure will land tomorrow.**

### 4. Initial thoughts on feeding MetaDynamics data back into GenSLM

This subsection is preliminary. The 10-walker production has only been running a few hours and the proxy data does not yet exist; what follows is the framing I want to commit to before the next group meeting, not a finalized design.

**Why this is the right next step.** Maria-Solano et al. (JACS 2019) established the central observation that motivates Phase 2: the TrpB variants with higher catalytic turnover are the ones whose protein body moves quickly and reliably across the open / partially closed / closed conformations. MetaDynamics is the only computational method I can run on a single variant that gives a quantitative read on those transitions. So if I want a reward signal that is mechanistically tied to catalysis (and not just to substrate binding affinity, which is what a docking score gives), MetaDynamics output is the most direct source.

**How the reward function works, in plain language.** For each variant, MetaDynamics returns a 2D free energy surface. From that surface I read two things: the energy barrier between the open and closed states (a low barrier means the protein gets to the catalytic state fast) and the depth of the closed-state basin (a deep basin means the protein actually stays in the catalytic state long enough for chemistry to happen). I combine the two into one number per variant. The functional form is the standard Kramers / Boltzmann combination from physical chemistry; the contribution is in using MetaDynamics output as the source of the two terms, not in inventing a new formula.

**The design constraint that frames everything else.** By the time I am ready to plug this back into the GenSLM-25M sequence generator (Lambert et al. 2026), I will have on the order of 30 to 50 (sequence, MetaDynamics-output) labeled pairs, not thousands. That sample size rules out approaches that fine-tune the generator's weights directly, because the generator has 25M parameters and would overfit to the labeled set, partially erasing what it learned during pretraining. The plan I want to commit to instead is: leave GenSLM unchanged, treat the 30-50 labeled pairs as a "preference direction" that steers the generator's output at generation time, and grow the labeled set through an active-learning loop that adds new pairs after each round of MetaDynamics. The published precedents for this kind of small-N steering on protein language models came out in the last 12 months (Yang et al., NeurIPS 2025; Stark et al. 2024); I intend to walk through the choice between them at the feasibility meeting next week.

**What is NOT being claimed.** The reward weights have not yet been calibrated against measured TrpB k_cat values; that calibration is a near-term task once production gives me one or two converged free energy surfaces. The small-N steering approach has not yet been benchmarked on GenSLM specifically; the simplest baseline (just rerank GenSLM's outputs by a generic protein-language-model likelihood) needs to be measured first, and the more elaborate approach earns its compute budget only if it beats that baseline. The Phase 2 deliverable depends on choosing an activity proxy (MMPBSA rank, literature k_cat, or hand-binned classes), which is one of the open questions for the May 1 meeting.

## Section 3: Problems Encountered and How I Solved Them

### Problem 1: 10-walker production crashed inside 12 minutes with LINCS bond-stress

*What happened:* All 10 walkers in the previous attempt reported `LINCS WARNING` on atoms 4463 through 4465 followed by `Fatal error` and exit code 139. The crash was within the first 12 minutes, well before any meaningful sampling.

*Root cause:* The walker MDP file had `continuation=no`, `gen_vel=yes`, and PLUMED biasing turned on simultaneously. Velocities were being initialized at 350 K at the same step that the path-CV bias started pushing on the system. Bond-stressed coordinates could not satisfy LINCS constraints.

*How I fixed it:* I split walker startup into three stages: energy minimization (PLUMED off), NVT 100 ps (PLUMED off, `gen_vel=yes`), and MetaDynamics (`continuation=yes`, reads `nvt.cpt`, PLUMED turns on for the first time). The smoke test on this design passed 10 of 10 walkers.

*Lesson:* Never bias an un-thermalized system. PLUMED on plus `gen_vel=yes` in the same MDP is a footgun; this rule is now in the validation checklist.

### Problem 2: Walker 9 starts close to the upper restraint wall

*What happened:* My seed selection rule picks the frame with minimum z (path deviation) inside each target-s window. The high-s region of the Initial pilot has very few low-z frames, so walker 9 ended up at z = 2.01 inverse Angstroms squared. The production wall is at z = 2.5, so walker 9 begins near the restraint.

*Root cause:* The Initial pilot has under-sampled the high-s, low-z corner. This is a pilot under-sampling issue, not a selection-rule issue.

*How I fixed it:* I retained walker 9 because the smoke-test EM converged in 759 steps without violating the upper wall. I documented a fallback in the validation report: if walker 9 collapses against the wall during production, I extend the pilot to 30 ns and re-materialize.

*Lesson:* Document fallbacks even when the current run passes. A passing smoke test on 1000 steps does not prove the same configuration survives a 50 ns production run.

## Section 4: Open Questions

1. **Activity proxy choice.** Without a primary activity signal (Yu's MMPBSA rank, literature k_cat, or hand-binned activity classes), the supervised target for the proxy model and the DPO reward is undefined. This blocks Phase 2 end-to-end. Resolves with one decision from the lab.

2. **Proxy data volume.** 30 to 50 (sequence, MetaD-output) training pairs is small for an 11-output regression head, even with LoRA. The Explore task running in parallel will report whether published examples of LoRA on N less than 200 protein-property regression exist; this informs whether to keep 11 targets or collapse to a single kinetic-barrier-plus-occupancy scalar.

3. **Wall-clock budget for production.** A 24-hour wall budget gives roughly 20 ns per walker. The published convergence diagnostic (JACS 2019 SI Fig S4 / S5) needs 45 ns per walker for the `|delta-delta-G(50ns) - delta-delta-G(40ns)|` plateau test to apply. Do I extend wall to 72 hours or accept a partial-converged ship for the May 1 deck?

4. **GenSLM architecture details.** Lambert 2026 supplies a 25M checkpoint. The hidden size and Fig 2A pooling rule are not in the paper. I have a one-shot extraction script for `hidden_size` from the public `config.json`. Pooling needs author contact unless it can be reverse-engineered from the released embeddings.

## Section 5: Next Week Plan

**Papers to read:**

- Lambert et al. 2026 (GenSLM-25M-TrpB): focus on Fig 2A pooling rule and embedding access pattern.

**Tasks:**

1. Monitor production 45784112 to 10 ns per walker; auto-render the SI-comparable production FES via `plumed sum_hills` on a compute node.
2. Confirm the full pipeline runs end-to-end: production simulation, post-processing, FES rendering, walker-explore tracking, into the deck. The goal for next week is "the pipeline is plumbed from raw HILLS to a labeled figure with no manual steps."
3. After the 10-walker production confirms the pipeline, schedule a meeting with the lab on the MetaDynamics-to-GenSLM outer-layer feasibility (LoRA proxy, DPO loop, activity-proxy choice). The goal is alignment on whether the design is worth building under realistic data constraints.
4. Run the GenSLM `hidden_size` extraction on the public checkpoint. If it returns one integer, BLOCKED #1 closes mechanically; if it does not, escalate to the GenSLM authors.
5. Apply the parallel-research findings on LoRA + small-N protein regression to the proxy-model architecture before the feasibility meeting.

## Section 6: Key Simulation Parameters

| Parameter | Value | Source |
|---|---|---|
| Force field | ff14SB | SI Methods, JACS 2019 |
| Water model | TIP3P | SI Methods, JACS 2019 |
| Temperature | 350 K | SI Methods (P. furiosus thermophile) |
| MetaD engine | GROMACS 2026.0 plus PLUMED 2.9.2 (source build) | SI specifies GROMACS plus PLUMED |
| Path-CV LAMBDA | 100.79 inverse Angstroms | Branduardi self-compute on realigned path |
| Path-CV ADAPTIVE scheme | DIFF | Codex SI re-read |
| Gaussian HEIGHT (production) | 0.15 kcal/mol | Author email 2026-04-23 |
| Biasfactor (production) | 10 | Author email 2026-04-23 |
| PACE (deposition rate) | 1000 steps = 1 hill / 2 ps | SI |
| Walker count | 10 | SI |
| WALKERS_RSTRIDE (cross-walker bias sync) | 3000 steps = 6 ps | SI |
| UPPER_WALLS on z | AT = 2.5 inverse Angstroms squared, KAPPA = 800 kcal/mol/A^4 | SI Methods |
| Conventional MD (per-system pre-MetaD) | 500 ns AMBER pmemd.cuda | SI Methods |
| WT-MetaD walker time budget | 50 ns per walker | SI |

Author-clarified parameters that the SI does not state numerically (the production-vs-Initial Gaussian height split, the upper-wall constants, neighbor-list strides, sigma floors per axis) are documented as "author-clarified per email 2026-04-23" in the PLUMED template header.

## Section 7: Attached Figures

1. `reports/figures/before_after_fp034.png` — before-vs-after comparison of the Initial pilot s-vs-time trajectory. Left panel: the pre-realignment baseline, walker stuck at s less than 1.9 over 17 ns. Right panel: the current 24 ns Initial pilot, walker explores s = 1 to 14.05 across the full open-to-closed path.
2. `reports/figures/initial_pilot_latest_fes.png` — latest Initial pilot 2D FES at 24 ns, single-walker, in the JACS 2019 SI Fig S2/S3 style. x-axis: s (path coordinate, dimensionless). y-axis: z RMSD in Angstroms (square root of the raw MSD). Color: ΔG in kcal/mol. The figure differs from the published Fig S2 because (a) the published figure aggregates 10 walkers over 50 ns each (~500 ns total), and (b) my pilot is single-walker at 24 ns of the upstream fallback contract; the overall shape and basin assignments are consistent.

## Section 8: References

1. Maria-Solano, M. A. et al. *Enzyme conformational dynamics in the catalytic cycle of tryptophan synthase.* JACS 141, 13049-13056 (2019). DOI: 10.1021/jacs.9b03646. The reference protocol I am replicating.
2. Branduardi, D., Gervasio, F. L. and Parrinello, M. *From A to B in free energy space.* J. Chem. Phys. 126, 054103 (2007). DOI: 10.1063/1.2432340. Defines the path-CV LAMBDA = 2.3 / mean adjacent MSD.
3. Tribello, G. A. et al. *PLUMED 2: New feathers for an old bird.* Comput. Phys. Commun. 185, 604-613 (2014). DOI: 10.1016/j.cpc.2013.09.018. The PLUMED engine.
4. Henzler-Wildman, K. and Kern, D. *Dynamic personalities of proteins.* Nature 450, 964-972 (2007). DOI: 10.1038/nature06522. Establishes that enzyme function is governed by inter-state transition rates, not single-state occupancy. Base assumption for the kinetic-agility reward.
5. Boehr, D. D. et al. *The dynamic energy landscape of dihydrofolate reductase catalysis.* Science 313, 1638-1642 (2006). DOI: 10.1126/science.1130258. Direct evidence linking conformational transition rates to catalytic activity.
6. Yang, J. et al. *Steering generative models with experimental data for protein fitness optimization.* NeurIPS 2025. arXiv:2505.15093. Benchmarks plug-and-play steering on TrpB at small N; supports the no-fine-tune Phase 2 plan.
7. Stark, P. et al. *ProtRL: Guiding generative protein LMs with reinforcement learning.* arXiv:2412.12979 (2024). Recipe for RL on protein LMs once the labeled set is large enough.
8. Lambert, S. M. et al. *Generative protein language modeling for tryptophan synthase variants.* arXiv (2026). Supplies the 25M GenSLM checkpoint that Phase 2 targets.
