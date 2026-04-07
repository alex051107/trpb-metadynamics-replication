#!/usr/bin/env python3
"""
Assess Path-CV FES convergence from a time series of blockwise fes.dat files.

The script expects multiple FES snapshots, e.g.

  fes_050ns.dat
  fes_100ns.dat
  fes_150ns.dat
  ...

For each file it computes:
  - O-basin minimum
  - C-basin minimum
  - Delta G(C-O)

It then performs non-overlapping block averaging on Delta G(C-O) to determine
whether the late-time estimates have plateaued.
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = str(Path(tempfile.gettempdir()) / "matplotlib-codex")
if "XDG_CACHE_HOME" not in os.environ:
    os.environ["XDG_CACHE_HOME"] = str(Path(tempfile.gettempdir()) / "xdg-cache-codex")

import matplotlib.pyplot as plt
import numpy as np

import analyze_fes as fes_tools


@dataclass
class TimepointEstimate:
    fes_path: str
    time_ns: float
    delta_g_oc_kcal_mol: float
    c_minus_lowest_opc_kcal_mol: float


@dataclass
class BlockAverage:
    block_index: int
    start_time_ns: float
    end_time_ns: float
    mean_delta_g_oc_kcal_mol: float
    std_delta_g_oc_kcal_mol: float
    count: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check FES convergence from blockwise fes.dat files.")
    parser.add_argument(
        "--fes-glob",
        required=True,
        help="Glob pattern for FES files, e.g. 'analysis/fes_blocks/fes_*ns.dat'",
    )
    parser.add_argument(
        "--times-ns",
        default=None,
        help="Comma-separated times matching the sorted FES files; otherwise parsed from filenames",
    )
    parser.add_argument(
        "--blocks-per-average",
        type=int,
        default=2,
        help="Number of consecutive FES files per block average",
    )
    parser.add_argument(
        "--plateau-window-blocks",
        type=int,
        default=2,
        help="Number of trailing block means used for the plateau assessment",
    )
    parser.add_argument(
        "--plateau-tolerance-kcal",
        type=float,
        default=2.0,
        help="Maximum allowed spread among trailing block means for convergence",
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="Output prefix for the convergence plot/report",
    )
    return parser.parse_args()


def parse_time_from_filename(path: Path) -> float:
    matches = re.findall(r"(\d+(?:\.\d+)?)", path.stem)
    assert matches, (
        f"Could not infer time from filename '{path.name}'. Provide --times-ns explicitly."
    )
    value = float(matches[-1])
    assert math.isfinite(value), f"Parsed non-finite time from {path.name}: {value}"
    return value


def resolve_time_axis(fes_paths: list[Path], times_ns_raw: str | None) -> list[float]:
    if times_ns_raw is None:
        times = [parse_time_from_filename(path) for path in fes_paths]
    else:
        times = [float(item.strip()) for item in times_ns_raw.split(",") if item.strip()]
        assert len(times) == len(fes_paths), (
            f"Received {len(times)} time values for {len(fes_paths)} FES files"
        )
    assert all(math.isfinite(time_ns) for time_ns in times), "Time axis contains non-finite values"
    return times


def load_timepoint_estimates(fes_paths: list[Path], times_ns: list[float]) -> list[TimepointEstimate]:
    estimates: list[TimepointEstimate] = []
    for path, time_ns in zip(fes_paths, times_ns):
        analysis = fes_tools.run_analysis(
            path,
            reference_c_minus_opc_kcal=5.0,
            reference_pc_to_c_barrier_kcal=6.0,
            comparison_tolerance_kcal=2.0,
        )
        estimate = TimepointEstimate(
            fes_path=str(path),
            time_ns=float(time_ns),
            delta_g_oc_kcal_mol=float(analysis["delta_g_kcal_mol"]["C_minus_O"]),
            c_minus_lowest_opc_kcal_mol=float(analysis["delta_g_kcal_mol"]["C_minus_lowest_O_PC"]),
        )
        assert -20.0 <= estimate.delta_g_oc_kcal_mol <= 20.0, (
            f"Delta G(C-O) at {time_ns:.3f} ns is outside a plausible range: "
            f"{estimate.delta_g_oc_kcal_mol:.3f} kcal/mol"
        )
        estimates.append(estimate)
    return estimates


def compute_nonoverlapping_block_averages(
    estimates: list[TimepointEstimate],
    blocks_per_average: int,
) -> list[BlockAverage]:
    assert blocks_per_average >= 1, "blocks_per_average must be >= 1"
    block_averages: list[BlockAverage] = []
    for start in range(0, len(estimates), blocks_per_average):
        chunk = estimates[start : start + blocks_per_average]
        if len(chunk) < blocks_per_average:
            break
        values = np.array([entry.delta_g_oc_kcal_mol for entry in chunk], dtype=float)
        block = BlockAverage(
            block_index=len(block_averages),
            start_time_ns=chunk[0].time_ns,
            end_time_ns=chunk[-1].time_ns,
            mean_delta_g_oc_kcal_mol=float(np.mean(values)),
            std_delta_g_oc_kcal_mol=float(np.std(values, ddof=0)),
            count=len(chunk),
        )
        assert 0.0 <= block.std_delta_g_oc_kcal_mol <= 20.0, (
            f"Block std outside expected range: {block.std_delta_g_oc_kcal_mol:.3f} kcal/mol"
        )
        block_averages.append(block)
    assert block_averages, "No complete blocks were produced; reduce --blocks-per-average"
    return block_averages


def assess_plateau(
    block_averages: list[BlockAverage],
    plateau_window_blocks: int,
    plateau_tolerance_kcal: float,
) -> dict[str, float | bool]:
    assert plateau_window_blocks >= 1, "plateau_window_blocks must be >= 1"
    trailing = block_averages[-plateau_window_blocks:]
    means = np.array([block.mean_delta_g_oc_kcal_mol for block in trailing], dtype=float)
    spread = float(np.max(means) - np.min(means))
    return {
        "plateau_window_blocks": len(trailing),
        "plateau_spread_kcal_mol": spread,
        "plateau_tolerance_kcal_mol": plateau_tolerance_kcal,
        "converged": spread <= plateau_tolerance_kcal,
    }


def plot_convergence(
    estimates: list[TimepointEstimate],
    block_averages: list[BlockAverage],
    output_png: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(10, 6), dpi=150)

    times = [entry.time_ns for entry in estimates]
    values = [entry.delta_g_oc_kcal_mol for entry in estimates]
    ax.plot(times, values, marker="o", color="#1f77b4", linewidth=1.5, label="Delta G(C-O)")

    block_centers = [(block.start_time_ns + block.end_time_ns) / 2.0 for block in block_averages]
    block_means = [block.mean_delta_g_oc_kcal_mol for block in block_averages]
    block_stds = [block.std_delta_g_oc_kcal_mol for block in block_averages]
    ax.errorbar(
        block_centers,
        block_means,
        yerr=block_stds,
        fmt="s",
        color="#d62728",
        capsize=4,
        linewidth=1.2,
        label="Block averages",
    )

    ax.set_xlabel("Time (ns)")
    ax.set_ylabel("Delta G(C-O) (kcal/mol)")
    ax.set_title("FES convergence: Delta G(C-O) vs time")
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_png, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    fes_paths = [Path(path).resolve() for path in sorted(glob.glob(args.fes_glob))]
    assert fes_paths, f"No FES files matched pattern: {args.fes_glob}"

    times_ns = resolve_time_axis(fes_paths, args.times_ns)
    estimates = load_timepoint_estimates(fes_paths, times_ns)
    block_averages = compute_nonoverlapping_block_averages(estimates, args.blocks_per_average)
    plateau = assess_plateau(
        block_averages,
        args.plateau_window_blocks,
        args.plateau_tolerance_kcal,
    )

    output_prefix = (
        Path(args.output_prefix).resolve()
        if args.output_prefix
        else fes_paths[0].with_name("fes_convergence")
    )
    output_png = output_prefix.with_name(output_prefix.name + "_plot.png")
    output_json = output_prefix.with_name(output_prefix.name + "_report.json")

    print("=" * 72)
    print("FES convergence check")
    print("=" * 72)
    for estimate in estimates:
        print(
            f"[INFO] t={estimate.time_ns:8.3f} ns ; "
            f"Delta G(C-O)={estimate.delta_g_oc_kcal_mol:8.3f} kcal/mol ; "
            f"C-lowest(O,PC)={estimate.c_minus_lowest_opc_kcal_mol:8.3f} kcal/mol ; "
            f"file={estimate.fes_path}"
        )

    print("[INFO] block averages:")
    for block in block_averages:
        print(
            f"  block={block.block_index} ; "
            f"t={block.start_time_ns:.3f}-{block.end_time_ns:.3f} ns ; "
            f"mean={block.mean_delta_g_oc_kcal_mol:.3f} kcal/mol ; "
            f"std={block.std_delta_g_oc_kcal_mol:.3f} kcal/mol"
        )

    status = "PASS" if plateau["converged"] else "FAIL"
    print(
        f"[INFO] plateau_spread={plateau['plateau_spread_kcal_mol']:.3f} kcal/mol ; "
        f"tolerance={plateau['plateau_tolerance_kcal_mol']:.3f} kcal/mol -> {status}"
    )

    plot_convergence(estimates, block_averages, output_png)
    report_payload = {
        "fes_glob": args.fes_glob,
        "timepoints": [asdict(entry) for entry in estimates],
        "block_averages": [asdict(block) for block in block_averages],
        "plateau_assessment": plateau,
        "plot_png": str(output_png),
    }
    output_json.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[INFO] wrote plot: {output_png}")
    print(f"[INFO] wrote report: {output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
