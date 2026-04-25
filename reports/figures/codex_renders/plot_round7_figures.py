#!/usr/bin/env python3
"""Round-7 production/pilot FES renders with SI-style RMSD y axis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"

PROD_FES = DATA / "production_early_fes_sumhills.dat"
PILOT_FES = RAW / "fes_initial_seqaligned_sumhills.dat"
PILOT_COLVAR = RAW / "longleaf_initial_seqaligned_COLVAR"
WALKER_COLVAR = DATA / "all_walkers_colvar_20260425_1637.txt"

OUT_PROD_ROOT_PNG = ROOT / "production_fes_early_10walker.png"
OUT_PROD_ROOT_PDF = ROOT / "production_fes_early_10walker.pdf"
OUT_PROD_COPY_PNG = HERE / "production_fes_early_10walker_rmsd.png"
OUT_PROD_COPY_PDF = HERE / "production_fes_early_10walker_rmsd.pdf"
OUT_WALKER_PNG = HERE / "walker_explore_progress.png"
OUT_WALKER_PDF = HERE / "walker_explore_progress.pdf"
OUT_COMPARE_PNG = HERE / "comparison_pilot_vs_production_2panel.png"
OUT_COMPARE_PDF = HERE / "comparison_pilot_vs_production_2panel.pdf"

FES_MAX = 14.0
X_MIN, X_MAX = 0.8, 15.2
Y_MIN, Y_MAX = 0.0, np.sqrt(2.8)
WALL_RMSD = np.sqrt(2.5)


@dataclass(frozen=True)
class Surface:
    s_axis: np.ndarray
    y_axis: np.ndarray
    s_grid: np.ndarray
    y_grid: np.ndarray
    f_grid: np.ndarray
    f_max: float


def read_surface(path: Path, *, smooth_sigma: float = 0.55) -> Surface:
    arr = np.loadtxt(path, comments="#")
    s_axis = np.unique(arr[:, 0])
    z_axis = np.unique(arr[:, 1])
    if len(s_axis) * len(z_axis) != len(arr):
        raise ValueError(f"unexpected grid shape in {path}")
    f_grid = arr[:, 2].reshape(len(z_axis), len(s_axis))
    f_grid = f_grid - np.nanmin(f_grid)
    if smooth_sigma:
        f_grid = gaussian_filter(f_grid, sigma=smooth_sigma)
        f_grid = f_grid - np.nanmin(f_grid)
    y_axis = np.sqrt(np.maximum(z_axis, 0.0))
    s_grid, y_grid = np.meshgrid(s_axis, y_axis)
    return Surface(
        s_axis=s_axis,
        y_axis=y_axis,
        s_grid=s_grid,
        y_grid=y_grid,
        f_grid=f_grid,
        f_max=float(np.nanmax(f_grid)),
    )


def setup_style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 10,
            "axes.titlesize": 9.2,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 7.1,
            "savefig.dpi": 200,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def style_fes_axis(ax: plt.Axes, *, show_ylabel: bool = True) -> None:
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.set_yticks([0.0, 0.4, 0.8, 1.2, 1.6])
    ax.set_xlabel("Open-to-Closed Path", fontstyle="italic")
    if show_ylabel:
        ax.set_ylabel(r"$z_{\mathrm{RMSD}}=\sqrt{p1.zzz}$ ($\AA$)", fontstyle="italic")
    ax.tick_params(direction="out", width=0.8, length=3)
    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
        spine.set_color("0.25")


def draw_fes(
    ax: plt.Axes,
    surface: Surface,
    *,
    vmax: float,
    title: str,
    show_ylabel: bool,
    label_c: bool = True,
) -> matplotlib.contour.QuadContourSet:
    cmap = plt.get_cmap("jet")
    levels = np.linspace(0.0, vmax, 29)
    line_levels = np.arange(1.0, vmax, 1.0)
    cf = ax.contourf(
        surface.s_grid,
        surface.y_grid,
        surface.f_grid,
        levels=levels,
        cmap=cmap,
        extend="max",
    )
    ax.contour(
        surface.s_grid,
        surface.y_grid,
        surface.f_grid,
        levels=line_levels,
        colors="0.18",
        linewidths=0.28,
        alpha=0.55,
    )
    ax.set_facecolor(cmap(0.99))
    style_fes_axis(ax, show_ylabel=show_ylabel)
    ax.set_title(title, pad=3)
    ax.axhline(WALL_RMSD, color="0.35", ls="--", lw=0.7, alpha=0.78)
    ax.text(15.05, WALL_RMSD + 0.02, "wall", ha="right", va="bottom", fontsize=7.2, color="0.25")
    for text, x in [("O", 1.25), ("PC", 5.15), ("C", 11.25)]:
        if text == "C" and not label_c:
            continue
        ax.text(
            x,
            0.28,
            text,
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="white",
            bbox=dict(boxstyle="square,pad=0.15", facecolor="black", alpha=0.54, lw=0),
            zorder=10,
        )
    return cf


def render_production_fes() -> None:
    prod = read_surface(PROD_FES)
    vmax = prod.f_max if prod.f_max < FES_MAX else FES_MAX
    fig = plt.figure(figsize=(6.8, 4.55))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 0.045], left=0.10, right=0.91, bottom=0.15, top=0.79, wspace=0.04)
    ax = fig.add_subplot(gs[0, 0])
    cax = fig.add_subplot(gs[0, 1])
    cf = draw_fes(
        ax,
        prod,
        vmax=vmax,
        title="10-walker production FES, early snapshot",
        show_ylabel=True,
    )
    cbar = fig.colorbar(cf, cax=cax)
    cbar.set_label(r"$\Delta G$ (kcal mol$^{-1}$)", fontstyle="italic")
    cbar.set_ticks(np.arange(0, np.floor(vmax) + 0.1, 1.0))
    fig.text(0.10, 0.94, "Early 10-walker production FES", fontsize=13.5, weight="bold", ha="left")
    fig.text(
        0.10,
        0.885,
        "TENTATIVE - RMSD-axis render from PLUMED path.zzz; 846 hills, HILLS.9 absent in snapshot",
        fontsize=8.4,
        color="0.18",
        ha="left",
    )
    fig.text(
        0.112,
        0.165,
        "L0/L1 fingerprint only - not a thermodynamic label",
        fontsize=7.6,
        color="white",
        bbox=dict(boxstyle="square,pad=0.24", facecolor="black", alpha=0.62, lw=0),
    )
    for out in (OUT_PROD_ROOT_PNG, OUT_PROD_COPY_PNG):
        fig.savefig(out, bbox_inches="tight")
    for out in (OUT_PROD_ROOT_PDF, OUT_PROD_COPY_PDF):
        fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def read_walkers(path: Path) -> dict[str, np.ndarray]:
    walkers: dict[str, list[list[float]]] = {}
    current: str | None = None
    for line in path.read_text().splitlines():
        if line.startswith("==="):
            current = line.strip("= ").strip()
            walkers[current] = []
            continue
        if not current or line.startswith("#") or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 3:
            walkers[current].append([float(parts[0]), float(parts[1]), float(parts[2])])
    return {name: np.asarray(rows, dtype=float) for name, rows in walkers.items() if rows}


def render_walker_progress() -> None:
    walkers = read_walkers(WALKER_COLVAR)
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    fig.subplots_adjust(left=0.09, right=0.82, bottom=0.18, top=0.74)
    ax.axhspan(0.0, 2.0, color="#dbeafe", alpha=0.60, lw=0)
    ax.axhspan(4.0, 6.0, color="#dcfce7", alpha=0.50, lw=0)
    ax.axhspan(10.0, 15.2, color="#fee2e2", alpha=0.48, lw=0)
    colors = plt.get_cmap("tab10").colors
    for i, (name, arr) in enumerate(sorted(walkers.items())):
        ax.plot(arr[:, 0], arr[:, 1], lw=1.05, color=colors[i % 10], label=name.replace("walker_", "w"))
    ax.text(0.985, 0.88, "C", transform=ax.transAxes, ha="right", va="center", fontsize=8, color="0.35")
    ax.text(0.985, 0.43, "PC", transform=ax.transAxes, ha="right", va="center", fontsize=8, color="0.35")
    ax.text(0.985, 0.11, "O", transform=ax.transAxes, ha="right", va="center", fontsize=8, color="0.35")
    ax.set_xlim(0, max(float(arr[-1, 0]) for arr in walkers.values()))
    ax.set_ylim(0.8, 15.2)
    ax.set_xlabel("time (ps)")
    ax.set_ylabel("Path coordinate s")
    fig.text(
        0.09,
        0.94,
        "10-walker shared-HILLS exploration progress, t≈250-320 ps",
        ha="left",
        va="top",
        fontsize=11,
        weight="bold",
    )
    fig.text(
        0.09,
        0.875,
        "walker_09 started latest; bands mark O (s≤2), PC (4≤s≤6), and C (s≥10)",
        ha="left",
        va="top",
        fontsize=8,
        color="0.25",
    )
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, ncol=1)
    ax.grid(axis="y", color="0.85", lw=0.45)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    fig.savefig(OUT_WALKER_PNG, bbox_inches="tight")
    fig.savefig(OUT_WALKER_PDF, bbox_inches="tight")
    plt.close(fig)


def pilot_ns() -> float:
    return float(np.loadtxt(PILOT_COLVAR, comments="#", usecols=(0,))[-1] / 1000.0)


def render_comparison() -> None:
    pilot = read_surface(PILOT_FES)
    prod = read_surface(PROD_FES)
    fig = plt.figure(figsize=(7.8, 3.75))
    gs = fig.add_gridspec(
        1,
        3,
        width_ratios=[1, 1, 0.05],
        left=0.075,
        right=0.94,
        bottom=0.18,
        top=0.74,
        wspace=0.16,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[0, 2])
    cf = draw_fes(
        ax_a,
        pilot,
        vmax=FES_MAX,
        title=rf"(a) Initial pilot, {pilot_ns():.1f} ns",
        show_ylabel=True,
        label_c=True,
    )
    draw_fes(
        ax_b,
        prod,
        vmax=FES_MAX,
        title="(b) 10-walker production, ~0.25-0.32 ns/walker",
        show_ylabel=False,
        label_c=True,
    )
    cbar = fig.colorbar(cf, cax=cax)
    cbar.set_ticks(np.arange(0, FES_MAX + 0.1, 2))
    cbar.set_label(r"$\Delta G$ (kcal mol$^{-1}$)", fontstyle="italic")
    fig.text(0.075, 0.94, "Exploration progress on the FP-034 corrected path", fontsize=12.2, weight="bold", ha="left")
    fig.text(
        0.075,
        0.885,
        "Do not sum these surfaces: pilot uses fallback contract (0.3/15), production uses primary contract (0.15/10).",
        fontsize=8,
        ha="left",
        color="0.20",
    )
    fig.text(
        0.075,
        0.825,
        "Pilot is PROVISIONAL; production is TENTATIVE and will be re-rendered at 5-10 ns/walker.",
        fontsize=8,
        ha="left",
        color="0.20",
    )
    fig.savefig(OUT_COMPARE_PNG, bbox_inches="tight")
    fig.savefig(OUT_COMPARE_PDF, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    setup_style()
    for path in (PROD_FES, PILOT_FES, PILOT_COLVAR, WALKER_COLVAR):
        if not path.exists():
            raise FileNotFoundError(path)
    render_production_fes()
    render_walker_progress()
    render_comparison()
    walkers = read_walkers(WALKER_COLVAR)
    print(f"wrote {OUT_PROD_ROOT_PNG}")
    print(f"wrote {OUT_PROD_ROOT_PDF}")
    print(f"wrote {OUT_PROD_COPY_PNG}")
    print(f"wrote {OUT_WALKER_PNG}")
    print(f"wrote {OUT_WALKER_PDF}")
    print(f"wrote {OUT_COMPARE_PNG}")
    print(f"wrote {OUT_COMPARE_PDF}")
    for name, arr in sorted(walkers.items()):
        print(
            f"{name}: t={arr[-1,0]:.1f} ps s_now={arr[-1,1]:.2f} "
            f"s_range=[{arr[:,1].min():.2f},{arr[:,1].max():.2f}]"
        )


if __name__ == "__main__":
    main()
