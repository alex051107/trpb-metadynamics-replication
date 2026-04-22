#!/bin/bash
# Purpose: extend probe_P3 from 10 ns to 30 ns total without changing any locked MetaD factors.
# Usage on Longleaf: copy into probe_P3/ and run `sbatch submit_p3_extend_30ns.sh`
# Safety protocol follows FP-026: convert-tpr -extend + explicit PLUMED RESTART + append checks.

#SBATCH --job-name=trpb_probe_p3x
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

cd "${SLURM_SUBMIT_DIR}"

for f in metad.cpt metad.tpr HILLS COLVAR plumed.dat; do
  if [[ ! -s "$f" ]]; then
    echo "FATAL: required restart file missing: $f"
    exit 1
  fi
done

python3 - <<'PY'
from pathlib import Path

src = Path("plumed.dat").read_text().splitlines()
dst = ["RESTART", ""] + src
Path("plumed_restart.dat").write_text("\n".join(dst) + "\n")
PY

python3 - <<'PY'
from pathlib import Path

def normalize(path):
    lines = []
    for raw in Path(path).read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line == "RESTART":
            continue
        lines.append(line)
    return lines

if normalize("plumed.dat") != normalize("plumed_restart.dat"):
    raise SystemExit("FATAL: plumed_restart.dat differs from plumed.dat by more than RESTART")
PY

PRE_HILLS_ROWS=$(wc -l < HILLS)
PRE_COLVAR_ROWS=$(wc -l < COLVAR)
PRE_HILLS_FIRST=$(grep -v '^#' HILLS | head -1)
PRE_COLVAR_FIRST=$(grep -v '^#' COLVAR | head -1)

gmx convert-tpr -s metad.tpr -extend 20000 -o metad_30ns.tpr

gmx mdrun \
  -s metad_30ns.tpr \
  -cpi metad.cpt \
  -deffnm metad \
  -plumed plumed_restart.dat \
  -ntmpi 1 \
  -ntomp "${OMP_NUM_THREADS}"

POST_HILLS_ROWS=$(wc -l < HILLS)
POST_COLVAR_ROWS=$(wc -l < COLVAR)
POST_HILLS_FIRST=$(grep -v '^#' HILLS | head -1)
POST_COLVAR_FIRST=$(grep -v '^#' COLVAR | head -1)

if [[ ${POST_HILLS_ROWS} -le ${PRE_HILLS_ROWS} ]]; then
  echo "FATAL: HILLS did not grow"
  exit 11
fi
if [[ ${POST_COLVAR_ROWS} -le ${PRE_COLVAR_ROWS} ]]; then
  echo "FATAL: COLVAR did not grow"
  exit 12
fi
if ls bck.*.HILLS 1>/dev/null 2>&1; then
  echo "FATAL: bck.*.HILLS detected"
  exit 13
fi
if ls bck.*.COLVAR 1>/dev/null 2>&1; then
  echo "FATAL: bck.*.COLVAR detected"
  exit 14
fi
if [[ "${PRE_HILLS_FIRST}" != "${POST_HILLS_FIRST}" ]]; then
  echo "FATAL: HILLS first data row changed"
  exit 15
fi
if [[ "${PRE_COLVAR_FIRST}" != "${POST_COLVAR_FIRST}" ]]; then
  echo "FATAL: COLVAR first data row changed"
  exit 16
fi

echo "P3 extension completed cleanly"
echo "HILLS rows: ${PRE_HILLS_ROWS} -> ${POST_HILLS_ROWS}"
echo "COLVAR rows: ${PRE_COLVAR_ROWS} -> ${POST_COLVAR_ROWS}"
