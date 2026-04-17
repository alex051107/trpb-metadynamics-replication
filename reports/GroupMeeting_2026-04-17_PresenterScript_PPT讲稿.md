# GroupMeeting 2026-04-17 — PPT 讲稿 双语对照版

> **用法**: 每段先念中文，括号内英文供 Yu 追问时切换。每 slide 约 90 秒。
> **Meeting**: 1-on-1 with Yu Zhang · 2026-04-17 · ~15 min
> **Deck arc**: FP-024 诊断 → 修复（参数单位完整推导）→ probe → FP-027 wrong turn → 50 ns 续跑 → process
> **注**: CV audit（Slide 8）上周已验证，本次只一句话带过，重点移到参数单位逻辑链。

---

## Slide 1 — Title: TrpB MetaDynamics Week 6 Progress
（约 30 秒）

**中** 好，今天是 Week 6 的组会，主要讲两件事：SIGMA 塌缩的诊断与修复——这里面有一套完整的参数单位逻辑，我会详细说——以及新起的 checkpoint 重启流程。总体进度：50 ns 单 walker 正在 Longleaf 上跑，今天下午 3:32 的数据是 27.68 ns、max s=3.494 — walker 刚刚首次越过 s=3 门槛。

**EN** This is our Week 6 report. Two main topics: diagnosing and fixing the SIGMA collapse — there's a full parameter-unit derivation I want to walk through carefully — and the checkpoint restart protocol (FP-026). Current status: the 50 ns single-walker job is live on Longleaf. As of 3:32 PM today, 27.68 ns completed, max s=3.494 — the walker just crossed s=3 for the first time.

---

## Slide 2 — Recap of 2026-04-09: λ 的单位怎么来的
（约 90 秒）

**中** 先回顾上周定的核心参数 λ，它是整套 path CV 的基础，单位推导值得再讲清楚。PATHMSD 的 s(R) 公式是 Σ i·exp(−λ·MSD_i) 除以 Σ exp(−λ·MSD_i)。λ 出现在 exp 的指数里，MSD_i 是每个参考帧的 per-atom 均方位移。要让 exp 是无量纲的，λ 的单位必须是 MSD 的倒数。MSD 的单位是 nm²，所以 λ 的单位是 nm⁻²。数值来自 SI 的经验公式：λ = 2.3 / MSD_adj。MSD_adj 是我们 15 帧路径相邻帧之间的 per-atom 平均位移，算出来是 0.006056 nm²，所以 λ=2.3/0.006056=379.77 nm⁻²。上周修正之前用的 3.3910 是把 RMSD（Å 单位）错当成 MSD（nm²）算的，差了 112 倍。这个数值上周已经验证正确，今天后面讲到的所有参数都建立在这个 λ 之上。

**EN** Let me re-derive λ cleanly, because it underpins every other parameter. The PATHMSD formula for s(R) is Σ i·exp(−λ·MSD_i) / Σ exp(−λ·MSD_i). λ appears in the exponent alongside MSD_i (per-atom mean squared displacement per reference frame). For the exponent to be dimensionless, λ must have units that are the reciprocal of MSD. MSD is in nm², so λ is in nm⁻². The numerical value comes from the SI empirical formula: λ = 2.3 / MSD_adj, where MSD_adj is the per-atom mean squared displacement between adjacent frames along our 15-frame reference path. We computed MSD_adj = 0.006056 nm², giving λ = 2.3 / 0.006056 = 379.77 nm⁻². The old wrong value (3.3910) came from using RMSD in Å instead of MSD in nm² — a 112× error. This λ is now verified and is the foundation for all subsequent parameter choices.

---

## Slide 3 — Job 42679152: walker stuck in O basin
（约 90 秒）

**中** Job 42679152 的结果是机械上完全健康，物理上 walker 没动。机械上：50 ns 整整跑完，25,000 个 Gaussian 准确沉积，累计 48 kJ/mol bias，HILLS 里 0 个 NaN。物理上死：整个 50 ns 的 s(R) 范围是 [1.00, 1.63]，99%+ 时间驻留在 s<1.1，也就是 O basin 底部。关键签名在 HILLS 第 4 列：sigma_path.sss 塌缩成针尖 — 0.011 到 0.072 s-units，占 path 轴 14 s-units 的 0.07% 到 0.5%。这就是典型的 FP-024 签名。

**EN** Job 42679152 was mechanically perfect but physically dead. Mechanically: full 50 ns completed, exactly 25,000 Gaussians deposited, 48 kJ/mol accumulated bias, zero NaN in HILLS. Physically stuck: s(R) stayed in [1.00, 1.63] for the entire 50 ns, with over 99% of frames at s<1.1 — the bottom of the O basin. The key signature is HILLS column 4: sigma_path.sss collapsed to needle-thin values — 0.011 to 0.072 s-units, which is 0.07–0.5% of the 14-unit path axis. This is the classic FP-024 signature.

---

## Slide 4 — FP-024 root cause: SIGMA is Cartesian nm, not CV units
（约 110 秒）

**中** FP-024 的根本原因：`SIGMA=0.05` 在 `ADAPTIVE=GEOM` 下是笛卡尔 nm 单标量，不是 per-CV 单位。PLUMED 2.9 文档原话：'Sigma is one number that has distance units'。ADAPTIVE=GEOM 在运行时把这个 Cartesian 种子投射到每个 CV 上，再根据 free-energy surface 本地曲率自适应调整。发生在我们系统里的链条：0.05 nm 种子投到 path.sss 得到很窄的初始 σ；没有 SIGMA_MIN 护栏；自适应允许 σ 一路缩到 0.011 s-units；25,000 个针尖 Gaussian 全堆在 s≈1.05；形成又深（48 kJ/mol）又极窄的井；井壁梯度几乎零；walker 感受不到推力，晃荡 50 ns。

**EN** Root cause of FP-024 — the causal chain has five links:

**Link 1 — SI gives no numerical SIGMA.** Osuna 2019 SI p.S3 only says "adaptive Gaussian width scheme" (Branduardi 2012). No number. We fell back to the PLUMED default of 0.05.

**Link 2 — SIGMA=0.05 is a single Cartesian nm scalar.** PLUMED 2.9 METAD docs: "Sigma is one number that has distance units." It lives in 3D Cartesian space (nm), not in CV space.

**Link 3 — ADAPTIVE=GEOM projects this nm seed onto each CV axis.** The projection maps one Cartesian length onto whatever units each CV uses. For path.sss (dimensionless, range 1–15) and path.zzz (nm², range ~0–0.1), the projected per-CV σ values are tiny. Crucially, the adaptive algorithm then continues to shrink σ further based on local free-energy curvature — with no lower bound.

**Link 4 — Without SIGMA_MIN, the per-CV σ collapsed to near zero.** In the O basin the FES is steep (deep well), so the adaptive algorithm saw high curvature and shrank σ_sss from ~0.05 to 0.011 s-units — that is 0.07% of the 14-unit path axis. Every Gaussian became a needle.

**Link 5 — Needle Gaussians produce zero gradient outside the needle.** 25,000 needles piled at s≈1.05 built a 48 kJ/mol well, but the well is so narrow that the gradient outside it is essentially zero. The protein atoms felt no force. The walker oscillated at the bottom for 50 ns with no net displacement.

---

## Slide 5 — Fix: SIGMA_MIN / SIGMA_MAX floors (deployed 2026-04-15)
（约 100 秒）

**中** 修复 2026-04-15 部署。METAD 行改了三处：SIGMA 从 0.05 改到 0.1 nm，种子翻倍；新加 `SIGMA_MIN=0.3,0.005`，这是 per-CV 下限，s 方向最小 0.3 s-units 约是 path 轴 2%，z 方向最小 0.005 nm² 略高于热噪声；新加 `SIGMA_MAX=1.0,0.05` 天花板防过宽。顺手发现 FP-025：之前 tutorial 里 `SIGMA=0.2,0.1 [SI p.S3]` 这个引用是伪造的，我用 Zotero 全文读了 SI p.S1 到 S10，完全没有数值 SIGMA，只有 'adaptive Gaussian width scheme' 这个定性描述。早期写 tutorial 的 AI 凭感觉编了一个数字。记了 FP-025 加 rule 20。

**EN** Fix deployed April 15th. Before listing the changes, here is the full parameter unit map — this is what makes the fix make sense:

| Parameter | Value | Unit type | Why that unit |
|-----------|-------|-----------|---------------|
| LAMBDA | 379.77 | nm⁻² | reciprocal of MSD (nm²) to make exp dimensionless |
| SIGMA | 0.1 | nm (Cartesian scalar) | PLUMED METAD: "one number that has distance units" — lives in 3D space, not CV space |
| SIGMA_MIN[sss] | 0.3 | s-units (dimensionless) | after projection, σ lives in CV-native units; path.sss is dimensionless (index 1–15) |
| SIGMA_MIN[zzz] | 0.005 | nm² | path.zzz = −(1/λ)·ln(…), so z inherits units of 1/λ = nm² |
| SIGMA_MAX[sss] | 1.0 | s-units | same as SIGMA_MIN — per-CV ceiling |
| SIGMA_MAX[zzz] | 0.05 | nm² | same |
| HEIGHT | 0.628 | kJ/mol | SI gives 0.15 kcal/mol × 4.184 = 0.628; GROMACS uses kJ throughout |
| BIASFACTOR | 10 | dimensionless | γ in well-tempered formula; SI direct quote |
| TEMP | 350 | K | thermophilic enzyme; SI direct quote |

The three SIGMA changes fix links 2–4: SIGMA 0.05→0.1 nm (larger seed); SIGMA_MIN=0.3,0.005 (per-CV floor in CV units, not nm — this is the critical distinction); SIGMA_MAX=1.0,0.05 (ceiling).

How SIGMA_MIN values were chosen: 0.3 s-units = ~2% of the 14-unit path axis (literature convention for path CV floor); 0.005 nm² = ~2× observed z thermal noise from the probe COLVAR. Both are "Our-choice" — SI provides no numerical guidance.

Also discovered FP-025: our tutorial had `SIGMA=0.2,0.1 [SI p.S3]` as a direct quote. Full-text search of SI p.S1–S10 found no numerical SIGMA. An earlier AI fabricated the number. Rule 20 added: no numerical SI citation without source-text verification.

---

## Slide 6 — Job 43813633 probe: escape signature at 10 ns
（约 100 秒）

**中** 10 ns probe 的结果表面上仍卡：max s=1.393 还在 O basin。但最后 2 ns 出现逃逸签名。看这个表：[0,2] ns 窗口 s↔z 相关 +0.14，弱热噪声；[4,6] ns 窗口相关 -0.31，walker 在 path 两侧垂直摆动不沿 s 走；[8,10] ns 窗口相关跳到 +0.49，这是经典的 activated-barrier crossing 签名 — walker 穿越 barrier 时会拖着 z 一起走。同一窗口逃逸速度从 0.000086 翻倍到 0.000192 per ps。局部 bias 在 s≈1 处达 55.5 kJ/mol，约 2.2 倍 O→PC 典型能垒。解读：walker 在 10 ns 壁时间截断的一瞬间开始逃逸，但数据太短不能断言。

**EN** The 10 ns probe still looks stuck on the surface — max s=1.393, still inside the O basin. But the last 2 ns show an escape signature. s↔z correlation: [0,2] ns window +0.14 (weak, thermal noise); [4,6] ns window -0.31 (walker oscillating perpendicular to path, not progressing along s); [8,10] ns window jumps to +0.49 — the classic activated-barrier crossing signature, where the walker drags z along as it crosses. Escape velocity in the same window doubled from 0.000086 to 0.000192 s-units/ps. Local bias at s≈1 reached 55.5 kJ/mol, roughly 2.2× the typical O→PC barrier. Interpretation: the walker was beginning to escape exactly when walltime hit. 10 ns is too short to confirm — the 50 ns extension will decide.

---

## Slide 7 — Wrong turn caught by Codex (FP-027)
（约 110 秒）

**中** 今天下午我走了一次错路，讲一下因为它引出了新的系统规则。我读 SI p.S3 原文 '2.3 multiplied by the inverse of MSD ... 80'，把末尾的 80 读成 λ=80 nm⁻²。对比我们的 379.77，推出 '我们 4.75× 过大'，开 worktree 写诊断脚本，烧掉 3 小时。Codex adversarial review 一句话打穿：'you're comparing different quantities, premise unsound'。更打脸的是我自己仓库里的 summary.txt line 23-25 早就写了：'Reported MSD: ~80 Å² / Our total SD: 67.826 Å² (ratio 0.85×)'。summary.txt 已经把 '80' 解释为 total SD Å² 不是 λ，按这读法我们和 SI 差 0.85× 基本匹配。忽略既有注释、重新推断然后浪费 3 小时。记为 FP-027 + rule 21：SI 数值重新诠释前必须读仓库既有注释。

**EN** This afternoon I went down a wrong path. Reading SI p.S3 — "2.3 multiplied by the inverse of MSD ... 80" — I misread the trailing "80" as λ=80 nm⁻². Comparing to our 379.77, I concluded "our λ is 4.75× too large," opened a worktree, and spent 3 hours writing a diagnostic script. Codex adversarial review stopped me in one line: "you're comparing different quantities, premise unsound." More embarrassing: my own repo's summary.txt lines 23–25 already said "Reported MSD: ~80 Å² (interpreted as total SD) / Our total SD: 67.826 Å² (ratio 0.85×)." summary.txt had already resolved the "80" as total SD in Å², not λ — under that reading our value matches SI at 0.85×. I ignored an existing annotation, re-derived the same number independently, and wasted 3 hours. Logged as FP-027 + rule 21: always check repo annotations before re-interpreting any SI numerical value.

---

## Slide 8 — CV status (brief)
（约 20 秒）

**中** Path CV 上周已经验证过，λ、Kabsch 对齐、15 帧端点全部正确，这里不重复。probe 卡住是 kinetic timescale 问题，不是 CV 问题。直接看续跑。

**EN** Path CV was fully validated last week — λ, Kabsch alignment, and the 15-frame endpoints all check out. The probe being stuck is a kinetic timescale issue, not a CV issue. Moving on to the extension job.

---

## Slide 9 — Job 44008381: safe checkpoint restart (running now)
（约 110 秒）

**中** Job 44008381 从 Job 43813633 的 10 ns checkpoint 续跑到 50 ns。协议是两步：第一步 `gmx convert-tpr -extend 40000` 把 tpr 里 nsteps 从 5M 扩到 25M；第二步 `gmx mdrun -cpi metad.cpt -plumed plumed_restart.dat`，其中 `plumed_restart.dat` 第 1 行是 RESTART 指令。这两步每步都对应一个 Codex 抓到的 bug，记为 FP-026。三条硬 assert 验证通过：HILLS 行数增长、没有 bck.*.HILLS、HILLS 首行数据不变。今天下午 3:32 状态：已跑 27.68 ns，max s=3.494，首次越过 s=3 门槛（1.41% 帧 s>3）。5-ns 窗口单调上升：1.18→1.39→1.46→1.81→2.79→3.49。决策闸门：max s≥5 走 Phase 2（10-walker）；3–5 之间等 50 ns 跑完；<3 找我，需要讨论下一步。

**EN** Job 44008381 extends from the 10 ns checkpoint of Job 43813633 to 50 ns total. Protocol: first, `gmx convert-tpr -extend 40000` to expand nsteps from 5M to 25M in the tpr; second, `gmx mdrun -cpi metad.cpt -plumed plumed_restart.dat` where plumed_restart.dat has RESTART as its first line. Each of these two steps had a corresponding silent bug caught by Codex, logged as FP-026. Three hard assertions verified: HILLS line count increasing, no bck.*.HILLS file, HILLS first-line data unchanged. Status as of 3:32 PM today: 27.68 ns completed, max s=3.494, first time crossing s=3 (1.41% of frames with s>3). 5-ns window trend is monotonically increasing: 1.18→1.39→1.46→1.81→2.79→3.49. Decision gates: max s≥5 triggers Phase 2 (10-walker per SI); between 3 and 5 we wait for the full 50 ns; below 3 I'll come back to you — we need to discuss the path forward.

---

## Slide 10 — Process improvements + next steps
（约 100 秒）

**中** 流程改进五项：第一，新建 `PARAMETER_PROVENANCE.md`，每个参数带 source tag 和 verified 栏；第二，failure-patterns.md 更新到 FP-027，共 21 条规则；第三，`project_structures.py` CV audit 硬化成 gate，带退出码；第四，repo 已私有化；第五，3 个 branch 推到远端。下一步：50 ns 完成时读 max s，按闸门决策。如果 Phase 2：从轨迹按你 2026-04-09 的指示用 PyMOL 眼看挑 10 个 snapshot。目标：FES 重构 + 对比 JACS 2019 Fig 2a 在 2026-04-24 前完成。

**EN** Five process improvements this week. One: created `PARAMETER_PROVENANCE.md` — every production parameter now has a source tag and verified column. Two: failure-patterns.md updated through FP-027, 21 rules total. Three: `project_structures.py` CV audit hardened into a real gate with exit codes. Four: repo privatized per your request. Five: three branches pushed to remote. Next steps: read max s when the 50 ns job finishes and apply the decision gate. If Phase 2: extract 10 snapshots from the trajectory using PyMOL visual inspection per your April 9th directive — not strided. Target: FES reconstruction and comparison against JACS 2019 Fig 2a by April 24th.

---

## 附录 — Q&A 急救包 / Q&A Quick Reference

| Yu 的问题 / Yu's question | 中文答案 | English answer |
|--------------------------|---------|----------------|
| "379.77 怎么来的" | 2.3 除以 per-atom MSD_adj 0.006056 nm² | 2.3 divided by per-atom MSD_adj 0.006056 nm² |
| "SIGMA_MIN=0.3 哪来" | path 轴 14 s-units 的 2%，我自己选的 | Our choice: 2% of the 14-unit path axis |
| "HEIGHT=0.628" | SI 0.15 kcal × 4.184 = 0.628 kJ/mol | SI value 0.15 kcal/mol × 4.184 = 0.628 kJ/mol |
| "为什么 10 walkers" | SI 明说 10 replicas，严格复现 | SI explicitly states 10 replicas — strict replication |
| "4HPX 为什么 s=14.91" | Pf A-A 态 COMM 已闭合，跟 St closed 态保守 | PfTrpB A-A state has closed COMM domain, conserved with StTrpS closed state |
| "+0.49 相关是噪声吗" | p<1e-270 显著，但样本只 2 ns，要 50 ns 验 | p<1e-270, statistically significant, but only 2 ns of data — needs 50 ns confirmation |
| "--kt 2.908 为什么" | 0.695 是 kcal，GROMACS 用 kJ，差 4.184×（FP-021）| 0.695 is kcal/mol; GROMACS needs kJ/mol — using wrong unit inflates FES by 4.184× |
| "SI 80 是什么" | summary.txt 解释为 total SD Å²，不是 λ；我们差 0.85× 基本匹配 | summary.txt interprets "80" as total SD in Å², not λ — our value matches at ratio 0.85× |

---

**讲稿结束 / End of script** — 总时长估算 15 分钟
