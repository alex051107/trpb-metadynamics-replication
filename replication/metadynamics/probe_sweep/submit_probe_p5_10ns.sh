#!/bin/bash
# Purpose: launch the fresh 10 ns P5 diagnostic without touching the completed P1-P4 probe directories.
# Usage on Longleaf: run from probe_sweep/ root with `sbatch submit_probe_p5_10ns.sh`

#SBATCH --job-name=trpb_probe_P5
#SBATCH --partition=volta-gpu
#SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=15:00:00
#SBATCH --qos=gpu_access
#SBATCH --output=slurm-%x-%j.out

set -eo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

PROBE_ID=P5
PROBE_DIR="${SLURM_SUBMIT_DIR}/probe_${PROBE_ID}"

for f in "${PROBE_DIR}/metad.mdp" "${PROBE_DIR}/plumed.dat" "${PROBE_DIR}/path_gromacs.pdb"; do
  if [[ ! -s "${f}" ]]; then
    echo "FATAL: missing probe input ${f}"
    exit 1
  fi
done

cp "${SLURM_SUBMIT_DIR}/../single_walker/start.gro" "${PROBE_DIR}/start.gro"
cp "${SLURM_SUBMIT_DIR}/../single_walker/topol.top" "${PROBE_DIR}/topol.top"

cd "${PROBE_DIR}"

gmx grompp -f metad.mdp -c start.gro -p topol.top -o metad.tpr -maxwarn 2
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"
