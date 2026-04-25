"""Draw the canonical Week-7 FES in the JACS 2019 SI red-blue style.

The goal here is visual comparability to the SI panels: full sum_hills grid,
no sampled-region mask, blue low-free-energy basins, red high-free-energy
walls, thin contour lines, and minimal O/PC labels.

Run:
    python3 reports/figures/plot_canonical_fes.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import gaussian_filter


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "raw_data"

PRE_FP034_FES = DATA_DIR / "fes_initial_single_sumhills.dat"
POST_FP034_FES = DATA_DIR / "fes_initial_seqaligned_sumhills.dat"
PRE_FP034_COLVAR = DATA_DIR / "longleaf_initial_single_COLVAR"
POST_FP034_COLVAR = DATA_DIR / "longleaf_initial_seqaligned_COLVAR"

OUT_PNG = HERE / "sz_2d_distribution.png"
OUT_PDF = HERE / "sz_2d_distribution.pdf"

FES_MAX = 14.0
X_MIN, X_MAX = 0.8, 15.2
Y_MIN, Y_MAX = 0.2, 2.65


@dataclass(frozen=True)
class Surface:
    s_axis: np.ndarray
    y_axis: np.ndarray
    s_grid: np.ndarray
    y_grid: np.ndarray
    f_grid: np.ndarray


def read_surface(path: Path) -> Surface:
    """Read PLUMED sum_hills grid as SI-literal axes: y = raw p1.zzz."""
    arr = np.loadtxt(path, comments="#")
    s = arr[:, 0]
    y = arr[:, 1]
    f = np.clip(arr[:, 2], 0.0, FES_MAX)
    s_axis = np.unique(s)
    y_axis = np.unique(y)
    if len(s_axis) * len(y_axis) != len(arr):
        raise ValueError(f"unexpected grid shape in {path}")
    s_grid, y_grid = np.meshgrid(s_axis, y_axis)
    f_grid = f.reshape(len(y_axis), len(s_axis))
    return Surface(s_axis=s_axis, y_axis=y_axis, s_grid=s_grid, y_grid=y_grid, f_grid=f_grid)


def colvar_ns(path: Path) -> float:
    arr = np.loadtxt(path, comments="#", usecols=(0,))
    return float(arr[-1] / 1000.0)


def basin_in_window(
    surface: Surface,
    f_grid: np.ndarray,
    *,
    s_min: float,
    s_max: float,
    y_min: float = Y_MIN,
    y_max: float = Y_MAX,
) -> tuple[float, float, float]:
    s_mask = (surface.s_axis >= s_min) & (surface.s_axis <= s_max)
    y_mask = (surface.y_axis >= y_min) & (surface.y_axis <= y_max)
    sub = f_grid[np.ix_(y_mask, s_mask)]
    iy, ix = np.unravel_index(np.argmin(sub), sub.shape)
    return (
        float(surface.s_axis[s_mask][ix]),
        float(surface.y_axis[y_mask][iy]),
        float(sub[iy, ix]),
    )


def style_axis(ax: plt.Axes, *, show_ylabel: bool) -> None:
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.set_yticks([0.5, 1.0, 1.5, 2.0, 2.5])
    ax.set_xlabel("Open-to-Closed Path", fontsize=10, fontstyle="italic")
    if show_ylabel:
        ax.set_ylabel(r"RMSD Deviation ($\AA$)", fontsize=10, fontstyle="italic")
    ax.tick_params(direction="out", width=0.8, length=3, labelsize=9)
    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
        spine.set_color("0.25")


def label_basin(ax: plt.Axes, text: str, s: float, y: float) -> None:
    ax.text(
        s,
        y,
        text,
        ha="center",
        va="center",
        color="white",
        fontsize=11,
        fontweight="bold",
        zorder=10,
    )


def draw() -> dict[str, tuple[float, float, float]]:
    pre = read_surface(PRE_FP034_FES)
    post = read_surface(POST_FP034_FES)
    pre_f = gaussian_filter(pre.f_grid, sigma=0.65)
    post_f = gaussian_filter(post.f_grid, sigma=0.65)

    pre_ns = colvar_ns(PRE_FP034_COLVAR)
    post_ns = colvar_ns(POST_FP034_COLVAR)

    pre_o = basin_in_window(pre, pre_f, s_min=0.9, s_max=2.3, y_min=0.4, y_max=2.1)
    post_o = basin_in_window(post, post_f, s_min=0.9, s_max=2.5, y_min=0.4, y_max=1.8)
    post_pc = basin_in_window(post, post_f, s_min=3.0, s_max=6.5, y_min=0.6, y_max=1.8)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "savefig.dpi": 300,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    fig = plt.figure(figsize=(7.6, 3.15))
    gs = fig.add_gridspec(
        1,
        3,
        width_ratios=[1, 1, 0.048],
        left=0.08,
        right=0.94,
        bottom=0.20,
        top=0.77,
        wspace=0.18,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[0, 2])

    levels = np.linspace(0.0, FES_MAX, 29)
    line_levels = np.arange(1.0, FES_MAX, 1.0)
    cmap = plt.get_cmap("jet")

    # extend="max": F values > FES_MAX (panel a max ~28.6, panel b max ~18.0)
    # render at the topmost color band, NOT as white. Without this, the high-F
    # walls leak through as transparent white and the panels look unfilled.
    cf = ax_a.contourf(pre.s_grid, pre.y_grid, pre_f, levels=levels,
                       cmap=cmap, extend="max")
    ax_a.contour(pre.s_grid, pre.y_grid, pre_f, levels=line_levels,
                 colors="0.20", linewidths=0.28, alpha=0.55)
    ax_b.contourf(post.s_grid, post.y_grid, post_f, levels=levels,
                  cmap=cmap, extend="max")
    ax_b.contour(post.s_grid, post.y_grid, post_f, levels=line_levels,
                 colors="0.20", linewidths=0.28, alpha=0.55)
    # Set both panels' background to the cmap's top color so any sub-pixel
    # gaps still read as "high free energy" rather than "missing data".
    top_color = cmap(0.99)
    ax_a.set_facecolor(top_color)
    ax_b.set_facecolor(top_color)

    style_axis(ax_a, show_ylabel=True)
    style_axis(ax_b, show_ylabel=False)

    ax_a.set_title(
        rf"(a) Naive path (pre-FP-034) — {pre_ns:.1f} ns",
        fontsize=8.8,
        pad=3,
    )
    ax_b.set_title(
        rf"(b) Sequence-aligned (post-FP-034) — {post_ns:.1f} ns",
        fontsize=8.8,
        pad=3,
    )

    label_basin(ax_a, "O", pre_o[0], pre_o[1])
    label_basin(ax_b, "O", post_o[0], post_o[1])
    label_basin(ax_b, "PC", post_pc[0], post_pc[1])

    cbar = fig.colorbar(cf, cax=cax)
    cbar.set_ticks(np.arange(0, FES_MAX + 0.1, 2))
    cbar.set_label(r"$\Delta G$ (kcal/mol)", fontsize=9, fontstyle="italic")
    cbar.ax.tick_params(labelsize=8, width=0.8, length=2.5)

    fig.text(0.02, 0.93, "(a) $\\it{Pf}$TrpB initial runs", fontsize=12, ha="left", va="center")

    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")

    return {
        "pre_FP034_O": pre_o,
        "post_FP034_O": post_o,
        "post_FP034_PC": post_pc,
    }


def main() -> None:
    for path in (PRE_FP034_FES, POST_FP034_FES, PRE_FP034_COLVAR, POST_FP034_COLVAR):
        if not path.exists():
            raise FileNotFoundError(path)
    basins = draw()
    print(f"wrote {OUT_PNG}")
    print(f"wrote {OUT_PDF}")
    print("style=JACS2019_SI_red_blue_full_grid_no_mask")
    for name, (s, y, f) in basins.items():
        print(f"{name}: s={s:.3f}, y={y:.3f}, F={f:.3f} kcal/mol")


if __name__ == "__main__":
    main()
