#!/bin/bash

# SLURM batch script for alanine dipeptide MetaDynamics production run
# HPC: UNC Longleaf
# Queue: general (CPU), 4 cores, 1 hour walltime

#SBATCH --job-name=ala-dipeptide-metad
#SBATCH --partition=general
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --mail-type=END,FAIL
#SBATCH --mail-user=liualex@ad.unc.edu
#SBATCH --output=metad_%j.log
#SBATCH --error=metad_%j.err

# ============================================================================
# Alanine Dipeptide MetaDynamics Production Run
# ============================================================================

echo "=========================================="
echo "Job: Alanine Dipeptide MetaDynamics"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "=========================================="
echo ""

# ============================================================================
# Load environment
# ============================================================================

echo "[$(date)] Loading conda environment..."
module load conda >/dev/null 2>&1 || true
source /opt/conda/etc/profile.d/conda.sh || source ~/anaconda3/etc/profile.d/conda.sh

# Activate the trpb-md environment (contains GROMACS 2026.0 + PLUMED 2.9)
conda activate trpb-md

# Verify installations
echo "GROMACS version: $(gmx --version 2>&1 | head -1)"
echo "PLUMED version: $(plumed --version 2>&1 | head -1)"
echo ""

# ============================================================================
# Check required input files
# ============================================================================

echo "[$(date)] Checking input files..."

required_files=("equil_npt.gro" "topol.top" "run_metad.mdp" "plumed_metad.dat")
missing_files=0

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        echo "  ERROR: Missing file: $file"
        missing_files=1
    else
        echo "  ✓ $file"
    fi
done

if [[ $missing_files -eq 1 ]]; then
    echo ""
    echo "ERROR: One or more required files missing. Exiting."
    exit 1
fi

echo "✓ All input files present"
echo ""

# ============================================================================
# Preprocessing (gmx grompp)
# ============================================================================

echo "[$(date)] Preprocessing: gmx grompp..."

gmx grompp -f run_metad.mdp \
           -c equil_npt.gro \
           -t equil_npt.cpt \
           -p topol.top \
           -o metad.tpr \
           -maxwarn 1 \
           > grompp.log 2>&1

if [[ $? -ne 0 ]]; then
    echo "ERROR: grompp failed. Check grompp.log"
    cat grompp.log
    exit 1
fi

echo "✓ Preprocessing complete (metad.tpr)"
echo ""

# ============================================================================
# Production Run (gmx mdrun with PLUMED)
# ============================================================================

echo "[$(date)] Starting MetaDynamics production run..."
echo "  - System: Alanine dipeptide"
echo "  - CVs: phi, psi dihedral angles"
echo "  - Ensemble: NVT, 300 K"
echo "  - Simulation time: 10 ns"
echo "  - CPUs: $SLURM_CPUS_PER_TASK"
echo ""

# Run GROMACS with PLUMED interface
# -deffnm metad: Use 'metad' as prefix for all output files
# -plumed plumed_metad.dat: Load PLUMED input file
# -ntmpi 1: Single MPI rank (not using distributed memory)
# -ntomp $SLURM_CPUS_PER_TASK: Use all allocated CPU cores
# -v: Verbose output

gmx mdrun -deffnm metad \
          -plumed plumed_metad.dat \
          -ntmpi 1 \
          -ntomp $SLURM_CPUS_PER_TASK \
          -v \
          > mdrun.log 2>&1

mdrun_exit_code=$?

if [[ $mdrun_exit_code -ne 0 ]]; then
    echo "ERROR: mdrun exited with code $mdrun_exit_code"
    echo "Last 50 lines of mdrun.log:"
    tail -50 mdrun.log
    exit $mdrun_exit_code
fi

echo ""
echo "=========================================="
echo "[$(date)] MetaDynamics run completed!"
echo "=========================================="
echo ""

# ============================================================================
# Check output files
# ============================================================================

echo "Output files generated:"
ls -lh metad.* COLVAR HILLS 2>/dev/null | awk '{print "  " $9 " (" $5 ")"}'
echo ""

# ============================================================================
# Quick summary
# ============================================================================

echo "Summary:"
echo "  Trajectory: metad.trr (positions + velocities)"
echo "  Energy: metad.edr (thermodynamic data)"
echo "  CV evolution: COLVAR (phi, psi, bias vs time)"
echo "  Gaussian hills: HILLS (raw MetaD parameters)"
echo ""
echo "Next step: Run 'python3 analyze_fes.py' to generate FEL plot"
echo ""

# ============================================================================
# Cleanup (optional)
# ============================================================================

# Uncomment to save space (keep only essentials for analysis):
# rm -f metad.trr  # Large trajectory file (keep .xtc instead)
# rm -f mdrun.log grompp.log

echo "[$(date)] Job complete."
