"""Plot TrpB path-CV surfaces with rigorous unit-correctness.

Inputs are PLUMED `sum_hills` grids generated on Longleaf from the HILLS files:

    plumed sum_hills --hills HILLS --min 0.5,0.0 --max 15.5,2.8 \
        --bin 300,140 --mintozero --outfile fes_*.dat

The PLUMED `path.zzz` column is in length-squared units (Å² = MSD) when
`UNITS LENGTH=A` is set, because the Branduardi soft-min closed form
    z(R) = -(1/lambda) * ln  Sum_i exp(-lambda * MSD_i(R))
must have the same units as MSD_i. Plotting it directly under an Angstrom
label would be a unit lie. We take sqrt(p1.zzz) to recover the per-atom RMSD
deviation in Angstrom, matching JACS 2019 SI Fig 3.

Two figures are written:
  1. CANONICAL — y = sqrt(p1.zzz) [Å], y-label "RMSD Deviation (Å)".
                 Saved to sz_2d_unit_checked_sumhills.png AND copied as the
                 canonical filename `sz_2d_distribution.png`.
  2. AUDIT     — y = raw p1.zzz [Å²], y-label "p1.zzz (Å² = MSD)".
                 Saved as audit artefact only, NEVER overwrites canonical.

Single-walker fallback variant of the Miguel contract was used for both runs
(HEIGHT=0.3, BIASFACTOR=15, KAPPA=800 wall) — NOT the Miguel primary 10-walker
contract (HEIGHT=0.15, BIASFACTOR=10, KAPPA=500). Captions hedge accordingly.

Codex independent verdict on the units: agreed (CCB task 20260424-234500).
Full audit log: deliverables/week7_2026-04-24/08_figures/UNIT_AUDIT.md
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors

HERE = Path(__file__).resolve().parent


def find_repo_root(start: Path) -> Path:
    for parent in (start, *start.parents):
        if (parent / "reports" / "figures" / "raw_data").exists():
            return parent
    raise FileNotFoundError("could not locate reports/figures/raw_data from script path")


REPO_ROOT = find_repo_root(HERE)
FIG_DIR = HERE
DATA_DIR = REPO_ROOT / "reports" / "figures" / "raw_data"

NAIVE_FES = DATA_DIR / "fes_initial_single_sumhills.dat"
SEQALN_FES = DATA_DIR / "fes_initial_seqaligned_sumhills.dat"
NAIVE_COLVAR = DATA_DIR / "longleaf_initial_single_COLVAR"
SEQALN_COLVAR = DATA_DIR / "longleaf_initial_seqaligned_COLVAR"

OUT_AUDIT = FIG_DIR / "sz_2d_raw_msd_audit.png"          # raw p1.zzz (Å²) — audit only
OUT_AUDIT_PDF = FIG_DIR / "sz_2d_raw_msd_audit.pdf"
OUT_UNIT = FIG_DIR / "sz_2d_unit_checked_sumhills.png"   # sqrt(p1.zzz) (Å) — canonical
OUT_UNIT_PDF = FIG_DIR / "sz_2d_unit_checked_sumhills.pdf"
OUT_CANONICAL = FIG_DIR / "sz_2d_distribution.png"        # historical name

FES_MAX = 14.0
UPPER_WALL_Z_RAW = 2.5


def read_sumhills(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read PLUMED sum_hills grid, returning (s_grid, z_raw_grid, F_grid).

    F_grid is in kcal/mol, clipped at FES_MAX. NaN/Inf are kept so the caller
    can decide how to mask them (the previous nan_to_num that filled NaN with
    FES_MAX painted unsampled regions at the colorbar maximum, hiding the
    real basin structure on a short-pilot dataset)."""
    arr = np.loadtxt(path, comments="#")
    s = arr[:, 0]
    z_raw = arr[:, 1]
    f = arr[:, 2]
    xs = np.unique(s)
    zs = np.unique(z_raw)
    if len(xs) * len(zs) != len(arr):
        raise ValueError(f"unexpected grid shape in {path}")
    s_grid = s.reshape(len(zs), len(xs))
    z_grid = z_raw.reshape(len(zs), len(xs))
    f_grid = f.reshape(len(zs), len(xs))
    return s_grid, z_grid, f_grid


def read_colvar(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (t_ps, s, z_raw_A2) from a PLUMED COLVAR file."""
    arr = np.loadtxt(path, comments="#")
    return arr[:, 0], arr[:, 1], arr[:, 2]


def read_colvar_stats(path: Path) -> dict[str, float]:
    t, s, z = read_colvar(path)
    return {
        "n": float(len(t)),
        "ns": float(t[-1] / 1000.0),
        "s_min": float(np.min(s)),
        "s_max": float(np.max(s)),
        "z0": float(z[0]),
        "s0": float(s[0]),
    }


def find_basins(
    f_grid_masked: np.ndarray,
    s_axis: np.ndarray,
    z_axis: np.ndarray,
    *,
    f_threshold: float = 1.0,
    min_separation_s: float = 2.0,
) -> list[tuple[float, float, float]]:
    """Locate FES basin minima within sampled regions.

    Returns list of (s_center, z_center, F_min) sorted by s. Basin centroids
    must be at least `min_separation_s` apart in s to count as distinct.
    """
    finite_mask = np.isfinite(f_grid_masked)
    if not np.any(finite_mask):
        return []

    # 1D projection over z to find local minima in s
    f_along_s = np.where(finite_mask, f_grid_masked, np.nan)
    f_min_z = np.nanmin(f_along_s, axis=0)
    z_argmin = np.nanargmin(np.where(finite_mask, f_along_s, np.inf), axis=0)

    candidates = []
    for i in range(1, len(s_axis) - 1):
        if not np.isfinite(f_min_z[i]):
            continue
        if f_min_z[i] >= f_threshold:
            continue
        # Local minimum in s
        left = f_min_z[i - 1] if np.isfinite(f_min_z[i - 1]) else np.inf
        right = f_min_z[i + 1] if np.isfinite(f_min_z[i + 1]) else np.inf
        if f_min_z[i] <= left and f_min_z[i] <= right:
            s_val = float(s_axis[i])
            z_val = float(z_axis[z_argmin[i]])
            candidates.append((s_val, z_val, float(f_min_z[i])))

    if not candidates:
        return []

    # Greedy: pick deepest, then exclude neighbours within min_separation_s
    candidates.sort(key=lambda c: c[2])
    accepted: list[tuple[float, float, float]] = []
    for s_val, z_val, f_val in candidates:
        if all(abs(s_val - s_acc) >= min_separation_s for s_acc, _, _ in accepted):
            accepted.append((s_val, z_val, f_val))
    accepted.sort(key=lambda c: c[0])
    return accepted


def build_sampled_mask(
    colvar_path: Path,
    s_axis: np.ndarray,
    z_axis: np.ndarray,
    *,
    z_in_angstrom: bool,
    min_frames: int = 3,
    smooth_sigma: float = 1.2,
) -> np.ndarray:
    """Return a boolean mask, shape (len(z_axis), len(s_axis)).

    True where the walker actually visited the (s, z) bin (>= min_frames after
    a small Gaussian smooth so adjacent bins reachable by the kernel are kept).
    The FES on unsampled bins is meaningless for short-pilot data, so the
    caller paints them white to focus the eye on the actual basins.
    """
    from scipy.ndimage import gaussian_filter

    _, s_col, z_col_a2 = read_colvar(colvar_path)
    z_col = np.sqrt(np.clip(z_col_a2, 0.0, None)) if z_in_angstrom else z_col_a2
    h, _, _ = np.histogram2d(
        s_col, z_col,
        bins=[len(s_axis), len(z_axis)],
        range=[[s_axis.min(), s_axis.max()], [z_axis.min(), z_axis.max()]],
    )
    h = h.T  # shape (NZ, NS) to match F_grid
    h_smooth = gaussian_filter(h, sigma=smooth_sigma)
    return h_smooth >= min_frames


def setup_axes(ax: plt.Axes, y_label: str, y_limit: tuple[float, float]) -> None:
    ax.set_xlabel("Open-to-Closed Path", fontsize=10)
    ax.set_ylabel(y_label, fontsize=10)
    ax.set_xlim(0.8, 15.2)
    ax.set_ylim(*y_limit)
    ax.set_xticks([1, 3, 5, 7, 9, 11, 13, 15])
    ax.tick_params(direction="out", length=3, labelsize=8.5)
    for spine in ax.spines.values():
        spine.set_linewidth(0.8)


def draw_pair(
    *,
    transform: str,
    out_png: Path,
    out_pdf: Path | None = None,
) -> None:
    s_a, z_a_raw, f_a = read_sumhills(NAIVE_FES)
    s_b, z_b_raw, f_b = read_sumhills(SEQALN_FES)
    stats_a = read_colvar_stats(NAIVE_COLVAR)
    stats_b = read_colvar_stats(SEQALN_COLVAR)

    if transform == "raw_msd":
        # Audit-only: plot raw p1.zzz in length-squared (MSD) units.
        # Never used as the canonical figure — this is here so a reviewer can
        # verify the sqrt transform matches the PLUMED grid before scaling.
        z_a = z_a_raw
        z_b = z_b_raw
        y_label = r"$p1.zzz$  ($\AA^2$ = MSD, raw PLUMED output)"
        y_limit = (0.0, 2.85)
        wall_y = UPPER_WALL_Z_RAW
        start_y = stats_b["z0"]
        subtitle = (
            "AUDIT ARTEFACT — y = raw p1.zzz in $\\AA^2$ (MSD). "
            "Not the canonical figure; canonical uses sqrt(p1.zzz) in $\\AA$."
        )
    elif transform == "sqrt":
        # Canonical: y = sqrt(p1.zzz) recovers per-atom RMSD deviation in Å,
        # matching the JACS 2019 SI Fig 3 axis convention.
        z_a = np.sqrt(np.clip(z_a_raw, 0.0, None))
        z_b = np.sqrt(np.clip(z_b_raw, 0.0, None))
        y_label = r"RMSD Deviation ($\AA$)  =  $\sqrt{p1.zzz}$"
        y_limit = (0.0, 1.7)
        wall_y = np.sqrt(UPPER_WALL_Z_RAW)
        start_y = np.sqrt(stats_b["z0"])
        subtitle = (
            "Single-walker fallback variant (HEIGHT=0.3, BIASFACTOR=15, KAPPA=800); "
            "diagnostic surfaces clipped to SI 0-14 kcal/mol — not a converged WT FES."
        )
    else:
        raise ValueError(transform)

    # Apply sampled-region masks: paint bins the walker never visited as
    # transparent so the eye focuses on real basin structure.
    s_axis_a = s_a[0, :]
    z_axis_a = z_a[:, 0]
    s_axis_b = s_b[0, :]
    z_axis_b = z_b[:, 0]
    mask_a = build_sampled_mask(NAIVE_COLVAR, s_axis_a, z_axis_a,
                                z_in_angstrom=(transform == "sqrt"))
    mask_b = build_sampled_mask(SEQALN_COLVAR, s_axis_b, z_axis_b,
                                z_in_angstrom=(transform == "sqrt"))
    f_a_masked = np.where(mask_a, np.clip(np.nan_to_num(f_a, nan=FES_MAX), 0, FES_MAX), np.nan)
    f_b_masked = np.where(mask_b, np.clip(np.nan_to_num(f_b, nan=FES_MAX), 0, FES_MAX), np.nan)

    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.linewidth": 0.8,
        "savefig.dpi": 300,
    })

    fig = plt.figure(figsize=(10.8, 4.6))
    gs = fig.add_gridspec(
        1, 3,
        width_ratios=[1.0, 1.0, 0.045],
        left=0.065, right=0.935, top=0.74, bottom=0.16,
        wspace=0.18,
    )
    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    cax = fig.add_subplot(gs[0, 2])

    levels = np.linspace(0.0, FES_MAX, 29)
    cmap = plt.get_cmap("turbo").copy()
    cmap.set_bad(color="white", alpha=1.0)
    norm = colors.Normalize(0.0, FES_MAX)

    # Use pcolormesh on masked arrays so NaN bins render as white.
    pm_a = ax_a.pcolormesh(s_a, z_a, np.ma.masked_invalid(f_a_masked),
                           cmap=cmap, norm=norm, shading="auto")
    cs_a = ax_a.contour(s_a, z_a, np.ma.masked_invalid(f_a_masked),
                        levels=np.arange(1, FES_MAX, 1),
                        colors="black", linewidths=0.25, alpha=0.30)
    pm_b = ax_b.pcolormesh(s_b, z_b, np.ma.masked_invalid(f_b_masked),
                           cmap=cmap, norm=norm, shading="auto")
    cs_b = ax_b.contour(s_b, z_b, np.ma.masked_invalid(f_b_masked),
                        levels=np.arange(1, FES_MAX, 1),
                        colors="black", linewidths=0.25, alpha=0.30)

    for ax in (ax_a, ax_b):
        ax.axhline(wall_y, color="0.25", linestyle=(0, (4, 2)),
                   linewidth=0.9, alpha=0.85)
        setup_axes(ax, y_label, y_limit)
        ax.set_facecolor("white")

    ax_a.set_title(
        f"(a)  Naive path  (pre-FP-034, {stats_a['ns']:.1f} ns)",
        loc="left", fontsize=10.5, weight="bold",
    )
    ax_b.set_title(
        f"(b)  Sequence-aligned path  (post-FP-034, {stats_b['ns']:.1f} ns)",
        loc="left", fontsize=10.5, weight="bold",
    )
    ax_b.scatter([stats_b["s0"]], [start_y], marker="*", s=190,
                 facecolor="#ff3030", edgecolor="white", linewidth=1.1, zorder=5)
    ax_b.text(stats_b["s0"] + 0.35, start_y, "start.gro", color="white", fontsize=8.5,
              ha="left", va="center",
              bbox=dict(boxstyle="round,pad=0.22", facecolor="black", alpha=0.55, edgecolor="none"))

    ax_a.text(
        0.02, 0.03, f"s = {stats_a['s_min']:.2f}-{stats_a['s_max']:.2f}",
        transform=ax_a.transAxes, ha="left", va="bottom", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.70, edgecolor="none"),
    )
    ax_b.text(
        0.02, 0.03, f"s = {stats_b['s_min']:.2f}-{stats_b['s_max']:.2f}",
        transform=ax_b.transAxes, ha="left", va="bottom", fontsize=8.0,
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.70, edgecolor="none"),
    )

    cbar = fig.colorbar(pm_b, cax=cax)
    cbar.set_ticks(np.arange(0, FES_MAX + 0.1, 2))
    cbar.set_label(r"$\Delta G$ (kcal mol$^{-1}$)", fontsize=9.5)
    cbar.ax.tick_params(labelsize=8.5)

    fig.suptitle(
        "FEL associated with COMM-domain Open-to-Closed exchange",
        fontsize=12.0, weight="bold", y=0.955,
    )
    fig.text(0.5, 0.855, subtitle, ha="center", va="center", fontsize=8.2, color="0.25")

    fig.savefig(out_png, bbox_inches="tight")
    if out_pdf is not None:
        fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_png}")
    if out_pdf is not None:
        print(f"wrote {out_pdf}")


def main() -> None:
    for path in (NAIVE_FES, SEQALN_FES, NAIVE_COLVAR, SEQALN_COLVAR):
        if not path.exists():
            raise FileNotFoundError(path)
    # Canonical (unit-correct) figure — y = sqrt(p1.zzz) in Å.
    draw_pair(transform="sqrt",    out_png=OUT_UNIT,  out_pdf=OUT_UNIT_PDF)
    # Audit artefact — raw p1.zzz in Å². Never overwrites canonical.
    draw_pair(transform="raw_msd", out_png=OUT_AUDIT, out_pdf=OUT_AUDIT_PDF)
    # Historical filename now points at the unit-correct figure.
    OUT_CANONICAL.write_bytes(OUT_UNIT.read_bytes())
    print(f"canonical (unit-correct, sqrt) -> {OUT_CANONICAL}")


if __name__ == "__main__":
    main()
