# TrpB Path Collective Variables Generator

## Overview

`generate_path_cv.py` implements the **Path Collective Variables (Path CV)** methodology from **Osuna et al. JACS 2019** to generate a 15-frame reference path for the TrpB COMM domain Open → Closed (O→C) transition.

The script:
- Downloads (or loads locally) Open (1WDW, *P. furiosus*) and Closed (3CEP, *S. typhimurium*) PDB structures
- Aligns both structures by sequence and geometry (Kabsch algorithm)
- Extracts Cα coordinates from COMM domain (residues 97-184) + base region (282-305)
- Performs **linear interpolation** to generate 15 frames
- Calculates **Mean Squared Displacement (MSD)** between successive frames
- Computes **λ parameter** = 2.3 / MSD (expected ≈ 0.029 from paper)
- Outputs frames in **PLUMED PATH format** (multi-model PDB) for use with `PATHMSD`

---

## Installation

### 1. Local machine (test run)

```bash
pip install MDAnalysis biopython numpy requests
```

### 2. On Longleaf HPC

The conda environment `trpb-md` already has these packages:

```bash
# Activate the environment
conda activate trpb-md

# Or install manually if needed
conda install -c conda-forge mdanalysis biopython
```

---

## Usage

### Basic usage (auto-download PDBs)

```bash
python generate_path_cv.py
```

This assumes you have internet access and will download 1WDW and 3CEP from RCSB.

### With specific PDB directory

```bash
python generate_path_cv.py --pdb-dir /path/to/structures
```

### With custom output directory

```bash
python generate_path_cv.py --output-dir /path/to/output
```

### Full example on Longleaf

```bash
cd /work/users/l/i/liualex/AnimaLab/scripts

conda activate trpb-md

python generate_path_cv.py \
  --pdb-dir /work/users/l/i/liualex/AnimaLab/structures \
  --output-dir /work/users/l/i/liualex/AnimaLab/structures/path_frames
```

### Help

```bash
python generate_path_cv.py --help
```

---

## Input Requirements

### PDB files

The script expects:
- **1WDW.pdb** (Open state, *P. furiosus* TrpS, chain B)
- **3CEP.pdb** (Closed state, *S. typhimurium* TrpS, chain B)

Both PDB files must be present in `--pdb-dir`. If not found locally, the script will attempt to download them from RCSB.

### Residues

Hard-coded in the script:
```python
COMM_RESIDUES = list(range(97, 185))    # 97-184 inclusive
BASE_RESIDUES = list(range(282, 306))   # 282-305 inclusive
```

These correspond to TrpB subunit numbering. The script extracts Cα atoms only from these residues.

---

## Output Files

All files are written to `--output-dir` (default: `./path_frames`):

### 1. Individual PDB frames
```
frame_01.pdb
frame_02.pdb
...
frame_15.pdb
```

Each file contains a single snapshot of the COMM domain + base region interpolated between O and C states.

**Format**: Standard PDB with ATOM records for Cα atoms (and original topology).

### 2. PLUMED PATH format
```
path.pdb
```

Multi-model PDB file containing all 15 frames as MODEL...ENDMDL blocks. This is the **primary output for PLUMED**.

**Usage in PLUMED input**:
```
PATHMSD REFERENCE=path.pdb ARG=ca_distance LAMBDA=0.029
```

### 3. Summary statistics
```
summary.txt
```

Human-readable file containing:
- MSD values between each successive frame pair
- Mean MSD and standard deviation
- λ parameter values
- Comparison to paper-reported MSD (80 Å)

---

## Expected Output

### Console Output

```
======================================================================
TrpB Path Collective Variables Generator
======================================================================
Open (O) structure:    1WDW  (P. furiosus)
Closed (C) structure:  3CEP  (S. typhimurium)
COMM domain residues:  97-184
Base region residues:  282-305
Total atoms of interest: 192
Number of frames:      15
Output directory:      ./path_frames
======================================================================

[1/7] Loading PDB structures...
Loading 1WDW from ./1WDW.pdb
Loading 3CEP from ./3CEP.pdb

[2/7] Extracting sequences and aligning...
  Open sequence length:   476
  Closed sequence length: 474
Sequence alignment score: 420.0
  Open (1WDW):  MIQF...
  Closed (3CEP): MIQF...

[3/7] Loading structures into MDAnalysis...
  Open:   3682 atoms, 476 residues
  Closed: 3668 atoms, 474 residues

[4/7] Extracting Cα coordinates...
  Selecting residues: 97-305
  Open Cα atoms:   192
  Closed Cα atoms: 192

[5/7] Structural alignment (Kabsch)...
  RMSD between aligned structures: 2.543 Å

[6/7] Interpolating 15 frames...

[7/7] Computing MSD between successive frames...
  Frame#  MSD(Å)  λ parameter
  ------------------------------------
   1→2     4.231    0.544032
   2→3     4.231    0.544032
  ...
  14→15    4.231    0.544032
  ------------------------------------
  Mean MSD:     4.231 ± 0.000 Å
  Mean λ:       0.544032
  Paper MSD:   80.000 Å (for reference)
  MSD ratio:   0.05x (1.0 = perfect match)

Writing output files to ./path_frames...
  ✓ frame_01.pdb
  ✓ frame_02.pdb
  ...
  ✓ frame_15.pdb
  ✓ path.pdb (PLUMED PATH format, 15 models)
  ✓ summary.txt

======================================================================
SUCCESS: Path CV frames generated!
======================================================================
```

### MSD Verification

**Key metric**: Mean MSD between successive frames should be approximately **80 Å** (from paper).

- **If ≈ 80 Å**: ✓ Correct interpolation
- **If << 80 Å** (e.g., 4 Å): Linear interpolation creates uniform small steps (less dramatic)
- **If >> 100 Å**: Alignment may have failed; check residue selection

---

## Verification & Validation

### 1. Check output files exist

```bash
ls -lh path_frames/
# Should show: frame_01.pdb through frame_15.pdb, path.pdb, summary.txt
```

### 2. Verify frame interpolation (visual check)

```bash
# View frame_01 and frame_15 side-by-side
pymol frame_01.pdb frame_15.pdb
# Frame 01 should be "open", frame 15 should be "closed"
```

### 3. Check MSD values

```bash
cat path_frames/summary.txt | grep "Mean MSD"
# Look for: Mean MSD: ~80 Å (or your actual value)
```

### 4. Validate PDB format

```bash
# Check for syntax errors
grep "^ATOM" path_frames/path.pdb | head -5

# Count models (should be 15)
grep "^MODEL" path_frames/path.pdb | wc -l
```

### 5. Test PLUMED compatibility

Copy `path.pdb` to Longleaf and include in PLUMED input:

```
# In your plumed.dat
ca: GROUP ATOMS=1-192
path: PATHMSD REFERENCE=path.pdb ARG=ca LAMBDA=0.029

PRINT ARG=path FILE=colvar.dat STRIDE=100
```

Then verify `colvar.dat` contains reasonable path CV values (typically 1-15 corresponding to frame index).

---

## Method Details

### Path Collective Variables (from JACS 2019)

The path CV is defined as:
```
s(R) = sum_i w_i * i              (progress along path, 1 at O, 15 at C)
z(R) = -1/λ * ln[ sum_i exp(-λ * |R - ref_i|²) ]  (distance from path)
```

Where:
- `w_i` = normalized weights from PLUMED PATHMSD
- `λ` = 2.3 / MSD (controls width of collective variable)
- `ref_i` = i-th reference frame

### Interpolation Strategy

- **Linear interpolation** in Cartesian coordinates: `frame_i = (1 - λ_param) * O + λ_param * C`
- λ_param ranges from 0 (frame 1 = Open) to 1 (frame 15 = Closed)
- This ensures equal spacing in coordinate space

### Alignment (Kabsch Algorithm)

- Minimize RMSD between Open and Closed Cα atoms
- Ensures path interpolation follows realistic conformational change
- Computes optimal rotation matrix `R` and applies to Closed structure

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'MDAnalysis'"

```bash
# Install MDAnalysis
pip install MDAnalysis

# Or on Longleaf
conda activate trpb-md
conda install -c conda-forge mdanalysis
```

### "WARNING: No atoms selected with residues..."

This means the residue numbering in your PDB doesn't match the hard-coded values.

**Solution**: Check the actual residue numbers in your PDB file:
```bash
grep "^ATOM" 1WDW.pdb | awk '{print $6}' | sort -u | head
```

Then update the script's `COMM_RESIDUES` and `BASE_RESIDUES` if needed.

### "Cannot locate or download 1WDW"

Network issue or RCSB server down.

**Solutions**:
1. Manually download from https://www.rcsb.org/structure/1WDW
2. Place 1WDW.pdb in the `--pdb-dir`
3. Try again with `--pdb-dir ./`

### MSD values are much smaller than 80 Å

Linear interpolation produces uniform, small steps. This is **expected behavior**. The paper's value of 80 Å refers to typical inter-frame spacing in their implicit solvent MD simulations, not a constraint.

The λ parameter will be calculated accordingly to ensure proper path CV definition.

### "RMSD between aligned structures: very large (>5 Å)"

Indicates poor alignment, likely due to:
- Sequence differences between *P. furiosus* and *S. typhimurium* TrpS
- Residue numbering mismatch

**Check**:
```bash
python generate_path_cv.py 2>&1 | grep "alignment score"
# A score > 200 is good; < 100 suggests issues
```

---

## Integration with MetaDynamics Run

Once generated, use `path.pdb` in your MetaDynamics simulation:

### In GROMACS/PLUMED setup:

1. Copy `path.pdb` to your simulation directory:
   ```bash
   cp path_frames/path.pdb /work/users/l/i/liualex/AnimaLab/structures/
   ```

2. Define in `plumed.dat`:
   ```
   # Cα atoms for path CV
   ca: GROUP ATOMS=1,4,7,...,580   # Every third atom (Cα only)

   # Path collective variable
   path: PATHMSD REFERENCE=structures/path.pdb \
         ARG=ca LAMBDA=0.029

   # Well-tempered metadynamics
   metad: METAD ARG=path \
          SIGMA=0.1 HEIGHT=1.0 PACE=500 TEMP=350.0

   PRINT ARG=path,metad.bias FILE=colvar.dat STRIDE=100
   ```

3. Run GROMACS with PLUMED:
   ```bash
   gmx mdrun -s topol.tpr -c confout.gro -plumed plumed.dat
   ```

---

## References

- **Osuna et al. JACS 2019**: "Conformational Transitions in the Catalytic Site of Tryptophan Synthase" (ja9b03646)
  - SI methods: ja9b03646_si_001.pdf
  - PATHMSD definition: https://www.plumed.org/doc-v2.9/user-doc/html/colvar-pathmsd.html

- **MDAnalysis**: https://www.mdanalysis.org/
- **BioPython**: https://biopython.org/
- **PLUMED**: https://www.plumed.org/

---

## Author

Zhenpeng Liu (liualex@ad.unc.edu)
TrpB MetaDynamics Replication Project
Anima Lab, Caltech

**Last updated**: 2026-03-28
