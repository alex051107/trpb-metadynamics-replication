# Modern Alternatives to MD+MetaD — Research Brief

> Compiled 2026-03-31 from web search. Key findings integrated into MASTER_TECHNICAL_GUIDE.md Section 6.2-6.5.

## Can It Replace MetaD for TrpB?

| Method | Replace MetaD? | Production-ready? | FEL Quality | Key Limitation |
|--------|---------------|-------------------|-------------|----------------|
| AF-Cluster / tAF2 | Partially (screening) | Yes | Qualitative | No energetics |
| AlphaFlow | No | Nearly | Qualitative | No free energies |
| Boltzmann Generators | No | No (max 56 residues) | Exact in principle | Scale limit |
| Diffusion models (DiG) | No | No | No Boltzmann weighting | No guarantees |
| CG + Backmapping | No | Yes | Poor for enzymes | Loses active site |
| String method / TPS | Yes (more rigorous) | Yes (expert) | Excellent | Very expensive |
| **OPES** | **Yes (direct upgrade)** | **Yes** | **Quantitative** | Still needs CVs |
| Weighted Ensemble | Yes (complementary) | Yes (WESTPA 2.0) | Quantitative + kinetics | Needs many GPUs |
| ML potentials (MACE) | No | No at protein scale | Better in principle | ~7000 atoms infeasible |
| tAF2-MD-SPM (Osuna) | Partially (screening) | Yes | Semi-quantitative | Not rigorous FEL |

## Key Finding: Osuna Group Has Moved Beyond WT-MetaD

Osuna group now uses **tAF2-MD-SPM** (Faraday Discussions 2024) for rapid screening:
1. Template-based AlphaFold2 → diverse conformations (minutes)
2. Short 10-50 ns MD from each tAF2 structure (hours)
3. SPM analysis → identify conformational hotspots (hours)

**Same conformational insights as WT-MetaD, but hours instead of weeks.** They still use MetaD for quantitative FEL when needed.

## If Starting TrpB Project in 2026

| Aspect | 2019 (Osuna) | 2026 (Today) |
|--------|-------------|--------------|
| Endpoint structures | PDB curation | AF2/tAF2 in minutes |
| Enhanced sampling | WT-MetaD | OPES |
| CV selection | Expert intuition | ML-guided (Deep-TDA) |
| Variant screening | Full MetaD per variant | tAF2-MD-SPM in hours |
| Kinetics | Not from MetaD | WE or OPES-flooding |
| Force fields | ff14SB (unchanged) | ff14SB (ML potentials not yet feasible) |

## What HASN'T Changed (Unsolved)
1. CV selection remains the central problem
2. Force field accuracy ceiling (~2-4 kJ/mol systematic errors)
3. PLP parameterization still needs manual GAFF+RESP
4. Convergence verification is hard regardless of method
5. Timescale gap (us-ms) persists

## Sources
- AF-Cluster: Nature 2023, DOI:10.1038/s41586-023-06832-9
- AlphaFlow: ICML 2024, arXiv:2402.04845
- Scalable BG: ICLR 2024, arXiv:2401.04246
- DiG: Nat. Mach. Intell. 2024, DOI:10.1038/s42256-024-00837-3
- WESTPA 2.0: JCTC 2022, DOI:10.1021/acs.jctc.1c01154
- OPES: JPCL 2020; OneOPES: JCTC 2023
- Osuna tAF2-MD-SPM: Faraday Discussions 2024, DOI:10.1039/D3FD00156C
- MACE-OFF: JACS 2024, DOI:10.1021/jacs.4c07099
