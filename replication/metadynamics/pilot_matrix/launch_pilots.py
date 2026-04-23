"""Materialize pilot_matrix/ pilots from ladder.yaml with assertions.

Schema differences from probe_sweep/launch_sweep.py:
- adds sigma_seed (tunable initial SIGMA) to the substitution set
- adds lambda (per-anchor-set; must be finite for launch)
- adds anchor_set; resolves to a path_gromacs.pdb under
    ../probe_sweep/../single_walker/path_gromacs.pdb   (anchor_set=current)
    ../pilot_matrix/anchors/dw5dw0/path_gromacs.pdb    (anchor_set=dw5dw0)
  The dw5dw0 anchor must exist (with its own self-projection PASS
  provenance next to it) before Pilot 3/4 can be materialized.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "plumed_template.dat"
LADDER = HERE / "ladder.yaml"
MDP = HERE.parent / "probe_sweep" / "metad_probe.mdp"
CURRENT_ANCHOR = HERE.parent / "single_walker" / "path_gromacs.pdb"
DW5DW0_ANCHOR = HERE / "anchors" / "dw5dw0" / "path_gromacs.pdb"

ADAPTIVE_LITERAL = "ADAPTIVE=GEOM"
PATHMSD_LITERAL = "PATHMSD REFERENCE=path_gromacs.pdb"
PLUMED_KERNEL = "/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so"
ANCHOR_REGISTRY = {
    "current": CURRENT_ANCHOR,
    "dw5dw0": DW5DW0_ANCHOR,
}


def git_head():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=HERE
        ).decode().strip()
    except subprocess.CalledProcessError:
        return "UNKNOWN"


def substitute(template_text, smin, smax, sigma_seed, lam):
    out = (
        template_text
        .replace("__SIGMA_SEED__", f"{sigma_seed}")
        .replace("__SIGMA_MIN_S__", f"{smin[0]}")
        .replace("__SIGMA_MIN_Z__", f"{smin[1]}")
        .replace("__SIGMA_MAX_S__", f"{smax[0]}")
        .replace("__SIGMA_MAX_Z__", f"{smax[1]}")
        .replace("__LAMBDA__", f"{lam}")
    )
    assert "__" not in out, f"placeholder left after substitution: {out}"
    assert ADAPTIVE_LITERAL in out, f"missing {ADAPTIVE_LITERAL}"
    assert PATHMSD_LITERAL in out, f"missing {PATHMSD_LITERAL}"
    return out


def range_check(smin, smax, sigma_seed, lam):
    assert 0 < smin[0] < smax[0] <= 3.5, f"s-range violated: min={smin[0]} max={smax[0]}"
    assert 0 < smin[1] < smax[1] <= 0.5, f"z-range violated: min={smin[1]} max={smax[1]}"
    assert 0 < sigma_seed <= 1.0, f"sigma_seed out of band: {sigma_seed}"
    assert isinstance(lam, (int, float)) and lam > 0, f"lambda must be numeric > 0: {lam}"


def resolve_anchor(anchor_id):
    if anchor_id not in ANCHOR_REGISTRY:
        raise KeyError(f"unknown anchor_set: {anchor_id}; registry={list(ANCHOR_REGISTRY)}")
    path = ANCHOR_REGISTRY[anchor_id]
    if not path.exists():
        raise FileNotFoundError(
            f"anchor path missing: {path}. "
            f"For dw5dw0 the 15-frame path must be built + self-projection PASS before launch."
        )
    return path


def write_provenance(pilot_dir, pilot, commit, anchor_path, lam):
    lines = [
        f"pilot_id={pilot['id']}",
        f"anchor_set={pilot['anchor_set']}",
        f"anchor_path={anchor_path}",
        f"sigma_seed={pilot['sigma_seed']}",
        f"SIGMA_MIN_s={pilot['smin'][0]}",
        f"SIGMA_MIN_z={pilot['smin'][1]}",
        f"SIGMA_MAX_s={pilot['smax'][0]}",
        f"SIGMA_MAX_z={pilot['smax'][1]}",
        f"LAMBDA={lam}",
        "ADAPTIVE=GEOM",
        "BIASFACTOR=10",
        "HEIGHT=0.628",
        "PACE=1000",
        "TEMP=350",
        f"plan_commit_hash={commit}",
        f"plumed_kernel_path={PLUMED_KERNEL}",
        f"notes={pilot.get('notes', '')}",
    ]
    (pilot_dir / "provenance.txt").write_text("\n".join(lines) + "\n")


def materialize_pilot(pilot, template_text, mdp_template, commit):
    pid = pilot["id"]
    lam_raw = pilot["lambda"]
    if lam_raw == "UNDERIVED" or lam_raw is None:
        raise ValueError(
            f"{pid}: LAMBDA is UNDERIVED. Build the anchor path + re-derive lambda before launching."
        )
    lam = float(lam_raw)
    smin = pilot["smin"]
    smax = pilot["smax"]
    sigma_seed = pilot["sigma_seed"]
    range_check(smin, smax, sigma_seed, lam)
    anchor_path = resolve_anchor(pilot["anchor_set"])
    pilot_dir = HERE / f"pilot_{pid}"
    pilot_dir.mkdir(exist_ok=True)
    plumed_text = substitute(template_text, smin, smax, sigma_seed, lam)
    (pilot_dir / "plumed.dat").write_text(plumed_text)
    shutil.copy(mdp_template, pilot_dir / "metad.mdp")
    shutil.copy(anchor_path, pilot_dir / "path_gromacs.pdb")
    write_provenance(pilot_dir, pilot, commit, anchor_path, lam)
    print(
        f"[{pid}] anchor={pilot['anchor_set']} sigma_seed={sigma_seed} "
        f"SIGMA_MIN={smin} SIGMA_MAX={smax} LAMBDA={lam} -> {pilot_dir}"
    )
    return {"id": pid, "dir": str(pilot_dir)}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pilot",
        help="materialize only one pilot ID (e.g. Pilot2); omit for all",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    template_text = TEMPLATE.read_text()
    ladder = yaml.safe_load(LADDER.read_text())
    pilots = ladder["pilots"]
    if args.pilot:
        pilots = [p for p in pilots if p["id"] == args.pilot]
        if not pilots:
            raise KeyError(f"pilot {args.pilot} not in ladder")
    commit = git_head()
    summary = []
    for pilot in pilots:
        summary.append(materialize_pilot(pilot, template_text, MDP, commit))
    (HERE / "launch_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"wrote {len(summary)} pilots, plan_commit={commit}")


if __name__ == "__main__":
    main()
