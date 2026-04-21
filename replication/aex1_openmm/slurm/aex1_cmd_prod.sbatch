#!/bin/bash
#SBATCH --job-name=aex1_openmm
#SBATCH --partition=a100-gpu
#SBATCH --qos=gpu_access
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=72:00:00
#SBATCH --output=/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm/logs/%x_%j.out
#SBATCH --error=/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm/logs/%x_%j.err

set -eo pipefail

REMOTE_ROOT="${REMOTE_ROOT:-/work/users/l/i/liualex/AnimaLab/classical_md/aex1_openmm}"
SCRIPT_DIR="${SCRIPT_DIR:-${REMOTE_ROOT}/scripts}"
BUILD_DIR="${BUILD_DIR:-${REMOTE_ROOT}/build}"
RUN_DIR="${RUN_DIR:-${REMOTE_ROOT}/prod}"
SOURCE_PDB="${SOURCE_PDB:-${REMOTE_ROOT}/inputs/5DW0.pdb}"
BUILD_SCRIPT="${BUILD_SCRIPT:-${SCRIPT_DIR}/build_aex1_system.py}"
RUN_SCRIPT="${RUN_SCRIPT:-${SCRIPT_DIR}/run_aex1_cmd.py}"
ENV_PREFIX="${ENV_PREFIX:-/work/users/l/i/liualex/conda/envs/md_setup_trpb}"
MODE="${MODE:-production}"
PROD_NS="${PROD_NS:-500}"
NVT_NS="${NVT_NS:-0.5}"
NPT_NS="${NPT_NS:-0.5}"
REPORT_PS="${REPORT_PS:-100}"
STATE_PS="${STATE_PS:-1000}"

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "ERROR: $*"
  exit 1
}

require_nonempty_file() {
  local path="$1"
  [[ -s "$path" ]] || fail "Required file missing or empty: $path"
}

probe_cuda() {
  log "CUDA probe start"
  python - <<'PY'
from openmm import Context, Platform, System, VerletIntegrator
from openmm import unit

system = System()
system.addParticle(39.948)
integrator = VerletIntegrator(0.001 * unit.picoseconds)
platform = Platform.getPlatformByName("CUDA")
props = {"Precision": "mixed"}
context = Context(system, integrator, platform, props)
print("CUDA_PLATFORM_OK")
print("cuda_platform", context.getPlatform().getName())
print("cuda_device_index", platform.getPropertyValue(context, "DeviceIndex"))
print("cuda_precision", platform.getPropertyValue(context, "Precision"))
PY
}

main() {
  mkdir -p "${REMOTE_ROOT}" "${REMOTE_ROOT}/logs" "${REMOTE_ROOT}/inputs" "${SCRIPT_DIR}" "${BUILD_DIR}" "${RUN_DIR}"

  module purge
  source /nas/longleaf/rhel9/apps/anaconda/2024.02/etc/profile.d/conda.sh
  conda activate "${ENV_PREFIX}"

  export PATH="${ENV_PREFIX}/bin:${PATH}"
  export OPENMM_PLATFORM=CUDA
  export OPENMM_PRECISION=mixed

  log "MODE=${MODE}"
  log "REMOTE_ROOT=${REMOTE_ROOT}"
  log "BUILD_DIR=${BUILD_DIR}"
  log "RUN_DIR=${RUN_DIR}"
  log "SOURCE_PDB=${SOURCE_PDB}"
  log "ENV_PREFIX=${ENV_PREFIX}"
  nvidia-smi --query-gpu=name,driver_version --format=csv,noheader || true
  python -c "import openmm; print('openmm', openmm.__version__)"
  python -c "from openmmplumed import PlumedForce; print('openmm-plumed OK')"

  require_nonempty_file "${BUILD_SCRIPT}"
  require_nonempty_file "${RUN_SCRIPT}"
  require_nonempty_file "${SOURCE_PDB}"

  probe_cuda || fail "CUDA still blocked (FP-028)"

  python "${BUILD_SCRIPT}" \
    --source-pdb "${SOURCE_PDB}" \
    --outdir "${BUILD_DIR}" \
    --pdbfixer-platform Reference \
    --minimization-platform CUDA \
    --cuda-precision mixed

  require_nonempty_file "${BUILD_DIR}/aex1_system.xml"
  require_nonempty_file "${BUILD_DIR}/aex1_initial.pdb"

  python "${RUN_SCRIPT}" \
    --system-xml "${BUILD_DIR}/aex1_system.xml" \
    --initial-pdb "${BUILD_DIR}/aex1_initial.pdb" \
    --workdir "${RUN_DIR}" \
    --platform CUDA \
    --precision mixed \
    --nvt-ns "${NVT_NS}" \
    --npt-ns "${NPT_NS}" \
    --prod-ns "${PROD_NS}" \
    --report-ps "${REPORT_PS}" \
    --state-ps "${STATE_PS}"

  require_nonempty_file "${RUN_DIR}/run_summary.json"
  log "AEX1_CMD_BATCH_OK"
}

main "$@"
