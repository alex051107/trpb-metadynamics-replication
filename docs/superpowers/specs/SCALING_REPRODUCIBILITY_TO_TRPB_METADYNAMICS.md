# Scaling Reproducibility -> TrpB Dynamics Pipeline

## Paper

**Title:** Scaling Reproducibility: An AI-Assisted Workflow for Large-Scale Reanalysis  
**Authors:** Yiqing Xu, Leo Yang Yang  
**arXiv:** 2602.16733  

## One-Sentence Thesis

The paper shows that complex scientific workflows scale when the research question is frozen into an explicit template, execution is decomposed into modular stages, and recurring fixes become reusable knowledge.

## What Their “Skill” Actually Is

Their “skill” is not a single prompt. It is a workflow architecture:

1. an orchestrator
2. stage-specific `SKILL.md` files that act as both contracts and knowledge bases
3. deterministic executors for numerically sensitive work

The most important design choice is:

> the LLM does not own the numerical path

For the IV paper, that meant routing and failure interpretation stayed in the LLM while the actual estimation and diagnostics stayed in code.

## What Transfers Cleanly To This Project

The following ideas transfer well to the TrpB project:

- separate campaign design from execution
- store recurring failures as reusable rules
- use explicit intermediate artifacts instead of hidden state
- treat setup, path cleanup, reporting, and feature export as automatable
- keep scientific choices human-reviewed and versioned

## What Does Not Transfer Directly

The paper's executor is built around social-science replication packages. This project is different in three important ways:

1. the main target is not a single benchmark reproduction
2. some critical quantities are still hypotheses, especially for `D-Trp` selectivity
3. the downstream goal is integration into a generative enzyme pipeline

So for this project, the fixed template must capture:

- campaign mode
- research question
- systems to compare or screen
- CV and analysis definition
- software stack
- validation criteria
- downstream consumer of the result

## Mapping To The Current TrpB Project

| Paper workflow piece | TrpB project meaning |
|---|---|
| Profiler | turn papers, weekly reports, and pipeline notes into a frozen campaign definition |
| Librarian | gather structures, supplements, candidate assets, and authoritative references |
| Janitor | normalize workspace, paths, filenames, and campaign directories |
| Runner | stage deterministic commands, analyses, and feature exports |
| Skeptic | check operational validity, scientific validity, and integration readiness |
| Journalist | write campaign reports and handoff notes |

## Current Local Reality

Based on local project files and weekly reports:

- the main use case is to connect MetaDynamics to the generative TrpB pipeline
- `GenSLM-230` vs `NdTrpB` is the first concrete mechanistic comparison target
- a `D-Trp` conformational filter is a longer-term goal but its metric is not yet fixed
- benchmark reproduction remains useful as calibration, not as the endpoint

That means the best immediate use of the paper is to build a reusable campaign architecture, not to pretend the project is already a push-button executor.

## Implemented Skill Scheme

The project-level skill scaffold now lives here:

- `.codex/skills/trpb-dynamics-pipeline/SKILL.md`
- `.codex/skills/trpb-dynamics-pipeline/references/workflow-map.md`
- `.codex/skills/trpb-dynamics-pipeline/references/failure-patterns.md`
- `.codex/skills/trpb-dynamics-pipeline/templates/campaign_manifest.template.yaml`
- `.codex/skills/trpb-dynamics-pipeline/templates/campaign_report.template.md`

The same stage-skill scheme is mirrored into `.claude/skills/`.

## How To Use It On This Project

Use the scheme in one of four modes:

1. `benchmark_reproduction`
2. `mechanism_comparison`
3. `physics_filter`
4. `surrogate_bootstrap`

The first two concrete manifests to keep alive are:

- `osuna2019_benchmark_manifest.yaml`
- `genslm230_vs_ndtrpb_manifest.yaml`

That gives the project both a calibration template and a real pipeline-facing campaign template.

## Bottom Line

The main lesson from the paper is not “let AI run everything.”

It is:

> build a versioned boundary between science, execution, and downstream use

That is the right discipline for this project because the main risk is not only runtime failure, but drifting from benchmark calibration into unjustified filtering or model-integration claims.
