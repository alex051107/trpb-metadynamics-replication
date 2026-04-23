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
            ["Date", "April 18, 2026"],
            [
              "Week",
              "Week 6: SI parameter fixes + OpenMM/PLUMED porting",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 120 } }),

        // summary
        heading("Summary", 1),
        para(
          "This week had three threads. " +
            "First, I added SIGMA floor parameters to the PLUMED metadynamics (a bias-adding sampling method) script because the single-walker job was stuck in the open basin and the published SI did not quote numerical SIGMA values. " +
            "Second, I sent a question email to the JACS 2019 first author and began a follow-up to the second author after the first did not reply."
        ),
        para(
          "Third, I built a clean OpenMM 8.4 conda environment with openmm-plumed (a plugin that lets OpenMM call PLUMED) and verified two toy alanine-dipeptide runs on the CPU queue. " +
            "The CUDA build is blocked by a driver-PTX mismatch that I have a fix path for."
        ),
        para(
          "One note: I am in a round of finals this week, which compressed the available research time."
        ),

        // work done
        heading("Work Done", 1),
        makeTable(
          ["#", "Task", "Category", "Status"],
          [
            [
              "1",
              "Add SIGMA_MIN=0.3,0.005 + SIGMA_MAX=1.0,0.05 floors to plumed.dat",
              "Parameter fix",
              "Done",
            ],
            [
              "2",
              "Submit Job 43813633 (10 ns probe) then Job 44008381 (50 ns extension)",
              "Simulation",
              "Running",
            ],
            [
              "3",
              "Email Maria-Solano (1st author) about alignment and SIGMA",
              "Communication",
              "Sent, no reply",
            ],
            [
              "4",
              "Attempt 2nd-author contact (Iglesias-Fernandez); both addresses bounced",
              "Communication",
              "Dropped",
            ],
            [
              "5",
              "Build md_setup_trpb conda env with OpenMM 8.4 + openmm-plumed 2.1",
              "Environment",
              "Done",
            ],
            [
              "6",
              "Run toy_cmd.py and toy_metad.py on alanine dipeptide (Job 44296608, CPU)",
              "Validation",
              "Done",
            ],
            [
              "7",
              "Group meeting with Dr. Zhang and John (April 17)",
              "Meeting",
              "Done",
            ],
            [
              "8",
              "Read ByteDance STAR-MD preprint (arXiv 2602.02128)",
              "Paper",
              "In progress",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 60 } }),

        // what i learned
        heading("What I Learned", 1),

        heading("1. SIGMA floors and our deviations from the SI", 2),
        para(
          "The JACS 2019 SI protocol lists ADAPTIVE=GEOM for the Gaussian widths but does not quote the numerical SIGMA values used during the published run. " +
            "My single-walker job kept oscillating near s(R)=0.2 with z(R) small and never climbed out of the open basin. " +
            "I decided this was an under-deposition problem: the adaptive SIGMA was shrinking too aggressively so the bias potential never accumulated enough to push the system over the transition region."
        ),
        para(
          "I added two floors to the PLUMED script: SIGMA_MIN=0.3,0.005 and SIGMA_MAX=1.0,0.05 for the s and z axes. " +
            "I want to be explicit with the advisors that these numbers are my choice and not a literal reading of the SI. " +
            "The first resubmission (Job 43813633, 10 ns) reached max s=1.393, which was the first time the system left the open basin. " +
            "The follow-up extension (Job 44008381) is now around 45 of 50 ns with max s plateaued at 4.1."
        ),
        para(
          "I re-read SI p.S4 to decide whether this run is good enough to launch the 10-walker stage. " +
            "The SI says: 'After an initial metadynamics run, we extracted ten snapshots for each system covering approximately all the conformational space available.' " +
            "The same page defines the s(R) axis as open = 1-5, partially closed = 5-10, closed = 10-15. " +
            "In other words, the 10 starting snapshots must span s(R) roughly 1 to 15 across the O, PC, and C basins. " +
            "My current max s(R) is 4.1, which is still inside the O basin. " +
            "So by the SI criterion the initial run is not done yet. " +
            "The plateau at s=4.1 means either the current SIGMA floors are still too narrow for the deposition to push the walker past the O-to-PC transition, or the walker needs substantially longer than 50 ns to sample PC and C. " +
            "Launching the 10-walker production now would violate the SI protocol because the starting snapshots would only cover O."
        ),

        heading("2. Emails to the Osuna group", 2),
        para(
          "I sent a question email to Dr. Miguel A. Maria-Solano (first author of the JACS 2019 paper) on April 17. " +
            "The send went through cleanly but there has been no reply by April 18 morning. " +
            "I also tried two addresses for Dr. Iglesias-Fernandez (second author) and both bounced, so I am dropping that channel and will send directly to Prof. Silvia Osuna at silvia.osuna@udg.edu if Dr. Maria-Solano does not reply by April 21."
        ),
        para(
          "I am asking two concrete questions. " +
            "First: what structural alignment protocol was used to build the 15-frame reference path between 1WDW (open) and 3CEP (closed), and was any PLUMED runtime alignment used in addition to offline alignment. " +
            "This matters because our projected s(R) values differ from Figure 2a of the paper by roughly 10 percent at the same endpoints, which is the kind of offset an alignment-method difference produces. " +
            "Second: what numerical SIGMA, SIGMA_MIN, and SIGMA_MAX values were used in the published run. " +
            "The SI describes only the adaptive width scheme qualitatively and does not quote numbers."
        ),

        heading("3. OpenMM plus PLUMED toy project", 2),
        para(
          "I built a new conda environment called md_setup_trpb using the conda-forge channel. " +
            "Packages: OpenMM 8.4 plus openmm-plumed 2.1. " +
            "This is the official conda-forge install path, so nothing is compiled from source at this stage."
        ),
        para(
          "I then ran two toy scripts on a 22-atom alanine dipeptide system. " +
            "toy_cmd.py confirmed that ff14SB loads through OpenMM and that the LangevinMiddle integrator runs 50 ps without numerical issues. " +
            "toy_metad.py confirmed that openmm-plumed PlumedForce deposits Gaussian hills and writes a COLVAR file in the same format our GROMACS runs produce. " +
            "Job 44296608 ran on a CPU node of Longleaf and returned both TOY_CMD_OK and TOY_METAD_OK tags."
        ),
        para(
          "The CUDA path is currently blocked. " +
            "I logged this as FP-028. " +
            "conda-forge pulled cuda-nvrtc 13.2 as a default dependency. " +
            "Longleaf A100 cards support up to CUDA 13.0 PTX at the driver level, so the newer runtime crashes at kernel load. " +
            "The fix is to pin cuda-version=12 when creating the environment. " +
            "I will redo the env build next week."
        ),

        // resources needed
        heading("Resources Needed", 1),
        para(
          "Dr. Yu Zhang: please send the desktop access link for the lab OpenMM workstation. " +
            "I would like to mirror the environment there and verify configuration against a system that has confirmed CUDA working, so my Longleaf driver issue (FP-028) is not a single point of failure for the OpenMM porting path."
        ),

        // next week plan
        heading("Next Week Plan", 1),
        para(
          "1. Monitor Job 44008381 to the 50 ns gate. " +
            "Per SI p.S4, the initial run has to cover s(R) roughly 1 to 15 (O plus PC plus C) before the 10 starting snapshots can be extracted. " +
            "If the run ends still plateaued inside O (max s well below 10), raise SIGMA_MIN and extend, rather than forcing an underpowered 10-walker launch."
        ),
        para(
          "2. Fix the CUDA block by pinning cuda-version=12 in a fresh md_setup_trpb build. " +
            "Then re-run toy_metad.py on a GPU node to confirm the openmm-plumed GPU path works."
        ),
        para(
          "3. If Dr. Maria-Solano has not replied by April 21, send the same question list directly to Prof. Silvia Osuna."
        ),
        para(
          "4. Only after the single-walker trajectory covers s(R) roughly 1 to 15, extract 10 snapshots spanning O / PC / C (per SI p.S4) and launch the 10-walker production run on Longleaf."
        ),
        para(
          "5. Continue reading the ByteDance STAR-MD preprint (arXiv 2602.02128). " +
            "Target: working-level pass by April 25."
        ),
        para(
          "One open direction question, based on the Slack thread between Amin, Arvind, and Prof. Anandkumar. " +
            "The thread narrowed the lab's angle toward a sequence-conditioned Recurrent Neural Operator (RNO) that parameterizes the Mori-Zwanzig memory kernel K(t-tau) on protein language model embeddings, with STAR-MD's diffusion-based side-chain repacking and coarse-graining treated as complementary pieces rather than the core novelty. " +
            "The stated targets are long-horizon prediction, cross-family generalization (with Arvind's enzyme-family MD dataset as training signal), and recovering conformational substates that currently require metadynamics. " +
            "I would appreciate a short read on which part each of you wants me to push on next: (a) generate TrpB metadynamics trajectories as one of the cross-family validation targets for the sequence-conditioned RNO, (b) study the coarse-grained representation choice and its effect on the Markovian-vs-non-Markovian assumption, or (c) keep digging into STAR-MD as reference implementation for the diffusion and repacking pieces. " +
            "This would let me align my TrpB effort with the model side rather than reading breadth-first."
        ),

        // openmm environment configuration
        heading("OpenMM Environment Configuration", 1),
        makeTable(
          ["Item", "Value", "Note"],
          [
            [
              "Conda env name",
              "md_setup_trpb",
              "Built under /work/users/l/i/liualex/conda/envs/",
            ],
            [
              "Python",
              "3.11",
              "Pinned by openmm-plumed solver",
            ],
            [
              "Conda channel",
              "conda-forge only",
              "Official install path per the openmm-plumed GitHub README",
            ],
            [
              "Install command",
              "mamba install -c conda-forge openmm openmm-plumed plumed",
              "Single line, no manual version pins on first attempt",
            ],
            [
              "OpenMM version",
              "8.4.0",
              "Solver picked this as the latest stable on conda-forge (2026-04)",
            ],
            [
              "openmm-plumed version",
              "2.1",
              "Plugin that injects a PLUMED script as an OpenMM Force",
            ],
            [
              "PLUMED (bundled)",
              "2.9.2",
              "Pulled in as a dependency of openmm-plumed; matches our Longleaf GROMACS+PLUMED stack",
            ],
            [
              "AmberTools (for tleap)",
              "24",
              "Needed to generate the alanine dipeptide PDB with correct column alignment",
            ],
            [
              "GPU platform",
              "CUDA",
              "Blocked (FP-028). See conda-env section below.",
            ],
            [
              "CPU platform",
              "Working",
              "69.2 ns/day on 22-atom alanine dipeptide",
            ],
            [
              "Toy script 1",
              "replication/openmm_toy/toy_cmd.py",
              "Vacuum NVT, 50 ps, ff14SB, TOY_CMD_OK",
            ],
            [
              "Toy script 2",
              "replication/openmm_toy/toy_metad.py",
              "PlumedForce with METAD block, 50 Gaussians deposited, TOY_METAD_OK",
            ],
            [
              "SLURM script",
              "replication/openmm_toy/submit_toy.sbatch",
              "Job 44296608 on general partition (CPU)",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 120 } }),

        // references
        heading("References", 1),
        para(
          "1. Maria-Solano et al. Enzyme Conformational Dynamics in the Catalytic Cycle of Tryptophan Synthase. " +
            "JACS 141 (2019): 13049-13056."
        ),
        para(
          "2. Eastman et al. OpenMM 8: Molecular Dynamics Simulation with Machine Learning Potentials. " +
            "J. Phys. Chem. B 128 (2024): 109-117."
        ),
        para(
          "3. Tribello et al. PLUMED 2: New Feathers for an Old Bird. " +
            "Comput. Phys. Commun. 185 (2014): 604-613."
        ),
      ],
    },
  ],
});

// write
const outPath = path.resolve(
  __dirname,
  "..",
  "WeeklyReport_Week6_2026-04-18.docx"
);

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outPath, buffer);
  console.log("Saved:", outPath);
  console.log("Size:", buffer.length, "bytes");
});
