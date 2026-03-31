# Enhanced Sampling Method Evolution — Research Brief

> Compiled 2026-03-31 from web search. Key findings integrated into MASTER_TECHNICAL_GUIDE.md Section 6.2.

## Timeline

| Method | Year | Key Paper | Core Idea | Status |
|--------|------|-----------|-----------|--------|
| Umbrella Sampling | 1977 | Torrie & Valleau, JCP 23 | Harmonic windows + WHAM | Classical |
| Standard MetaD | 2002 | Laio & Parrinello, PNAS 99, DOI:10.1073/pnas.202427399 | Gaussian hills in CV space | Superseded |
| Parallel Tempering MetaD | 2006 | Bussi et al., JACS 128, DOI:10.1021/ja062463w | MetaD + temperature replicas | Niche |
| Well-Tempered MetaD | 2008 | Barducci et al., PRL 100, DOI:10.1103/PhysRevLett.100.020603 | Decaying hill height (bias factor gamma) | **Our project** |
| Funnel MetaD | 2013 | Limongelli et al., PNAS 110, DOI:10.1073/pnas.1303186110 | Cone restraint for binding | Binding-specific |
| GaMD | 2015 | Miao et al., JCTC 11, DOI:10.1021/acs.jctc.5b00436 | Boost potential, no CV needed | Complementary |
| OPES | 2020 | Invernizzi & Parrinello, JPCL 11, 2731 | KDE-based bias, faster convergence | **New standard** |
| OneOPES | 2023 | Rizzi et al., JCTC 19, 5731 | OPES + replica exchange | State-of-the-art |

## Key Findings for TrpB

1. **WT-MetaD was correct for 2019** — OPES not yet published, GaMD too unfocused, REST2 gives no FES
2. **WT-MetaD's biggest weakness**: orthogonal slow DOF problem — if CV misses a coupled slow motion, FES is biased toward first-sampled basin
3. **2026 recommendation**: OPES or OneOPES + ML-learned CV (Deep-TDA)
4. **Yang et al. 2025 (Nat. Commun.)**: "biased trajectories from empirical CVs display non-physical features"
5. **GaMD developer (Miao Lab) is at UNC** — potential local resource

## Sources
- Barducci et al. 2008, PRL 100, 020603
- Invernizzi & Parrinello 2020, JPCL 11, 2731-2736
- Miao et al. 2015, JCTC 11, 3584-3595
- Rizzi et al. 2023, JCTC 19, 5731-5742
- Yang et al. 2025, Nat. Commun., DOI:10.1038/s41467-025-55983-y
- Enhanced Sampling in the Age of ML, Chem. Rev. 2025, DOI:10.1021/acs.chemrev.5c00700
