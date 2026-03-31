# TrpB MetaDynamics Replication Protocol

**⚠️ 这不是 entry point。Entry point 是 `CLAUDE.md`（系统自动加载）。**
**本文件是 6-stage pipeline 的详细参考手册。核心强制规则已搬到 CLAUDE.md 的"强制规则"部分。**

---

## What this project is

Using MetaDynamics (enhanced sampling MD) as a physics layer inside a generative TrpB pipeline.
Full context: `project-guide/PROJECT_OVERVIEW.md`

## The one rule

> Separate scientific decisions, execution decisions, and downstream integration claims.

Scientific decisions = what we measure and why.
Execution decisions = how we run the software.
Integration claims = what the result means for the pipeline.

These three must never collapse into one another.

---

## How to use this protocol

### Option A — Start a new campaign

Tell your AI assistant:

> "Follow `PROTOCOL.md`. Run the **Profiler** stage on [paper or task]. Freeze a campaign manifest and stop for my review."

The AI reads this file, reads `project-guide/stages/1-profiler.md`, extracts campaign facts from the paper, writes a draft `replication/manifests/[campaign_id]_manifest.yaml`, and **stops for human review before doing anything else.**

You then review and approve the manifest. Only then does the AI continue.

### Option B — Continue an existing campaign

Tell your AI assistant:

> "Follow `PROTOCOL.md`. The manifest is at `replication/manifests/[filename].yaml`. Run the **[stage name]** stage."

The AI reads the frozen manifest, reads the corresponding stage file, and executes only that stage.

### Option C — Full pipeline run (rare, only after manifest is confirmed)

Tell your AI assistant:

> "Follow `PROTOCOL.md`. Run all stages in order from Librarian to Journalist. Manifest is at `replication/manifests/[filename].yaml`. Stop if any stage produces a blocker."

---

## Stages (in order)

| # | Stage | File | What it does | When to stop for human |
|---|-------|------|-------------|------------------------|
| 0 | **Profiler** | `project-guide/stages/1-profiler.md` | Convert paper → frozen manifest | **Always. Manifest needs human sign-off.** |
| 1 | **Librarian** | `project-guide/stages/2-librarian.md` | Audit what resources exist, what's missing | When a required resource is missing or access-restricted |
| 2 | **Janitor** | `project-guide/stages/3-janitor.md` | Normalize directory structure | Rarely — flag only if paths conflict |
| 3 | **Runner** | `project-guide/stages/4-runner.md` | Generate commands / Slurm scripts / execute | When a parameter is ambiguous or unconfirmed |
| 4 | **Skeptic** | `project-guide/stages/5-skeptic.md` | Validate results against frozen manifest | When scientific validity is uncertain |
| 5 | **Journalist** | `project-guide/stages/6-journalist.md` | Write campaign summary report | Never — just write the report |

---

## Current campaigns

| Campaign | Manifest | Status |
|----------|---------|--------|
| JACS 2019 benchmark reproduction | `replication/manifests/osuna2019_benchmark_manifest.yaml` | **Runner stage** (2026-03-30) — PLP parameterization in progress |
| GenSLM-230 vs NdTrpB comparison | `replication/manifests/genslm230_vs_ndtrpb_manifest.yaml` | Blocked on benchmark + lab assets |

---

## What the frozen manifest must contain

Before any run, the manifest must answer all of these:

1. Campaign mode: `benchmark_reproduction` / `mechanism_comparison` / `physics_filter` / `surrogate_bootstrap`
2. Research question (one sentence)
3. Systems under study (names, PDB IDs or sequence sources)
4. CV definition (path CV parameters, reference structures)
5. Software stack (AMBER version, PLUMED version, force field, water model)
6. Readouts to measure (barrier heights, populations, RMSD values)
7. Success criteria (explicit numbers, not vague descriptions)
8. Downstream consumer (who uses this result, what for)
9. Known blockers (what is missing or unconfirmed)

If any of these are blank or labelled "draft", the campaign is not ready to run.

---

## What AI can automate

- Converting papers and notes into draft manifests (Profiler)
- Building resource inventory tables (Librarian)
- Standardizing directory layouts (Janitor)
- Generating AMBER/PLUMED command sequences and Slurm scripts (Runner)
- Checking whether expected files exist (Skeptic)
- Writing campaign reports (Journalist)

## What requires human judgment

- Approving the frozen manifest before any run starts
- Deciding whether a CV design captures the right biology
- Deciding whether a benchmark result is good enough to transfer to a new system
- Deciding whether a comparison result is ready to feed downstream

The AI flags these; the human decides.

---

## File locations

```
tryp B project/
├── PROTOCOL.md                     ← you are here (详细参考，entry point 是 CLAUDE.md)
├── project-guide/
│   ├── PROJECT_OVERVIEW.md         ← full project context
│   ├── stages/                     ← stage-by-stage instructions
│   │   ├── 1-profiler.md
│   │   ├── 2-librarian.md
│   │   ├── 3-janitor.md
│   │   ├── 4-runner.md
│   │   ├── 5-skeptic.md
│   │   └── 6-journalist.md
│   ├── workflow-map.md             ← how this maps from the source paper
│   └── weekly-report-guide.md     ← weekly report instructions
│
├── papers/
│   ├── annotations/                ← HTML deep annotations
│   └── reading-notes/             ← .md reading notes (one per paper)
│
├── replication/
│   ├── manifests/                  ← frozen campaign definitions
│   ├── inventories/               ← resource status tables
│   ├── runs/                       ← execution artifacts
│   ├── validations/               ← Skeptic output
│   └── campaign-reports/          ← Journalist output
│
└── reports/                        ← weekly reports
```

---

## PLP Parameterization: Literature Sources & Decisions

> 以下记录了 PLP 参数化过程中所有科学决策的来源。每个决策必须有原文出处。

### Protonation States (Ain intermediate, LLP residue)

| Group | State | Source | Evidence |
|-------|-------|--------|----------|
| Phosphate | Dianionic (-2) | Caulkins et al., JACS 2014, 136, 12824 (DOI: 10.1021/ja506267d) | ³¹P NMR chemical shift |
| Phenolate O3 | Deprotonated (-1) | Caulkins et al., JACS 2014 | ¹³C shifts on C2, C3 |
| Pyridine N1 | Deprotonated (0) | Caulkins et al., JACS 2014 | ¹⁵N δ = 294.7 ppm |
| Schiff base N (NZ) | Protonated (+1) | Caulkins et al., JACS 2014 | ¹⁵N δ = 202.3 ppm |
| **Net charge** | **-2** | Derived from above | |

### RESP Charge Fitting Protocol

| Parameter | Value | Source |
|-----------|-------|--------|
| QM level | HF/6-31G(d) | JACS 2019 SI p.S2; confirmed in Kinateder 2025, Prot. Sci. 34, e70103 |
| Charge model | RESP (Merz-Singh-Kollman) | JACS 2019 SI; Kinateder 2025 |
| Force field | GAFF | JACS 2019 SI (GAFF2 used in Kinateder 2025, but GAFF for strict replication) |
| QM software (original) | Gaussian09 | JACS 2019 SI |
| QM software (ours) | Gaussian16c02 | PI approved; minor numerical differences expected |
| Geometry optimization | Direct from PDB + reduce (ours) vs. B3LYP/6-31G(d)+D3-BJ+PCM (Kinateder 2025) | See note below |

**Note on geometry optimization**: JACS 2019 SI does not specify whether geometry optimization was performed before RESP fitting. Kinateder 2025 uses B3LYP/6-31G(d). Our Gaussian input includes `opt` keyword, which will optimize at HF/6-31G(d) level. This is acceptable — RESP charges are not highly sensitive to geometry optimization method.

### ACE/NME Capping

**Status**: RESOLVED (2026-03-30). **Capping required.**

LLP is a polymer-linked modified residue (not a free ligand). In 5DVZ, it connects to HIS81 and THR83 via peptide bonds. RESP charges must be derived on a capped ACE-LLP-NME fragment to avoid artifacts at broken peptide-bond boundaries.

- ACE cap: seeded from HIS81 CA/C/O
- NME cap: seeded from THR83 N/CA
- Charge remains -2 (caps are neutral)
- Source: AMBER advanced tutorial §1 + basic tutorial A26
- Analysis: `replication/validations/2026-03-30_capping_analysis.md` (Codex)
- Generator: `scripts/build_llp_ain_capped_resp.py`
- **Gaussian job submitted**: Job 40364008 on Longleaf (55-atom ACE-LLP-NME, HF/6-31G(d), charge=-2)

### Cross-validation with MD literature

| Paper | PLP Treatment | Consistent? |
|-------|--------------|-------------|
| Huang et al. 2016, Prot. Sci. 25, 166 | vCharge model, 17 protonation schemes, Amber99SB+GAFF | ✅ Same protonation states |
| Kinateder et al. 2025, Prot. Sci. 34, e70103 | GAFF2, RESP @ HF/6-31G(d), K84=LYN at Q₂ | ✅ Updated but compatible |

---

## Compatibility

This protocol is plain markdown. It works with:

- Claude (Cowork / Claude Code / API)
- OpenAI Codex / GPT-4 with file access
- Anthropic API with tool use
- Any AI assistant that can read markdown files

No tool-specific syntax. No YAML triggers. No vendor lock-in.
To use: tell your AI to read this file, then tell it which stage to run.
