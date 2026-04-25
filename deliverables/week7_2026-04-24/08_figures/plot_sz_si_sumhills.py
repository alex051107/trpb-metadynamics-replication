"""Plot TrpB path-CV surfaces in the visual convention used by the SI.

Inputs are PLUMED `sum_hills` grids generated on Longleaf from the HILLS files:

    plumed sum_hills --hills HILLS --min 0.5,0.0 --max 15.5,2.8 \
        --bin 300,140 --mintozero --outfile fes_*.dat

Two figures are written:
  1. SI-literal: raw p1.zzz on the y-axis, labelled as RMSD Deviation (A)
     to match the JACS 2019/SI visual convention.
  2. Unit-checked: sqrt(p1.zzz) on the y-axis, labelled explicitly.

The data are short single-walker pilots, so these are diagnostic surfaces rather
than converged production FELs.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

HERE = Path(__file__).resolve().parent


def find_repo_root(start: Path) -> Path:
    for parent in (start, *start.parents):
        if (parent / "reports" / "figures" / "raw_data").exists():
            return parent
    raise FileNotFoundError("could not locate reports/figures/raw_data from script path")


REPO_ROOT = find_repo_root(HERE)
FIG_DIR = HERE
DATA_DIR = REPO_ROOT / "reports" / "figures" / "raw_data"

NAIVE_FES = DATA_DIR / "fes_initial_single_sumhills.dat"
SEQALN_FES = DATA_DIR / "fes_initial_seqaligned_sumhills.dat"
NAIVE_COLVAR = DATA_DIR / "longleaf_initial_single_COLVAR"
SEQALN_COLVAR = DATA_DIR / "longleaf_initial_seqaligned_COLVAR"

OUT_SI = FIG_DIR / "sz_2d_si_literal_sumhills.png"
OUT_SI_PDF = FIG_DIR / "sz_2d_si_literal_sumhills.pdf"
OUT_UNIT = FIG_DIR / "sz_2d_unit_checked_sumhills.png"
OUT_CANONICAL = FIG_DIR / "sz_2d_distribution.png"

FES_MAX = 14.0
UPPER_WALL_Z_RAW = 2.5


def read_sumhills(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    arr = np.loadtxt(path, comments="#")
    s = arr[:, 0]
    z_raw = arr[:, 1]
    f = arr[:, 2]
    xs = np.unique(s)
    zs = np.unique(z_raw)
    if len(xs) * len(zs) != len(arr):
        raise ValueError(f"unexpected grid shape in {path}")
    s_grid = s.reshape(len(zs), len(xs))
    z_grid = z_raw.reshape(len(zs), len(xs))
    f_grid = f.reshape(len(zs), len(xs))
    f_grid = np.nan_to_num(f_grid, nan=FES_MAX, posinf=FES_MAX, neginf=0.0)
    return s_grid, z_grid, np.clip(f_grid, 0.0, FES_MAX)


def read_colvar_stats(path: Path) -> dict[str, float]:
    arr = np.loadtxt(path, comments="#")
    s = arr[:, 1]
    z = arr[:, 2]
    return {
        "n": float(len(arr)),
        "ns": float(arr[-1, 0] / 1000.0),
        "s_min": float(np.min(s)),
        "s_max": float(np.max(s)),
        "z0": float(z[0]),
        "s0": float(s[0]),
    }


def setup_axes(ax: plt.Axes, y_label: str, y_limit: tuple[float, float]) -> None:
    ax.set_xlabel("Open-to-Closed Path", fontsize=10)
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_xlim(0.8, 15.2)
    ax.set_ylim(*y_limit)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.tick_params(direction="out", length=3, labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)


def draw_pair(
    *,
    transform: str,
    out_png: Path,
    out_pdf: Path | None = None,
) -> None:
    s_a, z_a_raw, f_a = read_sumhills(NAIVE_FES)
    s_b, z_b_raw, f_b = read_sumhills(SEQALN_FES)
    stats_a = read_colvar_stats(NAIVE_COLVAR)
    stats_b = read_colvar_stats(SEQALN_COLVAR)

    if transform == "si_literal":
        z_a = z_a_raw
        z_b = z_b_raw
        y_label = r"RMSD Deviation ($\AA$)"
        y_limit = (0.2, 2.65)
        wall_y = UPPER_WALL_Z_RAW
        start_y = stats_b["z0"]
        subtitle = "SI-literal axes: raw PLUMED p1.zzz plotted with the paper's RMSD-Deviation label"
    elif transform == "sqrt":
        z_a = np.sqrt(np.clip(z_a_raw, 0.0, None))
        z_b = np.sqrt(np.clip(z_b_raw, 0.0, None))
        y_label = r"$\sqrt{\mathrm{p1.zzz}}$  ($\AA$)"
        y_limit = (0.0, 1.7)
        wall_y = np.sqrt(UPPER_WALL_Z_RAW)
        start_y = np.sqrt(stats_b["z0"])
        subtitle = "Unit-checked axes: y = sqrt(raw PLUMED p1.zzz)"
    else:
        raise ValueError(transform)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.linewidth": 0.8,
        "savefig.dpi": 300,
    })

    fig = plt.figure(figsize=(10.8, 4.25))
    gs = fig.add_gridspec(
        1, 3,
        width_ratios=[1.0, 1.0, 0.045],
        left=0.065, right=0.935, top=0.78, bottom=0.17,
        wspace=0.18,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[0, 2])

    levels = np.linspace(0.0, FES_MAX, 29)
    cmap = plt.get_cmap("turbo")
    norm = colors.Normalize(0.0, FES_MAX)

    cf_a = ax_a.contourf(s_a, z_a, f_a, levels=levels, cmap=cmap, norm=norm, extend="max")
    ax_a.contour(s_a, z_a, f_a, levels=np.arange(2, FES_MAX, 2),
                 colors="black", linewidths=0.25, alpha=0.35)
    cf_b = ax_b.contourf(s_b, z_b, f_b, levels=levels, cmap=cmap, norm=norm, extend="max")
    ax_b.contour(s_b, z_b, f_b, levels=np.arange(2, FES_MAX, 2),
                 colors="black", linewidths=0.25, alpha=0.35)

    for ax in (ax_a, ax_b):
        ax.axhline(wall_y, color="white", linestyle=(0, (4, 2)), linewidth=0.8, alpha=0.75)
        setup_axes(ax, y_label, y_limit)

    ax_a.set_title(
        f"(a)  Naive path  (pre-FP-034, {stats_a['ns']:.1f} ns)",
        loc="left", fontsize=10.5, weight="bold",
    )
    ax_b.set_title(
        f"(b)  Sequence-aligned path  (post-FP-034, {stats_b['ns']:.1f} ns)",
        loc="left", fontsize=10.5, weight="bold",
    )
    ax_b.scatter([stats_b["s0"]], [start_y], marker="*", s=190,
                 facecolor="#ff3030", edgecolor="white", linewidth=1.1, zorder=5)
    ax_b.text(stats_b["s0"] + 0.35, start_y, "start.gro", color="white", fontsize=8.5,
              ha="left", va="center",
              bbox=dict(boxstyle="round,pad=0.22", facecolor="black", alpha=0.55, edgecolor="none"))

    ax_a.text(
        0.02, 0.03, f"s = {stats_a['s_min']:.2f}-{stats_a['s_max']:.2f}",
        transform=ax_a.transAxes, ha="left", va="bottom", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.70, edgecolor="none"),
    )
    ax_b.text(
        0.02, 0.03, f"s = {stats_b['s_min']:.2f}-{stats_b['s_max']:.2f}",
        transform=ax_b.transAxes, ha="left", va="bottom", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.70, edgecolor="none"),
    )

    cbar = fig.colorbar(cf_b, cax=cax)
    cbar.set_ticks(np.arange(0, FES_MAX + 0.1, 2))
    cbar.set_label(r"$\Delta G$ (kcal mol$^{-1}$)", fontsize=9.5)
    cbar.ax.tick_params(labelsize=8.5)

    fig.suptitle(
        "FEL associated with COMM-domain Open-to-Closed exchange",
        fontsize=12.0, weight="bold", y=0.955,
    )
    fig.text(0.5, 0.855, subtitle, ha="center", va="center", fontsize=8.2, color="0.25")

    fig.savefig(out_png, bbox_inches="tight")
    if out_pdf is not None:
        fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    if out_pdf is not None:
        print(f"wrote {out_pdf}")


def main() -> None:
    for path in (NAIVE_FES, SEQALN_FES, NAIVE_COLVAR, SEQALN_COLVAR):
        if not path.exists():
            raise FileNotFoundError(path)
    draw_pair(transform="si_literal", out_png=OUT_SI, out_pdf=OUT_SI_PDF)
    draw_pair(transform="sqrt", out_png=OUT_UNIT)
    # Keep the historical filename pointing at the SI-literal version, because
    # this is the file used in existing reports/results pages.
    OUT_CANONICAL.write_bytes(OUT_SI.read_bytes())
    print(f"updated canonical {OUT_CANONICAL}")


if __name__ == "__main__":
    main()
