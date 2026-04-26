#!/usr/bin/env python3
"""Render initial-pilot FES in the preferred SI-like red/blue contour style."""

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

FES_MAX = 12.0
MASK_ABOVE = 12.0


def read_surface(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    arr = np.loadtxt(path, comments="#")
    s_axis = np.unique(arr[:, 0])
    z_msd_axis = np.unique(arr[:, 1])
    if len(arr) != len(s_axis) * len(z_msd_axis):
        raise ValueError(f"unexpected PLUMED grid shape in {path}")
    free = arr[:, 2].reshape(len(z_msd_axis), len(s_axis))
    free = free - np.nanmin(free)
    free = gaussian_filter(free, sigma=0.55)
    free = free - np.nanmin(free)
    z_rmsd_axis = np.sqrt(np.maximum(z_msd_axis, 0.0))
    return s_axis, z_rmsd_axis, free


def basin_xy(
    s_axis: np.ndarray,
    z_axis: np.ndarray,
    free: np.ndarray,
    s_range: tuple[float, float],
    z_range: tuple[float, float],
) -> tuple[float, float]:
    sm = (s_axis >= s_range[0]) & (s_axis <= s_range[1])
    zm = (z_axis >= z_range[0]) & (z_axis <= z_range[1])
    sub = free[np.ix_(zm, sm)]
    iy, ix = np.unravel_index(np.argmin(sub), sub.shape)
    return float(s_axis[sm][ix]), float(z_axis[zm][iy])


def main() -> None:
    if not FES.exists():
        raise FileNotFoundError(FES)

    s_axis, z_axis, free = read_surface(FES)
    s_grid, z_grid = np.meshgrid(s_axis, z_axis)

    labels = {
        "O": basin_xy(s_axis, z_axis, free, (0.8, 2.0), (0.45, 1.25)),
        "PC": basin_xy(s_axis, z_axis, free, (3.5, 6.2), (0.55, 1.45)),
        "C": basin_xy(s_axis, z_axis, free, (10.0, 13.0), (0.75, 1.7)),
    }
    # The O minimum sits on the left boundary; nudge its label inside the panel.
    labels["O"] = (1.22, labels["O"][1])

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.labelsize": 13,
            "axes.titlesize": 12.5,
            "xtick.labelsize": 11,
            "ytick.labelsize": 11,
            "savefig.dpi": 200,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig = plt.figure(figsize=(8.0, 4.5), dpi=200)
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[1.0, 0.04],
        left=0.085,
        right=0.925,
        bottom=0.18,
        top=0.80,
        wspace=0.05,
    )
    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])

    cmap = plt.get_cmap("jet").copy()
    cmap.set_bad((0.96, 0.96, 0.96, 1.0))
    shown = np.ma.masked_where(free > MASK_ABOVE, free)
    levels = np.linspace(0.0, FES_MAX, 25)
    cf = ax.contourf(
        s_grid,
        z_grid,
        shown,
        levels=levels,
        cmap=cmap,
        extend="neither",
    )
    ax.contour(
        s_grid,
        z_grid,
        shown,
        levels=np.arange(1.0, FES_MAX, 1.0),
        colors="0.18",
        linewidths=0.26,
        alpha=0.58,
    )
    ax.set_facecolor((0.96, 0.96, 0.96))

    ax.set_xlim(1.0, 13.0)
    ax.set_ylim(0.3, 1.8)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13])
    ax.set_yticks([0.4, 0.8, 1.2, 1.6])
    ax.set_xlabel("Open-to-Closed Path", fontstyle="italic")
    ax.set_ylabel("RMSD Deviation (Å)", fontstyle="italic")
    ax.set_title("Initial pilot 24 ns free energy surface", pad=5)
    ax.tick_params(direction="out", length=3.2, width=0.8)
    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
        spine.set_color("0.25")

    # Direct text labels, matching the preferred supplementary style.
    for text, (x, y) in labels.items():
        ax.text(
            x,
            y,
            text,
            ha="center",
            va="center",
            fontsize=15 if text == "PC" else 13,
            fontweight="bold",
            color="white",
            zorder=10,
        )

    cbar = fig.colorbar(cf, cax=cax)
    cbar.set_ticks(np.arange(0, FES_MAX + 0.1, 2))
    cbar.set_label("ΔG (kcal/mol)", fontstyle="italic", fontsize=12)
    cbar.ax.tick_params(labelsize=10, width=0.8, length=3)
    cbar.outline.set_linewidth(0.8)

    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    print(f"wrote {OUT_PNG}")
    print(f"wrote {OUT_PDF}")
    for text, (x, y) in labels.items():
        print(f"{text}: s={x:.3f}, z_RMSD={y:.3f}")


if __name__ == "__main__":
    main()
