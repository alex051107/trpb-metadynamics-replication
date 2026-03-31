---
name: weekly-report
description: >
  Generate a formatted weekly research report (.docx) for Zhenpeng Liu's TrpB
  MetaDynamics project. Covers papers read, hands-on work, problems solved, open
  questions, and next-week plan. Triggered by "generate this week's report",
  "create weekly report", "write the weekly update", or "make a report for week N".
---

# Weekly Report Generator

Write a professional weekly research report and export it as .docx. The report
goes to the advisor and should read like a grad student wrote it. Direct,
specific, honest about what worked and what didn't.

## Step 1: Gather inputs

Read these files in order. Skip any that don't exist.

1. `研究进展日志.md` (find the latest `## Week N` entry)
2. `CHANGELOG.md` (find entries dated within the report week)
3. `replication/validations/failure-patterns.md` (any new FP-XXX entries this week)
4. `papers/reading-notes/` (any new .md files added this week)
5. `replication/manifests/` (current campaign status and blockers)

Cross-reference these sources. The 研究进展日志 has the plan and questions; the
CHANGELOG has what actually happened; failure-patterns has debugging stories.

## Step 2: Determine report metadata

- **Week number**: from the latest 研究进展日志 entry
- **Date**: Friday of that week, or today's date
- **Theme**: one phrase summarizing the week (e.g., "HPC setup + toy MetaD test")
- **Advisor**: read from project context; if unknown, use placeholder

## Step 3: Write the report

The report has exactly **six sections**. Follow the template in
`reference/report-template.md`. Apply all language rules from
`reference/de-ai-rules.md` while writing.

### Section overview

| # | Section | Length | Source |
|---|---------|--------|--------|
| 0 | Project Context | 2-3 sentences | CLAUDE.md project description |
| 0.5 | Pipeline Overview | compact list | NEXT_ACTIONS.md + manifests |
| 1 | Header + Summary | 3-5 sentences | 研究进展日志 "这周干了什么" |
| 2 | Work Done | table, 5-15 rows | CHANGELOG + 研究进展日志 |
| 3 | What I Learned | 800-1200 words | reading-notes + CHANGELOG |
| 4 | Problems Encountered | 1-3 stories | failure-patterns + CHANGELOG |
| 5 | Open Questions | 3-5 items | 研究进展日志 "待问问题" |
| 6 | Key Simulation Parameters | formal table | replication/parameters/ |
| 7 | Next Week Plan | numbered list | 研究进展日志 "下周计划" + manifests |
| 8 | References | bibliography | all cited papers |

**Section 4 is the key addition for weeks with hands-on work.** Each problem
gets three parts: what happened, how I fixed it, what I learned. If the week
was paper-reading only, this section can be short or merged into Section 3.

### Writing guidelines (quick reference)

- Write as "I", not "we"
- Numbers over abstractions: "2 kcal/mol" not "a significant reduction"
- No em dashes anywhere. Rewrite as two sentences or use a colon.
- Max one comma per sentence; if two or more, split it
- If uncertain, say so: "I'm not sure about X" not "further investigation is warranted"
- Never mention AI tools. All work is "I did X". Full rules in `reference/de-ai-rules.md`
- **Big-picture anchoring**: when introducing a technical topic, first connect it to the project goal in one sentence. Instead of "I installed GROMACS 2026.0", write "The published MetaDynamics protocol requires GROMACS + PLUMED2. I installed GROMACS 2026.0 on Longleaf."
- **First-use term explanation**: the first time a technical term appears, add a brief parenthetical. After the first explanation, use the bare term.

## Step 4: Generate .docx

Use Node.js `docx` library. Formatting spec in `reference/docx-format.md`.

```bash
cd "/Users/liuzhenpeng/Desktop/UNC/暑研 /Caltech Interview/tryp B project"
node generate_report.js
```

Save to: `reports/WeeklyReport_Week[N]_[YYYY-MM-DD].docx`

## Step 5: Validate

After writing, run these checks:

- [ ] Scan for every banned phrase in `reference/de-ai-rules.md`. Replace all.
- [ ] No two consecutive paragraphs start with the same word
- [ ] Every number has a traceable source (log entry, paper, or manifest)
- [ ] Section 3 word count is 800-1200
- [ ] Section 4 has at least one concrete problem (if hands-on work happened)
- [ ] "I" count > "we" count
- [ ] No sentences with 3+ commas
- [ ] .docx file size > 50 KB and opens without errors
- [ ] Launch advisor-perspective sub-agent review before finalizing (see below)

### Advisor-perspective review (sub-agent)

Before generating the final .docx, launch a sub-agent with this prompt:

> "You are a busy professor reading a student's weekly research report. You have
> not been involved in the day-to-day work. Read this report and flag:
> (a) any place where you don't understand what the student is doing or why,
> (b) any jargon that isn't explained on first use,
> (c) whether the report clearly answers: what did you do, why, and what's next."

Apply the sub-agent's feedback before generating the final .docx.
