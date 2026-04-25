"""
plot_sz_distribution.py — initial single-walker FES(s, z) comparison

Two COMPLETED single-walker runs under the Miguel MetaD contract:
  a) Naive path       (pre-FP-034)  — job 45324928, 16 ns, 81 479 frames
  b) Sequence-aligned (post-FP-034) — job 45515869,  8 ns, 40 193 frames

Same start.gro, same Miguel params.  Only path.pdb differs.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "chatgpt_pro_consult_45558834" / "raw_data"
BASELINE = DATA / "baseline_45324928_COLVAR"
PILOT = DATA / "pilot_45515869_COLVAR"
OUT = ROOT / "reports" / "figures" / "sz_2d_distribution.png"

kB = 0.0019872041
T = 350.0
kT = kB * T
FES_MAX = 6.0

# JACS-2019-Fig3 convention: y-axis displays the per-Cα RMSD-scaled distance
# from the path (in Å), not the raw path.zzz which PLUMED writes in Å² (MSD).
# We take sqrt(zzz) to match the SI plotting convention while keeping the
# physical content unchanged.
S_RANGE = (0.5, 15.3)
Z_RANGE = (0.0, 1.7)            # axis in Å (= sqrt of Å²)
NS, NZ = 260, 160

# start.gro projection. COLVAR row at t=0 has path.zzz = 1.68 Å² → 1.30 Å RMSD.
START_S = 7.09
START_Z_RAW_A2 = 1.68           # Å² (raw)
START_Z_ANG = START_Z_RAW_A2 ** 0.5  # 1.296 Å on RMSD axis

# UPPER_WALLS: AT=2.5 Å² → sqrt → 1.581 Å on RMSD axis
UPPER_WALL_RAW_A2 = 2.5
UPPER_WALL_ANG = UPPER_WALL_RAW_A2 ** 0.5


def load_colvar(p: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return (s, z_in_angstrom).

    PLUMED writes path.zzz in Å² (MSD).  We return its sqrt so downstream
    plotting and statistics are in the RMSD scale used by JACS 2019 Fig 3.
    """
    a = np.loadtxt(p, comments="#")
    s = a[:, 1]
    z_a2 = np.clip(a[:, 2], 0.0, None)      # guard tiny negative noise
    z_ang = np.sqrt(z_a2)                    # Å² → Å (RMSD)
    return s, z_ang


def fes(s: np.ndarray, z: np.ndarray):
    """KDE on the (s, z_RMSD) plane → free energy in kcal/mol."""
    kde = gaussian_kde(np.vstack([s, z]), bw_method=0.18)
    sx = np.linspace(*S_RANGE, NS)
    zx = np.linspace(*Z_RANGE, NZ)
    S, Z = np.meshgrid(sx, zx)
    with np.errstate(divide="ignore"):
        p = kde(np.vstack([S.ravel(), Z.ravel()])).reshape(S.shape)
        F = -kT * np.log(np.clip(p, 1e-300, None) / p.max())
    return S, Z, np.clip(F, 0.0, FES_MAX)


def panel(ax, S, Z, F, tag: str, title: str, show_star: bool):
    levels = np.linspace(0.0, FES_MAX, 41)
    cmap = plt.get_cmap("viridis_r")
    cf = ax.contourf(
        S, Z, F, levels=levels, cmap=cmap,
        norm=mcolors.Normalize(0.0, FES_MAX), extend="max",
    )
    ax.contour(
        S, Z, F, levels=np.arange(1, FES_MAX, 1),
        colors="white", linewidths=0.45, alpha=0.5,
    )

    # UPPER_WALLS guide line (drawn at sqrt(2.5 A^2) = 1.581 A on RMSD axis)
    ax.axhline(UPPER_WALL_ANG, color="white", linestyle=(0, (4, 2)),
               linewidth=0.8, alpha=0.6)

    # start.gro marker (s=7.09, z=1.30 A on RMSD axis)
    if show_star:
        ax.scatter(
            [START_S], [START_Z_ANG], marker="*", s=340,
            facecolor="#ff3d3d", edgecolor="white", linewidth=1.4, zorder=6,
        )
        ax.text(
            START_S + 0.4, START_Z_ANG - 0.04, "start.gro",
            fontsize=9, color="white", va="center", ha="left",
            bbox=dict(facecolor="black", alpha=0.45, edgecolor="none",
                      boxstyle="round,pad=0.2"),
        )

    # Combined tag + title (no overlapping large tag)
    ax.set_title(f"({tag})   {title}", fontsize=12.5, loc="left", pad=6, weight="bold")

    ax.set_xlabel(r"path.s   (progression  1WDW  $\rightarrow$  3CEP,   MODEL 1 $\rightarrow$ 15)",
                  fontsize=10.5)
    ax.set_ylabel(r"path.z   (off-path RMSD, Å)", fontsize=10.5)
    ax.set_xlim(*S_RANGE)
    ax.set_ylim(*Z_RANGE)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.set_yticks([0.0, 0.25, 0.50, 0.75, 1.00, 1.25, 1.50])
    ax.tick_params(direction="out", length=3.5, labelsize=9.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.9)
        spine.set_color("0.25")
    return cf


def main() -> None:
    assert BASELINE.exists()
    assert PILOT.exists()

    s_a, z_a = load_colvar(BASELINE)
    s_b, z_b = load_colvar(PILOT)

    print(f"a  naive   45324928  n={len(s_a):>6d}  "
          f"s∈[{s_a.min():.2f}, {s_a.max():.2f}]  z∈[{z_a.min():.2f}, {z_a.max():.2f}]")
    print(f"b  seqaln  45515869  n={len(s_b):>6d}  "
          f"s∈[{s_b.min():.2f}, {s_b.max():.2f}]  z∈[{z_b.min():.2f}, {z_b.max():.2f}]")
    print(f"   walker exploration widened from s<{s_a.max():.1f} to s<{s_b.max():.1f}  "
          f"({s_b.max()/s_a.max():.1f}× wider in max-s)")

    Sa, Za, Fa = fes(s_a, z_a)
    Sb, Zb, Fb = fes(s_b, z_b)

    # ------------------------------------------------------------------
    # Layout: wider fig, tall caption row under each panel, separate cbar
    # ------------------------------------------------------------------
    plt.rcParams["font.family"] = "DejaVu Sans"  # Helvetica missing glyph fallback
    plt.rcParams["axes.titlepad"] = 6

    fig = plt.figure(figsize=(13.6, 5.9), constrained_layout=False)
    gs = fig.add_gridspec(
        nrows=2, ncols=3,
        width_ratios=[1.0, 1.0, 0.03],
        height_ratios=[1.0, 0.18],
        left=0.055, right=0.955, top=0.87, bottom=0.08,
        wspace=0.18, hspace=0.22,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[0, 2])
    cap_a = fig.add_subplot(gs[1, 0]); cap_a.axis("off")
    cap_b = fig.add_subplot(gs[1, 1]); cap_b.axis("off")

    panel(ax_a, Sa, Za, Fa,
          tag="a",
          title="Naive path   (pre-FP-034)",
          show_star=False)
    cf_b = panel(ax_b, Sb, Zb, Fb,
                 tag="b",
                 title="Sequence-aligned path   (post-FP-034)",
                 show_star=True)

    cap_a.text(
        0.0, 1.0,
        "single walker   ·   job 45324928   ·   16 ns\n"
        f"n = {len(s_a):,} frames   ·   "
        f"s ∈ [{s_a.min():.2f},  {s_a.max():.2f}]   ·   "
        "75 % of time at s < 1.25",
        transform=cap_a.transAxes, fontsize=9.8, va="top", ha="left",
        color="0.15",
    )
    cap_b.text(
        0.0, 1.0,
        "single walker   ·   job 45515869   ·   8 ns\n"
        f"n = {len(s_b):,} frames   ·   "
        f"s ∈ [{s_b.min():.2f},  {s_b.max():.2f}]   ·   "
        f"exposes s = 1 – 12 region ({s_b.max()/s_a.max():.1f}× wider in max-s)",
        transform=cap_b.transAxes, fontsize=9.8, va="top", ha="left",
        color="0.15",
    )

    cbar = fig.colorbar(cf_b, cax=cax, extend="max")
    cbar.set_label(r"free energy  (kcal mol$^{-1}$)", fontsize=10)
    cbar.ax.tick_params(labelsize=9)
    cbar.set_ticks([0, 1, 2, 3, 4, 5, 6])

    fig.suptitle(
        "FES(s, z)   ·   same start.gro, same Miguel MetaD contract, only path.pdb differs",
        fontsize=12.5, weight="bold", y=0.965,
    )

    fig.savefig(OUT, dpi=220, bbox_inches="tight")
    print(f"\nwrote {OUT}  ({OUT.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
