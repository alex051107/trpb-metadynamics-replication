# JACS 2019 — Complete Computational Parameters

> Source: ja9b03646_si_001.pdf (Supporting Information)
> Paper: Maria-Solano, Iglesias-Fernández & Osuna, JACS 2019, 141, 13049–13056
> DOI: 10.1021/jacs.9b03646

---

## 1. System Preparation

| Item | Value |
|------|-------|
| Starting structure | PDB 1WDW (open *Pf*TrpS) |
| Complex used | αβ heterodimer (one TrpA + one TrpB) |
| Isolated TrpB | Manually remove TrpA from PDB |
| *Pf*TrpB⁰ᴮ² mutations | Introduced with RosettaDesign |
| Reaction intermediates modeled | Ain, Aex1, A-A, Q₂ |

### Ligand / Cofactor Parameterization

| Item | Value |
|------|-------|
| Software | Antechamber module of AMBER16 |
| Force field for ligands | GAFF (General AMBER Force Field) |
| Charge method | RESP (Restrained Electrostatic Potential) |
| QM level for charges | HF/6-31G(d) |
| QM software | Gaussian09 |
| Intermediates parameterized | IGP, G3P, Ain, Aex1, A-A, Q₂ |

### Systems Studied

| System | Intermediates | Notes |
|--------|--------------|-------|
| *Pf*TrpS (αβ) | Ain, Aex1, A-A, Q₂ | IGP in TrpA at Ain/Aex1/A-A; G3P at Q₂ |
| *Pf*TrpB (isolated) | Ain, Aex1, A-A, Q₂ | TrpA removed |
| *Pf*TrpB⁰ᴮ² (evolved) | Ain, Aex1, A-A, Q₂ | 6 DE mutations |
| *Pf*TrpA-*Pf*TrpB⁰ᴮ² | Q₂ only | Inactivation study (SI uses "respectively": this system = Q₂) |
| *Pf*TrpB₂ (dimer) | Ain only | Validation: monomer vs dimer (SI "respectively": this system = Ain) |

**Total: 12 primary systems** (3 variants × 4 intermediates)

---

## 2. Conventional MD Simulations

| Parameter | Value |
|-----------|-------|
| Software | AMBER16 (production runs) |
| Hardware | In-house GPU cluster |
| Force field (protein) | ff14SB (amber99 modification) |
| Water model | TIP3P |
| Box type | Pre-equilibrated cubic box |
| Buffer distance | 10 Å |
| Approx. water molecules | ~15,000 |
| Neutralization | Explicit counterions (Na⁺ or Cl⁻) |

### Minimization (2-stage)

| Stage | Description |
|-------|-------------|
| Stage 1 | Minimize solvent + ions; positional restraints on solute (500 kcal·mol⁻¹·Å⁻²) |
| Stage 2 | Unrestrained minimization of entire system |

### Heating

| Parameter | Value |
|-----------|-------|
| Protocol | Seven 50-ps steps (0→350 K, 50 K increments) |
| Ensemble | NVT (constant-volume, periodic boundary) |
| Timestep | 1 fs |
| Restraints | Decreasing harmonic: 210, 165, 125, 85, 45, 10 kcal/mol·Å² |
| Thermostat | Langevin |
| Bond constraints | SHAKE (constrain water molecule geometry: H-O-H angle + O-H bonds) |

### Equilibration

| Parameter | Value |
|-----------|-------|
| Duration | 2 ns |
| Ensemble | NPT |
| Pressure | 1 atm |
| Temperature | 350 K |
| Timestep | 2 fs |
| Restraints | None |

### Production MD

| Parameter | Value |
|-----------|-------|
| Duration | 500 ns per system |
| Ensemble | NVT |
| Boundary | Periodic |
| Timestep | 2 fs |
| Temperature | 350 K |
| Electrostatics | PME (Particle-Mesh Ewald) |
| Cutoff (LJ + electrostatic) | 8 Å |

---

## 3. Well-Tempered Metadynamics with Path CVs

### Collective Variables (Path CVs)

| Parameter | Value |
|-----------|-------|
| CV type | Path collective variables: s(R) and z(R) |
| s(R) meaning | Progression along the O→C path (1 = open, 15 = closed) |
| z(R) meaning | Mean square deviation (distance) from reference path |
| Reference path source | Linear interpolation between X-ray structures |
| Open reference | PDB 1WDW |
| Closed reference | PDB 3CEP |
| Number of path frames | 15 conformations |
| Atoms used for path | Cα atoms of COMM domain (residues 97–184) + base region (residues 282–305) |
| λ parameter | 2.3 × (1 / mean square displacement between successive frames) = 2.3 × (1/80) ≈ 0.029 |

### State Definitions (from s(R))

| State | s(R) range |
|-------|-----------|
| Open (O) | 1–5 |
| Partially Closed (PC) | 5–10 |
| Closed (C) | 10–15 |

### MetaDynamics Engine

| Parameter | Value |
|-----------|-------|
| MetaDynamics software | PLUMED 2 |
| MD engine (for MetaD) | GROMACS 5.1.2 |
| MetaDynamics variant | Well-tempered |

> **CRITICAL NOTE**: The conventional MD (500 ns production) used **AMBER16**.
> The metadynamics simulations used **GROMACS 5.1.2 + PLUMED2**.
> This means the equilibrated structures from AMBER were transferred to GROMACS for the MetaD runs.

### Well-Tempered MetaDynamics Parameters

| Parameter | Value |
|-----------|-------|
| Initial Gaussian height | 0.15 kcal/mol |
| Gaussian deposition pace | Every 2 ps |
| Bias factor (γ) | 10 |
| Temperature | 350 K |
| Gaussian width scheme | **Adaptive** (hills variance adapts to local FES properties) |

### Multiple-Walker Protocol

| Parameter | Value |
|-----------|-------|
| Method | Multiple-walker metadynamics |
| Starting configurations | 10 snapshots from initial MetaD run (covering all conformational space) |
| Number of walkers | 10 replicas per system |
| Simulation time per replica | 50–100 ns |
| Total simulation time per system | 500–1000 ns |
| Accumulated wall-clock equivalent | ~7 μs per system |

### Convergence Assessment

| Method | Details |
|--------|---------|
| Criterion | Monitor energy differences between O and C local minima over simulation time |
| Plots | Figures S4 and S5 in SI |
| For single-minimum systems | Compare energy of local minimum vs. higher energy region |

### FEL Post-Processing

| Step | Details |
|------|---------|
| FEL estimation | Sum Gaussian potentials from all walkers as f(CV values) |
| Metastable state extraction | Cluster structures from each local energy minimum |
| Representative structures | Obtained by clustering metastable conformations (Figure S7) |

---

## 4. Additional Simulations

### Arg159 Role Study (PfTrpB⁰ᴮ²)

| Parameter | Value |
|-----------|-------|
| Systems | 5 (R159 IN/OUT × Ain/Ser/Trp intermediates) |
| Replicas per system | 5 |
| Duration per replica | 800 ns |
| Protocol | Same as conventional MD above |

### CAVER Tunnel Analysis

| Parameter | Value |
|-----------|-------|
| Software | CAVER 3.0 |
| Snapshots | 100 per local energy minimum |
| Probe radius | 0.9 Å |
| Weighting coefficient | 1 |
| Clustering threshold | 12.0 |
| Starting point | Indole active site coordinates (aligned to PDB 4HPX, A-A intermediate) |

### SPM Analysis

| Tool | Shortest Path Map (Dijkstra on Cα correlation graph) |
|------|------|
| Distance cutoff | 6 Å (Cα neighbors) |
| Edge weight | d_ij = −log|C_ij| (correlation-based) |
| Reference | Romero-Rivera et al. ACS Catal. 2017, 7, 8524 |

### H-bond / Aromatic Interaction Analysis

| Tool | cpptraj (AmberTools16) |
|------|------|
| Aromatic atoms | Hydrogens of Phe, Tyr, Trp |
| Angle cutoff | 30° |
| Distance cutoff | 5 Å |

---

## 5. Key PDB Structures Referenced

| PDB | Role in this study |
|-----|-------------------|
| 1WDW | Starting structure (open *Pf*TrpS); open reference for path CV |
| 3CEP | Closed reference for path CV (*St*TrpS, Q analogue) |
| 5DVZ | *Pf*TrpB open (Ain) — RMSD reference |
| 5DW0 | *Pf*TrpB PC (Aex1) |
| 5DW3 | *Pf*TrpB PC (L-Trp product) |
| 4HPX | *St*TrpS closed (A-A benzimidazole) — CAVER reference |
| 5IXJ | *Pf*TrpB (Ain, L-Thr) — Ser/Trp initial conformations |
| 4HN4 | *St*TrpS closed (A-A) |

---

## 6. Summary for Replication

To replicate the JACS 2019 MetaDynamics workflow on Longleaf:

1. **System prep**: Use AMBER (ff14SB + GAFF/RESP for PLP intermediates) with TIP3P, cubic box 10 Å buffer
2. **Conventional MD**: AMBER/pmemd.cuda — 500 ns NVT production at 350 K
3. **MetaDynamics**: Transfer equilibrated structures to GROMACS+PLUMED2
   - OR: Use AMBER+PLUMED (runtime patching) if avoiding GROMACS
4. **Path CVs**: 15-frame O→C path from 1WDW→3CEP Cα interpolation (residues 97–184 + 282–305)
5. **Well-tempered MetaD**: height=0.15 kcal/mol, pace=2 ps, bias_factor=10, adaptive Gaussian width
6. **Multiple walkers**: 10 replicas × 50–100 ns each

### AMBER vs GROMACS Decision

The original paper used GROMACS for MetaD. On Longleaf we have AMBER+PLUMED. Two options:

- **Option A (recommended)**: Install GROMACS+PLUMED2 to exactly replicate the original protocol
- **Option B**: Use AMBER+PLUMED2 (already set up). The physics is identical (same force field ff14SB, same PLUMED2 MetaD engine), only the MD integrator differs. This is scientifically valid but not an exact replication.

---

*Extracted: 2026-03-27 from ja9b03646_si_001.pdf*
