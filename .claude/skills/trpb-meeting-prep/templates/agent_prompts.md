# 7 Agent Prompt Templates — instantiate slot values before dispatch

Slots use `{{SLOT_NAME}}`. Fill these from Section "Required inputs" in SKILL.md
before dispatching. All 7 prompts go in ONE message with 7 Agent tool calls.

---

## Agent A — PPT theme + source-URL footers

```
Implementing Track A of {{MEETING_DATE}} meeting prep.

Goal: (1) Keep black-and-white pptx theme from 2026-04-17 (do not revert to dark
navy). (2) Add per-slide `sources` array for problem-diagnosis slides so Yu can
click through to PLUMED forum / GROMACS docs / DOI.

Scripts & data:
- `reports/tools/generate_groupmeeting.js` (engine, data-driven, do not rewrite)
- `reports/tools/groupmeeting_{{MEETING_DATE}}.data.json` (scaffold — fill this in)

COLOR lock (do not change):
BG:FFFFFF FG:000000 ACCENT:000000 MUTED:555555 CODE_BG:F5F5F5
Code block border: 333333. Table header fill: E0E0E0.

For each problem-diagnosis slide this week ({{NEW_FPS_THIS_WEEK}}), populate
`sources` with 1-3 verified URLs. Every URL must pass `curl -sI` 200/301/302.
Failing URLs fall back to "see PARAMETER_PROVENANCE.md row X".

Regenerate: `node reports/tools/generate_groupmeeting.js
reports/tools/groupmeeting_{{MEETING_DATE}}.data.json`.

Report: URL verification results, pptx size, any rendering issues.
```

---

## Agent B — TechDoc + PresenterScript + archive last week's bundle

```
Implementing Track B of {{MEETING_DATE}} meeting prep.

Create 2 new files (consolidating OR fresh this week, never 5 scattered .md):

1. `reports/GroupMeeting_{{MEETING_DATE}}_TechDoc_技术文稿.md` (800-1500 lines, 9 chapters):
   1. 背景与本周目标 (continue from last week's TechDoc 第9章 "下周计划")
   2. 问题链: one subsection per new FP ({{NEW_FPS_THIS_WEEK}})
   3. 参数完整表: every parameter in current plumed.dat with 值/Source/调大调小/Yu 可能会问/Honest answer
   4. 代码 walkthrough (3 key scripts this week)
   5. 结果分析 — CRITICAL: for any CV/validation check that resembles a prior week's check, state explicitly "上周是 X / 本周新做是 Y / 区别是 Z"
   6. Job 时间线 (current: Job {{CURRENT_JOB_ID}} at {{CURRENT_SIM_NS}} ns, max s={{CURRENT_MAX_S}})
   7. 下周 / 下阶段计划
   8. 阶段→脚本对照表
   9. Honest-broker (weak claims + systemic defenses)

2. `reports/GroupMeeting_{{MEETING_DATE}}_PresenterScript_PPT讲稿.md` (200-400 lines):
   Per-slide spoken Chinese, 100-150 字 per slide. Write for reading aloud, not for reading silently.

Archive last week's old bundle into `reports/archive/{{LAST_MEETING_DATE}}/`:
- Outline / Parameter_Defense / Drill_Prep / Script_Bilingual (use git mv if tracked, mv if untracked)

Context files to read:
- `reports/GroupMeeting_{{LAST_MEETING_DATE}}_TechDoc_技术文稿.md` (continuity)
- `replication/validations/failure-patterns.md` (every FP)
- `replication/parameters/PARAMETER_PROVENANCE.md` (parameter table source)
- `PIPELINE_STATE.json` (job state)

CRITICAL: script-name references in Chapter 8 table MUST match the actual filenames Track E produces. If uncertain, list-only, do not invent.

Report: new file line counts, archive confirmation, any source-material gaps.
```

---

## Agent C — annotated/plumed_annotated.dat sensitivity + Source upgrade

```
Implementing Track C of {{MEETING_DATE}} meeting prep.

For every parameter in `replication/metadynamics/annotated/plumed_annotated.dat`,
ensure a comment block exists directly above the parameter line following this
template:

```
# ─── <NAME> = <VALUE> ────────────────────────────────────
# Source: <SI-quote|SI-derived|Our-choice|PLUMED-default|Legacy-bug>
# 含义: <one-line physical meaning>
# 调大 2× → <value×2>: <what breaks>
# 调小 2× → <value/2>: <what breaks>
# 推荐区间: <empirical range>
```

For any new parameter introduced this week, add a new block. For parameters
whose Source changed this week (e.g. moved from Legacy-bug to SI-derived after
a paper read), update the block.

Source-tag vocabulary:
SI-quote / SI-derived / Our-choice / PLUMED-default / Legacy-bug

Sync verification (MANDATORY):
```
cd replication/metadynamics/annotated
diff <(grep -v '^#' plumed_annotated.dat | grep -v '^$') plumed.dat
# output MUST be empty
```

If diff is non-empty, annotations broke the action lines. Fix.

Report: list all parameters and their Source tag, diff verification result.
```

---

## Agent D — metadynamics folder cleanup

```
Implementing Track D of {{MEETING_DATE}} meeting prep.

Check `replication/metadynamics/` for:
- New `.bak_*` files introduced this week → move to `archive_pre_{{MEETING_DATE}}/`
- Any new subdirectories that lack a README.md
- Any Apr/May dates on "current" files that are older than the parameters that cite them (stale)

If `archive_pre_{{LAST_MEETING_DATE}}/` exists (from last week), merge new
archives into it rather than creating a new dated archive dir every week.

Update `replication/metadynamics/README.md` if any sub-folder's role changed
(e.g. multi_walker went from "staged" to "running").

Report: what was archived, which READMEs updated, any files where you weren't
sure what to do with (flag for user).
```

---

## Agent E — new MetaD variant scripts (only if needed this week)

```
Implementing Track E of {{MEETING_DATE}} meeting prep.

This week's new MetaD variant: {{NEW_METAD_VARIANT_IF_ANY}}

If Phase 2 triggered (10-walker production): scripts exist already in
multi_walker/; this week validate they still match current single_walker/plumed.dat
physics parameters (SIGMA, LAMBDA, etc.) and update if single_walker drifted.

If Phase 3 triggered (4HPX dual-seed): new scripts needed in
`replication/metadynamics/dual_seed/`. Follow the multi_walker/ pattern (plumed.dat
+ setup_walkers.sh + submit_array.sh + README.md with SI-derived rationale).

If neither: skip Track E this week. Report: "no new MetaD variant scripts needed
this week because {{REASON}}".

Report: files created/updated, bash -n pass, diff vs single_walker/plumed.dat
showing only intended differences.
```

---

## Agent F — timeline + state sync

```
Implementing Track F of {{MEETING_DATE}} meeting prep.

Create `replication/validations/{{MEETING_DATE}}_single_walker_timeline.md`
updating the cumulative Job timeline. Latest row: Job {{CURRENT_JOB_ID}},
{{CURRENT_SIM_NS}} ns, max s={{CURRENT_MAX_S}}.

Update `PIPELINE_STATE.json`:
- top-level `last_updated`: {{MEETING_DATE}}T<HH:MM:SS>Z
- `stages.3_runner.current_job`: {{CURRENT_JOB_ID}}
- `stages.3_runner.current_sim_ns`: {{CURRENT_SIM_NS}}
- `stages.3_runner.current_max_s`: {{CURRENT_MAX_S}}
- `stages.4_skeptic.blocking_issue`: updated to reflect current job, not stale prior-week job
- `active_failure_patterns`: add any new FP-XXX entries from this week (dict schema: id/discovered/title/severity/status/see_also)

Update `NEXT_ACTIONS.md`:
- replace `## Current` block with current state
- replace `## Next 48 hours` block with decisions that follow from {{KEY_DECISION_GATE}}

Report: timeline line count, before/after PIPELINE_STATE field values, any
inconsistencies discovered (e.g. stage 3 says still in Ain.frcmod but we're
well past that).
```

---

## Agent G — SSH inspection checklist refresh

```
Implementing Track G of {{MEETING_DATE}} meeting prep.

Current file: `replication/metadynamics/single_walker/SSH_INSPECTION_CHECKLIST.md`

Review for drift:
- Does the checklist reference the right current Job ID ({{CURRENT_JOB_ID}})?
- Any new failure signatures this week (from failure-patterns.md this week's
  additions) that need a new inspection step?
- GROMACS version / partition / conda env names still accurate?

If 10-walker now running: create a parallel
`multi_walker/SSH_INSPECTION_CHECKLIST.md` with per-walker COLVAR + shared HILLS
checks (10 COLVAR files in walker_0..9 + HILLS.0..HILLS.9 in parent).

Use md5sum (Linux), not md5 (macOS). Test any embedded Python heredoc syntax
locally before committing (python3 -c should parse).

Report: line count, all 8 steps still have command + 健康/异常 labels, any
Longleaf-specific commands that need verification.
```

---

## Agent dispatch convention

All 7 agents run in one message. General-purpose for A/B/C/D/F/G; codex:codex-rescue for E (scripts).

After all return:
1. Claude cross-track coherence check (Step 2 of SKILL.md)
2. `/ask codex` adversarial review (Step 3)
3. Git merge only after Codex greenlight (Step 4)
