# P3 high-z cluster analysis

## Method

- Probe: `probe_P3` completed 10 ns trajectory (`metad.xtc`, 10 ps stride) with matching `COLVAR`.
- High-z subset: top 10% of XTC-aligned frames, threshold `z >= 0.078071` (101 / 1001 frames).
- Atom set: 111 common Cα atoms from residues 97-184 and 282-305, excluding residue 285 because `5DW3` chain A lacks it.
- Reference-chain mapping follows the earlier CV audit convention: `1WDW=B`, `3CEP=B`, `4HPX=B`, `5DW0=A`, `5DW3=A`.
- Clustering: KMeans on the 5-reference RMSD feature vectors, `k` chosen by silhouette over 3..5; selected `k=3` with silhouette `0.8752`.

## Cluster Table

| Cluster | Closest reference | Mean RMSD (A) | Frame fraction | Mean z | Mean time (ps) |
|---|---|---:|---:|---:|---:|
| C1 | 5DW3 | 13.065 | 0.198 | 0.084655 | 8995.0 |
| C2 | 5DW3 | 2.453 | 0.624 | 0.099881 | 7975.6 |
| C3 | 5DW0 | 20.167 | 0.178 | 0.083807 | 9147.2 |

## Interpretation

PC-like: The dominant high-z population sits closer to PC references (5DW0/5DW3) than to the open or closed endpoints.

Reference ordering for the RMSD feature vectors was `1WDW, 5DW0, 5DW3, 3CEP, 4HPX`.
