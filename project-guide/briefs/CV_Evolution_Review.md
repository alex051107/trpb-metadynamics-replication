# Evolution of Collective Variables for Enhanced Sampling of Protein Dynamics

> Literature review compiled 2026-03-31. All citations are from web search results; no DOIs are fabricated.
> Relevance to TrpB project: We use Path CVs (s(R), z(R)) to study O/PC/C transitions in the COMM domain. Understanding the full CV landscape helps evaluate whether our approach is adequate and what alternatives exist.

---

## 1. Simple Geometric CVs (RMSD, Distances, Dihedral Angles)

**When introduced:** The earliest enhanced sampling approach. Metadynamics itself was introduced by Laio and Parrinello in 2002 (*PNAS* 99, 12562-12566, "Escaping free-energy minima"). The original demonstration used backbone dihedral angles (Phi, Psi) of alanine dipeptide in water as collective variables.

**What they measure:**
- **Dihedral angles** (phi, psi, chi): torsion angles along the backbone or side chains
- **RMSD:** root-mean-square deviation from a reference structure (global shape similarity)
- **Distances:** atom-atom or center-of-mass distances (e.g., salt bridges, hydrogen bonds)
- **Coordination numbers:** number of contacts within a cutoff

**Key assumption(s):**
- The user knows a priori which geometric degrees of freedom are relevant to the process of interest.
- The slow dynamics can be captured by a small number (typically 1-3) of these intuitive coordinates.

**Limitations / when it fails:**
- **Requires expert knowledge:** Choosing the wrong CV leads to poor sampling and incorrect free energy surfaces.
- **Low dimensionality curse:** Complex conformational changes (e.g., allosteric transitions involving many residues) cannot be captured by 1-2 geometric CVs.
- **RMSD is too coarse:** It conflates distinct conformational states that have similar RMSD values but different structural details.
- **Dihedral angles are too local:** They miss correlated, long-range motions relevant to domain movements.
- For proteins, these geometric CVs work well for local events (e.g., sidechain rotations, small loop movements) but fail for large-scale conformational changes like the O-to-C transition in TrpB's COMM domain.

**What replaced/improved it:** Path collective variables (2007) and PCA-based CVs provided ways to capture extended, multi-residue conformational changes.

---

## 2. Path Collective Variables (Branduardi, Gervasio, Parrinello, 2007)

**Key paper:** Branduardi, D., Gervasio, F.L., Parrinello, M. "From A to B in free energy space." *J. Chem. Phys.* 126, 054103 (2007). DOI: 10.1063/1.2432340.

**This is what our TrpB project uses** -- the Osuna 2019 JACS paper biases metadynamics along s(R) and z(R) to study the O/PC/C conformational landscape of the COMM domain.

**What it measures:**
- **s(R):** Progress along a predefined reference path from state A to state B (in our case, Open to Closed, via structures 1WDW and 3CEP).
- **z(R):** Distance (deviation) from the reference path -- how far the system strays from the predefined trajectory.

**Key assumption(s):**
1. A reasonable reference path between endpoints A and B is known or can be constructed.
2. The true conformational transition approximately follows this reference path (or at least passes near it).
3. The path can be discretized into a finite number of frames (landmarks), and the metric used (typically RMSD of selected atoms) meaningfully captures structural similarity.
4. Two variables (progress + deviation) provide sufficient dimensionality to describe the transition.

**Limitations / when it fails:**

1. **Dependence on reference path quality.** The path CV is only as good as the reference path. If the interpolated path passes through unphysical high-energy regions, s(R) and z(R) will not correspond to the true reaction coordinate. Linear interpolation between Open and Closed states may force the system through steric clashes or physically meaningless intermediate geometries.

2. **Linear interpolation is not physically meaningful for large protein motions.** Cartesian-space linear interpolation between two protein conformations does not respect the curved, high-dimensional nature of the conformational energy landscape. It can produce frames with broken bonds, steric clashes, or unrealistic backbone geometries. For the TrpB COMM domain (residues 97-184), linearly interpolating between 1WDW (Open) and 3CEP (Closed) assumes the transition is a smooth morph, which may miss the actual pathway that goes through the PC (partially closed) intermediate.

3. **Sensitivity to endpoint structure quality.** The quality of PDB structures 1WDW and 3CEP directly determines the path CV. Crystal packing artifacts, missing residues, different ligand states (Ain vs other intermediates), or resolution differences between the two structures introduce systematic errors. If an endpoint does not represent a true metastable state in solution, the path CV anchors the simulation to an artifact.

4. **Path shortcutting.** During metadynamics, the system can find shortcuts between different points on the path that bypass the intended route. This is especially problematic when the path has high curvature in CV space, causing s(R) to become multi-valued (different conformations map to the same s value).

5. **C-alpha-only path CVs miss side-chain contributions.** As noted in Felts et al. (*J. Phys. Chem. B* 2023, 10.1021/acs.jpcb.3c02028), "CA-PCV can be misleading in conformational transitions where certain side chain conformational changes are biologically relevant but have barriers such that they are not sampled sufficiently." The backbone can adopt the target conformation while critical side chains remain trapped, giving a false impression of successful transition.

6. **Fixed path limitation.** The original Path CV uses a fixed, pre-defined reference path. If the actual minimum free energy path (MFEP) differs from the reference, the simulation is biased along a suboptimal coordinate. This was addressed by adaptive path CVs (Diaz Leines & Ensing, 2012; Leines & Ensing, *Phys. Rev. Lett.* 109, 020601), where the path updates during the simulation to converge toward the MFEP.

**Known failure modes for large-scale protein motions:**
- When the conformational transition involves multiple sequential substeps (e.g., first loop closure, then helix rotation, then domain compaction), a single path CV may conflate these steps, producing an artificially smooth free energy profile.
- When the system accesses conformations far from the reference path (large z(R) values), the mapping becomes unreliable because the metric space around the path is poorly defined.
- For allosteric systems where the transition involves correlated motions across distant regions, the path CV may adequately capture the COMM domain movement but miss coupled changes elsewhere (e.g., in the alpha-subunit interface).

**What replaced or improved it:**
- **Adaptive path CVs** (Diaz Leines & Ensing, 2012): the path updates on-the-fly to converge to the MFEP.
- **Deep-LNE** (Frohlking, Bonati, Rizzi, Gervasio, *J. Chem. Phys.* 160, 174109, 2024): a deep-learning path-like CV ("deep locally non-linear embedding") that learns the path from a reactive trajectory without handpicking landmarks. Automatically selects the metric and generates a nonlinear combination of features.
- **DeepLNE++** (2024): extends Deep-LNE with knowledge distillation for multi-state path-like CVs.
- **WTM-eABF with adaptive path CVs** (Lesage et al., *J. Chem. Theory Comput.* 2023, 10.1021/acs.jctc.3c00938): dramatically improved sampling efficiency through stabilized extended-system dynamics.

### Critical Assessment for Our TrpB Project

| Question | Assessment |
|----------|-----------|
| Is the 1WDW-to-3CEP interpolated path reliable? | Risky. Linear interpolation in Cartesian space between two crystal structures at different resolutions, with different ligand states, may produce unphysical intermediates. The Osuna 2019 paper used 15 frames; the quality of these frames is critical. |
| Does it matter that 1WDW is PfTrpS (with TrpA) and 3CEP is StTrpS? | Yes. Using structures from different organisms and different oligomeric states (holoenzyme vs standalone) means the endpoints may not represent the same conformational basin for the same enzyme. The Osuna group chose these because they represent the clearest O and C states available. |
| Is 2D (s, z) sufficient for the COMM domain? | Probably adequate for a first-pass FEL, which is what the 2019 paper aimed for. But it cannot capture orthogonal slow modes that decouple from the O-to-C path. |
| Has anyone compared Path CV vs ML CVs for TrpB-like systems? | No direct comparison found in the literature. The closest is general work showing ML CVs outperform handcrafted CVs for complex allosteric transitions, but no TrpB-specific benchmark exists. |

---

## 3. Sketch-Map / Dimensionality Reduction CVs (Ceriotti et al. 2011)

**Key paper:** Ceriotti, M., Tribello, G.A., Parrinello, M. "Simplifying the representation of complex free-energy landscapes using sketch-map." *PNAS* 108, 13023-13028 (2011).

**Follow-up:** Tribello, G.A., Ceriotti, M., Parrinello, M. "Using sketch-map coordinates to analyze and bias molecular dynamics simulations." *PNAS* 109, 5196-5201 (2012).

**What it measures:**
Sketch-map constructs a low-dimensional (typically 2D) map of the conformational space by preserving the relative distances between configurations in a high-dimensional space. It is a nonlinear dimensionality reduction technique (related to multidimensional scaling) that focuses on preserving intermediate distances rather than very short or very long ones.

**Key assumption(s):**
- The high-dimensional conformational space can be meaningfully projected onto 2-3 dimensions while preserving the topology of the free energy landscape.
- A pre-existing dataset (e.g., from an unbiased or mildly biased simulation) is available to train the map.

**Limitations:**
- Requires a training dataset that already samples the relevant conformational space -- a chicken-and-egg problem for rare events.
- The mapping is not unique; different training sets can produce different maps.
- Sketch-map coordinates are not differentiable in a straightforward way for use as CVs in biased simulations (though this was addressed in the 2012 paper via "reconnaissance metadynamics").
- The method is computationally expensive for large proteins.

**What replaced/improved it:** ML-based methods (Deep-LDA, Deep-TDA, spectral map) provide more principled, trainable, and differentiable embeddings.

---

## 4. Deep-LDA / Deep-TDA (Bonati, Rizzi, Parrinello, 2020-2021)

**Key papers:**
- Bonati, L., Rizzi, V., Parrinello, M. "Data-Driven Collective Variables for Enhanced Sampling." *J. Phys. Chem. Lett.* 11, 2998-3004 (2020). -- introduces Deep-LDA.
- Bonati, L., Piccini, G., Parrinello, M. "Deep learning the slow modes for rare events sampling." *PNAS* 118, e2113533118 (2021). -- introduces Deep-TDA.

**What they measure:**
- **Deep-LDA:** A neural network learns a nonlinear transformation of physical descriptors (e.g., interatomic distances), followed by Fisher's linear discriminant analysis (LDA) in the final layer. The resulting CV maximally separates known metastable states.
- **Deep-TDA (Targeted Discriminant Analysis):** Instead of just separating states, the network is trained so that the projected distributions of training data in each state match target distributions (e.g., Gaussians centered at specified positions). This allows the CV to be used directly in enhanced sampling without post-processing.

**Key assumption(s):**
- Short unbiased simulations of each metastable state are available as training data.
- The relevant metastable states are known a priori (supervised learning).
- The chosen physical descriptors (input features) contain information about the slow modes.

**Limitations:**
- **Supervised:** Requires knowing the metastable states beforehand. If there are unknown intermediates, the CV will not be trained to distinguish them.
- **Training data quality:** The CVs are only as good as the preliminary simulations used for training. If the training data does not cover the transition region, the CV may be poorly defined there.
- **Generalization:** A CV trained on one system/condition may not transfer to different temperatures, mutations, or ligand states.
- **Interpretability:** The neural network is a black box; the resulting CV is a nonlinear combination of hundreds of features, making physical interpretation difficult.

**Recent improvement:** TPI-Deep-TDA (Transition Path Informed Deep-TDA) incorporates transition path information to ensure the CV passes through the correct transition state region.

**What replaced/improved it:** Methods that do not require labeled states (unsupervised approaches like spectral map, VAMPnets) or that iteratively refine CVs during simulation.

---

## 5. VAMPnets / SRVs (Mardt, Pasquali, Wu, Noe, 2018)

**Key papers:**
- Mardt, A., Pasquali, L., Wu, H., Noe, F. "VAMPnets for deep learning of molecular kinetics." *Nature Communications* 9, 5 (2018).
- Wehmeyer, C., Noe, F. "Time-lagged autoencoders: Deep learning of slow collective variables for molecular kinetics." *J. Chem. Phys.* 148, 241703 (2018).
- Chen, W., Sidky, H., Ferguson, A.L. "Nonlinear discovery of slow molecular modes using state-free reversible VAMPnets." *J. Chem. Phys.* 150, 214114 (2019).

**What they measure:**
- **VAMPnets** use the Variational Approach for Markov Processes (VAMP) to learn a mapping from molecular coordinates directly to Markov states. The network maximizes a variational score (VAMP score) that measures how well the learned features approximate the dominant eigenfunctions of the transfer operator governing the dynamics.
- **Time-lagged autoencoders (SRVs -- Slow Reversible Variables):** Autoencoders trained with a time-lag, so the bottleneck layer learns the slowest collective degrees of freedom. The encoder compresses configurations, and the decoder reconstructs the configuration after a time lag tau.

**Key assumption(s):**
- The dynamics are approximately Markovian on the timescale of the lag time tau.
- Sufficient simulation data covering the relevant transitions is available.
- The slow modes are the most important for describing the process of interest.

**Limitations:**
- **Data-hungry:** Requires extensive unbiased MD data that already samples the transitions of interest. This is a bootstrap problem -- the method that should help you sample rare events requires data from those rare events.
- **Choice of lag time:** Results depend on the lag time tau. Too short: noise dominates. Too long: loss of resolution on intermediate timescales.
- **Not directly usable as biasing CVs:** VAMPnets were originally designed for analysis (building MSMs), not for biased simulations. Using learned features as CVs in metadynamics requires additional steps.
- **Computational cost:** Training deep networks on large trajectory datasets is expensive.

**What replaced/improved it:**
- **GraphVAMPNet** (Mardt et al., 2022): uses graph neural networks instead of feedforward networks, respecting molecular topology.
- Integration with enhanced sampling: learned slow modes from VAMPnets/SRVs can be fed into OPES or metadynamics as CVs.

---

## 6. MLCV with OPES -- Combining ML CVs with Modern Enhanced Sampling

**Key references:**
- Invernizzi, M., Parrinello, M. "Rethinking Metadynamics." *J. Phys. Chem. Lett.* 11, 2731-2736 (2020). -- introduces OPES.
- "Advanced simulations with PLUMED: OPES and Machine Learning Collective Variables." arXiv:2410.18019 (2024). -- tutorial/review on combining OPES + ML CVs.

**What OPES is:**
On-the-fly Probability Enhanced Sampling (OPES) is an evolution of metadynamics from Parrinello's group. Instead of depositing Gaussian hills, OPES directly estimates and iteratively corrects the bias potential to flatten the probability distribution along the CV. It converges faster than standard well-tempered metadynamics and handles multi-dimensional CVs more efficiently.

**OPES variants:**
- **OPES-Explore:** Optimized for quickly escaping metastable states (exploration over convergence).
- **OneOPES** (2024): A replica-exchange variant that uses multiple OPES walkers.

**Why combine with ML CVs:**
OPES is more robust than metadynamics when the CV is suboptimal -- it degrades gracefully rather than catastrophically. This makes it a natural partner for ML-learned CVs, which may be imperfect. The workflow:
1. Run short unbiased simulations of metastable states.
2. Train Deep-LDA or Deep-TDA to learn a CV.
3. Use the learned CV with OPES (instead of metadynamics) for production enhanced sampling.

**Advantage over Path CV + metadynamics (our current approach):**
- No need to construct a reference path between endpoints.
- The CV is learned from data, not assumed from crystal structures.
- OPES is more forgiving of CV imperfections than well-tempered metadynamics.

**Limitation:**
- Requires the iterative train-bias-retrain cycle to converge.
- Still depends on the quality of input features and training data.
- Less mature than path CV metadynamics; fewer published applications to large allosteric systems.

---

## 7. Time-Lagged Independent Component Analysis (TICA)

**Key papers:**
- Schwantes, C.R., Pande, V.S. "Improvements in Markov State Model Construction Reveal Many Non-Native Interactions in the Folding of NTL9." *J. Chem. Theory Comput.* 9, 2000-2009 (2013). -- introduced TICA for MSM construction.
- Perez-Hernandez, G., Paul, F., Giorgino, T., De Fabritiis, G., Noe, F. "Identification of slow molecular order parameters for Markov model construction." *J. Chem. Phys.* 139, 015102 (2013). -- parallel introduction.
- Naritomi, Y., Fuchigami, S. "Slow dynamics in protein fluctuations revealed by time-structure based independent component analysis: the case of domain motions." *J. Chem. Phys.* 134, 065101 (2011). -- earliest application to proteins.

**What it measures:**
TICA finds the linear combinations of input coordinates (e.g., backbone dihedrals, interatomic distances) that have the maximum autocorrelation at a chosen lag time tau. These are the "slowest" collective motions in the data. Mathematically, it solves a generalized eigenvalue problem involving the time-lagged covariance matrix.

**Key assumption(s):**
- The slow dynamics are well-described by linear combinations of input features.
- The lag time tau is chosen appropriately (long enough to capture the slow process, short enough to retain resolution).
- Sufficient sampling of the relevant dynamics is already present in the input trajectory.

**Relation to MSMs:**
TICA is often used as a preprocessing step before building Markov State Models (MSMs). The TICA components serve as the state space in which clustering and MSM construction are performed. It was shown to be superior to PCA for this purpose because PCA maximizes variance (which may be dominated by fast, large-amplitude motions) while TICA maximizes autocorrelation (which selects for slow, kinetically relevant motions).

**Limitations:**
- **Linear method:** Cannot capture nonlinear relationships between input features. This is why kernel TICA and deep TICA (using neural networks) were developed.
- **Requires existing data:** Like VAMPnets, TICA needs trajectory data that already samples the transitions. It is an analysis tool, not an enhanced sampling method by itself.
- **Feature selection matters:** The quality of TICA components depends heavily on the input features. Using raw Cartesian coordinates gives poor results; curated features (dihedrals, contacts) are needed.
- **Not directly a biasing CV:** TICA components can be used as CVs for metadynamics, but this requires careful validation that the linear combination is physically meaningful.

**What replaced/improved it:**
- **Kernel TICA** (Schwantes & Pande, 2015): nonlinear extension using kernel trick.
- **Deep TICA:** neural network nonlinear extension.
- **VAMPnets** (Mardt et al. 2018): end-to-end deep learning that subsumes TICA as a special case.

---

## 8. Adaptive CV Learning During Simulation (Recent Work)

**Key references:**
- **REAP** (Reinforcement Learning based Adaptive Sampling): Shamsi, Z. et al. Uses reinforcement learning to determine which subset of candidate CVs is most informative at each point in the simulation. The "active" CV set changes on-the-fly as the system explores different regions of phase space.
- **Adaptive Path CVs** (Diaz Leines & Ensing, 2012; improved by Lesage et al. *J. Chem. Theory Comput.* 2023, 10.1021/acs.jctc.3c00938): The reference path is not fixed but updates during the simulation to converge toward the minimum free energy path (MFEP). Combined with WTM-eABF for dramatic efficiency gains.
- **Iterative ML-bias loops** (described in arXiv:2410.18019, 2024): The workflow alternates between running biased simulations with current ML CVs, collecting new data, retraining the CV, and running again. Each iteration improves both the CV and the sampling.
- **Spectral Map** (Rydzewski, J. *J. Phys. Chem. Lett.* 14, 5216-5220, 2023; extended in *J. Chem. Theory Comput.* 2024): Learns slow CVs by maximizing the spectral gap between slow and fast eigenvalues of a transition matrix estimated via an anisotropic diffusion kernel. A single learned CV can serve as a reaction coordinate for protein folding.

**Key advantage:**
These methods address the fundamental chicken-and-egg problem: you need good CVs to sample rare events, but you need data from rare events to learn good CVs. By iteratively updating the CV during or between simulation rounds, the sampling and CV quality improve together.

**Limitations:**
- Convergence of the adaptive cycle is not guaranteed.
- Computational overhead from retraining.
- Risk of instability if the CV changes too rapidly during a simulation (addressed by the stabilized extended-system dynamics of Lesage et al. 2023).

---

## Summary: Chronological Evolution

| Era | Method | Year | Key Idea | Status |
|-----|--------|------|----------|--------|
| Classical | Dihedral angles, distances, RMSD | 2002+ | Expert-chosen geometric CVs | Still used for simple systems |
| Path-based | Path CV (s, z) | 2007 | Progress + deviation along reference path | **Our project uses this** |
| Dimensionality reduction | Sketch-map | 2011 | Nonlinear projection preserving topology | Superseded by ML methods |
| Linear data-driven | TICA | 2011-2013 | Slowest linear combinations of features | Widely used for MSMs |
| Deep supervised | Deep-LDA, Deep-TDA | 2020-2021 | Neural net + discriminant analysis | Active development |
| Deep unsupervised | VAMPnets, SRVs | 2018 | Variational score for slow modes | Active; mainly for analysis |
| Modern sampling | OPES + ML CVs | 2020+ | Robust biasing + learned CVs | State-of-the-art |
| Deep path-like | Deep-LNE, DeepLNE++ | 2024 | Learned path CV from trajectory | Bleeding edge |
| Adaptive | REAP, adaptive path CV, iterative ML | 2019+ | CV updates during/between simulations | Active frontier |
| Spectral | Spectral Map | 2023-2024 | Maximize spectral gap for slow modes | Very recent |

---

## Implications for Our TrpB Path CV Approach

### What we should be aware of:

1. **Our approach is methodologically sound for replication.** The Osuna 2019 paper used path CVs with well-tempered metadynamics, and we are replicating their protocol. For the purpose of benchmarking, we should use exactly their method.

2. **The linear interpolation between 1WDW and 3CEP is the weakest link.** The quality of the reference path determines the quality of the free energy landscape. The Osuna group used 15 frames from Calpha interpolation. Any unphysical intermediate frames will distort the FEL.

3. **For future work beyond replication,** the clear upgrade path would be:
   - First: Use adaptive path CVs (the path converges to the MFEP during simulation)
   - Second: Train Deep-LDA or Deep-TDA from short unbiased simulations of O and C states, use with OPES
   - Third: Use Deep-LNE to learn a path-like CV directly from a reactive trajectory (if one can be obtained)

4. **The field is moving fast.** The 2024-2025 literature shows rapid convergence toward ML CVs + OPES as the new standard. Path CVs remain useful when endpoint structures are known but the transition mechanism is not.

5. **No one has done a direct Path CV vs ML CV comparison for TrpB or similar allosteric enzymes.** This would be a novel contribution if our project reaches that stage.

---

## Sources

- [Branduardi et al. 2007 - From A to B in free energy space (PubMed)](https://pubmed.ncbi.nlm.nih.gov/17302470/)
- [Ceriotti et al. 2011 - Sketch-map (PNAS)](https://www.pnas.org/content/108/32/13023)
- [Tribello et al. 2012 - Using sketch-map coordinates (PNAS)](https://www.pnas.org/doi/10.1073/pnas.1201152109)
- [Bonati et al. 2020 - Data-Driven CVs / Deep-LDA (J. Phys. Chem. Lett.)](https://pubs.acs.org/doi/abs/10.1021/acs.jpclett.0c00535)
- [Bonati et al. 2021 - Deep-TDA (PNAS)](https://www.pnas.org/doi/10.1073/pnas.2113533118)
- [Mardt et al. 2018 - VAMPnets (Nature Communications)](https://www.nature.com/articles/s41467-017-02388-1)
- [Wehmeyer & Noe 2018 - Time-lagged autoencoders (J. Chem. Phys.)](https://pubs.aip.org/aip/jcp/article/148/24/241703/958887/Time-lagged-autoencoders-Deep-learning-of-slow)
- [Schwantes & Pande 2013 - TICA for MSMs (J. Chem. Theory Comput.)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3673732/)
- [Frohlking et al. 2024 - Deep-LNE (J. Chem. Phys.)](https://pubs.aip.org/aip/jcp/article/160/17/174109/3287814/Deep-learning-path-like-collective-variable-for)
- [Rydzewski 2023 - Spectral Map (J. Phys. Chem. Lett.)](https://pubs.acs.org/doi/10.1021/acs.jpclett.3c01101)
- [Rydzewski 2024 - Spectral Map extended (J. Chem. Theory Comput.)](https://pubs.acs.org/doi/full/10.1021/acs.jctc.4c00428)
- [Lesage et al. 2023 - Adaptive Path CV stabilization (J. Chem. Theory Comput.)](https://pubs.acs.org/doi/10.1021/acs.jctc.3c00938)
- [Felts et al. 2023 - Path CV for large conformational changes (J. Phys. Chem. B)](https://pubs.acs.org/doi/10.1021/acs.jpcb.3c02028)
- [OPES + ML CVs tutorial 2024 (arXiv)](https://arxiv.org/abs/2410.18019)
- [Invernizzi & Parrinello - OPES (Parrinello group page)](https://parrinello.ethz.ch/research/opes.html)
- [Yang et al. 2024 - CV learning with geodesic interpolation (arXiv)](https://arxiv.org/html/2402.01542v3)
- [Chen et al. 2019 - State-free reversible VAMPnets (J. Chem. Phys.)](https://pubs.aip.org/aip/jcp/article/150/21/214114/197931/Nonlinear-discovery-of-slow-molecular-modes-using)
- [Tiwary & Berne 2022 - CV discovery review (RSC Advances / arXiv)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9437778/)
- [Yang et al. 2024 - From Human Learning to Machine Learning (J. Phys. Chem. Lett.)](https://pubs.acs.org/doi/10.1021/acs.jpclett.3c03542)
- [Enhanced Sampling in the Age of Machine Learning 2025 (Chemical Reviews)](https://pubs.acs.org/doi/10.1021/acs.chemrev.5c00700)
- [Laio & Parrinello 2002 - Escaping free-energy minima (PubMed)](https://pubmed.ncbi.nlm.nih.gov/12271136/)
- [Kinateder et al. 2025 - Standalone TrpB insights (Protein Science)](https://onlinelibrary.wiley.com/doi/abs/10.1002/pro.70103)
