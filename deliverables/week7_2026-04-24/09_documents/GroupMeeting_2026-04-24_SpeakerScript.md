# GroupMeeting 2026-04-24 · Page-by-Page 讲稿

> **用途**: 组会现场逐页的口头叙述稿，控制节奏 + 防守 pushback。
> **时长目标**: 28–30 min 讲 + 10–15 min Q&A。
> **配合**: 打开 pptx (`reports/GroupMeeting_2026-04-24.pptx`) + 手边放 `CHEATSHEET.md` 做数字 backup。
> **语言**: 以中文为主, 关键术语保留英文; 念给 Yu Chen。

---

## Slide 1 — 标题页 (30 秒)

**开场一句** (看着 Yu):
> "这周的核心进展是**发现并修复了 path CV 的一个跨物种 residue mapping bug**。修完后, 8 ns 单 walker pilot 已经 sample 到 `s = 1 到 12.87`, 老 path 跑 16 ns 都卡在 `s < 1.9`。但 10-walker production 前两次都 fail, v3 pipeline 已经设计好等您 approve。"

**过渡**: "我按 5 个主题讲, 不超过 30 分钟。"

---

## Slide 2 — 本周 5 个重点 · Roadmap (1 min)

**逐条点出, 不展开** (每条 ~10 秒):

1. **Re-alignment (FP-034)** — "cross-species residue mapping bug, NW 修复 +5 offset"
2. **Miguel author contract** — "Osuna 组一作邮件回复, 一次性终结 3 周的调参 debate"
3. **Current results** — "pilot 8 ns vs baseline 16 ns, FES(s,z) 前后对比图"
4. **10-walker seeding 的故事** — "v1 scancel, v2 全崩, v3 pipeline Codex 验证了"
5. **ML 层未来 + kill-switch** — "外部 audit 收窄到 MNG, 5-1 硬 gate"

**过渡**: "第一部分 Re-alignment 我要多花一点时间, 因为这是本周的 main result。"

---

## Slide 3 — Topic 1 · FP-034 Root Cause (3 min)

**主叙述** (指 slide 左右两个 box):

> "1WDW 是嗜热菌 *P. furiosus* 的 TrpB β 亚基, Open 态。3CEP 是沙门菌 *S. typhimurium* 的 TrpB β, Closed 态。这两个晶体被原文当 path 端点用, 但它们**长度不一样**: 1WDW-B 385 aa, 3CEP-B 393 aa。3CEP 的 N 端多 5 个 residue (signal peptide 处理不同)。"

> "所以 1WDW resid 97 的 **真正同源 residue 是 3CEP resid 102, 不是 97**。但我们的 `generate_path_cv.py` 没做 sequence alignment, 直接按 residue number 配对——就相当于把两个不同蛋白的 backbone 硬叠。"

**数字 hit** (指右下两个表):
- "naive mapping: 112 个 residue identity 只有 6.2%, RMSD 10.89 Å"
- "seq-aligned: identity 59.0% (9.5× 提升), RMSD 2.115 Å (5× 紧)"
- "λ 从 3.80 修到 100.79 Å⁻² —— 比值跟 Miguel 的 80 是 1.26×, 同一 kernel 宽度量级。"

**关键 line** (必须说, pause 1 秒):
> "**这个 bug silent 了 3 周**。代码跑不报错, path.pdb 长得正常, λ = 3.80 也能跑 MetaD。问题只在下游表现为 'walker 卡在 s=1'。"

**防守预案**:
- 如果 Yu 问 "为什么早没发现" → "因为用 `_gaff` 脚本的是 Codex+我, 没人 cross-check alignment identity。FP-034 已经加进 `failure-patterns.md`, 以后所有 future path-builder 脚本头部必须 `assert identity > 50%`。"
- 如果 Yu 问 "NW 怎么做的" → 过渡到 slide 4 (或者说 "下一页就详细讲算法")

**过渡**: "修复算法我下一页讲, 这一页先看一下修复之后的生物学 sanity。"

---

## Slide 4 — Topic 1 · 数值 + Sanity Check (3 min)

**数值表** (指 slide 左侧):
> "这是核心数字的 before/after。9.5× identity 提升, 5× RMSD 紧, 26× MSD 小, λ 26× 大。注意最后一行: 我们的 λ 除以 Miguel 的 80 是 1.26×, 这在 Branduardi 2007 的启发式 tolerance 内 (通常 < 2×)。"

**生物学 sanity 表** (指 slide 右下):
> "这是**独立** sanity check——我们没用这些晶体构造 path, 它们是事后 validation。"

指表逐行:
- "5DW0 chain A 是文献标注的 βPC + L-Ser (Aex1 intermediate)。naive path 上它塌到 s≈1.07 (等同于 Open, 物理荒谬), corrected path 上落在 s=9.46 (path 中段, 合理的 partial closure)。"
- "5DW3 和 5DVZ 是另外两个 βPC 晶体, corrected path 上分别 s=8.51 和 5.37, 都在 mid-path 合理区间。"
- "4HPX 是 Pf 的 A-A 中间体, 接近 Closed, 两种 path 都落在 s≈14.9 —— 说明它本就接近 C 端点, 对 path 修正不敏感。"

**关键 line**:
> "**3 个 βPC 晶体**在 naive path 上**全都塌到 s≈1**, 在 corrected path 上分散在 s=5.4–9.5。这是 path 修复有效的硬证据, 不是我自己 hand-wave。"

**如果被追问 NW 算法细节** (Yu 可能会问):
> "NW 我是用 numpy 手写的——不依赖 BioPython。评分矩阵 match=+2, mismatch=-1, gap=-2, 最简单的 scheme, 因为两条 chain identity > 50% 任何合理评分都会收敛到同一个 alignment。Codex 独立实现 (只给序列, 不看我代码) 跑出 identity 59.0331%, score 286, 跟我 byte-level 一致。"

> "NW 的**真正 value-add 是证明 112 residue 内部没有 indel** —— 如果有 indel, uniform +5 就数学上不合法, 需要逐 residue 重新映射。这一点 offset 检查: `min([mapping[r]-r for r in COMM+BASE]) == max(...)`, 两个都是 5, 所以 uniform 合法。"

**过渡**: "下一页是视觉证据。"

---

## Slide 5 — Topic 1 · 视觉 proof + start.gro s=7 解释 (3 min)

**指 FES(s,z) 图** (嵌入 slide):

> "这就是最重要的一张图。左 panel 是老 path baseline, 16 ns, 81479 frames; 右 panel 是 corrected path pilot, 8 ns, 40193 frames。**两个 panel 唯一的变量是 path.pdb, 其他完全一样 (同 start.gro, 同 Miguel params, 同 single walker)**。"

> "左边密度压在窄窄的 s<2 条带; 右边铺开到 s=1 到 12 整段。time 只用了一半, 空间宽了 6.8 倍。"

**关键 line — start.gro 这个点必须 preempt**:
> "右图那个**红色星星**是 start.gro 的位置, 投到 s=7.09, z=1.68。可能会有人问 '这不就说明 Ain 已经在 PC basin 了吗'。**这是 overclaim, 我不这么读。**"

**解释 soft-min 伪影** (这是 slide 最难讲的一段):
> "start.gro 对 path 上每一个 MODEL 做直接 Kabsch, RMSD 都在 1.3-1.8 Å 之间, **差距只有 0.3-0.5 Å**。也就是说 start.gro 离每一个 MODEL 都差不多近, 没有一个 dominant 的 'nearest MODEL'。"

> "在 Branduardi soft-min 公式下, 当所有 MSD_i 差不多时, 分子变成所有整数 index 的加权平均, 自然集中在 N/2 ≈ 7。这是 **linear-interpolation path 的已知几何性质**, 不是 numerical bug, **也不是生物学陈述**。"

> "z = 1.68 Å² 这一项也佐证: walker 的 off-path deviation 很大 (mean_z = 1.53 贯穿 8 ns), 说明蛋白**不在 path 上**, 投到的 s 只是几何软平均, 不是 basin identification。"

**防守预案**:
- Yu 可能直接说: "那你为啥 start.gro 是这个构象?" → "因为是 500 ns cMD 在 Ain 体系下 equilibrate 的终态, 预期应该在 Open basin (s≈1); 但 linear-interp path 的中点 MODEL 恰好跟 start.gro 几何上都很近, 所以 soft-min 把它算到 s=7。**这是 path CV 的局限, 不是 start.gro 的 biology。**"

**过渡**: "OK, Topic 1 讲完——bug 找到了, fix 对了, 视觉也看见了。下一个 topic 讲这周最重要的外部输入, Miguel 的 email。"

---

## Slide 6 — Topic 2 · Miguel Author Parameter Contract (3 min)

**开场直给契约** (指 slide 里代码块):

> "Miguel Maria-Solano 是原文一作。我 2026-04-22 写信问他 MetaD 参数细节, 他 4-23 回复了一个 verbatim 的 PLUMED 参数块。我把关键修改列在这里。"

**4 个关键点, 每个 30 秒**:

1. **ADAPTIVE = DIFF, not GEOM** — "PLUMED doc 明确说 GEOM 在 path 两端 ill-defined, 因为 chord direction 不稳; DIFF 用连续步差分直接估 σ, 端点稳。我们之前用 GEOM 是误读了 FP-031。"

2. **UNITS = A / kcal, not nm / kJ** — "Miguel SIGMA 字面值 (0.1, 0.3, 0.005) 是 Å/kcal; 我们用 GROMACS native nm/kJ 跑, 等效 σ 差一个单位转换因子。这是 FP-032。"

3. **Primary set = HEIGHT=0.15 / BF=10 / WALKERS_N=10** — "不是 0.3 / 15。后者是 Miguel 邮件里标的 'aggressive fallback', 只在 primary 不收敛时才用。"

4. **λ 按 path 自洽, 不普适** — "Miguel 的 80 是在**他的 path** 上自洽, 不是 universal constant。Branduardi 启发式 λ ≈ 2.3/⟨MSD⟩ 本身就依赖 path 几何。我们的 corrected path 算出 100.79, 比值 1.26×, 同一量级。"

**关键 line**:
> "这个 email 一次性终结了我们之前 3 周在 plumed.dat 上的调参 debate——probe_sweep 2×2, wall4 扫描, piecewise-λ 设计都停了, 全部 align 到这个契约。"

**防守预案**:
- 如果 Yu 问 "你怎么证明邮件是真的 Miguel 发的" → "邮件保存在 `chatgpt_pro_consult_45558834/miguel_email.md`, header 完整, 学术邮箱发的。"
- 如果 Yu 问 "为什么不直接用 λ=80" → "因为 Miguel 自己在邮件里说 λ 要 per-path 重新算。我们的 100.79 和他的 80 是 1.26× 比值, 同 regime, 这才是一致的读法。"

**过渡**: "有了对的 path + 对的参数, pilot run 结果我下一页讲。"

---

## Slide 7 — Topic 3 · s(t) Trace (2 min)

**指 s(t) 图 (slide 左图)**:

> "这张是 s(t) 时间序列。蓝线是 baseline 45324928 (naive path, 16 ns, 卡在 s<1.9), 橙线是 pilot 45515869 (corrected path, 8 ns, sample 到 s=12.87)。"

**关键数字**:
- "pilot min(s) = 1.000 at t = 4920 ps, **确实到过 O 端点**"
- "pilot max(s) = 12.867 at t = 6085 ps, **单次 ~120 ps transient, 很近 UPPER_WALLS z=2.5**"
- "437 ps 之后有 ~4.3 ns plateau, max_s ≈ 10.92"

**必须说的 caveat**:
> "这不是 '500× speedup'。这是 coordinate system rescaling —— kernel λ 从 3.80 变成 100.79, 坐标分辨率不一样了, 不能当 MetaD 采样效率的直接比较。真效率 gain 要等 10-walker converged FES 才能测。"

**过渡**: "2D 分布下一页看。"

---

## Slide 8 — Topic 3 · (s, z) 2D Density (2 min)

**指 JACS-style 2D 图** (slide 单面板):

> "这是 pilot 单个 walker 的 (s, z) 2D 密度图, 风格 mimic JACS 2019 原文 Fig 3。"

**要点**:
- "s 从 1 铺到 12, 整段 path 都有 walker 停留; s=1-7 密度最高, 合理 (walker 从 start.gro 出发然后往 Closed 方向去)。"
- "红色星星是 start.gro (s=7.09, z=1.68); 它**不**在最高密度区域内, 因为它 z 值高 (1.68 vs mean_z 1.53), 偏离 path。"
- "右上角 z>2 有个 transient 尾巴, 对应 max_s=12.87 那次穿越; 到达了 UPPER_WALLS z=2.5 附近。"

**关键 line**:
> "**WT FES 没有复现**。单 walker 8 ns 采样密度在 s 空间是**不均匀**的, free-energy 重建需要 10-walker production 加 sum_hills 才算数。"

**过渡**: "说到 10-walker, 这是我这周最郁闷的一块——"

---

## Slide 9 — Topic 4 · 10-Walker v1 / v2 / v3 (4 min)

**指 slide 表格** (诚实讲失败):

> "10-walker production 我跑了两次, 两次都不能用。"

**v1 (45558834)**:
> "第一次: 从 500 ns Ain cMD 抽 t=50/100/.../500 ns 做 seed, 准备跑。但 cMD 早就 equilibrate 到 Open basin 了, 10 个'不同时间'的 seed 在 CV 空间**全塌在 s≈1**。这违反 FP-030 (shared-HILLS MetaD 需要 walker 在 CV 空间分散)。PM 和 Codex 独立 flag, 22:05 scancel。"

**v2 (45570699)**:
> "第二次: seed 改成从 pilot COLVAR 挑, 对每个 target_s=1..10 挑 min(z) 的 frame。这回 CV 空间分散了——但**所有 10 个 walker 全 crash, exit 139**, 最快 14 分钟最慢 3 小时。"

**指 slide 里的 LINCS log**:
> "crash 都是同一个 pattern: LINCS 在 atom 4463-4465 (一个 CH3 methyl 键) 爆炸, 键长从 0.11 nm 拉到 0.70 nm 甚至 3.67 nm (33× stretched), 然后 SETTLE 跟着 fail, GROMACS segfault。"

> "另外 COLVAR 末尾出现 **metad.bias 负值** (物理上不可能, 累加高斯必须 ≥ 0), 这是下游 corruption: 坐标失稳后喂给 PATHMSD 的 Cα 数组越界, PLUMED 状态也一起炸。"

**Codex 诊断 (30 秒)**:
> "我把完整的 crash log 丢给 Codex 审查。Codex 的诊断是: **seed 来自 pilot xtc, 携带的是 biased-MetaD 过程中的中间构象, 这些构象有残留应力**; 加上 `gmx trjconv -dump` 出的 .gro 没 velocities, GROMACS 在 biased 几何上重新生成速度分布, 第一步 LINCS 就 fail。"

**v3 pipeline**:
> "v3 的修复方案 Codex 已经给了, 三段式: (1) EM 1000 步去 bad contacts; (2) NVT 100 ps at 350 K, PLUMED off, gen_vel=yes 重新生成速度; (3) 从 NVT checkpoint 继续进 production MetaD。"

> "另外 materialize 脚本要加 3 条 assertion: unique-frame guard, seed s 方差 > 2.0, velocity-presence check on start.gro。这些都在 slide 表格最后一列, deliverables 里 submit_v3_template.sh 已经写好了, 等您 approve 之后 sbatch。"

**诚实 line** (必须说):
> "所以**本周的 slide 里所有图都只用 single-walker 的数据**, 没有任何 v1 / v2 的 10-walker frame 冒充 production。10-walker FES 是下周的 deliverable, 不是这周的。"

**过渡**: "接下来讲 ML 层——但先说结论: **如果 10-walker FES 2026-05-01 前不通过 sanity, 所有 ML 扩展全暂停。**"

---

## Slide 10 — Topic 5 · ML-Layer Audit + v2.0 Pivot (3 min)

**直接讲结论, 不 deep dive**:

> "之前 MetaD Cartridge Feasibility Memo v1.2 给了 5 个 ML 方向 (A/B/C/D/E)。本周对 2024-2026 arXiv / Nature / JCTC 做外部 prior art 审计, 结果是**只有 MNG 一条 alive, 两条 weakened, 两条 dead**。"

**逐条 10 秒扫过** (slide 左表):
- "A · CRR — PocketX / ResiDPO / ProteinZero 已经做了类似 reward head → **weakened**"
- "B · PP-Prior — Enhanced Diffusion Sampling 2602.16634 已经做了 path-guided diffusion → **weakened**"
- "C · LBP — NN-VES / Deep-TICA / OPES+mlcolvar 都是 learned bias → **dead**"
- "D · TCR — Thermodynamic Interpolation JCTC 2024 已经做了 FES-matching loss → **dead-ish**"
- "E · MNG — MEMnets 是 CV discovery 不是 runtime gate, 这条**独立 novelty 还在**。"

**Meta 结论** (必须说):
> "audit 的 meta 结论是: **cartridge 这个 artifact 本身可能比任何单层 ML 更 novel**。所以 v1.2 → v2.0 的 pivot 是: 把定位从 'ML 算法创新者' 变成 'F0 PathGate evaluator 的 pip-installable wrapper 作者'。"

**v2.0 sharpen**:
> "F0 PathGate 的 deliverable 是一个 Python 包, 输入任何 trajectory (STAR-MD / ConfRover / classical MD), 输出 (a) project_to_path → (s, z), (b) score_trajectory → JSD + state occupancy + rare-state recall。这是**具体的**东西给 Yu / Amin / Raswanth 用。"

**过渡**: "下一页是具体 deliverables + hard gate。"

---

## Slide 11 — Topic 5 · Deliverables + 2026-05-01 Hard Gate (2 min)

**三段讲完**:

**本周 (D2 + D3)**:
> "D2 是 API 设计文档 `replication/cartridge/API_DESIGN.md` —— 签名 + I/O + 一个 example call, 不写 implementation。D3 是给 Yu 或 Amin 看的 demo, 一个 Jupyter notebook 或 2 页 write-up, 证明 PATHMSD cartridge 能区分 PC 和 O (简单 1D CV 做不到)。"

**下周 (10-walker v3 production)**:
> "v3 pipeline 跑出 10 walker × 30-50 ns, 得到 FES(s, z), 跟 JACS 2019 Fig 2a 比, 至少 2 个 PC 晶体投影到 2D occupancy。block-analysis CI 即使宽也要标出来。"

**2026-05-01 硬 gate** (最关键):
> "**binary 三条**: (1) WT FES 出现 O / PC / C 三个 basin; (2) block CI defined; (3) ≥ 2 个 PC 晶体 2D 投影。"

> "**Gate FAIL → 所有 5 个 ML 方向全暂停**, 回到单 walker → 10 walker 的 debug。不对 Amin / Raswanth / Arvind 做任何 pitch, 因为 WT 自己都没 defensible。"

> "**Gate PASS → D2 freeze, D3 run, Aex1 variant 作为下一个 target, MNG 从 memo 升级到 scoping doc。**"

**过渡**: "最后一页是总结。"

---

## Slide 12 — Summary + Q & A (2 min)

**三段 summary**:

**能 claim 的** (指 slide 左列):
1. Path CV fixed via FP-034 NW +5 offset, 4 层独立验证
2. Miguel contract 锁定
3. Corrected path 让 single walker 8 ns 暴露 s=1-12 区间
4. failure-patterns.md 新增 3 条可复用条目 (FP-031/032/034)

**不能 claim 的** (指 slide 右列):
- ❌ 500× speedup (coord rescaling)
- ❌ start.gro 在 PC basin (soft-min 伪影)
- ❌ barrier crossed (transient, 不 sustained)
- ❌ WT FES 复现了 (10-walker 没完)

**最终 takeaway** (整个 meeting 最重要一句, 必须说出来):
> "**Cross-species PATH-CV construction 必须在选定 residue 范围内硬 gate: sequence identity > 50%。这条已经写进 failure-patterns.md FP-034, 所有 future path-builder 脚本头部必须 assert。**"

> "这句话的意义是: 从**修一个 bug**升级到**建了一条规则**。Yu, 我觉得这是本周最重要的 takeaway, 不是 pilot 的 s=12。"

---

## Q & A 预案 (放在心里, 不上 slide)

### Q1: "+5 offset 不就是 PDB 编号惯例差吗, 听起来不像 bug"
**答**: "对, 大部分是编号惯例差。NW 的 value-add 不是**发现** offset, 是**证明 112 residue 内部没有 indel**, 所以 uniform +5 合法。如果有 indel, 单一数字的 fix 数学上不可能, bug 会错得更彻底。"

### Q2: "zero neighbor_msd_cv = 没 physical intermediate, 你 s=8 凭什么代表 PC?"
**答** (分两句, 不合并):
1. "Path 本身是 geometric reference, s=8 **不 define** PC。"
2. "但 5DW0/5DW3 是**独立**的 biological PC 晶体, 它们 projection 恰好落在 s=8-9, 这是**事后 validation 不是 prior**。真 mechanistic path 需要 string method 或 TMD, 在 future work。"

### Q3: "500 ns cMD 之前的分析是不是也污染了?"
**答**: "cMD trajectory 本身**没污染** (unbiased Cartesian, 没用 path CV)。污染的只是**用老 path 做过的 project_to_path.py 产出**。TechDoc Ch 3.4 列了 3 条 downstream 要重跑: (a) path_piecewise audit retracted, (b) probe_sweep stall 重解释, (c) FP-032 21× 纠正到 1.26×。"

### Q4: "MNG 需要 qMSM, 你会吗?"
**答** (坦白):
"不会。这是下个月关键技术风险。mitigation: Huang lab 教程 + PyEMMA/Deeptime 现成实现。1 个月判断学不动就 drop 给未来 grad student。"

### Q5: "你哪些东西是 Claude / Codex 写的, 哪些是你写的?"
**答**: "build_seqaligned_path.py (NW + Kabsch) 是我写的, 纯 numpy 没依赖。verify_and_materialize_seqaligned_path.py 是 Codex 独立实现的, 用来交叉验证 (结果 byte-level 一致)。v3 submit template 是 Codex 根据 v2 crash log 诊断后给的脚本。Slides 和 TechDoc 的 prose 是 Claude 写的, 我 review + 改。**每个数字都是脚本输出, 不是手算**。"

### 如果 Yu 追问太多 detail → 临时降级话术
"这个我 hot-path 答不对可能犯错。**TechDoc § X** / **VERIFICATION_REPORT** 都写了完整溯源, 我们会后过一遍。"

---

## 上场前 30 秒自检清单

- [ ] pptx 打开到 slide 1, 全屏
- [ ] `CHEATSHEET.md` / `TechDoc_Bilingual.md` / `SELECTION_LOGIC.md` 三个文件窗口待命
- [ ] 笔记本 battery > 50%
- [ ] 喝一口水
- [ ] 深呼吸, 稳住, 你做的是对的事

---

## 最后一句 — 心态

你本周的真实贡献是 (3 件):
1. 发现了一个 2 个月没人发现的 silent bug
2. 独立 + Codex 双实现 cross-verification
3. 诚实承认 10-walker 没跑成功, 不 overclaim

Yu 的 pushback 是保护你, 不是针对你。**稳住、诚实、承认 limitation, 就赢了**。
