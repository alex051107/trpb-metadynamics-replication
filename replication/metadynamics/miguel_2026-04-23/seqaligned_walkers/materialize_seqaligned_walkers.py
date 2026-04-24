"""Materialize 10-walker production on sequence-aligned path.

Designed to run on Longleaf (needs gmx in PATH + AnimaLab tree).

For each walker_NN (NN=00..09):
  1. Extract snapshot at t = (NN+1)*50 ns from 500 ns Ain cMD trajectory
     via `gmx trjconv` → start.gro
  2. Copy path_seqaligned_gromacs.pdb + metad.mdp + topol.top
  3. Substitute WALKERS_ID=NN into plumed_template.dat → plumed.dat
  4. Build metad.tpr via `gmx grompp`
  5. Write provenance.txt

Shared HILLS_DIR/ at the parent level; all 10 walkers sync via
WALKERS_RSTRIDE=3000 (= 6 ps).

Pre-flight assertions:
- template has exactly one __WALKERS_ID__ placeholder
- path_seqaligned_gromacs.pdb has 15 MODELs × 112 atoms
- cMD trajectory has ≥ 500 ns of data (sanity: file exists, fits duration)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "plumed_template.dat"
PATH_PDB = HERE.parent.parent / "path_seqaligned" / "path_seqaligned_gromacs.pdb"

# Longleaf defaults — override with CLI flags if paths differ
DEFAULT_CMD_TPR = Path("/work/users/l/i/liualex/AnimaLab/classical_md/slurm/prod.tpr")
DEFAULT_CMD_XTC = Path("/work/users/l/i/liualex/AnimaLab/classical_md/slurm/prod.xtc")
DEFAULT_MDP = HERE.parent / "initial_seqaligned" / "metad.mdp"
DEFAULT_TOPOL = HERE.parent / "initial_seqaligned" / "topol.top"

HILLS_DIR = HERE / "HILLS_DIR"

UNIT_LITERAL = "UNITS LENGTH=A ENERGY=kcal/mol"
SCHEME_LITERAL = "ADAPTIVE=DIFF SIGMA=1000"
LAMBDA_LITERAL = "LAMBDA=80"
PATH_REF_LITERAL = "REFERENCE=path_seqaligned_gromacs.pdb"
WALKERS_N_LITERAL = "WALKERS_N=10"
HEIGHT_LITERAL = "HEIGHT=0.15"
BIASFACTOR_LITERAL = "BIASFACTOR=10.0"


def git_head():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=HERE, text=True
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"


def verify_template(template_text: str) -> None:
    placeholder = "__WALKERS_ID__"
    assert template_text.count(placeholder) == 1, (
        f"expected exactly one {placeholder}; found {template_text.count(placeholder)}"
    )
    for literal in (UNIT_LITERAL, SCHEME_LITERAL, LAMBDA_LITERAL,
                    PATH_REF_LITERAL, WALKERS_N_LITERAL,
                    HEIGHT_LITERAL, BIASFACTOR_LITERAL):
        assert literal in template_text, f"template missing required literal: {literal}"


def verify_path_pdb(path_pdb: Path) -> None:
    assert path_pdb.exists(), f"path reference missing: {path_pdb}"
    content = path_pdb.read_text()
    n_models = content.count("MODEL ")
    assert n_models == 15, f"expected 15 MODELs, got {n_models}"
    # per-model atom count: count ATOM lines / 15
    n_atoms_total = sum(1 for line in content.splitlines() if line.startswith("ATOM"))
    assert n_atoms_total == 15 * 112, (
        f"expected {15*112} ATOM lines, got {n_atoms_total}"
    )


def substitute(template_text: str, walker_id: int) -> str:
    out = template_text.replace("__WALKERS_ID__", str(walker_id))
    for lit in (UNIT_LITERAL, SCHEME_LITERAL, LAMBDA_LITERAL,
                PATH_REF_LITERAL, WALKERS_N_LITERAL):
        assert lit in out
    return out


def extract_snapshot(cmd_tpr: Path, cmd_xtc: Path, time_ps: float,
                     out_gro: Path) -> None:
    """Extract single frame at t = time_ps from cMD trajectory."""
    # gmx trjconv -s TPR -f XTC -o OUT.gro -dump time_ps
    # selection "0" = System (all atoms)
    proc = subprocess.run(
        ["gmx", "trjconv", "-s", str(cmd_tpr), "-f", str(cmd_xtc),
         "-o", str(out_gro), "-dump", str(time_ps)],
        input="0\n", text=True, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        print(f"gmx trjconv failed for t={time_ps} ps:")
        print(proc.stdout[-500:])
        print(proc.stderr[-500:])
        raise RuntimeError(f"trjconv failed for t={time_ps}")
    assert out_gro.exists() and out_gro.stat().st_size > 1000, (
        f"snapshot not written or too small: {out_gro}"
    )


def grompp(walker_dir: Path, mdp: Path, start_gro: Path, topol: Path) -> None:
    """Build metad.tpr for this walker."""
    tpr_out = walker_dir / "metad.tpr"
    proc = subprocess.run(
        ["gmx", "grompp", "-f", str(mdp), "-c", str(start_gro),
         "-p", str(topol), "-o", str(tpr_out), "-maxwarn", "2"],
        cwd=walker_dir, text=True, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        print(f"gmx grompp failed in {walker_dir}:")
        print(proc.stderr[-1000:])
        raise RuntimeError("grompp failed")
    assert tpr_out.exists()


def materialize_walker(walker_id: int, template_text: str, args, commit: str) -> dict:
    walker_dir = HERE / f"walker_{walker_id:02d}"
    walker_dir.mkdir(exist_ok=True)

    # 1. Snapshot at t = (walker_id + 1) * 50 ns = (walker_id + 1) * 50000 ps
    t_ps = (walker_id + 1) * 50_000  # 50, 100, ..., 500 ns
    start_gro = walker_dir / "start.gro"
    if not args.skip_snapshot:
        if args.cmd_xtc.exists():
            extract_snapshot(args.cmd_tpr, args.cmd_xtc, t_ps, start_gro)
        else:
            print(f"WARNING: cMD trajectory not found at {args.cmd_xtc}")
            print(f"  walker_{walker_id:02d} start.gro must be provided manually")
    # 2. Copy static refs
    shutil.copy(PATH_PDB, walker_dir / "path_seqaligned_gromacs.pdb")
    if args.mdp.exists():
        shutil.copy(args.mdp, walker_dir / "metad.mdp")
    # 3. Substituted plumed.dat
    (walker_dir / "plumed.dat").write_text(substitute(template_text, walker_id))
    # 4. topol + grompp (needs gmx)
    if not args.skip_grompp:
        if args.topol.exists() and (walker_dir / "metad.mdp").exists() and start_gro.exists():
            try:
                grompp(walker_dir, args.mdp, start_gro, args.topol)
            except RuntimeError as e:
                print(f"  grompp failed for walker_{walker_id:02d}: {e}")
    # 5. provenance
    provenance = [
        f"walker_id={walker_id:02d}",
        "source=miguel_email_2026-04-23 + FP-034 sequence-aligned path fix",
        "contract=PRIMARY_10WALKER (not fallback)",
        "UNITS=LENGTH_A_ENERGY_kcal_mol",
        "LAMBDA=80_Ainv2 (sequence-aligned path, Branduardi ratio 1.26x)",
        "ADAPTIVE=DIFF SIGMA=1000_steps",
        "HEIGHT=0.15_kcal_per_mol",
        "BIASFACTOR=10.0",
        "TEMP=350.0",
        "WALKERS_N=10 shared_HILLS_DIR=../HILLS_DIR WALKERS_RSTRIDE=3000",
        "UPPER_WALLS_p1.zzz_at_2.5A_kappa_800",
        "WHOLEMOLECULES_ENTITY0=1-39268",
        f"seed_source_cMD_time_ps={t_ps}",
        f"plan_commit_hash={commit}",
        "path_pdb=path_seqaligned_gromacs.pdb (NW +5 offset, FP-034 corrected)",
    ]
    (walker_dir / "provenance.txt").write_text("\n".join(provenance) + "\n")
    print(f"[walker_{walker_id:02d}] t_seed={t_ps} ps -> {walker_dir}")
    return {"id": walker_id, "dir": str(walker_dir), "t_seed_ps": t_ps}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, help="walker id (0..9) only")
    ap.add_argument("--cmd-tpr", type=Path, default=DEFAULT_CMD_TPR,
                    help="cMD production TPR")
    ap.add_argument("--cmd-xtc", type=Path, default=DEFAULT_CMD_XTC,
                    help="cMD production XTC (500 ns Ain)")
    ap.add_argument("--mdp", type=Path, default=DEFAULT_MDP,
                    help="MetaD mdp")
    ap.add_argument("--topol", type=Path, default=DEFAULT_TOPOL,
                    help="topology .top")
    ap.add_argument("--skip-snapshot", action="store_true",
                    help="don't extract snapshots (if already done)")
    ap.add_argument("--skip-grompp", action="store_true",
                    help="don't run grompp (if gmx unavailable)")
    args = ap.parse_args()

    template_text = TEMPLATE.read_text()
    verify_template(template_text)
    verify_path_pdb(PATH_PDB)

    HILLS_DIR.mkdir(exist_ok=True)
    commit = git_head()
    ids = [args.only] if args.only is not None else list(range(10))
    if args.only is not None:
        assert 0 <= args.only < 10

    summary = [materialize_walker(i, template_text, args, commit) for i in ids]
    (HERE / "walkers_manifest.json").write_text(json.dumps(summary, indent=2))
    print(f"\nwrote {len(summary)} walkers, plan_commit={commit}")
    print(f"shared HILLS dir: {HILLS_DIR}")
    print(f"\nnext: sbatch submit_array.sh")


if __name__ == "__main__":
    main()
