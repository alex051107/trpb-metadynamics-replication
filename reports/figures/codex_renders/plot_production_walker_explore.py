#!/usr/bin/env python3
"""Render 10-panel production walker s(t) progress."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "codex_renders" / "data" / "production_walker_colvars"
OUT_PNG = ROOT / "production_walker_explore.png"
OUT_PDF = ROOT / "production_walker_explore.pdf"


def read_manifest() -> dict[str, tuple[float, float]]:
    path = DATA / "seed_manifest.tsv"
    seeds: dict[str, tuple[float, float]] = {}
    if not path.exists():
        return seeds
    with path.open() as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            wid = f"walker_{int(row['walker_id']):02d}"
            seeds[wid] = (float(row["s"]), float(row["z"]) ** 0.5)
    return seeds


def read_colvar(path: Path) -> np.ndarray:
    return np.loadtxt(path, comments="#")


def main() -> None:
    files = sorted(DATA.glob("walker_*_COLVAR"))
    if len(files) != 10:
        raise FileNotFoundError(f"expected 10 walker COLVAR files, got {len(files)}")
    seeds = read_manifest()
    walkers = {p.name[:9]: read_colvar(p) for p in files}
    avg_ns = sum(arr[-1, 0] for arr in walkers.values()) / len(walkers) / 1000.0
    max_t = max(float(arr[-1, 0]) for arr in walkers.values())
    max_s = max(float(np.max(arr[:, 1])) for arr in walkers.values())

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 7.5,
            "axes.labelsize": 8,
            "axes.titlesize": 7.6,
            "xtick.labelsize": 6.7,
            "ytick.labelsize": 6.7,
            "savefig.dpi": 200,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, axes = plt.subplots(2, 5, figsize=(7.9, 4.75), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.07, right=0.99, bottom=0.12, top=0.77, wspace=0.14, hspace=0.48)
    colors = plt.get_cmap("viridis")(np.linspace(0.08, 0.92, 10))

    for idx, (name, arr) in enumerate(sorted(walkers.items())):
        ax = axes.flat[idx]
        ax.plot(arr[:, 0], arr[:, 1], color=colors[idx], lw=0.9)
        for y in (2, 6, 10):
            ax.axhline(y, color="0.55", lw=0.45, ls="--", alpha=0.65)
        seed_s, seed_z = seeds.get(name, (float("nan"), float("nan")))
        short = name.replace("walker_", "w")
        ax.set_title(f"{short}: seed s={seed_s:.2f}, z={seed_z:.2f} Å", pad=2, fontsize=6.5)
        ax.set_xlim(0, max_t)
        ax.set_ylim(0, 15.5)
        ax.grid(axis="y", color="0.90", lw=0.35)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        if idx % 5 == 0:
            ax.set_ylabel("s")
        if idx >= 5:
            ax.set_xlabel("t (ps)")

    fig.text(
        0.07,
        0.955,
        f"10-walker production 45784112 — multi-walker shared HILLS, snapshot at {avg_ns:.2f} ns/walker average",
        ha="left",
        va="top",
        fontsize=10.5,
        weight="bold",
    )
    fig.text(
        0.07,
        0.902,
        "Dashed references: s=2 (O boundary), s=6 (PC), s=10 (C). Seed z values are RMSD Å.",
        ha="left",
        va="top",
        fontsize=7.8,
        color="0.25",
    )
    fig.text(0.5, 0.025, "time since production MetaD start (ps)", ha="center", fontsize=8.2)
    fig.savefig(OUT_PNG, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    print(f"wrote {OUT_PNG}")
    print(f"wrote {OUT_PDF}")
    print(f"avg_ns_per_walker={avg_ns:.4f}")
    print(f"max_walker_s={max_s:.4f}")
    print(f"max_t_ps={max_t:.1f}")


if __name__ == "__main__":
    main()
