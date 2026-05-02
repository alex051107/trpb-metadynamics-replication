#!/usr/bin/env python3
"""
Rebuild TrpB O→C 15-frame PATHMSD reference path with PROPER cross-species
sequence-aligned residue mapping.

CRITICAL BUG FIX (2026-04-23): our previous path (single_walker/path_gromacs.pdb)
compared 1WDW-B (Pf) residue X vs 3CEP-B (St) residue X by naive residue-number
match. But 3CEP-B starts at resid 2 with 5 extra N-terminal residues vs 1WDW-B,
so residue 97 in 1WDW is homologous to residue 102 in 3CEP, NOT residue 97.

Naive mapping: 6.2% sequence identity at matched positions → spurious 10.89 Å
O↔C RMSD → λ = 3.80 Å⁻² (21× too small vs Miguel's 80).

Sequence-aligned mapping: 59.0% identity → 2.115 Å O↔C RMSD → ⟨MSD⟩ = 0.0228 Å²
→ λ = 100.79 Å⁻² ≈ Miguel's 80 within 26%.

This script:
1. Needleman-Wunsch aligns 1WDW-B and 3CEP-B full β sequences
2. Maps residues 97-184 + 282-305 (COMM + base) of 1WDW-B to homologous
   residues in 3CEP-B (offset +5 throughout)
3. Kabsch-aligns the 112 mapped Cα of 3CEP onto 1WDW's 112 Cα
4. Linear interpolation → 15 frames
5. Writes path_seqaligned.pdb + summary.txt + plumed_path.dat

Pure numpy; no BioPython dependency.
"""

import argparse
import sys
from pathlib import Path
import numpy as np

AA3 = {'ALA':'A','ARG':'R','ASN':'N','ASP':'D','CYS':'C','GLU':'E','GLN':'Q',
       'GLY':'G','HIS':'H','ILE':'I','LEU':'L','LYS':'K','MET':'M','PHE':'F',
       'PRO':'P','SER':'S','THR':'T','TRP':'W','TYR':'Y','VAL':'V'}

COMM_RESIDUES = list(range(97, 185))   # 88 residues
BASE_RESIDUES = list(range(282, 306))  # 24 residues
NUM_FRAMES = 15


def load_ca(pdb, chain):
    seq, resids, coords = [], [], []
    seen = set()
    with open(pdb) as f:
        for line in f:
            if not line.startswith("ATOM  "): continue
            if line[12:16].strip() != "CA": continue
            if line[16] not in " A": continue
            if line[21] != chain: continue
            try: r = int(line[22:26])
            except ValueError: continue
            if r in seen: continue
            seen.add(r)
            seq.append(AA3.get(line[17:20].strip(), 'X'))
            resids.append(r)
            coords.append([float(line[30:38]),
                           float(line[38:46]),
                           float(line[46:54])])
    return "".join(seq), resids, np.array(coords)


def needleman_wunsch(s1, s2, match=2, mismatch=-1, gap=-2):
    m, n = len(s1), len(s2)
    M = np.zeros((m + 1, n + 1), dtype=int)
    T = np.zeros((m + 1, n + 1), dtype=int)
    for i in range(1, m + 1): M[i, 0] = i * gap; T[i, 0] = 1
    for j in range(1, n + 1): M[0, j] = j * gap; T[0, j] = 2
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            d = M[i-1, j-1] + (match if s1[i-1] == s2[j-1] else mismatch)
            u = M[i-1, j] + gap
            l = M[i, j-1] + gap
            best = max(d, u, l)
            M[i, j] = best
            T[i, j] = 0 if best == d else (1 if best == u else 2)
    aligned1, aligned2 = [], []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and T[i, j] == 0:
            aligned1.append(s1[i-1]); aligned2.append(s2[j-1]); i -= 1; j -= 1
        elif i > 0 and T[i, j] == 1:
            aligned1.append(s1[i-1]); aligned2.append('-'); i -= 1
        else:
            aligned1.append('-'); aligned2.append(s2[j-1]); j -= 1
    return "".join(reversed(aligned1)), "".join(reversed(aligned2)), M[m, n]


def build_mapping(a1, a3, resids1, resids3):
    """alignment strings → {resid_1wdw: resid_3cep}."""
    mapping = {}
    i1 = i3 = 0
    for c1, c3 in zip(a1, a3):
        if c1 != '-' and c3 != '-':
            mapping[resids1[i1]] = resids3[i3]
        if c1 != '-': i1 += 1
        if c3 != '-': i3 += 1
    return mapping


def kabsch(mob, tgt):
    cm, ct = mob.mean(0), tgt.mean(0)
    M, T = mob - cm, tgt - ct
    H = M.T @ T
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1.0, 1.0, d])
    R = Vt.T @ D @ U.T
    return (R @ M.T).T + ct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--structures", default="../path_piecewise/structures")
    ap.add_argument("--output-dir", default=".")
    args = ap.parse_args()

    struct = Path(args.structures)
    out = Path(args.output_dir); out.mkdir(exist_ok=True, parents=True)

    # 1. Load
    s1, r1, c1 = load_ca(struct / "1WDW.pdb", "B")
    s3, r3, c3 = load_ca(struct / "3CEP.pdb", "B")
    print(f"1WDW-B: {len(s1)} residues, resid {r1[0]}-{r1[-1]}")
    print(f"3CEP-B: {len(s3)} residues, resid {r3[0]}-{r3[-1]}")

    # 2. NW
    a1, a3, score = needleman_wunsch(s1, s3)
    ident = sum(1 for x, y in zip(a1, a3) if x == y and x != '-') / max(len(s1), len(s3))
    print(f"\nNW score: {score}")
    print(f"Sequence identity: {100*ident:.1f}%")

    # 3. Mapping
    mapping = build_mapping(a1, a3, r1, r3)
    target = COMM_RESIDUES + BASE_RESIDUES
    mapped = [(r, mapping.get(r)) for r in target]
    missing = [r for r, m in mapped if m is None]
    if missing:
        print(f"\nWARNING: {len(missing)} residues unmapped: {missing}")
        sys.exit(2)
    offsets = [mapping[r] - r for r in target]
    print(f"Offset range: {min(offsets)} to {max(offsets)} "
          f"({'uniform' if min(offsets) == max(offsets) else 'variable'})")

    # 4. Extract coords
    lut1 = {r: i for i, r in enumerate(r1)}
    lut3 = {r: i for i, r in enumerate(r3)}
    O = np.stack([c1[lut1[r]] for r in target])
    C = np.stack([c3[lut3[mapping[r]]] for r in target])

    # 5. Kabsch
    C_aligned = kabsch(C, O)
    msd_OC = float(np.mean(np.sum((C_aligned - O)**2, axis=1)))
    rmsd_OC = np.sqrt(msd_OC)
    print(f"\nO↔C per-atom RMSD (sequence-aligned): {rmsd_OC:.3f} Å")

    # 6. Interpolate
    frames = [(1 - i/(NUM_FRAMES-1)) * O + (i/(NUM_FRAMES-1)) * C_aligned
              for i in range(NUM_FRAMES)]

    # 7. Adjacent MSD
    msds = np.array([
        float(np.mean(np.sum((frames[i+1] - frames[i])**2, axis=1)))
        for i in range(NUM_FRAMES - 1)
    ])
    mean_msd = float(msds.mean())
    cv = float(msds.std() / mean_msd)
    lam = 2.3 / mean_msd
    print(f"\n⟨MSD_adj⟩ = {mean_msd:.4f} Å²  (naive path: 0.606)")
    print(f"neighbor_msd_cv = {cv:.4f}")
    print(f"λ = {lam:.4f} Å⁻²  (naive: 3.80; Miguel: 80; ratio = {lam/80:.3f}×)")

    # 8. Self-projection sanity
    def project(cand, frames, lam):
        msds_ = np.array([float(np.mean(np.sum((fr - cand)**2, axis=1))) for fr in frames])
        m = (-lam * msds_).max()
        w = np.exp(-lam * msds_ - m)
        i_idx = np.arange(1, len(frames) + 1)
        s = float(np.sum(i_idx * w) / np.sum(w))
        z = float(-(m + np.log(w.sum())) / lam)
        return s, z

    print(f"\n── Self-projection (sanity) ──")
    print(f"{'frame':>6} {'s':>8} {'z':>10}")
    for k in (0, 1, 7, 13, 14):
        s, z = project(frames[k], frames, lam)
        print(f"  {k+1:2d}    {s:7.3f}   {z:9.4f}")

    # 9. Write PATH.pdb (atom serial 1..N, resid 1..N)
    pdb_out = out / "path_seqaligned.pdb"
    with open(pdb_out, 'w') as f:
        for mi, coords in enumerate(frames, start=1):
            f.write(f"MODEL     {mi:4d}\n")
            for ai, (r, pos) in enumerate(zip(target, coords), start=1):
                # Use Ala placeholder; PATHMSD only cares about Cα coords
                f.write(f"ATOM  {ai:5d}  CA  ALA A{ai:4d}    "
                        f"{pos[0]:8.3f}{pos[1]:8.3f}{pos[2]:8.3f}"
                        f"  1.00  0.00           C  \n")
            f.write("ENDMDL\n")
    print(f"\n✓ wrote {pdb_out}")

    # 10. Summary
    with open(out / "summary.txt", 'w') as f:
        f.write(f"Sequence-aligned TrpB 15-frame path (2026-04-23)\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Bug fix: 1WDW-B vs 3CEP-B naive residue-number mapping was\n")
        f.write(f"comparing non-homologous positions. Proper sequence alignment\n")
        f.write(f"has consistent offset +5: 1WDW resid X -> 3CEP resid (X+5).\n\n")
        f.write(f"Aligned N: {len(target)} Cα\n")
        f.write(f"Selection: COMM 97-184 + base 282-305 (1WDW numbering)\n")
        f.write(f"Corresponding 3CEP: COMM 102-189 + base 287-310\n\n")
        f.write(f"Alignment stats:\n")
        f.write(f"  NW score = {score}\n")
        f.write(f"  sequence identity = {100*ident:.1f}%\n")
        f.write(f"  offset = +5 (uniform across all {len(target)} residues)\n\n")
        f.write(f"Path geometry:\n")
        f.write(f"  O↔C per-atom RMSD = {rmsd_OC:.3f} Å\n")
        f.write(f"  ⟨MSD_adj⟩ = {mean_msd:.4f} Å² per atom\n")
        f.write(f"  neighbor_msd_cv = {cv:.4f}\n")
        f.write(f"  λ = {lam:.4f} Å⁻²  = {lam*100:.2f} nm⁻²\n\n")
        f.write(f"Comparison:\n")
        f.write(f"  naive mapping:   O↔C RMSD 10.89 Å, λ = 3.80 Å⁻²\n")
        f.write(f"  this path:       O↔C RMSD  {rmsd_OC:.3f} Å, λ = {lam:.2f} Å⁻²\n")
        f.write(f"  Miguel email:    λ = 80 Å⁻² (our λ / Miguel = {lam/80:.3f}×)\n")
    print(f"✓ wrote {out / 'summary.txt'}")

    # 11. plumed_path.dat
    with open(out / "plumed_path.dat", 'w') as f:
        f.write(f"# Sequence-aligned 15-frame path\n")
        f.write(f"# neighbor_msd_cv = {cv:.4f}, O↔C RMSD = {rmsd_OC:.3f} Å\n")
        f.write(f"# Branduardi λ = {lam:.2f} Å⁻²; Miguel's email uses LAMBDA=80 Å⁻²\n")
        f.write(f"p1: PATHMSD REFERENCE=path_seqaligned.pdb LAMBDA=80 "
                f"NEIGH_STRIDE=100 NEIGH_SIZE=6\n")
    print(f"✓ wrote {out / 'plumed_path.dat'}")


if __name__ == "__main__":
    main()
