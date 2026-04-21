#!/bin/bash
# Purpose: SLURM array submission for the 4-probe SIGMA_MIN/MAX sweep (P1..P4).
#SBATCH --job-name=trpb_probe
#SBATCH --partition=volta-gpu
#SBATCH --array=1-4
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=15:00:00
#SBATCH --qos=gpu_access
#SBATCH --output=slurm-%x-%A_%a.out

set -eo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

PROBE_ID=P${SLURM_ARRAY_TASK_ID}
PROBE_DIR="${SLURM_SUBMIT_DIR}/probe_${PROBE_ID}"

cp ${SLURM_SUBMIT_DIR}/../single_walker/start.gro ${PROBE_DIR}/start.gro
cp ${SLURM_SUBMIT_DIR}/../single_walker/topol.top ${PROBE_DIR}/topol.top

cd ${PROBE_DIR}

gmx grompp -f metad.mdp -c start.gro -p topol.top -o metad.tpr -maxwarn 2
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS}
