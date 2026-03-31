# Workflow Map: Paper Architecture -> TrpB Dynamics Pipeline

This file maps the architecture from `Scaling Reproducibility` onto the actual TrpB project direction: enhanced sampling as a physics layer for a larger generative pipeline.

## 1. What the paper is actually proposing

The paper does **not** claim that LLMs should invent diagnostics or produce results directly.

It proposes:

- humans freeze a scientific template
- an orchestrator routes work across modular stages
- deterministic code performs the numerically sensitive work
- recurring failures are recorded as reusable rules between runs

That is a workflow architecture, not a single prompt.

## 2. Paper stages vs. this project

| Paper role | Paper responsibility | TrpB project equivalent | Concrete artifact |
|---|---|---|---|
| Orchestrator | route tasks, inspect failures, update knowledge between runs | coordinate campaign framing, setup, execution prep, analysis, and handoff | top-level skill + campaign manifest |
| Profiler | extract metadata and specs | extract campaign facts from papers, weekly reports, and local notes | `campaign_manifest.yaml`, metric spec |
| Librarian | fetch replication package | fetch structures, supplements, assay context, and candidate assets | resource inventory |
| Janitor | repair paths and environment assumptions | normalize directory layout, filenames, manifests, and exports | workspace plan |
| Runner | execute code and export analysis data | stage deterministic commands, analyses, and feature exports | logs, analysis outputs, feature tables |
| Skeptic | apply fixed diagnostics deterministically | validate operational status, scientific status, and downstream readiness | validation report |
| Journalist | generate report | summarize what worked, what failed, what is still unsupported | campaign report |

## 3. What is the fixed template here?

For this project, the fixed template is not just a protocol. It is a campaign definition:

- campaign mode
- research question
- systems under study
- CV and analysis plan
- stack assumptions
- readouts to measure
- validation criteria
- downstream consumer

This must be fixed before automation is trusted.

## 4. Supported campaign modes

Use these four modes:

1. `benchmark_reproduction`
2. `mechanism_comparison`
3. `physics_filter`
4. `surrogate_bootstrap`

These correspond to the current project trajectory:

- calibrate on Osuna systems
- explain `GenSLM-230` vs `NdTrpB`
- define a `D-Trp` filter
- export features for later ML use

## 5. What should not be automated loosely

These need explicit human review:

- whether a benchmark protocol transfers to a new sequence comparison
- whether the chosen CV package captures the biology of the COMM-domain transition
- whether a proposed `D-Trp` metric is actually mechanistic rather than decorative
- whether exported features are comparable enough to support downstream modeling

## 6. What can be automated now

Even before HPC access is ready, the following are good automation targets:

- convert papers and weekly reports into structured manifests
- track missing resources and provenance
- prepare campaign directories
- generate deterministic command plans
- validate required inputs before execution
- write campaign reports and handoff notes

## 7. Current blockers in this project

From local project files and weekly reports:

- Caltech HPC access is still pending
- some benchmark parameters remain literature-derived rather than verbatim-confirmed
- the `D-Trp` geometric criterion is still a hypothesis
- some candidate assets are still pending from JP

So the project is ready for a strong orchestration scaffold, but not yet for a fully autonomous production executor.

## 8. The most transferable lesson from the paper

The most important transferable idea is:

> version the questions, version the artifacts, and version the fixes

For this project, every time a setup issue or interpretive boundary is resolved, record:

- context
- problem
- generalized fix
- impact on future campaigns

That is what lets the workflow scale from benchmark calibration to real generative-pipeline integration.
