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
results/                 Production outputs from Longleaf Job 44008381 (50 ns)
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

Four files required on the cluster:

```
plumed.dat         PLUMED input (PATHMSD path CV + well-tempered MetaD)
metad.mdp          GROMACS MDP (NVT, 2 fs, 350 K, 50 ns)
submit.sh          SLURM submission (volta-gpu, 1 GPU)
path_gromacs.pdb   15-frame reference path in nm, multi-model PDB
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

---

## Current production result — Job 44008381 (single walker, 50 ns)

Outputs stored under `results/`:

```
results/COLVAR              2.0 MB, 50,002 frames
results/HILLS               4.4 MB, 25,006 deposited Gaussians
results/metad_summary.png   s(t), z(t), s histogram, per-5-ns-window max s
```

| Metric | Value |
|---|---|
| Simulated time | 50.0 ns |
| Max s(R) | 4.126 |
| Frames with s > 3 | 16.94 % |
| Frames with s > 5 (PC entry) | 0.00 % |
| Frames with s > 10 (C entry) | 0.00 % |

The walker climbed monotonically (per-5-ns-window max s: 1.18 → 1.39 → 1.46 → 1.81 → 2.79 → 3.49 → …) but did not reach the Partially-Closed basin (s ≥ 5) within 50 ns. The SI protocol requires the initial single-walker run to cover s ∈ [1, 15] so the Phase 4 10-walker stage can be seeded across the full path; the current `SIGMA_MIN` / `SIGMA_MAX` configuration therefore does not complete Phase 3 of this replication.

Intervention history:

- 2026-04-09 — switched from FUNCPATHMSD to PATHMSD after re-diagnosing the λ-units issue; λ recomputed to 379.77 nm⁻² from the per-atom MSD convention.
- 2026-04-15 — widened `SIGMA` and added `SIGMA_MIN` / `SIGMA_MAX` bounds to prevent adaptive-Gaussian needle collapse; Job 44008381 used this configuration.
- 2026-04-20 — λ independently re-verified against PLUMED 2.9 `PATHMSD` / `PROPERTYMAP` / `RMSD` / `METAD` semantics and a 6-PDB CV audit (endpoints project to s ≈ 1.09 and 15.00; adjacent-frame kernel overlap exp(−2.3) = 0.10, the Branduardi tuning target). The remaining open knob is therefore the numerical `SIGMA_MIN` / `SIGMA_MAX` bounds, which the SI does not specify.

## Reproducing the single-walker run

```bash
# 1. Build the system (Phase 1) and run 500 ns conventional MD (AMBER)
bash phase1_system_setup/parameterize_plp.sh
bash phase1_system_setup/build_system_tleap.sh
sbatch phase1_system_setup/submit_production.sh

# 2. Convert to GROMACS format and generate the 15-frame reference path
python3 phase2_path_cv/convert_amber_to_gromacs.py
python3 phase2_path_cv/generate_path_cv.py --pdb-dir . --output-dir phase3_single_walker

# 3. Submit the single-walker MetaD
sbatch phase3_single_walker/submit.sh

# 4. Analyse the COLVAR + reconstruct the FES
python3 phase5_analysis/check_convergence.py --colvar results/COLVAR
python3 phase5_analysis/analyze_fes.py --hills results/HILLS
```
