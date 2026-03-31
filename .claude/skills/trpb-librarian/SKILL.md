---
name: trpb-librarian
description: Gather and audit external resources for the TrpB dynamics pipeline. Use when fetching PDB structures, supplementary information, candidate assets, lab references, assay context, or when building a resource inventory for benchmark, comparison, or filter campaigns.
---

# TrpB Librarian

Use this skill to make the project's external dependencies explicit and auditable.

## Purpose

This skill answers:

- Which resources are already local?
- Which need to be downloaded?
- Which are missing or paywalled?
- Which URLs should be considered authoritative?
- Which assets are benchmark-only versus pipeline-facing?

## Inputs

- DOI
- PDB IDs
- supplementary URLs
- lab or paper references

## Outputs

Prefer leaving behind:

- a resource inventory note
- a status table of available vs missing resources
- explicit local file paths for downloaded structures or papers
- provenance for candidate or assay assets

## Rules

1. Prefer authoritative sources over secondary mentions.
2. Record missing resources explicitly instead of guessing.
3. Keep a paper-first and DOI-first retrieval strategy.
4. Distinguish:
   - available locally
   - available remotely
   - unavailable or access-restricted
5. Record how each resource will be used in the current campaign.

## Resource Priorities

For benchmark campaigns, prioritize:

- RCSB PDB entries
- paper supplementary methods
- Osuna lab pages
- PLUMED documentation or PathCV examples

For comparison or filter campaigns, prioritize:

- lab-provided sequence or structure assets
- exact identifiers for `GenSLM-230`, `NdTrpB`, and candidate proteins
- assay summaries or internal notes that define the biological question
- any prior preparation scripts or parameter files that should be reused

## Good Outputs

- “These structures are present locally; these are still missing.”
- “The SI link exists but exact parameter extraction is not yet confirmed.”
- “This comparison can be framed now, but candidate-specific assets are still missing.”
