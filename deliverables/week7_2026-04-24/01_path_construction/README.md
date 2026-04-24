# 01 · Path construction (FP-034 fix)

The core fix of the week. The previous path CV naively mapped residue *X* in 1WDW-B to residue *X* in 3CEP-B, which is wrong because the two chains differ by a uniform +5 N-terminal offset. The scripts here rebuild the reference path using a proper cross-species sequence alignment.

## Files

| File | What it is | When you use it |
|---|---|---|
| `build_seqaligned_path.py` | **Primary** build script. Loads `1WDW.pdb` chain B and `3CEP.pdb` chain B, runs numpy-handwritten Needleman-Wunsch, builds the residue-to-residue mapping, checks offset uniformity, Kabsch-aligns 3CEP onto 1WDW for the 112 selected residues, linearly interpolates 15 frames, and writes `path_seqaligned.pdb`. | First step of every rebuild. |
| `verify_and_materialize_seqaligned_path.py` | Independent verification script (Codex-authored, blind re-implementation of NW + offset check). Also produces `path_seqaligned_gromacs.pdb` with atom serials preserved to match GROMACS topology. | Second step; must pass 7+ of 8 strict checks. |
| `path_seqaligned.pdb` | Minimal PATHMSD reference with ALA placeholders and serial 1..N. | Driver-level testing via `plumed driver`. |
| `path_seqaligned_gromacs.pdb` | Production PDB with real residue names and atom serials matching the 39 268-atom GROMACS topology. | This is what `single_walker/plumed.dat` actually references. |
| `summary.txt` | NW score, identity, offset, O↔C RMSD, ⟨MSD⟩, λ, all on one page. | First file to read after a rebuild. |
| `VERIFICATION_REPORT.md` | 8 strict verification checks with pass/fail status. 7 of 8 pass; the one partial is a CV-coverage informational check (not a correctness issue). | Defends the fix against pushback. |
| `REVERSE_SANITY_CHECK.md` | Endpoint round-trip self-projection (1WDW → s = 1.14, 3CEP → s = 14.86) + held-out PC crystal projection (5DW0, 5DW3, 5DVZ, 4HPX). | Biology sanity. |
| `plumed.dat` | Complete PLUMED input used to test `path_seqaligned_gromacs.pdb` on a trajectory. | Diagnostic. |
| `plumed_path.dat` | Minimal PATHMSD line (for driver-level smoke test). | Sanity check. |

## Key numbers (from `summary.txt`)

```
Aligned N           : 112 Cα
Selection           : COMM 97-184 + base 282-305 (1WDW numbering)
Corresponding 3CEP  : COMM 102-189 + base 287-310
NW score            : 286
Sequence identity   : 59.0 %
Offset              : +5 (uniform across all 112 residues)
O↔C per-atom RMSD   : 2.115 Å
⟨MSD_adjacent⟩      : 0.0228 Å²
Branduardi λ        : 100.79 Å⁻²  (1.26 × Miguel's 80, same regime)
```

## Algorithm (reproducible summary)

1. Manual fixed-column PDB reader produces `(seq, resids, coords)` for each chain-B Cα (altloc blank or "A").
2. Needleman-Wunsch with `match = +2, mismatch = -1, gap = -2`. No BioPython, no BLOSUM62 — these choices are equivalent here because `identity > 50 %`, and avoiding the dependencies keeps the algorithm auditable.
3. Walk the two aligned strings in parallel; whenever neither position is a gap, associate `resid_1wdw[i] ↔ resid_3cep[j]`.
4. Compute `offsets = [mapping[r] - r for r in COMM + BASE]`. If `min == max`, a uniform offset is legal; otherwise the +5 fix does not apply and a per-residue remapping would be needed.
5. Kabsch-superimpose 3CEP's 112 Cα onto 1WDW's 112 Cα (SVD-based).
6. Linear interpolation: `frame_i = (1 - i/14) · O + (i/14) · C_aligned` for `i ∈ {0..14}`.

See Technical Manuscript § 1.3 for full prose derivation.
