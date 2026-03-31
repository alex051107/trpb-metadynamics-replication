# Paper Annotation Skill — Deep Dual-Column HTML

## Purpose

When the user says any of the following, invoke this skill:
- "帮我用论文标注格式分析这篇文章"
- "deep annotate this paper"
- "做一个像 JACS2019 那样的深度标注"
- "annotate every paragraph of [paper]"
- "帮我把这篇论文每段都分析一遍"

This skill produces a self-contained **single HTML file** with:
- Every paragraph of the paper annotated in **dual-column format** (left = English text with highlights, right = Chinese annotation panel)
- Five-color highlight system (thesis, concept, evidence, counter-argument, method)
- Sticky sidebar navigation
- Top legend bar
- Project connection table at the end

---

## Output Format Specification

### File naming
`[JournalYear]_[FirstAuthorLastName]_DeepAnnotation.html`
Example: `JACS2019_MariaSolano_DeepAnnotation.html`

### Top Navigation Bar (`#topnav`)
- Navy background (`#1a2744`)
- Logo text: paper short title + year
- Right side: 5 legend pills showing the highlight color system

### Left Sidebar (`#sidebar`)
- Sticky, full-height
- Groups: Abstract / Introduction (P1–Pn) / Methods (Pm–Pk) / Results (Pl–Pz) / Synthesis / Project Connection
- Each item is a `<a class="nav-link">` scrolling to anchor

### Main Content Layout
Each paragraph gets one `<div class="para-block">` with two columns:

**Left column** (`.para-left`):
- Paragraph ID badge: `<span class="para-id">P1</span>`
- English text with inline `<span class="hl-y/r/b/g/p">` highlights
- Highlight colors: yellow=thesis/claim, red=technical concept, blue=experimental evidence, green=counter/limitation, purple=method/protocol

**Right column** (`.para-right`):
- **段落功能** (Paragraph function): one sentence saying what rhetorical role this paragraph plays
- **逻辑角色**: e.g., "建立研究背景" / "提出中心假说" / "展示实验验证" / "讨论局限性"
- **专业术语速查表**: mini table of key technical terms from this paragraph with brief Chinese definitions
- **值得注意** (Notable): the single most important insight, in a styled callout box
- **与你的项目的关联** (Project connection): explicit 1–2 sentence bridge to Zhenpeng's project

### Color-coded highlights

| Class | Color | Use for |
|-------|-------|---------|
| `hl-y` | Yellow (#fef3c7) | Central thesis, key claims, conclusions |
| `hl-r` | Red (#fee2e2) | Technical concepts being introduced |
| `hl-b` | Blue (#dbeafe) | Experimental data, quantitative evidence |
| `hl-g` | Green (#dcfce7) | Limitations, counter-arguments, caveats |
| `hl-p` | Purple (#f3e8ff) | Methods, protocols, computational procedures |

---

## Required Sections Beyond Paragraph-by-Paragraph

### §A — Argument Skeleton (论证骨架)
A linear chain showing how each paragraph connects to the next:
```
[Background] → [Gap] → [Hypothesis] → [Method] → [Key Result] → [Conclusion]
  P1–P2           P3          P4            P5–P6       P7–P12         P13–P15
```

### §B — Project Connection Table (与你的项目的关联总表)
A styled HTML table with columns:
| 论文中的内容 | Zhenpeng 项目中的对应 | 具体操作建议 |

Minimum 5 rows covering the main concepts of the paper.

### §C — Key Terms Glossary (关键术语总表)
All technical terms encountered in the paper, consolidated into one reference table.

---

## CSS Variables to Use (copy verbatim)

```css
:root {
  --navy:#1a2744; --blue:#2563EB; --teal:#0d9488;
  --paper:#faf8f3; --paper2:#f3f0e8; --border:#d4c9a8;
  --text:#2d2d2d; --gray:#6b7280; --lg:#f3f4f6;
  --hl-thesis:#fef3c7; --hl-thesis-b:#d97706;
  --hl-concept:#fee2e2; --hl-concept-b:#dc2626;
  --hl-evidence:#dbeafe; --hl-evidence-b:#2563eb;
  --hl-counter:#dcfce7; --hl-counter-b:#16a34a;
  --hl-method:#f3e8ff; --hl-method-b:#7c3aed;
  --sidebar-w:220px;
}
```

Use Google Fonts: `Lora` (serif, for headings) + `IBM Plex Sans` (body) + `IBM Plex Mono` (code).

---

## Workflow When Invoked

1. **Identify paper** — get DOI, authors, journal, year, abstract
2. **Retrieve full text** — try PubMed MCP (`get_full_text_article`) if open access; if paywalled, reconstruct from training knowledge paragraph by paragraph; inform user of access status
3. **Segment into paragraphs** — label P1, P2, ... sequentially; note section boundaries (Abstract, Introduction, Methods, Results, Discussion, Conclusion)
4. **Annotate left column** — apply 5-color highlights inline; never omit paragraph content; reproduce every sentence
5. **Write right column** — for each paragraph: 段落功能, 逻辑角色, 专业术语速查表, 值得注意, 与你的项目的关联
6. **Write synthesis sections** — §A Argument Skeleton, §B Project Connection Table, §C Glossary
7. **Assemble HTML** — single file, all CSS inline in `<style>`, no external dependencies except Google Fonts
8. **Save** — to workspace as `[JournalYear]_[Author]_DeepAnnotation.html`

---

## Quality Rules

- **Never omit paragraphs.** If a section has 8 paragraphs, all 8 get full dual-column treatment.
- **The right column must be specific**, not generic. "这段很重要" is not acceptable. Write what specifically is important and why for Zhenpeng's project.
- **Every 与你的项目的关联** should name a concrete step: "在你用 MetaDynamics 跑 FEL 时，这意味着你需要…"
- **Quantitative data gets highlighted in blue** (hl-b) and must be repeated in the 值得注意 callout if it is a key result.
- **The paper's core argument must be traceable** through the yellow (hl-y) highlights alone.

---

## Example Right-Column Panel Structure

```html
<div class="para-right">
  <div class="para-id">P3</div>

  <p><strong>段落功能：</strong>提出本文核心假说——通过 MetaDynamics 预测突变对 COMM 结构域关闭状态的影响，从而理性设计更活跃的 TrpB 变体。</p>

  <p><strong>逻辑角色：</strong>假说提出 (Hypothesis)</p>

  <table class="term-table">
    <tr><th>术语</th><th>解释</th></tr>
    <tr><td>COMM domain</td><td>TrpB β亚基中约40-50残基的移动loop（残基97–184），控制活性位点开/关转换</td></tr>
    <tr><td>MetaDynamics</td><td>增强采样 MD 方法，通过填充 Gaussian "山丘"加速越过能垒</td></tr>
    <tr><td>FEL</td><td>自由能全貌图 (Free Energy Landscape)，二维 ΔG 图</td></tr>
  </table>

  <div class="notable-box">
    💡 <strong>值得注意：</strong>本段的核心假设是 ΔΔG(closed−open) 可以预测酶活性——这正是你整个项目 pipeline 中 Step 4 MetaDynamics 的理论基础。
  </div>

  <p><strong>与你的项目的关联：</strong>你在用 MetaDynamics 计算 ΔG 时，判断设计成功的标准就来自这里：ΔG(closed−open) &lt; −2 kcal/mol 判定为活性构象，反之为非活性。</p>
</div>
```

---

## Notes for Future Papers in This Project

Priority papers to annotate next:
1. **ACS Catal 2021** (Maria-Solano et al., PMID 34777912, PMC8576815) — full text available via PubMed; covers SPM method + FEL axes s/z
2. **Protein Science 2022** (Osuna group, tAF2-MD method)
3. **Arnold PNAS 2015** (PMID 26553994, PMC4664345) — TrpB stand-alone function directed evolution
4. **Arnold JACS 2018** (PMID 29712420, PMC5999571) — "Directed Evolution Mimics Allosteric Activation"

When the user says "annotate ACS Catal 2021", fetch PMC8576815 full text first, then follow this skill.
