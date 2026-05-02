#!/bin/bash
#SBATCH --job-name=tier1p5_3w
#SBATCH --partition=volta-gpu
#SBATCH --qos=gpu_access
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=16G
#SBATCH --time=0-10:00:00
#SBATCH --array=0-2
#SBATCH --output=slurm-%x-%A_%a.out

set -euo pipefail

module purge
module load anaconda/2024.02
eval "$(conda shell.bash hook)"
conda activate trpb-md

export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
export LD_LIBRARY_PATH=/work/users/l/i/liualex/plumed-2.9.2/lib:${LD_LIBRARY_PATH:-}
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

ACTIVE_WALKERS=3
BASE=/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_tier1p5
HILLS_DIR="${BASE}/HILLS_DIR_tier1p5"
JOB_KEY="${SLURM_ARRAY_JOB_ID:-${SLURM_JOB_ID:-manual}}"
HILLS_OWNER="${HILLS_DIR}/.owner_${JOB_KEY}"

if mkdir "${HILLS_DIR}" 2>/dev/null; then
  echo "created_by_job=${JOB_KEY}" > "${HILLS_OWNER}"
else
  for _ in $(seq 1 30); do
    [[ -f "${HILLS_OWNER}" ]] && break
    sleep 1
  done
  if [[ ! -f "${HILLS_OWNER}" ]]; then
    echo "ERROR: ${HILLS_DIR} already exists and is not owned by this array job." >&2
    echo "Archive/remove it only after PM approval; refusing silent overwrite." >&2
    exit 20
  fi
fi

WALKER_ID=$(printf "%02d" "${SLURM_ARRAY_TASK_ID}")
WDIR="${BASE}/walker_${WALKER_ID}"
cd "${WDIR}"

echo "=== Tier 1.5 walker_${WALKER_ID} start === $(date)"
echo "active_walkers=${ACTIVE_WALKERS}"
echo "base=${BASE}"
echo "hills_dir=${HILLS_DIR}"
echo "host=$(hostname)"
nvidia-smi -L || true

materialize_plumed() {
  local src="$1"
  local out="${src%.dat}_${ACTIVE_WALKERS}w_active.dat"
  sed "s/WALKERS_N=10/WALKERS_N=${ACTIVE_WALKERS}/" "${src}" > "${out}"
  echo "${out}"
}

run_grompp_mdrun() {
  local label="$1"
  local mdp="$2"
  local coord="$3"
  local checkpoint="$4"
  local plumed="$5"
  echo "--- ${label} ---"
  grep -E '^(; Tier|;   SI-literal|;   Tier|; Numeric check|dt|nsteps|lincs_iter|continuation|gen_vel)' "${mdp}" || true
  grep -E 'HEIGHT=|BIASFACTOR=|LAMBDA=|GRID_MAX=|WALKERS_DIR=|WALKERS_N=' "${plumed}" || true
  gmx grompp -f "${mdp}" -c "${coord}" -t "${checkpoint}" -p topol.top -o "${label}.tpr" -maxwarn 1
  gmx mdrun -deffnm "${label}" -plumed "${plumed}" -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"
}

echo "--- EM from coordinate-only seed ---"
gmx grompp -f em.mdp -c start.gro -p topol.top -o em.tpr -maxwarn 1
gmx mdrun -deffnm em -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"

echo "--- 1 ns NVT, PLUMED off, gen_vel=yes ---"
grep -E '^(; Tier|;   SI-literal|;   Tier|; Numeric check|dt|nsteps|lincs_iter|continuation|gen_vel|gen_temp)' nvt.mdp || true
gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -maxwarn 1
gmx mdrun -deffnm nvt -ntmpi 1 -ntomp "${OMP_NUM_THREADS}"

p1=$(materialize_plumed plumed_stage1.dat)
p2=$(materialize_plumed plumed_stage2.dat)
p3=$(materialize_plumed plumed_stage3.dat)
p4=$(materialize_plumed plumed_stage4.dat)
p5=$(materialize_plumed plumed_stage5.dat)
pp=$(materialize_plumed plumed_prod.dat)

run_grompp_mdrun metad_stage1 metad_stage1.mdp nvt.gro nvt.cpt "${p1}"
run_grompp_mdrun metad_stage2 metad_stage2.mdp metad_stage1.gro metad_stage1.cpt "${p2}"
run_grompp_mdrun metad_stage3 metad_stage3.mdp metad_stage2.gro metad_stage2.cpt "${p3}"
run_grompp_mdrun metad_stage4 metad_stage4.mdp metad_stage3.gro metad_stage3.cpt "${p4}"
run_grompp_mdrun metad_stage5 metad_stage5.mdp metad_stage4.gro metad_stage4.cpt "${p5}"
run_grompp_mdrun metad_prod metad_prod.mdp metad_stage5.gro metad_stage5.cpt "${pp}"

grep -E "LINCS WARNING|Segmentation fault|can not be settled" em.log nvt.log metad_stage*.log metad_prod.log && exit 2 || true
tail -5 COLVAR || true
echo "=== Tier 1.5 walker_${WALKER_ID} done === $(date)"
