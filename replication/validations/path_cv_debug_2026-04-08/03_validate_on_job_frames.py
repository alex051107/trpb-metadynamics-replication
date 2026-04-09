#!/usr/bin/env python3
"""
Checklist item 1: Re-compute LAMBDA from the ACTUAL job frames on Longleaf.

The repo's path.pdb and the Longleaf job frames may differ (unit conventions,
alignment method, or different versions of generate_path_cv.py). Before
committing to any fix value, run the self-consistency test on the real
production frames, not the repo copy.

Input: tmp/metad_review_41514529/frames/frame_01.pdb ... frame_15.pdb
       (these are a snapshot of /work/.../single_walker/frames/ on Longleaf
        that Codex pulled down during the second-round diagnostic)

Output:
  - Per-atom MSD_adjacent from the actual job frames
  - Implied correct LAMBDA under both conventions
  - Self-consistency test results for each candidate LAMBDA
"""

from pathlib import Path
import numpy as np

WORKTREE_ROOT = Path(__file__).resolve().parents[3]
JOB_FRAMES_DIR = WORKTREE_ROOT / "tmp/metad_review_41514529/frames"


def load_pdb_ca(path: Path) -> np.ndarray:
    coords = []
    with path.open() as f:
        for line in f:
            if line.startswith("ATOM") and " CA " in line:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append([x, y, z])
    return np.array(coords, dtype=float)


def kabsch_rmsd(A: np.ndarray, B: np.ndarray) -> float:
    A = A - A.mean(axis=0)
    B = B - B.mean(axis=0)
    H = A.T @ B
    U, _, Vt = np.linalg.svd(H)
    d = float(np.sign(np.linalg.det(Vt.T @ U.T)))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    diff = A @ R.T - B
    return float(np.sqrt((diff ** 2).sum() / A.shape[0]))


def compute_s(rmsd_to_refs: np.ndarray, lambda_val: float, squared: bool) -> float:
    d = rmsd_to_refs ** 2 if squared else rmsd_to_refs
    weights = np.exp(-lambda_val * d)
    num = sum((idx + 1) * w for idx, w in enumerate(weights))
    den = weights.sum()
    return num / den


def main() -> int:
    # Load job frames (Longleaf path.pdb is in nm, per Codex Finding 5)
    frames_nm = []
    for i in range(1, 16):
        path = JOB_FRAMES_DIR / f"frame_{i:02d}.pdb"
        assert path.exists(), f"missing job frame: {path}"
        coords = load_pdb_ca(path)
        frames_nm.append(coords)

    n_atoms = frames_nm[0].shape[0]
    assert n_atoms == 112, f"expected 112 Cα atoms, got {n_atoms}"
    print(f"Loaded 15 JOB frames from {JOB_FRAMES_DIR}")
    print(f"  {n_atoms} Cα atoms per frame")
    print(f"  First atom of frame_01: {frames_nm[0][0]}")

    # Verify nm units (reasonable range for Cα coordinates in nm is ~1-10)
    max_coord = max(abs(frames_nm[0]).max() for _ in [0])
    assert 1 < max_coord < 50, (
        f"coordinate range looks wrong: max abs = {max_coord}. "
        f"Expected nm (1-50). If Å, multiply input by 0.1."
    )
    print(f"  Unit check: max |coord| = {max_coord:.2f} nm (OK)")

    # Full RMSD matrix in nm
    N = 15
    rmsd_matrix = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            rmsd_matrix[i, j] = kabsch_rmsd(frames_nm[i], frames_nm[j])

    adjacent = np.array([rmsd_matrix[i, i + 1] for i in range(N - 1)])
    print(f"\nAdjacent-frame RMSD (nm):")
    print(f"  min={adjacent.min():.6f}, max={adjacent.max():.6f}, mean={adjacent.mean():.6f}")
    assert adjacent.std() / adjacent.mean() < 0.05, (
        f"adjacent spacing varies by more than 5% — path may not be linear"
    )

    per_atom_msd_adj = adjacent.mean() ** 2
    print(f"\nPer-atom MSD_adjacent (nm²): {per_atom_msd_adj:.6f}")

    lambda_squared_conv = 2.3 / per_atom_msd_adj
    lambda_plain_conv = 2.3 / adjacent.mean()
    print(f"\nImplied LAMBDA (SQUARED convention): {lambda_squared_conv:.2f}")
    print(f"Implied LAMBDA (plain RMSD convention): {lambda_plain_conv:.2f}")

    # Self-consistency test with candidate LAMBDAs
    print("\n" + "=" * 78)
    print("Self-consistency test on JOB frames (not repo frames)")
    print("=" * 78)
    candidates = [
        ("3.391 (current, broken)", 3.391),
        ("29.57 (plain RMSD convention)", lambda_plain_conv),
        ("379.8 (SQUARED convention)", lambda_squared_conv),
        ("1000", 1000.0),
    ]
    print(f"{'LAMBDA':>32} | {'plain':^22} | {'SQUARED':^22}")
    print(f"{'':>32} | {'f01':>6} {'f08':>6} {'f15':>6}  | {'f01':>6} {'f08':>6} {'f15':>6}")
    print("-" * 78)
    for label, lam in candidates:
        sp = [compute_s(rmsd_matrix[i], lam, False) for i in (0, 7, 14)]
        ss = [compute_s(rmsd_matrix[i], lam, True) for i in (0, 7, 14)]
        print(f"{label:>32} | "
              f"{sp[0]:6.2f} {sp[1]:6.2f} {sp[2]:6.2f}  | "
              f"{ss[0]:6.2f} {ss[1]:6.2f} {ss[2]:6.2f}")

    # Confirm our LAMBDA fix is correct for the actual job frames
    s1_fixed = compute_s(rmsd_matrix[0], lambda_squared_conv, squared=True)
    s15_fixed = compute_s(rmsd_matrix[14], lambda_squared_conv, squared=True)
    assert abs(s1_fixed - 1) < 0.5, (
        f"LAMBDA={lambda_squared_conv:.2f} + SQUARED does not give s(f01)≈1: {s1_fixed}"
    )
    assert abs(s15_fixed - 15) < 0.5, (
        f"LAMBDA={lambda_squared_conv:.2f} + SQUARED does not give s(f15)≈15: {s15_fixed}"
    )

    print("\n" + "=" * 78)
    print("VERDICT for checklist item 1:")
    print("=" * 78)
    print(f"  Correct LAMBDA for SQUARED convention = {lambda_squared_conv:.2f} nm⁻²")
    print(f"  (computed from actual job frames, not repo)")
    print(f"  s(frame_01) = {s1_fixed:.4f}, s(frame_15) = {s15_fixed:.4f}")
    print(f"  → PASS: fix is valid for the real production frames")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
