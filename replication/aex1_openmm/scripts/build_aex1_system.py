#!/usr/bin/env python3
"""Build the Aex1 OpenMM system for the 5DW0 chain-A pilot.

B4 scope:
- protein-only cleanup via PDBFixer
- PM-default PLS chemistry via OpenFF + AM1-BCC
- GAFF-2.11 primary template generation, SMIRNOFF fallback
- optional dry run that stops before solvation
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from openff.toolkit.topology import Molecule
from openff.toolkit.utils import AmberToolsToolkitWrapper, ToolkitRegistry
from openff.units import unit as off_unit
from openmm import LangevinIntegrator, NonbondedForce, Platform, Vec3, XmlSerializer, unit
from openmm.app import (
    HBonds,
    Modeller,
    NoCutoff,
    PDBFile,
    PME,
    Simulation,
)
from openmm.unit import femtosecond, kelvin, molar, nanometer, picosecond
from openmmforcefields.generators import SystemGenerator
from pdbfixer import PDBFixer


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_PDB = ROOT / "structures" / "5DW0.pdb"
DEFAULT_OUTDIR = Path.cwd() / "aex1_build"

DEFAULT_PDB_ID = "5DW0"
DEFAULT_CHAIN_ID = "A"
DEFAULT_LIGAND_CODE = "PLS"
DEFAULT_PH = 7.0
DEFAULT_PADDING_NM = 1.0
DEFAULT_IONIC_STRENGTH_M = 0.0
DEFAULT_MINIMIZATION_MAX_ITER = 10000
DEFAULT_MINIMIZATION_TOLERANCE = 10.0
MAX_FORCE_GATE = 1.0e4
PLS_EXPECTED_FORMAL_CHARGE = -2.0
PLS_HEAVY_ATOM_TARGET = 22
PLS_HEAVY_ATOM_TOL = 2
TOTAL_CHARGE_TOL = 1.0e-3
FORCE_GATE_TOL = 1.0e-3

PLS_SMILES_PM_DEFAULT = (
    "Cc1c(c(c(c[nH+]1)COP(=O)([O-])[O-])/C=[NH+]/[C@@H](CO)C(=O)[O-])[O-]"
)

# OpenFF atom index -> 5DW0 PLS heavy-atom name.
PLS_ATOM_NAME_BY_INDEX: Dict[int, str] = {
    14: "N",
    15: "CA",
    16: "CB",
    17: "OG",
    18: "C",
    19: "O",
    20: "OXT",
    6: "N1",
    1: "C2",
    0: "C2A",
    2: "C3",
    21: "O3",
    3: "C4",
    13: "C4A",
    4: "C5",
    5: "C6",
    7: "C5A",
    8: "O4P",
    9: "P",
    10: "O1P",
    11: "O2P",
    12: "O3P",
}

STANDARD_AA = {
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


@dataclass
class ResidueAtom:
    name: str
    element: str
    xyz: np.ndarray


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-pdb", type=Path, default=DEFAULT_SOURCE_PDB)
    parser.add_argument("--pdb-id", default=DEFAULT_PDB_ID)
    parser.add_argument("--chain", default=DEFAULT_CHAIN_ID)
    parser.add_argument("--ligand-code", default=DEFAULT_LIGAND_CODE)
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR)
    parser.add_argument("--dry", action="store_true")
    parser.add_argument("--forcefield-primary", default="gaff-2.11")
    parser.add_argument("--forcefield-fallback", default="openff-2.2.1")
    return parser.parse_args()


def ensure_source_pdb(source_pdb: Path, pdb_id: str) -> Path:
    if source_pdb.exists():
        print(f"source_pdb={source_pdb}")
        return source_pdb
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    source_pdb.parent.mkdir(parents=True, exist_ok=True)
    print(f"source_pdb_missing -> fetching {url}")
    urllib.request.urlretrieve(url, source_pdb)
    print(f"source_pdb_downloaded={source_pdb}")
    return source_pdb


def line_chain_id(line: str) -> str:
    return line[21].strip() or "_"


def line_resname(line: str) -> str:
    return line[17:20].strip()


def line_atom_name(line: str) -> str:
    return line[12:16].strip()


def line_element(line: str) -> str:
    element = line[76:78].strip()
    if element:
        return element
    return line_atom_name(line)[0]


def line_xyz(line: str) -> np.ndarray:
    return np.array(
        [
            float(line[30:38]),
            float(line[38:46]),
            float(line[46:54]),
        ],
        dtype=float,
    )


def extract_chain_a_protein(source_pdb: Path, chain_id: str, out_pdb: Path) -> None:
    selected: List[str] = []
    with source_pdb.open() as handle:
        for line in handle:
            record = line[:6].strip()
            if record == "ATOM" and line_chain_id(line) == chain_id and line_resname(line) in STANDARD_AA:
                selected.append(line)
            elif record in {"TER", "END"}:
                continue
    if not selected:
        raise RuntimeError(f"No protein ATOM records found for chain {chain_id} in {source_pdb}")
    with out_pdb.open("w") as handle:
        for line in selected:
            handle.write(line)
        handle.write("TER\nEND\n")


def extract_pls_residue(source_pdb: Path, chain_id: str, ligand_code: str) -> Dict[str, ResidueAtom]:
    atoms: Dict[str, ResidueAtom] = {}
    with source_pdb.open() as handle:
        for line in handle:
            if not line.startswith("HETATM"):
                continue
            if line_chain_id(line) != chain_id or line_resname(line) != ligand_code:
                continue
            atom_name = line_atom_name(line)
            atoms[atom_name] = ResidueAtom(
                name=atom_name,
                element=line_element(line),
                xyz=line_xyz(line),
            )
    if len(atoms) != PLS_HEAVY_ATOM_TARGET:
        raise RuntimeError(
            f"Expected {PLS_HEAVY_ATOM_TARGET} heavy atoms for {ligand_code} chain {chain_id}, found {len(atoms)}"
        )
    return atoms


def assert_ambertools_available() -> ToolkitRegistry:
    env_bin = Path(sys.executable).resolve().parent
    os.environ["PATH"] = f"{env_bin}:{os.environ.get('PATH', '')}"
    wrapper = AmberToolsToolkitWrapper()
    print(f"ambertools_wrapper={wrapper.__class__.__name__}")
    print(f"antechamber={shutil.which('antechamber')}")
    print(f"sqm={shutil.which('sqm')}")
    return ToolkitRegistry([wrapper])


def build_pls_molecule(toolkit_registry: ToolkitRegistry) -> Molecule:
    mol = Molecule.from_smiles(
        PLS_SMILES_PM_DEFAULT,
        allow_undefined_stereo=False,
    )
    mol.name = DEFAULT_LIGAND_CODE
    heavy_atom_count = sum(1 for atom in mol.atoms if atom.atomic_number > 1)
    formal_charge = mol.total_charge.m_as(off_unit.elementary_charge)
    print(f"pls_smiles={PLS_SMILES_PM_DEFAULT}")
    print(f"pls_atom_count_total={mol.n_atoms}")
    print(f"pls_heavy_atom_count={heavy_atom_count}")
    print(f"pls_formal_charge={formal_charge:.6f}")
    if not (PLS_HEAVY_ATOM_TARGET - PLS_HEAVY_ATOM_TOL <= heavy_atom_count <= PLS_HEAVY_ATOM_TARGET + PLS_HEAVY_ATOM_TOL):
        raise AssertionError(
            f"PLS heavy atoms {heavy_atom_count} outside expected window {PLS_HEAVY_ATOM_TARGET}+/-{PLS_HEAVY_ATOM_TOL}"
        )
    if abs(formal_charge - PLS_EXPECTED_FORMAL_CHARGE) > TOTAL_CHARGE_TOL:
        raise AssertionError(f"PLS formal charge {formal_charge} != {PLS_EXPECTED_FORMAL_CHARGE}")
    mol.assign_partial_charges("am1bcc", toolkit_registry=toolkit_registry)
    partial_charge_sum = mol.partial_charges.sum().m_as(off_unit.elementary_charge)
    print(f"pls_partial_charge_sum={partial_charge_sum:.6f}")
    if abs(partial_charge_sum - PLS_EXPECTED_FORMAL_CHARGE) > TOTAL_CHARGE_TOL:
        raise AssertionError(
            f"PLS partial charge sum {partial_charge_sum} != {PLS_EXPECTED_FORMAL_CHARGE}"
        )
    return mol


def kabsch_transform(source_xyz: np.ndarray, target_xyz: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    source_center = source_xyz.mean(axis=0)
    target_center = target_xyz.mean(axis=0)
    source_shifted = source_xyz - source_center
    target_shifted = target_xyz - target_center
    cov = source_shifted.T @ target_shifted
    v, _, wt = np.linalg.svd(cov)
    d = np.sign(np.linalg.det(v @ wt))
    rot = v @ np.diag([1.0, 1.0, d]) @ wt
    trans = target_center - source_center @ rot
    return rot, trans


def prepare_pls_positions(pls_mol: Molecule, crystal_atoms: Dict[str, ResidueAtom]) -> unit.Quantity:
    pls_mol.generate_conformers(n_conformers=1)
    conformer = pls_mol.conformers[0].m_as(off_unit.angstrom)
    source_idx = sorted(PLS_ATOM_NAME_BY_INDEX)
    source_xyz = np.vstack([conformer[idx] for idx in source_idx])
    target_xyz = np.vstack([crystal_atoms[PLS_ATOM_NAME_BY_INDEX[idx]].xyz for idx in source_idx])
    rot, trans = kabsch_transform(source_xyz, target_xyz)
    aligned = conformer @ rot + trans
    for idx, atom_name in PLS_ATOM_NAME_BY_INDEX.items():
        aligned[idx] = crystal_atoms[atom_name].xyz
    rmsd = np.sqrt(np.mean(np.sum((aligned[source_idx] - target_xyz) ** 2, axis=1)))
    print(f"pls_heavy_alignment_rmsd_A={rmsd:.6f}")
    return unit.Quantity(aligned.tolist(), unit.angstrom)


def build_ligand_topology(pls_mol: Molecule, positions_angstrom: unit.Quantity):
    off_top = pls_mol.to_topology()
    omm_top = off_top.to_openmm()
    positions_nm = positions_angstrom.value_in_unit(unit.nanometer)
    positions = [Vec3(*row) for row in positions_nm] * unit.nanometer
    return omm_top, positions


def configure_system_generator(
    small_molecule_forcefield: str,
    pls_mol: Molecule,
) -> SystemGenerator:
    return SystemGenerator(
        forcefields=[
            "amber/ff14SB.xml",
            "amber/tip3p_standard.xml",
            "amber/tip3p_HFE_multivalent.xml",
        ],
        small_molecule_forcefield=small_molecule_forcefield,
        molecules=[pls_mol],
        forcefield_kwargs={
            "constraints": HBonds,
            "rigidWater": True,
        },
        nonperiodic_forcefield_kwargs={
            "constraints": HBonds,
            "rigidWater": True,
            "nonbondedMethod": NoCutoff,
        },
        periodic_forcefield_kwargs={
            "constraints": HBonds,
            "rigidWater": True,
            "nonbondedMethod": PME,
            "nonbondedCutoff": DEFAULT_PADDING_NM * nanometer,
        },
    )


def count_residue_name(topology, residue_name: str) -> int:
    return sum(1 for residue in topology.residues() if residue.name == residue_name)


def count_atoms(topology) -> int:
    return sum(1 for _ in topology.atoms())


def choose_safe_platform() -> Platform:
    for name in ("CPU", "Reference"):
        try:
            platform = Platform.getPlatformByName(name)
            print(f"minimization_platform={name}")
            return platform
        except Exception:
            continue
    raise RuntimeError("No safe OpenMM platform available for B4 minimization")


def system_total_charge(system) -> float:
    nonbonded = next(force for force in system.getForces() if isinstance(force, NonbondedForce))
    total = 0.0
    for idx in range(system.getNumParticles()):
        charge, _, _ = nonbonded.getParticleParameters(idx)
        total += charge.value_in_unit(unit.elementary_charge)
    return total


def max_force_kj_mol_nm(simulation: Simulation) -> float:
    state = simulation.context.getState(getForces=True)
    forces = state.getForces(asNumpy=True).value_in_unit(unit.kilojoule_per_mole / unit.nanometer)
    norms = np.linalg.norm(forces, axis=1)
    return float(norms.max())


def write_pdb(topology, positions, output_path: Path) -> None:
    with output_path.open("w") as handle:
        PDBFile.writeFile(topology, positions, handle, keepIds=True)


def main() -> int:
    args = parse_args()
    source_pdb = ensure_source_pdb(args.source_pdb, args.pdb_id)
    args.outdir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="aex1_build_") as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        protein_pdb = tmpdir / "5DW0_chainA_protein.pdb"
        extract_chain_a_protein(source_pdb, args.chain, protein_pdb)
        crystal_atoms = extract_pls_residue(source_pdb, args.chain, args.ligand_code)
        print(f"chain={args.chain}")
        print(f"ligand_code={args.ligand_code}")
        print(f"crystal_pls_heavy_atoms={len(crystal_atoms)}")

        fixer = PDBFixer(filename=str(protein_pdb))
        fixer.platform = Platform.getPlatformByName("Reference")
        fixer.findMissingResidues()
        fixer.findMissingAtoms()
        missing_atom_count = sum(len(v) for v in fixer.missingAtoms.values())
        fixer.addMissingAtoms()
        fixer.addMissingHydrogens(pH=DEFAULT_PH)
        protein_atom_count = count_atoms(fixer.topology)
        print(f"protein_atom_count_after_pdbfixer={protein_atom_count}")
        print(f"protein_missing_atoms_added={missing_atom_count}")

        toolkit_registry = assert_ambertools_available()
        pls_mol = build_pls_molecule(toolkit_registry)
        ligand_topology, ligand_positions = build_ligand_topology(
            pls_mol,
            prepare_pls_positions(pls_mol, crystal_atoms),
        )

        modeller = Modeller(fixer.topology, fixer.positions)
        modeller.add(ligand_topology, ligand_positions)
        print(f"complex_atom_count_pre_solvation={count_atoms(modeller.topology)}")

        chosen_path = None
        system_generator = None
        dry_system = None
        for candidate in (args.forcefield_primary, args.forcefield_fallback):
            try:
                print(f"trying_small_molecule_forcefield={candidate}")
                system_generator = configure_system_generator(candidate, pls_mol)
                dry_system = system_generator.create_system(modeller.topology)
                chosen_path = candidate
                break
            except Exception as exc:  # pragma: no cover - exercised on Longleaf
                print(f"small_molecule_forcefield_failed={candidate}")
                print(f"failure_type={type(exc).__name__}")
                print(f"failure_message={exc}")
        if system_generator is None or dry_system is None or chosen_path is None:
            raise RuntimeError(
                "Both GAFF-2.11 and SMIRNOFF fallback failed. Stop and escalate to AMBER+RESP+tleap."
            )

        print(f"selected_small_molecule_forcefield={chosen_path}")
        dry_charge = system_total_charge(dry_system)
        print(f"dry_system_charge_e={dry_charge:.6f}")
        if args.dry:
            print("dry_run_complete=yes")
            return 0

        pre_na = count_residue_name(modeller.topology, "NA")
        modeller.addSolvent(
            system_generator.forcefield,
            model="tip3p",
            padding=DEFAULT_PADDING_NM * nanometer,
            ionicStrength=DEFAULT_IONIC_STRENGTH_M * molar,
            neutralize=True,
        )
        post_na = count_residue_name(modeller.topology, "NA")
        print(f"na_added={post_na - pre_na}")
        print(f"atom_count_post_solvation={count_atoms(modeller.topology)}")

        system = system_generator.create_system(modeller.topology)
        total_charge = system_total_charge(system)
        print(f"system_total_charge_e={total_charge:.6f}")
        if abs(total_charge) > TOTAL_CHARGE_TOL:
            raise AssertionError(f"System total charge {total_charge} exceeds tolerance {TOTAL_CHARGE_TOL}")

        integrator = LangevinIntegrator(350 * kelvin, 1.0 / picosecond, 2.0 * femtosecond)
        platform = choose_safe_platform()
        simulation = Simulation(modeller.topology, system, integrator, platform)
        simulation.context.setPositions(modeller.positions)
        simulation.minimizeEnergy(
            maxIterations=DEFAULT_MINIMIZATION_MAX_ITER,
            tolerance=DEFAULT_MINIMIZATION_TOLERANCE * unit.kilojoule_per_mole / unit.nanometer,
        )
        state = simulation.context.getState(getEnergy=True, getPositions=True)
        potential = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        max_force = max_force_kj_mol_nm(simulation)
        print(f"minimized_potential_kj_mol={potential:.6f}")
        print(f"max_force_kj_mol_nm={max_force:.6f}")
        if max_force > MAX_FORCE_GATE + FORCE_GATE_TOL:
            raise AssertionError(f"max_force_kj_mol_nm={max_force} exceeds gate {MAX_FORCE_GATE}")

        xml_path = args.outdir / "aex1_system.xml"
        pdb_path = args.outdir / "aex1_initial.pdb"
        xml_path.write_text(XmlSerializer.serialize(system))
        write_pdb(modeller.topology, state.getPositions(), pdb_path)
        print(f"system_xml={xml_path}")
        print(f"initial_pdb={pdb_path}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
