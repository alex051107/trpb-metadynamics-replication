#!/usr/bin/env python3
"""Materialize an isolated v3 validation bundle on Longleaf.

This script does not submit Slurm jobs.  It selects 10 unique pilot frames,
asserts seed diversity, writes EM/NVT/production MDPs, and optionally extracts
coordinate-only start.gro files from the sequence-aligned pilot trajectory.

2026-04-25 SI-faithfulness patch (Codex R0/R0.5/R4 cross-audit):
  TARGETS widened from tuple(range(1, 11)) (= [1..10] integer) to
  numpy.linspace(1.0, max_s_observed, 10) so the 10 walker seeds cover
  the FULL pilot path (including C-region s>=10) per SI quote (Codex R0.5):
  "extracted ten snapshots covering conformational space".

2026-04-25 PM v2 + Codex R8 cleanup:
  Replaced tiered-z fallback with window-min-z (no ceiling).  PM directive:
  "选择尽可能广的 SR + 每一个 sr 选一个相对 Z 比较小的".  Codex R8 verified
  this is equivalent to v1 tiered output on current pilot data (every window
  already has low-z candidates) but is conceptually cleaner: lowest-z is a
  GEOMETRY-STABILITY heuristic (less off-path/wall stress at seed time),
  NOT an equilibrium proof.  Hard assertions retained: unique times,
  unique rounded s, s_std>=3.0, O/PC/C coverage, seed.z<2.5.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import statistics
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path


BASE = Path("/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23")
PILOT = BASE / "initial_seqaligned"
SEQ_WALKERS = BASE / "seqaligned_walkers"
PATH_SOURCE = BASE / "seqaligned_walkers_v2" / "walker_00" / "path_seqaligned_gromacs.pdb"
PLUMED_TEMPLATE = SEQ_WALKERS / "plumed_template.dat"
OUT_DEFAULT = BASE / "seqaligned_walkers_v3_validation"

N_WALKERS = 10
N_ATOMS = 39268

# Hard upper-wall guard: if any window-min-z candidate is at/above the production
# UPPER_WALLS AT=2.5, the seed itself is wall-stressed and the run will likely
# degrade — assertion in assert_seed_suite() rejects these.
Z_HARD_CAP = 2.5

SELECTION_RULE = "window_min_z"  # Codex R8: PM v2 — pick min(z) in [target-Δ/2, target+Δ/2)


@dataclass(frozen=True)
class Seed:
    walker_id: int
    target_s: float
    time_ps: float
    s: float
    z: float
    selection_rule: str = SELECTION_RULE
    candidates_in_window: int = 0


def compute_targets(max_s: float, n: int = N_WALKERS) -> tuple[float, ...]:
    """Return n target s-values uniformly spaced in [1.0, max_s].

    Replaces the legacy ``tuple(range(1, n+1))`` which truncated at s=10
    regardless of pilot max_s (Codex R0.5 SI-violation).
    """
    if max_s <= 1.0:
        raise ValueError(f"max_s={max_s} too small for widened TARGETS")
    if n < 2:
        raise ValueError("need at least 2 targets")
    step = (max_s - 1.0) / (n - 1)
    return tuple(round(1.0 + step * i, 4) for i in range(n))


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
    targets: tuple[float, ...],
    *,
    min_s_gap: float,
    min_time_gap_ps: float,
) -> list[Seed]:
    """Pick one seed per target via window-min-z (PM v2 / Codex R8).

    For each target window [target-Δ/2, target+Δ/2), gather ALL candidates
    (no z ceiling) and sort by (z, |s-target|, time).  Pick the first
    candidate that satisfies pairwise s-gap and time-gap uniqueness.

    Lowest-z is a GEOMETRY-STABILITY heuristic: it picks the frame closest
    to the supplied path at that s, hence less off-path/wall stress at the
    moment the seed is grabbed.  It is NOT proof of equilibrium — a frame
    with lowest z may still be a transient low-z crossing.  Hard cap
    seed.z < Z_HARD_CAP enforced in assert_seed_suite().
    """
    seeds: list[Seed] = []
    delta = (targets[-1] - targets[0]) / (len(targets) - 1) if len(targets) > 1 else 1.0
    half_window = delta / 2.0
    for walker_id, target in enumerate(targets):
        lo = max(0.0, target - half_window)
        hi = target + half_window if walker_id < len(targets) - 1 else float("inf")

        candidates = [row for row in rows if lo <= row[1] < hi]
        if not candidates:
            raise ValueError(
                f"no COLVAR rows in window for target_s={target} [{lo}, {hi})"
            )
        candidates.sort(key=lambda row: (row[2], abs(row[1] - target), row[0]))

        picked: Seed | None = None
        for time_ps, s_val, z_val in candidates:
            if all(abs(s_val - seed.s) >= min_s_gap for seed in seeds) and all(
                abs(time_ps - seed.time_ps) >= min_time_gap_ps for seed in seeds
            ):
                picked = Seed(
                    walker_id=walker_id,
                    target_s=float(target),
                    time_ps=time_ps,
                    s=s_val,
                    z=z_val,
                    selection_rule=SELECTION_RULE,
                    candidates_in_window=len(candidates),
                )
                break
        if picked is None:
            raise ValueError(
                f"could not select unique seed for target_s={target} in [{lo}, {hi})"
                f" — {len(candidates)} candidates, all violated s-gap/time-gap"
            )
        seeds.append(picked)
    return seeds


def assert_seed_suite(seeds: list[Seed], *, min_s_gap_floor: float) -> None:
    if len(seeds) != N_WALKERS:
        raise AssertionError(f"expected {N_WALKERS} seeds, got {len(seeds)}")
    times = [seed.time_ps for seed in seeds]
    rounded_s = [round(seed.s, 4) for seed in seeds]
    if len(set(times)) != len(times):
        raise AssertionError("duplicate seed time detected")
    if len(set(rounded_s)) != len(rounded_s):
        raise AssertionError("duplicate rounded s detected")
    s_std = statistics.pstdev(seed.s for seed in seeds)
    # Widened TARGETS (linspace 1..max_s where max_s>=10) → s_std should be >=3.0
    if s_std < 3.0:
        raise AssertionError(f"seed s spread too small for widened TARGETS: std={s_std:.3f}")
    min_pairwise = min(
        abs(a.s - b.s)
        for i, a in enumerate(seeds)
        for b in seeds[i + 1:]
    )
    if min_pairwise < min_s_gap_floor:
        raise AssertionError(
            f"seed pairwise s gap too small: min_pairwise={min_pairwise:.3f}"
            f" < floor {min_s_gap_floor:.3f}"
        )
    if any(seed.z >= Z_HARD_CAP for seed in seeds):
        bad = [asdict(seed) for seed in seeds if seed.z >= Z_HARD_CAP]
        raise AssertionError(f"seed at or beyond upper wall (z>={Z_HARD_CAP}): {bad}")
    # Coverage: at least one seed in O (s<=2), one in PC (4<=s<=6), one in C (s>=10)
    s_values = [seed.s for seed in seeds]
    if not any(s <= 2.0 for s in s_values):
        raise AssertionError(f"no seed in O-region (s<=2): {s_values}")
    if not any(4.0 <= s <= 6.0 for s in s_values):
        raise AssertionError(f"no seed in PC-region (4<=s<=6): {s_values}")
    if not any(s >= 10.0 for s in s_values):
        raise AssertionError(f"no seed in C-region (s>=10): {s_values}")


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
        "targets": list(args.targets) if hasattr(args, "targets") and args.targets else None,
        "max_s_observed": args.max_s,
        "seeds": [asdict(seed) for seed in seeds],
        "s_std": statistics.pstdev(seed.s for seed in seeds),
        "min_pairwise_s_gap": min(
            abs(a.s - b.s)
            for i, a in enumerate(seeds)
            for b in seeds[i + 1:]
        ),
        "selection_rule": SELECTION_RULE,
        "z_hard_cap": Z_HARD_CAP,
        "candidates_in_window_per_walker": {
            seed.walker_id: seed.candidates_in_window for seed in seeds
        },
    }
    (out_dir / "seed_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with (out_dir / "seed_manifest.tsv").open("w") as handle:
        handle.write("walker_id\ttarget_s\ttime_ps\ts\tz\trule\tcandidates_in_window\n")
        for seed in seeds:
            handle.write(
                f"{seed.walker_id:02d}\t{seed.target_s:.4f}\t{seed.time_ps:.1f}\t"
                f"{seed.s:.4f}\t{seed.z:.4f}\t{seed.selection_rule}\t"
                f"{seed.candidates_in_window}\n"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    parser.add_argument("--max-s", type=float, default=None,
                        help="max_s for TARGETS=linspace(1, max_s, 10); auto-detect from COLVAR if omitted")
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

    # Auto-detect max_s if not provided (Codex R0.5 widening per SI-faithful TARGETS)
    if args.max_s is None:
        args.max_s = max(row[1] for row in rows)
        print(f"[INFO] auto-detected max_s={args.max_s:.4f} from {len(rows)} COLVAR rows")
    targets = compute_targets(args.max_s, n=N_WALKERS)
    args.targets = targets
    delta = (targets[-1] - targets[0]) / (len(targets) - 1)
    min_s_gap = delta * 0.5
    print(f"[INFO] TARGETS = {targets}")
    print(f"[INFO] window Δ = {delta:.4f}, half-window = {delta/2:.4f}, min_s_gap = {min_s_gap:.4f}")
    print(f"[INFO] selection_rule={SELECTION_RULE}, z_hard_cap={Z_HARD_CAP}")

    seeds = select_seeds(
        rows,
        targets,
        min_s_gap=min_s_gap,
        min_time_gap_ps=args.min_time_gap_ps,
    )
    assert_seed_suite(seeds, min_s_gap_floor=min_s_gap * 0.9)

    print("walker_id target_s time_ps s z rule candidates_in_window")
    for seed in seeds:
        print(
            f"{seed.walker_id:02d} {seed.target_s:7.4f} "
            f"{seed.time_ps:8.1f} {seed.s:7.4f} {seed.z:7.4f} "
            f"{seed.selection_rule} {seed.candidates_in_window}"
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
