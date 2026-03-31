# Alanine Dipeptide MetaDynamics Toy Test — QUICKSTART

**Goal:** Validate GROMACS 2026.0 + PLUMED 2.9 installation on UNC Longleaf HPC.

**Time estimate:** ~2 hours total (30 min setup + 60 min MetaD run + 30 min analysis)

---

## 0. Prerequisites

- SSH access to UNC Longleaf HPC (username: `liualex`)
- Conda environment `trpb-md` set up with:
  - GROMACS 2026.0 (with PLUMED support)
  - PLUMED 2.9
  - Python 3 with numpy, matplotlib

**Check environment:**
```bash
ssh longleaf
conda activate trpb-md
gmx --version | head -2
plumed --version
which python3
```

---

## 1. Copy Files to Longleaf

```bash
ssh longleaf
mkdir -p /work/users/l/i/liualex/AnimaLab/runs/toy-alanine
cd /work/users/l/i/liualex/AnimaLab/runs/toy-alanine

# Copy all files from your local project directory
# (Adjust path as needed)
scp -r ~/projects/AnimaLab/replication/scripts/toy-alanine/* .

# Verify files
ls -la
```

Should see:
```
setup_alanine.sh
plumed_metad.dat
run_metad.mdp
submit_metad.slurm
analyze_fes.py
README.md
QUICKSTART.md
```

---

## 2. Setup System (30 minutes)

**What this does:**
- Creates alanine dipeptide topology (Ace-Ala-Nme)
- Minimizes energy
- Heats to 300 K (100 ps)
- Equilibrates at constant pressure (100 ps)
- Outputs: `equil_npt.gro`, `topol.top` (ready for production)

**Run:**
```bash
cd /work/users/l/i/liualex/AnimaLab/runs/toy-alanine
bash setup_alanine.sh
```

**Expected output:**
```
[1/7] Activating conda environment...
✓ Environment activated: /work/.../gmx
...
[8/8] NPT equilibration phase (300 K, 100 ps)...
✓ Equilibration complete: equil_npt.gro

Setup Complete!
Final structure: equil_npt.gro
```

**Check:** Look for `equil_npt.gro` and `topol.top`

---

## 3. Submit MetaDynamics Job (1 minute)

**What this does:**
- Preprocesses system (grompp)
- Submits GROMACS + PLUMED job to SLURM
- Runs 10 ns well-tempered MetaDynamics
- CVs: phi and psi dihedral angles
- Outputs: `metad.trr`, `COLVAR`, `HILLS`

**Run:**
```bash
sbatch submit_metad.slurm
```

**Check job status:**
```bash
squeue -u liualex
# or
squeue --me
```

**Monitor progress:**
```bash
tail -f metad_*.log     # Live output
# or
less mdrun.log          # Check after job starts
```

**Expected runtime:**
- CPU (general partition): ~45 min – 1 hour
- GPU (a100-gpu partition): ~10 min (if you modify submit_metad.slurm to use GPU)

**Job will produce:**
- `metad.tpr` — Input topology
- `metad.trr` — Full trajectory (can be large, ~1–5 GB)
- `metad.edr` — Energy file
- `COLVAR` — CV evolution (phi, psi, bias over time)
- `HILLS` — Gaussian hills parameters (used for FES)

---

## 4. Analyze Results (30 minutes)

**Wait for job to complete**, then:

```bash
# Check job is done
squeue -u liualex
# (should show no running jobs)

# Generate FEL plot
python3 analyze_fes.py
```

**What this does:**
1. Calls `plumed sum_hills` to compute free energy surface from HILLS
2. Loads 2D grid (phi vs psi)
3. Plots contour landscape with marked minima
4. Saves PNG and prints statistics

**Output:**
```
=== Computing Free Energy Surface from HILLS ===
[1/3] Running: plumed sum_hills --hills HILLS
✓ FES computed successfully
✓ Output: fes.dat

[2/3] Loading FES data...
✓ Loaded 3600 grid points
  Phi range: [-180.0, 180.0]°
  Psi range: [-180.0, 180.0]°

[3/3] Generating 2D FEL plot...
✓ Plot saved: fes_alanine.png

=== Free Energy Statistics ===
Minimum FE:  0.00 kJ/mol
Maximum FE:  22.34 kJ/mol
Mean FE:     8.56 kJ/mol
Range (ΔG):  22.34 kJ/mol

Global minimum at:
  φ = -54.4°
  ψ = -42.3°
  FE = 0.00 kJ/mol

Expected minima (Ramachandran plot):
  α-helix:  φ ≈ -60°,  ψ ≈ -45°  (most stable)
  β-sheet:  φ ≈ -120°, ψ ≈ +120° (secondary)

α-region energy: 0.00 kJ/mol at φ=-54°, ψ=-42°
β-region energy: 2.34 kJ/mol at φ=-120°, ψ=+120°
ΔG(α→β):        2.34 kJ/mol
```

**View results:**
```bash
ls -lh *.png *.dat
open fes_alanine.png          # macOS
# or
display fes_alanine.png       # Linux (ImageMagick)
# or download and view locally
scp longleaf:~/AnimaLab/runs/toy-alanine/fes_alanine.png .
```

---

## 5. Interpret Results

### FEL Landscape
The 2D plot shows free energy as a function of backbone dihedrals (phi, psi):
- **Blue regions** = low free energy (stable)
- **Red regions** = high free energy (unfavorable)
- **Contour lines** = energy levels (0, 2, 5, 10, 20 kJ/mol)

### Alanine Dipeptide Minima
1. **α-helix region** (φ ≈ −60°, ψ ≈ −45°)
   - **Most stable** (global minimum, ΔG = 0)
   - Expected for protein helices

2. **β-sheet region** (φ ≈ −120°, ψ ≈ +120°)
   - **Secondary minimum** (ΔG ≈ 2–3 kJ/mol relative to α)
   - Less favorable than α, but still populated

### Convergence Check
- **10 ns runtime** should be sufficient to explore both minima
- **Smooth landscape** = good sampling (PLUMED is filling the CV space)
- **Rough landscape** = may need longer simulation or lower BIASFACTOR

### Quality Metrics
✓ **GOOD** if:
- Both α and β regions are clearly visible
- ΔG between regions is 2–4 kJ/mol (literature: 2–3 kJ/mol)
- Contours are smooth (no holes)
- Sampling time > 5 ns

✗ **POOR** if:
- Only one minimum visible (sampling failed)
- ΔG is wildly different from literature (< 1 kJ/mol or > 10 kJ/mol)
- Landscape is very rough/noisy (noise, need more sampling)

---

## 6. Troubleshooting

### Setup (bash setup_alanine.sh) fails

**Error:** `gmx: command not found`
```bash
source /opt/conda/etc/profile.d/conda.sh
conda activate trpb-md
which gmx  # Should return path to gmx binary
```

**Error:** `pdb2gmx: Could not find force field file...`
- Check AMBER ff14SB is installed: `ls $GMXLIB/amber99sb-ildn.ff/`
- May need to use `amber99sb` instead (check available: `ls $GMXLIB/ | grep amber`)

**Error:** `Fatal error: Gromacs version mismatch between run input and trajectory`
- Make sure you use same GROMACS version for preprocessing and mdrun

---

### Job submission (sbatch) fails

**Error:** `Job submission failed: invalid partition`
- Check available partitions: `sinfo -p`
- Modify `submit_metad.slurm` partition (line 6): try `general`, `gpu`, `a100-gpu`, `volta-gpu`

**Error:** `Out of memory`
- System needs only ~100 MB RAM (water box is tiny)
- Check HPC status: `sinfo` (look for % used)

**Error:** `plumed: command not found` (during job)
- Conda environment not activated in submit script
- Check line 21: `conda activate "$CONDA_ENV"`

---

### Analysis (python3 analyze_fes.py) fails

**Error:** `plumed sum_hills: No such file or directory`
- Make sure PLUMED is installed: `which plumed`
- Activate conda: `conda activate trpb-md`

**Error:** `FileNotFoundError: [Errno 2] No such file or directory: 'HILLS'`
- MetaDynamics job didn't finish
- Check job status: `squeue -u liualex`
- Check logs: `cat mdrun.log | tail -50`

**Error:** `No valid data found in fes.dat`
- PLUMED sum_hills succeeded but output is empty
- Check HILLS file: `head -20 HILLS`
- May need to run sum_hills manually: `plumed sum_hills --hills HILLS --outfile fes.dat`

**Error:** Plot is blank or all white
- FES grid was not loaded properly
- Check format of fes.dat: `head -10 fes.dat`
- Expected: three tab-separated columns (phi, psi, free_energy)

---

## 7. Next Steps

Once you've validated GROMACS+PLUMED with this toy test:

1. **Check CLAUDE.md** for current project status
2. **Update NEXT_ACTIONS.md** to mark "Toy MetaD test" as ✓ complete
3. **Begin real system setup** (PfTrpS with PLP cofactor):
   - Parameterize PLP (GAFF+RESP → antechamber)
   - Build O→C conformational path (15 frames, 1WDW→3CEP)
   - Run conventional MD (500 ns)
   - Run well-tempered MetaD on real system

---

## 8. File Reference

| File | Purpose |
|------|---------|
| `setup_alanine.sh` | Build, minimize, heat, equilibrate (~30 min) |
| `plumed_metad.dat` | PLUMED well-tempered MetaD configuration |
| `run_metad.mdp` | GROMACS production MD parameters (10 ns) |
| `submit_metad.slurm` | SLURM batch script (1 hour walltime) |
| `analyze_fes.py` | Post-processing: FES computation + plotting |
| `README.md` | Detailed documentation |
| `QUICKSTART.md` | This file |

---

## 9. References

**Key Parameters (from setup):**
- Force field: AMBER ff14SB (amber99sb-ildn in GROMACS)
- Water: TIP3P
- Temperature: 300 K
- System size: ~2,700 atoms (alanine dipeptide + water box)

**MetaDynamics Settings (from plumed_metad.dat):**
- CVs: phi, psi (backbone dihedral angles)
- HEIGHT: 1.2 kJ/mol
- SIGMA: 0.35 rad (≈ 20°)
- PACE: 500 steps (1 ps between hills)
- BIASFACTOR: 10 (well-tempered)
- TEMP: 300 K

**Expected Timing:**
- Setup: 25–35 min (mostly equilibration)
- MetaD: 45–75 min (CPU; 10–15 min on GPU)
- Analysis: 5–10 min
- **Total: ~2 hours**

---

**Questions?** Check the detailed README.md in this directory.
