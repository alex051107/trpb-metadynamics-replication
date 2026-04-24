# 02 · Miguel parameter contract

The first author of the original JACS 2019 paper — Dr Miguel Maria-Solano — replied to our parameter-request email on 2026-04-23 with a verbatim PLUMED parameter block. This subdirectory preserves that contract and the memos that locked it into our pipeline.

## Files

| File | What it is | When you consult it |
|---|---|---|
| `miguel_email.md` | Full text of Miguel's reply. Source of truth for every MetaD parameter. | First file to open when challenged on any parameter choice. |
| `plumed_template.dat` | Our parsed version of the contract, ready for `__WALKERS_ID__` substitution at materialization time. | Every `plumed.dat` in production is built from this template. |
| `lambda_audit_2026-04-23.md` | Cross-model audit of λ (Codex + me) after the email came in. Explains why λ must be per-path self-consistent, not universal, and why Miguel's 80 is in the same regime as our 100.79. | When justifying why we did not simply copy λ=80. |
| `path_construction_ABC_plan.md` | Memo written before we knew about FP-034, outlining three path-construction hypotheses (A = naive, B = piecewise, C = linear interp with sequence alignment). C won after FP-034 surfaced. | Historical context for why the NW path was chosen. |

## Key contract terms

```
UNITS         LENGTH=A  ENERGY=kcal/mol          # NOT nm / kJ   (fixes FP-032)
METAD ARG=path.sss  PACE=500                     # MULTIPLE_WALKERS protocol
  HEIGHT         0.15 kcal/mol                   # primary       (0.3 = aggressive fallback)
  BIASFACTOR     10                              # primary       (15  = aggressive fallback)
  SIGMA          ADAPTIVE=DIFF                   # NOT GEOM      (fixes FP-031)
  WALKERS_N      10                              # shared HILLS, 10 walkers
  TEMP           350
  LAMBDA         80  (A^-2)                      # self-consistent on HIS path
UPPER_WALLS ARG=path.zzz  AT=2.5  KAPPA=500
```

## Why this is the single most important external input of the week

Three weeks of internal parameter debates (probe_sweep HEIGHT/BIASFACTOR 2×2, wall4 AT-scan, piecewise-λ design) were all stalled on the absence of an authoritative reference. Miguel's email terminated these debates. Every subsequent choice in this package ultimately flows from the four corrections below:

1. **ADAPTIVE = DIFF, not GEOM** — GEOM projects σ onto the chord direction, which is ill-defined at path endpoints (PLUMED documentation). DIFF estimates σ directly from consecutive-step CV differences and is endpoint-stable. Closes FP-031.
2. **UNITS = A / kcal, not nm / kJ** — Miguel's SIGMA literals (0.1, 0.3, 0.005) are Å/kcal. Running with GROMACS native nm/kJ yields an effective σ off by a unit-conversion factor. Closes FP-032.
3. **`HEIGHT = 0.15 kcal/mol, BIASFACTOR = 10, WALKERS_N = 10` is the primary set.** The alternate `HEIGHT = 0.3, BIASFACTOR = 15` is an *aggressive fallback* only, to be used if primary fails to converge.
4. **`λ = 80 Å⁻²` is self-consistent on Miguel's path, NOT a universal constant.** It must be re-derived per path from the Branduardi heuristic `λ ≈ 2.3 / ⟨MSD⟩`. Our corrected path yields `λ = 100.79 Å⁻²`, ratio 1.26× vs Miguel — same regime.

See Technical Manuscript § 3 for full prose treatment.
