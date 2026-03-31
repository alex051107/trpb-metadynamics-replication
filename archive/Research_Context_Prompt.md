# Complete Research Context Prompt
## TrpB MetaDynamics Reproduction — aNima Lab, Caltech

> **How to use this document:** Copy the entire contents of the "MASTER PROMPT" section below into any AI assistant (Claude, GPT-4, Gemini, etc.) at the start of a new conversation. The AI will then have complete context about your project, your lab, your background, and your technical goals — and can help you immediately without re-explaining anything.

---

## Part 1: Situation Description (Full Narrative)

### Who You Are

You are **Zhenpeng Liu**, an undergraduate researcher at **Caltech** (California Institute of Technology), working in the **aNima AI + Science Lab** directed by **Prof. Anima Anandkumar** (Bren Professor of Computing and Mathematical Sciences). You previously worked in the **Miao Lab** at KU (University of Kansas), where you gained hands-on experience with **LiGaMD** (Ligand Gaussian Accelerated Molecular Dynamics) — an enhanced sampling simulation method similar in spirit to the MetaDynamics technique you are now trying to learn and reproduce.

### What the aNima Lab Does (and Why This Project Exists)

The aNima lab sits at the intersection of **machine learning and physical sciences**, with a particular focus on *AI for molecular simulation and drug/protein design*. Key relevant work from the lab includes:

- **NeuralMD**: A physics-informed, multi-grained, group-symmetric ML surrogate for accelerating molecular dynamics simulations of protein-ligand binding. Published in *Nature Communications* 2025 (DOI: 10.1038/s41467-025-67808-z).
- **NeuralPlexer**: A state-specific protein-ligand complex structure prediction model using multi-scale deep generative modeling. (arXiv: 2209.15171).
- **NucleusDiff**: A manifold-constrained nucleus-level denoising diffusion model for structure-based drug design, reducing collision rates up to 100% and improving binding affinity by up to 22%. Published in *PNAS* 2025.
- **GenSLM for TrpB**: The aNima lab collaborated on a project using **GenSLM** (a codon-level protein language model) to generate novel β-subunit tryptophan synthase (TrpB) enzymes. Many of these AI-generated TrpBs showed expanded substrate scope, outperforming natural and laboratory-evolved variants. Published in *Nature Communications* (in press, 2025): *"Sequence-based generative AI design of versatile tryptophan synthases."*

The last point is the **direct origin of this project**: The aNima lab has generated (or is generating) novel TrpB variants using generative AI. But the lab lacks the **computational enzymology expertise** to evaluate *whether these AI-designed proteins will actually be catalytically active*. The **Osuna Lab** at the University of Girona (Spain), led by Prof. **Sílvia Osuna**, has published a rigorous computational framework — using **MetaDynamics + Free Energy Landscape (FEL) analysis** — that is the gold standard for predicting TrpB catalytic activity from structure alone.

**Your job is to reproduce the Osuna lab's MetaDynamics computational pipeline** and then apply it to evaluate the aNima lab's AI-generated TrpB candidates.

---

### The Scientific Problem: Why D-Tryptophan?

The longer-term goal (that your PI's vision is pointing toward) is the **de novo design of an enzyme that synthesizes D-Tryptophan (D-Trp)**.

- **L-Tryptophan** is the natural form — all biological organisms make only the L-enantiomer.
- **D-Tryptophan** is the mirror-image form. It has pharmaceutical value (used in peptide therapeutics, serotonin receptor ligands, anticancer compounds) but no natural enzyme makes it efficiently.
- **The challenge**: Natural TrpB produces L-Trp because the active site geometry forces indole to attack the aminoacrylate intermediate from the *si-face*. To make D-Trp, you need *re-face* attack — which requires a completely different active site geometry. This cannot be achieved by simple mutation of natural TrpB; it requires **de novo protein design** with a new geometric arrangement of catalytic residues.

The pipeline your lab is pursuing:
1. **RFDiffusion2** generates novel protein backbones scaffolding the D-Trp-specific catalytic geometry
2. **ProteinMPNN** designs amino acid sequences for each backbone
3. **AlphaFold2** (reduced MSA, "tAF2") filters sequences by structural fidelity
4. **MetaDynamics FEL analysis** (Osuna's method — YOUR ROLE) evaluates whether each candidate has the correct conformational dynamics
5. **Wet lab** (collaborating lab) tests top candidates

---

### The Osuna Lab Method You Are Reproducing

**Prof. Sílvia Osuna** (Institut de Química Computacional i Catàlisi, Universitat de Girona, Spain) is the world's leading expert on using conformational ensemble analysis to understand and engineer TrpB. Her core insight:

> **The Free Energy Landscape (FEL) of a TrpB variant — specifically, the relative stability of the open vs. closed states of the COMM domain — directly predicts catalytic activity.** Active enzymes have a deep, accessible free energy minimum in the COMM-closed state. Inactive enzymes do not.

**Key papers to reproduce:**

| Paper | Journal | Year | DOI | Access |
|-------|---------|------|-----|--------|
| "Deciphering the Allosterically Driven Conformational Ensemble in Tryptophan Synthase Evolution" | JACS | 2019 | 10.1021/jacs.9b03646 | Institutional |
| "In Silico Identification and Experimental Validation of Distal Activity-Enhancing Mutations in Tryptophan Synthase" | ACS Catal | 2021 | 10.1021/acscatal.1c03950 | CC-BY Open |
| "Estimating conformational heterogeneity of tryptophan synthase with a template-based AlphaFold2 approach" | Protein Science | 2022 | 10.1002/pro.4426 | PMC Open |
| "A naturally occurring standalone TrpB provides insights into allosteric communication" | Protein Science | 2025 | 10.1002/pro.70103 | Recent |

**The computational method:**
- **Software**: GROMACS (MD engine) + PLUMED (MetaDynamics plugin)
- **Force field**: AMBER ff14SB for protein; GAFF2/Meagher parameters for PLP cofactor
- **Collective Variables (CVs)**:
  - CV1: RMSD of COMM domain Cα atoms from the reference open-state structure
  - CV2: Path collective variable (deviation from the ideal open-to-closed pathway)
- **MetaDynamics flavor**: Well-Tempered MetaDynamics (WTMetaD), biasfactor = 10–15, HEIGHT = 0.3–1.2 kJ/mol, SIGMA = 0.05 nm, PACE = 500 steps
- **Sampling strategy**: Multiple Walkers (4–8 parallel replicas sharing bias), each 100–200 ns
- **FEL reconstruction**: `plumed sum_hills` after simulation completion
- **Key metric**: ΔG(closed − open) — the free energy difference between the COMM-closed and COMM-open minima; deeply negative = catalytically active
- **Salt bridge monitor**: R141–D305 distance as a secondary indicator of COMM closure

**The tAF2-MD shortcut** (Osuna 2022, Protein Science):
- Instead of running full MetaDynamics on every candidate (expensive), first run short ~10 ns MD on ~60 structures generated by AlphaFold2 with reduced MSA (32–64 seqs) and structural templates
- The resulting conformational spread approximates the MetaDynamics FEL at lower cost
- Use this to pre-screen before committing to full MetaDynamics

---

### The Full Technical Pipeline (Your Mental Model)

```
[AI GENERATIVE DESIGN]
         │
         ▼
Step 1: Define Theozyme (catalytic geometry for D-Trp)
        Tool: Gaussian QM or Rosetta Theozyme
        Output: 3D atom coordinates of key catalytic groups
         │
         ▼
Step 2: Backbone Scaffolding — RFDiffusion2 (Baker Lab, 2025)
        Paper: Nature Methods, DOI: 10.1038/s41592-025-02975-x
        Key: Atom-level input (no sequence indices needed), 41/41 benchmark
        Output: ~500–1000 novel backbone .pdb files
         │
         ▼
Step 3: Sequence Design — ProteinMPNN (Baker Lab, 2022)
        Paper: Science, DOI: 10.1126/science.add2187
        Key: Graph neural network, 52.4% native sequence recovery
        Output: 10–50 sequences per backbone
         │
         ▼
Step 4: Structure Validation — AlphaFold2 (tAF2, reduced MSA)
        Paper: Protein Science 2022, DOI: 10.1002/pro.4426
        Key: TM-score filter (keep if > 0.6 vs design backbone)
        Output: ~50–200 validated candidates
         │
         ▼
Step 5: Conformational Dynamics Screening — MetaDynamics FEL  ← YOUR ROLE
        Software: GROMACS + PLUMED
        Key output: 2D FEL figure; ΔG(closed), barrier height, R141–D305 %
        Filter: Keep candidates where ΔG(closed) < −2 kcal/mol
        Output: ~5–20 top-ranked candidates
         │
         ▼
Step 6: Wet Lab Testing (collaborating lab)
        Tools: E. coli expression, HPLC, chiral HPLC for D/L-Trp
```

---

### The COMM Domain — What You Are Simulating

The **COMM domain** (~40 residues, approx. positions 100–150 in PfTrpB numbering) is the mobile loop/helix that acts as a lid over the TrpB active site. It must **fully close** during the E(A-A) intermediate state for productive catalysis. The five catalytic states are:

| State | Chemical Species | COMM State |
|-------|-----------------|------------|
| E(Ain) | Internal aldimine (PLP–K82) | Open |
| E(Aex1) | External aldimine (PLP–Ser) | Partially closed |
| E(Q1) | Quinonoid 1 | Partially closed |
| E(A-A) | Aminoacrylate — CRITICAL | **Fully closed — required** |
| E(Q2/Q3) | Quinonoid 2/3 → L-Trp | Reopening |

**The R141–D305 salt bridge** forms when the COMM domain is fully closed and is the key structural indicator in simulations. Distance < 3.5 Å = closed.

---

### What You Will Produce

**Primary deliverable**: A set of **2D Free Energy Landscape (FEL) figures** — one per candidate protein — showing:
- X-axis: CV1 (COMM RMSD from open state, in nm)
- Y-axis: CV2 (path deviation)
- Color: Free energy in kcal/mol (blue = stable, red = unstable)
- Annotated: ΔG(closed), barrier height, R141–D305 formation %
- Verdict: Recommend / Do not recommend for wet lab

**Secondary deliverable**: A ranked candidate table and automated GROMACS+PLUMED workflow scripts.

**Advanced deliverable**: A reward function (Python module) extracting FEL features for feeding back into the generative design loop.

---

## Part 2: MASTER PROMPT (Copy-Paste This into AI)

---

```
═══════════════════════════════════════════════════════════════════════════════
RESEARCH CONTEXT — PLEASE READ FULLY BEFORE RESPONDING
═══════════════════════════════════════════════════════════════════════════════

## WHO I AM

I am Zhenpeng Liu, an undergraduate researcher at Caltech working in Prof.
Anima Anandkumar's aNima AI + Science Lab (tensorlab.cms.caltech.edu). I have
prior wet-lab and computational experience from the Miao Lab (KU) where I ran
LiGaMD (Ligand Gaussian Accelerated MD) simulations and built ML models on
the resulting trajectories.

## MY PROJECT

I am reproducing the computational enzyme analysis pipeline of Prof. Sílvia
Osuna's lab (University of Girona, Spain) — specifically their MetaDynamics +
Free Energy Landscape (FEL) methodology for evaluating TrpB (tryptophan
synthase β-subunit) enzyme variants — with the goal of applying this pipeline
to evaluate AI-generated TrpB candidates from the aNima lab's own generative
design work.

I am NOT in Osuna's lab. I am at Caltech trying to REPRODUCE their method.

## SCIENTIFIC BACKGROUND: THE ENZYME

TrpB (Tryptophan Synthase β-subunit, e.g., PfTrpB from Pyrococcus furiosus,
PDB: 5DW3) is a PLP-dependent enzyme that catalyzes:

    Indole + L-Serine + PLP → L-Tryptophan

The catalytic cycle has 5 states:
  E(Ain)  → E(Aex1) → E(Q1) → E(A-A) → E(Q2/Q3)
  [open]   [partial] [partial] [CLOSED] [reopening]

The E(A-A) state (aminoacrylate intermediate) is critical — it requires the
COMM domain (~40-residue mobile loop, ~res 100–150 in PfTrpB) to be FULLY
CLOSED. COMM closure is the rate-limiting step. The R141–D305 salt bridge
(distance < 3.5 Å) is the structural indicator of the closed state.

Key active site residues:
  K82  — anchors PLP via Schiff base; cannot be mutated
  E104 — controls regioselectivity of indole attack (si vs re face)
  R141 — salt bridge partner (COMM closure indicator)
  D305 — salt bridge partner (COMM closure indicator)

## SCIENTIFIC BACKGROUND: D-TRYPTOPHAN GOAL

Long-term goal: de novo design of a D-Trp-producing enzyme. Natural TrpB
produces only L-Trp (si-face indole attack). D-Trp requires re-face attack —
a completely different active site geometry that cannot be obtained by simple
mutagenesis. The aNima lab uses generative AI (RFDiffusion2, ProteinMPNN,
GenSLM) to design novel scaffolds for this geometry.

## THE OSUNA LAB METHOD I AM REPRODUCING

Prof. Sílvia Osuna's core discovery: The shape of the conformational FEL —
specifically the relative stability of the COMM-open vs COMM-closed states —
directly predicts catalytic activity. This is the "population shift" paradigm.

KEY PAPERS (with DOIs):
  1. JACS 2019: 10.1021/jacs.9b03646
     "Deciphering the Allosterically Driven Conformational Ensemble in TrpS"
     — Original paper establishing MetaDynamics FEL for TrpB

  2. ACS Catalysis 2021: 10.1021/acscatal.1c03950
     "In Silico Identification and Experimental Validation of Distal Mutations"
     — SPM method + MetaDynamics validation on LBCA-TrpB and variants

  3. Protein Science 2022: 10.1002/pro.4426
     "Estimating conformational heterogeneity with template-based AlphaFold2"
     — tAF2-MD: cheap pre-screening using reduced-MSA AF2 + 10 ns MD

  4. Protein Science 2025: 10.1002/pro.70103
     "A naturally occurring standalone TrpB provides insights into allostery"
     — Most recent application of MetaDynamics + SPM correlation analysis

SIMULATION PROTOCOL:
  Software:     GROMACS 2021+ with PLUMED 2.8+ plugin
  Force field:  AMBER ff14SB (protein) + GAFF2/Meagher parameters (PLP)
  Water model:  TIP3P, SPC/E, or OPC (varies by paper)
  System size:  ~50,000 atoms (protein + water box + ions)

  Collective Variables (CVs):
    CV1: RMSD of COMM domain Cα atoms from open-state reference
         PLUMED keyword: RMSD TYPE=OPTIMAL ATOMS=[COMM Cα indices]
    CV2: Path collective variable (deviation from O→C pathway)
         PLUMED keyword: PATH REFERENCE=path.pdb

  MetaDynamics parameters (Well-Tempered):
    PACE=500         (add hill every 500 MD steps = 1 ps)
    HEIGHT=0.3–1.2   (kJ/mol per hill)
    SIGMA=0.05       (nm, for RMSD CV)
    BIASFACTOR=10–15 (γ, well-tempered scaling)
    TEMP=300         (K)
    FILE=HILLS       (hill deposition file)

  Multiple Walkers: 4–8 walkers, each 100–200 ns
  Total sampling: 400–1600 ns per candidate

  Post-processing:
    plumed sum_hills --hills HILLS --outfile fes.dat --stride 1000
    Plot fes.dat as 2D heatmap (matplotlib or gnuplot)

PLUMED INPUT TEMPLATE:
  WHOLEMOLECULES ENTITY0=1-[N_atoms]
  cv1: RMSD REFERENCE=open_comm.pdb TYPE=OPTIMAL ATOMS=[COMM_Calpha_indices]
  metad: METAD ARG=cv1 PACE=500 HEIGHT=0.6 SIGMA=0.05 BIASFACTOR=15 \
         TEMP=300 FILE=HILLS WALKERS_N=4 WALKERS_ID=0 \
         WALKERS_DIR=../ WALKERS_RSTRIDE=500
  d_sb: DISTANCE ATOMS=[R141_idx],[D305_idx]
  PRINT ARG=cv1,metad.bias,d_sb STRIDE=100 FILE=COLVAR

KEY METRICS FROM FEL:
  ΔG(closed)      < −2 kcal/mol  → good candidate (deep closed minimum)
  Barrier height  < 5 kcal/mol   → good candidate (accessible transition)
  R141–D305 %     > 30% time     → good candidate (salt bridge formation)
  CV space        covers both open AND closed regions → good convergence

SHORTCUT METHOD (tAF2-MD):
  1. Generate ~60 AF2 structures using reduced MSA (32–64 seqs) + structural
     templates from MD snapshots
  2. Run 10 ns standard MD on each
  3. Plot conformational spread as proxy for FEL
  4. Pre-screen before committing to full MetaDynamics (saves ~10–50x compute)

## THE FULL DE NOVO DESIGN PIPELINE

Step 1: Theozyme (QM geometry of D-Trp active site)
Step 2: RFDiffusion2 (Baker Lab, Nature Methods 2025, DOI: 10.1038/s41592-025-02975-x)
        — Atom-level backbone scaffolding, 41/41 benchmark success
Step 3: ProteinMPNN (Baker Lab, Science 2022, DOI: 10.1126/science.add2187)
        — Sequence design for each backbone, 52.4% native sequence recovery
        (Also: LigandMPNN, Nature Methods 2025, for ligand-aware design)
Step 4: AlphaFold2 filter (tAF2, reduced MSA, TM-score > 0.6 threshold)
Step 5: MetaDynamics FEL screening ← MY ROLE
Step 6: Wet lab validation

## THE ANIMA LAB CONTEXT

Key relevant aNima lab publications:
  - "Sequence-based generative AI design of versatile tryptophan synthases"
    Nature Communications 2025 (GenSLM-generated TrpBs with expanded substrate scope)
  - NeuralMD: ML surrogate for protein-ligand MD
    Nature Communications 2025, DOI: 10.1038/s41467-025-67808-z
  - NucleusDiff: nucleus-level diffusion for drug design
    PNAS 2025
  - NeuralPlexer: protein-ligand complex structure prediction
    arXiv: 2209.15171

## MY PERSONAL BACKGROUND & SKILLS

  - LiGaMD experience (enhanced sampling, comparable to MetaDynamics)
  - ML modeling on MD trajectory data
  - HPC cluster job automation (Bash scripting)
  - Python (numpy, matplotlib, scikit-learn)
  - Some experience with GROMACS/AMBER setup
  - Biochemistry coursework; familiar with enzyme kinetics

## WHAT I NEED HELP WITH (specify in each session)

[FILL IN per session, e.g.:]
  - Setting up GROMACS topology for PfTrpB (5DW3) with PLP cofactor
  - Writing PLUMED input file for COMM domain MetaDynamics
  - Analyzing COLVAR output and plotting FEL with Python
  - Interpreting FEL figures: what do the features mean?
  - Comparing my reproduced FEL to Osuna's published figures
  - Troubleshooting convergence issues in MetaDynamics
  - Setting up multiple walkers on an HPC (SLURM) cluster
  - Extracting FEL features for a reward function (Python)
  - Understanding the SPM (Shortest Path Map) method
  - Running tAF2-MD pre-screening on a new candidate set

## KEY RESOURCES

  PDB structure: 5DW3 (PfTrpB, P. furiosus, thermostable reference)
  PDB structure: 1K8Z (StTrpB, S. typhimurium, classical reference)
  PLUMED docs: https://www.plumed.org/doc-master/user-doc/html/
  GROMACS manual: https://manual.gromacs.org/
  Osuna lab SPM server: https://spmosuna.com/
  Osuna lab website: https://www.osunalab.com/
  aNima lab website: https://tensorlab.cms.caltech.edu/
  AMBER parameter set for PLP (Meagher et al.): search "AMBER PLP parameters"

═══════════════════════════════════════════════════════════════════════════════
END OF CONTEXT. Please confirm you have read it, then ask what specific help
I need today.
═══════════════════════════════════════════════════════════════════════════════
```

---

## Part 3: Specialized Sub-Prompts

These are shorter prompts for specific tasks. Add them AFTER the master prompt.

### Sub-Prompt A: Setting Up the First Simulation

```
TASK: Help me set up my first MetaDynamics simulation of PfTrpB (PDB: 5DW3).

Specific steps I need help with:
1. How do I obtain and validate the starting PDB structure (5DW3)?
2. How do I add PLP parameters to GROMACS topology?
   (I'm using AMBER ff14SB force field)
3. What is the exact procedure for solvation + ion addition?
4. What NVT/NPT equilibration settings should I use?
5. How do I define the COMM domain RMSD collective variable in PLUMED?
   (What are the atom indices for the COMM domain in 5DW3?)
6. Give me a complete, working plumed.dat file I can start from.

Please be extremely specific — include actual GROMACS command-line syntax and
actual PLUMED input text. I will run this on a Linux HPC with SLURM.
```

### Sub-Prompt B: Reproducing the Osuna FEL

```
TASK: I want to reproduce Figure 2 (or equivalent) from Osuna JACS 2019
(DOI: 10.1021/jacs.9b03646) — the Free Energy Landscape of pfTrpB showing
open, partially closed, and closed COMM domain states.

1. What exact system setup (protein preparation, water model, ions) did
   Osuna use in this paper?
2. What are the exact CV definitions (COMM atom selection, path reference)?
3. What MetaDynamics parameters (HEIGHT, SIGMA, BIASFACTOR, PACE, length)?
4. How do I check convergence of my MetaDynamics simulation?
5. How do I generate a 2D FEL figure from the HILLS file using Python?
   (Give me working matplotlib code that reads fes.dat and produces a
   publication-quality 2D heatmap with proper axis labels and colorbar)
6. What should the FEL look like for active pfTrpB vs inactive standalone TrpB?
   Describe the specific features I should see.
```

### Sub-Prompt C: Analyzing New Candidates

```
TASK: I have completed MetaDynamics simulations for [N] de novo designed TrpB
candidates from RFDiffusion2/ProteinMPNN. Each candidate has a HILLS file and
a COLVAR file. Help me:

1. Write a Python script that:
   a. Reads each candidate's fes.dat (output of sum_hills)
   b. Identifies the position and depth of the closed-state minimum
   c. Calculates ΔG(closed − open)
   d. Calculates the barrier height
   e. Reads the COLVAR file and calculates the R141–D305 salt bridge
      formation fraction (< 3.5 Å)
   f. Outputs a ranked DataFrame (pandas) sorted by ΔG(closed)
   g. Generates a 2D FEL plot for each candidate, saved as PDF

2. What statistical tests should I apply to compare candidates?
3. How do I identify if a simulation has NOT converged and needs more sampling?
4. What is a robust reward function formula that combines these FEL features
   into a single scalar score I can use to guide the next design iteration?
```

### Sub-Prompt D: Understanding the SPM Method

```
TASK: I want to understand and apply the Shortest Path Map (SPM) method from
the Osuna lab (available at https://spmosuna.com/).

1. What exactly is SPM? How is it computed from an MD trajectory?
2. What are the inputs (distance matrix + correlation matrix from MD)?
3. How do I generate these matrices from a GROMACS trajectory in Python?
   (using MDAnalysis or MDTraj — give me working code)
4. How do I submit a job to the SPM web server?
5. How do I interpret the output? What does a high-SPM-score residue mean?
6. How do I use SPM results to identify distal mutation candidates for
   improving COMM domain closure in my de novo designed TrpBs?
```

### Sub-Prompt E: tAF2-MD Pre-Screening

```
TASK: Before running full MetaDynamics on all my de novo TrpB candidates, I
want to use the tAF2-MD pre-screening method (Osuna Protein Science 2022,
DOI: 10.1002/pro.4426) to reduce my candidate pool cheaply.

1. What exactly is the tAF2-MD protocol?
   - How many AF2 structures do I generate per candidate?
   - What MSA depth setting do I use (32? 64?)?
   - What templates do I provide?
   - How long are the short MD simulations (10 ns?)?
   - How many structures total?
2. How do I run AlphaFold2 with reduced MSA depth?
   (I have access to AlphaFold2 on our HPC cluster)
3. How do I extract conformational descriptors from the 10 ns trajectories?
4. How do I plot the tAF2-MD conformational spread and compare it to a
   reference MetaDynamics FEL?
5. What cutoff/threshold do I use to decide which candidates pass tAF2-MD
   screening and deserve full MetaDynamics treatment?
```

---

## Part 4: Key Papers Checklist

Mark these as you read them:

- [ ] **JACS 2019** — Osuna MetaDynamics FEL (10.1021/jacs.9b03646) ← START HERE
- [ ] **ACS Catalysis 2021** — SPM + distal mutations (10.1021/acscatal.1c03950) ← SECOND
- [ ] **Protein Science 2022** — tAF2-MD method (10.1002/pro.4426) ← THIRD
- [ ] **Science 2022** — ProteinMPNN (10.1126/science.add2187)
- [ ] **Nature 2023** — RFDiffusion1 (10.1038/s41586-023-06415-8)
- [ ] **Nature Methods 2025** — RFDiffusion2 (10.1038/s41592-025-02975-x)
- [ ] **Nat Comm 2025** — aNima GenSLM-TrpB (search: "Sequence-based generative AI design of versatile tryptophan synthases")
- [ ] **Nat Comm 2025** — NeuralMD (10.1038/s41467-025-67808-z)
- [ ] **Protein Science 2025** — Osuna standalone TrpB (10.1002/pro.70103)

---

## Part 5: Quick Reference — PLUMED Keywords

| Keyword | What it does | Example |
|---------|-------------|---------|
| `RMSD` | RMSD from reference structure | `cv1: RMSD REFERENCE=open.pdb TYPE=OPTIMAL ATOMS=120-160` |
| `PATH` | Path collective variable | `cv2: PATH REFERENCE=path.pdb TYPE=RMSD LAMBDA=50000` |
| `DISTANCE` | Distance between two atoms | `d: DISTANCE ATOMS=2150,4812` |
| `METAD` | MetaDynamics bias | `METAD ARG=cv1 PACE=500 HEIGHT=0.6 SIGMA=0.05 BIASFACTOR=15 TEMP=300 FILE=HILLS` |
| `PRINT` | Write output | `PRINT ARG=cv1,metad.bias STRIDE=100 FILE=COLVAR` |
| `WHOLEMOLECULES` | Fix periodic boundary | `WHOLEMOLECULES ENTITY0=1-4500` |
| `WALKERS_N` | Multiple walkers count | Part of METAD line |
| `WALKERS_ID` | This walker's index | Part of METAD line (0-indexed) |

---

*Document prepared March 2026 | Zhenpeng Liu | aNima Lab, Caltech*
*Reproduction target: Osuna Lab MetaDynamics pipeline for TrpB conformational analysis*
