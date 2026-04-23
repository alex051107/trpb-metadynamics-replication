# Chapter 04 — Protein Design ML: The Stack Your Lab Is Actually Running

> **Audience**: Zhenpeng Liu, preparing for Caltech/Anima Lab summer research.
> **Prereqs**: Basic familiarity with proteins and MD. You don't need to have touched a generative model before.
> **Position in map**: 04 comes after (01) the TrpB biology, (02) the PLP chemistry, (03) the conformational dynamics story. This chapter explains the *design* half — what Raswanth and Amin are actually running — so you can talk to them without pretending.
> **Honest disclaimer**: The field moves fast. Papers listed here are accurate as of April 2026. Where the evidence is weak, I say so. Where things are marketing, I say so. The review at `project-guide/REWARD_FUNCTION_LITERATURE_REVIEW_v2.md` covers *reward functions* in depth; this chapter covers the *generation and filtering pipeline* and only recaps reward material where it changes the picture.

---

## 1. The three problems (and which one is TrpB)

There are three distinct "protein ML" problems, and people confuse them constantly.

**Forward folding — sequence to structure.** Given amino acids, predict 3D coordinates. This is the AlphaFold/RoseTTAFold problem. Solved ~80% for single-domain globular proteins; still broken for intrinsically disordered regions, multi-state allostery, large conformational change. This is *prediction*, not design.

**Inverse folding — structure to sequence.** Given a backbone, predict amino acids that will fold into it. This is ProteinMPNN / ESM-IF / LigandMPNN territory. Well-defined problem, good benchmarks, solved enough to be industrially useful. This is where you "paint" a sequence onto a scaffold.

**De novo design — target to structure to sequence.** Given a *functional specification* (a binding pocket, a catalytic geometry, an interface), invent both a backbone and a sequence that realizes it. RFdiffusion, Chroma, FrameDiff. This is the harder problem.

**Enzyme redesign**, which is what the lab is doing with TrpB, is mostly de novo scaffolding conditioned on a fixed *theozyme* — a quantum-mechanically-optimized geometric arrangement of catalytic residues around the transition state. The pipeline is: theozyme (chemistry-fixed) → scaffold (RFdiffusion) → sequence (MPNN) → refold check (RF) → dynamics check (MD) → binding check (MMPBSA / docking). Each arrow is lossy; the stack filters rather than optimizes end-to-end.

For TrpB specifically, the theozyme must hold (a) PLP covalently bound to Lys82 as an internal aldimine, (b) the α-carbon of the substrate positioned so the scissile bond is perpendicular to the PLP π-system per Dunathan (1966) — otherwise you get decarboxylation instead of deprotonation, or the wrong stereochemistry, and (c) a proton donor/acceptor positioned on the correct face of the planar quinonoid intermediate so reprotonation delivers the desired D vs L stereocenter. Standard protein design tools know nothing about (b) and (c). This is the gap.

## 2. Structure prediction: the lineage

**AlphaFold 2** (Jumper et al., 2021, *Nature*). The architecture has four moving parts. (i) An **MSA representation** built from retrieving homologous sequences — this gives evolutionary covariation signal (if two positions co-mutate, they're probably in contact). (ii) A **pair representation** encoding inter-residue distances and orientations. (iii) Evoformer blocks that iterate information between MSA and pair towers, letting geometry inform evolutionary interpretation and vice versa. (iv) A **structure module** with **Invariant Point Attention (IPA)** that outputs a backbone as a set of SE(3) frames (rotation + translation per residue), plus sidechain torsion angles. Training combined MSA reconstruction loss, distogram loss, per-residue confidence (pLDDT), and the frame-aligned-point-error (FAPE) on ground-truth structures. It beat everything at CASP14 by a wide margin. For single-domain globular proteins under ~500 residues with good MSA coverage, AF2 is accurate enough to use as a drop-in replacement for a crystal structure.

**AlphaFold-Multimer** (Evans et al., 2021, bioRxiv) adapted AF2 to hetero-oligomers. It's the tool most people use when they need a complex structure and don't want to dock. Accuracy is worse than for monomers and drops further on transient or weakly-evolved interfaces.

**AlphaFold 3** (Abramson et al., 2024, *Nature* 630:493) changed the architecture. Out: the Evoformer. In: a "Pairformer" feeding a **diffusion head** that denoises an atomic cloud directly. Crucially it now handles DNA, RNA, small-molecule ligands, ions, and modified residues. Reported gains: >50% improvement on protein–ligand complex prediction over docking, substantial gains on protein–nucleic-acid. Caveat: AF3 still overpredicts static structures — it's not giving you conformational ensembles, and for TrpB the O/PC/C states are not reliably recovered without tricks (multi-MSA, subsampling, template bias).

**RoseTTAFold** (Baek et al., 2021, *Science*) is the Baker-lab alternative. Three-track architecture (1D sequence, 2D pair, 3D structure) updated jointly. Was ~tied with AF2 at release and remains the scaffold under RFdiffusion. **RoseTTAFold 2** improved accuracy and compute. **RoseTTAFold All-Atom / RFAA** (Krishna et al., 2024, *Science* 384:eadl2528) is the major step: it unifies protein, DNA, small molecule, metal, and covalent-modification representations so you can model TrpB+PLP+substrate as one system. This matters for your work — with RFAA you can structurally reason about PLP as a bonded entity rather than a bolted-on docking target. The same paper introduced **RFdiffusionAA** for designing proteins around arbitrary small molecules.

**ESMFold** (Lin et al., 2023, *Science* 379:1123) skipped MSA entirely. A 15B-parameter protein language model (ESM-2) learns evolution implicitly from single-sequence training over ~65M proteins, and a structure head predicts coordinates. Accuracy is a notch below AF2 but inference is ~10× faster and works on orphan sequences with no homologs — important for the "designed novel sequences" use case where MSAs don't exist.

**Where these still fail.** Intrinsically disordered regions (all of them refuse to predict reasonably — IDRs are ensembles by definition). Multi-state proteins (TrpB's COMM domain is a textbook case; AF2 will return one state). Large allosteric transitions (the original validation against FEL comes from your Chapter 03). Membrane proteins beyond the simplest TM helix bundles. Novel folds — if a fold isn't in the PDB, predictions degrade.

## 3. Backbone generation: de novo design

**RFdiffusion** (Watson et al., 2023, *Nature* 620:1089). Fine-tune RoseTTAFold as a **denoising diffusion** model on protein backbones. Forward process adds SE(3) noise to coordinates; reverse process denoises. Trained to reverse that. At inference you start from noise and get a backbone. Capabilities validated: motif scaffolding (put these three catalytic residues in geometry X, invent a protein around them), binder design (hit this epitope), oligomer/symmetric assembly (C2/C3/D2...), unconditional generation. The Baker lab validated hundreds of designs experimentally with success rates (correct fold, binds target) of ~10–25% on non-trivial tasks — much higher than prior methods.

**RFdiffusion All-Atom / RFdiffusionAA** (Krishna et al., 2024, *Science*) added explicit ligand conditioning. You give it PLP coordinates, it generates a scaffold whose sidechains and backbone respect the ligand's atomic constraints (H-bond donors/acceptors, burial). Experimentally validated on digoxigenin, heme, bilin binders. This is the version that's directly relevant to TrpB.

**RFdiffusion2** (Ahern et al., 2024/2025 Baker lab series, see the metallohydrolase *Nature* 2025 paper, Kim, Woodbury, Ahern et al.) further relaxes constraints: you no longer need to specify both sequence position and backbone coords for each catalytic residue — the model figures out where to place them. Used to design zinc metallohydrolases with kcat/Km up to 53,000 M^-1 s^-1 (orders of magnitude better than prior designed metallohydrolases; still orders of magnitude below the best natural enzymes).

**RFdiffusion3 (December 2025)** treats *atoms* — not residues — as the diffusion units. Each residue is modeled with 4 backbone and 10 sidechain atoms. This enables direct conditioning on "make an H-bond donor here" rather than "place a serine". Reported 10× faster than RFdiffusion2 and winning on 37/41 active-site benchmarks and 90% of atomic-motif enzyme benchmarks. Open-sourced via Baker's Foundry. This is probably what Raswanth means when he says "RFD3" — it is the third-generation RFdiffusion line released Dec 2025 by the Baker lab, not an internal version name. **Confirm with Raswanth directly**, but the timing and naming match. ([IPD announcement, Dec 2025](https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available/), bioRxiv 2025.09.18.676967).

**Chroma** (Ingraham et al., 2023, *Nature* 623:1070) is Generate:Biomedicines' alternative. Joint sequence+structure diffusion with programmable "conditioners" — symmetry, shape, substructure, and even text-based conditioning. Designs large complexes in minutes on a commodity GPU. Philosophically different from RFdiffusion: Chroma is built to be programmable at inference, RFdiffusion is built around strong physical priors from RoseTTAFold.

**FrameDiff** (Yim et al., 2023, ICML) and **FrameFlow** (Yim et al., 2023, arXiv 2310.05297) are smaller, academic-scale models. FrameDiff operates on SE(3) rigid-body frames, FrameFlow is its flow-matching upgrade — 5× fewer sampling steps, 2× better designability. These are what academics use when they can't afford or don't need RFdiffusion. For your project, they're probably irrelevant — the lab is using RFD3.

## 4. Sequence design: inverse folding

**ProteinMPNN** (Dauparas et al., 2022, *Science* 378:49). A message-passing graph neural network. Nodes are residues, edges encode spatial relationships. Given a backbone, predict amino acids position-by-position. Trained on PDB. Native sequence recovery ~52%, far higher than Rosetta fixbb (~33%). Adopted across the field because it is fast (seconds per backbone), robust, and produces sequences that actually fold — AF2 re-folding validation shows 70–90% of MPNN outputs recover the target fold, compared to ~20% for Rosetta. This is the workhorse.

**LigandMPNN** (Dauparas et al., 2025, *Nature Methods* 22:717). ProteinMPNN that knows about non-protein atoms — ligands, nucleotides, metals. Native sequence recovery at binding-site residues jumps from 50% (MPNN) to 63% (LigandMPNN) for small molecules, 34% → 50% for nucleotides, 40% → 78% for metals. It also outputs sidechain conformations, not just sequences, so you can evaluate binding geometry. Over 100 experimentally validated small-molecule and DNA-binding proteins at time of publication. **This is the module your lab needs for TrpB** — PLP is a covalently bound ligand in the pocket, and regular MPNN will miss the geometric constraints around it. Ask Raswanth whether the stack uses vanilla MPNN or LigandMPNN at the sequence step.

**ESM-IF** (Hsu et al., 2022, ICML). Inverse folding via a Transformer on ESM-2 embeddings. Works well, sometimes slightly worse than MPNN at recovery but with better out-of-distribution generalization. Less common in production pipelines than MPNN.

**Where this fits in Raswanth's stack.** `RFD3 → MPNN → RF3` reads as: generate a backbone conditioned on the theozyme; paint amino acids onto the backbone; re-predict the structure from the painted sequence with an RF variant (RoseTTAFold or AF2) to check it folds back. This "self-consistency" loop is the field's de facto filter for "is this a real protein or an RFdiffusion artifact". Success criterion: Cα RMSD of RF prediction to RFD3 backbone below ~2 Å, pLDDT above ~80. Everything that fails either step is discarded before docking even runs.

## 5. Theozymes and enzyme design philosophy

"Theozyme" was coined by Tantillo, Chen, and Houk (1998, *Curr Opin Chem Biol* 8:743) and operationalized by the Houk lab for decades. Procedure: compute the transition state of the desired reaction at DFT level in the presence of a minimal set of catalytic side-chain analogs (methylamine for Lys, propionate for Glu, etc.), optimize the geometry, freeze the relative positions. That frozen geometry is the theozyme. It tells you "these chemical groups, in this arrangement, stabilize this transition state by X kcal/mol." The design problem becomes: find a protein scaffold that holds that arrangement.

**Baker-lab enzyme design history — the honest version.**

*Röthlisberger et al., 2008, Nature*. Kemp eliminase — proton abstraction from 5-nitrobenzisoxazole. Eight designs, rate enhancements up to ~10^5. Big milestone. But kcat/Km was ~5 M^-1 s^-1, roughly 10^9-fold below diffusion. Directed evolution by Hilvert's group and others pushed KE07/KE70/KE59 up ~2000× to the 10^5–10^6 range — meaning 99.9% of final activity came from evolution, not design.

*Retro evaluation*. Honestly? The designed scaffold held the catalytic base roughly in place, but the geometry wasn't tight enough, the dynamics were wrong (see Kamerlin/Warshel critiques, PNAS 2010), and active-site water and preorganization were not modeled. For a decade this was the unspoken ceiling: design got you a starting point; evolution did the real work.

*Hilvert's RA95 retro-aldolase* evolved from a computational design up to kcat/Km ~10^5 M^-1 s^-1, but again directed evolution did the heavy lifting.

*2025 inflection*. The Baker lab now claims near-natural catalytic efficiency directly from computation. *Computational design of serine hydrolases* (Lauko/Anishchenko et al., Feb 2025, *Science* 387:eadu2454) reached kcat/Km up to 2.2×10^5 M^-1 s^-1 with Cα RMSD to design <1 Å — directly from RFdiffusion + new scorers, without multiple rounds of evolution. *Computational design of metallohydrolases* (Kim, Woodbury, Ahern et al., 2025, *Nature*) reached kcat/Km up to 53,000 M^-1 s^-1 from just 192 designs tested total. This is genuinely different from 2008 — order-of-magnitude improvements per design round, crystal structures matching computational predictions to sub-angstrom.

**Why the 2025 gains.** Three things. (i) RFdiffusion2/3 makes scaffolds that actually hold geometry. (ii) **PLACER** (see next section) rapidly filters designs whose active site geometry breaks down under conformational sampling. (iii) Scale — instead of testing 8 designs they test 96–192 and use computational scorers to pick the winner.

**What this means for TrpB**. Standalone TrpB redesign has a head start: you're not designing a new fold, you're modifying an existing one. The theozyme problem is reduced to finding the geometric tweaks that make the PLP pocket accept D-serine's opposite stereochemistry and deliver the proton to the re- rather than si-face of the quinonoid. The 2025 Baker-lab successes are on simpler reactions (hydrolysis) with flat substrates. PLP chemistry is harder — covalent cofactor, planar intermediate, stereochemistry constraint. Manage expectations.

## 6. GenSLM — the Argonne line

**GenSLM** (Zvyagin et al., 2023, *Int J High Perform Comput Appl* 37, Gordon Bell Special Prize 2022; Ramanathan lab, Argonne). Autoregressive transformer trained on ~110M prokaryotic *gene* sequences — codon-level tokenization, 64-token vocabulary instead of 20 amino acids. Originally validated on SARS-CoV-2 variant analysis. Generalized since then. 25M-parameter version is what Argonne uses for most protein tasks; larger versions exist.

**Why codon-level?** Two arguments. (i) Codon usage carries information about translation efficiency, mRNA folding, and expression that amino-acid-only models discard. (ii) The model learns evolutionary statistics at the DNA level, which is where selection actually operates. Lambert et al. (2026, *Nat Commun* 17:1680) fine-tuned GenSLM on ~30,000 TrpB DNA sequences and generated thousands of novel TrpBs, some with room-temperature activity and promiscuity absent from natural enzymes — GenSLM-230 beat PfTrpB-0B2 on native and non-native substrates. 11 of 11 purified designs showed activity; expression yields averaged 84 mg/L.

**Honest caveats.** (i) Codon-level tokenization sounds great but all the downstream scorers (ESM, MPNN, Rosetta, MD) work at the amino acid level — synonymous codon variation is invisible to reward signals, so the codon-level advantage collapses at evaluation time. Amin's work is partially about closing this gap. (ii) GenSLM generates *plausible* sequences; whether they're catalytically better is a separate question solved by the filter stack. (iii) The 11/11 success rate was after aggressive heuristic filtering (start codon, length, active-site conservation) — the raw generative quality is much lower. A learned reward function would plausibly do better than heuristics, which is why this whole pipeline exists.

**How GenSLM fits with RF.** GenSLM generates sequences; RoseTTAFold/AF2 fold them; downstream MD/docking validates. It's complementary to RFdiffusion rather than competing — RFdiffusion starts from a *geometric* specification (theozyme), GenSLM starts from *evolutionary* distribution (thousands of natural TrpBs). In your lab's stack, GenSLM is upstream sequence generation that feeds into the same MD/MMPBSA/GRPO filter as the RFD3 pipeline.

## 7. The reward/filter stack (the research frontier)

This is where the lab is actually iterating. Read the reward review (`REWARD_FUNCTION_LITERATURE_REVIEW_v2.md`) for the exhaustive version; here is what *changed* with Raswanth's 4/4 pivot.

**PLACER** (Jadhav, Lauko, Baker et al., 2024, *Science* for the serine-hydrolase paper, also published separately as the PLACER method). PLACER = **P**rotein–**L**igand **A**tomistic **C**onformational **E**nsemble **R**eproduction. A deep neural network trained on PDB protein–small-molecule complexes to predict active-site atomic arrangements — hydrogen bond geometries, rotamer packing, sidechain positioning around ligands. Critically, PLACER can generate *ensembles* for each step of a reaction (substrate, TS, product, intermediates), so you can check whether catalytic residues adopt the active conformation *throughout* the mechanism rather than at just one snapshot. It's fast — seconds to minutes per design, not the hours/days of MD. This is Raswanth's **F0 fidelity** and the one that now enters GRPO.

**GRPO** — Group Relative Policy Optimization (Shao et al., 2024, *DeepSeekMath*, arXiv 2402.03300). Variant of PPO that *removes the value/critic network*. Instead of learning a value function to estimate advantages per-token, GRPO samples N completions per prompt, computes the reward for each, and uses the *group mean* as the baseline. Advantage for completion i = (reward_i − mean(reward_group)) / std(reward_group). Policy update uses the standard PPO-style clipped objective. Saves roughly 50% compute and memory versus PPO (no critic to train), which matters when the policy is a protein language model at GPU-scale.

**GRPO vs DPO** (Rafailov et al., 2023, NeurIPS). DPO sidesteps RL entirely by reparameterizing the reward model as implicit in the policy — you train on paired (preferred, rejected) examples with a classification loss. Simpler, more stable than PPO/GRPO, but needs *pairs* and optimizes *relative* preference. GRPO takes *absolute* scalar rewards and handles continuous reward signals directly. For protein design, PLACER outputs a continuous score per design, so GRPO is the better fit. DPO shows up when you have expert-curated A-vs-B judgments or experimental yes/no assays — ProtRL (Widatalla et al., 2024, arXiv 2412.12979) uses both weighted-DPO and GRPO for ZymCTRL, producing EGFR binders with K_d from ~800 nM down to 27 nM. That's the reference application to protein design.

**MFBO — Multi-Fidelity Bayesian Optimization**. Foundational work: Kennedy & O'Hagan (2000, *Biometrika* 87:1) — a Gaussian-process framework where low-fidelity and high-fidelity simulations share an autoregressive correlation. Modern treatment: Poloczek et al. (2017, NeurIPS) on knowledge-gradient acquisition. Core idea: you have several simulators of the same function with different accuracy/cost trade-offs — cheap-and-noisy (F0 = PLACER, seconds), medium (F1 = short MD, hours), accurate-and-expensive (F2 = MMPBSA on 50–100 ns, days). A single GP models all fidelities jointly; the acquisition function decides *which fidelity to query next for which candidate* based on (value of information) / (cost). You end up spending most of F0 query budget on broad exploration, F1 on narrowing, F2 only on the final shortlist.

2024/2025 application to chemistry: Lin et al., 2025, *ACS Central Science*, "Bayesian Optimization over Multiple Experimental Fidelities Accelerates Automated Discovery of Drug Molecules" — concrete demonstration that MFBO beats single-fidelity BO on real drug-discovery campaigns. Fare et al., 2025, *Nature Computational Science*, "Best practices for multi-fidelity Bayesian optimization in materials and molecular research" — current guideline paper. These are the references to cite when talking to Amin or Raswanth.

**Why Raswanth's 4/4 pivot is smart**. The original plan was: F0+F1+F2 all enter GRPO as a composite reward. Reward hacking is a well-documented risk (Weng 2024 *Lil'Log*; and for molecular design specifically: Feng et al., 2025, *Nat Commun*, "A data-driven generative strategy to avoid reward hacking"). The fidelity most vulnerable to hacking is MMPBSA — it's noisy (Genheden & Ryde, 2015, *Expert Opin Drug Discov*), sensitive to simulation length (50 ns is borderline), and can be "exploited" by designs with bizarre solvation terms that score well but don't reflect real binding. Once MMPBSA is in the gradient update, the generator learns to produce these exploits. Raswanth's fix: **F0 (PLACER) is the only reward that enters GRPO** (fast, geometric, hard to hack — you can't fake H-bond geometries without actually placing them); **F1 (MD) and F2 (MMPBSA) enter MFBO** as expensive-but-accurate oracles that rank a shortlist. The generator never sees MD/MMPBSA reward directly, so it can't learn to game them. Good separation of concerns. This mirrors RLHF practice: reward models that are too smooth or too expensive go outside the RL loop, acting as late-stage selection rather than gradient signal.

## 8. Failure modes (concrete, per stage)

**RFdiffusion failure mode**: produces backbones that *look* protein-like but don't round-trip through MPNN+AF2. Fraction that fails self-consistency depends on the task — ~10–30% for simple binders, higher for multi-chain or ligand-conditioned. Current mitigation: generate more, filter harder. RFdiffusion3 improves this but doesn't eliminate it.

**MPNN failure mode**: hands you high-pLDDT sequences that, under MD, lose active-site geometry. The backbone RMSDs look fine for 100 ns, then a key H-bond breaks and the pocket opens. This is why the MD filter exists — it's the cheapest way to catch "structurally passable but dynamically broken" designs.

**Docking (Vina) failure mode**: scoring function correlation to experimental ΔG is ~0.5 (Pearson) across standard benchmarks (Wang et al., 2016, *PCCP* — DUD-E benchmark; and various chemrxiv re-analyses). That's useful for *ranking* within a narrow chemical series but uninformative for absolute binding prediction. Vina also famously misses induced-fit rearrangement — it treats the receptor as rigid by default, and TrpB's COMM domain is anything but rigid.

**MMPBSA failure mode**: convergence requires ≫50 ns for flexible complexes (Hou et al., 2011, *J Chem Inf Model* 51:69; Genheden & Ryde, 2015). Standard deviation within a single 50 ns run can easily be 5–10 kcal/mol, which is larger than the experimental ΔΔG you're trying to distinguish. Entropy terms (normal mode analysis or interaction entropy) add more noise. Many MMPBSA campaigns report beautiful rank correlations that collapse on independent re-simulation. The correct way to use MMPBSA is as a *tie-breaker on a shortlist*, never as a primary ranking signal.

**All of the above → the ground-truth problem**. Your pipeline has six lossy stages and no stage has a quantitative correlation to experimental activity above ~0.5. This is where **MetaDynamics / your dynamics work plugs in**: FEL-based scoring of a final shortlist (5–10 variants) gives a *mechanistically interpretable* signal — does this variant actually close the COMM domain? — that neither docking nor MMPBSA can provide. It's slow (~500 ns + PLUMED = days per variant), but *unhackable* in a way MMPBSA isn't, because the generator can't plausibly produce a variant that fakes an FEL minimum without genuinely restructuring dynamics.

## 9. Where TrpB diverges from every standard design benchmark

Every binder-design benchmark in the Baker papers involves a small molecule (digoxigenin, heme, bilin) sitting in a pocket as a **static** ligand. That's not TrpB.

PLP is **covalently attached** to Lys82 as a Schiff base. Standard docking pipelines remove covalent partners; you need to either parameterize the covalent ligand (RESP charges on the Ain/Aex1/quinonoid adducts, which is your Chapter 02 work) or design constraints around an adducted state. Neither docking, Vina, AutoDock, MMPBSA's default ligand workflow, nor MPNN's default ligand modeling handles covalent cofactors correctly. You have to patch around every stage.

The **quinonoid intermediate is planar** — nearly sp² at Cα — and faces two possible reprotonation directions. One gives L-Trp; the other gives D-Trp. The enzyme's job isn't to "hold the substrate" but to bias the reprotonation *face*. This is a stereochemistry constraint on the *dynamic trajectory* of a proton, not a static geometry constraint. Theozyme-based design can specify the geometry of the donor (e.g., Glu197 sidechain at distance X from Cα on the re-face), but whether the design *preserves* that geometry under thermal motion is a dynamics question. Static-pocket scoring misses it entirely.

**Dunathan orbital alignment** — the scissile bond must be perpendicular to the PLP π-system or you get the wrong chemistry (decarboxylation instead of β-elimination, or the wrong reaction altogether). This is an angular constraint that ProteinMPNN, LigandMPNN, Vina, and MMPBSA all ignore. PLACER might catch it (ensemble scoring with the PLP adduct present), but only if the training data included enough PLP-adduct chemistry, which it probably didn't.

**Bottom line**: standard pipelines treat PLP like a bolted-on cofactor. The chemistry demands a **chemistry-aware validator**. That's the angle your metadynamics work opens up — CV design that probes Dunathan angle, reprotonation face, and COMM closure simultaneously. If you can demonstrate that FEL-based scoring separates D-Trp-selective from L-Trp-selective designs on a retrospective TrpB dataset, that's a publishable contribution *and* a concrete reason the lab needs you.

## 10. Pros/cons matrix

| Tool | Stage | Ligand-aware | Accuracy (as of 2026) | Speed | Main failure mode | When to trust |
|---|---|---|---|---|---|---|
| AlphaFold 2 | Structure pred | No | High on monomers, low on multi-state | ~min/seq | One static state only | Single fold, good MSA |
| AlphaFold 3 | Structure pred | Yes (limited) | Better than docking on complexes | ~min/seq | Still static; limited ligand training | Complex geometry baseline |
| RoseTTAFold-AA | Structure pred | Yes | ≈AF3 on tested benchmarks | ~min/seq | Same as AF3 | When you need protein+ligand+DNA |
| ESMFold | Structure pred | No | ~10% worse than AF2 | ~10× faster than AF2 | Poor on orphan/disordered | Orphan sequences, screens |
| RFdiffusion 1/2 | Backbone gen | Partial (AA version) | High designability | ~min/design | Self-consistency fails ~10–30% | Well-defined motif |
| RFdiffusion 3 | Backbone gen | Full atomic | Best in class (Dec 2025) | ~10× faster than RFD2 | Too new to know; benchmarks only | Active-site design |
| Chroma | Backbone gen | Via conditioners | Competitive | ~min/design | Less validated on enzymes | Programmable conditioning |
| FrameDiff/Flow | Backbone gen | No | Good for its size | Fast | Smaller model, limited tasks | Academic reproduction |
| ProteinMPNN | Sequence | No | 52% NSR, high fold recovery | sec/design | Misses ligand interactions | Apo scaffold |
| LigandMPNN | Sequence | Yes | 63%/77% NSR on small molecule/metal sites | sec/design | New; limited cofactor coverage | Holo scaffold, your case |
| ESM-IF | Sequence | No | ≈MPNN, better OOD | sec/design | Less used in production | Unusual folds |
| GenSLM | Sequence (de novo) | No | 11/11 active TrpBs after filtering | min/seq generated | Codon-level advantage lost downstream | Distribution-matched novelty |
| PLACER | Filter F0 | Yes | Captures geometric preorganization | ~sec–min/design | Training data chemistry gaps | Geometric sanity check, GRPO reward |
| Docking (Vina) | Filter | Yes | Pearson ~0.5 vs exp | ~s–min/design | Rigid receptor, ignores covalent | Ranking within series only |
| Short MD (F1) | Filter | Yes | Captures short-timescale instability | hours/design | Too short for slow motions | Catches blatant unfolding |
| MMPBSA (F2) | Filter | Yes | Noisy | days/design | Convergence, entropy, solvation | Shortlist tie-breaking |
| MetaDynamics / FEL | Filter | Yes (with custom params) | Best mechanistic signal | days–weeks/design | Expensive; CV design required | Top 2–5 final candidates |

## 11. Meeting prep Q&A

*For the Amin meeting or any lab conversation where you want to look competent.*

**Q1 — "Why LigandMPNN over ProteinMPNN for this project?"** Because PLP is a covalently bound cofactor in every TrpB pocket. ProteinMPNN native-sequence recovery at ligand-contacting residues is 50%; LigandMPNN is 63%. A 13-point gap on the 10–15 residues that define chemistry is meaningful. If the stack is still on vanilla MPNN, that's an obvious upgrade to propose.

**Q2 — "Why is RFdiffusion3 the right scaffolder for us?"** Atomic-resolution conditioning on the PLP adduct rather than residue-resolution. 37/41 active-site benchmarks won over RFD2. Direct conditioning on "H-bond donor here, carbonyl oxygen here" which is what a theozyme specifies. If the alternative is RFD2 or RFAA, the upgrade path is clear — but also flag that RFD3 is 4 months old (Dec 2025) and benchmarks are from the paper authors themselves.

**Q3 — "Explain GRPO like I've only seen PPO."** GRPO removes the critic/value model. Instead of learning a per-token value function, it samples a group of completions per prompt, uses the group mean reward as the baseline, and the group std as the normalizer. Advantage = (reward − group mean) / group std. Then standard clipped policy-gradient update. Saves ~50% compute vs PPO. Originally from DeepSeekMath (Shao et al., 2024). First protein application: ProtRL (Widatalla et al., 2024).

**Q4 — "Why does only F0 enter GRPO?"** Reward hacking. PLACER is geometric and hard to fake. MD/MMPBSA are noisy, expensive, and can be exploited by generators that learn pathological solvation tricks. Keep the gradient signal clean; use MD/MMPBSA as MFBO oracles for selection rather than optimization. Standard RLHF hygiene applied to protein design.

**Q5 — "How does MFBO actually allocate budget?"** Gaussian process over (candidate × fidelity). Acquisition function — typically knowledge-gradient or entropy-search — computes expected information gain per dollar of compute for each (candidate, fidelity) pair. You spend lots of cheap F0 queries to identify the Pareto front, a few F1 MD queries to narrow, F2 MMPBSA only on the final 5–10 candidates. Reference: Kennedy & O'Hagan 2000, Poloczek et al. 2017; recent molecular applications: Fare et al., 2025, *Nat Comput Sci*.

**Q6 — "What's the stereochemistry risk you see in the D-serine project?"** Two. (i) Dunathan — scissile bond perpendicular to PLP π-system. If the design drifts off that geometry even slightly, you lose rate or get the wrong reaction. (ii) Reprotonation face — the quinonoid is planar, so the enzyme has to bias which face gets the proton back. Static-pocket scoring (MPNN, Vina, even MMPBSA) doesn't see this; it's a dynamic geometry problem on the femtosecond-picosecond timescale of proton transfer.

**Q7 — "What does MetaDynamics add that their current stack doesn't?"** COMM-domain FEL. Osuna 2019 showed that catalytic efficiency in TrpB correlates with O→C closure energetics, and 5 of 6 activity-enhancing mutations in PfTrpB-0B2 are distal to the active site. Your MetaD setup probes whether a designed variant actually closes. Docking/MMPBSA score static pockets; FEL scores the conformational ensemble the pocket lives in. Different fidelity, different information.

**Q8 — "What would you want the lab to share so you can contribute?"** (i) Which stereochemistry is the GRPO reward currently rewarding (D vs L) — is it even chirality-aware, or just "stable pocket"? (ii) The 12 theozymes targeting 104–109, 298, 301 — what was the selection criterion, and are any of them near the Dunathan axis through Lys82–PLP? (iii) Whether vanilla MPNN or LigandMPNN is in the sequence step. (iv) The MD protocol — classical MD or enhanced sampling, PLP bonded or fixed, buffer/ionic conditions.

---

## Further reading and videos

**Videos** (YouTube, watch these before the Amin meeting).

- David Baker, "Design of New Protein Functions Using Deep Learning," In Silico Drug Discovery Workshop, Oct 2024 — YouTube `EcPCQC1_4Ks`. Best single overview of the whole Baker-lab stack as of late 2024; pre-dates RFD3 but covers RFD2, RFAA, LigandMPNN.
- Search "RFdiffusion walkthrough" on YouTube — several community paper-walkthroughs from 2023–2024 exist (Yannic Kilcher, AI Coffee Break, etc.). Use one of these if you want the diffusion math explained slowly.
- Sergey Ovchinnikov talks on ColabDesign / AlphaFold hallucination — he's moved to MIT and gives frequent public talks; search YouTube for "Ovchinnikov protein design 2024". Useful counterpoint: design-as-inverted-prediction rather than design-as-diffusion.
- Arvind Ramanathan Argonne talks — his BNL ModSim 2025 slides (linked from [bnl.gov/modsim](https://www.bnl.gov/modsim/events/2025/)) cover GenSLM + multi-scale integration; Argonne's ALCF YouTube channel has several Ramanathan-group talks.
- Nazim Bouatta's MLCB and Harvard lectures on AlphaFold — if you want the foundational pipeline explained rigorously.

**Key papers to actually read (not just skim)** — in priority order for this meeting:

1. Dauparas et al. 2025 *Nature Methods* — LigandMPNN. 30 minutes. Highest ROI.
2. Shao et al. 2024 arXiv 2402.03300 — GRPO / DeepSeekMath. Section 4 only. 45 minutes.
3. The RFdiffusion3 preprint (bioRxiv 2025.09.18.676967) — abstract + benchmark table. 20 minutes.
4. Kennedy & O'Hagan 2000 — MFBO foundation. Difficult but short. 60 minutes.
5. The Baker serine-hydrolase *Science* 2025 paper — the PLACER workflow is the template your lab is reproducing. 90 minutes.
6. Lambert et al. 2026 *Nat Commun* — GenSLM + TrpB. 60 minutes. This is the paper that established Amin's project.
7. Osuna 2019 *JACS* — if you haven't already absorbed it, this is the reason your MetaD work matters.

**Sources for this chapter**

- [RFdiffusion3 announcement (IPD, Dec 2025)](https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available/)
- [RFdiffusion3 bioRxiv preprint](https://www.biorxiv.org/content/10.1101/2025.09.18.676967v2)
- [LigandMPNN Nature Methods 2025](https://www.nature.com/articles/s41592-025-02626-1)
- [AlphaFold 3 Nature 2024](https://www.nature.com/articles/s41586-024-07487-w)
- [RoseTTAFold All-Atom Science 2024](https://www.science.org/doi/10.1126/science.adl2528)
- [Computational design of serine hydrolases (Baker lab 2025)](https://www.science.org/doi/10.1126/science.adu2454)
- [Computational design of metallohydrolases (Baker lab 2025)](https://www.nature.com/articles/s41586-025-09746-w)
- [Chroma Nature 2023](https://www.nature.com/articles/s41586-023-06728-8)
- [DeepSeekMath / GRPO paper](https://arxiv.org/abs/2402.03300)
- [DPO paper (Rafailov 2023)](https://arxiv.org/abs/2305.18290)
- [Best practices MFBO in molecular research (Nat Comput Sci 2025)](https://www.nature.com/articles/s43588-025-00822-9)
- [MFBO in drug discovery (ACS Cent Sci 2025)](https://pubs.acs.org/doi/10.1021/acscentsci.4c01991)
- [ESMFold Science 2023](https://www.science.org/doi/10.1126/science.ade2574)
- [GenSLM IJHPCA 2023](https://journals.sagepub.com/doi/10.1177/10943420231201154)
- [MM/PBSA review (Genheden & Ryde 2015)](https://pubs.acs.org/doi/10.1021/acs.jctc.1c00374)
- [Controlling reaction specificity in PLP enzymes (Dunathan)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3359020/)
- [Theozymes (Tantillo, Chen, Houk 1998)](https://www.ch.ic.ac.uk/local/organic/pericyclic/theozyme.pdf)
