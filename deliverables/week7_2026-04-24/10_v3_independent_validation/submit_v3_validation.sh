#!/bin/bash
#SBATCH --job-name=seqaligned_v3_val
#SBATCH --partition=volta-gpu
#SBATCH --qos=gpu_access
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=0-00:30:00
#SBATCH --array=0-9
#SBATCH --output=slurm-%x-%A_%a.out

set -eo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md

export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export LD_LIBRARY_PATH=/work/users/l/i/liualex/plumed-2.9.2/lib:${LD_LIBRARY_PATH:-}
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

WALKER_ID=$(printf "%02d" "${SLURM_ARRAY_TASK_ID}")
BASE=/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_v3_validation
WDIR=${BASE}/walker_${WALKER_ID}
cd "${WDIR}"

echo "=== v3 validation walker_${WALKER_ID} start === $(date)"
echo "host=$(hostname)"
nvidia-smi -L || true

echo "--- stage 1: EM from coordinate-only seed ---"
gmx grompp -f em.mdp -c start.gro -p topol.top -o em.tpr -maxwarn 1
gmx mdrun -deffnm em -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"

echo "--- stage 2: short NVT settle, PLUMED off, gen_vel=yes ---"
gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -maxwarn 1
gmx mdrun -deffnm nvt -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"

echo "--- stage 3: short production MetaD, PLUMED on, continuation from nvt.cpt ---"
grep -E 'UNITS|LAMBDA|ADAPTIVE|HEIGHT|PACE|BIASFACTOR|WALKERS_ID|WALKERS_N|UPPER_WALLS' plumed.dat
gmx grompp -f metad.mdp -c nvt.gro -t nvt.cpt -p topol.top -o metad.tpr -maxwarn 1
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"

grep -E "LINCS WARNING|Segmentation fault|can not be settled" em.log nvt.log metad.log && exit 2 || true
tail -5 COLVAR || true
echo "=== v3 validation walker_${WALKER_ID} done === $(date)"
