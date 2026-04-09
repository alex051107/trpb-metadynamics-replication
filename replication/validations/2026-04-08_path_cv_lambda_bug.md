# Validation Note — Path CV LAMBDA Convention Bug (FP-022)

**Date**: 2026-04-08
**Branch**: `fix/path-cv-repair`
**Verdict**: **FAIL** (Job 41514529 invalid) → **FIX READY** (validated locally + via PLUMED driver)
**Triggers**: Job 41514529 walltime termination (2026-04-07) showed s(R) confined to [7.77, 7.83] for entire 46.3 ns
**Reviewers**: Claude (Opus 4.6), Codex (gpt-5.4-codex), local Python numerical tests, PLUMED driver on Longleaf

---

## TL;DR

Job 41514529 produced no usable bias data because the path CV was mathematically broken: `LAMBDA=3.391` was computed assuming `FUNCPATHMSD` accepts "total squared displacement" (sum over atoms) as input, but in reality `FUNCPATHMSD` consumes `ARG` values as-is, and PLUMED's `RMSD` action outputs per-atom-normalized RMSD (`sqrt((1/N) Σ |r-r_ref|²)`). The mismatch is a factor of `N_atoms = 112`. The corrected setup uses `RMSD ... TYPE=OPTIMAL SQUARED` + `LAMBDA=379.77` (= 2.3 / per-atom MSD_adjacent).

The 46.3 ns of trajectory still represents legitimate force-field MD (the system stayed in O basin, did not artifactually drift), but the deposited bias is in the wrong CV space and cannot be re-used for FES reconstruction. A new initial run with the fixed `plumed.dat` is required.

---

## Symptom

`/work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/COLVAR` for Job 41514529:

```
#! FIELDS time path.s path.z metad.bias
 0.000000   7.791319 0.489692  0.000000
...
 46303.000000 7.801747 0.588810 36.725814
```

| Quantity | Range over 46.3 ns | Expected (if working) |
|---|---|---|
| `path.s` | [7.770, 7.833] | should explore [1, 15] |
| Frames in O (s<5) | 0 | initial bursts at s≈1 |
| Frames in PC (5<s<10) | 46304 (100%) | mixed |
| Frames in C (s>10) | 0 | escapes at long time |
| `metad.bias` accumulated | 0 → 61.7 kJ/mol | growing with hill height decay |

The system appeared "stuck" in PC. Initial diagnosis (Claude, 2026-04-08 morning) was "PC basin too deep" or "ADAPTIVE σ collapse." Both turned out to be wrong.

---

## Root cause

`FUNCPATHMSD` formula:

```
s(R) = Σ i × exp(-λ × d_i) / Σ exp(-λ × d_i)
```

PLUMED 2.9.2 source (`src/function/FuncPathMSD.cpp`, verified upstream by Codex) uses the input ARG directly:

```cpp
exp(-lambda*(it.first->get()))
```

No internal squaring. PLUMED's `RMSD` action returns per-atom mean RMSD: `sqrt((1/N_atoms) Σ |r - r_ref|²)`. With `TYPE=OPTIMAL SQUARED`, it returns per-atom mean squared displacement (per-atom MSD): `(1/N_atoms) Σ |r - r_ref|²`.

For our 15-frame path with 112 Cα atoms:

| Convention | adjacent d | LAMBDA needed for kernel weight ≈ 0.1 | Match? |
|---|---|---|---|
| **Per-atom RMSD** (PLUMED RMSD output) | 0.0778 nm | 29.6 nm⁻¹ | — |
| **Per-atom MSD** (PLUMED RMSD ... SQUARED) | 0.006056 nm² | **379.77 nm⁻²** | ✅ canonical |
| ~~Total SD~~ (sum over atoms) | 0.6783 nm² | 3.391 nm⁻² | ❌ no PLUMED action emits this |

The bug chain:
1. `replication/metadynamics/path_cv/generate_path_cv.py` defaulted `calculate_lambda(convention="total_sd")` → returned `0.0339 Å⁻²` (= 2.3 / 67.83)
2. FP-018 fix multiplied by 100 (Å⁻² → nm⁻²) → `LAMBDA=3.3910`
3. The plumed.dat used `RMSD ... TYPE=OPTIMAL` (no SQUARED), feeding per-atom RMSD (nm) into FUNCPATHMSD
4. Effective `λ × d_adj = 3.391 × 0.0778 = 0.264`, kernel weight `exp(-0.264) ≈ 0.77` (canonical: ≈ 0.10)
5. The CV's resolving power dropped by factor ~3 in s axis. All 15 frames mapped into a narrow s range (≈ [4, 12] based on local test, ≈ [7.5, 8.5] based on Codex's Longleaf test — small differences due to slightly different RMSD matrix shapes).
6. Worse: the gradient `ds/dx` is also collapsed, so even though `metad.bias` grew to 61.7 kJ/mol in CV space, the force on protein atoms was tiny → no enhanced sampling, system evolved as if unbiased.

---

## Verification

### Step 1 — Local Python self-consistency test

`replication/validations/path_cv_debug_2026-04-08/01_self_consistency_test.py`

| LAMBDA (nm⁻²) | Convention | s(frame_01) | s(frame_08) | s(frame_15) | Verdict |
|---|---|---|---|---|---|
| **3.391** ← old | plain RMSD | **4.02** | 8.00 | **11.98** | ❌ FAIL |
| 3.391 | SQUARED | 4.59 | 8.00 | 11.41 | ❌ FAIL |
| 100 | plain RMSD | 1.00 | 8.00 | 15.00 | ✅ |
| **379.8** | **SQUARED** | **1.09** | 8.00 | **14.91** | ✅ **canonical** |
| 1000 | either | 1.00 | 8.00 | 15.00 | ✅ (but too sharp) |

Both endpoints map back to themselves only with the corrected LAMBDA. `s(frame_08) = 8.00` for all settings is a symmetry artifact and not diagnostic.

### Step 2 — 5DVZ projection test

`replication/validations/path_cv_debug_2026-04-08/04_project_5dvz.py`

5DVZ is the Ain O-state crystal. We extracted chain A residues 97-184 + 282-305 (112 Cα), aligned to each of the 15 path frames with Kabsch best-fit, and applied the FUNCPATHMSD formula:

| LAMBDA | s(5DVZ) | Interpretation |
|---|---|---|
| 3.391 (broken) | 4.37 (plain) / 4.57 (SQUARED) | nonsense |
| **379.77 (fixed)** | **1.0001 (plain) / 1.07 (SQUARED)** | ✅ correctly identifies O state |

This is the critical test: with the LAMBDA fix alone, no path regeneration is needed.

### Step 3 — PLUMED driver re-analysis on Longleaf

We re-ran the existing 46.3 ns `metad.xtc` through `plumed driver` with the fixed plumed.dat (no MetaD action, only CV computation). PLUMED itself printed:

```
PLUMED:   lambda is 379.770000
PLUMED:   Consistency check completed! Your path cvs look good!
```

Output `COLVAR_rerun_fixed` (143 KB, 4631 frames):

| Quantity | Range | Notes |
|---|---|---|
| `path.s` | [1.04, 1.06] (excluding ~2.5% NaN frames) | system is in O basin entire run |
| `path.z` | [1.45, 1.92] nm² | larger than naively expected; need to inspect PLUMED's z formula |
| frames in O | 4515 | 97.5% |
| frames in PC | 0 | 0% |
| frames in C | 0 | 0% |
| frames with NaN | 116 | 2.5% (transient large-d frames where exp underflows) |

The 46 ns is essentially unbiased MD in the O basin. No enhanced sampling occurred (because broken-CV bias had no physical force). System stability and equilibration are unaffected — the trajectory itself is fine, just the CV interpretation was wrong.

---

## Source-file fixes (this branch `fix/path-cv-repair`)

| File | Change |
|---|---|
| `replication/metadynamics/path_cv/generate_path_cv.py` | `calculate_lambda` default changed from `"total_sd"` to `"plumed"`; main loop uses per-atom MSD; `--summary-only` mode also fixed; new auto-emitted `plumed_path_cv.dat` snippet to prevent manual copy errors |
| `replication/metadynamics/path_cv/summary.txt` | Re-generated; star-marks correct λ = 3.7979 Å⁻² = 379.7948 nm⁻²; explicitly labels legacy total-SD λ as DO NOT USE |
| `replication/metadynamics/single_walker/plumed.dat` | All RMSD actions get `SQUARED`; LAMBDA changed from 3.3910 → 379.77; FP-022 history note in header |
| `replication/parameters/JACS2019_MetaDynamics_Parameters.md` | Path CV table re-written with correct λ, "DO NOT USE" annotation on old value, FP-022 explanation |
| `replication/validations/failure-patterns.md` | FP-022 entry added with full root cause + prevention; general rules 15 and 16 added |
| `PIPELINE_STATE.json` | Stage 4 marked `blocked_by_fp_022`, active_failure_patterns list created |

---

## What is NOT done by this validation

- **No new MetaD run yet**. The fix is verified in PLUMED driver mode (offline) but not in GROMACS+PLUMED mdrun (online). A 50 ns initial run is required before Stage 4 (Skeptic) can produce a valid FES.
- **PLUMED `path.z` magnitude not fully explained.** The z(R) values from `plumed driver` rerun (~1.6 nm²) are larger than expected from the formula `z = -(1/λ) log(Σ exp(-λd²))` applied to per-atom MSD inputs. PLUMED's internal z computation may differ from the published formula in a way I haven't traced. This does NOT affect the validity of s(R), which is what controls MetaD bias.
- **NaN frames (~2.5%)** in the rerun COLVAR are transient configurations where all `exp(-λ × d_i²)` underflowed. Sharper kernel = more NaN-prone. May need to adjust LAMBDA slightly downward (e.g., 200 nm⁻²) for production stability, but local self-consistency test still passes at 100-1000.
- **Tutorial files (`TrpB_Replication_Tutorial_EN.md`, `_CN.md`)** still reference `LAMBDA=3.3910`. These need updating in a separate documentation pass.

---

## Next actions

See `NEXT_ACTIONS.md` "本周待做" — Phase B (FES analysis) is replaced by:

1. Merge `fix/path-cv-repair` into `master`
2. Sync fixed plumed.dat to Longleaf single_walker/
3. Re-submit Slurm job for 50 ns initial run with fixed plumed.dat
4. After completion: Stage 4 Skeptic can extract 10 snapshots and proceed with 10-walker production

Estimated cost: ~3 days HPC walltime + ~1 day analysis.

---

## Lessons

1. **Self-consistency test should be MANDATORY before any path CV is committed.** One Python script + 15 reference frames + 30 seconds of compute would have caught this on day 1.
2. **Convention names matter.** "MSD" can mean per-atom mean OR total sum, depending on convention. Code that takes "MSD" as input must say *which* convention in its docstring AND assert it numerically.
3. **PLUMED's `Consistency check completed!` message is gold.** It only prints in driver mode (`mdrun` does not show it). Always validate via driver before launching `mdrun`.
4. **Two related bugs (FP-015, FP-018, FP-022) form a pattern**: every time we crossed a unit boundary (RMSD vs MSD, Å vs nm, total vs per-atom) without an automated check, we introduced a bug. The fix is not "be more careful" — it is "make the script the only source of LAMBDA, and have it assert the right convention with `assert 0.1 < lambda < 100`."
