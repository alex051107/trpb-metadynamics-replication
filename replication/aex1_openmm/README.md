# Aex1 + OpenMM parallel pilot

Chemistry-control pilot running in parallel to the `new_idea_explore` probe sweep. Tests whether the O-basin stall observed with Ain (isolated PfTrpB + LLP cofactor) is chemistry-specific, by swapping the intermediate to Aex1 (PLP–Ser external aldimine, PDB 5DW0) while keeping PATHMSD + λ + `plumed.dat` byte-identical.

## Branch
`aex1-openmm-parallel` off `new_idea_explore` at commit `e2f19f4` (path-CV diagnostic suite).

## Why OpenMM
Lab standard (Yu's group). OpenMM + `openmm-plumed` plugin already CPU-validated in `replication/openmm_toy/` (Job 44296608). PLUMED syntax is byte-compatible with our GROMACS+PLUMED 2.9 stack, so `plumed.dat` can be reused verbatim. Primary parameterization path = `openmmforcefields.generators.SystemGenerator` with GAFF-2.11 templates. GAFF+RESP+tleap kept as fallback only if the PLS covalent adduct breaks the SystemGenerator template.

## Reframing
5DW0 chain A projects to `s ≈ 1.07` on the current 15-frame 1WDW→3CEP path (prior CV audit, `reports/GroupMeeting_2026-04-17_TechDoc_技术文稿.md:665`). So this pilot does NOT bypass the O-endpoint start. It is a **chemistry control**, not a geometry bypass.

Interpretation:
- Aex1 walker escapes `s ≈ 1` → O-basin trap is Ain-specific (chemistry).
- Aex1 shows identical OFF-TANGENT signature → path weakness is not Ain-specific; chord-geometry fix becomes leading candidate.

## Workstream (plan file: `~/.claude/plans/clever-tickling-sparrow.md` §Phase B)

| Step | Gate | Status |
|------|------|--------|
| B0 branch scaffolding | —  | in progress |
| B1 pilot objective one-liner | PM sign-off | pending |
| B2 manifest freeze | PM sign-off | pending |
| B3 PLS chemistry memo | PM sign-off REQUIRED | pending |
| B4 OpenMM SystemGenerator parameterization | atom/charge self-consistency | pending |
| B4b GAFF+RESP+tleap fallback | only if B4 fails | pending |
| B5 system build (Modeller + TIP3P solvation) | minimize < 1e4 kJ/mol/nm RMS force | pending |
| B6 new path reference with Aex1 atom serials | Kabsch coord preservation | pending |
| B7 self-projection regression | s: 1.09 → 14.91; 5DW0 → s ≈ 1.07 | pending |
| B8 Aex1 MetaD pilot | FP-028 CUDA env re-pin required first | pending |
| B9 decision memo | — | pending |

## Critical references
- `replication/openmm_toy/OPENMM_SETUP_TECHDOC.md` — lab env `md_setup_trpb`
- `replication/metadynamics/path_cv/diagnostics/VERDICT_2026-04-21.md` — diagnostic outcome
- `replication/parameters/JACS2019_MetaDynamics_Parameters.md` §3 — Ain parameter provenance (reuse unchanged)
- `replication/validations/failure-patterns.md` FP-028 — CUDA driver/PTX blocker for B8

## Explicit non-goals
- Does NOT touch production Ain files on `new_idea_explore` (`replication/metadynamics/single_walker/*`, `probe_sweep/**`).
- Does NOT draw conclusions about path chord geometry — that is the probe sweep's job.
- Does NOT revisit `λ = 379.77 nm⁻²` (FP-022-settled per FP-027 warning).
