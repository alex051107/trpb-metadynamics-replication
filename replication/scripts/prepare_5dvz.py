#!/usr/bin/env python3
"""Prepare chain A of 5DVZ for tleap assembly with residue 82 renamed to AIN.

UNVERIFIED handling:
- Histidine protonation is assigned with a conservative oxygen-contact heuristic.
- Residues 385-396 are missing from chain A in the deposited structure and are
  not modeled here. The prepared structure therefore ends at the last resolved
  residue in the deposited coordinates.
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path


STANDARD_RESIDUES = {
    "ALA",
    "ARG",
    "ASN",
    "ASP",
    "CYS",
    "GLN",
    "GLU",
    "GLY",
    "HIS",
    "ILE",
    "LEU",
    "LYS",
    "MET",
    "PHE",
    "PRO",
    "SER",
    "THR",
    "TRP",
    "TYR",
    "VAL",
}
REMOVED_HETATM_RESIDUES = {"HOH", "WAT", "NA", "PO4"}
EXPECTED_AIN_HEAVY_ATOMS = (
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
)


def info(message: str) -> None:
    print(f"[INFO] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def unverified(message: str) -> None:
    print(f"[UNVERIFIED] {message}")


def fail(message: str) -> None:
    raise SystemExit(f"[FAIL] {message}")


def assert_probability(value: float, label: str) -> float:
    assert math.isfinite(value), f"{label} occupancy is not finite: {value}"
    assert 0.0 <= value <= 1.0, f"{label} occupancy {value} is outside [0, 1]"
    return value


def assert_positive_integer(value: int, label: str) -> int:
    assert isinstance(value, int), f"{label} must be an integer"
    assert value > 0, f"{label} must be positive, got {value}"
    return value


def assert_distance_threshold_angstrom(value: float, label: str) -> float:
    assert math.isfinite(value), f"{label} is not finite"
    assert 0.0 < value < 10.0, f"{label}={value:.3f} A is outside a physically sensible range"
    return value


def calculate_distance_angstrom(atom_a: dict, atom_b: dict) -> float:
    dx = atom_a["x"] - atom_b["x"]
    dy = atom_a["y"] - atom_b["y"]
    dz = atom_a["z"] - atom_b["z"]
    distance = math.sqrt(dx * dx + dy * dy + dz * dz)
    assert 0.0 <= distance, f"Interatomic distance cannot be negative: {distance:.3f} A"
    return distance


def parse_pdb_atom_record(line: str) -> dict:
    assert line.startswith(("ATOM", "HETATM")), "Non-coordinate record passed to parse_pdb_atom_record"
    return {
        "record_type": line[0:6].strip(),
        "serial": int(line[6:11]),
        "name": line[12:16].strip(),
        "altloc": line[16].strip(),
        "resname": line[17:20].strip(),
        "chain": line[21].strip(),
        "resid": int(line[22:26]),
        "icode": line[26].strip(),
        "x": float(line[30:38]),
        "y": float(line[38:46]),
        "z": float(line[46:54]),
        "occupancy": assert_probability(float(line[54:60]), f"serial {int(line[6:11])}"),
        "tempfactor": float(line[60:66]),
        "element": (line[76:78].strip() or line[12:16].strip()[0]).strip(),
        "charge": line[78:80].strip(),
    }


def format_pdb_atom_record(record: dict, serial: int) -> str:
    atom_name_field = format_pdb_atom_name_field(record["name"], record["element"])
    return (
        f"{record['record_type']:<6}{serial:>5} "
        f"{atom_name_field}"
        f"{' ':1}"
        f"{record['resname']:>3} "
        f"{record['chain'] or ' ':1}"
        f"{record['resid']:>4}"
        f"{record['icode'] or ' ':1}   "
        f"{record['x']:>8.3f}"
        f"{record['y']:>8.3f}"
        f"{record['z']:>8.3f}"
        f"{record['occupancy']:>6.2f}"
        f"{record['tempfactor']:>6.2f}          "
        f"{record['element']:>2}"
        f"{record['charge']:>2}"
    )


def format_pdb_atom_name_field(atom_name: str, element: str) -> str:
    assert 1 <= len(atom_name) <= 4, f"Atom name must contain 1-4 characters, got {atom_name!r}"
    if len(atom_name) == 4 or len(element.strip()) == 2:
        return f"{atom_name:<4}"
    return f" {atom_name:<3}"


def format_ter_record(serial: int, last_record: dict) -> str:
    return (
        f"TER   {serial:>5}      "
        f"{last_record['resname']:>3} "
        f"{last_record['chain'] or ' ':1}"
        f"{last_record['resid']:>4}"
        f"{last_record['icode'] or ' ':1}"
    )


def read_pdb_lines(path: Path) -> list[str]:
    lines = path.read_text().splitlines()
    assert lines, f"PDB file is empty: {path}"
    return lines


def parse_coordinate_records(lines: list[str]) -> list[dict]:
    records = [parse_pdb_atom_record(line) for line in lines if line.startswith(("ATOM", "HETATM"))]
    assert records, "No coordinate records were parsed from the PDB"
    return records


def parse_missing_residues(lines: list[str], chain: str) -> list[tuple[str, int]]:
    missing = []
    for line in lines:
        if not line.startswith("REMARK 465"):
            continue
        fields = line.split()
        if len(fields) != 5:
            continue
        _, remark_id, resname, remark_chain, resid_text = fields
        if remark_id != "465" or remark_chain != chain or not resid_text.isdigit():
            continue
        missing.append((resname, int(resid_text)))
    return missing


def parse_missing_atoms(lines: list[str], chain: str) -> list[tuple[str, int, tuple[str, ...]]]:
    missing = []
    for line in lines:
        if not line.startswith("REMARK 470"):
            continue
        fields = line.split()
        if len(fields) < 6:
            continue
        if fields[1] != "470":
            continue
        resname = fields[2]
        remark_chain = fields[3]
        resid_text = fields[4]
        atom_names = tuple(fields[5:])
        if remark_chain == chain and resid_text.isdigit() and atom_names:
            missing.append((resname, int(resid_text), atom_names))
    return missing


def calculate_ssbond_count(lines: list[str], chain: str) -> int:
    count = 0
    for line in lines:
        if not line.startswith("SSBOND"):
            continue
        chain_a = line[15].strip()
        chain_b = line[29].strip()
        if chain in {chain_a, chain_b}:
            count += 1
    assert count >= 0, "SSBOND count must be non-negative"
    return count


def select_preferred_altloc_records(records: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, int, str, str, str], list[dict]] = defaultdict(list)
    for record in records:
        key = (record["chain"], record["resid"], record["icode"], record["resname"], record["name"])
        grouped[key].append(record)

    selected: list[dict] = []
    altloc_decision_count = 0
    for key, group in grouped.items():
        if len(group) == 1:
            chosen = dict(group[0])
            chosen["altloc"] = ""
            selected.append(chosen)
            continue

        altloc_decision_count += 1
        occupancy_sum = sum(assert_probability(record["occupancy"], f"{key} altloc") for record in group)
        assert 0.5 <= occupancy_sum <= 1.5, f"altLoc occupancy sum for {key} is suspicious: {occupancy_sum:.2f}"

        chosen = sorted(
            group,
            key=lambda record: (-record["occupancy"], record["altloc"] not in {"", "A"}, record["serial"]),
        )[0]
        chosen = dict(chosen)
        original_altloc = chosen["altloc"] or "blank"
        chosen["altloc"] = ""
        selected.append(chosen)

        candidate_summary = ", ".join(
            f"{record['altloc'] or 'blank'}:{record['occupancy']:.2f}" for record in sorted(group, key=lambda r: r["altloc"])
        )
        info(
            f"altLoc selection for {key[3]} {key[0]} {key[1]} atom {key[4]} -> {original_altloc} "
            f"(candidates {candidate_summary})"
        )

    info(f"altLoc arbitration groups resolved={altloc_decision_count}")
    return sorted(selected, key=lambda record: record["serial"])


def filter_chain_a_records(records: list[dict], chain: str, ain_resid: int) -> list[dict]:
    kept: list[dict] = []
    removed_residue_counts: dict[str, int] = defaultdict(int)

    for record in records:
        if record["chain"] != chain:
            continue

        if record["resname"] in REMOVED_HETATM_RESIDUES:
            removed_residue_counts[record["resname"]] += 1
            continue

        if record["record_type"] == "ATOM" and record["resname"] in STANDARD_RESIDUES:
            kept.append(dict(record))
            continue

        if record["record_type"] == "HETATM" and record["resname"] == "LLP" and record["resid"] == ain_resid:
            updated = dict(record)
            updated["record_type"] = "ATOM"
            updated["resname"] = "AIN"
            kept.append(updated)
            continue

        removed_residue_counts[record["resname"]] += 1

    for resname in sorted(removed_residue_counts):
        info(f"removed {removed_residue_counts[resname]} atoms from residue {resname}")

    assert kept, "No records survived chain-A filtering"
    return kept


def calculate_unique_residue_order(records: list[dict]) -> list[tuple[str, int, str, str]]:
    ordered: list[tuple[str, int, str, str]] = []
    seen = set()
    for record in records:
        key = (record["chain"], record["resid"], record["icode"], record["resname"])
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    assert ordered, "Residue order is empty"
    return ordered


def assert_contiguous_chain_numbering(records: list[dict]) -> None:
    residue_order = calculate_unique_residue_order(records)
    residue_numbers = [resid for _, resid, _, _ in residue_order]
    assert residue_numbers == list(range(residue_numbers[0], residue_numbers[-1] + 1)), (
        f"Resolved chain numbering is not contiguous: first={residue_numbers[0]}, last={residue_numbers[-1]}"
    )
    info(
        f"resolved chain residue numbering is contiguous from {residue_numbers[0]} to {residue_numbers[-1]} "
        f"({len(residue_numbers)} residues)"
    )


def read_ain_mol2_heavy_atom_names(path: Path) -> list[str]:
    lines = path.read_text().splitlines()
    try:
        start = lines.index("@<TRIPOS>ATOM") + 1
        end = lines.index("@<TRIPOS>BOND")
    except ValueError as exc:
        fail(f"Could not locate MOL2 ATOM/BOND sections in {path}: {exc}")

    heavy_atom_names: list[str] = []
    for line in lines[start:end]:
        if not line.strip():
            continue
        fields = line.split()
        atom_name = fields[1]
        if atom_name.startswith("H"):
            continue
        heavy_atom_names.append(atom_name)

    assert heavy_atom_names, "AIN MOL2 heavy-atom list is empty"
    info(f"Ain_gaff.mol2 heavy_atom_count={len(heavy_atom_names)}")
    return heavy_atom_names


def assert_ain_matches_parameter_atom_order(records: list[dict], mol2_path: Path, ain_resid: int) -> None:
    ain_records = [record for record in records if record["resname"] == "AIN" and record["resid"] == ain_resid]
    pdb_atom_names = [record["name"] for record in ain_records]
    mol2_atom_names = read_ain_mol2_heavy_atom_names(mol2_path)

    assert len(pdb_atom_names) == len(EXPECTED_AIN_HEAVY_ATOMS), (
        f"AIN residue {ain_resid} has {len(pdb_atom_names)} atoms, expected {len(EXPECTED_AIN_HEAVY_ATOMS)}"
    )
    assert tuple(pdb_atom_names) == EXPECTED_AIN_HEAVY_ATOMS, (
        f"AIN atom order in prepared PDB does not match expected LLP order: {pdb_atom_names}"
    )
    assert pdb_atom_names == mol2_atom_names, (
        f"AIN atom order mismatch between 5DVZ and Ain_gaff.mol2:\nPDB={pdb_atom_names}\nMOL2={mol2_atom_names}"
    )
    info("AIN atom names and order match Ain_gaff.mol2 exactly")


def calculate_histidine_contact_summary(
    histidine_records: list[dict],
    environment_records: list[dict],
    cutoff_angstrom: float,
) -> dict[str, float]:
    cutoff_angstrom = assert_distance_threshold_angstrom(cutoff_angstrom, "histidine oxygen-contact cutoff")
    residue_key = (histidine_records[0]["chain"], histidine_records[0]["resid"], histidine_records[0]["icode"])
    nd1 = next(record for record in histidine_records if record["name"] == "ND1")
    ne2 = next(record for record in histidine_records if record["name"] == "NE2")

    oxygen_acceptors = [
        record
        for record in environment_records
        if record["element"] == "O"
        and (record["chain"], record["resid"], record["icode"]) != residue_key
    ]
    assert oxygen_acceptors, "No oxygen acceptors were available for histidine-contact analysis"

    nd1_distances = [calculate_distance_angstrom(nd1, acceptor) for acceptor in oxygen_acceptors]
    ne2_distances = [calculate_distance_angstrom(ne2, acceptor) for acceptor in oxygen_acceptors]

    nd1_contacts = [distance for distance in nd1_distances if distance <= cutoff_angstrom]
    ne2_contacts = [distance for distance in ne2_distances if distance <= cutoff_angstrom]

    summary = {
        "nd1_contact_count": float(len(nd1_contacts)),
        "ne2_contact_count": float(len(ne2_contacts)),
        "nd1_min_distance": min(nd1_distances),
        "ne2_min_distance": min(ne2_distances),
    }
    return summary


def calculate_histidine_label(
    contact_summary: dict[str, float],
    cutoff_angstrom: float,
    ambiguity_margin_angstrom: float,
) -> tuple[str, str]:
    cutoff_angstrom = assert_distance_threshold_angstrom(cutoff_angstrom, "histidine oxygen-contact cutoff")
    ambiguity_margin_angstrom = assert_distance_threshold_angstrom(
        ambiguity_margin_angstrom, "histidine ambiguity margin"
    )

    nd1_count = int(contact_summary["nd1_contact_count"])
    ne2_count = int(contact_summary["ne2_contact_count"])
    nd1_min = contact_summary["nd1_min_distance"]
    ne2_min = contact_summary["ne2_min_distance"]

    if nd1_count > 0 and ne2_count == 0:
        return "HID", "oxygen-contact heuristic"
    if ne2_count > 0 and nd1_count == 0:
        return "HIE", "oxygen-contact heuristic"
    if nd1_count == 0 and ne2_count == 0:
        return "HIE", "UNVERIFIED: no oxygen acceptor within cutoff"

    if abs(nd1_min - ne2_min) > ambiguity_margin_angstrom:
        return ("HID", "oxygen-contact heuristic") if nd1_min < ne2_min else ("HIE", "oxygen-contact heuristic")
    return "HIE", "UNVERIFIED: ambiguous double-contact environment"


def assign_histidine_labels(
    filtered_records: list[dict],
    environment_records: list[dict],
    cutoff_angstrom: float,
    ambiguity_margin_angstrom: float,
) -> list[dict]:
    grouped: dict[tuple[str, int, str], list[dict]] = defaultdict(list)
    for record in filtered_records:
        if record["resname"] == "HIS":
            grouped[(record["chain"], record["resid"], record["icode"])].append(record)

    updated_records = [dict(record) for record in filtered_records]
    for residue_key, histidine_records in sorted(grouped.items(), key=lambda item: item[0][1]):
        atom_names = {record["name"] for record in histidine_records}
        assert {"ND1", "NE2"}.issubset(atom_names), f"HIS {residue_key} is missing ND1 or NE2"
        summary = calculate_histidine_contact_summary(histidine_records, environment_records, cutoff_angstrom)
        label, rationale = calculate_histidine_label(summary, cutoff_angstrom, ambiguity_margin_angstrom)

        message = (
            f"HIS {residue_key[0]} {residue_key[1]}: "
            f"ND1 contacts={int(summary['nd1_contact_count'])} min={summary['nd1_min_distance']:.2f} A; "
            f"NE2 contacts={int(summary['ne2_contact_count'])} min={summary['ne2_min_distance']:.2f} A -> {label} "
            f"({rationale})"
        )
        if rationale.startswith("UNVERIFIED"):
            unverified(message)
        else:
            info(message)

        for record in updated_records:
            if (record["chain"], record["resid"], record["icode"]) == residue_key and record["resname"] == "HIS":
                record["resname"] = label

    return updated_records


def write_prepared_pdb(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for serial, record in enumerate(records, start=1):
            handle.write(format_pdb_atom_record(record, serial) + "\n")
        handle.write(format_ter_record(len(records) + 1, records[-1]) + "\n")
        handle.write("END\n")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("replication/structures/5DVZ.pdb"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ain-mol2", type=Path, required=True)
    parser.add_argument("--chain", default="A")
    parser.add_argument("--ain-resid", type=int, default=82)
    parser.add_argument("--histidine-cutoff-angstrom", type=float, default=3.20)
    parser.add_argument("--histidine-ambiguity-margin-angstrom", type=float, default=0.20)
    return parser


def main() -> None:
    args = build_argument_parser().parse_args()

    assert len(args.chain) == 1, f"Chain identifier must be a single character, got {args.chain}"
    assert_positive_integer(args.ain_resid, "AIN residue number")
    assert_distance_threshold_angstrom(args.histidine_cutoff_angstrom, "histidine oxygen-contact cutoff")
    assert_distance_threshold_angstrom(
        args.histidine_ambiguity_margin_angstrom,
        "histidine ambiguity margin",
    )

    input_lines = read_pdb_lines(args.input)
    all_records = parse_coordinate_records(input_lines)
    altloc_selected_records = select_preferred_altloc_records(all_records)
    filtered_records = filter_chain_a_records(altloc_selected_records, args.chain, args.ain_resid)

    raw_chain_atom_count = sum(1 for record in altloc_selected_records if record["chain"] == args.chain)
    chain_atom_count = len(filtered_records)
    chain_residue_count = len(calculate_unique_residue_order(filtered_records))
    info(f"raw chain {args.chain} atom_count after altLoc selection={raw_chain_atom_count}")
    info(f"filtered chain {args.chain} atom_count={chain_atom_count}")
    info(f"filtered chain {args.chain} residue_count={chain_residue_count}")
    assert chain_residue_count > 300, f"Expected >300 residues in prepared chain {args.chain}, found {chain_residue_count}"

    assert_contiguous_chain_numbering(filtered_records)
    assert_ain_matches_parameter_atom_order(filtered_records, args.ain_mol2, args.ain_resid)

    missing_residues = parse_missing_residues(input_lines, args.chain)
    if missing_residues:
        first_missing = missing_residues[0][1]
        last_missing = missing_residues[-1][1]
        resolved_terminal_resid = calculate_unique_residue_order(filtered_records)[-1][1]
        unverified(
            f"5DVZ chain {args.chain} has missing residues {first_missing}-{last_missing}; "
            f"this script does not model them and leaves the resolved chain ending at residue {resolved_terminal_resid}"
        )

    missing_atoms = parse_missing_atoms(input_lines, args.chain)
    info(f"REMARK 470 missing-atom entries for chain {args.chain}={len(missing_atoms)}")
    if missing_atoms:
        warn(
            f"Standard residues with missing atoms will be handed to tleap for completion; "
            f"first entry={missing_atoms[0][0]} {missing_atoms[0][1]} missing {' '.join(missing_atoms[0][2])}"
        )

    ssbond_count = calculate_ssbond_count(input_lines, args.chain)
    info(f"SSBOND count touching chain {args.chain}={ssbond_count}")
    assert ssbond_count == 0, f"Expected no disulfide bridges for chain {args.chain}, found {ssbond_count}"

    updated_records = assign_histidine_labels(
        filtered_records,
        altloc_selected_records,
        args.histidine_cutoff_angstrom,
        args.histidine_ambiguity_margin_angstrom,
    )
    remaining_his = [record for record in updated_records if record["resname"] == "HIS"]
    assert not remaining_his, f"Unresolved HIS records remain after relabeling: {len(remaining_his)} atoms"

    write_prepared_pdb(args.output, updated_records)
    info(f"Wrote prepared PDB to {args.output}")


if __name__ == "__main__":
    main()
