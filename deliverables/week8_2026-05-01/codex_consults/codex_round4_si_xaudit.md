# Codex Round 4 — SI Cross-Audit of Week-8 A0 Patches (2026-04-25)

CCB task: `20260425-153216-837-17500`
Reviewer: Codex
Context: Cross-audit of PM-approved Week-8 plan's A0.1/A0.2/A0.3 SI-faithfulness patches before smoke test launch.

## Reply (verbatim)

> 1. **Widened TARGETS sanity**
>
>    `srun` awk count on `/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/initial_seqaligned/COLVAR`:
>
>    | window | target | s window | all frames | z<1.0 | z<1.5 | z<2.5 |
>    |---|---:|---|---:|---:|---:|---:|
>    | 0 | 1.000 | open-left | 14853 | 6958 | 10172 | 14360 |
>    | 1 | 2.324 | [1.662,2.987) | 16819 | 7256 | 10549 | 16093 |
>    | 2 | 3.649 | [2.987,4.311) | 16083 | 6914 | 10354 | 15499 |
>    | 3 | 4.973 | [4.311,5.636) | 15955 | 6199 | 9530 | 15276 |
>    | 4 | 6.298 | [5.636,6.960) | 15564 | 5227 | 8485 | 14741 |
>    | 5 | 7.622 | [6.960,8.284) | 12818 | 3406 | 6254 | 11999 |
>    | 6 | 8.947 | [8.284,9.609) | 10252 | 2268 | 4679 | 9518 |
>    | 7 | 10.271 | [9.609,10.933) | 7291 | 950 | 3025 | 6863 |
>    | 8 | 11.596 | [10.933,12.258) | 3040 | 161 | 837 | 2738 |
>    | 9 | 12.920 | [12.258,∞) | 477 | 2 | 35 | 417 |
>
>    Verdict: technically every window has ≥1 frame with `z<1.0`, but the last C-window is fragile: only 2 frames. Fallback should be tiered: first try `z<1.0`; if uniqueness/time-gap fails for the final window, relax only high-s windows to `z<1.5`; if still failing, extend pilot. Do not compress windows yet.
>
> 2. **λ change downstream**
>
>    I reprojected `metad.xtc` on compute node with `PATHMSD LAMBDA=80` vs `LAMBDA=100.79`, sampled every 50 xtc frames:
>
>    - `N = 46`
>    - mean `Δs = s_100.79 - s_80 = -0.0037`
>    - mean `|Δs| = 0.0158`
>    - median `|Δs| = 0.0132`
>    - p95 `|Δs| = 0.0403`
>    - max `|Δs| = 0.0535`
>    - max row: time 340 ps, `s80=1.2212`, `s100=1.1677`
>    - mean `Δz = 0.00143`, max `|Δz| = 0.00201`
>
>    Verdict: max `|Δs|=0.054 << 0.66`, so seed picks are not invalidated by λ=80→100.79. Reprojecting before final manifest is still cleaner, but not mandatory for window validity.
>
> 3. **Smoke-test risk after A0**
>
>    Predictable risks in `submit_v3_validation.sh` / materializer:
>
>    - Validation NVT is not 100 ps by default: `nvt_nsteps=1000` at 2 fs = 2 ps. That is fine for a short smoke, but it does not validate the real 100 ps settling premise.
>    - `grompp -maxwarn 1` is still too permissive.
>    - Shared HILLS path must be rechecked after materializer rewrite: if workers `cd walker_XX`, `WALKERS_DIR` must point to parent shared HILLS, not local.
>    - Existing script still allows `--write` without `--extract`, creating unlaunchable walker dirs without `start.gro`.
>    - It copies `path_seqaligned_gromacs.pdb` but must assert `REFERENCE=` in `plumed.dat` names that exact file.
>    - A0 seed widening creates a sparse last window; final high-s seed may be unusually rare. Add manifest fields for candidate count per window and z-threshold tier used.
>
> 4. **Track E priority**
>
>    Run parallel; do not block A2 smoke test. Docs cleanup does not change physics, and smoke output will help provenance. But block **production launch** until docs are cleaned enough that there is one live λ story: `λ=100.79 Å^-2 for current seq-aligned path`, with old `379.77 nm^-2 / 3.77 Å^-2` marked legacy and path-specific.
>
> 5. **Anti-overclaim labels**
>
>    Missing / corrections:
>
>    - `WHOLEMOLECULES ENTITY0=1-39268`: SI-silent, author/implementation-added, not SI-prescribed.
>    - `PRINT STRIDE=100 FMT=...`: SI-silent implementation/logging choice.
>    - `UNITS LENGTH=A ENERGY=kcal/mol`: SI-silent PLUMED implementation choice, though consistent with SI units.
>    - `GRID_MIN`, `GRID_MAX`, `GRID_BIN`: SI-silent; author-clarified if from Miguel email.
>    - `WALKERS_DIR`, `WALKERS_ID`, `WALKERS_N`, `WALKERS_RSTRIDE`: SI prescribes 10 replicas conceptually; PLUMED keywords/layout are implementation/author-clarified. `WALKERS_RSTRIDE=3000` is not SI.
>    - `SIGMA_MIN=0.1,0.01`: DEBATE_OPEN if labeled Miguel. The quoted Miguel block has `ADAPTIVE=DIFF SIGMA=1000` but not `SIGMA_MIN`; this should be labeled "our stabilization/PLUMED setting," not "author-clarified," unless there is another author source.
>    - `UPPER_WALLS`, `KAPPA=800`, `NEIGH_STRIDE=100`, `NEIGH_SIZE=6`, `ADAPTIVE=DIFF`, `SIGMA=1000`: SI-silent; author-clarified if directly from Miguel email.
>    - `TEMP=350`, `HEIGHT=0.15`, `PACE=1000` as 2 ps, `BIASFACTOR=10`, `10 replicas`: SI-supported values.

## Action items applied (2026-04-25)

| Codex R4 finding | Action |
|---|---|
| Q1 walker-9 z<1.0 fragile (2 frames) | Tiered z-fallback implemented in `select_seeds()`; manifest now logs `z_tier_used` + `candidates_at_strict_z` per walker |
| Q2 λ change safe (max \|Δs\|=0.054) | Proceeded with λ=80→100.79; existing seed picks re-validated under new λ |
| Q3 NVT 2 ps too short for 100-ps premise | OK for smoke (A2); production (A3) will use longer NVT |
| Q3 grompp -maxwarn 1 | Not yet tightened — TODO before A3 production launch |
| Q3 walker_XX cd → WALKERS_DIR=../HILLS_DIR | Already correct in patched plumed.dat (Codex misread; verified post-patch) |
| Q3 missing `REFERENCE=` assertion | Pre-existing assertion in materialize_v3_validation.py:248 ensures REFERENCE=path_seqaligned_gromacs.pdb literal |
| Q3 manifest sparse-window field | Added `z_tier_used_per_walker` + `candidates_at_strict_z_per_walker` |
| Q4 Track E parallel OK; block A3 not A2 | Track E completed (PARAMETER_PROVENANCE.md + JACS2019_MetaDynamics_Parameters.md SUPERSEDED markers) |
| Q5 SIGMA_MIN labeling — "our stabilization" | Updated plumed_template.dat header to label SIGMA_MIN as "our stabilization" not "author-clarified" |
| Q5 WHOLEMOLECULES, PRINT, UNITS, GRID_*, WALKERS_DIR/ID/N/RSTRIDE labels | Added to plumed_template.dat header anti-overclaim labels |
