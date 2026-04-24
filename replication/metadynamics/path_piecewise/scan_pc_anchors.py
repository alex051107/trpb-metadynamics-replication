#!/usr/bin/env python3
"""
Project candidate PC anchors onto the current direct 1WDW→3CEP path.

Per PM directive 2026-04-23: the MODEL-8 single-λ design failed audit
(neighbor_msd_cv=0.96 on 5DW0/5DW3). Question is now whether any βPC-labeled
experimental structure actually falls near the geometric midpoint of the
direct path in the 112-Cα PATHMSD subspace.

For each candidate C:
  1. Extract its 112 Cα on residues 97-184 + 282-305 (same selection as path)
  2. Kabsch-align onto each of the 15 reference frames individually
  3. Compute per-frame MSDᵢ(R)
  4. Apply PATHMSD formula with λ=3.77 Å⁻²:
       s(R) = Σ i·exp(-λ·MSDᵢ) / Σ exp(-λ·MSDᵢ)
       z(R) = -1/λ · ln Σ exp(-λ·MSDᵢ)
  5. Report s, z, RMSD_to_O, RMSD_to_C, verdict

Healthy PC anchor needs: s ≈ 5-10, z not huge, RMSD_to_O and RMSD_to_C
both substantial (not extremely lopsided like 5DW0/5DW3).

Pure numpy — no MDAnalysis dependency.
"""

import argparse
import sys
from pathlib import Path
import numpy as np

COMM_RESIDUES = list(range(97, 185))
BASE_RESIDUES = list(range(282, 306))
ATOMS_OF_INTEREST = set(COMM_RESIDUES + BASE_RESIDUES)
LAMBDA = 3.77  # Å⁻²  — current direct path

# Default chain per anchor (β-subunit chain)
CHAIN_MAP = {
    "1WDW": "B",
    "3CEP": "B",
    "5DW0": "A",
    "5DW3": "A",
    "5DVZ": "A",
    "4HPX": "A",   # C-side sanity reference only
}


def parse_pdb_ca(path: Path, chain: str, residues: set):
    """Return ordered lists (resids, coords Nx3) of first-altloc Cα on chain."""
    found = {}
    with open(path) as f:
        for line in f:
            if not line.startswith("ATOM  "):
                continue
            if line[12:16].strip() != "CA":
                continue
            if line[16] not in (" ", "A"):
                continue
            if line[21] != chain:
                continue
            try:
                r = int(line[22:26])
            except ValueError:
                continue
            if r not in residues:
                continue
            if r in found:
                continue
            found[r] = np.array([float(line[30:38]),
                                 float(line[38:46]),
                                 float(line[46:54])])
    return found


def parse_multimodel_path(path: Path):
    """Parse 15-MODEL path.pdb. Returns list of 15 coord arrays."""
    frames = []
    current = []
    with open(path) as f:
        for line in f:
            if line.startswith("MODEL"):
                current = []
            elif line.startswith("ATOM"):
                current.append([float(line[30:38]),
                                float(line[38:46]),
                                float(line[46:54])])
            elif line.startswith("ENDMDL") and current:
                frames.append(np.array(current))
                current = []
    return frames


def kabsch_msd(mobile: np.ndarray, target: np.ndarray) -> float:
    """Per-atom MSD after optimal Kabsch alignment of mobile onto target."""
    c_mob = mobile.mean(axis=0)
    c_tgt = target.mean(axis=0)
    M = mobile - c_mob
    T = target - c_tgt
    H = M.T @ T
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    aligned = (R @ M.T).T
    diff = aligned - T
    return float(np.mean(np.sum(diff ** 2, axis=1)))


def project_pathmsd(candidate: np.ndarray, frames: list, lam: float):
    """PATHMSD s(R), z(R) for candidate vs 15 reference frames."""
    N = len(frames)
    assert N == 15
    msds = np.array([kabsch_msd(candidate, fr) for fr in frames])
    # Shift for numerical stability
    shift = -lam * msds
    shift -= shift.max()
    w = np.exp(shift)
    i_idx = np.arange(1, N + 1)
    s = float(np.sum(i_idx * w) / np.sum(w))
    # z with original (unshifted) kernel — reconstruct
    log_sum = shift.max() + np.log(w.sum())
    z = float(-log_sum / lam)
    return s, z, msds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True,
                    help="Multi-MODEL direct path.pdb (15 frames x 112 Cα)")
    ap.add_argument("--structures", default="structures")
    ap.add_argument("--candidates", nargs="+",
                    default=["5DW0", "5DW3", "5DVZ", "4HPX"])
    ap.add_argument("--output", default="pc_anchor_scan.txt")
    args = ap.parse_args()

    # Load direct path
    frames = parse_multimodel_path(Path(args.path))
    print(f"Loaded direct path: {len(frames)} frames × {len(frames[0])} atoms")
    print(f"Using λ = {LAMBDA} Å⁻² (direct path Branduardi)")
    print()

    # Load 1WDW / 3CEP for O/C RMSD reference
    struct_dir = Path(args.structures)

    # To match path's 112-atom ordering we must use the SAME resid order
    # the path was built from. Since direct path doesn't preserve resid
    # metadata (atoms are renumbered 1..112), we assume the path was built
    # from residues 97-184 + 282-305 ORDERED INCREASING.
    resid_order = sorted(ATOMS_OF_INTEREST)
    assert len(resid_order) == 112

    def load_candidate(code):
        pdb = struct_dir / f"{code}.pdb"
        chain = CHAIN_MAP.get(code, "B")
        d = parse_pdb_ca(pdb, chain, ATOMS_OF_INTEREST)
        missing = [r for r in resid_order if r not in d]
        if len(missing) > 5:
            return None, f"missing {len(missing)}/112 resids on chain {chain}"
        # Allow up to 5 missing: project on the intersection with path
        common = [r for r in resid_order if r in d]
        return (np.stack([d[r] for r in common]), common), None

    # O and C references for RMSD sanity
    r, err = load_candidate("1WDW")
    if err:
        print(f"FATAL: 1WDW failed: {err}"); sys.exit(2)
    O_coords, O_resids = r
    r, err = load_candidate("3CEP")
    if err:
        print(f"FATAL: 3CEP failed: {err}"); sys.exit(2)
    C_coords, C_resids = r

    print(f"{'code':6} {'chain':5} {'s(R)':>7} {'z(R)[Å²]':>9} "
          f"{'RMSD→O':>8} {'RMSD→C':>8} {'MSD_min':>8} {'argmin':>6} verdict")
    print("─" * 90)

    rows = []
    for code in args.candidates:
        r, err = load_candidate(code)
        if err:
            print(f"{code:6} {'':5} {'':>7} {'':>9} {'':>8} {'':>8} {'':>8} {'':>6} SKIP ({err})")
            continue
        coords, cand_resids = r

        # Project: need frames to subset to matching resids if any missing
        # For simplicity, if candidate has all 112 resids, use full frames.
        # Otherwise subset frame coords by candidate's resid order indices.
        if len(cand_resids) == 112:
            use_frames = frames
        else:
            idx = [resid_order.index(r) for r in cand_resids]
            use_frames = [fr[idx] for fr in frames]

        s, z, msds = project_pathmsd(coords, use_frames, LAMBDA)
        # Same subset for O / C
        if len(cand_resids) == 112:
            rmsd_o = np.sqrt(kabsch_msd(coords, O_coords))
            rmsd_c = np.sqrt(kabsch_msd(coords, C_coords))
        else:
            idx = [resid_order.index(r) for r in cand_resids]
            rmsd_o = np.sqrt(kabsch_msd(coords, O_coords[idx]))
            rmsd_c = np.sqrt(kabsch_msd(coords, C_coords[idx]))
        msd_min = float(msds.min())
        argmin = int(np.argmin(msds) + 1)  # 1-indexed frame

        # Verdict
        if 5.0 <= s <= 10.0 and abs(z) < 1.0 and \
           rmsd_o > 3.0 and rmsd_c > 3.0:
            verdict = "✓ PC candidate"
        elif s < 3.0:
            verdict = "✗ O-proximal (not PC)"
        elif s > 12.0:
            verdict = "✗ C-proximal (not PC)"
        elif abs(z) >= 1.0:
            verdict = "⚠ off-path high z"
        else:
            verdict = "⚠ borderline"

        print(f"{code:6} {CHAIN_MAP[code]:5} {s:7.3f} {z:9.4f} "
              f"{rmsd_o:8.3f} {rmsd_c:8.3f} {msd_min:8.4f} {argmin:6d} {verdict}")
        rows.append((code, CHAIN_MAP[code], s, z, rmsd_o, rmsd_c, msd_min, argmin, verdict))

    # Write output file
    with open(args.output, 'w') as f:
        f.write(f"PC anchor projection scan — 2026-04-23\n")
        f.write(f"Direct path: {args.path}\n")
        f.write(f"λ = {LAMBDA} Å⁻²\n")
        f.write(f"Selection: residues 97-184 + 282-305 (112 Cα)\n\n")
        f.write(f"{'code':6} {'chain':5} {'s(R)':>7} {'z(R)[Å²]':>9} "
                f"{'RMSD→O':>8} {'RMSD→C':>8} {'MSD_min':>8} {'argmin':>6} verdict\n")
        f.write("─" * 90 + "\n")
        for r in rows:
            f.write(f"{r[0]:6} {r[1]:5} {r[2]:7.3f} {r[3]:9.4f} "
                    f"{r[4]:8.3f} {r[5]:8.3f} {r[6]:8.4f} {r[7]:6d} {r[8]}\n")
        f.write("\nHealthy PC criteria:\n")
        f.write("  • s(R) ∈ [5, 10]  (geometric midpoint of 15-frame path)\n")
        f.write("  • |z(R)| < 1 Å²   (on-path, not off to the side)\n")
        f.write("  • RMSD_to_O > 3 Å (substantial deformation from Open)\n")
        f.write("  • RMSD_to_C > 3 Å (still far from Closed)\n\n")
        f.write("Interpretation notes:\n")
        f.write("  4HPX is a C-side (Q₂) reference — expected s ≈ 15, not PC.\n")
        f.write("  5DVZ is LLP (internal aldimine) intermediate — chemical, not geom PC.\n")
        f.write("  5DW0 / 5DW3 are β-partially-closed by label, but this scan tests\n")
        f.write("  whether they land geometrically at s ≈ 5-10 in our CV space.\n")

    print(f"\n✓ wrote {args.output}")


if __name__ == "__main__":
    main()
