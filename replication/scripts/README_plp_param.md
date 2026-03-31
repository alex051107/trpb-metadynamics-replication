# PLP Parameterization Workflow

> **Reference**: JACS 2019 SI (ja9b03646_si_001.pdf), Section "Ligand / Cofactor Parameterization"
>
> **Project**: TrpB MetaDynamics Replication
>
> **Author**: Zhenpeng Liu (liualex@ad.unc.edu)
>
> **Last Updated**: 2026-03-28

---

## Overview

This document describes how to generate **force field parameters** for the four catalytic intermediates of tryptophan synthase β-subunit (TrpB):

| Intermediate | Full Name | COMM State | Role |
|--|--|--|--|
| **Ain** | Internal aldimine | Open | Resting state: PLP-K82 Schiff base |
| **Aex1** | External aldimine 1 | PC | L-Serine bound; new Schiff base formed |
| **A-A** | Aminoacrylate | Closed | Dehydrated intermediate; awaits indole |
| **Q₂** | Quinonoid 2 | Closed | Indole-amino acid Schiff base (post-coupling) |

## Why Parameterization Matters

TrpB catalyzes the synthesis of L-tryptophan by:

1. **Nucleophilic attack** by indole on the aminoacrylate (A-A)
2. **Electrophilic attack** by serine or indole-glyceraldehyde-3-phosphate on the PLP-K82 Schiff base
3. **Product release** of L-tryptophan

The **pyridoxal phosphate (PLP)** cofactor is central to all steps. PLP is a non-standard residue, so its force field parameters must be generated separately using **QM-based charge fitting** (RESP) rather than relying on standard force field databases.

## Methodology: AMBER GAFF + RESP

The workflow follows **AMBER16 antechamber** (as used in the original JACS 2019 paper):

| Step | Tool | Input | Output | Purpose |
|--|--|--|--|--|
| 1 | Manual extraction | PDB file | PLP structure (PDB) | Isolate cofactor |
| 2 | **antechamber** | PLP PDB | MOL2 (GAFF atoms) | Assign atom types |
| 3 | **Gaussian09** | MOL2 | .log file (QM-optimized) | HF/6-31G(d) geometry + ESP |
| 4 | **antechamber** | Gaussian .log | MOL2 (RESP charges) | Extract RESP charges |
| 5 | **parmchk2** | MOL2 (RESP) | frcmod file | Add missing bond/angle params |
| 6 | **tleap** | protein PDB + frcmod | topology.parm7, coords.inpcrd | Build complete system |

---

## Detailed Workflow

### Step 1: Extract PLP Structures

**Input**: PDB files of TrpB crystal structures containing intermediates

**Output**: Individual PLP residues (PDB format)

#### What the script does:

```bash
grep "^HETATM.*PLP" crystal.pdb > plp.pdb
```

This extracts the **heteroatom** (HETATM) records for PLP.

#### Manual verification:

```bash
# Check that PLP is correctly extracted
cat plp_structures/Ain_plp.pdb

# Should show:
# HETATM 1245  PA  PLP B 401 ...
# HETATM 1246  CB  PLP B 401 ...
# ... (about 30-40 atoms total)
```

---

### Step 2: Antechamber - GAFF Atom Type Assignment

**Input**: PLP structure (PDB)

**Output**: MOL2 file with GAFF atom types

#### Command:

```bash
antechamber -i Ain_plp.pdb -fi pdb -o Ain_gaff.mol2 -fo mol2 \
  -at gaff -c bcc -rn PLP -m 1
```

#### Parameters explained:

| Flag | Value | Meaning |
|--|--|--|
| `-i` | `Ain_plp.pdb` | Input file (PLP structure) |
| `-fi` | `pdb` | Input format = PDB |
| `-o` | `Ain_gaff.mol2` | Output file (MOL2 format) |
| `-fo` | `mol2` | Output format = MOL2 |
| `-at` | `gaff` | Atom type scheme = GAFF (General AMBER FF) |
| `-c` | `bcc` | Charge method = BCC (Bond Charge Correction) — **fast but inaccurate** |
| `-rn` | `PLP` | Residue name |
| `-m` | `1` | Multiplicity (1 = singlet, closed shell) |

#### MOL2 file structure:

```
@<tripos>MOLECULE
PLP
 39 38  0  0  0
SMALL
...

@<tripos>ATOM
      1 PA          23.4560   18.9320   20.1240 P.3     PLP  1       PLP    -0.2400
      2 O1          23.5060   19.0920   21.5420 O.2     PLP  1       PLP    -0.5400
      3 C1          21.2450   19.8760   20.3400 C.ar    PLP  1       PLP    -0.0300
      ... (one line per atom with: atom#, name, x, y, z, GAFF type, charge)

@<tripos>BOND
      1     1     2    1  (bonds between atoms)
```

#### Check output:

```bash
# Verify atom types were assigned
grep "@<tripos>ATOM" Ain_gaff.mol2 -A 40

# Should show GAFF types like: C.ar (aromatic carbon), P.3 (phosphorus), O.2 (oxygen sp2)
```

---

### Step 3: RESP Charge Calculation (Gaussian09)

**Why RESP?** BCC charges (from Step 2) are ~80% accurate. RESP charges fitted to QM electrostatic potential are ~95%+ accurate. This matters for electrostatic interactions with the protein.

#### Sub-step 3a: Generate Gaussian input

The script creates a template for Gaussian09:

```
%chk=PLP_opt.chk
%nprocshared=4
%mem=4GB
# HF/6-31G(d) Opt Pop=ESP

PLP geometry optimization for RESP charge fitting

[CHARGE] [MULTIPLICITY]
[CARTESIAN_COORDINATES]
```

#### Sub-step 3b: Run Gaussian (manual, off-site)

```bash
# On a machine with Gaussian09 installed:
g09 Ain_opt.com
# Output: Ain_opt.log

# Takes ~10-30 minutes depending on PLP size
```

#### Sub-step 3c: Extract RESP charges from Gaussian output

```bash
# Back on Longleaf:
antechamber -i Ain_opt.log -fi gout -o Ain_resp.mol2 -fo mol2 -c resp

# This reads the QM output (.log) and fits RESP charges
```

---

### Step 4: parmchk2 - Generate Missing Parameters

**Input**: MOL2 file with RESP charges

**Output**: frcmod file (contains missing bond, angle, dihedral, nonbond parameters)

#### Command:

```bash
parmchk2 -i Ain_resp.mol2 -f mol2 -o Ain.frcmod
```

#### How it works:

1. **Checks** each bond, angle, dihedral in the molecule against GAFF database
2. **If found**: writes nothing (parameter already in GAFF)
3. **If missing**: writes parameter estimated from similar GAFF terms
4. **Output**: frcmod file with only the missing parameters

#### Example output:

```
Ain_resp.mol2
MOL2
# 1  1  1  0  0
@<tripos>FFTYPE
MISSING_PARAMETERS

Atom Type Definition Section:
{TRUNCATED}

Bond Parameters:
P3-O2   380.00   1.48   (missing bond P-O double bond)
C.ar-C.ar 389.10   1.39  (aromatic C-C)

Angle Parameters:
O2-P3-O2  50.00  109.47  (P-O-O angle)

Dihedral Parameters:
O2-P3-C.ar-C.ar  1.1 180.0 2.0  (P-C torsion)
```

---

### Step 5: tleap - Build Complete System

**Input**:
- Protein structure (PDB)
- PLP parameters (MOL2 + frcmod)

**Output**:
- Topology file (`.parm7`)
- Coordinates file (`.inpcrd`)

#### tleap script:

```tcl
# Load force fields
source leaprc.ff14SB        # AMBER protein FF
source leaprc.gaff          # GAFF (needed for PLP)
source leaprc.water.tip3p   # Water model

# Load ligand parameters
PLP = loadmol2 Ain_resp.mol2
loadamberparams Ain.frcmod

# Load protein structure
Complex = loadpdb structure.pdb

# Solvate with TIP3P (10 Å buffer around protein)
solvateoct Complex TIP3PBOX 10.0

# Neutralize with ions
addions Complex Na+ 0  # Add Na+ to neutralize negative charge
addions Complex Cl- 0  # Add Cl- if needed

# Save topology and coordinates
saveamberparm Complex Ain_complete.parm7 Ain_complete.inpcrd
quit
```

#### Execute tleap:

```bash
tleap -f Ain_build.in > tleap_Ain.log 2>&1
```

---

## Implementation: The Script

### File: `parameterize_plp.sh`

**Location**: `/work/users/l/i/liualex/AnimaLab/replication/scripts/parameterize_plp.sh`

**Execution**:

```bash
# Load AMBER environment on Longleaf
module load amber/24p3

# Run the script
bash replication/scripts/parameterize_plp.sh

# Output directory structure created:
# parameters/
#   ├── plp_structures/      ← Ain_plp.pdb, Aex1_plp.pdb, A-A_plp.pdb, Q2_plp.pdb
#   ├── mol2/                ← *_gaff.mol2 (initial), *_resp.mol2 (after RESP)
#   ├── frcmod/              ← *.frcmod files
#   ├── resp_charges/        ← Gaussian templates
#   ├── tleap_inputs/        ← *_build.in tleap scripts
#   └── logs/                ← antechamber/parmchk2 logs
```

### What the script does:

1. **Section 1**: Sets up directories and paths
2. **Section 2**: Extracts PLP from PDB files (uses grep)
3. **Section 3**: Runs antechamber for each intermediate
4. **Section 4**: Creates Gaussian input templates (manual step needed)
5. **Section 5**: Runs parmchk2 for each intermediate
6. **Section 6**: Generates tleap scripts
7. **Section 7**: Creates batch runner script
8. **Section 8**: Prints summary and next steps

---

## Quick Start

### Option 1: Fully Automated (Fast, less accurate)

If you **skip RESP** and use BCC charges:

```bash
module load amber/24p3

# Run steps 1-2, 5-6 (skip Gaussian)
bash parameterize_plp.sh

# Then run tleap
bash parameters/run_all_tleap.sh
```

**Trade-off**: BCC charges are ~80% as accurate as RESP but 10× faster.

### Option 2: Full RESP Workflow (Recommended, slower)

```bash
# Step 1: Run the script (generates templates)
module load amber/24p3
bash parameterize_plp.sh

# Step 2: Move Gaussian inputs to a machine with Gaussian09
scp parameters/resp_charges/*.com gaussbox:~/

# Step 3: On Gaussian box, optimize geometries
cd ~/
for f in *.com; do g09 $f; done

# Step 4: Copy .log files back
scp gaussbox:~/*.log parameters/resp_charges/

# Step 5: Extract RESP charges on Longleaf
cd parameters/resp_charges
module load amber/24p3
for f in Ain Aex1 A-A Q2; do
  antechamber -i ${f}_opt.log -fi gout -o ../mol2/${f}_resp.mol2 -fo mol2 -c resp
done

# Step 6: Rerun parmchk2 with RESP MOL2s
cd ../frcmod
for f in Ain Aex1 A-A Q2; do
  parmchk2 -i ../mol2/${f}_resp.mol2 -f mol2 -o ${f}_resp.frcmod
done

# Step 7: Run tleap (update scripts to use *_resp.mol2)
cd ../tleap_inputs
bash ../run_all_tleap.sh
```

---

## Troubleshooting

### Error: "antechamber: command not found"

**Solution**: Load AMBER module first
```bash
module load amber/24p3
```

### Error: "No PLP HETATM found"

**Cause**: PDB file doesn't contain a PLP residue record

**Solution**:
1. Verify the PDB has PLP: `grep PLP *.pdb | head -5`
2. Check if it's named differently (e.g., "PLY", "PYD")
3. Update the grep pattern in Step 2 of the script

### Warning: "Missing dihedral X-Y-Z"

**Cause**: GAFF doesn't have a parameter for that atom type combination

**Solution**: parmchk2 automatically extrapolates similar dihedrals. Check the frcmod file for warnings and validate manually if critical.

### Tleap error: "loadamberparams: can't find frcmod"

**Solution**:
1. Verify the .frcmod file exists
2. Use absolute path in tleap script
3. Check that parmchk2 ran successfully (should have created the file)

---

## Force Field References

### GAFF (General AMBER Force Field)

- **Paper**: Wang et al., *J Comput Chem* 2004, **25**, 1157–1174
- **Scope**: Small molecules, organic ligands, cofactors
- **Atom types**: ~40 types (C.ar, C.sp2, P.3, etc.)
- **Parameters**: Bond, angle, dihedral, nonbond; fitted to QM data

### RESP (Restrained Electrostatic Potential)

- **Paper**: Bayly et al., *J Phys Chem* 1993, **97**, 10269–10280
- **Method**: Fit point charges to QM electrostatic potential
- **Accuracy**: ~95% agreement with QM dipoles
- **QM level**: Typically HF/6-31G(d) or B3LYP/6-31G(d)*

### ff14SB (AMBER Protein Force Field)

- **Paper**: Maier et al., *J Chem Theory Comput* 2015, **11**, 3696–3713
- **Scope**: Protein backbone, standard amino acids
- **Improvement over ff99SB**: Better Phi/Psi distributions (from MD validation)

---

## Expected Outputs

After completing the workflow, you should have:

### For each intermediate (Ain, Aex1, A-A, Q2):

| File | Size | Contains |
|--|--|--|
| `plp_structures/*_plp.pdb` | ~2 KB | PLP coordinates (37–40 atoms) |
| `mol2/*_gaff.mol2` | ~3 KB | Atom types, BCC charges |
| `mol2/*_resp.mol2` | ~3 KB | Atom types, **RESP charges** (after Gaussian) |
| `frcmod/*.frcmod` | ~1–5 KB | Missing bond/angle/dihedral parameters |
| `tleap_inputs/*_build.in` | ~1 KB | tleap build script |
| `tleap_inputs/*_complete.parm7` | ~5–10 MB | AMBER topology (protein + PLP) |
| `tleap_inputs/*_complete.inpcrd` | ~500 KB | Initial coordinates (solvated system) |

### Example topology inspection:

```bash
# Check topology contains both protein and PLP
ambpdb -p Ain_complete.parm7 -c Ain_complete.inpcrd > Ain_complete.pdb

# Should show ~14,000 atoms: protein + PLP + water + ions
grep "^ATOM\|^HETATM" Ain_complete.pdb | wc -l
```

---

## Next Steps After Parameterization

Once you have `.parm7` and `.inpcrd` files for each intermediate:

1. **Minimize**: Run 1000 steepest descent steps → 1000 conjugate gradient steps
2. **Heat**: 7 × 50 ps from 0→350 K with restraints
3. **Equilibrate**: 2 ns NPT at 350 K, 1 atm
4. **Production MD**: 500 ns NVT at 350 K (conventional MD)
5. **MetaDynamics**: Transfer to GROMACS + PLUMED for well-tempered MetaD

---

## Files Reference

| File | Purpose |
|--|--|
| `parameterize_plp.sh` | Main automation script |
| `plumed_trpb_metad.dat` | PLUMED input for multi-walker MetaD |
| `plumed_trpb_metad_single.dat` | PLUMED input for single-walker exploration |
| `JACS2019_MetaDynamics_Parameters.md` | Full parameter reference from paper SI |

---

## References

1. **Original JACS paper**: Maria-Solano et al., *JACS* 2019, **141**, 13049–13056 (DOI: 10.1021/jacs.9b03646)
2. **AMBER/antechamber**: Case et al., *AMBER 2024 Reference Manual* (ambermd.org)
3. **GAFF**: Wang et al., *J Comput Chem* 2004, **25**, 1157–1174
4. **RESP**: Bayly et al., *J Phys Chem* 1993, **97**, 10269–10280
5. **Gaussian HF/6-31G(d)**: Frisch et al., *Gaussian 09 Manual*

---

## Contact

For issues with this workflow:

- **Zhenpeng Liu**: liualex@ad.unc.edu
- **Project**: TrpB MetaDynamics Replication (Anima Lab, Caltech)
- **Updated**: 2026-03-28
