# Campaign Report: osuna2019_benchmark

**Campaign ID**: osuna2019-benchmark
**Mode**: Benchmark reproduction
**Date**: 2026-03-31
**Stage completed**: Stage 3 (Runner) → Stage 4 (Skeptic) PASS

---

## Objective

Reproduce the PLP-K82 parameterization and system preparation steps from Maria-Solano, Iglesias-Fernández & Osuna, JACS 2019 (doi:10.1021/jacs.9b03646) for PfTrpS(Ain) with well-tempered MetaDynamics using GROMACS+PLUMED2.

**Downstream consumer**: Calibration baseline for GenSLM-230 vs NdTrpB pairwise comparison campaigns.

---

## Artifacts Produced

### PLP-K82 (Ain) Force Field Parameters

| Artifact | Location | Status |
|----------|----------|--------|
| Ain_gaff.mol2 | `replication/parameters/mol2/Ain_gaff.mol2` | PASS |
| Ain.frcmod | `replication/parameters/frcmod/Ain.frcmod` | PASS |

- **42 atoms** (24 heavy + 18 H), charge = -2.000
- GAFF atom types for PLP ring + Schiff base; ff14SB types for backbone (N, CA, C, O) and K82 sidechain (CB, CG, CD, CE)
- NZ (Schiff base N) = GAFF `nh` — boundary between ff14SB and GAFF domains
- RESP charges via Gaussian 16 HF/6-31G(d) with ACE/NME capping, cap charges redistributed

### Path Collective Variable

| Artifact | Location | Status |
|----------|----------|--------|
| path.pdb (15 frames) | `replication/structures/path_frames/path.pdb` | PASS |
| summary.txt | `replication/structures/path_frames/summary.txt` | PASS |

- 15-frame Cα interpolation: 1WDW (open, PfTrpS) → 3CEP (closed, StTrpS)
- 112 Cα atoms: COMM domain (97-184) + base region (282-305)
- λ(total SD) = 0.0339 (JACS 2019: ~0.029, ratio 1.17×)

### Simulation System

| Artifact | Location (Longleaf) | Status |
|----------|---------------------|--------|
| pftrps_ain.parm7 | `/work/.../AnimaLab/replication/systems/pftrps_ain/` | PASS |
| pftrps_ain.inpcrd | same | PASS |

- 39,268 atoms, orthorhombic box 76.4 × 88.1 × 73.2 Å
- ff14SB + GAFF + TIP3P, 4 Na+ counterions
- Source: 5DVZ chain A, altLoc resolved, LLP→AIN, HIS tautomers assigned

---

## Validation Summary

Full validation: `replication/validations/2026-03-31_osuna2019_benchmark_stage4_validation.md`

| Artifact | Verdict | Key Checks |
|----------|---------|------------|
| Ain_gaff.mol2 | PASS | charge=-2.000, 24/24 heavy atoms match 5DVZ, no cap residuals |
| Ain.frcmod | PASS | 0 ATTN warnings, 4 high-penalty DIHE (Schiff base, low impact) |
| path.pdb | PASS | 15 frames × 112 CA, correct residue selection |
| summary.txt | PASS | λ=0.034 after FP-015 fix (was 3.798 before) |
| tleap system | PASS | 39,268 atoms, 0 errors, AIN present, neutralized |

---

## Failure Patterns Encountered

| FP | Description | Resolution |
|----|-------------|------------|
| FP-014 | Script/live file inconsistency (iop residual) | Grep whole repo after fixing live files |
| FP-015 | calculate_msd() returned RMSD not MSD (λ 130× wrong) | Removed sqrt, added assertions, split into explicit functions |

---

## Known Limitations

1. **HIS tautomers**: HIS A 77, 180, 190 assigned by geometry heuristic — marked UNVERIFIED
2. **Missing residues 385-396**: C-terminal tail not modeled (absent from crystal structure)
3. **frcmod high-penalty DIHE**: Schiff base torsion parameters from generic GAFF analogy (penalty=136); acceptable for COMM domain MetaD, would need QM refinement for active-site mechanism studies
4. **λ ratio 1.17×**: Our λ=0.034 vs JACS λ≈0.029; small deviation likely from path construction differences (different structural alignment or atom selection). Acceptable for benchmark.

---

## Next Steps

1. **Minimization → Heating → Equilibration → 500 ns Production MD** (AMBER pmemd.cuda, 350 K)
2. **GROMACS conversion** (AMBER→GROMACS topology for MetaD with PLUMED2)
3. **Well-tempered MetaDynamics** (10 walkers, path CV, GROMACS+PLUMED2)
4. **FES analysis + SPM** → compare with JACS 2019 Figure 2a
