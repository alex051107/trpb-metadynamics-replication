#!/bin/bash

set -euo pipefail

ANIMALAB_ROOT="${ANIMALAB_ROOT:-/work/users/l/i/liualex/AnimaLab/replication}"
AMBER_RUN_DIR="${AMBER_RUN_DIR:-${ANIMALAB_ROOT}/runs/pftrps_ain_md}"
PARM7="${PARM7:-${ANIMALAB_ROOT}/systems/pftrps_ain/pftrps_ain.parm7}"
TRAJ="${TRAJ:-${AMBER_RUN_DIR}/prod_500ns.nc}"
SNAPSHOT_DIR="${SNAPSHOT_DIR:-${ANIMALAB_ROOT}/runs/pftrps_ain_gmx/snapshots}"
FRAME_STRIDE="${FRAME_STRIDE:-5000}"
NUM_SNAPSHOTS="${NUM_SNAPSHOTS:-10}"

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

extract_single_snapshot() {
  local frame_index="$1"
  local amber_restart="$2"

  cpptraj -p "${PARM7}" <<EOF >/dev/null
trajin ${TRAJ} ${frame_index} ${frame_index} 1
trajout ${amber_restart} restart
run
EOF
}

convert_restart_to_gro() {
  local amber_restart="$1"
  local gro_output="$2"

  python3 - <<PY
import math
import sys
try:
    import parmed as pmd
except ImportError as exc:
    raise SystemExit("ParmEd is required. Load amber/24p3 before running this script.") from exc

parm7 = ${PARM7@Q}
rst7 = ${amber_restart@Q}
gro = ${gro_output@Q}

structure = pmd.load_file(parm7, rst7)
atom_count = len(structure.atoms)
total_charge = float(sum(atom.charge for atom in structure.atoms))

assert atom_count == 39268, f"Expected 39268 atoms, found {atom_count}"
assert math.isfinite(total_charge), "Total charge is not finite"
assert abs(total_charge) < 1.0e-6, f"Expected neutral system, got {total_charge:.6e} e"

print(f"[INFO] converting {rst7} -> {gro}")
print(f"[INFO] atom_count={atom_count}")
print(f"[INFO] total_charge={total_charge:.6f} e")
structure.save(gro, overwrite=True)
PY
}

main() {
  module purge
  module load amber/24p3

  require_nonempty_file "${PARM7}"
  require_nonempty_file "${TRAJ}"

  mkdir -p "${SNAPSHOT_DIR}"

  log "UNVERIFIED: The paper specifies 10 starting conformations spanning conformational space, but it does not publish the exact snapshot timestamps. This script uses evenly spaced 50 ns intervals across the 500 ns production trajectory."
  log "PARM7=${PARM7}"
  log "TRAJ=${TRAJ}"
  log "SNAPSHOT_DIR=${SNAPSHOT_DIR}"
  log "FRAME_STRIDE=${FRAME_STRIDE}"
  log "NUM_SNAPSHOTS=${NUM_SNAPSHOTS}"

  local index
  for (( index=0; index<NUM_SNAPSHOTS; index++ )); do
    local frame_index=$((1 + index * FRAME_STRIDE))
    local tag
    tag=$(printf '%02d' "${index}")
    local amber_restart="${SNAPSHOT_DIR}/snapshot_${tag}.rst7"
    local gro_output="${SNAPSHOT_DIR}/snapshot_${tag}.gro"

    extract_single_snapshot "${frame_index}" "${amber_restart}"
    require_nonempty_file "${amber_restart}"
    convert_restart_to_gro "${amber_restart}" "${gro_output}"
    require_nonempty_file "${gro_output}"

    log "snapshot_${tag}: frame_index=${frame_index}"
  done

  log "Extracted ${NUM_SNAPSHOTS} restart snapshots and converted them to .gro."
}

main "$@"
