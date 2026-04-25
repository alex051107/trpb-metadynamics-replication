# Codex Round 8 — SI HILLS construction + PM seed strategy v2 (2026-04-25)

CCB task: dispatched 16:45 local; reply 16:48 (≈3 min).
Reviewer: Codex (clean context, with local SI PDF + pilot COLVAR access)
Context: PM saw Codex R7 early production figure, asked two questions:
  (Q1) Does SI build production FES from initial+production HILLS or production-only?
  (Q2) Is "max-spread s + window-min-z" (PM v2) more defensible than current v1 tiered-z, and should we scancel 45784112 to relaunch with v2?

## Q1 — SI quote on production FES HILLS construction

**Verdict: ONLY 10-walker production HILLS. Do NOT combine initial-pilot HILLS.**

SI p.S3-S4 verbatim (via Codex local PDF extraction):
> "The free energy landscape associated with the metadynamics CVs is estimated by summing the Gaussian potentials deposited by all walker replicas as a function of the CVs values."

Immediately after:
> "After an initial metadynamics run, we extracted ten snapshots for each system covering approximately all the conformational space available. Then, multiple-walkers metadynamics simulations with 10 replicas were computed."

The SI is SILENT on the explicit sentence "we discarded initial HILLS," but the described construction is (A), not (B). Initial MetaD is a seed-discovery stage; production FEL is from Gaussians deposited by the 10 walker replicas.

**Project-specific implication**: mixing initial fallback contract HILLS (`HEIGHT=0.3 / BIASFACTOR=15`) with production primary contract HILLS (`0.15 / 10`) violates the WT-MetaD theorem that requires a single biasfactor. Not defensible regardless of SI silence on explicit discard.

## Q2a — Is PM's "window-min-z" more defensible than v1 tiered-z?

**Directionally yes, but with a precise caveat.**

Lowest z is NOT the same thing as thermodynamic equilibration. It means "closest to the supplied path at that s," hence less off-path/wall stress and better as a seed. It can still select a transient low-z crossing.

**Better wording**: lowest-z is a geometry-stability heuristic, not an equilibrium proof.

## Q2b — Should we scancel 45784112 and relaunch with v2 seeds?

**Verdict: DO NOT scancel based on seed strategy alone.**

Codex independently recomputed the seeds from pilot COLVAR using both v1 (tiered) and v2 (window-min-z, no ceiling). Result: **seeds are identical** because every window already has low-z candidates:

```
target_s: 1.00, 2.32, 3.65, 4.97, 6.30, 7.62, 8.94, 10.27, 11.59, 12.92
selected s: 1.440, 2.718, 3.766, 5.418, 6.188, 7.044, 9.024, 9.716, 10.964, 12.346
selected z: 0.215, 0.201, 0.194, 0.190, 0.189, 0.225, 0.345, 0.510, 0.624, 0.976 (Å²)
s_std=3.442
min_s_gap=0.693
z_range=0.189–0.976 Å²
```

The current production seed logic is already essentially PM-v2 for this data: wide `linspace(min_s, max_s, 10)` plus low-z priority. The live run also already spans `s≈1.0–10.7` by ~0.3 ns/walker.

**Restart only if** later diagnostics show persistent collapse, LINCS instability, or no C-region retention after several ns/walker.

## Q2c — Minimum diff to select_seeds() for conceptual cleanliness

If patching:
1. Do NOT merely delete `Z_TIERS` blindly.
2. Build candidates as all rows in `[lo, hi)` with NO `z <= tier` ceiling.
3. Sort by `(z, abs(s-target), time)` — same as before.
4. Keep uniqueness/time-gap checks.
5. Keep hard assertions: unique times, unique rounded s, `s_std >= 3.0`, O/PC/C coverage, `seed.z < 2.5` (avoids upper-wall starts).
6. Rename `z_tier_used` field → `selection_rule="window_min_z"`.

Patch applied to `deliverables/week7_2026-04-24/10_v3_independent_validation/materialize_v3_validation.py` 2026-04-25 post-R8.

## Decision summary

| Question | Verdict | Action |
|---|---|---|
| Q1 SI HILLS | Production-only | TechDoc + plot_production_fes use HILLS.0..9 only |
| Q2a v2 strategy | Yes, with "geometry-stability" caveat (not equilibrium proof) | Rename field, document caveat |
| Q2b Scancel? | No | Continue 45784112; HILLS already match v2 |
| Q2c Patch? | Yes for cleanliness | Drop tier filter, rename, keep assertions |

## Artifacts

- This transcript: `deliverables/week8_2026-05-01/codex_consults/codex_round8_seed_strategy_and_si_hills.md`
- Original prompt: `/tmp/codex_round8_seed_strategy.md` (archived inline below for git-traceability)
- Updated materializer: `deliverables/week7_2026-04-24/10_v3_independent_validation/materialize_v3_validation.py`
- Production job state: 45784112 RUNNING (not cancelled)

---

## Original prompt (archive)

```
[CONSULT - SI re-read: production FES 是否合并 initial MetaD HILLS? + seed selection 策略 v2]

Q1 — SI 的 production FES 是合并 initial+10walkers 还是只 10 walkers?
Q2 — Validate PM seed strategy v2 (max-spread s + window-min-z, no ceiling)
```
