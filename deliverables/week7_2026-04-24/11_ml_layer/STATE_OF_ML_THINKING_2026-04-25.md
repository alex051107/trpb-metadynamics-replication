# State of ML-Layer Thinking (TrpB MetaD project) — 2026-04-25

## 1. Current ambition
The ML layer is a **TrpB candidate-evaluator that consumes MetaD output and reranks generator output**, not a new dynamics model. Per `Convergence_Memo_v2_2026-04-24.md` §0–§2, framing is **F0+PathGate Evaluator**: F0 = fast geometry/docking scores, PathGate = MetaD state evidence when F0 is ambiguous. MVP: descriptor extraction + small supervised readiness scorer (`FEL_to_ML_conversion_design_2026-04-24.md` Pattern 5). Stretch: FES-scalar → activity regression for PLP enzymes (same doc §7 Option A) — flagged as real novelty but blocked on ≥3 variant FES.

## 2. What's decided (not being re-litigated)
- **Cartridge ≠ product; cartridge = internal scaffolding** under `trpb_function_evaluator/pathgate/` (`Convergence_Memo_v2` §0, §2.3, §8; supersedes `MetaD_Cartridge_Feasibility_Memo_2026-04-22.md` v1.2).
- **Five generic-ML framings are dead/weakened**: LBP, TCR, generic energy-guided diffusion, GRPO catalysis-reward, RNO sequence-conditioned operator (`MetaD_Cartridge_Feasibility_Memo` §1.5; `真正卡点与可行性判断.md`).
- **MetaD = escalation evidence, not headline** (`Convergence_Memo_v2` §1, Codex synthesis quote).
- **Label hierarchy is L0 descriptors / L1 diagnostic pseudo-labels / L2 thermodynamic / L3 generator target** with hard gates between L1 and L2 (`MetaD_to_ML_Label_Contract_2026-04-25.md` §2).
- **No L2/L3 labels are usable today**: single-walker pilot supports descriptors only (`Label_Contract` §0; project memory FP-034).

## 3. What's open / blocked
- **Variant FES count** — Option A needs ≥3 variants; only WT pilot exists (`FEL_to_ML_conversion_design` §7.4; `genslm230_vs_ndtrpb_manifest.yaml` blockers).
- **Yu's MMPBSA table** — 30-candidate ranking unconfirmed shareable (`FEL_to_ML_conversion_design` §8 Q1).
- **Activity proxy choice** — MMPBSA rank vs experimental k_cat vs Yu's binned ranking (`Label_Contract` §7.1).
- **Conformational vs reactive path-CV scope** — current path is O/PC/C only; D-Trp reprotonation is the silent killer (project memory `project_metad_ml_cartridge.md`).
- **Arvind tie-breaker unanswered** — "reward funnel vs Yu mechanism" (`Convergence_Memo_v2` §5).

## 4. GenSLM interaction surface
GenSLM exposes **DNA/codon-level autoregressive sampling and learned embeddings**, not a dynamics interface. Per `GenSLM_ReadingNotes.md`: Zvyagin 2023 "extract embeddings from the fine-tuned model, cluster in latent space"; Lambert 2026 "Autoregressive sampling starting from ATG codon" producing 60,000 nucleotide sequences filtered by length / pLDDT / identity. The project has the **GenSLM-230 + NdTrpB sequences** (`genslm230_vs_ndtrpb_manifest.yaml`, structures still "pending lab asset"). No token logits or hidden states are in hand. All ML-layer docs implicitly assume **sequences in, rerank scores out**, not GenSLM internals.

## 5. Next concrete decision
**Pick the activity proxy** (Yu's MMPBSA rank vs experimental k_cat-when-available vs hand-scored ranking) — without it, no L2/L3 supervised target can be written and the whole label contract stalls.
