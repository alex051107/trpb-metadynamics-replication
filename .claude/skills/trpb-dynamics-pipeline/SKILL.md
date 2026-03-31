---
name: trpb-dynamics-pipeline
description: Operate the enhanced-sampling layer of the Caltech TrpB generative pipeline. Use when the task involves benchmark metadynamics reproduction, GenSLM-230 vs NdTrpB comparison, D-Trp conformational-filter design, trajectory feature export, PLUMED path collective variables, AMBER setup, or converting papers and weekly reports into frozen campaign manifests and validation reports.
---

# TrpB Dynamics Pipeline

This is the top-level orchestration skill for the enhanced-sampling portion of the TrpB project.

It adapts the architecture from `Scaling Reproducibility: An AI-Assisted Workflow for Large-Scale Reanalysis` to a project where MetaDynamics is a calibration and integration layer for a broader generative pipeline.

The core rule is:

> Separate science, execution, and downstream integration claims.

For this project, that means:

- human-reviewed campaign choices stay fixed during a run
- setup, staging, path normalization, artifact checks, and reporting can be automated
- the LLM does not invent numerical results or silently rewrite the scientific question
- new fixes are recorded between runs, not improvised silently mid-run

Read these first when the skill is triggered:

- [METADYNAMICS_PROJECT_INTENT.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/METADYNAMICS_PROJECT_INTENT.md)
- [PROJECT_PROTOCOL.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/repro-workflow/PROJECT_PROTOCOL.md)
- [SCALING_REPRODUCIBILITY_TO_TRPB_METADYNAMICS.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/SCALING_REPRODUCIBILITY_TO_TRPB_METADYNAMICS.md)

## Project Scope

This skill is specifically for:

- benchmark reproduction on literature TrpB systems
- mechanistic comparison campaigns such as `GenSLM-230` vs `NdTrpB`
- designing a physics-based conformational filter for `D-Trp`
- exporting trajectory-derived features for later surrogate or scoring work
- PLUMED + AMBER or related metadynamics workflows
- translating papers, weekly reports, and local notes into versioned manifests and campaign reports

Primary local project references:

- [MetaDynamics_Setup_Notes.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/MetaDynamics_Setup_Notes.md)
- [RESOURCE_INDEX.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/RESOURCE_INDEX.md)
- [TASKS.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/TASKS.md)
- [3.21_ZhenpengLiu_Weekly_report.docx](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/3.21_ZhenpengLiu_Weekly_report.docx)
- [WeeklyReport_Week1_final.docx](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/reports/WeeklyReport_Week1_final.docx)

Useful companion skill packs already vendored in this project:

- [molecular-dynamics](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/tools/claude-scientific-skills/scientific-skills/molecular-dynamics/SKILL.md)
- [paper-annotation-skill](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/paper-annotations/paper-annotation-skill/SKILL.md)

## Supported Modes

Every task should declare one of these modes explicitly:

1. `benchmark_reproduction`
2. `mechanism_comparison`
3. `physics_filter`
4. `surrogate_bootstrap`

If a task combines multiple modes, split it into separate manifests and reports.

## Fixed Campaign Template Before Any Run

Before generating or executing any run plan, freeze the following into a manifest:

1. campaign mode
2. research question
3. systems under study
4. CV or analysis definition
5. simulation and analysis stack
6. measurable readouts
7. validation criteria
8. downstream consumer of the result
9. blockers and unresolved assumptions

Do not change these silently once a run starts.

Use [campaign_manifest.template.yaml](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/.codex/skills/trpb-dynamics-pipeline/templates/campaign_manifest.template.yaml) as the starting point.

Two example manifests already exist:

- [osuna2019_benchmark_manifest.yaml](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/repro-workflow/manifests/osuna2019_benchmark_manifest.yaml)
- [genslm230_vs_ndtrpb_manifest.yaml](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/repro-workflow/manifests/genslm230_vs_ndtrpb_manifest.yaml)

## Workflow

Follow these stages in order.

### 1. Profiler

Goal:
- convert papers, weekly reports, and local notes into structured campaign facts

Inputs:
- paper PDF or notes
- weekly reports
- current project docs

Outputs:
- `campaign_manifest.yaml`
- `metric_spec.md`
- `study_info.json` if a downstream stage needs it

Tasks:
- identify campaign mode, research question, systems, readouts, and downstream consumer
- distinguish explicit facts from inference or hypothesis
- mark uncertainty fields clearly

### 2. Librarian

Goal:
- gather external resources deterministically and keep provenance explicit

Inputs:
- DOI, PDB IDs, supplementary links, lab resources, candidate assets

Outputs:
- local download inventory
- resource status table

Tasks:
- fetch structures, supplements, and local candidate inputs
- locate SI, PLUMED examples, or assay references
- record missing resources instead of guessing

### 3. Janitor

Goal:
- normalize the execution workspace for a specific campaign

Outputs:
- workspace plan
- cleaned paths
- normalized filenames
- environment notes

Tasks:
- standardize relative paths
- separate raw inputs, generated artifacts, and exported features
- prepare directory layout for benchmark vs comparison vs filter campaigns
- record all repairs in a changelog

### 4. Runner

Goal:
- generate or execute deterministic commands and analysis steps

Outputs:
- staged command list
- run logs
- exported analysis files
- feature tables if applicable

Tasks:
- prefer a validation ladder:
  1. toy enhanced-sampling validation
  2. published TrpB benchmark
  3. pairwise comparison campaign
  4. filter or surrogate-export batch
- never claim success without artifacts on disk

### 5. Skeptic

Goal:
- validate outputs against the fixed campaign template

Outputs:
- validation report

Tasks:
- verify expected files exist
- compare observed behavior with mode-specific expectations
- flag ambiguous success conditions
- separate operational failure, scientific mismatch, and integration overreach

### 6. Journalist

Goal:
- produce a reusable report for the campaign

Outputs:
- campaign summary
- blockers
- next actions

Use [campaign_report.template.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/.codex/skills/trpb-dynamics-pipeline/templates/campaign_report.template.md).

## Stage Skills

This orchestration skill assumes the following stage-specific skills exist in the project and may be invoked manually or conceptually:

- `trpb-profiler`
- `trpb-librarian`
- `trpb-janitor`
- `trpb-runner`
- `trpb-skeptic`
- `trpb-journalist`

## Adaptation Rules

Use the paper's four-phase adaptation cycle:

1. detect anomaly
2. diagnose root cause
3. generalize fix
4. record the fix

Record recurring issues in [failure-patterns.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/.codex/skills/trpb-dynamics-pipeline/references/failure-patterns.md).

Important:
- do not bake benchmark-specific hacks into a single run without documenting them
- do not overwrite the campaign template while debugging execution
- do not confuse “environment repaired” with “science validated”
- do not confuse “scientifically interesting” with “ready to feed downstream”

## Current Project Reality

This repository is not yet at the "press run and get production features" stage.

Current known blockers from project docs:

- Caltech HPC access still pending
- some exact benchmark parameters from Osuna 2019 may still require manual confirmation
- a rigorous `D-Trp` metric is not yet fixed
- some candidate assets are still pending from JP

Therefore, the most valuable automation right now is:

- campaign freezing
- resource tracking
- workspace normalization
- validation checklist generation
- report generation
- feature-export planning

## Output Standard

Whenever this skill is used, aim to leave behind:

- one fixed `campaign_manifest.yaml`
- one explicit execution or analysis plan
- one validation report
- one updated failure-pattern entry if a new blocker was resolved
