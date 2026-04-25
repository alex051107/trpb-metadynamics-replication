# v3 Independent 10-Walker Validation Report (2026-04-25 SI-Faithful Patch)

Date: 2026-04-24 (initial), **2026-04-25 (re-materialized after Codex R0/R0.5/R4 SI cross-audit)**

Remote directory:

```text
/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_v3_validation
```

## 2026-04-25 Patch Summary (SI-Faithful)

Three Week-8 A0 patches applied (per `deliverables/week7_2026-04-24/11_ml_layer/PM_BRIEF` + `clever-tickling-sparrow.md` plan):

1. **λ corrected** from Miguel email's literal 80 → **100.79 Å⁻²** (Branduardi `2.3/⟨MSD_adj⟩` self-computed on our seq-aligned path; Codex R4 verified max \|Δs(λ=80→100.79)\| = 0.054 ≪ window-half 0.66, so existing seed picks remain valid).
2. **TARGETS widened** from `tuple(range(1, 11))` (legacy [1..10] integer truncation) → `numpy.linspace(1.0, max_s_observed, 10)`. With pilot at 22.8 ns / max_s=13.90, TARGETS = [1.00, 2.43, 3.87, 5.30, 6.73, 8.17, 9.60, 11.04, 12.47, 13.90]. Covers full path including C-region (s≥10) per SI quote (Codex R0.5) "extracted ten snapshots covering conformational space" + PM directive "cover 足够广".
3. **Tiered z-fallback** added (Codex R4): try z<1.0 first, then 1.5, 2.0, 2.45 — only for windows where strict z fails uniqueness/time-gap.

## Seed Set (post-patch)

```text
walker_id target_s   time_ps        s        z   z_tier  strict_candidates
00          1.0000   14073.2   1.4402   0.2152    1.00    7308
01          2.4337   17889.8   3.1445   0.1869    1.00    7783
02          3.8673   14748.4   4.0954   0.2095    1.00    7330
03          5.3010   17765.6   5.4179   0.1899    1.00    6577
04          6.7347   14967.2   6.1878   0.1888    1.00    4915
05          8.1683   19601.6   7.6422   0.2651    1.00    3367
06          9.6020   12972.0   9.0238   0.3447    1.00    1715
07         11.0357   12770.8  10.4928   0.5901    1.00     450
08         12.4693   10733.4  11.8264   0.8160    1.00      22
09         13.9030   22460.2  13.2854   2.0058    2.45       0
```

Assertions (post-patch):

```text
s_std = 3.6909  (legacy was 2.7593 — wider coverage)
min_pairwise_s_gap = 0.7699  (legacy was 0.4180)
unique_start_hashes = 10 / 10
ASSERTIONS_PASS
```

State coverage check (NEW gate per A0.2 implementation):
- O-region (s ≤ 2): walker_00 ✓
- PC-region (4 ≤ s ≤ 6): walkers 02, 03 ✓
- C-region (s ≥ 10): walkers 07, 08, 09 ✓

## Walker 09 Caveat (z=2.00, tier=2.45)

C-region of pilot has very few low-z frames; window 9 ([13.24, ∞)) had 0 candidates at z<1.0 even after pilot extended to 22.8 ns. Tiered fallback engaged: z<1.5 (35 frames), z<2.0 (still failed min_s_gap), z<2.45 (1 valid frame at z=2.00). Walker 09 starts close to UPPER_WALLS AT=2.5, but:
- NVT pre-equilibration (PLUMED off, gen_vel=yes, 100 ps) is expected to relax z before MetaD wall takes effect.
- If smoke test shows walker_09 NVT immediately violating UPPER_WALLS, fallback action: extend pilot to 25-30 ns to give more high-s low-z frames (Codex R4 recommendation), then re-materialize.

## Handoff Logic

Each walker has:

```text
start.gro   -> em.mdp    -> em.tpr
em.gro      -> nvt.mdp   -> nvt.tpr   # PLUMED off, gen_vel=yes
nvt.gro+cpt -> metad.mdp -> metad.tpr # PLUMED on, continuation=yes, gen_vel=no
```

plumed.dat per walker contains: `LAMBDA=100.79, ADAPTIVE=DIFF, SIGMA=1000, HEIGHT=0.15, BIASFACTOR=10.0, WALKERS_N=10` (full SI-literal MetaD primary contract).

This bundle tests the SI-literal "10 replicas" production protocol without reusing v2's unsafe direct-production launch.

## Codex Audit Chain

- **Round 0** (CCB `20260425-145238`): clean-context SI re-read identified 3 drifts — λ provenance fork, pilot-as-production overclaim, non-SI engineering labels missing.
- **Round 0.5** (CCB `20260425-150747`): SI literal protocol verbatim — 10 walkers from CV-diverse seeds extracted from initial MetaD; path-CV reference path NOT rebuilt; Fig S4/S5 = ΔΔG-vs-time convergence test.
- **Round 4** (CCB `20260425-153216`): cross-audit of A0 patches — confirmed λ change safe, widened windows all populated (window 9 fragile), 3 additional v3 hardening recommendations (NVT 2 ps too short for 100 ps validation, grompp -maxwarn 1 too permissive, walker 9 high-z manifest field).

Transcripts archived in `deliverables/week8_2026-05-01/codex_consults/`.

## Remaining Action

```bash
cd /work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/seqaligned_walkers_v3_validation
sbatch submit_v3_validation.sh
```

This launches the smoke test (10-way array, 30 min wall, partition `volta-gpu`, EM 1000 + NVT 1000 + MetaD 1000 steps). PASS gates per Week-8 plan A2:

1. EM completes with `Maximum force < 1e4 kJ/mol/nm` and no NaN.
2. NVT completes 100 ps without LINCS warning on atoms 4463-4465 (v2 crash signature).
3. MetaD step phase produces COLVAR with `metad.bias > 0` for ALL rows.
4. No exit code 139 on any walker.

If any gate fails: STOP, post failure pattern as FP-035 candidate, do NOT proceed to production launch.

## 2026-04-25 Codex Round 8 Addendum — window-min-z (PM v2)

**PM directive after Codex R7 figures**: "选择尽可能广的 SR + 每一个 sr 选一个相对 Z 比较小的".

Codex R8 verdict (transcript: `deliverables/week8_2026-05-01/codex_consults/codex_round8_seed_strategy_and_si_hills.md`):

1. **Seed strategy**: window-min-z (no ceiling) is conceptually cleaner than tiered-z fallback. Lowest-z is a *geometry-stability heuristic* (less off-path/wall stress), NOT proof of equilibrium. Hard cap `seed.z < 2.5` retained to reject upper-wall starts.

2. **Equivalence**: on local 19.8 ns pilot COLVAR (max_s=12.917), the window-min-z rule produces seeds byte-identical to v1 tiered output:

```text
walker_id target_s   time_ps        s        z   rule              candidates_in_window
00          1.0000   14073.2   1.4400   0.2150   window_min_z      14180
01          2.3241   17892.8   2.7180   0.2010   window_min_z      15810
02          3.6481   14756.4   3.7660   0.1940   window_min_z      15487
03          4.9722   17765.6   5.4180   0.1900   window_min_z      14704
04          6.2963   14967.2   6.1880   0.1890   window_min_z      13141
05          7.6203   14306.4   7.0440   0.2250   window_min_z      10105
06          8.9444   12972.0   9.0240   0.3450   window_min_z      7612
07         10.2685   13146.8   9.7160   0.5100   window_min_z      5702
08         11.5925   12782.0  10.9640   0.6240   window_min_z      2291
09         12.9166   11553.4  12.3460   0.9760   window_min_z      116
```

s_std=3.4417, min_pairwise_s=0.6926, z_range=[0.189, 0.976].

3. **Production decision**: **DO NOT scancel 45784112**. Current production seeds (from Longleaf 22.8 ns pilot with TARGETS=[1.00..13.90]) are functionally equivalent to v2 — wide linspace + low-z priority — and live walkers already span s∈[1.0, 10.7] by 0.3 ns/walker. Restart only if persistent collapse, LINCS instability, or no C-region retention emerges after several ns/walker.

4. **Code patch applied**: `materialize_v3_validation.py:select_seeds()` rewritten:
   - `Z_TIERS = (1.0, 1.5, 2.0, 2.45)` removed.
   - Candidates = all rows in `[lo, hi)` with NO z ceiling.
   - Sort by `(z, abs(s-target), time)` (unchanged).
   - `Seed.z_tier_used` field renamed to `Seed.selection_rule="window_min_z"`.
   - `Seed.candidates_at_strict_z` renamed to `Seed.candidates_in_window`.
   - `Z_HARD_CAP = 2.5` constant; `assert_seed_suite()` rejects any seed at/beyond UPPER_WALLS.
   - Manifest TSV columns: `walker_id  target_s  time_ps  s  z  rule  candidates_in_window`.

5. **Walker 09 caveat retained**: under window-min-z, current Longleaf production seed for walker_09 (max_s=13.90 → window [13.18, ∞)) still picks z=2.00 because no lower-z C-region frames exist in pilot. This is a *pilot under-sampling* issue, not a *selection-rule* issue. Mitigation: extend pilot to 30 ns post-deck (Codex R4 fallback) and re-materialize.

## Status

- 2026-04-24 first materialization with TARGETS=[1..10] integer + λ=80: ✅ documented (preserved in git history)
- 2026-04-25 SI-faithful re-materialization with widened TARGETS + λ=100.79 + tiered-z: ✅ done, smoke test PASS
- 2026-04-25 PM v2 + Codex R8 cleanup (window-min-z, no ceiling): ✅ patched in materialize_v3_validation.py — equivalent seeds on current pilot, no rerun needed
- Smoke test (45783311): ✅ PASS (10/10 walkers, 24 min wall, no LINCS, no exit-139)
- Production launch (45784112): ✅ RUNNING since 16:06:22 — at 0.3 ns/walker, all 10 walkers active
