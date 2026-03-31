# MetaDynamics Project Intent

## Short Version

This project is not a stand-alone metadynamics reproduction exercise.

Its long-term goal is to use enhanced sampling as a physics layer inside a larger generative TrpB pipeline.

The work therefore has two connected layers:

1. **Calibration layer:** reproduce or benchmark published TrpB dynamics so the workflow is scientifically trustworthy.
2. **Integration layer:** use enhanced-sampling outputs to explain model behavior, design filters, and later export data for surrogate modeling.

Benchmark reproduction matters, but it is a support mode rather than the final destination.

## Long-Term Research Goal

The key scientific question is what dynamics can tell us that sequence generation and static structure prediction cannot.

Current project documents and weekly reports point to three concrete integration targets:

- explain the functional divergence between `GenSLM-230` and `NdTrpB` despite nearly identical predicted structures
- test whether MetaDynamics can become a physics-based conformational filter for `D-Trp` selectivity
- eventually export trajectory-derived features for a faster surrogate model that can score larger candidate libraries

That is the real project boundary. Proposal-era framing is no longer the source of truth.

## Near-Term Goal

Before any filtering or surrogate work is credible, the project needs one trustworthy enhanced-sampling workflow.

In practice that means:

- choosing a campaign mode explicitly
- freezing a reviewed campaign manifest before execution
- keeping benchmark calibration separate from novel scientific claims
- validating outputs with explicit checks rather than narrative interpretation

## Supported Campaign Modes

This project should be treated as a small portfolio of related campaign types:

1. **Benchmark reproduction**
   - validate setup on literature systems such as Osuna 2019
2. **Mechanistic comparison**
   - compare sequence pairs such as `GenSLM-230` vs `NdTrpB`
3. **Physics-based filter design**
   - define and test a dynamics-derived criterion for `D-Trp` selectivity
4. **Surrogate data bootstrap**
   - export traceable features from trajectories for later ML use

Only the first mode is about reproduction alone.

## Why the Reproducibility Architecture Still Matters

This project has the same structural risk that `Scaling Reproducibility` is trying to control:

- some scientific facts are explicit in literature
- some decisions remain hypotheses or local inferences
- the compute environment is heavy
- the gap between “runnable” and “scientifically meaningful” is large

The paper is useful here because it enforces a boundary between:

- **scientific choices**
- **execution choices**
- **downstream integration claims**

That boundary is what prevents a workflow from drifting from calibration into over-interpretation.

## Operational Meaning

When building skills or automation for this project:

- freeze the research question, system set, readouts, and validation criteria before execution
- automate retrieval, normalization, staging, artifact checks, and reporting
- keep the numerically sensitive path in deterministic code or audited commands
- record recurring failures as reusable rules
- never silently upgrade a hypothesis or inferred parameter into a confirmed fact
