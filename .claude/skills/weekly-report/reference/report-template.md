# Report Template

## Header Table

| Field | Value |
|-------|-------|
| To | [Advisor Name] |
| From | Zhenpeng Liu |
| Date | [YYYY-MM-DD] |
| Week | #N: [one-phrase theme] |

## Project Context (2-3 sentences)

Explain what the project is and why it matters, in plain language that someone
outside the project can follow. Future reports can shorten this to one sentence
("continuing from last week...") but Week 1-2 reports need the full version.

Example: "I am replicating a MetaDynamics-based conformational analysis of TrpB
enzymes (Osuna group, JACS 2019). The goal is to validate this method on known
systems, then apply it to screen AI-generated enzyme variants from the Anima Lab
GenSLM pipeline."

## Pipeline Overview

A compact numbered list showing the overall plan with current position marked.
Update the marker each week. Example:

```
Phase 1: Replicate published results
  [1] Environment setup            DONE
  [2] PLP cofactor parameterization   ← NEXT
  [3] Reference path generation
  [4] System preparation
  [5] 500 ns conventional MD
  [6] Well-tempered MetaDynamics
  [7] Compare with published results
Phase 2: Apply to GenSLM-designed enzymes
Phase 3: Build reward function for design loop
```

## Summary Box

One paragraph, 3-5 sentences. Answer two questions:
- What was the central focus this week?
- What is the main unresolved question right now?

## Section 1: Work Done

Table with 5 columns:

| # | Task | Category | Context | Status |
|---|------|----------|---------|--------|

**Category values**: Paper | Setup | Simulation | Debug | Analysis | Documentation

**Status values**: Done | Partial | Running | Blocked | Queued

Include both papers read and hands-on tasks. One row per distinct item.

## Section 2: What I Learned

One subsection per major topic. Two types of subsection:

**Type A: Paper insight**
1. One sentence: what is this paper about?
2. 2-3 specific findings relevant to the project. Cite inline: (Author, Year) or (SI Table S2).
3. How it changes my plan or understanding

**Type B: Hands-on insight**
1. One sentence: what did I set up or run?
2. What I learned that I wouldn't have known from just reading
3. How it affects the next step

**Inline citations:** When stating a specific number (barrier height, distance,
parameter value), always note where it came from. Examples:
- "The O-to-C barrier is ~6 kcal/mol (Maria-Solano et al., JACS 2019, Figure 2a)"
- "Gaussian height = 0.15 kcal/mol (SI Table S1)"
- "K82-Q2 distance threshold of 3.6 A (main text, p. 4)"

Target: 800-1200 words total for Section 2. Vary paragraph lengths. Don't
make every subsection the same shape.

## Section 3: Problems Encountered and How I Solved Them

For each problem:

**[Problem title]**

*What happened:* One sentence describing the symptom.

*Root cause:* One sentence explaining why.

*How I fixed it:* What I did, concretely.

*Lesson:* One sentence. What I'll do differently next time.

If no problems this week, write "No major blockers this week" and skip to
Section 4. Don't fabricate problems.

## Section 4: Open Questions

List 3-5 concrete uncertainties. For each:
1. State the question
2. Why it matters (what does it block?)
3. What would resolve it (optional)

## Section 5: Next Week Plan

Part A: **Papers to read** (if any):
- Title, why it matters

Part B: **Tasks**
- Numbered list, concrete and achievable
- Note dependencies between tasks
- Be realistic about HPC queue times, runtime, etc.

## Section 6: Key Simulation Parameters

Formal table listing all confirmed parameters with source citations.

| Parameter | Value | Source |
|-----------|-------|--------|
| Force field | ff14SB | SI Methods, JACS 2019 |
| Water model | TIP3P | SI Methods |
| ... | ... | ... |

Only include parameters that have been confirmed from primary sources.
If a parameter is estimated or assumed, mark it clearly.

## Section 7: References

Full bibliography. For each paper:
- Authors, title, journal, year, DOI
- One sentence: what this paper contributes to the project

Format: numbered list, sorted by first citation order in the report.
