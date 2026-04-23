#!/bin/bash
#SBATCH --job-name=miguel_initial
#SBATCH --partition=volta-gpu
#SBATCH --qos=gpu_access
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=1-00:00:00
#SBATCH --output=slurm-%x-%j.out

set -eo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export LD_LIBRARY_PATH=/work/users/l/i/liualex/plumed-2.9.2/lib:${LD_LIBRARY_PATH:-}

cd /work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/initial_single

echo "=== initial_single start === $(date)"
echo "PLUMED_KERNEL=${PLUMED_KERNEL}"
echo "host=$(hostname)  gpu=$(nvidia-smi -L | head -1)"
grep -E 'UNITS|LAMBDA|ADAPTIVE|HEIGHT|BIASFACTOR|SIGMA' plumed.dat

gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS}

echo "=== initial_single done === $(date)"
ls -lh HILLS COLVAR metad.log 2>/dev/null || true
wc -l COLVAR HILLS 2>/dev/null || true
