#!/bin/bash
# Purpose: launch one materialized Phase 3 probe directory without touching the live array probes.
# Usage on Longleaf: sbatch --export=PROBE_ID=P5 submit_single_probe.sh
#SBATCH --job-name=trpb_probe_1x
#SBATCH --partition=volta-gpu
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --qos=gpu_access
#SBATCH --output=slurm-%x-%j.out

set -eo pipefail

: "${PROBE_ID:?must set PROBE_ID, e.g. sbatch --export=PROBE_ID=P5 submit_single_probe.sh}"

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

PROBE_DIR="${SLURM_SUBMIT_DIR}/probe_${PROBE_ID}"

cp ${SLURM_SUBMIT_DIR}/../single_walker/start.gro ${PROBE_DIR}/start.gro
cp ${SLURM_SUBMIT_DIR}/../single_walker/topol.top ${PROBE_DIR}/topol.top

cd ${PROBE_DIR}

gmx grompp -f metad.mdp -c start.gro -p topol.top -o metad.tpr -maxwarn 2
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp ${OMP_NUM_THREADS}
