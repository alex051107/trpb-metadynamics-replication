#!/usr/bin/env python3
"""
Checklist item 2 — THE CRITICAL TEST:
Does 5DVZ (Ain O-state crystal structure) map to s≈1 under the fixed LAMBDA?

If yes:
  Fixing LAMBDA + SQUARED is sufficient. The path itself is usable;
  Job 41514529's apparent "stuck at s=7.79" was purely a CV artifact.
  Can restart from 5DVZ crystal and expect initial s ≈ 1.

If no:
  The path endpoint 1WDW (which is what frame_01 was built from via linear
  interpolation) does NOT represent the same structure as 5DVZ, even though
  both are nominally "open" PfTrpB states. That means no amount of LAMBDA
  tweaking will put 5DVZ at s=1 — the path itself needs to be regenerated
  with 5DVZ (or 5DVZ-derived frames) as the O-state endpoint.

Procedure:
  1. Extract chain A of 5DVZ (the β-subunit)
  2. Select Cα atoms of residues 97-184 (COMM) + 282-305 (base)
  3. Best-fit align to each of the 15 job frames, compute RMSD
  4. Compute s(R=5DVZ) using fixed LAMBDA (379.77, SQUARED)
  5. Report and compare against s=1 target
"""

from pathlib import Path
import numpy as np

WORKTREE_ROOT = Path(__file__).resolve().parents[3]
FIVE_DVZ_PDB = WORKTREE_ROOT / "replication/structures/5DVZ.pdb"
JOB_FRAMES_DIR = WORKTREE_ROOT / "tmp/metad_review_41514529/frames"

# SI path CV atom selection: COMM domain 97-184 + base region 282-305
COMM_RESIDUES = set(range(97, 185))   # 88 residues
BASE_RESIDUES = set(range(282, 306))  # 24 residues
TARGET_RESIDUES = COMM_RESIDUES | BASE_RESIDUES
assert len(TARGET_RESIDUES) == 112, f"expected 112 target residues, got {len(TARGET_RESIDUES)}"

# Fix value from checklist item 1
LAMBDA_FIX = 379.77


def load_job_frame(path: Path) -> np.ndarray:
    """Job frames are in nm with residue numbers 1..112 (renumbered)."""
    coords = []
    with path.open() as f:
        for line in f:
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                coords.append([x, y, z])
    return np.array(coords, dtype=float)


def extract_5dvz_ca(path: Path, chain_id: str = "A") -> np.ndarray:
    """Extract chain A Cα atoms of residues 97-184 + 282-305 from 5DVZ.

    Returns (112, 3) array in nm (converted from PDB Å).
    """
    # Collect residue -> coord mapping (first occurrence wins)
    res_to_coord = {}
    with path.open() as f:
        for line in f:
            if not line.startswith("ATOM"):
                continue
            # PDB fixed columns:
            #   atom_name:  cols 13-16 (1-indexed) = [12:16]
            #   chain_id:   col 22              = [21]
            #   resnum:     cols 23-26           = [22:26]
            #   x,y,z:      cols 31-38, 39-46, 47-54 = [30:38], [38:46], [46:54]
            atom_name = line[12:16].strip()
            chain = line[21]
            if atom_name != "CA" or chain != chain_id:
                continue
            try:
                resnum = int(line[22:26])
            except ValueError:
                continue
            if resnum in TARGET_RESIDUES and resnum not in res_to_coord:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                res_to_coord[resnum] = (resnum, np.array([x, y, z]))

    # Order by residue number: COMM first (97..184), then base (282..305)
    ordered = []
    for r in sorted(TARGET_RESIDUES):
        assert r in res_to_coord, (
            f"5DVZ chain {chain_id} missing residue {r}. "
            f"Found {len(res_to_coord)}/{len(TARGET_RESIDUES)} target residues."
        )
        ordered.append(res_to_coord[r][1])

    arr_angstrom = np.array(ordered, dtype=float)
    # Convert Å → nm (PDB is in Å, job frames are in nm)
    return arr_angstrom / 10.0


def kabsch_rmsd(A: np.ndarray, B: np.ndarray) -> float:
    A = A - A.mean(axis=0)
    B = B - B.mean(axis=0)
    H = A.T @ B
    U, _, Vt = np.linalg.svd(H)
    d = float(np.sign(np.linalg.det(Vt.T @ U.T)))
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    diff = A @ R.T - B
    return float(np.sqrt((diff ** 2).sum() / A.shape[0]))


def compute_s(rmsds: np.ndarray, lam: float, squared: bool) -> float:
    d = rmsds ** 2 if squared else rmsds
    weights = np.exp(-lam * d)
    num = sum((i + 1) * w for i, w in enumerate(weights))
    return num / weights.sum()


def main() -> int:
    # Load 5DVZ chain A, selected residues, in nm
    five_dvz = extract_5dvz_ca(FIVE_DVZ_PDB, chain_id="A")
    print(f"Loaded 5DVZ chain A selection: {five_dvz.shape[0]} Cα atoms")
    assert five_dvz.shape[0] == 112, f"expected 112, got {five_dvz.shape[0]}"

    # Load the 15 job frames
    frames = []
    for i in range(1, 16):
        frames.append(load_job_frame(JOB_FRAMES_DIR / f"frame_{i:02d}.pdb"))

    # Compute RMSD from 5DVZ to each frame (both in nm)
    rmsds = np.array([kabsch_rmsd(five_dvz, f) for f in frames])
    print(f"\nRMSD (5DVZ → frame_i), in nm:")
    for i, r in enumerate(rmsds, start=1):
        print(f"  frame_{i:02d}: {r:.4f} nm = {r*10:.3f} Å")

    closest_frame = int(np.argmin(rmsds)) + 1
    print(f"\nClosest frame: {closest_frame} (RMSD = {rmsds.min():.4f} nm)")

    # Project under both conventions, fixed LAMBDA
    s_plain = compute_s(rmsds, LAMBDA_FIX, squared=False)
    s_sq = compute_s(rmsds, LAMBDA_FIX, squared=True)

    print("\n" + "=" * 78)
    print(f"PROJECTION of 5DVZ onto path CV with LAMBDA={LAMBDA_FIX}")
    print("=" * 78)
    print(f"  s(5DVZ) under PLAIN RMSD convention:   {s_plain:.4f}")
    print(f"  s(5DVZ) under SQUARED convention:      {s_sq:.4f}")
    print(f"  Target for O-state endpoint:           1.00")
    print(f"  Observed in COLVAR at t=0 (old run):   7.79")

    # Also project under the broken LAMBDA so we can compare directly
    s_plain_broken = compute_s(rmsds, 3.391, squared=False)
    s_sq_broken = compute_s(rmsds, 3.391, squared=True)
    print(f"\n  For reference, under broken LAMBDA=3.391:")
    print(f"    s(5DVZ) plain:  {s_plain_broken:.4f}")
    print(f"    s(5DVZ) SQUARED: {s_sq_broken:.4f}")

    print("\n" + "=" * 78)
    print("VERDICT for checklist item 2:")
    print("=" * 78)
    if s_sq < 3.0:
        print(f"  ✓ 5DVZ maps to s = {s_sq:.2f} (near O state)")
        print(f"  → LAMBDA fix alone is sufficient. Path is usable.")
        print(f"  → Can restart from equil.rst7 and expect initial s ≈ 1-3.")
    elif s_sq > 12.0:
        print(f"  ✗ 5DVZ maps to s = {s_sq:.2f} (near C state — nonsense)")
        print(f"  → Path is fundamentally wrong: endpoint labels may be swapped.")
        print(f"  → Regenerate path.")
    else:
        print(f"  ✗ 5DVZ maps to s = {s_sq:.2f} (middle of path, should be 1)")
        print(f"  → Path endpoints (1WDW, 3CEP) do NOT represent the same O/C")
        print(f"    states as 5DVZ / 5DW0. Ain-state crystal structures may have")
        print(f"    significantly different COMM domain geometry than the cofactor-")
        print(f"    free crystals used for path construction.")
        print(f"  → ACTION REQUIRED: regenerate path using 5DVZ (or 5DVZ-derived)")
        print(f"    as the O-state endpoint, or use a longer conventional MD to")
        print(f"    sample a broader O-state ensemble before building the path.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
