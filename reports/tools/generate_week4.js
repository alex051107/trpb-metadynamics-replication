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

// ── helpers ──────────────────────────────────────────────────
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
        size: level === 1 ? 28 : 24, // half-points: 14pt / 12pt
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
        size: 22, // 11pt
        color: BLACK,
        bold: opts.bold || false,
        italics: opts.italic || false,
      }),
    ],
  });
}

function multiRunPara(runs, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.afterSpacing || 120 },
    children: runs.map(
      (r) =>
        new TextRun({
          text: r.text,
          font: FONT,
          size: r.size || 22,
          color: BLACK,
          bold: r.bold || false,
          italics: r.italic || false,
        })
    ),
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

// ── document ─────────────────────────────────────────────────

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
        // ── HEADER TABLE ──
        makeTable(
          ["Field", "Value"],
          [
            ["Date", "April 4, 2026"],
            [
              "Week",
              "Week 4: Classical MD Complete + MetaDynamics Pipeline",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 120 } }),

        // ── SUMMARY ──
        heading("Summary", 1),
        para(
          "The 500 ns classical MD run for PfTrpB(Ain) finished this week. " +
            "I then switched from AMBER to GROMACS+PLUMED for the MetaDynamics phase. " +
            "ParmEd handled the format conversion without issues."
        ),
        para(
          "The majority of my time this week was spent resolving three compatibility issues between GROMACS 2026 and PLUMED 2.9. " +
            "Each required extended debugging because the error messages were misleading. " +
            "All three are now resolved. " +
            "A single-walker MetaDynamics job is running on Longleaf as of today (s=7.8, z=0.5 nm after 55 min). " +
            "These early CV values are physically reasonable."
        ),

        // ── WORK DONE ──
        heading("Work Done", 1),
        makeTable(
          ["#", "Task", "Category", "Status"],
          [
            [
              "1",
              "500 ns NVT production MD (PfTrpB-Ain, 39268 atoms, Job 40806029)",
              "Simulation",
              "Done",
            ],
            [
              "2",
              "Group meeting with Dr. Zhang and Amin (April 2)",
              "Meeting",
              "Done",
            ],
            [
              "3",
              "AMBER-to-GROMACS format conversion via ParmEd",
              "Setup",
              "Done",
            ],
            [
              "4",
              "Debug FP-018: LAMBDA unit conversion (\u00C5 to nm)",
              "Debugging",
              "Done",
            ],
            [
              "5",
              "Debug FP-019: GROMACS 2026 PLUMED line-continuation syntax",
              "Debugging",
              "Done",
            ],
            [
              "6",
              "Debug FP-020: conda PLUMED missing modules; build from source",
              "Debugging",
              "Done",
            ],
            [
              "7",
              "Submit single-walker MetaDynamics (Job 41500355)",
              "Simulation",
              "Running",
            ],
            [
              "8",
              "Write TrpB Replication Tutorial (EN + CN)",
              "Documentation",
              "In Process",
            ],
          ]
        ),
        new Paragraph({ spacing: { after: 60 } }),

        para(
          "Job 40806029 finished in 71.55 hours at 167.72 ns/day on a single GPU. " +
            "That gives us the equilibrated PfTrpB(Ain) structure we need as the MetaDynamics starting point."
        ),
        para(
          "The AMBER-to-GROMACS format conversion completed without issues. " +
            "ParmEd read the topology and restart files and wrote out GROMACS-compatible inputs directly."
        ),
        para(
          "For the path collective variable, I interpolated 15 reference structures between the open conformation (1WDW) and the closed conformation (3CEP). " +
            "These use 112 C\u03B1 atoms from the COMM domain (residues 97-184) to define the reaction coordinate."
        ),
        para(
          "Debugging the three GROMACS-PLUMED compatibility issues occupied Thursday and Friday. " +
            "Details are in the Problems section below."
        ),
        para(
          "The MetaDynamics simulation is now running with parameters matching the SI protocol. " +
            "Adaptive Gaussian widths (ADAPTIVE=GEOM) are enabled. " +
            "Early CV values are consistent with expectations."
        ),
        para(
          "On April 2 I met with Dr. Zhang and Amin. " +
            "Dr. Zhang confirmed the Gaussian input setup for the PLP charge calculation and shared the lab's existing AMBER MD pipeline."
        ),

        // ── PROBLEMS ENCOUNTERED ──
        heading("Problems Encountered", 1),

        heading("Problem 1: Unit mismatch between simulation engines", 2),
        para(
          "z(R) returned a value of -78, when the expected value was approximately 0.5. " +
            "This indicated a problem with the LAMBDA parameter."
        ),
        para(
          "AMBER uses angstroms and GROMACS uses nanometers. " +
            "I had calculated LAMBDA=0.034 on the AMBER side (in \u00C5\u207B\u00B2) and transferred it directly into the PLUMED input without unit conversion. " +
            "This made the exponential kernel 100x too flat, so the path function could not distinguish between reference frames."
        ),
        para(
          "This was resolved by multiplying LAMBDA by 100 when converting from \u00C5\u207B\u00B2 to nm\u207B\u00B2 (0.034 becomes 3.39). " +
            "After correction, z(R) returned to ~0.5 nm as expected. " +
            "I now maintain a unit conversion checklist for any parameter crossing the AMBER-to-GROMACS boundary."
        ),

        heading("Problem 2: PLUMED input parsing through GROMACS interface", 2),
        para(
          "PLUMED .dat files normally support backslash line continuation. " +
            "Standalone plumed driver handles this correctly. " +
            "However, GROMACS 2026 pre-processes the input when loading PLUMED as a plugin and silently drops everything after the backslash."
        ),
        para(
          "I encountered a misleading error (\"SIGMA is compulsory\") because SIGMA was on a continuation line that GROMACS truncated. " +
            "Initially this suggested ADAPTIVE=GEOM was unsupported, but it functions correctly once all parameters are placed on a single line. " +
            "The root cause of why GROMACS handles the backslash differently from standalone PLUMED remains unclear."
        ),

        heading("Problem 3: Incomplete PLUMED shared library from conda", 2),
        para(
          "I first attempted to use the conda-forge PLUMED 2.9.2 package. " +
            "The command-line tool (plumed driver) worked correctly, but gmx mdrun -plumed failed silently. " +
            "After investigation, I determined the issue was in the shared library (libplumedKernel.so) that GROMACS loads at runtime."
        ),
        para(
          "The conda build compiles the CLI with all features, but the shared library is missing key modules (PATHMSD and METAD among them). " +
            "I compiled PLUMED 2.9.2 from source on Longleaf and set PLUMED_KERNEL to point to the new library, which resolved the issue."
        ),
        para(
          "A separate issue arose with PATHMSD and atom indexing. " +
            "PATHMSD reads a multi-model PDB with all 15 reference frames and matches atoms by serial number. " +
            "Our 112 C\u03B1 atoms have non-sequential serials (1614, 1621, 1643, etc.) scattered across a 39,268-atom system. " +
            "Through gmx mdrun, PATHMSD reported zero atoms per frame, though the same file worked correctly in standalone mode."
        ),
        para(
          "I switched to FUNCPATHMSD, which uses 15 individual RMSD calculations with single-frame PDB files. " +
            "Non-sequential atom serials are handled correctly with this approach. " +
            "The path function combines the 15 RMSD values into s(R) and z(R) using the same formula as PATHMSD."
        ),

        // ── OPEN QUESTIONS ──
        heading("Open Questions", 1),
        para(
          "1. FUNCPATHMSD vs PATHMSD. " +
            "I switched to FUNCPATHMSD because of the atom-indexing issue described in Problem 3. " +
            "This was a practical workaround; the underlying math is identical, as s(R) and z(R) are computed the same way."
        ),
        para(
          "I plan to verify whether the separate RMSD alignment steps in FUNCPATHMSD introduce any subtle numerical differences. " +
            "I will run a short test using both methods through plumed driver and compare the outputs directly."
        ),
        para(
          "2. MSD discrepancy with the published value. " +
            "The SI reports MSD=80 \u00C5\u00B2 between successive path frames (\u03BB=0.029 \u00C5\u207B\u00B2). " +
            "I obtain MSD=67.8 \u00C5\u00B2 (\u03BB=0.034 \u00C5\u207B\u00B2), which is 17% higher. " +
            "One possible explanation is that the SI does not specify how they aligned 1WDW and 3CEP before interpolation (the two structures come from different species). " +
            "Whole-chain alignment instead of COMM-domain-only alignment could bring our MSD closer to 80. " +
            "I plan to test this hypothesis."
        ),

        // ── NEXT WEEK ──
        heading("Next Week", 1),
        para(
          "Job 41500355 should finish in approximately 17 hours. " +
            "Once complete, I will run plumed sum_hills to reconstruct the free energy surface. " +
            "The priority is to determine whether the O and C basins appear at the expected s(R) positions. " +
            "If so, I will proceed to set up the 10-walker production run."
        ),
        para(
          "I also plan to review Dr. Zhang's md_setup pipeline, which may simplify future system preparation compared to following the JACS 2019 SI protocol manually."
        ),
        para(
          "The Replication Tutorial (EN and CN) remains on hold pending MetaDynamics results."
        ),
      ],
    },
  ],
});

// ── write ────────────────────────────────────────────────────
const outPath = path.resolve(
  __dirname,
  "..",
  "WeeklyReport_Week4_2026-04-04.docx"
);

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync(outPath, buffer);
  console.log("Saved:", outPath);
  console.log("Size:", buffer.length, "bytes");
});
