# VERIFICATION_REPORT

## Verdict

Independent recomputation from raw PDBs confirms the sequence-aligned `1WDW-B -> 3CEP-B` path. The production-ready file `path_seqaligned_gromacs.pdb` was built with the original Longleaf atom serials preserved. Strict 0.01-tolerance verification gives 7/8 PASS. The only strict mismatch is `Sequence identity (%)` because the Claude summary rounded the value.

## PASS/FAIL vs Claude numbers

| Claim | Claude | Independent | |diff| | Status |
| --- | --- | --- | --- | --- |
| Uniform offset across 112 residues | 5.0000 | 5.0000 | 0.0000 | PASS |
| 1WDW resid 97 maps to 3CEP resid 102 | 102.0000 | 102.0000 | 0.0000 | PASS |
| Sequence identity (%) | 59.0000 | 59.0331 | 0.0331 | FAIL |
| Endpoint RMSD (A) | 2.1150 | 2.1149 | 0.0001 | PASS |
| Mean adjacent MSD (A^2) | 0.0228 | 0.0228 | 0.0000 | PASS |
| Lambda (A^-2) | 100.7900 | 100.7916 | 0.0016 | PASS |
| Self-projection frame 1 s | 1.0900 | 1.0913 | 0.0013 | PASS |
| Self-projection frame 15 s | 14.9100 | 14.9087 | 0.0013 | PASS |

Derived check (not part of the 8-claim gate): `neighbor_msd_cv = 1.960036e-14`.

## Independent NW result

- `1WDW-B` length: 385 residues
- `3CEP-B` length: 393 residues
- NW score: 286
- Sequence identity: 59.0331%
- Uniform mapping offset on the 112 target residues: +5
- Root-cause contrast: naive number match gives 6.2500% identity and endpoint RMSD 10.8947 A

## Residue mapping table (first 5 + last 5)

| 1WDW resid | 3CEP resid | Offset |
| --- | --- | --- |
| 97 | 102 | 5 |
| 98 | 103 | 5 |
| 99 | 104 | 5 |
| 100 | 105 | 5 |
| 101 | 106 | 5 |
| 301 | 306 | 5 |
| 302 | 307 | 5 |
| 303 | 308 | 5 |
| 304 | 309 | 5 |
| 305 | 310 | 5 |

## Path geometry

- Endpoint RMSD after Kabsch on the mapped 112 Ca: 2.114851 A
- Mean adjacent MSD: 0.022819 A^2
- Neighbor MSD CV: 1.960036e-14
- Branduardi lambda: 100.791625 A^-2
- Current production path for comparison: mean adjacent MSD 0.605590 A^2, lambda 3.797948 A^-2
- Miguel email reference: lambda 80.000000 A^-2, ratio new/current = 26.5384x, new/Miguel = 1.2599x

## Per-frame adjacent MSD table

| Step | MSD (A^2) |
| --- | --- |
| 01->02 | 0.022819 |
| 02->03 | 0.022819 |
| 03->04 | 0.022819 |
| 04->05 | 0.022819 |
| 05->06 | 0.022819 |
| 06->07 | 0.022819 |
| 07->08 | 0.022819 |
| 08->09 | 0.022819 |
| 09->10 | 0.022819 |
| 10->11 | 0.022819 |
| 11->12 | 0.022819 |
| 12->13 | 0.022819 |
| 13->14 | 0.022819 |
| 14->15 | 0.022819 |

## Self-projection of the 15 reference frames

| Frame | s | z (A^2) |
| --- | --- | --- |
| 01 | 1.091298 | -0.000949 |
| 02 | 2.000168 | -0.001814 |
| 03 | 3.000000 | -0.001815 |
| 04 | 4.000000 | -0.001815 |
| 05 | 5.000000 | -0.001815 |
| 06 | 6.000000 | -0.001815 |
| 07 | 7.000000 | -0.001815 |
| 08 | 8.000000 | -0.001815 |
| 09 | 9.000000 | -0.001815 |
| 10 | 10.000000 | -0.001815 |
| 11 | 11.000000 | -0.001815 |
| 12 | 12.000000 | -0.001815 |
| 13 | 13.000000 | -0.001815 |
| 14 | 13.999832 | -0.001814 |
| 15 | 14.908702 | -0.000949 |

Monotonicity check: PASS
Max abs(z): 0.001815 A^2

## Projection of candidate crystal structures onto the new path

| Code | Chain | Mapped | Offset(s) | SeqID % | s | z (A^2) | RMSD->O (A) | RMSD->C (A) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5DW0 | A | 112 | 0 | 99.23 | 9.4550 | 0.8400 | 1.5714 | 1.2400 |
| 5DW3 | A | 111 | 0 | 99.22 | 8.5079 | 0.8197 | 1.4466 | 1.3312 |
| 5DVZ | A | 112 | 0 | 99.48 | 5.3711 | 1.3127 | 1.3236 | 1.8455 |
| 4HPX | B | 112 | 5 | 58.73 | 14.8976 | 0.0167 | 2.1149 | 0.1332 |

## Production artifact checks

| Check | Value |
| --- | --- |
| Models | 15 |
| Atoms per model | 112 |
| Template serial preserved | YES |
| Trailing END record | NO |
| Template file | replication/metadynamics/single_walker/path_gromacs.pdb |
| Coord diff vs existing path_seqaligned.pdb | 0.000000 A |

## Diff vs Claude numbers

- Sequence identity (%): Claude 59.0000, independent 59.0331, |diff| = 0.0331 -> FAIL
- The largest absolute delta among the 8 checked claims was 0.033079.
