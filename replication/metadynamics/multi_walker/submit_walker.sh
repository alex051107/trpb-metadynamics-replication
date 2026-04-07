#!/bin/bash
#SBATCH --job-name=metad_wX
#SBATCH --partition=general
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=72:00:00
#SBATCH --output=slurm-%x-%j.out

# Single walker instance for multi-walker MetaDynamics
# JACS 2019: 10 walkers x 50 ns = 500 ns total
# WALKERS_DIR=../ lets each walker read HILLS from sibling directories

set -eo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

cd $SLURM_SUBMIT_DIR

echo "=== Walker: $(basename $PWD) ==="
echo "PLUMED_KERNEL: $PLUMED_KERNEL"
echo "OMP_NUM_THREADS: $OMP_NUM_THREADS"
echo "Working dir: $PWD"

# grompp
gmx grompp -f metad.mdp -c start.gro -p topol.top -o metad.tpr -maxwarn 2

# mdrun with PLUMED
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS}

echo "=== Walker $(basename $PWD) Done ==="
ls -lh COLVAR HILLS metad.log 2>/dev/null
wc -l COLVAR HILLS 2>/dev/null
