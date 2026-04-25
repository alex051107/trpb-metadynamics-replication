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
              "Week 8: SI-faithful 10-walker production + ML cartridge V1 contract",
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
          "Phase 2: Apply to GenSLM-designed enzymes (V1 ship target 2026-07-18)"
        ),
        para("Phase 3: Build reward function for design loop (V2)"),

        heading("Summary", 1),
        para(
          "This week the central focus was getting the 10-walker MetaDynamics production stage to actually run under the published protocol. " +
            "The first launch (v1) was cancelled because all 10 walkers used the same starting frame and stayed trapped at the open conformation. " +
            "The second launch (v2) crashed within 12 minutes with LINCS bond-stress on three atoms."
        ),
        para(
          "I diagnosed both root causes and built a v3 design that adds an energy minimization plus 100 ps NVT pre-equilibration before the MetaDynamics phase. " +
            "The smoke test passed on all 10 walkers and the production array (SLURM 45784112) is running now."
        ),
        para(
          "The main unresolved question is whether the production run will reach the convergence gate by the May 1 group meeting. " +
            "The honest answer is no: with a 24-hour wall budget I expect roughly 20 ns per walker by meeting time, well short of the 45 ns per walker that the SI convergence diagnostic needs. " +
            "I will ship a PROVISIONAL early-stage figure with the convergence_grade flag set accordingly, and ask the lab whether to extend wall time or accept the PROVISIONAL ship."
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
              "Designed 4-tier ML conversion framework (L0 to L3) and wrote schemas",
              "Documentation",
              "Done",
            ],
            [
              "13",
              "Conducted 8 rounds of cross-audit on ML schemas plus 1 independent second-pass",
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
              "Rendered the latest Initial pilot FES at 24 ns with proper RMSD axis units",
              "Analysis",
              "Done",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 60 } }),

        heading("What I Learned", 1),

        heading(
          "1. FP-034 path realignment was the campaign's largest single-point delta",
          2
        ),
        para(
          "The published path coordinate uses 15 frames between an open structure (1WDW chain B, P. furiosus TrpB) and a closed structure (3CEP chain B, S. typhimurium TrpB). " +
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
          "The design constraint that frames everything else. " +
            "By the time I am ready to plug this back into the GenSLM-25M sequence generator (Lambert et al. 2026), I will have on the order of 30 to 50 labeled (sequence, MetaDynamics-output) pairs, not thousands. " +
            "That sample size rules out approaches that fine-tune the generator's weights directly. " +
            "The plan I want to commit to is: leave GenSLM unchanged, treat the 30 to 50 labeled pairs as a preference direction that steers the generator's output at generation time, and grow the labeled set through an active-learning loop that adds new pairs after each round of MetaDynamics. " +
            "Published precedents for small-N steering on protein language models came out in the last 12 months (Yang et al., NeurIPS 2025; Stark et al. 2024); I plan to walk through the choice between candidate methods at the feasibility meeting next week."
        ),
        para(
          "What is NOT being claimed. " +
            "The reward weights have not yet been calibrated against measured TrpB k_cat values; that calibration is a near-term task once production gives me one or two converged free energy surfaces. " +
            "The small-N steering approach has not been benchmarked on GenSLM specifically. " +
            "The simplest baseline (just rerank GenSLM's outputs by a generic protein-language-model likelihood) must be measured first; the more elaborate approach earns its compute budget only if it beats that baseline. " +
            "Phase 2 also depends on the activity-proxy decision (MMPBSA rank, literature k_cat, or hand-binned classes) called out in the open questions section."
        ),

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
          "1. Activity proxy choice. Is the V1 supervised target Yu's MMPBSA rank, experimental k_cat where measured, or hand-binned activity classes? " +
            "Without an answer, the L2 column is undefined and V1 ships descriptor-only."
        ),
        para(
          "2. Wall-clock budget for production. A 24-hour wall budget gives roughly 20 ns per walker. " +
            "The published convergence gate is 45 ns per walker with the |delta-delta-G_PC-O(50ns) - delta-delta-G_PC-O(40ns)| less than 0.5 kcal/mol plateau test (JACS 2019 SI Fig S4). " +
            "Do I extend wall to 72 hours, or accept a PROVISIONAL ship at 20 ns per walker for the May 1 deck?"
        ),
        para(
          "3. GenSLM column populated or null in V1. Lambert 2026 supplies a 25M-parameter checkpoint with d_model and pooling rule both unstated. " +
            "I have a one-shot extraction script that pulls hidden_size from any config.json on the GitHub repo. " +
            "Is V1 narrative shape F0+state-pseudo-labels with GenSLM null, or delay V1 by 3 weeks for full populate?"
        ),
        para(
          "4. Walker 9 monitoring. If walker 9 collapses against UPPER_WALLS in the next 24 hours, the documented fallback is to extend the pilot to 30 ns and re-materialize. " +
            "Is there a shorter-loop fallback the lab prefers?"
        ),
        para(
          "5. Convergence grading at the May 1 meeting. " +
            "Production cannot reach 45 ns per walker by May 1. " +
            "The deck figure will carry convergence_grade=PROVISIONAL per JACS 2019 SI Fig S4 / S5 methodology. " +
            "Is the lab comfortable shipping at PROVISIONAL with the kill-switch wiring documented, or should I delay the deck until convergence PASSes?"
        ),

        heading("Next Week Plan", 1),
        heading("Papers to read", 2),
        para(
          "Lambert et al. 2026 (GenSLM-25M-TrpB): I have read the methods but want to fully resolve Fig 2A's t-SNE pooling rule before the V1 GenSLM-column decision."
        ),
        heading("Tasks", 2),
        para(
          "1. Monitor production 45784112 to 10 ns per walker (ETA 2026-04-26 morning EDT). " +
            "Auto-render the SI-comparable production FES via plumed sum_hills on a compute node."
        ),
        para(
          "2. Land 3 remaining deck figures: 10-walker explore progress, before/after FP-034 comparison, and ML 4-tier schematic."
        ),
        para(
          "3. Run the GenSLM hidden_size one-shot extraction script. " +
            "If it returns a single integer, populate INTERFACE BLOCKED #1 mechanically; if not, escalate to the GenSLM authors."
        ),
        para(
          "4. Monitor convergence diagnostics: ESS per state, block-bootstrap CI, and the |delta-delta-G(t) - delta-delta-G(t-10)| plateau test from JACS 2019 SI Fig S4."
        ),
        para(
          "5. Group meeting May 1: walk through the deck, surface the 5 PM decisions, get the activity-proxy answer."
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
          "6. Yang, J. et al. Steering generative models with experimental data for protein fitness optimization. NeurIPS 2025. arXiv:2505.15093. Benchmarks plug-and-play steering on TrpB at small N; supports the no-fine-tune Phase 2 plan."
        ),
        para(
          "7. Stark, P. et al. ProtRL: Guiding generative protein LMs with reinforcement learning. arXiv:2412.12979 (2024). Recipe for RL on protein LMs once the labeled set is large enough."
        ),
        para(
          "8. Lambert, S. M. et al. Generative protein language modeling for tryptophan synthase variants. arXiv (2026). Supplies the 25M GenSLM checkpoint that Phase 2 targets."
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
