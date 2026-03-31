#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BUILD_DIR="${REPO_ROOT}/replication/systems/pftrps_ain"

INPUT_PDB="${REPO_ROOT}/replication/structures/5DVZ.pdb"
AIN_MOL2="${REPO_ROOT}/replication/parameters/mol2/Ain_gaff.mol2"
AIN_FRCMOD="${REPO_ROOT}/replication/parameters/frcmod/Ain.frcmod"

PREP_SCRIPT="${SCRIPT_DIR}/prepare_5dvz.py"
TLEAP_INPUT="${SCRIPT_DIR}/tleap_pftrps_ain.in"

PREPARED_PDB="${BUILD_DIR}/5DVZ_chainA_prepared.pdb"
PREP_LOG="${BUILD_DIR}/prepare_5dvz.log"
TLEAP_LOG="${BUILD_DIR}/tleap_pftrps_ain.log"
PARM7="${BUILD_DIR}/pftrps_ain.parm7"
INPCRD="${BUILD_DIR}/pftrps_ain.inpcrd"
LEAP_PDB="${BUILD_DIR}/pftrps_ain_leap.pdb"

info() {
  echo "[INFO] $*"
}

warn() {
  echo "[WARN] $*"
}

unverified() {
  echo "[UNVERIFIED] $*"
}

fail() {
  echo "[FAIL] $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [[ -f "${path}" ]] || fail "Required file not found: ${path}"
}

require_nonempty_file() {
  local path="$1"
  require_file "${path}"
  [[ -s "${path}" ]] || fail "Required file is empty: ${path}"
}

require_command() {
  local command_name="$1"
  command -v "${command_name}" >/dev/null 2>&1 || fail "Required command not found in PATH: ${command_name}"
}

load_amber_module_if_available() {
  if command -v tleap >/dev/null 2>&1; then
    info "AmberTools already available in PATH"
    return 0
  fi

  if [[ -f /etc/profile.d/modules.sh ]]; then
    # shellcheck disable=SC1091
    source /etc/profile.d/modules.sh
  fi

  if command -v module >/dev/null 2>&1; then
    info "Loading amber/24p3 via environment modules"
    module load amber/24p3
  else
    unverified "Environment modules are unavailable in this shell. Assuming AmberTools was preloaded."
  fi
}

assert_integer_greater_than() {
  local label="$1"
  local value="$2"
  local lower_bound="$3"

  [[ "${value}" =~ ^-?[0-9]+$ ]] || fail "${label} is not an integer: ${value}"
  (( value > lower_bound )) || fail "${label}=${value} must be greater than ${lower_bound}"
  info "${label}=${value} > ${lower_bound}"
}

assert_float_between() {
  local label="$1"
  local value="$2"
  local lower_bound="$3"
  local upper_bound="$4"

  python3 - "${label}" "${value}" "${lower_bound}" "${upper_bound}" <<'PY'
import math
import sys

label = sys.argv[1]
value = float(sys.argv[2])
lower = float(sys.argv[3])
upper = float(sys.argv[4])

assert math.isfinite(value), f"{label} is not finite: {value}"
assert lower < upper, f"Invalid bounds for {label}: {lower} >= {upper}"
assert lower < value < upper, f"{label}={value:.6f} must satisfy {lower:.6f} < value < {upper:.6f}"
print(f"[INFO] {label}={value:.6f} within ({lower:.6f}, {upper:.6f})")
PY
}

validate_parameter_inputs() {
  info "Validating RESP/GAFF input artifacts before tleap"
  python3 - "${AIN_MOL2}" "${AIN_FRCMOD}" <<'PY'
from pathlib import Path
import math
import sys

mol2_path = Path(sys.argv[1])
frcmod_path = Path(sys.argv[2])


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def calculate_mol2_atom_block(lines: list[str]) -> list[str]:
    try:
        start = lines.index("@<TRIPOS>ATOM") + 1
        end = lines.index("@<TRIPOS>BOND")
    except ValueError as exc:
        fail(f"Could not locate MOL2 ATOM/BOND sections: {exc}")
    atom_lines = [line for line in lines[start:end] if line.strip()]
    assert atom_lines, "MOL2 ATOM block is empty"
    return atom_lines


def calculate_mol2_atom_count(atom_lines: list[str]) -> int:
    atom_count = len(atom_lines)
    assert atom_count > 0, "MOL2 atom count must be positive"
    print(f"[INFO] Ain_gaff.mol2 atom_count={atom_count} atoms")
    return atom_count


def calculate_mol2_heavy_atom_count(atom_lines: list[str]) -> int:
    heavy_count = sum(1 for line in atom_lines if not line.split()[1].startswith("H"))
    assert heavy_count >= 0, "Heavy-atom count must be non-negative"
    print(f"[INFO] Ain_gaff.mol2 heavy_atom_count={heavy_count} atoms")
    return heavy_count


def calculate_mol2_total_charge_e(atom_lines: list[str]) -> float:
    total_charge = sum(float(line.split()[-1]) for line in atom_lines)
    assert math.isfinite(total_charge), "MOL2 total charge is not finite"
    print(f"[INFO] Ain_gaff.mol2 total_charge={total_charge:.6f} e")
    return total_charge


def calculate_backbone_presence(atom_lines: list[str]) -> tuple[bool, bool]:
    atom_names = {line.split()[1] for line in atom_lines}
    has_n = "N" in atom_names
    has_c = "C" in atom_names
    print(f"[INFO] Ain_gaff.mol2 backbone_atoms_present N={has_n} C={has_c}")
    return has_n, has_c


mol2_lines = mol2_path.read_text().splitlines()
atom_lines = calculate_mol2_atom_block(mol2_lines)
atom_count = calculate_mol2_atom_count(atom_lines)
heavy_count = calculate_mol2_heavy_atom_count(atom_lines)
total_charge = calculate_mol2_total_charge_e(atom_lines)
has_n, has_c = calculate_backbone_presence(atom_lines)

assert atom_count == 42, f"Expected 42 atoms in Ain_gaff.mol2, found {atom_count}"
assert heavy_count == 24, f"Expected 24 heavy atoms in Ain_gaff.mol2, found {heavy_count}"
assert abs(total_charge - (-2.0)) <= 0.01, f"AIN charge mismatch: {total_charge:.6f} e"
assert has_n and has_c, "AIN backbone N/C atoms must be present for polymer linkage"

frcmod_text = frcmod_path.read_text()
print(f"[INFO] Ain.frcmod size={frcmod_path.stat().st_size} bytes")
assert frcmod_path.stat().st_size > 0, "Ain.frcmod is empty"
assert "ATTN" not in frcmod_text, "Ain.frcmod still contains ATTN warnings"
PY
}

calculate_pdb_atom_count() {
  local pdb_path="$1"
  python3 - "${pdb_path}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
atom_count = sum(1 for line in path.read_text().splitlines() if line.startswith(("ATOM", "HETATM")))
assert atom_count > 0, "PDB atom count must be positive"
print(atom_count)
PY
}

calculate_pdb_residue_count() {
  local pdb_path="$1"
  python3 - "${pdb_path}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
residue_keys = []
seen = set()
for line in path.read_text().splitlines():
    if not line.startswith(("ATOM", "HETATM")):
        continue
    key = (line[21], int(line[22:26]), line[26].strip())
    if key not in seen:
        seen.add(key)
        residue_keys.append(key)
residue_count = len(residue_keys)
assert residue_count > 0, "PDB residue count must be positive"
print(residue_count)
PY
}

calculate_box_lengths_angstrom() {
  local inpcrd_path="$1"
  python3 - "${inpcrd_path}" <<'PY'
from pathlib import Path
import math
import sys

path = Path(sys.argv[1])
lines = [line.rstrip() for line in path.read_text().splitlines() if line.strip()]
assert len(lines) >= 3, "Amber restart file is too short to contain coordinates and box lengths"
box_fields = lines[-1].split()
assert len(box_fields) == 6, f"Expected 6 box fields in final restart line, found {len(box_fields)}"
lengths = [float(value) for value in box_fields[:3]]
angles = [float(value) for value in box_fields[3:]]
for axis, length in zip(("box_x", "box_y", "box_z"), lengths):
    assert math.isfinite(length), f"{axis} is not finite"
    assert length > 0.0, f"{axis} must be positive, got {length}"
for axis, angle in zip(("alpha", "beta", "gamma"), angles):
    assert math.isfinite(angle), f"{axis} is not finite"
    assert 0.0 < angle <= 180.0, f"{axis} must lie in (0, 180], got {angle}"
print(f"{lengths[0]} {lengths[1]} {lengths[2]}")
PY
}

validate_tleap_log() {
  local log_path="$1"

  local parameter_failures
  local missing_atom_warnings
  local generic_warnings

  parameter_failures="$(grep -En "FATAL|Fatal Error|Could not find atom type|does not have a type|Unknown residue|No torsion terms|No angle terms|No bond parameter|not found in any table|For atom .* could not find" "${log_path}" || true)"
  missing_atom_warnings="$(grep -En "Created a new atom named|Added missing heavy atom" "${log_path}" || true)"
  generic_warnings="$(grep -En "Warning|WARNING" "${log_path}" || true)"

  if [[ -n "${generic_warnings}" ]]; then
    warn "tleap reported warnings:"
    printf '%s\n' "${generic_warnings}"
  fi

  if [[ -n "${missing_atom_warnings}" ]]; then
    unverified "tleap added missing atoms from standard residue templates:"
    printf '%s\n' "${missing_atom_warnings}"
  fi

  if [[ -n "${parameter_failures}" ]]; then
    printf '[FAIL] tleap reported fatal residue/parameter problems:\n%s\n' "${parameter_failures}" >&2
    exit 1
  fi
}

main() {
  mkdir -p "${BUILD_DIR}"

  require_file "${INPUT_PDB}"
  require_nonempty_file "${AIN_MOL2}"
  require_nonempty_file "${AIN_FRCMOD}"
  require_nonempty_file "${PREP_SCRIPT}"
  require_nonempty_file "${TLEAP_INPUT}"

  load_amber_module_if_available
  require_command python3
  require_command tleap
  validate_parameter_inputs

  info "Preparing chain A PDB with LLP residue 82 converted to AIN"
  python3 "${PREP_SCRIPT}" \
    --input "${INPUT_PDB}" \
    --ain-mol2 "${AIN_MOL2}" \
    --output "${PREPARED_PDB}" | tee "${PREP_LOG}"

  if grep -q '^\[UNVERIFIED\]' "${PREP_LOG}"; then
    unverified "prepare_5dvz.py reported heuristic decisions. Review ${PREP_LOG} before production MD."
  fi

  require_nonempty_file "${PREPARED_PDB}"

  info "Running tleap with the polymer-residue AIN template"
  (
    cd "${SCRIPT_DIR}"
    tleap -f "${TLEAP_INPUT}" | tee "${TLEAP_LOG}"
  )

  require_nonempty_file "${PARM7}"
  require_nonempty_file "${INPCRD}"
  require_nonempty_file "${LEAP_PDB}"
  validate_tleap_log "${TLEAP_LOG}"

  local solute_atom_count
  local solute_residue_count
  local final_atom_count
  local final_residue_count
  local box_lengths
  local box_x box_y box_z

  solute_atom_count="$(calculate_pdb_atom_count "${PREPARED_PDB}")"
  solute_residue_count="$(calculate_pdb_residue_count "${PREPARED_PDB}")"
  final_atom_count="$(calculate_pdb_atom_count "${LEAP_PDB}")"
  final_residue_count="$(calculate_pdb_residue_count "${LEAP_PDB}")"
  box_lengths="$(calculate_box_lengths_angstrom "${INPCRD}")"
  read -r box_x box_y box_z <<<"${box_lengths}"

  info "Prepared solute atom_count=${solute_atom_count}"
  info "Prepared solute residue_count=${solute_residue_count}"
  info "Final solvated atom_count=${final_atom_count}"
  info "Final solvated residue_count=${final_residue_count}"
  info "Final box_lengths=${box_x} ${box_y} ${box_z} Angstrom"

  assert_integer_greater_than "prepared_solute_residue_count" "${solute_residue_count}" 300
  assert_float_between "box_x_angstrom" "${box_x}" 50 200
  assert_float_between "box_y_angstrom" "${box_y}" 50 200
  assert_float_between "box_z_angstrom" "${box_z}" 50 200

  info "System assembly completed successfully"
  info "parm7   = ${PARM7}"
  info "inpcrd  = ${INPCRD}"
  info "leappdb = ${LEAP_PDB}"
  info "tleaplog= ${TLEAP_LOG}"
}

main "$@"
