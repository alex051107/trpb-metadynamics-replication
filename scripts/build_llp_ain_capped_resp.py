#!/usr/bin/env python3
"""
Build a local ACE-LLP-NME Gaussian input for Ain RESP fitting.

This script uses the crystal geometry from 5DVZ chain A:
- ACE cap is seeded from HIS81 CA/C/O
- LLP is residue 82
- NME cap is seeded from THR83 N/CA

The goal is not to reproduce the inaccessible Longleaf file byte-for-byte.
It creates a defensible repo-local replacement that can be reviewed, copied
to Longleaf, and then optimized by Gaussian before RESP charge extraction.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
INPUT_PDB = REPO_ROOT / "replication" / "structures" / "5DVZ.pdb"
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "replication"
    / "parameters"
    / "resp_charges"
    / "ain"
    / "LLP_ain_resp_capped.gcrt"
)


def norm(vector: np.ndarray) -> np.ndarray:
    magnitude = np.linalg.norm(vector)
    if magnitude < 1e-8:
        raise ValueError("Zero-length vector encountered while building geometry")
    return vector / magnitude


def perpendicular_basis(axis: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    axis = norm(axis)
    reference = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    first = norm(np.cross(axis, reference))
    second = norm(np.cross(axis, first))
    return first, second


def one_h(atom: np.ndarray, neighbors: list[np.ndarray], bond_length: float) -> np.ndarray:
    direction = np.zeros(3)
    for neighbor in neighbors:
        direction += norm(neighbor - atom)
    return atom - norm(direction) * bond_length


def two_h(atom: np.ndarray, neighbor_a: np.ndarray, neighbor_b: np.ndarray, bond_length: float) -> list[np.ndarray]:
    u = norm(neighbor_a - atom)
    v = norm(neighbor_b - atom)
    bisector = -norm(u + v)
    normal = np.cross(u, v)
    if np.linalg.norm(normal) < 1e-6:
        normal = perpendicular_basis(bisector)[0]
    else:
        normal = norm(normal)

    angle = math.radians(54.75)
    directions = [
        norm(math.cos(angle) * bisector + math.sin(angle) * normal),
        norm(math.cos(angle) * bisector - math.sin(angle) * normal),
    ]
    return [atom + direction * bond_length for direction in directions]


def three_h(atom: np.ndarray, neighbor: np.ndarray, bond_length: float) -> list[np.ndarray]:
    axis = norm(atom - neighbor)
    first, second = perpendicular_basis(axis)
    angle = math.radians(70.53)

    hydrogens = []
    for phi in (0.0, 2.0 * math.pi / 3.0, 4.0 * math.pi / 3.0):
        direction = norm(
            math.cos(angle) * axis
            + math.sin(angle) * (math.cos(phi) * first + math.sin(phi) * second)
        )
        hydrogens.append(atom + direction * bond_length)
    return hydrogens


def parse_pdb(
    pdb_path: Path,
) -> tuple[
    dict[tuple[str, int, str, str], np.ndarray],
    dict[tuple[str, int, str, str], str],
    dict[int, tuple[str, int, str, str]],
    dict[int, set[int]],
]:
    coords: dict[tuple[str, int, str, str], np.ndarray] = {}
    elements: dict[tuple[str, int, str, str], str] = {}
    serial_map: dict[int, tuple[str, int, str, str]] = {}
    connectivity: dict[int, set[int]] = {}

    for line in pdb_path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            atom = line[12:16].strip()
            residue = line[17:20].strip()
            chain = line[21].strip()
            residue_id = int(line[22:26])
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            element = line[76:78].strip() or atom[0]
            serial = int(line[6:11])

            key = (chain, residue_id, residue, atom)
            coords[key] = np.array([x, y, z], dtype=float)
            elements[key] = element
            serial_map[serial] = key
        elif line.startswith("CONECT"):
            parts = line.split()
            if len(parts) >= 3:
                source = int(parts[1])
                connectivity.setdefault(source, set()).update(int(value) for value in parts[2:])

    return coords, elements, serial_map, connectivity


def build_geometry() -> list[tuple[str, np.ndarray]]:
    coords, elements, serial_map, connectivity = parse_pdb(INPUT_PDB)

    def xyz(chain: str, residue_id: int, residue: str, atom: str) -> np.ndarray:
        key = (chain, residue_id, residue, atom)
        if key not in coords:
            raise KeyError(f"Missing atom in {INPUT_PDB}: {key}")
        return coords[key]

    llp_atoms = [
        "N1",
        "C2",
        "C2'",
        "C3",
        "O3",
        "C4",
        "C4'",
        "C5",
        "C6",
        "C5'",
        "OP4",
        "P",
        "OP1",
        "OP2",
        "OP3",
        "N",
        "CA",
        "CB",
        "CG",
        "CD",
        "CE",
        "NZ",
        "C",
        "O",
    ]

    heavy_atoms: list[tuple[str, str, np.ndarray]] = [
        ("C", "ACE_CH3", xyz("A", 81, "HIS", "CA")),
        ("C", "ACE_C", xyz("A", 81, "HIS", "C")),
        ("O", "ACE_O", xyz("A", 81, "HIS", "O")),
    ]

    for atom in llp_atoms:
        heavy_atoms.append((elements[("A", 82, "LLP", atom)], atom, xyz("A", 82, "LLP", atom)))

    heavy_atoms.extend(
        [
            ("N", "NME_N", xyz("A", 83, "THR", "N")),
            ("C", "NME_CH3", xyz("A", 83, "THR", "CA")),
        ]
    )

    positions = {label: atom_xyz for _, label, atom_xyz in heavy_atoms}
    hydrogens: list[tuple[str, str, np.ndarray]] = []

    for index, atom_xyz in enumerate(three_h(positions["ACE_CH3"], positions["ACE_C"], 1.09), start=1):
        hydrogens.append(("H", f"HACE{index}", atom_xyz))

    for index, atom_xyz in enumerate(three_h(positions["C2'"], positions["C2"], 1.09), start=1):
        hydrogens.append(("H", f"HC2P{index}", atom_xyz))

    # C5 is fully substituted (C4, C6, C5') — no hydrogen.
    # C6 has two ring bonds (N1, C5) and one hydrogen.
    hydrogens.append(("H", "HC6", one_h(positions["C6"], [positions["N1"], positions["C5"]], 1.08)))

    for index, atom_xyz in enumerate(two_h(positions["C5'"], positions["C5"], positions["OP4"], 1.09), start=1):
        hydrogens.append(("H", f"HC5P{index}", atom_xyz))

    hydrogens.append(("H", "HC4P", one_h(positions["C4'"], [positions["C4"], positions["NZ"]], 1.08)))
    hydrogens.append(("H", "HN", one_h(positions["N"], [positions["ACE_C"], positions["CA"]], 1.01)))
    hydrogens.append(("H", "HCA", one_h(positions["CA"], [positions["N"], positions["C"], positions["CB"]], 1.09)))

    for index, atom_xyz in enumerate(two_h(positions["CB"], positions["CA"], positions["CG"], 1.09), start=1):
        hydrogens.append(("H", f"HCB{index}", atom_xyz))

    for index, atom_xyz in enumerate(two_h(positions["CG"], positions["CB"], positions["CD"], 1.09), start=1):
        hydrogens.append(("H", f"HCG{index}", atom_xyz))

    for index, atom_xyz in enumerate(two_h(positions["CD"], positions["CG"], positions["CE"], 1.09), start=1):
        hydrogens.append(("H", f"HCD{index}", atom_xyz))

    for index, atom_xyz in enumerate(two_h(positions["CE"], positions["CD"], positions["NZ"], 1.09), start=1):
        hydrogens.append(("H", f"HCE{index}", atom_xyz))

    hydrogens.append(("H", "HNZ", one_h(positions["NZ"], [positions["C4'"], positions["CE"]], 1.01)))
    hydrogens.append(("H", "HNME", one_h(positions["NME_N"], [positions["C"], positions["NME_CH3"]], 1.01)))

    for index, atom_xyz in enumerate(three_h(positions["NME_CH3"], positions["NME_N"], 1.09), start=1):
        hydrogens.append(("H", f"HNMEC{index}", atom_xyz))

    if len(heavy_atoms) != 29 or len(hydrogens) != 25:
        raise ValueError(f"Unexpected capped fragment size: {len(heavy_atoms)} heavy, {len(hydrogens)} H")

    # Electron count parity check: singlet requires even electrons.
    Z_MAP = {"H": 1, "C": 6, "N": 7, "O": 8, "P": 15}
    z_total = sum(Z_MAP[elem] for elem, _, _ in heavy_atoms) + len(hydrogens)
    charge = -2
    n_electrons = z_total - charge
    if n_electrons % 2 != 0:
        raise ValueError(f"Odd electron count ({n_electrons}): Z_total={z_total}, charge={charge}. Singlet impossible.")

    # Basic clash check to catch obviously bad geometry before writing the file.
    atom_records = heavy_atoms + hydrogens
    bond_pairs = {
        tuple(sorted(pair))
        for pair in {
            ("ACE_CH3", "ACE_C"),
            ("ACE_C", "ACE_O"),
            ("ACE_C", "N"),
            ("C", "NME_N"),
            ("NME_N", "NME_CH3"),
        }
    }

    serial_to_llp_label = {
        serial: atom
        for serial, (chain, residue_id, residue, atom) in serial_map.items()
        if chain == "A" and residue_id == 82 and residue == "LLP"
    }
    for source, targets in connectivity.items():
        if source not in serial_to_llp_label:
            continue
        for target in targets:
            if target not in serial_to_llp_label:
                continue
            bond_pairs.add(tuple(sorted((serial_to_llp_label[source], serial_to_llp_label[target]))))
    labels = [label for _, label, _ in atom_records]
    xyz_by_label = {label: atom_xyz for _, label, atom_xyz in atom_records}

    parent_map = {label: None for _, label, _ in heavy_atoms}
    for hydrogen_label in [label for _, label, _ in hydrogens]:
        if hydrogen_label.startswith("HACE"):
            parent_map[hydrogen_label] = "ACE_CH3"
        elif hydrogen_label.startswith("HC2P"):
            parent_map[hydrogen_label] = "C2'"
        elif hydrogen_label == "HC6":
            parent_map[hydrogen_label] = "C6"
        elif hydrogen_label.startswith("HC5P"):
            parent_map[hydrogen_label] = "C5'"
        elif hydrogen_label == "HC4P":
            parent_map[hydrogen_label] = "C4'"
        elif hydrogen_label == "HN":
            parent_map[hydrogen_label] = "N"
        elif hydrogen_label == "HCA":
            parent_map[hydrogen_label] = "CA"
        elif hydrogen_label.startswith("HCB"):
            parent_map[hydrogen_label] = "CB"
        elif hydrogen_label.startswith("HCG"):
            parent_map[hydrogen_label] = "CG"
        elif hydrogen_label.startswith("HCD"):
            parent_map[hydrogen_label] = "CD"
        elif hydrogen_label.startswith("HCE"):
            parent_map[hydrogen_label] = "CE"
        elif hydrogen_label == "HNZ":
            parent_map[hydrogen_label] = "NZ"
        elif hydrogen_label == "HNME":
            parent_map[hydrogen_label] = "NME_N"
        elif hydrogen_label.startswith("HNMEC"):
            parent_map[hydrogen_label] = "NME_CH3"
        else:
            raise KeyError(f"Unknown hydrogen parent for {hydrogen_label}")

    for child, parent in parent_map.items():
        if parent is not None:
            bond_pairs.add(tuple(sorted((child, parent))))

    for index, label_a in enumerate(labels):
        for label_b in labels[index + 1 :]:
            if tuple(sorted((label_a, label_b))) in bond_pairs:
                continue
            distance = float(np.linalg.norm(xyz_by_label[label_a] - xyz_by_label[label_b]))
            if distance < 1.50:
                raise ValueError(f"Nonbonded clash detected: {label_a} - {label_b} = {distance:.3f} A")

    return [(element, atom_xyz) for element, _, atom_xyz in atom_records]


def write_gaussian_input(output_path: Path) -> None:
    atoms = build_geometry()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "%chk=LLP_ain_resp_capped.chk",
        "%nprocshared=8",
        "%mem=8GB",
        "#HF/6-31G* SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt",
        "",
        "ACE-LLP-NME Ain fragment for RESP charge fitting",
        "",
        "-2 1",
    ]

    for element, atom_xyz in atoms:
        lines.append(f"{element:<2} {atom_xyz[0]:>12.6f} {atom_xyz[1]:>12.6f} {atom_xyz[2]:>12.6f}")

    lines.append("")
    output_path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Gaussian .gcrt output path")
    args = parser.parse_args()

    write_gaussian_input(args.output)
    print(f"Wrote capped Gaussian input to {args.output}")


if __name__ == "__main__":
    main()
