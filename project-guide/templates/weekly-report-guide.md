# Weekly Report Generation Guide

> This guide explains how to structure and write your weekly research reports for the TrpB MetaDynamics project. The format mirrors the style of the Week 1 report (March 22, 2026).

---

## Overview

Your weekly reports go to your advisor and serve two purposes:
1. Document what you actually did and learned (not what you planned to do)
2. Identify gaps, blockers, and next steps clearly

The report is a conversation starter, not a paper. It should be honest about uncertainty and specific about what you're stuck on.

---

## Report Structure

### 1. Header Table

Create a simple 4-row table with two columns:

```
To:      [Advisor Name]
From:    Zhenpeng Liu (aNima Lab, Caltech)
Date:    [Friday of that week]
Week:    #N [1-2 sentence theme/focus]
```

The "Week" field is a short descriptor, e.g., "#1 Literature review and project scoping".

---

### 2. Summary Box

A single paragraph (3–5 sentences) in a light blue box that answers: **What was the central focus this week, and what's the main unresolved question you want to discuss?**

Example from Week 1:
> "This week I focused on reading the core papers behind the TrpB MetaDynamics project and our lab's 2026 Nature Communications paper on generative TrpB design. The main goal was to understand what MetaDynamics can and cannot tell us about enzyme function, and how it might complement the generative pipeline our lab has already built. I have not run any simulations yet. The central open question I want to discuss is how MetaDynamics could serve as a physics-based filter for D-tryptophan selectivity, which is a conformational property that the language model has no training signal for."

**Guidelines for the summary:**
- Start with what you actually did (papers read, code written, experiments run, etc.)
- Explain why that matters for the project
- Name the one biggest question you want feedback on
- Keep it short—your advisor should understand the week's theme in one minute

---

### 3. Section 1: Work Done

A table listing all major deliverables: papers read, code written, directories organized, anything concrete.

| # | Paper/Task | Journal | DOI | Status |
|---|---|---|---|---|
| 1 | Author, Year, Full Title | *Journal Name* | 10.xxxx/xxxxx | Read / Partial / Queued |
| 2 | Code task: set up AMBER environment | — | — | Done |
| 3 | Downloaded PDB structures for benchmark | — | — | Done |

**Status codes:**
- **Read**: Fully processed and understood
- **Partial**: Skimmed or read selectively; you know what it says but not all details
- **Queued**: On the list for this week but not done yet
- **Done**: For non-paper tasks (code, downloads, organization)

**For each row, specify:**
- What it is (paper title, code milestone, dataset)
- Source (journal, repository, link)
- Current understanding (status)

---

### 4. Section 2: What I Learned

This is the heart of the report. **One subsection per major topic.**

**For each subsection:**
1. Start with a 1–2 sentence summary of what the material covers
2. Explain 2–3 key insights that directly matter to your project
3. End with how it changes your understanding or plan

**Tone:** Write like you're explaining it to a labmate who knows the general context but not the details. Be specific. Use numbers, structures, and observations rather than vague claims.

**Example structure:**

**Subsection: "JACS 2019 (Osuna group): Free Energy Landscapes of TrpB"**

This paper uses well-tempered MetaDynamics with path collective variables to reconstruct the conformational landscape of the COMM domain in three systems: PfTrpS (complex), isolated wild-type PfTrpB, and the evolved variant PfTrpB0B2.

Key finding 1: The wild-type PfTrpB struggles to close productively when isolated from TrpA. In the Q2 intermediate, it can reach Closed-like states, but these are geometrically off-path—the COMM domain closes in the wrong orientation, with the K82-to-intermediate distance at 3.9 Å instead of the 3.6 Å seen in productive closure.

Key finding 2: The six distal mutations in 0B2 fix this. They lower the O→PC→C barrier from ~6 kcal/mol to ~2 kcal/mol and allow the COMM domain to reach genuinely productive Closed states.

Why this matters to me: The productive closure metric (RMSD < 1.5 Å from reference path, K82-Q2 ≤ 3.6 Å) is exactly what I'll use to evaluate whether MetaDynamics can rank sequences by their likely activity. If I can reproduce this result on GenSLM-230, I'll have validated my pipeline.

---

**Before writing Section 2, check these directories for additional inputs:**
- `papers/reading-notes/` — Your own concise summaries of papers read
- `papers/annotations/` — HTML-formatted deep annotations (if you used the paper-annotation skill)

If you have notes from the paper-reading skill or Zotero annotations, reference them here and pull the key takeaways forward.

---

### 5. Section 3: Points I Am Still Uncertain About

List 3–5 specific things you don't know and why they matter.

**For each uncertainty:**
1. State it clearly and concisely
2. Explain why it's blocking progress
3. Optionally: what would resolve it?

**Example from Week 1:**
> "The biggest gap is how to define D-tryptophan selectivity as a measurable conformational property. The Osuna papers give clear structural metrics for L-Trp activity: deviation from the reference O-to-C transition path (where > 1.5 Angstrom indicates unproductive closure) and the K82-to-intermediate proton transfer distance (productive at 3.6 Angstrom or below). For D-Trp, the corresponding metric would need to capture whether the active site geometry supports the opposite facial approach of indole to the aminoacrylate intermediate, since the face of approach determines product chirality. I do not yet know which geometric quantity to track in a simulation trajectory for this, and I have not found a published precedent for TrpB specifically."

**Tone:** Honest. Don't hide uncertainty. This section is where you ask for help.

---

### 6. Section 4: Potential Directions and Next Week Plan

Split this into subsections:

**A. Potential Research Directions** (if you discovered multiple paths forward)

For each direction, write:
1. A one-sentence problem statement
2. What the outcome would tell you
3. Why it's worth trying (or not)
4. Rough effort estimate

Example:
> **Direction A: Explain GenSLM-230 vs NdTrpB functional divergence**
>
> The most immediately testable question is why 230 and NdTrpB have nearly identical predicted structures but dramatically different activity profiles. Running MetaDynamics on both and comparing their COMM domain free energy landscapes could directly test whether 230 has a lower O-to-C barrier or a higher population of productive Closed states. If it does, that provides a mechanistic explanation that static structure prediction cannot, and serves as a proof of concept that MetaDynamics captures functionally relevant differences between sequences that look structurally identical.

**B. Next Week's Plan**

List concrete, achievable steps in order of priority:

```
1. [Task A] — expected to take X days
2. [Task B] — depends on outcome of A
3. [Task C] — can run in parallel with B
```

Be realistic about time. MetaDynamics runs are slow; simulation setup is fiddly. Better to commit to one complete thing than three partial things.

**Before writing Section 4, check:**
- `replication/manifests/` — Do you have campaign manifest drafts from previous weeks? Mention current blockers.
- Your progress log (`研究进展日志.md`) — What did you actually plan to do last week? Did you do it?

---

## Language Guidelines (De-AI Instructions)

Your report is written by a grad student to an advisor. It should sound like you thinking out loud, not like an AI summary.

### Words to avoid:
- **Filler academic phrases**: "delve into", "it's important to note", "this is particularly interesting because", "moving forward", "in terms of", "leverage", "utilize"
- **Vague transitions**: "Additionally", "Furthermore", "Moreover", "Notably", "Specifically", "Importantly"
- **Abstract marketing language**: "comprehensive", "robust", "significant", "fundamental", "multifaceted", "intricate"

### How to write instead:

| Don't write | Write instead |
|---|---|
| "Furthermore, MetaDynamics provides a robust framework for..." | "MetaDynamics lets me..." |
| "We conducted a comprehensive literature review." | "I read 4 papers on..." |
| "The results are particularly significant because..." | "This matters because..." |
| "One leverages path CV formalism to..." | "The path CV approach tracks..." |
| "It is important to note that..." | "[Just state the fact.]" |
| "In terms of computational cost..." | "The runtime is about X hours per system." |

### Tone rules:

1. **Use "I" not "we"** (unless you actually collaborated with someone on that specific task)
2. **Prefer short sentences.** If you write a sentence with 2+ commas, split it.
3. **When uncertain, say it directly:** "I'm not sure about X" not "Further investigation is warranted"
4. **Numbers and specifics beat vague claims:** "Read 3 papers" not "conducted extensive literature review"; "The barrier is 6 kcal/mol" not "a significant energy difference"
5. **Curious, slightly tentative on unknowns; direct on facts:**
   - Facts: "The 0B2 variant has six distal mutations."
   - Uncertain: "I'm not sure whether the K82-to-Q2 distance alone explains the functional difference, or if other contacts also matter."

---

## Workflow: How to Generate the Report

1. **Fill in `研究进展日志.md`** with raw notes during the week (Chinese, informal, no structure required)

2. **At end of week, read the log** and extract:
   - Papers/tasks completed (→ Section 1)
   - Key learnings (→ Section 2)
   - Blockers (→ Section 3)
   - Next steps (→ Section 4)

3. **Check these directories for inputs:**
   - `papers/reading-notes/` for paper summaries
   - `papers/annotations/` for deep-dive HTML notes
   - `replication/manifests/` for campaign status and blockers

4. **Generate the .docx file** using the Node.js docx library (same approach as `wr_v6.js`)

5. **Proofread for de-AI language** before sending

---

## Report Template

Use this skeleton for each week:

```markdown
# Weekly Research Update

To:     [Advisor Name]
From:   Zhenpeng Liu (aNima Lab, Caltech)
Date:   [YYYY-MM-DD]
Week:   #N [1-2 sentence theme]

---

## Summary

[One paragraph: what you did, why it matters, what you want to discuss.]

---

## 1. Work Done

| # | Paper/Task | Source | DOI/Link | Status |
|---|---|---|---|---|
| 1 | | | | |

---

## 2. What I Learned

### [Topic 1]
[Body paragraph]

### [Topic 2]
[Body paragraph]

---

## 3. Points I Am Still Uncertain About

1. [Uncertainty A] — Why it matters...
2. [Uncertainty B] — Why it matters...

---

## 4. Potential Directions and Next Week Plan

### Direction A: [Title]
[Rationale + expected outcome]

### Direction B: [Title]
[Rationale + expected outcome]

### Next Week
1. [Task] — X days
2. [Task] — depends on Task 1
3. [Task] — can parallelize

---

[Closing thought]

[Your name]
[Your email + lab affiliation]
```

---

## Technical Note: Generating the .docx

The report is generated as a .docx file using the Node.js `docx` library. The setup mirrors `wr_v6.js`:

- **Color palette**: Navy headings, blue accents, light gray backgrounds
- **Typography**: Arial, varying font sizes for hierarchy
- **Layout**: Two-column metadata table (left: labels, right: values), then full-width sections
- **Summary box**: Full-width table with light blue background
- **Work Done table**: Five columns (index, title, journal, DOI, status with status-based coloring)

When you run the weekly-report skill, it will:
1. Read your `研究进展日志.md` for the current week
2. Scan `papers/reading-notes/` and `replication/manifests/` for cross-references
3. Compile the .docx using the Node.js docx library
4. Save to `reports/WeeklyReport_Week[N].docx`

---

## FAQ

**Q: How long should Section 2 be?**
A: Typically 3–5 subsections, each 1–2 paragraphs. Aim for 1500–2000 words total in the report.

**Q: What if I didn't finish a paper?**
A: Mark it as "Partial" and write what you did understand. Don't pretend you read it all.

**Q: What if this week was mostly blocked or unproductive?**
A: That's fine. Say so explicitly. In Section 3, explain the blockers. In Section 4, explain how you'll unblock next week.

**Q: Can I include figures or tables?**
A: Yes. Use the same docx styling as the Word Done table. Keep them clean and minimal.

**Q: Who reads this?**
A: Your advisor, and you (6 months later when you're writing your thesis and need to remember what you did).
