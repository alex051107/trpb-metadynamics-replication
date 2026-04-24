# Week-7 Complete Deliverable Package — 2026-04-24

Everything used in Week 7 of the TrpB MetaDynamics replication, organized by logical stage of the pipeline. Each subdirectory is self-describing via its own `README.md`.

**Scope**: the path-CV bug fix (FP-034), the Miguel first-author parameter contract, the completed single-walker pilot, both failed 10-walker attempts, and the design of the v3 pipeline. Topics covered correspond to § 1-5 of the bilingual technical manuscript.

**All files are English-only.** Internal Chinese notes kept separately in `09_documents/GroupMeeting_2026-04-24_TechDoc_技术文稿.md` (bilingual reader: use the `_Bilingual.md` file).

---

## Directory index

| # | Directory | What it contains | Main output |
|---|---|---|---|
| 01 | `01_path_construction/` | Needleman-Wunsch + Kabsch + interpolation scripts, verification reports, final reference PDB | `path_seqaligned_gromacs.pdb`, λ = 100.79 Å⁻² |
| 02 | `02_miguel_contract/` | First-author email reply, parsed PLUMED template, λ-audit memo | Frozen parameter spec |
| 03 | `03_pilot_run/` | Single-walker pilot submit script + PLUMED + statistics | `max(s) = 12.87` in 8 ns |
| 04 | `04_baseline_naive_path/` | Single-walker baseline on naive path (pre-FP-034) | Stuck at `s < 1.9` over 16 ns |
| 05 | `05_v1_10walker_scancelled/` | v1 submit script + materialize (scancelled for FP-030 homogeneous start) | Evidence of why seeds diverged wrongly |
| 06 | `06_v2_10walker_crashed/` | Crash logs, Codex root-cause diagnosis, sacct output, COLVAR blow-up excerpts | Diagnostic package |
| 07 | `07_v3_pipeline_plan/` | Codex-verified EM + NVT + production submit template, assertion suite | Ready to submit after PI approval |
| 08 | `08_figures/` | `plot_sz_distribution.py` + 3 rendered PNGs | `sz_2d_distribution.png` (headline figure) |
| 09 | `09_documents/` | Group-meeting slides (11 pp) + 4 TechDocs (EN+ZH, ZH, cheatsheet, selection-logic) | Full narrative |

---

## Reading order for a newcomer

1. `09_documents/GroupMeeting_2026-04-24_TechDoc_Bilingual.md` — **start here**; the 7-section bilingual manuscript is the canonical story.
2. `08_figures/sz_2d_distribution.png` — the one figure that summarises the Week-7 result.
3. `01_path_construction/summary.txt` — concrete numbers: identity 59.0 %, RMSD 2.115 Å, λ = 100.79 Å⁻², ratio vs Miguel = 1.26×.
4. `01_path_construction/VERIFICATION_REPORT.md` — independent Codex re-implementation, 7 of 8 strict checks pass.
5. `02_miguel_contract/miguel_email.md` — verbatim text of the author's parameter reply.
6. `03_pilot_run/pilot_45515869_stats.txt` — the completed pilot that validates the path fix.
7. `06_v2_10walker_crashed/` + `07_v3_pipeline_plan/` — where production stands and what the next step is.

---

## Reproducibility guarantee

Every numerical claim in this package can be regenerated from:

```bash
# Reconstruct the sequence-aligned path from source PDBs
cd 01_path_construction/
python3 build_seqaligned_path.py \
    --structures ../../../replication/metadynamics/path_piecewise/structures \
    --output-dir .

# Regenerate the FES figure (requires COLVAR files kept outside this package)
cd ../08_figures/
python3 plot_sz_distribution.py

# Full verification suite (Codex cross-check)
cd ../01_path_construction/
python3 verify_and_materialize_seqaligned_path.py
```

---

## What is NOT in this package

- **Raw COLVAR time series** (pilot 2.3 MB, baseline 4.8 MB, walkers 3.2 MB). These live in `chatgpt_pro_consult_45558834/raw_data/` one level up, because they are too large and a bit redundant with the summary statistics kept here.
- **HILLS deposition logs** (pilot 726 KB). Same reason.
- **`start.gro`** (2.6 MB GROMACS structure). Kept at the HPC source of truth on UNC Longleaf at `/work/users/l/i/liualex/AnimaLab/metadynamics/miguel_2026-04-23/initial_seqaligned/start.gro`.
- **`topol.top` + force-field directories** (80+ MB). Longleaf source of truth as above.
- **ML-layer future plans**. Excluded by PI request for this week's deliverable.

---

## Commit history behind this package

Each of the following commits on branch `path-piecewise-pilot` contributed material in this package:

```
eccd929  Add root README + clean English Week-7 results release
e739a18  TechDoc: new bilingual (EN+ZH) manuscript + correct NW implementation details
75a4794  GroupMeeting 2026-04-24 v3: 5-topic slides + clean FES figure + Codex v2 diagnosis
694508b  Slide 10 + slide 19: (s, z) 2D density — JACS-Fig3 style
2969680  Slide 10 s-trend figure: before/after FP-034
9951c5a  Meeting prep: SELECTION_LOGIC.md
6d613e4  Pro verdict pass 3: soften s=7 to "off-path projection", slide 9 rewrite
46eebd3  10-walker primary production LAUNCHED: Longleaf SLURM 45558834 (later scancelled)
7eb6dbb  GATE CLEARED real-time update: pilot max_s=12.87 at t=6085 ps
```

Upstream: <https://github.com/alex051107/trpb-metadynamics-replication> · branch `path-piecewise-pilot`.
