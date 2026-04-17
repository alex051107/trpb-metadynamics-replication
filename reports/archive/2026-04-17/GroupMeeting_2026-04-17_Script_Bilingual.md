# GroupMeeting 2026-04-17 — Bilingual Speaking Script

**Meeting**: 1-on-1 with Yu Zhang · 2026-04-17 · ~15 min · tech-deep 1:1 format

**Lineage**: mirrors 2026-04-09 script (10 slides, per-slide `### 中文` + `### English`) with NEW `### Yu 可能会问` sub-section per slide anticipating drill questions. Expected-Q&A appendix at end.

**Companion docs**:
- `GroupMeeting_2026-04-17_Outline.md` — 10-slide outline (scan)
- `GroupMeeting_2026-04-17_Parameter_Defense.md` — every-number-has-source table
- `GroupMeeting_2026-04-17_Drill_Prep.md` — sensitivity + honest-broker + code walkthrough (cold-read survival)

---

## Slide 1 — Title

### 中文
这是我 Week 6 的进度汇报。这周的主线是 FP-024 诊断 + 修复、然后 path CV audit。上周我们定下的目标是 Job 42679152（50 ns 单 walker）跑出 FES 对比 JACS 2019 Figure 2a；这周的结果是 Job 42679152 虽然正常跑完但 walker 卡在 O basin，我们诊断到是 FP-024（SIGMA 塌缩），修复后的 10 ns 探针 Job 43813633 也还卡着；今天 Job 44008381 把 10 ns 续跑到 50 ns 判断最终能不能逃出去。

### English
Week 6 progress report. Main thread: diagnosed and fixed **FP-024** (adaptive-σ collapse), then ran an offline path-CV audit. Last week's Job 42679152 completed the 50 ns cleanly but the walker never left O basin, which we traced to FP-024. The SIGMA-floor-fixed probe (Job 43813633) also stayed near O. Right now Job 44008381 is extending that probe to 50 ns to decide whether the last-2-ns escape signature was real.

---

## Slide 2 — Recap of 2026-04-09 state

### 中文
上周讨论之后定下的事情：
1. **λ 从 3.3910 nm⁻² 修正到 379.77 nm⁻²**（FP-022）— 单位惯例从 total-SD 改成 per-atom MSD
2. **FUNCPATHMSD 换回 PATHMSD** — conda-forge 的 PLUMED 2.9.2 libplumedKernel.so 缺 PATHMSD 模块，我们源码编译了 PLUMED
3. **提交了 Job 42679152**（50 ns）等结果

上周会议之后，Job 42679152 在 2026-04-12 按时完成。

### Yu 可能会问
- Q: "λ=379.77 再讲一遍怎么来的？" → A: 公式 `λ = 2.3 / MSD_adj`；MSD_adj 是相邻帧的 per-atom 平均 squared displacement = 0.006056 nm²；所以 `λ = 2.3 / 0.006056 = 379.77 nm⁻²`。SI p.S3 说 "2.3 / MSD_adj = 80" — 他们的 80 是 total SD Å²，跟我们的 per-atom 规约不一样。（详细见 Slide 7）
- Q: "为什么 PATHMSD 上周突然能用了？" → A: 源码编译 PLUMED 2.9.2 修好 libplumedKernel.so（之前 conda 版残缺，FP-020）。现在 plumed driver 验证 path CV self-consistency + "Consistency check completed!" 都 pass。

### English
Last week's action items, updated: (1) λ corrected from 3.3910 to 379.77 nm⁻² (FP-022), (2) switched FUNCPATHMSD back to PATHMSD with source-compiled PLUMED 2.9.2, (3) Job 42679152 (50 ns single walker) submitted. Job completed on schedule 2026-04-12. But the result surprised us — see next slide.

---

## Slide 3 — Job 42679152 result

### 中文
Job 42679152 **机械上完全健康**：
- 50 ns 整整跑完，没崩
- 沉积了 25,000 个 Gaussian（50 ns / 2 ps PACE = 25k 正好）
- 积累了 48 kJ/mol bias
- HILLS 里 0 个 NaN

但**物理上 walker 没动**：
- 整个 50 ns 的 `s(R) ∈ [1.00, 1.63]`
- 99%+ 时间 walker 驻留在 s<1.1（O basin 的底部）

我重新看 HILLS 的第 4 列（`sigma_path.sss`）发现 Gaussian **塌缩成针尖** — 0.011 到 0.072 s-units，占 path 轴 [1, 15]（14 s-units）的 0.07%–0.5%。这就是**典型 FP-024 signature**。

### Yu 可能会问
- Q: "s 范围 [1.00, 1.63] 的精确数值怎么算的？" → A: `python3 -c "import numpy; d=numpy.loadtxt('COLVAR',comments='#'); print(d[:,1].min(), d[:,1].max())"` 直接读 Longleaf COLVAR
- Q: "25000 Gaussian 怎么验的？" → A: `wc -l HILLS` 减去 2 行 header。公式 `50 ns × 500 steps/ns × (1 deposit per 500 steps) = 25,000` 对上
- Q: "48 kJ/mol bias 对应多少 kcal？" → A: 48 / 4.184 ≈ 11.5 kcal/mol。基本不小了，但 walker 还是没动，所以 **bias 大小不是问题，bias 的 localization 是问题**
- Q: "HILLS 第 4 列就是 sigma？" → A: 是 per-CV projected σ（ADAPTIVE=GEOM 下把 Cartesian SIGMA 投射到每个 CV 的结果）。FIELDS 头行明确写 `sigma_path.sss_path.sss`

### English
Job 42679152 was **mechanically clean**: 50 ns completed, 25,000 Gaussians deposited, 48 kJ/mol bias, zero NaN. But **physically dead**: s(R) stayed in [1.00, 1.63] the entire run, walker never left O basin. The smoking gun is HILLS column 4 — `sigma_path.sss` collapsed to 0.011–0.072 s-units, which is 0.07% to 0.5% of the path axis width. That's the classic FP-024 signature.

---

## Slide 4 — FP-024 root cause

### 中文
**根本原因**：`SIGMA=0.05` 在 `ADAPTIVE=GEOM` 下是**笛卡尔 nm 单标量**，不是 CV 单位。

PLUMED 2.9 METAD 官方文档原话（查了好几遍）："Sigma is one number that has distance units"。意思是 SIGMA 是单个 Cartesian 长度（nm），不是 per-CV。

**发生了什么**：
1. 我们写 `SIGMA=0.05`，PLUMED 把它当成 0.05 nm 的 Cartesian 种子
2. `ADAPTIVE=GEOM` 会自动根据 free-energy surface 本地曲率调整各 CV 的 σ
3. **没有 SIGMA_MIN/MAX 护栏**，自动调整可以让某 CV 的 σ 任意塌缩
4. 结果：25,000 个针尖 Gaussian 全堆在 s=1 附近，形成**又深又窄的井** — bias 累到 48 kJ/mol 但 walker 脚下梯度接近 0，力传不到蛋白原子上

**诊断方式**：4 个并行 Explore agent（physics / literature / Longleaf forensics / PLUMED source code）独立验证。

### Yu 可能会问
- Q: "SIGMA=0.05 是上周 SI 里的吗？" → A: **不是**。SI 只写 "adaptive Gaussian width scheme"（引 Branduardi 2012），没给任何数值 SIGMA。0.05 是我们早期抄 tutorial 里抄来的，tutorial 里的 `[SI p.S3]` 引用是伪造的（FP-025，同时发现的）
- Q: "为什么 SIGMA 是 Cartesian 不是 CV 单位？" → A: PLUMED METAD 文档 + 源码里确认。在 ADAPTIVE 模式下 SIGMA 是单个 scalar，单位是 plumed 默认单位（GROMACS 下是 nm）。反投影到每个 CV 得到 per-CV σ 才是 CV 单位
- Q: "你怎么这么肯定是 SIGMA 而不是 LAMBDA？" → A: 因为上周已经修 LAMBDA（FP-022），本次 probe 用的就是修好的 LAMBDA=379.77。走 CV audit（Slide 8）也证明 LAMBDA 对了

### English
Root cause: `SIGMA=0.05` under `ADAPTIVE=GEOM` is a single **Cartesian nm scalar**, not a per-CV unit floor. PLUMED 2.9 METAD docs (quoted verbatim): "Sigma is one number that has distance units." Without `SIGMA_MIN`, adaptive σ can collapse to near-zero on any CV axis. Our Job 42679152 showed Gaussians of 0.011 s-units — effectively needles. 25,000 needles piled at s=1 created a deep-but-gradient-less well: huge bias magnitude, zero force on the protein. Four parallel Explore agents (physics, literature, Longleaf forensics, PLUMED source) independently converged on this diagnosis.

---

## Slide 5 — FP-024 fix (deployed 2026-04-15)

### 中文
新的 METAD 行（Longleaf 上已部署，md5 `aca3f0c4...`）：

```
metad: METAD ARG=path.sss,path.zzz \
       SIGMA=0.1 ADAPTIVE=GEOM \
       SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05 \
       HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
```

改了 3 样：
1. **SIGMA 0.05 → 0.1 nm**（种子翻倍）
2. **新加 `SIGMA_MIN=0.3,0.005`** — per-CV floor，在 CV 单位：s 方向最小 0.3（≈ path 轴 2%），z 方向最小 0.005 nm²（在观测 z 噪声水平）
3. **新加 `SIGMA_MAX=1.0,0.05`** — 天花板，防 Gaussian 过宽失分辨率

同时发现 **FP-025**：之前 tutorial 里写 `SIGMA=0.2,0.1 [SI p.S3]` 这个引用是**伪造的** — SI 根本没提到 0.2,0.1。早期 AI 写 tutorial 时凭感觉编的。

部署后立刻提交 Job 43813633（10 ns probe）测 SIGMA floor 是否生效。

### Yu 可能会问
- Q: "为什么 SIGMA_MIN=0.3 是 0.3？怎么算的？" → A: path 轴 [1, 15] 共 14 s-units，0.3 ≈ 2% 轴。选 2% 是因为：够宽让邻近 reference frame 的 kernel 有重叠（让 walker 能从一帧跨到下一帧感受到 bias），够窄不把 basin 结构洗掉。详细 sensitivity 见 Drill_Prep 6A。**没有 SI formula**，我自己选的
- Q: "SIGMA_MAX=1.0 呢？" → A: 1.0 s-units 约是 path 轴 7%。比典型 basin 略宽但不跨盆；防止 Gaussian 无限膨胀把 FES 特征洗掉
- Q: "FP-025 你怎么发现的？" → A: 我 FP-024 诊断时 grep 仓库所有 SIGMA 相关字段发现 5 个互相冲突的数值。最"可信"的是 tutorial 里带 `[SI p.S3]` 引用的 0.2,0.1，但我用 Zotero MCP 完整读了 SI p.S1-S10，没有任何数值 SIGMA。所以引用是伪造的
- Q: "SIGMA=0.1 会不会还是太小？" → A: 比 0.05 大了一倍，但主要防护来自 SIGMA_MIN floor（0.3 in s）。如果 SIGMA_MIN 生效，SIGMA 初值影响小

### English
Fix deployed 2026-04-15 to Longleaf (md5 `aca3f0c4...`): SIGMA 0.05 → 0.1 nm (geometric seed doubled), + `SIGMA_MIN=0.3,0.005` (per-CV floor, in CV units — 0.3 is ~2% of path axis, 0.005 nm² is above typical z-noise), + `SIGMA_MAX=1.0,0.05` (ceiling). Also logged FP-025: tutorial's `[SI p.S3]` citation for SIGMA=0.2,0.1 was fabricated — SI has no numerical SIGMA anywhere. Probe Job 43813633 (10 ns) submitted same day to validate.

---

## Slide 6 — Job 43813633 probe result

### 中文
10 ns probe 2026-04-16 07:59 完成。表面看仍然卡：
- `max s(R) = 1.393` — 还在 O basin（SI 定义 O = [1, 5]）
- 99%+ 时间驻留 s<1.05

**但是**最后 2 ns 出现了逃逸 signature：

| 窗口 | max s | s↔z 相关 | 含义 |
|------|-------|---------|------|
| t=[0, 2] ns | 1.18 | +0.14 | 弱热噪声 |
| t=[4, 6] ns | 1.18 | **-0.31** | 垂直 path 方向摆动（不沿 s） |
| **t=[8, 10] ns** | **1.39** | **+0.49** | **沿 path 运动，典型活化 barrier 穿越** |

- **逃逸速度翻倍**：0.000086 → 0.000192 per ps（最后 2 ns）
- s↔z 相关从 -0.31（垂直）变 +0.49（同向）是典型 activated-barrier 签名 — 实际穿越时 walker "拖着" 正交方向一起走

**解读**：walker 在 10 ns 壁时间截断的**一瞬间开始逃逸** — 但 10 ns 数据太短，不能断言 50 ns 会不会继续。

### Yu 可能会问
- Q: "+0.49 相关是噪声还是真的？" → A: 相关 p 值 < 1e-270（非常显著）。但**样本量只有 2 ns（= 4000 COLVAR 点）**。我相信是真 signal 因为：(a) 跟 bias 累积轨迹一致（前 8 ns 积 bias，最后 2 ns 终于能挣脱）；(b) 物理解释通（活化 barrier 穿越，s 和 z 运动耦合）。但**单看 10 ns 数据本身不足以盖棺**。50 ns 续跑就是为了验证这个
- Q: "逃逸速度怎么算？" → A: 滑动窗口 d(max_s)/dt，每 2 ns 一个值。具体 Agent C 报告里有
- Q: "+0.49 vs -0.31 的物理含义？" → A: 正相关 = walker 往 s 前进时 z 也在变（沿 path 飞跃）；负相关 = walker 在 path 两侧振荡但不沿 s 动。经典 MetaD literature 说这是 barrier 穿越的指纹
- Q: "SI 里 walker O 占比的参考值是？" → A: 没直接数字，但 Figure S15 展示了 PfTrpB Ain 的 FES 分布，定性上说 O 是"highly favored"。我们的 99% 驻留跟 SI 定性一致

### English
Probe result — mechanical numbers stuck, but last-2-ns signals suggest imminent escape. Max s(R) = 1.393 (still in O, SI defines O=[1,5]). But the last 2 ns shows: (1) s-z Pearson correlation jumped from -0.31 (mid-run, orthogonal) to +0.49 (end, aligned) — the classic activated-barrier crossing signature; (2) escape velocity doubled (0.000086 → 0.000192 per ps). My interpretation: walker was starting to escape at walltime. 10 ns is too short to confirm; hence the 50 ns extension (Slide 9).

---

## Slide 7 — Wrong turn caught by Codex (FP-027)

### 中文
今天下午我走了**一次错路**，Codex 打穿了。

**我的误读**：看 SI p.S3 原文 "The λ parameter was computed as 2.3 multiplied by the inverse of the mean square displacement between successive frames, **80**"。我把末尾的 "80" 读作 **λ=80 nm⁻²**。对比我们的 λ=379.77，推出 "我们 4.75× 过大"，提了 alignment-method 假设，花 3 小时开 worktree 做诊断脚本。

**Codex adversarial review 的反驳**：
> "your new SI-80-vs-379.77 diagnosis is comparing different quantities, so the core premise is not sound"

**仓库自己的答案（我忽略了）**：`replication/metadynamics/path_cv/summary.txt` line 23-25：
```
Reference (JACS 2019 SI):
  Reported MSD: ~80 Å² (interpreted as total SD)
  Our total SD: 67.826 Å² (ratio 0.85x)
```

**summary.txt 把 "80" interpret 为 total SD Å²**（而不是 λ）。按这读法，我们的 total SD = 67.826 Å² 跟 SI 的 80 Å² 差 0.85× — 基本匹配。

我忽略了仓库既有解释、自己重新做了一次推断，然后基于那个错推断浪费 3 小时。

**已记为 FP-027** + 新增**规则 21**："SI 数值重新诠释前必须读本仓库对该数值的既有注释"。

### Yu 可能会问
- Q: "为什么 80 更可能是 total SD 而不是 λ？" → A: 关键是 SI 没给单位。summary.txt 的 interpretation 选 total SD 是因为按 total SD 读我们的 67.826 跟 80 的比值是 0.85×（近乎匹配），合理；按 λ 读差 4.75× 就不合理。所以 summary.txt 作出了一个 Judgment call
- Q: "那 SI 到底是什么意思？" → A: **不确定**。SI 原文语法上也可以读成 λ=80。但**无论哪种读法，CV audit（Slide 8）独立证明了我们 path CV 物理上对** — 4HPX → s=14.91。所以 SI "80" 的歧义不是 blocker
- Q: "你怎么保证下次不再犯？" → A: 4 条结构性修复（完整见 Drill_Prep 6E）：(1) PARAMETER_PROVENANCE.md 强制优先查仓库；(2) 重大诊断方向切换前必跑 Codex adversarial review；(3) 仓库 transcript 作 prior；(4) failure-patterns.md 规则 21 写进硬规则

### English
I went down a wrong path today afternoon; Codex adversarial review caught it. My misread: SI p.S3 "λ = 2.3 × (1/MSD) = 80" — I read the "80" as λ=80 nm⁻². Claimed "we're 4.75× off," started an alignment-method hypothesis, spent 3 hours on a worktree to test it. Codex pushback: "comparing different quantities, premise unsound." Repo evidence I ignored: `summary.txt` line 23-25 already interpreted "80" as total SD Å² (matches our 67.826 at 0.85×). Logged as **FP-027** + new rule 21: "SI numeric re-interpretation must read repo's existing notes first." Systemic fixes detailed in Drill_Prep 6E.

---

## Slide 8 — CV audit (Codex recommendation)

### 中文
Codex 的正向建议：不要直接改 LAMBDA / 重建 path，先做一个**离线 CV audit** — 把已知结构投影到当前 PATHMSD 上，看 s 值合不合理。

脚本：`.worktrees/cv-audit/project_structures.py`（branch-local，hermetic，exit 0/2/3/4 gate）。用 PATHMSD 公式的原生 Python 实现（不依赖 PLUMED 运行时）：
```
s(R) = Σ i · exp(-λ·MSD_i) / Σ exp(-λ·MSD_i)
z(R) = -(1/λ) · log Σ exp(-λ·MSD_i)
```
对每个 walker 坐标 → 112 Cα → Kabsch 对齐到 15 个 reference frames → MSD → s/z。

**结果**：

| PDB | chain | s(R) | z(R) nm² | 物理含义 |
|-----|-------|------|----------|---------|
| 1WDW (O endpoint) | B | **1.09** | -0.00025 | ≈1 ✓（构造时就在 path frame 1） |
| 3CEP (C endpoint) | B | **14.91** | -0.00025 | ≈15 ✓ |
| **4HPX (Pf A-A)** | B | **14.91** | -0.00005 | **跨物种验证**：Pf A-A 态 ≈ St closed 态 |
| 5DW0 (Pf+Ser, Aex1) | A | 1.07 | 0.024 | O-like（SI: O=1-5）✓ |
| 5DVZ (Pf holo) | A | 1.07 | 0.017 | O-like ✓ |
| 5DW3 (Pf+Trp) | A | 部分 | — | CV atom 缺 1 个（informational）|

**核心证据**：**4HPX (PfTrpB A-A 态) 投影到 s=14.91，跟 3CEP (StTrpS closed) 几乎完全重合**。这说明：
1. path CV 能正确识别 closed 构象（跨物种）
2. Pf 自己的 PC/C 态结构跟 St 的 closed 态在 COMM 域上保守
3. **我们的 CV 物理上是对的** — LAMBDA + alignment + endpoints 都对

**结论**：问题不是 CV 出错，是 **walker 的 kinetic timescale 问题**。10 ns / 单 walker 自然不够 cover s=1-15。

### Yu 可能会问
- Q: "frame 1 自己怎么 s=1.09 而不是 1.0？" → A: PATHMSD 公式的 kernel 加权形式（不是 delta function），即使 walker 完全 = frame 1，公式给的还是 `s = (1×1 + 2×exp(-λ·MSD₁₂) + ...) / (1 + exp(-λ·MSD₁₂) + ...) > 1.0`。1.09 是 textbook 正常
- Q: "4HPX 不是 Ain 体系吗，怎么跟 3CEP closed 一样？" → A: COMM 域运动是 domain-level 的（大约 10 Å 的 hinge 闭合），跟 active site 小分子（Ain vs A-A）无关。4HPX 的 A-A 中间体 = COMM 已经闭合 = s 值接近 closed endpoint
- Q: "5DW3 chain A 只有 111/112 是怎么回事？" → A: 残基 285 在 5DW3 chain A 里缺失（可能是 disorder）。我的 audit 把它标为 informational（soft fail），不影响 strict 判定
- Q: "为什么不直接用 PLUMED driver 而是 Python 手撸？" → A: PLUMED driver 需要准备完整 topology + xtc；我只想投影 static PDB，Python 实现更轻。公式跟 PLUMED 源码（我看过 FuncPathMSD.cpp）一致

### English
Codex's forward-looking recommendation: before changing anything else, run an offline CV audit — project known structures onto current PATHMSD and check s values make physical sense. I ran `project_structures.py` (pure Python, replicates PATHMSD math). Key result: **4HPX (PfTrpB in A-A catalytic intermediate) projects to s=14.91**, same as 3CEP (StTrpS closed). This is cross-species validation that the path CV correctly identifies the O→C conformational axis. Also: 1WDW→1.09, 3CEP→14.91, 5DW0→1.07, 5DVZ→1.07 — all within SI-expected ranges. **Path CV is physically correct**. The probe's kinetic stagnation is a time-budget problem, not a CV pathology.

---

## Slide 9 — Job 44008381: safe checkpoint restart (currently running)

### 中文
今天下午提交了 Job 44008381 — 从 Job 43813633 的 10 ns checkpoint 续跑到 50 ns 总时长。

**协议**（两步）：
```bash
# Step 1: extend .tpr 的 nsteps 从 5M 到 25M
gmx convert-tpr -s metad.tpr -extend 40000 -o metad_ext.tpr

# Step 2: mdrun 从 checkpoint 续跑，用带 RESTART 的 plumed 文件
gmx mdrun -s metad_ext.tpr -cpi metad.cpt \
          -deffnm metad -plumed plumed_restart.dat \
          -ntmpi 1 -ntomp 8
```

**关键**：`plumed_restart.dat` 是 `plumed.dat` 加一行 `RESTART`（PLUMED 2.9 文档原话："not all MD codes send PLUMED restart info. If unsure, always put RESTART when restarting"）。如果没有 RESTART，PLUMED 会备份旧 HILLS 然后从零开始 → 丢 10 ns bias history。

**Codex stop-hook 抓了 v1 两个 bug → FP-026**：
1. `gmx mdrun -nsteps 25000000` **不能**绕过 "simulation already complete" — 必须用 `convert-tpr -extend`
2. plumed.dat 没 RESTART 会 clobber HILLS

**Runtime 验证通过**：
- HILLS 行数从 5003 → 5106+（append 生效）
- 没有 `bck.*.HILLS` 产生（没被备份）
- HILLS 首个 data 行不变（前缀连续）

**25 ns checkpoint 决策规则**：
- max s ≥ 5 → **Phase 2**（10-walker production，SI 协议）
- 3 ≤ max s < 5 → 让 50 ns 跑完再看
- max s < 3 → **Phase 3**（4HPX-seeded dual-walker，~1 天搭 system）

ETA：明天早上（~2026-04-18 AM）到 25 ns 决策点。

### Yu 可能会问
- Q: "为什么不直接 `-nsteps` 参数续？" → A: `gmx mdrun -cpi metad.cpt -nsteps 25000000` 会因为 metad.tpr 的 nsteps 还是 5M 先报 "simulation already complete" 退出。必须用 `convert-tpr -extend` 改 .tpr 里的 nsteps。FP-026
- Q: "RESTART 放哪里？METAD 自动检测不行吗？" → A: 放 plumed 文件第 1 行。METAD 有自己的 RESTART=YES/NO/AUTO 每-action 选项，AUTO 理论上能自动检测，但 PLUMED 文档明确说 GROMACS-PLUMED 接口不总是传 restart info。保险做法是手写 RESTART 指令
- Q: "runtime 怎么确认 RESTART 生效？" → A: 3 个 pre/post-flight 硬 assert：(1) plumed.dat 跟 plumed_restart.dat normalized diff 空（只差 RESTART 行）；(2) 跑完没有 bck.*.HILLS；(3) HILLS 首行数据不变。已在 extend_to_50ns.sh 里 exit 11/12/13/14 硬编码
- Q: "25 ns 决策阈值 5 和 3 怎么选的？" → A: SI 定义 O=[1,5], PC=[5,10], C=[10,15]。阈值 5 = 进 PC 区证明能逃；阈值 3 = 已经过了 O basin 的 3σ 边界但还没进 PC。3-5 之间是模糊地带让它继续跑完 50 ns

### English
Job 44008381 submitted this afternoon. Two-step protocol: (1) `gmx convert-tpr -extend 40000` to raise .tpr nsteps from 5M to 25M (without this, `-nsteps` alone doesn't override "simulation complete"); (2) `gmx mdrun -cpi metad.cpt -plumed plumed_restart.dat` where plumed_restart.dat = plumed.dat + `RESTART` directive (required per PLUMED docs). Codex stop-hook caught two bugs in the v1 script (FP-026). Runtime-verified: HILLS grew from 5003 rows, no `bck.*.HILLS`, first data row unchanged. **25 ns decision gate tomorrow morning**: max s ≥ 5 → Phase 2 (10-walker SI protocol); max s < 3 → Phase 3 (4HPX-seeded dual-walker).

---

## Slide 10 — Process improvements + next steps

### 中文
**这周做的流程改进**：
1. **`PARAMETER_PROVENANCE.md`** — 每个 production 参数都有 source tag（SI-quote / SI-derived / PLUMED-default / Our-choice / Legacy-bug），verified 栏，known alternate interpretations 栏。防 FP-027 重现
2. **`failure-patterns.md`** — FP-001..027 + 21 条通用规则。本周新增 FP-024/025/026/027 + 规则 20-21
3. **`project_structures.py`** CV audit 硬化成真 gate — exit 0 pass / 2 missing inputs / 3 invariant fail / 4 crash，`AuditError` 类，malformed input 不 crash
4. **repo 已私有化**（Yu 你让我做的）
5. **3 branch 推到远端**：`fix/fp024-sigma-floor`, `feature/probe-extension-50ns`, `diag/cv-audit`

**下一步**：
1. 2026-04-18 AM → Job 44008381 在 25 ns 查 max s → 选 Phase 2 或 Phase 3
2. **如果 Phase 2**（max s ≥ 5）：从 50 ns 轨迹抽 10 个 snapshots，部署 10-walker 到 `feature/10-walker-metad` branch，总计 50-100 ns/walker = 500-1000 ns
   - **按你（Yu）2026-04-09 的指令**：10 个起点用**眼睛看 PyMOL** 挑结构差异大的，不要每隔 N frame 机械取
   - 我的计划：Python 脚本按 (s, z) bin 找候选 medoids → 导出 PDBs → PyMOL 叠加检查 → 眼睛做最终筛选
3. **如果 Phase 3**（max s < 3）：搭 4HPX-seeded Ain-PLP 系统（大约 1 天），同时从 s≈1 和 s≈15 推 walker 相遇
4. **目标**：FES 重构 + 对比 JACS 2019 Fig 2a 在 **2026-04-24** 前完成
5. **OpenMM 迁移**：你上周说 e-track pipeline 有过期包 + memory 问题，defer（不 blocking）

### Yu 可能会问
- Q: "10 snapshots 具体怎么挑？" → A: 不是纯粹 visual，也不是纯粹 strided。工作流：(a) 脚本按 (s, z) bin 找候选 medoid；(b) 导出候选 PDB；(c) PyMOL 同时打开 10 个看结构差异；(d) 如果太像，回到候选池换一个；(e) 最终 10 个结构上的差异由你（Yu）和我一起确认。要用眼睛，但不是 10 个 frame 都用眼盯挑（效率不够）
- Q: "Phase 3 的 4HPX 系统多久能搭好？" → A: 估 1 天。4HPX 里有 indoline analogue，需要换成 Ain PLP；拓扑要重新 tleap；equilibration 要 ~2 ns。依赖 Longleaf GPU 队列等待
- Q: "OpenMM 真的 defer 吗？你本来不是说 secondary 的吗？" → A: 是 secondary。你上周（L4095,L4185）说 e-track pipeline 包过期、memory 问题。没意义在这个 pipeline 不 ready 时做工程迁移。先把 PLUMED path 跑通
- Q: "PARAMETER_PROVENANCE.md 谁会用？" → A: 主要是我自己下次想改参数时先查。也是 FP-027 的系统性防御 — 改 SI 数值前必须看过 existing interpretation

### English
Process improvements: (1) `PARAMETER_PROVENANCE.md` — every parameter now has source tag + verification; (2) `failure-patterns.md` grew to FP-027 + 21 rules; (3) CV audit script is a real gate (exit 0/2/3/4); (4) repo privatized per your ask; (5) 3 branches pushed. Next steps: tomorrow 25 ns decision → Phase 2 (10-walker) or Phase 3 (4HPX dual-seed). **For 10-walker snapshot picking, I'll follow your 2026-04-09 directive — visual inspection in PyMOL, not strided** (workflow: script narrows candidates by (s,z) clustering, I eyeball final 10 in PyMOL). FES comparison target 2026-04-24. OpenMM deferred (your e-track feedback noted).

---

## Appendix — Expected Q&A

6 questions I'm most likely to be asked but don't obviously belong on any specific slide:

### Q1: "为什么 10 walkers 而不是跑 1 个更长的？"
SI 明确用 10 walkers × 50-100 ns = 500-1000 ns 总时间。单 walker 跑 500 ns 理论可行但 (a) 单 walker 只能从一个 starting basin 出发，cover conformational space 效率低；(b) SI 是严格的 replication 目标，shared HILLS 的 multi-walker 是协议的一部分。

### Q2: "如果 Job 44008381 25 ns 没过 s=3，Phase 3 的 4HPX 系统会有 PLP 参数问题吗？"
有风险。4HPX 带的是 indoline analogue，不是 Ain。需要 (a) 保留 4HPX 的 backbone + COMM 构象；(b) 在 K82 上重新 Schiff base Ain PLP；(c) 重新 RESP + tleap。我们 2026-03-31 已经做过一次 Ain PLP 参数化（charge=-2, FP-015 后 MSD 修好），所以流程熟。但 4HPX vs 5DVZ 的 context 不同，可能需要重新 equilibration。估 1 天 + 2 ns eq。

### Q3: "SI 说 'cover approximately all conformational space available' — 这 all 指什么？"
**你 2026-04-09 L3009 提过这个点**。"all conformational space available" 是指 initial run 跑出来的空间，**不是指 O/PC/C 全覆盖**。所以即使我们的 initial run 只 cover 到 s=1.4，按 SI 字面意思 10 snapshots 就从这 1.4 以内挑。但**这又回到你的另一个 point**：要挑结构差异大的。实际操作：10 个 snapshots 不一定跨 s=1-15，但必须**结构上** diverse。如果实在都挤在 s=1 附近长得都像，那就要换策略（Phase 3）。

### Q4: "为什么 CV audit 里 4HPX 对应的 chain 是 B 不是 A？"
4HPX 是 TrpS heterodimer（TrpA 链 A，TrpB 链 B）。我们 CV 取的是 TrpB 的 COMM 域 + base，所以应该用 chain B。1WDW 也是同样理由用 chain B。这是跟 SI p.S3 + Figure S1 的 consistency。

### Q5: "failure-patterns.md 现在 27 个 FP，会不会太多了？"
27 个 FP 覆盖 4 周工作。**单位/约定 bug 6 个**（FP-015, 018, 021, 022, 024, 027）是主线。**工具兼容 bug 4 个**（FP-020 PLUMED build, FP-023 END line, FP-026 restart, FP-025 伪造引用）。剩下的是早期流程 bug（FP-001..014）。密度不算异常 — MD + PLUMED + 跨 AI 协作的 pipeline 边界处本来就多。重要的是每个 FP 都记了防范措施 + 通用规则。

### Q6: "这周你最确定的结果是什么？最不确定的是什么？"
**最确定**：path CV 物理上对（CV audit 硬证据，4HPX projection）。LAMBDA=379.77 self-consistent（自测 + projection）。FP-024 root cause 正确（4 个 agent + primary source）。

**最不确定**：Job 44008381 在 50 ns 能不能真逃出 O。10 ns 探针的 +0.49 correlation 是逃逸 signature 但样本小（只 2 ns）。明天 25 ns checkpoint 才有答案。如果失败我切 Phase 3（不是继续烧 HPC）。
