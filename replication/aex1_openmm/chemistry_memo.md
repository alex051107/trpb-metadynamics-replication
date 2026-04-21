# PLS chemistry memo (PLACEHOLDER — B3 gate, PM sign-off required)

**Status:** unfilled. Do NOT proceed to B4 parameterization until this memo is populated, reviewed by PM, and marked `approved`.

**Purpose:** pin down the chemistry decisions that dominate parameterization validity. Getting any one of these wrong silently corrupts the entire pilot, and will not be caught by downstream assertions.

## Open decisions

### 1. Ligand identity and connectivity

- PDB residue code: `PLS` (from 5DW0 chain A).
- Composition: PLP cofactor covalently linked to serine side chain through an **external aldimine** (C=N Schiff base between PLP C4A and serine backbone N).
- Heavy-atom count (from PDB, `replication/parameters/JACS2019_MetaDynamics_Parameters.md`): 22 per chain.
- In the Ain system, LLP bonds covalently to K82 NZ (internal aldimine); **in Aex1, K82 is free Lys**, and PLS carries the Schiff base to serine instead. Confirm this wiring against the actual 5DW0 coordinates before parameterization.

### 2. Net charge

- Literature prior: **-2** (phosphate fully deprotonated = −2; Schiff-base N protonated = +1; pyridine ring N protonated or not depending on tautomer; serine carboxylate −1 counts separately from ligand).
- Alternative readings exist depending on tautomer and whether serine α-carboxylate is part of the ligand or a separate terminal.
- **Decision required:** PM confirms literature reference (Caulkins 2014 NMR, as with Ain? Or Aex1-specific NMR?) and the tautomer assumption.

### 3. Protonation states

- Schiff-base N: **expected protonated** at physiological pH for external aldimine (pKa ~ 11 literature).
- Pyridine ring N: **expected protonated** in active site (H-bond to Asp).
- Phosphate: **expected −2** (fully deprotonated).
- Serine hydroxyl: expected neutral.
- **Decision required:** PM signs off on each of the four.

### 4. QM fragment definition (for GAFF+RESP fallback path B4b)

- Capped fragment: ACE-PLS-NME? Or keep serine backbone explicit? Ain used ACE-LLP-NME; Aex1 likely parallels but needs explicit confirmation since the covalent partner changed.
- Total capped atom count: projected ~52-56 (vs 54 for Ain capped).
- Gaussian route line: same as Ain `# HF/6-31G(d) SCF=Tight Pop=MK IOp(6/33=2,6/42=6)` (no `IOp(6/50=1)` per FP-013)?

### 5. Ligand-vs-capped-residue treatment in system build

- Option A: treat PLS as a single ligand separate from the protein, K82 as normal Lys.
- Option B: treat PLS as a modified serine residue bonded into the protein chain.
- Each has different implications for GAFF generator vs. manual force-field merging.
- **Decision required:** PM picks one; defensibility to a reviewer matters more than minor ergonomics.

### 6. Atom name convention

- 5DW0 PDB uses PLS atom naming. Confirm atom names match what `openmmforcefields.generators.SystemGenerator` expects (GAFF2 tolerates arbitrary names; RESP does not).
- For fallback path, atom names must match `Ain_gaff.mol2`-style convention; may need a renaming pass.

## Deliverable when approved

Re-save this file with the null fields filled, status `approved`, and a clear authorship line. Commit to branch `aex1-openmm-parallel` with a message `Aex1 chemistry memo: approved at B3 gate (<date>)`.

## Related artifacts

- Ain analog: `replication/parameters/JACS2019_MetaDynamics_Parameters.md` §1 "Ain/LLP Capped Fragment" — 2026-03-31 ACE-LLP-NME, charge −2, multiplicity 1.
- 5DW0 PDB: `/work/users/l/i/liualex/AnimaLab/structures/5DW0.pdb` (assumed; verify before use).

## Explicit non-scope

- This memo does NOT prescribe parameterization commands. It decides chemistry. Parameterization (B4 / B4b) is downstream and must read this memo as approved input.
