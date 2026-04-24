# TrpB MetaDynamics Replication

**Project**: Independent replication of the free-energy landscape (FEL) reported in Maria-Solano *et al.* JACS 2019 (DOI: [10.1021/jacs.9b03646](https://doi.org/10.1021/jacs.9b03646)) for the β-subunit of tryptophan synthase (TrpB) from *Pyrococcus furiosus*.

**Author**: Zhenpeng Liu (UNC-Chapel Hill, undergraduate researcher).
**Target lab**: Anima Anandkumar group (Caltech) — this work is a technical portfolio piece prepared for a summer research application.
**Language**: this repository is maintained in English. Internal planning notes may contain Chinese; all code, scripts, and published results are English.

---

## 1 · What this repo is

A faithful, bit-level reproducible implementation of the original protocol:

- **Conventional MD**: AMBER 24p3 `pmemd.cuda`, 500 ns WT TrpB-Pf + PLP-Ser (Ain intermediate).
- **Metadynamics engine**: GROMACS 2026.0 + PLUMED 2.9.2 (source-built kernel).
- **Collective variable**: PATHMSD with 15-frame linear-interpolation path between 1WDW (Open) and 3CEP (Closed) β-subunit Cα coordinates.
- **Force field**: ff14SB + TIP3P, T = 350 K, 2 fs timestep, LINCS on h-bonds.
- **Parameters**: frozen from the first author's (Miguel Maria-Solano) email reply of 2026-04-23; see [`replication/metadynamics/miguel_2026-04-23/`](replication/metadynamics/miguel_2026-04-23/).

## 2 · Current status (2026-04-24, Week 7)

| Milestone | Status |
|---|---|
| PLP-Ser (Ain) RESP parameterization | ✅ done |
| System build (tleap) | ✅ done — 39 268 atoms, charge-neutral |
| Toy MetaD validation (alanine dipeptide) | ✅ done |
| Conventional MD — 500 ns | ✅ done (job 40806029) |
| AMBER → GROMACS conversion | ✅ done (ParmEd) |
| PLUMED 2.9.2 source build | ✅ done |
| Path CV reference v1 (naive resid mapping) | ❌ superseded by FP-034 fix |
| **Path CV reference v2 (sequence-aligned)** | ✅ done — see [`replication/metadynamics/path_seqaligned/`](replication/metadynamics/path_seqaligned/) |
| Single-walker pilot on corrected path | ✅ done — job 45515869, 8 ns, max(s) = 12.87 |
| 10-walker production v1 | ❌ scancelled (FP-030 homogeneous start) |
| 10-walker production v2 | ❌ all FAILED exit 139 (LINCS blow-up, seed not equilibrated) |
| **10-walker production v3 with EM + NVT settle** | 🟡 pipeline designed (Codex-verified), awaiting PI go |
| Free-energy surface FES(s, z) — WT | ⏳ pending v3 |
| Aex1 / Q₂ / A-A variant FES | ⏳ downstream of WT |

## 3 · Headline result — Path-CV bug fix (FP-034)

The original path CV compared 1WDW-B residue *X* to 3CEP-B residue *X* by residue number, which is **wrong** because the two chains differ by a +5 N-terminal offset. After fixing the mapping with a sequence-aligned `build_seqaligned_path.py`, the walker exploration widens dramatically:

|  | Naive path (pre-FP-034) | Sequence-aligned (post-FP-034) |
|---|---:|---:|
| Cα identity over 112 residues | 6.2 % | **59.0 %** |
| O↔C per-atom RMSD (Å) | 10.89 | **2.115** |
| ⟨MSD_adj⟩ along path (Å²) | 0.606 | **0.0228** |
| λ = 2.3 / ⟨MSD⟩ (Å⁻²) | 3.80 | **100.79** |
| Single-walker pilot max(s), 8 ns | 1.90 (16 ns) | **12.87** |

See the side-by-side FES(s, z) figure: [`results/week7_2026-04-24/sz_2d_distribution.png`](results/week7_2026-04-24/sz_2d_distribution.png).

## 4 · Repository layout

```
.
├── README.md                      — this file
├── results/
│   └── week7_2026-04-24/          — clean English release of Week-7 deliverables
│       ├── README.md              — result summary
│       ├── sz_2d_distribution.png — FES(s, z) naive vs sequence-aligned
│       ├── path_seqaligned_summary.txt
│       ├── pilot_45515869_stats.txt
│       └── baseline_45324928_stats.txt
├── replication/
│   ├── metadynamics/
│   │   ├── path_seqaligned/       — FP-034 fix: NW alignment + path construction
│   │   ├── miguel_2026-04-23/     — frozen parameter spec from author email
│   │   ├── single_walker/         — pilot runs (legacy + current)
│   │   └── archive_pre_2026-04-15/— deprecated runs kept for audit
│   ├── parameters/                — PLP RESP + ff14SB + TIP3P + MetaD parameter tables
│   ├── validations/
│   │   └── failure-patterns.md    — registry of documented mistakes (FP-001 … FP-034)
│   └── scripts/                   — reusable build/convert/project utilities
├── reports/
│   ├── GroupMeeting_2026-04-24_TechDoc_Bilingual.md   — full EN+ZH technical manuscript
│   ├── GroupMeeting_2026-04-24.pptx                   — group-meeting slides (11 pages)
│   └── figures/
│       ├── plot_sz_distribution.py                    — reproducible figure script
│       └── sz_2d_distribution.png                     — rendered figure
└── papers/                        — primary literature, annotations, reading notes
```

## 5 · Reproducing the FES figure

```bash
git clone https://github.com/alex051107/trpb-metadynamics-replication.git
cd trpb-metadynamics-replication

# Install plotting dependencies
pip install numpy scipy matplotlib

# The two COLVAR inputs are held in a sibling data directory
# (not redistributed here because of size; see results README for how to regenerate on HPC).
python3 reports/figures/plot_sz_distribution.py
# → reports/figures/sz_2d_distribution.png
```

## 6 · Rebuilding the sequence-aligned path from source structures

```bash
cd replication/metadynamics/path_seqaligned/

# Needs 1WDW.pdb and 3CEP.pdb in ../path_piecewise/structures/
python3 build_seqaligned_path.py --structures ../path_piecewise/structures --output-dir .
# → path_seqaligned.pdb, summary.txt, plumed_path.dat

# Materialize the GROMACS-atom-serial-preserving production PDB
python3 verify_and_materialize_seqaligned_path.py
# → path_seqaligned_gromacs.pdb, VERIFICATION_REPORT.md
```

## 7 · Collaboration model

This project uses a three-role architecture documented in [`CLAUDE.md`](CLAUDE.md) and based on arXiv 2602.02128 (scaling reproducibility):

- **PI (Yu Chen, UNC-CH)** — scientific decisions, priority calls, sign-off.
- **Designer (Claude)** — planning, coordination, review of Codex output, writing.
- **Executor (Codex)** — script authoring, file edits, command generation, numerical artifacts.

Formal debate protocol for disagreements: [`.ccb/debate-protocol.md`](.ccb/debate-protocol.md).

## 8 · Failure patterns registry

The repository maintains a disciplined failure-patterns registry at [`replication/validations/failure-patterns.md`](replication/validations/failure-patterns.md). Notable Week-7 entries:

- **FP-031** — ADAPTIVE=GEOM misread. GEOM projects σ onto the chord direction, which is ill-defined at path endpoints. Fix: use ADAPTIVE=DIFF.
- **FP-032** — PLUMED UNITS nm/kJ vs Å/kcal. Miguel's SIGMA literals (0.1, 0.3, 0.005) are Å/kcal. Fix: `UNITS LENGTH=A ENERGY=kcal/mol` as the very first line of `plumed.dat`.
- **FP-034** — cross-species residue-number naive mapping. 1WDW-B resid *X* is homologous to 3CEP-B resid *X+5*, not *X*. Fix: Needleman-Wunsch alignment of crystal-chain Cα sequences with an empirical uniform-offset check over the 112 selected residues.

## 9 · Licence and citation

All source code is released under the MIT licence. Any downstream use of the methodology should cite Maria-Solano *et al.* 2019 (the original FES study) and this repository.

## 10 · Contact

Zhenpeng Liu — `liualex@ad.unc.edu`
