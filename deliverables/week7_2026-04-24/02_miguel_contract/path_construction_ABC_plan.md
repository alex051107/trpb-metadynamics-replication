# Path-construction A/B/C comparison plan (2026-04-23)

## Motivation

PM correction (2026-04-23) to the λ audit: "alignment" conflates two operations. `PATHMSD` internally handles **runtime alignment** (optimal Kabsch of the current frame against each reference at every MD step) — this is settled; manual pre-rotation of the trajectory does not change the runtime MSD metric. But **path-construction alignment** — how the 15 reference frames themselves were built before being written to `path.pdb` — is NOT controlled by PLUMED and IS a candidate for the λ discrepancy axis. The SI says only "15 conformations, linear interpolation between the X-ray available data" and does not pin down endpoint-alignment subset, interpolation convention, or intermediate-crystal interposition.

Until we reconstruct Miguel's actual 2019 PATH.pdb construction recipe, λ and path-density are entangled: our λ=3.77 is self-consistent with our path, his λ=80 is plausibly self-consistent with his — neither can judge the other directly.

This plan separates the two variables into three orthogonal sub-experiments.

## Ground rules

- **Production untouched.** `replication/metadynamics/miguel_2026-04-23/path_gromacs.pdb`, `plumed_template.dat`, `single_walker/plumed.dat`, and the running 10-walker job (45322604) remain on our current path + λ=3.77. All A/B/C work lives in a new `replication/metadynamics/path_construction_ABC/` tree.
- **Diagnostic only.** No artifact from A/B/C becomes a production path until PM explicitly promotes it.
- **Scriptized numerics.** Every ⟨MSD_adj⟩, λ, and CV in the output must come from a script with assertions (FP-015 rule).

## A. Fix path, vary λ (isolates λ effect)

**Variables held constant:** current `path_gromacs.pdb` (112 Cα, 15 frames, 1WDW→3CEP linear interp).

**Variables swept:** LAMBDA ∈ {3.77, 10, 30, 80} Å⁻².

**Outputs per λ:**
1. `plumed driver` self-projection of the 15 reference frames through `PATHMSD LAMBDA=λ` — produce `self_proj_lambda_{λ}.dat` with (frame_idx, s, z).
2. `plumed driver` projection of a short external trajectory (first 2 ns of the 45322604 walker_00 trajectory, sampled every 10 ps) onto PATHMSD with this λ — produce `traj_proj_lambda_{λ}.dat`.

**Metrics reported:**
- Self-projection monotonicity (Spearman ρ of s vs frame index; expect ~1.0).
- Neighbor-weight ratio w₂/w₁ = exp(−λ·⟨MSD_adj⟩): target ~0.1 (Branduardi heuristic). Report per λ.
- Short-trajectory s dynamic range — does s still vary smoothly, or does it integer-snap?

**Interpretation:** A confirms the claim "λ=80 is over-sharp on our path" by showing the kernel-collapse transition as λ scans upward. Does NOT test whether 80 is correct on a different path — that's B.

## B. Fix λ formula, vary path-construction recipe (isolates path-construction alignment)

**Variables held constant:** Branduardi formula λ = 2.3 / ⟨MSD_adj⟩ is applied to each resulting path independently; 112 Cα atom selection.

**Variables swept — four path-construction variants:**

| Variant | Endpoint alignment | Interpolation | Intermediate crystals interposed |
|---|---|---|---|
| B1 | None (use raw 1WDW chain A + raw 3CEP chain A, no pre-rotation) | Linear 2-point (14 interior steps) | — |
| B2 | Kabsch on 112 Cα subset (this is our current recipe) | Linear 2-point | — |
| B3 | Kabsch on full protein (residues 1–388) | Linear 2-point | — |
| B4 | Kabsch on 112 Cα subset | Piecewise linear through 5DVZ(1)→5DW0(2)→5DW3(3)→3CEP(4)→4HPX(5) | 5DVZ, 5DW0, 5DW3, 4HPX |

**Outputs per variant:**
- `path_v{N}.pdb` — 15-frame, 112 Cα, MODEL 1..15 ordering.
- `neighbor_msd_v{N}.csv` — 14 rows: MSD(i, i+1) per-atom mass-weighted, Kabsch-aligned.
- `lambda_v{N}.txt` — one number: λ = 2.3 / mean(neighbor_msd).
- `self_proj_v{N}.dat` — 15 rows of (frame_idx, s, z) at this λ.

**Interpretation:** B tells us how much the path-construction recipe moves ⟨MSD_adj⟩ and therefore λ. If B1/B3/B4 land near 80, we've located the axis. If they all stay in the 1–10 Å⁻² band, then Miguel's 80 is NOT explained by these recipe choices and a different hypothesis is needed (e.g., different atom selection, chain B, or he truncated to a smaller residue set).

## C. Per-path health metrics (Belfast tutorial's diagnostic set)

Applied to every path from A (just the one) and B (four variants). All diagnostics are plotted/tabulated, not gated pass/fail.

| Metric | Definition | Healthy range |
|---|---|---|
| mean_neighbor_msd | mean of MSD(i, i+1), i=1..14 | no fixed target — reports the density |
| neighbor_msd_cv | std/mean of neighbor MSD | ≤ 0.15 (Belfast tutorial: neighbor distances should be roughly equal) |
| s_range_monotonic | Spearman ρ of self-projected s vs frame index | > 0.98 |
| s_span | (max s − min s) from self-projection | ≈ 14 if path spans full 1→15 range |
| z_self | max|z| across 15 self-projected frames | small (kernel-average boundary effect only) |
| crystal_projections | s value for each of {5DVZ, 5DW0, 5DW3, 4HPX, 3CEP} projected onto this path | should land at roughly monotonic s values, consistent with their known O→C conformational ordering |

Output: one summary table `health_summary.csv` with one row per path variant and one column per metric, plus a matplotlib plot of neighbor-MSD vs index for each variant.

## Dispatch contract to Codex (when approved)

- Base dir: `replication/metadynamics/path_construction_ABC/` (new).
- Tools: `plumed driver`, `scripts/generate_path_cv.py` (existing, extend), `mdtraj` or `MDAnalysis` for Kabsch, `numpy`.
- Inputs: `structures/1WDW_chainA.pdb`, `3CEP_chainA.pdb`, `5DVZ_chainA.pdb`, `5DW0_chainA.pdb`, `5DW3_chainA.pdb`, `4HPX_chainA.pdb` (all exist in `structures/`).
- No SLURM jobs needed — `plumed driver` self-projection is ~seconds per path.
- Deliverable: `path_construction_ABC/SUMMARY.md` with the health table + interpretation pointing to whether path-construction recipe explains the 3.77↔80 gap.
- Stop condition: if B4 (intermediate-crystals interposed) lands λ near 80, escalate to PM before doing anything else — that would be the load-bearing evidence for a recipe swap.

## What this plan does NOT do

- Does not scancel or modify running job 45322604 (λ=3.77 on current path is its own self-consistent run, endorsed by PM as "current path's correct λ").
- Does not change the Miguel production contract (UNITS, ADAPTIVE=DIFF, HEIGHT=0.15, BIASFACTOR=10, 10 walkers).
- Does not touch `path_gromacs.pdb` or anything in `single_walker/`.
- Does not attempt to rebuild Miguel's PATH.pdb from scratch (no ground truth to compare against); instead, surveys the recipe space to see which variants land near ⟨MSD⟩ ≈ 0.029 Å² (λ≈80).

## Open question that A/B/C cannot answer

If none of B1–B4 land near λ=80, path-construction alignment is exonerated and the actual axis shifts to one of: atom selection (different Cα subset), chain (B vs A), residue-range truncation, or he used a different pair of endpoint crystals. At that point the honest next step is to email Miguel for his path-construction script/recipe.
