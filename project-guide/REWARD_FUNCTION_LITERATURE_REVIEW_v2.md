# Reward Functions for Protein Language Model-Guided Enzyme Design: A Comprehensive Literature Review

> **Authors**: Zhenpeng Liu (UNC Chapel Hill)
> **Date**: April 2, 2026
> **Prepared for**: Caltech / Anima Lab Summer Research Position
> **Papers surveyed**: 75+ primary sources
> **Method**: Multi-agent literature search (PubMed, bioRxiv, Semantic Scholar, Web) + dual adversarial review

---

## Abstract

Protein language models (PLMs) can generate vast libraries of candidate enzyme sequences, but they lack intrinsic mechanisms to ensure catalytic function. A reward function — a computational scoring system that evaluates candidate sequences and feeds that signal back to the generative model — could in principle guide PLMs toward designs with improved activity, stability, and selectivity. This review critically examines the landscape of available reward signals for enzyme design, ranging from inexpensive sequence-based predictors to computationally demanding physics-based simulations. We evaluate zero-shot fitness predictors (ESM-1v, EVE, TranceptEVE, SaProt), few-shot active learning approaches (EVOLVEpro, Gaussian process regression), reinforcement learning frameworks for PLM alignment (ProtRL, RLXF, muProtein), and physics-based validation methods including metadynamics free energy landscapes and AlphaFold2-based conformational ensemble prediction. Using tryptophan synthase beta-subunit (TrpB) as a case study — for which a 160,000-variant deep mutational scanning dataset, multiple directed evolution campaigns, and detailed conformational dynamics studies exist — we assess the feasibility of constructing a tiered reward architecture that connects sequence generation to catalytic function. We identify critical gaps including the extrapolation problem (models trained on four active-site residues cannot score full-sequence variants), cofactor compatibility (PLP binding is unaddressed by standard scoring methods), and the composite reward problem (linear combination of heterogeneous scores lacks theoretical justification). We conclude that retrospective benchmarking of scoring methods against known TrpB variants represents the most defensible near-term research direction, with physics-based conformational validation reserved for a small number of top candidates.

---

## 1. Introduction

The intersection of generative artificial intelligence and enzyme engineering represents one of the most rapidly evolving frontiers in computational biology. Over the past three years, protein language models trained on evolutionary sequence data have demonstrated a remarkable capacity to generate novel protein sequences that fold into stable structures and, in some cases, exhibit catalytic function comparable to or exceeding that of their natural counterparts^1,2,3^. GenSLM, a codon-level transformer developed at Argonne National Laboratory and trained on over 110 million prokaryotic gene sequences^4^, was recently fine-tuned on approximately 30,000 tryptophan synthase beta-subunit (TrpB) DNA sequences to generate novel enzymes with activity at both room temperature and 75 °C, with some designs surpassing the lab-evolved benchmark PfTrpB-0B2 on non-native substrates^5^. Similarly, ProGen demonstrated that autoregressive transformers can generate functional lysozymes at sequence identities as low as 31.4% to any natural protein^1^, while ZymCTRL produced functional carbonic anhydrases and lactate dehydrogenases conditioned solely on EC number^6^. Most dramatically, ESM3, a 98-billion-parameter multimodal model, generated a functional green fluorescent protein (esmGFP) with only 58% identity to the closest natural fluorescent protein — a divergence estimated to correspond to roughly 500 million years of natural evolution^7^.

Despite these successes, a fundamental challenge remains: generative models produce sequences, but they do not inherently distinguish between sequences that will be catalytically active and those that will not. Lambert and colleagues^5^ addressed this by applying heuristic filters — start codon checks, sequence length constraints, active-site conservation — but these filters are crude proxies for enzymatic function. A more principled approach would be to construct a **reward function**: a computational scoring system that evaluates each candidate sequence along dimensions relevant to catalytic activity, and to use that score to guide the generative model toward improved designs through reinforcement learning, preference optimization, or guided decoding.

The concept is straightforward in principle but fraught with difficulty in practice. What should the reward function measure? How accurately can each component be computed? Can heterogeneous scores be meaningfully combined? And is the resulting composite signal informative enough to guide generation without inducing reward hacking — the well-documented tendency of optimizers to exploit weaknesses in surrogate scoring functions^8,9^? This review examines these questions through the lens of enzyme engineering, with particular attention to tryptophan synthase as a case study where unusually rich experimental and computational data exist.

---

## 2. Zero-Shot Fitness Prediction from Protein Language Models

The most computationally inexpensive approach to scoring protein variants is zero-shot fitness prediction, in which a pretrained language model estimates the functional impact of mutations without any task-specific training data. The underlying assumption is that evolutionary plausibility — as captured by the model's learned sequence distribution — correlates with functional fitness.

### 2.1 Masked marginal scoring and its limitations

ESM-1v, a 650-million-parameter transformer trained on 98 million protein sequences, introduced masked marginal scoring for zero-shot variant effect prediction^10^. The approach masks each position in turn and evaluates the log-likelihood of the wild-type amino acid under the model's conditional distribution. Across the 41 deep mutational scanning (DMS) assays available at the time, ESM-1v outperformed the MSA-based method DeepSequence^11^ on 17 tasks, with the advantage of requiring no multiple sequence alignment computation. However, the method was designed for scoring single-point mutations around a reference sequence, not for evaluating highly divergent full-length sequences. As the number of mutations relative to the reference increases, the conditional independence assumption underlying position-wise masking becomes increasingly violated, and the score becomes unreliable^12^. This limitation is critical for evaluating GenSLM-generated sequences, which may differ from the closest natural TrpB at dozens of positions simultaneously.

The ProteinGym benchmark^12^, comprising over 250 standardized DMS assays with 2.7 million mutated sequences across 217 protein families, has become the standard evaluation platform for fitness predictors. Across this benchmark, the best zero-shot models achieve average Spearman rank correlations of approximately 0.47–0.50 with experimental measurements. Notably, no single model dominates across all protein families, and a critical observation for enzyme engineering is that these models predict **stability better than catalytic activity**^12,13^. The benchmark aggregates diverse assay types — including binding, expression, stability, and activity — without distinguishing among them, making it difficult to assess how well any particular model performs specifically on enzyme catalysis.

### 2.2 Structure-aware and evolutionary models

Beyond sequence-only approaches, several methods incorporate structural or evolutionary information to improve fitness prediction. EVE, a Bayesian variational autoencoder trained on evolutionary sequence alignments^14^, achieves Spearman correlations of approximately 0.45 on ProteinGym by computing an evolutionary index that captures higher-order constraints beyond single-site frequencies. TranceptEVE^15^ combines autoregressive sequence modeling with retrieval-augmented inference from homologous sequences, achieving the strongest general-purpose zero-shot performance reported to date.

More recently, SaProt^16^ introduced a structure-aware vocabulary based on Foldseek structural tokens combined with sequence tokens, achieving the top ranking on the ProteinGym leaderboard as of early 2024. By encoding three-dimensional structural context directly into the token representation, SaProt captures positional effects that sequence-only models miss — a potentially important advantage for enzyme active-site mutations where the structural environment is critical. However, the approach requires AlphaFold-predicted structures as input, adding computational overhead that may limit its applicability as a fast pre-filter in high-throughput screening.

GEMME^17^, a phylogeny-based approach that quantifies site sensitivity from evolutionary tree topology, provides a complementary signal to neural network-based methods. Its interpretability and minimal computational requirements make it an attractive component of multi-method ensembles. ProtSSN^18^, which integrates sequential and geometric encoders for protein primary and tertiary structure, has shown exceptional zero-shot performance across more than 300 DMS assays with minimal trainable parameters, suggesting that the combination of sequence and structural information may be more important than model scale for fitness prediction.

### 2.3 The activity prediction gap

A persistent finding across the fitness prediction literature is that zero-shot methods are substantially more accurate at predicting stability and conservation effects than at predicting catalytic activity^12,19^. This gap arises because PLMs capture the evolutionary distribution of sequences — which is shaped primarily by the need to fold stably and avoid aggregation — rather than the specific geometric and electronic requirements for catalysis. Goldman and colleagues^20^ demonstrated this limitation explicitly by showing that compound-protein interaction models trained on current data are incapable of learning enzyme-substrate interactions, with non-interaction baselines outperforming more sophisticated approaches. For enzyme engineering, this means that zero-shot PLM scores are useful as pre-filters to eliminate sequences that are evolutionary implausible or unlikely to fold, but they are insufficient as primary reward signals for catalytic activity.

---

## 3. Few-Shot and Supervised Approaches

When even small amounts of experimental fitness data are available for the target enzyme, few-shot approaches can dramatically improve prediction accuracy by combining PLM representations with task-specific labels.

### 3.1 EVOLVEpro and active learning

EVOLVEpro^21^ represents the current state of the art in few-shot protein engineering. The framework extracts ESM-2 embeddings for each variant, trains a lightweight random forest regressor on as few as 10–20 experimentally characterized variants, and iteratively proposes new candidates for experimental testing. Across six diverse proteins spanning RNA production, genome editing (CRISPR nucleases), and antibody binding, EVOLVEpro achieved up to 100-fold improvements in desired properties within a small number of active learning rounds. The approach is fast (seconds per sequence after training), requires modest experimental data, and generalizes across protein families — making it the most practical few-shot method for enzyme engineering currently available.

The Bayesian Gaussian process framework introduced by Romero, Krause, and Arnold^22^ for navigating protein fitness landscapes provided the conceptual foundation for much of this work. By modeling the fitness landscape as a Gaussian process and using acquisition functions that balance exploration and exploitation, the approach engineered cytochrome P450 enzymes more thermostable than any previously made by chimeragenesis, rational design, or directed evolution. Wu and colleagues^23^ extended this to machine learning-assisted directed evolution (MLDE) with combinatorial libraries, demonstrating that ML models trained on partial library data could identify variants with higher fitness than standard directed evolution screening — a result validated on enzyme stereodivergence for carbene Si–H insertion.

### 3.2 Active learning on TrpB

The TrpB system has been the subject of intensive ML-guided engineering efforts, owing largely to the availability of the 160,000-variant combinatorial fitness landscape constructed by Johnston and colleagues^24^ at Caltech. This dataset encompasses all 20^4 amino acid combinations at four active-site residues (positions 183, 184, 227, and 228) in thermostable TrpB from *Pyrococcus furiosus*, with fitness measured as tryptophan formation rate via growth coupling. The landscape exhibits significant epistasis and many local optima, making it a challenging but information-rich testbed for ML methods.

Wittmann and colleagues^25^ evaluated MLDE protocols on this landscape and identified a key insight: reducing "holes" (zero-fitness variants) in training data is more critical than increasing dataset size. Their focused training MLDE (ftMLDE) approach uses zero-shot predictors to generate informative training sets, substantially improving ML model accuracy. Yang and colleagues^26^ extended this to active learning-assisted directed evolution (ALDE), applying iterative ML-guided exploration to five epistatic TrpB active-site residues for a non-native cyclopropanation reaction, improving product yield from 12% to 93% in three wet-lab rounds. Most recently, Li and colleagues^27^ conducted a systematic evaluation of MLDE strategies across 16 protein fitness landscapes spanning six protein systems and two function types, finding that ML advantages are greatest on the most challenging (highly epistatic) landscapes.

### 3.3 The extrapolation problem

A critical limitation of DMS-trained models must be confronted directly. The Johnston TrpB dataset covers four active-site residues; GenSLM mutates the entire ~400-residue sequence. Positional extrapolation — predicting the effects of mutations at positions never seen in training — is known to fail for DMS-trained models. Livesey and Marsh^28^ explicitly demonstrated that "the performance of all models is drastically reduced" when predicting effects at unseen positions. This is not a minor concern for TrpB: the Arnold laboratory's directed evolution campaigns repeatedly demonstrated that distal mutations — located 18–29 Å from the active site — are critical for enhancing standalone TrpB activity^29,30,31^. A model trained on four active-site residues is structurally blind to these distal effects.

The dynamics-based epistasis predictor of Huynh and colleagues^32^ offers a potential bridge across this gap. Their graph neural network, which uses an asymmetric dynamic coupling index (DCI) derived from molecular dynamics simulations, outperforms existing approaches on DMS datasets across four proteins despite not training on epistasis data. By capturing allosteric communication between residues, the approach can in principle predict how distal mutations modulate active-site function — precisely the capability that static DMS models lack.

---

## 4. Reinforcement Learning for Protein Language Model Alignment

The past two years have seen rapid development of frameworks for fine-tuning protein language models using reward signals, drawing directly on techniques developed for aligning large language models in natural language processing.

### 4.1 Frameworks and methods

ProtRL^33^, developed by Adaptyv Bio, implements weighted direct preference optimization (wDPO) and group relative policy optimization (GRPO) for autoregressive protein language models. Applied to ZymCTRL for EGFR binder design, ProtRL produced four of nine tested sequences that outperformed the best initial binder, including a top candidate with K_d = 27.4 nM — a substantial improvement from approximately 800 nM in the first round. The framework is open-source and designed to work with any autoregressive PLM and any fitness signal, making it the most accessible RL toolkit for protein engineering.

RLXF^34^, from the Romero laboratory, adapts the RLHF paradigm from ChatGPT to protein engineering. Using supervised fine-tuning followed by PPO with experimental fluorescence measurements as reward, RLXF aligned an ESM-2 model to generate CreiLOV fluorescent protein variants with approximately 16-fold increased brightness — the most fluorescent CreiLOV variants reported to date. The approach was validated across five diverse protein families (GB1, avGFP, Ube4b, Bgl3, Pab1) and requires only three days of training on a single GPU, making it accessible to most academic laboratories.

The most impressive demonstration of RL for enzyme engineering comes from muProtein^35^, which couples a deep learning model for mutational effect prediction (muFormer) with an RL search algorithm (muSearch). Trained only on single-mutation data for TEM-1 beta-lactamase, muProtein discovered multi-site mutants with up to 2,000-fold increased growth rate, surpassing one of the highest known activity levels. This result is remarkable because it demonstrates that RL can effectively navigate the combinatorial explosion of multi-site mutant space starting from single-mutation measurements alone.

### 4.2 Guided decoding and inference-time steering

An alternative to fine-tuning is to modify the generative model's output distribution at inference time, avoiding the computational and stability costs of RL training. ASPO (Activation Steering-based Protein Optimization)^36^, presented at ICML 2025, derives steering vectors from contrasting protein sets and applies them to perturb PLM activations during inference. The approach is training-free and works with both autoencoding (ESM) and autoregressive protein LMs. ST-PARM^37^ extends this concept to multi-objective settings, using smooth Tchebycheff scalarization to provide Pareto-complete coverage of non-convex trade-off surfaces while steering a frozen PLM at inference time.

### 4.3 The codon-level mismatch

A fundamental technical obstacle for applying these methods to GenSLM deserves explicit discussion. GenSLM operates at the codon level (64 tokens), but all available reward signals — ESM-2 scores, DMS fitness measurements, Rosetta stability estimates, structural predictions — operate at the amino acid level. This means that synonymous codon differences are invisible to the reward function. The optimization effectively collapses from codon space back to amino acid space during reward evaluation, negating whatever codon-level advantages GenSLM's representation might provide for protein function.

codonGPT^38^ addresses a related but distinct problem: optimizing mRNA codon usage for a fixed protein sequence to improve translational efficiency. Its RL reward function combines five biological components (CAI, GC content, RNA folding ΔG, codon entropy, and codon repeats), but because codonGPT constrains generation to synonymous codons, it preserves the amino acid sequence exactly. Several other codon-level models — CodonBERT^39^, CaLM^40^, SynCodonLM^41^, Pichia-CLM^42^, and Trias^43^ — have since appeared, all focused on mRNA optimization rather than protein sequence design. The codon-level modeling landscape is active but orthogonal to the reward function problem for enzyme catalytic activity.

---

## 5. Physics-Based Validation: Molecular Dynamics and Free Energy Methods

At the opposite end of the computational cost spectrum from sequence-based scoring lie physics-based simulation methods, which can in principle capture the conformational dynamics that determine enzyme function but require days to weeks of GPU computation per variant.

### 5.1 Metadynamics and the TrpB conformational landscape

The foundational work of Maria-Solano, Iglesias-Fernández, and Osuna^44^ established that the catalytic efficiency of standalone TrpB variants correlates with the conformational equilibrium of the COMM (communication) domain, a mobile structural element that transitions between open (O), partially closed (PC), and closed (C) states. Using well-tempered metadynamics with path collective variables s(R) and z(R) at 350 K, they reconstructed the free energy landscape for TrpB variants along the directed evolution trajectory from wild-type PfTrpB to the highly active engineered variant PfTrpB-0B2^29^. Evolved variants progressively stabilize the closed state relative to the open state, and the O→C barrier height decreases with increasing catalytic activity. This work, performed with GROMACS 5.1.2 and PLUMED2, required approximately 500 ns of well-tempered metadynamics per system — corresponding to 3–20 GPU-days on modern hardware for the ~50,000-atom TrpB system.

Maria-Solano and colleagues^31^ subsequently demonstrated that the computational approach could identify novel activity-enhancing mutations: distal mutations predicted by shortest path map (SPM) analysis^45,46^ of the conformational landscape were experimentally validated to enhance TrpB standalone activity comparably to multiple rounds of laboratory directed evolution. This constitutes the strongest evidence that dynamics-based scoring has predictive, not merely explanatory, power for TrpB.

The broader conformational dynamics literature reinforces the importance of this approach. Crean, Gardner, and Kamerlin^47^ argued in a major review that conformational plasticity is an underexploited design principle, with most computational enzyme design approaches still relying on static or minimally flexible structural representations. St-Jacques and colleagues^48^ demonstrated that computational remodeling of an aminotransferase's conformational landscape could achieve approximately 100-fold activity increase and up to 1,900-fold selectivity switch for non-native substrates, with room-temperature crystallography confirming the designed conformational equilibria. Rakotoharisoa and colleagues^49^ showed that ensemble-based design using crystallographically derived conformational states improved Kemp eliminase activity by 100–250-fold while screening fewer than 10 variants — efficiency comparable to multiple rounds of directed evolution. Most recently, Guo and colleagues^50^ demonstrated deep learning-guided de novo design of proteins that transition between user-specified structural states with microsecond kinetics and atomic precision, establishing that designed conformational dynamics is now achievable.

### 5.2 The AlphaFold2 alternative

A critical finding that any reward function architecture must address is that the Osuna laboratory itself has published evidence that AlphaFold2 can approximate the conformational landscapes obtainable by metadynamics at drastically reduced computational cost. Casadevall, Duran, and Osuna^51^ demonstrated that template-based AF2 predictions, generated at multiple MSA depths and subjected to short (10 ns) MD simulations, can reproduce free energy landscapes comparable to those from well-tempered metadynamics. A companion study^52^ specifically applied this approach to tryptophan synthase conformational heterogeneity, estimating the O/PC/C state distribution for TrpB variants. The cost difference is approximately three orders of magnitude: minutes per sequence for AF2-based FEL versus days per sequence for full metadynamics.

If AF2-based FEL prediction is sufficiently accurate for ranking TrpB variants, it would transform the computational feasibility of physics-based reward signals. Rather than validating only 3–5 top candidates with full metadynamics (given a typical academic compute budget of ~10,000 GPU-hours per semester), one could screen hundreds of candidates with AF2-based FEL, reserving metadynamics for final validation of the top 2–3 designs. The critical unanswered question is whether AF2-FEL accuracy is sufficient for ranking — that is, whether the rank ordering of variants by AF2-predicted ΔG(C−O) agrees with the ordering by full metadynamics ΔG(C−O), and whether either ordering predicts experimental catalytic activity.

### 5.3 The dynamics-activity correlation: how strong is the evidence?

An honest assessment of the dynamics-activity relationship for TrpB must acknowledge that the current evidence, while consistent, is limited in scope. The Osuna 2019 study^44^ compared approximately 5–6 variants along one evolutionary trajectory and observed a qualitative trend: evolved variants stabilize the closed state. There is no reported quantitative correlation coefficient (Pearson or Spearman) between ΔG(C−O) and k_cat across a large variant set. The relationship could be confounded: variants along the directed evolution trajectory differ at many positions, and the observed FEL changes could be consequences of activity-improving mutations rather than their mechanistic cause.

Kinateder and colleagues^53^ strengthened the dynamics-activity link by identifying a naturally occurring standalone TrpB from *Pelodictyon luteolum* (plTrpB) with high standalone activity. Conformational landscape analysis confirmed that plTrpB displays efficient COMM domain closure in isolation, while a consensus variant lacking six key residues (plTrpB-con) loses this ability — a natural experiment that parallels the computational predictions. SPM analysis revealed tight interconnection of the COMM domain with catalytic loops exclusively in the activating context. However, this adds only one additional data point to an already small sample.

For a reward function, one needs not merely a qualitative correlation but a quantitative, predictive relationship robust enough that optimizing against it produces enzymes with improved activity rather than enzymes that merely achieve favorable ΔG(C−O) through mechanisms irrelevant to catalysis. This level of validation does not yet exist.

---

## 6. The TrpB System: A Uniquely Data-Rich Case Study

Tryptophan synthase beta-subunit occupies a privileged position in the enzyme design landscape owing to the convergence of multiple data sources that, collectively, provide an unusually complete picture of the sequence-structure-dynamics-function relationship.

### 6.1 The catalytic and allosteric mechanism

TrpB is a pyridoxal 5'-phosphate (PLP)-dependent enzyme that catalyzes the final step of tryptophan biosynthesis. In its native context, TrpB functions as part of the αββα tryptophan synthase complex, where the α-subunit (TrpA) allosterically activates TrpB through conformational changes in the COMM domain^54^. The Arnold laboratory demonstrated through directed evolution that standalone TrpB activity lost by removing TrpA can be recovered — and even surpassed — by accumulating mutations that mimic the allosteric activation signal^29,30^. Remarkably, five of six mutations in the most evolved variant (PfTrpB-0B2) are located distal from the active site, acting through modulation of the COMM domain conformational ensemble rather than through direct modification of catalytic residues.

This finding has profound implications for reward function design: any scoring method that considers only the active site — including models trained on the 160K DMS dataset at four active-site positions — will be blind to the dominant mechanism of activity enhancement in TrpB.

### 6.2 PLP cofactor compatibility: a critical blind spot

TrpB catalysis is absolutely dependent on the PLP cofactor, which forms a Schiff base with Lys82 (internal aldimine) and participates in every step of the catalytic cycle. If a generated sequence disrupts PLP binding — by mutating Lys82, altering the hydrogen bonding network to the phosphate group, or modifying the hydrophobic pocket that positions the pyridine ring — the enzyme is catalytically dead regardless of its conformational dynamics or thermostability.

None of the standard reward signals explicitly model cofactor binding. ESM-2 captures evolutionary conservation of PLP-binding residues implicitly, but RL optimization that pushes sequences into novel regions of sequence space may inadvertently move away from these conserved positions. Rosetta ddG estimates do not account for covalent cofactor attachment. AlphaFold predictions do not include PLP in the structural model. The DMS dataset at four active-site residues measures activity in the presence of PLP but does not independently assess cofactor binding.

This gap is not hypothetical. Dick and colleagues^55^ demonstrated through six generations of directed evolution that TrpB can be engineered for entirely novel PLP-dependent chemistry (quaternary C–C bond formation with 400-fold improved activity), but only because each variant in their evolutionary trajectory maintained PLP binding integrity. In a generative setting without explicit PLP constraints, there is no guarantee that this will hold.

The minimum requirement for any reward function architecture is a hard binary gate — not a soft score — checking conservation of Lys82 and the 8–10 residues within 4 Å of PLP in the crystal structure. Molecular docking of PLP into the predicted structure would provide additional confidence but at substantially higher computational cost.

### 6.3 The GenSLM connection

Lambert and colleagues^5^ fine-tuned a 25-million-parameter GenSLM model on approximately 30,000 unique TrpB DNA sequences and generated thousands of novel designs. After heuristic filtering (start codon, length, active-site conservation), 105 candidates entered experimental characterization. Of the 11 purified designs, all showed activity at room temperature; GenSLM-230 surpassed PfTrpB-0B2 on both native and non-native substrates, with several designs exhibiting substrate promiscuity absent from natural TrpBs. Expression yields averaged 84 mg/L, indicating that the generative model implicitly learned to produce expressible sequences.

This result establishes that GenSLM can generate functional TrpB enzymes, but it also highlights the limitation of heuristic filtering: the vast majority of generated sequences were not experimentally tested, and the filtering criteria were hand-designed rather than learned. A learned reward function could, in principle, identify active candidates more efficiently — provided the reward signal is accurate enough to avoid enriching for false positives.

---

## 7. Multi-Objective Optimization and the Composite Reward Problem

Enzyme engineering inherently involves multiple objectives — catalytic activity, thermostability, solubility, substrate selectivity, cofactor compatibility, expression yield — that may partially conflict. This raises the question of how to combine heterogeneous scoring signals into a unified reward.

### 7.1 Why linear combination fails

The most commonly proposed approach is a weighted linear combination of normalized component scores:

score = w₁ · normalize(activity_pred) + w₂ · normalize(stability_pred) + w₃ · normalize(evolutionary_score)

This formulation has fundamental scientific problems. First, the component scores live on incomparable scales: ESM-2 masked marginal scores are log-likelihoods, DMS fitness values are growth rates in arbitrary units, and Rosetta ddG values are in Rosetta Energy Units. Min-max normalization to [0,1] destroys information about prediction confidence. Second, there is no theoretical basis for additivity: enzyme activity depends nonlinearly on folding, binding, catalysis, and dynamics, and a sequence scoring well on stability and evolutionary plausibility may have zero activity due to incorrect active-site geometry. Third, learning the weights requires a dataset with activity labels and all component scores for the same variants; for TrpB, the Osuna evolutionary trajectory provides only 5–6 data points, and the 160K DMS dataset provides scores at only four positions.

Johnson and colleagues^56^ provided the most sobering empirical assessment of computational scoring for generated enzymes. Across over 500 expressed and purified enzyme sequences generated by three different methods (ancestral reconstruction, GANs, and PLMs), neither sequence identity to natural enzymes nor AlphaFold2 pLDDT scores predicted catalytic activity. The authors developed an improved filter that increased experimental success rates by 50–150%, but their core finding — that standard computational metrics are poor predictors of enzyme function — applies directly to the reward function problem.

### 7.2 Pareto and constraint-based alternatives

The multi-objective optimization literature offers more principled alternatives to linear combination. MosPro^57^ frames protein sequence design as discrete sampling using differentiable property predictors, navigating parameter spaces with adaptive weights to identify Pareto-optimal designs. MAProt^58^, a multi-agent framework combining ProteinMPNN (structure-based) and ESM/SaProt (PLM-based) agents, introduces a Pareto-based negotiation module that resolves conflicts between agents and finds consensus solutions. Constraint-based approaches — fix stability above a threshold, then maximize activity — avoid the weight-learning problem entirely and are conceptually better matched to enzyme engineering, where minimum stability is a prerequisite rather than a continuously tradeable property.

The reward hacking problem compounds the difficulty. When optimizing against surrogate fitness models, RL agents systematically exploit model weaknesses, generating sequences that score high on the surrogate but have low true fitness^8^. A data-driven strategy to avoid reward hacking in multi-objective molecular design was recently proposed^9^, using built-in diversity constraints to prevent mode collapse. The autofocusing framework of Fannjiang and Listgarten^59^ formalizes oracle-based design as a non-zero-sum game and proposes iteratively updating the surrogate oracle as the design algorithm explores beyond the training distribution — a theoretically principled but computationally expensive mitigation.

---

## 8. Computational Feasibility and Tiered Architecture

The cost differential between available scoring methods spans approximately seven orders of magnitude, from milliseconds per sequence for ESM-2 inference to weeks per sequence for well-converged metadynamics. This disparity necessitates a tiered screening architecture in which cheap methods filter large candidate pools and expensive methods validate small shortlists.

### 8.1 Cost estimates

The following estimates assume a single ~400-residue TrpB variant in a ~50,000-atom solvated system on contemporary GPU hardware (NVIDIA A100):

| Method | Approximate time per sequence | GPU-hours per 1,000 sequences |
|--------|-------------------------------|-------------------------------|
| ESM-2 masked marginal (400 aa) | 5–30 s | 5–50 |
| EVOLVEpro inference (post-training) | < 1 s | ~1 |
| ESMFold structure prediction | 2–15 min | 50–250 |
| Rosetta ddG | minutes (CPU) | ~10 (CPU) |
| AF2-based FEL (template + 10 ns MD) | 30–60 min | 500–1,000 |
| Short conventional MD (10 ns) | 1–2 hr | ~1,500 |
| Well-tempered MetaDynamics (800 ns) | 4–8 days | ~144,000 |

### 8.2 A realistic tiered pipeline

Given these costs and a typical academic compute budget of approximately 10,000 GPU-hours per semester, a realistic architecture might proceed as follows:

**Tier 1** (Sequence filters, ~free): Remove sequences lacking Lys82 conservation, PLP-binding pocket integrity, and minimum sequence identity to known active TrpBs. Apply ESM-2 or SaProt zero-shot scores to eliminate evolutionary implausible designs. This reduces a candidate pool of 10,000 to approximately 2,000.

**Tier 2** (Structure prediction, ~50–300 GPU-hours): Apply ESMFold or AF2 to predict structures. Filter by COMM domain RMSD to known closed-state structures and by Rosetta ddG stability estimates. This reduces to approximately 200 candidates.

**Tier 3** (Data-driven activity prediction, ~50 GPU-hours): Apply EVOLVEpro or a DMS-trained model to rank candidates by predicted catalytic fitness. For positions covered by the 160K DMS dataset, this provides high-confidence scoring; for distal positions, the prediction is less reliable but still informative through ESM-2 embedding-based regression. This identifies the top 10–50 candidates.

**Tier 4** (Physics-based validation, ~500–2,000 GPU-hours): For the top 5–10 candidates, run AF2-based FEL to assess COMM domain conformational landscape. For the top 2–3, run full well-tempered metadynamics for detailed free energy landscape reconstruction and comparison to the Osuna 2019 benchmark.

This architecture fits within 10,000 GPU-hours while providing progressively deeper evaluation at each stage. Critically, each tier serves as a **binary gate** (pass/fail) rather than a soft score that is combined with other tiers — avoiding the composite reward problem entirely.

### 8.3 What does not fit

Several commonly proposed activities are computationally infeasible within realistic academic budgets. Full metadynamics on 50+ candidates (~150,000 GPU-hours) is prohibitive. Multiple rounds of generate → score → fine-tune → generate, with physics-based scoring in the loop, requires an order of magnitude more compute than available. Training a neural network surrogate for metadynamics from scratch requires approximately 50 metadynamics runs (~500,000 GPU-hours of training data generation). These activities may be feasible for industrial laboratories with dedicated HPC resources but are not realistic for a summer undergraduate project.

---

## 9. Prior Art and Novelty Assessment

Before proposing any new research direction, it is essential to assess honestly what has already been done and what genuinely novel contributions remain.

### 9.1 What already exists

Lambert and colleagues^5^ demonstrated GenSLM + heuristic filtering for TrpB design. Yang and colleagues^26^ demonstrated active learning-assisted directed evolution on the TrpB fitness landscape. EVOLVEpro^21^ demonstrated few-shot PLM-guided optimization for diverse proteins. ProtRL^33^ and RLXF^34^ demonstrated RL fine-tuning of protein language models with experimental reward signals. Casadevall and Osuna^51,52^ demonstrated AF2-based conformational landscape prediction for TrpB. Maria-Solano and colleagues^31^ demonstrated computationally predicted, experimentally validated distal mutations for TrpB activity enhancement.

### 9.2 What remains novel

The only clearly novel contribution in this space would be the integration of conformational physics as a reward signal in a PLM-guided generation loop for a conformationally gated enzyme. No published work has closed the loop from PLM generation → conformational scoring → feedback to the generative model for TrpB or any similar system. However, the contribution is narrower than it might initially appear, because the physics-based component can only be applied to 3–10 sequences per round given compute constraints, limiting its direct utility as a reward signal.

A more defensible novel contribution would be a systematic retrospective benchmark: given the known experimental activities of Lambert et al.'s GenSLM-designed TrpBs and the Arnold laboratory's directed evolution variants, how well does each available scoring method — alone and in combination — predict the experimental rank ordering? This would provide the first quantitative assessment of whether any computational metric actually enriches for catalytic activity in designed TrpB variants, answering a foundational question that all subsequent reward function work depends upon.

---

## 10. Conclusions and Recommendations

This review has examined the landscape of reward functions for protein language model-guided enzyme design through the lens of tryptophan synthase, a system with unusually rich experimental and computational resources. Several conclusions emerge clearly from the evidence.

First, **zero-shot fitness predictors are useful pre-filters but insufficient reward signals for catalytic activity**. The best models achieve Spearman correlations of ~0.5 with experimental fitness across heterogeneous assay types, with substantially lower accuracy for enzyme activity specifically. They should be used to eliminate evolutionarily implausible designs, not to rank candidates for catalytic function.

Second, **few-shot approaches with experimental activity data represent the current practical frontier**. EVOLVEpro and related active learning methods can achieve large activity improvements with minimal experimental data. For TrpB, the 160,000-variant DMS dataset provides an unprecedented training resource, but its limitation to four active-site residues severely constrains extrapolation to full-sequence variants where distal mutations are the primary driver of activity enhancement.

Third, **RL fine-tuning of protein language models is technically feasible and experimentally validated**, with muProtein achieving 2,000-fold activity improvements for beta-lactamase and RLXF achieving 16-fold fluorescence improvements for CreiLOV. However, the quality of the reward signal is the binding constraint — gains from RL scale with reward accuracy, and noisy rewards cap improvements regardless of policy capacity.

Fourth, **physics-based conformational validation provides mechanistic insight but is too expensive for closed-loop reward optimization**. Metadynamics can validate 3–10 candidates per round; AF2-based FEL extends this to hundreds but with uncertain accuracy for ranking. The dynamics-activity correlation for TrpB, while consistent, is based on fewer than 10 data points and has not been demonstrated to be quantitatively predictive.

Fifth, **composite reward functions combining heterogeneous scores lack theoretical justification and risk reward hacking**. Tiered binary gating — where each scoring method serves as a pass/fail filter — is scientifically more defensible than weighted linear combination.

Sixth, **PLP cofactor compatibility is a critical gap** in all current scoring proposals. Any reward function for TrpB must include an explicit cofactor-binding gate.

Given these conclusions, we recommend the following research program, ordered by decreasing feasibility and defensibility:

**Near-term (achievable in a summer project)**: Retrospective benchmarking of scoring methods against known TrpB variant activities. Take GenSLM-designed and Arnold-lab-evolved TrpB variants with measured k_cat values, compute all available scores (ESM-2, EVOLVEpro trained on 160K DMS, Rosetta ddG, AF2-FEL), and assess which methods — alone or in tiered combination — best predict the experimental rank ordering. This answers the foundational question on which all reward function work depends.

**Medium-term**: Train an ESM-2-embedding model on the 160K DMS dataset and validate on known distal TrpB mutants from the Arnold laboratory. If the model generalizes (Spearman > 0.3 on distal mutants), it becomes a viable Tier 3 reward component. If it does not generalize, the DMS-based reward is limited to active-site redesign only.

**Long-term**: One complete cycle through the tiered pipeline — GenSLM generation → tiered filtering → AF2-FEL for top candidates → MetaDynamics validation of top 2–3 — with experimental measurement of designed variants to close the loop.

---

## References

1. Madani A, et al. Large language models generate functional protein sequences across diverse families. *Nat Biotechnol* 41, 1099–1106 (2023).
2. Dauparas J, et al. Robust deep learning-based protein sequence design using ProteinMPNN. *Science* 378, 49–56 (2022).
3. Yeh AHW, et al. De novo design of luciferases using deep learning. *Nature* 614, 774–780 (2023).
4. Zvyagin M, et al. GenSLMs: Genome-scale language models reveal SARS-CoV-2 evolutionary dynamics. *Int J High Perform Comput Appl* 37, (2023).
5. Lambert J, Tavakoli A, et al. Sequence-based generative AI design of versatile tryptophan synthases. *Nat Commun* 17, 1680 (2026).
6. Munsamy G, et al. Conditional language models enable the efficient design of proficient enzymes. bioRxiv (2024).
7. Hayes T, et al. Simulating 500 million years of evolution with a language model. *Science* 387, 850–858 (2025).
8. Lilian Weng. Reward Hacking in Reinforcement Learning. *Lil'Log* (2024).
9. A data-driven generative strategy to avoid reward hacking in multi-objective molecular design. *Nat Commun* 16, (2025).
10. Meier J, et al. Language models enable zero-shot prediction of the effects of mutations on protein function. *NeurIPS* (2021).
11. Riesselman AJ, Ingraham JB, Marks DS. Deep generative models of genetic variation capture the effects of mutations. *Nat Methods* 15, 816–822 (2018).
12. Notin P, et al. ProteinGym: Large-scale benchmarks for protein fitness prediction and design. *NeurIPS* (2023).
13. Chen L, et al. Learning protein fitness landscapes from multiple sources of deep mutational scanning data. *Cell Syst* 14, 706–721 (2023).
14. Frazer J, et al. Disease variant prediction with deep generative models of evolutionary data. *Nature* 599, 91–95 (2021).
15. Notin P, et al. Tranception: Protein fitness prediction with autoregressive transformers and inference-time retrieval. *ICML* (2022).
16. Su J, et al. SaProt: Protein language modeling with structure-aware vocabulary. *ICLR* (2024).
17. Laine E, Karami Y, Carbone A. GEMME: A simple and fast global epistatic model predicting mutational effects. *Mol Biol Evol* 36, 2604–2619 (2019).
18. Tan Y, et al. Semantical and topological protein encoding toward enhanced bioactivity and thermostability. *eLife* 13, (2025).
19. Goldman S, et al. Machine learning modeling of family wide enzyme-substrate specificity screens. *PLoS Comput Biol* 18, e1009853 (2022).
20. (Same as 19)
21. Jiang K, et al. Rapid in silico directed evolution by a protein language model with EVOLVEpro. *Science* 387, eadr6006 (2025).
22. Romero PA, Krause A, Arnold FH. Navigating the protein fitness landscape with Gaussian processes. *PNAS* 110, E193–E201 (2013).
23. Wu Z, et al. Machine learning-assisted directed protein evolution with combinatorial libraries. *PNAS* 116, 8852–8858 (2019).
24. Johnston KE, et al. A combinatorially complete epistatic fitness landscape in an enzyme active site. *PNAS* 121, e2400439121 (2024).
25. Wittmann BJ, Yue Y, Arnold FH. Informed training set design enables efficient machine learning-assisted directed protein evolution. *Cell Syst* 12, 1026–1045 (2021).
26. Yang J, et al. Active learning-assisted directed evolution. *Nat Commun* 16, 714 (2025).
27. Li FZ, et al. Evaluation of machine learning-assisted directed evolution across diverse combinatorial landscapes. *Cell Syst* (2025).
28. Livesey BJ, Marsh JA. Learning protein fitness landscapes from multiple sources. *Cell Syst* 14, 706–721 (2023).
29. Buller AR, et al. Directed evolution of the tryptophan synthase beta-subunit for stand-alone function recapitulates allosteric activation. *PNAS* 112, 14599–14604 (2015).
30. Buller AR, et al. Directed evolution mimics allosteric activation by stepwise tuning of the conformational ensemble. *J Am Chem Soc* 140, 7256–7266 (2018).
31. Maria-Solano MA, et al. In silico identification and experimental validation of distal activity-enhancing mutations in tryptophan synthase. *ACS Catal* 11, 13733–13743 (2021).
32. Huynh N, et al. Protein dynamics-based deep learning enables prediction of epistatic effects in protein evolution. *PNAS* 122, e2502444122 (2025).
33. Widatalla T, et al. Guiding generative protein language models with reinforcement learning. arXiv:2412.12979 (2024).
34. RLXF: Functional alignment of protein language models via reinforcement learning. bioRxiv (2025).
35. Sun Y, et al. muProtein: Accelerating protein engineering with fitness landscape modeling and reinforcement learning. *Nat Mach Intell* 7, 1446–1460 (2025).
36. Huang LK, et al. Steering protein language models. *ICML* (2025).
37. Yin R, Shen Y. ST-PARM: Pareto-complete inference-time alignment for multi-objective protein design. bioRxiv (2026).
38. codonGPT: Reinforcement learning on a generative language model enables scalable mRNA design. *Nucleic Acids Res* 53, gkaf1345 (2025).
39. Li S, et al. CodonBERT large language model for mRNA vaccines. *Genome Res* 34, 1027–1035 (2024).
40. Outeiral C, Deane CM. Codon language embeddings provide strong signals for use in protein engineering. *Nat Mach Intell* (2024).
41. Heuschkel J, et al. Advancing codon language modeling with synonymous codon constrained masking. *Nucleic Acids Res* 54, gkag166 (2026).
42. Narayanan H, Love JC. Pichia-CLM: A language model-based codon optimization pipeline. *PNAS* 123, e2522052123 (2026).
43. Faizi M, et al. A generative language model decodes contextual constraints on codon choice for mRNA design. bioRxiv (2025).
44. Maria-Solano MA, Iglesias-Fernández J, Osuna S. Deciphering the allosterically driven conformational ensemble in tryptophan synthase evolution. *J Am Chem Soc* 141, 13049–13056 (2019).
45. Casadevall G, et al. The shortest path method (SPM) webserver for computational enzyme design. *Protein Eng Des Sel* 37, gzae005 (2024).
46. Duran C, et al. Harnessing conformational dynamics in enzyme catalysis to achieve nature-like catalytic efficiencies. *Faraday Discuss* (2024).
47. Crean RM, Gardner JM, Kamerlin SCL. Harnessing conformational plasticity to generate designer enzymes. *J Am Chem Soc* 142, 11324–11342 (2020).
48. St-Jacques AD, et al. Computational remodeling of an enzyme conformational landscape for altered substrate selectivity. *Nat Commun* 14, 6058 (2023).
49. Rakotoharisoa RV, et al. Design of efficient artificial enzymes using crystallographically enhanced conformational sampling. *J Am Chem Soc* 146, 10001–10013 (2024).
50. Guo AB, et al. Deep learning guided design of dynamic proteins. *Science* 388, eadr7094 (2025).
51. Casadevall G, Duran C, Osuna S. AlphaFold2 and deep learning for elucidating enzyme conformational flexibility and its application for design. *JACS Au* 3, 1554–1562 (2023).
52. Casadevall G, et al. Estimating conformational heterogeneity of tryptophan synthase with a template-based AlphaFold2 approach. *Protein Sci* 31, e4426 (2022).
53. Kinateder T, et al. A naturally occurring standalone TrpB enzyme provides insights into allosteric communication within tryptophan synthase. *Protein Sci* 34, e70103 (2025).
54. Miles EW. The tryptophan synthase α2β2 complex: A model for substrate channeling, allosteric communication, and pyridoxal phosphate catalysis. *J Biol Chem* 288, 10084–10091 (2013).
55. Dick M, et al. Tailoring tryptophan synthase TrpB for selective quaternary carbon bond formation. *J Am Chem Soc* 141, 19817–19822 (2019).
56. Johnson SR, et al. Computational scoring and experimental evaluation of enzymes generated by neural networks. *Nat Biotechnol* (2024).
57. Luo J, et al. Pareto-optimal sampling for multi-objective protein sequence design. *iScience* 28, 112119 (2025).
58. Zhu M, et al. Advancing protein design via multi-agent reinforcement learning with Pareto-based collaborative optimization. bioRxiv (2026).
59. Fannjiang C, Listgarten J. Autofocused oracles for model-based design. *NeurIPS* (2020).
60. Osuna S. The challenge of predicting distal active site mutations in computational enzyme design. *WIREs Comput Mol Sci* 11, e1502 (2021).
61. D'Amico RN, Boehr DD. Allostery, engineering and inhibition of tryptophan synthase. *Curr Opin Struct Biol* 82, 102657 (2023).
62. Notin P, et al. Machine learning for functional protein design. *Nat Biotechnol* 42, 216–228 (2024).
63. Zhang Q, et al. ML-guided evolution of PylRS for improved enzyme activity. *Nat Commun* 16, 6648 (2025).
64. Jiang T, et al. PRIME: A general temperature-guided language model to design proteins of enhanced stability and activity. *Sci Adv* 10, eadr2641 (2024).
65. Hsu C, et al. Learning protein fitness models from evolutionary and assay-labeled data. *Nat Biotechnol* 40, 1114–1122 (2022).
66. Romero-Rivera A, Garcia-Borras M, Osuna S. Role of conformational dynamics in the evolution of retro-aldolase activity. *ACS Catal* 7, 8524–8532 (2017).
67. Russ WP, et al. An evolution-based model for designing chorismate mutase enzymes. *Science* 369, 440–445 (2020).
68. Murciano-Calles J, et al. A panel of TrpB biocatalysts derived from tryptophan synthase through the transfer of mutations that mimic allosteric activation. *Angew Chem Int Ed* 55, 11577–11581 (2016).
69. Zhou J, Huang M. Navigating the landscape of enzyme design: from molecular simulations to machine learning. *Chem Soc Rev* 53, 8202–8239 (2024).
70. Hie BL, Yang KK. Adaptive machine learning for protein engineering. *Curr Opin Struct Biol* 72, 145–152 (2022).
