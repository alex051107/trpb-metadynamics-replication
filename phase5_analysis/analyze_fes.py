from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

if "MPLCONFIGDIR" not in os.environ:
    os.environ["MPLCONFIGDIR"] = str(Path(tempfile.gettempdir()) / "matplotlib-codex")
if "XDG_CACHE_HOME" not in os.environ:
    os.environ["XDG_CACHE_HOME"] = str(Path(tempfile.gettempdir()) / "xdg-cache-codex")

import matplotlib.pyplot as plt
import numpy as np

KJ_PER_KCAL = 4.184
DEFAULT_STATE_WINDOWS = {
    "O": (1.0, 5.0),
    "PC": (5.0, 10.0),
    "C": (10.0, 15.0),
}

@dataclass
class BasinMinimum:
    state: str
    s_value: float
    z_value: float
    energy_kj_mol: float
    energy_kcal_mol: float

@dataclass
class BarrierEstimate:
    name: str
    start_state: str
    end_state: str
    saddle_s: float
    saddle_energy_kj_mol: float
    saddle_energy_kcal_mol: float
    barrier_kj_mol: float
    barrier_kcal_mol: float

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze a TrpB Path-CV FES grid.")
    parser.add_argument("--fes", required=True, help="Path to fes.dat")
    parser.add_argument(
        "--output-prefix",
        default=None,
        help="Prefix for .png/.json outputs (default: derived from --fes)",
    )
    parser.add_argument(
        "--reference-c-minus-opc-kcal",
        type=float,
        default=5.0,
        help="JACS reference for C relative to the lower of O/PC minima in kcal/mol",
    )
    parser.add_argument(
        "--reference-pc-to-c-barrier-kcal",
        type=float,
        default=6.0,
        help="JACS reference for the PC->C barrier in kcal/mol",
    )
    parser.add_argument(
        "--comparison-tolerance-kcal",
        type=float,
        default=2.0,
        help="Allowed absolute deviation vs literature reference in kcal/mol",
    )
    return parser.parse_args()

def kj_to_kcal(value_kj: float) -> float:
    return value_kj / KJ_PER_KCAL

def kcal_to_kj(value_kcal: float) -> float:
    return value_kcal * KJ_PER_KCAL

def assert_finite(value: float, label: str) -> None:
    assert math.isfinite(value), f"{label} is not finite: {value}"

def load_fes_grid(fes_path: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    path = Path(fes_path)
    assert path.is_file(), f"FES file not found: {path}"
    assert path.stat().st_size > 0, f"FES file is empty: {path}"

    data_rows: list[tuple[float, float, float]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            fields = line.split()
            if len(fields) < 3:
                continue
            s_value = float(fields[0])
            z_value = float(fields[1])
            energy_value = float(fields[2])
            data_rows.append((s_value, z_value, energy_value))

    assert data_rows, f"No grid data parsed from {path}"

    s_values = np.array(sorted({row[0] for row in data_rows}), dtype=float)
    z_values = np.array(sorted({row[1] for row in data_rows}), dtype=float)
    grid = np.full((len(s_values), len(z_values)), np.nan, dtype=float)

    s_lookup = {value: index for index, value in enumerate(s_values)}
    z_lookup = {value: index for index, value in enumerate(z_values)}
    for s_value, z_value, energy_value in data_rows:
        grid[s_lookup[s_value], z_lookup[z_value]] = energy_value

    assert np.isfinite(grid).any(), "FES grid does not contain any finite energies"
    assert 0.5 <= float(np.nanmin(s_values)) <= 5.0, (
        f"Unexpected minimum s value {np.nanmin(s_values):.3f}; expected a Path-CV grid"
    )
    assert 10.0 <= float(np.nanmax(s_values)) <= 20.0, (
        f"Unexpected maximum s value {np.nanmax(s_values):.3f}; expected Path-CV coverage up to C"
    )
    return s_values, z_values, grid

def calculate_projected_profile_kj_mol(fes_grid_kj_mol: np.ndarray) -> np.ndarray:
    profile = np.nanmin(fes_grid_kj_mol, axis=1)
    assert np.isfinite(profile).any(), "Projected FES profile contains no finite values"
    return profile

def get_state_mask(s_values: np.ndarray, state: str) -> np.ndarray:
    lower, upper = DEFAULT_STATE_WINDOWS[state]
    if state == "C":
        mask = (s_values >= lower) & (s_values <= upper)
    else:
        mask = (s_values >= lower) & (s_values < upper)
    assert mask.any(), f"State window {state} has no sampled grid points"
    return mask

def find_basin_minimum(
    s_values: np.ndarray,
    z_values: np.ndarray,
    fes_grid_kj_mol: np.ndarray,
    state: str,
) -> BasinMinimum:
    mask = get_state_mask(s_values, state)
    subgrid = fes_grid_kj_mol[mask, :]
    assert np.isfinite(subgrid).any(), f"{state} basin subgrid contains no finite values"

    flat_index = int(np.nanargmin(subgrid))
    local_s_index, z_index = np.unravel_index(flat_index, subgrid.shape)
    s_index = np.where(mask)[0][local_s_index]

    energy_kj = float(fes_grid_kj_mol[s_index, z_index])
    basin = BasinMinimum(
        state=state,
        s_value=float(s_values[s_index]),
        z_value=float(z_values[z_index]),
        energy_kj_mol=energy_kj,
        energy_kcal_mol=kj_to_kcal(energy_kj),
    )
    assert -50.0 <= basin.energy_kcal_mol <= 50.0, (
        f"{state} basin energy {basin.energy_kcal_mol:.3f} kcal/mol is outside a plausible range"
    )
    assert basin.z_value >= 0.0, f"{state} basin z value must be non-negative, got {basin.z_value:.3f}"
    return basin

def calculate_barrier_from_profile(
    name: str,
    s_values: np.ndarray,
    projected_profile_kj_mol: np.ndarray,
    start_basin: BasinMinimum,
    end_basin: BasinMinimum,
) -> BarrierEstimate:
    lower = min(start_basin.s_value, end_basin.s_value)
    upper = max(start_basin.s_value, end_basin.s_value)
    mask = (s_values >= lower) & (s_values <= upper)
    assert mask.any(), f"No s values found between basins for {name}"

    segment_s = s_values[mask]
    segment_profile = projected_profile_kj_mol[mask]
    local_index = int(np.nanargmax(segment_profile))
    saddle_s = float(segment_s[local_index])
    saddle_energy_kj = float(segment_profile[local_index])
    barrier_kj = saddle_energy_kj - start_basin.energy_kj_mol
    barrier = BarrierEstimate(
        name=name,
        start_state=start_basin.state,
        end_state=end_basin.state,
        saddle_s=saddle_s,
        saddle_energy_kj_mol=saddle_energy_kj,
        saddle_energy_kcal_mol=kj_to_kcal(saddle_energy_kj),
        barrier_kj_mol=barrier_kj,
        barrier_kcal_mol=kj_to_kcal(barrier_kj),
    )
    assert 0.0 <= barrier.barrier_kcal_mol <= 40.0, (
        f"{name} barrier {barrier.barrier_kcal_mol:.3f} kcal/mol is outside 0-40 kcal/mol"
    )
    return barrier

def compare_to_reference(
    observed_kcal: float,
    reference_kcal: float,
    tolerance_kcal: float,
    label: str,
) -> dict[str, float | bool | str]:
    delta = observed_kcal - reference_kcal
    return {
        "label": label,
        "observed_kcal_mol": observed_kcal,
        "reference_kcal_mol": reference_kcal,
        "delta_kcal_mol": delta,
        "absolute_delta_kcal_mol": abs(delta),
        "within_tolerance": abs(delta) <= tolerance_kcal,
        "tolerance_kcal_mol": tolerance_kcal,
    }

def plot_fes(
    s_values: np.ndarray,
    z_values: np.ndarray,
    fes_grid_kj_mol: np.ndarray,
    basins: dict[str, BasinMinimum],
    output_png: Path,
) -> None:
    fes_grid_kcal = fes_grid_kj_mol / KJ_PER_KCAL
    fig, ax = plt.subplots(figsize=(10, 7), dpi=150)

    level_max = float(np.nanmax(fes_grid_kcal))
    levels = np.linspace(float(np.nanmin(fes_grid_kcal)), level_max, 25)
    contour = ax.contourf(s_values, z_values, fes_grid_kcal.T, levels=levels, cmap="viridis")
    plt.colorbar(contour, ax=ax, label="Free energy (kcal/mol)")

    for state, basin in basins.items():
        ax.plot(basin.s_value, basin.z_value, "wo", markersize=6, markeredgecolor="black")
        ax.text(
            basin.s_value,
            basin.z_value,
            f" {state}",
            fontsize=10,
            color="white",
            ha="left",
            va="center",
            fontweight="bold",
        )

    for boundary in (5.0, 10.0):
        ax.axvline(boundary, color="white", linestyle="--", linewidth=1.0, alpha=0.7)

    ax.set_xlabel("s(R)")
    ax.set_ylabel("z(R)")
    ax.set_title("TrpB Path-CV Free Energy Surface")
    ax.set_xlim(float(np.nanmin(s_values)), float(np.nanmax(s_values)))
    ax.set_ylim(float(np.nanmin(z_values)), float(np.nanmax(z_values)))
    fig.tight_layout()
    fig.savefig(output_png, bbox_inches="tight")
    plt.close(fig)

def basin_report_lines(basins: dict[str, BasinMinimum]) -> list[str]:
    lines: list[str] = []
    for state in ("O", "PC", "C"):
        basin = basins[state]
        lines.append(
            f"{state}: s={basin.s_value:.3f}, z={basin.z_value:.3f}, "
            f"F={basin.energy_kcal_mol:.3f} kcal/mol"
        )
    return lines

def run_analysis(
    fes_path: str | Path,
    *,
    reference_c_minus_opc_kcal: float,
    reference_pc_to_c_barrier_kcal: float,
    comparison_tolerance_kcal: float,
) -> dict:
    s_values, z_values, fes_grid_kj_mol = load_fes_grid(fes_path)
    projected_profile_kj = calculate_projected_profile_kj_mol(fes_grid_kj_mol)
    basins = {
        state: find_basin_minimum(s_values, z_values, fes_grid_kj_mol, state)
        for state in ("O", "PC", "C")
    }

    opc_lowest_kcal = min(basins["O"].energy_kcal_mol, basins["PC"].energy_kcal_mol)
    c_minus_opc_kcal = basins["C"].energy_kcal_mol - opc_lowest_kcal
    delta_g_oc_kcal = basins["C"].energy_kcal_mol - basins["O"].energy_kcal_mol
    delta_g_pc_c_kcal = basins["C"].energy_kcal_mol - basins["PC"].energy_kcal_mol

    barrier_o_pc = calculate_barrier_from_profile(
        "O_to_PC",
        s_values,
        projected_profile_kj,
        basins["O"],
        basins["PC"],
    )
    barrier_pc_c = calculate_barrier_from_profile(
        "PC_to_C",
        s_values,
        projected_profile_kj,
        basins["PC"],
        basins["C"],
    )
    barrier_o_c = calculate_barrier_from_profile(
        "O_to_C",
        s_values,
        projected_profile_kj,
        basins["O"],
        basins["C"],
    )

    comparisons = {
        "c_minus_opc": compare_to_reference(
            c_minus_opc_kcal,
            reference_c_minus_opc_kcal,
            comparison_tolerance_kcal,
            "C relative to lowest(O,PC)",
        ),
        "pc_to_c_barrier": compare_to_reference(
            barrier_pc_c.barrier_kcal_mol,
            reference_pc_to_c_barrier_kcal,
            comparison_tolerance_kcal,
            "PC -> C barrier",
        ),
    }

    assert -20.0 <= c_minus_opc_kcal <= 20.0, (
        f"C relative to lowest(O,PC) = {c_minus_opc_kcal:.3f} kcal/mol outside expected range"
    )
    assert -20.0 <= delta_g_oc_kcal <= 20.0, (
        f"Delta G(C-O) = {delta_g_oc_kcal:.3f} kcal/mol outside expected range"
    )
    assert -20.0 <= delta_g_pc_c_kcal <= 20.0, (
        f"Delta G(C-PC) = {delta_g_pc_c_kcal:.3f} kcal/mol outside expected range"
    )

    return {
        "s_values": s_values,
        "z_values": z_values,
        "fes_grid_kj_mol": fes_grid_kj_mol,
        "projected_profile_kj_mol": projected_profile_kj,
        "basins": basins,
        "barriers": {
            barrier.name: barrier for barrier in (barrier_o_pc, barrier_pc_c, barrier_o_c)
        },
        "delta_g_kcal_mol": {
            "C_minus_O": delta_g_oc_kcal,
            "C_minus_PC": delta_g_pc_c_kcal,
            "C_minus_lowest_O_PC": c_minus_opc_kcal,
        },
        "comparisons": comparisons,
    }

def main() -> int:
    args = parse_args()
    fes_path = Path(args.fes).resolve()
    output_prefix = (
        Path(args.output_prefix).resolve()
        if args.output_prefix
        else fes_path.with_suffix("")
    )
    output_png = output_prefix.with_name(output_prefix.name + "_plot.png")
    output_json = output_prefix.with_name(output_prefix.name + "_report.json")

    analysis = run_analysis(
        fes_path,
        reference_c_minus_opc_kcal=args.reference_c_minus_opc_kcal,
        reference_pc_to_c_barrier_kcal=args.reference_pc_to_c_barrier_kcal,
        comparison_tolerance_kcal=args.comparison_tolerance_kcal,
    )

    basins: dict[str, BasinMinimum] = analysis["basins"]
    barriers: dict[str, BarrierEstimate] = analysis["barriers"]

    print("=" * 72)
    print("TrpB FES analysis")
    print("=" * 72)
    print(f"[INFO] fes={fes_path}")
    print(f"[INFO] s_range=({analysis['s_values'].min():.3f}, {analysis['s_values'].max():.3f})")
    print(f"[INFO] z_range=({analysis['z_values'].min():.3f}, {analysis['z_values'].max():.3f})")
    print("[INFO] basin minima:")
    for line in basin_report_lines(basins):
        print(f"  {line}")

    print("[INFO] free-energy differences:")
    for label, value in analysis["delta_g_kcal_mol"].items():
        print(f"  {label} = {value:.3f} kcal/mol")

    print("[INFO] projected barriers:")
    for name in ("O_to_PC", "PC_to_C", "O_to_C"):
        barrier = barriers[name]
        print(
            f"  {name}: saddle_s={barrier.saddle_s:.3f}, "
            f"barrier={barrier.barrier_kcal_mol:.3f} kcal/mol"
        )

    print("[INFO] JACS comparison:")
    for key, comparison in analysis["comparisons"].items():
        status = "PASS" if comparison["within_tolerance"] else "FAIL"
        print(
            f"  {key}: observed={comparison['observed_kcal_mol']:.3f}, "
            f"reference={comparison['reference_kcal_mol']:.3f}, "
            f"abs_delta={comparison['absolute_delta_kcal_mol']:.3f} kcal/mol -> {status}"
        )

    plot_fes(analysis["s_values"], analysis["z_values"], analysis["fes_grid_kj_mol"], basins, output_png)

    report_payload = {
        "fes": str(fes_path),
        "basins": {state: asdict(basin) for state, basin in basins.items()},
        "barriers": {name: asdict(barrier) for name, barrier in barriers.items()},
        "delta_g_kcal_mol": analysis["delta_g_kcal_mol"],
        "comparisons": analysis["comparisons"],
        "plot_png": str(output_png),
    }
    output_json.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[INFO] wrote plot: {output_png}")
    print(f"[INFO] wrote report: {output_json}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
