# Codex Round 0 — Clean-Context SI Re-Read (2026-04-25)

CCB task: `20260425-145238-191-53774`
Reviewer: Codex
Context: Clean — no prior conversation, no artifacts, no audits. Treats PM_BRIEF / INTERFACE_DESIGN / PR_FAQ / RED_TEAM_ATTACK / Round 1 / Round 2 as nonexistent.
Authoritative source consulted: `papers/ja9b03646_si_001.pdf` directly.

## Reply (verbatim)

> 1. **SI literal protocol**
>
>    - (a) Walker count: SI p. S3–S4, "Well-tempered Metadynamics simulations with Path Collective Variables": quote: "10 replicas." Literal: production was 10-walker MetaD.
>    - (b) Production duration per walker: same section, quote: "50 – 100 ns." Literal: each walker replica ran 50–100 ns, total 500–1000 ns/system.
>    - (c) Convergence/FES gate: same section: quote: "energy difference." Literal: convergence was evaluated by monitoring energy differences between selected local-minimum regions over simulation time, shown in Fig. S4/S5. No numeric PASS/FAIL threshold.
>    - (d) λ value: SI p. S3: quote: "80." Literal text says λ was computed from 2.3 divided by mean square displacement between successive frames, giving 80.
>    - (e) Biasfactor: SI p. S3: quote: "bias factor of 10."
>    - (f) Hill height: SI p. S3: quote: "height 0.15 kcal mol-1."
>    - (g) Hill deposition rate: SI p. S3: quote: "deposited every 2 ps."
>    - (h) Implementation choice: SI says PLUMED2 + GROMACS 5.1.2 and "path CVs"; it does **not** name `PATHMSD`, `FUNCPATHMSD`, `NEIGH_STRIDE`, `WALKERS_RSTRIDE`, grid, or upper wall. Mark implementation choice as **SILENT**.
>
> 2. **Parameter audit**
>
> | Item | SI says | I run | DELTA |
> |---|---|---|---|
> | Walker count | 10 replicas | v1/v2/v3 scaffold uses 10; pilot is 1 | DOCUMENTED for pilot; OK for production |
> | Duration/walker | 50–100 ns/walker | pilot ~22 ns single; v2 crashed; v3 not smoke-tested | MAJOR if called production |
> | Convergence | ΔG between FEL regions over time, no numeric cutoff | no completed 10-walker FES gate yet | MAJOR gap |
> | λ | literal SI value 80 | current FP-034 seq-aligned pilot uses λ=80; older parameter docs also contain 3.77/379.77 lineage | DEBATE_OPEN: repo provenance contradicts itself |
> | Biasfactor | 10 | current stated primary BF=10; older fallback docs mention 15 | OK for primary; MAJOR if fallback presented as SI |
> | Height | 0.15 kcal/mol | current primary 0.15; fallback docs mention 0.3 | OK for primary; MAJOR if fallback presented as SI |
> | Deposition | every 2 ps | `PACE=1000` at 2 fs = 2 ps; one v3 comment says `PACE=500` | MINOR doc bug if comment only; MAJOR if actual plumed uses 500 |
> | Adaptive width | adaptive Gaussian width scheme; no exact PLUMED keyword | `ADAPTIVE=DIFF SIGMA=1000` from Miguel email | DOCUMENTED; SI silent on DIFF vs GEOM |
> | PATHMSD/FUNCPATHMSD | SILENT | `PATHMSD` | DOCUMENTED implementation choice |
> | Upper wall | SILENT | `UPPER_WALLS z=2.5` | DOCUMENTED non-SI stabilizer |
> | Grid/binning | SILENT | grid choices in PLUMED/sum_hills | DOCUMENTED engineering |
>
> 3. The SI describes one workflow: equilibrated structures → initial MetaD run → extract 10 snapshots covering conformational space → 10-walker production. It does **not** describe a long single-walker pilot as a publishable stage. Your 22 ns pilot is methodologically acceptable only as a preparatory/diagnostic analog of the SI "initial metadynamics run," not as SI production and not as FES evidence.
>
> 4. Your 10-walker scaffolding matches the SI at the highest level only if it becomes: 10 walkers, CV-diverse starts from an initial MetaD run, 50–100 ns per walker, summed HILLS, convergence by ΔG-region stability. It does **not** yet match because v1 was homogeneous start, v2 crashed, and v3 is not smoke-tested. "Ship 10-walker production" is the right next move only after v3 fixes seed diversity, EM/NVT settling, shared-HILLS path, and stale-file hygiene. A single longer walker is less SI-faithful than a fixed 10-walker production.
>
> 5. Verdict: the project is directionally on track but has quiet drift reviewers could catch.
>
>    The main drift is treating the single-walker pilot as if it carries production-level interpretive weight. SI evidence: p. S3–S4 requires 10 replicas × 50–100 ns and convergence by FEL-region energy differences. Your pilot is only a seed-discovery/diagnostic run.
>
>    The second drift is parameter-provenance confusion. `JACS2019_MetaDynamics_Parameters.md` and `PARAMETER_PROVENANCE.md` preserve older λ=3.77/379.77 logic, while the current FP-034 path uses λ=80. That must be cleaned or future reviewers will see an unresolved parameter fork.
>
>    The third drift is non-SI engineering additions: `UPPER_WALLS`, `NEIGH_STRIDE`, `WALKERS_RSTRIDE`, grid bins, and `ADAPTIVE=DIFF` are not SI-literal. They may be justified by Miguel/email and modern PLUMED, but must be labeled "author-clarified / implementation choice," not "SI says."

## Notes / corrections from later rounds

- Q1(d): Codex R0 wrote "literal SI value 80" — Round 0.5 + R4 refined this to: SI's "80" is path-specific instance of the Branduardi formula λ = 2.3/⟨MSD_adj⟩; the formula itself is the SI prescription. On our seq-aligned path the formula gives λ = 100.79.
- Q2 PACE row: Codex R0 worried about a "v3 comment says PACE=500" — verified non-existent; current production template uses PACE=1000.
- Q2 LAMBDA row: "DEBATE_OPEN" — resolved 2026-04-25 in PARAMETER_PROVENANCE.md by marking legacy 379.77 nm⁻² and Miguel literal 80 both SUPERSEDED → 100.79 Å⁻² active.
