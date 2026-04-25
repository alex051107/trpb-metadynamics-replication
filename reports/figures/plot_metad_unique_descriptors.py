"""Plot the 3 MetaD-unique descriptors that ANin GenSLM and Yu MMPBSA cannot produce.

Panel A: P(state) raw frame counts (O / PC / C / off).
Panel B: mean off-path RMSD per state ⟨z_RMSD⟩|state in Å.
Panel C: bias-deposit shape σ_s(t) from HILLS.

Caveat (Week 8 deck framing): raw frame counts are NOT Boltzmann-reweighted.
Tiwary-Parrinello c(t) reweighting will replace these after Track A v3 production
FES converges (post 2026-05-01 kill-switch).

Run:
    python3 reports/figures/plot_metad_unique_descriptors.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent.parent
DATA_DIR = HERE / "raw_data"
COLVAR_PATH = DATA_DIR / "longleaf_initial_seqaligned_COLVAR"
HILLS_PATH = DATA_DIR / "longleaf_initial_seqaligned_HILLS"

# Import descriptors module
sys.path.insert(0, str(PROJECT_ROOT / "replication" / "cartridge"))
from descriptors import (  # noqa: E402
    extract_metad_unique_descriptors,
    parse_colvar,
    STATE_MASKS,
)


# Visual style
STATE_COLORS = {
    "O": "#1f77b4",   # blue (open)
    "PC": "#2ca02c",  # green (partially closed)
    "C": "#d62728",   # red (closed)
    "off": "#7f7f7f", # gray (off-path)
}
STATE_ORDER = ["O", "PC", "C", "off"]
STATE_LABELS = {
    "O": "Open\n(s ≤ 2)",
    "PC": "Partially Closed\n(4 ≤ s ≤ 6)",
    "C": "Closed\n(s ≥ 10)",
    "off": "Off-path\n(other)",
}


def render() -> None:
    desc = extract_metad_unique_descriptors(COLVAR_PATH, HILLS_PATH)
    print(f"Pilot: t={desc.pilot_t_ns:.2f} ns, n_rows={desc.pilot_n_rows}, "
          f"max_s={desc.pilot_max_s:.3f}")
    print("State occupancy (raw, NOT reweighted):")
    for state in STATE_ORDER:
        frac = desc.state_occupancy.fractions[state]
        n = desc.state_occupancy.counts[state]
        print(f"  {state}: {frac*100:5.2f}%  (n={n})")
    print("Mean z_RMSD per state (Å):")
    for state in STATE_ORDER:
        z = desc.mean_z_per_state.mean_z_rmsd[state]
        n = desc.mean_z_per_state.n_frames_per_state[state]
        print(f"  {state}: {z:.3f}  (n={n})")
    print(f"σ_s(t): {len(desc.sigma_s_t.time_ps)} HILLS rows, "
          f"σ_s range [{desc.sigma_s_t.sigma_s.min():.3f}, "
          f"{desc.sigma_s_t.sigma_s.max():.3f}]")

    fig, (ax_a, ax_b, ax_c) = plt.subplots(1, 3, figsize=(13, 4))

    # ---- Panel A: P(state) bar chart ----
    fractions = [desc.state_occupancy.fractions[s] for s in STATE_ORDER]
    bars = ax_a.bar(
        range(len(STATE_ORDER)), [f * 100 for f in fractions],
        color=[STATE_COLORS[s] for s in STATE_ORDER],
        edgecolor="black", linewidth=0.6,
    )
    for bar, frac in zip(bars, fractions):
        ax_a.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                  f"{frac*100:.1f}%", ha="center", va="bottom", fontsize=9)
    ax_a.set_xticks(range(len(STATE_ORDER)))
    ax_a.set_xticklabels([STATE_LABELS[s] for s in STATE_ORDER], fontsize=8)
    ax_a.set_ylabel("Frame fraction (%)")
    ax_a.set_title("(a) State occupancy P(state)\nraw frame counts (NOT reweighted)",
                   fontsize=10)
    ax_a.set_ylim(0, max(f * 100 for f in fractions) * 1.18)
    ax_a.grid(axis="y", alpha=0.3, linestyle="--")

    # ---- Panel B: ⟨z_RMSD⟩|state strip plot ----
    colvar = parse_colvar(COLVAR_PATH)
    s_vals = colvar[:, 1]
    z_msd = colvar[:, 2]
    z_rmsd = np.sqrt(np.maximum(z_msd, 0.0))
    for i, state in enumerate(STATE_ORDER):
        if state == "off":
            mask = ~np.any([STATE_MASKS[k](s_vals) for k in STATE_MASKS], axis=0)
        else:
            mask = STATE_MASKS[state](s_vals)
        if mask.sum() == 0:
            continue
        # Subsample for visual clarity
        idx = np.where(mask)[0]
        if len(idx) > 1500:
            idx = np.random.RandomState(0).choice(idx, 1500, replace=False)
        z_subset = z_rmsd[idx]
        x_jitter = np.random.RandomState(i).normal(i, 0.08, size=len(z_subset))
        ax_b.scatter(x_jitter, z_subset, s=4, alpha=0.3,
                     color=STATE_COLORS[state], edgecolors="none")
        # Mean as horizontal line
        mean_z = float(z_subset.mean()) if len(z_subset) > 0 else 0.0
        ax_b.plot([i - 0.3, i + 0.3], [mean_z, mean_z],
                  color="black", linewidth=2, zorder=10)
        ax_b.text(i, mean_z + 0.06, f"⟨z⟩={mean_z:.2f}", ha="center",
                  fontsize=8, fontweight="bold")
    ax_b.set_xticks(range(len(STATE_ORDER)))
    ax_b.set_xticklabels([s for s in STATE_ORDER], fontsize=10)
    ax_b.set_ylabel("z_RMSD (Å)")
    ax_b.set_title("(b) Off-path geometry ⟨z_RMSD⟩|state\nUNIQUE to physical sampling",
                   fontsize=10)
    ax_b.grid(axis="y", alpha=0.3, linestyle="--")
    ax_b.set_ylim(0, max(2.5, np.percentile(z_rmsd, 99) * 1.05))

    # ---- Panel C: σ_s(t) ----
    t_ns = desc.sigma_s_t.time_ps / 1000.0
    ax_c.plot(t_ns, desc.sigma_s_t.sigma_s, color="#9467bd", linewidth=0.8)
    ax_c.set_xlabel("Time (ns)")
    ax_c.set_ylabel("σ_s (path-CV units)")
    ax_c.set_title("(c) Bias-deposit shape σ_s(t)\nADAPTIVE=DIFF — sampling difficulty proxy",
                   fontsize=10)
    ax_c.grid(alpha=0.3, linestyle="--")
    ax_c.set_xlim(0, t_ns.max() * 1.02)

    fig.suptitle(
        f"MetaD-unique descriptors (Initial seq-aligned pilot, {desc.pilot_t_ns:.1f} ns)\n"
        f"Three observables that GenSLM (sequence) + MMPBSA (single-frame docking) cannot produce",
        fontsize=11, y=1.02
    )
    fig.tight_layout()

    out_png = HERE / "metad_unique_descriptors.png"
    out_pdf = HERE / "metad_unique_descriptors.pdf"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"\nSaved: {out_png}")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    render()
