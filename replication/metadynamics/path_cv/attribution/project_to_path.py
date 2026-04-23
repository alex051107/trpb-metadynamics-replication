#!/usr/bin/env python3
"""Project an unbiased cMD trajectory window onto the production PATHMSD path.

Purpose: cheap front-run check before spending Aex1 MetaD quota. Compares
Ain vs Aex1 unbiased cMD windows — if Aex1 explores the same narrow
s ≈ 1.07 ± epsilon region that Ain does, the σ_min saturation is a path/
geometry property not Ain-specific chemistry (ChatGPT Pro follow-up 2026-04-23).

Strategy:
    1. Parse path_gromacs.pdb (15 MODELs, 112 Cα per MODEL) to learn the
       exact (resid, atom_name) pattern used by the production path CV.
    2. Load target trajectory + topology via MDAnalysis (works for AMBER .nc,
       OpenMM .dcd, GROMACS .xtc).
    3. Select matching 112 Cα atoms by (resid, name) pair.
    4. Slice the requested time window.
    5. Write a multi-MODEL PDB with per-MODEL atom serials renumbered 1..112
       (driver-local semantics, FP-030 pattern from 00b_self_projection_renumbered.sh).
    6. Run `plumed driver --mf_pdb` with a minimal PATHMSD projection deck.
    7. Emit COLVAR_proj with s, z columns.

Output is atomic: target COLVAR_proj is written once, with a provenance
header line prefixed `# provenance:` so downstream comparator can trace
which (trajectory, window, path_ref) produced it.

Assertions:
    - path_gromacs.pdb has exactly 15 MODELs and 112 ATOM lines per MODEL
    - Target trajectory selection resolves to exactly 112 atoms
    - Window time bounds fall inside trajectory span
    - plumed driver exit code is 0
    - COLVAR_proj row count equals sliced frame count

Usage:
    python project_to_path.py \\
        --traj <traj> --top <topology> \\
        --path-pdb <path_gromacs.pdb> \\
        --begin-ps <begin> --end-ps <end> --stride <n> \\
        --output-colvar <out.colvar> \\
        --plumed-exe <plumed_binary> \\
        [--timestep-ps <dt>] [--label <tag>]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple

import MDAnalysis as mda
from MDAnalysis import transformations as mdat


PATH_N_MODELS_EXPECTED = 15
PATH_N_ATOMS_PER_MODEL_EXPECTED = 112


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--traj", required=True, type=Path)
    ap.add_argument("--top", required=True, type=Path,
                    help="Topology file (.parm7 for AMBER, .pdb for OpenMM, .tpr for GROMACS)")
    ap.add_argument("--path-pdb", required=True, type=Path,
                    help="Multi-MODEL reference path PDB (e.g. path_gromacs.pdb)")
    ap.add_argument("--begin-ps", type=float, required=True,
                    help="Window start in picoseconds (inclusive)")
    ap.add_argument("--end-ps", type=float, required=True,
                    help="Window end in picoseconds (exclusive)")
    ap.add_argument("--stride", type=int, default=1,
                    help="Take every Nth frame inside the window (default=1)")
    ap.add_argument("--output-colvar", required=True, type=Path)
    ap.add_argument("--plumed-exe", default="plumed",
                    help="plumed binary path (default: first on PATH)")
    ap.add_argument("--lambda-val", type=float, default=379.77,
                    help="PATHMSD LAMBDA in nm^-2, FP-022-settled (default 379.77)")
    ap.add_argument("--timestep-ps", type=float, default=0.002,
                    help="Trajectory MD timestep in ps, only used to pass "
                         "--timestep to plumed driver (default 0.002)")
    ap.add_argument("--label", default="",
                    help="Freeform tag written into provenance header")
    ap.add_argument("--keep-tmp", action="store_true",
                    help="Keep driver-local renumbered PDB for inspection")
    return ap.parse_args()


def parse_path_pdb(path_pdb: Path) -> List[Tuple[int, str]]:
    """Return the (resid, atom_name) pattern used by the path reference.

    Uses MODEL 1; asserts subsequent MODELs share the identical pattern.
    """
    models: List[List[Tuple[int, str]]] = [[]]
    with path_pdb.open() as fh:
        for line in fh:
            if line.startswith("MODEL"):
                if models[-1]:
                    models.append([])
                continue
            if line.startswith("ENDMDL"):
                continue
            if not line.startswith("ATOM"):
                continue
            atom_name = line[12:16].strip()
            resid = int(line[22:26])
            models[-1].append((resid, atom_name))
    models = [m for m in models if m]

    assert len(models) == PATH_N_MODELS_EXPECTED, (
        f"path_gromacs.pdb must have {PATH_N_MODELS_EXPECTED} MODELs, "
        f"found {len(models)}"
    )
    n_atoms = len(models[0])
    assert n_atoms == PATH_N_ATOMS_PER_MODEL_EXPECTED, (
        f"Expected {PATH_N_ATOMS_PER_MODEL_EXPECTED} atoms per MODEL, "
        f"got {n_atoms}"
    )
    for i, m in enumerate(models[1:], start=2):
        assert m == models[0], (
            f"MODEL {i} (resid,name) pattern differs from MODEL 1; "
            f"path ref is not atomically consistent"
        )
    return models[0]


def select_matching_atoms(universe: mda.Universe,
                          pattern: List[Tuple[int, str]]) -> mda.AtomGroup:
    """Resolve the (resid, name) pattern to an AtomGroup in trajectory order.

    Every (resid, name) in pattern must resolve to exactly one atom. The
    returned AtomGroup preserves the pattern order so that projection onto
    the multi-MODEL path reference uses the same atom order per frame.
    """
    selected_indices: List[int] = []
    missing: List[Tuple[int, str]] = []
    for resid, name in pattern:
        sel = universe.select_atoms(f"resid {resid} and name {name}")
        if len(sel) != 1:
            missing.append((resid, name))
            continue
        selected_indices.append(sel[0].ix)
    assert not missing, (
        f"Failed to uniquely resolve {len(missing)} atoms in topology "
        f"(first 5: {missing[:5]}). Check resid convention alignment "
        f"between path_gromacs.pdb and the trajectory's topology."
    )
    assert len(selected_indices) == PATH_N_ATOMS_PER_MODEL_EXPECTED, (
        f"Selected {len(selected_indices)} atoms; expected "
        f"{PATH_N_ATOMS_PER_MODEL_EXPECTED}"
    )
    return universe.atoms[selected_indices]


def write_driver_pdb(universe: mda.Universe,
                     atom_group: mda.AtomGroup,
                     begin_ps: float,
                     end_ps: float,
                     stride: int,
                     out_pdb: Path) -> int:
    """Write multi-MODEL PDB with per-MODEL serial renumbering 1..N.

    Returns number of MODELs written. Asserts at least one frame was written.
    """
    assert end_ps > begin_ps, "end_ps must exceed begin_ps"
    n_atoms = len(atom_group)

    traj_begin_ps = universe.trajectory[0].time
    traj_end_ps = universe.trajectory[-1].time
    assert traj_begin_ps <= begin_ps < traj_end_ps, (
        f"begin_ps={begin_ps} outside trajectory span "
        f"[{traj_begin_ps}, {traj_end_ps}]"
    )
    assert begin_ps < end_ps <= traj_end_ps + 1e-3, (
        f"end_ps={end_ps} outside trajectory span "
        f"[{traj_begin_ps}, {traj_end_ps}]"
    )

    n_written = 0
    with out_pdb.open("w") as fh:
        fh.write("REMARK  driver-local serial renumbering per MODEL (FP-030)\n")
        frame_count = 0
        for ts in universe.trajectory:
            if ts.time < begin_ps:
                continue
            if ts.time >= end_ps:
                break
            if frame_count % stride != 0:
                frame_count += 1
                continue
            frame_count += 1

            fh.write(f"MODEL     {n_written + 1:>4d}\n")
            positions = atom_group.positions
            for i, atom in enumerate(atom_group, start=1):
                x, y, z = positions[i - 1]
                # path_gromacs.pdb normalizes all 112 Cα residues to "ALA" and
                # uses PDB-standard atom name alignment " CA " (space-pad the
                # 4-char atom name field with a leading space for 2-char
                # element atoms). plumed PATHMSD matches atoms by
                # (resname, resid, name), so we must write "ALA" + " CA "
                # to line up with the reference path.
                fh.write(
                    f"ATOM  {i:>5d}  CA  ALA A"
                    f"{atom.resid:>4d}    "
                    f"{x:>8.3f}{y:>8.3f}{z:>8.3f}  1.00  0.00           C  \n"
                )
            fh.write("ENDMDL\n")
            n_written += 1

    assert n_written > 0, (
        f"No frames written. Window [{begin_ps}, {end_ps}] may not overlap "
        f"trajectory frame times."
    )
    assert n_atoms == PATH_N_ATOMS_PER_MODEL_EXPECTED
    return n_written


def run_plumed_driver(pdb_in: Path,
                      path_ref: Path,
                      out_colvar: Path,
                      plumed_exe: str,
                      lambda_val: float,
                      timestep_ps: float,
                      work_dir: Path) -> None:
    """Invoke plumed driver to project pdb_in onto path_ref via PATHMSD.

    Writes out_colvar (s, z per MODEL). Asserts driver exit 0 and row count
    matches pdb MODEL count.
    """
    plumed_dat = work_dir / "project_path.dat"
    plumed_dat.write_text(
        f"p: PATHMSD REFERENCE={path_ref} LAMBDA={lambda_val}\n"
        f"PRINT ARG=p.sss,p.zzz FILE={out_colvar} STRIDE=1 FMT=%12.6f\n"
    )
    cmd = [
        plumed_exe, "driver",
        "--plumed", str(plumed_dat),
        "--mf_pdb", str(pdb_in),
        "--timestep", f"{timestep_ps:.6f}",
        "--trajectory-stride", "1",
    ]
    proc = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(
            f"plumed driver failed (exit {proc.returncode})\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}\n"
        )
        raise RuntimeError("plumed driver returned non-zero")
    assert out_colvar.exists(), "plumed driver reported success but produced no COLVAR"


def count_models(pdb: Path) -> int:
    with pdb.open() as fh:
        return sum(1 for line in fh if line.startswith("MODEL"))


def count_data_rows(colvar: Path) -> int:
    n = 0
    with colvar.open() as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            n += 1
    return n


def prepend_provenance(colvar: Path, provenance: str) -> None:
    body = colvar.read_text()
    colvar.write_text(f"# provenance: {provenance}\n{body}")


def main() -> int:
    args = parse_args()

    pattern = parse_path_pdb(args.path_pdb)

    print(f"[load] topology={args.top}")
    print(f"[load] trajectory={args.traj}")
    u = mda.Universe(str(args.top), str(args.traj))
    print(f"[load] n_atoms={u.atoms.n_atoms} n_frames={len(u.trajectory)} "
          f"dt={u.trajectory.dt:.3f}ps")

    # PBC unwrap: if the protein spans a periodic boundary, raw Cα coords
    # can have >100 Å inter-atomic gaps that break PATHMSD Kabsch alignment
    # and produce NaN s/z. Apply per-frame unwrap on the protein backbone.
    # Uses the "protein" selection since AMBER .nc / OpenMM .dcd don't always
    # store bonds reliably; we unwrap via COM-following instead.
    protein = u.select_atoms("protein")
    if protein.n_atoms > 0 and u.dimensions is not None:
        try:
            u.trajectory.add_transformations(mdat.unwrap(protein))
            print(f"[pbc] unwrap transformation applied to {protein.n_atoms} "
                  f"protein atoms")
        except Exception as exc:
            print(f"[pbc] unwrap transformation NOT applied ({exc}); "
                  f"relying on raw coordinates")

    ag = select_matching_atoms(u, pattern)
    print(f"[select] resolved {len(ag)}/{PATH_N_ATOMS_PER_MODEL_EXPECTED} atoms")

    workdir = Path(tempfile.mkdtemp(prefix="proj_path_"))
    print(f"[tmp] {workdir}")
    try:
        driver_pdb = workdir / "window_driver.pdb"
        n_models = write_driver_pdb(u, ag, args.begin_ps, args.end_ps,
                                    args.stride, driver_pdb)
        print(f"[slice] wrote {n_models} MODELs "
              f"[{args.begin_ps:.1f}, {args.end_ps:.1f}] ps stride={args.stride}")

        ref_drv = workdir / "path_driver.pdb"
        _renumber_reference(args.path_pdb, ref_drv)
        assert count_models(ref_drv) == PATH_N_MODELS_EXPECTED

        run_plumed_driver(
            pdb_in=driver_pdb,
            path_ref=ref_drv,
            out_colvar=args.output_colvar,
            plumed_exe=args.plumed_exe,
            lambda_val=args.lambda_val,
            timestep_ps=args.timestep_ps,
            work_dir=workdir,
        )

        n_rows = count_data_rows(args.output_colvar)
        assert n_rows == n_models, (
            f"COLVAR row count ({n_rows}) differs from PDB MODEL count "
            f"({n_models})"
        )

        prov = (
            f"traj={args.traj} top={args.top} path={args.path_pdb} "
            f"window_ps=[{args.begin_ps},{args.end_ps}] stride={args.stride} "
            f"lambda={args.lambda_val} label={args.label}"
        )
        prepend_provenance(args.output_colvar, prov)

        print(f"[done] wrote {args.output_colvar} ({n_rows} rows)")
    finally:
        if args.keep_tmp:
            print(f"[tmp retained] {workdir}")
        else:
            for f in workdir.glob("*"):
                f.unlink()
            workdir.rmdir()
    return 0


def _renumber_reference(src_pdb: Path, dst_pdb: Path) -> None:
    """Apply per-MODEL serial renumbering to path_gromacs.pdb (FP-030 pattern)."""
    with src_pdb.open() as src, dst_pdb.open("w") as dst:
        serial = 0
        for line in src:
            if line.startswith("MODEL"):
                serial = 0
                dst.write(line)
                continue
            if line.startswith("ATOM"):
                serial += 1
                dst.write(f"{line[:6]}{serial:>5d}{line[11:]}")
                continue
            dst.write(line)


if __name__ == "__main__":
    sys.exit(main())
