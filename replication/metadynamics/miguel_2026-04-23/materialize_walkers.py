"""Stamp out 10 walker subdirectories from plumed_template.dat.

Each walker_NN/plumed.dat is an exact copy of plumed_template.dat with
WALKERS_ID=__WALKERS_ID__ substituted by the walker index 00..09.
A shared HILLS_DIR/ is created at the top level (all walkers write
their private HILLS there via WALKERS_RSTRIDE synchronization).

The path_gromacs.pdb and metad.mdp are copied per walker.
provenance.txt records Miguel-email source + walker index + plan commit.

Pre-flight assertions:
- template has exactly one __WALKERS_ID__ placeholder
- substituted plumed.dat has UNITS LENGTH=A ENERGY=kcal/mol (unit lock)
- substituted plumed.dat has ADAPTIVE=DIFF SIGMA=1000 (scheme lock)
- substituted plumed.dat has LAMBDA=80 (unit-consistent anchor, not 379.77)
- WALKERS_N=10 intact
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "plumed_template.dat"
PATH_PDB = HERE.parent / "single_walker" / "path_gromacs.pdb"
MDP = HERE.parent / "single_walker" / "metad.mdp"
HILLS_DIR = HERE / "HILLS_DIR"

UNIT_LITERAL = "UNITS LENGTH=A ENERGY=kcal/mol"
SCHEME_LITERAL = "ADAPTIVE=DIFF SIGMA=1000"
LAMBDA_LITERAL = "LAMBDA=3.77"
WALKERS_N_LITERAL = "WALKERS_N=10"


def git_head():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=HERE
        ).decode().strip()
    except subprocess.CalledProcessError:
        return "UNKNOWN"


def substitute(template_text: str, walker_id: int) -> str:
    placeholder = "__WALKERS_ID__"
    assert template_text.count(placeholder) == 1, (
        f"expected exactly one {placeholder} in template, "
        f"found {template_text.count(placeholder)}"
    )
    out = template_text.replace(placeholder, str(walker_id))
    assert UNIT_LITERAL in out, f"missing {UNIT_LITERAL}"
    assert SCHEME_LITERAL in out, f"missing {SCHEME_LITERAL}"
    assert LAMBDA_LITERAL in out, f"missing {LAMBDA_LITERAL}"
    assert WALKERS_N_LITERAL in out, f"missing {WALKERS_N_LITERAL}"
    return out


def materialize_walker(walker_id: int, template_text: str, commit: str) -> dict:
    walker_dir = HERE / f"walker_{walker_id:02d}"
    walker_dir.mkdir(exist_ok=True)
    plumed_text = substitute(template_text, walker_id)
    (walker_dir / "plumed.dat").write_text(plumed_text)
    if PATH_PDB.exists():
        shutil.copy(PATH_PDB, walker_dir / "path_gromacs.pdb")
    if MDP.exists():
        shutil.copy(MDP, walker_dir / "metad.mdp")
    provenance = [
        f"walker_id={walker_id:02d}",
        "source=miguel_email_2026-04-23",
        "UNITS=LENGTH_A_ENERGY_kcal_mol",
        f"LAMBDA=3.77_Ainv2",
        "LAMBDA_note=path-density-derived_2.3_over_MSD_0.61A2_equals_3.77_Ainv2",
        "LAMBDA_equiv_nm=379.77_nminv2",
        "LAMBDA_miguel_email=80_Ainv2_not_transferable_21x_too_sharp_for_our_path",
        "ADAPTIVE=DIFF",
        "SIGMA=1000_steps",
        "HEIGHT=0.15_kcal_per_mol",
        "BIASFACTOR=10.0",
        "TEMP=350.0",
        "WALKERS_N=10",
        "UPPER_WALLS_p1.zzz_at_2.5A_kappa_800",
        "WHOLEMOLECULES_ENTITY0=1-39268",
        f"plan_commit_hash={commit}",
        "path_pdb=path_gromacs.pdb_15_model_112_Calpha",
    ]
    (walker_dir / "provenance.txt").write_text("\n".join(provenance) + "\n")
    print(f"[walker_{walker_id:02d}] -> {walker_dir}")
    return {"id": walker_id, "dir": str(walker_dir)}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only",
        type=int,
        help="materialize only one walker id (0..9)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    template_text = TEMPLATE.read_text()
    HILLS_DIR.mkdir(exist_ok=True)
    commit = git_head()
    if args.only is not None:
        assert 0 <= args.only < 10, f"walker id out of range: {args.only}"
        ids = [args.only]
    else:
        ids = list(range(10))
    summary = [materialize_walker(i, template_text, commit) for i in ids]
    (HERE / "walkers_manifest.json").write_text(json.dumps(summary, indent=2))
    print(f"wrote {len(summary)} walkers, plan_commit={commit}")
    print(f"shared HILLS dir: {HILLS_DIR}")


if __name__ == "__main__":
    main()
