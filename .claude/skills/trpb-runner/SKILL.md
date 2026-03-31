---
name: trpb-runner
description: Generate or execute deterministic run steps for the TrpB dynamics pipeline. Use when staging benchmark or comparison commands, planning Slurm jobs, creating dry-run command sequences, exporting trajectory features, or moving from a frozen campaign manifest to concrete execution steps.
---

# TrpB Runner

Move from a frozen campaign manifest to explicit execution or analysis steps.

## Purpose

Use this skill when the scientific template is already frozen and the task is now:

- build a deterministic command list
- plan a validation ladder
- stage a dry run
- execute a local preparation or analysis step
- collect the outputs of an actual run
- export traceable features for downstream use

## Validation Ladder

Prefer this order:

1. toy or tutorial enhanced-sampling validation
2. published TrpB benchmark
3. pairwise comparison campaign
4. candidate-filter or surrogate-export batch

Do not jump to production if earlier validation artifacts do not exist.

## Rules

1. Never claim a run succeeded without concrete artifacts on disk.
2. Use the frozen campaign manifest as the source of truth.
3. Distinguish between:
   - command plan
   - dry run
   - executed run
   - exported analysis product
4. If HPC is unavailable, generate a run plan instead of pretending execution happened.
5. Use comparable preparation and analysis settings across systems in a comparison campaign.

## Good Outputs

- staged command list
- Slurm job sketch
- artifact checklist
- run folder containing logs and outputs
- feature table with provenance

## Non-Goals

- Do not rewrite scientific assumptions inside the execution stage.
- Do not merge environment success with scientific success.
