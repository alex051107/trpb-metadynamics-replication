#!/bin/bash

# Setup alanine dipeptide system for MetaDynamics toy test
# Workflow: pdb2gmx → solvate → ions → minimize → heat → equilibrate
# Environment: conda activate trpb-md (GROMACS 2026.0, PLUMED 2.9)

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

CONDA_ENV="trpb-md"
FF="amber99sb-ildn"          # AMBER ff14SB equivalent in GROMACS
WATER="tip3p"
OUTDIR="."                    # Current directory

echo "=========================================="
echo "Alanine Dipeptide System Setup"
echo "=========================================="
echo "Output directory: $OUTDIR"
echo "Force field: $FF"
echo "Water model: $WATER"
echo ""

# ============================================================================
# Activate conda environment
# ============================================================================

echo "[1/7] Activating conda environment..."
source /opt/conda/etc/profile.d/conda.sh || source ~/anaconda3/etc/profile.d/conda.sh
conda activate "$CONDA_ENV"
echo "✓ Environment activated: $(which gmx)"
echo "  GROMACS: $(gmx --version | head -1)"
echo "  PLUMED: $(plumed --version 2>&1 | head -1)"
echo ""

# ============================================================================
# Step 1: Create alanine dipeptide PDB
# ============================================================================

echo "[2/7] Creating alanine dipeptide (Ace-Ala-Nme) topology..."

# Use GROMACS to generate the topology directly from sequence.
# First, create a simple PDB with a linear tripeptide (Ace-Ala-Nme).
# We'll use pdb2gmx with the -nocharmm flag to skip capping via CHARMM script.
# Instead, we manually create a minimal PDB:

cat > alaninedip.pdb << 'EOF'
REMARK   Acetyl-Alanine-N-methyl (alanine dipeptide)
REMARK   Capped N and C termini for stable simulation
ATOM      1  N   ACE     1      -0.679   1.418   2.614  1.00  0.00           N
ATOM      2  CA  ACE     1       0.000   2.109   1.741  1.00  0.00           C
ATOM      3  C   ACE     1       1.338   1.518   1.386  1.00  0.00           C
ATOM      4  O   ACE     1       2.139   1.191   2.250  1.00  0.00           O
ATOM      5  N   ALA     2       1.668   1.296   0.148  1.00  0.00           N
ATOM      6  CA  ALA     2       2.943   0.739  -0.238  1.00  0.00           C
ATOM      7  C   ALA     2       3.691   0.206   0.980  1.00  0.00           C
ATOM      8  O   ALA     2       4.882   0.455   1.176  1.00  0.00           O
ATOM      9  CB  ALA     2       3.767   1.846  -0.921  1.00  0.00           C
ATOM     10  N   NME     3       2.993  -0.548   1.854  1.00  0.00           N
ATOM     11  C   NME     3       3.615  -1.093   3.069  1.00  0.00           C
END
EOF

echo "✓ Created alaninedip.pdb"
echo ""

# ============================================================================
# Step 2: Run pdb2gmx
# ============================================================================

echo "[3/7] Running pdb2gmx (topology generation)..."
gmx pdb2gmx -f alaninedip.pdb \
            -o alaninedip_processed.gro \
            -p topol.top \
            -ff "$FF" \
            -water "$WATER" \
            -his \
            -ignh \
            << 'PDBINPUT'

PDBINPUT

echo "✓ Generated: alaninedip_processed.gro, topol.top"
echo ""

# ============================================================================
# Step 3: Create simulation box and solvate
# ============================================================================

echo "[4/7] Creating box and solvating..."
gmx editconf -f alaninedip_processed.gro \
             -o alaninedip_box.gro \
             -c -d 0.8 -bt cubic

gmx solvate -cp alaninedip_box.gro \
            -cs spc216.gro \
            -o alaninedip_solvated.gro \
            -p topol.top

echo "✓ Generated: alaninedip_solvated.gro"
echo ""

# ============================================================================
# Step 4: Add ions for neutralization
# ============================================================================

echo "[5/7] Preparing for ion addition (genion)..."

# Create minimal .mdp for preprocessing
cat > ions.mdp << 'EOF'
integrator = steep
nsteps     = 0
cutoff-scheme = verlet
coulombtype = pme
rcoulomb    = 0.9
rvdw        = 0.9
rlist       = 0.9
pbc         = xyz
EOF

gmx grompp -f ions.mdp \
           -c alaninedip_solvated.gro \
           -p topol.top \
           -o ions.tpr

# Add Cl- to neutralize (alanine dipeptide has +1 charge from ACE cap)
echo "13" | gmx genion -s ions.tpr \
                       -o alaninedip_ions.gro \
                       -p topol.top \
                       -pname NA \
                       -nname CL \
                       -neutral

echo "✓ Generated: alaninedip_ions.gro (neutralized)"
echo ""

# ============================================================================
# Step 5: Energy Minimization
# ============================================================================

echo "[6/7] Energy minimization (steepest descent)..."

cat > minim.mdp << 'EOF'
; Minimization input file
integrator      = steep         ; Steepest descent
nsteps          = 1000          ; Max 1000 steps
emstep          = 0.01          ; Initial step size (nm)
emtol           = 100.0         ; Tolerance (kJ/mol/nm)
emtol-init      = NaN

; System definition
cutoff-scheme   = verlet
coulombtype     = pme
rcoulomb        = 0.9
rvdw            = 0.9
rlist           = 0.9
pbc             = xyz

; Dispersion correction
DispCorr        = EnerPres

; Output
nstlog          = 10
nstenergy       = 10
nstxout         = 100
EOF

gmx grompp -f minim.mdp \
           -c alaninedip_ions.gro \
           -p topol.top \
           -o minim.tpr \
           -maxwarn 1

gmx mdrun -v -deffnm minim -nt 4

echo "✓ Minimization complete: minim.gro"
echo ""

# ============================================================================
# Step 6: NVT Heating (10 K → 300 K, 100 ps)
# ============================================================================

echo "[7/7] NVT heating phase (10 → 300 K, 100 ps)..."

cat > heat_nvt.mdp << 'EOF'
; NVT heating (constant volume)
integrator      = md
nsteps          = 50000         ; 100 ps (dt=0.002)
dt              = 0.002         ; 2 fs timestep

; Output
nstxout         = 100           ; Write trajectory every 0.2 ps
nstlog          = 100
nstenergy       = 100
nstvout         = 100

; Cutoffs
cutoff-scheme   = verlet
coulombtype     = pme
rcoulomb        = 0.9
rvdw            = 0.9
rlist           = 0.9
pbc             = xyz

; Thermostat (NVT)
tcoupl          = v-rescale
tau_t           = 0.1
tc-grps         = System
ref_t           = 300           ; Target temperature
gen_vel         = yes           ; Generate velocities
gen_temp        = 10            ; Initial temperature (K)
gen_seed        = -1

; Pressure (none - NVT ensemble)
pcoupl          = no

; Constraints
constraints     = h-bonds
constraint_algorithm = lincs
EOF

gmx grompp -f heat_nvt.mdp \
           -c minim.gro \
           -p topol.top \
           -o heat_nvt.tpr \
           -maxwarn 1

gmx mdrun -v -deffnm heat_nvt -nt 4

echo "✓ Heating complete: heat_nvt.gro"
echo ""

# ============================================================================
# Step 7: NPT Equilibration (300 K, 100 ps)
# ============================================================================

echo "[8/8] NPT equilibration phase (300 K, 100 ps)..."

cat > equil_npt.mdp << 'EOF'
; NPT equilibration (constant pressure)
integrator      = md
nsteps          = 50000         ; 100 ps
dt              = 0.002

; Output
nstxout         = 100
nstlog          = 100
nstenergy       = 100
nstvout         = 100

; Cutoffs
cutoff-scheme   = verlet
coulombtype     = pme
rcoulomb        = 0.9
rvdw            = 0.9
rlist           = 0.9
pbc             = xyz

; Thermostat (NVT stage first, then NPT)
tcoupl          = v-rescale
tau_t           = 0.1
tc-grps         = System
ref_t           = 300

; Barostat (NPT)
pcoupl          = Berendsen      ; Weak coupling for equilibration
pcoupltype      = isotropic
tau_p           = 5.0
ref_p           = 1.0
compressibility = 4.5e-5

; Constraints
constraints     = h-bonds
constraint_algorithm = lincs

; Dispersion correction
DispCorr        = EnerPres
EOF

gmx grompp -f equil_npt.mdp \
           -c heat_nvt.gro \
           -t heat_nvt.cpt \
           -p topol.top \
           -o equil_npt.tpr \
           -maxwarn 1

gmx mdrun -v -deffnm equil_npt -nt 4

echo "✓ Equilibration complete: equil_npt.gro"
echo ""

# ============================================================================
# Cleanup and final summary
# ============================================================================

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Final structure: equil_npt.gro"
echo "Topology: topol.top"
echo ""
echo "Next step: Run MetaDynamics production"
echo "  sbatch submit_metad.slurm"
echo ""
