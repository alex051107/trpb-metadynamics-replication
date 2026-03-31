# Force Field & Charge Method Evolution — Research Brief

> Compiled 2026-03-31 from web search. Key findings integrated into MASTER_TECHNICAL_GUIDE.md Section 6.4.

## Force Field Summary

| FF | Year | Key Feature | PLP Suitability | Status |
|----|------|-------------|-----------------|--------|
| GAFF | 2004 | 33 atom types, transferable | Weak torsions for conjugated heterocycles | **Our project** |
| GAFF2 | ~2015 | Better vdW + torsion | Improved, Kinateder 2025 uses it | Available |
| CGenFF | 2010 | CHARMM ecosystem | Comparable to GAFF | Alternative |
| OpenFF Sage 2.0 | 2023 | SMIRNOFF, data-driven | BespokeFit per-molecule torsion optimization | Future |
| Espaloma-0.3 | 2024 | GNN-based, self-consistent protein+ligand | Untested on PLP | Future |
| MACE-OFF | 2024 | Near-DFT for organics | 100-1000x too slow for MetaD | Research |

## Charge Method Summary

| Method | Year | PLP Works? | Key Issue |
|--------|------|-----------|-----------|
| RESP (HF/6-31G*) | 1993 | Yes (our choice) | Gas-phase assumption for -2 charged cofactor |
| AM1-BCC | 2002 | **No (FP-009)** | SQM SCF diverges on PLP |
| RESP2 | 2020 | Better (gas+aqueous mix) | Not in antechamber yet |
| EspalomaCharge | 2024 | No (reproduces AM1-BCC failure) | Accelerates AM1-BCC, not RESP |
| QM/MM | Established | Gold standard for chemistry | Overkill for COMM dynamics |

## Critical Assessment

- **GAFF is the weakest link** in our parameterization chain. PLP's torsion profiles around pyridine/Schiff base/phosphate are from generic training sets.
- **RESP gas-phase assumption**: HF/6-31G(d) overpolarization "trick" was calibrated for neutral drug-like molecules, not -2 phosphorylated heterocycles. Schauperl 2020 RESP2 addresses this.
- **For COMM domain dynamics** (our question): PLP charge precision is secondary to backbone dynamics. GAFF+RESP is defensible.
- **For catalytic chemistry** (future question): Must upgrade to QM/MM.

## Sources
- Wang et al. 2004, JCC 25, 1157-1174
- Bayly et al. 1993, JPC 97, 10269-10280
- Schauperl et al. 2020, Commun. Chem. 3, 44
- Batatia et al. 2024, JACS, DOI:10.1021/jacs.4c07099
- Boothroyd et al. 2023, JCTC, DOI:10.1021/acs.jctc.3c00039
- Galvelis et al. 2024, JPCA, DOI:10.1021/acs.jpca.4c01287
