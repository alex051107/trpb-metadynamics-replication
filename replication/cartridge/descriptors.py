"""MetaD-unique descriptors for ML/cross-lab interface (Week 8 Track B).

Extracts three descriptors from a single-walker MetaD pilot's COLVAR + HILLS
that **only physical sampling produces** — sequence-only models (GenSLM) and
single-frame docking (MMPBSA) cannot generate these:

  1. State-occupancy P(state) = {P(O), P(PC), P(C), P(off)}
     - State masks: O (s ≤ 2), PC (4 ≤ s ≤ 6), C (s ≥ 10), off (else)
     - Reported as raw frame counts (NOT Boltzmann-reweighted; Tiwary-Parrinello
       c(t) reweighting is NotImplementedError — see reweight_to_unbiased() stub)

  2. Mean off-path RMSD per state ⟨z_RMSD⟩|state in Å
     - Source: COLVAR p1.zzz (PLUMED PATHMSD MSD output, units Å²)
     - Conversion: z_RMSD = sqrt(p1.zzz) gives Å distance from reference path

  3. Bias-deposit shape σ_s(t)
     - Source: HILLS sigma_p1.sss_p1.sss column
     - Acts as proxy for sampling difficulty per region under ADAPTIVE=DIFF

References: see `deliverables/week7_2026-04-24/11_ml_layer/INTERFACE_DESIGN_2026-04-25.md`
§3.1 + §6 for the full schema; this file implements the descriptor-extraction
half of the interface (NOT reweighting; NOT FES estimation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


# State masks per `Convergence_Memo_v2_2026-04-24.md` §2 + INTERFACE_DESIGN §3.1
STATE_MASKS = {
    "O": (lambda s: s <= 2.0),
    "PC": (lambda s: (s >= 4.0) & (s <= 6.0)),
    "C": (lambda s: s >= 10.0),
}


@dataclass
class StateOccupancy:
    counts: dict[str, int]
    fractions: dict[str, float]
    total_frames: int
    note: str = (
        "Raw frame counts; NOT Boltzmann-reweighted. Tiwary-Parrinello c(t) "
        "reweighting required for true thermodynamic populations — see "
        "reweight_to_unbiased() NotImplementedError stub."
    )


@dataclass
class MeanZRmsdPerState:
    mean_z_rmsd: dict[str, float]  # Å
    n_frames_per_state: dict[str, int]
    units: str = "Å (sqrt of PLUMED p1.zzz MSD)"


@dataclass
class BiasDepositShape:
    time_ps: np.ndarray
    sigma_s: np.ndarray
    note: str = "ADAPTIVE=DIFF sigma_p1.sss_p1.sss column from HILLS"


@dataclass
class MetadUniqueDescriptors:
    state_occupancy: StateOccupancy
    mean_z_per_state: MeanZRmsdPerState
    sigma_s_t: BiasDepositShape
    pilot_max_s: float
    pilot_n_rows: int
    pilot_t_ns: float


def parse_colvar(colvar_path: Path) -> np.ndarray:
    """Return ndarray of shape (n_rows, 6): [time, s, z, bias, uwall_bias, uwall_force2].

    PLUMED COLVAR with FIELDS time p1.sss p1.zzz @3.bias uwall.bias uwall.force2.
    z is MSD in Å² (since plumed.dat uses UNITS LENGTH=A).
    """
    data = []
    with colvar_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cols = line.split()
            if len(cols) < 3:
                continue
            try:
                row = [float(x) for x in cols[:6]]
            except ValueError:
                continue
            while len(row) < 6:
                row.append(0.0)
            data.append(row)
    arr = np.array(data, dtype=float)
    if arr.size == 0:
        raise ValueError(f"empty COLVAR {colvar_path}")
    return arr


def parse_hills(hills_path: Path) -> np.ndarray:
    """Return ndarray of shape (n_rows, 8): [time, s, z, sigma_s, sigma_z, sigma_zs, height, biasf]."""
    data = []
    with hills_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            cols = line.split()
            if len(cols) < 8:
                continue
            try:
                data.append([float(x) for x in cols[:8]])
            except ValueError:
                continue
    arr = np.array(data, dtype=float)
    if arr.size == 0:
        raise ValueError(f"empty HILLS {hills_path}")
    return arr


def state_occupancy(colvar: np.ndarray) -> StateOccupancy:
    """Bin COLVAR by s into {O, PC, C, off}; return raw fractions."""
    s = colvar[:, 1]
    n_total = len(s)
    counts: dict[str, int] = {}
    accounted = np.zeros_like(s, dtype=bool)
    for state, mask_fn in STATE_MASKS.items():
        mask = mask_fn(s)
        counts[state] = int(mask.sum())
        accounted |= mask
    counts["off"] = int(n_total - accounted.sum())
    fractions = {state: counts[state] / n_total for state in counts}
    # Sanity: probabilities sum to 1 within float tolerance
    assert abs(sum(fractions.values()) - 1.0) < 1e-9, (
        f"state fractions don't sum to 1: {fractions}"
    )
    return StateOccupancy(
        counts=counts,
        fractions=fractions,
        total_frames=n_total,
    )


def mean_z_per_state(colvar: np.ndarray) -> MeanZRmsdPerState:
    """Per-state mean of sqrt(p1.zzz) in Å.

    p1.zzz is PLUMED's MSD output in Å² (under UNITS LENGTH=A); sqrt gives RMSD in Å.
    """
    s = colvar[:, 1]
    z_msd = colvar[:, 2]
    # Guard against negative z due to LINCS-corruption (FP-033 signature)
    if (z_msd < 0).any():
        n_neg = int((z_msd < 0).sum())
        raise ValueError(
            f"COLVAR has {n_neg} rows with z<0 — LINCS corruption signature; "
            "investigate before computing sqrt"
        )
    z_rmsd = np.sqrt(z_msd)  # Å
    means: dict[str, float] = {}
    n_per_state: dict[str, int] = {}
    accounted = np.zeros_like(s, dtype=bool)
    for state, mask_fn in STATE_MASKS.items():
        mask = mask_fn(s)
        accounted |= mask
        if mask.sum() > 0:
            means[state] = float(z_rmsd[mask].mean())
            n_per_state[state] = int(mask.sum())
        else:
            means[state] = float("nan")
            n_per_state[state] = 0
    off_mask = ~accounted
    if off_mask.sum() > 0:
        means["off"] = float(z_rmsd[off_mask].mean())
        n_per_state["off"] = int(off_mask.sum())
    else:
        means["off"] = float("nan")
        n_per_state["off"] = 0
    return MeanZRmsdPerState(mean_z_rmsd=means, n_frames_per_state=n_per_state)


def bias_deposit_shape(hills: np.ndarray) -> BiasDepositShape:
    """Return σ_s(t) from HILLS sigma_p1.sss_p1.sss column."""
    time_ps = hills[:, 0]
    sigma_s = hills[:, 3]
    if (sigma_s < 0).any():
        raise ValueError("HILLS has sigma_s<0 — corrupt or pre-burn-in rows")
    return BiasDepositShape(time_ps=time_ps, sigma_s=sigma_s)


def extract_metad_unique_descriptors(
    colvar_path: Path,
    hills_path: Path,
) -> MetadUniqueDescriptors:
    """Extract the 3 MetaD-unique descriptors from pilot COLVAR + HILLS.

    Returns a structured dataclass with state occupancy, mean z RMSD per state,
    and bias-deposit shape σ_s(t). All raw — no reweighting applied.
    """
    colvar = parse_colvar(colvar_path)
    hills = parse_hills(hills_path)
    occ = state_occupancy(colvar)
    z_per_state = mean_z_per_state(colvar)
    sigma_t = bias_deposit_shape(hills)
    return MetadUniqueDescriptors(
        state_occupancy=occ,
        mean_z_per_state=z_per_state,
        sigma_s_t=sigma_t,
        pilot_max_s=float(colvar[:, 1].max()),
        pilot_n_rows=int(len(colvar)),
        pilot_t_ns=float(colvar[-1, 0] / 1000.0),
    )


def reweight_to_unbiased(*args, **kwargs):
    """Tiwary-Parrinello c(t) reweighting — NOT YET IMPLEMENTED.

    Per INTERFACE_DESIGN_2026-04-25.md §6, this requires:
    - HILLS deposition history
    - WT bias parameters (biasfactor, T)
    - Per-frame c(t) recomputation

    Stub raises NotImplementedError until v3 production FES is converged.
    """
    raise NotImplementedError(
        "Tiwary-Parrinello c(t) reweighting deferred to post-v3-PASS "
        "(per INTERFACE_DESIGN_2026-04-25.md §6 BLOCKED #5). "
        "Use raw frame counts (state_occupancy()) for L0/L1 descriptors only."
    )
