# Reading Notes: RFDiffusion, RFdiffusion3 (RFD3), and LigandMPNN

**Prepared for:** TrpB MetaDynamics replication project — Yu Zhang (Ramanathan Lab) pipeline context
**Date:** 2026-04-05
**Relevance:** In the Ramanathan Lab pipeline, Yu Zhang uses RFDiffusion/RFD3 to generate protein backbones and LigandMPNN to design sequences around the PLP cofactor. Zhenpeng handles downstream MD validation of these designed sequences.

---

## Paper 1: RFdiffusion

### Paper Info

| Field | Value |
|-------|-------|
| Title | De novo design of protein structure and function with RFdiffusion |
| Authors | Joseph L. Watson, David Juergens, Nathaniel R. Bennett, Brian L. Trippe, Jason Yim, Helen E. Eisenach, Woody Ahern, Andrew J. Borst, Robert J. Ragotte, Lukas F. Milles, Basile I.M. Wicky, Nikita Hanikel, Samuel J. Pellock, Alexis Courbet, William Sheffler, Jue Wang, Preetham Venkatesh, Isaac Sappington, Susana Vázquez Torres, Anna Lauko, Valentin De Bortoli, Emile Mathieu, Sergey Ovchinnikov, Regina Barzilay, Tommi S. Jaakkola, Frank DiMaio, Minkyung Baek, David Baker |
| Venue | Nature |
| Year | 2023 |
| PMID | 37433327 |
| DOI | 10.1038/s41586-023-06415-8 |
| Lab | Baker Lab, Institute for Protein Design, University of Washington |

---

### What Problem Does It Solve?

Traditional protein design methods (Rosetta-based hallucination, fragment assembly) are slow, require extensive expert guidance, and fail at high rates — it was common to test tens of thousands of designs before finding one functional protein. There was no principled generative model that could sample diverse, designable protein backbones conditioned on complex structural constraints (motif scaffolding, symmetric assemblies, binding targets).

RFdiffusion provides a general-purpose diffusion-based framework for *de novo* protein backbone generation, capable of producing functional proteins at dramatically higher success rates.

---

### How Does It Work?

#### Core Approach: Denoising Diffusion on SE(3)

RFdiffusion adapts the RoseTTAFold (RF) structure prediction network into a denoising diffusion model:

1. **Forward process**: Protein backbone frames (Cα positions + residue orientations) are progressively noised. Translations use standard Gaussian noise; rotations use IGSO₃ (isotropic Gaussian on SO(3)) to maintain rotational symmetry.

2. **Reverse process (denoising)**: A fine-tuned RoseTTAFold network predicts the clean structure from a noisy intermediate. The model performs T denoising steps to recover a protein backbone from pure noise.

3. **Representation**: Each residue is represented as a rigid-body frame in SE(3) — position (3D translation) + orientation (SO(3) rotation matrix). This is the same representation used in AlphaFold2.

> Why SE(3)? Protein conformations are physically invariant to global rotation and translation. Modeling in SE(3) ensures the generative model respects this symmetry, producing physically valid structures regardless of reference frame.

#### Conditioning Mechanisms

- **Motif scaffolding**: Fixed residues (e.g., an active site or binding interface) are held constant; the model generates a surrounding scaffold.
- **Symmetric assembly design**: Conditioned on point group symmetry (C₂, C₃, D₂, tetrahedral, etc.) to generate oligomeric assemblies.
- **Binder design**: Conditioned on a target protein structure; generates a binder complementary to the target surface.
- **Partial diffusion**: Applies less noise to an existing structure, then denoises — effectively a structural refinement or diversification.

#### Fine-Tuning Strategy

Rather than training from scratch, the authors fine-tuned a pretrained RoseTTAFold checkpoint. The key architectural modification was minimal — the same network learns to denoise rather than predict from MSAs. This leverages the enormous structural knowledge already encoded in RF.

---

### Key Results

| Task | Result |
|------|--------|
| Unconditional monomer design | Outperforms hallucination; AF2-reprediction TM-score >0.8 up to ~400 aa |
| Protein binder design | Picomolar affinity binders by pure computation (no experimental iteration) |
| Symmetric assembly design | Hundreds of assemblies confirmed by EM |
| Enzyme active site scaffolding | Successful motif scaffolding for metal-binding and catalytic sites |
| Design efficiency | As few as 1 test per design challenge (vs. tens of thousands with prior methods) |

> The picomolar binder result is the headline achievement. Prior computational binder design typically required experimental screening of ~10,000 candidates before finding a functional one. RFdiffusion can find one in the first test.

---

### Connection to TrpB Pipeline

In the Ramanathan Lab pipeline:

1. Yu Zhang uses RFdiffusion to generate **new TrpB backbone variants** — novel scaffolds that position the PLP cofactor and catalytic residues in a design-optimal geometry.
2. The generated backbones define the structural context (binding pocket shape, catalytic site geometry) that LigandMPNN then sequences.
3. Zhenpeng's role: take these designed sequences and run **MetaDynamics simulations** to validate that the designed proteins sample the correct conformational states (O→PC→C transition in the COMM domain).

> RFdiffusion gives us the backbone. The backbone defines which conformational states are accessible and how the COMM domain moves. Our MD validation step answers: does this designed backbone actually adopt the correct dynamics?

---

### What We Can Use

- **Partial diffusion** (noise + denoise around a known TrpB structure): generate structural variants of the COMM domain region without redesigning the entire protein.
- **Motif scaffolding with PLP active site**: fix the PLP-binding residues (Lys100/Lys87, Asp300 etc.) as a motif constraint; let RFdiffusion generate novel surrounding scaffolds.
- **GitHub**: https://github.com/RosettaCommons/RFdiffusion

---

## Paper 2: RFdiffusion3 (RFD3)

### Paper Info

| Field | Value |
|-------|-------|
| Title | De novo Design of All-atom Biomolecular Interactions with RFdiffusion3 |
| Authors | Baker Lab team (David Baker senior author) |
| Venue | bioRxiv (preprint posted September 2025) |
| Year | 2025 |
| DOI | 10.1101/2025.09.18.676967 |
| PubMed | 41000976 |
| PMC | PMC12458353 |
| Status | Preprint; also available open source via IPD (December 2025) |

---

### What Problem Does It Solve?

RFdiffusion (v1) generates protein *backbones only* — sidechains and non-protein molecules (cofactors, ligands, DNA) are not modeled during diffusion. This creates a chicken-and-egg problem: you design the protein, then try to fit the ligand, and the fit is often poor because the pocket geometry was not explicitly designed around the ligand's atomic details.

RFdiffusion3 extends diffusion to **all atoms simultaneously** — protein backbone, sidechains, AND non-protein molecules are all generated together in a single diffusion process.

---

### How Does It Work?

#### All-Atom SE(3) Diffusion

RFdiffusion3 upgrades the diffusion framework from backbone frames to explicit atomic coordinates:

- **Input representation**: Not just Cα frames, but all heavy atoms including sidechains and non-protein atoms (ligand carbons, cofactor oxygens, DNA phosphates, metals)
- **Joint diffusion**: All atoms are noised and denoised together, so the protein pocket and its contents co-evolve during generation
- **Conditioning**: Atom-level constraints can be applied — fix the ligand pose, design the pocket around it

> Why all-atom? In enzyme design, the active site geometry must be precise at the angstrom level. If you design the backbone first and then try to fit the cofactor, you often get clashes or incorrect bond angles. Generating everything together avoids this by construction.

#### Architecture

Built on RoseTTAFold All-Atom (RFAA, Science 2024) — a generalist structure prediction network that handles protein + ligand + nucleic acid systems. RFD3 fine-tunes RFAA as a denoising model, analogous to how RFD1 fine-tuned RF.

---

### Key Results

| Task | Result |
|------|--------|
| Protein-protein binders | Outperforms RFD1 in 4/5 cases without clustering; all 5/5 with clustering |
| DNA-binding protein design | Designed functional DNA binders without providing DNA structure — previously intractable |
| Enzyme active site scaffolding | 90% success rate on 41-enzyme benchmark (vs. lower with prior tools) |
| Computational cost | 10× reduction vs. competing all-atom approaches |

---

### Connection to TrpB Pipeline

RFD3 is more relevant to TrpB design than RFD1 because:

1. **PLP is a cofactor, not a substrate** — it must be explicitly modeled during design. RFD1 ignores the PLP; RFD3 designs around it directly.
2. Yu Zhang can use RFD3 to generate TrpB backbone variants where the PLP binding geometry (Schiff base with Lys100/Lys87, phosphate H-bonds to Ser residues) is enforced at the atomic level during generation.
3. The 90% success rate on enzyme active site scaffolding is directly relevant to TrpB variant generation.

> The key upgrade: RFD1 gives a backbone that *might* accommodate PLP; RFD3 gives a backbone that is *designed* around PLP's atomic geometry. This matters because PLP makes covalent Schiff base bonds — the geometry must be exactly right.

---

### What We Can Use

- **Enzyme design with cofactor constraint**: Fix PLP pose (from 5DVZ crystal structure), use RFD3 to generate novel backbone scaffolds around it.
- **Experimental status**: Open-sourced December 2025 — available now.
- **GitHub**: Available via Institute for Protein Design (IPD) at UW

---

## Paper 3: LigandMPNN

### Paper Info

| Field | Value |
|-------|-------|
| Title | Atomic context-conditioned protein sequence design using LigandMPNN |
| Authors | Justas Dauparas, Gyu Rie Lee, Robert Pecoraro, et al. (Baker Lab) |
| Venue | Nature Methods |
| Year | 2025 |
| Volume/Pages | 22, 717–723 |
| PMID | 40155723 |
| PMC | PMC11978504 |
| DOI | 10.1038/s41592-025-02626-1 |
| Preprint | bioRxiv 10.1101/2023.12.22.573103 (December 2023) |

---

### What Problem Does It Solve?

ProteinMPNN (the standard sequence design tool) treats proteins as chains of amino acid nodes connected by edges — it completely ignores non-protein atoms. When designing an enzyme active site or a cofactor-binding pocket, ProteinMPNN has no representation of the ligand/cofactor and therefore cannot rationally choose residues that interact with it.

LigandMPNN adds explicit representation of **all non-protein atoms** (small molecules, nucleotides, metals) into the message-passing graph, enabling sequence design that is conditioned on atomic-level ligand context.

---

### How Does It Work?

#### Architecture: Message Passing Neural Network on a Heterogeneous Graph

LigandMPNN extends ProteinMPNN's encoder-decoder architecture:

1. **ProteinMPNN baseline**: Graph nodes = amino acid residues; edges = spatial proximity (k-nearest neighbors). Messages encode Cα-Cα distances and relative orientations.

2. **LigandMPNN extension**: Adds a second class of nodes for non-protein atoms. Non-protein nodes encode:
   - Atom type (element, aromaticity, charge)
   - 3D position relative to nearby protein residues
   - Chemical environment (bonds, hybridization)

3. **Message passing**: Protein residue nodes now receive messages from both other protein residues AND nearby non-protein atoms. The aggregated message encodes "what ligand atoms are near me and how are they oriented?"

4. **Sidechain packing**: LigandMPNN also predicts sidechain rotamer angles for designed residues, not just sequence identity — enabling immediate structural evaluation of binding interactions.

> The key insight: residue identity at the binding interface should depend on the ligand's atomic geometry. An Arg that H-bonds to a phosphate, a His that coordinates a metal, a Trp that stacks with an aromatic ring — these choices require knowing where the non-protein atoms are.

#### Training Data

Trained on PDB structures with diverse ligand types: small molecules, nucleotides, metals, cofactors (including PLP-like cofactors). The training set explicitly includes enzyme active sites.

---

### Key Results

| Task | LigandMPNN | ProteinMPNN | Rosetta |
|------|------------|-------------|---------|
| Sequence recovery (small molecule interface) | **63.3%** | 50.5% | 50.4% |
| Sequence recovery (nucleotide interface) | **50.5%** | 34.0% | 35.2% |
| Sequence recovery (metal coordination) | **77.5%** | 40.6% | 36.0% |
| Experimental validation | >100 validated binders | — | — |

> Sequence recovery = fraction of residues where the designed amino acid matches the native (wild-type) residue in a held-out PDB structure. Higher = better recapitulation of natural sequence logic for binding.

The metal coordination result (77.5% vs. 40.6%) is particularly striking — a near 2× improvement. This suggests LigandMPNN has learned the geometry of metal coordination chemistry, which requires precise sidechain positioning.

---

### Connection to TrpB Pipeline

LigandMPNN is the **sequence design step** that follows RFdiffusion backbone generation in the Ramanathan Lab pipeline:

1. **Input to LigandMPNN**: A designed backbone (from RFD1 or RFD3) + fixed PLP pose (from 5DVZ crystal structure coordinates)
2. **LigandMPNN output**: An amino acid sequence optimized to:
   - Maintain the PLP Schiff base with Lys100/Lys87
   - Preserve phosphate H-bonds
   - Pack the aromatic ring system of the cofactor
   - Accommodate the indole substrate
3. **Why LigandMPNN over ProteinMPNN**: ProteinMPNN does not see the PLP — it would design residues that clash with it or fail to coordinate it. LigandMPNN explicitly models the PLP phosphate, pyridine ring, and formyl group atoms.

> Our downstream role: after Yu Zhang generates a designed sequence with LigandMPNN, we run MetaDynamics to test whether the COMM domain of the designed protein actually undergoes O→PC→C conformational transitions, confirming the designed sequence produces correct catalytic dynamics — not just correct static structure.

---

### What We Can Use

- **Direct application**: Use LigandMPNN with PLP from 5DVZ (or 5DW0) as the ligand context to redesign TrpB COMM domain residues while maintaining cofactor binding.
- **Sidechain output**: The sidechain rotamer predictions allow us to build starting structures for MD without additional rotamer sampling steps.
- **GitHub**: https://github.com/dauparas/LigandMPNN
- **Command-line use**: Straightforward Python CLI; input requires backbone PDB + ligand PDB; output is sampled sequences in FASTA format + sidechain-packed PDB

---

## Cross-Paper Synthesis: The Design Pipeline

```
RFdiffusion / RFD3           LigandMPNN              MD Validation (Zhenpeng)
─────────────────────────    ──────────────────────  ──────────────────────────────
Input:                       Input:                  Input:
  target function            backbone PDB (from      LigandMPNN-designed sequence
  (TrpB COMM dynamics)       RFD) + PLP pose
                                                      ↓
  ↓                            ↓                     Build system (tleap)
Generate backbone variants   Design sequences          ↓
that position PLP active     conditioned on PLP        500 ns conventional MD
site correctly               atomic geometry           ↓
  ↓                            ↓                     MetaDynamics (path CV)
Output: backbone PDB         Output: FASTA +           ↓
                             sidechain PDB           Assess:
                                                     - Does COMM domain open/close?
                                                     - Is FEL correct?
                                                     - Does design recapitulate
                                                       wild-type dynamics?
```

### Key Design Constraints That Must Pass Through the Pipeline

| Constraint | Source | How Enforced |
|------------|--------|--------------|
| PLP Schiff base Lys100/Lys87 | 5DVZ crystal structure | RFD3 active site motif; LigandMPNN ligand conditioning |
| PLP phosphate H-bond network | 5DVZ crystal structure | LigandMPNN explicitly models phosphate atoms |
| COMM domain O/PC/C transitions | JACS2019 MetaDynamics | Our path CV (s, z variables in PLUMED) |
| Thermostability at 350 K | P. furiosus origin | MD temperature; ff14SB + TIP3P at 350 K |

---

## Gaps and Open Questions

1. **RFD3 + LigandMPNN pipeline**: Can we combine them? RFD3 designs backbone+ligand jointly; LigandMPNN then redesigns the sequence given the RFD3 output. Is there double-counting of PLP constraints? — UNVERIFIED

2. **COMM domain flexibility in RFD designs**: RFdiffusion tends to generate low-energy, folded backbones. Does it preserve the intrinsic flexibility of the COMM domain (residues 97-184) that is required for catalysis? — Not addressed in Watson et al.

3. **Partial diffusion for TrpB variants**: Using partial diffusion (noise level σ<1) on 5DVZ could generate structurally similar but sequence-diversified TrpB variants — a lower-risk approach than de novo backbone generation.

4. **LigandMPNN temperature sampling**: LigandMPNN has a temperature parameter for sequence sampling. Lower T → more conservative (near wild-type); higher T → more diverse. Optimal T for generating functional variants while maintaining COMM dynamics is unknown.

---

## Sources

- Watson et al. (2023) *Nature*: https://www.nature.com/articles/s41586-023-06415-8
- PubMed RFdiffusion: https://pubmed.ncbi.nlm.nih.gov/37433327/
- Baker Lab RFdiffusion blog: https://www.bakerlab.org/2023/07/11/diffusion-model-for-protein-design/
- RFdiffusion3 bioRxiv: https://www.biorxiv.org/content/10.1101/2025.09.18.676967v1
- RFdiffusion3 PubMed: https://pubmed.ncbi.nlm.nih.gov/41000976/
- IPD RFdiffusion3 release: https://www.ipd.uw.edu/2025/12/rfdiffusion3-now-available/
- Dauparas et al. (2025) *Nature Methods*: https://www.nature.com/articles/s41592-025-02626-1
- LigandMPNN PubMed: https://pubmed.ncbi.nlm.nih.gov/40155723/
- LigandMPNN PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC11978504/
- LigandMPNN GitHub: https://github.com/dauparas/LigandMPNN
- IPD LigandMPNN introduction: https://www.ipd.uw.edu/2025/03/introducing-ligandmpnn/
