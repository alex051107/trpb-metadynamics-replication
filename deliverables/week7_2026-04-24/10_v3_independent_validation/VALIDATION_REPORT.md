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

## Status

- 2026-04-24 first materialization with TARGETS=[1..10] integer + λ=80: ✅ documented (preserved in git history)
- 2026-04-25 SI-faithful re-materialization with widened TARGETS + λ=100.79: ✅ done, awaiting smoke test
- Smoke test launch: pending Codex Round 4 NVT/grompp recommendations + PM go-ahead
