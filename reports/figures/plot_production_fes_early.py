"""Render early 10-walker shared-HILLS production FES via Python sum_hills.

Workaround: local machine has no `plumed` binary; this script implements
multivariate-diagonal Gaussian sum_hills equivalent in pure Python/NumPy.
For deck-quality FES once production reaches 10 ns/walker, use the Codex R5
PLUMED command on Longleaf compute and `plot_production_fes_snapshot.py`.

Usage:
    python3 reports/figures/plot_production_fes_early.py \
        reports/figures/raw_data/production_fes_early/ \
        --biasfactor 10 \
        --label "early-fingerprint, ~50 ps/walker × 9 walkers"

Caveat per Codex R5 §Q2a: <10 ns/walker is "early fingerprint, no basin-depth
claims". Tag PROVISIONAL or even TENTATIVE.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent


def parse_hills(path: Path) -> np.ndarray:
    rows = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cols = line.split()
            if len(cols) < 8:
                continue
            try:
                rows.append([float(x) for x in cols[:8]])
            except ValueError:
                continue
    return np.array(rows, dtype=float)


def sum_hills_fes(
    hills: np.ndarray,
    s_grid: np.ndarray,
    z_grid: np.ndarray,
    biasfactor: float,
) -> np.ndarray:
    S, Z = np.meshgrid(s_grid, z_grid, indexing="ij")
    if hills.size == 0:
        return np.zeros_like(S)
    s_h = hills[:, 1][:, None, None]
    z_h = hills[:, 2][:, None, None]
    sigma_s = hills[:, 3][:, None, None]
    sigma_z = hills[:, 4][:, None, None]
    height = hills[:, 6][:, None, None]
    ds = (S[None, :, :] - s_h) / sigma_s
    dz = (Z[None, :, :] - z_h) / sigma_z
    gauss = height * np.exp(-0.5 * (ds**2 + dz**2))
    V_bias = gauss.sum(axis=0)
    F = -(1.0 - 1.0 / biasfactor) * V_bias
    return F


def render_fes(
    hills_dir: Path,
    out_dir: Path,
    biasfactor: float,
    label: str,
    convergence_grade: str = "TENTATIVE",
) -> None:
    hills_files = sorted(hills_dir.glob("HILLS.*"))
    if not hills_files:
        raise FileNotFoundError(f"no HILLS.* files in {hills_dir}")
    print(f"Found {len(hills_files)} HILLS files in {hills_dir.name}/")
    all_hills = []
    n_per_walker = []
    for hf in hills_files:
        h = parse_hills(hf)
        all_hills.append(h)
        n_per_walker.append((hf.name, len(h),
                             float(h[-1, 0]) if len(h) > 0 else 0.0))
    combined = np.concatenate(all_hills, axis=0) if all_hills else np.zeros((0, 8))
    print(f"Total hills across {len(hills_files)} walkers: {len(combined)}")
    for name, n, last_t in n_per_walker:
        print(f"  {name}: {n} hills, last_t={last_t:.1f} ps")

    s_grid = np.linspace(0.5, 15.5, 300)
    z_grid = np.linspace(0.0, 2.8, 100)
    F = sum_hills_fes(combined, s_grid, z_grid, biasfactor)
    F = F - F.min()  # zero baseline
    F_clipped = np.clip(F, 0, max(F.max(), 14))

    cmap = plt.get_cmap("RdYlBu_r").copy()
    cmap.set_bad("white")

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=200)
    im = ax.pcolormesh(s_grid, z_grid, F_clipped.T, shading="auto",
                       cmap=cmap, vmin=0, vmax=min(14, F_clipped.max()))
    if F_clipped.max() > 1.5:
        ax.contour(s_grid, z_grid, F_clipped.T,
                   levels=np.arange(0, max(15, int(F_clipped.max())), 2),
                   colors="k", linewidths=0.35, alpha=0.45)

    ax.set_xlim(0.8, 15.2)
    ax.set_ylim(0.0, 2.8)
    ax.set_xlabel("s = Open→Closed path coordinate", fontsize=11)
    ax.set_ylabel("z = path.zzz (Å²)", fontsize=11)

    ax.axvline(2.0, ls=":", color="white", linewidth=0.8, alpha=0.7)
    ax.axvline(4.0, ls=":", color="white", linewidth=0.8, alpha=0.7)
    ax.axvline(6.0, ls=":", color="white", linewidth=0.8, alpha=0.7)
    ax.axvline(10.0, ls=":", color="white", linewidth=0.8, alpha=0.7)
    ax.text(1.0, 2.6, "O", color="white", fontweight="bold", fontsize=11)
    ax.text(5.0, 2.6, "PC", color="white", fontweight="bold", fontsize=11)
    ax.text(11.0, 2.6, "C", color="white", fontweight="bold", fontsize=11)

    ax.axhline(2.5, ls="--", lw=0.8, color="0.4", label="UPPER_WALLS AT=2.5")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.85)

    title = (f"10-walker shared-HILLS production FES — {label}\n"
             f"(BIASFACTOR={biasfactor}, {len(combined)} total hills "
             f"across {len(hills_files)} walkers; convergence_grade={convergence_grade})")
    ax.set_title(title, fontsize=9)

    cb = fig.colorbar(im, ax=ax)
    cb.set_label("ΔG (kcal/mol)")
    fig.tight_layout()

    out_png = out_dir / "production_fes_early_10walker.png"
    out_pdf = out_dir / "production_fes_early_10walker.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"\nSaved: {out_png}")
    print(f"Saved: {out_pdf}")
    print(f"\nFES range: [{F.min():.2f}, {F.max():.2f}] kcal/mol")
    # Basin minima diagnostic
    s_O_mask = (s_grid >= 0.5) & (s_grid <= 2.0)
    s_PC_mask = (s_grid >= 4.0) & (s_grid <= 6.0)
    s_C_mask = (s_grid >= 10.0) & (s_grid <= 12.0)
    F_min_O = F[s_O_mask, :].min() if s_O_mask.any() else float("nan")
    F_min_PC = F[s_PC_mask, :].min() if s_PC_mask.any() else float("nan")
    F_min_C = F[s_C_mask, :].min() if s_C_mask.any() else float("nan")
    print(f"\nBasin minima (kcal/mol, raw, NOT block-bootstrapped, NOT converged):")
    print(f"  F_min(O)  = {F_min_O:.2f}")
    print(f"  F_min(PC) = {F_min_PC:.2f}")
    print(f"  F_min(C)  = {F_min_C:.2f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("hills_dir", type=Path,
                    help="directory containing HILLS.* files (one per walker)")
    ap.add_argument("--out-dir", type=Path, default=HERE)
    ap.add_argument("--biasfactor", type=float, default=10.0,
                    help="MetaD biasfactor (PRIMARY=10 per Miguel email)")
    ap.add_argument("--label", type=str, default="early fingerprint")
    ap.add_argument("--convergence-grade", type=str, default="TENTATIVE",
                    choices=["TENTATIVE", "PROVISIONAL", "PASS"])
    args = ap.parse_args()
    render_fes(
        args.hills_dir.expanduser().resolve(),
        args.out_dir.expanduser().resolve(),
        args.biasfactor,
        args.label,
        args.convergence_grade,
    )


if __name__ == "__main__":
    main()
