#!/usr/bin/env python3
"""Before/after path realignment s(t) comparison."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
DATA = ROOT / "codex_renders" / "data"

PRE = RAW / "longleaf_initial_single_COLVAR"
POST = DATA / "initial_pilot_latest_COLVAR"
OUT_PNG = ROOT / "before_after_fp034.png"
OUT_PDF = ROOT / "before_after_fp034.pdf"


def read_colvar(path: Path) -> tuple[np.ndarray, np.ndarray]:
    arr = np.loadtxt(path, comments="#")
    return arr[:, 0] / 1000.0, arr[:, 1]


def style_axis(ax: plt.Axes, *, title: str) -> None:
    ax.set_title(title, fontsize=9.7, weight="bold", loc="left")
    ax.set_xlim(0, 25)
    ax.set_ylim(0, 16)
    ax.set_xticks([0, 5, 10, 15, 20, 25])
    ax.set_yticks([0, 2, 6, 10, 14])
    for y, label in [(2, "O boundary"), (6, "PC boundary"), (10, "C boundary")]:
        ax.axhline(y, color="0.35", lw=0.65, ls="--", alpha=0.7)
        ax.text(24.6, y + 0.15, label, ha="right", va="bottom", fontsize=6.8, color="0.25")
    ax.grid(axis="y", color="0.88", lw=0.45)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def main() -> None:
    if not PRE.exists() or not POST.exists():
        raise FileNotFoundError("required COLVAR file missing")
    t_pre, s_pre = read_colvar(PRE)
    t_post, s_post = read_colvar(POST)

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.6,
            "axes.labelsize": 9.3,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "savefig.dpi": 200,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(7.8, 3.95), sharey=True)
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.17, top=0.78, wspace=0.13)

    axes[0].plot(t_pre, s_pre, color="#475569", lw=1.05)
    axes[1].plot(t_post, s_post, color="#0f766e", lw=0.95)
    style_axis(axes[0], title="Before alignment fix")
    style_axis(axes[1], title="After alignment fix (current 24 ns)")

    axes[0].set_ylabel("s = Open→Closed path coordinate (dimensionless)")
    for ax in axes:
        ax.set_xlabel("t (ns)")

    axes[0].text(
        0.045,
        0.90,
        "17.7 ns: walker stuck at s<1.9\nnaive residue-number pairing across two chains\nof different length; λ=3.80 Å$^{-2}$",
        transform=axes[0].transAxes,
        ha="left",
        va="top",
        fontsize=7.4,
        color="white",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="#334155", alpha=0.88, lw=0),
    )
    axes[1].text(
        0.045,
        0.90,
        "24.0 ns: full O→C path explored\nmax_s=14.05 after NW alignment\nλ=100.79 Å$^{-2}$ self-consistent",
        transform=axes[1].transAxes,
        ha="left",
        va="top",
        fontsize=7.4,
        color="white",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="#115e59", alpha=0.90, lw=0),
    )
    fig.text(
        0.075,
        0.94,
        "Path realignment expanded the conformations the walker can explore",
        ha="left",
        va="top",
        fontsize=12,
        weight="bold",
    )
    fig.text(
        0.075,
        0.885,
        "Initial pilot single-walker MetaD trajectory: residue-number-paired path (original) vs sequence-aligned path (current)",
        ha="left",
        va="top",
        fontsize=8.2,
        color="0.22",
    )
    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    print(f"wrote {OUT_PNG}")
    print(f"wrote {OUT_PDF}")
    print(f"pre_ns={t_pre[-1]:.4f} pre_max_s={np.max(s_pre):.4f}")
    print(f"post_ns={t_post[-1]:.4f} post_max_s={np.max(s_post):.4f}")


if __name__ == "__main__":
    main()
