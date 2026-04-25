# RED-TEAM ATTACK — F0+PathGate Evaluator (V1)
> 2026-04-25 | Targets: `STATE_OF_ML_THINKING_2026-04-25.md`, `INTERFACE_DESIGN_2026-04-25.md` | Method: 🔴 华为味 — 蓝军自攻击 + RCA. 自我批判先于发布。

```
┌──── BLUE-TEAM PANEL ─────────────────────────────┐
│ 8 vectors  3 CRIT  4 HIGH  1 MED                 │
│ 4 hidden gates breached   3 kill-switches        │
│ Verdict: SHIP V1 ONLY WITH §8 KILL-SWITCHES WIRED│
└──────────────────────────────────────────────────┘
```

## §0 Executive summary — 3 likeliest failures
1. **D-Trp transfer void** (CRIT, §1). PathGate is L-Trp-only (5DVZ/5DW0; Lambert Fig 1B = L-Trp cycle; GenSLM-230 activity is L-Trp k_cat). If the funnel's target is D-Trp, V1's signal is uncorrelated with truth. Detect: confirm with PI/Yu in week 1.
2. **MMPBSA-as-truth recursion** (CRIT, §3). `Convergence_Memo_v2` §2.5 demands V1 disagree with MMPBSA on ≥1 candidate, but no independent ground truth adjudicates. Detect: Spearman ρ(PathGate, MMPBSA) on Yu's 30-Y301K; |ρ|>0.8 = nothing learned; |ρ|<0.3 = unadjudicable.
3. **Convergence-grade silent miscall** (HIGH, §5). INTERFACE §3.2's `convergence_grade ∈ {PASS,PROVISIONAL,FAIL}` has **no operational thresholds**; PROVISIONAL bleeds into `joint_features.parquet`. Detect: regression test re-injects job 41514529 (walltime crash) and asserts FAIL.

---

## §1 D-Trp mechanism transfer [CRITICAL]
**Fail.** `s,z` along seqaligned PATHMSD encode **L-Trp** COMM closure; no orientation term distinguishes which face of indole approaches K82-PLP-Aex1. PathGate cannot separate L-closer from D-closer.
**Load-bearing.** `Convergence_Memo_v2` §0 + `project_metad_ml_cartridge.md` silent-killer #0. Every PathGate "rescue" is false-positive if the funnel is D-selective.
**Detect.** Pick from Buller/Hilvert lit 2 variants with D/L k_cat ≥3× but Cα RMSD ≤1.5 Å. If `|Δs̄|,|Δz̄|,|ΔF_C| < 1σ` → PathGate D-blind. n=2 falsifies.
**Fix.** Best: re-pitch as "L-Trp catalytic-progression rescore" (cost 0). Acceptable: add Cβ pro-R/pro-S indole-orientation to L0 (~3 days). Nuclear: reactive-PATHMSD with Schiff-base C4'-Cα torsion (Method F, `v1.2 memo`).

---

## §2 GenSLM black-box risks [HIGH]
**Fail.** Beyond INTERFACE §4 BLOCKED: 25M params on 22,800 AAs is small (ESM-2-650M saw ~65M UniRef50). Lambert Fig 2A separates "natural vs generated", **not** "active vs inactive" — no published evidence the embedding encodes AVOI/INACTIVE.
**Load-bearing.** `genslm_embed` is the only sequence→label feature. If uninformative, only PathGate state-occupancy carries signal — and that's tiny-n.
**Detect.** Ridge on Yu's MMPBSA-30 with X = (a) GenSLM-25M-TrpB mean-pool, (b) ESM-2-650M-frozen, (c) ProtBert-BFD. Pre-register ranking. If ESM-2 R² ≥ GenSLM, the codon-level rationale is unsupported.
**Fix.** Best: run the 3-baseline ablation **before** any GenSLM-novelty pitch. Acceptable: concat GenSLM+ESM-2 + attribution. Nuclear: drop GenSLM (loses Anandkumar/Ramanathan alignment).

---

## §3 Activity-proxy fragility [CRITICAL]
**Fail.** Yu's MMPBSA is a calculation. MMPBSA on PLP/Schiff-base with GAFF+ff14SB+TIP3P has documented force-field sensitivity (no FP entry — silent). Hand-binning adds quantization noise. **No published ρ(MMPBSA, TrpB k_cat)** for D-Trp or L-Trp.
**Load-bearing.** `Label_Contract` §7.1 makes MMPBSA the primary proxy; every L2 gate grades against it. If true ρ < 0.5, the evaluator is calibrated on noise.
**Detect.** Demand n ≥ 12 paired (MMPBSA, k_cat) from Yu. At n=12, |ρ| < 0.6 is statistically random. If n=5–8, MMPBSA cannot be proxy — fall back to bins with `EVAL_ONLY`.
**Fix.** Best: anchor V1 success on bin-agreement. Acceptable: triangulate MMPBSA + bins + ≥1 literature k_cat. Nuclear: block V1 until ≥12 measured k_cat.

---

## §4 Pilot extrapolation [HIGH]
**Fail.** L2 needs **10 walkers × 250 ns × {Aex1, Q2}** per variant. Memory: job 45558834 launched 2026-04-09; v1=homogeneous-start fail, v2=LINCS-blowup, v3 pending. Empirical ≈3 attempts per WT-Ain success; Aex1+Q2 not started. ~600+ GPU-hr/variant. With Longleaf caps + FP-031/032, **3+ variants by week 10 is implausible**.
**Load-bearing.** INTERFACE §5 reserves L2/L3 columns assuming arrival ~week 7.
**Detect.** Week-4 audit: graded-PASS WT across Ain/Aex1/Q2. <2 of 3 PASS → freeze L2/L3.
**Fix.** Best: pre-commit week 1 that L2 = WT-Ain only. Acceptable: 1 variant + 1 intermediate. Nuclear: cMD only — lose rare-state claim.

---

## §5 Convergence-grade silent miscall [HIGH]
**Fail.** INTERFACE §3.2 declares `convergence_grade ∈ {PASS,PROVISIONAL,FAIL}` but defines **no thresholds**. PROVISIONAL becomes a back-door; downstream notebooks render it identical to PASS. One corruption shipped → permanent.
**Load-bearing.** `Convergence_Memo_v2` §6 failure mode #2.
**Detect — hard test.**
```python
def test_known_fail_is_graded_fail():
    # job 41514529 hit walltime 46.3/50 ns; lost C basin
    assert grade_convergence(load_run("41514529")) == "FAIL"
def test_basin_reentry_required_for_pass():
    fes = synthetic_unconverged_fes_with_one_C_visit()
    assert grade_convergence(fes) != "PASS"
```
Pre-register thresholds: block-CI half-width on ΔG_PC-O ≤ 0.5 kcal/mol; ESS_min ≥ 0.05·N; ≥3 independent re-entries to deepest basin.
**Fix.** Best: implement `grade_convergence()` + tests before next 10-walker (~1 day). Acceptable: Skeptic sign-off on every PROVISIONAL row. Nuclear: binary PASS/REJECT only.

---

## §6 Reweighting fragility (Tiwary–Parrinello) [CRITICAL]
**Fail.** INTERFACE §6 gates `ESS > 0.05·N`, `max(w)/sum(w) < 0.01`. On the 19.8 ns pilot, the transient `max_s=12.87` at t=6085 ps (commit `7eb6dbb`) likely puts one frame in the weight tail — both gates probably already fail. Function "tags UNCERTAIN, does not raise" — UNCERTAIN-but-realistic rows ship silently.
**Load-bearing.** L2 entirely. ESS is physics+protocol — failing pilot predicts failing 10-walker without protocol change.
**Detect.** Run `reweight_to_unbiased()` **today** on the seq-aligned pilot COLVAR. If ESS/N < 0.02, pre-register v3 must hit ≥0.05 empirically before any L2 row is written.
**Fix.** Best: relax gate to ESS/N ≥ 0.02 with `EVAL_ONLY`; confidence-weighted training. Acceptable: state-level integrals only. Nuclear: OPES raw counts; breaks INTERFACE §2 cadence.

---

## §7 "5 dead framings" gravity well [MED]
**Fail.** STATE §2 lists LBP/TCR/diffusion/GRPO/RNO as dead but **does not diagnose whether F0+PathGate inherits the same modes**. TCR died from "small training set + over-parameterized matching loss + no held-out variants" (`v1.2 memo` §3.4). F0+PathGate has all three.
**Load-bearing.** `Convergence_Memo_v2` §10 success metric needs a held-out set; INTERFACE defines none.
**Detect.** Add `assert_split_independence(train, test, key=("sequence_id",))` to `validate_joint(df)`. INTERFACE §5 names the split unit but doesn't enforce. Pre-register before first model.
**Fix.** Best: leave-one-sequence-out CV from week 1. Acceptable: hold out 1 of Yu's 30. Nuclear: no published numbers until n_seq ≥ 5.

---

## §8 Kill-switches for V1

Three pre-declared outcomes. **Any trip → V1 ships F0-only; PathGate = research-mode.**

1. **D-Trp blindness (§1):** if `|Δs̄|, |Δz̄|, |ΔF_C| < 1σ` on n=2 Buller D-divergent variants → strip D-Trp claims.
2. **MMPBSA recursion (§3):** if Yu's paired (MMPBSA, k_cat) gives |ρ| < 0.5 at n ≥ 12 → success metric pivots to bin-agreement; PathGate = descriptor only.
3. **PathGate–MMPBSA disjointness:** if PathGate-top-3 ∩ MMPBSA-top-3 = ∅ on n=30 **and** §3 trips → V1 = F0-only; no joint reranker.

```
┌──── KILL-SWITCH WIRING ─────────────────────────────┐
│ §1 → PathGate scope = L-Trp only                    │
│ §3 → success metric = bin-agreement                 │
│ §1+§3 → V1 = F0-only; PathGate = research-mode      │
└─────────────────────────────────────────────────────┘
```

> ▎[🔴 华为味] 烧不死的鸟是凤凰。8 vectors、3 kill-switches、4 hidden gates 已识破。V1 不是不能 ship——是带着这页 ship。
