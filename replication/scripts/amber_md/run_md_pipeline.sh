#!/bin/bash
#SBATCH --job-name=pftrps_ain_prep
#SBATCH --partition=gpu
#SBATCH --qos=gpu_access
#SBATCH --gres=gpu:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --output=slurm-%x-%j.out

set -euo pipefail

WORKDIR="${WORKDIR:-/work/users/l/i/liualex/AnimaLab/replication/runs/pftrps_ain_md}"
TOPOLOGY_REL="${TOPOLOGY_REL:-../../systems/pftrps_ain/pftrps_ain.parm7}"
INITIAL_COORDS_REL="${INITIAL_COORDS_REL:-../../systems/pftrps_ain/pftrps_ain.inpcrd}"
MDIN_DIR_REL="${MDIN_DIR_REL:-../../scripts/amber_md}"
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

run_pmemd_step() {
  local step_name="$1"
  shift
  log "Starting ${step_name}"
  if ! "$PMEMD_BIN" "$@"; then
    fail "${step_name} failed"
  fi
  log "Finished ${step_name}"
}

validate_prep_outputs() {
  local required_outputs=(
    min1.out min1.rst7 min1.mdinfo
    min2.out min2.rst7 min2.mdinfo
    heat1.out heat1.rst7 heat1.nc heat1.mdinfo
    heat2.out heat2.rst7 heat2.nc heat2.mdinfo
    heat3.out heat3.rst7 heat3.nc heat3.mdinfo
    heat4.out heat4.rst7 heat4.nc heat4.mdinfo
    heat5.out heat5.rst7 heat5.nc heat5.mdinfo
    heat6.out heat6.rst7 heat6.nc heat6.mdinfo
    heat7.out heat7.rst7 heat7.nc heat7.mdinfo
    equil.out equil.rst7 equil.nc equil.mdinfo
  )
  local output
  for output in "${required_outputs[@]}"; do
    require_nonempty_file "$output"
  done
}

main() {
  module purge
  module load amber/24p3
  export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"

  mkdir -p "$WORKDIR"
  cd "$WORKDIR"

  require_nonempty_file "$TOPOLOGY_REL"
  require_nonempty_file "$INITIAL_COORDS_REL"
  require_nonempty_file "$MDIN_DIR_REL/min1.in"
  require_nonempty_file "$MDIN_DIR_REL/min2.in"
  require_nonempty_file "$MDIN_DIR_REL/heat1.in"
  require_nonempty_file "$MDIN_DIR_REL/heat7.in"
  require_nonempty_file "$MDIN_DIR_REL/equil.in"

  assert_file_contains_literal "$MDIN_DIR_REL/min1.in" "restraint_wt=500.0"
  assert_file_contains_literal "$MDIN_DIR_REL/min2.in" "ntr=0"
  assert_file_contains_literal "$MDIN_DIR_REL/heat1.in" "VALUE1=0.0, VALUE2=50.0"
  assert_file_contains_literal "$MDIN_DIR_REL/heat7.in" "VALUE1=300.0, VALUE2=350.0"
  assert_file_contains_literal "$MDIN_DIR_REL/equil.in" "nstlim=1000000"
  assert_file_contains_literal "$MDIN_DIR_REL/equil.in" "barostat=1"

  log "UNVERIFIED: SI extract does not specify heating/equilibration trajectory or restart write frequencies; the mdin files use NetCDF trajectories and end-of-stage restarts for operational convenience."
  log "UNVERIFIED: SI extract does not explicitly state the restrained-reference coordinate file; this launcher uses min2.rst7 as the common reference for all heating stages."
  log "Topology: $TOPOLOGY_REL"
  log "Initial coordinates: $INITIAL_COORDS_REL"
  log "MD input directory: $MDIN_DIR_REL"
  log "PMEMD binary: $PMEMD_BIN"
  log "OMP_NUM_THREADS=${OMP_NUM_THREADS}"

  run_pmemd_step "min1" \
    -O \
    -i "$MDIN_DIR_REL/min1.in" \
    -o min1.out \
    -p "$TOPOLOGY_REL" \
    -c "$INITIAL_COORDS_REL" \
    -ref "$INITIAL_COORDS_REL" \
    -r min1.rst7 \
    -inf min1.mdinfo
  require_nonempty_file min1.rst7

  run_pmemd_step "min2" \
    -O \
    -i "$MDIN_DIR_REL/min2.in" \
    -o min2.out \
    -p "$TOPOLOGY_REL" \
    -c min1.rst7 \
    -r min2.rst7 \
    -inf min2.mdinfo
  require_nonempty_file min2.rst7

  run_pmemd_step "heat1" \
    -O \
    -i "$MDIN_DIR_REL/heat1.in" \
    -o heat1.out \
    -p "$TOPOLOGY_REL" \
    -c min2.rst7 \
    -ref min2.rst7 \
    -r heat1.rst7 \
    -x heat1.nc \
    -e heat1.mden \
    -inf heat1.mdinfo
  require_nonempty_file heat1.rst7

  local previous_restart="heat1.rst7"
  local step
  for step in 2 3 4 5 6 7; do
    run_pmemd_step "heat${step}" \
      -O \
      -i "$MDIN_DIR_REL/heat${step}.in" \
      -o "heat${step}.out" \
      -p "$TOPOLOGY_REL" \
      -c "$previous_restart" \
      -ref min2.rst7 \
      -r "heat${step}.rst7" \
      -x "heat${step}.nc" \
      -e "heat${step}.mden" \
      -inf "heat${step}.mdinfo"
    require_nonempty_file "heat${step}.rst7"
    previous_restart="heat${step}.rst7"
  done

  run_pmemd_step "equil" \
    -O \
    -i "$MDIN_DIR_REL/equil.in" \
    -o equil.out \
    -p "$TOPOLOGY_REL" \
    -c heat7.rst7 \
    -r equil.rst7 \
    -x equil.nc \
    -e equil.mden \
    -inf equil.mdinfo

  validate_prep_outputs
  log "All minimization/heating/equilibration outputs validated."
}

main "$@"
