# Dynamics Pipeline Protocol

This file is the project-level protocol for the enhanced-sampling layer of the TrpB generative pipeline.

## 1. Core Rule

Separate:

- **scientific judgment**
- **execution automation**
- **integration claims**

Scientific judgment includes:

- campaign mode
- research question
- system choice
- CV design
- force-field and solvent assumptions
- what counts as a scientifically meaningful readout

Execution automation includes:

- resource retrieval
- path normalization
- manifest filling
- command staging
- artifact collection
- feature export
- report generation

Integration claims include:

- whether a signal is ready to compare `GenSLM-230` and `NdTrpB`
- whether a proposed `D-Trp` criterion is measurable and defensible
- whether an exported feature table is reliable enough to feed a later surrogate or scoring workflow

Do not let these three layers collapse into one another.

## 2. Freeze a Campaign Manifest

Before any run or analysis step, freeze the work in a manifest.

At minimum, the manifest must specify:

- campaign id
- campaign mode
- research question
- systems under study
- CV or analysis definition
- simulation and analysis stack
- readouts to measure
- validation criteria
- downstream consumer of the result
- known blockers

Do not silently change the manifest during execution.

## 3. Supported Campaign Modes

Use one of these modes explicitly:

1. `benchmark_reproduction`
2. `mechanism_comparison`
3. `physics_filter`
4. `surrogate_bootstrap`

If a task spans more than one mode, split it into multiple manifests.

## 4. Stage Order

Use this order:

1. `Profiler`
2. `Librarian`
3. `Janitor`
4. `Runner`
5. `Skeptic`
6. `Journalist`

Do not skip to `Runner` if campaign facts, system assets, or success criteria are still ambiguous.

## 5. Artifact Rule

Every stage writes explicit outputs.

Preferred locations:

- `repro-workflow/manifests/`
- `repro-workflow/inventories/`
- `repro-workflow/runs/`
- `repro-workflow/validations/`
- `repro-workflow/reports/`
- `repro-workflow/exports/`

Do not rely on hidden state or memory of a previous conversation.

## 6. Explicit Fact vs Hypothesis

Always distinguish:

- explicit literature fact
- local project assumption
- mechanistic hypothesis
- unresolved question

If a parameter or metric is inferred rather than explicitly confirmed, label it as such in both the manifest and the report.

## 7. Failure Handling

When something fails:

1. detect the anomaly
2. identify root cause
3. generalize the fix if appropriate
4. record it in `failure-patterns.md`

Do not apply a one-off fix without documenting it.

## 8. Validation Rule

A campaign is not “successful” merely because code ran.

Use `Skeptic` to separate:

- `operational validity`
- `scientific validity`
- `integration readiness`

Examples:

- a benchmark run can be operationally valid but scientifically uncertain
- a pairwise comparison can be scientifically interesting but not yet safe to feed downstream
- a feature export can exist on disk but still fail provenance or comparability checks

## 9. Human Review Boundary

Human review is required when:

- a new scientific assumption is introduced
- a metric is promoted from hypothesis to decision rule
- a benchmark-calibration choice is reused for a novel sequence
- an execution fix might change scientific interpretation
- a proposed downstream score could influence candidate selection

## 10. Preferred Near-Term Priority

Given the current project state, prioritize:

- benchmark calibration on literature systems
- explicit framing of the `GenSLM-230` vs `NdTrpB` comparison campaign
- a written hypothesis for the `D-Trp` conformational criterion
- traceable feature-export planning for later surrogate work

Do not present the project as fully automated while HPC access, candidate assets, and the `D-Trp` metric definition are still incomplete.
