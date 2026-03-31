# Pipeline Enforcement Design

> **Problem**: AI agents repeatedly skip pipeline stages (Librarian, Janitor) and jump directly to Runner execution. This has happened at least 3 times (documented in FP-011), causing wrong parameters, SCF failures, and wasted HPC time.

> **Author**: Systems analysis, 2026-03-30
> **Status**: Design complete, ready for implementation

---

## 1. Root Cause Analysis

### 1.1 Why agents skip stages

After reading CLAUDE.md, PROTOCOL.md, RULES.md, failure-patterns.md (FP-011), and the coordinator agent definition, there are **five compounding root causes**:

#### RC-1: Prose instructions lack machine-enforceable gates

CLAUDE.md lines 59-68 describe the pipeline as a **table** -- a human-readable reference, not a machine-checkable constraint. The agent reads "Librarian -> Janitor -> Runner" as information, not as a hard gate. There is no mechanism that prevents the agent from issuing a `ssh longleaf` command while the campaign status says "Librarian done -- Janitor stage next."

The instructions say "don't skip stages" but never define **what artifact proves a stage is complete**. Without a concrete completeness test, the agent has no way to verify compliance even if it wants to.

#### RC-2: No single source of truth for current stage

The campaign's current stage is recorded in three places:
- `CLAUDE.md` line 103: "Librarian done (2026-03-30) -- Janitor stage next"
- `PROTOCOL.md` line 70: same text, duplicated
- `NEXT_ACTIONS.md`: implicit from task list

These can drift. The agent picks whichever it reads first (usually CLAUDE.md), and even then, the status is embedded in a markdown table cell -- easy to overlook during a long context window.

#### RC-3: Eager execution bias in LLMs

LLMs have a well-documented tendency to "be helpful" by producing concrete outputs (commands, code, file modifications) rather than performing meta-cognitive checks. When a user says "run PLP parameterization," the agent's strongest activation is toward the Runner skill, not toward checking whether Librarian and Janitor are complete. The startup sequence in CLAUDE.md (lines 3-10) tries to counter this, but it's a soft instruction competing against a strong behavioral bias.

#### RC-4: Skills are invocable but not gated

The `trpb-runner` skill exists alongside `trpb-librarian` and `trpb-janitor`, but nothing prevents invoking `trpb-runner` before `trpb-librarian` has produced its required artifact. The skills are peer-level tools, not stages in a pipeline with dependencies.

#### RC-5: The coordinator agent is advisory, not authoritative

`trpb-coordinator.md` has a startup sequence and dispatch rules, but it's an agent definition -- it only activates when explicitly invoked. The main agent (the one the user talks to directly) has no obligation to route through the coordinator. And even the coordinator's rules are prose, not programmatic gates.

### 1.2 Summary

The system relies entirely on the agent **choosing** to follow instructions. There is no mechanism that **prevents** non-compliance. This is like having a fire code written on a poster but no fire doors.

---

## 2. Solution Evaluation

### Option A: Claude Code Hooks

**Mechanism**: Configure `settings.json` hooks to run a script before every `Bash` tool call. The script reads a `PIPELINE_STATE.json` file, checks the current stage, and blocks commands that belong to a later stage (e.g., blocks `ssh`, `antechamber`, `sbatch` if stage < Runner).

**Reliability**: HIGH. Hooks execute outside the LLM -- they are programmatic enforcement, not prompt-based. The agent literally cannot run blocked commands.

**Overhead**: LOW. A 50ms JSON check before each Bash call.

**User friction**: LOW. The user only needs to advance the stage marker when ready (by editing a JSON file or running a stage-advance command).

**Compatibility**: GOOD. Claude Code hooks support `pre-tool-call` events with match patterns on tool names.

**Limitations**: Hooks can only block tool calls, not ensure the agent performs the right stage. An agent could technically sit idle and not do Librarian work -- it just can't skip to Runner. Also, hooks cannot currently inspect the *content* of a Bash command in all configurations (they can match tool name but content filtering depends on the hook script).

**Verdict**: Strong foundation but insufficient alone -- prevents bad actions but doesn't drive correct actions.

### Option B: Agent Teams with Stage Gates

**Mechanism**: Each stage is a separate agent. The coordinator dispatches to stage-specific agents. Stage N agent's instructions say "you can ONLY do X." Stage N+1 agent requires a specific artifact file from stage N before it activates.

**Reliability**: MEDIUM-HIGH. Each agent has a narrow scope, reducing eager execution. But the main agent still needs to correctly dispatch, and agent teams add context overhead.

**Overhead**: HIGH. Each agent invocation is a separate context window. The coordinator agent must read state, dispatch, collect results, update state -- 4-5 extra LLM calls per stage.

**User friction**: MEDIUM. User must understand the agent team model. Debugging failures requires understanding which agent did what.

**Compatibility**: GOOD. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is already enabled in settings.json.

**Limitations**: Agent teams are still LLM-based -- a sufficiently "eager" agent could still deviate within its own scope. Also, the current agent team implementation uses `SendMessage` which is asynchronous and hard to gate.

**Verdict**: Good for separation of concerns but too much overhead for a single-user research project.

### Option C: Enhanced CLAUDE.md with Mandatory Checklist

**Mechanism**: Add a machine-readable `PIPELINE_STATE` block to CLAUDE.md. Before any action, the agent must read and output the current stage. Add explicit "STOP: you are in stage X, you cannot do Y" instructions.

**Reliability**: LOW. This is what the current system already does (prose instructions). Making the checklist more explicit helps marginally, but the core problem remains: the agent can choose to ignore it. FP-011 proves this approach fails under the "eager execution" bias.

**Overhead**: LOW. Just reading a few extra lines.

**User friction**: LOW.

**Compatibility**: GOOD.

**Verdict**: Necessary complement but not sufficient as the primary mechanism.

### Option D: Pipeline Enforcer Sub-Agent

**Mechanism**: Before any work session, a "pipeline enforcer" sub-agent runs automatically. It reads all state files, determines the current stage, and outputs a binding instruction block that the main agent must follow. The enforcer also runs after every N tool calls to check for violations.

**Reliability**: MEDIUM. Better than prose alone because the enforcer is a separate "voice" that explicitly states constraints. But it's still LLM-based -- the main agent can override it.

**Overhead**: MEDIUM. One extra agent call at session start, periodic checks.

**User friction**: LOW.

**Compatibility**: MEDIUM. Requires either hooks or manual invocation to trigger the enforcer.

**Verdict**: Good for detection but not prevention.

### Option E: Skeptic Auto-Review

**Mechanism**: A background skeptic agent reviews actions periodically and flags violations.

**Reliability**: LOW for prevention. The violation has already happened by the time the skeptic catches it. Good for detection and documentation.

**Overhead**: HIGH if continuous. Must run in background, consuming context.

**User friction**: LOW.

**Compatibility**: MEDIUM. Background agents via ralph-loop or similar.

**Verdict**: Useful as a safety net but too late for prevention.

---

## 3. Recommended Solution: Hooks + State File + Enhanced CLAUDE.md (A + C hybrid)

The best approach combines:

1. **PIPELINE_STATE.json** -- single source of truth for current stage (from Option C, but machine-readable)
2. **Pre-tool-call hook** -- blocks Runner-stage commands when stage < 3 (from Option A)
3. **Stage-advance command** -- a simple script the user or agent runs to advance the stage after verification
4. **Enhanced CLAUDE.md instructions** -- explicit "read PIPELINE_STATE.json before any action" (from Option C)
5. **Post-session skeptic check** -- optional, lightweight validation (from Option E, as safety net)

### Why this combination works

- **Hooks** handle prevention (hard gate, not bypassable by the LLM)
- **State file** provides a single, unambiguous source of truth
- **Enhanced instructions** guide the agent toward correct behavior within the allowed stage
- **Skeptic check** catches edge cases the hook missed

### What this does NOT try to do

- Does not use agent teams (too much overhead for a solo researcher)
- Does not try to make the LLM perfectly obedient (impossible; instead, it constrains the action space)
- Does not add user friction beyond a simple stage-advance step

---

## 4. Implementation

### 4.1 PIPELINE_STATE.json

Location: `/Users/liuzhenpeng/trpb-project/PIPELINE_STATE.json`

```json
{
  "schema_version": 1,
  "campaign_id": "osuna2019_benchmark",
  "current_stage": 2,
  "stage_name": "janitor",
  "stages": {
    "0_profiler": {
      "status": "complete",
      "completed_at": "2026-03-28",
      "artifact": "replication/manifests/osuna2019_benchmark_manifest.yaml",
      "verified_by": "human"
    },
    "1_librarian": {
      "status": "complete",
      "completed_at": "2026-03-30",
      "artifact": "replication/inventories/resource_inventory.md",
      "verified_by": "human"
    },
    "2_janitor": {
      "status": "in_progress",
      "started_at": "2026-03-30",
      "artifact": null,
      "verified_by": null
    },
    "3_runner": {
      "status": "not_started",
      "artifact": null
    },
    "4_skeptic": {
      "status": "not_started",
      "artifact": null
    },
    "5_journalist": {
      "status": "not_started",
      "artifact": null
    }
  },
  "blocked_tools_until_stage": {
    "3": ["ssh", "antechamber", "parmchk2", "tleap", "sbatch", "srun", "pmemd", "gmx mdrun", "gaussian"],
    "4": ["fes_analysis", "reweight"]
  },
  "last_updated": "2026-03-30T12:00:00Z"
}
```

**Design decisions**:
- `current_stage` is an integer for easy comparison in shell scripts
- `blocked_tools_until_stage` maps stage numbers to command substrings that should be blocked until that stage is reached
- `artifact` is the file that proves stage completion -- the hook can verify it exists
- `verified_by` tracks whether human or agent approved the stage transition

### 4.2 Pipeline Gate Hook Script

Location: `/Users/liuzhenpeng/trpb-project/.claude/hooks/pipeline_gate.sh`

```bash
#!/bin/bash
# Pipeline Gate Hook
# Runs before every Bash tool call in the trpb-project directory.
# Reads PIPELINE_STATE.json and blocks commands belonging to future stages.
#
# Exit 0 = allow the command
# Exit 2 = block the command (Claude Code hook convention)

set -euo pipefail

STATE_FILE="/Users/liuzhenpeng/trpb-project/PIPELINE_STATE.json"

# If no state file exists, allow everything (first-time setup)
if [ ! -f "$STATE_FILE" ]; then
  exit 0
fi

# Read current stage
CURRENT_STAGE=$(python3 -c "
import json, sys
with open('$STATE_FILE') as f:
    state = json.load(f)
print(state.get('current_stage', 99))
" 2>/dev/null || echo "99")

# Read the command being executed from stdin (Claude Code passes tool input as JSON)
TOOL_INPUT=$(cat)
COMMAND=$(echo "$TOOL_INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('command', ''))
" 2>/dev/null || echo "")

# If we couldn't parse, allow (fail open for non-pipeline commands)
if [ -z "$COMMAND" ]; then
  exit 0
fi

# Stage 3 (Runner) blocked commands -- these are execution commands
if [ "$CURRENT_STAGE" -lt 3 ]; then
  RUNNER_BLOCKED="antechamber|parmchk2|tleap|pmemd|gmx mdrun|sbatch|srun|gaussian|g16"

  if echo "$COMMAND" | grep -qEi "$RUNNER_BLOCKED"; then
    # Output error message that Claude Code will show to the agent
    cat <<ERRMSG
PIPELINE GATE BLOCKED: Cannot run execution commands.

Current stage: $CURRENT_STAGE ($(python3 -c "
import json
with open('$STATE_FILE') as f:
    print(json.load(f).get('stage_name', 'unknown'))
"))
Required stage: 3 (runner)

The command "$COMMAND" belongs to the Runner stage.
You must complete the current stage first.

To advance the stage, run: python3 /Users/liuzhenpeng/trpb-project/.claude/hooks/advance_stage.py

Read PIPELINE_STATE.json to see what artifacts are needed to complete the current stage.
ERRMSG
    exit 2
  fi
fi

# Allow everything else
exit 0
```

### 4.3 Stage Advance Script

Location: `/Users/liuzhenpeng/trpb-project/.claude/hooks/advance_stage.py`

```python
#!/usr/bin/env python3
"""
Advance the pipeline stage after verifying the current stage's artifact exists.

Usage:
  python3 advance_stage.py                  # interactive: show status, ask to advance
  python3 advance_stage.py --check          # just print current stage, no changes
  python3 advance_stage.py --force <N>      # force set to stage N (human override)
"""

import json
import os
import sys
from datetime import datetime, timezone

STATE_FILE = "/Users/liuzhenpeng/trpb-project/PIPELINE_STATE.json"
PROJECT_ROOT = "/Users/liuzhenpeng/trpb-project"

STAGE_NAMES = {
    0: "profiler",
    1: "librarian",
    2: "janitor",
    3: "runner",
    4: "skeptic",
    5: "journalist",
}

# What artifact must exist for each stage to be considered complete
STAGE_ARTIFACTS = {
    0: "replication/manifests/osuna2019_benchmark_manifest.yaml",
    1: "replication/inventories/resource_inventory.md",
    2: None,  # Janitor completion is verified by directory structure check
    3: None,  # Runner completion is verified by run output files
    4: None,  # Skeptic completion is verified by validation notes
    5: None,  # Journalist completion is verified by campaign report
}


def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    print(f"State saved. Current stage: {state['current_stage']} ({state['stage_name']})")


def check_artifact(stage_num):
    """Check if the artifact for the given stage exists."""
    artifact = STAGE_ARTIFACTS.get(stage_num)
    if artifact is None:
        return True  # No artifact required
    full_path = os.path.join(PROJECT_ROOT, artifact)
    return os.path.exists(full_path)


def main():
    if not os.path.exists(STATE_FILE):
        print(f"ERROR: {STATE_FILE} does not exist. Create it first.")
        sys.exit(1)

    state = load_state()
    current = state["current_stage"]

    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        print(f"Current stage: {current} ({STAGE_NAMES.get(current, '?')})")
        for stage_key, stage_data in state["stages"].items():
            status = stage_data.get("status", "unknown")
            print(f"  {stage_key}: {status}")
        return

    if len(sys.argv) > 2 and sys.argv[1] == "--force":
        new_stage = int(sys.argv[2])
        state["current_stage"] = new_stage
        state["stage_name"] = STAGE_NAMES.get(new_stage, "unknown")
        save_state(state)
        print(f"FORCED to stage {new_stage} ({STAGE_NAMES.get(new_stage, '?')})")
        return

    # Normal advance: check artifact, then advance
    if current >= 5:
        print("Already at final stage (journalist). Nothing to advance.")
        return

    if not check_artifact(current):
        artifact = STAGE_ARTIFACTS.get(current)
        print(f"CANNOT ADVANCE: Stage {current} ({STAGE_NAMES[current]}) artifact missing.")
        print(f"  Required: {artifact}")
        print(f"  Full path: {os.path.join(PROJECT_ROOT, artifact)}")
        sys.exit(1)

    # Mark current stage complete
    stage_key = f"{current}_{STAGE_NAMES[current]}"
    state["stages"][stage_key]["status"] = "complete"
    state["stages"][stage_key]["completed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Advance to next stage
    next_stage = current + 1
    next_key = f"{next_stage}_{STAGE_NAMES[next_stage]}"
    state["stages"][next_key]["status"] = "in_progress"
    state["stages"][next_key]["started_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    state["current_stage"] = next_stage
    state["stage_name"] = STAGE_NAMES[next_stage]

    save_state(state)
    print(f"Advanced: {current} ({STAGE_NAMES[current]}) -> {next_stage} ({STAGE_NAMES[next_stage]})")


if __name__ == "__main__":
    main()
```

### 4.4 Claude Code Hooks Configuration

Location: `/Users/liuzhenpeng/trpb-project/.claude/settings.json`

This is a **new project-level settings file** (separate from the global `~/.claude/settings.json`).

```json
{
  "hooks": {
    "pre-tool-call": [
      {
        "matcher": {
          "tool_name": "Bash"
        },
        "hooks": [
          {
            "type": "command",
            "command": "bash /Users/liuzhenpeng/trpb-project/.claude/hooks/pipeline_gate.sh"
          }
        ]
      }
    ]
  }
}
```

**How this works**:
- Every time Claude Code is about to execute a `Bash` tool call, the hook runs `pipeline_gate.sh` first
- The hook reads `PIPELINE_STATE.json`, checks the current stage, and greps the command for blocked patterns
- If the command is blocked, the hook exits with code 2 and prints an error message
- Claude Code shows the error to the agent, which must then adjust its behavior
- Non-Bash tool calls (Read, Write, Edit, Grep) are not gated -- agents can always read and plan

### 4.5 Changes to CLAUDE.md

The following block should be added to CLAUDE.md immediately after the startup sequence (after line 10), replacing the current pipeline table (lines 59-68):

```markdown
### Pipeline Enforcement (HARD GATE)

> **Before ANY action in this project, read `PIPELINE_STATE.json` in the project root.**
> This file contains the current pipeline stage as a machine-readable integer.
> A pre-tool-call hook BLOCKS execution commands (antechamber, sbatch, gmx, etc.)
> if the current stage < 3 (Runner). You cannot bypass this.

**To check current stage:**
```bash
python3 /Users/liuzhenpeng/trpb-project/.claude/hooks/advance_stage.py --check
```

**To advance to the next stage (after completing current stage work):**
```bash
python3 /Users/liuzhenpeng/trpb-project/.claude/hooks/advance_stage.py
```

**If the hook blocks you, do NOT try to work around it.** Instead:
1. Read PIPELINE_STATE.json to understand what stage you are in
2. Do the work for that stage (Librarian = resource audit, Janitor = directory check)
3. Advance the stage when the work is done
4. Then proceed to the next stage

**Human override (emergency only):**
```bash
python3 /Users/liuzhenpeng/trpb-project/.claude/hooks/advance_stage.py --force 3
```
```

The existing pipeline table (lines 59-68) should be kept as reference but annotated:

```markdown
> The table below is for human reference. Enforcement is via PIPELINE_STATE.json + hooks.
```

### 4.6 Updated Coordinator Agent

Add the following to the top of `.claude/agents/trpb-coordinator.md`, after the existing startup sequence:

```markdown
## Pipeline Gate (MANDATORY)

Before dispatching ANY task:

1. Run `python3 /Users/liuzhenpeng/trpb-project/.claude/hooks/advance_stage.py --check`
2. If current_stage < the required stage for the task, STOP and complete prerequisite stages first
3. The Bash hook will block execution commands anyway, but checking first avoids wasted context

Stage requirements:
- Librarian tasks: stage >= 1
- Janitor tasks: stage >= 2
- Runner tasks (antechamber, tleap, sbatch, etc.): stage >= 3
- Skeptic tasks: stage >= 4
- Journalist tasks: stage >= 5
```

---

## 5. Addressing Eager Execution Bias

The hook-based solution addresses eager execution at multiple levels:

### Level 1: Hard block (hook)
The agent physically cannot run `antechamber` or `sbatch` if the stage is wrong. This is not a suggestion -- it's an OS-level gate.

### Level 2: Error message redirection
When blocked, the hook prints a clear message telling the agent what it SHOULD be doing. This redirects the agent's attention from "run the command" to "complete the prerequisite stage."

### Level 3: Explicit stage-check instruction
The CLAUDE.md instruction to read PIPELINE_STATE.json before any action creates a "speed bump" -- the agent must first perform a read operation that reveals its constraints, before it can plan actions.

### Level 4: Narrow allowed actions per stage
By not gating Read/Write/Edit/Grep, the agent can still do productive work within the allowed stage (e.g., write inventory files during Librarian, organize directories during Janitor). It's not stuck -- it's just constrained to the right work.

---

## 6. Auto-Detection and Correction

### Detection
If an agent attempts a blocked command, the hook:
1. Prints the violation to stderr (captured by Claude Code)
2. The agent sees the error and knows it violated the pipeline
3. The error message includes the current stage and required stage

### Correction
The agent should:
1. Acknowledge the violation
2. Read PIPELINE_STATE.json
3. Determine what work remains in the current stage
4. Complete that work
5. Advance the stage
6. Retry the original command

This correction loop is automatic from the agent's perspective -- it tries, gets blocked, reads the state, does the right work, advances, and succeeds.

### Safety net: Post-session validation
Optionally, the user can add a post-session hook that runs the Skeptic check:

```json
{
  "hooks": {
    "post-session": [
      {
        "type": "command",
        "command": "python3 /Users/liuzhenpeng/trpb-project/.claude/hooks/advance_stage.py --check"
      }
    ]
  }
}
```

This prints the final state when the session ends, so the user always knows where things stand.

---

## 7. Reproducibility

The solution is reproducible because:

1. **State is in a file** (PIPELINE_STATE.json), not in the agent's memory or conversation history
2. **Enforcement is outside the LLM** (bash hook), not dependent on the agent choosing to comply
3. **Stage advance requires artifact verification** (the script checks if expected files exist)
4. **Every session starts the same way**: read PIPELINE_STATE.json, check stage, act within constraints

A new agent session tomorrow will read the same state file and face the same constraints, regardless of which model, temperature, or system prompt is used.

---

## 8. File Summary

| File | Purpose | Action |
|------|---------|--------|
| `PIPELINE_STATE.json` | Single source of truth for current stage | CREATE |
| `.claude/hooks/pipeline_gate.sh` | Pre-tool-call hook that blocks future-stage commands | CREATE |
| `.claude/hooks/advance_stage.py` | Stage advance script with artifact verification | CREATE |
| `.claude/settings.json` | Project-level hooks configuration | CREATE |
| `CLAUDE.md` | Add pipeline enforcement section after line 10 | EDIT (add ~20 lines) |
| `.claude/agents/trpb-coordinator.md` | Add pipeline gate check to startup | EDIT (add ~15 lines) |

---

## 9. Limitations and Future Work

### Known limitations

1. **Command pattern matching is imperfect**: The hook greps for command substrings like `antechamber`. An agent could theoretically run a renamed binary or use a wrapper script. This is unlikely in practice but not impossible.

2. **Stage advance is manual**: The agent or user must explicitly run `advance_stage.py`. An automated "stage is complete when artifact X exists" check could be added but risks false positives.

3. **Single campaign**: The current PIPELINE_STATE.json tracks one campaign. Multi-campaign support would need a campaign ID parameter.

4. **No rollback**: If a stage is advanced prematurely, the only fix is `--force`. A rollback command could be added.

### Future enhancements

1. **Artifact content validation**: Instead of just checking file existence, verify that `resource_inventory.md` actually has all items marked as "available" before allowing Librarian->Janitor advance.

2. **Hook logging**: Log every blocked attempt to a file for post-mortem analysis.

3. **Integration with NEXT_ACTIONS.md**: Auto-update the task queue when stages advance.

4. **Multi-campaign**: Support multiple concurrent campaigns with independent pipeline states.

---

## Appendix A: Today's Failure Trace (FP-011)

What happened on 2026-03-30:

1. User asked to run PLP parameterization
2. Agent read CLAUDE.md (saw "Librarian done -- Janitor stage next")
3. Agent **ignored** the stage indicator and jumped to Runner
4. Agent ran `antechamber -c bcc` on Longleaf with charge=0
5. SCF failed (FP-009: BCC doesn't work for PLP)
6. Agent tried charge=-2, also failed
7. Agent finally realized the charge was wrong and Librarian hadn't verified it
8. ~45 minutes of HPC time wasted

With the hook-based solution:

1. User asks to run PLP parameterization
2. Agent tries to run `antechamber` via Bash
3. Hook reads PIPELINE_STATE.json: current_stage=2 (Janitor)
4. Hook blocks the command: "Cannot run execution commands. Current stage: 2 (janitor). Required: 3 (runner)."
5. Agent reads the error, checks the state file
6. Agent completes Janitor work (directory verification)
7. Agent advances to stage 3
8. Agent reviews Librarian artifact (resource_inventory.md) to verify charge values
9. Agent runs antechamber with verified parameters

Time saved: ~45 minutes of HPC time + debugging time.
