# Week 8 Group Meeting TechDoc — 10-Walker Production + ML Layer Status

**Date**: 2026-05-01 group meeting target
**Author**: Zhenpeng Liu (alex051107)
**Branch**: path-piecewise-pilot
**Status as of 2026-04-25 16:18 EDT**: A2 PASS, A3 production launched (in progress)

> Bilingual: 中文写解释和 motivation；English for technical terms / file paths / commands. Per memory `feedback_language.md`.

---

## 0. TL;DR (30 seconds for PI)

1. **v2 LINCS exit-139 bug FIXED**：v3 design (EM + NVT pre-equilibration before MetaD) validated with 10/10 walkers PASS in smoke test (45783311). Root cause closed.
2. **10-walker SI-literal production LAUNCHED** as SLURM 45784112: 10 walkers × 50 ns × shared HILLS (Multiple-Walkers MetaD per Maria-Solano JACS 2019 §S3-S4). 3-stage staging (EM → 100 ps NVT → 50 ns MetaD).
3. **3 个 SI-faithfulness drift 修好了**（Codex 5 轮 audit chain）：λ=80→100.79（Branduardi 真值），TARGETS [1..10] → [1..13.9] full-path coverage，production materializer 改用 Initial MetaD COLVAR 抽 CV-diverse seeds（不再用 cMD 等距）。
4. **Two MetaD-unique descriptor figures rendered today** for "ML 转化 demo" topic: state occupancy + ⟨z_RMSD⟩|state + σ_s(t); SI Fig S4/S5-style ΔΔG-vs-time methodology demo.
5. **Production FES 2D figure** to be rendered tonight (~19:00-20:00 EDT, when first 10 ns/walker accumulates).

---

## 1. Topic 1 — Initial Run (latest, post-FP-034 path realignment) + Unit Audit Wrap

**Deck main figure**: `reports/figures/initial_pilot_latest_fes.png` (Codex render via `beautiful-data-viz` skill, frozen Longleaf snapshot 2026-04-25 17:26 EDT)

Pilot 45699102 (single walker, FALLBACK contract HEIGHT=0.3 kcal/mol, BIASFACTOR=15, T=350 K) — **latest 24.03 ns / max_s≈14.05 / 12,015 deposited Gaussians**. Axis units: y=z_RMSD (Å), x=s (dimensionless), color=ΔG (kcal/mol).

### Path realignment evidence (before vs after FP-034)

| | Before FP-034 (naive resid match) | After FP-034 (NW-aligned, this run) |
|---|---|---|
| 16 ns max_s reached | < 1.9 (stuck at O endpoint) | s=14.05 ≈ full Open→Closed path |
| Identity (1WDW vs 3CEP, 112 res) | 6.2 % | 59.0 % (9.5×) |
| ⟨MSD_adj⟩ on path | inflated 26× | self-consistent Branduardi λ=100.79 Å⁻¹ |
| 24 ns explore | (would still be stuck) | s ∈ [1, 14.05], C-region count = 12,179 frames |

**Path realignment is the single largest delta this campaign.** The FES contour above shows clear O / PC / C basins on a fully-explored path — none of this exists on the pre-FP-034 baseline.

### Why this is NOT the SI Fig S2/S3 result yet

SI Fig S2/S3 = **10-walker × 50 ns × shared HILLS** (≈500 ns aggregate sampling, PRIMARY contract HEIGHT=0.15, BIASFACTOR=10). What we're showing is the **upstream Initial pilot**: single walker, FALLBACK contract, 24 ns. This is the *seed-discovery stage* per Codex R0.5 SI re-read:

> "After an initial metadynamics run, we extracted ten snapshots ... Then, multiple-walkers metadynamics simulations with 10 replicas were computed."

The 10-walker production (45784112) is running now and will produce the SI-comparable FES once 10 ns/walker accumulates (ETA 2026-04-26 ~6 AM EDT, watcher armed). At that point the deck main figure swaps from this single-walker 24 ns to 10-walker production aggregate.

UNIT_AUDIT.md verdict (Codex CCB 20260424-234500): PASS — λ=100.79 Å⁻¹ Branduardi self-computed, MSD↔RMSD axis-unit conventions confirmed across all artifacts, including this latest render.

---

## 2. Topic 2 — 10-Walker Production 推进

### 2.1 v1 + v2 失败回顾（背景）

- **v1** (45558834, 2026-04-23): scancelled after 1h28m — homogeneous start (all 10 walkers seeded from same equilibrated frame, all stuck at s≈1).
- **v2** (45570699, 2026-04-24): all 10 walkers crashed within minutes, exit code 139, LINCS WARNING on atoms 4463-4465. Root cause documented in `deliverables/week7_2026-04-24/06_v2_10walker_crashed/codex_root_cause.md`: production launched directly from coordinate-only `start.gro` files (`continuation = no, gen_vel = yes` but PLUMED on simultaneously with un-thermalized frames → bond-stress LINCS overflow).

### 2.2 v3 design (validated 2026-04-25 by smoke 45783311)

3-stage flow per walker:
```
start.gro → EM (1000 steps) → em.gro
em.gro    → NVT (100 ps, PLUMED off, gen_vel=yes) → nvt.gro + nvt.cpt
nvt.gro + nvt.cpt → MetaD (50 ns, PLUMED on, continuation=yes) → metad.xtc + COLVAR
```

PASS gates (smoke 45783311 verified):
- EM Max force < 1000 kJ/mol/nm (range 938-986)
- 0 LINCS warnings, 0 atoms 4463-4465 errors
- HILLS deposited per walker (1 hill / 2 ps, PACE=1000)
- 0 exit 139, all walkers COMPLETED 0:0

### 2.3 SI-literal seed selection (Codex R0.5 SI requirement)

10 walker starting structures = CV-diverse snapshots from Initial MetaD (NOT cMD). Materialized by `materialize_v3_validation.py:select_seeds()` with:
- TARGETS = `numpy.linspace(1.0, max_s_observed, 10)` (covers full path, NOT integer-truncated)
- Tiered z-fallback (try z<1.0, then 1.5, 2.0, 2.45 if uniqueness fails — Codex R4 recommendation for sparse C-region)

Resulting seed set (s_std=3.69, min_s_gap=0.77, all 10 hashes unique):

| walker | target_s | t_pilot (ps) | s | z | z_tier |
|---|---|---|---|---|---|
| 00 | 1.00 | 14073 | 1.44 | 0.22 | 1.0 |
| 01 | 2.43 | 17890 | 3.14 | 0.19 | 1.0 |
| 02 | 3.87 | 14748 | 4.10 | 0.21 | 1.0 |
| 03 | 5.30 | 17766 | 5.42 | 0.19 | 1.0 |
| 04 | 6.73 | 14967 | 6.19 | 0.19 | 1.0 |
| 05 | 8.17 | 19602 | 7.64 | 0.27 | 1.0 |
| 06 | 9.60 | 12972 | 9.02 | 0.34 | 1.0 |
| 07 | 11.04 | 12771 | 10.49 | 0.59 | 1.0 |
| 08 | 12.47 | 10733 | 11.83 | 0.82 | 1.0 |
| 09 | 13.90 | 22460 | 13.29 | 2.01 | 2.45 |

Walker 09 fragility note (Codex R4 flagged): C-region of pilot has very few low-z frames; fallback z=2.0 used. NVT pre-equilibration expected to relax z before MetaD wall takes effect; smoke test confirmed walker 09 EM converged in 759 steps without UPPER_WALLS violation.

### 2.4 Production launch state (45784112, 2026-04-25 16:08 EDT)

- 9 walkers RUNNING on volta-gpu, walker 9 PENDING for resources
- HILLS_DIR/HILLS.0-6 已 deposit 20-27 hills/walker (~50 ps MetaD) ✓
- Multiple-Walkers MetaD shared bias confirmed (one HILLS file per walker, all 10 walkers reading from same WALKERS_DIR=../HILLS_DIR)
- 0 LINCS, 0 crashes, 0 exit 139

### 2.5 Production FES 2D figure (TBD tonight)

Auto-render watcher armed (background poll every 5 min). When `min(HILLS rows) >= 5000` (= 10 ns/walker), trigger:
1. `srun plumed sum_hills --hills HILLS.0,...,HILLS.9 --kt 0.695 --min 0.5,0.0 --max 15.5,2.8 --bin 300,100 --mintozero` on compute node
2. scp `fes_sumhills.dat` to local
3. Render via `plot_production_fes_snapshot.py` → `production_fes_snapshot.{png,pdf}`

**Image to insert here when ready**: `reports/figures/production_fes_snapshot.png`. Caveat label: `convergence_grade=PROVISIONAL` (per Codex R5 §Q3c — drift > 0.5 kcal/mol over last 10 ns means NOT PASS yet; we ship as L0/L1 fingerprint, NOT TRAIN target).

### 2.6 Codex Round 8 verdicts (2026-04-25 post-PM-feedback)

**PM 看到 Codex R7 的 early production figure 后两个问题** → 全 dispatch Codex R8 干净上下文裁决：

#### Q1 — production FES 是 production-only HILLS 还是与 initial 合并?

**Verdict: production-only**, do NOT combine initial pilot HILLS into production FES sum.

SI p.S3-S4 verbatim：
> "The free energy landscape associated with the metadynamics CVs is estimated by summing the Gaussian potentials deposited by all walker replicas as a function of the CVs values."

> "After an initial metadynamics run, we extracted ten snapshots ... Then, multiple-walkers metadynamics simulations with 10 replicas were computed."

SI 描述的 construction 就是 (A) 只用 production HILLS。Initial MetaD 是 seed-discovery 阶段，不是 FEL evidence。我们项目额外约束：initial pilot 用 FALLBACK 合约（HEIGHT=0.3, BIASFACTOR=15），production 用 PRIMARY（0.15, 10）。WT-MetaD 理论要求单 biasfactor，混不可。

→ `plot_production_fes_snapshot.py` 调用 `plumed sum_hills --hills HILLS.0,...,HILLS.9` (production only), no initial-pilot HILLS merging.

#### Q2 — PM seed strategy v2 (window-min-z, no z ceiling) 是否要 scancel 重启?

**Verdict: DO NOT scancel 45784112**.

PM v2 directive: "选择尽可能广的 SR + 每一个 sr 选一个相对 Z 比较小的".

Codex R8 用相同 pilot COLVAR 重新计算了 v1 (tiered) vs v2 (window-min-z, no ceiling)，发现：
- 两套规则在 19.8 ns 本地 pilot 上 **seed 完全相同**：every window already has low-z candidates.
- 本地 19.8 ns: walker_09 picks s=12.346, z_MSD=0.976 (z_RMSD≈0.99 Å).
- Longleaf 22.8 ns（live）: walker_09 picks s=13.29, z_MSD=2.01（pilot under-sampling 高 s 区域，window-min-z 也救不了）.
- 当前 production seeds 实际就是 v2 等价：wide linspace + low-z priority + 沉默退守。
- Live 跑了 0.3 ns/walker 已经覆盖 s∈[1.0, 10.7]，没崩没塌. 不需要重启.

**Caveat per Codex R8**: lowest-z 是 *geometry-stability heuristic*（seed 处 path-distance 小 → off-path/wall stress 小），**不是** equilibrium proof — 仍有可能选到 transient low-z crossing.

#### Q2c — 概念清理 patch

`materialize_v3_validation.py:select_seeds()` 仍按 R8 建议清理：
- `Z_TIERS = (1.0, 1.5, 2.0, 2.45)` 删除.
- 候选 = 全部 in-window，按 `(z, |s-target|, time)` 排.
- `Seed.z_tier_used` → `Seed.selection_rule="window_min_z"`.
- `Seed.candidates_at_strict_z` → `Seed.candidates_in_window`.
- `Z_HARD_CAP = 2.5` 常量 + `assert_seed_suite()` 拒绝 z>=2.5.
- 本地 19.8 ns pilot dry-run 验证：seeds byte-identical to R8 recompute.

---

## 3. Topic 3 — ML 转化（整体思路）

### 3.0 4-tier 渐进式转化框架

把 MetaD 输出按信息层级切 4 层，每一层在 ML 训练 pipeline 里**承担不同的 input role**——这是整套设计的骨架。

```
MetaD 原始输出
  │
  ├─→ L0 描述符层  ──────→ ML 输入特征 (input feature, always available)
  │
  ├─→ L1 状态标签层 ─────→ ML 分类目标 (soft pseudo-label, always available)
  │
  ├─→ L2 热力学层 ──────→ ML 监督回归目标 (regression target, gated on convergence PASS)
  │
  └─→ L3 候选排序层 ─────→ ML 输出 (final scoring, gated on L2 + activity proxy)
```

| 层 | 在 General Run pipeline 里是什么角色 | 需要的 input | 产出 artifact | 现在能不能给 |
|---|---|---|---|---|
| L0 | input feature (任何下游模型的 column) | `COLVAR.0..9` | `(s, z, time, walker, bias)` per frame | ✅ pilot 数据现在就有 |
| L1 | classification pseudo-label | COLVAR + state-mask 阈值 (s≤2 / 4≤s≤6 / s≥10) | `state_pseudo ∈ {O, PC, C, off}` per frame | ✅ pilot 数据现在就有 |
| L2 | supervised regression target (free energy per frame) | `HILLS.0..9` + `plumed sum_hills` + convergence diagnostics (ESS, block-bootstrap CI) | `fes_grid.npz` + `F_kcalmol` per frame | ❌ 等 production convergence PASS |
| L3 | final ranking output | L2 + sequence embedding (GenSLM/ESM-2) + activity proxy (MMPBSA / k_cat / 手分箱) | `(F0_score, pathgate_score, combined_rank)` per sequence | ❌ 等 L2 + PM 选 activity proxy |

**核心思想**：L0/L1 任何时候都能给（描述性，不需要 convergence），所以 V1 ship 至少不空手；L2/L3 是 **gate-controlled** 的——convergence_grade 不 PASS 就不开 gate，整套退化到 F0+L0+L1 research mode（kill-switch 设计）。

### 3.1 Three descriptors that GenSLM (sequence) + MMPBSA (single-frame) cannot produce

[Image: `reports/figures/metad_unique_descriptors.png`]

| Descriptor | Pilot 19.83 ns value | Why unique to MetaD |
|---|---|---|
| **P(O)** state occupancy | 18.67% | Requires biased sampling to populate non-equilibrium regions |
| **P(PC)** | 22.50% | Same |
| **P(C)** | 6.16% | C state is high-energy; only accessible via biased dynamics |
| **⟨z_RMSD⟩|state** | O: 1.04 Å, PC: 1.08 Å, C: 1.28 Å | Per-state geometric stability; needs trajectory, not docking pose |
| **σ_s(t)** | range [0.003, 1.401] | Adaptive bias deposition; proxies sampling difficulty |

**Anti-overclaim caveat**: raw frame counts are NOT Boltzmann-reweighted. Tiwary-Parrinello c(t) reweighting deferred to v3 production PASS (per `INTERFACE_DESIGN_2026-04-25.md` §6 BLOCKED #5).

### 3.2 SI Fig S4/S5-style ΔΔG-vs-time methodology demo

[Image: `reports/figures/si_style_convergence_pilot.png`]

Pilot 19.83 ns single-walker (fallback contract): F_min(O)=0, F_min(PC)=−1.50, F_min(C)=+7.05 kcal/mol.

**Methodology validation only** — pilot uses Miguel FALLBACK (HEIGHT=0.3, BIASFACTOR=15) not SI PRIMARY (0.15, 10). 真正可比 SI 的 ΔΔG-vs-time 图 needs production data (will append tonight from 45784112).

### 3.3 ML interface contract (Codex R0/R0.5/R1/R2/R4 全部 audit 过)

**V1 ship target**: 2026-07-18 (~12 weeks) — `pip install trpb-function-evaluator`

**Demo command**: `evaluator score-fasta GenSLM230.fasta --against WT_PfTrpB_FES_v1.npz`

**Output**: CSV `(sequence_id, F0_score, pathgate_score, combined_rank, confidence_band)` — PathGate column populated only if `convergence_grade.status == PASS`; else tag `EVAL_ONLY`.

**3 kill-switches wired** (per RED_TEAM_ATTACK §8): D-Trp blindness / MMPBSA recursion / PathGate-MMPBSA disjoint. Failure of any → degrade to F0-only research mode.

**5 PM decisions still pending** (PM_BRIEF §1):
1. Activity proxy (MMPBSA / k_cat / hand-bins) — blocks L2/L3 supervised label
2. GenSLM hidden_size populated or null
3. L2 scope (WT-Ain only / WT×{Aex1, Q2} / 3+ variants)
4. Reweight estimator (TP c(t) / WHAM / MBAR)
5. Burn-in policy (flat / adaptive s-histogram-plateau)

---

## 4. SI-Faithfulness Audit Chain (full Codex history)

| Round | CCB ID | Scope | Outcome |
|---|---|---|---|
| R1 | 20260425-123133 | INTERFACE_DESIGN schema | Caught 3 critical bugs (z_path_A2/A unit inversion, GenSLM token/nt mismatch, convergence_grade structure) |
| R2 | 20260425-131225 | PM_BRIEF + PR_FAQ + INTERFACE decision logic | Caught 5 internal contradictions; all fixed inline |
| R0 | 20260425-145238 | Clean-context SI re-read (no prior bundle) | 3 docs-level drifts: λ provenance fork, pilot-as-production overclaim, non-SI labels missing |
| R0.5 | 20260425-150747 | SI literal protocol (10-walker workflow + Fig S4/S5) | Confirmed: 10 walkers from CV-diverse seeds; path NOT rebuilt; convergence diagnostic = ΔΔG-vs-time |
| R4 | 20260425-153216 | A0 patch cross-audit | λ change safe (max \|Δs\|=0.054), TARGETS C-end fragile (tiered z fix), 5 hardening items |
| R5 | 20260425-161301 | Production health + FES rendering + convergence criterion | Per-timepoint commands + sum_hills syntax + PASS thresholds |
| R6 | 20260425-163XXX | Codex deck-quality figure rendering (Round 6 reusable plotter) | `beautiful-data-viz` skill PFC RMSD-axis FES + walker explore + 2-panel comparison |
| R7 | 20260425-164142 | Codex z-axis fix + figure refinements (post-PM critique on z=Å² unit) | `production_fes_early_10walker_rmsd.{png,pdf}` + `walker_explore_progress.{png,pdf}` + 2-panel `comparison_pilot_vs_production_2panel` |
| R8 | 20260425-164510 | SI HILLS construction + PM seed strategy v2 cross-audit | (Q1) production-only HILLS, do NOT mix initial pilot. (Q2) DO NOT scancel 45784112; v2 equivalent to v1 on current pilot. (Q2c) `select_seeds()` clean-up applied. |

All 8 rounds archived in `deliverables/week8_2026-05-01/codex_consults/`.

---

## 5. Files Modified (commit-pending)

**SI-faithfulness patches (Track A0 + E + F)**:
- `replication/metadynamics/miguel_2026-04-23/seqaligned_walkers/plumed_template.dat` (λ=80→100.79, anti-overclaim labels)
- `replication/metadynamics/path_seqaligned/plumed.dat` (λ=80→100.79)
- `replication/metadynamics/miguel_2026-04-23/plumed_single.dat` (DEPRECATED marker)
- `replication/parameters/PARAMETER_PROVENANCE.md` (legacy λ marked SUPERSEDED)
- `replication/parameters/JACS2019_MetaDynamics_Parameters.md` (legacy 379.77/3.77 references SUPERSEDED)
- `deliverables/week7_2026-04-24/10_v3_independent_validation/materialize_v3_validation.py` (TARGETS widening, tiered z, max_s auto-detect)
- `deliverables/week7_2026-04-24/10_v3_independent_validation/VALIDATION_REPORT.md` (post-A0 seed set + walker 09 caveat)
- `replication/metadynamics/miguel_2026-04-23/seqaligned_walkers/materialize_seqaligned_walkers.py` (full rewrite: COLVAR-CV-diverse seeds, NOT cMD-equidistant)

**ML/cartridge layer (Track B)**:
- `replication/cartridge/descriptors.py` (extract_metad_unique_descriptors + state_occupancy + mean_z_per_state + bias_deposit_shape)
- `reports/figures/plot_metad_unique_descriptors.py`
- `reports/figures/plot_si_style_convergence.py`
- `reports/figures/plot_production_fes_snapshot.py`
- `reports/figures/metad_unique_descriptors.{png,pdf}`
- `reports/figures/si_style_convergence_pilot.{png,pdf}`

**Codex transcripts + plan**:
- `deliverables/week8_2026-05-01/codex_consults/codex_round0_si_clean.md`
- `deliverables/week8_2026-05-01/codex_consults/codex_round0p5_si_protocol.md`
- `deliverables/week8_2026-05-01/codex_consults/codex_round4_si_xaudit.md`
- `deliverables/week8_2026-05-01/codex_consults/codex_round5_production_fes.md`
- `deliverables/week8_2026-05-01/10walker_v3_smoke_test/result.md`
- `deliverables/week8_2026-05-01/10walker_v3_smoke_test/sacct_log.txt`

---

## 6. Open Questions for PI (group meeting agenda)

1. PM_BRIEF §1 Q1: activity proxy decision (MMPBSA / k_cat / hand-bins) — needed before 2026-05-01 to unblock L2/L3 supervised labels.
2. v3 production wall-clock budget: 24h might give ~20 ns/walker rather than 50 ns; do we extend wall or accept partial production for May 1 deadline?
3. ML layer V1 ship target 2026-07-18 — after May 1 group meeting decision, lock activity proxy + GenSLM populate decision so V1 has unambiguous label semantics.
