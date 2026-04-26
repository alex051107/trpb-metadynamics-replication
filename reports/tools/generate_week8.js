const docx = require("docx");
const fs = require("fs");
const path = require("path");

const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  WidthType,
  AlignmentType,
  BorderStyle,
  HeadingLevel,
  convertInchesToTwip,
  TableLayoutType,
} = docx;

// helpers
const FONT = "Arial";
const BLACK = "000000";

function heading(text, level) {
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 240 : 180, after: 120 },
    children: [
      new TextRun({
        text,
        bold: true,
        font: FONT,
        size: level === 1 ? 28 : 24,
        color: BLACK,
      }),
    ],
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.afterSpacing || 120 },
    children: [
      new TextRun({
        text,
        font: FONT,
        size: 22,
        color: BLACK,
        bold: opts.bold || false,
        italics: opts.italic || false,
      }),
    ],
  });
}

const thinBorder = {
  style: BorderStyle.SINGLE,
  size: 1,
  color: BLACK,
};
const borders = {
  top: thinBorder,
  bottom: thinBorder,
  left: thinBorder,
  right: thinBorder,
};

function makeTable(headers, rows) {
  const headerRow = new TableRow({
    children: headers.map(
      (h) =>
        new TableCell({
          borders,
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: h,
                  bold: true,
                  font: FONT,
                  size: 20,
                  color: BLACK,
                }),
              ],
            }),
          ],
        })
    ),
  });
  const dataRows = rows.map(
    (row) =>
      new TableRow({
        children: row.map(
          (val) =>
            new TableCell({
              borders,
              children: [
                new Paragraph({
                  children: [
                    new TextRun({
                      text: String(val),
                      font: FONT,
                      size: 20,
                      color: BLACK,
                    }),
                  ],
                }),
              ],
            })
        ),
      })
  );
  return new Table({
    rows: [headerRow, ...dataRows],
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.AUTOFIT,
  });
}

// document
const doc = new Document({
  sections: [
    {
      properties: {
        page: {
          margin: {
            top: convertInchesToTwip(1),
            bottom: convertInchesToTwip(1),
            left: convertInchesToTwip(1),
            right: convertInchesToTwip(1),
          },
        },
      },
      children: [
        // header table
        makeTable(
          ["Field", "Value"],
          [
            ["To", "Prof. Anima Anandkumar; Dr. Yu Zhang"],
            ["From", "Zhenpeng Liu (liualex@ad.unc.edu)"],
            ["Date", "May 1, 2026"],
            [
              "Week",
              "Week 8: Path realignment unblocks Initial pilot, 10-walker production launched, MetaD-to-GenSLM staged plan drafted",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 120 } }),

        heading("Project Context", 1),
        para(
          "I am replicating a MetaDynamics-based conformational analysis of the TrpB enzyme (an enhanced sampling method that pushes a system across rare-event barriers, applied to the open-to-closed motion of TrpB; Maria-Solano et al., JACS 2019). " +
            "The goal is to validate the published method on the wild-type system, then apply it to score AI-generated enzyme variants from the Anima Lab GenSLM pipeline."
        ),

        heading("Pipeline Overview", 1),
        para(
          "Phase 1: Replicate published results"
        ),
        para("  [1] Environment setup                 DONE"),
        para("  [2] PLP cofactor parameterization     DONE"),
        para(
          "  [3] Reference path generation         DONE (FP-034 realigned this week)"
        ),
        para("  [4] System preparation                DONE"),
        para("  [5] 500 ns conventional MD            DONE"),
        para(
          "  [6] Well-tempered MetaDynamics        IN PROGRESS  <-- here"
        ),
        para("  [7] Compare with published results    NEXT"),
        para(
          "Phase 2: Apply MetaDynamics output to score / fine-tune GenSLM"
        ),
        para("Phase 3: Build reward function for design loop (V2)"),

        heading("Summary", 1),
        para(
          "The flagship result this week is that the Initial pilot finally ran correctly under the author-supplied parameters (HEIGHT=0.3 kcal/mol fallback contract, BIASFACTOR=15) for 24 ns and reached max_s=14.05 along the open-to-closed path coordinate. " +
            "Before this week, the same pilot was stuck at s less than 1.9 over 17 ns despite identical engine settings."
        ),
        para(
          "The unblock came from rebuilding the reference path with a proper sequence alignment between the two source structures. " +
            "The published protocol uses two different species in the same path: 1WDW (P. furiosus TrpB) is the only available high-resolution open-state crystal, and 3CEP (S. typhimurium TrpB) is the only available high-resolution closed-state crystal — there is no single-species crystal pair that covers both endpoints, so the path is necessarily inter-species. " +
            "The two β-subunits are not the same length: 3CEP carries five extra N-terminal residues (a vestigial signal-peptide region of the bacterial enzyme that the archaeal enzyme does not have). " +
            "My original path-builder paired residues by raw residue number, so 1WDW residue 97 was paired with 3CEP residue 97 instead of 3CEP residue 102. " +
            "Across the 112 selected COMM-domain Cα positions this matched non-homologous residues; sequence identity dropped to 6.2 percent and the open-to-closed RMSD inflated to 10.89 Å. " +
            "The Branduardi formula λ = 2.3 / mean adjacent MSD then collapsed λ to 3.80 inverse Å, about 21 times below what the SI implies. " +
            "After a Needleman-Wunsch realignment recovered the uniform +5 residue-number offset, sequence identity climbed to 59.0 percent, RMSD fell to 2.115 Å, and λ settled at 100.79 inverse Å on the realigned path. " +
            "The pilot then unlocked, and the canonical Initial pilot 24 ns FES (Figure 2) is now in hand."
        ),
        para(
          "Building on the unblocked Initial pilot, I picked 10 starting frames spread across the realigned path coordinate by reading the Initial pilot COLVAR and selecting frames that minimized off-path deviation inside ten target s-windows. " +
            "I launched the 10-walker production array under Miguel's primary contract (HEIGHT=0.15, BIASFACTOR=10, shared HILLS) as SLURM 45784112; the smoke test passed all 10 walkers, and the array has been running for around five hours. " +
            "I have observed some LINCS warnings appearing mid-run on a subset of walkers and will spend next week debugging that signature."
        ),
        para(
          "The other major block of work was drafting the MetaDynamics-to-GenSLM outer layer in Section 2.4. " +
            "I plan to walk Prof. Anandkumar through the staged plan, the activity-proxy decision, and the transition-state data integration question in a short feasibility meeting next week before committing to Stage 1 implementation."
        ),

        heading("Work Done", 1),
        makeTable(
          ["#", "Task", "Category", "Status"],
          [
            [
              "1",
              "Diagnosed v1 10-walker scancel: homogeneous-start failure (FP-030)",
              "Debug",
              "Done",
            ],
            [
              "2",
              "Diagnosed v2 10-walker exit-139: LINCS atoms 4463 to 4465 plus missing velocity initialization",
              "Debug",
              "Done",
            ],
            [
              "3",
              "Designed v3 3-stage flow: EM 1000 steps, then NVT 100 ps PLUMED-off, then MetaD with continuation=yes",
              "Setup",
              "Done",
            ],
            [
              "4",
              "Smoke test 45783311: 10 of 10 walkers PASS, 24 minute wall, 0 LINCS warnings",
              "Simulation",
              "Done",
            ],
            [
              "5",
              "Launched 10-walker production 45784112 with shared HILLS_DIR",
              "Simulation",
              "Running",
            ],
            [
              "6",
              "Applied FP-034 path realignment using a hand-coded Needleman-Wunsch alignment (1WDW vs 3CEP)",
              "Setup",
              "Done",
            ],
            [
              "7",
              "Self-computed Branduardi LAMBDA on the realigned path: 100.79 inverse Angstroms",
              "Analysis",
              "Done",
            ],
            [
              "8",
              "Re-read JACS 2019 SI for the 10-walker protocol; logged 3 drifts and corrected each",
              "Documentation",
              "Done",
            ],
            [
              "9",
              "Rewrote production materializer to extract seeds from initial-MetaD COLVAR, not from cMD",
              "Setup",
              "Done",
            ],
            [
              "10",
              "Widened seed targets from integer 1 to 10 to a uniform linspace 1 to max_s observed",
              "Setup",
              "Done",
            ],
            [
              "11",
              "Wrote select_seeds with window-min-z rule and a hard cap z less than 2.5",
              "Setup",
              "Done",
            ],
            [
              "12",
              "Drafted a staged MetaDynamics-to-GenSLM adjustment plan indexed by labeled-pair count (small N: ranking head over GenSLM embeddings; medium N: activation steering on the residual stream; large N: PiSSA adapter with DoRA / LoRA+ ablations or GRPO RL); see Section 2.4",
              "Documentation",
              "Draft",
            ],
            [
              "13",
              "Ran 8 rounds of cross-audit plus 1 independent second-pass on the outer-layer design (Codex peer review and a separate sub-agent reviewer)",
              "Documentation",
              "Done",
            ],
            [
              "14",
              "Wrote 12-slide bilingual presenter script for the May 1 group meeting",
              "Documentation",
              "Done",
            ],
            [
              "15",
              "Rendered two figures for the report: latest Initial pilot 24 ns FES with proper RMSD axis units, and the before-vs-after path realignment trajectory",
              "Analysis",
              "Done",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 60 } }),

        heading("What I Learned", 1),

        heading(
          "1. The reference path needed re-aligning before the Initial pilot would explore",
          2
        ),
        para(
          "The published path coordinate uses 15 frames between an open structure (1WDW chain B, P. furiosus TrpB) and a closed structure (3CEP chain B, S. typhimurium TrpB). " +
            "The reason the path is necessarily inter-species is that 1WDW is the only available high-resolution open-state TrpB crystal in the PDB and 3CEP is the only available high-resolution closed-state TrpB crystal; no single species has crystals of both endpoints. " +
            "My original path-builder paired residues by raw residue number, so 1WDW residue 97 was paired with 3CEP residue 97."
        ),
        para(
          "The two chains are not the same length: 3CEP carries five extra N-terminal signal-peptide residues, so 1WDW residue 97 is actually homologous to 3CEP residue 102. " +
            "The naive pairing matched non-homologous residues across the 112 selected positions. " +
            "Sequence identity dropped to 6.2 percent and the per-atom open-to-closed RMSD inflated to 10.89 A."
        ),
        para(
          "The Branduardi formula LAMBDA = 2.3 / mean MSD between adjacent frames (Branduardi 2007) then collapsed LAMBDA to 3.80 inverse Angstroms, about 21 times smaller than what the SI implies."
        ),
        para(
          "I fixed this by writing a Needleman-Wunsch alignment in numpy (match=+2, mismatch=-1, gap=-2). " +
            "The result is a uniform +5 offset across the 112 selected residues. " +
            "After fixing the pairing, identity climbed to 59.0 percent and RMSD fell to 2.115 A."
        ),
        para(
          "LAMBDA settled at 100.79 inverse Angstroms. " +
            "The ratio between my LAMBDA and Miguel's reported 80 is 1.26, which sits inside the Branduardi tolerance of 2 (Branduardi 2007). " +
            "The bug was silent for three weeks because the path file syntax was valid and PLUMED accepted it without complaint."
        ),
        para(
          "The only downstream symptom was that the single-walker pilot stayed trapped at s less than 1.9 over 16 ns. " +
            "After the realignment the same pilot now reaches s=14.05 at 24 ns and explores the full open-to-closed path. " +
            "I logged the case as FP-034 with the rule that any future path-builder script must assert sequence identity above 50 percent before writing the path file."
        ),

        heading("2. v3 design and why three stages were needed", 2),
        para(
          "The v2 10-walker run launched directly from coordinate-only start.gro files with continuation=no, gen_vel=yes, and PLUMED biasing turned on at the same time. " +
            "All 10 walkers crashed inside 12 minutes with LINCS bond-stress on atoms 4463 through 4465. " +
            "The root cause is that PLUMED started depositing path-CV bias before the velocities had Maxwell-Boltzmann thermalized at 350 K."
        ),
        para(
          "Bond-stressed atoms cannot satisfy LINCS constraints under sudden bias and the integrator gives up with exit code 139."
        ),
        para(
          "The v3 design splits the walker startup into three stages. " +
            "Stage 1 is energy minimization for 1000 steps with PLUMED off. " +
            "Stage 2 is NVT for 100 ps with PLUMED still off and gen_vel=yes, which initializes velocities at 350 K. " +
            "Stage 3 is MetaDynamics with continuation=yes so that the velocities and box from nvt.cpt are inherited. " +
            "PLUMED turns on for the first time at this stage."
        ),
        para(
          "The smoke test (SLURM 45783311) ran 10 walkers for 1000+1000+1000 steps as a 30-minute sanity check. " +
            "All 10 walkers passed: EM Maximum force in the range 938 to 986 kJ/mol/nm, 0 LINCS warnings, 0 atoms 4463 to 4465 errors, HILLS deposited at 1 hill per 2 ps, and 0 exit code 139. " +
            "The production array launched immediately after the smoke pass."
        ),

        heading(
          "3. The published FES uses production-only HILLS, not initial-plus-production",
          2
        ),
        para(
          "I wanted to render an early figure for the deck by combining the 22 ns of initial pilot HILLS (the bias-deposit history file) with the first 300 ps of the 10-walker production HILLS, on the assumption that more bias data is better. " +
            "I asked for an SI re-read first."
        ),
        para(
          'The relevant lines on SI p.S3-S4 are: "The free energy landscape associated with the metadynamics CVs is estimated by summing the Gaussian potentials deposited by all walker replicas as a function of the CVs values." ' +
            'And: "After an initial metadynamics run, we extracted ten snapshots ... Then, multiple-walkers metadynamics simulations with 10 replicas were computed."'
        ),
        para(
          "The construction in the SI is production replicas only, not initial run plus production. " +
            "Initial metadynamics is a seed-discovery stage, not FES evidence."
        ),
        para(
          "There is also a project-specific reason the merge would have been wrong: my initial pilot uses the FALLBACK contract (HEIGHT=0.3 kcal/mol, BIASFACTOR=15) while the production uses the PRIMARY contract (0.15, 10). " +
            "Well-tempered MetaDynamics theory requires a single biasfactor for one self-consistent FES estimate. " +
            "When production reaches 10 ns per walker, the FES is built only from the 10 production HILLS files, by plumed sum_hills with --kt 0.695 --mintozero."
        ),

        heading(
          "4. Initial thoughts on feeding MetaDynamics data back into GenSLM",
          2
        ),
        para(
          "This subsection is preliminary. " +
            "The 10-walker production has only been running a few hours and the labeled MetaDynamics-to-sequence pairs do not yet exist; what follows is the framing I want to commit to before the next group meeting, not a finalized design.",
          { italic: true }
        ),
        para(
          "Why this is the right next step. " +
            "Maria-Solano et al. (JACS 2019) established the observation that motivates Phase 2: the TrpB variants with higher catalytic turnover are the ones whose protein body moves quickly and reliably across the open / partially closed / closed conformations. " +
            "MetaDynamics is the only computational method I can run on a single variant that gives a quantitative read on those transitions. " +
            "If I want a reward signal that is mechanistically tied to catalysis, and not just to substrate binding affinity (which is what a docking score gives), MetaDynamics output is the most direct source."
        ),
        para(
          "How the reward function works, in plain language. " +
            "For each variant, MetaDynamics returns a 2D free energy surface. " +
            "From that surface I read two things: the energy barrier between the open and closed states (a low barrier means the protein reaches the catalytic state fast) and the depth of the closed-state basin (a deep basin means the protein stays in the catalytic state long enough for chemistry to happen). " +
            "I combine the two into one scalar reward per variant. " +
            "The functional form is the standard Kramers and Boltzmann combination from physical chemistry; the contribution is in using MetaDynamics output as the source of the two terms, not in inventing a new formula."
        ),
        para(
          "The staged adjustment plan, indexed by data volume. " +
            "GenSLM-25M is built and maintained by another lab member; my contribution is the rule for how the MetaDynamics-derived reward attaches to it. " +
            "I want to propose a staged plan whose stage is decided by the size of the labeled (sequence, MetaDynamics-output) pair set, not by method preference. " +
            "Every stage is conditional, in the sense that we only run a method whose statistical defensibility matches the available data budget."
        ),
        para(
          "Stage 1, small N on the order of 30 to 50 pairs (where I am now). " +
            "Keep GenSLM weights and activations frozen. " +
            "Sample N candidate sequences from GenSLM, score each one with a ranking head (ridge regression or a Gaussian-process surrogate) trained on the labeled set in GenSLM's own embedding space, and ship the top-K to wet lab. " +
            "The closest small-N protein-LM TrpB benchmark in the literature is SGPO (Yang et al., NeurIPS 2025; arXiv:2505.15093), which uses classifier-guided posterior sampling on a discrete-diffusion protein language model rather than a regression head over an autoregressive model. " +
            "GenSLM is autoregressive, so my Stage 1 is the classical Bayesian-optimization-over-PLM-embeddings analogue of SGPO; the same small-N feasibility argument applies. " +
            "No reinforcement learning, no weight updates."
        ),
        para(
          "Stage 2, medium N on the order of 500 pairs (after one or two active-learning rounds). " +
            "Switch from re-ranking-only to steering at generation time. " +
            "Train a contrastive direction in GenSLM's hidden-state space (Turner et al. 2023 activation engineering; Zou et al. 2023 representation engineering), then add it to the residual stream during sampling so the generator probabilistically prefers high-reward sequences. " +
            "GenSLM weights still stay frozen; the only learned object is one direction vector per layer (on the order of d_model floats per layer). " +
            "The robustness property I want at this stage is that the steering can be turned off at inference time by zeroing the direction, recovering the original GenSLM."
        ),
        para(
          "Stage 3, large N on the order of 5000 pairs and beyond (late stage). " +
            "Weight-level adjustment becomes statistically defensible. " +
            "After consulting Codex on the LoRA-family alternatives, my preferred Stage 3 adapter is PiSSA (Meng, Wang and Zhang, 2024; arXiv:2404.02948), which initializes the low-rank update matrices from the SVD of the pretrained weights so the adapter trains the principal directions rather than random or zero ones; this is attractive for noisy low-N scalar rewards like a MetaDynamics-derived FES summary. " +
            "DoRA (Liu et al., ICML 2024 Oral; arXiv:2402.09353; decouples adapter magnitude and direction) is a strong second choice. " +
            "LoRA+ (Hayou, Ghosh and Yu, 2024; arXiv:2402.12354; better learning-rate / scaling rule) is the safe baseline alongside the original LoRA (Hu et al. 2021; arXiv:2106.09685). " +
            "There is no head-to-head adapter benchmark on enzyme variant ranking yet, so I would run PiSSA, DoRA and LoRA+ as a small adapter ablation at the start of Stage 3."
        ),
        para(
          "Beyond parameter-efficient adapters, full reinforcement learning with continuous reward (GRPO, as in Stocco et al. 2024 ProtRL; arXiv:2412.12979) is the upper-end option once a few thousand labeled pairs exist. " +
            "ReFT (Wu et al. 2024; arXiv:2404.03592) is a conceptually attractive alternative because it intervenes on representations rather than weights, which composes naturally with my Stage 2 steering, but it is less standard for protein language models. " +
            "Each stage's labeled-pair budget is conservatively about 10 times the previous; I will not move from one stage to the next until the data budget supports it."
        ),
        para(
          "On 'eLoRA' specifically. PM asked about this candidate. " +
            "Codex disambiguation: there is an ELoRA: Equivariant Low-Rank Adaptation for equivariant graph neural networks (Wang et al., ICML 2025; targeted at SO(3)-equivariant interatomic potentials, not autoregressive protein LMs); there is ElaLoRA: Elastic Low-Rank Adaptation (arXiv:2504.00254, 2025; rank pruning and expansion); and some secondary sources call Kopiczko et al.'s VeRA (arXiv:2310.11454, 2023) 'ELoRA' because of the random shared matrices. " +
            "None of these is the right shape for my Stage 3 problem; I will not list 'eLoRA' as a candidate without a specific arXiv pointer."
        ),
        para(
          "What is NOT being claimed. " +
            "The reward weights have not yet been calibrated against measured TrpB k_cat values; that calibration is a near-term task once production gives me one or two converged free energy surfaces. " +
            "Stage 2 and Stage 3 have not been benchmarked on GenSLM specifically. " +
            "The simplest baseline (just rerank GenSLM's outputs by a generic protein-language-model likelihood) must be measured first; every more elaborate stage earns its compute budget only if it beats that baseline. " +
            "Phase 2 also depends on the activity-proxy decision (MMPBSA rank, literature k_cat, or hand-binned classes) called out in the open questions section."
        ),
        para(
          "How my plan compares to other recent work in this area:"
        ),
        makeTable(
          ["Work", "Method", "Stage in my plan", "Relation"],
          [
            [
              "Yang et al. NeurIPS 2025 (SGPO; arXiv:2505.15093)",
              "Classifier-guided posterior sampling on a discrete-diffusion protein LM, benchmarked on TrpB at small N",
              "Stage 1 (small N) — small-N feasibility precedent",
              "Closest small-N protein-LM TrpB benchmark; their PLM is discrete-diffusion while GenSLM is autoregressive, so my Stage 1 is the BO-over-PLM-embeddings analogue of SGPO with the same small-N feasibility argument.",
            ],
            [
              "Turner et al. 2023 (activation engineering / addition; arXiv:2308.10248); Zou et al. 2023 (representation engineering; arXiv:2310.01405)",
              "Add a contrastively-derived steering vector to the residual stream at inference; weights stay frozen",
              "Stage 2 (medium N)",
              "The steering target is a contrastive direction trained on (high-reward, low-reward) pairs derived from MetaDynamics-derived reward.",
            ],
            [
              "Meng, Wang and Zhang 2024 (PiSSA; arXiv:2404.02948)",
              "SVD-initialized LoRA: trains the principal directions of the pretrained weights",
              "Stage 3 (large N) — preferred adapter",
              "Best fit for noisy low-N scalar rewards (e.g., MetaD-derived FES summary); chosen over DoRA after Codex consult on adapter robustness at small rank.",
            ],
            [
              "Liu et al. ICML 2024 Oral (DoRA; arXiv:2402.09353)",
              "Decomposes pretrained weights into magnitude and direction; LoRA only on direction",
              "Stage 3 (large N) — second choice / ablation",
              "Strong improvement over the original LoRA (Hu et al. 2021; arXiv:2106.09685) at low rank, but not protein-validated head-to-head against PiSSA on enzyme variant ranking.",
            ],
            [
              "Hayou, Ghosh and Yu 2024 (LoRA+; arXiv:2402.12354)",
              "Original LoRA with a better learning-rate / scaling rule",
              "Stage 3 baseline / control",
              "Cheap, stable and easy to debug at N≈5000; used as the control for the PiSSA / DoRA adapter ablation.",
            ],
            [
              "Stocco et al. 2024 (ProtRL; arXiv:2412.12979)",
              "wDPO + GRPO reinforcement learning of ZymCTRL family; produced low-nM EGFR binders",
              "Stage 3 (large N, RL upper bound)",
              "Recipe for the reinforcement-learning option once the labeled set is materially larger than my 30 to 50.",
            ],
            [
              "ByteDance Seed et al. 2026 (arXiv:2602.02128)",
              "Causal SE(3)-equivariant diffusion transformer that rolls out microsecond-scale all-atom protein trajectories from a sequence; not coarse-grained",
              "Orthogonal",
              "Generates approximate MD trajectories from a sequence; my plan runs ground-truth PLUMED MetaDynamics on a fixed sequence and feeds that MetaDynamics output back into a sequence model. Their generative MD is a complementary scaling lever, not a substitute for the reward source.",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 60 } }),

        heading("Problems Encountered and How I Solved Them", 1),

        heading("Problem 1: v2 10-walker LINCS exit code 139", 2),
        para("What happened: All 10 walkers in production v2 crashed within 12 minutes. The Slurm logs all reported LINCS WARNING on atoms 4463 through 4465 followed by Fatal error and exit code 139.", { italic: true }),
        para("Root cause: The walker MDP had continuation=no plus gen_vel=yes plus PLUMED bias on. Velocities were being initialized at 350 K at the same step that the path-CV bias started pushing on the system. The bond-stressed coordinates could not satisfy LINCS constraints.", { italic: true }),
        para("How I fixed it: I split the walker startup into three stages: EM with PLUMED off, NVT with PLUMED off and gen_vel=yes, then MetaDynamics with continuation=yes that reads nvt.cpt and inherits velocities. PLUMED turns on only after the system is fully thermalized.", { italic: true }),
        para("Lesson: Never bias an un-thermalized system. PLUMED on plus gen_vel=yes in the same MDP is a footgun.", { italic: true }),

        heading("Problem 2: Walker 9 starts close to the upper wall", 2),
        para("What happened: My seed selection rule picks the frame with minimum z (path deviation) inside each target-s window. The high-s region of the initial pilot has very few low-z frames, so walker 9 ended up at z=2.01 inverse Angstroms squared. The production wall is z=2.5, so walker 9 is starting close to the wall.", { italic: true }),
        para("Root cause: The initial pilot has under-sampled the high-s, low-z corner. This is a pilot under-sampling issue, not a selection-rule issue.", { italic: true }),
        para("How I fixed it: I retained walker 9 because the smoke test EM converged in 759 steps without violating UPPER_WALLS. I documented a fallback in VALIDATION_REPORT.md: if walker 9 collapses against the wall during production, I extend the pilot to 30 ns and re-materialize.", { italic: true }),
        para("Lesson: Document fallbacks even when the current run passes. A passing smoke test on 1000 steps does not prove the same configuration survives 50 ns.", { italic: true }),

        heading("Open Questions", 1),
        para(
          "1. Activity proxy choice. The reward function in Section 2.4 needs an activity ground truth to anchor against once production reaches a converged FES. " +
            "Candidate signals: Yu's MMPBSA rank, literature k_cat where measured, or hand-binned activity classes. " +
            "Without a decision the reward weights cannot be calibrated against measured TrpB activity."
        ),
        para(
          "2. Transition-state data integration. " +
            "Stage 1 of my Section 2.4 plan reduces the FES to two scalars (transition-state height; closed-state stability). " +
            "Should the reward also fold in the geometry of the saddle region (curvature at the transition state, or path-CV bottleneck width), or is the two-scalar reduction sufficient? " +
            "I would like Anima's read on this before committing to the Stage 1 ranking-head training."
        ),
        para(
          "3. GenSLM checkpoint introspection. " +
            "Lambert 2026 supplies a 25M-parameter checkpoint with d_model and pooling rule both unstated. " +
            "I have a one-shot extraction script that pulls hidden_size from the public config.json on the GitHub repo. " +
            "If it returns one integer, the dependency clears mechanically; if not, I will escalate to the GenSLM authors."
        ),
        para(
          "4. Convergence labeling at the May 1 meeting. " +
            "Even with a clean 10-walker production, the published convergence gate is 45 ns per walker (JACS 2019 SI Fig S4 plateau test); a 24-hour wall budget falls short of that. " +
            "Is the lab comfortable shipping a PROVISIONAL convergence label with the diagnostic plot included, or should the deck wait until the plateau test PASSes?"
        ),

        heading("Next Week Plan", 1),
        heading("Papers to read", 2),
        para(
          "Lambert et al. 2026 (GenSLM-25M-TrpB): I have read the methods but want to fully resolve Fig 2A's pooling rule before the staged-plan feasibility meeting."
        ),
        heading("Tasks", 2),
        para(
          "1. Debug the 10-walker production. " +
            "I have observed LINCS warnings appearing mid-run on a subset of walkers (around 1 to 3 ns into the MetaDynamics phase, distinct from the v2 startup-LINCS signature). " +
            "Next week's first job is to localize the failure mode (most likely a bias-rate / time-step interaction with water settling in high-bias regions) and decide between a shorter time step, a lower Gaussian height, or a damped early-stage bias schedule."
        ),
        para(
          "2. Think through how to integrate transition-state data into the reward function. " +
            "The reward I sketched in Section 2.4 reads two scalars off the FES (transition-state height between O and C, and closed-state stability). " +
            "What I want to explore next week is whether the path-coordinate free-energy profile itself, including the geometry of the saddle region, can be folded into the reward — for example by adding a curvature term at the saddle, or by using the path-CV bottleneck width — without losing the small-N statistical defensibility argument from Stage 1."
        ),
        para(
          "3. Schedule a short feasibility meeting with Prof. Anandkumar to walk through the staged MetaDynamics-to-GenSLM plan (Stage 1 ranking head; Stage 2 activation steering; Stage 3 PiSSA / DoRA / LoRA+ ablation), the activity-proxy decision, and the transition-state-integration question above."
        ),
        para(
          "4. Continue Lambert et al. 2026 (GenSLM-25M-TrpB) reading; resolve Fig 2A's pooling rule before the feasibility meeting."
        ),

        heading("Key Simulation Parameters", 1),
        makeTable(
          ["Parameter", "Value", "Source"],
          [
            ["Force field", "ff14SB", "SI Methods, JACS 2019"],
            ["Water model", "TIP3P", "SI Methods, JACS 2019"],
            [
              "Temperature",
              "350 K",
              "SI Methods (P. furiosus thermophile)",
            ],
            [
              "MetaD engine",
              "GROMACS 2026.0 + PLUMED 2.9.2 (source)",
              "SI specifies GROMACS+PLUMED",
            ],
            [
              "Path-CV LAMBDA",
              "100.79 inverse Angstroms",
              "Branduardi self-compute on FP-034 path",
            ],
            [
              "Path-CV ADAPTIVE scheme",
              "DIFF",
              "Codex SI re-read; FP-031 corrects earlier GEOM mis-read",
            ],
            [
              "Gaussian HEIGHT (production)",
              "0.15 kcal/mol",
              "Miguel email 2026-04-23 (PRIMARY contract)",
            ],
            ["BIASFACTOR (production)", "10", "Miguel email 2026-04-23"],
            [
              "PACE (production)",
              "1000 steps = 1 hill / 2 ps",
              "SI",
            ],
            ["Walker count", "10", "SI"],
            ["WALKERS_RSTRIDE", "3000 steps = 6 ps", "SI"],
            [
              "UPPER_WALLS on z",
              "AT=2.5 A^2, KAPPA=800 kcal/mol/A^4",
              "SI Methods",
            ],
            [
              "Conventional MD",
              "500 ns AMBER pmemd.cuda",
              "SI Methods (per-system pre-MetaD)",
            ],
            [
              "WT-MetaD walker time budget",
              "50 ns per walker",
              "SI",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 60 } }),
        para(
          "Author-clarified parameters that the SI does not state numerically (HEIGHT=0.15 vs FALLBACK 0.3, KAPPA=800, NEIGH_STRIDE, NEIGH_SIZE, SIGMA_MIN per axis, the upper-wall constants) are documented as 'author-clarified per Miguel email 2026-04-23' in the PLUMED template header."
        ),

        heading("Attached Figures", 1),
        para(
          "Figure 1 — reports/figures/before_after_fp034.png. " +
            "Two-panel side-by-side comparison of the Initial pilot s-vs-time trajectory."
        ),
        para(
          "Source data. Left panel: pre-realignment baseline single-walker pilot COLVAR from before this week's path-builder fix (the legacy run that stayed at s less than 1.9 over 17 ns). " +
            "Right panel: current 24 ns Initial pilot COLVAR (reports/figures/raw_data/longleaf_initial_seqaligned_COLVAR, frozen Longleaf snapshot 2026-04-25 11:49 EDT, 24.03 ns of MetaDynamics, 12,015 Gaussian deposits)."
        ),
        para(
          "Transformation. From each COLVAR, read columns 1, 2 and 3 (time in ps, s in dimensionless path units, z in Angstroms squared) and plot s vs time in the corresponding panel. " +
            "Horizontal dashed reference lines at s=2 (O boundary), s=6 (PC), s=10 (C). " +
            "Per-panel annotation reports the walker's max(s) value."
        ),
        para(
          "Figure 2 — reports/figures/initial_pilot_latest_fes.png. " +
            "Latest Initial pilot 2D free energy surface at 24 ns, single-walker, in the JACS 2019 SI Fig S2/S3 style."
        ),
        para(
          "Source data. reports/figures/raw_data/fes_initial_seqaligned_sumhills.dat. " +
            "Produced by running plumed sum_hills --hills longleaf_initial_seqaligned_HILLS --kt 0.695 --mintozero on a compute node, on the same frozen 24.03 ns Longleaf snapshot used in Figure 1."
        ),
        para(
          "Transformation. The .dat file is a regular grid of s, z, ΔG values. I plot it with matplotlib pcolormesh; x-axis is s (path coordinate, dimensionless), y-axis is z RMSD in Angstroms (computed as the square root of the raw MSD column z to give a length-scale axis), color is ΔG in kcal/mol with the colorbar capped at 30. " +
            "The figure differs from the published Fig S2 because (a) Fig S2 aggregates 10 walkers over 50 ns each (~500 ns total), and (b) my pilot is single-walker at 24 ns of the upstream FALLBACK contract; the overall basin shape and assignments are consistent."
        ),
        heading("References", 1),
        para(
          "1. Maria-Solano, M. A. et al. Enzyme conformational dynamics in the catalytic cycle of tryptophan synthase. JACS 141, 13049-13056 (2019). DOI: 10.1021/jacs.9b03646. Reference protocol I am replicating."
        ),
        para(
          "2. Branduardi, D., Gervasio, F. L. and Parrinello, M. From A to B in free energy space. J. Chem. Phys. 126, 054103 (2007). DOI: 10.1063/1.2432340. Defines the path-CV LAMBDA = 2.3 / mean adjacent MSD."
        ),
        para(
          "3. Tribello, G. A. et al. PLUMED 2: New feathers for an old bird. Comput. Phys. Commun. 185, 604-613 (2014). DOI: 10.1016/j.cpc.2013.09.018. The PLUMED engine I use for the bias."
        ),
        para(
          "4. Henzler-Wildman, K. and Kern, D. Dynamic personalities of proteins. Nature 450, 964-972 (2007). DOI: 10.1038/nature06522. Establishes that enzyme function is governed by inter-state transition rates, not single-state occupancy."
        ),
        para(
          "5. Boehr, D. D. et al. The dynamic energy landscape of dihydrofolate reductase catalysis. Science 313, 1638-1642 (2006). DOI: 10.1126/science.1130258. Direct evidence linking conformational transition rates to catalytic activity."
        ),
        para(
          "6. Yang, J., Chu, W., Khalil, D., Astudillo, R., Wittmann, B. J., Arnold, F. H. and Yue, Y. Steering Generative Models with Experimental Data for Protein Fitness Optimization. NeurIPS 2025. arXiv:2505.15093. Plug-and-play classifier guidance / posterior sampling on discrete-diffusion protein language models, benchmarked on TrpB and CreiLOV at small N (~hundreds of labels). Supports the small-N feasibility for my Stage 1."
        ),
        para(
          "7. Stocco, F., Artigues-Lleixa, M., Hunklinger, A., Widatalla, T., Guell, M. and Ferruz, N. Guiding Generative Protein Language Models with Reinforcement Learning. arXiv:2412.12979 (2024). Implements wDPO and GRPO RL fine-tuning of protein LMs (ZymCTRL family); produced low-nM EGFR binders. Reference recipe for my Stage 3 RL upper bound."
        ),
        para(
          "8. Lambert, S. M. et al. Generative protein language modeling for tryptophan synthase variants. arXiv (2026). Supplies the 25M GenSLM checkpoint that Phase 2 targets."
        ),
        para(
          "9. ByteDance Seed and collaborators. Scalable Spatio-Temporal SE(3) Diffusion for Long-Horizon Protein Dynamics. arXiv:2602.02128 (Feb 2026). Causal SE(3)-equivariant diffusion transformer that rolls out microsecond-scale all-atom protein trajectories from a sequence. Discussed in Section 2.4 as orthogonal: their direction is sequence to MD trajectory; mine is MD trajectory to sequence-scoring reward."
        ),
        para(
          "10. Turner, A. M., Thiergart, G., Leech, G., Udell, D., Vazquez, J. J., Mini, U. and MacDiarmid, M. Steering Language Models With Activation Engineering. arXiv:2308.10248 (Aug 2023; v4 retitled Activation Addition: Steering Language Models Without Optimization). Adds a contrastively-derived steering vector to the residual stream at inference; weights stay frozen. Reference recipe for my Stage 2."
        ),
        para(
          "11. Zou, A., Phan, L., Chen, S. et al. Representation Engineering: A Top-Down Approach to AI Transparency. arXiv:2310.01405 (Oct 2023). Identifies and manipulates population-level internal representations to steer high-level concepts in language models. Companion reference for my Stage 2."
        ),
        para(
          "12. Liu, S.-Y., Wang, C.-Y., Yin, H., Molchanov, P., Wang, Y.-C. F., Cheng, K.-T. and Chen, M.-H. DoRA: Weight-Decomposed Low-Rank Adaptation. ICML 2024 Oral. arXiv:2402.09353. Decomposes pretrained weights into magnitude and direction; LoRA only on direction. Preferred adapter for my Stage 3 weight-level adjustment."
        ),
        para(
          "13. Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L. and Chen, W. LoRA: Low-Rank Adaptation of Large Language Models. arXiv:2106.09685 (June 2021); ICLR 2022. The original low-rank adapter recipe that PiSSA, DoRA, and LoRA+ refine."
        ),
        para(
          "14. Meng, F., Wang, Z. and Zhang, M. PiSSA: Principal Singular Values and Singular Vectors Adaptation of Large Language Models. arXiv:2404.02948 (2024). Initializes the LoRA matrices from the SVD of the pretrained weights so the adapter trains principal directions instead of random/zero updates. Preferred Stage 3 adapter for my plan."
        ),
        para(
          "15. Hayou, S., Ghosh, N. and Yu, B. LoRA+: Efficient Low Rank Adaptation of Large Models. arXiv:2402.12354 (2024). Provides a corrected learning-rate / scaling rule for the original LoRA decomposition; used as the safe baseline alongside the original LoRA."
        ),
        para(
          "16. Wu, Z., Arora, A., Wang, Z. et al. ReFT: Representation Finetuning for Language Models. arXiv:2404.03592 (2024). Discussed in Section 2.4 as a representation-level alternative that composes naturally with my Stage 2 activation steering."
        ),
      ],
    },
  ],
});

// write
const outPath = path.resolve(
  __dirname,
  "..",
  "WeeklyReport_Week8_2026-05-01.docx"
);

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outPath, buffer);
  console.log("Saved:", outPath);
  console.log("Size:", buffer.length, "bytes");
});
