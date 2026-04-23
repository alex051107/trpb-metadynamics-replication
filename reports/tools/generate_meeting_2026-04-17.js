const docx = require("docx");
const fs = require("fs");
const path = require("path");

const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  WidthType,
  BorderStyle,
  HeadingLevel,
  convertInchesToTwip,
} = docx;

const FONT = "Arial";
const BLACK = "000000";

function heading(text, level) {
  return new Paragraph({
    heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 300 : 220, after: 140 },
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
    spacing: { after: opts.afterSpacing || 140, line: 300 },
    children: [
      new TextRun({
        text,
        font: FONT,
        size: 22,
        color: BLACK,
        bold: opts.bold || false,
      }),
    ],
  });
}

function numberedItem(num, text) {
  return new Paragraph({
    spacing: { after: 100, line: 300 },
    indent: { left: 360, hanging: 360 },
    children: [
      new TextRun({
        text: `${num}. ${text}`,
        font: FONT,
        size: 22,
        color: BLACK,
      }),
    ],
  });
}

function headerLine(label, value) {
  return new Paragraph({
    spacing: { after: 80, line: 260 },
    children: [
      new TextRun({
        text: `${label}: `,
        bold: true,
        font: FONT,
        size: 22,
        color: BLACK,
      }),
      new TextRun({
        text: value,
        font: FONT,
        size: 22,
        color: BLACK,
      }),
    ],
  });
}

function hrParagraph() {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    border: {
      bottom: { color: BLACK, space: 1, style: BorderStyle.SINGLE, size: 6 },
    },
  });
}

const children = [];

// ── Title ─────────────────────────────────────────────
children.push(
  new Paragraph({
    spacing: { after: 200 },
    children: [
      new TextRun({
        text: "Meeting Notes 2026-04-17",
        bold: true,
        font: FONT,
        size: 32,
        color: BLACK,
      }),
    ],
  })
);

// ── Header info ──
children.push(headerLine("Date", "April 17, 2026"));
children.push(headerLine("Attendees", "Alex Liu, Yu Zhang"));
children.push(headerLine("Format", "1-on-1, ~15 min"));
children.push(hrParagraph());

// ── Summary ──
children.push(heading("Summary", 1));
children.push(
  para(
    "Walked through why Job 42679152 (50 ns single walker) finished mechanically but stayed stuck in the O basin, and the SIGMA fix deployed April 15. Job 44008381 is the 50 ns continuation from the 10 ns probe checkpoint; at meeting time it had reached 27.68 ns with max s(R) = 3.49."
  )
);

// ── Discussion ──
children.push(heading("Discussion", 1));

function bullet(text) {
  return new Paragraph({
    spacing: { after: 100, line: 300 },
    indent: { left: 360, hanging: 240 },
    children: [
      new TextRun({ text: "• ", font: FONT, size: 22, color: BLACK }),
      new TextRun({ text, font: FONT, size: 22, color: BLACK }),
    ],
  });
}

children.push(
  bullet(
    "Why the last job got stuck. SIGMA was set to the PLUMED default 0.05 nm. ADAPTIVE=GEOM shrank the per-CV Gaussian widths to about 0.01 s-units, making every hill a needle. 25,000 needles piled at s ≈ 1.05 built a deep but locally flat well, so the walker felt no force."
  )
);
children.push(
  bullet(
    "Fix (2026-04-15). Raised SIGMA to 0.1 nm. Added SIGMA_MIN=0.3,0.005 (per-CV floor in s-units and nm^2) and SIGMA_MAX=1.0,0.05 (ceiling). SI does not specify these values; both floors are my choice."
  )
);
children.push(
  bullet(
    "Tutorial citation error. An earlier tutorial draft quoted SIGMA=0.2,0.1 as if from SI p.S3. Full-text search of the SI confirms SI gives no numerical SIGMA. Removed the fake citation."
  )
);
children.push(
  bullet(
    "Restart protocol. Extended Job 43813633 (10 ns probe) to 50 ns via two steps: gmx convert-tpr -extend 40000, then gmx mdrun -cpi metad.cpt with RESTART on line 1 of plumed.dat so HILLS appends instead of rotating to bck.0.HILLS."
  )
);
children.push(
  bullet(
    "Current run (Job 44008381). 5 ns windowed max s trend: 1.18 → 1.39 → 1.46 → 1.81 → 2.79 → 3.49. Monotonic, consistent with walker climbing out of O toward PC."
  )
);
children.push(
  bullet(
    "Decision gate at 50 ns. max s ≥ 5 → Phase 2 (10 walkers). 3 ≤ max s < 5 → wait for full 50 ns. max s < 3 → regroup."
  )
);

// ── Post-meeting status ──
children.push(heading("Post-meeting status (20:30 EDT)", 1));
children.push(
  para(
    "Job 44008381 at 34.94 ns, max s(R) = 4.13. sigma_path.sss holding at the 0.30 floor. On track to finish within walltime."
  )
);

// ── Next Steps ──
children.push(heading("Next Steps", 1));
children.push(
  numberedItem(1, "Monitor Job 44008381 to 50 ns and apply the decision gate.")
);
children.push(
  numberedItem(
    2,
    "If Phase 2: pick ~10 diverse starting snapshots by PyMOL inspection (not strided frames), per Yu's April 9 direction."
  )
);
children.push(
  numberedItem(3, "FES reconstruction + JACS 2019 Fig 2a comparison by April 24.")
);
children.push(
  numberedItem(
    4,
    "Shared repo: https://github.com/alex051107/trpb-metadynamics-replication"
  )
);
children.push(
  numberedItem(
    5,
    "Send draft email to Maria-Solano (CC Osuna, Amin, Yu) asking for the plumed.dat files of Aex1 / A-A / Q2 and the 15-frame path alignment method."
  )
);

const doc = new Document({
  creator: "Zhenpeng Liu",
  title: "Meeting Notes 2026-04-17",
  styles: {
    default: {
      document: { run: { font: FONT, size: 22, color: BLACK } },
    },
  },
  sections: [
    {
      properties: {
        page: {
          margin: {
            top: convertInchesToTwip(1),
            right: convertInchesToTwip(1),
            bottom: convertInchesToTwip(1),
            left: convertInchesToTwip(1),
          },
        },
      },
      children,
    },
  ],
});

const outPath = path.resolve(__dirname, "..", "MeetingNotes_2026-04-17.docx");
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outPath, buf);
  const stat = fs.statSync(outPath);
  console.log(`Wrote ${outPath} (${(stat.size / 1024).toFixed(1)} KB)`);
});
