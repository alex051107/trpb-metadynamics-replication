# Reverse sanity check — endpoint crystals project to path boundaries

**Date**: 2026-04-24 (just after FP-034 fix)
**Purpose**: Defend against the Yu-Chen-lens killer question "how do we
know the new path isn't itself an artifact, like the old one was?"

## Method

Project RAW PDB crystal Cα coordinates of the two endpoints through the
corrected `path_seqaligned_gromacs.pdb` using PATHMSD formula
(log-sum-exp stable). For a well-constructed 15-frame path where MODEL 1
derives from 1WDW and MODEL 15 derives from 3CEP(+5), the crystal
structures themselves SHOULD project to s ≈ 1 and s ≈ 15 respectively.

## Results

| Structure | N_Cα | s(λ=80) | s(λ=100) | z(λ=80) Å² | Verdict |
|---|---|---|---|---|---|
| 1WDW-B (resid 97-184 + 282-305) | 112 | **1.140** | 1.093 | -0.002 | ✅ O-end matches |
| 3CEP-B (resid 102-189 + 287-310, NW+5) | 112 | **14.860** | 14.907 | -0.002 | ✅ C-end matches |
| 3CEP-B (naive resid 97-184 + 282-305) | 112 | 6.768 | 6.785 | **117.97** | ❌ massive off-path |

## Interpretation

1. **1WDW projects to s=1.14** (not exactly 1.0 due to the kernel
   averaging boundary effect). Matches the standard PATHMSD behavior
   seen earlier in `plumed driver` self-projection (frame 1 → s=1.091).
2. **3CEP with NW+5 mapping projects to s=14.86** (mirror boundary
   effect). Confirms that residues 102-189 + 287-310 of 3CEP are the
   correct homologous set.
3. **3CEP with naive same-resid (97-184+282-305) projects to s=6.77
   with z=117.97 Å²** — z value is enormous (vs on-path z ≈ 0). This
   positively confirms that naive-mapped 3CEP positions are NOT on the
   path manifold; they're ~10.9 Å RMSD away from any path frame in a
   perpendicular direction. This is the quantitative signature of the
   FP-034 cross-species bug: non-homologous residues → massive z-dev.

## Caveat — self-projection vs independent test

MODEL 1 and MODEL 15 of the path file ARE literally the Kabsch-aligned
1WDW and 3CEP(+5) Cα coordinates. Projecting those raw crystals back is
**internal consistency**, not an external verification. A correctly-built
path is guaranteed to round-trip its endpoints by construction.

The load-bearing INDEPENDENT test comes from non-endpoint PDBs that
were not part of path construction — `VERIFICATION_REPORT.md` Codex
run:

| Candidate | s on corrected path | Biological label |
|---|---|---|
| 5DW0 chain A | 9.455 | PC crystal (mid-path ✓) |
| 5DW3 chain A | 8.508 | PC crystal (mid-path ✓) |
| 5DVZ chain A | 5.371 | LLP intermediate (early mid-path ✓) |
| 4HPX chain A | 14.898 | Q₂ / C-side reference (near C-end ✓) |

These four candidates were never part of path construction, so their
projections are genuine independent tests. All four land at biologically
plausible s-values. This is the actual evidence that the corrected
path's s-coordinate has physical meaning.

## What "offset +5" actually means

NW alignment gave uniform offset +5 across all 112 selected residues
with zero indels in the COMM (97-184) and base (282-305) segments.
Because there are no gaps in that range, the +5 is effectively a
**PDB numbering convention difference** (different N-terminal
signal-peptide handling between 1WDW and 3CEP deposits), not an
alignment "discovery". The value-add of the NW step is not "finding
offset"; it is **proving that no internal indel exists** that would
invalidate 1-to-1 mapping in the selected range. If an indel had been
found, uniform offset would have been mathematically impossible.

## What this still does NOT rule out

- Whether Miguel's 2019 PATH.pdb used the SAME residue selection vs
  some other subset — this still requires his actual file.
- Whether ⟨MSD_adj⟩ = 0.0228 Å² on our path matches his 0.029 exactly
  or happens to be 1.26× by coincidence of linear-interp geometry.

## Reproduction

```python
python3 <<PY
# full code path preserved in the Bash-shell invocation that produced
# this file on 2026-04-24; see repo git log 237136e..HEAD for context.
# key numbers above were computed using:
#   - path_seqaligned_gromacs.pdb 15 MODELs × 112 Cα
#   - 1WDW chain B resid {97-184, 282-305}
#   - 3CEP chain B resid {102-189, 287-310} (NW +5)
#   - PATHMSD log-sum-exp with lam=80 and 100
PY
```

Full runnable version is inline in the commit that added this file.
