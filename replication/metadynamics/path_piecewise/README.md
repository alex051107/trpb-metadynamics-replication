# Path-piecewise audit — REJECTED for production (2026-04-23)

**Verdict: diagnostic artifact only. Do not use PC-at-MODEL8 single-λ
paths for MetaD production or FES claims.**

## What this directory contains

- `generate_piecewise_path.py` — builds 15-frame path with O=MODEL 1,
  PC=MODEL 8, C=MODEL 15; computes per-segment MSD and single-λ
  Branduardi estimate.
- `scan_pc_anchors.py` — projects candidate βPC/intermediate structures
  onto the current direct 1WDW→3CEP path (λ=3.77 Å⁻²) to test whether any
  actually lands near s ≈ 5-10 in the 112-Cα CV subspace.
- `path_5DW0/`, `path_5DW3/` — generated piecewise path files + summaries.
- `pc_anchor_scan.txt` — anchor projection table.
- `structures/` — local PDB inputs.

## Why this was attempted

After Miguel's aggressive single-walker fallback (HEIGHT=0.3, BIASFACTOR=15,
ADAPTIVE=DIFF, λ=3.77 Å⁻²) stalled at max_s=1.496 after 3.76 ns on the
direct 1WDW→3CEP linear-interpolation path, both the PM and ChatGPT Pro
independently reasoned that the rate-limiter is most likely the path
geometry itself (O-endpoint tangent misaligned with physical escape
direction), not the MetaD layer parameters.

The hypothesis under test here: insert 5DW0 or 5DW3 (Table S1 βPC labels)
at MODEL 8 to re-parameterize the path so that frames 1–8 cover the
O→PC half and frames 8–15 cover the PC→C half. If this produces a
healthier path (neighbor_msd_cv ≤ 0.15 per Belfast tutorial), walker
exploration should ratchet forward instead of stalling.

## Findings

### Path builder audit (generate_piecewise_path.py)

| PC anchor | O↔PC RMSD (Å) | PC↔C RMSD (Å) | ⟨MSD⟩ O→PC (Å²) | ⟨MSD⟩ PC→C (Å²) | neighbor_msd_cv | single λ (Å⁻²) |
|---|---|---|---|---|---|---|
| 5DW0 | 1.571 | 11.061 | 0.0504 | 2.4969 | **0.960** ❌ | 1.806 |
| 5DW3 | 1.447 | 10.988 | 0.0427 | 2.4638 | **0.966** ❌ | 1.835 |

Per-segment λ (what a true piecewise path would need):
- O→PC segment: λ ≈ 45.6–53.9 Å⁻² (matches Miguel's native ~80 scale —
  confirms his path is probably O-dense, not a true O→C path)
- PC→C segment: λ ≈ 0.92 Å⁻² (far too loose for meaningful resolution)

`neighbor_msd_cv = 0.96` vs Belfast healthy threshold ≤ 0.15. Off by 6×.
A single-λ PATHMSD on this path would give uninterpretable walker
dynamics: frames 1–8 nearly superimposed (s would glide across them as
artifacts), while frames 8–15 would integer-snap.

### Anchor projection scan (scan_pc_anchors.py)

All locally-available candidates project to s ≈ 1.07 on the direct
1WDW→3CEP path (λ=3.77 Å⁻²):

| Code | Chain | s(R) | z(R) Å² | RMSD→O (Å) | RMSD→C (Å) | Verdict |
|---|---|---|---|---|---|---|
| 5DW0 | A | 1.069 | −0.019 | 1.571 | 11.059 | O-proximal (not PC geometrically) |
| 5DW3 | A | 1.075 | −0.021 | 1.447 | 10.986 | O-proximal |
| 5DVZ | A | 1.067 | −0.018 | 1.324 | 11.032 | O-proximal |
| 4HPX | A | — | — | — | — | SKIP (24/112 resids missing on chain A; C-side reference, not PC anyway) |

**Healthy PC criteria (used in the scan):**
- s(R) ∈ [5, 10]
- |z(R)| < 1 Å²
- RMSD_to_O > 3 Å AND RMSD_to_C > 3 Å

**None of the three candidates satisfy any of these.** All three are
geometrically in the O cluster despite their Table S1 "βPC" labels.

## Interpretation

The biological/crystallographic PC label does NOT correspond to a
geometric midpoint in the 112-Cα PATHMSD subspace we use for the direct
O→C path.

5DW0 / 5DW3 have not "failed" — they are legitimate βPC structures.
What has failed is the design assumption that they land at s ≈ 8 when
forced into MODEL 8 of a 15-frame linearly-interpolated path. That
assumption is wrong: they land at s ≈ 1.07, essentially on top of O.

## Consequences for the pipeline

1. **Do not run PC-at-MODEL 8 + single-λ paths as MetaD pilots.** The
   walker response would be uninterpretable. This is audit-fail.

2. **Do not substitute 4HPX as the PC anchor.** 4HPX / 3CEP are C-side
   references (Q₂-like / closed); using them as PC pushes the problem
   from the O-side to the C-side without solving it.

3. **Do not expand scope to 4HPX- or 5DVZ-based paths without
   independently re-examining the argument.** The argument for rebuilding
   path geometry still stands, but a new PC anchor search is needed
   first.

## Next steps (not executed here)

- **Extended anchor scan** (PDBs not yet downloaded): 5VM5, 6AMH, 4HT3,
  2CLL, 5CGQ and any other Table S1 βPC-labeled structures. Run
  `scan_pc_anchors.py` against them to check if ANY βPC label lands near
  s ≈ 5–10.
- **If extended scan returns no candidate**: the load-bearing conclusion
  is *"βPC label in the literature does not equal geometric midpoint in
  our 112-Cα CV subspace"* — a substantive finding about path
  construction that should be written up before any further MetaD tuning.
- **Optional local O→PC diagnostic** (user-approved scope): 1–2 ns run
  with 1WDW→5DW3 as a standalone 8-frame path (λ=53.9 Å⁻²), Miguel DIFF
  fallback, loose or no wall. Answers *only* whether the walker can be
  pushed in a very local CV near the O basin — does NOT test O→C
  transition.

## Explicitly NOT in scope here

- Modifying the production `single_walker/path_gromacs.pdb` (unchanged).
- Changing LAMBDA on the current direct path (still 3.77 Å⁻², FP-022-settled).
- Switching away from the Miguel 2026-04-23 MetaD contract for the
  main production run (still on `miguel_2026-04-23/initial_single`).
- Rebuilding the direct path from scratch with different endpoint
  alignment or interpolation recipes (that is the FP-033 A/B/C plan;
  independent axis).
