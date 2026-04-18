from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

EXPECTED_ATOM_COUNT = 39_268
EXPECTED_TOTAL_CHARGE = 0.0
BOX_TOLERANCE_ANGSTROM = 0.02
CHARGE_TOLERANCE_E = 1.0e-6
ENERGY_REL_TOL = 1.0e-3
ENERGY_CUTOFF_ANGSTROM = 8.0

class ConversionStopCondition(RuntimeError):
    """Raised when ParmEd cannot safely translate the AMBER system."""

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert AMBER parm7/rst7 to GROMACS top/gro and validate the result."
    )
    parser.add_argument("--parm7", required=True, help="Input AMBER topology (.parm7)")
    parser.add_argument("--rst7", required=True, help="Input AMBER restart/coordinates (.rst7)")
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory for converted GROMACS files and energy-check artifacts",
    )
    parser.add_argument(
        "--top-name",
        default="topol.top",
        help="Output GROMACS topology filename inside --output-dir",
    )
    parser.add_argument(
        "--gro-name",
        default="conf.gro",
        help="Output GROMACS coordinate filename inside --output-dir",
    )
    parser.add_argument(
        "--expected-atom-count",
        type=int,
        default=EXPECTED_ATOM_COUNT,
        help=f"Expected atom count assertion (default: {EXPECTED_ATOM_COUNT})",
    )
    parser.add_argument(
        "--expected-total-charge",
        type=float,
        default=EXPECTED_TOTAL_CHARGE,
        help=f"Expected net charge in elementary charge units (default: {EXPECTED_TOTAL_CHARGE:.1f})",
    )
    parser.add_argument(
        "--box-tolerance",
        type=float,
        default=BOX_TOLERANCE_ANGSTROM,
        help="Allowed per-edge AMBER↔GROMACS box mismatch in Angstrom",
    )
    parser.add_argument(
        "--charge-tolerance",
        type=float,
        default=CHARGE_TOLERANCE_E,
        help="Allowed AMBER↔GROMACS total-charge mismatch in e",
    )
    parser.add_argument(
        "--energy-rel-tol",
        type=float,
        default=ENERGY_REL_TOL,
        help="Allowed relative AMBER↔GROMACS potential-energy deviation",
    )
    parser.add_argument(
        "--gmx",
        default="gmx",
        help="GROMACS executable (default: gmx)",
    )
    parser.add_argument(
        "--sander",
        default="sander",
        help="AMBER single-point executable (default: sander)",
    )
    parser.add_argument(
        "--skip-energy-check",
        action="store_true",
        help="Convert and assert topology/charge/box only; do not run AMBER/GROMACS reruns",
    )
    return parser.parse_args()

def load_parmed_module():
    try:
        import parmed as pmd
    except ImportError as exc:
        raise SystemExit(
            "ParmEd is not available. Load AmberTools first, then rerun. "
            "Example: module load amber/24p3"
        ) from exc
    return pmd

def require_file(path: Path) -> None:
    assert path.is_file(), f"Required file does not exist: {path}"
    assert path.stat().st_size > 0, f"Required file is empty: {path}"

def run_command(
    command: list[str],
    *,
    cwd: Path,
    stdin_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    print(f"[RUN] {' '.join(command)}")
    result = subprocess.run(
        command,
        cwd=str(cwd),
        input=stdin_text,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result

def assert_finite(value: float, label: str) -> None:
    assert math.isfinite(value), f"{label} is not finite: {value}"

def format_triplet(values: Iterable[float]) -> str:
    return ", ".join(f"{value:.3f}" for value in values)

def get_box_lengths(structure) -> tuple[float, float, float]:
    box = getattr(structure, "box", None)
    assert box is not None, "Structure does not contain periodic box information"
    assert len(box) >= 3, f"Unexpected box record: {box}"
    lengths = tuple(float(box[index]) for index in range(3))
    for axis, value in zip(("a", "b", "c"), lengths):
        assert_finite(value, f"box[{axis}]")
        assert 10.0 < value < 300.0, (
            f"Box length {axis}={value:.3f} A outside expected 10-300 A range"
        )
    return lengths

def get_total_charge(structure) -> float:
    total_charge = float(sum(atom.charge for atom in structure.atoms))
    assert_finite(total_charge, "total_charge")
    assert -100.0 < total_charge < 100.0, (
        f"Total charge {total_charge:.6f} e is physically unreasonable"
    )
    return total_charge

def assert_atom_count(actual: int, expected: int) -> None:
    print(f"[INFO] atom_count={actual}")
    assert actual == expected, f"Expected {expected} atoms, found {actual}"

def assert_charge_expected(total_charge: float, expected_charge: float, tolerance: float) -> None:
    delta = abs(total_charge - expected_charge)
    print(
        f"[INFO] total_charge={total_charge:.6f} e ; "
        f"expected={expected_charge:.6f} e ; abs_delta={delta:.6e} e"
    )
    assert delta <= tolerance, (
        f"Total charge mismatch vs expected value: {delta:.6e} e > {tolerance:.6e} e"
    )

def assert_box_consistency(
    amber_box: tuple[float, float, float],
    gromacs_box: tuple[float, float, float],
    tolerance: float,
) -> None:
    deltas = tuple(abs(a - b) for a, b in zip(amber_box, gromacs_box))
    print(
        f"[INFO] amber_box_A=({format_triplet(amber_box)}) ; "
        f"gromacs_box_A=({format_triplet(gromacs_box)}) ; "
        f"abs_delta_A=({format_triplet(deltas)})"
    )
    for axis, delta in zip(("a", "b", "c"), deltas):
        assert delta <= tolerance, (
            f"Box mismatch along {axis}: {delta:.4f} A exceeds tolerance {tolerance:.4f} A"
        )

def assert_charge_consistency(
    amber_charge: float,
    gromacs_charge: float,
    tolerance: float,
) -> None:
    delta = abs(amber_charge - gromacs_charge)
    print(
        f"[INFO] amber_charge={amber_charge:.6f} e ; "
        f"gromacs_charge={gromacs_charge:.6f} e ; "
        f"abs_delta={delta:.6e} e"
    )
    assert delta <= tolerance, (
        f"AMBER↔GROMACS charge mismatch {delta:.6e} e exceeds tolerance {tolerance:.6e} e"
    )

def assert_energy_consistency(
    amber_energy: float,
    gromacs_energy: float,
    tolerance: float,
) -> float:
    denominator = max(abs(amber_energy), abs(gromacs_energy), 1.0)
    relative_delta = abs(amber_energy - gromacs_energy) / denominator
    print(
        f"[INFO] amber_potential={amber_energy:.6f} kJ/mol ; "
        f"gromacs_potential={gromacs_energy:.6f} kJ/mol ; "
        f"relative_delta={relative_delta:.6e}"
    )
    assert relative_delta <= tolerance, (
        f"AMBER↔GROMACS potential-energy relative deviation {relative_delta:.6e} "
        f"exceeds tolerance {tolerance:.6e}"
    )
    return relative_delta

def convert_to_gromacs(pmd, parm7: Path, rst7: Path, top_path: Path, gro_path: Path):
    try:
        structure = pmd.load_file(str(parm7), str(rst7))
    except Exception as exc:
        raise ConversionStopCondition(
            "STOP CONDITION: ParmEd could not load the AMBER parm7/rst7 pair. "
            "Do not proceed until the custom GAFF/ff14SB topology issue is resolved."
        ) from exc

    assert_atom_count(len(structure.atoms), args.expected_atom_count)
    amber_charge = get_total_charge(structure)
    amber_box = get_box_lengths(structure)
    assert_charge_expected(amber_charge, args.expected_total_charge, args.charge_tolerance)
    print(f"[INFO] amber_box_lengths_A=({format_triplet(amber_box)})")

    try:
        structure.save(str(top_path), overwrite=True)
        structure.save(str(gro_path), overwrite=True)
    except Exception as exc:
        raise ConversionStopCondition(
            "STOP CONDITION: ParmEd failed to serialize the system as GROMACS .top/.gro. "
            "This may indicate unsupported GAFF custom-residue handling."
        ) from exc

    require_file(top_path)
    require_file(gro_path)

    try:
        roundtrip = pmd.load_file(str(top_path), xyz=str(gro_path))
    except Exception as exc:
        raise ConversionStopCondition(
            "STOP CONDITION: ParmEd wrote GROMACS files but could not read them back. "
            "Treat this as an unsupported custom-residue translation until proven otherwise."
        ) from exc

    assert_atom_count(len(roundtrip.atoms), args.expected_atom_count)
    gromacs_charge = get_total_charge(roundtrip)
    gromacs_box = get_box_lengths(roundtrip)
    assert_charge_expected(gromacs_charge, args.expected_total_charge, args.charge_tolerance)
    assert_box_consistency(amber_box, gromacs_box, args.box_tolerance)
    assert_charge_consistency(amber_charge, gromacs_charge, args.charge_tolerance)

    return {
        "structure": structure,
        "amber_charge_e": amber_charge,
        "amber_box_A": amber_box,
        "gromacs_charge_e": gromacs_charge,
        "gromacs_box_A": gromacs_box,
    }

def write_gromacs_energy_check_mdp(path: Path) -> None:
    mdp = f"""\
integrator              = md
dt                      = 0.002
nsteps                  = 0
cutoff-scheme           = Verlet
nstlist                 = 20
rlist                   = {ENERGY_CUTOFF_ANGSTROM / 10.0:.1f}
coulombtype             = PME
rcoulomb                = {ENERGY_CUTOFF_ANGSTROM / 10.0:.1f}
vdwtype                 = Cut-off
rvdw                    = {ENERGY_CUTOFF_ANGSTROM / 10.0:.1f}
fourier-spacing         = 0.12
pme-order               = 4
constraints             = none
constraint-algorithm    = lincs
tcoupl                  = no
pcoupl                  = no
pbc                     = xyz
DispCorr                = no
nstenergy               = 1
nstcalcenergy           = 1
nstlog                  = 1
gen-vel                 = no
continuation            = yes
"""
    path.write_text(mdp, encoding="ascii")

def write_amber_energy_check_input(path: Path) -> None:
    amber_input = f"""\
Single-point energy check against GROMACS rerun
&cntrl
  imin=1,
  maxcyc=0,
  ntx=1,
  ntb=1,
  igb=0,
  cut={ENERGY_CUTOFF_ANGSTROM:.1f},
  ntc=1,
  ntf=1,
  ntpr=1,
/
"""
    path.write_text(amber_input, encoding="ascii")

def parse_gmx_potential_kj_mol(xvg_path: Path) -> float:
    require_file(xvg_path)
    last_value = None
    with xvg_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith(("#", "@")):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            last_value = float(parts[1])
    assert last_value is not None, f"Could not parse a potential-energy value from {xvg_path}"
    assert_finite(last_value, "gromacs_potential")
    return last_value

def parse_amber_potential_kj_mol(output_path: Path) -> float:
    require_file(output_path)
    energy_patterns = [
        re.compile(r"^\s*\d+\s+(-?\d+\.\d+E[+-]\d+|-?\d+\.\d+)"),
        re.compile(r"EPtot\s*=\s*(-?\d+\.\d+E[+-]\d+|-?\d+\.\d+)"),
        re.compile(r"Etot\s*=\s*(-?\d+\.\d+E[+-]\d+|-?\d+\.\d+)"),
    ]
    for line in output_path.read_text(encoding="utf-8", errors="replace").splitlines():
        for pattern in energy_patterns:
            match = pattern.search(line)
            if match:
                kcal_mol = float(match.group(1))
                kj_mol = kcal_mol * 4.184
                assert_finite(kj_mol, "amber_potential")
                return kj_mol
    raise RuntimeError(
        f"Could not parse AMBER potential energy from {output_path}. "
        "Inspect the single-point output manually."
    )

def ensure_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(
            f"Required executable not found in PATH: {name}. "
            "Load the Longleaf toolchain or rerun with --skip-energy-check."
        )

def run_energy_check(
    *,
    parm7: Path,
    rst7: Path,
    top_path: Path,
    gro_path: Path,
    output_dir: Path,
    gmx_binary: str,
    sander_binary: str,
) -> dict[str, float | str]:
    ensure_binary(gmx_binary)
    ensure_binary(sander_binary)

    gmx_mdp = output_dir / "energy_check.mdp"
    amber_in = output_dir / "energy_check.in"
    amber_out = output_dir / "amber_energy.out"
    gromacs_tpr = output_dir / "energy_check.tpr"
    gromacs_xvg = output_dir / "energy_check_potential.xvg"

    write_gromacs_energy_check_mdp(gmx_mdp)
    write_amber_energy_check_input(amber_in)

    run_command(
        [
            sander_binary,
            "-O",
            "-i",
            str(amber_in),
            "-o",
            str(amber_out),
            "-p",
            str(parm7),
            "-c",
            str(rst7),
        ],
        cwd=output_dir,
    )

    run_command(
        [
            gmx_binary,
            "grompp",
            "-f",
            str(gmx_mdp),
            "-c",
            str(gro_path),
            "-p",
            str(top_path),
            "-o",
            str(gromacs_tpr),
        ],
        cwd=output_dir,
    )

    run_command(
        [
            gmx_binary,
            "mdrun",
            "-s",
            str(gromacs_tpr),
            "-deffnm",
            "energy_check",
            "-rerun",
            str(gro_path),
            "-ntmpi",
            "1",
            "-ntomp",
            "1",
        ],
        cwd=output_dir,
    )

    run_command(
        [
            gmx_binary,
            "energy",
            "-f",
            str(output_dir / "energy_check.edr"),
            "-o",
            str(gromacs_xvg),
        ],
        cwd=output_dir,
        stdin_text="Potential\n0\n",
    )

    amber_potential = parse_amber_potential_kj_mol(amber_out)
    gromacs_potential = parse_gmx_potential_kj_mol(gromacs_xvg)
    relative_delta = assert_energy_consistency(
        amber_potential,
        gromacs_potential,
        args.energy_rel_tol,
    )

    return {
        "amber_single_point_kj_mol": amber_potential,
        "gromacs_single_point_kj_mol": gromacs_potential,
        "relative_delta": relative_delta,
    }

def write_report(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

def main() -> int:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    parm7 = Path(args.parm7).resolve()
    rst7 = Path(args.rst7).resolve()
    top_path = output_dir / args.top_name
    gro_path = output_dir / args.gro_name

    require_file(parm7)
    require_file(rst7)

    print("=" * 72)
    print("AMBER -> GROMACS conversion with physics checks")
    print("=" * 72)
    print(f"[INFO] parm7={parm7}")
    print(f"[INFO] rst7={rst7}")
    print(f"[INFO] output_dir={output_dir}")
    print(f"[INFO] expected_atom_count={args.expected_atom_count}")
    print(f"[INFO] expected_total_charge={args.expected_total_charge:.6f} e")

    pmd = load_parmed_module()

    try:
        conversion = convert_to_gromacs(pmd, parm7, rst7, top_path, gro_path)
    except ConversionStopCondition as exc:
        print(str(exc), file=sys.stderr)
        return 2

    report = {
        "parm7": str(parm7),
        "rst7": str(rst7),
        "topol_top": str(top_path),
        "conf_gro": str(gro_path),
        "atom_count": args.expected_atom_count,
        "amber_box_A": list(conversion["amber_box_A"]),
        "gromacs_box_A": list(conversion["gromacs_box_A"]),
        "amber_total_charge_e": conversion["amber_charge_e"],
        "gromacs_total_charge_e": conversion["gromacs_charge_e"],
        "energy_check": "skipped",
    }

    if not args.skip_energy_check:
        energy = run_energy_check(
            parm7=parm7,
            rst7=rst7,
            top_path=top_path,
            gro_path=gro_path,
            output_dir=output_dir,
            gmx_binary=args.gmx,
            sander_binary=args.sander,
        )
        report["energy_check"] = energy
    else:
        print("[INFO] Skipping AMBER↔GROMACS single-point energy check by request.")

    report_path = output_dir / "conversion_report.json"
    write_report(report_path, report)

    print(f"[INFO] Wrote report: {report_path}")
    print("[SUCCESS] Conversion and validation completed.")
    return 0

if __name__ == "__main__":
    args = parse_args()
    sys.exit(main())
