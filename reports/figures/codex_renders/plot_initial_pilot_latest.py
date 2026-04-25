#!/usr/bin/env python3
"""Render the latest initial-pilot FES with SI-style RMSD units."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "codex_renders" / "data"

FES = DATA / "fes_initial_pilot_latest.dat"
COLVAR = DATA / "initial_pilot_latest_COLVAR"
HILLS = DATA / "initial_pilot_latest_HILLS"

OUT_PNG = ROOT / "initial_pilot_latest_fes.png"
OUT_PDF = ROOT / "initial_pilot_latest_fes.pdf"
OUT_META = ROOT / "initial_pilot_latest_fes.meta.txt"

X_MIN, X_MAX = 0.5, 15.5
Y_MIN, Y_MAX = 0.0, 1.7
FES_MAX = 14.0
WALL_RMSD = float(np.sqrt(2.5))


def read_grid(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    arr = np.loadtxt(path, comments="#")
    s_axis = np.unique(arr[:, 0])
    z_msd_axis = np.unique(arr[:, 1])
    expected = len(s_axis) * len(z_msd_axis)
    if len(arr) != expected:
        raise ValueError(f"unexpected grid shape: got {len(arr)}, expected {expected}")
    f_grid = arr[:, 2].reshape(len(z_msd_axis), len(s_axis))
    f_grid = f_grid - np.nanmin(f_grid)
    # Smooth only for SI-style visual readability; all metadata uses raw COLVAR/HILLS.
    f_grid = gaussian_filter(f_grid, sigma=0.55)
    f_grid = f_grid - np.nanmin(f_grid)
    z_rmsd_axis = np.sqrt(np.maximum(z_msd_axis, 0.0))
    return s_axis, z_rmsd_axis, f_grid


def read_colvar(path: Path) -> np.ndarray:
    return np.loadtxt(path, comments="#")


def count_hills(path: Path) -> int:
    count = 0
    with path.open() as handle:
        for line in handle:
            if line.strip() and not line.startswith("#"):
                count += 1
    return count


def render() -> dict[str, float | int]:
    s_axis, z_rmsd_axis, f_grid = read_grid(FES)
    colvar = read_colvar(COLVAR)
    time_ns = float(colvar[-1, 0] / 1000.0)
    max_s = float(np.max(colvar[:, 1]))
    max_s_window_count = int(np.sum(colvar[:, 1] >= max_s - 0.5))
    c_region_count = int(np.sum(colvar[:, 1] >= 10.0))
    hills_count = count_hills(HILLS)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9.0,
            "axes.labelsize": 10.5,
            "xtick.labelsize": 8.8,
            "ytick.labelsize": 8.8,
            "savefig.dpi": 200,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    s_grid, y_grid = np.meshgrid(s_axis, z_rmsd_axis)
    fig = plt.figure(figsize=(7.0, 4.6), dpi=200)
    gs = fig.add_gridspec(
        1,
        2,
        width_ratios=[1, 0.045],
        left=0.105,
        right=0.90,
        bottom=0.14,
        top=0.76,
        wspace=0.035,
    )
    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])

    cmap = plt.get_cmap("RdYlBu_r")
    levels = np.linspace(0.0, FES_MAX, 29)
    line_levels = np.arange(1.0, FES_MAX, 1.0)
    cf = ax.contourf(s_grid, y_grid, f_grid, levels=levels, cmap=cmap, extend="max")
    ax.contour(
        s_grid,
        y_grid,
        f_grid,
        levels=line_levels,
        colors="0.18",
        linewidths=0.30,
        alpha=0.52,
    )

    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.set_yticks([0.0, 0.4, 0.8, 1.2, 1.6])
    ax.set_xlabel("s = Open→Closed path coordinate (dimensionless)")
    ax.set_ylabel(r"$z_{\mathrm{RMSD}}$ ($\AA$)")
    ax.tick_params(direction="out", width=0.8, length=3)

    for x in (2.0, 6.0, 10.0):
        ax.axvline(x, color="white", lw=0.85, ls=(0, (1.5, 2.4)), alpha=0.9)
    for label, x in (("O", 1.0), ("PC", 5.0), ("C", 11.0)):
        ax.text(
            x,
            0.17,
            label,
            ha="center",
            va="center",
            fontsize=10.8,
            fontweight="bold",
            color="white",
            bbox=dict(boxstyle="square,pad=0.14", facecolor="black", alpha=0.52, lw=0),
        )

    ax.axhline(WALL_RMSD, color="0.25", lw=0.8, ls="--", alpha=0.82)
    ax.text(15.25, WALL_RMSD + 0.025, r"wall $\sqrt{2.5}=1.58$ Å", ha="right", va="bottom", fontsize=7.2, color="0.18")

    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
        spine.set_color("0.25")

    cbar = fig.colorbar(cf, cax=cax)
    cbar.set_ticks(np.arange(0, FES_MAX + 0.1, 2))
    cbar.set_label(r"$\Delta G$ (kcal/mol)")

    fig.text(
        0.105,
        0.94,
        f"Initial pilot single-walker MetaD, {time_ns:.1f} ns / max_s≈{max_s:.2f}",
        ha="left",
        va="top",
        fontsize=12.3,
        fontweight="bold",
    )
    fig.text(
        0.105,
        0.885,
        "FALLBACK: HEIGHT=0.3 kcal/mol, BIASFACTOR=15, T=350 K",
        ha="left",
        va="top",
        fontsize=8.5,
        color="0.18",
    )
    fig.text(
        0.105,
        0.842,
        "convergence_grade=TENTATIVE (seed-discovery stage, NOT production FES)",
        ha="left",
        va="top",
        fontsize=8.2,
        color="0.18",
    )

    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)

    meta = {
        "time_ns": time_ns,
        "max_s": max_s,
        "max_s_window_count_s_ge_max_minus_0p5": max_s_window_count,
        "c_region_count_s_ge_10": c_region_count,
        "hills_count": hills_count,
        "fes_path": str(FES),
        "colvar_path": str(COLVAR),
        "hills_path": str(HILLS),
        "z_axis": "sqrt(path.zzz_A2) in Angstrom",
        "energy_unit": "kcal/mol; sum_hills --kt 0.695",
        "fes_color_vmax_kcalmol": FES_MAX,
    }
    OUT_META.write_text("\n".join(f"{k}={v}" for k, v in meta.items()) + "\n")
    return meta


def main() -> None:
    for path in (FES, COLVAR, HILLS):
        if not path.exists():
            raise FileNotFoundError(path)
    meta = render()
    print(f"wrote {OUT_PNG}")
    print(f"wrote {OUT_PDF}")
    print(f"wrote {OUT_META}")
    print(f"time_ns={meta['time_ns']:.4f}")
    print(f"max_s={meta['max_s']:.4f}")
    print(f"hills_count={meta['hills_count']}")


if __name__ == "__main__":
    main()
