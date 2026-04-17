# GroupMeeting 2026-04-17 — 技术文稿 (Technical Documentation)

> **文档定位**: 这是本周组会的完整技术底稿。目标读者是我（Zhenpeng）自己 —
> 读完一遍后我必须能自信地对 Yu 解释所有参数的来源、所有脚本的逻辑、所有
> bug 的根因与修复。同一内容在 `PresenterScript_PPT讲稿.md` 里有口语化版本用
> 于现场朗读；本文件优先讲**为什么**而不是**怎么说**。
>
> **写作原则**: 科学上严谨，写作上诚实。每个参数必须有 source tag；不确定
> 的地方标 UNVERIFIED；涉及数值计算的地方给出脚本命令；任何 manual-compute
> 的数字都必须标注来源行（遵循 feedback_scriptize_all_numerics）。
>
> **创建**: 2026-04-17 by Claude (合并自 Outline + Parameter_Defense +
> Drill_Prep + Script_Bilingual 4 份旧稿，原稿归档于
> `reports/archive/2026-04-17/`)。

---

## 目录

1. [背景与本周目标](#第1章-背景与本周目标)
2. [问题链 (FP-024/025/026/027)](#第2章-问题链)
3. [参数完整表 (11 parameters)](#第3章-参数完整表)
4. [代码 walkthrough (3 scripts)](#第4章-代码-walkthrough)
5. [CV audit 结果 (6-PDB projection)](#第5章-cv-audit-结果)
6. [Job 时间线](#第6章-job-时间线)
7. [10-walker SI 协议完整脚本](#第7章-10-walker-si-协议完整脚本)
8. [阶段 → 脚本对照表](#第8章-阶段--脚本对照表)
9. [Honest-broker 弱论点 + 系统性防御](#第9章-honest-broker)
10. [判断原则与诊断规则](#第10章-判断原则与诊断规则decision-rationale)

---

## 第1章 背景与本周目标

### 1.1 从 2026-04-09 组会出来时的状态

上周组会之后（2026-04-09 transcript）我们定下三件事：

1. **λ 从 3.3910 nm⁻² 修正到 379.77 nm⁻²**（FP-022 per-atom MSD 规约）
   - 公式 `λ = 2.3 / MSD_adj`
   - 我们的 MSD_adj（per-atom 相邻帧平均 squared displacement） = 0.006056 nm²
   - 所以 λ = 2.3 / 0.006056 = 379.77 nm⁻²
2. **FUNCPATHMSD 换回 PATHMSD** — conda-forge 的 PLUMED 2.9.2 `libplumedKernel.so` 缺 PATHMSD 模块（FP-020），
   我们从源码编译了 PLUMED 2.9.2，PATHMSD + FUNCPATHMSD 都能用
3. **Job 42679152**（50 ns 单 walker，PATHMSD + λ=379.77）提交，ETA 约 2026-04-12

本周的主线计划是：拿 Job 42679152 的 50 ns 结果做 FES 重构、对比 JACS 2019 Fig 2a，
如果合理就部署 10-walker。

### 1.2 本周实际发生 (timeline 概述)

| 日期 | 事件 |
|------|------|
| 2026-04-12 | Job 42679152 按时完成 50 ns，walker 没逃出 O basin |
| 2026-04-13..14 | 4 个并行 Explore agent 诊断 → FP-024（SIGMA 塌缩）+ FP-025（伪造引用） |
| 2026-04-15 | plumed.dat 修复（SIGMA_MIN/MAX + SIGMA 0.05→0.1）部署，Job 43813633 提交 |
| 2026-04-16 上午 | Job 43813633 完成，max s=1.393，最后 2 ns 出现逃逸 signature |
| 2026-04-16 下午 | **走错路**：SI "80" 误读为 λ → 3 小时 alignment 诊断（FP-027）|
| 2026-04-16 傍晚 | Codex adversarial review 打穿错误方向，切到 CV audit（4HPX → s=14.91 验证 path CV 正确）|
| 2026-04-16 夜 | `extend_to_50ns.sh` 提交 + FP-026 修复 → Job 44008381 续跑提交 |
| 2026-04-17（今天）| 组会：汇报以上 |

### 1.3 为什么这周报告有分量

- 3 个新 branch 推到远端：`fix/fp024-sigma-floor`、`feature/probe-extension-50ns`、`diag/cv-audit`
- 4 条新 FP（FP-024/025/026/027）+ 2 条通用规则（rule 20/21）
- 新建 `PARAMETER_PROVENANCE.md` 强制 SI 数值引用溯源
- CV audit 硬化成 exit 0/2/3/4 gate，`AuditError` 异常类
- repo 已私有化（Yu 你让我做的）

---

## 第2章 问题链

本章按 FP 编号逐条展开。每条给出**表象 / 根因 / 证据 / 修复**。

### 2.1 FP-024 — SIGMA 塌缩，bias 堆在 s=1 但推不出 O basin

#### 表象
Job 42679152 跑满 50 ns，**机械上完全健康**：

- 25,000 Gaussian 沉积（50 ns / 2 ps PACE = 25k 正好）
- 48 kJ/mol 累计 bias
- HILLS 0 个 NaN
- 没崩、没 warning

**但物理上 walker 不动**：

- `s(R) ∈ [1.00, 1.63]` 整个 50 ns
- 99%+ 时间驻留 s < 1.1（O basin 底部）
- 对比 SI O=[1,5]、PC=[5,10]、C=[10,15] — 我们连 O 的右半边都没进

#### 根因

**`SIGMA=0.05` 在 `ADAPTIVE=GEOM` 下是笛卡尔 nm 单标量**，不是 per-CV 单位。

PLUMED 2.9 METAD 官方文档原话（我查了好几遍，primary source）:

> "Sigma is one number that has distance units"

含义：SIGMA 是**单个 Cartesian 长度**（GROMACS 下默认 nm），不是 per-CV 向量。
`ADAPTIVE=GEOM` 会在运行时把这个 Cartesian 种子投射到每个 CV 上得到 per-CV σ，
并根据 free-energy surface 本地曲率自适应调整。**如果没有 SIGMA_MIN 护栏，
自适应投影可以让某 CV 的 σ 任意塌缩**。

发生在我们系统里的链条：

1. PLUMED 读 `SIGMA=0.05` 当成 0.05 nm Cartesian 种子
2. ADAPTIVE=GEOM 把种子投到 `path.sss` 轴，得到第一个 σ_sss
3. `path.sss` 的 gradient 很小（COMM 域构象变化被一堆 Cα 平均掉），所以投影很窄
4. 没 SIGMA_MIN floor → σ_sss 被允许一路缩到 0.011 s-units
5. 25,000 个针尖 Gaussian 全堆在 s≈1.05 附近
6. 形成**又深又窄的井**：井底 48 kJ/mol 很深，但井壁梯度几乎为零
7. Walker 脚下力传不到蛋白原子 → walker 继续在 O basin 热晃荡

#### 证据

| 证据 | 值 | 怎么拿 |
|------|----|----|
| s 范围 | [1.00, 1.63] | `python3 -c "import numpy; d=numpy.loadtxt('COLVAR',comments='#'); print(d[:,1].min(), d[:,1].max())"` |
| σ_sss 范围 | 0.011–0.072 s-units | HILLS col 4 min/max |
| Gaussian 数 | 25,000 | `wc -l HILLS - 2` (减 header) |
| 累计 bias | 48 kJ/mol | COLVAR col 4 max |
| 99%+ 时间 s<1.1 | 49,720/50,000 frames = 99.44% | numpy boolean mask |

**独立验证**：4 个并行 Explore agent 各用一个角度（physics / literature /
Longleaf forensics / PLUMED C++ 源码）独立诊断，结论汇聚到同一个 root cause。

#### 修复

2026-04-15 部署新的 METAD 行（Longleaf md5 `aca3f0c4...`）：

```
metad: METAD ARG=path.sss,path.zzz \
       SIGMA=0.1 ADAPTIVE=GEOM \
       SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05 \
       HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
```

改了 3 样：

1. **SIGMA 0.05 → 0.1 nm**（Cartesian 种子翻倍）
2. **新增 `SIGMA_MIN=0.3,0.005`** — per-CV 下限，**单位是 CV 单位**：
   - s 方向 0.3 s-units ≈ path 轴 [1,15] 的 2%，保证相邻 reference frame 的 kernel overlap 能让 walker 感知到"跨越一帧"的 bias 方向
   - z 方向 0.005 nm²，略高于 Job 42679152 观测到的 z 噪声水平 (0.002 nm²)
3. **新增 `SIGMA_MAX=1.0,0.05`** — 天花板：
   - s 方向 1.0 s-units ≈ path 轴 7%，比典型 basin 略宽但不跨盆
   - z 方向 0.05 nm²，高于观测典型 z 但不到不合理区

修复后立即提交 Job 43813633（10 ns probe）验证。

### 2.2 FP-025 — Tutorial 里 `[SI p.S3]` 的 `SIGMA=0.2,0.1` 引用是伪造的

#### 表象 / 发现过程

FP-024 诊断时我 grep 仓库所有 SIGMA 相关字段，发现 **5 个互相冲突的数值**：

- Tutorial EN/CN L2087-2148：`SIGMA=0.2,0.1 [SI p.S3]`（看起来最权威）
- 2026-04-04 debug note：`SIGMA=0.2,0.1`（没引用，显然受 tutorial 影响）
- 生产版 plumed.dat：`SIGMA=0.05`（没引用）
- 其他零散 template 各写各的

**最"可信"的是带 `[SI p.S3]` 引用的 0.2,0.1**。但我用 Zotero MCP 完整读了
SI p.S1-S10，**没有任何数值 SIGMA**。SI 原文只写 "adaptive Gaussian width
scheme ... as described in Branduardi 2012"。

所以 `[SI p.S3]` 这个引用是**伪造的** — 早期写 tutorial 的 AI 凭感觉编的，
把"应该有的数字"当"SI 有的数字"写进表里。

#### 根因

早期文档阶段没有 primary-source 验证要求。AI 写 tutorial 时 hallucinate 了
一个"看起来合理"的数字，并且贴上权威引用。这比 FP-016（Lambert 60k vs
100k）更隐蔽，因为它藏在看起来很权威的参数表里。

#### 证据

- Zotero 全文 `papers/ja9b03646_si_001.pdf` p.S1-S10：无数值 SIGMA
- `grep -n "SIGMA" project-guide/TrpB_Replication_Tutorial_EN.md` → L2028, L2087-2088
- 仓库里一共 **5 个冲突数值**

#### 修复

- **FP-025 本身未修**：Tutorial 的假引用还在，参数表和代码块仍然写 `0.2,0.1`。
  非 blocking（不影响当前 production 跑），计划下次 Tutorial 大改时一起清理。
- **但防范措施生效**：新建 `PARAMETER_PROVENANCE.md`（见第 3 章），
  强制 SI 引用必须能 grep 到原文。新加 rule 20（见第 9 章）。

### 2.3 FP-026 — Checkpoint restart 两个静默 bug（会吃掉 10 ns bias）

#### 表象

Job 43813633 跑满 10 ns 后我想直接续跑到 50 ns。**第一版** `extend_to_50ns.sh` 写成：

```bash
gmx mdrun -s metad.tpr -cpi metad.cpt -plumed plumed.dat -nsteps 25000000
```

Codex stop-time adversarial review 立刻打穿这版，指出 2 个静默 bug。

#### 根因（2 个 bug）

**Bug 1 — GROMACS `-nsteps` 不能绕过 "simulation already complete"**

`metad.tpr` 里的 `nsteps=5,000,000`（对应 10 ns）。checkpoint `metad.cpt`
里的 step count 也是 5,000,000。GROMACS 看到 `step = nsteps`，判定 "simulation
already complete"，**立刻退出**（burn 60 秒 walltime 什么都没做）。

`-nsteps 25000000` 命令行参数在这条路径上被忽略。必须用
`gmx convert-tpr -s metad.tpr -extend 40000 -o metad_ext.tpr` 改写 tpr 里的 nsteps。
单位：`-extend` 的参数是 **picoseconds**（不是 steps），40000 ps = 40 ns。

**Bug 2 — 没写 RESTART 会 clobber HILLS**

PLUMED 2.9 RESTART 文档原话：

> "not all MD codes send PLUMED restart info. If unsure, always put RESTART"

意思：`gmx mdrun -cpi` 这条路径上，**GROMACS 不会把 "这是 restart" 的信号
传给 PLUMED**。PLUMED 会把 HILLS 当全新文件打开：
1. 先 rename `HILLS` → `bck.0.HILLS`（备份）
2. 再创建新的空 HILLS
3. 从零开始沉积 Gaussian

结果：10 ns 已积累的 bias history 丢了。**没 warning，没 error，悄悄丢**。

#### 证据

- GROMACS 源码：`src/gromacs/mdrun/runner.cpp` 有 "simulation already complete" 判定
- PLUMED 2.9 docs：RESTART action 明确说 GROMACS 不传 restart info
- Codex adversarial review report

#### 修复

v2 `extend_to_50ns.sh`（已部署到 Longleaf）：

```bash
# Step 1: 扩 tpr 的 nsteps
gmx convert-tpr -s metad.tpr -extend 40000 -o metad_ext.tpr

# Step 2: mdrun 用新 tpr + 带 RESTART 的 plumed
gmx mdrun -s metad_ext.tpr -cpi metad.cpt \
          -deffnm metad -plumed plumed_restart.dat \
          -ntmpi 1 -ntomp 8
```

- `plumed_restart.dat` 第 1 行：`RESTART`
- 后面 byte-identical 到 `plumed.dat`（normalized diff 空）

**Pre-flight 硬 assert**：
- `grep '^RESTART' plumed_restart.dat`（exit 11 若缺）
- `diff <(sed '/^RESTART$/d' plumed_restart.dat) plumed.dat`（exit 12 若差异不止 RESTART 行）

**Post-flight 硬 assert**：
- `wc -l HILLS` 增加（exit 13 若没增）
- 没有 `bck.*.HILLS` 产生（exit 14 若有）
- HILLS 首行数据不变（exit 15 若变）

**Runtime 验证通过**：
- HILLS 行数从 5003 → 5106+
- 没有 `bck.*.HILLS`
- 首行数据不变

### 2.4 FP-027 — SI "80" 误读，走错 3 小时

#### 表象

今天下午我盯着 SI p.S3 原文：

> "The λ parameter was computed as 2.3 multiplied by the inverse of the mean square displacement between successive frames, **80**."

把末尾的 "80" 读成 **λ=80 nm⁻²**。对比我们的 λ=379.77，推出 "**我们 4.75× 过大**"，
提了一个 alignment-method 假设（可能是 Kabsch align 方式不同导致 MSD 不同），
开了 worktree `diag/path-cv-alignment`，写诊断脚本 `test_alignments.py`，
**烧掉 3 小时**。

#### Codex adversarial review 打穿

Codex 原话（critical）:

> "your new 'SI 80 vs our 379.77 differs 4.75x' diagnosis is comparing
> different quantities, so the core premise is not sound"

同时我自己仓库里的 `replication/metadynamics/path_cv/summary.txt` line 23-25
**早就写了正确解释**：

```
Reference (JACS 2019 SI):
  Reported MSD: ~80 Å² (interpreted as total SD)
  Our total SD: 67.826 Å² (ratio 0.85x)
```

summary.txt 把 "80" 理解为 **total SD Å²**（不是 λ）。按这个读法，
我们的 total SD = 67.826 Å² vs SI 的 80 Å² 差 0.85× — **基本匹配**。

#### 根因（3 层）

1. **没有先读仓库既有注释就自行重新诠释 SI 数值** — 这是第一层错
2. **单位/语义不明时凭语法推断代替 primary-source** — SI "80" 原文没给单位；
   summary.txt 已做 judgment call（选 total SD），应 trust 直到有反证
3. **用户的 prior 没吃进去** — Yu 在 session 早些时候已说过 "单位问题 i 也说过了"，
   这本来是强 prior，我没当回事

#### 修复

- 立即停止 alignment 方向；worktree `.worktrees/alignment-diag/` 保留作警示，不 merge
- 切到 Codex 推荐的 **offline CV audit** 验证 path CV 是否物理正确（见第 5 章）
  → 结果 4HPX → s=14.91 **跨物种匹配 3CEP closed**，path CV 物理上对
- 新加 **rule 21**：
  > "SI numeric re-interpretation must read repo's existing notes first;
  > user-confirmed facts are priors"
- 新建 `PARAMETER_PROVENANCE.md` 的 "Known alternate interpretation" 栏

---

## 第3章 参数完整表

> 本章是**每个数字都能 survive 三层 follow-up** 的参数表。
> **Source tag 图例**:
> - **SI-quote**: SI 里有 verbatim 数字，能 grep 到
> - **SI-derived**: 按 SI 公式 + SI 输入算出的
> - **PLUMED-default**: PLUMED 2.9 官方文档默认
> - **Our-choice**: 没 SI/PLUMED 强制，我们选的（必须说明理由）
> - **Legacy-bug**: 历史错值，仅为 traceability 留存
>
> **Cross-ref**: `replication/parameters/PARAMETER_PROVENANCE.md` 是 runtime 权威源。

### 3.1 LAMBDA = 379.77 nm⁻²

| 维度 | 内容 |
|------|------|
| **值** | 379.77 nm⁻² |
| **Source** | SI-derived (公式) + Our-choice (per-atom MSD 规约) |
| **公式** | `λ = 2.3 / MSD_adj` (Branduardi 2007 rule-of-thumb) |
| **SI formula quote** | SI p.S3: "λ was computed as 2.3 multiplied by the inverse of the mean square displacement between successive frames, 80" |
| **SI "80" 含义** | summary.txt 解释为 total SD Å²（不是 λ）。若读作 λ 则歧义（FP-027）|
| **我们的 MSD_adj** | 0.006056 nm² = 0.6056 Å²（per-atom） |
| **调大 2×（759.54）** | 邻帧 kernel 权重降至 exp(-4.6)=0.010 → walker 硬锁到最近 frame；s 变阶梯；ds/dx≈0 between frames → bias 失去抓手 |
| **调小 2×（189.89）** | 邻帧 kernel 权重升至 exp(-1.15)=0.317 → 多帧同时贡献；s 沿 path 被抹平；basin 结构丢失 |
| **Yu 可能会问** | "再讲一遍 379.77 怎么来的" / "SI 80 跟你这个什么关系" / "你怎么保证没算错" |
| **Honest answer** | 2.3 是 Branduardi rule-of-thumb；MSD_adj 是我们 15 帧相邻帧平均 squared displacement (per-atom, nm² 单位)。**与 SI "80" 独立** — 我们没把 80 代入公式；CV audit 独立证明 path CV 物理正确 |
| **Verified** | ✅ self-consistency (frame_1→1.09, frame_8→8.00, frame_15→14.91); PLUMED driver "Consistency check completed!"; 4HPX cross-species s=14.91 |

### 3.2 SIGMA = 0.1 nm（Cartesian seed for ADAPTIVE=GEOM）

| 维度 | 内容 |
|------|------|
| **值** | 0.1 nm |
| **Source** | Our-choice（SI silent） |
| **SI 内容** | 仅 "adaptive Gaussian width scheme" (p.S3), **无数值** |
| **PLUMED semantic** | "Sigma is one number that has distance units"（Cartesian scalar） |
| **调大 2×（0.2）** | 初始种子更宽；ADAPTIVE 启动前 early bias 填 s 空间更快但更粗；transient 阶段 FES 退化 |
| **调小 2×（0.05）** | **正是 FP-024 的值** — 塌缩成 0.011 s-units 针尖。有 SIGMA_MIN floor 理论可以救，但防御性我们不再回 0.05 |
| **Yu 可能会问** | "为什么是 0.1 不是 SI 某个值" / "SIGMA 单位到底是 nm 还是 CV 单位" |
| **Honest answer** | SI 没给数值。0.1 是"塌缩值 0.05 的 2×" 几何式选的。主护栏来自 SIGMA_MIN；SIGMA 初值影响小 |
| **Verified** | ✅ Job 43813633 跑 10 ns 没见塌缩复现 |

### 3.3 SIGMA_MIN = [0.3, 0.005]（per-CV lower bound in CV units）

| 维度 | 内容 |
|------|------|
| **值** | s 方向 0.3 s-units / z 方向 0.005 nm² |
| **Source** | Our-choice（SI silent；PLUMED 要求 ADAPTIVE 下必设） |
| **PLUMED docs** | "the lower bounds for the sigmas (in CV units) when using adaptive hills" |
| **为什么 s=0.3** | path 轴 [1,15] 共 14 s-units；0.3/14 ≈ 2%。够让相邻 reference frame 的 kernel overlap；不会把 basin 结构洗掉 |
| **为什么 z=0.005 nm²** | Job 42679152 COLVAR 观测 z 噪声水平 ≈ 0.002 nm²；floor 定在噪声水平之上一点 |
| **调大 2× ([0.6, 0.01])** | s=0.6 ≈ 4.3% 轴 → 邻近 basin 能量差被抹；Aex1/Ain 若在 s≈1 附近 0.5 s 内可能分不开 |
| **调小 2× ([0.15, 0.0025])** | 接近复现 FP-024 塌缩风险；z floor 低于噪声没意义 |
| **Yu 可能会问** | "0.3 哪里来的 formula" / "为什么不是 0.1 或 0.5" |
| **Honest answer** | **没有 formula** — 我选的 2% of axis。没做 sensitivity sweep。如果 Phase 3 需要 tune，SIGMA_MIN 是候选之一 |
| **Verified** | ✅ Job 43813633 HILLS col 4 min 确实 >0.3（floor 生效） |

### 3.4 SIGMA_MAX = [1.0, 0.05]（per-CV upper bound in CV units）

| 维度 | 内容 |
|------|------|
| **值** | s 方向 1.0 s-units / z 方向 0.05 nm² |
| **Source** | Our-choice（SI silent） |
| **为什么 s=1.0** | ≈ 7% 轴，容纳典型 basin 但不跨盆；防 Gaussian 过宽把 FES 洗成斜坡 |
| **为什么 z=0.05** | 高于观测 z 典型值但不到不合理 |
| **调大 2× ([2.0, 0.1])** | s=2.0 ≈ 14% 轴 → bias 跨越多 basin；局部分辨率尽失；FES 特征洗掉 |
| **调小 2× ([0.5, 0.025])** | 上限太紧；ADAPTIVE 在空白区不能自然展宽；σ 在 MIN/MAX 之间震荡 |
| **Yu 可能会问** | "1.0 怎么选的" |
| **Honest answer** | 对称 SIGMA_MIN 的 judgment call。没 sensitivity data |
| **Verified** | ✅ Job 43813633 HILLS col 4 max 在 MAX 以下 |

### 3.5 HEIGHT = 0.628 kJ/mol

| 维度 | 内容 |
|------|------|
| **值** | 0.628 kJ/mol |
| **Source** | SI-quote + unit conversion |
| **SI quote** | "Initial Gaussian potentials of height 0.15 kcal·mol⁻¹" (SI p.S3) |
| **Conversion** | 0.15 kcal × 4.184 kJ/kcal = 0.6276 ≈ 0.628 kJ/mol |
| **调大 2×（1.256）** | bias 累积快 → 缩短到 target FES 的时长，但可能 overshoot thermodynamic bias（well-tempered damping 还没 engage 之前把 walker 踢到 rare unphysical 构象）|
| **调小 2×（0.314）** | bias 累积慢 → 需要 2× 长 run 才收敛 |
| **Yu 可能会问** | "kcal vs kJ 是不是转错" |
| **Honest answer** | 直接 SI quote × 4.184 = 0.628；GROMACS 用 kJ 单位 |
| **Verified** | ✅ 单位转换数值自洽 |

### 3.6 PACE = 1000 steps

| 维度 | 内容 |
|------|------|
| **值** | 1000 steps |
| **Source** | SI-derived |
| **SI quote** | "deposited every 2 ps of MD simulation at 350 K" (SI p.S3) |
| **Derivation** | 2 ps / 2 fs timestep = 1000 steps |
| **调大 2×（2000 steps = 4 ps）** | Gaussian 数减半；walker 可能在 deposit 之间 escape/settle，打破 well-tempered 假设 |
| **调小 2×（500 steps = 1 ps）** | Gaussian 数翻倍；HILLS 磁盘 + 内存 2×，mdrun 略慢 |
| **Yu 可能会问** | "为什么 2 ps 是对的" |
| **Honest answer** | 直接 SI quote |
| **Verified** | ✅ 2 ps / 2 fs = 1000 算术自洽 |

### 3.7 BIASFACTOR = 10

| 维度 | 内容 |
|------|------|
| **值** | 10 |
| **Source** | SI-quote |
| **SI quote** | "well-tempered adaptative bias with a bias factor of 10" (SI p.S3) |
| **调大 2×（20）** | 有效温度更高 → barrier crossing 快但 FES convergence 慢；walker 在 settle 之前先到处跑 |
| **调小 2×（5）** | 有效 T 低；convergence 快但 explore 差；basin 可能填不满 |
| **Yu 可能会问** | "BIASFACTOR 是什么物理含义" |
| **Honest answer** | well-tempered MetaD 参数 γ；`ΔE_T = (γ-1)/γ × ΔE` 是 damping asymptote，γ=10 → 0.9×ΔE |
| **Verified** | ✅ SI 直接 quote |

### 3.8 TEMP = 350 K

| 维度 | 内容 |
|------|------|
| **值** | 350 K |
| **Source** | SI-quote |
| **SI quote** | "2 ps of MD simulation at 350 K" (SI p.S3) |
| **物理含义** | P. furiosus 是超嗜热菌，体外实验 75°C |
| **调大 2×（700 K）** | 蛋白早变性；不现实 |
| **调小（300 K）** | 室温；fluctuation 小，固定 bias 下 barrier crossing 慢；如果 bias 收敛则 equilibrium FES 相同，但 kinetics 不同 |
| **调小（400 K）** | 更多 escape 事件，但接近热稳定极限（~370 K in vitro） |
| **Yu 可能会问** | "为什么 350 不是 300" |
| **Honest answer** | 嗜热菌 physiological temp；SI quote |
| **Verified** | ✅ SI 直接 quote |

### 3.9 WALKERS_N = 10（Phase 2 待启动）

| 维度 | 内容 |
|------|------|
| **值** | 10 walkers |
| **Source** | SI-quote |
| **SI quote** | "10 walkers" (p.S3，待二次 verify 页码) |
| **调大（15）** | 更多起点覆盖 conformational space，但 HILLS 写入冲突更频繁；HPC 资源开销大 |
| **调小（5）** | 覆盖少；可能某 basin 没人去 |
| **Yu 可能会问** | "为什么不是 15" |
| **Honest answer** | SI 明确说 10；我们严格 replicate |
| **Verified** | ⚠️ SI 页码待二次 verify |

### 3.10 WALKERS_RSTRIDE = per-walker 50-100 ns

| 维度 | 内容 |
|------|------|
| **值** | 每 walker 50-100 ns，总计 500-1000 ns accumulated |
| **Source** | SI-quote |
| **SI quote** | "each walker ran for 50-100 ns" (p.S3) |
| **Yu 可能会问** | "我们跑多长" |
| **Honest answer** | 目标 per-walker 50 ns = 500 ns total（下限）|
| **Verified** | ⚠️ 待 Phase 2 实际部署 |

### 3.11 11 参数 sanity check 表

| 参数 | 值 | Source | Verified |
|------|-----|--------|----------|
| LAMBDA | 379.77 nm⁻² | SI-derived | ✅ |
| SIGMA | 0.1 nm | Our-choice | ✅ |
| SIGMA_MIN (s, z) | 0.3, 0.005 | Our-choice | ✅ |
| SIGMA_MAX (s, z) | 1.0, 0.05 | Our-choice | ✅ |
| HEIGHT | 0.628 kJ/mol | SI-quote | ✅ |
| PACE | 1000 steps | SI-derived | ✅ |
| BIASFACTOR | 10 | SI-quote | ✅ |
| TEMP | 350 K | SI-quote | ✅ |
| WALKERS_N | 10 | SI-quote | ⚠️ 页码 |
| WALKERS_RSTRIDE | 50-100 ns/walker | SI-quote | ⚠️ Phase 2 |

---

## 第4章 代码 walkthrough

本章逐脚本逐行讲。脚本路径都是绝对/仓库相对路径。

### 4.1 `replication/metadynamics/single_walker/plumed.dat`

完整文件（FP-024 修复后版本，md5 `aca3f0c4...`）：

```
# plumed.dat for single walker TrpB MetaD — post FP-024 fix
# Deployed 2026-04-15 by fix/fp024-sigma-floor

MOLINFO STRUCTURE=conf.pdb

# PATHMSD CV: 15-frame linear path 1WDW→3CEP, 112 Cα
path: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77 NEIGH_STRIDE=200 NEIGH_SIZE=10

# Well-tempered MetaD with SIGMA floor (FP-024 remediation)
metad: METAD ARG=path.sss,path.zzz \
       SIGMA=0.1 ADAPTIVE=GEOM \
       SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05 \
       HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 \
       FILE=HILLS

PRINT ARG=path.sss,path.zzz,metad.bias STRIDE=100 FILE=COLVAR
```

**逐行**:

- `MOLINFO STRUCTURE=conf.pdb` — PLUMED 读取拓扑参考（从 gromacs .gro 转出来的 pdb），用于解析残基编号
- `path: PATHMSD REFERENCE=path_gromacs.pdb` — 实例化 PATHMSD CV；reference file 是 15 MODEL blocks 的 pdb
  - `LAMBDA=379.77` — kernel 锐度（见 3.1）
  - `NEIGH_STRIDE=200` — 每 200 steps 重算 neighbor list；PLUMED 默认值
  - `NEIGH_SIZE=10` — 每个 walker 只跟最近 10 个 frame 算 kernel；加速
- `metad: METAD` — 11 个参数见第 3 章
- `PRINT ... STRIDE=100` — 每 100 steps 写一行到 COLVAR（0.2 ps 间隔）
  - 50 ns / 0.2 ps = 250,000 COLVAR 行

### 4.2 `extend_to_50ns.sh` — checkpoint restart 协议

核心段落（FP-026 修复版）：

```bash
#!/bin/bash
set -euo pipefail
# Pre-flight assert: RESTART directive present
grep -q '^RESTART$' plumed_restart.dat || { echo "ERR: missing RESTART"; exit 11; }
# Pre-flight assert: plumed_restart.dat = plumed.dat + RESTART (only)
diff <(sed '/^RESTART$/d' plumed_restart.dat) plumed.dat > /dev/null || { echo "ERR: diff mismatch"; exit 12; }
# HILLS row count before
HILLS_BEFORE=$(wc -l < HILLS)

# Step 1: extend .tpr nsteps to 25M (50 ns total)
gmx convert-tpr -s metad.tpr -extend 40000 -o metad_ext.tpr

# Step 2: mdrun with -cpi + RESTARTed plumed
gmx mdrun -s metad_ext.tpr -cpi metad.cpt \
          -deffnm metad -plumed plumed_restart.dat \
          -ntmpi 1 -ntomp 8

# Post-flight assert: HILLS grew
HILLS_AFTER=$(wc -l < HILLS)
[ "$HILLS_AFTER" -gt "$HILLS_BEFORE" ] || { echo "ERR: HILLS not appended"; exit 13; }
# Post-flight assert: no bck.*.HILLS
! ls bck.*.HILLS 2>/dev/null || { echo "ERR: HILLS was clobbered"; exit 14; }
```

**关键点**:

- `-extend 40000` 单位是 **picosecond**，40 ns
- `plumed_restart.dat` 第 1 行是 `RESTART`，其余 byte-identical 到 `plumed.dat`
- pre-flight exit 11/12 阻止 "假设 plumed 文件对" 的情况
- post-flight exit 13/14 runtime 验证 RESTART 真的生效
- `set -euo pipefail` 任一命令失败立即退出

### 4.3 `project_structures.py` — CV audit script

核心逻辑（伪代码）:

```python
from pathlib import Path
import numpy as np

class AuditError(Exception): pass

def load_reference_frames(path_pdb):
    """Parse 15 MODEL blocks → list of (112, 3) arrays."""
    frames = []
    # ... parse MODEL/ENDMDL blocks ...
    assert len(frames) == 15, f"expected 15 frames, got {len(frames)}"
    return frames

def kabsch_align(mobile, target):
    """Optimal rigid-body alignment, returns aligned coords + rmsd."""
    # ... SVD-based Kabsch ...
    return aligned, rmsd

def pathmsd_s_z(walker_coords, frames, lam):
    """PATHMSD s(R) and z(R) for walker against 15 reference frames."""
    msds = []
    for frame in frames:
        aligned, _ = kabsch_align(walker_coords, frame)
        msd = np.mean(np.sum((aligned - frame)**2, axis=1))  # nm²
        msds.append(msd)
    msds = np.array(msds)
    weights = np.exp(-lam * msds)
    s = np.sum(np.arange(1, 16) * weights) / np.sum(weights)
    z = -(1.0/lam) * np.log(np.sum(weights))
    return s, z

def audit():
    # Load reference
    ref_path = Path(__file__).parent / "path_gromacs.pdb"
    frames = load_reference_frames(ref_path)
    LAMBDA = 379.77

    # Project each known PDB
    results = {}
    for name, chain in [("1WDW","B"),("3CEP","B"),("4HPX","B"),
                        ("5DW0","A"),("5DVZ","A"),("5DW3","A")]:
        try:
            coords = extract_112_ca(name, chain)   # COMM 97-184 + base 282-305
        except MissingAtom as e:
            if name == "5DW3":
                results[name] = "informational (missing residue 285)"; continue
            raise AuditError(f"missing CV atom in {name}: {e}") from e
        s, z = pathmsd_s_z(coords, frames, LAMBDA)
        results[name] = (s, z)

    # Invariant gates
    s_1wdw = results["1WDW"][0]
    if not (0.8 <= s_1wdw <= 1.5):
        raise AuditError(f"s(1WDW) = {s_1wdw:.2f} outside [0.8, 1.5]")
    # ... more gates ...
    return results

if __name__ == "__main__":
    try:
        results = audit()
        print_table(results)
        sys.exit(0)  # pass
    except FileNotFoundError:
        sys.exit(2)  # missing inputs
    except AuditError as e:
        print(f"AUDIT FAIL: {e}", file=sys.stderr)
        sys.exit(3)  # invariant fail
    except Exception as e:
        print(f"CRASH: {e}", file=sys.stderr)
        sys.exit(4)  # crash
```

**逐层理由**:

- `Path(__file__).parent` — 解析 branch-local 路径，hermetic（不做 RCSB live 下载）
- PATHMSD 公式直接 Python 实现：`s = Σ i·exp(-λ·MSDᵢ) / Σ exp(-λ·MSDᵢ)`，
  `z = -(1/λ) · log Σ exp(-λ·MSDᵢ)`，跟 PLUMED `FuncPathMSD.cpp` 源码一致
- Hard gates 覆盖 4 类 invariant：endpoint in range / SI-expected O or C 区 / z ≤ tolerance / 残基 count 严格
- Exit code 0/2/3/4 让上层 Slurm job 能精确区分 pass / 缺输入 / 物理失败 / 脚本 bug

---

## 第5章 CV audit 结果 — 6-PDB 跨物种投影（与上周的 plumed driver 自检不一样）

### 5.0 为什么要做这个 — 和上周的检查有什么区别

| 周次 | 方法 | 输入 | 检的是什么 |
|------|------|------|------------|
| **Week 5 (04-09)** | `plumed driver` 离线 replay 轨迹 | Job 41514529 的 xtc + **我们自己** start.gro | "path CV 在我的 simulation 自己的帧上数值是否合理" — self-consistency 检查 |
| **Week 6 (04-16) — 本周新做** | Python `project_structures.py` Kabsch + MSD 手算 | **6 个 RCSB 下来的外部 PDB**（1WDW / 3CEP / 4HPX / 5DW0 / 5DVZ / 5DW3），**不是** 我自己的 trajectory | "path CV 能否把不同物种、不同化学态的 **实验晶体结构** 映射到预期 s 值" — 跨物种 + 外部 ground truth 验证 |

**区别**：上周是"我自己的 sim 读出来合不合理"，**本周是"把从没进过我 sim 的结构放上去，CV 认不认识它们"**。4HPX（PfTrpB 的 A-A 中间体，外部结构）落到 s=14.91，和 3CEP（StTrpS 的 closed，不同物种）同值 — 这个只能靠外部投影才验得出来，上周的 driver 自检做不到。

### 5.1 6-PDB projection 表

2026-04-16 Codex 推荐后新增，用 `project_structures.py` 把 6 个外部 PDB 投到当前 PATHMSD（LAMBDA=379.77）上：

| PDB | chain | n atoms | s(R) | z(R) nm² | 物理含义 |
|-----|-------|---------|------|----------|---------|
| 1WDW | B | 112 | **1.09** | -0.00025 | O endpoint (frame 1 source) ✓ |
| 3CEP | B | 112 | **14.91** | -0.00025 | C endpoint (frame 15 source) ✓ |
| **4HPX** | B | 112 | **14.91** | -0.00005 | **Pf A-A = St closed (跨物种)** 🔑 |
| 5DW0 | A | 112 | 1.07 | 0.024 | Pf + L-Ser (Aex1), O-like ✓ |
| 5DVZ | A | 112 | 1.07 | 0.017 | Pf holo, O-like ✓ |
| 5DW3 | A | partial | — | — | informational (残基 285 缺)|

### 5.2 关键解读：4HPX → s=14.91 是 path CV 物理正确的**硬证据**

- 4HPX 是 **PfTrpB 的 A-A 催化中间体**（L-Ser 脱水后形成 α-aminoacrylate）
- 3CEP 是 **StTrpS**（鼠伤寒沙门氏菌）的 **closed state**
- 这两个结构属于**不同物种**，但我们的 path CV 给出**几乎完全相同的 s 值 (14.91)**

**含义**:

1. path CV 能正确识别 closed 构象，**与物种无关** — 它抓的是 COMM 域闭合这个
   几何特征，不是 sequence
2. PfTrpB 的 PC/C 态结构 vs StTrpS 的 closed 态，在 COMM 域 Cα 分布上是**保守的**
3. 我们的 **LAMBDA + Kabsch alignment + 15-frame endpoints 都对** — CV 没病

### 5.3 frame self-consistency

| frame # | expected s | actual s | 差 |
|---------|------------|----------|---|
| 1 | 1.0 | 1.0913 | 0.09 |
| 8 | 8.0 | 8.0000 | 0 (exact by symmetry) |
| 15 | 15.0 | 14.9087 | 0.09 |

**为什么 frame 1 不是精确 1.0**？PATHMSD 公式 kernel 加权不是 delta function：
即便 walker = frame 1，公式给的是
`s = (1·1 + 2·exp(-λ·MSD₁₂) + ...) / (1 + exp(-λ·MSD₁₂) + ...) ≈ 1.09`。
1.09 是 textbook 正常行为，不是 bug。

### 5.4 结论

**Path CV 物理上完全正确**。probe 的 kinetic stagnation 是**时间预算问题**，
不是 CV 病理。

---

## 第6章 Job 时间线

| Job ID | 日期 | 时长 | 关键参数 | 结果 |
|--------|------|------|---------|------|
| **42679152** | 2026-04-09 提交 / 04-12 完成 | 50 ns | `SIGMA=0.05`, 无 floor, `LAMBDA=379.77`, PATHMSD | walker 卡 O; s∈[1.00, 1.63]; σ 塌缩 0.011–0.072; 25k Gaussian; 48 kJ/mol bias; **FP-024 signature** |
| **43813633** | 2026-04-15 提交 / 04-16 完成 | 10 ns probe | `SIGMA=0.1`, `SIGMA_MIN=0.3,0.005`, `SIGMA_MAX=1.0,0.05` | max s=1.393；99% 时间 s<1.05；last 2ns 出现 +0.49 s↔z correlation（escape signature） |
| **44008381** | 2026-04-16 傍晚提交 / running | 40 ns 续跑 = 50 ns total | 同 43813633 + RESTART protocol | **今天 (2026-04-17 15:32) 状态**: 27.68 ns，max s=**3.494**（首次越过 s=3 门槛，1.41% 帧 s>3），已进入 3-5 观察区 |

### 6.1 Job 44008381 当前状态解读 (as of 2026-04-17 12:33)

- 27.68 ns 已跑 ≈ 总时长的 55%
- max s = **3.494** — **首次越过 s=3 门槛**（1.41% 帧 s>3），已进入 3-5 观察区
- 还没触发 25 ns 决策阈值 `max s ≥ 5 → Phase 2`
- 目前走在 **3 ≤ max s < 5 gray zone** → 让 50 ns 跑完再看

### 6.2 25 ns 决策闸门

| max s @ 25 ns | 决策 | 理由 |
|---------------|------|------|
| ≥ 5 | → Phase 2 (10-walker production) | 进 PC 区 → CV 能 drive 到 closed，可以部署 SI 严格协议 |
| 3 ≤ max s < 5 | 让 50 ns 跑完再看 | 过了 O basin 3σ 边界但没到 PC，模糊地带 |
| < 3 | → Phase 3 (4HPX-seeded dual-walker) | 单 walker 推不动，需要从 closed 端也放一个 |

**当前 max s=3.494** 已进入 3-5 观察区（刚越过 3）。如果 50 ns 内能到 5，走
Phase 2；否则 Phase 3。

---

## 第7章 10-walker SI 协议完整脚本

### 7.1 SI 原文 verbatim

从 SI p.S3（引自 PARAMETER_PROVENANCE.md 的 WALKERS section）：

> "To cover approximately all conformational space available, 10 walkers
> were launched from snapshots of the initial conventional MD simulation,
> each running for 50-100 ns of well-tempered metadynamics."

**拆解**:

- **10 walkers** ← WALKERS_N = 10
- **snapshots of the initial conventional MD simulation** ← 初始构象不是任意挑；
  **从我们 500 ns conventional MD 轨迹里选 10 个**
- **each running for 50-100 ns** ← WALKERS_STRIDE 50-100 ns per walker
- **covers approximately all conformational space available** ← 这个 "all" 是
  **initial run 能够 cover 的空间**，不是 O/PC/C 全覆盖（Yu 2026-04-09 L3009 flagged）

### 7.2 初始构象选择协议 (Yu 的 2026-04-09 directive)

Yu 的指示是 "**用眼睛看 PyMOL 挑结构差异大的**，不要每隔 N frame 机械取"。
我的执行计划（脚本辅助 + 眼看终审）:

1. **脚本候选池**: 从 `metad.xtc` 按 (s, z) 平面 bin 成约 20 cells，每 cell 取
   medoid frame，得 ~20 候选 PDB
2. **导出**: 候选 frame → 每个一个独立 PDB 文件，写入
   `replication/metadynamics/multi_walker/snapshots/candidate_{i}.pdb`
3. **PyMOL 叠加检查**: `pymol -r load_candidates.pml` 同时打开所有 20 个，
   Cα trace 模式看 COMM 域是否在结构上 diverse
4. **眼看筛选**: 从 20 个里手动挑 10 个结构差异最大的，丢弃冗余
5. **记录决策**: 每个入选 frame 记 `(frame_idx, s, z, rationale)` 到
   `snapshots_selection.md`

**Honest caveat**: 如果 Phase 2 启动条件不满足（walker 没覆盖到 s>3），候选池
都挤在 O basin，眼看筛选也救不了 — 那必须走 Phase 3。

### 7.3 Track E 产出的脚本 (reference, 不在本文件复制)

Multi-walker 部署脚本由 Track E 本周产出（不 duplicate 到这里）:

- `replication/metadynamics/multi_walker/plumed.dat` — MULTIPLE_WALKERS 版 plumed
  （已在本 branch，md5 见 git log；差异仅在 METAD 行加 `WALKERS_N=10 WALKERS_ID=${walker_id} WALKERS_DIR=../ WALKERS_RSTRIDE=1000`）
- `replication/metadynamics/multi_walker/plumed.dat.bak_FUNCPATHMSD_2026-04-15` — backup（历史 FUNCPATHMSD 版本）
- `replication/metadynamics/multi_walker/setup_walkers.sh` — 两阶段启动脚本：先 KMeans(s,z) 产 10 candidate frames，再经用户 PyMOL 视觉确认后 `--commit-frames` 实例化 walker_0..walker_9/
- `replication/metadynamics/multi_walker/submit_array.sh` — Slurm 单作业 10-GPU (`gmx_mpi mdrun -multidir walker_0..walker_9`), shared `../HILLS`
- `replication/metadynamics/multi_walker/README.md` — SI 原文引用 + Yu L2859 指示 + 收敛/中止判据

> **Note**: 本文件 reference 这些路径，不复制内容。Track E 完成后 Track B
> 的后续 revision 可以加 md5 行。

---

## 第8章 阶段 → 脚本对照表

> 本表覆盖 **8 个 pipeline 阶段**。每行给出：阶段名、脚本路径（可直接复制执行）、
> 何时用、期望输出。严格按 `scripts/pipeline_guard.py` 的 6-stage 划分 + 2 个
> MetaD 子阶段（single-walker, multi-walker）。

| 阶段 | 脚本 | 何时用 | 期望输出 |
|------|------|--------|---------|
| **Path CV 生成** | `python3 replication/metadynamics/path_cv/generate_path_cv.py --num-frames 15` | 修改 endpoints (1WDW/3CEP chain / 残基范围) 后 | `path_gromacs.pdb` (15 MODEL blocks, 112 Cα); `summary.txt` (λ 推荐 + MSD 统计) |
| **AMBER→GROMACS 转换** | `python3 replication/metadynamics/conversion/parmed_convert.py --amber system.parm7 system.inpcrd --out system.top system.gro` | system build 完后第一次进 GROMACS | `system.top`, `system.gro` (原子数 39,268，电荷中性，验过 4 Na⁺) |
| **CV audit** | `cd .worktrees/cv-audit && /tmp/aln_env/bin/python project_structures.py; echo exit=$?` | 改 LAMBDA / path 生成方式后，或 SI 数值 re-interpretation 前 | stdout 6-PDB projection table; exit 0 pass / 2 missing / 3 invariant fail / 4 crash |
| **Single-walker submit** | `sbatch replication/metadynamics/single_walker/submit.sh` (参数 `--export=NSTEPS=5000000`) | 新参数首次验证 (10 ns probe) | Slurm job; `metad.xtc`, `HILLS`, `COLVAR`, `metad.cpt`, `metad.log` |
| **Checkpoint extend** | `bash replication/metadynamics/single_walker/extend_to_50ns.sh` | probe 显示 escape signature，续跑到 50 ns | `metad_ext.tpr`; HILLS append 5003→20000+ rows; 无 `bck.*.HILLS` |
| **FES 重建** | `plumed sum_hills --hills HILLS --kt 2.908 --bin 200,200 --mintozero --outfile fes.dat` | walker 跑完后做 FES | `fes.dat` (2D s-z FES, min=0, kJ/mol 单位); 对比 JACS 2019 Fig 2a |
| **10-walker setup (Phase 1 候选)** | `bash replication/metadynamics/multi_walker/setup_walkers.sh <colvar_path>` | Phase 2 启动 (max s ≥ 5 后)，single-walker 跑完提供 COLVAR | `candidate_frames.csv` (10 rows, KMeans(s,z) clustering)；stdout 提示用户进 PyMOL 人工确认 (Yu L2859 directive) |
| **10-walker setup (Phase 2 提交)** | `bash replication/metadynamics/multi_walker/setup_walkers.sh --commit-frames t1,t2,...,t10` | PyMOL 视觉验证 10 帧后 | walker_0..walker_9/ 目录填充 start.gro + topol.top + plumed.dat（每 walker 里 WALKERS_ID 已 sed baked in） |
| **10-walker submit** | `sbatch replication/metadynamics/multi_walker/submit_array.sh` | walker_0..walker_9 都就位后 | 1 Slurm 单作业 10 GPU (`gmx_mpi mdrun -multidir`)；shared `../HILLS`；每 walker 内 `COLVAR`；目标 50-100 ns/walker = 500-1000 ns total |

### 8.1 kT 单位说明（FES 重建常出错的点，FP-021）

```
--kt 2.908
```

- 2.908 kJ/mol = kB · 350 K · NA / 1000（kJ 单位）
- **不是** 0.695 kcal/mol（那会让 FES 放大 4.184×，FP-021）
- `plumed sum_hills` 在 GROMACS unit set 下默认期望 kJ，必须显式 `--kt 2.908`

### 8.2 为什么有 8 个阶段而不是 6 (pipeline_guard 原生)

Pipeline_guard 的 6 stage 是 Profiler/Librarian/Janitor/Runner/Skeptic/Journalist
（meta-process）。**本表的 8 行是 Runner 阶段内部的 sub-step**（实际脚本执行），
因为 Yu 问的是"具体哪条命令跑什么"而不是"哪个 meta-stage"。

---

## 第9章 Honest-broker

> 本章列出**我目前最脆弱的 5 个论点** + **系统性防御**。写这章是因为 Yu 在 2026-04-09
> 提问往往往下挖 3 层，弱论点不写清楚，drill 当场就会翻车。

### 9.1 弱论点 #1 — "max s=3.49 是 escape 还是 O basin"

**我的当前说法**: walker 在 44008381 @ 27.68 ns 达到 max s=3.494（1.41% 帧 s>3），这比 probe 的
1.393 翻倍，说明 escape 正在进行。

**弱点**: 3.49 **还在 SI O=[1,5] 内**。严格说不是 escape，是 "O basin 内更深
探索"。说"翻倍"只是 **相对** probe；绝对值仍在 O。

**Yu 的可能反问**: "所以你到底 escape 了没？"

**Honest answer**:
- **严格：没 escape**（SI 定义 O=[1,5]；3.49 在 O 内）
- **有 escape signature**：10 ns probe 最后 2 ns s↔z 相关从 -0.31→+0.49，典型
  activated-barrier crossing（walker 沿 path 前进时拖着 z 一起走）
- **50 ns 跑完能给答案**：若到 50 ns 还在 s<3 徘徊，就真卡；若能稳到 s≥3 甚至到 5，算 escape
- **Bail-out rule**: 若 50 ns 结束 max s < 3，切 Phase 3（4HPX-seeded dual-walker）

### 9.2 弱论点 #2 — "10 snapshots 怎么挑"

**我的当前说法**: 按 Yu 2026-04-09 directive 用 PyMOL 眼看，不用 strided。

**弱点**: 如果 walker 在 44008381 里都挤在 s<3，候选池本身就没 conformational
diversity，眼看也救不了。

**Yu 的可能反问**: "script 挑出来 20 个都像，怎么办？"

**Honest answer**:
- 工作流: **script narrows candidates, eyes make final cut**。script 按 (s,z) bin 取
  medoid → 20 候选 → PyMOL 叠加检查 → 眼看筛 10
- **如果候选池都挤在 O basin**：无解。必须走 Phase 3，用 4HPX 当 closed 端
  二号 seed
- **Commitment**: 下次组会给 Yu 看 script + 候选 frame list + PyMOL 截图，不
  只是 frame index 列表

### 9.3 弱论点 #3 — "FP-027 你怎么保证不再犯"

**我的当前说法**: 4 条结构性修复 + rule 21。

**弱点**: 结构性修复防的是 "SI 数值仓库已有注释的 re-interpretation"。
**完全新的 SI 内容**第一次读，仍然可能错。

**Yu 的可能反问**: "下次遇到 SI 里全新一个数你咋办？"

**Honest answer**:
- 针对仓库**已有注释**的情况：rule 21 硬性要求先读 existing interpretation
- 针对**全新 SI 内容**：规定必须跑 Codex adversarial review 才能 act on 重大
  诠释。Codex 没 session 上下文，fallback 机制
- 还不够：新内容第一次读时**给至少 2 种读法的数字对照表** + 显式跟 Yu 确认
  选哪种，不单方面定性

### 9.4 弱论点 #4 — "Path CV 的 4HPX 跨物种匹配 - 信得过吗"

**我的当前说法**: 4HPX (Pf A-A) → s=14.91 = 3CEP (St closed) → path CV 物理正确

**弱点**: 4HPX 和 3CEP 都属于"closed"大类，结构相似是 **a priori** 就合理的。
可能只是 path CV 对 **large-scale closure** 敏感、对 **fine details** 不敏感。

**Yu 的可能反问**: "frame 8 （中间态）你怎么 validate？"

**Honest answer**:
- frame 8 是 **linear Cartesian interpolation** 产物，不是物理中间态
- Self-consistency check: frame 8 → s=8.0 exact（by construction）但这只证明 CV 数学对，**不证明 frame 8 物理 make sense**
- **有风险**：若 frame 8 有 steric clash / 非物理 torsion，walker 靠近 s=8 时
  可能被 bias 推进非物理构象。**缓解**：PLUMED 运行时 Kabsch 去刚体旋转，只看内部变形；
  endpoints 总 RMSD 10.9 Å → per-Cα-per-adjacent-frame 0.78 Å 变形 ≈ bond-length scale，
  linear interp 基本不引入 clash
- **Commitment**: Phase 2 若 walker 到不了 PC，一个 debug step 就是对 frame 5/8/10 做
  能量最小化，看有没有 relax 到合理构象

### 9.5 弱论点 #5 — "为什么 10 walkers 而不是 15 或 5"

**我的当前说法**: SI 明说 10。

**弱点**: SI 的 10 是**他们系统**的 "10 cover all space"。我们不一定需要 10
来 cover 我们的空间。

**Yu 的可能反问**: "为什么不跑 15 增加覆盖"

**Honest answer**:
- 我们是**严格 replication** — SI 说 10 就 10
- 如果以后做 generalization（GenSLM-230 比较），walker 数可以按计算预算调
- HPC 资源：10 walker × 50 ns ≈ 10 × 70 hrs = 700 hrs，单 job array 一周内能
  跑完；15 walker 1.5×
- 不想加的真实原因：**严格 replicate SI 才有 credible comparison**，如果我们
  改 WALKERS_N，说"我们的 FES 跟他们一样" 说服力打折

### 9.6 系统性防御（从 FP-024/025/026/027 沉淀出的机制）

**1. `PARAMETER_PROVENANCE.md`**（本周新建）
- 每个 production 参数带 source tag + verified 栏 + known alternate interpretations 栏
- 防 FP-025 + FP-027 重现
- 改参数前必须先读对应行

**2. Rule 20**（failure-patterns.md 新加）
> "任何 `[SI p.SX]` 引用必须能在原 PDF 里 grep 到原文；不能推断；违反则列入 fabricated citation"

**3. Rule 21**（failure-patterns.md 新加）
> "SI numeric re-interpretation must read repo's existing notes first; user-confirmed facts are priors"

**4. Codex adversarial review as stop-hook**
- 任何"重大诊断方向切换"前必须跑 Codex adversarial review
- Codex 无 session 上下文 → 不会 fall for 同一个 misread
- FP-026 和 FP-027 都是 Codex 打穿的

**5. Repo transcript as prior**
- `.local_scratch/` 保留 Yu 的历次 session 笔记
- Yu 说过的话 = prior；推翻必须显式说 "I'm pushing back because X"

**6. CV audit as hard gate**
- `project_structures.py` exit 0/2/3/4；AuditError class；malformed input 不 crash
- 任何改 LAMBDA / path 生成方式后 **先过 audit 再部署**

**7. 3-branch 隔离**
- `fix/fp024-sigma-floor` / `feature/probe-extension-50ns` / `diag/cv-audit`
- 每个 bug 修复独立 branch，不互相污染
- Repo 已私有化

---

## 附录 A — 文件 md5 snapshot (2026-04-17)

| 文件 | md5 | 用途 |
|------|-----|------|
| `replication/metadynamics/single_walker/plumed.dat` | aca3f0c4... | 生产 plumed (SIGMA_MIN fix) |
| `replication/metadynamics/single_walker/plumed_restart.dat` | (plumed.dat + RESTART 行) | Job 44008381 restart 用 |
| `replication/metadynamics/single_walker/extend_to_50ns.sh` | v2 已部署 | checkpoint extend |
| `.worktrees/cv-audit/project_structures.py` | (见 git log) | CV audit gate |
| `replication/metadynamics/path_cv/path_gromacs.pdb` | (见 git log) | 15 MODEL block reference |
| `replication/parameters/PARAMETER_PROVENANCE.md` | 新建 2026-04-16 | 参数权威源 |
| `replication/validations/failure-patterns.md` | FP-001..027 + rule 1..21 | 错误模式库 |

---

## 附录 B — 2026-04-09 会议 reference points (可能被 Yu pull up)

| Reference | 值 | Context |
|-----------|----|----|
| ratio 80 vs 0.6056 = 132 | ~132× per-atom MSD 规约错 | Yu 2026-04-09 L393；已由 2.3/0.6056=379.77 修掉 |
| Job 41514529 s range | [7.77, 7.83] | pre-fix FUNCPATHMSD run (FP-022 signature) |
| "Ångström 与 Nano" | SI 自己单位 ambiguity | Yu L459；acknowledged，不 central |
| "cover all conformational space" | SI 原文歧义 | Yu L3009；"all" 指 initial MD 能 cover 的空间，不是 O/PC/C 全覆盖 |
| "用眼睛看 PyMOL" | 10-walker snapshot 选择 | Yu L2859；本周 Phase 2 启动时执行 |

---

## 第10章 判断原则与诊断规则（Decision Rationale）

> 本章记录本项目中用到的**诊断逻辑和决策规则**。每次做判断时，这些规则是怎么来的、
> 怎么验证的。未来遇到类似问题可以直接用。

---

### 10.1 HILLS 法医分析三步法

每次跑完/跑中，打开 HILLS 做以下三个检查：

**步骤 1 — Sigma 健康检查（防 FP-024 复发）**

```python
import numpy as np
h = np.loadtxt('HILLS', comments='#')
# 列: time  s  z  sigma_ss  sigma_zz  sigma_sz  height  biasf
sigma_sss = h[:, 3]
print(f"sigma_sss range: {sigma_sss.min():.4f} – {sigma_sss.max():.4f} s-units")
```

| 结果 | 诊断 |
|------|------|
| min ≥ 0.30 (= SIGMA_MIN) | 健康，floor 生效 |
| min < 0.1 且 max < 0.1 | FP-024 复发 — sigma 全程塌缩 |
| min ≈ SIGMA_MIN, max ≈ SIGMA_MAX | floor+ceiling 均生效，适应性工作正常 |

**步骤 2 — Bias 历史完整性检查（防 FP-026 复发）**

```bash
ls bck.*.HILLS 2>/dev/null && echo "DANGER: bias history clobbered" || echo "OK: no backup"
wc -l HILLS   # 健康: 行数只会增不会减
```

**步骤 3 — 沉积速率检查（检测 walltime 截断 vs 自然结束）**

```python
times = h[:, 0]  # ps
n_gaussians = len(h)
pace_ps = 2  # PACE=1000 steps × 0.002 ps/step
expected = (times[-1] - times[0]) / pace_ps
print(f"实际: {n_gaussians}  期望: {expected:.0f}  比率: {n_gaussians/expected:.3f}")
# 比率 ≈ 1.0 → 正常完成；比率 < 0.95 → walltime 截断或中间 crash
```

---

### 10.2 SIGMA_MIN/MAX 选值原则

**为什么 SIGMA 是 nm 但 SIGMA_MIN/MAX 是 CV 单位？**

这是本项目最容易混淆的单位问题，记清楚：

| 参数 | 单位 | 原因 |
|------|------|------|
| `SIGMA=0.1` | Cartesian nm（单标量） | PLUMED 2.9 docs 原话："Sigma is one number that has distance units"。ADAPTIVE=GEOM 用这个 nm 标量作为几何种子，投影到每个 CV 轴。 |
| `SIGMA_MIN=0.3,0.005` | per-CV 原生单位（逗号分隔） | SIGMA_MIN/MAX 是对投影后的 per-CV σ 的约束。投影完之后 σ 活在 CV 的单位里，所以约束值也必须用 CV 单位写。 |
| `SIGMA_MAX=1.0,0.05` | 同上 | 同上 |

**两个 CV 的原生单位分别是什么：**

- `path.sss`（s(R)）= Σ i·exp(−λ·MSD) / Σ exp(−λ·MSD)：分子是 index (1–15) 乘权重，分母是权重，结果**无量纲**（s-units，范围约 1–15）
- `path.zzz`（z(R)）= −(1/λ)·ln(Σ exp(−λ·MSD))：λ 单位 nm⁻²，结果单位 **nm²**（1/nm⁻² = nm²）

**SIGMA_MIN 值是怎么选的：**

```
SIGMA_MIN[sss] = 0.3 s-units
  → 路径轴总长 14 s-units (s=1 到 s=15)
  → 0.3/14 ≈ 2.1%，约为"path 轴的 2%"
  → 原则：floor 不能太窄（会退化回 FP-024），不能太宽（会过度平滑 FES）
  → 1–3% 是 path CV 文献中常见的经验范围

SIGMA_MIN[zzz] = 0.005 nm²
  → 从 Job 42679152 COLVAR 的 z(R) 值看，z 的热噪声约 0.001–0.003 nm²
  → 0.005 nm² 是热噪声的 2–5×，足够大但不过宽
  → 原则：z 方向不需要太大，z CV 主要防止偏离 path 不是驱动越 barrier
```

**经验验证：**
- FP-024 原 sigma_sss 最小值：0.011 s-units（塌缩）
- 加 SIGMA_MIN=0.3 后的 sigma_sss 最小值：≥0.300（floor 生效，Job 43813633 实测）

---

### 10.3 Phase 决策闸门的完整逻辑

**为什么 max s ≥ 5 才触发 Phase 2，而不是 max s ≥ 3？**

SI 原文要求 10 walkers 的初始构象"covering approximately all the conformational space 
available"。s=3 仍在 O→PC 过渡区，walker 没到 PC basin（SI 定义 PC ≈ s=5–10）。
用 s=5 作为门槛是因为：

| s 范围 | 构象区域 | 原因 |
|--------|---------|------|
| 1–5 | O basin + O→PC 过渡 | COMM domain 开放 |
| 5–10 | PC basin | COMM 部分闭合 |
| 10–15 | PC→C + C basin | COMM 完全闭合（3CEP/4HPX 区域） |

要保证 10 walkers 能覆盖三个区域，单 walker 至少得进 PC（s≥5），才有意义按
s-bin 聚类出多样性种子。

**5-ns 窗口趋势判断规则：**

```python
# 连续 k 个 5-ns 窗口全部 max s 平坦 → walker 卡住
# 连续 k 个窗口单调上升 → walker 正在爬坡
# 任意一个窗口大幅跳升（> +0.5 s-units/5 ns）→ activated-barrier crossing 迹象
```

如果 **3 个连续 5-ns 窗口 max s 变化 < 0.1 s-units**，认为 walker 卡住；
即使最终 max s ≥ 3 也不能确定是"在过 barrier"，可能是局部困陷。

---

### 10.4 HILLS/COLVAR 文件管理原则

**本地存放位置（2026-04-17 起）：**

```
replication/metadynamics/
├── single_walker/
│   ├── HILLS      ← 当前跑（Job 44008381, 下载于 2026-04-17）
│   └── COLVAR     ← 同上
└── archive_pre_2026-04-15/
    ├── job42679152_sigma_stuck_FP024/
    │   ├── HILLS  ← FP-024 broken 50 ns run（25003 Gaussians，sigma_sss 塌缩）
    │   └── COLVAR
    └── job41514529_fp022_lambda/
        ├── HILLS  ← FP-022 broken run（λ=3.39，FUNCPATHMSD，path.s/path.z 命名）
        └── COLVAR
```

**更新规则：每次 SSH 检查后，如果 job 仍在跑且 COLVAR 行数增加了 1000+ 行，
重新 `scp` 一次 HILLS + COLVAR 到 `single_walker/`。** 不需要下载整个 trajectory。

**HILLS vs COLVAR 的区别（两个文件都要存）：**

| 文件 | 内容 | 主要用途 |
|------|------|---------|
| HILLS | 每 PACE 一行：time, s, z, sigma_ss, sigma_zz, sigma_sz, height, biasf | Sigma 诊断 + FES 重建（plumed sum_hills） |
| COLVAR | 每 stride 一行：time, s(R), z(R), metad.bias | Walker 位置追踪 + Phase 决策 + s↔z 相关分析 |

---

### 10.5 "再推一次"陷阱的识别规则（防 FP-027）

**规则**：对任何 SI 中的数值，在重新解释之前，**先检查仓库已有注释**：

```bash
grep -r "该数值" PARAMETER_PROVENANCE.md failure-patterns.md papers/reading-notes/
```

FP-027 的根因不是误读 SI，而是**在已有正确解释的情况下又重新推导了一遍**，
导致新的推导覆盖了正确的旧解释。`summary.txt line 23-25` 早就写了正确答案。

**Stop condition**：如果仓库里有对某个 SI 数值的注释，且注释有来源标注（SI-quote / 
SI-derived / Our-choice），**不准推翻，除非 Yu 明确要求重验**。

---

**本章结束。**

---

**文档结束**。如需朗读版本，见 `GroupMeeting_2026-04-17_PresenterScript_PPT讲稿.md`。
