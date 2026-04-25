#!/usr/bin/env python3
"""Materialize an isolated v3 validation bundle on Longleaf.

This script does not submit Slurm jobs.  It selects 10 unique pilot frames,
asserts seed diversity, writes EM/NVT/production MDPs, and optionally extracts
coordinate-only start.gro files from the sequence-aligned pilot trajectory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import statistics
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


BASE = Path("/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23")
PILOT = BASE / "initial_seqaligned"
SEQ_WALKERS = BASE / "seqaligned_walkers"
PATH_SOURCE = BASE / "seqaligned_walkers_v2" / "walker_00" / "path_seqaligned_gromacs.pdb"
PLUMED_TEMPLATE = SEQ_WALKERS / "plumed_template.dat"
OUT_DEFAULT = BASE / "seqaligned_walkers_v3_validation"

N_WALKERS = 10
N_ATOMS = 39268
TARGETS = tuple(range(1, 11))


@dataclass(frozen=True)
class Seed:
    walker_id: int
    target_s: int
    time_ps: float
    s: float
    z: float


COMMON_MD = """\
nstlog                  = 1000
nstcalcenergy           = 1000
nstenergy               = 1000
nstxout                 = 0
nstvout                 = 0
nstfout                 = 0
nstxout-compressed      = 5000
compressed-x-grps       = System

cutoff-scheme           = Verlet
nstlist                 = 20
rlist                   = 0.8

coulombtype             = PME
rcoulomb                = 0.8
vdwtype                 = Cut-off
rvdw                    = 0.8
pme-order               = 4
fourier-spacing         = 0.12

pbc                     = xyz
DispCorr                = no

constraints             = h-bonds
constraint-algorithm    = lincs
lincs_iter              = 1
lincs_order             = 4
"""


def parse_colvar(path: Path) -> list[tuple[float, float, float]]:
    rows: list[tuple[float, float, float]] = []
    with path.open() as handle:
        for line in handle:
            if not line.strip() or line.startswith("#"):
                continue
            time_ps, s_val, z_val = map(float, line.split()[:3])
            rows.append((time_ps, s_val, z_val))
    if not rows:
        raise ValueError(f"no COLVAR rows parsed from {path}")
    return rows


def select_seeds(
    rows: list[tuple[float, float, float]],
    *,
    z_max: float,
    min_s_gap: float,
    min_time_gap_ps: float,
) -> list[Seed]:
    seeds: list[Seed] = []
    for walker_id, target in enumerate(TARGETS):
        lo = 0.5 if target == 1 else target - 0.5
        hi = target + 0.5
        candidates = [
            row for row in rows
            if lo <= row[1] < hi and row[2] <= z_max
        ]
        candidates.sort(key=lambda row: (row[2], abs(row[1] - target), row[0]))
        if not candidates:
            raise ValueError(f"no candidates for target_s={target} in [{lo}, {hi})")

        picked = None
        for time_ps, s_val, z_val in candidates:
            if all(abs(s_val - seed.s) >= min_s_gap for seed in seeds) and all(
                abs(time_ps - seed.time_ps) >= min_time_gap_ps for seed in seeds
            ):
                picked = Seed(walker_id, target, time_ps, s_val, z_val)
                break
        if picked is None:
            raise ValueError(
                f"could not select unique seed for target_s={target}; "
                f"relax min_s_gap/min_time_gap_ps only after inspecting candidates"
            )
        seeds.append(picked)
    return seeds


def assert_seed_suite(seeds: list[Seed]) -> None:
    if len(seeds) != N_WALKERS:
        raise AssertionError(f"expected {N_WALKERS} seeds, got {len(seeds)}")
    times = [seed.time_ps for seed in seeds]
    rounded_s = [round(seed.s, 4) for seed in seeds]
    if len(set(times)) != len(times):
        raise AssertionError("duplicate seed time detected")
    if len(set(rounded_s)) != len(rounded_s):
        raise AssertionError("duplicate rounded s detected")
    s_std = statistics.pstdev(seed.s for seed in seeds)
    if s_std < 2.0:
        raise AssertionError(f"seed s spread too small: std={s_std:.3f}")
    min_s_gap = min(
        abs(a.s - b.s)
        for i, a in enumerate(seeds)
        for b in seeds[i + 1:]
    )
    if min_s_gap < 0.25:
        raise AssertionError(f"seed s gap too small: min_gap={min_s_gap:.3f}")
    if any(seed.z >= 2.5 for seed in seeds):
        bad = [asdict(seed) for seed in seeds if seed.z >= 2.5]
        raise AssertionError(f"seed at or beyond upper wall: {bad}")


def gro_has_velocities(path: Path) -> bool:
    lines = path.read_text().splitlines()
    if int(lines[1].strip()) != N_ATOMS:
        raise AssertionError(f"{path} atom count mismatch: {lines[1]}")
    token_counts = [len(line.split()) for line in lines[2:12]]
    return any(count >= 9 for count in token_counts)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_mdp_files(walker_dir: Path, *, nvt_nsteps: int, metad_nsteps: int) -> None:
    (walker_dir / "em.mdp").write_text(
        f"""\
integrator              = steep
emtol                   = 1000.0
emstep                  = 0.01
nsteps                  = 1000

{COMMON_MD}
tcoupl                  = no
pcoupl                  = no
continuation            = no
gen_vel                 = no
"""
    )
    (walker_dir / "nvt.mdp").write_text(
        f"""\
integrator              = md
dt                      = 0.002
nsteps                  = {nvt_nsteps}

{COMMON_MD}
tcoupl                  = v-rescale
tc-grps                 = System
tau_t                   = 0.1
ref_t                   = 350
pcoupl                  = no
continuation            = no
gen_vel                 = yes
gen_temp                = 350
gen_seed                = -1
"""
    )
    (walker_dir / "metad.mdp").write_text(
        f"""\
integrator              = md
dt                      = 0.002
nsteps                  = {metad_nsteps}

{COMMON_MD}
tcoupl                  = v-rescale
tc-grps                 = System
tau_t                   = 0.1
ref_t                   = 350
pcoupl                  = no
continuation            = yes
gen_vel                 = no
"""
    )


def extract_snapshot(seed: Seed, out_gro: Path) -> None:
    cmd = [
        "gmx", "trjconv",
        "-s", str(PILOT / "metad.tpr"),
        "-f", str(PILOT / "metad.xtc"),
        "-o", str(out_gro),
        "-dump", f"{seed.time_ps:.1f}",
    ]
    proc = subprocess.run(
        cmd, input="0\n", text=True, capture_output=True, check=False
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"trjconv failed for walker_{seed.walker_id:02d} at {seed.time_ps} ps\n"
            f"STDOUT:\n{proc.stdout[-2000:]}\nSTDERR:\n{proc.stderr[-2000:]}"
        )


def write_bundle(args: argparse.Namespace, seeds: list[Seed]) -> None:
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "HILLS_DIR").mkdir(exist_ok=True)

    template = PLUMED_TEMPLATE.read_text()
    if template.count("__WALKERS_ID__") != 1:
        raise AssertionError("PLUMED template must contain exactly one __WALKERS_ID__")
    required = (
        "UNITS LENGTH=A ENERGY=kcal/mol",
        "ADAPTIVE=DIFF SIGMA=1000",
        "HEIGHT=0.15",
        "BIASFACTOR=10.0",
        "WALKERS_N=10",
        "UPPER_WALLS ARG=p1.zzz AT=2.5",
    )
    for literal in required:
        if literal not in template:
            raise AssertionError(f"PLUMED template missing {literal}")

    hashes: list[str] = []
    for seed in seeds:
        walker_dir = out_dir / f"walker_{seed.walker_id:02d}"
        walker_dir.mkdir(exist_ok=True)
        shutil.copy2(PILOT / "topol.top", walker_dir / "topol.top")
        shutil.copy2(PATH_SOURCE, walker_dir / "path_seqaligned_gromacs.pdb")
        write_mdp_files(
            walker_dir,
            nvt_nsteps=args.nvt_nsteps,
            metad_nsteps=args.metad_nsteps,
        )
        (walker_dir / "plumed.dat").write_text(
            template.replace("__WALKERS_ID__", str(seed.walker_id))
        )
        start_gro = walker_dir / "start.gro"
        if args.extract:
            extract_snapshot(seed, start_gro)
            if gro_has_velocities(start_gro):
                raise AssertionError(f"{start_gro} unexpectedly contains velocities")
            hashes.append(sha256(start_gro))
        (walker_dir / "provenance.txt").write_text(
            "\n".join(
                [
                    f"walker_id={seed.walker_id:02d}",
                    "source=initial_seqaligned/metad.xtc",
                    f"pilot_time_ps={seed.time_ps:.1f}",
                    f"pilot_s={seed.s:.4f}",
                    f"pilot_z={seed.z:.4f}",
                    "pipeline=EM_1000_steps_then_NVT_no_PLUMED_then_MetaD_PLUMED",
                    "note=start.gro is coordinate-only; nvt.mdp gen_vel=yes is required",
                ]
            )
            + "\n"
        )

    if hashes and len(set(hashes)) != len(hashes):
        raise AssertionError("duplicate start.gro coordinate hash detected")

    manifest = {
        "out_dir": str(out_dir),
        "pilot_colvar": str(PILOT / "COLVAR"),
        "extract": args.extract,
        "nvt_nsteps": args.nvt_nsteps,
        "metad_nsteps": args.metad_nsteps,
        "seeds": [asdict(seed) for seed in seeds],
        "s_std": statistics.pstdev(seed.s for seed in seeds),
        "min_pairwise_s_gap": min(
            abs(a.s - b.s)
            for i, a in enumerate(seeds)
            for b in seeds[i + 1:]
        ),
    }
    (out_dir / "seed_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with (out_dir / "seed_manifest.tsv").open("w") as handle:
        handle.write("walker_id\ttarget_s\ttime_ps\ts\tz\n")
        for seed in seeds:
            handle.write(
                f"{seed.walker_id:02d}\t{seed.target_s}\t{seed.time_ps:.1f}\t"
                f"{seed.s:.4f}\t{seed.z:.4f}\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--z-max", type=float, default=2.45)
    parser.add_argument("--min-s-gap", type=float, default=0.25)
    parser.add_argument("--min-time-gap-ps", type=float, default=100.0)
    parser.add_argument("--nvt-nsteps", type=int, default=1000)
    parser.add_argument("--metad-nsteps", type=int, default=1000)
    parser.add_argument("--extract", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    required_paths = [
        PILOT / "COLVAR",
        PILOT / "metad.tpr",
        PILOT / "metad.xtc",
        PILOT / "topol.top",
        PLUMED_TEMPLATE,
        PATH_SOURCE,
    ]
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(path)

    rows = parse_colvar(PILOT / "COLVAR")
    seeds = select_seeds(
        rows,
        z_max=args.z_max,
        min_s_gap=args.min_s_gap,
        min_time_gap_ps=args.min_time_gap_ps,
    )
    assert_seed_suite(seeds)

    print("walker_id target_s time_ps s z")
    for seed in seeds:
        print(
            f"{seed.walker_id:02d} {seed.target_s:2d} "
            f"{seed.time_ps:8.1f} {seed.s:7.4f} {seed.z:7.4f}"
        )
    print(f"s_std={statistics.pstdev(seed.s for seed in seeds):.4f}")
    print(
        "min_pairwise_s_gap="
        f"{min(abs(a.s-b.s) for i, a in enumerate(seeds) for b in seeds[i+1:]):.4f}"
    )

    if args.write:
        write_bundle(args, seeds)
        print(f"wrote validation bundle: {args.out_dir}")
    else:
        print("dry-run only; add --write to materialize files")


if __name__ == "__main__":
    main()
