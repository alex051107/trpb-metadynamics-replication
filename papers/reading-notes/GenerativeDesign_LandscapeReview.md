# Evolution of Generative Protein/Enzyme Design Methods
## With Focus on Physics-Based Simulations as Validation/Reward Signals

**Author**: Zhenpeng Liu (compiled 2026-03-31)
**Purpose**: Frame the entire project motivation — why GenSLM + MetaDynamics matters

---

## Part A: Enzyme Engineering Method Evolution

### Era 1: Directed Evolution (1990s--present)

**Key figure**: Frances Arnold (Nobel Chemistry 2018)

**How it works**: Random mutagenesis + high-throughput screening. Iterate: mutate DNA randomly, express variants, screen for desired activity, pick winners, repeat.

**Achievements**:
- Arnold's lab has produced hundreds of engineered enzymes, including stand-alone TrpB variants (Buller et al. PNAS 2015)
- 60% of activating mutations in TrpB were located within 5 A of the alpha/beta interface, the COMM domain, or regions undergoing motion upon closure (Buller et al. 2015)

**Fundamental limitation**: Combinatorial explosion. A 100-amino-acid protein has 1,900 single mutants and >1.5 million double mutants. The number of possible sequences increases exponentially, and complete sampling is beyond the capacity of most screens. Physical assays are the bottleneck — you can only test ~10^3-10^4 variants per round in a typical lab.

> Citation: [DIRECTED EVOLUTION OF ENZYMES AND BINDING PROTEINS — Nobel Committee 2018](https://www.nobelprize.org/uploads/2018/10/advanced-chemistryprize-2018.pdf); [Exploring protein fitness landscapes by directed evolution (Romero & Arnold, Nature Rev. Mol. Cell Biol. 2009)](https://pmc.ncbi.nlm.nih.gov/articles/PMC2997618/)

---

### Era 2: Rational/Computational Design (2000s--present)

**Key tools**: Rosetta (Baker Lab), FoldX

**How it works**: Use protein structure + energy functions to predict which mutations will improve stability/activity. Design mutations computationally, test only the top candidates.

**Achievements**:
- RFdiffusion (Baker Lab, Nature 2023): de novo protein backbone design via diffusion, generating picomolar-affinity binders through pure computation
- Chroma (Generate Biomedicines, Nature 2023): conditional generative model for protein structures and complexes

**Fundamental limitation**: Static structure assumption. Rosetta-ddG and FoldX assume mutations exert only local effects on protein structure and leave the rest of the system unperturbed. They do NOT model large conformational changes. Matthews correlation coefficients between 0.3-0.5; success rates ~15-40% for stability predictions. They cannot capture dynamics — the open/closed transitions critical for enzyme catalysis.

> Citation: [Computational Modeling of Protein Stability (Razvi & Scholtz, Structure 2020)](https://www.cell.com/structure/fulltext/S0969-2126(20)30122-2); [Predicting protein stability changes — comparison of tools (Bib. Bioinf. 2022)](https://academic.oup.com/bib/article/23/2/bbab555/6502552)

---

### Era 3: Machine Learning on Sequence (2019--2023)

**Key models**: UniRep (Church Lab, 2019), ESM (Meta AI, 2019-2023), ProtTrans (Rost Lab, 2021)

**How it works**: Train large language models on millions of protein sequences. The models learn evolutionary patterns (co-variation, conservation) and produce embeddings that encode biophysical properties.

- **UniRep** (2019): Trained on 24M UniRef50 sequences using next-amino-acid prediction. Predicts stability, function of mutants. First to show unsupervised representations rival supervised models.
- **ESM-2** (2022-2023): Scaled to 15B parameters; atomic-resolution structure emerges in learned representations. Orders of magnitude faster than AF2 for large-scale structure characterization.
- **ProtTrans** (2021): Trained 6 transformer variants on up to 393B amino acids. ProtT5 embeddings outperformed SOTA without using evolutionary (MSA) information.

**Limitation**: No physics. These models learn statistical correlations from evolutionary data, not the physical mechanisms of how mutations affect dynamics, binding, or catalysis. They cannot tell you WHY a mutation works — only that it resembles known functional sequences. Zero-shot performance degrades for truly novel sequences lacking homologs.

> Citation: [UniRep (Alley et al., Nature Methods 2019)](https://www.nature.com/articles/s41592-019-0598-1); [ESM-2 (Lin et al., Science 2023)](https://www.science.org/doi/10.1126/science.ade2574)

---

### Era 4: Protein Language Models for Generation (2022--present)

**Key models**: ProtGPT2, ESM-IF, GenSLM, EvoDiff, ProGen2

**How it works**: Instead of predicting properties of known sequences, these models GENERATE novel sequences from scratch or conditionally.

- **ProtGPT2** (2022): Autoregressive GPT-2 fine-tuned on UniRef50. Generates sequences that fold into stable structures.
- **ProGen2** (2023): Autoregressive protein LM. Balanced performance across quality, diversity, novelty.
- **EvoDiff** (2023, Microsoft): Discrete diffusion model for proteins. Excels at diversity and novelty.
- **GenSLM** (2022, Argonne/NVIDIA): Genome-scale LM trained on 110M prokaryotic gene sequences. Up to 25B parameters. Unique: works at codon level (DNA), not amino acid level. Won 2022 Gordon Bell Special Prize.
- **ESM-IF** (Meta): Inverse folding — design sequences for given structures.

**Benchmark comparison** (ProteinBench, ICLR 2025):
- ProGen2: balanced quality/diversity/novelty
- EvoDiff + ESM3: better diversity and novelty
- DPLM: best at highly structural sequences

**The critical question**: Once you generate 60,000 novel sequences, how do you validate them without wet lab? This is the validation bottleneck.

> Citation: [ProteinBench (ICLR 2025)](https://arxiv.org/abs/2409.06744); [GenSLMs (Zvyagin et al., IJHPCA 2023)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9709791/); [EvoDiff (Alamdari et al., bioRxiv 2023)](https://www.biorxiv.org/content/10.1101/2023.09.11.556673v1.full)

---

### Era 5: Physics-Informed Generative Design — THIS IS WHERE OUR PROJECT SITS

**The gap**: Generative models produce sequences. Static structure predictors (AlphaFold) give you one structure. Neither tells you about conformational dynamics — the time-dependent motions that govern enzyme catalysis.

**Our approach**: GenSLM (generates) → MetaDynamics (simulates conformational landscape) → Free Energy Landscape features become the "conformational filter" or "reward signal."

This bridges eras 4 and 2 with enhanced sampling physics.

---

## Part B: The Physics Validation Problem

### B1. Why AlphaFold Cannot Validate Generated Sequences

AlphaFold2 predicts a single ground-state structure. It was NOT designed to predict conformational landscapes.

**Specific limitations** (documented in recent reviews):

1. **No free energy landscapes**: AF2 "likely does not learn the energy landscapes underpinning protein folding and function" (Lane, 2023)
2. **Single-state bias**: An AF2 ensemble "usually represents a single conformational state with minimal structural heterogeneity"
3. **No dynamics**: AF2-based methods "rely on co-evolutionary information contained in sub-MSAs" and are "limited in capturing protein dynamics"
4. **Memorization risk**: AF2 is a "weak predictor of fold switching" and some successes result from "memorization of training-set structures rather than learned protein energetics"

For TrpB specifically, the O→C transition of the COMM domain is a large-scale conformational change (residues 102-189 moving). This is exactly the kind of motion AlphaFold CANNOT characterize.

**Partial workaround**: Template-based AF2 (tAF2) with subsampled MSAs can generate some conformational diversity, but without thermodynamic weighting — you don't know which states are energetically accessible.

> Citation: [Beyond static structures: protein dynamic conformations modeling in the post-AlphaFold era (Briefings Bioinf. 2025)](https://academic.oup.com/bib/article/26/4/bbaf340/8202937); [AlphaFold and protein folding: Not dead yet! (PMC 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11892350/)

---

### B2. Why Conventional MD Alone Is Not Enough

Conventional MD simulates atomic motions but is limited by timescale. The O→C transition in TrpB occurs on microsecond-millisecond timescales. Even with GPU acceleration, a single 500 ns simulation may never sample this rare event.

**Enhanced sampling solves this**: Metadynamics adds a history-dependent bias potential in collective variable (CV) space, forcing the system to explore high-energy barriers it would never cross in conventional MD. Well-tempered MetaD converges to the true free energy surface.

---

### B3. MetaDynamics as Conformational Filter

**What makes a good "reward signal" from MetaD output?**

From Osuna's work (JACS 2019, ACS Catal. 2021), the key FEL features for TrpB are:

| Feature | What it measures | Good filter? |
|---------|-----------------|-------------|
| Barrier height O→C | Activation energy for closure | YES — lower = more productive |
| Relative stability C vs O | Thermodynamic preference for Closed | YES — more stable C = better catalyst |
| Number of metastable minima | Conformational complexity | YES — fewer = more cooperative |
| Position of global minimum | Where enzyme spends most time | YES — should be near Closed/PC |
| Path CV z(R) | Deviation from reference O→C path | YES — on-path = productive closure |

**The Osuna lab demonstrated this directly**: In the JACS 2019 paper (Maria-Solano, Iglesias-Fernandez, Osuna), well-tempered multiple-walker metadynamics reconstructed the FEL for pfTrpB at different reaction intermediates. They showed that:
- Open COMM domain = inactive state
- Closed COMM domain = catalytically competent state
- Laboratory-evolved TrpB variants shift the FEL toward the Closed state

In the ACS Catal. 2021 paper, they used the Shortest Path Map (SPM) tool with MetaD to identify distal activity-enhancing mutations in TrpB — mutations far from the active site that alter conformational dynamics.

> Citation: [Maria-Solano et al. JACS 2019, 141, 13049-13056](https://pubs.acs.org/doi/10.1021/jacs.9b03646); [Maria-Solano et al. ACS Catal. 2021, 11, 13733-13743](https://pubs.acs.org/doi/10.1021/acscatal.1c03950)

---

### B4. The Speed Bottleneck — How to Scale MetaDynamics

A single well-tempered MetaD run for TrpB takes days to weeks on GPU. If GenSLM generates 1000 candidates, naive MetaD on all of them would take years.

**Existing solutions (from literature)**:

| Strategy | Speed-up | Maturity | Reference |
|----------|---------|----------|-----------|
| **Multiple walkers MetaD** | Linear scaling with # walkers | Mature (PLUMED) | Raiteri et al. J. Phys. Chem. B 2006 |
| **Coarse-grained funnel MetaD** | 10-100x (Martini 3 + MetaD) | Emerging (2025) | ChemRxiv 2025 |
| **SPM + short MD** (Osuna) | Hours instead of days/weeks | Validated for TrpB | Osuna Faraday Discuss. 2024 |
| **ML collective variables** (RAVE, DeepTDA) | Faster convergence, fewer CVs needed | Active research | Ribeiro et al.; PLUMED PyTorch module |
| **Boltzmann Generators** | Orders of magnitude (no MD needed) | Early stage for proteins | Noe et al. Science 2019; ICLR 2025 |
| **ML surrogate models** | 1000x+ (trained on MetaD data) | Emerging | NeuralMD (Anandkumar Lab) |
| **Transfer learning of bias** | Reuse converged bias for similar mutants | Untested for protein MetaD | Conceptual |

**Most promising near-term approach for our pipeline**: SPM + tAF2 as fast pre-filter (hours per mutant), then full MetaD only on top ~10-50 candidates.

> Citation: [Enhanced Sampling with Machine Learning (Chem. Rev. 2025)](https://pubs.acs.org/doi/10.1021/acs.chemrev.5c00700); [SPM webserver (Protein Eng. Des. Sel. 2024)](https://academic.oup.com/peds/article-abstract/doi/10.1093/protein/gzae005/7618441); [Scalable Boltzmann Generators (ICLR 2025)](https://arxiv.org/abs/2401.04246)

---

## Part C: Current State-of-the-Art (2024--2026)

### C1. Lambert et al. 2026 — The Key Paper

**"Sequence-based generative AI design of versatile tryptophan synthases"**
Lambert T, Tavakoli A, Arnold FH. *Nature Communications* 17, 1680 (2026).

**What they did**:
- Fine-tuned GenSLM on 30,000 unique trpB nucleotide sequences (22,800 unique amino acid sequences)
- Generated 60,000 TrpB sequences
- Applied multi-stage in silico filtering: sequentially removed least viable sequences, balancing novelty vs. functionality
- Validated experimentally (NOT computationally — this is the gap our project fills)

**Key results**:
- Generated TrpBs express in E. coli, are stable, catalytically active
- Many show significant substrate promiscuity, outperforming natural counterparts on non-native substrates
- Some surpass laboratory-evolved TrpBs
- Most-active/most-promiscuous generated TrpB vs. closest natural homolog: enhanced versatility absent from natural enzyme

**What they did NOT do**: No molecular dynamics. No MetaDynamics. No conformational dynamics analysis. Their in silico filters were sequence-based (ESM scores, homology filters, etc.), not physics-based.

**THIS IS THE GAP**: Lambert showed GenSLM can generate functional TrpBs but didn't explain WHY they work. Our project adds the physics layer — MetaDynamics to reveal whether the generated variants achieve productive O→C closure.

> Citation: [Lambert et al. Nature Communications 2026](https://www.nature.com/articles/s41467-026-68384-6)

---

### C2. Physics-Informed PLMs

**METL** (Nature Methods 2025): Pretrain transformers on Rosetta biophysical simulation data (millions of variants). Fine-tune on experimental data. Excels at predicting thermostability, catalytic activity from as few as 64 training examples. Can use function-specific MD simulations for pretraining.

**SeqDance / ESMDance** (PNAS 2026): PLMs trained on dynamic biophysical properties from MD simulations + normal mode analyses of >64,000 proteins. SeqDance's attentions capture dynamic interaction and comovement between residues. ESMDance (built on ESM2) substantially outperforms ESM2 at zero-shot prediction of mutation effects for designed and viral proteins.

**Dynamics-based GNN** (PNAS 2025): Graph neural network using Asymmetric Dynamic Coupling Index (DCIasym) from MD to model allosteric interactions. Outperforms existing methods at predicting epistasis and distal mutation effects — exactly the kind of mutations Osuna identified in TrpB.

> Citation: [METL (Nature Methods 2025)](https://www.nature.com/articles/s41592-025-02776-2); [SeqDance (PNAS 2026)](https://www.pnas.org/doi/10.1073/pnas.2530466123); [DCIasym GNN (PNAS 2025)](https://www.pnas.org/doi/10.1073/pnas.2502444122)

---

### C3. Reinforcement Learning for Guided Protein Generation

**ProteinRL** (2024): RL framework for fine-tuning generative PLMs toward specific properties (charge, solubility, structure).

**RLXF** (2025): Reinforcement Learning from eXperimental Feedback — aligns PLMs with measured functional objectives.

**ORI** (Nature Communications 2025): Ontology Reinforcement Iteration — closed-loop: generate → test → retrain. Engineered a lysozyme with 100x higher activity, a chitinase stable at 85C.

**Key insight**: RL effectiveness depends on a three-factor interaction: task difficulty x reward model accuracy x policy capacity. Noisy rewards or capacity bottlenecks cap improvements despite exploration.

**Relevance to our project**: MetaDynamics FEL features could serve as reward signals for RL-guided GenSLM. But MetaD is expensive — need a fast surrogate (SPM? ML classifier?) to make RL iteration feasible.

> Citation: [ProteinRL (arXiv 2024)](https://arxiv.org/abs/2412.12979); [ORI (Nature Communications 2025)](https://www.nature.com/articles/s41467-026-69855-6); [RLXF (bioRxiv 2025)](https://www.biorxiv.org/content/10.1101/2025.05.02.651993v1.full)

---

### C4. Generative Active Learning with Physics Oracles

**REINVENT + ESMACS** (J. Chem. Theory Comput. 2024): Closed-loop molecular design combining generative AI (REINVENT) with absolute binding free energy simulations (ESMACS). Deployed on Frontier exascale machine. Uses active learning to select which molecules to simulate next.

**Architecture**: Generative model (inner loop, RL-based) → ML surrogate (ChemProp) → Physics oracle (free energy simulation, outer loop) → Retrain surrogate → Repeat.

**Relevance**: This is the closest existing analog to a "GenSLM + MetaD" closed loop, but for small molecules, not proteins. The key architectural insight is the two-tier oracle: fast ML surrogate for most candidates, expensive physics simulation only for calibration points.

> Citation: [REINVENT + ESMACS (JCTC 2024)](https://pubs.acs.org/doi/10.1021/acs.jctc.4c00576)

---

### C5. Anima Anandkumar Lab (Caltech)

Anandkumar's lab develops ML methods at the intersection of molecular dynamics and deep learning:

- **NeuralMD**: ML surrogate that accelerates MD simulations of protein-ligand binding using a physics-informed, multi-grained, group-symmetric framework
- **NeuralPLexer**: Deep generative model for predicting protein-ligand complex structures and their fluctuations (dynamics!)
- **Neural Operators**: For learning multiscale phenomena (fluid dynamics, wave propagation — potentially adaptable to conformational dynamics)

**Connection to our project**: If this is the "Anima Lab" referenced in the project, their expertise in ML surrogates for MD could directly address the MetaD scaling bottleneck.

> Citation: [Anandkumar Lab publications](https://www.eas.caltech.edu/people/anima); [NeuralPLexer (Nature 2024)](https://www.caltech.edu/about/news/new-ai-model-for-drug-design-brings-more-physics-to-bear-in-predictions)

---

## Part D: Critical Assessment

### D1. Is MetaDynamics the right physics layer, or too slow?

**Assessment: MetaDynamics is the gold standard for accuracy, but too slow for high-throughput screening alone.**

- Pro: MetaD gives thermodynamically rigorous FEL. For TrpB, Osuna demonstrated it correctly captures the O→C transition energetics.
- Con: Days-weeks per mutant at all-atom resolution. Cannot screen 1000 candidates.
- **Resolution**: Use a tiered approach:
  1. Fast filter (SPM + short MD, hours): screen 1000 → top 50
  2. Full MetaD (days): screen 50 → top 10
  3. Experimental validation: test top 10

---

### D2. Faster alternatives for conformational dynamics scoring

| Method | Time per mutant | Accuracy | Physics content |
|--------|---------------|----------|-----------------|
| AlphaFold2 (tAF2) | Minutes | Low (no thermodynamics) | None |
| SPM + short MD | Hours | Medium (captures allosteric networks) | Partial |
| RAVE/ML-CV MetaD | 1-3 days | High (converges faster) | Full |
| Boltzmann Generators | Minutes-hours | Unknown for large proteins | Approximate |
| ML surrogates (NeuralMD) | Seconds | Depends on training data | Learned |
| SeqDance/ESMDance | Seconds | Medium (dynamics-informed) | Pretrained |
| DCIasym GNN | Minutes | High for epistasis | MD-derived |

**Best near-term combo**: SeqDance/ESMDance for initial ranking (seconds) → SPM + short MD (hours) → full MetaD on finalists (days).

---

### D3. "Conformational dynamics → catalytic activity" — how well-supported for TrpB?

**Very well-supported. This is one of the strongest cases in enzymology.**

Evidence:
1. Buller et al. (PNAS 2015): 60% of activating mutations in stand-alone TrpB are in the COMM domain or interface regions that undergo conformational changes
2. Maria-Solano et al. (JACS 2019): MetaD FEL directly shows that lab-evolved variants shift equilibrium toward Closed (active) state
3. Maria-Solano et al. (ACS Catal. 2021): SPM-identified distal mutations validated experimentally — conformational dynamics predict activity
4. Boehr & Stern (2018): Directed evolution "rescued" conformational dynamics in adenylate kinase — accelerated interconversion between catalytically essential sub-states correlates with catalysis
5. Osuna (Faraday Discuss. 2024): SPM tool rationale — "efficient catalysis requires optimization of the conformational ensemble," and conformational dynamics is the mechanism by which distal mutations enhance activity

**For TrpB specifically**: The COMM domain closure is the rate-determining conformational step. Mutations that stabilize the Closed state or lower the O→C barrier directly enhance catalytic turnover. This is not a hypothesis — it's been demonstrated experimentally and computationally by multiple groups.

---

### D4. Could you replace MetaD with something cheaper?

**Partially, yes.** Several approaches could serve as cheaper proxies:

1. **SPM + tAF2** (Osuna lab): Already validated for TrpB. Results in hours, not days. Identifies key conformational hotspots. Could serve as the fast pre-filter.
2. **Short MD + ML classifier**: Train a classifier on MetaD-labeled data (productive vs non-productive closure). Input: 10 ns MD trajectory features (RMSD, RMSF, inter-domain distances). Could work if trained on enough TrpB MetaD data. UNTESTED.
3. **SeqDance zero-shot**: Trained on MD dynamics from 64,000 proteins. Could predict dynamic property changes from mutations without any simulation. UNTESTED for TrpB.
4. **DCIasym GNN**: Already demonstrated for predicting epistatic effects using dynamics-derived features. Could score TrpB variants for allosteric coupling. UNTESTED for TrpB.

**Cannot fully replace MetaD**: None of these give you the actual FEL. For publication-quality claims about free energy barriers, MetaD remains necessary. But for screening, cheaper proxies are adequate.

---

### D5. Scaling limit — can you MetaD 1000 candidates?

**Not with full all-atom MetaD. But with a tiered strategy, yes.**

Rough calculation (based on Osuna's published protocols):
- Full well-tempered MetaD for TrpB: ~500 ns total simulation time, 4 walkers, ~3-7 days on 1 GPU
- 1000 candidates x 5 days = 5000 GPU-days = ~14 GPU-years
- On a 100-GPU cluster: ~50 days. Expensive but not impossible.
- With multiple-walker MetaD (linear scaling): could reduce to ~1 day per mutant on 4 GPUs

**Practical strategy**:
- Screen 1000 with SPM (1 hour each, 1000 hours = 42 days on 1 CPU, or 1 day on 42 CPUs)
- MetaD the top 50 (50 x 5 days / 50 GPUs = 5 days)
- Total: ~1 week wall time with moderate HPC resources

---

### D6. Has anyone closed the loop (generate → simulate → re-train)?

**For small molecules: YES.**
- REINVENT + ESMACS (JCTC 2024): generative AI + binding free energy simulations, closed loop on Frontier exascale machine.
- ORI framework (Nature Communications 2025): closed loop with experimental feedback.

**For proteins with conformational dynamics: NO. Nobody has done this yet.**

The closest attempts:
- METL: Pretrain on Rosetta simulations, fine-tune on experiments. But not a generative loop — it's a prediction model, not a generator.
- SeqDance: Trained on MD data, but again prediction, not generation.
- Lambert 2026: Generated with GenSLM, validated experimentally. No physics in the loop.

**OUR PROJECT WOULD BE THE FIRST TO CLOSE THE LOOP: GenSLM (generate) → MetaDynamics (conformational filter) → retrain/select.**

This is the novelty claim.

---

## Part E: The Bigger Picture

### E1. Position in AI-for-Science Landscape

This project sits at the intersection of three converging trends:

```
  Generative AI          Physics Simulation       Enzyme Engineering
  (GenSLM, ESM)    +     (MetaD, MD)        +     (TrpB, directed evolution)
       |                      |                          |
       v                      v                          v
  Generate novel         Compute FEL               Validate activity
  TrpB sequences         (O→C barrier,             experimentally
                         C stability)
       |                      |                          |
       +----------+-----------+                          |
                  |                                      |
                  v                                      |
         Conformational Filter                           |
         (physics-based reward)                          |
                  |                                      |
                  +-------------------+------------------+
                                     |
                                     v
                           Closed-Loop Pipeline
```

This approach directly addresses what the AI-for-science community has identified as a key challenge: "there are still no reliable metrics that correlate well with [protein] affinity" and "function-based prediction AI tools would strengthen synthesis screening over current sequence-based tools."

---

### E2. What Would Make This Pipeline Genuinely Novel vs Incremental?

**Incremental**: Just running MetaD on a few Lambert TrpB variants and saying "the good ones close better."

**Genuinely novel**:

1. **Conformational dynamics as a learned reward signal**: Train an ML surrogate on MetaD FEL features across multiple TrpB variants. Use this surrogate as a fast reward function for RL-guided GenSLM fine-tuning. This closes the loop computationally.

2. **Dynamics-aware sequence generation**: Show that GenSLM, when guided by conformational dynamics feedback, generates sequences with different (better) properties than when guided by sequence-only filters. This would demonstrate that physics adds information beyond evolution.

3. **Transferable conformational filter**: Demonstrate that the MetaD-trained filter generalizes — not just for TrpB, but for other PLP-dependent enzymes or COMM-domain proteins. This makes it a method contribution, not just a case study.

4. **Quantitative dynamics-activity relationship**: Establish a quantitative correlation: delta(FEL barrier) → delta(k_cat). Currently Osuna's work is qualitative ("shifted toward closed = more active"). Putting numbers on this would be a significant advance.

---

### E3. Open Problems Nobody Has Solved

1. **The reward signal design problem**: What specific FEL features best predict catalytic activity? Barrier height alone? Relative basin depth? Path fidelity? Nobody has systematically compared these as reward signals.

2. **Generalization of dynamics filters**: All existing dynamics-based enzyme studies are case-specific (TrpB, adenylate kinase, etc.). No general framework for "this enzyme needs dynamics type X."

3. **Speed-accuracy Pareto frontier**: What's the optimal trade-off between simulation accuracy and throughput? At what level of approximation do you lose predictive power?

4. **Multi-objective optimization**: Enzymes need to be stable AND active AND expressible AND selective. How do you combine MetaD conformational data with stability/solubility predictions in one optimization?

5. **Epistasis in conformational space**: How do multiple mutations interact to shift the FEL? The DCIasym GNN (PNAS 2025) shows this is tractable, but nobody has applied it to generative design.

6. **Data-efficient MetaD**: Current MetaD protocols are designed for single systems. Can you transfer converged bias potentials between similar mutants to drastically reduce convergence time?

7. **The validation paradox**: To train an ML surrogate for MetaD, you need MetaD data on many variants. But MetaD is expensive. The chicken-and-egg problem of bootstrapping the training set.

---

## Summary Table: Method Evolution

| Era | Method | Data → Design | Dynamics? | Throughput | Our Position |
|-----|--------|--------------|-----------|------------|--------------|
| 1 | Directed evolution | Random → screen | No | 10^3/round | Historical |
| 2 | Rational design | Structure → mutate | No (static) | 10^1-10^2 | Background |
| 3 | ML on sequence | Evolution → predict | No | 10^6+ | Background |
| 4 | Generative PLMs | Train → generate | No | 10^4-10^5 | Input (GenSLM) |
| 5 | **Physics-informed** | Generate → simulate → filter | **YES** | 10^1-10^2 (MetaD) | **US** |
| 5+ | **Closed-loop** | Generate → simulate → retrain | **YES** | Target: 10^3 | **GOAL** |

---

## Key References (Comprehensive)

### TrpB-Specific
1. Maria-Solano, Iglesias-Fernandez, Osuna. "Deciphering the Allosterically Driven Conformational Ensemble in TrpB Evolution." JACS 2019, 141, 13049-13056. DOI: 10.1021/jacs.9b03646
2. Maria-Solano et al. "In Silico Identification and Experimental Validation of Distal Activity-Enhancing Mutations in TrpB." ACS Catal. 2021, 11, 13733-13743. DOI: 10.1021/acscatal.1c03950
3. Lambert T, Tavakoli A, Arnold FH. "Sequence-based generative AI design of versatile tryptophan synthases." Nature Communications 2026, 17, 1680. DOI: 10.1038/s41467-026-68384-6
4. Buller AR et al. "Directed evolution of the tryptophan synthase beta-subunit for stand-alone function recapitulates allosteric activation." PNAS 2015, 112, 14599-14604.

### Protein Language Models
5. Alley EC et al. "Unified rational protein engineering with sequence-based deep representation learning." Nature Methods 2019, 16, 1315-1322. DOI: 10.1038/s41592-019-0598-1
6. Zvyagin M et al. "GenSLMs: Genome-scale language models reveal SARS-CoV-2 evolutionary dynamics." IJHPCA 2023. DOI: 10.1177/10943420231201154
7. Ferruz N et al. "ProtGPT2 is a deep unsupervised language model for protein design." Nature Communications 2022.

### Physics-Informed ML
8. Gelman S et al. "Biophysics-based protein language models for protein engineering (METL)." Nature Methods 2025. DOI: 10.1038/s41592-025-02776-2
9. "Protein language models trained on biophysical dynamics inform mutation effects (SeqDance/ESMDance)." PNAS 2026. DOI: 10.1073/pnas.2530466123
10. "A protein dynamics-based deep learning model enhances predictions of fitness and epistasis." PNAS 2025. DOI: 10.1073/pnas.2502444122

### Enhanced Sampling + ML
11. "Enhanced Sampling in the Age of Machine Learning: Algorithms and Applications." Chemical Reviews 2025. DOI: 10.1021/acs.chemrev.5c00700
12. Osuna S. "Harnessing conformational dynamics in enzyme catalysis — the SPM tool." Faraday Discussions 2024. DOI: 10.1039/D3FD00156C

### Generative Design + Physics
13. "Optimal Molecular Design: REINVENT with Binding Free Energy." JCTC 2024. DOI: 10.1021/acs.jctc.4c00576
14. "Functional protein design with ontology reinforcement iteration (ORI)." Nature Communications 2025. DOI: 10.1038/s41467-026-69855-6
15. "Guiding Generative Protein Language Models with Reinforcement Learning." arXiv 2024. 2412.12979

### Structure Prediction + Dynamics
16. Watson JL et al. "De novo design of protein structure and function with RFdiffusion." Nature 2023. DOI: 10.1038/s41586-023-06415-8
17. "Beyond static structures: protein dynamic conformations modeling in the post-AlphaFold era." Briefings in Bioinformatics 2025.

### Boltzmann Generators
18. "Scalable Normalizing Flows Enable Boltzmann Generators for Macromolecules." ICLR 2025. arXiv: 2401.04246
