---
name: trpb-meeting-prep
description: One-shot generate the weekly group-meeting deliverable bundle (pptx + TechDoc + PresenterScript) for TrpB MetaDynamics progress. Use when user says "准备组会" / "meeting prep" / "下周组会材料" / "写这周的 PPT".
---

# TrpB Group Meeting Prep — one-shot bundle generator

This skill generates the weekly deliverable bundle for Yu Zhang meetings in the
established format. Output = 3 files + 1 skeleton for post-meeting notes:

1. `reports/GroupMeeting_<DATE>.pptx` — **black-and-white** slide deck, 10 slides
2. `reports/GroupMeeting_<DATE>_TechDoc_技术文稿.md` — 800–1500 line deep-dive tech doc (for post-meeting reference + drill-depth answers)
3. `reports/GroupMeeting_<DATE>_PresenterScript_PPT讲稿.md` — 200–400 line 对着念的 Chinese口语讲稿
4. `reports/MeetingNotes_<DATE>.docx` — skeleton to fill after meeting

## Invocation

User says something like:
- "准备 2026-04-24 组会"
- "下周组会材料"
- "meeting prep for this week"
- "写这周的 PPT"

## Preconditions (check FIRST, do not proceed without)

1. Current `PIPELINE_STATE.json` stage + `current_job` fields populated (the deliverables need real numbers)
2. `replication/validations/failure-patterns.md` up-to-date (every FP-XXX that happened this week is logged)
3. `replication/parameters/PARAMETER_PROVENANCE.md` covers every numerical parameter currently in production plumed.dat
4. Last week's `reports/GroupMeeting_<prev-date>.pptx` exists (visual-style reference)

If any precondition fails, STOP and tell user what's missing before generating anything.

## The 7-track parallel dispatch pattern

The 2026-04-17 meeting prep validated this pattern. Reuse it unchanged:

| Track | Scope | Agent type |
|-------|-------|------------|
| **A** | PPT theme (black-white) + source-URL footer per problem slide | general-purpose |
| **B** | Reports tri-file consolidation (TechDoc + PresenterScript; archive last week's stale bundle) | general-purpose |
| **C** | Upgrade `replication/metadynamics/annotated/plumed_annotated.dat` with any new parameter + Source + 调大/调小 sensitivity | general-purpose |
| **D** | Clean `replication/metadynamics/` — archive .bak files introduced this week | general-purpose |
| **E** | Any new MetaD variant scripts this week needs (e.g. 10-walker setup, Phase-3 dual-seed) | codex:codex-rescue |
| **F** | Update `replication/validations/<DATE>_single_walker_timeline.md` + `PIPELINE_STATE.json` + `NEXT_ACTIONS.md` | general-purpose |
| **G** | Refresh `single_walker/SSH_INSPECTION_CHECKLIST.md` if any new failure signature this week | general-purpose |

Dispatch all 7 **in a single message with 7 Agent tool calls in parallel**.
Each agent's full prompt lives in `templates/agent_prompts.md` (load that file
and instantiate with this week's facts before dispatching).

## Required inputs to instantiate the skill

Before firing agents, collect these from user or PIPELINE_STATE:

| Slot | Example | Where it comes from |
|------|---------|---------------------|
| `MEETING_DATE` | `2026-04-24` | user asks for this date |
| `LAST_MEETING_DATE` | `2026-04-17` | previous file in `reports/` |
| `CURRENT_JOB_ID` | `44008381` | `PIPELINE_STATE.json` |
| `CURRENT_SIM_NS` | `25.56` | `PIPELINE_STATE.json` |
| `CURRENT_MAX_S` | `2.794` | `PIPELINE_STATE.json` |
| `NEW_FPS_THIS_WEEK` | `["FP-024","FP-025","FP-026","FP-027"]` | diff failure-patterns.md vs last week |
| `KEY_DECISION_GATE` | "50 ns max s≥5 → Phase 2" | user-stated milestone |
| `TOP_3_STORYLINES` | e.g. "SIGMA-floor fix / CV audit cross-species / safe checkpoint restart" | user |

## Execution workflow

### Step 0 — Scaffold data JSON

Copy `templates/groupmeeting_data.template.json` to
`reports/tools/groupmeeting_<DATE>.data.json` and fill in the slot values.

### Step 1 — Fire 7 agents in parallel

Single message, 7 Agent tool calls. Each prompt pulled from
`templates/agent_prompts.md` and instantiated with the slot values above.

**CRITICAL constraints every agent must receive**:
- "Every numerical parameter you cite must trace to `PARAMETER_PROVENANCE.md`. If it's not there, STOP and flag — do not invent."
- "Every external URL you embed must be `curl -sI` verified 200/301/302. Failing URLs fall back to internal provenance reference."
- "Do NOT duplicate last-week's CV checks. If the same CV-level validation is being done again, explicitly label what's NEW vs REPEAT in the wording."

### Step 2 — Cross-track coherence check (Claude self-review)

After all 7 return, verify:
- Track B's TechDoc Chapter 8 script-names match Track E's actual filenames (most common drift bug)
- Track A's pptx sources[] array matches the PLUMED/GROMACS URLs that Track B's TechDoc cites (same URL on both surfaces)
- Track C's annotated file Source tags match Track B's Chapter 3 parameter table Source column (no conflict)
- Track F's timeline job numbers match Track A's Slide 6 numbers

Fix any drift BEFORE exiting. This is what failed in 2026-04-17 v1 (TechDoc said `select_snapshots.py` but Track E produced `setup_walkers.sh`).

### Step 3 — Codex adversarial review (mandatory, not skippable)

After Step 2 passes, send to Codex via `/ask codex`:
```
/ask codex 请 review 本周组会产出：
- reports/GroupMeeting_<DATE>.{pptx, TechDoc, PresenterScript}
- replication/metadynamics/annotated/plumed_annotated.dat
- replication/validations/<DATE>_single_walker_timeline.md
重点：(1) SI 引用对不对（防 FP-027 类误读）；(2) 和上周比，哪些是真新工作，哪些是重复检查（用户讨厌被当成重复劳动）；(3) 所有 Our-choice 参数的 sensitivity 叙述有无 overstate
```

Do NOT merge before Codex greenlights or raises addressable issues.
If Codex is rate-limited, schedule a `ScheduleWakeup` 2 hours out to retry.

### Step 4 — Git merge + cleanup

After Codex signoff:
- Commit all 7 tracks in ONE commit (not per-track) with message template from `templates/commit_message.md`
- Delete any `diag/` branches that were wrong-turns this week (confirm with user first)
- Leave `fix/*` branches intact for future squash-merge to master
- Do NOT push unless user explicitly says "push" — this is a private research repo, but still require explicit authorization

### Step 5 — Register post-meeting cron

Schedule a `/cron_create` one-shot reminder 1 hour after meeting start:
"Fill MeetingNotes_<DATE>.docx with Yu's feedback from transcript at `.local_scratch/<DATE> 组会.md`"

## Anti-patterns (learned from 2026-04-17 retro)

1. **Don't frame recurring validations as "fresh"** — if it's "we're double-checking X again", say so; if it's genuinely a new dimension (different method, different inputs, different species, etc.), label it explicitly as different. Cross-species projection (4HPX) vs plumed driver replay on own trajectory = different; rerunning the same sanity check on a new SIGMA value = same.

2. **Don't cite fake PLUMED forum URLs** — the bottom-of-slide source links must be verified live. This was the FP-027 lesson crystallized: Yu will click a link; if it 404s your credibility dies.

3. **Don't consolidate TechDoc + PresenterScript into one file** — they serve different cognitive modes (read-and-understand vs read-aloud-while-performing).

4. **Don't let multiple agents modify the same file** — the 7-track split was specifically designed so each track touches disjoint paths.

5. **Don't skip the cross-track coherence check (Step 2)** — the script-name drift between TechDoc Ch8 and multi_walker/ actuals bit us once; the check catches it.

## Diagnostic Judgment Principles (add to every TechDoc as Chapter 10)

When preparing meeting materials, every TechDoc MUST include a "判断原则与诊断规则"
chapter. This chapter captures the reasoning behind decisions so the user (and future
agents) can verify them independently.

### Required sections in Chapter 10

**10.1 HILLS 法医分析三步法** — Always include:
1. Sigma health check: `sigma_path.sss` min/max vs SIGMA_MIN/SIGMA_MAX
2. Bias history check: absence of `bck.*.HILLS`
3. Deposition rate check: actual line count vs expected from PACE

**10.2 Per-parameter unit clarification** — For any parameter with non-obvious units,
explain why it's in those units. Specifically for SIGMA / SIGMA_MIN / SIGMA_MAX:
- `SIGMA` = single Cartesian nm scalar (PLUMED docs: "one number that has distance units")
- `SIGMA_MIN/MAX` = per-CV values in native CV units, comma-separated
- s(R) is dimensionless (1–15); z(R) is nm² (because z = (1/λ)·..., λ in nm⁻²)
- Never mix units: 0.3 s-units ≠ 0.3 nm

**10.3 Phase decision logic** — Document the threshold, the SI basis, and what
conformational state it corresponds to. Phase gates must cite SI line numbers
or explicit "Our-choice" if SI is silent.

**10.4 File locations** — After any HILLS/COLVAR download, update this section
with the local paths, download date, and line counts for traceability.

**10.5 "Re-derive trap" rule** — Before re-interpreting any SI numerical value,
check the repo annotations (PARAMETER_PROVENANCE.md, failure-patterns.md,
papers/reading-notes/). If a prior annotation exists with a source tag, do NOT
re-derive without explicit PM instruction.

### How to instantiate Chapter 10 for a new meeting

1. Run HILLS forensics and paste the sigma_sss range into 10.1
2. List any new parameters introduced this week and explain their units in 10.2
3. Update Phase thresholds and SI citations in 10.3 if milestones changed
4. Update file paths/dates in 10.4 after downloading fresh HILLS/COLVAR
5. Add any new FP-XXX lessons to 10.5 that fall in the "re-derive trap" category

---

## References

- `templates/agent_prompts.md` — the 7 agent prompts with slot placeholders
- `templates/groupmeeting_data.template.json` — JSON shape for the pptx data file
- `templates/commit_message.md` — git commit message template
- `reference/2026-04-17_retro.md` — what went right/wrong this week (living doc)
- `reports/tools/generate_groupmeeting.js` — the data-driven pptx engine (don't modify unless adding new slide type)
- `reports/GroupMeeting_2026-04-17.*` — reference implementation of the 3-file bundle
- `replication/metadynamics/single_walker/HILLS` — current production HILLS (download fresh each time)
- `replication/metadynamics/archive_pre_2026-04-15/job42679152_sigma_stuck_FP024/HILLS` — FP-024 reference (sigma collapse signature)
- `replication/metadynamics/archive_pre_2026-04-15/job41514529_fp022_lambda/HILLS` — FP-022 reference (wrong λ signature)
