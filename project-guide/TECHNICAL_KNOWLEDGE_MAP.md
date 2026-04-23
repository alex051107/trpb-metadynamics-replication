# TECHNICAL KNOWLEDGE MAP — TrpB MetaDynamics × Anima/Arvind Lab

**Purpose**: Complete technical reference for Zhenpeng Liu to (a) hold his own in the 4/23 Amin meeting, (b) have independent aesthetic to judge improvement plans across the lab's project stack, (c) know the pros/cons of every method in the pipeline.

**Created**: 2026-04-19
**Total**: 10 chapters, ~40,000 words, ~200 KB of markdown

**Reading time**:
- **Minimal path** (meeting prep, 2 hours): Ch 00 + Ch 03 §3.4 + Ch 05 §2 + Ch 09 §9.4
- **Full pass** (complete understanding, ~6 hours total): Ch 00 → 01 → 02 → ... → 09 in order
- **Reference-only pattern**: Ch 00 first, then dip into specific chapters as questions arise

---

## Chapter index

| # | Title | Words | File | Core topic |
|---|-------|-------|------|-----------|
| 00 | **TL;DR for Amin Meeting** | ~1,500 | `knowledge-map/00_tldr_for_amin_meeting.md` | Compressed meeting-prep reference |
| 01 | **MD Foundations** | ~2,500 | `knowledge-map/01_md_foundations.md` | Force fields, water, thermo/barostats, software stack |
| 02 | **Enhanced Sampling** | ~7,500 | `knowledge-map/02_enhanced_sampling.md` | Where WTMetaD+PATHMSD sits in the full taxonomy |
| 03 | **PLP Chemistry & TrpB Mechanism** | ~3,500 | `knowledge-map/03_plp_chemistry.md` | Dunathan, quinonoid, D/L selectivity, parameterization |
| 04 | **Protein Design ML Pipeline** | ~5,400 | `knowledge-map/04_protein_design_ml.md` | RFdiffusion, MPNN/LigandMPNN, GenSLM, GRPO, MFBO |
| 05 | **ML for Dynamics (STAR-MD & landscape)** | ~7,500 | `knowledge-map/05_dynamics_ml.md` | STAR-MD deep dive, BioEmu, MDGen, Boltzmann, MSMs |
| 06 | **Memory Kernels & Neural Operators** | ~3,500 | `knowledge-map/06_memory_kernels_neural_operators.md` | Mori-Zwanzig, GLE, FNO, MemNO |
| 07 | **Evaluation Metrics** | ~6,500 | `knowledge-map/07_evaluation_metrics.md` | JSD/tICA/VAMP-2 + chemistry-aware proposals |
| 08 | **Pros/Cons Matrix** | ~2,500 | `knowledge-map/08_pros_cons_matrix.md` | Consolidated table, every method in one place |
| 09 | **Improvement Levers** | ~3,500 | `knowledge-map/09_improvement_levers.md` | 15 concrete improvement opportunities, ranked |

---

## "Find X here" lookup table

Use this when a specific topic comes up and you need to navigate fast.

### Enhanced sampling / MD theory
| Topic | Chapter | Section |
|-------|---------|---------|
| Why TIP3P not OPC | 01 | §1.3 |
| AMBER ff14SB vs ff19SB vs CHARMM36m | 01 | §1.2 |
| HMR (hydrogen mass repartitioning) | 01 | §1.1 |
| PME electrostatics | 01 | §1.5 |
| Kramers rate theory arithmetic | 02 | §1 |
| Well-tempered MetaD derivation | 02 | §3 + MASTER_TECHNICAL_GUIDE.md §6 |
| OPES vs WTMetaD (when to switch) | 02 | §8 |
| WESTPA weighted ensemble | 02 | §7 |
| REST2 / HREMD | 02 | §6 |
| PATHMSD math + λ derivation | 02 | §4 + MASTER_TECHNICAL_GUIDE.md §5 |
| DeepTDA / ML-learned CVs | 02 | §4.5 |
| Umbrella sampling + WHAM/MBAR | 02 | §5 |
| Adaptive Gaussian width (SIGMA) | 02 | §3 + failure-patterns.md FP-024 |
| Multi-walker metadynamics | 02 | §3.3 |

### Protein / enzyme chemistry
| Topic | Chapter | Section |
|-------|---------|---------|
| PLP catalytic cycle | 03 | §3.2 |
| Dunathan hypothesis | 03 | §3.3 |
| Quinonoid intermediate + chirality | 03 | §3.4 |
| TrpB COMM domain O/PC/C | 03 | §3.5 |
| PDB residues (LLP, PLS, 0JO) | 03 | §3.6 |
| GAFF + RESP parameterization gotchas | 03 | §3.7 |
| D-serine redesign problem | 03 | §3.8 |
| Why TrpB is hard for ML-dynamics | 03 | §3.9 |

### Protein design ML
| Topic | Chapter | Section |
|-------|---------|---------|
| AlphaFold 2/3 architectures | 04 | §2 |
| RFdiffusion / RFdiffusion3 | 04 | §3 |
| RoseTTAFold All-Atom (RFAA) | 04 | §2, §3 |
| ProteinMPNN / LigandMPNN | 04 | §4 |
| ESM-IF | 04 | §4 |
| GenSLM | 04 | §6 |
| Theozyme philosophy | 04 | §5 |
| PLACER scoring | 04 | §7 |
| GRPO (DeepSeek 2024) | 04 | §7 |
| DPO vs PPO vs GRPO | 04 | §7 |
| MFBO (multi-fidelity BO) | 04 | §7 |
| Baker lab Kemp eliminase history | 04 | §5 |

### ML for dynamics
| Topic | Chapter | Section |
|-------|---------|---------|
| STAR-MD architecture | 05 | §2 |
| STAR-MD limitations (ligand, Δt, scale) | 05 | §2 + Ch 00 §1 |
| BioEmu | 05 | §3 |
| MDGen | 05 | §4 |
| Boltzmann generators | 05 | §5 |
| Flow matching | 05 | §6 |
| Markov state models | 05 | §7 |
| VAMPnets | 05 | §7 |
| Time-lagged autoencoders | 05 | §7 |
| AlphaFlow | 05 | §4 |
| Distributional Graphormer | 05 | §3 |

### Memory / non-Markovian dynamics
| Topic | Chapter | Section |
|-------|---------|---------|
| Why coarse-graining → memory | 06 | §1 |
| Generalized Langevin equation | 06 | §2 |
| Memory kernel estimation methods | 06 | §3 |
| Vroylandt 2022 likelihood estimator | 06 | §3 |
| Ayaz 2021 / Dalton 2023 protein folding | 06 | §3 |
| Fourier Neural Operator (FNO) | 06 | §4 |
| DeepONet | 06 | §4 |
| Neural Operator general theory | 06 | §4 |
| MemNO (memory-augmented FNO) | 06 | §5 |
| Markov Neural Operator | 06 | §5 |
| "Recurrent Neural Operator" (what Anandkumar meant) | 06 | §5 |
| What the undergrad can actually contribute | 06 | §7 |
| Berezhkovskii-Makarov Markovianity test | 06 | §3 |

### Evaluation metrics
| Topic | Chapter | Section |
|-------|---------|---------|
| JSD, Recall, AA% | 07 | §2 |
| tICA | 07 | §2 |
| VAMP-2 score | 07 | §2 |
| Free-energy-surface overlap | 07 | §2 |
| Why Cα-based metrics fail for enzymes | 07 | §3 |
| Precedents for chemistry-aware validation | 07 | §4 |
| Dunathan angle distribution as metric | 07 | §5 |
| Reprotonation-face geometry metric | 07 | §5 |
| Lid-closure metric | 07 | §5 |
| Active-site water occupancy | 07 | §5 |
| PLP SASA metric | 07 | §5 |
| Benchmark packaging | 07 | §6 |
| Reward-hacking concerns | 07 | §1 |

### Consolidated tables & judgment
| Topic | Chapter | Section |
|-------|---------|---------|
| All force fields compared | 08 | §8.1 |
| All water models compared | 08 | §8.2 |
| All enhanced-sampling methods | 08 | §8.4 |
| All CV methods | 08 | §8.5 |
| All structure-prediction | 08 | §8.6 |
| All generative design | 08 | §8.7 |
| All inverse folding | 08 | §8.8 |
| All reward/filter stacks | 08 | §8.9 |
| All ML-dynamics methods | 08 | §8.10 |
| All evaluation metrics | 08 | §8.12 |
| All memory/non-Markovian methods | 08 | §8.13 |

### Strategic / ownership-level decisions
| Topic | Chapter | Section |
|-------|---------|---------|
| Top 5 summer deliverables ranked | 09 | §9.9 |
| TrpB MetaD Benchmark Pack spec | 09 | §9.4 (V1) |
| Markovianity diagnostic proposal | 09 | §9.4 (V3) |
| STAR-MD failure quantification | 09 | §9.4 (V2) |
| OPES vs WTMetaD benchmark | 09 | §9.3 (M1) |
| Contingency table (if lab pivots) | 09 | §9.11 |
| What NOT to propose | 09 | §9.10 |
| Self-assessment of this chapter's limits | 09 | §9.12 |

---

## Minimal reading path for the Amin meeting

**If you only have 2 hours before the 4/23 meeting, read in this order:**

1. **Ch 00 entire** (20 min) — the meeting compression.
2. **Ch 03 §3.4** (quinonoid chirality, 10 min) — Raswanth's Slack concern.
3. **Ch 05 §2** (STAR-MD deep dive + limitations, 30 min) — what Amin just published.
4. **Ch 06 §1-3** (Mori-Zwanzig intuition + memory kernel estimation, 40 min) — Amin's 4/11 topic.
5. **Ch 09 §9.4 and §9.9** (your proposed owned contributions, 20 min) — what you pitch.

That's 2 hours. After this you can talk about anything likely to come up.

---

## Full reading path

**If you have a weekend (~6 hours):**

Read straight through Ch 00 → Ch 09. Budget:
- Day 1 morning: Ch 00 + Ch 01 + Ch 02 (MD + enhanced sampling, your stack)
- Day 1 afternoon: Ch 03 + Ch 04 (chemistry + design pipeline)
- Day 2 morning: Ch 05 + Ch 06 (dynamics ML + memory kernels)
- Day 2 afternoon: Ch 07 + Ch 08 + Ch 09 (evaluation + synthesis)

---

## Interactive use pattern

**When mid-meeting you realize you need depth on something**, Ctrl+F the lookup table above. Most answers are 3–5 sentences, findable in <30 seconds.

---

## Videos and tutorials referenced (consolidated)

**Molecular dynamics**:
- Justin Lemkul GROMACS tutorials (mdtutorials.com)
- AMBER tutorial site (ambermd.org/tutorials)
- Giovanni Bussi MetaD lectures (YouTube)

**Enhanced sampling**:
- PLUMED-NEST tutorials (plumed-nest.org)
- CECAM workshops (cecam.org/library) — 2023/2024 on ML for MD
- Luigi Bonati talks on ML CVs (YouTube)

**Protein design**:
- David Baker lab talks (YouTube, multiple)
- RFdiffusion paper-walkthrough videos
- Sergey Ovchinnikov talks

**Dynamics ML**:
- Frank Noé generative learning talks (YouTube: `XhAP2VNPVhg` and others)
- Tommi Jaakkola MIT CSAIL (YouTube: `GLEwQAWQ85E`)
- Microsoft Research BioEmu talk
- Cecilia Clementi talks on generative MD

**Memory kernels / neural operators**:
- Anima Anandkumar 2021 FNO talk
- Anima Anandkumar 2023 AI-for-Science keynote
- George Karniadakis DeepONet CBMM lecture 2020
- Frank Noé IPAM 2023 talk on memory in biomolecules

**Enzyme chemistry**:
- Frances Arnold lectures on directed evolution
- Richard Silverman organic chemistry of enzymes (textbook)

---

## Related existing project docs (do not duplicate)

These are already in the project and should be read alongside the knowledge map:

- `project-guide/MASTER_TECHNICAL_GUIDE.md` — detailed derivations of WTMetaD + PATHMSD math
- `project-guide/FEL_DEEP_DIVE_AND_NEW_DIRECTIONS.md` — FES reconstruction + reweighting
- `project-guide/FULL_LOGIC_CHAIN.md` — 12-chapter project logic from zero
- `project-guide/PLP_SYSTEM_SETUP_LOGIC_CHAIN.md` — PLP parameterization walkthrough
- `project-guide/REWARD_FUNCTION_LITERATURE_REVIEW_v2.md` — detailed reward-design survey
- `project-guide/CRITICAL_THINKING_PROMPTS.md` — sanity-check questions
- `project-guide/TrpB_Replication_Tutorial_EN.md` / `_CN.md` — the student-facing tutorial
- `replication/validations/failure-patterns.md` — canonical debug log (FP-020 through FP-027)

---

## How this knowledge map was produced

2026-04-19. Five research agents dispatched in parallel (Mori-Zwanzig, STAR-MD, protein-design-ML, enhanced-sampling, evaluation-metrics). Three additional chapters written directly from existing project knowledge (MD foundations, PLP chemistry, TL;DR). Two synthesis chapters (pros/cons matrix, improvement levers) written last to consolidate.

Each chapter includes:
- Intuition-first explanation (math only when needed)
- Pros/cons table
- "If asked X, say Y" meeting-prep Q&A where relevant
- Landmark paper citations with author + year
- Video recommendations
- Honest limitations / uncertainty flags

Total effort: one working session, ~2 hours of parallel agent dispatch + synthesis.

---

## Self-assessment / known gaps

This knowledge map:
- ✓ Covers the methods you will encounter in the Amin meeting
- ✓ Gives you independent judgment on pros/cons
- ✓ Provides concrete improvement levers you could own
- ✗ Is not a substitute for reading the actual papers — citations point to originals
- ✗ Will age poorly on the ML-for-dynamics chapter (field moves fast; 2027 may invalidate half)
- ✗ Does not cover lab-internal tooling (GenSLM implementation specifics, Longleaf-specific HPC setup) — that's in CLAUDE.md and PROTOCOL.md
- ✗ Has limited coverage of wet-lab validation protocols (Ziqi's work) — project_timeline_2026-04-18.md has the collaborative-stack context

If you want deeper treatment of any specific topic, follow the citations. The knowledge map is the index, not the encyclopedia.

---

**You're ready for Wednesday. Good luck.**
