# Chapter 02 — Enhanced Sampling: The Full Landscape Around Your WTMetaD Choice

> **Purpose**: You have spent six weeks debugging PATHMSD + well-tempered MetaDynamics (WTMetaD) on TrpB. That is enough depth to build one pipeline. It is *not* yet enough to defend the design choice against the question Amin or Yu will almost certainly ask: *"Why not use X instead?"* This chapter puts your method inside the full enhanced-sampling taxonomy so you can answer that question quickly, concretely, and without hedging.
>
> **What you will NOT find here**: Re-derivations of WTMetaD convergence, PATHMSD math, or Osuna 2019 parameter tables — those are in `MASTER_TECHNICAL_GUIDE.md` §4–§6 and `FEL_DEEP_DIVE_AND_NEW_DIRECTIONS.md` §2–§4. This chapter is *comparative*: each method is framed as "what problem it solves that WTMetaD does not, and what price you pay".

---

## 2.1 The rare-event problem, in numbers you can quote

Unbiased MD samples the Boltzmann distribution at rate limited by the fastest degree of freedom (bond vibrations, ~10 fs). Any process gated by a free-energy barrier ΔG experiences a mean first-passage time that scales as Kramers:

τ_MFP ≈ τ₀ · exp(ΔG / kT)

where τ₀ is a prefactor of ~10 ps–1 ns set by the diffusion along the reaction coordinate in the barrier region.

Plug in your TrpB numbers. At 350 K (the thermophilic production temperature from the Osuna JACS 2019 SI), kT ≈ 0.696 kcal/mol. The O→C COMM-domain closure barrier in PfTrpB estimated from both experiment (NMR line-shape analysis) and MetaD reconstructions sits in the 8–12 kcal/mol range. Taking 10 kcal/mol:

exp(10 / 0.696) ≈ exp(14.4) ≈ 1.76 × 10⁶

Multiply by τ₀ ≈ 100 ps and you get τ_MFP ≈ 176 μs — *per crossing*. Your 500 ns unbiased run (job 40806029, 71.55 h on one A100) samples roughly 1/350 of one crossing on average. You would need ~60,000 ns of wall time to observe *one* O→C event with any statistical confidence, and ~600,000 ns to resolve the FES.

This is the concrete justification for enhanced sampling. When Amin pushes on this, your answer is: *"At 350 K with a 10 kcal/mol barrier, unbiased MD needs ~175 μs per crossing. 500 ns saw zero transitions, which is exactly what Kramers predicts. That is why the enhanced-sampling decision is not optional."*

---

## 2.2 Taxonomy of enhanced-sampling methods

Methods fall into five families. The taxonomy matters because each family has a *different* failure mode, and confusing them in a meeting is an easy tell that someone has only used one method.

**Biased-potential methods** add an external potential that depends on one or more collective variables (CVs). The bias deliberately distorts the Hamiltonian to flatten barriers. Examples: umbrella sampling (US), metadynamics and its variants, adaptive biasing force (ABF), variationally enhanced sampling (VES), OPES. Failure mode: if the CV misses an orthogonal slow mode, the recovered FES is *systematically wrong*, not just noisy.

**Generalized-ensemble / exchange methods** do not bias along a CV. They couple multiple replicas at different temperatures or Hamiltonian scalings and exchange configurations with Metropolis acceptance, so cold replicas inherit diversity from hot replicas. Examples: T-REMD, H-REMD, REST2, integrated tempering sampling (ITS). Failure mode: computational cost scales with system size (more replicas needed to maintain exchange probability), and for ~40,000-atom solvated proteins T-REMD is effectively dead.

**Path-sampling / rate methods** sample trajectories that start in one basin and end in another, rather than biasing equilibrium populations. Examples: transition interface sampling (TIS), forward flux sampling (FFS), milestoning, weighted ensemble (WE / WESTPA). Failure mode: also need a reasonable progress coordinate; *do not distort the Hamiltonian*, so rates are physically meaningful.

**Force-driven methods** apply an external time-dependent force that drives the system from A to B. Examples: steered MD (SMD), targeted MD (TMD), Jarzynski-based free energy reconstructions. Failure mode: nonequilibrium work must be extrapolated to equilibrium via Jarzynski's equality, which is exponentially dominated by rare low-work trajectories. For barriers >5 kT this is unreliable unless many replicas are averaged.

**Modified-potential methods** reshape the underlying potential energy surface globally, lowering all barriers simultaneously. Examples: accelerated MD (aMD), Gaussian accelerated MD (GaMD — developed in the Miao group at UNC), scaled MD. Failure mode: no focus — they speed up fast irrelevant modes at the same time, so free energies converge slowly and the effective temperature is non-uniform across the landscape.

The Osuna 2019 pipeline you are replicating falls in family 1 (WTMetaD) with CVs from family that I will call "path-parametric" — PATHMSD — which bridges families 1 and 3.

---

## 2.3 The metadynamics family — variants you should know exist

Everything below is "metadynamics with one twist". They share the core move: deposit Gaussians in CV space to flatten barriers. What differs is *how* you deposit, *how fast the hills shrink*, *how many CVs* you bias, and *how many copies* share the bias.

**Standard MetaD (Laio & Parrinello, PNAS 2002)**. Constant hill height. Never converges; the bias oscillates around the true −F(s). You can average across a window, but you cannot tell *when* to stop. Not used since ~2010 for quantitative FES work.

**Well-tempered MetaD (Barducci, Bussi & Parrinello, PRL 2008)**. Hill height decays as exp(−V(s,t)/ΔT), where ΔT = (γ−1)T and γ is the bias factor. In the long-time limit, V(s,∞) = −(1 − 1/γ)·F(s), so you recover F(s) deterministically. This is what you are running (γ=10, HEIGHT=0.628 kJ/mol, PACE=1000, SI-documented).

**Multiple-walker MetaD (Raiteri et al., JPC B 2006)**. N independent replicas share a single HILLS file. Wall-clock speedup close to N× if walkers start from diverse configurations; otherwise they redundantly fill the same basin. The Osuna SI uses 10 walkers; your Phase 2 uses 10 with diverse initial snapshots harvested from unbiased trajectories. **Key subtle point**: walkers do *not* give statistically independent error bars — they share bias — so you cannot just compute std across walkers as an uncertainty estimate. Block analysis on the time series of V(s,t) is the correct uncertainty.

**Bias-exchange MetaD (BEMD; Piana & Laio, JPC B 2007)**. M replicas, each biasing a *different* CV, exchange configurations Metropolis-style. Useful when you suspect ≥3 slow CVs but any single WTMetaD in 3D CV space would not converge in reasonable time. Cost: M-fold GPU-hours. Largely superseded by PBMetaD for most use cases.

**Parallel-bias MetaD (PBMetaD; Pfaendtner & Bonomi, JCTC 2015)**. Bias N one-dimensional CVs *simultaneously* rather than one N-dimensional bias. Uses N independent 1D grids instead of one N-D grid — memory scales as N·k instead of k^N. Exactly the tool you would reach for if you decided to add side-chain dihedrals alongside the path CV, which is the natural next step if you believe Felts et al. 2023's critique that Cα-only path CVs miss side chain reorganization. PLUMED keyword: `PBMETAD`.

**OPES (Invernizzi & Parrinello, JPC Lett 2020)**. See §2.8 — important enough that it gets its own section.

**Meta-parameter sensitivity** — the three knobs and what happens when you turn each one wrong:

| Knob | What it does | Too low | Too high |
|---|---|---|---|
| `HEIGHT` | Gaussian amplitude | Slow barrier crossing, long convergence | Overshoots the basin, inflates FES error |
| `PACE` | Deposition interval (steps) | Noisy bias, large fluctuations | Missed transitions between depositions |
| `BIASFACTOR` γ | Controls hill decay ΔT = (γ−1)T | γ near 1: acts like unbiased; no FES recovered | γ very large: pure exploration, slow convergence |

Osuna's choice (0.628 kJ/mol, 1000 steps = 2 ps, γ=10) is conservative — low HEIGHT, long PACE, moderate γ. That is appropriate for a deep barrier you do not want to overshoot. Modern ML-CV + OPES workflows often use more aggressive settings because OPES self-tunes.

---

## 2.4 Path CVs in depth — the exact choice you made

Your PATHMSD line in `plumed_trpb_metad.dat` is the single most consequential design decision in the project. Names the alternatives you did *not* pick.

**Branduardi path CV (JCP 2007)**. Given K reference frames R_k along O→C:

s(R) = Σ_k k · exp(−λ·MSD(R,R_k)) / Σ_k exp(−λ·MSD(R,R_k))
z(R) = −(1/λ) · ln Σ_k exp(−λ·MSD(R,R_k))

s is soft progress, z is orthogonal distance. Bias s, restrain z. Rule of thumb: λ ≈ 2.3 / ⟨MSD⟩_nearest. Yours is 379.77 nm⁻², matching the SI.

**PATHMSD (Leines & Ensing, PRL 2012)**. PLUMED implementation. MSD is internally A² but λ must be in nm⁻² in PLUMED 2.x — the FP-020 trap, re-diagnosed and fixed 2026-04-09. Hard-codes RMSD; faster than generic PATH.

**FUNCPATHMSD**. Accepts arbitrary distance functions. Strictly slower. Use only for non-RMSD metrics (contact maps for binding).

**ADAPTIVE_PATH (Leines & Ensing, PLUMED 2.9)**. Path frames drift toward running-average trajectory during the run. The escape hatch if Amin questions the linear-Cartesian 1WDW→3CEP interpolation. Trade-off: bias and path convergence couple, harder to diagnose.

**Shortest Path Map (SPM; Osuna group, 2016 onward; webserver — Casadevall & Osuna, *Protein Eng. Design & Selection* 2024, DOI 10.1093/protein/gzae005)**. *Not* enhanced sampling — a CV-discovery tool. From unbiased MD, build a residue-correlation graph, extract shortest path between active-site and distal residue. Nodes are "conformationally relevant positions" for mutagenesis. *Complements* MetaD: SPM picks residues, MetaD computes FES shift.

**Committor-based CVs (Peters, van Erp)**. Rigorous reaction coordinate: p_B(R) = probability a trajectory from R reaches B before A. Expensive (many spawns per R). Used for *post-hoc CV validation*, not as bias. Yang et al. (Nat. Commun. 2025, DOI 10.1038/s41467-025-55983-y) use committor-derived CVs to show path CVs miss features — cite this if anyone paints WTMetaD as infallible.

**ML-learned CVs** — four to know:
- *DeepLDA* (Bonati, JPC Lett 2020): supervised LDA via NN on two-state data.
- *Deep-TDA* (Bonati, PNAS 2021): force projected distributions to match a preset Gaussian mixture. Currently the most popular CV for OPES.
- *DeepTICA* (Bonati, JCTC 2021; linear: Schwantes & Pande 2013): time-lagged autoencoder; learns slowest kinetic modes. Best when kinetics matter.
- *State-free reversible VAMPnets* (Mardt, Nat. Commun. 2018): variational Koopman score. Principled; longer training.

Workflow: short unbiased MD → train Deep-TDA on descriptors (Cα distances, contacts, dihedrals) → load NN as a PLUMED pytorch CV → OPES or WTMetaD → retrain and iterate. Reference: PLUMED+mlcolvar tutorial (arXiv:2410.18019, Oct 2024).

Honest note: *no published Deep-TDA vs PATHMSD comparison exists for TrpB O→C*. Running both post-replication is a publishable result.

---

## 2.5 Umbrella sampling — the boring one that still wins sometimes

Umbrella sampling (US; Torrie & Valleau, J. Comput. Phys. 1977) places N harmonic windows V_i(s) = (k/2)(s − s_i)² along the CV, runs each window independently, and stitches with WHAM (Kumar 1992) or MBAR (Shirts & Chodera, JCP 2008). What US gives that MetaD does not: rigorous per-bin error estimates from MBAR, trivial job-array parallelism (windows are non-communicating, so Longleaf can pack 32 A100s instead of one walker node), and no overfill problem. What it does not give: exploration (you must know the path), or robustness to bad CVs — if the CV misses a slow orthogonal mode, different windows equilibrate to *different* hidden-mode ensembles and WHAM yields a discontinuous FES. Prefer US when the CV is 1D and pre-validated (small-molecule binding along a pulling coordinate). Not this project.

---

## 2.6 REMD and variants — the method your system is too big for

T-REMD (Sugita & Okamoto, CPL 1999) runs M replicas at T_1 < … < T_M, swaps neighbors with Metropolis probability. Replica count scales as √N_dof: for TrpB (39,268 atoms, ~117,000 DOF), 350→500 K needs ~50 replicas, i.e., 25,000 GPU-hours for 500 ns each. Dead for solvated enzymes.

H-REMD exchanges along a λ ladder scaling the potential; still ~10–20 replicas.

REST2 (Wang, Friesner & Berne, JPCB 2011) scales only solute-solute and solute-solvent terms by β_0/β_m, keeping solvent-solvent cold. Drops to 4–8 replicas for folded proteins. The IDP/folding tool of choice. *Caveat*: Qu et al. (JCTC 2023, DOI 10.1021/acs.jctc.2c01139) showed REST2 causes artificial chain collapse in large IDPs; they proposed REST3.

**Why Osuna did not use REMD**: TrpB is not disordered, the motion is spatially localized (COMM vs TIM-barrel), and a good path CV exists. CV-biasing is cheaper and more interpretable than tempering whenever you can write the CV. Defense: *we have a CV*.

---

## 2.7 Weighted ensemble (WESTPA) — the threat you should take seriously

WE (Huber & Kim, Biophys J 1996; Zwier/Chong group development from ~2010; WESTPA 2.0: Russo et al., JCTC 2022) is fundamentally different: it does *not* distort the Hamiltonian. Many short unbiased segments run in parallel, bin by progress coordinate; at each resampling step, underpopulated bins duplicate trajectories (halving weights), overpopulated bins merge (summing weights). Effort flows to rare regions while each trajectory stays physically faithful.

Strengths: rates are recovered directly (MFPT = flux of weight across an interface near B, no Kramers extrapolation); any observable reweights from unperturbed trajectories; scales to thousands of GPU-parallel segments; RED estimator (Copperman & Zuckerman, JCTC 2020) cuts rate-convergence cost ~50%.

Weaknesses: still needs a progress coordinate (less sensitive than MetaD's CV, but not zero); published protein-protein association studies cost 10⁵–10⁶ GPU-seconds, so a TrpB O→C→O cycle is ~10⁴ GPU-hours — comparable to a 10-walker WTMetaD; integration with AMBER/GROMACS and a path CV is labor-intensive.

**When WE beats MetaD**: the question is *rate*, not FES. WTMetaD gives a rough infrequent-metadynamics rate (Tiwary & Parrinello, PRL 2013); WE gives it directly with smaller error bars.

**For this project**: Osuna 2019 reports FES and populations, not rates. WTMetaD answers the scientific question. WE becomes the right tool only if the downstream pivot is evolution→k_closure, which it currently is not.

Honest meeting answer: *"For the FES question, WTMetaD is correct. WE is correct if we pivot to rates. The lab has not pivoted."*

---

## 2.8 OPES vs WTMetaD — the 300 words that matter

OPES (Invernizzi & Parrinello, JPC Lett 11, 2731–2736, 2020; arXiv:2101.06991) rewrites the MetaD update rule. Instead of depositing Gaussians into a bias potential V(s,t), OPES estimates the *probability distribution* P(s) from collected samples using kernel density estimation, then applies a bias V(s) = −kT · log(P(s)/P_target(s)) where P_target is typically uniform (the "WELL-TEMPERED" variant matches WTMetaD behavior). The bias is updated on the fly in a way that self-regularizes.

**What OPES does better than WTMetaD**:
1. *Faster convergence.* Published benchmarks (Invernizzi & Parrinello, JCTC 2022, DOI 10.1021/acs.jctc.2c00152) show OPES reaches the same FES accuracy in ~3–5× fewer simulation steps than WTMetaD on ala2, chignolin, and RNA tetraloops.
2. *Fewer hyperparameters.* OPES essentially has one critical parameter, the BARRIER (maximum expected barrier height), vs WTMetaD's HEIGHT + PACE + BIASFACTOR.
3. *Robust to bad CVs.* When the CV is suboptimal, OPES still converges (slowly); WTMetaD can get stuck or overshoot. This is documented on multi-basin systems where one basin has a hidden slow mode.
4. *Natural multi-replica extension.* OneOPES (Rizzi et al., JCTC 2023, DOI 10.1021/acs.jctc.3c00254) combines OPES replicas at different effective temperatures; it has been reported to produce reproducible GPCR-activation FESs (Alibay et al., JCTC 2025, DOI 10.1021/acs.jctc.5c00600).

**What WTMetaD still does better**:
1. *Exploration in the early phase.* WTMetaD dumps hills aggressively for the first ~10 ns; OPES is more conservative. For a system that has never been sampled before, WTMetaD finds basins faster (and OPES-Explore, a variant, fixes this).
2. *Literature-canonical.* For a replication project specifically, using the *original* method is the correct choice. You cannot claim to "reproduce Osuna 2019" if you use a different sampling algorithm, even a better one.

**Was OPES considered for this project?** Based on the project record (`CLAUDE.md`, `FEL_DEEP_DIVE_AND_NEW_DIRECTIONS.md` §6.2), no — the choice was locked by the replication mandate. A reasonable follow-up experiment after the baseline converges would be: re-run one TrpB variant with OPES at matched wall-clock and compare convergence. If OPES converges to the same FES in 30% of the time, the entire pipeline speed-up argument tilts toward OPES + ML-CV for the Phase-3 Lambert-screening workflow. This is the exact place where you can honestly tell Amin "yes, there is a better choice for the forward problem; we are using WTMetaD to match the benchmark".

---

## 2.9 Comparison table — the slide for the meeting

| Method | Recovers rates? | Needs good CV? | Scales to 600 res? | Convergence difficulty (1–5) | Software | Notes |
|---|---|---|---|---|---|---|
| Unbiased MD | Yes | No | Yes | 5 (never converges past 10 kT) | GROMACS/AMBER native | Your 500 ns baseline |
| Umbrella sampling | No (FES only) | Yes | Yes | 2 | GROMACS+PLUMED | Great if CV is known |
| Standard MetaD | Approximate | Yes | Yes | 4 (oscillates) | PLUMED | Obsolete; don't use |
| WTMetaD | Approximate (infreq. MetaD) | Yes | Yes | 3 | PLUMED | **Your method** |
| Multiple-walker WTMetaD | Approximate | Yes | Yes | 3 | PLUMED | Phase 2 plan |
| PBMetaD | Approximate | Partially | Yes | 3 | PLUMED | Good for many 1D CVs |
| BEMD | Approximate | Partially | Expensive | 4 | PLUMED | Replaced by PBMetaD/OneOPES |
| OPES (WT) | Approximate | Yes (more tolerant) | Yes | 2 | PLUMED 2.8+ | Better convergence, 1 knob |
| OneOPES | Approximate | Yes (more tolerant) | Yes, 8 replicas | 2 | PLUMED 2.8+ | Best 2023 tool for hard cases |
| T-REMD | No (ensemble) | No | No (~50 replicas) | 4 | GROMACS native | Dead for 40k-atom systems |
| REST2 | No (ensemble) | No | Yes, ~8 replicas | 3 | GROMACS+PLUMED | IDP/folding tool |
| ABF / extABF | No (FES) | Yes | Yes | 3 | NAMD, Colvars, PLUMED | Linear CVs; high-D struggles |
| String method (swarms) | No (path + FES) | No (finds path) | Yes | 4 | custom; Roux group scripts | Gold standard for *finding* path |
| SMD + Jarzynski | No (FES approx.) | Yes | Yes | 5 | GROMACS+PLUMED | Unreliable for ΔG > 5 kT |
| GaMD | Partially | No (CV-free) | Yes | 3 | AMBER pmemd.cuda | Miao group (UNC); broad but unfocused |
| WE / WESTPA | **Yes, rigorously** | Partially (progress coord) | Yes | 3 | WESTPA 2.0 | Best for rates |
| Deep-TDA + OPES | Approximate | Learns CV | Yes | 2 | PLUMED+mlcolvar+pytorch | 2024 state of the art |
| Committor-based | Yes (rigorous) | Validates CV | Barely | 5 | Custom | Validation, not production |

"Convergence difficulty" is my subjective wall-clock + tuning effort index. 1 = easy, 5 = will eat your quarter.

---

## 2.10 Decision tree — what to reach for when

Known CV, want equilibrium distribution → **WTMetaD or OPES**. US if the CV is 1D and you need rigorous error bars.

Known CV, want rate → **WE (WESTPA)**. Or infrequent metadynamics if you already have a MetaD pipeline and cannot invest in rewriting for WESTPA.

No good CV, small system (<200 residues, no explicit solvent shell issue) → **REST2** or T-REMD.

No good CV, large system (≥300 residues with explicit solvent) → **train Deep-TDA or DeepTICA from short unbiased MD → OPES or WTMetaD with learned CV**. This is the 2024–2025 state of the art.

Want to *discover* the reaction path (not just sample along a known one) → **string method with swarms of trajectories** (Roux/Chipot tradition). SPM on a prior unbiased ensemble is a cheaper, correlation-based alternative specifically for enzymes with allosteric coupling (Osuna 2024).

Memory effects / non-Markovian dynamics relevant → see Chapter 06 (to be written); key keywords are TICA lag choice, GLE, and generalized Langevin reweighting.

---

## 2.11 Why the lab chose WTMetaD + PATHMSD, and what they might revise

Osuna 2019 defaults are the result of two constraints: (a) the method had to be reproducible in GROMACS 5.1.2 + PLUMED 2 on the 2017–2018 HPC hardware available to them, and (b) they needed FES, not rates, for the enzyme-engineering question.

Given those constraints, the choice was correct:
- WTMetaD was the most-converged adaptive-bias method in 2018.
- PATHMSD gave a one-dimensional (s only, z restrained) CV that captured the O→C motion they could identify structurally from 1WDW and 3CEP crystal structures.
- 10 walkers made the 50–100 ns per walker budget tractable on their GPU queue.

What they might revise if starting today (2026):
- **CV**: switch to Deep-TDA learned from 100 ns of unbiased MD per state, trained on a descriptor set including PLP-pocket contacts. The single biggest defensible upgrade.
- **Sampler**: OPES-WELL-TEMPERED or OneOPES. Same FES, ~3× less wall time.
- **Path validation**: use ADAPTIVE_PATH or committor analysis to validate the linear-interpolation path; if it fails, the old FES numbers would be quantitatively off.
- **Stability analysis**: PLP parameters revisited with OpenFF 2.2 or Espaloma-0.3 instead of GAFF+RESP (per your FP-010 findings and the Osuna-lab 2025 parameterization updates).

None of these invalidates the replication. The replication is a necessary control for any of those upgrades to be meaningful — you need the baseline to subtract from.

---

## 2.12 The question Amin will ask, and your honest answer

*"Would OPES or a ML-learned CV have been better than PATHMSD-WTMetaD for TrpB O→C?"*

Answer: Probably yes for convergence speed. Almost certainly yes if the Cα-only path misses side-chain reorganization (Felts 2023's critique applies). But the 2019 paper defined a reference FES with PATHMSD-WTMetaD; to meaningfully compare any variant, the benchmark must match the original. Once Phase-1 replication is confirmed against the published FES, a targeted Phase-3 experiment — same TrpB variant, OPES-WT with a Deep-TDA CV trained on 100 ns of unbiased MD, matched wall-clock budget — is the natural novel contribution. Expected outcome, based on OPES benchmarks in similar systems (Invernizzi 2022, Rizzi 2023, Bonati 2024): ~2–3× convergence speedup and a possible reveal of a side-chain rotamer basin that Cα-only PATHMSD flattens out. If the side-chain basin appears, the lab's entire "FES shift as an activity proxy" framework may need one more coordinate. If it does not appear, PATHMSD is vindicated and OPES can be justified on speed alone.

That sentence is the meeting answer. It is neither defensive nor dismissive; it names the weakness of your own method while explaining why the current design is still the right call for this stage of the project.

---

## 2.13 Video and tutorial recommendations

If the written references are not enough, the following are *dense, practitioner-level* resources worth watching in order:

- **Giovanni Bussi — Metadynamics lectures** (YouTube; Trieste School on Molecular Dynamics). Bussi is a co-author of well-tempered MetaD. The classic pedagogical source. Start here if any WTMetaD derivation feels shaky.
- **PLUMED Masterclass 21.4 (Bussi et al.) and 22.3 (Invernizzi, "Rethinking Metadynamics")** — official tutorials on YouTube with GitHub inputs. 22.3 is the definitive OPES tutorial.
- **PLUMED Masterclass 22.9 (Ensing et al.) — Path CVs**. Covers PATHMSD, FUNCPATHMSD, ADAPTIVE_PATH with live demonstrations. Watch this before your next FP-020-style debugging session.
- **Luigi Bonati — ML collective variables** (EMBL-EBI seminars and CECAM Lugano 2023 talk on YouTube). Bonati wrote `mlcolvar`; the talk includes live Deep-TDA training.
- **CECAM tutorials on enhanced sampling** (multiple years, cecam.org/library). Particularly the 2023 and 2024 workshops on "ML for molecular simulations" — lecture recordings are public.
- **WESTPA workshops (LLNL/Pittsburgh)** — YouTube channel "WESTPA Weighted Ensemble". For when the rate-constant pivot becomes real.

---

## Self-check before the meeting

1. Can you state the Kramers arithmetic for τ_MFP at 350 K with a 10 kcal/mol barrier in under 30 seconds?
2. Can you name three enhanced-sampling families and give one concrete failure mode for each, without peeking?
3. What does BIASFACTOR=10 mean physically, and what changes if you used 5?
4. Why PATHMSD and not FUNCPATHMSD? What goes wrong if you flip to FUNCPATHMSD without rederiving λ?
5. For each of {US, WE, OPES, REST2, Deep-TDA+OPES}, name the one situation where it beats your current WTMetaD and the one reason you did *not* use it.
6. What is the honest weakness of your Cα-only PATHMSD that Felts et al. 2023 exposes, and what is the one-line rebuttal?

If any answer is shaky, do not go into the meeting. Re-read the relevant section above, and consult `MASTER_TECHNICAL_GUIDE.md` §6 for the WTMetaD-specific derivations.
