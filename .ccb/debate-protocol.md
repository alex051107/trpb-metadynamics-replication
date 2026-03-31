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

```json
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
```

## State Machine

```
DEBATE_OPEN → DEBATE_REPLY → DEBATE_UPDATE (repeat as needed) →
DEBATE_SYNTHESIS (proposed by one side when positions align) →
DEBATE_ACK (from other side) → RESOLVED
```

## Rules

1. Every reply MUST do one of: supply new evidence, refute a specific claim,
   or retract/revise a prior claim.
2. "I disagree" without artifact-backed evidence is invalid.
3. After 3 rounds without new evidence, the next move MUST be an evidence-
   gathering action (file read, dry run, log check, minimal reproducer).
   Debate continues afterward, but stagnation is not allowed.
4. No user-facing report until both sides emit matching resolution.

## Stop Conditions

| Condition | Meaning |
|-----------|---------|
| `CONSENSUS_CONFIRMED` | Both agree: same bug, root cause, fix, verification step |
| `CONSENSUS_REJECTED` | Both agree: not actually a bug |
| `CONSENSUS_BLOCKED` | Both agree: cannot resolve without missing artifact or human decision |
| `CONSENSUS_OUT_OF_SCOPE` | Both agree: PM/PI scientific decision, not executor/coordinator issue |

## Storage

- Each debate transcript: `.ccb/debates/<issue_id>.jsonl` (one JSON object per message)
- Debate index: `.ccb/debates/index.json`
- Final consensus feeds `replication/validations/failure-patterns.md` if new pattern

## Consensus Summary Format

After DEBATE_ACK, the closing agent writes:

```json
{
  "final_claim": "...",
  "evidence_basis": ["..."],
  "agreed_fix_or_blocker": "...",
  "owner": "claude|codex|human",
  "user_safe_summary": "One paragraph for the PM"
}
```

## Index Schema

`.ccb/debates/index.json`:

```json
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
