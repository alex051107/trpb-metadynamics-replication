# GroupMeeting 2026-04-17 — Slide Outline

**Meeting**: 1-on-1 with Yu Zhang | **Date**: 2026-04-17 | **Format**: ~15 min tech deep-dive  
**Audience expectation**: per-parameter drill (reference 2026-04-09 transcript)  
**This deck's arc**: FP-024 diagnosis → fix → probe → wrong turn (FP-027) → CV audit → current 50 ns extension → process improvements

---

## Slide 1 — Title

- **Title**: TrpB MetaDynamics — Week 6 Progress
- **Subtitle**: SIGMA Floor Fix + Path CV Audit
- **Meta**: Zhenpeng Liu · 2026-04-17 · 1-on-1 with Yu Zhang
- **Reference**: Maria-Solano et al., JACS 2019, 141, 13049-13056

## Slide 2 — Recap: where we left off (2026-04-09)

- λ corrected 3.3910 → **379.77 nm⁻²** (per-atom MSD convention, FP-022)
- Switched FUNCPATHMSD → **PATHMSD** (source-compiled PLUMED 2.9.2)
- Job 42679152 submitted (50 ns single walker, ETA ~04-12)
- Action items carried: run, FES reconstruction, 10-walker

## Slide 3 — Job 42679152 result: walker stuck in O

- 50 ns complete, 25,000 Gaussians, 48 kJ/mol bias, 0 NaN — mechanically healthy
- **But `s(R) ∈ [1.00, 1.63]` over full run** — never left O basin
- HILLS column 4: `sigma_path.sss` collapsed to 0.011–0.072 s-units (0.07–0.5% of path axis)
- Classic **FP-024 signature**: biased adaptive-σ collapse

## Slide 4 — FP-024 root cause: SIGMA is Cartesian nm, not CV units

- PLUMED 2.9 METAD docs (primary source): "Sigma is one number that has distance units"
- Single Cartesian scalar → no floor on per-CV projected σ → can collapse to near-zero
- 25,000 needle Gaussians pile at s=1 → deep narrow well, zero force gradient on protein atoms
- 4 parallel Explore agents independently verified (physics, literature, Longleaf, PLUMED source)

## Slide 5 — Fix: add SIGMA_MIN / SIGMA_MAX floors (deployed 2026-04-15)

```
metad: METAD ARG=path.sss,path.zzz SIGMA=0.1 ADAPTIVE=GEOM
       SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05
       HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
```

- SIGMA 0.05→0.1 nm (larger seed); **SIGMA_MIN/MAX are per-CV in CV units** (PLUMED docs)
- 10 ns probe Job 43813633 submitted same day (partition=hov, 14h walltime)
- Also logged **FP-025**: `[SI p.S3]` SIGMA=0.2,0.1 citation was fabricated by earlier AI

## Slide 6 — Job 43813633 probe: max s=1.393 — stuck or escaping?

- t=[0,8] ns: 99%+ time in s=1.0–1.05 (confined)
- t=[8,10] ns: abrupt mobilization, max s jumps 1.19 → **1.393** in final 2 ns
- s↔z correlation: -0.31 (orthogonal motion) → **+0.49** (aligned escape, classic barrier crossing)
- Escape velocity roughly **doubles** in the last window (0.000086 → 0.000192 per ps)

## Slide 7 — Wrong turn (FP-027): Codex adversarial review caught me

- **My misread**: SI p.S3 "λ = ... 80" → interpreted as λ=80 nm⁻² → "we're 4.75× off" → 3 h on alignment-method hypothesis
- **Codex pushback**: comparing different quantities; premise unsound
- **Repo evidence (line 23-25 of summary.txt)** already said: "Reported MSD: ~80 Å² (interpreted as total SD) / Our total SD: 67.826 Å² (ratio 0.85x)"
- **Lesson**: SI re-interpretation must read repo notes first. Logged FP-027 + new rule 21.

## Slide 8 — CV audit (Codex recommendation): path CV is physically correct

Projected 6 known PDB structures onto current PATHMSD (LAMBDA=379.77):

| PDB | chain | n | s(R) | z(R) nm² | Note |
|-----|-------|---|------|----------|------|
| 1WDW | B | 112 | **1.09** | -0.00025 | O endpoint (frame 1 source) |
| 3CEP | B | 112 | **14.91** | -0.00025 | C endpoint (frame 15 source) |
| **4HPX** | B | 112 | **14.91** | -0.00005 | Pf A-A intermediate = StTrpS C (cross-species) |
| 5DW0 | A | 112 | 1.07 | 0.024 | Pf+L-Ser (Aex1), O-like |
| 5DVZ | A | 112 | 1.07 | 0.017 | Pf holo, O-like |
| 5DW3 | A | partial | — | — | informational |

- **Strongest evidence**: Pf-closed (4HPX) projects to s=14.91, matching St-closed (3CEP) — CV correctly spans cross-species conformational axis
- Path CV physics confirmed. Remaining issue is **kinetic timescale**, not CV pathology.

## Slide 9 — Job 44008381: extend 10→50 ns via safe checkpoint restart

```
gmx convert-tpr -s metad.tpr -extend 40000 -o metad_ext.tpr
gmx mdrun -s metad_ext.tpr -cpi metad.cpt -plumed plumed_restart.dat
```

- `plumed_restart.dat` = plumed.dat + `RESTART` directive (PLUMED 2.9 docs: required; not auto-passed by gmx)
- Codex stop-hook caught 2 bugs in v1 → **FP-026**: `-nsteps` alone doesn't bypass "sim complete"; no RESTART clobbers HILLS
- Runtime verified: HILLS 5003→5106+ rows, no `bck.*.HILLS`, first data rows unchanged
- **Decision gate @ 25 ns** (~2026-04-18 AM):
  - max s ≥ 5 → Phase 2 (10-walker production, SI protocol)
  - 3 ≤ max s < 5 → finish 50 ns, re-evaluate
  - max s < 3 → Phase 3 (4HPX-seeded dual-walker, ~1 day setup)

## Slide 10 — Process improvements + next steps

**Process this week**
- `PARAMETER_PROVENANCE.md` — every numerical parameter tagged (SI-quote / SI-derived / PLUMED-default / Our-choice / Legacy-bug) + verification status
- `failure-patterns.md`: FP-001..FP-027 + 21 general rules (added FP-024..027 this week)
- `project_structures.py` CV audit is a hard gate now: exit 0/2/3/4 with AuditError class; malformed input → exit 3 (not crash)
- Repo made private; 3 branches pushed: `fix/fp024-sigma-floor`, `feature/probe-extension-50ns`, `diag/cv-audit`

**Next steps**
1. 2026-04-18 AM: check Job 44008381 @ 25 ns → Phase 2 vs 3
2. **If Phase 2**: pick 10 snapshots by **visual inspection in PyMOL** (Yu's 2026-04-09 directive — not strided frame index), deploy 10-walker (~500 ns total)
3. **If Phase 3**: build 4HPX-seeded Ain-PLP system (~1 day), dual-seed multi-walker
4. FES reconstruction + JACS 2019 Fig 2a comparison target: **2026-04-24**
5. OpenMM migration: **defer** (Yu flagged e-track pipeline has outdated packages + memory issues on 2026-04-09)
