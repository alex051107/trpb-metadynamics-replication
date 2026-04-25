#!/usr/bin/env python3
"""Render JACS-style 2D FES snapshots from PLUMED sum_hills grids."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


def read_fes(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    data = np.loadtxt(path, comments="#")
    if data.ndim != 2 or data.shape[1] < 3:
        raise ValueError(f"expected at least 3 columns in {path}")
    s_axis = np.unique(data[:, 0])
    z_axis_raw = np.unique(data[:, 1])
    expected = len(s_axis) * len(z_axis_raw)
    if data.shape[0] != expected:
        raise ValueError(
            f"grid row count mismatch: got {data.shape[0]}, expected {expected}"
        )
    # PLUMED writes s fastest for each z block, so reshape as (z, s).
    free = data[:, 2].reshape(len(z_axis_raw), len(s_axis))
    free = free - np.nanmin(free)
    z_axis = np.sqrt(np.maximum(z_axis_raw, 0.0))
    return s_axis, z_axis, free


def parse_counts(text: str) -> tuple[int | None, str]:
    text = text.strip()
    if not text:
        return None, ""
    total = 0
    parts: list[str] = []
    for token in text.replace(",", " ").split():
        if ":" not in token:
            continue
        name, value = token.split(":", 1)
        n = int(value)
        total += n
        parts.append(f"{name}:{n}")
    return total, " ".join(parts)


def draw(args: argparse.Namespace) -> None:
    s_axis, z_axis, free = read_fes(args.fes)
    finite_max = float(np.nanmax(free))
    vmax = min(args.vmax, finite_max) if finite_max > args.vmax else finite_max
    if vmax <= 0:
        vmax = args.vmax
    shown = np.clip(free, 0, vmax)

    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 11,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.dpi": 450,
        }
    )

    fig, ax = plt.subplots(figsize=(7.4, 4.95), dpi=220)
    fig.subplots_adjust(left=0.105, right=0.875, bottom=0.13, top=0.82)
    cmap = plt.get_cmap(args.cmap).copy()
    cmap.set_bad("white")

    mesh = ax.pcolormesh(
        s_axis,
        z_axis,
        shown,
        shading="auto",
        cmap=cmap,
        vmin=0,
        vmax=vmax,
        rasterized=True,
    )

    levels = np.arange(0, max(args.contour_step, vmax + args.contour_step), args.contour_step)
    levels = levels[(levels > 0) & (levels < vmax)]
    if len(levels):
        ax.contour(
            s_axis,
            z_axis,
            shown,
            levels=levels,
            colors="black",
            linewidths=0.34,
            alpha=0.5,
        )

    ax.set_xlim(args.xmin, args.xmax)
    ax.set_ylim(args.ymin, args.ymax)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.set_xlabel("Open-to-Closed Path")
    ax.set_ylabel(r"$z_{\mathrm{RMSD}}=\sqrt{p1.zzz}$ ($\AA$)")
    total_hills, counts_text = parse_counts(args.hills_counts)
    if total_hills is None:
        total_label = args.total_hills or "not recorded"
    else:
        total_label = f"{total_hills:,}"

    fig.text(0.105, 0.945, args.title, ha="left", va="top", fontsize=13.2, weight="bold")
    fig.text(
        0.105,
        0.895,
        f"{args.convergence_grade} - {args.subtitle} | total hills: {total_label}",
        ha="left",
        va="top",
        fontsize=9.4,
        color="#1f2937",
    )

    ax.text(
        0.012,
        0.018,
        args.footer,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=8.1,
        color="white",
        bbox=dict(boxstyle="square,pad=0.25", facecolor="black", alpha=0.62, lw=0),
    )

    for label, x, y in [("O", 1.25, 0.28), ("PC", 5.2, 0.28), ("C", 11.3, 0.28)]:
        ax.text(
            x,
            y,
            label,
            ha="center",
            va="center",
            fontsize=10.5,
            weight="bold",
            color="white",
            bbox=dict(boxstyle="square,pad=0.22", facecolor="black", alpha=0.58, lw=0),
        )

    wall_y = 2.5 ** 0.5
    ax.axhline(wall_y, color="#4b5563", ls="--", lw=0.8, alpha=0.85)
    ax.text(
        15.08,
        wall_y + 0.015,
        "wall",
        ha="right",
        va="bottom",
        fontsize=8,
        color="#374151",
    )

    ax.grid(False)
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_linewidth(0.8)
    ax.spines["bottom"].set_linewidth(0.8)

    cbar = fig.colorbar(mesh, ax=ax, pad=0.018, fraction=0.045)
    cbar.set_label("$\\Delta G$ (kcal mol$^{-1}$)")
    cbar.set_ticks(np.arange(0, np.floor(vmax / 2) * 2 + 0.1, 2))
    if finite_max > vmax:
        cbar.ax.text(
            0.5,
            1.015,
            f">={vmax:g}",
            transform=cbar.ax.transAxes,
            ha="center",
            va="bottom",
            fontsize=8,
        )

    out_png = args.out_png
    out_pdf = args.out_pdf or out_png.with_suffix(".pdf")
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.035)
    fig.savefig(out_pdf, bbox_inches="tight", pad_inches=0.035)
    plt.close(fig)

    meta = out_png.with_suffix(".meta.txt")
    meta.write_text(
        "\n".join(
            [
                f"fes={args.fes}",
                f"out_png={out_png}",
                f"out_pdf={out_pdf}",
                f"finite_f_kcalmol_max={finite_max:.6f}",
                f"color_vmax={vmax:.6f}",
                f"total_hills={total_label}",
                f"hills_counts={counts_text}",
                f"convergence_grade={args.convergence_grade}",
            ]
        )
        + "\n"
    )
    print(f"wrote {out_png}")
    print(f"wrote {out_pdf}")
    print(f"wrote {meta}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fes", type=Path, required=True)
    parser.add_argument("--out-png", type=Path, required=True)
    parser.add_argument("--out-pdf", type=Path)
    parser.add_argument("--title", default="10-walker production FES")
    parser.add_argument(
        "--subtitle",
        default="early 10-walker fingerprint, NOT converged",
    )
    parser.add_argument("--convergence-grade", default="TENTATIVE")
    parser.add_argument(
        "--footer",
        default="L0/L1 fingerprint only - not a thermodynamic label",
    )
    parser.add_argument("--hills-counts", default="")
    parser.add_argument("--total-hills", default="")
    parser.add_argument("--cmap", default="jet")
    parser.add_argument("--vmax", type=float, default=14.0)
    parser.add_argument("--contour-step", type=float, default=2.0)
    parser.add_argument("--xmin", type=float, default=0.5)
    parser.add_argument("--xmax", type=float, default=15.5)
    parser.add_argument("--ymin", type=float, default=0.0)
    parser.add_argument("--ymax", type=float, default=2.8 ** 0.5)
    args = parser.parse_args()
    draw(args)


if __name__ == "__main__":
    main()
