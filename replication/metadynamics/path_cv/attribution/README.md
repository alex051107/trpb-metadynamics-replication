# Path projection attribution check (Ain vs Aex1)

Purpose: decide whether the σ_min saturation we see in the Ain probe sweep
(P1–P5, all bound at >90% on σ_s MIN or σ_z MIN past 3 ns) is a
**chemistry-specific** property of Ain, or a **geometry/path** property
that will reproduce on Aex1 before any Aex1 MetaD is run.

ChatGPT Pro recommended this as a cheap front-run before spending a week on
Aex1 MetaD; their prior was 60% geometry-dominant, 25% mixed, 15%
Ain-chemistry-specific (consult
`.local_scratch/chatgpt_pro_ain_nextstep/followup_aex1_sigma_attribution.md`
for the full reasoning).

## Workflow

```
    Ain 500 ns cMD (.nc)            Aex1 cMD (.dcd, running)
            |                                |
            | 100-105 ns window              | 10-15 ns window
            v                                v
    project_to_path.py               project_to_path.py
            |                                |
            +-> COLVAR_proj (s, z)  <-+
                                     |
                                     v
                         compare_projections.py
                                     |
                                     v
               4-readout table + verdict tag
```

## Files

| File | Role |
|---|---|
| `project_to_path.py` | Load (traj, topology), select 112 Cα by (resid, name) pattern read from `path_gromacs.pdb`, slice time window, write per-MODEL renumbered PDB (FP-030 pattern), run `plumed driver` with PATHMSD projection. |
| `compare_projections.py` | Parse two COLVAR_proj, emit median/IQR/p95/max/frac(s>1.5,2.0)/occupied_bins, apply ChatGPT Pro's pass/fail thresholds, print Markdown + JSON. |
| `run_attribution.sh` | Longleaf-side wrapper that invokes the projector on both lines and then the comparator. Window + path + topology all overridable via env vars. |
| `README.md` | This file. |

## Usage

On a Longleaf login node, inside `conda activate trpb-md`:

```bash
cd replication/metadynamics/path_cv/attribution
# defaults: Ain 100-105 ns, Aex1 10-15 ns, same path_gromacs.pdb + lambda=379.77
bash run_attribution.sh
# or override
AEX1_BEGIN_NS=5 AEX1_END_NS=10 bash run_attribution.sh
```

Outputs land in `${ANIMA_ROOT}/analysis/path_projection_attribution_<utc>/`:

```
ain_proj.colvar       # s, z time series for Ain window
aex1_proj.colvar      # s, z time series for Aex1 window
comparison.md         # Markdown table + verdict, pasteable into PR
comparison.json       # structured
```

## Verdict thresholds (from ChatGPT Pro 2026-04-23)

| Signal | Threshold | Interpretation |
|---|---|---|
| p95(s) Aex1 - Ain ≥ +0.5 | chemistry-prior-strengthened | Aex1 explores materially further along path |
| occupied_bins Aex1 / Ain ≥ 2.0 | chemistry-prior-strengthened | Aex1 covers much larger (s, z) area |
| \|median_s Aex1 - Ain\| < 0.2 AND IQR ratio ∈ [0.80, 1.25] AND \|p95(s) delta\| < 0.3 | geometry-prior-strengthened | Distributions overlap; path/metric is the bottleneck |
| Both chemistry and geometry signals | ambiguous | Extend both lines to 20-30 ns before deciding |
| Neither | no-clear-signal | Extend both lines to 20-30 ns before deciding |

**Even a geometry-prior-strengthened verdict does not replace the planned
10 ns Aex1 MetaD** — this check only sharpens the prior before committing
GPU time.

## Assumptions / caveats

1. `path_gromacs.pdb` has 15 MODELs × 112 Cα (asserted at load time).
2. The (resid, atom_name) pattern from MODEL 1 of `path_gromacs.pdb`
   resolves uniquely in both the Ain parm7 and the Aex1 OpenMM pdb.
   If Aex1 (5DW0 numbering) uses different residue numbers than Ain
   (1WDW/tleap numbering), the projector will fail at select_matching_atoms
   with a clear missing-atom list — in that case we need an explicit
   Aex1↔Ain residue mapping before this run is valid.
3. Ain cMD `prod_500ns.nc` was a single-replica 500 ns pmemd.cuda run
   (job 40806029). Window 100-105 ns is well past thermal relaxation.
4. Aex1 cMD (job 45186335) post-equilibration; default 10-15 ns window
   assumes prod.dcd has reached ≥15 ns. Override if shorter.
5. PLUMED version = `plumed` in `trpb-md` conda env (same binary that
   produced the PASS results in `diagnostics/VERDICT_2026-04-21.md`).
6. λ=379.77 nm⁻² (FP-022-settled per-atom MSD convention) — not revisited.

## Provenance in output COLVAR

`project_to_path.py` prepends a `# provenance:` line to each COLVAR_proj
recording (traj, topology, path_ref, window, stride, lambda, label). The
comparator surfaces both provenance strings in its Markdown output.

## Related

- `../diagnostics/VERDICT_2026-04-21.md` — PATHMSD / λ / metric layer
  cleared (steps 1+2 PASS). This attribution check is the follow-up for
  step 3's unresolved "chord-geometry vs filling-pattern" ambiguity.
- `../../probe_sweep/ladder.yaml` — the 5-probe σ scan that motivated
  the attribution question.
- FP-022 (λ convention), FP-030 (driver-local serial renumbering).
