---
name: trpb-janitor
description: Normalize the TrpB dynamics-pipeline workspace. Use when preparing campaign directories, standardizing file paths, organizing raw and generated assets, staging inputs for benchmark or comparison runs, or making the project ready for deterministic execution on local or HPC environments.
---

# TrpB Janitor

Prepare a clean, explicit workspace for reproducible dynamics-pipeline work.

## Purpose

Use this skill when the project has:

- scattered files
- ambiguous input/output locations
- path assumptions tied to one machine
- missing separation between raw resources and generated artifacts
- no consistent campaign-level directory boundary

## Outputs

Prefer leaving behind:

- a cleaned directory plan
- explicit input and output locations
- normalized filenames
- a short note describing what was changed

## Rules

1. Keep raw inputs separate from generated outputs.
2. Prefer relative, project-local paths.
3. Never rename or move files without recording the change in a note or report.
4. Do not alter scientific content while cleaning execution layout.
5. Keep benchmark, comparison, and export artifacts separate.

## For This Project

Good Janitor tasks include:

- preparing `repro-workflow/` subdirectories
- deciding where manifests, run logs, validation reports, and exported features belong
- staging PDBs, topology files, PLUMED files, and run logs consistently
- preparing a clean `campaigns/<campaign_id>/inputs|configs|runs|analysis|exports|reports` separation

## Non-Goals

- Do not reinterpret protocol parameters.
- Do not declare a workspace “ready” if required external assets are still missing.
