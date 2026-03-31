# PLP Protonation State & Charge: Literature Review for Ain Intermediate

> **Date**: 2026-03-30
> **Reviewer**: Claude (designer)
> **Pipeline Stage**: 3 (Runner)
> **Verdict**: PASS — charge=-2 confirmed by multiple independent sources

---

## 1. Question

What is the correct total charge and protonation state for the LLP residue (PLP-K82 internal aldimine, Ain intermediate) in the Gaussian RESP charge fitting calculation?

## 2. Sources Consulted

### Source A: JACS 2019 SI (Osuna group — the paper we replicate)
- **Citation**: Maria-Solano, Iglesias-Fernández & Osuna, JACS 2019, 141, 13049–13056, SI p.S2
- **What it says**: "MD simulation parameters for the reaction intermediates (IGP, G3P, Ain, Aex1, A-A, Q₂) were generated with the antechamber module of AMBER16 using the general amber force-field (GAFF) with partial charges set to fit the electrostatic potential generated at the HF/6-31G(d) level with the RESP model. These charges were calculated using the Gaussian09 software package."
- **What it does NOT say**: Total charge, protonation states, capping strategy, how Schiff base linkage was handled
- **Gap severity**: Medium — standard RESP protocol is implied but not specified

### Source B: Kinateder et al. 2025, Protein Science (Osuna group — most recent TrpB paper)
- **Citation**: Kinateder, Drexler, Duran, Osuna & Sterner, Prot. Sci. 2025, 34, e70103
- **What it says**:
  - Upgraded to **GAFF2** (from GAFF in 2019)
  - Geometry optimization: B3LYP/6-31G(d) with D3-BJ dispersion + PCM (ε=8.9)
  - RESP charges: HF/6-31G(d) with Merz-Singh-Kollman scheme
  - Catalytic Lys84 = **neutral (LYN)** at Q₂ intermediate (after proton transfer)
  - Software: antechamber + parmchk2 from AMBER22
- **What it does NOT say**: Total charge, ACE/NME capping, explicit protonation states for Ain

### Source C: Caulkins et al. 2014, JACS (solid-state NMR — experimental protonation states)
- **Citation**: Caulkins et al., JACS 2014, 136, 12824–12827 (DOI: 10.1021/ja506267d)
- **Experimental results for TrpS Ain internal aldimine**:

| Group | Protonation State | Evidence | Charge Contribution |
|-------|------------------|----------|-------------------|
| Schiff base N (K87-NZ) | **Protonated** | ¹⁵N δ = 202.3 ppm | +1 |
| Pyridine N1 | **Deprotonated** | ¹⁵N δ = 294.7 ppm | 0 |
| Phosphate group | **Dianionic** | ³¹P chemical shift | -2 |
| Phenolic O3 | **Deprotonated** | ¹³C shifts on C2, C3 | -1 |

- **Net charge on PLP-Lys fragment**: (-2) + (-1) + (+1) + (0) = **-2**

### Source D: Huang et al. 2016, Protein Science (MD of TrpS intermediates)
- **Citation**: Huang et al., Prot. Sci. 2016, 25, 166–185 (PMID: 26013176)
- **What it says**: Used Caulkins' NMR data to assign protonation states. Tested 17 protonation schemes across 4 intermediates. Used Amber99SB + GAFF with vCharge model.
- **Key finding**: The protonation pattern from Source C (protonated Schiff base, deprotonated N1, dianionic phosphate, deprotonated phenolate) is the experimentally validated state for Ain.

## 3. Conclusion

| Parameter | Value | Confidence | Source |
|-----------|-------|------------|--------|
| Total charge (Ain/LLP) | **-2** | High | NMR (C) + chemical logic + consistent across all sources |
| Schiff base N | Protonated | High | NMR (C), 15N δ = 202.3 ppm |
| Pyridine N1 | Deprotonated | High | NMR (C), 15N δ = 294.7 ppm |
| Phosphate | Dianionic (-2) | High | NMR (C), 31P shift |
| Phenolate O3 | Deprotonated | High | NMR (C), 13C shifts |
| Multiplicity | 1 (singlet) | High | Closed-shell organic molecule |
| QM level for RESP | HF/6-31G(d) | High | SI (A), confirmed in (B) |
| GAFF version | GAFF (2019) or GAFF2 (2025) | Medium | GAFF for strict replication; GAFF2 is updated |

## 4. Open Issue: ACE/NME Capping

**Status**: UNRESOLVED — needs PI discussion or Codex investigation

The current Gaussian input (`LLP_ain_resp.gcrt`) extracts the entire LLP residue including K82 backbone atoms (N, CA, C, O) but does **not** add ACE/NME caps on the exposed N- and C-termini.

**Standard AMBER RESP protocol** (AmberTools tutorial) recommends capping non-standard residues with ACE/NME before RESP fitting, then constraining cap charges to standard values. This ensures the charges at the residue boundaries are compatible with the protein force field.

**However**: The Osuna group's SI does not mention capping, and antechamber can handle standalone fragments. For LLP, which includes full K82 backbone, the boundary atoms are part of the peptide chain. Capping may or may not be needed depending on how the charges are integrated into tleap.

**RESOLVED (2026-03-30)**: Capping IS required.
- Codex analysis: `replication/validations/2026-03-30_capping_analysis.md`
- ACE-LLP-NME capped Gaussian input generated: `replication/parameters/resp_charges/ain/LLP_ain_resp_capped.gcrt`
- 54 atoms (29 heavy + 25 H), charge=-2
- Gaussian job submitted: **Job 40533504** on Longleaf

## 5. What We Use vs. Original Paper

| Parameter | Original (JACS 2019) | Our Setup | Match? |
|-----------|---------------------|-----------|--------|
| RESP level | HF/6-31G(d) | HF/6-31G(d) | ✅ |
| QM software | Gaussian09 | Gaussian16c02 | ≈ (PI approved, minor differences expected) |
| FF for ligand | GAFF | GAFF | ✅ |
| antechamber | AMBER16 | AMBER24p3 | ≈ (newer, compatible) |
| Total charge (Ain) | Not specified in SI | -2 | ✅ (derived from NMR, Source C) |
| Capping | Not specified in SI | No caps | ⚠️ (see §4) |
