# STAR-MD (ByteDance Seed, Feb 2026) — Round 1 Scientific Context Review

**Paper:** Shoghi, Liu, Shen, Brekelmans, Li, Gu. *Scalable Spatio-Temporal SE(3) Diffusion for Long-Horizon Protein Dynamics.* arXiv:2602.02128v2, 11 Feb 2026.
**Project page:** https://bytedance-seed.github.io/ConfRover/starmd (note: hosted *under* ConfRover project)
**Reviewer role:** Scientific-context researcher (round 1)
**Date:** 2026-04-17

---

## 1. ATLAS benchmark — what it actually is

ATLAS is the database introduced by Vander Meersche, Cretin, Gheeraert, Gelly & Galochkina in *Nucleic Acids Research* Jan 2024 (https://academic.oup.com/nar/article/52/D1/D384/7438909; https://www.dsimb.inserm.fr/ATLAS). Verified properties:

- **1,390 protein chains** selected from the PDB (July 2022), ≥38 residues, resolution ≤2 Å, non-membrane. Non-redundancy enforced at ECOD X-class level (1,149 non-redundant domains). 322 of the 1,068 core proteins receive extra simulations of alternative high-quality structures → 1,390 chains total.
- **Simulation protocol:** GROMACS v2019.4, **CHARMM36m force field**, **TIP3P water**, 150 mM Na⁺/Cl⁻, 3 replicates of **100 ns** production per chain, 2 fs timestep, coordinates every 10 ps.
- Two specialty sub-datasets: Dual Personality Fragments (100) and Chameleon sequences (32), totaling 1,522 chains / 4,566 trajectories / **456.6 μs aggregate** / 13.2 TB raw.

**Critical limitations (acknowledged by ATLAS authors):**
- "three replicates of 100 ns simulations ... limited for exploration of rare events or major conformational rearrangements of large proteins." Pearson correlation of RMSF between replicates averages only ~**0.88**, an empirical *upper bound* for any model trained on ATLAS RMSF.
- CHARMM36m + TIP3P is a reasonable but not universally validated force field for long timescales; sidechain rotamer statistics and protonation states are default.
- **No ligands, no explicit binding partners.**
- **No standard train/test split is defined in the ATLAS paper itself.** The split STAR-MD uses comes from downstream ML papers, specifically the MDGen (Jing et al. 2024, https://arxiv.org/abs/2409.17808) and ConfRover (Shen et al. 2025, https://arxiv.org/abs/2505.17478) protocols: a temporal split where the 82-protein test set consists of PDB entries deposited after 1 May 2019. STAR-MD writes "standard train/val/test splits from prior works [13, 26]" — this is accurate but worth flagging that "standard" here means *the split the co-author's own prior paper chose*, not an ATLAS-authored gold standard.

**Is the split rigorous?** Partially. The post-2019 deposition cutoff provides temporal leakage protection, but does not guarantee structural/fold-level separation — nothing prevents a 2019 test protein from being a close homolog of a 2018 training protein. ProteinBench-style redundancy filters (MMseqs2 at 30% seq-id, or CATH/SCOP at fold level) are stricter and not used here.

## 2. ConfRover — the prior work from the same group

ConfRover (Shen, Wang, Yuan, Wang, Yang, Gu, NeurIPS 2025, https://neurips.cc/virtual/2025/loc/san-diego/poster/116440; arXiv:2505.17478, https://arxiv.org/abs/2505.17478) is by the **same senior authors (Shen + Gu) as STAR-MD**. Shared first-author Yuning Shen and corresponding author Quanquan Gu appear on both.

ConfRover's architecture (verified via arXiv abstract):
1. FrameEncoder built on a protein folding module producing single + pair features
2. A temporal module over frames
3. An SE(3) diffusion decoder

Claim: "**first model to sample both protein conformations and trajectories within a single framework**." Benchmark: ATLAS.

**Architectural contrast with STAR-MD** (from STAR-MD §3.2 and Appendix B):
- ConfRover retains **pairwise features + Pairformer/triangular attention** → O(N³L) spatial + O(N²L²) temporal cost, and critically **O(N²L) KV-cache** because it does temporal attention over pair features.
- STAR-MD projects *out* pair features for the temporal axis, doing **joint spatio-temporal attention on singles only** → O(N²L²) compute but only **O(NL) KV cache**. This is the dominant practical advantage claimed.
- STAR-MD adds: continuous-time ∆t conditioning (LogUniform[10⁻², 10¹] ns), contextual noise perturbation à la Diffusion Forcing (Chen et al. 2024), block-causal training.

**Bias risk:** Same lab / same corresponding author / project page hosted under /ConfRover/. STAR-MD's long-horizon comparison uses a **ConfRover-W** variant (windowed attention with sinks from StreamingLLM, Xiao et al. 2023) because full ConfRover blows memory at 240 ns / 1 μs. That is a legitimate fair-comparison choice, but also conveniently makes the prior work look worse at long horizons — **Table 2 does not show full ConfRover at 100 ns vs long ConfRover-W to separate "the prior method fails" from "the windowed hack fails."** An honest ablation would report ConfRover-W at 100 ns too.

## 3. MDGen — is it the right baseline for μs?

MDGen (Jing, Stärk, Jaakkola, Berger, NeurIPS 2024, https://proceedings.neurips.cc/paper_files/paper/2024/hash/478b06f60662d3cdc1d4f15d4587173a-Abstract-Conference.html; https://arxiv.org/abs/2409.17808; https://github.com/bjing2016/mdgen):

- Tokenizes trajectories into SE(3)-invariant tokens (residue offsets vs keyframes + torsion angles).
- Backbone: Scalable Interpolant Transformer (SiT); for long trajectories, replaces time-wise attention with **Hyena** long-context op → proof-of-concept scaling to *tetrapeptide* trajectories of 100k frames.
- ATLAS protein setup: 250 frames subsampled every 40 → effectively covers ~100 ns, conditioned on first frame (forward simulation).
- MIT news piece (https://news.mit.edu/2025/toward-video-generative-models-molecular-world-0123) describes MDGen as "10-100× faster than physical simulation" but at a fixed horizon per sample.

**Is MDGen a fair μs baseline?** Not really designed for autoregressive μs rollout. Its ATLAS model is a **fixed 250-frame / keyframe-anchored** generator. STAR-MD (§4.1) says MDGen "is generated at native resolution and then subsampled" — at 1 μs this means either extending by keyframe re-anchoring (lose memory between windows — STAR-MD itself flags this in §2 Related Work) or extrapolating far beyond training distribution. MDGen's failure at 1 μs (56% all-atom validity falling to 25% CA+AA) is not surprising because it was not designed for that regime.

**Takeaway:** Comparing STAR-MD to MDGen at 1 μs is technically legitimate — no other open model exists — but the headline "baselines fail catastrophically" partially reflects that the baselines weren't built for this setting. This deserves acknowledgement in STAR-MD's framing.

## 4. AlphaFolding / AlphaFlow / BioEmu — apples-to-apples?

**AlphaFolding** (Cheng et al., AAAI 2025, https://arxiv.org/abs/2408.12419; https://github.com/Kaihui-Cheng/AlphaFolding) — Fudan + Alibaba DAMO. 4D diffusion over dynamic structures with reference-frame and motion-alignment modules. It *is* trained on MD trajectory data. So yes, it is an in-class trajectory baseline. STAR-MD's complaint about scalability (OOMs on 4 largest ATLAS test proteins) is consistent with the AAAI paper's architecture leaning heavily on Pairformer-style modules.

**AlphaFlow** (Jing, Berger, Jaakkola, ICML 2024, https://arxiv.org/abs/2402.04845; https://github.com/bjing2016/alphaflow) — this is an **ensemble sampler**, not a trajectory model. Repurposes AlphaFold as a flow-matching generator over the equilibrium distribution. Different problem class: AlphaFlow answers "what conformations does this protein adopt?" not "what does its trajectory look like over time?" STAR-MD cites it (ref [12]) but does *not* benchmark against it, which is correct — AlphaFlow would look good on coverage but has no dynamic fidelity metric.

**BioEmu** (Lewis et al., Microsoft Research; bioRxiv Dec 2024 https://www.biorxiv.org/content/10.1101/2024.12.05.626885v1; published *Science* July 2025 https://www.science.org/doi/10.1126/science.adv9817; code at https://github.com/microsoft/bioemu). Trained on >200 ms of aggregated MD + 500k MEGAscale stability measurements. Claims **"thousands of statistically independent structures per hour per GPU"** and **≈1 kcal/mol accuracy** on relative free energies vs ms MD. BioEmu is explicitly an **equilibrium ensemble emulator, not a trajectory model** — it samples independent structures i.i.d., with no time ordering. STAR-MD cites it (ref [16]) but doesn't benchmark against it. That's correct for a trajectory benchmark but hides the fact that BioEmu may dominate STAR-MD on the only question that actually matters for many downstream applications: "does the ensemble cover the right states with the right relative populations?"

**Summary of the comparison matrix:**

| Model | Problem | Time ordering? | Microsecond-scale? | Head-to-head in STAR-MD Tables 1-2? |
|-------|---------|----------------|---------------------|-------------------------------------|
| MDGen | Trajectory (keyframe-anchored) | Yes (within window) | Not designed for | Yes |
| AlphaFolding | Trajectory (4D diffusion) | Yes | Not designed for | Yes (partial — OOMs on 4 proteins) |
| ConfRover / ConfRover-W | Trajectory (autoregressive) | Yes | Partial (needs windowing) | Yes |
| AlphaFlow | Equilibrium ensemble | **No** | N/A | No (correctly excluded) |
| BioEmu | Equilibrium ensemble | **No** | N/A | No (but arguably should be mentioned as alternative paradigm) |

## 5. Mori-Zwanzig — what it actually gives us and what the paper does with it

**Mori (1965, Prog. Theor. Phys. 33:423) and Zwanzig (1961, Phys. Rev. 124:983)** derived the Generalized Langevin Equation (GLE) by projecting full-phase-space Hamiltonian dynamics onto a reduced set of "relevant" variables A(t). The exact form is
dA/dt = Ω A(t) + ∫₀ᵗ K(t−τ) A(τ) dτ + F(t)
with Markovian drift Ω, memory kernel K encoding eliminated DOFs, and fluctuating force F related to K by the fluctuation-dissipation theorem. This is faithfully reproduced in STAR-MD Appendix A.2 (Eq. 5).

**What MZ actually lets you compute:** The formalism is *exact but non-constructive*. The memory kernel K(t) contains e^((1−P)Lt), i.e. dynamics orthogonal to the projected subspace, which cannot be directly integrated. Practical MZ work consists of operational schemes to estimate K numerically from all-atom MD.

**Who has actually learned memory kernels from MD?**
- **Hijón, Español, Vanden-Eijnden, Delgado-Buscalioni (Faraday Discuss. 2010)** — "MZ formalism as a practical computational tool"; constrained-MD scheme, star-polymer example. The seminal operational paper (https://online.kitp.ucsb.edu/online/multiscale12/vandeneijnden/).
- **Lemke & Peter (J. Phys. Chem. B 2021, "Introducing Memory in Coarse-Grained Molecular Simulations"** https://pubs.acs.org/doi/10.1021/acs.jpcb.1c01120; review in PMC https://pmc.ncbi.nlm.nih.gov/articles/PMC8154603/).
- **Klippenstein, van der Vegt and colleagues (2021-2024)** — iterative Gauss-Newton reconstruction of kernels for CG water and polymers (https://pubmed.ncbi.nlm.nih.gov/36745567/, https://pubmed.ncbi.nlm.nih.gov/38804493/).
- **Ayaz, Dalton, Netz et al. (PNAS 2021 "Non-Markovian modeling of protein folding" https://www.pnas.org/doi/10.1073/pnas.2023856118; PNAS 2023 "Fast protein folding is governed by memory-dependent friction" https://www.pnas.org/doi/10.1073/pnas.2220068120).** These explicitly extract memory kernels from MD of fast-folding proteins and show folding rates are dominated by friction memory — *directly relevant biology* that STAR-MD does not cite.
- **Ma et al. (PRL 2023, "Construction of Coarse-Grained MD with Many-Body Non-Markovian Memory"** https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.131.177301).

**Does a transformer's attention window correspond to a memory kernel?** Only in a loose analogical sense. A transformer attending to L past frames implements a *learned, input-dependent linear combination* of past states, which is structurally reminiscent of ∫ K(t−τ) A(τ) dτ. But:
- MZ's K is **system-specific, non-input-dependent** (for Gaussian approximation of fluctuating force), determined by the underlying Hamiltonian and the projection operator; attention is data-driven and conditional.
- MZ's kernel connects to **fluctuating force F(t) by fluctuation-dissipation**; nothing enforces this in a transformer.
- MZ is **causal with fixed-length semi-infinite memory in principle**; transformers truncate to context window.
- Attention operates on **abstract latent features** (single embeddings), not on the physical observables where MZ is derived.

**STAR-MD's "Memory Inflation Proposition" (§A.3)** claims that projecting out pair features "inflates" the memory kernel on singles, requiring richer temporal history and non-separable S×T attention. The argument is structurally correct in the MZ sense — eliminating more DOFs does inflate memory — but the leap from "the memory kernel is non-separable" to "therefore use joint rather than factorized attention" is a motivational analogy, not a theorem. A factorized S+T model could in principle approximate a non-separable kernel with enough depth (universal approximation); the paper shows empirically that joint is better, but the theoretical section overstates the bridge between MZ and the architectural choice. **This is the paper's most oversold framing.**

## 6. CG non-Markovian protein dynamics — actual SOTA

Beyond MZ-based CG, the field's consensus in 2024-2026:
- **VAMPnets / VAMP-2 score** (Mardt, Pasquali, Wu, Noé 2018; Wu & Noé J. Nonlinear Sci. 2020) remain the standard for learning slow collective modes. STAR-MD uses VAMP-2 as a fidelity metric — appropriate.
- Markov State Models + extended dynamical operator theory recover MFPTs reliably when enough data exists; see Bonati, Rizzi, Parrinello and the MSMs-after-ML reviews (e.g. JACS Au 2021 https://pubs.acs.org/doi/10.1021/jacsau.1c00254).
- *Whether generative models actually recover slow timescales* is contested. The "tICA lag-time correlation" metric STAR-MD reports (0.17 for MD oracle vs 0.17 for STAR-MD, Table 1) suggests parity — but tICA slow-mode recovery at 100 ns is a weak test, since the reference itself has only 3×100 ns of data per protein.
- MFPTs / transition rates: **No generative MD paper (STAR-MD, ConfRover, MDGen, AlphaFolding) has demonstrated quantitatively correct MFPTs for a rare biologically meaningful transition in an ATLAS-class protein.** BioEmu does claim ≈1 kcal/mol on relative populations (which is thermodynamic, not kinetic).

## 7. SE(3)-equivariant diffusion for proteins — how crowded is the niche?

By 2026 this niche is extremely crowded. Major entries:
- **RFdiffusion** (Watson et al., Nature 2023) — backbone design, not dynamics.
- **FrameDiff / FrameFlow** (Yim et al. ICML 2023; Yim et al. https://arxiv.org/abs/2310.05297) — SE(3) diffusion/flow on backbone frames.
- **FoldFlow** (Bose et al.) — conditional flow matching on SO(3).
- **Genie / Genie 2** (Lin & AlQuraishi, https://arxiv.org/abs/2405.15489) — SE(3) diffusion for scaffolding.
- **AlphaFold3** (Abramson et al. Nature 2024) — generative all-atom structure predictor.
- **Chroma, Proteus, Protpardelle, Multiflow** — adjacent families.

All of the above are **static structure/ensemble** generators, not trajectory models. The *trajectory* subfield (the actual competitor set) is much narrower: MDGen, AlphaFolding, ConfRover, EquiJump (Costa et al. 2024, https://arxiv.org/abs/2410.09667), Timewarp (Klein et al. NeurIPS 2023), ITO (Schreiner et al. NeurIPS 2023), JAMUN (2024), BioMD (Sep 2025 https://arxiv.org/abs/2509.02642), DeepJump (2025 https://arxiv.org/abs/2509.13294), HemePLM-Diffuse (Aug 2025).

**Where STAR-MD fits:** a scaling + architecture contribution within the *trajectory autoregressive* subcluster. Not novel in being SE(3)-equivariant or diffusion-based; novel in combining causal diffusion + joint S×T attention + singles-only KV cache at ATLAS scale.

## 8. Microsecond-scale generative MD — is STAR-MD first?

Recent or concurrent μs-scale claims:
- **BioMD (Sep 2025, arXiv:2509.02642)** — "all-atom generative model ... conditional flow matching that decouples long-term evolution from local dynamics" explicitly targets long trajectories. Concurrent.
- **BioKinema / "Physically Grounded Generative Modeling of All-Atom Biomolecular Dynamics"** (bioRxiv Feb 2026 https://www.biorxiv.org/content/10.64898/2026.02.15.705956v1) — hierarchical forecast+interpolate, diffusion architecture with Langevin-derived temporal attention. Nearly simultaneous with STAR-MD.
- **DeepJump (2025)** — large timestep protein MD via learned operators.
- **ITO (Schreiner et al. 2023, https://arxiv.org/abs/2305.18046)** — *claims* timesteps "at least six orders of magnitude larger than MD" for fast-folders. Different setup (coarse-grained, fast-folders not ATLAS), but the microsecond claim is arguably older.
- **Timewarp (Klein et al. 2023, https://arxiv.org/abs/2302.01170)** — large time jumps via normalizing flow, transferable across peptides.
- **Distributional Graphormer (Zheng et al., Nature Machine Intelligence 2024, https://www.nature.com/articles/s42256-024-00837-3)** — equilibrium distribution, not trajectory; predates the trajectory-μs question.
- **BoltzGen (Nov 2025 https://www.biorxiv.org/content/10.1101/2025.11.20.689494v1)** — despite name, is a **binder design** model, not a trajectory model. Not relevant to STAR-MD's claim.

**Bottom line:** STAR-MD is *not* the first to claim microsecond-scale generative protein dynamics (ITO predates), but it is one of the first to do so **on ATLAS-class proteins (50-1000 residues, all-atom backbones)** rather than on fast-folders or small peptides. The true novelty is the scale, not the timescale.

## 9. Verification of load-bearing citations

**Citation [30] Vander Meersche et al. 2024 (ATLAS)** — framing "contains 100 ns MD trajectories for 1390 structurally diverse proteins." Accurate. Minor omission: each protein has 3 replicates (300 ns effective per protein), which STAR-MD does not state explicitly in §4.1.

**Citation [13] Jing et al. 2024 (MDGen)** — framing "models the joint distribution of frames across 100-ns trajectories" and "discard[s] memory of earlier windows." Accurate regarding the ATLAS model (250-frame fixed window, keyframe-anchored). Slightly uncharitable in not mentioning that MDGen's primary architectural contribution (Hyena-based scaling to 100k frames) was demonstrated on tetrapeptides — i.e., MDGen as deployed on ATLAS is a deliberately scaled-back instance.

**Citation [6] Cheng et al. 2025 (AlphaFolding)** — framing "incorporates higher-order information through additional motion frames." Accurate — the AAAI paper's motion-alignment and reference modules match.

**Citation [26] Shen et al. 2025 (ConfRover)** — framing as the autoregressive predecessor that "compresses all preceding frames into a static condition c(x<l)." This is a charitable reading; ConfRover does use a temporal module over frames, and compressing-to-static vs autoregressive-conditioning-on-history is a real difference, but the phrasing makes ConfRover sound more naive than its arXiv description suggests. Full ConfRover paper (https://arxiv.org/html/2505.17478) describes a "temporal module ... sequence model that captures conformational dynamics across frames" — which sounds like sequence-level, not static, conditioning. STAR-MD's critique is therefore arguably a strawman-adjacent framing of a same-lab prior. Debate-worthy.

**Citation [23] Mori 1965 + [38] Zwanzig 1961** — formalism reproduced correctly in Appendix A.2. The Eq. 5 GLE decomposition is standard.

**Citation [4] Chen et al. 2024 (Diffusion Forcing)** — correctly credited for the noisy-context technique. Accurate.

## 10. Novelty assessment

**Genuinely novel / defensible contributions of STAR-MD:**
1. **Singles-only KV cache** for autoregressive trajectory diffusion → O(NL) memory vs ConfRover's O(N²L). This is the most concrete engineering win and is supported by Figure 5 (ConfRover hits 2 TB cache on protein size 500, STAR-MD stays under 256 GB). **Real contribution.**
2. **Joint spatio-temporal attention on singles** within the diffusion decoder, rather than interleaved S+T or external static conditioning. Ablation Table 3 shows this is material (Rec 0.57 → 0.46 when factorized).
3. **Continuous-time ∆t conditioning via AdaLN with LogUniform[10⁻², 10¹] ns** — decouples physical duration from context length. Genuinely useful and empirically validated (Fig 4: stable at 2.5 ns vs 1.2 ns strides).
4. **Demonstrating stable 1 μs rollouts on ATLAS-scale proteins** — incremental over ITO/Timewarp in principle (they claimed larger time jumps earlier), but on a harder benchmark (larger proteins, all-atom).
5. **Contextual noise perturbation** (Diffusion-Forcing-style) applied to trajectory MD — adapted, not invented, but the ablation (77.8% → 85.2% CA+AA validity) justifies inclusion.

**Incremental / overclaimed:**
1. SE(3)-equivariant backbone parameterization — standard since FrameDiff (Yim 2023); no novelty.
2. MZ formalism "justifies" joint attention — motivational analogy only; not a theorem connecting MZ memory kernels to attention, and the claim that factorized attention *cannot* approximate the non-separable kernel is not proven.
3. "SOTA on ATLAS" — true under the specific split and metric set chosen by the prior ConfRover paper; the split is not field-standard (no redundancy filter beyond temporal cutoff).
4. "Microsecond timescales" — ITO claimed larger timestep ratios in 2023; BioKinema/BioMD make overlapping μs claims concurrently.
5. BioEmu / AlphaFlow not benchmarked — sidesteps the question "do trajectory models beat equilibrium samplers on coverage after you throw away the time ordering?"

---

## Where the paper's framing is misleading

- **"SOTA on the standard ATLAS benchmark"** — the "standard" split was defined by the same lab's previous paper (ConfRover/Shen 2025); it has temporal but no sequence/fold-redundancy filter. It is not an ATLAS-authored canonical split.
- **ConfRover-W vs ConfRover** comparison at long horizons conflates "prior method failed" with "memory-hacked variant of prior method failed." Table 2 should report ConfRover-W at 100 ns to isolate the windowing penalty.
- **Mori-Zwanzig as "theoretical justification"** — MZ gives non-Markovian generalized Langevin equations, not a theorem recommending joint over factorized attention. The "Memory Inflation Proposition" supports "you need some non-separable modeling," not specifically "you need joint attention." The paper presents an analogy as a proof.
- **MDGen + AlphaFolding "failing catastrophically" at 1 μs** — accurate but both were not designed for that regime; the framing obscures that this is partially an out-of-distribution-for-baselines comparison.
- **Microsecond scale novelty** — ITO (2023) and Timewarp (2023) already claimed very large time jumps; the novel axis is *protein size* (ATLAS-class), not timescale per se.
- **No comparison against equilibrium samplers** (AlphaFlow, BioEmu, DiG). For many biological questions — e.g. "does the ensemble of conformations have the right Boltzmann weights?" — equilibrium samplers may dominate trajectory models, and the paper does not engage this question.

## Genuinely novel contributions

- **Singles-only KV cache** enabling full-history autoregressive generation without CPU offloading at ATLAS scale; the O(NL) vs O(N²L) memory argument in §3.2 / Appendix B is correct and load-bearing.
- **Joint spatio-temporal attention integrated *inside* the diffusion decoder** with block-causal training — the ablation (w/ Preproc Attn: Rec 0.48, Validity 82.6%) shows integration matters, not just presence.
- **Continuous-time ∆t conditioning** allowing a model trained at short windows to generate at arbitrary strides (2.5 ns, 1.2 ns) in a 1 μs rollout without retraining — genuinely elegant and well-validated in Figure 4.
- **Empirical demonstration of controlled error accumulation over 1 μs for 50-1000-residue proteins** (Figure 3 right panel) — whether or not the theoretical framing is oversold, the stability plot is the most compelling single piece of evidence in the paper and is without clear precedent on ATLAS-class systems.

---

**Sources (key URLs):**
- STAR-MD: https://arxiv.org/abs/2602.02128 ; https://bytedance-seed.github.io/ConfRover/starmd
- ATLAS: https://academic.oup.com/nar/article/52/D1/D384/7438909 ; https://www.dsimb.inserm.fr/ATLAS
- ConfRover: https://arxiv.org/abs/2505.17478 ; https://neurips.cc/virtual/2025/loc/san-diego/poster/116440
- MDGen: https://arxiv.org/abs/2409.17808 ; https://github.com/bjing2016/mdgen
- AlphaFolding: https://arxiv.org/abs/2408.12419
- AlphaFlow: https://arxiv.org/abs/2402.04845 ; https://github.com/bjing2016/alphaflow
- BioEmu: https://www.biorxiv.org/content/10.1101/2024.12.05.626885v1 ; https://www.science.org/doi/10.1126/science.adv9817
- Distributional Graphormer: https://www.nature.com/articles/s42256-024-00837-3
- Timewarp: https://arxiv.org/abs/2302.01170
- ITO: https://arxiv.org/abs/2305.18046
- EquiJump: https://arxiv.org/abs/2410.09667
- Hijón et al. (MZ operational): Faraday Discuss. 2010; https://online.kitp.ucsb.edu/online/multiscale12/vandeneijnden/
- Lemke & Peter (memory in CG): https://pubs.acs.org/doi/10.1021/acs.jpcb.1c01120 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC8154603/
- Ayaz/Dalton/Netz (memory-friction protein folding): https://www.pnas.org/doi/10.1073/pnas.2023856118 ; https://www.pnas.org/doi/10.1073/pnas.2220068120
- Ma et al. PRL 2023 (ML memory kernels): https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.131.177301
- BioMD: https://arxiv.org/abs/2509.02642
- BioKinema: https://www.biorxiv.org/content/10.64898/2026.02.15.705956v1
