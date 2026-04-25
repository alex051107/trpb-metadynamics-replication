# ML Layer Sub-Agent Second-Pass Audit (2026-04-25)

**Trigger**: PM directive "ML 层的设计你确定跟 codex 以及对应的 subagent 进行二次确定过了吗?"

**Sub-agent**: Explore subagent dispatched 2026-04-25 16:54, completed 16:57, ~35 min wall (id `a2393f03f164e7061`).

**Lens**: Independent second-pass; assume zero context from prior 6-round Codex chain (R1, R2, R0, R0.5, R4, R5, R7, R8). Find what 6-round chain MISSED.

**Result**: 10 findings (6 HIGH, 4 MEDIUM). 0 LOW. Software-engineering debt rather than science gaps — fixable via rewording + schema annotation, no design work needed.

---

## Findings

### 1. [HIGH] MMPBSA-truth recursion kill-switch threshold inconsistency
- File: `RED_TEAM_ATTACK_2026-04-25.md` §8.2 lines 99-103 vs `PM_BRIEF_2026-04-25.md` §1 Q2 line 50
- RED_TEAM: `|ρ| < 0.6` → TRAIN-proxy fail; `0.6-0.75` → EVAL_ONLY; `≥0.75` → usable.
- PM_BRIEF kill-switch table: threshold = `|ρ| < 0.5`.
- Decision-point divergence: a measured ρ=0.55 is TRAIN-fail per RED_TEAM but EVAL_ONLY per PM_BRIEF.
- **Fix**: align PM_BRIEF row 2 to RED_TEAM's `0.6` cutoff with explicit note `0.5 < |ρ| < 0.6 = EVAL_ONLY downgrade`.

### 2. [HIGH] state_mask_l2 mandatory vs optional contradiction
- File: `INTERFACE_DESIGN_2026-04-25.md` §5 line 126 vs §6 line 164
- §5: `state_mask_l2` is "optional" (only set if `convergence_grade.status=PASS`).
- §6: `reweight_to_unbiased()` docstring implies a row ALWAYS gets `label_grade`.
- For PROVISIONAL rows: `label_grade ∈ {EVAL_ONLY, UNCERTAIN}` but `state_mask_l2=null`. Logic correct, but never explicitly stated. Developer reading only §5 will miss the PROVISIONAL→EVAL_ONLY path.
- **Fix**: §5 line 128 annotate: `label_grade: [TRAIN only if convergence_grade.status=PASS and ESS gates pass; otherwise EVAL_ONLY if PROVISIONAL/PASS, UNCERTAIN/REJECTED if FAIL]`.

### 3. [MEDIUM] joint_features.parquet stale-state-mask propagation rule missing
- File: `INTERFACE_DESIGN_2026-04-25.md` §1 line 15 + `descriptors.py` lines 34-38
- STATE_MASKS hardcoded in descriptors.py. `mask_version` field hints at versioning but no trigger rule.
- Risk: in 4 weeks, if path-CV redefined (FP-034 style), old joint_features.parquet rows have stale `state_pseudo` labels silently propagating into L2 training.
- **Fix**: §3.1 add: "state_pseudo enum updates only on re-alignment of PATHMSD reference geometry per FP-034. On any path-CV redefine, all state_pseudo rows must be recomputed; mask_version incremented; old parquet archived."

### 4. [HIGH] GenSLM contingency narrative conflict
- File: `PR_FAQ_2026-07-18_v1_ship.md` §4 line 35 vs `PM_BRIEF_2026-04-25.md` §1 Q2 line 34
- PR_FAQ: "Fallback: V1 ships F0+state-pseudo-labels without GenSLM" (past tense, decided).
- PM_BRIEF Q2: framed as a CHOICE the PM still has to make.
- Result: question feels like theater — already decided in PR_FAQ but PM_BRIEF asks for input.
- **Fix**: rewrite PM_BRIEF Q2 lead-in: "Given INTERFACE §4 BLOCKED #1-#2 cannot close before week 3, should V1 go live with `genslm_embed=null` (recommended, unblocks V1 on time) or delay V1 for full GenSLM population?"

### 5. [MEDIUM] Activity-proxy Q1 cascades into 2 kill-switches but framed as one question
- File: `PM_BRIEF_2026-04-25.md` §1 Q1 line 33 vs `RED_TEAM_ATTACK_2026-04-25.md` §3, §8.2
- PM picks "MMPBSA" → commits V1 to MMPBSA-ρ measurement → kill-switch #2 fires on n<12 paired or |ρ|<0.6.
- Cascade not visible in PM_BRIEF Q1 framing.
- **Fix**: split PM_BRIEF Q1 → Q1a "primary activity proxy?" + Q1b "if MMPBSA, n≥12 paired commitment by week 3?".

### 6. [HIGH] Kill-switch #3 unsatisfiable preconditions
- File: `RED_TEAM_ATTACK_2026-04-25.md` §8.3 lines 106-107
- Trip if (a) PathGate-top-3 ∩ MMPBSA-top-3 = ∅ AND (b) #2 trips AND (c) no independent activity adjudication.
- If PM picks MMPBSA in Q1 (because k_cat unavailable), then (c) escape clause evaporates — kill-switch always trips on (a)+(b).
- **Fix**: rewrite §8.3 (c): "unless (c) PM pre-registered a secondary activity adjudication source (literature k_cat ≥ 5 measured values OR Yu hand-bins) before week 2. If not pre-registered, kill-switch #3 cannot be waived."

### 7. [MEDIUM] valid_for_L0/L1 boolean masks dead weight or undocumented gate?
- File: `INTERFACE_DESIGN_2026-04-25.md` §3.1 line 57 vs §5 line 131
- Schema declares `valid_for_L0` and `valid_for_L1` boolean provenance masks. §5 (joint_features schema) lists `label_grade` as gate, never references the booleans.
- Either dead weight, or implicit gate to label_grade. Two developers will wire it differently.
- **Fix**: either (a) remove valid_for_L0/L1 from schema (use label_grade only), OR (b) §6 docstring add: "Populates valid_for_L0/L1 from QC gates. valid_for_L1=False → label_grade=REJECTED in validate_joint()."

### 8. [MEDIUM] Burn-in Q5 default contradicts pilot ESS measurement
- File: `PM_BRIEF_2026-04-25.md` §1 Q5 line 37 vs `RED_TEAM_ATTACK_2026-04-25.md` §6 lines 71-76
- PM_BRIEF Q5 default = "(B) adaptive s-histogram-plateau, 5 ns crosses 0.05 PROVISIONAL gate."
- RED_TEAM §6 measured ESS/N = 0.052 at 5 ns burn-in (knife-edge); per-state ESS may still fail.
- **Fix**: PM_BRIEF Q5 default: "(B) adaptive if plateau-detection SSD converges; fallback to (A) flat 5 ns if plateau SSD < 0.5 units after 200 ps."

### 9. [MEDIUM] run_ids (plural) in meta vs run_id (singular) in CV split
- File: `INTERFACE_DESIGN_2026-04-25.md` §3.2 line 71 vs §5 lines 116-133
- fes_grid.npz meta says "run_ids" (plural) — implies multi-run pool.
- §5 CV split is by `(sequence_id, run_id)` (singular) — one run_id per row.
- Schema-name vs split-rule mismatch invites off-by-one CV grouping errors.
- **Fix**: §3.2 meta dict line 71: rename `run_ids` → `source_run_id` with clarification "single run_id that produced this FES grid (on 10-walker ensemble)."

### 10. [HIGH] state_occupancy reweighting documentation gap in user-facing PR_FAQ
- File: `descriptors.py` lines 126-146 vs `INTERFACE_DESIGN_2026-04-25.md` §6 lines 151-171 vs `PR_FAQ_2026-07-18_v1_ship.md` §1 line 4
- descriptors.py: state_occupancy() raw frame counts (NOT reweighted; explicit note).
- INTERFACE §6 reweight_to_unbiased() = NotImplementedError stub.
- PR_FAQ §1 demo output: "F0_score, pathgate_score, combined_rank" — nowhere says "raw or reweighted?"
- Future risk: developer implements reweight, regenerates joint_features, inflates PathGate scores silently without updating PR_FAQ §3 acceptance criteria.
- **Fix**: PR_FAQ §1 add: "State occupancy in V1 demo uses raw (unreweighted) frame counts per INTERFACE §6. Once Tiwary-Parrinello reweighting is implemented (V2), state-occupancy scores will be recomputed; acceptance criteria §3 do not apply to reweighted values."

---

## Disposition

| # | Severity | Type | W8 patch? | W9 follow-up? |
|---|---|---|---|---|
| 1 | HIGH | Threshold mismatch | YES (in-place) | — |
| 2 | HIGH | Implicit population rule | YES (annotate) | — |
| 3 | MEDIUM | Stale-mask trigger missing | YES (annotate) | — |
| 4 | HIGH | Q2 narrative theater | YES (rephrase) | — |
| 5 | MEDIUM | Cascade hidden | YES (split Q1) | — |
| 6 | HIGH | Unsatisfiable kill-switch precondition | YES (precondition fix) | Pre-register secondary activity source |
| 7 | MEDIUM | Dead-weight booleans | YES (annotate §6) | Decide remove vs keep in W9 |
| 8 | MEDIUM | Knife-edge default | YES (rewrite Q5 default) | — |
| 9 | MEDIUM | Plural vs singular run_id | YES (rename) | — |
| 10 | HIGH | Reweight scope undocumented in PR_FAQ | YES (PR_FAQ §1 add) | — |

All 10 fixable in W8 closeout via rewording. No design churn. Plan: apply patches in this commit, surface findings to PM in TechDoc §6 (Open Questions for PI) so PI can sanity-check.

## Compared to Codex 6-round chain

The Codex chain (R0/R0.5/R1/R2/R4/R5/R7/R8) caught schema bugs (z_path_A2/A unit inversion, GenSLM token/nt mismatch, decision-logic ordering, λ provenance, TARGETS truncation). It MISSED:
- **Cross-document threshold inconsistencies** (finding 1, 4) — Codex audited each doc separately.
- **Silent assumption documentation gaps** (findings 2, 3, 7, 10) — code/schema/narrative trio not fully connected.
- **Cascade visibility issues** (findings 5, 6) — kill-switch preconditions assume PM choices not yet made.
- **Knife-edge defaults** (finding 8) — Codex measured ESS but didn't tie back to PM_BRIEF default phrasing.

These are second-pass-of-second-pass issues — exactly the kind a sub-agent reading cleanly would catch.
