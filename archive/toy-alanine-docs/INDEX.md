# Alanine Dipeptide MetaDynamics Toy Test — Complete File Index

**Location:** `/work/users/l/i/liualex/AnimaLab/runs/toy-alanine/` (on Longleaf)
**Total Files:** 9 (+ __pycache__)
**Total Lines:** 1,917
**Total Size:** 80 KB
**Date Generated:** 2026-03-28

---

## START HERE

### For First-Time Users
→ Read **QUICKSTART.md** (8.7 KB, ~15 min read)
- Copy files to Longleaf
- Run setup, submit job, analyze
- Expected output and interpretation

### For Detailed Information
→ Read **README.md** (4.1 KB) or **MANIFEST.md** (12 KB)
- README: What each step does + troubleshooting
- MANIFEST: Complete file inventory + configuration reference

### For Verification
→ Run **validate_setup.sh**
```bash
bash validate_setup.sh
```
Checks all files present, syntax correct, ready to go.

---

## Complete File List

### 📘 Documentation (3 files)

#### 1. **README.md** (4.1 KB, 112 lines)
**Purpose:** Detailed setup guide and troubleshooting

**Contents:**
- Quick start instructions
- What each step does (setup, MetaD, analysis)
- Expected outputs and FEL interpretation
- Troubleshooting (gmx not found, PLUMED errors, timeouts, FEL blank)
- References and next steps

**When to read:** After QUICKSTART, when things break

---

#### 2. **QUICKSTART.md** (8.7 KB, 352 lines)
**Purpose:** Copy-paste workflow from start to finish

**Contents:**
- Prerequisites (conda env, SSH access)
- Step-by-step commands (1. copy files, 2. setup, 3. submit, 4. analyze)
- Interpretation guide (FEL landscape, minima, convergence metrics)
- Detailed troubleshooting (setup, job, analysis)
- Next steps (mark as complete, parameterize PLP, conventional MD)

**When to read:** First thing after accessing Longleaf

---

#### 3. **MANIFEST.md** (12 KB, 351 lines)
**Purpose:** Complete technical reference

**Contents:**
- File summary table (name, type, size, purpose)
- Execution flow diagram (setup → job → analysis)
- Detailed script breakdown:
  - setup_alanine.sh: Build, minimize, heat, equilibrate
  - plumed_metad.dat: CV definition + WT-MetaD parameters
  - run_metad.mdp: GROMACS MD parameters
  - submit_metad.slurm: SLURM job configuration
  - analyze_fes.py: FES computation and plotting
- Configuration reference tables (force field, topology, MetaD params, expected results)
- File dependencies graph
- Quick command reference
- Notes & tips (local testing, GPU acceleration, disk space)

**When to read:** Understanding the system, extending the test, debugging

---

### 🔧 Executable Scripts (4 files)

#### 4. **setup_alanine.sh** (9.0 KB, 307 lines)
**Executable:** ✓ (chmod +x)
**Language:** Bash
**Purpose:** Build alanine dipeptide system

**What it does:**
1. Activate conda environment (`trpb-md`)
2. Create minimal alanine dipeptide PDB (11 atoms, Ace-Ala-Nme)
3. pdb2gmx: Convert to GROMACS topology (AMBER ff14SB, TIP3P)
4. editconf: Define cubic box (0.8 nm padding)
5. solvate: Add water (~2,700 total atoms)
6. genion: Neutralize charge (Cl⁻)
7. Energy minimize (steepest descent, 1000 steps)
8. Heat NVT (100 ps, 10→300 K)
9. Equilibrate NPT (100 ps, 300 K, 1 atm)

**Output:** `equil_npt.gro`, `topol.top` (ready for production)
**Time:** ~30 min
**Run:** `bash setup_alanine.sh`

**Key inline heredocs:**
- alaninedip.pdb: Minimal structure
- minim.mdp: Steepest descent parameters
- heat_nvt.mdp: NVT heating parameters
- equil_npt.mdp: NPT equilibration parameters

---

#### 5. **submit_metad.slurm** (5.1 KB, 140 lines)
**Executable:** ✓ (chmod +x)
**Language:** Bash (SLURM directives)
**Purpose:** SLURM batch script for MetaDynamics production

**SLURM configuration:**
- Partition: `general` (CPU)
- CPUs: 4 cores
- Memory: 8 GB
- Walltime: 1 hour
- Email: liualex@ad.unc.edu on END/FAIL

**What it does:**
1. Load conda environment
2. Verify GROMACS + PLUMED versions
3. Check input files (equil_npt.gro, topol.top, .mdp, .dat)
4. Run gmx grompp (preprocessing)
5. Run gmx mdrun with PLUMED interface
6. Capture outputs to metad_*.log

**Outputs:** metad.tpr, metad.trr, metad.edr, COLVAR, HILLS
**Time:** ~45 min – 1 hour
**Run:** `sbatch submit_metad.slurm`

---

#### 6. **analyze_fes.py** (11 KB, 321 lines)
**Executable:** ✓ (chmod +x)
**Language:** Python 3
**Purpose:** Post-processing: FES computation and visualization

**Pipeline:**
1. Call `plumed sum_hills HILLS → fes.dat` (converts Gaussians to FES grid)
2. Load FES data (2D grid, phi vs psi)
3. Plot 2D landscape:
   - Filled contours (color gradient blue→red)
   - Overlay contour lines (0, 2, 5, 10, 20 kJ/mol)
   - Mark α-helix (−60°, −45°) and β-sheet (−120°, +120°)
4. Print statistics:
   - Min/max free energies
   - Global minimum (phi, psi)
   - ΔG(α→β) barrier
   - Expected minima energies

**Outputs:** `fes_alanine.png`, `fes.dat`
**Time:** ~5 min
**Run:** `python3 analyze_fes.py`

**Dependencies:** numpy, matplotlib, plumed

---

#### 7. **validate_setup.sh** (3.8 KB, 146 lines)
**Executable:** ✓ (chmod +x)
**Language:** Bash
**Purpose:** Pre-flight validation (run before submitting job)

**Checks:**
1. All required files present (7 files)
2. Executable permissions correct
3. Bash syntax valid
4. Python syntax valid
5. Configuration summary (conda env, FF, MetaD params, SLURM settings)

**Output:**
- ✓ Validation PASSED (all good, ready to run)
- ✗ Validation FAILED (lists errors, fixes permissions)

**Run:** `bash validate_setup.sh` (run anytime, especially before sbatch)

---

### ⚙️ Configuration Files (2 files)

#### 8. **plumed_metad.dat** (2.9 KB, 68 lines)
**Format:** PLUMED input
**Purpose:** Define collective variables and MetaDynamics parameters

**Collective Variables:**
- `phi`: C(−1)−N−CA−C torsion (backbone dihedral)
- `psi`: N−CA−C−N(+1) torsion (backbone dihedral)

**Well-Tempered MetaDynamics:**
```
METAD ARG=phi,psi \
      PACE=500 \        # Deposit Gaussian every 500 steps (1 ps)
      HEIGHT=1.2 \      # Height: 1.2 kJ/mol
      SIGMA=0.35,0.35 \ # Width: 0.35 rad (≈20°)
      FILE=HILLS \      # Output Gaussian parameters
      BIASFACTOR=10 \   # Well-tempered (smooth FEL)
      TEMP=300          # Must match simulation T
```

**Output:**
- COLVAR: Time series (phi, psi, metad.bias) every 100 steps
- HILLS: Gaussian parameters for `plumed sum_hills`

**Notes:**
- BIASFACTOR=10 enables well-tempered variant
- ~10,000 hills deposited over 10 ns (PACE=500, nsteps=5M)

---

#### 9. **run_metad.mdp** (6.7 KB, 140 lines)
**Format:** GROMACS MD parameters
**Purpose:** Production run configuration (10 ns NVT)

**Key parameters:**
- Integrator: `md` (leap-frog)
- Timestep: `dt = 0.002` ps (2 fs)
- Steps: `nsteps = 5000000` (5M → 10 ns)
- Ensemble: NVT (constant volume)
- Temperature: `ref_t = 300` K (v-rescale, tau=0.1 ps)
- Electrostatics: PME (rcoulomb=1.0 nm)
- VdW: Cut-off (rvdw=1.0 nm)
- Constraints: H-bonds (LINCS)

**Output control:**
- nstxout=5000: Trajectory every 10 ps
- nstxtcout=500: Compressed trajectory every 1 ps
- nstenergy=100: Energy every 0.2 ps

**Output files:** metad.trr, metad.xtc, metad.edr, metad.log

---

## Typical Workflow

```
1. QUICKSTART.md (read, 15 min)
   └─ Understand overview

2. validate_setup.sh (run, <1 min)
   └─ Verify all files present

3. setup_alanine.sh (run, ~30 min)
   ├─ Build Ace-Ala-Nme topology
   ├─ Solvate + ionize
   └─ Minimize → Heat → Equilibrate
   Outputs: equil_npt.gro, topol.top

4. submit_metad.slurm (submit, 1 min)
   ├─ sbatch submit_metad.slurm
   └─ Monitor: squeue -u liualex
   Outputs: metad.trr, COLVAR, HILLS (~1 hour)

5. analyze_fes.py (run, ~5 min)
   ├─ plumed sum_hills HILLS → fes.dat
   ├─ Load 2D grid
   ├─ Plot contours
   └─ Print statistics
   Outputs: fes_alanine.png, fes.dat

6. README.md or MANIFEST.md (read for interpretation)
   └─ Understand results, troubleshoot if needed

Total time: ~2 hours
```

---

## File Relationships

```
README.md ─────────────────────────────┐
QUICKSTART.md ─────────────────────────┤
MANIFEST.md ──────────────────────────┐│
validate_setup.sh ──┐                 ││
                    ├─ (checks) ─────────┤
setup_alanine.sh ───┤                 ││
plumed_metad.dat ───┼─→ run ─→ equil_npt.gro ──┐
run_metad.mdp ──────┤                 │  │     │
                    │                 │  │     ├─→ submit_metad.slurm ─→ HILLS
submit_metad.slurm ─┴─→ (requires) ───┘  │              │
                                         │              ├─→ COLVAR
analyze_fes.py ─────────────────────────→│              │
                                         └──────────────┘
```

---

## Key Metrics & Configuration

| Item | Value | Unit |
|------|-------|------|
| **System size** | 2,700 | atoms |
| **Simulation time** | 10 | ns |
| **Timestep** | 0.002 | ps |
| **Total steps** | 5,000,000 | — |
| **Temperature** | 300 | K |
| **Force field** | AMBER ff14SB | — |
| **Water model** | TIP3P | — |
| **MetaD HEIGHT** | 1.2 | kJ/mol |
| **MetaD SIGMA** | 0.35 | rad |
| **MetaD PACE** | 500 | steps |
| **MetaD BIASFACTOR** | 10 | — |
| **Expected α-helix ΔG** | 0 | kJ/mol |
| **Expected β-sheet ΔG** | 2–3 | kJ/mol |
| **CPU runtime** | 45–60 | min |
| **GPU runtime** | ~10 | min |

---

## Quick Reference

### Run Alanine Toy Test
```bash
ssh longleaf
cd /work/users/l/i/liualex/AnimaLab/runs/toy-alanine/
bash validate_setup.sh          # ~1 min
bash setup_alanine.sh           # ~30 min
sbatch submit_metad.slurm       # ~1 hour
python3 analyze_fes.py          # ~5 min
```

### Check Job Status
```bash
squeue -u liualex
tail -f mdrun.log
```

### Download Results
```bash
scp longleaf:~/AnimaLab/runs/toy-alanine/fes_alanine.png .
```

---

## Contact & Attribution

**Created:** Claude Code (Anthropic)
**Date:** 2026-03-28
**For:** Zhenpeng Liu, UNC Chapel Hill
**Project:** TrpB MetaDynamics Replication (Caltech/Anima Lab)

See `CLAUDE.md` and project documentation for full context.
