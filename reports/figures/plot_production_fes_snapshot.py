"""Render 10-walker shared-HILLS production FES snapshot.

Reads `fes_sumhills.dat` produced by `plumed sum_hills --hills HILLS.0,...,HILLS.9
--mintozero --kt 0.695 --min 0.5,0.0 --max 15.5,2.8 --bin 300,100` (Codex R5 §Q2b)
and renders a 2D F(s, z) contour plot in the JACS 2019 SI Fig S2/S3 style.

Usage:
    # After plumed sum_hills produces fes_sumhills.dat in a snapshot dir
    python3 reports/figures/plot_production_fes_snapshot.py /path/to/fes_sumhills.dat

Caveats per Codex R5 §Q3c:
  - Only honest at ≥10 ns/walker (HILLS.N rows ≥ 5000)
  - Tag PROVISIONAL until convergence criteria pass (SI Fig S4/S5 ΔΔG plateau)
  - Do NOT report basin populations from this plot — it's L0/L1 fingerprint only
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def render(fes_path: Path, out_dir: Path | None = None,
           title_suffix: str = "10-walker production FES snapshot",
           sim_time_ns: float | None = None,
           convergence_grade: str = "PROVISIONAL") -> None:
    if out_dir is None:
        out_dir = fes_path.parent

    data = np.loadtxt(fes_path, comments="#")
    s = np.unique(data[:, 0])
    z = np.unique(data[:, 1])
    F = data[:, 2].reshape(len(s), len(z)).T
    F = F - np.nanmin(F)
    F_clipped = np.clip(F, 0, 14)

    cmap = plt.get_cmap("RdYlBu_r").copy()
    cmap.set_bad("white")

    fig, ax = plt.subplots(figsize=(7.0, 4.6), dpi=200)
    im = ax.pcolormesh(s, z, F_clipped, shading="auto", cmap=cmap, vmin=0, vmax=14)
    ax.contour(s, z, F_clipped, levels=np.arange(0, 15, 2),
               colors="k", linewidths=0.35, alpha=0.45)

    ax.set_xlim(0.8, 15.2)
    ax.set_ylim(0.0, 2.8)
    ax.set_xlabel("s = Open→Closed path coordinate", fontsize=11)
    ax.set_ylabel("z = path.zzz (Å²)", fontsize=11)

    # State labels
    ax.axvline(2.0, ls=":", color="white", linewidth=0.8, alpha=0.7)
    ax.axvline(4.0, ls=":", color="white", linewidth=0.8, alpha=0.7)
    ax.axvline(6.0, ls=":", color="white", linewidth=0.8, alpha=0.7)
    ax.axvline(10.0, ls=":", color="white", linewidth=0.8, alpha=0.7)
    ax.text(1.0, 2.6, "O", color="white", fontweight="bold", fontsize=11)
    ax.text(5.0, 2.6, "PC", color="white", fontweight="bold", fontsize=11)
    ax.text(11.0, 2.6, "C", color="white", fontweight="bold", fontsize=11)

    ax.axhline(2.5, ls="--", lw=0.8, color="0.4", label="UPPER_WALLS AT=2.5")
    ax.legend(loc="lower right", fontsize=8, framealpha=0.85)

    title_parts = [title_suffix]
    if sim_time_ns is not None:
        title_parts.append(f"~{sim_time_ns:.0f} ns/walker")
    title_parts.append(f"convergence_grade={convergence_grade}")
    ax.set_title(" — ".join(title_parts), fontsize=10)

    cb = fig.colorbar(im, ax=ax)
    cb.set_label("ΔG (kcal/mol)")
    fig.tight_layout()

    out_png = out_dir / "production_fes_snapshot.png"
    out_pdf = out_dir / "production_fes_snapshot.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Saved: {out_png}")
    print(f"Saved: {out_pdf}")

    # Numeric basin minima (Codex R5 §Q3 diagnostic input)
    s_O_mask = (s >= 0.5) & (s <= 2.0)
    s_PC_mask = (s >= 4.0) & (s <= 6.0)
    s_C_mask = (s >= 10.0) & (s <= 12.0)
    F_min_O = F[:, s_O_mask].min() if s_O_mask.any() else float("nan")
    F_min_PC = F[:, s_PC_mask].min() if s_PC_mask.any() else float("nan")
    F_min_C = F[:, s_C_mask].min() if s_C_mask.any() else float("nan")
    print(f"\nBasin minima (kcal/mol, raw, NOT block-bootstrapped):")
    print(f"  F_min(O) = {F_min_O:.2f}")
    print(f"  F_min(PC) = {F_min_PC:.2f}")
    print(f"  F_min(C) = {F_min_C:.2f}")
    print(f"  ΔG(PC − O) = {F_min_PC - F_min_O:.2f}")
    print(f"  ΔG(C − O)  = {F_min_C - F_min_O:.2f}")
    print(f"  ΔG(C − PC) = {F_min_C - F_min_PC:.2f}")


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: plot_production_fes_snapshot.py <path/to/fes_sumhills.dat> [sim_time_ns] [convergence_grade]")
        print("Example: ./plot_production_fes_snapshot.py /tmp/fes_sumhills.dat 10 PROVISIONAL")
        sys.exit(1)
    fes_path = Path(sys.argv[1]).expanduser().resolve()
    sim_time_ns = float(sys.argv[2]) if len(sys.argv) > 2 else None
    convergence_grade = sys.argv[3] if len(sys.argv) > 3 else "PROVISIONAL"
    render(fes_path, sim_time_ns=sim_time_ns, convergence_grade=convergence_grade)


if __name__ == "__main__":
    main()
