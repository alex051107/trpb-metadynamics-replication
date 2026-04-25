"""Single-panel pilot (s, z) 2D-density figure in unit-correct JACS Fig 3 style.

Replaces the earlier sz_2d_pilot_jacs_style.png that plotted raw `path.zzz`
under an Angstrom label. PLUMED writes `path.zzz` in MSD units (Å²) when
`UNITS LENGTH=A` is set, so plotting it under "z (Å)" is a unit lie. This
script takes sqrt(p1.zzz) on the y-axis so the axis reads in Å (per-atom
RMSD deviation), matching the JACS 2019 SI Fig 3 convention.

Independent verification: Codex CCB task `20260424-234500`. Full unit chain
in deliverables/week7_2026-04-24/08_figures/UNIT_AUDIT.md.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
COLVAR_PATH = REPO / "reports" / "figures" / "raw_data" / "longleaf_initial_seqaligned_COLVAR"
OUT = HERE / "sz_2d_pilot_jacs_style.png"

UPPER_WALL_Z_RAW = 2.5
UPPER_WALL_Z_ANG = float(np.sqrt(UPPER_WALL_Z_RAW))


def main() -> None:
    if not COLVAR_PATH.exists():
        raise FileNotFoundError(COLVAR_PATH)

    arr = np.loadtxt(COLVAR_PATH, comments="#")
    t_ps = arr[:, 0]
    s = arr[:, 1]
    z_a2 = np.clip(arr[:, 2], 0.0, None)
    z_ang = np.sqrt(z_a2)
    n = len(arr)
    duration_ns = float(t_ps[-1]) / 1000.0

    s0 = float(s[0])
    z0_a2 = float(z_a2[0])
    z0_ang = float(z_ang[0])
    s_min = float(np.min(s))
    s_max = float(np.max(s))
    t_min = float(t_ps[int(np.argmin(s))]) / 1000.0
    t_max = float(t_ps[int(np.argmax(s))]) / 1000.0

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.linewidth": 0.9,
        "savefig.dpi": 300,
    })

    fig, ax = plt.subplots(figsize=(7.6, 5.2))

    h, xedges, yedges = np.histogram2d(
        s, z_ang,
        bins=[120, 70],
        range=[[0.5, 15.5], [0.0, 1.7]],
    )
    h_log = np.log10(h.T + 1.0)
    im = ax.imshow(
        h_log,
        origin="lower",
        extent=(xedges[0], xedges[-1], yedges[0], yedges[-1]),
        aspect="auto",
        cmap="viridis",
        norm=colors.Normalize(vmin=0.0, vmax=np.max(h_log)),
    )

    ax.axhline(
        UPPER_WALL_Z_ANG, color="white",
        linestyle=(0, (4, 2)), linewidth=1.0, alpha=0.85,
    )
    ax.text(
        14.6, UPPER_WALL_Z_ANG - 0.05,
        f"UPPER_WALLS: $\\sqrt{{2.5}}$ = {UPPER_WALL_Z_ANG:.2f} $\\AA$",
        color="white", fontsize=8.5, ha="right", va="top",
    )

    ax.scatter(
        [s0], [z0_ang], marker="s", s=110, facecolor="white",
        edgecolor="black", linewidth=1.4, zorder=6,
    )
    ax.annotate(
        f"start.gro\n(s = {s0:.2f}, $\\sqrt{{p1.zzz}}$ = {z0_ang:.2f} $\\AA$)",
        xy=(s0, z0_ang), xytext=(s0 + 1.2, z0_ang + 0.18),
        fontsize=8.5, color="white",
        arrowprops=dict(arrowstyle="-", color="white", lw=0.6),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="black",
                  alpha=0.55, edgecolor="none"),
    )

    s_minarg = int(np.argmin(s))
    z_at_smin_ang = float(z_ang[s_minarg])
    ax.scatter(
        [s_min], [z_at_smin_ang], marker="o", s=110,
        facecolor="#1eba6f", edgecolor="white", linewidth=1.0, zorder=5,
    )
    ax.text(
        s_min + 0.15, z_at_smin_ang + 0.05,
        f"min s = {s_min:.3f}\n@ t = {t_min:.2f} ns",
        fontsize=8.0, color="white",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="black",
                  alpha=0.55, edgecolor="none"),
    )

    s_maxarg = int(np.argmax(s))
    z_at_smax_ang = float(z_ang[s_maxarg])
    ax.scatter(
        [s_max], [z_at_smax_ang], marker="o", s=110,
        facecolor="#ff5050", edgecolor="white", linewidth=1.0, zorder=5,
    )
    ax.text(
        s_max - 0.2, z_at_smax_ang + 0.05,
        f"max s = {s_max:.2f}\n@ t = {t_max:.2f} ns",
        fontsize=8.0, color="white", ha="right",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="black",
                  alpha=0.55, edgecolor="none"),
    )

    ax.set_xlim(0.5, 15.5)
    ax.set_ylim(0.0, 1.7)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.set_yticks([0.0, 0.4, 0.8, 1.2, 1.6])
    ax.set_xlabel(r"$s(R)$ — path progress coordinate (dimensionless)", fontsize=10.5)
    ax.set_ylabel(r"RMSD Deviation ($\AA$)  =  $\sqrt{p1.zzz}$ — off-path",
                  fontsize=10.5)

    ax.text(0.02, 0.96, "Open  (s = 1)", transform=ax.transAxes,
            fontsize=9.5, color="white", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="black",
                      alpha=0.55, edgecolor="none"))
    ax.text(0.98, 0.96, "Closed  (s = 15)", transform=ax.transAxes,
            fontsize=9.5, color="white", fontweight="bold", ha="right",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="black",
                      alpha=0.55, edgecolor="none"))

    fig.suptitle(
        f"Pilot 45515869 — $(s, \\sqrt{{p1.zzz}})$ density, "
        f"{n:,} frames / {duration_ns:.2f} ns on FP-034 corrected path",
        fontsize=11.0, fontweight="bold", y=0.985,
    )
    fig.text(
        0.5, 0.945,
        "y-axis is unit-correct (Å) — matches JACS 2019 SI Fig 3 convention",
        ha="center", va="top", fontsize=8.5, color="0.30",
    )

    cbar = fig.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label(r"$\log_{10}$(frame count + 1)", fontsize=9.5)
    cbar.ax.tick_params(labelsize=8.5)

    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.92))
    fig.savefig(OUT, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
