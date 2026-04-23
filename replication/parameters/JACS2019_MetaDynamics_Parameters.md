# JACS 2019 — Complete Computational Parameters (Verified Edition)

> **Source**: ja9b03646_si_001.pdf (Supporting Information)
> **Paper**: Maria-Solano, Iglesias-Fernández & Osuna, JACS 2019, 141, 13049–13056
> **DOI**: 10.1021/jacs.9b03646
> **Last verified**: 2026-04-02 (skeptic audit: 61 PASS, 15 WARN, 3 FAIL→fixed)
>
> **⚠️ 2026-04-23 Miguel Iglesias-Fernández email override**: the original author clarified the MetaD recipe directly; several SI re-reads documented earlier in this file are now superseded. See `replication/metadynamics/miguel_2026-04-23/miguel_email.md` for the authoritative contract, and Section 3 below for the updated live parameters (UNITS=A / kcal·mol⁻¹, ADAPTIVE=DIFF SIGMA=1000 steps, 10 walkers, λ=3.77 Å⁻² per our path density). FP-031/FP-032 in `replication/validations/failure-patterns.md` log the re-interpretation.
>
> **约定**：每个参数标注三列——SI 原值、我们的复刻值、状态。
> 状态含义：✅ = 与 SI 一致 | ⚠️ = 有差异（已记录） | ❓ = SI 未报告

---

## 1. System Preparation

| Item | SI Value | Our Value | Status | SI Page |
|------|----------|-----------|--------|---------|
| Starting structure | PDB 1WDW (open PfTrpS) | 1WDW | ✅ | S2 |
| Complex | αβ heterodimer (1 TrpA + 1 TrpB) | 同 | ✅ | S2 |
| Isolated TrpB | Manually remove TrpA from PDB | 同 | ✅ | S2 |
| PfTrpB⁰ᴮ² mutations | RosettaDesign | 同 | ✅ | S2 |
| Intermediates modeled | Ain, Aex1, A-A, Q₂ | 当前只做 Ain | ✅ (scope) | S2 |

### Cofactor Parameterization

| Item | SI Value | Our Value | Status | SI Page |
|------|----------|-----------|--------|---------|
| Software | antechamber (AMBER16) | antechamber (AMBER 24p3) | ✅ | S2 |
| Force field | GAFF | GAFF | ✅ | S2 |
| Charge method | RESP | RESP | ✅ | S2 |
| QM level | HF/6-31G(d) | HF/6-31G(d) | ✅ | S2 |
| QM software | Gaussian09 | Gaussian 16c02 | ⚠️ G09→G16, 见 FP-013 | S2 |
| Gaussian route | 未报告具体 IOp | `# HF/6-31G(d) SCF=Tight Pop=MK IOp(6/33=2,6/42=6)` | ❓ 无 `IOp(6/50=1)`，见 FP-013 | — |
| antechamber input | 未报告 | `-fi gout`（读 Gaussian log，不用 .gesp）| ❓ 见 FP-014 | — |

### PDB Residue Names (项目验证 2026-03-28)

| PDB | Intermediate | Residue Name | Heavy Atoms | Status |
|-----|-------------|-------------|-------------|--------|
| 5DVZ | Ain | **LLP** (不是 PLP) | 24 per chain | ✅ PDB 验证 |
| 5DW0 | Aex1 | **PLS** (不是 PLP) | 22 per chain | ✅ PDB 验证 |
| 4HPX | A-A | **0JO** | 待核对 | ⚠️ 未验证原子数 |
| — | Q₂ | 无晶体结构 | — | ⚠️ 需建模 |

> **FP-003 教训**：永远不要凭记忆写残基名。必须从实际 PDB 提取。

### Ain/LLP Capped Fragment (RESP 用)

| Item | Value | Status |
|------|-------|--------|
| Capping | ACE-LLP-NME | ✅ 确认必须 (2026-03-31) |
| Total charge | -2 | ✅ Caulkins 2014 NMR 确认 |
| Multiplicity | 1 (closed shell) | ✅ |
| Capped atom count | ~54 | ✅ |

### 我们的实际产出 (Ain/LLP)

| Item | Value | Date |
|------|-------|------|
| Ain_gaff.mol2 | 42 atoms, charge=-2, backbone retyped to ff14SB | 2026-03-31 |
| Ain.frcmod | 无 ATTN warnings | 2026-03-31 |
| K82 sidechain | retyped to ff14SB (C8/HC/HP); NZ stays GAFF (nh) | 2026-03-31 |
| Skeptic result | 6/6 PASS | 2026-03-31 |

---

## 2. Conventional MD Simulations

### Force Field Stack

| Component | SI Value | Our Value | Status | SI Page |
|-----------|----------|-----------|--------|---------|
| Protein FF | ff14SB | ff14SB | ✅ | S2 |
| Cofactor FF | GAFF | GAFF | ✅ | S2 |
| Charge method | RESP @ HF/6-31G(d) | RESP @ HF/6-31G(d) | ✅ | S2 |
| Water model | TIP3P | TIP3P | ✅ | S2 |
| Box type | Cubic | Cubic | ✅ | S2 |
| Box buffer | 10 Å | 10 Å | ✅ | S2 |
| ~Water molecules | ~15,000 | 11,092 | ⚠️ 体系较小（仅 β 亚基 benchmark 时） | S2 |
| Counterions | Na⁺ or Cl⁻ | 4 Na⁺ | ✅ | S2 |
| Electrostatics | PME | PME | ✅ | S3 |
| LJ + elec cutoff | 8 Å | 8 Å | ✅ | S3 |
| MD software | AMBER16 | AMBER 24p3 (pmemd.cuda) | ⚠️ 版本升级，ff14SB 等价 | S3 |

### 我们的 tleap 实际产出

| Item | Value | Date |
|------|-------|------|
| Total atoms | 39,268 | 2026-03-31 |
| Box dimensions | 76.4 × 88.1 × 73.2 Å | 2026-03-31 |
| Net charge | 0 (4 Na⁺ 中和) | 2026-03-31 |

### Minimization (2-stage)

| Parameter | SI Value | Our AMBER .in Value | Status | SI Page |
|-----------|----------|---------------------|--------|---------|
| Stage 1 restraint | 500 kcal·mol⁻¹·Å⁻² | `restraint_wt=500.0` | ✅ | S2 |
| Stage 2 | Unrestrained | `ntr=0` | ✅ | S2 |
| maxcyc | 未报告 | 10000 | ❓ 工程选择 | — |
| ncyc | 未报告 | 5000 | ❓ 工程选择 | — |

### Heating (7 steps, 0→350 K)

| Parameter | SI Value | Our AMBER .in Value | Status | SI Page |
|-----------|----------|---------------------|--------|---------|
| Steps | 7 × 50 ps | 7 × 50 ps (`nstlim=50000, dt=0.001`) | ✅ | S2 |
| Temperature ramp | 0→350 K, 50 K/step | 0→50→100→150→200→250→300→350 | ✅ | S2 |
| Ensemble | NVT | `ntb=1, ntp=0` | ✅ | S2 |
| Timestep | 1 fs | `dt=0.001` | ✅ | S3 |
| Bond constraints | SHAKE | `ntc=2, ntf=2` | ✅ | S2-S3 |
| Thermostat | Langevin | `ntt=3` | ✅ | S3 |
| Langevin gamma | 未报告 | `gamma_ln=1.0` | ❓ 标准默认值 | — |
| Cutoff | 8 Å | `cut=8.0` | ✅ | S3 |
| Restraint mask | "applied to the protein" | `'!@H= & !:WAT & !:Na+'` | ❓ SI 未报告具体 mask | — |

**Restraint Schedule**:

| Step | SI Value (kcal/mol·Å²) | Our Value | Status |
|------|------------------------|-----------|--------|
| heat1 (0→50 K) | 210 | 210.0 | ✅ |
| heat2 (50→100 K) | 165 | 165.0 | ✅ |
| heat3 (100→150 K) | 125 | 125.0 | ✅ |
| heat4 (150→200 K) | 85 | 85.0 | ✅ |
| heat5 (200→250 K) | 45 | 45.0 | ✅ |
| heat6 (250→300 K) | 10 | 10.0 | ✅ |
| heat7 (300→350 K) | **未明确** (SI 只列了 6 个值) | 10.0 | ⚠️ **UNVERIFIED** |

> **⚠️ UNVERIFIED**: SI 列了 6 个 restraint 值 (210, 165, 125, 85, 45, 10) 但有 7 步加热。当前操作选择：heat6 和 heat7 都用 10.0。

### Equilibration (NPT, 2 ns)

| Parameter | SI Value | Our AMBER .in Value | Status | SI Page |
|-----------|----------|---------------------|--------|---------|
| Duration | 2 ns | `nstlim=1000000, dt=0.002` = 2 ns | ✅ | S3 |
| Ensemble | NPT, 1 atm | `ntb=2, ntp=1, pres0=1.0` | ✅ | S3 |
| Temperature | 350 K | `temp0=350.0` | ✅ | S3 |
| Timestep | 2 fs | `dt=0.002` | ✅ | S3 |
| Restraints | None | `ntr=0` | ✅ | S3 |
| Barostat | 未报告 | Berendsen (`barostat=1`) | ❓ 标准选择 | — |
| Pressure relaxation | 未报告 | `taup=2.0` | ❓ 标准默认值 | — |

### Production MD (NVT, 500 ns)

| Parameter | SI Value | Our AMBER .in Value | Status | SI Page |
|-----------|----------|---------------------|--------|---------|
| Duration | 500 ns | `nstlim=250000000, dt=0.002` = 500 ns | ✅ | S3 |
| Ensemble | NVT | `ntb=1, ntp=0` | ✅ | S3 |
| Temperature | 350 K | `temp0=350.0` | ✅ | S3 |
| Timestep | 2 fs | `dt=0.002` | ✅ | S3 |
| Thermostat | 未重复指定 | Langevin (`ntt=3, gamma_ln=1.0`) | ❓ 沿用加热设置 | — |

### 我们的 Production 状态

| Item | Value |
|------|-------|
| Job ID | 40806029 |
| Status | RUNNING (submitted 2026-04-01) |
| Output dir | `/work/.../AnimaLab/replication/runs/pftrps_ain_md/` |

---

## 3. Well-Tempered MetaDynamics with Path CVs

### Path Collective Variables

| Parameter | SI Value | Our Value | Status | SI Page |
|-----------|----------|-----------|--------|---------|
| CV type | s(R) + z(R) | s(R) + z(R) | ✅ | S3 |
| s(R) meaning | Progress along O→C path | 同 | ✅ | S3 |
| z(R) meaning | Deviation from reference path | 同 | ✅ | S3 |
| Open endpoint | PDB 1WDW | 1WDW | ✅ | S3, Fig.S1 |
| Closed endpoint | PDB 3CEP | 3CEP | ✅ | S3, Fig.S1 |
| Path frames | 15 | 15 | ✅ | S3 |
| Atoms | Cα of 97-184 + 282-305 | Cα of 97-184 + 282-305 | ✅ | S3 |
| Interpolation | Linear (Cartesian) | Linear (Cartesian) | ✅ | S3 |
| MSD (total SD, legacy ref) | 80 Å² | 67.826 Å² | ~15% 差异 | S3 |
| **Per-atom MSD (PLUMED)** | ~0.71 Å² (80/112) | **0.6056 Å²** | ✅ 用于计算 λ | S3 |
| **λ (PLUMED, correct)** | — | **3.7979 Å⁻² = 379.77 nm⁻²** | ✅ **FP-022 修复** | — |
| ~~λ (total-SD, broken)~~ | 0.029 Å⁻² | ~~0.0339 Å⁻² = 3.391 nm⁻²~~ | ❌ **DO NOT USE** | — |
| λ formula | 2.3 / MSD_per-atom | 同 | ✅ | S3 |
| RMSD convention | — | **`RMSD ... SQUARED`** (必须) | ✅ **FP-022 修复** | — |

> **⚠️ FP-022 (2026-04-08)**：之前的 λ = 3.391 nm⁻² 是用 "total SD" 约定（所有原子位移平方的总和）算出来的，但 PLUMED 的 `FUNCPATHMSD` 需要 "per-atom MSD" 约定（每原子位移平方的平均）。两种约定相差 N_atoms = 112 倍。
>
> **症状**：用 λ = 3.391 和 plain `RMSD` 输入时，相邻 frame 的 kernel weight 是 exp(-0.26) ≈ 0.77（应该是 exp(-2.3) ≈ 0.10），CV 完全无法区分 frame，所有构象被压缩到 s ≈ 4–12 区间，而不是 1–15。
>
> **修复**：
> 1. `plumed.dat` 每个 RMSD action 加 `TYPE=OPTIMAL SQUARED`
> 2. `FUNCPATHMSD LAMBDA=379.77`（不是 3.391）
> 3. 用 `generate_path_cv.py` 自动生成的 `plumed_path_cv.dat`，不要手动复制 λ
>
> **诊断经过**：`replication/validations/2026-04-08_path_cv_lambda_bug.md`
>
> **相关 FP**：FP-015（calculate_msd 返回 RMSD）、FP-018（Å⁻² → nm⁻² 缺 ×100）、FP-022（total-SD vs per-atom MSD 混淆）三者是同一类错误——物理约定和实现约定不匹配。

### State Definitions

| State | s(R) range | SI Page |
|-------|-----------|---------|
| Open (O) | 1–5 | S4 |
| Partially Closed (PC) | 5–10 | S4 |
| Closed (C) | 10–15 | S4 |

### MetaDynamics Engine

| Parameter | SI Value | Our Value | Status | SI Page |
|-----------|----------|-----------|--------|---------|
| MetaD software | PLUMED 2 | PLUMED 2.9 | ✅ | S3 |
| MD engine | GROMACS 5.1.2 | GROMACS 2026.0 (conda, PLUMED patched) | ⚠️ 版本升级 | S3 |
| MetaD variant | Well-tempered | Well-tempered | ✅ | S3 |

### Well-Tempered MetaDynamics Parameters (Miguel 2026-04-23 contract)

> **Authoritative contract**: `replication/metadynamics/miguel_2026-04-23/miguel_email.md`. All PLUMED `.dat` values below are in `UNITS LENGTH=A ENERGY=kcal/mol` — no kJ/nm conversion. `ADAPTIVE=DIFF SIGMA=1000` is a time window in integrator steps (≈2 ps at dt=2 fs), NOT a Gaussian width.

| Parameter | SI Value | PLUMED .dat Value (Miguel) | Status |
|-----------|----------|----------------------------|--------|
| UNITS | — | `UNITS LENGTH=A ENERGY=kcal/mol` | ✅ Miguel 2026-04-23 |
| Hill height | 0.15 kcal/mol | `HEIGHT=0.15` (kcal/mol) | ✅ |
| Deposition pace | Every 2 ps | `PACE=1000` | ✅ |
| Bias factor | 10 | `BIASFACTOR=10` | ✅ |
| Temperature | 350 K | `TEMP=350` | ✅ |
| Gaussian width scheme | "adaptive Gaussian width" | `ADAPTIVE=DIFF SIGMA=1000` (steps) | ✅ Miguel 2026-04-23 |
| z wall | (not in SI, in Miguel email) | `UPPER_WALLS ARG=p1.zzz AT=2.5 KAPPA=800` (Å, kcal/mol) | ✅ Miguel 2026-04-23 |
| Wholemolecules | (not in SI) | `WHOLEMOLECULES ENTITY0=1-39268` every step | ✅ Miguel 2026-04-23 |
| kT (for sum_hills) | — | `--kt 2.908` (= k_B × 350 K in kJ/mol; or `--kt 0.695` if you re-run `sum_hills` under kcal) | ✅ FP-021 |

> **⚠️ Historical FP-024/FP-025 (2026-04-15)** — under the (incorrect) `ADAPTIVE=GEOM` interpretation we needed `SIGMA_MIN`/`SIGMA_MAX` floors/ceilings to stop σ from collapsing. Under the correct Miguel contract `ADAPTIVE=DIFF` there is no σ-collapse pathology to floor; the old floor/ceiling literature (`SIGMA_MIN=0.3,0.005`, `SIGMA_MAX=1.0,0.05`) does not apply. The entire σ-ladder probe sweep (P1–P5) was a GEOM-specific artifact — see `replication/metadynamics/probe_sweep/DEPRECATED.md` and FP-031.

### Multiple-Walker Protocol (Miguel contract)

| Parameter | SI Value | Our Value | Status | Source |
|-----------|----------|-----------|--------|--------|
| Walkers | 10 replicas | `WALKERS_N=10` in plumed.dat | ✅ | S4 |
| HILLS sharing | Walkers read each other's HILLS | `WALKERS_DIR=HILLS_DIR WALKERS_RSTRIDE=3000` | ✅ | Miguel email |
| Time/walker | 50–100 ns | live (job 45320189, 3-day walltime) | 🟡 | S4 |
| Total/system | 500–1000 ns | — | 🟡 (计划) | S4 |
| Walker starts | 10 snapshots from initial MetaD | SI says seed from initial; Miguel contract launches all walkers from the same equilibrated system (`system_built.gro` + `metad.mdp`), each with independent GROMACS random seeds | ⚠️ deviation vs SI wording | — |

### Convergence Assessment

| Method | SI Value | Our Plan | Status | SI Page |
|--------|----------|----------|--------|---------|
| Criterion | ΔG(O-C) over time plateaus | blockwise FES 重建 | ✅ | S4 |
| Plots | Figures S4, S5 | 待执行 | ✅ (计划) | S4 |

### FES Post-Processing

| Step | SI Value | Our Command | Status |
|------|----------|-------------|--------|
| FES estimation | Sum HILLS from all walkers | `plumed sum_hills --hills HILLS_all --outfile fes.dat --mintozero --kt 0.695` | ✅ |
| Basin labeling | O=1-5, PC=5-10, C=10-15 | 同 | ✅ |

---

## 4. Additional Analyses (当前 benchmark 暂不执行)

### Arg159 Study

| Parameter | Value | SI Page |
|-----------|-------|---------|
| Systems | 5 (R159 IN/OUT × Ain/Ser/Trp) | S4 |
| Replicas | 5 per system | S4 |
| Duration | 800 ns per replica | S4 |

### CAVER Tunnel Analysis

| Parameter | Value | SI Page |
|-----------|-------|---------|
| Software | CAVER 3.0 | S5 |
| Probe radius | 0.9 Å | S5 |
| Weighting | 1 | S5 |
| Clustering threshold | 12.0 | S5 |
| Snapshots | 100 per local minimum | S5 |
| Starting point | 4HPX A-A coordinates | S5 |

### SPM Analysis

| Parameter | Value | SI Page |
|-----------|-------|---------|
| Distance cutoff | 6 Å (Cα neighbors) | S5 |
| Edge weight | d_ij = −log|C_ij| | S5 |
| Reference | Romero-Rivera et al. ACS Catal. 2017, 7, 8524 | S5 |

### H-bond / Aromatic Analysis

| Parameter | Value | SI Page |
|-----------|-------|---------|
| Tool | cpptraj (AmberTools) | S5 |
| Aromatic angle cutoff | 30° | S5 |
| Aromatic distance cutoff | 5 Å | S5 |

---

## 5. Key PDB Structures

| PDB | Role | Residue Name | Intermediate |
|-----|------|-------------|-------------|
| **1WDW** | Starting structure + Path CV open endpoint | — | — |
| **3CEP** | Path CV closed endpoint (StTrpS) | — | — |
| **5DVZ** | Ain parameterization source | **LLP** (24 atoms) | Ain |
| **5DW0** | Aex1 parameterization source | **PLS** (22 atoms) | Aex1 |
| **4HPX** | A-A structural template (StTrpS) | **0JO** | A-A |
| **5IXJ** | Ser/Trp substrate positioning | — | — |
| **5DW3** | Trp product structure | — | — |
| **4HN4** | Closed A-A reference | — | A-A |

---

## 6. Discrepancy Summary

| # | Parameter | SI / Miguel email | Ours | Severity | Resolution |
|---|-----------|-------------------|------|----------|-----------|
| 1 | Lambda (PATHMSD) | Miguel email: `LAMBDA=80 Å⁻²` for HIS denser path | `LAMBDA=3.77 Å⁻²` (= 379.77 nm⁻²) for our 15-frame / 112 Cα path | HIGH | ✅ resolved — Codex λ audit 2026-04-23, Branduardi textbook 2.3 / ⟨MSD⟩; Miguel's 80 not transferable (21× too sharp for our path density). See FP-032. |
| 2 | ADAPTIVE scheme | SI: "adaptive Gaussian width" (ambiguous) | `ADAPTIVE=DIFF SIGMA=1000` (time window, steps) | HIGH | ✅ resolved — Miguel 2026-04-23 email, FP-031 |
| 3 | UNITS | SI reports Å / kcal·mol⁻¹ | `UNITS LENGTH=A ENERGY=kcal/mol` | HIGH | ✅ resolved — Miguel 2026-04-23 email |
| 4 | Heat7 restraint | 未明确 | 10.0 | MEDIUM | 合理默认，待导师确认 |
| 5 | Gaussian version | 09 | 16 | LOW | ff14SB/GAFF 不受影响，IOp 已修正 |
| 6 | AMBER version | 16 | 24p3 | LOW | ff14SB 等价 |
| 7 | GROMACS version | 5.1.2 | 2026.0 | LOW | PLUMED 接口兼容 |
| 7 | Langevin gamma | 未报告 | 1.0 | LOW | 标准默认值 |
| 8 | Barostat | 未报告 | Berendsen | LOW | 仅影响 NPT 平衡阶段 |

---

## 7. Decision Log

| Decision | Choice | Date | Rationale |
|----------|--------|------|-----------|
| MetaD engine | GROMACS + PLUMED2 (不用 AMBER+PLUMED) | 2026-03-27 | 严格复刻原论文 |
| PLP charge | RESP (不用 AM1-BCC) | 2026-03-28 | SI 明确写 RESP (FP-009) |
| Gaussian IOp | 不用 `IOp(6/50=1)` | 2026-03-31 | G16 下会报错 (FP-013) |
| antechamber input | `-fi gout` (不用 `-fi gesp`) | 2026-03-31 | 配合去掉 IOp(6/50=1) (FP-014) |
| Lambda | 用本地值 0.0339 (暂定) | 2026-03-31 | 待导师确认 |
| Heat7 restraint | 10.0 | 2026-03-31 | SI 歧义，operational choice |

---

*Originally extracted: 2026-03-27*
*Verified & expanded: 2026-04-02 (skeptic audit + script cross-check)*
