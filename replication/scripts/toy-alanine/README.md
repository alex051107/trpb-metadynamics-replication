# Alanine Dipeptide MetaDynamics Toy Test

Validates GROMACS 2026.0 + PLUMED 2.9 installation on UNC Longleaf HPC.

## Quick Start

```bash
# On Longleaf, in /work/users/l/i/liualex/AnimaLab/runs/toy-alanine/
ssh longleaf
cd /work/users/l/i/liualex/AnimaLab/runs/toy-alanine/

# Copy files from replication/scripts/toy-alanine/
cp -r /nas/longleaf/home/liualex/projects/AnimaLab/replication/scripts/toy-alanine/* .

# 1. Setup system (build, minimize, equilibrate)
bash setup_alanine.sh

# 2. Submit MetaDynamics job
sbatch submit_metad.slurm

# 3. Once complete, analyze FES
python3 analyze_fes.py
```

## Files in This Directory

| File | Purpose |
|------|---------|
| `setup_alanine.sh` | Build alanine dipeptide topology, minimize, heat, equilibrate |
| `plumed_metad.dat` | PLUMED input: phi/psi dihedral CVs + well-tempered MetaD |
| `run_metad.mdp` | GROMACS production MD parameters (10 ns, NVT, 300 K) |
| `submit_metad.slurm` | SLURM batch script to run MetaDynamics job |
| `analyze_fes.py` | Post-processing: compute FES and plot 2D landscape |

## What Each Step Does

### 1. `setup_alanine.sh`
- Activates conda environment (`trpb-md`)
- Creates alanine dipeptide (Ace-Ala-Nme) using `gmx pdb2gmx`
- Solvates in cubic box with TIP3P water
- Adds Cl⁻ ions for neutralization
- Energy minimization (steepest descent, 1000 steps)
- NVT heating: 100 ps from 10→300 K
- NPT equilibration: 100 ps at 300 K, 1 atm
- Outputs: `alaninedip.gro`, `topol.top`, `equil.gro` (final equilibrated structure)

### 2. `run_metad.mdp`
- 10 ns production run (5M steps, dt=0.002 ps)
- NVT ensemble, T=300 K (v-rescale thermostat)
- Calculates phi/psi dihedrals every step (for PLUMED)
- PME electrostatics, cutoffs at 1.0 nm
- Outputs: `metad.trr`, `metad.edr`, `metad.log`

### 3. `plumed_metad.dat`
- Defines phi (backbone dihedral −180°→+180°)
- Defines psi (backbone dihedral −180°→+180°)
- Well-tempered MetaD: HEIGHT=1.2 kJ/mol, SIGMA=0.35 rad, BIASFACTOR=10
- Deposits Gaussian hills every 500 steps
- Writes phi, psi, metad.bias to COLVAR every 100 steps
- Outputs: `COLVAR`, `HILLS`

### 4. `submit_metad.slurm`
- SLURM partition: `general` (CPU, adequate for toy system)
- Walltime: 1 hour
- 4 CPU cores
- Activates conda, runs GROMACS with PLUMED
- Captures stdout/stderr to `metad.log`

### 5. `analyze_fes.py`
- Runs `plumed sum_hills` to convert HILLS → free energy surface
- Loads FES (phi vs psi grid)
- Plots 2D landscape with contours
- Saves `fes_alanine.png`
- Prints min/max FE and ΔG

## Expected Output

After ~30–60 min on Longleaf `general` partition:

```
ls -la
drwxr-xr-x  step1_*.gro          # trajectory snapshots
-rw-r--r--  equil.gro             # equilibrated structure
-rw-r--r--  metad.trr, metad.edr  # production trajectory
-rw-r--r--  COLVAR                # phi, psi, bias evolution
-rw-r--r--  HILLS                 # Gaussian hills data
-rw-r--r--  fes.dat               # Free energy surface
-rw-r--r--  fes_alanine.png       # 2D FEL plot
```

### FEL Interpretation

Alanine dipeptide has two major minima:
- **α-region** (φ ≈ −60°, ψ ≈ −45°) — most stable
- **β-region** (φ ≈ −120°, ψ ≈ +120°) — secondary minimum

At 300 K, well-tempered MetaD should explore both regions within 10 ns and show ΔG ≈ 2–3 kJ/mol between them.

## Troubleshooting

### `gmx: command not found`
→ Ensure `conda activate trpb-md` is in `setup_alanine.sh`. Check: `which gmx` (should be `/work/.../conda/envs/trpb-md/bin/gmx`)

### `PLUMED warning: METAD does not recognize keyword...`
→ Verify PLUMED 2.9 was built with GROMACS interface: `plumed config has gromacs` (should be `yes`)

### Job times out (walltime exceeded)
→ 10 ns may be too long for CPU. Reduce to 5 ns in `run_metad.mdp` (2.5M steps) or request GPU partition.

### FEL plot is blank or shows only one region
→ MetaD may not have filled the CV space. Extend runtime or lower BIASFACTOR (explore faster, less "smooth" sampling).

## References

- GROMACS Manual: http://manual.gromacs.org/
- PLUMED Documentation: https://www.plumed.org/
- Original alanine dipeptide MetaD benchmark: Bonomi et al., PLoS Comp. Biol. (2009)
