---
name: trpb-skeptic
description: Validate TrpB dynamics-pipeline artifacts and separate operational success from scientific validity and downstream readiness. Use when checking HILLS files, CV traces, FES outputs, feature exports, manifest compliance, or when deciding whether a campaign failed operationally, scientifically, or only at the integration layer.
---

# TrpB Skeptic

Validate outputs against the frozen campaign, not against wishful interpretation.

## Purpose

Use this skill when asking:

- Did the expected artifacts actually get produced?
- Did the run behave sanely?
- Is this an operational issue, a scientific issue, or an integration-readiness issue?

## Inputs

- protocol manifest
- campaign manifest
- run logs
- generated artifacts
- validation criteria from the project protocol

## Outputs

Prefer leaving behind:

- a validation note
- a pass/fail table
- a root-cause statement

## Rules

1. Check artifacts before interpretation.
2. Treat “it ran” and “it is scientifically acceptable” as different claims.
3. If a criterion is not yet well defined, say so explicitly.
4. Record recurring validation failures in `failure-patterns.md`.
5. If a downstream filter or exported feature is proposed, check that its provenance is explicit.

## Typical Checks

- expected files exist
- no NaN or obvious divergence
- CV range is plausible
- HILLS deposition is happening
- FES output exists and is not obviously corrupted
- interpretation is consistent with the chosen reference-state logic
- compared systems are actually comparable under the same setup
- downstream claim does not exceed the frozen campaign scope

## Output Style

Be explicit:

- `Operationally valid`
- `Operationally failed`
- `Scientifically uncertain`
- `Scientifically inconsistent with manifest`
- `Integration not yet justified`
