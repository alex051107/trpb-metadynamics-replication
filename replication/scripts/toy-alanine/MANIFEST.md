# Alanine Dipeptide MetaDynamics Toy Test — File Manifest

**Created:** 2026-03-28
**Purpose:** Validate GROMACS 2026.0 + PLUMED 2.9 on UNC Longleaf HPC
**Directory:** `/work/users/l/i/liualex/AnimaLab/runs/toy-alanine/` (on Longleaf)

---

## File Summary

| File | Type | Size | Purpose | Key Parameters |
|------|------|------|---------|-----------------|
| **setup_alanine.sh** | Shell (exec) | 9.0 KB | Build topology, minimize, heat, equilibrate | AMBER ff14SB, TIP3P, 300 K |
| **plumed_metad.dat** | PLUMED config | 2.9 KB | Well-tempered MetaD CV definition | HEIGHT=1.2, SIGMA=0.35, BIASFACTOR=10 |
| **run_metad.mdp** | GROMACS config | 6.7 KB | Production MD parameters (10 ns NVT) | dt=0.002, nsteps=5M, T=300 K |
| **submit_metad.slurm** | SLURM script (exec) | 5.1 KB | Job submission script | partition=general, time=1h, cpus=4 |
| **analyze_fes.py** | Python3 (exec) | 11 KB | Post-processing: FES computation + plotting | plumed sum_hills + matplotlib |
| **validate_setup.sh** | Shell (exec) | 3.8 KB | Pre-flight check (syntax, file presence) | Runs before submission |
| **README.md** | Documentation | 4.1 KB | Detailed guide (what each step does) | Troubleshooting, expected output |
| **QUICKSTART.md** | Guide | 8.7 KB | Quick walkthrough (copy→run→analyze) | ~2 hour end-to-end time estimate |
| **MANIFEST.md** | This file | — | File inventory and metadata | — |

**Total:** 68 KB (not including outputs)

---

## Execution Flow

```
1. setup_alanine.sh (30 min)
   ├─ Creates: alaninedip.pdb (minimal structure)
   ├─ Creates: alaninedip_processed.gro (after pdb2gmx)
   ├─ Creates: alaninedip_solvated.gro (after solvate)
   ├─ Creates: alaninedip_ions.gro (after ion addition)
   ├─ Creates: minim.gro (after steepest descent, 1000 steps)
   ├─ Creates: heat_nvt.gro (after 100 ps heating, 10→300 K)
   ├─ Creates: equil_npt.gro (after 100 ps equilibration, 300 K)
   └─ Creates: topol.top (force field topology)

2. submit_metad.slurm (1 hour on CPU)
   ├─ Calls: gmx grompp (preprocessing)
   ├─ Creates: metad.tpr (binary run input)
   ├─ Calls: gmx mdrun -plumed (production + PLUMED bias)
   ├─ Creates: metad.trr (full trajectory)
   ├─ Creates: metad.edr (energy data)
   ├─ Creates: metad.log (GROMACS log)
   ├─ Creates: mdrun.log (SLURM captured output)
   ├─ Creates: COLVAR (CV evolution: phi, psi, bias)
   └─ Creates: HILLS (Gaussian hills for FES)

3. analyze_fes.py (5 min)
   ├─ Calls: plumed sum_hills HILLS → fes.dat
   ├─ Loads: fes.dat (2D grid)
   ├─ Creates: fes_alanine.png (2D contour plot)
   └─ Prints: Statistics (min/max FE, minima locations)
```

---

## Script Breakdown

### setup_alanine.sh

**Workflow:**
1. Activate conda (`trpb-md`)
2. Create minimal alanine dipeptide PDB (Ace-Ala-Nme, 11 atoms)
3. **pdb2gmx**: Convert PDB → GROMACS topology (AMBER ff14SB, TIP3P)
4. **editconf**: Define cubic simulation box (0.8 nm padding)
5. **solvate**: Add TIP3P water (~2,700 atoms total)
6. **genion**: Neutralize charge (add Cl⁻)
7. **grompp + mdrun**: Energy minimize (steepest descent, 1000 steps)
8. **grompp + mdrun**: Heat NVT (100 ps, 10→300 K)
9. **grompp + mdrun**: Equilibrate NPT (100 ps, 300 K)

**Outputs:** `equil_npt.gro`, `topol.top` (final equilibrated structure + topology)

**Time:** ~25–35 min (mostly MD integration)

---

### plumed_metad.dat

**Collective Variables:**
- `phi`: Torsion angle C(-1)−N−CA−C (dihedral of ACE cap)
- `psi`: Torsion angle N−CA−C−N(+1) (dihedral to NME cap)

**Well-Tempered MetaDynamics:**
```
metad: METAD ARG=phi,psi \
             PACE=500 \         # Gaussian hills every 500 steps (1 ps)
             HEIGHT=1.2 \       # Each Gaussian: 1.2 kJ/mol
             SIGMA=0.35,0.35 \  # Width: 0.35 rad (≈20°)
             BIASFACTOR=10 \    # WT-MetaD: smooth filling of CV space
             TEMP=300
```

**Output:**
- `COLVAR`: Time series (phi, psi, metad.bias) every 100 steps
- `HILLS`: Gaussian parameters (used for `plumed sum_hills`)

**Notes:**
- BIASFACTOR=10 enables well-tempered variant (explores slower, smoother FEL)
- TEMP must match simulation temperature (300 K)
- Expected ~10,000 hills over 10 ns (PACE=500, total 5M steps)

---

### run_metad.mdp

**MD Parameters:**
- **Integrator:** leap-frog (md)
- **Timestep:** dt = 0.002 ps (2 fs, standard for constrained H)
- **Duration:** nsteps = 5,000,000 → 10 ns total
- **Ensemble:** NVT (constant volume, constant temperature)
- **Temperature:** 300 K (v-rescale thermostat, tau=0.1 ps)
- **Electrostatics:** PME, rcoulomb=1.0 nm
- **VdW:** Cut-off, rvdw=1.0 nm
- **Constraints:** H-bonds (LINCS)

**Output Control:**
- nstxout=5000: Trajectory every 10 ps (positions+velocities)
- nstxtcout=500: Compressed trajectory every 1 ps
- nstenergy=100: Energy every 0.2 ps

**Output Files:**
- `metad.trr`: Full trajectory (can be 1–5 GB for 10 ns)
- `metad.xtc`: Compressed trajectory (~50 MB)
- `metad.edr`: Energy file
- `metad.log`: Text log with energy values

---

### submit_metad.slurm

**SLURM Configuration:**
```bash
--job-name=ala-dipeptide-metad
--partition=general              # CPU partition (adequate for toy system)
--ntasks=1                        # Single MPI rank
--cpus-per-task=4                 # 4 OpenMP threads
--mem=8G                          # 8 GB RAM (plenty)
--time=01:00:00                   # 1 hour walltime
--mail-type=END,FAIL              # Notify on completion
--mail-user=liualex@ad.unc.edu
```

**Key Steps:**
1. Source conda environment
2. Verify GROMACS + PLUMED versions
3. Check input files (equil_npt.gro, topol.top, .mdp, .dat)
4. Run `gmx grompp` (preprocessing)
5. Run `gmx mdrun -deffnm metad -plumed plumed_metad.dat`
6. Capture output to metad_*.log

**Performance:**
- CPU (general): ~45 min – 1 hour for 10 ns
- GPU (a100-gpu): ~10 min for 10 ns (if modified to use GPU)

---

### analyze_fes.py

**Pipeline:**
1. **plumed sum_hills** → fes.dat (converts HILLS to FES)
   - Reads 10,000+ Gaussian parameters
   - Integrates on 2D grid (phi × psi)
   - Output: 3600–4000 grid points

2. **Load FES data**
   - Parse fes.dat (3 columns: phi, psi, free_energy)
   - Build 2D numpy array

3. **Plot 2D landscape**
   - Filled contours (color gradient, blue→red)
   - Overlay contour lines (0, 2, 5, 10, 20 kJ/mol)
   - Mark expected minima (α-helix, β-sheet)
   - Save as PNG (150 dpi)

4. **Print statistics**
   - Min/max free energies
   - Global minimum location (phi, psi)
   - Expected minima energies
   - ΔG(α→β) barrier
   - Sampling time estimate

**Dependencies:**
- numpy: Array operations
- matplotlib: Plotting
- plumed: sum_hills executable

**Output:**
- `fes_alanine.png`: 2D FEL contour plot
- `fes.dat`: Raw free energy grid (plaintext)
- Console: Statistics and interpretation

---

## Configuration Reference

### Force Field & Water
| Parameter | Value | Source | Notes |
|-----------|-------|--------|-------|
| Force field | AMBER ff14SB (amber99sb-ildn) | JACS 2019 SI | In GROMACS: amber99sb-ildn.ff |
| Water model | TIP3P | JACS 2019 SI | Three-point water |
| Temperature | 300 K | setup script | v-rescale thermostat |
| Pressure | 1 atm | equil_npt.mdp | Berendsen barostat (equilibration only) |

### Alanine Dipeptide Topology
| Component | Atoms | Charge | Notes |
|-----------|-------|--------|-------|
| Acetyl cap (ACE) | C,N,CA | +1 (N+H) | Mimics N-terminus |
| Alanine | N,CA,C,O,CB | 0 | Standard alanine residue |
| N-methyl cap (NME) | C | -1 (C=O) | Mimics C-terminus |
| **Total (dry)** | **11** | **0** | After ion neutralization |
| Water molecules | ~450 | 0 | TIP3P, cubic box |
| Ions | 1 Cl⁻ | −1 | Neutralize ACE N+H |
| **Total (solvated)** | **~2,700** | **0** | Periodic boundaries |

### MetaDynamics Parameters

| Parameter | Value | Interpretation | References |
|-----------|-------|-----------------|-----------|
| Collective Variables | phi, psi | Backbone dihedral angles (−180°→+180°) | Standard Ramachandran plot |
| HEIGHT | 1.2 kJ/mol | Gaussian height | Empirical; balance exploration vs convergence |
| SIGMA | 0.35 rad | Gaussian width (≈20°) | Empirical; covers typical dihedral widths |
| PACE | 500 steps | Deposit every 1 ps | 10 ns → 10,000 hills |
| BIASFACTOR | 10 | Well-tempered bias factor | WT-MetaD; smoother FEL than vanilla MetaD |
| TEMP | 300 K | Simulation temperature | Must match MD thermostat |

### Expected Results

| Metric | Expected | Literature | Notes |
|--------|----------|-------------|-------|
| α-helix minimum | φ ≈ −60°, ψ ≈ −45° | (−60°, −45°) | Most stable conformation |
| β-sheet minimum | φ ≈ −120°, ψ ≈ +120° | (−120°, +120°) | Secondary minimum |
| ΔG(α→β) | 2–4 kJ/mol | 2–3 kJ/mol | Energy difference |
| Convergence | ~10 ns sampling | — | WT-MetaD explores both regions |

---

## File Dependencies

```
setup_alanine.sh
├─ requires: conda env (gmx, plumed)
└─ outputs: equil_npt.gro, topol.top
           ├─→ run_metad.mdp
           └─→ plumed_metad.dat

submit_metad.slurm
├─ requires: equil_npt.gro, topol.top, run_metad.mdp, plumed_metad.dat
└─ outputs: metad.tpr, metad.trr, metad.edr, COLVAR, HILLS
           └─→ analyze_fes.py

analyze_fes.py
├─ requires: HILLS, COLVAR
└─ outputs: fes.dat, fes_alanine.png
```

---

## Quick Command Reference

| Task | Command | Time | Output |
|------|---------|------|--------|
| Validate files | `bash validate_setup.sh` | <1 min | Console output |
| Build system | `bash setup_alanine.sh` | ~30 min | equil_npt.gro, topol.top |
| Submit job | `sbatch submit_metad.slurm` | — | metad_*.log (job ID printed) |
| Check job status | `squeue -u liualex` | — | Job queue |
| Monitor progress | `tail -f mdrun.log` | — | Live simulation output |
| Run analysis | `python3 analyze_fes.py` | ~5 min | fes_alanine.png, fes.dat |
| View plot | `open fes_alanine.png` (macOS) or `display` (Linux) | — | 2D FEL contour plot |

---

## Notes & Tips

1. **Test locally first?** If you have GROMACS+PLUMED on your local machine, you can test the 10 ps version:
   - Modify run_metad.mdp: `nsteps = 5000` (10 ps instead of 10 ns)
   - Reduces runtime to ~30 sec
   - Validates workflow without HPC submission

2. **Extend runtime?** For better convergence:
   - Modify run_metad.mdp: `nsteps = 10000000` (20 ns)
   - Modify submit_metad.slurm: `--time=02:00:00`
   - Deposits ~20,000 hills (more thorough sampling)

3. **Reduce runtime?** For quick test:
   - Modify run_metad.mdp: `nsteps = 2500000` (5 ns)
   - Sufficient to see both minima (faster convergence)

4. **GPU acceleration?** Modify submit_metad.slurm:
   - Change partition to `a100-gpu` or `volta-gpu`
   - Add: `#SBATCH --gres=gpu:1`
   - Reduces 10 ns from 1 hour to ~10 minutes

5. **Save disk space?** After analysis, remove:
   - `metad.trr` (~2 GB, if keeping xtc)
   - `mdrun.log`, `grompp.log` (text logs)
   - Keep: HILLS, COLVAR, fes.dat, fes_alanine.png

---

## Contact & Attribution

**Created:** Claude Code (Anthropic)
**Date:** 2026-03-28
**For:** Zhenpeng Liu (UNC Chapel Hill → Caltech/Anima Lab)
**Purpose:** TrpB MetaDynamics replication project

See `CLAUDE.md`, `NEXT_ACTIONS.md`, and project documentation for context.
