# Convergence Memo v2.0 — Final Recommendation After 4-Way Synthesis

> **Date**: 2026-04-24
> **Author**: Claude (designer) + Codex (independent second opinion via CCB) + Reports 1/3 (prior AI analysis, 2026-04-20)
> **Supersedes**: `MetaD_Cartridge_Feasibility_Memo_2026-04-22.md` v1.2 (v1.2 kept as audit trail; its cartridge-as-center framing is **demoted**)
> **Audience**: Zhenpeng Liu — decision document, not analysis

---

## 0. TL;DR

**The recommended plan is not "build a cartridge." It is not "build an F0 reward." It is:**

> **"A tiered TrpB function-state evaluator. F0 catches obvious failures (D/L selectivity, catalytic-geometry, progression proxies). PATHMSD/PLUMED supplies rare-state/path evidence when F0 is ambiguous or likely false-positive. The cartridge is internal scaffolding for the escalation lane, not the product."**

This is the ONLY framing that survives all four independent reviews (Reports 1/2/3, Claude v1.2, user's own refinement, Codex).

---

## 1. Framing evolution — 4 independent opinions, how they converged

| Source | Date | Recommendation | Fate of MetaD |
|---|---|---|---|
| Reports 1, 2, 3 | 4-20 | **F0 evaluator / false-positive reduction** (Candidate A) | Harsh-eliminate full MetaD cartridge as main innovation |
| Claude v1.2 | 4-22 am | **MetaD Cartridge** as core artifact | MetaD-centric; cartridge was the product |
| User refinement | 4-22 pm | "Mechanism-grounded evaluation layer" | Already sliding from pure cartridge toward evaluator |
| Codex | 4-24 | **F0+PathGate Evaluator** (Plan A) | MetaD downgraded to **escalation lane**, not product |

Codex's synthesis is the one that reconciles everything:

> *"The prior reports killed MetaD as the product. They did not kill MetaD as ground truth / escalation evidence."*

> *"Yu's failure upgrades MetaD from 'background benchmark' to 'strategic evidence source.' It does not make FES the central deliverable."*

---

## 2. Recommended plan: Plan A — F0+PathGate Evaluator

### 2.1 What it is (one paragraph)

A tiered evaluator for TrpB design candidates. **F0 tier**: fast, alignment-independent scores for (a) D/L selectivity docking gap, (b) catalytic-lysine accessibility/orientation, (c) at least one later-stage progression proxy (product placement / reprotonation geometry / Dunathan-ish angle). **PathGate tier**: when F0 output is ambiguous or flags a likely false-positive, escalate the candidate to a PLUMED/PATHMSD evaluation using the WT-calibrated path CV infrastructure. Output: per-candidate reranking with rationale flags. Upstream consumer: Raswanth's GRPO F0 (`fidelity/f0/tier2_docking.py`) and the wet-lab shortlist.

### 2.2 What it is NOT

- NOT a new ML model
- NOT a STAR-MD competitor
- NOT a standalone published "cartridge" artifact
- NOT a new reward algorithm (Raswanth owns the algorithm; you provide the signal)
- NOT a theozyme redesign (Yu's)
- NOT a PLACER reimplementation (Raswanth's track)

### 2.3 Concrete artifact shipped (by week 10)

```
trpb_function_evaluator/
├── f0/
│   ├── dl_selectivity.py          # D/L docking gap (reuses Raswanth's tier2)
│   ├── catalytic_lysine.py        # K82 NZ accessibility + orientation
│   ├── progression_proxy.py       # later-stage geometry proxy (≥1 metric)
│   └── score_aggregate.py         # F0 composite + ambiguity flag
├── pathgate/
│   ├── pathmsd_project.py         # use existing PLUMED + seqaligned path
│   ├── state_mask.py              # O/PC/C classification
│   ├── rare_state_recall.py       # project trajectory → state report
│   └── escalation_policy.py       # when F0 → PathGate, when to give up
├── cartridge/                     # INTERNAL, not the product
│   ├── wt_reference_fes.nc
│   ├── path_pdb/                  # reconciled with Miguel
│   └── state_masks.json
├── tests/
│   └── regression_on_known_variants.py  # Y301K, E104P, WT
├── notebooks/
│   └── false_positive_case_studies.ipynb
└── README.md                      # 写给 Yu / Amin / Raswanth，不是 paper
```

### 2.4 Lab-internal champions

| Piece | Champion | Why |
|---|---|---|
| F0 D/L + catalytic-lysine | Raswanth | F0 is his turf; you augment his `tier2_docking.py` |
| F0 progression proxy | Yu + Raswanth | chemistry judgment from Yu, code from you |
| PathGate infrastructure | Yu | her OpenMM MetaD just failed; she needs PLUMED+PATHMSD now |
| Reranking / false-positive taxonomy | Arvind/Anima | they explicitly asked for reduced false positives |
| Regression on Y301K/E104P/WT | Yu (data) + you (code) | validates against her MMPBSA ranking |

### 2.5 Week-6 success criterion (falsifiable)

Run the evaluator on one real candidate set (Yu's MMPBSA 30-variant Y301K batch is the obvious choice). Output must:
1. Produce ranked D/L selectivity gap for all candidates
2. Flag ≥ 2 candidates as "F0-ambiguous → escalate"
3. Run PathGate on those escalated candidates, return either (a) additional state-occupancy evidence supporting or refuting F0 flag, or (b) explicit "PathGate insufficient, kick to higher fidelity"
4. At least one case where the evaluator output **disagrees with MMPBSA ranking** in a principled way (i.e., flags a high-MMPBSA candidate as dynamically incompetent)

**If week 6 does not produce the 4th result, the evaluator is no better than MMPBSA and should be reframed.**

### 2.6 STAR-MD deflection

STAR-MD handles long-horizon SE(3) diffusion on ATLAS-style globular proteins. This plan evaluates:
- PLP / cofactor compatibility — STAR-MD 不碰
- biased/CV sampling — STAR-MD 不做
- mutant-dynamics differences — STAR-MD frozen OpenFold features 瞎
- reaction states / proton transfer — STAR-MD 不涉及

The axes are orthogonal. ByteDance is not the threat here; Raswanth and Amin are the internal collision risks, both mitigated by the evaluator framing.

### 2.7 Biggest single risk

> "No agreed label contract."

If Raswanth/Yu/Arvind don't agree on what "good D-selective catalytic progression" means, the evaluator becomes descriptor soup — a dashboard nobody uses to make decisions. **Mitigation**: the first deliverable (week 1) is a 1-page label contract proposal, not code. Get it signed off before writing the first scorer.

---

## 3. Supporting plans to run alongside A

### Plan B — Yu Path-CV Rescue Kit

What: PLUMED config generator, PATHMSD templates, sequence-aligned atom mapping, FP-034 guardrails. Delivered to Yu as a Monday-morning handoff.

Why alongside A: Yu's failure is the reason Plan A has a PathGate tier at all. Plan B makes Plan A's escalation lane actually runnable — it is Plan A's enabling infrastructure, not a separate project.

Week-6 success: Yu launches one path-CV MetaD job without manual surgery.

Biggest risk: becomes pure support work. Framing fix: Plan B's deliverable is **packaged inside Plan A's `pathgate/` folder**, so it counts as infrastructure, not as Yu's errand.

### Plan C — Cross-Species Path Alignment / Rare-State Pack

What: The `path_seqaligned/` tool that fixes FP-034 (cross-species PATHMSD MSD 26× inflation), extended to handle variants.

Why alongside A: Without this, Plan A's PathGate is built on the FP-034 bug — garbage. You are already doing this; just package it properly.

Week-6 success: Regression test shows sequence-aligned path is stable across WT + 1 variant, with the naive-alignment baseline visibly broken.

---

## 4. Plans kept in backlog (not this rotation)

### Plan D — STAR-MD Enzyme-Function Reality Check

Adversarial benchmark of Amin's STAR-MD fork on TrpB using the evaluator's scoring. Strong paper material but depends on Amin sharing code/outputs. **Activate only after Plan A ships and Amin's STAR-MD is ready for evaluation**.

### Plan E — MFBO Escalation Policy

Cost-aware decision layer for F0 → F1 → F2. **Too abstract without real F1/F2 labels**. Consider only after Yu's MD + Raswanth's EVB have flowed into a dataset.

---

## 5. The one question to ask Arvind (tie-breaker)

Codex's recommended question, verbatim:

> *"For the next 10 weeks, should my deliverable be judged by improving the TrpB candidate-evaluation/reward funnel, or by producing mechanistic PLUMED/PATHMSD data for Yu's proton-transfer MetaD problem?"*

**If Arvind says "reward funnel"** → execute Plan A as described, Plan B/C as infrastructure.

**If Arvind says "Yu's mechanism"** → drop Plan A's evaluator framing entirely; make Plan B the main product, accept that it's more support-flavored but scientifically clean.

**If Arvind says "both"** → push back: "Which one is the week-6 success criterion?" Do not let him say both without picking a primary.

---

## 6. Top 3 failure modes (from Codex, verbatim, preserve the exact ranking)

1. **"The Cartridge quietly becomes a junk drawer."** Most likely failure. WT/variant FES, state masks, path CVs, rare-state packs, descriptors, scorer API — too many surfaces. Everyone can praise it, nobody has to depend on it. **Countermeasure**: never ship the cartridge as the top-level product. It lives at `trpb_function_evaluator/cartridge/`, nested, internal.

2. **"The evaluator has no agreed truth labels."** F0 can compute scores, but without Raswanth/Yu/Arvind agreed pass/fail/escalate labels, it becomes a dashboard. Dashboards do not reduce false positives by themselves. **Countermeasure**: label contract is week-1 deliverable before any code.

3. **"MetaD evidence stays methodologically unstable."** FP-034 already showed naive alignment inflated MSD 26×. If PATHMSD keeps being re-engineered, MetaD-derived labels may be garbage. **Countermeasure**: use MetaD as escalation evidence only. Do not let week-10 success depend on clean FES production.

---

## 7. Immediate actions (next 3 working days)

### Day 1 (2026-04-24, today)

- [ ] **Draft the 1-page label contract** (`label_contract_v0.md`): for TrpB candidate X, what counts as F0-pass / F0-ambiguous / F0-fail / PathGate-pass / PathGate-fail. Define the 4–5 categories concretely, not abstractly.
- [ ] Write the draft **Arvind tie-breaker message** (save as `message_to_arvind_tiebreaker.md`). Don't send yet — wait until you have the label contract to show alongside.

### Day 2 (2026-04-25)

- [ ] **Ping Yu** with the scripts from `0.4 对 Yu 怎么说` in v1.2 memo. Offer the PLUMED+PATHMSD infrastructure. Frame as "I can give you the path-CV setup you concluded you need — mind if I also help run it on a Y301K candidate as a PathGate proof of concept?"
- [ ] **Do NOT ping Raswanth or Amin yet.** Wait for Yu's buy-in first; her blessing legitimizes the evaluator framing with the ML postdocs.

### Day 3 (2026-04-26)

- [ ] If Yu responded positively: **reply with concrete week-1 artifact plan**: (a) you give her PLUMED template + path_seqaligned for her Y301K system, (b) she runs one MetaD, (c) you project result onto PathGate evaluator stub.
- [ ] **Commit all uncommitted changes** currently in git status (reports/tools, replication/cartridge/, 新任务explore/), branching off `new_idea_explore` to a clean `feature/f0-pathgate-evaluator` branch.
- [ ] Send the **Arvind tie-breaker message** attached to the label contract draft.

### Gate for the rest of the week

- WT FES (Job 44008381 or 10-walker follow-up) must converge AND pass the Osuna 2019 Fig 2a comparison.
- If WT FES is not ready by 2026-05-01, **PathGate tier cannot demo** and Plan A degrades to "F0 only with PathGate as aspirational." That is OK — it still beats the v1.2 cartridge-as-product failure mode.

---

## 8. File housekeeping

| File | Status | Action |
|---|---|---|
| `新任务explore/MetaD_Cartridge_Feasibility_Memo_2026-04-22.md` v1.2 | **Superseded** | Add prominent note at top pointing to this memo |
| `新任务explore/chatgpt_pro_prompt_cartridge_design_2026-04-22.md` | **Obsolete** | Codex already answered. Keep as reference only; do not send |
| `replication/cartridge/API_DESIGN.md` | **Salvageable** | Rename to `trpb_function_evaluator/pathgate/API.md`; API signatures still valid for the PathGate tier |
| `新任务explore/TrpB 锚定的序列条件动力学贡献设计书.md` | **Historical** | 4-20 framework; B2 chemistry descriptors can be lifted into evaluator |
| `新任务explore/真正卡点与可行性判断.md` | **Historical** | Still-valid kill-list for generic dynamics / RNO line |
| `新任务explore/deep-research-report*.md` | **Canonical** | Treat Reports 1/3 as the first authoritative F0-evaluator recommendation; this memo builds on it |

---

## 9. What this memo commits you to

By accepting v2.0 you are saying:

- You are the **evaluator/funnel person**, not the **MetaD cartridge person**.
- MetaD is your unique leverage tool, not your identity.
- Your week-10 success is measured by: "did the TrpB design pipeline's false-positive rate go down because of my evaluator?"
- If that question can't be answered in the affirmative, you reframe, not double down.

---

## 10. What to say to yourself in the mirror

> "STAR-MD made long-horizon dynamics generation cheap. My lab is generating TrpB candidates cheaply. The new bottleneck is not 'can we generate?' — it is 'are we generating the right thing?' My job is to own the layer that answers that question, using MetaD infrastructure as one of several evidence sources, not as the product."

---

## Appendix — Codex's 5 plans (verbatim from 2026-04-24 CCB consultation)

**Plan A — F0+PathGate Enzyme-Function Evaluator** ← recommended
**Plan B — Yu Path-CV Rescue Kit** ← supporting to A
**Plan C — Cross-Species Path Alignment / Rare-State Pack** ← supporting to A (FP-034 fix)
**Plan D — STAR-MD Enzyme-Function Reality Check** ← backlog
**Plan E — MFBO Escalation Policy** ← backlog

Codex rankings:
- Novelty under ByteDance: A > D > C > E > B
- Delivery probability in 10 weeks: B > A > C > E > D
- Pipeline impact: A > E > B > D > C

Recommendation: **Plan A, with B and C as infrastructure inside A's folder**.
