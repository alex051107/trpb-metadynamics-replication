#!/usr/bin/env python3
"""
Self-consistency test for FUNCPATHMSD path CV.

Background:
    Job 41514529 ran 46.3 ns of well-tempered MetaDynamics but s(R) stayed
    in [7.77, 7.83] the entire run — i.e., the CV appeared to put the system
    in a narrow PC region and never explored O or C basins.

    Codex review identified that FUNCPATHMSD feeds the input value directly
    into exp(-λ*d) (no internal squaring, per PLUMED 2.9.2 source code). The
    job's plumed.dat used plain RMSD (no SQUARED keyword) together with
    LAMBDA=3.391. This combination is NOT self-consistent: even the
    reference frames themselves don't map back to s=1..15 under this setup.

This script:
    - Loads the 15 path reference frames
    - Computes the 15×15 best-fit (Kabsch) RMSD matrix
    - Evaluates s(R=frame_i) for each i under TWO conventions:
        A. d_i = RMSD_i          (what plain RMSD in plumed.dat gives)
        B. d_i = RMSD_i²         (what RMSD ... SQUARED gives)
    - Sweeps LAMBDA over several candidate values
    - Reports which LAMBDA makes s(R=frame_i) ≈ i (the self-consistent value)

Correctness criterion:
    For a path CV to be usable, feeding a reference frame into it should
    return its own index. If s(frame_01) ≠ 1 or s(frame_15) ≠ 15, the CV
    cannot resolve the endpoints and MetaDynamics cannot distinguish O/PC/C.

Usage:
    cd replication/validations/path_cv_debug_2026-04-08/
    python3 01_self_consistency_test.py
"""

from pathlib import Path
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PATH_PDB = PROJECT_ROOT / "replication/metadynamics/path_cv/path.pdb"


def load_multi_model_pdb(path: Path):
    """Load all MODELs from a multi-model PDB as (N, 3) arrays.

    Coordinates are in PDB native units (Å for repo path.pdb, may be nm for
    PLUMED-ready versions). Returned as-is; caller is responsible for units.
    """
    models = []
    current = []
    with path.open() as f:
        for line in f:
            if line.startswith("MODEL"):
                current = []
            elif line.startswith("ENDMDL"):
                models.append(np.array(current, dtype=float))
            elif line.startswith("ATOM") and " CA " in line:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                current.append([x, y, z])
        if current and not models:
            models.append(np.array(current, dtype=float))
    return models


def kabsch_rmsd(A: np.ndarray, B: np.ndarray) -> float:
    """Best-fit RMSD between two (N,3) coordinate arrays (Kabsch algorithm).

    Returns scalar RMSD in the same units as the input arrays.
    """
    assert A.shape == B.shape, f"shape mismatch: {A.shape} vs {B.shape}"
    A = A - A.mean(axis=0)
    B = B - B.mean(axis=0)
    H = A.T @ B
    U, _, Vt = np.linalg.svd(H)
    d = float(np.sign(np.linalg.det(Vt.T @ U.T)))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    A_rot = A @ R.T
    diff = A_rot - B
    return float(np.sqrt((diff ** 2).sum() / A.shape[0]))


def compute_s(rmsd_to_refs: np.ndarray, lambda_val: float, squared: bool) -> float:
    """Apply the FUNCPATHMSD formula: s = Σ i * exp(-λ*d_i) / Σ exp(-λ*d_i).

    Args:
        rmsd_to_refs: array of 15 RMSD values from the test configuration
                      to each of the 15 reference frames.
        lambda_val:   LAMBDA parameter passed to FUNCPATHMSD.
        squared:      if True, compute d_i = RMSD_i² (what SQUARED keyword gives);
                      if False, d_i = RMSD_i (what plain RMSD gives).

    Returns:
        s(R) value.
    """
    d = rmsd_to_refs ** 2 if squared else rmsd_to_refs
    weights = np.exp(-lambda_val * d)
    num = sum((idx + 1) * w for idx, w in enumerate(weights))
    den = weights.sum()
    return num / den


def main() -> int:
    models = load_multi_model_pdb(PATH_PDB)
    assert len(models) == 15, f"expected 15 models, got {len(models)}"
    n_atoms = models[0].shape[0]
    assert n_atoms == 112, f"expected 112 Cα atoms, got {n_atoms}"
    print(f"Loaded {len(models)} models, {n_atoms} Cα atoms each")
    print(f"Source: {PATH_PDB}")

    # Repo path.pdb is in Å. PLUMED uses nm internally, so convert for the test.
    # (The path on Longleaf is stored in nm, but this script operates on the
    # repo copy and converts explicitly for clarity.)
    models_nm = [m / 10.0 for m in models]

    # Compute the full 15×15 RMSD matrix in nm
    rmsd = np.zeros((15, 15))
    for i in range(15):
        for j in range(15):
            rmsd[i, j] = kabsch_rmsd(models_nm[i], models_nm[j])

    # Sanity checks on the path geometry
    adj = np.array([rmsd[i, i + 1] for i in range(14)])
    assert np.allclose(adj, adj.mean(), rtol=0.01), \
        f"path is not linearly interpolated: adjacent RMSDs vary more than 1%"
    print(f"\nAdjacent-frame RMSD (nm):  {adj.mean():.6f}")
    print(f"Per-atom MSD_adjacent (nm²): {adj.mean() ** 2:.6f}")
    print(f"End-to-end frame 1↔15 (nm): {rmsd[0, 14]:.4f}")

    # Sweep LAMBDA values and check self-consistency
    test_frames = [0, 7, 14]  # frame indices (0-based): 1, 8, 15
    lambda_values = [
        ("3.391 (CURRENT, wrong)",   3.391),
        ("29.57 (2.3/adj_RMSD)",     29.57),
        ("100",                      100.0),
        ("379.8 (2.3/MSD per-atom)", 379.8),
        ("1000",                     1000.0),
        ("5000",                     5000.0),
    ]

    print("\n" + "=" * 78)
    print("Self-consistency: s(frame_i) under both conventions")
    print("=" * 78)
    header = f"{'LAMBDA':>28} | {'plain RMSD':^22} | {'RMSD² (SQUARED)':^22}"
    print(header)
    print(f"{'':>28} | {'f01':>6} {'f08':>6} {'f15':>6}  | {'f01':>6} {'f08':>6} {'f15':>6}")
    print("-" * 78)

    for label, lam in lambda_values:
        row_plain = [compute_s(rmsd[i], lam, squared=False) for i in test_frames]
        row_sq = [compute_s(rmsd[i], lam, squared=True) for i in test_frames]
        print(f"{label:>28} | "
              f"{row_plain[0]:6.2f} {row_plain[1]:6.2f} {row_plain[2]:6.2f}  | "
              f"{row_sq[0]:6.2f} {row_sq[1]:6.2f} {row_sq[2]:6.2f}")

    # Report which LAMBDA gives self-consistent endpoints
    print("\n" + "=" * 78)
    print("VERDICT: correct LAMBDA for each convention")
    print("=" * 78)

    def find_best_lambda(squared: bool, candidates) -> tuple[float, float]:
        best_lam = None
        best_err = float("inf")
        for _, lam in candidates:
            s1 = compute_s(rmsd[0], lam, squared=squared)
            s15 = compute_s(rmsd[14], lam, squared=squared)
            err = (s1 - 1) ** 2 + (s15 - 15) ** 2
            if err < best_err:
                best_err = err
                best_lam = lam
        return best_lam, best_err

    best_plain, err_plain = find_best_lambda(False, lambda_values)
    best_sq, err_sq = find_best_lambda(True, lambda_values)

    print(f"Plain RMSD convention: best LAMBDA ≈ {best_plain}")
    print(f"  → s(frame_01) = {compute_s(rmsd[0], best_plain, False):.4f} (should be 1)")
    print(f"  → s(frame_15) = {compute_s(rmsd[14], best_plain, False):.4f} (should be 15)")
    print(f"  total endpoint error² = {err_plain:.4e}")

    print(f"\nSQUARED convention: best LAMBDA ≈ {best_sq}")
    print(f"  → s(frame_01) = {compute_s(rmsd[0], best_sq, True):.4f} (should be 1)")
    print(f"  → s(frame_15) = {compute_s(rmsd[14], best_sq, True):.4f} (should be 15)")
    print(f"  total endpoint error² = {err_sq:.4e}")

    # Assertions: ensure CURRENT setup is broken (so the fix matters)
    s1_current = compute_s(rmsd[0], 3.391, squared=False)
    s15_current = compute_s(rmsd[14], 3.391, squared=False)
    assert abs(s1_current - 1) > 0.5, \
        f"current LAMBDA appears OK (s(frame_01)={s1_current:.3f}, expected 1)"
    assert abs(s15_current - 15) > 0.5, \
        f"current LAMBDA appears OK (s(frame_15)={s15_current:.3f}, expected 15)"
    print(f"\nCURRENT LAMBDA=3.391 CONFIRMED BROKEN:")
    print(f"  s(frame_01) = {s1_current:.3f} (should be 1) — error {abs(s1_current-1):.3f}")
    print(f"  s(frame_15) = {s15_current:.3f} (should be 15) — error {abs(s15_current-15):.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
