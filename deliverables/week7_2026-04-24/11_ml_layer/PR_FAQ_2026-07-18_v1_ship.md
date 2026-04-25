# PfTrpB Path-Gate Evaluator V1 — shipped 2026-07-18 (HYPOTHETICAL Working-Backwards memo, written 2026-04-25)

## §1 Press Release

Yu Chen's group can now rerank any TrpB candidate FASTA against a converged WT path-CV reference in under one wall-clock day on a single workstation. Yu installs `pip install trpb-function-evaluator` (sources at `trpb_function_evaluator/` per `Convergence_Memo_v2_2026-04-24.md` §2.3) and runs `evaluator score-fasta GenSLM230_top30.fasta --against cartridge/WT_PfTrpB_FES_v1.npz --intermediate Ain`. Output is a CSV with columns `sequence_id, F0_score, pathgate_score, combined_rank, confidence_band, escalation_flag, ess_min, block_ci_max_kcalmol`. Yu's lab-meeting screenshot shows the top three rows are GenSLM-230 candidates whose F0 was middling but whose PathGate flagged a stable PC-basin occupancy that her MMPBSA pipeline missed. Yu's handoff quote: "It runs without me babysitting it, and the confidence band stops me from over-trusting any single number — that is the part I needed."

## §2 FAQ

**Q1. Why trust pathgate when MetaD is not fully converged?** Every row carries `convergence_grade ∈ {PASS, PROVISIONAL, FAIL}` (`INTERFACE_DESIGN_2026-04-25.md` §3.2) and a `label_grade` (`MetaD_to_ML_Label_Contract_2026-04-25.md` §8). Non-PASS rows render grey and are excluded from `combined_rank` — censored, not silently inflated.

**Q2. How does this compare to MMPBSA rerank?** PathGate runs *after* MMPBSA. The acceptance bar (§3) requires PathGate's top-3 to contain ≥1 of Yu's MMPBSA top-3, AND flag ≥1 high-MMPBSA candidate as dynamically incompetent — agreement plus principled disagreement, per `Convergence_Memo_v2` §2.5 bullet 4.

**Q3. GenSLM-230 structure not predicted yet?** F0 needs sequence + AlphaFold; PathGate needs a docked PLP-bound structure. Sequence-only rows ship `pathgate_score = null, escalation_flag = "structure_pending"`. No silent imputation.

**Q4. Aex1 / Q2 intermediates?** `--intermediate` accepts `{Ain, Aex1, Q2}` (`INTERFACE_DESIGN` §3.1), but only `Ain` ships with a calibrated reference in V1. Aex1/Q2 raise `NotImplementedError("variant FES pending")`.

**Q5. Latency to score 30 candidates? When does V2 land?** F0 tier: 4 min. PathGate on ~5 escalated candidates: 8 GPU-h each, parallel across 4× H100, under one calendar day end-to-end. V2 targeted Week 18 (~2026-09-12), gated on §6 unknowns plus ≥3 variant FES.

## §3 Acceptance criteria

- Top-3 PathGate ⊃ ≥1 of Yu's MMPBSA top-3 AND flags ≥1 high-MMPBSA candidate as dynamically incompetent (`Convergence_Memo_v2` §2.5 #4).
- Identical input → byte-identical CSV (seeded, per `INTERFACE_DESIGN` §5 row_id).
- ≤8 GPU-h per escalation × ≤8 escalations = ≤64 GPU-h total for 30 candidates.
- Convergence gate fires on broken HILLS: `tests/regression_on_known_variants.py` injects NaN-corrupted HILLS, evaluator returns `convergence_grade = FAIL`.
- Sequence-aligned PATHMSD (FP-034 fix per `project_metad_ml_cartridge.md`; `Convergence_Memo_v2` §6 #3) exercised on WT + 1 variant in CI; naive-alignment baseline visibly broken.

## §4 What got cut from V1

- **L2/L3 supervised activity target** — `Label_Contract` §2 gates need a predeclared activity proxy; PM has not picked MMPBSA-rank vs k_cat vs binned (`STATE_OF_ML_THINKING_2026-04-25.md` §3 bullet 3). V1 ships descriptors + gated thermodynamic labels only.
- **`genslm_embed` populated** — `INTERFACE_DESIGN` §4 BLOCKED #1 (d_model) and #2 (Fig 2A pooling). Fallback: V1 ships F0 + state pseudo-labels (L0/L1) without GenSLM; column dtype reserved.
- **Aex1 / Q2 references** — variant FES count = 1 (WT-Ain only, `STATE_OF_ML_THINKING` §3).
- **Frame-level random splits** — forbidden by `Label_Contract` §7.1; CV unit is `(sequence_id, walker_id)`.

## §5 What V1 ABSOLUTELY DOES NOT CLAIM

- **No D-Trp stereoselectivity transfer.** Silent killer #0 per `project_metad_ml_cartridge.md`. Path CV is L-Trp-calibrated; D-Trp re-protonation geometry is out of scope.
- **Does not predict catalytic activity.** Predicts agreement with Yu's MMPBSA rank plus principled disagreement when state populations conflict — activity is downstream (`Label_Contract` §7.5 #6).
- **Does not generalize beyond PfTrpB-Ain.** Variant FES count = 1 (`STATE_OF_ML_THINKING` §3); no NdTrpB / Aex1 / Q2 shipped.
- **Does not replace MMPBSA or wet-lab assays.** Escalation layer for false-positive reduction (`Convergence_Memo_v2` §2.1).
- **No MetaD trajectory is ground truth.** Single-walker pilot stays diagnostic (`Label_Contract` §0); only PASS rows feed `combined_rank`.

## §6 Top-of-mind unknowns going into V2

- **`INTERFACE_DESIGN` §7 Q9 (CV split unit)** — if PM allows (B) walker-within-sequence, V2 can train an L2 regressor; if (A), V2 stays ranking-only until ≥3 variant FES exist.
- **§7 Q5 (genslm_embed placeholder)** — V1 used null placeholder; V2 hot-swaps `attach_genslm_embeddings` once `d_model` and pooling rule close (§4 BLOCKED #1, #2).
- **§7 Q7 (reweighting estimator)** — Tiwary-Parrinello c(t) vs Branduardi binless vs iterative WHAM decides whether V2 can pool WT + Y301K block-CIs into a joint label.
