#!/bin/bash
#SBATCH --job-name=trpb_metad
#SBATCH --partition=general
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=72:00:00
#SBATCH --output=slurm-%x-%j.out

set -eo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

cd $SLURM_SUBMIT_DIR

echo "=== Environment ==="
echo "PLUMED_KERNEL: $PLUMED_KERNEL"
echo "OMP_NUM_THREADS: $OMP_NUM_THREADS"
echo "LAMBDA: 3.3910 nm^-2 (= 0.033910 A^-2 x 100)"

gmx grompp -f metad.mdp -c start.gro -p topol.top -o metad.tpr -maxwarn 2
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS}

echo "=== Done ==="
ls -lh COLVAR HILLS metad.log
wc -l COLVAR HILLS
head -5 COLVAR
tail -5 COLVAR
