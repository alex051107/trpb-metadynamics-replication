---
name: trpb-profiler
description: Extract structured campaign facts for the TrpB dynamics pipeline. Use when converting papers, weekly reports, setup notes, or project planning documents into campaign manifests, metric definitions, comparison briefs, or fact-vs-hypothesis inventories.
---

# TrpB Profiler

Convert unstructured scientific material into a frozen campaign definition for the TrpB dynamics pipeline.

Read these references first:

- [METADYNAMICS_PROJECT_INTENT.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/METADYNAMICS_PROJECT_INTENT.md)
- [PROJECT_PROTOCOL.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/repro-workflow/PROJECT_PROTOCOL.md)
- [osuna2019_benchmark_manifest.yaml](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/repro-workflow/manifests/osuna2019_benchmark_manifest.yaml)
- [genslm230_vs_ndtrpb_manifest.yaml](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/repro-workflow/manifests/genslm230_vs_ndtrpb_manifest.yaml)

## Purpose

Use this skill to answer:

- What is the actual campaign mode?
- What is explicitly stated in the paper or weekly report?
- What is only inferred, hypothesized, or still unresolved?
- Which readouts are fixed enough to enter a manifest?
- Which uncertainties still require human review?

## Inputs

- paper PDFs
- weekly reports
- `MetaDynamics_Setup_Notes.md`
- `RESEARCH_SUMMARY.txt`
- flowchart or pipeline docs

## Outputs

Prefer leaving behind one of:

- updated campaign manifest
- metric-spec note
- fact-vs-hypothesis note
- comparison brief
- structured JSON or YAML summary if a downstream stage needs it

## Rules

1. Separate explicit fact from inference or hypothesis.
2. Preserve uncertainty labels.
3. Do not silently upgrade a guessed parameter or speculative metric into a confirmed one.
4. If multiple local docs disagree, surface the conflict explicitly.
5. Name the downstream consumer of the campaign, not just the science question.

## Working Pattern

1. Read the relevant source material.
2. Extract:
   - campaign mode
   - research question
   - systems under study
   - reference structures
   - CV design
   - software stack
   - measurable readouts
   - validation criteria
   - downstream consumer
3. Mark each extracted item as:
   - explicit
   - inferred
   - hypothesis
   - unresolved
4. Write results into the current manifest or a campaign note.
