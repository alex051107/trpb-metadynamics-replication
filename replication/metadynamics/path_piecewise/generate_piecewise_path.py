#!/usr/bin/env python3
"""
Piecewise 3-anchor path generator for TrpB COMM O→PC→C transition.

Diagnostic pilot per PM instruction 2026-04-23: insert a PC anchor at MODEL 8
and linearly interpolate O→PC (frames 1-8) + PC→C (frames 8-15). Preserves
global semantics O=1, PC=8, C=15.

Anchors:
  O  (MODEL 1)  = 1WDW chain B (P. furiosus, Open)
  PC (MODEL 8)  = 5DW0 chain A or 5DW3 chain A (Partially Closed)
  C  (MODEL 15) = 3CEP chain B (S. typhimurium, Closed)

All three are Kabsch-aligned onto O's 112-Cα selection (residues 97-184
+ 282-305) before interpolation.

Pure numpy — no MDAnalysis / BioPython dependency.

Output:
  path.pdb            — 15-MODEL PLUMED PATH file (atom serials 1..N per MODEL)
  summary.txt         — per-segment MSD, neighbor_msd_cv, λ
  plumed_path.dat     — ready-to-paste PATHMSD snippet with LAMBDA
"""

import argparse
import sys
from pathlib import Path
import numpy as np

COMM_RESIDUES = list(range(97, 185))
BASE_RESIDUES = list(range(282, 306))
ATOMS_OF_INTEREST = set(COMM_RESIDUES + BASE_RESIDUES)
NUM_FRAMES = 15
LAMBDA_SCALE = 2.3

CHAIN_MAP = {
    "1WDW": "B",
    "3CEP": "B",
    "5DW0": "A",
    "5DW3": "A",
}


def parse_pdb_ca(path: Path, chain: str, residues: set):
    """Return dict {resid: (x,y,z)} of CA atoms on given chain & resids.

    Uses only first altloc per residue. Skips HETATM.
    """
    found = {}
    with open(path) as f:
        for line in f:
            if not line.startswith("ATOM  "):
                continue
            atom_name = line[12:16].strip()
            if atom_name != "CA":
                continue
            alt = line[16]
            if alt not in (" ", "A"):
                continue
            chain_id = line[21]
            if chain_id != chain:
                continue
            try:
                resid = int(line[22:26])
            except ValueError:
                continue
            if resid not in residues:
                continue
            if resid in found:  # first occurrence wins
                continue
            x = float(line[30:38]); y = float(line[38:46]); z = float(line[46:54])
            found[resid] = np.array([x, y, z])
    return found


def kabsch_align(mobile: np.ndarray, target: np.ndarray) -> np.ndarray:
    c_mob = mobile.mean(axis=0)
    c_tgt = target.mean(axis=0)
    M = mobile - c_mob
    T = target - c_tgt
    H = M.T @ T
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    return (R @ M.T).T + c_tgt


def interp(a, b, n):
    return [(1 - i / (n - 1)) * a + (i / (n - 1)) * b for i in range(n)]


def msd_per_atom(c1, c2):
    return float(np.mean(np.sum((c1 - c2) ** 2, axis=1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pc", required=True, choices=["5DW0", "5DW3"])
    ap.add_argument("--structures", default="structures")
    ap.add_argument("--output-dir", default=None)
    args = ap.parse_args()

    struct_dir = Path(args.structures)
    out_dir = Path(args.output_dir or f"path_{args.pc}")
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Piecewise path: 1WDW → {args.pc} → 3CEP ===")
    print(f"Residues: 97-184 + 282-305 (|target| = {len(ATOMS_OF_INTEREST)})")
    print(f"PC = {args.pc} chain {CHAIN_MAP[args.pc]}\n")

    # Load three anchors
    anchor_coords = {}
    for code in ("1WDW", args.pc, "3CEP"):
        chain = CHAIN_MAP[code]
        d = parse_pdb_ca(struct_dir / f"{code}.pdb", chain, ATOMS_OF_INTEREST)
        if len(d) < 100:
            print(f"ERROR: {code} chain {chain} gave only {len(d)} Cα")
            sys.exit(2)
        anchor_coords[code] = d
        print(f"  {code} chain {chain}: {len(d)} Cα "
              f"(resid span {min(d)}-{max(d)})")

    # Common resids across all three
    common = sorted(set(anchor_coords["1WDW"]) &
                    set(anchor_coords[args.pc]) &
                    set(anchor_coords["3CEP"]))
    n = len(common)
    print(f"\nCommon resids = {n}")
    if n < 100:
        print("ERROR: <100 common — abort.")
        sys.exit(2)

    def stack(code):
        return np.stack([anchor_coords[code][r] for r in common])

    O = stack("1WDW")
    PC = stack(args.pc)
    C = stack("3CEP")

    # Kabsch PC, C onto O
    PC_a = kabsch_align(PC, O)
    C_a = kabsch_align(C, O)

    rmsd_o_pc = np.sqrt(msd_per_atom(O, PC_a))
    rmsd_pc_c = np.sqrt(msd_per_atom(PC_a, C_a))
    rmsd_o_c = np.sqrt(msd_per_atom(O, C_a))
    print(f"\nAnchor distances (per-atom RMSD after Kabsch onto O):")
    print(f"  O  ↔ PC  = {rmsd_o_pc:.3f} Å")
    print(f"  PC ↔ C   = {rmsd_pc_c:.3f} Å")
    print(f"  O  ↔ C   = {rmsd_o_c:.3f} Å")

    # Build 15 frames
    seg1 = interp(O, PC_a, 8)      # frames 1..8
    seg2 = interp(PC_a, C_a, 8)    # frames 8..15
    frames = seg1 + seg2[1:]       # 15 total
    assert len(frames) == NUM_FRAMES
    assert np.allclose(frames[0], O)
    assert np.allclose(frames[7], PC_a)
    assert np.allclose(frames[14], C_a)

    # Adjacent MSD
    print(f"\nAdjacent MSD (per-atom, Å²):")
    msds = []
    for i in range(NUM_FRAMES - 1):
        m = msd_per_atom(frames[i], frames[i + 1])
        msds.append(m)
        seg = "O→PC" if i < 7 else "PC→C"
        print(f"  {i+1:2d} → {i+2:2d} [{seg}]: {m:.4f}")

    msds = np.array(msds)
    mean_msd = float(msds.mean())
    std_msd = float(msds.std())
    cv = std_msd / mean_msd

    lam = LAMBDA_SCALE / mean_msd
    mean_s1 = float(msds[:7].mean())
    mean_s2 = float(msds[7:].mean())
    lam_s1 = LAMBDA_SCALE / mean_s1
    lam_s2 = LAMBDA_SCALE / mean_s2

    print(f"\n━━━ λ REPORT ━━━")
    print(f"  mean adjacent MSD (14 intervals) = {mean_msd:.4f} Å²")
    print(f"  std / mean (neighbor_msd_cv)     = {cv:.3f}  "
          f"({'✓ ≤0.15' if cv <= 0.15 else '⚠ >0.15 (uneven spacing)'})")
    print(f"  ★ λ single-path                   = {lam:.4f} Å⁻² "
          f"(= {lam*100:.4f} nm⁻²)")
    print(f"  O→PC segment: ⟨MSD⟩={mean_s1:.4f}  → λ={lam_s1:.4f} Å⁻²")
    print(f"  PC→C segment: ⟨MSD⟩={mean_s2:.4f}  → λ={lam_s2:.4f} Å⁻²")
    print(f"\nVs direct 1WDW→3CEP (⟨MSD⟩≈0.61 Å², λ=3.77 Å⁻²):")
    print(f"  MSD ratio  = {mean_msd/0.61:.2f}×")
    print(f"  λ   ratio  = {lam/3.77:.2f}×")

    # Write path.pdb
    path_file = out_dir / "path.pdb"
    with open(path_file, 'w') as f:
        for midx, coords in enumerate(frames, start=1):
            f.write(f"MODEL     {midx:4d}\n")
            for aidx, (r, pos) in enumerate(zip(common, coords), start=1):
                f.write(
                    f"ATOM  {aidx:5d}  CA  GLY A{r:4d}    "
                    f"{pos[0]:8.3f}{pos[1]:8.3f}{pos[2]:8.3f}"
                    f"  1.00  0.00           C  \n"
                )
            f.write("ENDMDL\n")

    # Summary
    summary_file = out_dir / "summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Piecewise path summary — PC = {args.pc}\n")
        f.write("=" * 60 + "\n")
        f.write(f"O  (MODEL 1)  = 1WDW chain B\n")
        f.write(f"PC (MODEL 8)  = {args.pc} chain {CHAIN_MAP[args.pc]}\n")
        f.write(f"C  (MODEL 15) = 3CEP chain B\n")
        f.write(f"Residues: 97-184 + 282-305 (common Cα = {n})\n\n")
        f.write(f"Anchor RMSDs (Kabsch onto O):\n")
        f.write(f"  O ↔ PC  = {rmsd_o_pc:.3f} Å\n")
        f.write(f"  PC ↔ C  = {rmsd_pc_c:.3f} Å\n")
        f.write(f"  O ↔ C   = {rmsd_o_c:.3f} Å\n\n")
        f.write(f"Adjacent MSD (Å²):\n")
        for i, m in enumerate(msds, start=1):
            seg = "O→PC" if i <= 7 else "PC→C"
            f.write(f"  {i:2d}→{i+1:2d} [{seg}]: {m:.4f}\n")
        f.write(f"\nStatistics:\n")
        f.write(f"  mean = {mean_msd:.4f} Å²\n")
        f.write(f"  std  = {std_msd:.4f} Å²\n")
        f.write(f"  CV   = {cv:.3f}\n\n")
        f.write(f"λ values (Branduardi 2.3/⟨MSD⟩):\n")
        f.write(f"  Single-path λ  = {lam:.4f} Å⁻²  (= {lam*100:.4f} nm⁻²)\n")
        f.write(f"  O→PC  segment  = {lam_s1:.4f} Å⁻²\n")
        f.write(f"  PC→C  segment  = {lam_s2:.4f} Å⁻²\n")
        f.write(f"\nDirect 1WDW→3CEP reference: ⟨MSD⟩≈0.61 Å², λ=3.77 Å⁻²\n")
        f.write(f"  MSD ratio (piecewise/direct) = {mean_msd/0.61:.2f}×\n")
        f.write(f"  λ   ratio (piecewise/direct) = {lam/3.77:.2f}×\n")

    plumed_file = out_dir / "plumed_path.dat"
    with open(plumed_file, 'w') as f:
        f.write(f"# Piecewise path: 1WDW → {args.pc} → 3CEP\n")
        f.write(f"# neighbor_msd_cv = {cv:.3f}\n")
        f.write(f"p1: PATHMSD REFERENCE=path.pdb LAMBDA={lam:.4f} "
                f"NEIGH_STRIDE=100 NEIGH_SIZE=6\n")

    print(f"\n  ✓ wrote {path_file}")
    print(f"  ✓ wrote {summary_file}")
    print(f"  ✓ wrote {plumed_file}")


if __name__ == "__main__":
    main()
