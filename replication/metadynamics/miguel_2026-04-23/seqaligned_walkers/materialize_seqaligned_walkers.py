"""Materialize 10-walker production on sequence-aligned path.

Designed to run on Longleaf (needs gmx in PATH + AnimaLab tree).

For each walker_NN (NN=00..09):
  1. Pick 10 CV-diverse snapshots from Initial MetaD pilot's COLVAR via
     compute_targets()/select_seeds() — same algorithm as
     materialize_v3_validation.py — and extract corresponding frames from
     pilot's metad.xtc via gmx trjconv → start.gro
  2. Copy path_seqaligned_gromacs.pdb + metad.mdp + topol.top
  3. Substitute WALKERS_ID=NN into plumed_template.dat → plumed.dat
  4. Build metad.tpr via gmx grompp
  5. Write provenance.txt

Shared HILLS_DIR/ at the parent level; all 10 walkers sync via
WALKERS_RSTRIDE=3000 (= 6 ps).

2026-04-25 SI-faithfulness rewrite (Codex R0/R0.5/R4 cross-audit):
  PRIOR BEHAVIOR (NON-SI, root cause of v1 homogeneous-start scancel):
    seeds extracted from 500 ns conventional MD trajectory at equidistant
    t = (walker_id+1)*50 ns = {50, 100, ..., 500} ns. cMD samples only the
    O-basin (no MetaD bias to push beyond), so all 10 seeds projected to
    s ≈ 1 — homogeneous start.
  CURRENT BEHAVIOR (SI-faithful per Codex R0.5 quote of SI p.S4
    "extracted ten snapshots covering conformational space"):
    seeds picked from Initial MetaD pilot's COLVAR via select_seeds() with
    TARGETS = linspace(1.0, max_s_observed, 10) covering O→PC→C path.
    Tiered z-fallback handles sparse high-s windows.

Pre-flight assertions:
- template has exactly one __WALKERS_ID__ placeholder
- path_seqaligned_gromacs.pdb has 15 MODELs × 112 atoms
- Initial pilot COLVAR + metad.xtc + topol.top all exist on Longleaf
- 10 selected seeds cover O (s≤2) + PC (4≤s≤6) + C (s≥10) regions
"""

import argparse
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "plumed_template.dat"
PATH_PDB = HERE.parent.parent / "path_seqaligned" / "path_seqaligned_gromacs.pdb"

# Longleaf defaults — Initial MetaD pilot is the seed source per SI protocol.
# cMD trajectory is NOT used for seed extraction (Codex R0.5 NON-SI flag).
DEFAULT_PILOT_DIR = Path(
    "/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/initial_seqaligned"
)
DEFAULT_MDP = DEFAULT_PILOT_DIR / "metad.mdp"
DEFAULT_TOPOL = DEFAULT_PILOT_DIR / "topol.top"

HILLS_DIR = HERE / "HILLS_DIR"

UNIT_LITERAL = "UNITS LENGTH=A ENERGY=kcal/mol"
SCHEME_LITERAL = "ADAPTIVE=DIFF SIGMA=1000"
LAMBDA_LITERAL = "LAMBDA=100.79"  # post 2026-04-25 SI-audit (Branduardi self-computed)
PATH_REF_LITERAL = "REFERENCE=path_seqaligned_gromacs.pdb"
WALKERS_N_LITERAL = "WALKERS_N=10"
HEIGHT_LITERAL = "HEIGHT=0.15"
BIASFACTOR_LITERAL = "BIASFACTOR=10.0"

N_WALKERS = 10
N_ATOMS = 39268

# Z-fallback tiers (Codex R4): identical to materialize_v3_validation.py — keep in sync.
Z_TIERS = (1.0, 1.5, 2.0, 2.45)


# -----------------------------------------------------------------------------
# Seed selection (mirrors materialize_v3_validation.py:select_seeds — KEEP IN SYNC)
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Seed:
    walker_id: int
    target_s: float
    time_ps: float
    s: float
    z: float
    z_tier_used: float
    candidates_at_strict_z: int = 0


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


def compute_targets(max_s: float, n: int = N_WALKERS) -> tuple[float, ...]:
    if max_s <= 1.0:
        raise ValueError(f"max_s={max_s} too small for widened TARGETS")
    if n < 2:
        raise ValueError("need at least 2 targets")
    step = (max_s - 1.0) / (n - 1)
    return tuple(round(1.0 + step * i, 4) for i in range(n))


def select_seeds(
    rows: list[tuple[float, float, float]],
    targets: tuple[float, ...],
    *,
    min_s_gap: float,
    min_time_gap_ps: float,
    z_tiers: tuple[float, ...] = Z_TIERS,
) -> list[Seed]:
    seeds: list[Seed] = []
    delta = (targets[-1] - targets[0]) / (len(targets) - 1) if len(targets) > 1 else 1.0
    half_window = delta / 2.0
    for walker_id, target in enumerate(targets):
        lo = max(0.0, target - half_window)
        hi = target + half_window if walker_id < len(targets) - 1 else float("inf")
        strict_z = z_tiers[0]
        strict_count = sum(
            1 for row in rows if lo <= row[1] < hi and row[2] <= strict_z
        )
        picked: Seed | None = None
        for tier in z_tiers:
            candidates = [
                row for row in rows
                if lo <= row[1] < hi and row[2] <= tier
            ]
            candidates.sort(key=lambda row: (row[2], abs(row[1] - target), row[0]))
            if not candidates:
                continue
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
                        z_tier_used=tier,
                        candidates_at_strict_z=strict_count,
                    )
                    break
            if picked is not None:
                break
        if picked is None:
            raise ValueError(
                f"could not select unique seed for target_s={target} in [{lo}, {hi})"
                f" even after tiered z-fallback through {z_tiers}"
            )
        seeds.append(picked)
    return seeds


def assert_seed_suite(seeds: list[Seed], *, min_s_gap_floor: float) -> None:
    assert len(seeds) == N_WALKERS, f"expected {N_WALKERS} seeds, got {len(seeds)}"
    times = [seed.time_ps for seed in seeds]
    rounded_s = [round(seed.s, 4) for seed in seeds]
    assert len(set(times)) == len(times), "duplicate seed time"
    assert len(set(rounded_s)) == len(rounded_s), "duplicate rounded s"
    s_std = statistics.pstdev(seed.s for seed in seeds)
    assert s_std >= 3.0, f"seed s spread too small: std={s_std:.3f}"
    min_pairwise = min(
        abs(a.s - b.s)
        for i, a in enumerate(seeds) for b in seeds[i + 1:]
    )
    assert min_pairwise >= min_s_gap_floor, (
        f"seed pairwise s gap too small: {min_pairwise:.3f} < floor {min_s_gap_floor:.3f}"
    )
    assert not any(seed.z >= 2.5 for seed in seeds), "seed at or beyond upper wall"
    s_values = [seed.s for seed in seeds]
    assert any(s <= 2.0 for s in s_values), f"no seed in O-region: {s_values}"
    assert any(4.0 <= s <= 6.0 for s in s_values), f"no seed in PC-region: {s_values}"
    assert any(s >= 10.0 for s in s_values), f"no seed in C-region: {s_values}"


# -----------------------------------------------------------------------------
# Standard production materializer pieces
# -----------------------------------------------------------------------------

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


def extract_snapshot(pilot_tpr: Path, pilot_xtc: Path, time_ps: float,
                     out_gro: Path) -> None:
    """Extract single frame at t = time_ps from Initial MetaD pilot trajectory.

    This is the SI-faithful seed source (Initial MetaD COLVAR + metad.xtc),
    NOT the legacy cMD-trajectory equidistant extraction.
    """
    proc = subprocess.run(
        ["gmx", "trjconv", "-s", str(pilot_tpr), "-f", str(pilot_xtc),
         "-o", str(out_gro), "-dump", f"{time_ps:.1f}"],
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize_walker(seed: Seed, template_text: str, args, commit: str) -> dict:
    walker_dir = HERE / f"walker_{seed.walker_id:02d}"
    walker_dir.mkdir(exist_ok=True)
    start_gro = walker_dir / "start.gro"
    if not args.skip_snapshot:
        pilot_tpr = args.pilot_dir / "metad.tpr"
        pilot_xtc = args.pilot_dir / "metad.xtc"
        if pilot_tpr.exists() and pilot_xtc.exists():
            extract_snapshot(pilot_tpr, pilot_xtc, seed.time_ps, start_gro)
        else:
            print(f"WARNING: pilot trajectory not found at {args.pilot_dir}")
            print(f"  walker_{seed.walker_id:02d} start.gro must be provided manually")
    shutil.copy(PATH_PDB, walker_dir / "path_seqaligned_gromacs.pdb")
    if args.mdp.exists():
        shutil.copy(args.mdp, walker_dir / "metad.mdp")
    (walker_dir / "plumed.dat").write_text(substitute(template_text, seed.walker_id))
    if not args.skip_grompp:
        if args.topol.exists() and (walker_dir / "metad.mdp").exists() and start_gro.exists():
            try:
                grompp(walker_dir, args.mdp, start_gro, args.topol)
            except RuntimeError as e:
                print(f"  grompp failed for walker_{seed.walker_id:02d}: {e}")
    provenance = [
        f"walker_id={seed.walker_id:02d}",
        "source=initial_seqaligned/COLVAR + initial_seqaligned/metad.xtc",
        "seeds_source=initial_seqaligned_COLVAR",  # NOT cMD_500ns_xtc — SI-faithful per Codex R0.5
        "contract=PRIMARY_10WALKER (SI-literal HEIGHT=0.15 BIASFACTOR=10)",
        "UNITS=LENGTH_A_ENERGY_kcal_mol",
        "LAMBDA=100.79_Ainv2 (Branduardi 2.3/<MSD_adj> on seq-aligned path; post 2026-04-25 SI-audit)",
        "ADAPTIVE=DIFF SIGMA=1000_steps",
        "HEIGHT=0.15_kcal_per_mol",
        "BIASFACTOR=10.0",
        "TEMP=350.0",
        "WALKERS_N=10 shared_HILLS_DIR=../HILLS_DIR WALKERS_RSTRIDE=3000",
        "UPPER_WALLS_p1.zzz_at_2.5A_kappa_800",
        "WHOLEMOLECULES_ENTITY0=1-39268",
        f"target_s={seed.target_s:.4f}",
        f"pilot_time_ps={seed.time_ps:.1f}",
        f"pilot_s={seed.s:.4f}",
        f"pilot_z={seed.z:.4f}",
        f"z_tier_used={seed.z_tier_used:.2f}",
        f"candidates_at_strict_z={seed.candidates_at_strict_z}",
        f"plan_commit_hash={commit}",
        "path_pdb=path_seqaligned_gromacs.pdb (NW +5 offset, FP-034 corrected)",
    ]
    (walker_dir / "provenance.txt").write_text("\n".join(provenance) + "\n")
    print(
        f"[walker_{seed.walker_id:02d}] target={seed.target_s:.2f} "
        f"t={seed.time_ps:.0f}ps s={seed.s:.3f} z={seed.z:.3f} "
        f"tier={seed.z_tier_used} -> {walker_dir}"
    )
    coord_hash = sha256(start_gro) if start_gro.exists() else "MISSING"
    return {
        "id": seed.walker_id,
        "dir": str(walker_dir),
        "target_s": seed.target_s,
        "pilot_time_ps": seed.time_ps,
        "pilot_s": seed.s,
        "pilot_z": seed.z,
        "z_tier_used": seed.z_tier_used,
        "candidates_at_strict_z": seed.candidates_at_strict_z,
        "start_gro_sha256": coord_hash,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=int, help="walker id (0..9) only")
    ap.add_argument("--pilot-dir", type=Path, default=DEFAULT_PILOT_DIR,
                    help="Initial MetaD pilot dir (COLVAR + metad.tpr + metad.xtc)")
    ap.add_argument("--max-s", type=float, default=None,
                    help="max_s for TARGETS=linspace(1, max_s, 10); auto-detect from COLVAR if omitted")
    ap.add_argument("--min-time-gap-ps", type=float, default=100.0)
    ap.add_argument("--mdp", type=Path, default=DEFAULT_MDP, help="MetaD mdp")
    ap.add_argument("--topol", type=Path, default=DEFAULT_TOPOL, help="topology .top")
    ap.add_argument("--skip-snapshot", action="store_true",
                    help="don't extract snapshots (if already done)")
    ap.add_argument("--skip-grompp", action="store_true",
                    help="don't run grompp (if gmx unavailable)")
    args = ap.parse_args()

    template_text = TEMPLATE.read_text()
    verify_template(template_text)
    verify_path_pdb(PATH_PDB)

    colvar_path = args.pilot_dir / "COLVAR"
    assert colvar_path.exists(), f"pilot COLVAR not found: {colvar_path}"
    rows = parse_colvar(colvar_path)
    if args.max_s is None:
        args.max_s = max(row[1] for row in rows)
        print(f"[INFO] auto-detected max_s={args.max_s:.4f} from {len(rows)} COLVAR rows")
    targets = compute_targets(args.max_s, n=N_WALKERS)
    delta = (targets[-1] - targets[0]) / (len(targets) - 1)
    min_s_gap = delta * 0.5
    print(f"[INFO] TARGETS = {targets}")
    print(f"[INFO] window Δ = {delta:.4f}, half-window = {delta/2:.4f}, min_s_gap = {min_s_gap:.4f}")

    seeds = select_seeds(
        rows, targets,
        min_s_gap=min_s_gap,
        min_time_gap_ps=args.min_time_gap_ps,
    )
    assert_seed_suite(seeds, min_s_gap_floor=min_s_gap * 0.9)

    HILLS_DIR.mkdir(exist_ok=True)
    commit = git_head()
    if args.only is not None:
        assert 0 <= args.only < N_WALKERS
        seeds_to_run = [s for s in seeds if s.walker_id == args.only]
    else:
        seeds_to_run = seeds

    summary = [materialize_walker(s, template_text, args, commit) for s in seeds_to_run]
    (HERE / "walkers_manifest.json").write_text(json.dumps({
        "plan_commit": commit,
        "pilot_dir": str(args.pilot_dir),
        "max_s_observed": args.max_s,
        "targets": list(targets),
        "min_s_gap": min_s_gap,
        "z_tiers": list(Z_TIERS),
        "seeds_source": "initial_seqaligned_COLVAR",
        "lambda": "100.79 (Branduardi self-computed, post 2026-04-25 SI-audit)",
        "walkers": summary,
    }, indent=2) + "\n")
    print(f"\nwrote {len(summary)} walkers, plan_commit={commit}")
    print(f"shared HILLS dir: {HILLS_DIR}")
    print(f"\nnext: sbatch submit_array.sh")


if __name__ == "__main__":
    main()
