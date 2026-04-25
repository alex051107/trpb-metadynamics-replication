"""SI Fig S4/S5-style ΔΔG-vs-time convergence diagnostic.

Reproduces the diagnostic style used in JACS 2019 SI Fig S4 + S5
(ja9b03646_si_001.pdf p.S10): for each candidate FEL "region", plot the
free-energy minimum within that region as a function of MetaD simulation time,
to assess convergence (curves should plateau when FES is converged).

Methodology:
  1. Sum HILLS up to each time cutoff t = 1, 2, ..., max_t ns.
  2. At each cutoff, compute F(s, z) = -(1 - 1/biasfactor) * Σ height * G(...).
  3. ΔG of region X = min(F where s ∈ region_X bounds).
  4. Plot ΔG_O(t), ΔG_PC(t), ΔG_C(t) and pairwise ΔΔG(t) vs t.

Caveat: pilot uses Miguel FALLBACK contract (HEIGHT=0.3, BIASFACTOR=15);
production uses PRIMARY (0.15, 10). Pilot ΔΔG-vs-time is ONLY a diagnostic
methodology demo, NOT the final SI-comparable result. Production 10-walker
v3 (job 45784112, launched 2026-04-25) will produce the comparable plot
once 5-50 ns of HILLS accumulate per walker.

Run:
    python3 reports/figures/plot_si_style_convergence.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "raw_data"
HILLS_PATH = DATA_DIR / "longleaf_initial_seqaligned_HILLS"

# Pilot contract (Miguel fallback)
BIASFACTOR_PILOT = 15.0

# State regions (s ranges)
REGIONS = {
    "O": (0.5, 2.0),
    "PC": (4.0, 6.0),
    "C": (10.0, 12.0),
}
REGION_COLORS = {
    "O": "#1f77b4",
    "PC": "#2ca02c",
    "C": "#d62728",
}


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
    """Return F(s, z) in kcal/mol from a Gaussian sum of HILLS rows.

    Uses multivariate-diagonal approximation (ignores σ_zs cross-correlation).
    Sufficient for ΔG-region diagnostic; full multivariate would need eigendecomp.
    """
    S, Z = np.meshgrid(s_grid, z_grid, indexing="ij")
    V = np.zeros_like(S)
    if hills.size == 0:
        return V
    # Vectorized Gaussian sum
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


def region_min_F(
    F: np.ndarray, s_grid: np.ndarray, lo: float, hi: float
) -> float:
    s_mask = (s_grid >= lo) & (s_grid <= hi)
    if not s_mask.any():
        return float("nan")
    return float(F[s_mask, :].min())


def render() -> None:
    hills = parse_hills(HILLS_PATH)
    print(f"Loaded {len(hills)} HILLS rows; max time = {hills[-1, 0]:.1f} ps "
          f"({hills[-1, 0]/1000:.2f} ns)")

    s_grid = np.linspace(0.0, 15.0, 200)
    z_grid = np.linspace(0.0, 2.5, 60)

    max_t_ns = hills[-1, 0] / 1000.0
    time_cutoffs_ns = np.arange(1.0, max_t_ns + 0.5, 1.0)

    F_min_by_region = {region: [] for region in REGIONS}
    for t in time_cutoffs_ns:
        mask = hills[:, 0] <= t * 1000.0
        F = sum_hills_fes(hills[mask], s_grid, z_grid, BIASFACTOR_PILOT)
        F = F - F.min()  # zero-baseline at global minimum so curves are absolute
        for region, (lo, hi) in REGIONS.items():
            F_min_by_region[region].append(region_min_F(F, s_grid, lo, hi))

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12, 4.5))

    # ---- Panel A: F_min(region, t) — same style as ΔΔG curves ----
    for region in REGIONS:
        F_vals = np.array(F_min_by_region[region])
        ax_a.plot(time_cutoffs_ns, F_vals, marker="o", markersize=4,
                  color=REGION_COLORS[region], linewidth=1.5,
                  label=f"{region}-region min F")
    ax_a.set_xlabel("Simulation time (ns)")
    ax_a.set_ylabel("F (kcal/mol, region minimum)")
    ax_a.set_title("(a) Per-region free-energy minimum vs time\n"
                   "(SI Fig S4/S5 style — pilot fallback contract demo)",
                   fontsize=10)
    ax_a.legend(loc="upper right", fontsize=9)
    ax_a.grid(alpha=0.3, linestyle="--")
    ax_a.set_xlim(0, max_t_ns + 1)

    # ---- Panel B: ΔΔG between regions ----
    F_O = np.array(F_min_by_region["O"])
    F_PC = np.array(F_min_by_region["PC"])
    F_C = np.array(F_min_by_region["C"])
    ax_b.plot(time_cutoffs_ns, F_PC - F_O, marker="o", markersize=4,
              color="#9467bd", linewidth=1.5, label="ΔΔG(PC − O)")
    ax_b.plot(time_cutoffs_ns, F_C - F_O, marker="s", markersize=4,
              color="#ff7f0e", linewidth=1.5, label="ΔΔG(C − O)")
    ax_b.axhline(0, color="black", linewidth=0.5, alpha=0.6)
    ax_b.set_xlabel("Simulation time (ns)")
    ax_b.set_ylabel("ΔΔG (kcal/mol)")
    ax_b.set_title("(b) Inter-region ΔΔG vs time\n"
                   "(plateau ⇒ converged; pilot 19.8 ns NOT yet plateaued)",
                   fontsize=10)
    ax_b.legend(loc="upper right", fontsize=9)
    ax_b.grid(alpha=0.3, linestyle="--")
    ax_b.set_xlim(0, max_t_ns + 1)

    fig.suptitle(
        "MetaD convergence diagnostic — JACS 2019 SI Fig S4/S5 style\n"
        f"Initial seq-aligned pilot ({hills[-1, 0]/1000:.1f} ns, single walker, "
        f"FALLBACK contract: HEIGHT=0.3, BF={BIASFACTOR_PILOT})",
        fontsize=11, y=1.02
    )
    fig.tight_layout()

    out_png = HERE / "si_style_convergence_pilot.png"
    out_pdf = HERE / "si_style_convergence_pilot.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"\nSaved: {out_png}")
    print(f"Saved: {out_pdf}")

    # Print numeric summary
    print("\nΔΔG summary (kcal/mol, last time cut):")
    print(f"  PC − O = {F_PC[-1] - F_O[-1]:.2f}")
    print(f"  C  − O = {F_C[-1] - F_O[-1]:.2f}")
    print(f"  C  − PC = {F_C[-1] - F_PC[-1]:.2f}")


if __name__ == "__main__":
    render()
