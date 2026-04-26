#!/usr/bin/env python3
"""Publication-quality single-panel initial pilot FES render."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter


ROOT = Path(__file__).resolve().parents[1]
FES = ROOT / "raw_data" / "fes_initial_seqaligned_sumhills.dat"
OUT_PNG = ROOT / "initial_pilot_latest_fes.png"
OUT_PDF = ROOT / "initial_pilot_latest_fes.pdf"

FES_MAX = 30.0
X_LIM = (0.0, 16.0)
Y_LIM = (0.0, 1.7)


def read_surface(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data = np.loadtxt(path, comments="#")
    s_axis = np.unique(data[:, 0])
    z_msd_axis = np.unique(data[:, 1])
    expected = len(s_axis) * len(z_msd_axis)
    if len(data) != expected:
        raise ValueError(f"unexpected PLUMED grid shape: got {len(data)}, expected {expected}")
    free = data[:, 2].reshape(len(z_msd_axis), len(s_axis))
    free = free - np.nanmin(free)
    free = gaussian_filter(free, sigma=0.45)
    free = free - np.nanmin(free)
    z_rmsd_axis = np.sqrt(np.maximum(z_msd_axis, 0.0))
    return s_axis, z_rmsd_axis, free


def basin_minimum(
    s_axis: np.ndarray,
    z_axis: np.ndarray,
    free: np.ndarray,
    *,
    s_range: tuple[float, float],
    z_range: tuple[float, float],
) -> tuple[float, float, float]:
    s_mask = (s_axis >= s_range[0]) & (s_axis <= s_range[1])
    z_mask = (z_axis >= z_range[0]) & (z_axis <= z_range[1])
    sub = free[np.ix_(z_mask, s_mask)]
    iy, ix = np.unravel_index(np.argmin(sub), sub.shape)
    return float(s_axis[s_mask][ix]), float(z_axis[z_mask][iy]), float(sub[iy, ix])


def main() -> None:
    if not FES.exists():
        raise FileNotFoundError(FES)

    s_axis, z_axis, free = read_surface(FES)
    s_grid, z_grid = np.meshgrid(s_axis, z_axis)

    basins = {
        "O": basin_minimum(s_axis, z_axis, free, s_range=(0.8, 2.2), z_range=(0.45, 1.45)),
        "PC": basin_minimum(s_axis, z_axis, free, s_range=(4.0, 6.7), z_range=(0.45, 1.45)),
        "C": basin_minimum(s_axis, z_axis, free, s_range=(10.0, 13.5), z_range=(0.55, 1.65)),
    }

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.5,
            "axes.labelsize": 10.5,
            "xtick.labelsize": 9.0,
            "ytick.labelsize": 9.0,
            "savefig.dpi": 200,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig = plt.figure(figsize=(8.0, 5.0), dpi=200)
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[1.0, 0.045],
        left=0.095,
        right=0.91,
        bottom=0.13,
        top=0.80,
        wspace=0.035,
    )
    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])

    cmap = plt.get_cmap("viridis").copy()
    levels = np.linspace(0.0, FES_MAX, 31)
    mesh = ax.contourf(
        s_grid,
        z_grid,
        free,
        levels=levels,
        cmap=cmap,
        vmin=0.0,
        vmax=FES_MAX,
        extend="max",
        antialiased=True,
    )
    ax.contour(
        s_grid,
        z_grid,
        free,
        levels=np.arange(2.0, FES_MAX, 2.0),
        colors="white",
        linewidths=0.30,
        alpha=0.38,
    )

    ax.set_xlim(*X_LIM)
    ax.set_ylim(*Y_LIM)
    ax.set_xticks(np.arange(0, 17, 2))
    ax.set_yticks([0.0, 0.4, 0.8, 1.2, 1.6])
    ax.set_xlabel("s = open-to-closed path coordinate (dimensionless)")
    ax.set_ylabel("z RMSD (Å)")
    ax.tick_params(direction="out", length=3.0, width=0.75)
    for spine in ax.spines.values():
        spine.set_linewidth(0.85)
        spine.set_color("#1f2937")

    # Boxed basin callouts with arrows pointing to local minima in the requested regions.
    label_specs = {
        "O": ((1.65, 0.24), "#0f172a"),
        "PC": ((5.85, 0.24), "#0f172a"),
        "C": ((11.85, 0.28), "#0f172a"),
    }
    for label, (xytext, color) in label_specs.items():
        x, y, fval = basins[label]
        ax.annotate(
            f"{label}",
            xy=(x, y),
            xytext=xytext,
            ha="center",
            va="center",
            color="white",
            fontsize=10.5,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.26,rounding_size=0.08", facecolor=color, edgecolor="white", lw=0.6, alpha=0.90),
            arrowprops=dict(arrowstyle="->", color="white", lw=0.85, shrinkA=4, shrinkB=4),
            zorder=8,
        )

    ax.text(
        0.982,
        0.035,
        "Initial pilot, 24.03 ns, 12,015 Gaussians, max_s=14.05",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7.7,
        color="#111827",
        bbox=dict(boxstyle="round,pad=0.28,rounding_size=0.06", facecolor="white", edgecolor="#d1d5db", alpha=0.92, lw=0.6),
    )

    cbar = fig.colorbar(mesh, cax=cax)
    cbar.set_label("ΔG (kcal/mol)")
    cbar.set_ticks(np.arange(0, FES_MAX + 0.1, 5))
    cbar.outline.set_linewidth(0.75)

    fig.text(
        0.095,
        0.935,
        "Initial pilot 24 ns free energy surface (single walker, fallback contract)",
        ha="left",
        va="top",
        fontsize=13.0,
        fontweight="bold",
        color="#111827",
    )

    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    print(f"wrote {OUT_PNG}")
    print(f"wrote {OUT_PDF}")
    for label, (x, y, fval) in basins.items():
        print(f"{label}: s={x:.3f} z_RMSD={y:.3f} F={fval:.3f}")


if __name__ == "__main__":
    main()
