# Glossary

## Acronyms
| Term | Meaning | Context |
|------|---------|---------|
| COMM | Communication domain | TrpB residues 97-184 |
| CV | Collective Variable | MetaDynamics biasing coordinate |
| FEL | Free Energy Landscape | 2D energy surface from MetaD |
| SPM | Shortest Path Map | Correlation tool for allosteric pathways |
| PLP | Pyridoxal phosphate | Cofactor covalently bound to K82 |
| DE | Directed Evolution | Arnold lab approach |
| ASR | Ancestral Sequence Reconstruction | Phylogenetic method |
| MSA | Multiple Sequence Alignment | Bioinformatics tool |
| GAFF | General AMBER Force Field | For small molecules/cofactors |
| RESP | Restrained Electrostatic Potential | Charge fitting method |
| PME | Particle-Mesh Ewald | Long-range electrostatics |
| MetaD | Metadynamics | Enhanced sampling method |
| WT-MetaD | Well-Tempered Metadynamics | Convergent variant |

## Reaction Intermediates
| Symbol | Name | COMM state |
|--------|------|-----------|
| E(Ain) | Internal aldimine (resting) | O |
| E(Aex1) | External aldimine | PC |
| E(A-A) | Amino acrylate | C |
| E(Q₂) | Quinonoid (post-indole) | C |
| E(Trp) | Product complex | PC |

## Key PDB Codes
| PDB | What | Role in project |
|-----|------|----------------|
| 1WDW | PfTrpS open | Starting structure + open endpoint for path CV |
| 3CEP | StTrpS closed (Q analogue) | Closed endpoint for path CV |
| 5DVZ | PfTrpB open (Ain) | RMSD reference |
| 5DW0 | PfTrpB PC (Aex1) | Structural comparison |
| 5DW3 | PfTrpB PC (L-Trp) | Structural comparison |
| 4HPX | StTrpS closed (A-A benzimidazole) | CAVER analysis reference |

## Pipeline Stages
| Stage | Role | Tool |
|-------|------|------|
| Profiler | Define research question + manifest | Any AI |
| Librarian | Gather all resources, verify | Any AI |
| Janitor | Clean/prepare simulation inputs | Longleaf |
| Runner | Execute simulations | Longleaf |
| Skeptic | Validate results against criteria | Any AI |
| Journalist | Write up findings | Any AI |
