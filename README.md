# TrpB MetaDynamics Replication

Replication of well-tempered MetaDynamics simulations from:

> Maria-Solano, M. A.; Iglesias-Fernández, J.; Osuna, S.
> *Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution.*
> J. Am. Chem. Soc. **2019**, 141(33), 13049–13056. DOI: 10.1021/jacs.9b03646

System: *P. furiosus* TrpS β-subunit (PfTrpB) with PLP cofactor (Ain state), 39,268 atoms.

HPC: UNC Longleaf cluster (SLURM), GROMACS 2026.0 + PLUMED 2.9.2, AMBER 24p3.

---

## Structure

```
phase1_system_setup/     PLP parameterization (GAFF/RESP) + system build (tleap) + conventional MD
phase2_path_cv/          Path collective variable: 15-frame O→C reference path, λ derivation
phase3_single_walker/    Single-walker well-tempered MetaD (50 ns, PATHMSD path CV)
phase4_multi_walker/     10-walker MetaD (SI: 50–100 ns × 10 replicas, Phase 2)
phase5_analysis/         FES reconstruction (sum_hills) + convergence checks
```

---

## Phase 1 — System Setup

| Script | What it does |
|--------|-------------|
| `parameterize_plp.sh` | antechamber (GAFF) + RESP charges for Ain/Aex1/A-A/Q2 |
| `build_system_tleap.sh` | tleap: solvation + 4 Na⁺ neutralization → pftrps_ain.parm7 |
| `submit_production.sh` | 500 ns NVT conventional MD (AMBER pmemd.cuda) |

Force field: ff14SB + TIP3P, 350 K, charge −2 confirmed.

---

## Phase 2 — Path CV

| Script | What it does |
|--------|-------------|
| `convert_amber_to_gromacs.py` | ParmEd AMBER→GROMACS coordinate conversion (39,268 atoms) |
| `generate_path_cv.py` | 15-frame O→C reference path; computes λ = 379.77 nm⁻² |

λ derivation: `λ = 2.3 / MSD_adj`, where MSD_adj = 0.006056 nm² (per-atom MSD between adjacent frames over 112 Cα atoms).

---

## Phase 3 — Single Walker MetaD

Three files required on the cluster:

```
plumed.dat      PLUMED input (PATHMSD path CV + well-tempered MetaD)
metad.mdp       GROMACS MDP (NVT, 2 fs, 350 K, 50 ns)
submit.sh       SLURM submission (volta-gpu, 1 GPU)
```

Key parameters (from SI + our derivation):

| Parameter | Value | Source |
|-----------|-------|--------|
| LAMBDA | 379.77 nm⁻² | SI-derived (2.3/MSD_adj) |
| SIGMA | 0.1 (seed, nm Cartesian) | Our-choice (PLUMED default) |
| SIGMA_MIN | 0.3,0.005 (s-units, z-units) | Our-choice (FP-024 fix) |
| SIGMA_MAX | 1.0,0.05 | Our-choice |
| HEIGHT | 0.628 kJ/mol | SI: 0.15 kcal/mol |
| PACE | 1000 steps (2 ps) | SI |
| BIASFACTOR | 10 | SI |
| TEMP | 350 K | SI |

---

## Phase 4 — Multi-Walker MetaD

Triggered when single-walker max s(R) ≥ 5 (conformational space roughly covered).

```
plumed.dat         Template with __WALKER_ID__ sentinel
setup_walkers.sh   KMeans(n=10) snapshot selection → 10 walker dirs
submit_array.sh    mpirun 10-walker job (-multidir)
```

Walkers share one HILLS file on GPFS. Sync interval: WALKERS_RSTRIDE=1000 steps (2 ps).
Run `setup_walkers.sh` first; it outputs candidate frames for manual PyMOL inspection before committing.

---

## Phase 5 — Analysis

```
analyze_fes.py       plumed sum_hills wrapper + matplotlib FES plot
check_convergence.py max s(R) windowed statistics + bias saturation check
```

FES reconstruction command:
```bash
plumed sum_hills --hills HILLS --kt 2.908 --bin 200,200 --outfile fes.dat
```
kT = 2.908 kJ/mol at 350 K.
