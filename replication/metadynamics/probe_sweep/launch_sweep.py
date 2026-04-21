"""Purpose: materialize P1..P4 probe directories from ladder.yaml with assertions and per-probe provenance."""

import hashlib
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
MDP = HERE / "metad_probe.mdp"
PATH_PDB = HERE.parent / "single_walker" / "path_gromacs.pdb"

LAMBDA_LITERAL = "LAMBDA=379.77"
ADAPTIVE_LITERAL = "ADAPTIVE=GEOM"
SIGMA_SEED_LITERAL = "SIGMA=0.1"
PLUMED_KERNEL = "/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so"


def git_head():
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE).decode().strip()
    except subprocess.CalledProcessError:
        return "UNKNOWN"


def substitute(template_text, smin, smax):
    out = (template_text
           .replace("__SIGMA_MIN_S__", f"{smin[0]}")
           .replace("__SIGMA_MIN_Z__", f"{smin[1]}")
           .replace("__SIGMA_MAX_S__", f"{smax[0]}")
           .replace("__SIGMA_MAX_Z__", f"{smax[1]}"))
    assert "__SIGMA_" not in out, "placeholder left after substitution"
    assert LAMBDA_LITERAL in out, f"missing {LAMBDA_LITERAL}"
    assert ADAPTIVE_LITERAL in out, f"missing {ADAPTIVE_LITERAL}"
    assert SIGMA_SEED_LITERAL in out, f"missing {SIGMA_SEED_LITERAL}"
    return out


def range_check(smin, smax):
    assert 0 < smin[0] < smax[0] <= 3.5, f"s-range violated: min={smin[0]} max={smax[0]}"
    assert 0 < smin[1] < smax[1] <= 0.5, f"z-range violated: min={smin[1]} max={smax[1]}"


def write_provenance(probe_dir, probe_id, smin, smax, commit):
    lines = [
        f"probe_id={probe_id}",
        f"SIGMA_MIN_s={smin[0]}",
        f"SIGMA_MIN_z={smin[1]}",
        f"SIGMA_MAX_s={smax[0]}",
        f"SIGMA_MAX_z={smax[1]}",
        "LAMBDA=379.77",
        "SIGMA=0.1",
        "ADAPTIVE=GEOM",
        "BIASFACTOR=10",
        "HEIGHT=0.628",
        "PACE=1000",
        "TEMP=350",
        f"plan_commit_hash={commit}",
        f"plumed_kernel_path={PLUMED_KERNEL}",
        "restart_source=/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/start.gro",
        "restart_source_md5_longleaf=7e94940db8c9da1ad37d01e8affe1f6a",
    ]
    (probe_dir / "provenance.txt").write_text("\n".join(lines) + "\n")


def main():
    template_text = TEMPLATE.read_text()
    ladder = yaml.safe_load(LADDER.read_text())
    commit = git_head()
    summary = []
    for probe in ladder["probes"]:
        pid = probe["id"]
        smin = probe["smin"]
        smax = probe["smax"]
        range_check(smin, smax)
        probe_dir = HERE / f"probe_{pid}"
        probe_dir.mkdir(exist_ok=True)
        plumed_text = substitute(template_text, smin, smax)
        (probe_dir / "plumed.dat").write_text(plumed_text)
        shutil.copy(MDP, probe_dir / "metad.mdp")
        if PATH_PDB.exists():
            shutil.copy(PATH_PDB, probe_dir / "path_gromacs.pdb")
        write_provenance(probe_dir, pid, smin, smax, commit)
        print(f"[{pid}] SIGMA_MIN={smin} SIGMA_MAX={smax} -> {probe_dir}")
        summary.append({"id": pid, "smin": smin, "smax": smax, "dir": str(probe_dir)})
    (HERE / "launch_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"wrote {len(summary)} probes, plan_commit={commit}")


if __name__ == "__main__":
    main()
