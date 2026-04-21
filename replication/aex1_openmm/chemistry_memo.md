# PLS chemistry memo — OpenMM-simplified version (B3 gate)

**Status:** approved-by-default-per-PM-directive-2026-04-21 alex051107

**Reframing (2026-04-21):** original draft of this memo was written against the AMBER+RESP+tleap chain and demanded too many decisions. The OpenMM stack the lab actually uses removes several of them. **PDBFixer + Modeller handle the protein, hydrogens, solvent, ions automatically.** **AM1-BCC replaces Gaussian HF/6-31G(d) RESP automatically.** What is left is genuinely small.

## What OpenMM does for free (no PM input)

- Protein missing atoms / missing residues / residue-level pH-7 hydrogens for standard residues of 5DW0 chain A → `PDBFixer.findMissingAtoms / addMissingAtoms / addMissingHydrogens(pH=7.0)`.
- Solvation box, Na⁺ neutralization → `Modeller.addSolvent(forcefield, model='tip3p', padding=1.0*nanometer, ionicStrength=0*molar)`.
- Small-molecule bonded params for PLS → `GAFFTemplateGenerator` (GAFF-2.11) via `openmmforcefields.generators.SystemGenerator`.
- Small-molecule partial charges for PLS → `openff-toolkit` `assign_partial_charges(partial_charge_method='am1bcc')`; no Gaussian, no antechamber.

## Why PLS is a single ligand (not a modified residue)

In the external aldimine state (Aex1), the Schiff base connects **PLP** to the **substrate α-amino group** (serine as free amino acid, not a residue in the protein chain). K82 is a regular, free lysine in 5DW0. So the covalent C4'=N bond is entirely *inside* PLS; **PLS is a closed-valence, ~22-heavy-atom small molecule**, parameterizable as one ligand. No cross-residue covalent stitching is needed. This is why the OpenMM template generator path works here — the case that breaks it (Ain's internal aldimine, covalent to K82 NZ) is not what we have.

## What actually needs PM sign-off (2 items, both RDKit-local)

Both must be decided before constructing the RDKit `Molecule` handed to `SMILES -> mol -> assign_partial_charges(am1bcc)`.

### 1. Net charge of PLS

Default proposal (pending PM confirm):

| fragment | contribution |
|---|---|
| phosphate (fully deprotonated) | −2 |
| pyridine ring N1 (protonated) | +1 |
| Schiff base N (protonated, imine C=N⁺H) | +1 |
| phenolate O3′ (deprotonated at active-site pH) | −1 |
| substrate Ser α-carboxylate (deprotonated) | −1 |
| **net** | **−2** |

Matches Ain charge (−2). Source: Caulkins 2014 ¹³C / ¹⁵N NMR on PfTrpB intermediates (cited in Osuna 2019 SI).

**PM decision required:** confirm −2 and tautomer assumptions above, or correct.

### 2. Protonation of the three titrating sites

- Schiff base N → **protonated** (external aldimine pKa ~ 11; active-site pH 7 → fully protonated).
- Pyridine ring N1 → **protonated** (H-bond to Asp222 backbone / active-site stabilization).
- Phosphate → **−2** (fully deprotonated, pH > phosphate pKa2).

**PM decision required:** confirm or adjust. These get encoded as explicit H atoms + formal charges on the RDKit `Molecule`.

## What does NOT need a decision (crossed off)

- ~~Ligand vs modified residue~~ — PLS is a free ligand (substrate-side Schiff base, not covalent to protein).
- ~~QM fragment / capped fragment definition~~ — AM1-BCC does not need a QM fragment. Runs on the whole PLS molecule.
- ~~Gaussian route line / IOp flags / antechamber options~~ — Gaussian is not in the OpenMM path at all.
- ~~Atom name convention~~ — GAFF2 template generator names internally via RDKit indices; the 5DW0 PDB atom names are only needed to map the coordinates in, which PDBFixer / OpenMM handle via residue template matching.

## Fallback (unlikely)

If GAFF2 templategen for some reason fails on PLS (e.g., RDKit can't perceive the extended Schiff-base + pyridinium π-system cleanly), fall back to SMIRNOFF (`SMIRNOFFTemplateGenerator`, OpenFF 2.x). If that also fails, only then revert to the AMBER chain (Gaussian RESP → antechamber → tleap). Track separately.

## When approved

Re-save this file with items 1 and 2 marked `approved: true` and a PM signature line. Commit to `aex1-openmm-parallel` with message `Aex1 chemistry memo: approved at B3 gate (<date>)`. Only then does B4 (parameterization spike) unblock.

## Sources

- OpenMM docs: `http://docs.openmm.org/` (PDBFixer, Modeller, openmmforcefields)
- openff-toolkit partial charges: `https://docs.openforcefield.org/projects/toolkit/en/stable/api/generated/openff.toolkit.topology.Molecule.html#openff.toolkit.topology.Molecule.assign_partial_charges`
- Caulkins 2014 ¹³C/¹⁵N NMR on TrpB intermediates: cited in Osuna 2019 SI
- Ain analog (internal aldimine, covalent to K82, CHARGE=−2): `replication/parameters/JACS2019_MetaDynamics_Parameters.md` §1 "Ain/LLP Capped Fragment"
