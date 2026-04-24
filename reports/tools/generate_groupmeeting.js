// Generic reusable group-meeting pptx generator.
//
// Style lineage: 2026-04-09 hand-built deck (dark theme, blue accents,
// monospace code, clean table borders, tech-deep 1:1 format).
//
// Usage:
//     node reports/tools/generate_groupmeeting.js <data.json> [outputPath]
//
// The data JSON drives all content. The JS here is the layout engine only.
// To make a new week's deck, write a new JSON with the same shape as
// groupmeeting_2026-04-17.data.json and point this script at it.
//
// JSON schema (abridged):
//     {
//       "meta": { "date", "author", "meeting_type", "outputFilename" },
//       "slides": [
//         { "type": "title", "title", "subtitle", "meta", "footer" },
//         { "type": "bullets", "title", "subtitle", "bullets", "footer" },
//         { "type": "bullets+code", "title", "subtitle", "bullets",
//            "bulletsBox", "code", "codeBox", "footer" },
//         { "type": "code+bullets", ... },
//         { "type": "table+bullets", "title", "subtitle", "table": {rows, box},
//            "bullets", "bulletsBox", "footer" },
//         { "type": "dual-box+bullets", "title", "subtitle", "leftBox",
//            "rightBox", "bullets", "bulletsBox", "footer" },
//         { "type": "two-column", "title", "subtitle", "leftColumn",
//            "rightColumn", "footer" }
//       ]
//     }
//
// Colors can be referenced by name (BG / FG / ACCENT / MUTED / CODE_BG /
// GOOD / BAD) in bullet items and box headings. Raw hex also accepted.

const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");

if (process.argv.length < 3) {
  console.error("Usage: node generate_groupmeeting.js <data.json> [output.pptx]");
  process.exit(1);
}

const dataPath = path.resolve(process.argv[2]);
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));

const meta = data.meta || {};
const slides = data.slides || [];

// Output path: CLI arg > data.meta.outputFilename > derived from data.date
let outPath;
if (process.argv[3]) {
  outPath = path.resolve(process.argv[3]);
} else if (meta.outputFilename) {
  outPath = path.resolve(__dirname, "..", meta.outputFilename);
} else {
  outPath = path.resolve(__dirname, "..", `GroupMeeting_${meta.date || "undated"}.pptx`);
}

// ===== Theme =====
// 2026-04-17: switched to pure black-and-white per Yu feedback
// (previous dark-navy theme archived in git; hex values intentional).
const COLOR = {
  BG: "FFFFFF",
  FG: "000000",
  ACCENT: "000000",
  MUTED: "555555",
  CODE_BG: "F5F5F5",
  GOOD: "000000",
  BAD: "000000"
};
const resolveColor = (c) => (c && COLOR[c] ? COLOR[c] : c) || COLOR.FG;

const FONT = "Arial";
const FONT_CODE = "Menlo";
const W = 13.333;
const H = 7.5;
const margin = { top: 0.35, left: 0.5, right: 0.5, bottom: 0.4 };
const content_w = W - margin.left - margin.right;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = meta.author || "Unknown";
pres.title = meta.title || `Group Meeting ${meta.date || ""}`;

// ===== Helpers (layout primitives) =====

function slideBase() {
  const s = pres.addSlide();
  s.background = { color: COLOR.BG };
  s.addShape("rect", {
    x: 0, y: H - 0.04, w: W, h: 0.04,
    fill: { color: "333333" },
    line: { color: "333333" }
  });
  return s;
}

function addTitle(s, text) {
  s.addText(text, {
    x: margin.left, y: margin.top, w: content_w, h: 0.7,
    fontFace: FONT, fontSize: 22, bold: true, color: COLOR.FG, align: "left"
  });
}

function addSubtitle(s, text, y) {
  if (!text) return;
  s.addText(text, {
    x: margin.left, y: y ?? 1.05, w: content_w, h: 0.35,
    fontFace: FONT, fontSize: 14, color: COLOR.ACCENT, italic: true, align: "left"
  });
}

function addFooter(s, text) {
  if (!text) return;
  s.addText(text, {
    x: margin.left, y: H - 0.38, w: content_w, h: 0.2,
    fontFace: FONT, fontSize: 9, color: COLOR.MUTED, align: "left"
  });
}

// Render 1-3 source URLs / citations stacked just above the main footer.
// Called BEFORE addFooter so the main footer stays on the bottom line.
// `sources` is an array of strings (URLs, DOIs, or "see file.md line X" refs).
// Each entry becomes one MUTED 9pt line; up to 3 rendered.
function addSourcesFooter(s, sources) {
  if (!Array.isArray(sources) || sources.length === 0) return;
  const capped = sources.slice(0, 3);
  const lineH = 0.18;
  const block_h = lineH * capped.length;
  const y0 = H - 0.38 - block_h - 0.02;
  const body = capped.map((src, i) => ({
    text: "Source: " + String(src),
    options: { paraSpaceAfter: 0, color: COLOR.MUTED, breakLine: i < capped.length - 1 }
  }));
  s.addText(body, {
    x: margin.left, y: y0, w: content_w, h: block_h,
    fontFace: FONT, fontSize: 9, color: COLOR.MUTED,
    valign: "top", align: "left"
  });
}

function addBullets(s, items, box) {
  if (!items || items.length === 0) return;
  // NOTE: match the original hand-built generator's behavior exactly —
  // string items get only the bullet/paraSpaceAfter paragraph options;
  // object items additionally get color/bold. Passing color/bold for
  // every paragraph regressed bullet rendering (Codex stop-hook 2026-04-16).
  const body = items.map((item) => {
    if (typeof item === "string") {
      return {
        text: item,
        options: { bullet: { code: "2022" }, paraSpaceAfter: 6 }
      };
    }
    return {
      text: item.text,
      options: {
        bullet: { code: "2022" },
        paraSpaceAfter: 6,
        color: resolveColor(item.color),
        bold: !!item.bold
      }
    };
  });
  s.addText(body, {
    x: box?.x ?? margin.left, y: box?.y ?? 1.6,
    w: box?.w ?? content_w, h: box?.h ?? H - 2.3,
    fontFace: FONT, fontSize: box?.fontSize ?? 14, color: COLOR.FG,
    valign: "top", align: "left", paraSpaceAfter: 6
  });
}

function addCodeBlock(s, code, box) {
  const x = box?.x ?? margin.left;
  const y = box?.y ?? 1.6;
  const w = box?.w ?? content_w;
  const h = box?.h ?? 1.5;
  s.addShape("rect", {
    x, y, w, h,
    fill: { color: COLOR.CODE_BG },
    line: { color: "333333", width: 0.5 }
  });
  s.addText(code, {
    x: x + 0.1, y: y + 0.1, w: w - 0.2, h: h - 0.2,
    fontFace: FONT_CODE, fontSize: box?.fontSize ?? 11, color: COLOR.FG,
    valign: "top", align: "left"
  });
}

function addTable(s, tableSpec) {
  if (!tableSpec || !tableSpec.rows) return;
  const rows = tableSpec.rows;
  const box = tableSpec.box || {};
  const tableRows = rows.map((row, rIdx) =>
    row.map((cell) => {
      const isHeader = rIdx === 0;
      return {
        text: String(cell),
        options: {
          fontFace: FONT, fontSize: 11,
          bold: isHeader, color: isHeader ? "000000" : COLOR.FG,
          fill: { color: isHeader ? "E0E0E0" : COLOR.CODE_BG },
          align: "left", valign: "middle",
          border: { type: "solid", color: COLOR.MUTED, pt: 0.5 }
        }
      };
    })
  );
  s.addTable(tableRows, {
    x: box.x ?? margin.left, y: box.y ?? 1.6,
    w: box.w ?? content_w,
    rowH: box.rowH ?? 0.3,
    colW: box.colW,
    fontFace: FONT, fontSize: 11
  });
}

function addBoxWithBody(s, boxSpec, x, y, w, h) {
  const borderColor = resolveColor(boxSpec.headingColor || "ACCENT");
  s.addShape("rect", {
    x, y, w, h,
    fill: { color: COLOR.CODE_BG },
    line: { color: borderColor, width: 1 }
  });
  const segments = [];
  if (boxSpec.heading) {
    segments.push({
      text: boxSpec.heading + "\n",
      options: { fontSize: 13, bold: true, color: borderColor }
    });
  }
  if (boxSpec.body) {
    segments.push({
      text: boxSpec.body,
      options: { fontSize: 12, color: COLOR.FG }
    });
  }
  s.addText(segments, {
    x: x + 0.1, y: y + 0.1, w: w - 0.2, h: h - 0.2,
    fontFace: FONT, valign: "top"
  });
}

// ===== Slide renderers by type =====

const renderers = {
  title(s, d) {
    s.addShape("rect", {
      x: 1.0, y: 2.2, w: W - 2.0, h: 0.06,
      fill: { color: COLOR.ACCENT }, line: { color: COLOR.ACCENT }
    });
    s.addText(d.title || "", {
      x: 1.0, y: 2.5, w: W - 2.0, h: 0.9,
      fontFace: FONT, fontSize: 40, bold: true, color: COLOR.FG, align: "left"
    });
    if (d.subtitle) {
      s.addText(d.subtitle, {
        x: 1.0, y: 3.5, w: W - 2.0, h: 0.5,
        fontFace: FONT, fontSize: 24, color: COLOR.ACCENT, italic: true, align: "left"
      });
    }
    if (d.meta) {
      s.addText(d.meta, {
        x: 1.0, y: 5.5, w: W - 2.0, h: 0.4,
        fontFace: FONT, fontSize: 16, color: COLOR.MUTED, align: "left"
      });
    }
    if (d.footer) {
      s.addText(d.footer, {
        x: 1.0, y: 6.0, w: W - 2.0, h: 0.3,
        fontFace: FONT, fontSize: 13, color: COLOR.MUTED, italic: true, align: "left"
      });
    }
  },

  bullets(s, d) {
    addTitle(s, d.title);
    addSubtitle(s, d.subtitle);
    addBullets(s, d.bullets, d.bulletsBox);
    addSourcesFooter(s, d.sources);
    addFooter(s, d.footer);
  },

  "bullets+code"(s, d) {
    addTitle(s, d.title);
    addSubtitle(s, d.subtitle);
    addBullets(s, d.bullets, d.bulletsBox);
    addCodeBlock(s, d.code, d.codeBox);
    addSourcesFooter(s, d.sources);
    addFooter(s, d.footer);
  },

  "code+bullets"(s, d) {
    addTitle(s, d.title);
    addSubtitle(s, d.subtitle);
    addCodeBlock(s, d.code, d.codeBox);
    addBullets(s, d.bullets, d.bulletsBox);
    addSourcesFooter(s, d.sources);
    addFooter(s, d.footer);
  },

  "table+bullets"(s, d) {
    addTitle(s, d.title);
    addSubtitle(s, d.subtitle);
    addTable(s, d.table);
    addBullets(s, d.bullets, d.bulletsBox);
    addSourcesFooter(s, d.sources);
    addFooter(s, d.footer);
  },

  "dual-box+bullets"(s, d) {
    addTitle(s, d.title);
    addSubtitle(s, d.subtitle);
    const halfW = content_w / 2 - 0.1;
    const y = 1.55;
    const h = 1.8;
    addBoxWithBody(s, d.leftBox || {}, margin.left, y, halfW, h);
    addBoxWithBody(s, d.rightBox || {}, margin.left + halfW + 0.2, y, halfW, h);
    addBullets(s, d.bullets, d.bulletsBox);
    addSourcesFooter(s, d.sources);
    addFooter(s, d.footer);
  },

  "two-column"(s, d) {
    addTitle(s, d.title);
    addSubtitle(s, d.subtitle);
    if (d.leftColumn) {
      s.addText(d.leftColumn.heading || "", {
        x: margin.left, y: 1.5, w: content_w / 2 - 0.25, h: 0.35,
        fontFace: FONT, fontSize: 15, bold: true, color: COLOR.ACCENT, align: "left"
      });
      addBullets(s, d.leftColumn.bullets, {
        x: margin.left, y: 1.95, w: content_w / 2 - 0.15, h: 3.0, fontSize: 12
      });
    }
    if (d.rightColumn) {
      s.addText(d.rightColumn.heading || "", {
        x: margin.left + content_w / 2 + 0.1, y: 1.5,
        w: content_w / 2 - 0.25, h: 0.35,
        fontFace: FONT, fontSize: 15, bold: true, color: COLOR.ACCENT, align: "left"
      });
      addBullets(s, d.rightColumn.bullets, {
        x: margin.left + content_w / 2 + 0.1, y: 1.95,
        w: content_w / 2, h: 3.0, fontSize: 12
      });
    }
    addSourcesFooter(s, d.sources);
    addFooter(s, d.footer);
  },

  "image+bullets"(s, d) {
    addTitle(s, d.title);
    addSubtitle(s, d.subtitle);
    if (d.image && d.image.path) {
      const opts = {
        path: d.image.path,
        x: d.image.x ?? margin.left,
        y: d.image.y ?? 1.55,
        w: d.image.w ?? 6.5,
        h: d.image.h ?? 5.0
      };
      s.addImage(opts);
    }
    if (d.bullets) {
      addBullets(s, d.bullets, d.bulletsBox);
    }
    addSourcesFooter(s, d.sources);
    addFooter(s, d.footer);
  }
};

// ===== Build =====

for (const [idx, slideData] of slides.entries()) {
  const type = slideData.type;
  if (!renderers[type]) {
    throw new Error(`Slide ${idx + 1}: unknown type "${type}". Valid: ${Object.keys(renderers).join(", ")}`);
  }
  const s = slideBase();
  renderers[type](s, slideData);
}

pres.writeFile({ fileName: outPath }).then((f) => {
  const stat = fs.statSync(f);
  console.log(`[ok] wrote ${f} (${(stat.size / 1024).toFixed(1)} KB) from ${dataPath}`);
});
