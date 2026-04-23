# Chapter 08 — Consolidated Pros/Cons Matrix

**Purpose**: A single-file table covering every method named across Chapters 01–07. When someone asks "why X not Y?", this is your lookup.

**Scale notes**:
- **Maturity**: 1 (research code only) → 5 (widely adopted production standard)
- **Cost**: 1 (cheap) → 5 (requires cluster / hundreds of GPU hours)
- **Accuracy**: 1 (qualitative only) → 5 (rigorous, benchmarked)
- **Ligand-aware**: ✓ explicit, △ partial/post-hoc, ✗ no

---

## 8.1 Force fields (protein, classical)

| Method | Year | Maturity | Cost | Accuracy | Ligand | Sweet spot | Avoid when |
|--------|------|---------|------|----------|--------|-----------|------------|
| AMBER ff14SB | 2015 | 5 | 2 | 4 | via GAFF | Globular proteins, 10-1000 ns MD | IDPs (use disp variants) |
| AMBER ff19SB | 2020 | 4 | 2 | 4 | via GAFF2 | CMAP-corrected φ/ψ, disordered regions | Reproducing ff14SB literature |
| CHARMM36m | 2016/2020 | 5 | 2 | 4 | via CGenFF | GROMACS-native, IDP-aware variant | Cross-benchmarking with AMBER stacks |
| a99SB-disp | 2018 | 3 | 2 | 4 for IDPs | via GAFF | IDP ensembles | Non-IDP systems (slow torsion issue) |
| CHARMM36m-TIP4P-D | 2020 | 3 | 2 | 4 for IDPs | via CGenFF | IDP ensembles, GROMACS | Folded targets |
| MACE-MP-0 | 2023 | 2 | 5 | 5 | △ | Small molecules, catalysis sketches | Proteins + solvent at 100 ns+ |
| Allegro / NequIP | 2022 | 2 | 5 | 5 | △ | Small systems, QM-accurate | Protein-scale MD |

**Key insight**: The gap between classical ff14SB and ML-potentials for protein MD will close in 2027–2028. For 2026, classical is still default.

---

## 8.2 Water models

| Model | Year | Maturity | Speed | Accuracy | Sweet spot | Avoid when |
|-------|------|---------|-------|----------|-----------|------------|
| TIP3P | 1983 | 5 | 5 | 3 | AMBER ecosystem, Osuna replication | Precise water dynamics needed |
| SPC/E | 1987 | 5 | 5 | 3 | CHARMM legacy | — |
| TIP4P/2005 | 2005 | 4 | 4 | 4 | Better thermodynamics | AMBER replication studies |
| TIP4P-D | 2015 | 3 | 4 | 4 for IDPs | IDP studies | Folded proteins (breaks AMBER calibration) |
| OPC | 2014 | 4 | 4 | 4 | Modern AMBER default emerging | Breaking Osuna 2019 comparison |

---

## 8.3 Ligand parameterization (for PLP-type cofactors)

| Method | Maturity | Accuracy | Effort | Best for | Avoid when |
|--------|---------|----------|--------|----------|------------|
| GAFF + RESP (HF/6-31G*) | 5 | 3 | 2 days | Published protocol (Osuna, Baker, Houk groups) | Torsion-sensitive catalysis |
| GAFF2 + RESP | 5 | 3-4 | 2 days | Modern default | — |
| GAFF + AM1-BCC | 5 | 3 | 2 hours | Quick screens, MMPBSA | Production catalysis MD |
| OpenFF 2.0 (Sage) | 4 | 4 | 1 day | Modern open-source default | AMBER-only pipelines |
| CGenFF | 5 | 3 | 1 day | CHARMM ecosystem | AMBER ecosystem |
| QM/MM (ONIOM, AMBER-ORCA) | 3 | 5 | weeks | Chemistry step validation | Production-scale ensembles |
| ML potentials (MACE) | 2 | 4-5 | days + training | Small-molecule cases | 40k-atom systems over 100 ns |

**For TrpB-PLP**: GAFF+RESP is defensible. OpenFF 2.0 would be incrementally better. QM/MM is needed only for the α-H abstraction step, not for O↔C conformational change.

---

## 8.4 Enhanced sampling (free-energy, rare events)

| Method | Year | Maturity | Cost | Rate? | Needs CV? | Scales to >500-AA? | Sweet spot | Avoid when |
|--------|------|---------|------|-------|-----------|-------------------|-----------|------------|
| Unbiased MD | — | 5 | variable | ✓ | ✗ | ✓ | Fast motions, control | Any ΔG>6 kcal/mol barrier |
| Umbrella sampling + WHAM | 1977 | 5 | 3 | △ | ✓ | △ | Known 1D CV, rigorous PMF | Exploring unknown landscape |
| Metadynamics (standard) | 2002 | 5 | 3 | ✗ | ✓ | ✓ | Historical | WTMetaD better in all cases |
| **Well-tempered MetaD** | **2008** | **5** | **3** | **✗** | **✓** | **✓** | **Your current method** | **When OPES / WE fits better** |
| Multiple-walker MetaD | 2006 | 5 | 4 | ✗ | ✓ | ✓ | Phase 2 production (your plan) | Single-machine experiments |
| PBMetaD | 2015 | 4 | 3 | ✗ | ✓ | ✓ | Non-commuting CVs | 1-2 CV cases |
| **OPES (on-the-fly)** | **2020** | **4** | **3** | **✗** | **✓** | **✓** | **Better convergence than WTMetaD** | **Already-committed WTMetaD studies** |
| T-REMD | 1999 | 5 | 5 | △ | ✗ | ✗ | Small-system ensemble | Large proteins + solvent |
| REST2 / HREMD | 2011 | 5 | 4 | △ | ✗ | △ | Conformational sampling | Rate constants |
| Weighted ensemble (WESTPA) | 2010 | 4 | 4 | ✓ | ✓ | ✓ | Rate constants, unbiased ensemble | No good progress coordinate |
| Steered MD | 1997 | 5 | 2 | △ | ✓ | ✓ | Pulling, Jarzynski work | Equilibrium ensembles |
| String method | 2002 | 4 | 4 | △ | ✓ | △ | Path optimization | Static FES along path |
| Milestoning | 2004 | 3 | 4 | ✓ | ✓ | △ | Rate constants, long timescale | Systems without clear milestones |
| aMD / GaMD | 2015 | 4 | 3 | △ | ✗ | ✓ | Exploration, no CV | Precise FES recovery |

**Key decisions**:
- Replication: Stick with WTMetaD + PATHMSD (matches Osuna).
- Kinetics: Switch to WESTPA or add milestoning analysis.
- Convergence: Consider OPES for future work.

---

## 8.5 Collective variable methods (what your s(R), z(R) is)

| Method | Year | Maturity | Interpretability | Transferability | Best for |
|--------|------|---------|------------------|-----------------|----------|
| RMSD to reference | — | 5 | 5 | 2 | One-state tracking |
| Radius of gyration | — | 5 | 5 | 3 | Compaction |
| Native contacts Q | 1998 | 5 | 5 | 3 | Folding |
| Branduardi path CV (s, z) | 2007 | 5 | 4 | 2 | O→C conformational change |
| **PATHMSD (Leines 2012)** | **2012** | **5** | **4** | **2** | **Your method** |
| FUNCPATHMSD | 2015 | 3 | 3 | 2 | When MSD mis-behaves at endpoints |
| SPM (Shortest Path Map, Osuna) | 2016 | 4 | 4 | 3 | Correlation-driven pathway discovery |
| Committor | 1998 | 4 | 5 | — | Rigorous kinetic analysis |
| tICA-derived CV | 2013 | 4 | 3 | 3 | Data-driven slow modes |
| DeepTICA / DeepTDA | 2020 | 3 | 2 | 4 | ML-learned CVs |
| SGOOP | 2016 | 3 | 3 | 4 | Iterative CV refinement |
| VAMPnets | 2018 | 3 | 2 | 4 | Koopman-based state identification |
| State-free reversible VAMPnets | 2020 | 3 | 2 | 4 | Modern VAMPnet variant |

**Your PATHMSD choice is defensible because**: the O→C path is well-characterized structurally (X-ray endpoints known), Osuna used this, interpretability is high for the meeting audience. Swapping to DeepTDA would be defensible for follow-up variants but breaks Osuna comparison.

---

## 8.6 Protein structure prediction

| Method | Year | Maturity | Single-seq? | Ligand-aware | Sweet spot | Avoid when |
|--------|------|---------|-------------|--------------|-----------|------------|
| AlphaFold 2 | 2021 | 5 | ✗ (needs MSA) | ✗ | Single-state structure | Multi-state, de novo without MSA |
| AlphaFold-Multimer | 2022 | 5 | ✗ | ✗ | Protein-protein complexes | Ligands |
| AlphaFold 3 | 2024 | 4 | △ | ✓ | Small-molecule + nucleic acids | Server-only availability concerns |
| RoseTTAFold 2 | 2023 | 4 | △ | ✗ | Comparable to AF2 | — |
| RoseTTAFold All-Atom (RFAA) | 2024 | 4 | △ | ✓ | Ligand-bound structures | — |
| ESMFold | 2022 | 4 | ✓ | ✗ | Fast screens, no MSA | Catalytic enzymes (uses MSA poorly) |
| OmegaFold | 2022 | 3 | ✓ | ✗ | Fast single-seq | — |

---

## 8.7 Generative protein design (backbone)

| Method | Year | Maturity | Ligand-aware | Unique strength | Avoid when |
|--------|------|---------|--------------|-----------------|------------|
| RFdiffusion | 2023 | 5 | ✗ | De novo scaffolding, binder design | Enzyme pocket with ligand |
| RFdiffusionAA | 2024 | 4 | ✓ | Ligand-aware scaffolding | Very early adoption |
| **RFdiffusion3 (Dec 2025)** | **2025** | **4** | **✓** | **Current IPD release — Raswanth's "RFD3"** | — |
| Chroma (Ingraham) | 2023 | 4 | ✗ | Programmable design, symmetry | Ligand-gated design |
| FrameDiff / FrameFlow | 2023/2024 | 3 | ✗ | Flow matching over frames | Baker-lab-equivalent maturity |
| Protpardelle | 2024 | 3 | ✗ | All-atom structure diffusion | — |
| Genie2 | 2024 | 3 | ✗ | Simpler/faster than RFdiffusion | — |

---

## 8.8 Sequence design (inverse folding)

| Method | Year | Maturity | Ligand-aware | NSR (at ligand site) | Sweet spot |
|--------|------|---------|--------------|----------------------|-----------|
| ProteinMPNN | 2022 | 5 | ✗ | ~45% | General, fast, well-validated |
| **LigandMPNN** | **2025** | **5** | **✓** | **~63%** | **Enzyme redesign (e.g., TrpB PLP)** |
| ESM-IF | 2022 | 4 | ✗ | ~52% | Language-model alternative |
| MIF (MPNN-IF) | 2024 | 3 | △ | — | Research |

**For your project**: If Raswanth's pipeline is on vanilla MPNN, LigandMPNN is an easy upgrade that respects PLP geometry.

---

## 8.9 Reward / ranking / filter stacks

| Method | Year | Purpose | Maturity | Fidelity | Cost |
|--------|------|---------|----------|----------|------|
| PLACER | 2024 | F0 geometric enzyme score (Baker lab) | 4 | Low | Seconds |
| Docking (AutoDock Vina) | 2010 | Pose + score | 5 | Low-Med | Minutes |
| MD (short, 10 ns) | — | Conformational stability | 5 | Medium | GPU-hours |
| **MMPBSA** | **2000s** | **Binding ΔG estimate** | **5** | **Medium, noisy (±2-3 kcal/mol)** | **GPU-day** |
| **MetaD-derived FES** | **2002-present** | **Free energy along CV** | **5** | **High** | **GPU-week** |
| QM/MM | — | Chemistry step ΔG | 4 | High | Many GPU-weeks |
| Alchemical FEP/TI | — | Rigorous binding ΔG | 5 | High | GPU-week per compound |
| GRPO (RL) | 2024 (DeepSeek) | On-policy reward shaping | 4 | Depends on signal | Cheap in inference |
| DPO | 2023 | Offline preference learning | 4 | Depends on data | Cheap |
| MFBO | 2017+ | Multi-fidelity Bayesian opt | 4 | Adaptive | Depends |

**Raswanth's stack**: F0 (PLACER) → GRPO. F1/F2 (MD + MMPBSA) → MFBO off-gradient. This is sound because reward-hacking risk scales with fidelity signal's gaming surface.

---

## 8.10 ML for protein dynamics (generative models)

| Method | Year | Maturity | Ligand-aware | Rates? | Size limit | Conditioning |
|--------|------|---------|--------------|--------|-----------|--------------|
| Boltzmann generators | 2019 | 3 | ✗ | ✗ | Small (<100 AA) | None |
| MDGen | 2024 | 3 | ✗ | △ | <300 AA | Δt |
| BioEmu | 2024/2025 | 4 | ✗ | △ | <500 AA | Sequence |
| **STAR-MD** | **2026** | **3** | **✗** | **✗** | **<384 AA (training)** | **Sequence + Δt** |
| Distributional Graphormer | 2024 | 3 | ✗ | ✗ | Small-medium | Sequence |

**Critical gap**: zero method in this table is ligand-aware. This is your opening — propose a TrpB-PLP benchmark that exposes this gap and gives the field a concrete metric to optimize.

---

## 8.11 Classical alternatives to ML dynamics (baselines)

| Method | Year | Purpose | Maturity | Rates? | Sweet spot |
|--------|------|---------|----------|--------|-----------|
| Markov State Models | 2007+ | Rate constants from MD | 5 | ✓ | Multi-state kinetics |
| VAMPnets | 2018 | Koopman-learned MSMs | 4 | ✓ | Modern data-driven MSM |
| tICA | 2013 | Slow-mode identification | 5 | — | Preprocessing for MSM |
| Time-lagged autoencoders | 2018 | Nonlinear tICA | 4 | — | Complex systems |

**When baseline MSM beats ML**: whenever you have enough MD data for an MSM to converge. Generative models only help when MD data is insufficient.

---

## 8.12 Evaluation metrics

| Metric | Chemistry-aware? | Computational cost | When to use |
|--------|------------------|--------------------|--------------|
| RMSD distribution | ✗ | Trivial | Coarse check, apo systems |
| JSD (on RMSD distr.) | ✗ | Trivial | ML model ensemble vs MD |
| tICA mode similarity | ✗ | Low | Compare slow modes |
| VAMP-2 score | ✗ | Low | Principled Koopman scoring |
| Contact-map Recall / AA% | ✗ | Low | Topology preservation |
| FES overlap on (s,z) | △ | Medium | Direct ensemble comparison |
| Rate-constant recovery (MSM) | ✗ | High | Kinetics validation |
| **Dunathan-angle distribution** | **✓** | **Low** | **PLP enzymes only (your proposal)** |
| **Reprotonation-face geometry** | **✓** | **Medium** | **D/L selectivity (your proposal)** |
| **Lid-closure occupancy** | **△** | **Low** | **Closed-state validation** |
| **Active-site water occupancy** | **✓** | **Low** | **Catalytic geometry validation** |
| **PLP SASA** | **△** | **Low** | **Cofactor solvent exposure** |

**Takeaway**: the chemistry-aware bottom five rows are your concrete proposal. None are in ATLAS or STAR-MD. All are trivially implementable from existing MDAnalysis + MDTraj.

---

## 8.13 Memory / non-Markovian methods (for Amin's 4/11 topic)

| Method | Year | Maturity | Scaling | Data requirement |
|--------|------|---------|---------|------------------|
| Generalized Langevin equation (GLE) | 1960s | 4 | Small CVs | Long unbiased trajectory |
| Volterra iteration (direct kernel inversion) | 2016 | 3 | CV-count dependent | Heavy (~μs) |
| Likelihood-based kernel (Vroylandt 2022) | 2022 | 3 | Small CVs | Medium (~100 ns) |
| Operator learning / Neural ODE memory | 2021+ | 2 | Promising | Heavy |
| **Recurrent Neural Operator (RNO)** | **2023+ (Anandkumar)** | **2** | **Research stage** | **Unknown — big open Q** |
| Transformer-based dynamics (STAR-MD) | 2026 | 3 | Learns memory implicitly | 1k+ trajectories |

**For Amin meeting**: say "Vroylandt 2022 gives a principled likelihood-based memory kernel estimator but has only been demonstrated on small CV spaces and short timescales. Whether this extrapolates to 400-residue enzymes is exactly the open question." This is truthful and shows you did the reading.

---

## 8.14 Meta-lesson: which methods have chemistry blind spots

**The pattern across this matrix**: every ML-era method (2019+) is either ligand-agnostic or ligand-handled-by-add-on. The classical methods (MD, MetaD, US) have been ligand-capable since 1980s because they're physics-based.

**Your unique angle**: bringing explicit **chemistry** (not just ligand atoms, but catalytic geometry) into the evaluation layer. This is feasible today, takes weeks not years, and fills a genuine literature gap.

---

**Next**: Chapter 09 (Improvement levers) translates this matrix into concrete improvement proposals for the TrpB project specifically.
