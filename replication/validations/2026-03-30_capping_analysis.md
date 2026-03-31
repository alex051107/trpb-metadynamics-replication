# ACE/NME Capping Analysis for LLP Ain RESP Fitting

> **Date**: 2026-03-30
> **Author**: Codex (executor)
> **Pipeline Stage**: 3 (Runner)
> **Verdict**: CAPPING REQUIRED

## 1. Question

Does the Ain intermediate (`LLP`, internal aldimine from `5DVZ`) need ACE/NME capping before the Gaussian RESP calculation, and if so, what should be prepared locally before the Longleaf job is submitted?

## 2. Files Read First

- [CLAUDE.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/CLAUDE.md)
- [replication/validations/failure-patterns.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/validations/failure-patterns.md)
- [replication/validations/2026-03-30_plp_protonation_literature_review.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/validations/2026-03-30_plp_protonation_literature_review.md)
- [project-guide/PLP_SYSTEM_SETUP_LOGIC_CHAIN.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/PLP_SYSTEM_SETUP_LOGIC_CHAIN.md)

## 3. Decision

Yes. `LLP` should be RESP-fit as an **ACE-LLP-NME capped fragment**, not as a bare extracted residue.

The reason is structural, not optional style:

1. `LLP` is not a free ligand. It is a **polymer-linked modified amino-acid residue** that keeps the K82 backbone atoms `N`, `CA`, `C`, `O`.
2. In [5DVZ.pdb](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/structures/5DVZ.pdb), the peptide-chain links are explicit:
   - `LINK C HIS A 81 -> N LLP A 82`
   - `LINK C LLP A 82 -> N THR A 83`
3. The intended AMBER integration path is to convert LLP into a **library residue with head=`N` and tail=`C`**, then load it into `tleap` as part of the protein chain, not as an isolated small molecule. That is the canonical path documented in [project-guide/PLP_SYSTEM_SETUP_LOGIC_CHAIN.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/project-guide/PLP_SYSTEM_SETUP_LOGIC_CHAIN.md).
4. If the bare extracted residue is fit without caps, the electrostatics at the backbone `N` and `C/O` boundaries reflect broken peptide bonds instead of the protein environment those atoms will have in `ff14SB`.

## 4. Standard AMBER Guidance

Official AMBER tutorials support the same logic:

- AMBER advanced tutorial section 1 states that when a covalent bond is broken for charge fitting, the bond should be capped before geometry optimization, and for proteins the standard cap procedure is to use **ACE or NME**:
  - https://ambermd.org/tutorials/advanced/tutorial1/section1.php
- AMBER basic tutorial A26 then shows the downstream step for a polymer-linked modified residue: after charge derivation, strip the temporary terminal atoms and define the residue with explicit `HEAD_NAME` and `TAIL_NAME` for use in the protein chain:
  - https://ambermd.org/tutorials/basic/tutorial5/index.php

That matches the local project logic chain: cap for QM/RESP, then build the final LLP residue definition for `tleap`.

## 5. Boundary Atoms and Cap Choice

For Ain in chain A of `5DVZ`, the relevant peptide-boundary atoms are:

- Previous residue anchor: `HIS 81` backbone `CA`, `C`, `O`
- Target residue: `LLP 82` backbone `N`, `CA`, `C`, `O`
- Next residue anchor: `THR 83` backbone `N`, `CA`

The local capped fragment therefore uses:

- **ACE cap on the N side**:
  - methyl carbon seeded from `HIS81 CA`
  - carbonyl `C/O` seeded from `HIS81 C/O`
- **NME cap on the C side**:
  - amide `N` seeded from `THR83 N`
  - methyl carbon seeded from `THR83 CA`

This preserves the peptide-bond geometry already present in the crystal structure and only uses the caps as a starting geometry for Gaussian optimization.

## 6. Charge and Multiplicity

The cap decision does **not** change the fragment charge assignment.

- Ain/LLP protonation state from [2026-03-30_plp_protonation_literature_review.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/validations/2026-03-30_plp_protonation_literature_review.md): **charge = -2**, multiplicity `1`
- ACE: neutral
- NME: neutral
- Final capped Gaussian input: **`-2 1`**

No stop-condition escalation was triggered on charge.

## 7. Prepared Files

Because the current Longleaf files under `/work/users/l/i/liualex/AnimaLab/parameterization/ain/` are not readable from this workspace, I prepared repo-local replacements:

- Gaussian input:
  - [replication/parameters/resp_charges/ain/LLP_ain_resp_capped.gcrt](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/parameters/resp_charges/ain/LLP_ain_resp_capped.gcrt)
- Slurm submission script:
  - [replication/parameters/resp_charges/ain/submit_gaussian_capped.slurm](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/parameters/resp_charges/ain/submit_gaussian_capped.slurm)
- Reproducible local generator:
  - [scripts/build_llp_ain_capped_resp.py](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/scripts/build_llp_ain_capped_resp.py)

The generator builds a **54-atom ACE-LLP-NME fragment** directly from `5DVZ` coordinates and standard H-placement rules, then writes a Gaussian input with:

- method: `HF/6-31G(d)`
- route keywords: `SCF=tight Pop=MK iop(6/33=2) iop(6/42=6) opt`
- charge/multiplicity: `-2 1`

## 8. Why I Did Not Edit `/work/.../LLP_ain_resp.gcrt` Directly

That file is outside the readable local workspace in this session. Editing it directly without reading it would violate the local evidence rule in [replication/validations/failure-patterns.md](/Users/liuzhenpeng/Desktop/UNC/暑研%20/Caltech%20Interview/tryp%20B%20project/replication/validations/failure-patterns.md): do not write structure data from memory or assumptions.

The repo-local replacements are therefore the correct executor output for review. After review, they can be copied to the matching Longleaf working directory and used instead of the uncapped file.

## 9. Next Concrete Action

Do **not** submit the job yet.

Next:

1. Review the repo-local capped `.gcrt` and `.slurm` files.
2. Copy them to `/work/users/l/i/liualex/AnimaLab/parameterization/ain/`.
3. Replace the uncapped `LLP_ain_resp.gcrt` with the capped version.
4. Submit only after Claude/PM confirm that the cap-seeding strategy is acceptable.
