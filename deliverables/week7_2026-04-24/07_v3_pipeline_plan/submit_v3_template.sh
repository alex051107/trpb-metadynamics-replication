#!/bin/bash
# -----------------------------------------------------------------------------
# v3 10-walker MetaD production — EM + NVT + production pipeline
# -----------------------------------------------------------------------------
# Closes v2 failure modes (LINCS blow-up, missing velocities, biased-seed strain)
# by inserting local relaxation stages before production MetaD.  Codex-verified
# diagnosis in ../06_v2_10walker_crashed/codex_root_cause.md.
#
# TEMPLATE ONLY — awaiting PI sign-off before submission.
# -----------------------------------------------------------------------------
#SBATCH --job-name=seqaligned_v3
#SBATCH --partition=volta-gpu
#SBATCH --qos=gpu_access
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=0-12:00:00
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
WDIR=/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_v3/walker_${WALKER_ID}
cd "${WDIR}"

echo "=== walker_${WALKER_ID} (v3 EM+NVT+production) start === $(date)"
echo "host=$(hostname)  gpu=$(nvidia-smi -L | head -1)"

# -----------------------------------------------------------------------------
# STAGE 1 — energy minimization
#   Eliminates bad contacts carried from the biased-pilot seed geometry.
#   emtol = 1000 kJ/mol/nm is standard for solvated protein systems.
# -----------------------------------------------------------------------------
echo "--- stage 1: EM ---"
gmx grompp -f em.mdp   -c start.gro -p topol.top -o em.tpr   -maxwarn 1
gmx mdrun  -deffnm em  -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"

# -----------------------------------------------------------------------------
# STAGE 2 — NVT settle (PLUMED OFF, velocities regenerated)
#   100 ps at 350 K with gen_vel = yes gives a proper Maxwell-Boltzmann
#   distribution on the relaxed geometry.  PLUMED off because we are not
#   sampling — we are settling.  LINCS must be stable by the end of this stage.
# -----------------------------------------------------------------------------
echo "--- stage 2: NVT settle (PLUMED off, 100 ps, gen_vel=yes) ---"
gmx grompp -f nvt.mdp  -c em.gro -r em.gro -p topol.top -o nvt.tpr -maxwarn 1
gmx mdrun  -deffnm nvt -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"

# -----------------------------------------------------------------------------
# STAGE 3 — production MetaD (PLUMED ON, continue from NVT checkpoint)
#   Miguel primary contract: HEIGHT=0.15, BIASFACTOR=10, PACE=500, WALKERS_N=10,
#   ADAPTIVE=DIFF, UNITS=A/kcal, UPPER_WALLS path.zzz AT=2.5.
#   gen_vel = no because we continue from nvt.cpt (preserves equilibrated
#   velocities).
# -----------------------------------------------------------------------------
echo "--- stage 3: production MetaD (PLUMED on, Miguel primary) ---"
grep -E 'LAMBDA|HEIGHT|BIASFACTOR|WALKERS_ID|UNITS|ADAPTIVE' plumed.dat
gmx grompp -f metad.mdp -c nvt.gro -t nvt.cpt -p topol.top -o metad.tpr -maxwarn 1
gmx mdrun  -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"

echo "=== walker_${WALKER_ID} done === $(date)"
