#!/usr/bin/env python3
"""Draw the L0/L1/L2/L3 ML conversion schematic."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT_PNG = ROOT / "ml_4tier_schematic.png"
OUT_PDF = ROOT / "ml_4tier_schematic.pdf"


def box(ax, xy, wh, text, fc, ec="#334155", fontsize=8.3, weight="normal"):
    x, y = xy
    w, h = wh
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.018,rounding_size=0.025",
        linewidth=0.9,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, weight=weight, color="#111827")
    return patch


def arrow(ax, start, end, color="#475569", lw=1.0):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10, linewidth=lw, color=color))


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "savefig.dpi": 200,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=(7.7, 4.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    fig.text(
        0.05,
        0.955,
        "ML conversion 4-tier framework: each tier maps to a different role in the general training pipeline",
        ha="left",
        va="top",
        fontsize=10.5,
        weight="bold",
    )

    source = box(
        ax,
        (0.34, 0.79),
        (0.32, 0.09),
        "MetaD raw output\nCOLVAR + HILLS",
        "#e0f2fe",
        ec="#0369a1",
        fontsize=8.8,
        weight="bold",
    )

    xs = [0.08, 0.315, 0.55, 0.785]
    w = 0.17
    tier_y = 0.52
    role_y = 0.22
    tiers = [
        ("L0 descriptors\ns, z, time\nwalker, bias", "#dcfce7", "#166534"),
        ("L1 state labels\nO / PC / C / off", "#dcfce7", "#166534"),
        ("L2 free energy\nF(s,z), masks\nconvergence gate", "#fef3c7", "#92400e"),
        ("L3 candidate rank\nF0 + PathGate\ncombined rank", "#fef3c7", "#92400e"),
    ]
    roles = [
        ("ML role\nINPUT\nFEATURE", "#f0fdf4", "#166534"),
        ("ML role\nCLASSIFICATION\nTARGET", "#f0fdf4", "#166534"),
        ("ML role\nREGRESSION\nTARGET\nLOCK: PASS", "#fffbeb", "#92400e"),
        ("ML role\nOUTPUT\nLOCK: L2 +\nactivity proxy", "#fffbeb", "#92400e"),
    ]

    for i, x in enumerate(xs):
        box(ax, (x, tier_y), (w, 0.16), tiers[i][0], tiers[i][1], ec=tiers[i][2], fontsize=7.8, weight="bold")
        box(ax, (x, role_y), (w, 0.18), roles[i][0], roles[i][1], ec=roles[i][2], fontsize=7.2, weight="bold")
        arrow(ax, (0.50, 0.79), (x + w / 2, tier_y + 0.16), color="#475569", lw=0.9)
        arrow(ax, (x + w / 2, tier_y), (x + w / 2, role_y + 0.18), color=tiers[i][2], lw=1.05)

    ax.text(
        0.50,
        0.47,
        "Available immediately",
        ha="center",
        va="center",
        fontsize=7.4,
        color="#166534",
        bbox=dict(boxstyle="round,pad=0.22", facecolor="#dcfce7", edgecolor="#166534", lw=0.7),
    )
    ax.text(
        0.74,
        0.47,
        "Gate-controlled",
        ha="center",
        va="center",
        fontsize=7.4,
        color="#92400e",
        bbox=dict(boxstyle="round,pad=0.22", facecolor="#fef3c7", edgecolor="#92400e", lw=0.7),
    )
    ax.text(
        0.55,
        0.105,
        "Do not train L2/L3 claims until convergence_grade.status=PASS and PM chooses the activity-proxy contract.",
        ha="left",
        va="center",
        fontsize=7.4,
        color="#374151",
    )

    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    print(f"wrote {OUT_PNG}")
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
