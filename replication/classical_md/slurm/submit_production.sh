#!/bin/bash
#SBATCH --job-name=pftrps_ain_prod
#SBATCH --partition=gpu
#SBATCH --qos=gpu_access
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=72:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

WORKDIR="${WORKDIR:-/work/users/l/i/liualex/AnimaLab/replication/runs/pftrps_ain_md}"
TOPOLOGY_REL="${TOPOLOGY_REL:-../../systems/pftrps_ain/pftrps_ain.parm7}"
PROD_MDIN_REL="${PROD_MDIN_REL:-../../scripts/amber_md/prod.in}"
INPUT_RESTART_REL="${INPUT_RESTART_REL:-equil.rst7}"
OUTPUT_PREFIX="${OUTPUT_PREFIX:-prod_500ns}"
PMEMD_BIN="${PMEMD_BIN:-pmemd.cuda}"

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

assert_file_contains_literal() {
  local path="$1"
  local literal="$2"
  grep -Fq "$literal" "$path" || fail "Expected literal not found in $path: $literal"
}

main() {
  module purge
  module load amber/24p3
  export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"

  mkdir -p "$WORKDIR"
  cd "$WORKDIR"

  require_nonempty_file "$TOPOLOGY_REL"
  require_nonempty_file "$PROD_MDIN_REL"
  require_nonempty_file "$INPUT_RESTART_REL"

  assert_file_contains_literal "$PROD_MDIN_REL" "nstlim=250000000"
  assert_file_contains_literal "$PROD_MDIN_REL" "dt=0.002"
  assert_file_contains_literal "$PROD_MDIN_REL" "temp0=350.0"
  assert_file_contains_literal "$PROD_MDIN_REL" "cut=8.0"
  assert_file_contains_literal "$PROD_MDIN_REL" "ntwx=5000"
  assert_file_contains_literal "$PROD_MDIN_REL" "ntwe=500"
  assert_file_contains_literal "$PROD_MDIN_REL" "ntwr=500000"

  log "UNVERIFIED: The SI specifies a total 500 ns NVT production template but does not specify a 72 h walltime chunk size. This launcher runs the exact 500 ns mdin and expects human-controlled resubmission from the latest restart if Longleaf walltime expires first."
  log "Topology: $TOPOLOGY_REL"
  log "Production input: $PROD_MDIN_REL"
  log "Input restart: $INPUT_RESTART_REL"
  log "Output prefix: $OUTPUT_PREFIX"
  log "PMEMD binary: $PMEMD_BIN"
  log "OMP_NUM_THREADS=${OMP_NUM_THREADS}"

  if ! "$PMEMD_BIN" \
    -O \
    -i "$PROD_MDIN_REL" \
    -o "${OUTPUT_PREFIX}.out" \
    -p "$TOPOLOGY_REL" \
    -c "$INPUT_RESTART_REL" \
    -r "${OUTPUT_PREFIX}.rst7" \
    -x "${OUTPUT_PREFIX}.nc" \
    -e "${OUTPUT_PREFIX}.mden" \
    -inf "${OUTPUT_PREFIX}.mdinfo"; then
    fail "Production run failed"
  fi

  require_nonempty_file "${OUTPUT_PREFIX}.out"
  require_nonempty_file "${OUTPUT_PREFIX}.rst7"
  require_nonempty_file "${OUTPUT_PREFIX}.nc"
  require_nonempty_file "${OUTPUT_PREFIX}.mdinfo"
  log "Production outputs validated."
}

main "$@"
