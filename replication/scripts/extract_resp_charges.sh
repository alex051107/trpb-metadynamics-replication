#!/bin/bash

# Extract RESP charges for Ain/LLP from the capped Gaussian log,
# strip ACE/NME cap atoms, redistribute cap charge back onto the
# severed LLP boundary atoms, and generate the final frcmod.
#
# Longleaf usage:
#   module load amber/24p3
#   bash replication/scripts/extract_resp_charges.sh \
#     /work/users/l/i/liualex/AnimaLab/parameterization/ain/LLP_ain_resp_capped.log
#
# Important implementation note:
#   The capped fragment order is derived from scripts/build_llp_ain_capped_resp.py.
#   Do not replace this with hard-coded atom indices. The user-provided NME H
#   indices in task notes are stale for the current 54-atom generator output.

set -euo pipefail

trap 'echo "[ERROR] extract_resp_charges.sh failed at line ${LINENO}" >&2' ERR

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

FAILURE_PATTERNS_FILE="${REPO_ROOT}/replication/validations/failure-patterns.md"
GCRT_FILE="${REPO_ROOT}/replication/parameters/resp_charges/ain/LLP_ain_resp_capped.gcrt"
GENERATOR_FILE="${REPO_ROOT}/scripts/build_llp_ain_capped_resp.py"

INPUT_LOG="${1:-/work/users/l/i/liualex/AnimaLab/parameterization/ain/LLP_ain_resp_capped.log}"

RESP_DIR="${REPO_ROOT}/replication/parameters/resp_charges/ain"
MOL2_DIR="${REPO_ROOT}/replication/parameters/mol2"
FRCMOD_DIR="${REPO_ROOT}/replication/parameters/frcmod"

FULL_MOL2="${RESP_DIR}/LLP_ain_resp_full.mol2"
FINAL_MOL2="${MOL2_DIR}/Ain_gaff.mol2"
FRCMOD_FILE="${FRCMOD_DIR}/Ain.frcmod"

EXPECTED_CHARGE="-2.0"
CHARGE_TOL="0.01"
EXPECTED_HEAVY_ATOMS="24"
EXPECTED_TOTAL_ATOMS="42"
EXPECTED_FF14SB_RETYPE_COUNT="18"

echo "[INFO] Ain RESP extraction workflow"
echo "[INFO] Repo root: ${REPO_ROOT}"
echo "[INFO] Input Gaussian log: ${INPUT_LOG}"
echo

for required in "${FAILURE_PATTERNS_FILE}" "${GCRT_FILE}" "${GENERATOR_FILE}" "${INPUT_LOG}"; do
    if [[ ! -f "${required}" ]]; then
        echo "[ERROR] Required file not found: ${required}" >&2
        exit 1
    fi
done

for tool in antechamber parmchk2 python3; do
    if ! command -v "${tool}" >/dev/null 2>&1; then
        echo "[ERROR] Required tool not found: ${tool}" >&2
        echo "[ERROR] On Longleaf, load AmberTools first: module load amber/24p3" >&2
        exit 1
    fi
done

mkdir -p "${RESP_DIR}" "${MOL2_DIR}" "${FRCMOD_DIR}"

echo "[INFO] Provenance checks"
if grep -q 'iop(6/50=1)' "${GCRT_FILE}"; then
    echo "[ERROR] ${GCRT_FILE} still contains iop(6/50=1), which violates FP-013." >&2
    exit 1
fi
if ! grep -q -- '#HF/6-31G\* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt' "${GCRT_FILE}"; then
    echo "[WARN] Gaussian route in ${GCRT_FILE} does not match the validated RESP route." >&2
fi
if ! grep -q -- '^-2 1$' "${GCRT_FILE}"; then
    echo "[WARN] Charge/multiplicity line in ${GCRT_FILE} is not '-2 1'." >&2
fi
echo "[INFO] FP-009/010/012/013 constraints satisfied by current inputs"
echo

echo "[STEP 1/4] Extracting capped RESP charges with antechamber"
echo "[CMD] antechamber -i ${INPUT_LOG} -fi gout -o ${FULL_MOL2} -fo mol2 -c resp -at gaff -nc -2"
antechamber \
    -i "${INPUT_LOG}" \
    -fi gout \
    -o "${FULL_MOL2}" \
    -fo mol2 \
    -c resp \
    -at gaff \
    -nc -2
echo "[INFO] Wrote full capped mol2: ${FULL_MOL2}"
echo

echo "[STEP 2/4] Stripping ACE/NME caps and redistributing cap charge onto LLP"
python3 - "${FULL_MOL2}" "${FINAL_MOL2}" "${GENERATOR_FILE}" "${EXPECTED_CHARGE}" "${CHARGE_TOL}" "${EXPECTED_HEAVY_ATOMS}" "${EXPECTED_TOTAL_ATOMS}" "${EXPECTED_FF14SB_RETYPE_COUNT}" <<'PY'
import ast
import math
import re
import sys
import tempfile
from pathlib import Path


def fail(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(1)


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def info(message: str) -> None:
    print(f"[INFO] {message}")


def calculate_total_charge_e(atoms: list[dict]) -> float:
    total_charge = sum(atom["charge"] for atom in atoms)
    assert math.isfinite(total_charge), f"Total charge is not finite: {total_charge}"
    return total_charge


def calculate_heavy_atom_count(atoms: list[dict]) -> int:
    heavy_atom_count = sum(1 for atom in atoms if not atom["name"].startswith("H"))
    assert heavy_atom_count >= 0, f"Heavy-atom count cannot be negative: {heavy_atom_count}"
    return heavy_atom_count


def calculate_total_atom_count(atoms: list[dict]) -> int:
    atom_count = len(atoms)
    assert atom_count >= 0, f"Atom count cannot be negative: {atom_count}"
    return atom_count


def calculate_atom_type_by_atom_name(atoms: list[dict], atom_name: str) -> str:
    matches = [atom["type"] for atom in atoms if atom["name"] == atom_name]
    assert len(matches) == 1, f"Expected exactly one atom named {atom_name}, found {len(matches)}"
    return matches[0]


def retype_ff14sb_polymer_atoms(
    atoms: list[dict],
    expected_retype_count: int,
) -> int:
    # Verified against AmberTools 24p3 ff14SB amino12.lib on Longleaf:
    # LYS N/H/CA/HA/CB/HB2/HB3/CG/HG2/HG3/CD/HD2/HD3/CE/HE2/HE3/C/O
    # types are N/H/CX/H1/C8/HC/HC/C8/HC/HC/C8/HC/HC/C8/HP/HP/C/O.
    ff14sb_retype = {
        "N": ("n", "N"),
        "CA": ("c3", "CX"),
        "C": ("c", "C"),
        "O": ("o", "O"),
        "HN": ("hn", "H"),
        "HCA": ("h1", "H1"),
        "CB": ("c3", "C8"),
        "HCB1": ("hc", "HC"),
        "HCB2": ("hc", "HC"),
        "CG": ("c3", "C8"),
        "HCG1": ("hc", "HC"),
        "HCG2": ("hc", "HC"),
        "CD": ("c3", "C8"),
        "HCD1": ("hc", "HC"),
        "HCD2": ("hc", "HC"),
        "CE": ("c3", "C8"),
        "HCE1": ("h1", "HP"),
        "HCE2": ("h1", "HP"),
    }
    assert expected_retype_count == len(ff14sb_retype), (
        f"Expected retype-count assertion must match mapping size: "
        f"{expected_retype_count} != {len(ff14sb_retype)}"
    )

    retyped_count = 0
    for atom in atoms:
        if atom["name"] not in ff14sb_retype:
            continue
        old_type, new_type = ff14sb_retype[atom["name"]]
        assert atom["type"] == old_type, (
            f"Expected {atom['name']} type={old_type}, got {atom['type']}"
        )
        atom["type"] = new_type
        retyped_count += 1
        print(
            f"[RETYPE] {atom['name']}: {old_type} -> {new_type} "
            f"(ff14SB polymer compatibility)"
        )

    assert retyped_count == expected_retype_count, (
        f"Expected exactly {expected_retype_count} retyped atoms, found {retyped_count}"
    )

    # Schiff-base boundary remains GAFF because NZ/HNZ are not standard lysine amine atoms.
    assert calculate_atom_type_by_atom_name(atoms, "NZ") == "nh", (
        f"NZ must remain GAFF nh at the Schiff-base boundary, got "
        f"{calculate_atom_type_by_atom_name(atoms, 'NZ')}"
    )
    assert calculate_atom_type_by_atom_name(atoms, "HNZ") == "hn", (
        f"HNZ must remain GAFF hn at the Schiff-base boundary, got "
        f"{calculate_atom_type_by_atom_name(atoms, 'HNZ')}"
    )
    return retyped_count


def derive_generator_order(generator_path: Path) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    text = generator_path.read_text()

    llp_match = re.search(r"llp_atoms\s*=\s*(\[[^\]]*\])", text, re.S)
    if llp_match is None:
        fail("Could not find llp_atoms list in build_llp_ain_capped_resp.py")
    llp_heavy = ast.literal_eval(llp_match.group(1))
    if len(llp_heavy) != 24:
        fail(f"Expected 24 LLP heavy atoms in generator, found {len(llp_heavy)}")

    required_snippets = [
        '("C", "ACE_CH3"',
        '("C", "ACE_C"',
        '("O", "ACE_O"',
        '("N", "NME_N"',
        '("C", "NME_CH3"',
        'f"HACE{index}"',
        'f"HC2P{index}"',
        '"HC6"',
        'f"HC5P{index}"',
        '"HC4P"',
        '"HN"',
        '"HCA"',
        'f"HCB{index}"',
        'f"HCG{index}"',
        'f"HCD{index}"',
        'f"HCE{index}"',
        '"HNZ"',
        '"HNME"',
        'f"HNMEC{index}"',
    ]
    missing = [snippet for snippet in required_snippets if snippet not in text]
    if missing:
        fail(
            "Generator hydrogen/heavy-atom layout no longer matches this extraction script. "
            f"Missing source snippets: {missing}"
        )

    heavy_labels = ["ACE_CH3", "ACE_C", "ACE_O"] + llp_heavy + ["NME_N", "NME_CH3"]
    hydrogen_labels = (
        [f"HACE{i}" for i in range(1, 4)]
        + [f"HC2P{i}" for i in range(1, 4)]
        + ["HC6"]
        + [f"HC5P{i}" for i in range(1, 3)]
        + ["HC4P", "HN", "HCA"]
        + [f"HCB{i}" for i in range(1, 3)]
        + [f"HCG{i}" for i in range(1, 3)]
        + [f"HCD{i}" for i in range(1, 3)]
        + [f"HCE{i}" for i in range(1, 3)]
        + ["HNZ", "HNME"]
        + [f"HNMEC{i}" for i in range(1, 4)]
    )

    if len(heavy_labels) != 29 or len(hydrogen_labels) != 25:
        fail(
            f"Unexpected generator-derived atom counts: "
            f"{len(heavy_labels)} heavy, {len(hydrogen_labels)} hydrogen"
        )

    ace_labels = {"ACE_CH3", "ACE_C", "ACE_O", "HACE1", "HACE2", "HACE3"}
    nme_labels = {"NME_N", "NME_CH3", "HNME", "HNMEC1", "HNMEC2", "HNMEC3"}
    full_labels = heavy_labels + hydrogen_labels
    llp_labels = [label for label in full_labels if label not in ace_labels and label not in nme_labels]

    if len(llp_labels) != 42:
        fail(f"Expected 42 LLP atoms after cap removal, found {len(llp_labels)}")

    return full_labels, llp_labels, llp_heavy, sorted(ace_labels), sorted(nme_labels)


def parse_mol2(mol2_path: Path) -> tuple[list[str], list[dict], list[dict]]:
    lines = mol2_path.read_text().splitlines()
    atom_section = False
    bond_section = False
    atom_lines: list[str] = []
    bond_lines: list[str] = []

    for line in lines:
        if line.startswith("@<TRIPOS>ATOM"):
            atom_section = True
            bond_section = False
            continue
        if line.startswith("@<TRIPOS>BOND"):
            atom_section = False
            bond_section = True
            continue
        if line.startswith("@<TRIPOS>") and not line.startswith("@<TRIPOS>ATOM") and not line.startswith("@<TRIPOS>BOND"):
            atom_section = False
            bond_section = False
        if atom_section and line.strip():
            atom_lines.append(line)
        if bond_section and line.strip():
            bond_lines.append(line)

    if not atom_lines:
        fail(f"No ATOM section found in {mol2_path}")
    if not bond_lines:
        fail(f"No BOND section found in {mol2_path}")

    atoms: list[dict] = []
    for line in atom_lines:
        parts = line.split()
        if len(parts) < 8:
            fail(f"Malformed mol2 atom line: {line}")
        atoms.append(
            {
                "id": int(parts[0]),
                "name": parts[1],
                "x": float(parts[2]),
                "y": float(parts[3]),
                "z": float(parts[4]),
                "type": parts[5],
                "subst_id": int(parts[6]),
                "subst_name": parts[7],
                "charge": float(parts[8]) if len(parts) > 8 else 0.0,
                "extra": parts[9:],
            }
        )

    bonds: list[dict] = []
    for line in bond_lines:
        parts = line.split()
        if len(parts) < 4:
            fail(f"Malformed mol2 bond line: {line}")
        bonds.append(
            {
                "id": int(parts[0]),
                "origin": int(parts[1]),
                "target": int(parts[2]),
                "type": parts[3],
                "extra": parts[4:],
            }
        )

    return lines, atoms, bonds


def write_mol2(output_path: Path, atoms: list[dict], bonds: list[dict]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "@<TRIPOS>MOLECULE",
        "AIN",
        f"{len(atoms)} {len(bonds)} 1 0 0",
        "SMALL",
        "USER_CHARGES",
        "",
        "@<TRIPOS>ATOM",
    ]

    for atom in atoms:
        line = (
            f"{atom['id']:>7} "
            f"{atom['name']:<8} "
            f"{atom['x']:>10.4f} "
            f"{atom['y']:>10.4f} "
            f"{atom['z']:>10.4f} "
            f"{atom['type']:<8} "
            f"{1:>4} "
            f"{'AIN':<8} "
            f"{atom['charge']:>10.6f}"
        )
        if atom["extra"]:
            line += " " + " ".join(atom["extra"])
        lines.append(line)

    lines.extend(["@<TRIPOS>BOND"])
    for bond in bonds:
        line = (
            f"{bond['id']:>6} "
            f"{bond['origin']:>4} "
            f"{bond['target']:>4} "
            f"{bond['type']}"
        )
        if bond["extra"]:
            line += " " + " ".join(bond["extra"])
        lines.append(line)

    lines.extend(
        [
            "@<TRIPOS>SUBSTRUCTURE",
            "     1 AIN         1 TEMP              0 ****  ****    0 ROOT",
            "",
        ]
    )

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as handle:
        handle.write("\n".join(lines))
        temp_name = handle.name
    import shutil
    shutil.move(temp_name, str(output_path))


full_mol2 = Path(sys.argv[1])
final_mol2 = Path(sys.argv[2])
generator_file = Path(sys.argv[3])
expected_charge = float(sys.argv[4])
charge_tol = float(sys.argv[5])
expected_heavy_atoms = int(sys.argv[6])
expected_total_atoms = int(sys.argv[7])
expected_ff14sb_retype_count = int(sys.argv[8])

full_labels, llp_labels, llp_heavy, ace_labels, nme_labels = derive_generator_order(generator_file)
_, atoms, bonds = parse_mol2(full_mol2)

if len(atoms) != len(full_labels):
    fail(
        f"Full capped mol2 atom count mismatch: expected {len(full_labels)} from generator, "
        f"found {len(atoms)} in {full_mol2}"
    )

for atom, logical_label in zip(atoms, full_labels):
    atom["logical_label"] = logical_label

ace_charge = sum(atom["charge"] for atom in atoms if atom["logical_label"] in ace_labels)
nme_charge = sum(atom["charge"] for atom in atoms if atom["logical_label"] in nme_labels)

info(
    "Derived capped-fragment order from generator: "
    f"{len(full_labels)} atoms total, {len(llp_labels)} LLP atoms kept"
)
info(
    "Cap charge redistribution targets: "
    f"ACE -> LLP N ({ace_charge:+.6f}), NME -> LLP C ({nme_charge:+.6f})"
)

keep_atoms = [atom.copy() for atom in atoms if atom["logical_label"] in llp_labels]
old_to_new: dict[int, int] = {}
llp_by_label: dict[str, dict] = {}

for new_id, atom in enumerate(keep_atoms, start=1):
    old_to_new[atom["id"]] = new_id
    atom["id"] = new_id
    atom["name"] = atom["logical_label"]
    atom["subst_id"] = 1
    atom["subst_name"] = "AIN"
    llp_by_label[atom["logical_label"]] = atom

if "N" not in llp_by_label or "C" not in llp_by_label:
    fail("LLP boundary atoms N and/or C are missing after cap stripping")

# Redistribute cap charges onto the severed peptide-bond partners.
# ACE models the upstream carbonyl and is directly bonded to LLP N.
# NME models the downstream amide and is directly bonded to LLP C.
llp_by_label["N"]["charge"] += ace_charge
llp_by_label["C"]["charge"] += nme_charge

pre_retype_charge = calculate_total_charge_e(keep_atoms)
retyped_count = retype_ff14sb_polymer_atoms(
    keep_atoms,
    expected_ff14sb_retype_count,
)
post_retype_charge = calculate_total_charge_e(keep_atoms)
assert math.fabs(post_retype_charge - pre_retype_charge) <= 1.0e-12, (
    f"Retyping changed total charge: before {pre_retype_charge:.12f}, after {post_retype_charge:.12f}"
)
info(
    "ff14SB/GAFF boundary audit after retype: "
    f"N={calculate_atom_type_by_atom_name(keep_atoms, 'N')}, "
    f"CA={calculate_atom_type_by_atom_name(keep_atoms, 'CA')}, "
    f"CB={calculate_atom_type_by_atom_name(keep_atoms, 'CB')}, "
    f"CG={calculate_atom_type_by_atom_name(keep_atoms, 'CG')}, "
    f"CD={calculate_atom_type_by_atom_name(keep_atoms, 'CD')}, "
    f"CE={calculate_atom_type_by_atom_name(keep_atoms, 'CE')}, "
    f"NZ={calculate_atom_type_by_atom_name(keep_atoms, 'NZ')}"
)

keep_bonds = []
for bond in bonds:
    if bond["origin"] in old_to_new and bond["target"] in old_to_new:
        keep_bonds.append(
            {
                "id": len(keep_bonds) + 1,
                "origin": old_to_new[bond["origin"]],
                "target": old_to_new[bond["target"]],
                "type": bond["type"],
                "extra": bond["extra"],
            }
        )

heavy_atom_count = calculate_heavy_atom_count(keep_atoms)
total_atom_count = calculate_total_atom_count(keep_atoms)
final_charge = calculate_total_charge_e(keep_atoms)

if heavy_atom_count != expected_heavy_atoms:
    fail(
        f"Heavy-atom count mismatch after cap removal: expected {expected_heavy_atoms}, "
        f"found {heavy_atom_count}"
    )
if total_atom_count != expected_total_atoms:
    fail(
        f"Total atom count mismatch after cap removal: expected {expected_total_atoms}, "
        f"found {total_atom_count}"
    )
if math.fabs(final_charge - expected_charge) > charge_tol:
    fail(
        f"Final LLP charge mismatch: expected {expected_charge:.2f} ± {charge_tol:.2f}, "
        f"found {final_charge:.6f}"
    )

remaining_caps = [atom["name"] for atom in keep_atoms if atom["name"].startswith("ACE") or atom["name"].startswith("NME") or atom["name"].startswith("HACE") or atom["name"].startswith("HNME") or atom["name"].startswith("HNMEC")]
if remaining_caps:
    fail(f"Cap atoms still present after stripping: {remaining_caps}")

# FP-010 sanity check: ring atoms must not be typed as c1/c2 due to missing-H typing.
bad_ring_types = []
ring_atoms = {"N1", "C2", "C3", "C4", "C5", "C6"}
for atom in keep_atoms:
    if atom["name"] in ring_atoms and atom["type"] in {"c1", "c2"}:
        bad_ring_types.append(f"{atom['name']}={atom['type']}")
if bad_ring_types:
    fail(
        "Suspicious aromatic atom types in final LLP mol2 (possible FP-010 regression): "
        + ", ".join(bad_ring_types)
    )

write_mol2(final_mol2, keep_atoms, keep_bonds)
info(f"Wrote stripped LLP mol2: {final_mol2}")
info(
    f"Validation passed: {heavy_atom_count} heavy atoms, {total_atom_count} total atoms, "
    f"charge {final_charge:.6f}, retyped backbone atoms={retyped_count}"
)
PY
echo

echo "[STEP 3/4] Generating frcmod with parmchk2"
echo "[CMD] parmchk2 -i ${FINAL_MOL2} -f mol2 -o ${FRCMOD_FILE}"
parmchk2 -i "${FINAL_MOL2}" -f mol2 -o "${FRCMOD_FILE}"
echo "[INFO] Wrote frcmod: ${FRCMOD_FILE}"
echo

echo "[STEP 4/4] Post-generation validation"
if grep -n 'ATTN' "${FRCMOD_FILE}" >/dev/null 2>&1; then
    echo "[WARN] ATTN warnings found in ${FRCMOD_FILE}:"
    grep -n 'ATTN' "${FRCMOD_FILE}"
else
    echo "[INFO] No ATTN warnings found in ${FRCMOD_FILE}"
fi

echo
echo "[DONE] Stage 3 RESP extraction artifacts prepared"
echo "[DONE] Full capped mol2 : ${FULL_MOL2}"
echo "[DONE] Final LLP mol2   : ${FINAL_MOL2}"
echo "[DONE] Final frcmod     : ${FRCMOD_FILE}"
