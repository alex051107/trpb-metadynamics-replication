#!/usr/bin/env python3
"""Compare two COLVAR_proj outputs (Ain baseline vs Aex1 pilot) and emit the
4 readouts ChatGPT Pro specified on 2026-04-23:

    1. median / IQR / p95 / max for s
    2. median / IQR / p95 for z
    3. fraction of frames with s > 1.5 and s > 2.0
    4. occupied-bin count in a fixed (s, z) grid

Prints a Markdown table (for PR comments) and a one-line pass/fail verdict
per ChatGPT Pro's operational rules:

    - chemistry prior strengthened if Aex1
        p95(s) ≥ Ain p95(s) + 0.5  OR
        Aex1 (s,z) occupied-bin area ≥ 2 × Ain area
    - geometry prior strengthened if
        |median_s_Aex1 - median_s_Ain| small AND
        IQR_s ratio within 25% AND
        |p95(s)_Aex1 - p95(s)_Ain| < 0.3
    - mixed / undecided otherwise -> need 10 ns Aex1 MetaD

Usage:
    python compare_projections.py ain.colvar aex1.colvar [--grid-ds 0.1] \\
        [--grid-dz 0.01] [--json out.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple


DEFAULT_GRID_DS = 0.1
DEFAULT_GRID_DZ = 0.01

P95_CHEMISTRY_DELTA = 0.5
AREA_CHEMISTRY_RATIO = 2.0
MEDIAN_GEOM_DELTA = 0.2
IQR_GEOM_RATIO_MAX = 1.25
P95_GEOM_DELTA_MAX = 0.3


def parse_colvar(path: Path) -> Tuple[List[float], List[float], str]:
    s_vals: List[float] = []
    z_vals: List[float] = []
    provenance = ""
    with path.open() as fh:
        for line in fh:
            if line.startswith("# provenance:"):
                provenance = line[len("# provenance:"):].strip()
                continue
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                s_vals.append(float(parts[1]))
                z_vals.append(float(parts[2]))
            except ValueError:
                continue
    assert len(s_vals) == len(z_vals)
    assert len(s_vals) > 0, f"No data rows parsed from {path}"
    return s_vals, z_vals, provenance


def quantile(xs: List[float], q: float) -> float:
    assert 0.0 <= q <= 1.0
    sorted_xs = sorted(xs)
    if len(sorted_xs) == 1:
        return sorted_xs[0]
    pos = q * (len(sorted_xs) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_xs[lo]
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


def stats(xs: List[float]) -> Dict[str, float]:
    return {
        "n": len(xs),
        "median": quantile(xs, 0.5),
        "q25": quantile(xs, 0.25),
        "q75": quantile(xs, 0.75),
        "iqr": quantile(xs, 0.75) - quantile(xs, 0.25),
        "p95": quantile(xs, 0.95),
        "min": min(xs),
        "max": max(xs),
    }


def fraction_above(xs: List[float], threshold: float) -> float:
    return sum(1 for x in xs if x > threshold) / len(xs)


def occupied_bins(s_vals: List[float], z_vals: List[float],
                  ds: float, dz: float) -> int:
    bins = set()
    for s, z in zip(s_vals, z_vals):
        bi = int(math.floor(s / ds))
        bj = int(math.floor(z / dz))
        bins.add((bi, bj))
    return len(bins)


def analyze(path: Path, ds: float, dz: float) -> Dict:
    s_vals, z_vals, prov = parse_colvar(path)
    return {
        "source": str(path),
        "provenance": prov,
        "n_frames": len(s_vals),
        "s": stats(s_vals),
        "z": stats(z_vals),
        "frac_s_gt_1p5": fraction_above(s_vals, 1.5),
        "frac_s_gt_2p0": fraction_above(s_vals, 2.0),
        "occupied_bins": occupied_bins(s_vals, z_vals, ds, dz),
        "grid_ds": ds,
        "grid_dz": dz,
    }


def verdict(ain: Dict, aex1: Dict) -> Tuple[str, List[str]]:
    """Return (verdict_tag, rationale_lines)."""
    reasons: List[str] = []
    chemistry_signal = False
    geometry_signal = False

    p95_delta = aex1["s"]["p95"] - ain["s"]["p95"]
    reasons.append(
        f"p95(s) Aex1 - Ain = {p95_delta:+.3f} "
        f"(chemistry threshold: >= +{P95_CHEMISTRY_DELTA:.2f})"
    )
    if p95_delta >= P95_CHEMISTRY_DELTA:
        chemistry_signal = True

    area_ratio = aex1["occupied_bins"] / max(ain["occupied_bins"], 1)
    reasons.append(
        f"occupied-bin ratio Aex1/Ain = {area_ratio:.2f} "
        f"(chemistry threshold: >= {AREA_CHEMISTRY_RATIO:.1f})"
    )
    if area_ratio >= AREA_CHEMISTRY_RATIO:
        chemistry_signal = True

    median_delta = abs(aex1["s"]["median"] - ain["s"]["median"])
    iqr_ratio = aex1["s"]["iqr"] / max(ain["s"]["iqr"], 1e-6)
    reasons.append(
        f"|median_s delta| = {median_delta:.3f} "
        f"(geometry threshold: < {MEDIAN_GEOM_DELTA:.2f})"
    )
    reasons.append(
        f"IQR_s ratio Aex1/Ain = {iqr_ratio:.2f} "
        f"(geometry threshold: {1.0 / IQR_GEOM_RATIO_MAX:.2f}..{IQR_GEOM_RATIO_MAX:.2f})"
    )
    reasons.append(
        f"|p95(s) delta| = {abs(p95_delta):.3f} "
        f"(geometry threshold: < {P95_GEOM_DELTA_MAX:.2f})"
    )
    if (
        median_delta < MEDIAN_GEOM_DELTA
        and 1.0 / IQR_GEOM_RATIO_MAX <= iqr_ratio <= IQR_GEOM_RATIO_MAX
        and abs(p95_delta) < P95_GEOM_DELTA_MAX
    ):
        geometry_signal = True

    if chemistry_signal and geometry_signal:
        tag = "ambiguous"
    elif chemistry_signal:
        tag = "chemistry-prior-strengthened"
    elif geometry_signal:
        tag = "geometry-prior-strengthened"
    else:
        tag = "no-clear-signal"
    return tag, reasons


def fmt_stats(row: Dict) -> str:
    s = row["s"]
    z = row["z"]
    return (
        f"n={row['n_frames']}  "
        f"s: median={s['median']:.3f} IQR={s['iqr']:.3f} p95={s['p95']:.3f} max={s['max']:.3f}  "
        f"z: median={z['median']:.4f} IQR={z['iqr']:.4f} p95={z['p95']:.4f}  "
        f"frac(s>1.5)={row['frac_s_gt_1p5']:.2%}  "
        f"frac(s>2.0)={row['frac_s_gt_2p0']:.2%}  "
        f"occupied_bins={row['occupied_bins']}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("ain_colvar", type=Path)
    ap.add_argument("aex1_colvar", type=Path)
    ap.add_argument("--grid-ds", type=float, default=DEFAULT_GRID_DS)
    ap.add_argument("--grid-dz", type=float, default=DEFAULT_GRID_DZ)
    ap.add_argument("--json", type=Path, help="Write structured output here")
    args = ap.parse_args()

    ain = analyze(args.ain_colvar, args.grid_ds, args.grid_dz)
    aex1 = analyze(args.aex1_colvar, args.grid_ds, args.grid_dz)
    tag, reasons = verdict(ain, aex1)

    print("## Path projection comparison\n")
    print(f"- Ain provenance : {ain['provenance']}")
    print(f"- Aex1 provenance: {aex1['provenance']}")
    print(f"- grid_ds={args.grid_ds} grid_dz={args.grid_dz}\n")
    print("| side | stats |")
    print("|---|---|")
    print(f"| Ain  | {fmt_stats(ain)} |")
    print(f"| Aex1 | {fmt_stats(aex1)} |\n")
    print(f"**Verdict**: {tag}\n")
    for r in reasons:
        print(f"- {r}")

    if args.json:
        args.json.write_text(json.dumps({
            "ain": ain,
            "aex1": aex1,
            "verdict": tag,
            "rationale": reasons,
        }, indent=2))
        print(f"\n[json] {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
