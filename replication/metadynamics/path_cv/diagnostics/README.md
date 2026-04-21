# Path CV diagnostic suite (2026-04-21)

Four-step sequence to cut the current stall into **technical bug** vs **SI-faithful-but-weak path**, before any more production sampling.

**Order matters.** If step 1 or 2 fails, steps 3-4 are meaningless.

## Step 1 — Self-projection of the 15 reference frames
**Script:** `00_self_projection.sh` (run on Longleaf login node, < 5 s)
**Input:** production `path_gromacs.pdb`, production `LAMBDA=379.77`
**Output:** `ref_selfproj.dat` with `s, z` for each of the 15 MODELs

**What to look for (PM 2026-04-21 clarification):**
- `s` must be **monotonic** across frames 1→15
- Middle frames should be close to their integer index
- **Endpoints expected NOT to be exactly 1 and 15.** With neighbor MSD calibrated to `exp(-λ·MSD_neighbor) = 0.10` (by construction), frame 1 ≈ (1+0.1·2)/(1+0.1) ≈ **1.09**, frame 15 ≈ **14.91**. This is normal kernel-average behavior, not an anomaly.
- `z` should be small on every row (≲ 0.01 Å² in per-atom MSD units)

**Pass criteria**: monotonic s, middle frames near integers, endpoints ≈ 1.09 / 14.91, z small.
**Fail mode**: non-monotonic s, scrambled order, or large z → atom-order / MODEL-order / PBC / reference-file format bug. Fix that before anything else.

## Step 2 — PATHMSD vs FUNCPATHMSD equivalence check
**Script:** `01_pathmsd_vs_funcpathmsd.sh` (run on Longleaf, ~30 s)
**Input:** same `path_gromacs.pdb`, split into 15 single-frame PDBs; same `LAMBDA=379.77`
**Output:** `path_compare.dat` with four columns: `pp.sss, pp.zzz, pf.s, pf.z`

Rationale: FUNCPATHMSD is the explicit-RMSD reconstruction; PATHMSD is the built-in multi-frame action. If `(pp.sss, pp.zzz) ≠ (pf.s, pf.z)` on the same input, the two definitions of "distance" diverge → either atom-order mismatch in one of them, or the offline λ derivation used a different distance convention than what production consumes.

**Pass**: the two pairs agree within numerical noise (< 1% relative).
**Fail**: metric inconsistency → technical bug in atom mapping or λ derivation.

## Step 3 — O-endpoint local tangent alignment
**Script:** `02_o_endpoint_tangent.py` (Python, runs locally or on Longleaf)
**Input:** `path_gromacs.pdb` + early O-basin MetaD trajectory (e.g. probe_P1 `metad.xtc` first 2 ns)
**Output:** table of `cos(θ)` and `f_perp` per snapshot

Rationale (PM 2026-04-21): the PLUMED Belfast tutorial says path CV at endpoints can exhibit small force + small CV motion even when the system moves substantially in Cartesian space. This test confirms whether that's what's happening here.

For each early snapshot `x_t`:
- Reference: `x_0` = frame 1 of path_gromacs.pdb (Kabsch-aligned on 112 Cα)
- Local tangent: `t_O = (x_2 - x_1) + 0.5·(x_3 - x_1)` (smoothed chord direction at O)
- `Δx_t = x_t - x_0`
- `cos(θ) = (Δx_t · t_O) / (‖Δx_t‖·‖t_O‖)`
- `f_perp = ‖Δx_t − proj_{t_O}(Δx_t)‖ / ‖Δx_t‖`

**Interpretation**:
- High `‖Δx_t‖`, low `cos(θ)`, high `f_perp`, s stuck ~1 → real motion exists but is perpendicular to the linear chord → path geometry is the problem.
- Low `‖Δx_t‖` → walker genuinely not moving → different problem (thermostat, equilibration).
- High `cos(θ)` + s stuck ~1 → motion aligned with tangent but not reflected in s → PATHMSD-specific issue, not a geometry issue.

## Step 4 — P5 5 ns falsification
Already wired into the cron monitor. When P5 reaches 5 ns, the next tick's `status.md` automatically includes its saturation stats. No separate script.

## After all 4 land

| Outcome | Conclusion |
|---|---|
| Step 1 fails | Technical: reference file / atom order / PBC bug. Fix that. |
| Step 1 OK, Step 2 fails | Technical: metric inconsistency. Fix λ derivation or atom mapping. |
| Steps 1+2 OK, Step 3 shows low cos(θ) | Path geometry: linear Cartesian chord at O endpoint is scientifically weak. Minimal-disruption fix = piecewise path with experimental anchors (1WDW → 5DW0/5DW3 → 3CEP or 4HPX), same PATHMSD machinery, same λ rule. Explicitly label as "SI-minimal-deviation extension", not replication. |
| Steps 1+2+3 OK, Step 4 shows P5 still floor-bound | SIGMA_MIN/MAX axis empirically exhausted. Document and escalate to PI. |
