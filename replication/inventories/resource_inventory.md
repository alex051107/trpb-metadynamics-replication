# Librarian Resource Inventory
> Campaign: osuna2019_benchmark_reproduction
> Last updated: 2026-03-30

## PDB Structures

| PDB | Description | Role in campaign | Status | Local path | Longleaf path |
|-----|------------|-----------------|--------|-----------|---------------|
| 5DVZ | Holo TrpB from P. furiosus (Ain, Open) | Reference; LLP residue (PLP-K82 Schiff base, 24 atoms/chain) | ✅ Local + Longleaf | `replication/structures/5DVZ.pdb` | `/work/.../AnimaLab/structures/5DVZ.pdb` |
| 5DW0 | TrpB + L-Ser external aldimine (Aex1, PC) | Reference; PLS residue (PLP-Serine, 22 atoms/chain) | ✅ Local + Longleaf | `replication/structures/5DW0.pdb` | `/work/.../AnimaLab/structures/5DW0.pdb` |
| 5DW3 | TrpB + product L-Trp (E(Trp), PC) | Reference; LLP residue (same as 5DVZ) | ✅ Local + Longleaf | `replication/structures/5DW3.pdb` | `/work/.../AnimaLab/structures/5DW3.pdb` |
| 1WDW | Open PfTrpS (alpha-beta heterodimer) | Starting structure; open endpoint for path CV | ✅ Longleaf only | — | `/work/.../AnimaLab/structures/1WDW.pdb` |
| 3CEP | StTrpS closed state (Q analogue) | Closed endpoint for path CV | ✅ Longleaf only | — | `/work/.../AnimaLab/structures/3CEP.pdb` |
| 4HPX | StTrpS aminoacrylate (A-A intermediate) | Structural template for A-A; 0JO residue | ✅ Longleaf only | — | `/work/.../AnimaLab/structures/4HPX.pdb` |
| 5IXJ | Additional reference | Supplementary | ✅ Longleaf only | — | `/work/.../AnimaLab/structures/5IXJ.pdb` |
| 4HN4 | TrpS closed state (Niks et al. 2013) | Additional C state reference | ❌ Not downloaded | — | — |
| 1V8Z | TrpB resting state (Hioki et al. 2004) | Historical reference | ❌ Not downloaded | — | — |

### PLP Residue Names (verified from actual PDB files, 2026-03-30)

| PDB | Intermediate | Residue name | Full name | Heavy atoms | Note |
|-----|-------------|-------------|-----------|-------------|------|
| 5DVZ | Ain | **LLP** | N6-pyridoxyl-lysine-5'-monophosphate | 24 | PLP-K82 Schiff base (covalent, internal aldimine) |
| 5DW0 | Aex1 | **PLS** | Pyridoxal-5'-phosphate-L-serine | 22 | External aldimine (K82 free) |
| 4HPX | A-A | **0JO** | Aminoacrylate-PLP adduct | 21 | From S. typhimurium, structural template only |
| — | Q2 | **unknown** | Quinonoid intermediate | — | No crystal structure available |

## Papers (PDF)

| Paper | PDF status | SI status | Reading notes | Deep annotation |
|-------|-----------|-----------|---------------|-----------------|
| JACS 2019 (Maria-Solano et al.) | ✅ `papers/maria-solano2019.pdf` | ✅ `papers/ja9b03646_si_001.pdf` | ✅ `papers/reading-notes/JACS2019_ReadingNotes.md` | ✅ `papers/annotations/JACS2019_DeepAnnotation_v2.html` |
| ACS Catal 2021 (Maria-Solano et al.) | ✅ In Zotero | ✅ Checked | ✅ `papers/reading-notes/ACSCatal2021_ReadingNotes.md` | ✅ `papers/annotations/ACSCatal2021_DeepAnnotation.html` |
| NatComm 2026 (Lambert et al.) | ✅ In Zotero | Not critical | ✅ `papers/reading-notes/NatCommun2026_ReadingNotes.md` | ✅ `papers/annotations/NatCommun2026_DeepAnnotation.html` |
| Protein Science 2025 (Kinateder et al.) | ✅ In Zotero | Not critical | ✅ `papers/reading-notes/ProtSci2025_ReadingNotes.md` | ✅ `papers/annotations/ProtSci2025_DeepAnnotation.html` |

### SI Extraction Status (JACS 2019)

| Item | Status | Source |
|------|--------|--------|
| Force field | ✅ **ff14SB** | SI p.S2 |
| Water model | ✅ **TIP3P**, cubic box, 10 A buffer | SI p.S2 |
| PLP parameterization method | ✅ **GAFF + RESP at HF/6-31G(d) via Gaussian09** | SI p.S2 |
| MetaDynamics parameters | ✅ All extracted | `replication/parameters/JACS2019_MetaDynamics_Parameters.md` |
| Heating protocol | ✅ 7x50ps, 0→350K, NVT, Langevin | SI p.S2 |
| Equilibration | ✅ 2ns NPT, 1atm, 350K, 2fs | SI p.S2 |
| Production | ✅ 500ns NVT, 350K, 2fs, PME, 8A cutoff | SI p.S2-S3 |
| Path CV definition | ✅ 15 frames, Calpha of COMM (97-184) + base (282-305) | SI p.S3 |

### SI Gaps Identified (2026-03-30)

| Gap | Severity | Status |
|-----|----------|--------|
| Protonation states (K82, PLP, His residues) | HIGH | **Open -- needs PI input** |
| PLP-K82 covalent bond treatment during RESP | HIGH | **Open -- needs PI input** |
| AMBER→GROMACS conversion method | HIGH | **Open -- plan to use ParmEd** |
| Missing residues in 1WDW | MEDIUM | **Open -- need to check PDB REMARK 465** |
| 7 heating steps vs 6 restraint values | LOW | Assume 7th step uses last value (10 kcal/mol/A2) |
| Minimization step counts | LOW | Use 5000 steps (standard) |
| Barostat type | LOW | Berendsen (AMBER default) |
| Trajectory save frequency | LOW | Use 10 ps (standard) |
| Salt concentration | LOW | Neutralizing ions only |

## Software Stack

| Component | Paper version | Our version | Status | Location |
|-----------|-------------|-------------|--------|----------|
| AMBER | AMBER16 | **AMBER 24p3** | ✅ Verified | `module load amber/24p3` |
| GROMACS | GROMACS 5.1.2 | **GROMACS 2026.0** | ✅ Verified (PLUMED-patched) | `conda activate trpb-md` |
| PLUMED | PLUMED 2 | **PLUMED 2.9** | ✅ Verified | `conda activate trpb-md` |
| Gaussian | Gaussian09 | **Gaussian 16c02** | ✅ Verified | `module load gaussian/16c02` |
| antechamber | AmberTools 16 | **AmberTools 24p3** | ✅ Verified | Included in amber/24p3 |
| parmchk2 | AmberTools 16 | **AmberTools 24p3** | ✅ Verified | Included in amber/24p3 |
| tleap | AmberTools 16 | **AmberTools 24p3** | ✅ Verified | Included in amber/24p3 |
| reduce (H addition) | — | **AmberTools 24p3** | ✅ Verified | Included in amber/24p3 |
| MDAnalysis | — | **installing** | ⏳ conda install in progress | trpb-md env |
| BioPython | — | **installing** | ⏳ conda install in progress | trpb-md env |

## Scripts

| Script | Purpose | Status | Location (local) | Location (Longleaf) |
|--------|---------|--------|-------------------|---------------------|
| parameterize_plp.sh | PLP GAFF+RESP parameterization | ✅ Rewritten v2 (754 lines) | `replication/scripts/parameterize_plp.sh` | `/work/.../AnimaLab/scripts/parameterize_plp.sh` |
| generate_path_cv.py | 15-frame O→C reference path | ✅ Ready | `replication/scripts/generate_path_cv.py` | `/work/.../AnimaLab/scripts/generate_path_cv.py` |
| toy-alanine/ | Alanine dipeptide MetaD test | ✅ Completed | `replication/scripts/toy-alanine/` | — |
| plumed_trpb_metad.dat | Multi-walker MetaD template | ✅ Ready | `replication/scripts/` | — |
| plumed_trpb_metad_single.dat | Single-walker MetaD template | ✅ Ready | `replication/scripts/` | — |

## Intermediate Files (on Longleaf)

| File | Purpose | Status | Path |
|------|---------|--------|------|
| LLP_chainA.pdb | Extracted LLP from 5DVZ chain A | ✅ Created | `/work/.../AnimaLab/parameterization/ain/LLP_chainA.pdb` |
| LLP_chainA_H.pdb | LLP with hydrogens (reduce) | ✅ Created (42 atoms) | `/work/.../AnimaLab/parameterization/ain/LLP_chainA_H.pdb` |
| LLP_ain_gas.mol2 | Gasteiger charges (for atom typing only) | ✅ Created | `/work/.../AnimaLab/parameterization/ain/LLP_ain_gas.mol2` |
| LLP_ain_bcc.mol2 | BCC charges (no H, wrong atom types) | ⚠️ Created but unreliable | `/work/.../AnimaLab/parameterization/ain/LLP_ain_bcc.mol2` |
| LLP_ain_resp.gcrt | Gaussian 16 RESP input | ✅ Created | `/work/.../AnimaLab/parameterization/ain/LLP_ain_resp.gcrt` |
| AIN.frcmod | Missing parameters (from BCC, needs redo) | ⚠️ Unreliable | `/work/.../AnimaLab/parameterization/ain/AIN.frcmod` |
| submit_gaussian.slurm | Slurm script for Gaussian RESP | ✅ Created, NOT submitted | `/work/.../AnimaLab/parameterization/ain/submit_gaussian.slurm` |

## Blockers Summary (updated 2026-03-30)

| # | Blocker | Severity | Status |
|---|---------|----------|--------|
| 1 | ~~JACS 2019 SI not downloaded~~ | ~~Critical~~ | **Resolved** -- SI downloaded, all parameters extracted |
| 2 | PLP protonation states unconfirmed | **High** | **Open** -- needs PI meeting |
| 3 | ~~AMBER + PLUMED on Longleaf not verified~~ | ~~Medium~~ | **Resolved** -- all verified |
| 4 | ~~Path CV reference structures not confirmed~~ | ~~Medium~~ | **Resolved** -- confirmed from SI |
| 5 | ~~Additional PDB structures~~ | ~~Low~~ | **Resolved** -- 3CEP, 4HPX, 1WDW downloaded |
| 6 | BCC charges fail for PLP (SCF non-convergence) | **Medium** | **Open** -- must use RESP/Gaussian path |
| 7 | Q2 intermediate has no crystal structure | **Medium** | **Open** -- needs PI guidance |
| 8 | MDAnalysis/BioPython not yet installed on Longleaf | **Low** | **In progress** -- conda install running |
