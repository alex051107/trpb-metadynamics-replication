# Claude+Codex Collaboration Architecture — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a PM → Claude (designer) → Codex (executor) collaboration architecture for the TrpB MetaDynamics project, with a rigorous debate protocol for bug resolution.

**Architecture:** Claude owns planning, coordination, and review. Codex owns script generation, file modifications, and command execution. When bugs or disagreements arise, both enter a structured JSON-envelope debate until consensus. The human (PM) only makes scientific decisions and priority calls.

**Tech Stack:** CCB (Claude Code Bridge), Claude Code skills, Codex agents, JSON-based debate protocol

---

## Context

This plan was produced through a 3-round Claude↔Codex discussion (2026-03-30). Both agents reviewed all project files and reached consensus on the architecture below.

### What stays unchanged
- 6-stage pipeline (Profiler→Librarian→Janitor→Runner→Skeptic→Journalist)
- `PIPELINE_STATE.json` enforcement via pre-tool-call hook
- `failure-patterns.md` as shared error knowledge base
- Campaign manifest as frozen source of truth
- All existing `trpb-*` SKILL.md content

### What changes
- Role Assignment in both CLAUDE.md files
- `openai.yaml` files get a `default_prompt` for Codex executor context
- New debate protocol spec at `.ccb/debate-protocol.md`
- New debate storage at `.ccb/debates/`
- Coordinator agent updated with Codex dispatch rules

---

### Task 1: Update Global Role Assignment

**Files:**
- Modify: `~/.claude/CLAUDE.md` (lines 19-33, Role Assignment section)

- [ ] **Step 1: Read current Role Assignment**

Current state:
```markdown
| Role | Provider | Description |
|------|----------|-------------|
| `designer` | `claude` | Primary planner and architect |
| `inspiration` | `gemini` | Creative brainstorming |
| `reviewer` | `codex` | Scored quality gate |
| `executor` | `claude` | Code implementation |
```

- [ ] **Step 2: Replace with new Role Assignment**

```markdown
| Role | Provider | Description |
|------|----------|-------------|
| `designer` | `claude` | Plans, coordinates, dispatches tasks to Codex, reviews output |
| `executor` | `codex` | Writes/modifies scripts, generates commands, produces artifacts |
| `reviewer` | `claude` | Normal review: Claude validates Codex output against manifest |
| `debate` | `claude+codex` | Bug/failure/disagreement → structured debate until consensus |
| `inspiration` | `gemini` | Creative brainstorming (unreliable, reference only) |
| `PM` | `human` | Scientific decisions, priority calls, approvals |
```

- [ ] **Step 3: Update Peer Review Framework**

Replace the current one-directional review with:
```markdown
## Peer Review Framework

### Normal Review (green path)
After Codex completes a task, Claude validates:
1. Output artifacts exist and match expected format
2. No known failure patterns triggered (check failure-patterns.md)
3. Parameters match frozen manifest

### Debate Review (bug/failure path)
When a bug, validation failure, or disagreement is detected:
1. Either agent opens a `DEBATE_OPEN` issue
2. Follow `.ccb/debate-protocol.md` until `CONSENSUS_CONFIRMED`
3. Only then report unified answer to human

Tag conventions:
- `[REVIEW REQUEST]` — normal Claude review of Codex output
- `[DEBATE_OPEN]` — triggers debate protocol
```

- [ ] **Step 4: Verify changes**

Read the file back to confirm Role Assignment and Peer Review sections are correct.

---

### Task 2: Update Project CLAUDE.md Role References

**Files:**
- Modify: `CLAUDE.md` (project root, lines mentioning Codex/reviewer)

- [ ] **Step 1: Add Collaboration Architecture section**

After the "Key Decisions" table, add:
```markdown
## Collaboration Architecture

| Role | Provider | What they do |
|------|----------|-------------|
| PM | Zhenpeng | 科学决策、优先级、审批。动嘴不动手 |
| Designer | Claude | 规划、协调、分发任务给 Codex、review 产出 |
| Executor | Codex | 写脚本、改文件、生成命令、产出 artifacts |
| Debate | Claude+Codex | Bug/分歧 → 结构化讨论直到共识 |

> 正常流程：PM 下指令 → Claude 分解任务 → Codex 执行 → Claude review → PM 确认
> 异常流程：发现 bug → debate protocol → 共识后报告 PM
```

- [ ] **Step 2: Verify no conflicting role references elsewhere in the file**

Search for "reviewer" or "executor" references and ensure consistency.

---

### Task 3: Create Debate Protocol Spec

**Files:**
- Create: `.ccb/debate-protocol.md`

- [ ] **Step 1: Write the debate protocol document**

```markdown
# CCB Debate Protocol v1

## Purpose

When a bug, validation failure, or factual disagreement is detected during
Claude↔Codex collaboration, both agents enter a structured debate. Neither
agent may report a final answer to the human until consensus is reached.

## Trigger Conditions

Any of these triggers a `DEBATE_OPEN`:
1. Validation failure (Skeptic finds artifact mismatch)
2. Bug in generated script (runtime error, wrong output)
3. Factual disagreement between Claude and Codex
4. Parameter mismatch with frozen manifest
5. New failure pattern not in failure-patterns.md

Normal review (green path) does NOT trigger debate. Only actual issues do.

## Message Envelope

Each debate message uses this JSON structure:

    {
      "proto": "ccb-debate-v1",
      "issue_id": "DBT-YYYYMMDD-NNN",
      "round": 1,
      "from": "claude|codex",
      "to": "codex|claude",
      "type": "open|counter|update|synthesis|ack",
      "position": "bug|not_bug|needs_evidence",
      "classification": "operational|scientific|integration",
      "severity": "low|medium|high|critical",
      "claim": "One-sentence claim",
      "evidence": [
        {"kind": "file|command|log|reference", "path": "...", "detail": "..."}
      ],
      "accepts": ["Claims from the other side I agree with"],
      "rejects": ["Claims I disagree with, with reason"],
      "next_check": "Concrete action to gather more evidence",
      "would_change_my_mind_if": "What evidence would make me change position",
      "consensus": false
    }

## State Machine

    DEBATE_OPEN → DEBATE_REPLY → DEBATE_UPDATE (repeat) →
    DEBATE_SYNTHESIS (proposed by one side) →
    DEBATE_ACK (from other side) → RESOLVED

## Rules

1. Every reply MUST do one of: supply new evidence, refute a specific claim,
   or retract/revise a prior claim.
2. "I disagree" without artifact-backed evidence is invalid.
3. After 3 rounds without new evidence, the next move MUST be an evidence-
   gathering action (file read, dry run, log check, minimal reproducer).
4. No user-facing report until both sides emit matching resolution.

## Stop Conditions

| Condition | Meaning |
|-----------|---------|
| CONSENSUS_CONFIRMED | Both agree: same bug, root cause, fix, verification step |
| CONSENSUS_REJECTED | Both agree: not actually a bug |
| CONSENSUS_BLOCKED | Both agree: cannot resolve without missing artifact or human decision |
| CONSENSUS_OUT_OF_SCOPE | Both agree: PM/PI scientific decision, not executor/coordinator issue |

## Storage

- Each debate transcript: `.ccb/debates/<issue_id>.jsonl`
- Debate index: `.ccb/debates/index.json`
- Final consensus feeds `replication/validations/failure-patterns.md` if new pattern

## Consensus Summary Format

After DEBATE_ACK, the closing agent writes:

    {
      "final_claim": "...",
      "evidence_basis": ["..."],
      "agreed_fix_or_blocker": "...",
      "owner": "claude|codex|human",
      "user_safe_summary": "One paragraph for the PM"
    }

## Index Schema

`.ccb/debates/index.json`:

    {
      "debates": [
        {
          "issue_id": "DBT-20260330-001",
          "status": "open|resolved|blocked",
          "classification": "operational|scientific|integration",
          "severity": "...",
          "opened_by": "claude|codex",
          "opened_at": "ISO timestamp",
          "resolved_at": null,
          "rounds": 0,
          "transcript": ".ccb/debates/DBT-20260330-001.jsonl"
        }
      ]
    }
```

- [ ] **Step 2: Create the debates directory and empty index**

```bash
mkdir -p .ccb/debates
echo '{"debates":[]}' > .ccb/debates/index.json
```

- [ ] **Step 3: Verify the protocol file is readable**

Read it back to confirm formatting.

---

### Task 4: Expand openai.yaml Files with Default Prompts

**Files:**
- Modify: `.claude/skills/trpb-runner/agents/openai.yaml`
- Modify: `.claude/skills/trpb-skeptic/agents/openai.yaml`
- Modify: `.claude/skills/trpb-janitor/agents/openai.yaml`
- Modify: `.claude/skills/trpb-profiler/agents/openai.yaml`
- Modify: `.claude/skills/trpb-librarian/agents/openai.yaml`
- Modify: `.claude/skills/trpb-journalist/agents/openai.yaml`
- Modify: `.claude/skills/trpb-dynamics-pipeline/agents/openai.yaml`

- [ ] **Step 1: Update trpb-runner/agents/openai.yaml**

```yaml
interface:
  display_name: "TrpB Runner"
  short_description: "Execute deterministic TrpB run steps with Codex under pipeline gates"
  default_prompt: >
    Use $trpb-runner to act as the Codex executor for this repository.
    Read CLAUDE.md, PIPELINE_STATE.json, NEXT_ACTIONS.md,
    replication/validations/failure-patterns.md, and the frozen campaign
    manifest before acting. Obey pipeline stage gates and never bypass them.
    Do not make scientific decisions. Generate or modify scripts, commands,
    and validation artifacts only from verified local sources. Stop and
    escalate for protonation, charge, multiplicity, capping choices,
    unresolved SI ambiguity, or jobs expected to run longer than 1 hour.
    If a bug, failed validation, or disagreement appears, switch to
    ccb-debate-v1 protocol and do not report a final answer until
    consensus is reached.
```

- [ ] **Step 2: Update trpb-skeptic/agents/openai.yaml**

```yaml
interface:
  display_name: "TrpB Skeptic"
  short_description: "Validate TrpB pipeline artifacts against frozen manifest"
  default_prompt: >
    Use $trpb-skeptic to validate outputs for this repository.
    Read CLAUDE.md, the frozen campaign manifest, and
    replication/validations/failure-patterns.md before validating.
    Separate operational failure from scientific mismatch from integration
    overreach. If validation fails, open a DEBATE_OPEN issue using
    ccb-debate-v1 protocol in .ccb/debate-protocol.md.
    Write validation notes to replication/validations/.
    Append new failure patterns to failure-patterns.md.
```

- [ ] **Step 3: Update trpb-janitor/agents/openai.yaml**

```yaml
interface:
  display_name: "TrpB Janitor"
  short_description: "Normalize TrpB workspace for reproducible execution"
  default_prompt: >
    Use $trpb-janitor to normalize the workspace.
    Read CLAUDE.md and PIPELINE_STATE.json first.
    Standardize paths, separate raw inputs from generated artifacts,
    prepare campaign directories. Record all changes in a note.
    Do not alter scientific content while cleaning layout.
```

- [ ] **Step 4: Update trpb-profiler/agents/openai.yaml**

```yaml
interface:
  display_name: "TrpB Profiler"
  short_description: "Extract campaign facts from papers into frozen manifests"
  default_prompt: >
    Use $trpb-profiler to extract structured campaign facts.
    Read CLAUDE.md and failure-patterns.md first.
    Distinguish explicit facts from inference. Mark uncertainty.
    Output a draft campaign_manifest.yaml and stop for human review.
```

- [ ] **Step 5: Update trpb-librarian/agents/openai.yaml**

```yaml
interface:
  display_name: "TrpB Librarian"
  short_description: "Audit and gather external resources with provenance"
  default_prompt: >
    Use $trpb-librarian to audit resources for this campaign.
    Read CLAUDE.md and the frozen manifest first.
    Fetch structures, supplements, and references.
    Record missing resources instead of guessing.
```

- [ ] **Step 6: Update trpb-journalist/agents/openai.yaml**

```yaml
interface:
  display_name: "TrpB Journalist"
  short_description: "Write concise campaign reports from validated artifacts"
  default_prompt: >
    Use $trpb-journalist to write a campaign report.
    Read CLAUDE.md, the frozen manifest, and validation notes first.
    Use the campaign_report template.
    Summarize what worked, what failed, what is unresolved.
```

- [ ] **Step 7: Update trpb-dynamics-pipeline/agents/openai.yaml**

```yaml
interface:
  display_name: "TrpB Dynamics Pipeline"
  short_description: "Top-level orchestration for TrpB enhanced-sampling campaigns"
  default_prompt: >
    Use $trpb-dynamics-pipeline as the top-level orchestrator.
    Read CLAUDE.md, PIPELINE_STATE.json, NEXT_ACTIONS.md, and
    failure-patterns.md in that order. Follow the 6-stage pipeline.
    Dispatch stage-specific work to the appropriate trpb-* skill.
    Never skip stages or bypass pipeline gates.
```

---

### Task 5: Update Coordinator Agent with Dispatch Rules

**Files:**
- Modify: `.claude/agents/trpb-coordinator.md`

- [ ] **Step 1: Add Codex Dispatch section after existing "Dispatch Rules"**

Insert after the current "When to use Skeptic" section:

```markdown
## Codex Dispatch Protocol

### When to dispatch to Codex (via /ask codex)
- Script generation or modification
- File creation (validation notes, workspace normalization)
- Command sequence generation (dry-run plans, Slurm scripts)
- Artifact production (mol2, frcmod, topology files)
- Any task where the output is deterministic code or files

### When Claude handles directly (no dispatch)
- Planning and task decomposition
- Reading and interpreting project state
- Reviewing Codex output against manifest
- Updating shared state files (CLAUDE.md, NEXT_ACTIONS.md, PIPELINE_STATE.json)
- Making recommendations to the PM

### Dispatch format
When dispatching to Codex, include:
1. Current pipeline stage (from PIPELINE_STATE.json)
2. Specific task description with expected output
3. Relevant file paths Codex should read
4. Stop conditions (what requires human decision)
5. Validation criteria (how to check the output)

### Debate trigger
If Codex output fails validation OR Claude disagrees with Codex's approach:
1. Open debate per `.ccb/debate-protocol.md`
2. Do NOT report to human until consensus
3. After consensus, update failure-patterns.md if new pattern
```

- [ ] **Step 2: Verify the coordinator file is coherent**

Read the full file back to ensure no contradictions with existing content.

---

### Task 6: Verify End-to-End Architecture

- [ ] **Step 1: Verify all modified files are consistent**

Check that:
- Global CLAUDE.md role table matches project CLAUDE.md
- Debate protocol references in openai.yaml match actual protocol file path
- Coordinator dispatch rules reference correct file paths
- No orphan references to old "reviewer = codex" pattern

- [ ] **Step 2: Send verification to Codex**

Ask Codex to read the changed files and confirm the architecture is self-consistent.

- [ ] **Step 3: Update NEXT_ACTIONS.md**

Add to Done section:
```markdown
| Claude+Codex 架构设计 + 实施 | 2026-03-30 | Claude Code + Codex (debate) |
```

---

## Execution Notes

- Tasks 1-4 are independent and can run in parallel
- Task 5 depends on Task 3 (needs debate protocol to exist)
- Task 6 depends on all previous tasks
- No HPC access needed — all changes are local config files
- Total: ~15 files modified/created, 0 scientific content changed
