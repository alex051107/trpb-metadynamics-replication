# Group Meeting 2026-04-09 — 讲稿（中英对照）

> **使用说明**
>
> - **中文部分**：给自己看的详细版，每个参数、每行代码、每个数字都讲清楚来源
> - **英文部分**：明天 lab meeting 上要说的版本，相对简洁
> - 讲稿顺序和 10 页 slides 一一对应

---

## Slide 1 — Title

### 中文（给自己看的详细版）

这一页就是开场。标题：**TrpB MetaDynamics Benchmark — Weekly Progress Report**，副标题写了名字、lab、日期。

我的工作是复刻 Osuna 组 2019 年那篇 JACS 的 MetaDynamics 协议。这周的重点是 debug 一个 path collective variable 的参数问题——表面上看起来 MetaDynamics "跑不动"，深挖下去发现是 CV 本身数学上有问题。我会从上周的进度说起，然后说这周遇到的问题、怎么找到根因、怎么修的，以及为什么我最后选择换回 SI 原版的 `PATHMSD`。

### English (for the talk)

Good morning. This is the weekly progress report on the TrpB MetaDynamics benchmark. I'm replicating the Maria-Solano 2019 JACS protocol on TrpB from *Pyrococcus furiosus* — the thermophilic homolog of tryptophan synthase. The reason I'm replicating an existing paper is that the free-energy surface I produce becomes the conformational F1 layer for three downstream pipelines in our lab: Amin's STAR-MD physics benchmark, where I provide the ground-truth FES; the GRPO reward signal for GenSLM sequence generation; and future TrpB variant screening, for example GenSLM-230 versus NdTrpB. In other words, every downstream consumer needs *my* FES to be correct. This week I'm going to walk through a path-CV parameter bug that I found and fixed, explain why our original "stuck in PC" interpretation was wrong, and then explain why I'm switching the production setup back to `PATHMSD`, which is what the original SI used, instead of the `FUNCPATHMSD` workaround we were on last week.

---

## Slide 2 — Background

### 中文

这一页一句话交代项目目的。我在做 `PfTrpS(Ain)` 的 COMM 域构象自由能面 (FES)，用 Well-Tempered MetaDynamics + Path CV。最终的 baseline FES 要被三条下游 pipeline 用：

1. **Amin 的 STAR-MD benchmark**：我的 FES 作为他那个 AI 动力学预测的 ground truth
2. **GenSLM + GRPO reward**：给 Raswanth 的 RL 训练提供 conformational reward 信号
3. **未来所有 TrpB 变体的 conformational screening**：比如 GenSLM-230 vs NdTrpB 对比，都走同一套 pipeline

SI 原版的协议是：先跑 initial run → 从里面提 10 个 snapshots → 从 10 个 snapshots 并行跑 10-walker production（每个 walker 50-100 ns）。我现在卡在 initial run 这一步。

### English

The physical goal is to build a benchmark free-energy surface for the COMM domain of `PfTrpS(Ain)` — that's TrpB bound to the Ain intermediate, which is the covalent PLP adduct formed right after Schiff-base exchange with the substrate. The COMM domain is a loop region that closes around the active site during catalysis, and its conformational equilibrium between Open, Partially Closed, and Closed states directly controls catalytic efficiency — this is why Osuna picked it as a design target. We use well-tempered MetaDynamics to accelerate the closure motion, and we parameterize the motion with two path collective variables: `s(R)` measures progress along an Open-to-Closed reference path with values from 1 to 15, and `z(R)` measures how far the current configuration deviates from that path perpendicular to the path direction. This two-dimensional (s, z) space is what we deposit Gaussian bias potential on. The SI protocol is: run one initial single-walker trajectory first, extract ten snapshots from it that span the Open, PC, and Closed basins, and then launch a ten-walker parallel production of 50 to 100 nanoseconds each for the actual benchmark. I'm currently stuck on the initial-run stage — that's what the whole talk today is about.

---

## Slide 3 — Last Week

### 中文

上周完成的工作：

- **500 ns conventional MD**（Job 40806029）：用 AMBER pmemd.cuda 跑完了，71.5 小时，产生 22 GB 的 .nc 轨迹。目的是生成一个合理平衡过的 starting structure 给 MetaD。用的参数全部照 SI：ff14SB, TIP3P, 350 K, 2 fs timestep, NVT。
- **AMBER → GROMACS 格式转换**：ParmEd，39,268 原子全部对上。因为 SI 原文用的是 GROMACS + PLUMED（不是 AMBER + PLUMED），所以 MetaDynamics 必须在 GROMACS 里跑。
- **PLUMED 2.9.2 从源码编译**：**这一步很关键**，conda-forge 那个版本的 `libplumedKernel.so` 模块残缺（没有 colvar/mapping/function 这些），直接用会让 `gmx mdrun -plumed` 报各种奇怪的错。后来这个 bug 被标成了 FP-020。
- **单 walker MetaD 提交**：Job 41514529，用的是 FUNCPATHMSD 写法（为什么用 FUNCPATHMSD 而不是 PATHMSD 下一页会讲）。

这页底部的代码块就是提交命令：

```
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp 8
```

`-ntmpi 1` 是因为 conda 装的 gmx 是 thread-MPI 版，不能跨节点。`-ntomp 8` 对应 Slurm 里 `--cpus-per-task=8`。

### English

Last week I finished the 500 nanosecond conventional MD production run on the AMBER side. For context on the scale: that's 250 million integration steps on a 39-thousand-atom solvated system at 350 kelvin — 350 being the thermophilic optimum for *P. furiosus*. The run took 71.5 wall-clock hours on a single A100 GPU and produced a 22-gigabyte NetCDF trajectory. After the MD finished I converted the system to GROMACS format with ParmEd and verified the conversion by running an AMBER-versus-GROMACS single-point energy comparison on the same coordinates — the two agreed to within one part in ten thousand, which confirmed that the force field parameters transferred cleanly. The reason we have to cross software ecosystems here is that the original SI used GROMACS plus PLUMED 2 for the MetaDynamics side, so strict replication means we can't just stay in AMBER. I also had to compile PLUMED 2.9.2 from source because the conda-forge build ships a broken shared-library module that I'll come back to at the end of the talk. And finally I submitted the single-walker MetaDynamics initial run, Job 41514529. That's the job I'll be discussing from here on.

---

## Slide 4 — This Week: Job 41514529 Result

### 中文

这是 initial run 的结果。Job 41514529 跑了 **46.3 / 50 ns** 就被 72 小时 walltime 杀了。但时间不是主要问题——主要问题是 **s(R) 这个 collective variable 整个 46 ns 都被困在 [7.77, 7.83] 这个极窄的区间**。

解释一下 s(R) 是什么：它是 path CV 的"进度坐标"，取值从 1（完全像 Open 端点）到 15（完全像 Closed 端点）。中间的值 7-8 代表 Partially Closed (PC) 状态。理论上 MetaDynamics 应该让系统沿 s 从 1 走到 15，扫完整条路径。

实际结果：

- **s 值始终在 7.77-7.83**——只有 0.06 个单位的范围
- **O 区间 (s<5) 的帧数: 0**
- **PC 区间 (5<s<10) 的帧数: 46304（100%）**
- **C 区间 (s>10) 的帧数: 0**
- 累积 bias 涨到了 **61.7 kJ/mol**，但系统死活推不出去

右边代码块是我写的快速统计脚本：

```python
import numpy as np
d = np.loadtxt('COLVAR', comments='#')
s = d[:,1]
print(f'O(s<5): {(s<5).sum()}'
      f' PC(5-10): {((s>5)&(s<10)).sum()}'
      f' C(s>10): {(s>10).sum()}')
# 输出: O: 0  PC: 46304  C: 0
```

`np.loadtxt` 读 COLVAR 文件（PLUMED 的标准输出），`comments='#'` 跳过表头。COLVAR 列是 `time, path.s, path.z, metad.bias`，所以 `d[:,1]` 是 s(R) 列。

**我一开始的判断是"系统卡在 PC basin 了"**——但这个判断是错的。下一页讲为什么。

### English

Job 41514529 ran for 46.3 out of 50 nanoseconds before hitting the 72-hour walltime. But the walltime wasn't actually the problem. The real issue was that the path progress coordinate `s(R)`, which has a theoretical range from 1 to 15 across Open to Closed, stayed confined to the extremely narrow interval 7.77 through 7.83 for the entire run. Every single one of the 46,304 COLVAR frames fell inside what the CV labeled as the Partially-Closed window. Not a single frame explored the Open or Closed regions. The accumulated bias potential on that narrow interval reached 61.7 kilojoules per mole, which for well-tempered MetaDynamics with a biasfactor of 10 is a significant investment, and yet the system showed no sign of moving. My initial interpretation was "the COMM domain is physically trapped in the Partially Closed basin, the barriers out are too high, we need to either run longer or crank up the bias." That interpretation was intuitive, it was consistent with PC being a deep catalytic intermediate in the original paper, and it turned out to be completely wrong — the system wasn't physically stuck at all, as the next three slides will show.

---

## Slide 5 — Why FUNCPATHMSD Instead of PATHMSD

### 中文

**这一页讲的是为什么我们一开始没用 SI 原版的 `PATHMSD`，而是换成了 `FUNCPATHMSD`。这个选择后面埋了一个 bug。**

SI 原文在 S3 页只说了用 "path collective variables" + GROMACS 5.1.2 + PLUMED2，**没给出具体的 PLUMED 输入文件**，也没说具体是 `PATHMSD` 还是 `FUNCPATHMSD`。这两个 action 在 PLUMED 里数学上等价，但语法不同：

**`PATHMSD`**（一体式，2 行搞定）：

```
path: PATHMSD REFERENCE=path.pdb LAMBDA=<λ>
```

它自己读多 model 的 PDB，内部算每个 frame 的 RMSD，然后组合成 s(R) 和 z(R)。非常简洁。

**`FUNCPATHMSD`**（拆分式，需要 16 行）：

```
r1: RMSD REFERENCE=frame_01.pdb TYPE=OPTIMAL
r2: RMSD REFERENCE=frame_02.pdb TYPE=OPTIMAL
... (共 15 行)
path: FUNCPATHMSD ARG=r1,r2,...,r15 LAMBDA=<λ>
```

它要求你自己分别算出 15 个 RMSD 值，然后把这些 RMSD 作为 ARG 喂给 `FUNCPATHMSD`。

**我们当时第一次试的是 `PATHMSD`——结果报错了**：

```
PLUMED: ERROR in input to action PATHMSD with label path :
number of atoms in a frame should be more than zero
```

当时的诊断是："PLUMED `PATHMSD` 在 `gmx mdrun` 接口下不认非连续编号的原子 serial"——因为我们的 path.pdb 里 atom serial 是 1614, 1621, 1643, ...（原始 AMBER 拓扑里 Cα 原子的实际索引，不连续）。

这个诊断**部分是对的**：当时 conda 版的 PLUMED 确实有 `libplumedKernel.so` 残缺的问题（标成 FP-020），确实通过 mdrun 接口跑 path CV 会失败。所以我们切换到 `FUNCPATHMSD`——但**保留了原来为 PATHMSD 算的 LAMBDA 值 3.391**。

这里埋的雷是：**切换 action 时没有重新审视 LAMBDA 的约定是否匹配**。下一页讲这个 bug 怎么被发现的。

右边代码块是当时坏掉的 plumed.dat 的关键行：

```
r1: RMSD REFERENCE=frames/frame_01.pdb TYPE=OPTIMAL   # 缺 SQUARED 关键字
...
path: FUNCPATHMSD ARG=r1,...,r15 LAMBDA=3.3910        # 差了 112 倍
```

底部脚注引用 SI 原话："The PLUMED2 software package together with the GROMACS 5.1.2 code were used" ——SI 就这么一句话，没给具体 action 名字。

### English

Quick flashback to how we got into this mess. The Maria-Solano 2019 SI says they used "path collective variables" with PLUMED 2 and GROMACS 5.1.2 — but it doesn't specify whether they used the built-in `PATHMSD` action or the more flexible `FUNCPATHMSD` action, and no PLUMED input file is provided in the supplement. These two actions are mathematically equivalent — they both implement the same Branduardi 2007 path-CV formula — but the API is very different. `PATHMSD` takes a single multi-model PDB and does the whole thing in one line, with a second line for the metadynamics itself. `FUNCPATHMSD` is a lower-level action that makes you compute 15 per-frame RMSDs yourself using 15 separate `RMSD` actions, and then feed those 15 values in as explicit arguments — that's 17 lines instead of 2. We first tried `PATHMSD`, but we hit a parse error that, at the time, we attributed to non-sequential atom serial numbers in our reference PDB. So we switched to `FUNCPATHMSD` as a workaround and kept going. What I did not do — and this is the critical step where the bug was seeded — is re-derive the `LAMBDA` parameter for the new action. I kept the old number, 3.391, and assumed the math was the same. It wasn't, and that single lazy assumption is what killed 46 nanoseconds of HPC time.

---

## Slide 6 — Self-Consistency Test Reveals the Bug

### 中文

**这是我发现 bug 的关键测试，也是本次汇报最重要的一页。**

原理很简单：path CV 的公式是

$$
s(R) = \frac{\sum_{i=1}^{15} i \cdot e^{-\lambda d_i}}{\sum_{i=1}^{15} e^{-\lambda d_i}}
$$

其中 $d_i$ 是当前构象和第 i 个参考帧之间的距离。**公式是自包含的**——如果我把第 8 帧本身作为"当前构象"喂进去，$d_8=0$，$e^{-\lambda \cdot 0}=1$，而其他帧 $d_i$ 非零，权重应该远小于 1。加权平均出来应该是 **s ≈ 8**。

对 15 个参考帧做一遍同样的检验，理论上：

- frame_01 → s = 1
- frame_02 → s = 2
- ...
- frame_15 → s = 15

**这是 path CV 最基础的自一致性要求**。如果连自己的参考帧都认不出来，CV 就是废的。

我用 Python 做了这个测试（脚本在 `01_self_consistency_test.py`）。结果：

| Frame | 期望 s | **实测 s (坏的 λ=3.391)** | 修复后 s (λ=379.77) |
| ----- | ------ | -------------------------------- | -------------------- |
| 1     | 1      | **4.02**                   | 1.09                 |
| 8     | 8      | 8.00 ✓（对称必然）              | 8.00                 |
| 15    | 15     | **11.98**                  | 14.91                |

frame_1 应该给出 s=1，实测给了 4.02。frame_15 应该给出 15，实测给了 11.98。**整条 [1, 15] 的路径被压缩成了 [4, 12]**。中间的 frame_8 给了 8 是因为 15 帧的对称性，这个值是欺骗性的。

这就解释了为什么 COLVAR 里 s 一直在 7.79——因为 CV 数学上就只能表达 4 到 12 之间的值，并且因为 ADAPTIVE=GEOM 的 kernel 太宽，实际输出还会进一步向中间的 8 坍缩。**系统可能物理上根本不在 PC basin，而是在 O basin，只是坏的 CV 把 O 也翻译成了 s≈7.8**。

脚本代码块（简化版）：

```python
# 读 15 个参考帧
frames = load_models("path.pdb")
# 对每个参考帧自己喂回 CV 公式
for i in range(15):
    d = np.array([kabsch_rmsd(frames[i], frames[j]) for j in range(15)])
    w = np.exp(-LAMBDA * d**2)  # RMSD² 作为距离度量
    s = sum((j+1)*w[j] for j in range(15)) / w.sum()
    print(f"frame_{i+1} → s = {s:.2f}")
```

`kabsch_rmsd` 是标准的 Kabsch 最优对齐 RMSD。公式里的 `d**2` 是因为 path CV 的标准约定用 MSD（平方距离）作为衰减指数。这 30 秒的测试就能抓到 3 天 HPC 时间才能暴露的 bug。

### English

Here's the test that caught the bug. The path-CV formula is self-consistent: if you feed reference frame number `i` back into the CV, you should get `s = i`, because the distance to frame `i` itself is zero. I ran this test on all 15 frames. With the old lambda of 3.391, frame 1 returned `s = 4.02` instead of 1, and frame 15 returned 11.98 instead of 15. The whole path collapsed into the interval from 4 to 12. Frame 8 happened to return 8, but only because of the symmetry of a 15-frame path — that number is misleading. The simulation was showing `s` around 7.79 not because the system was physically stuck in PC, but because the broken CV could only express values in that narrow compressed range. A 30 second Python script would have caught this before we spent three days of HPC time on it.

---

## Slide 7 — Root Cause: MSD Convention Mismatch

### 中文

**这一页讲根因。差的这 112 倍从哪来。**

Path CV 的 LAMBDA 有一个标准公式（PLUMED 文档原文）：

> "LAMBDA is generally calculated as **2.3 / `<rmsd>`²** where rmsd is calculated as the distance between a frame in the reference and the next one."
> — PLUMED users mailing list + PLUMED PATHMSD docs

这里的 `<rmsd>²` 就是相邻 frame 之间的 **MSD**（Mean Squared Displacement）。"Mean" 这个字是关键——它指的是**对所有原子做平均**，不是对所有原子做总和。

我们的脚本 `generate_path_cv.py` 里有一个 `calculate_msd` 函数，它是这么写的：

```python
def calculate_msd(coords1, coords2):
    diff = coords1 - coords2
    return np.sum(diff**2)   # ← 错在这里
```

`np.sum` 是**所有原子位移平方的总和**，不是平均值。对 112 个 Cα 原子，相邻 frame 的总和是 **67.83 Å²**，于是：

```
λ_broken = 2.3 / 67.83 = 0.0339 Å⁻²
        = 3.391 nm⁻²  (GROMACS 要求 nm 单位，× 100)
```

但 PLUMED 的 `RMSD` action 按定义输出的是 **per-atom 的 RMSD**：

```
RMSD_plumed = sqrt( (1/N_atoms) × Σ |Δrᵢ|² )
```

所以 PLUMED 内部用的 MSD 是 `(1/N_atoms) × Σ|Δrᵢ|²`，是**平均**不是**总和**。对我们这套 112 原子的 path，per-atom MSD 是 **0.6056 Å²**，所以：

```
λ_correct = 2.3 / 0.6056 = 3.798 Å⁻²
         = 379.77 nm⁻²  (× 100)
```

两个值相差恰好 **N_atoms = 112 倍**。

左边列公式推导：

```
错的: MSD = np.sum  →  λ = 2.3/67.83 = 3.391 nm⁻²
对的: MSD = np.mean →  λ = 2.3/0.6056 × 100 = 379.77 nm⁻²
Ratio: 379.77 / 3.391 = 112 = N_atoms
```

右边列效果：

```
坏 kernel (adjacent):  exp(-3.391 × 0.0778)  = exp(-0.264) = 0.77
对 kernel (adjacent):  exp(-379.77 × 0.006056) = exp(-2.3) = 0.10
```

0.77 意味着相邻 frame 的权重差不多大，所有 15 帧都在加权平均里"平等"贡献，所以 s 坍缩到中间值。0.10 是 path CV 的"健康"kernel 值（来自 Branduardi 2007 原 paper 的推荐）——相邻 frame 有清晰的区分度。

代码修复（右下角代码块）：

```python
# Bug (generate_path_cv.py 第 296 行):
def calculate_msd(coords1, coords2):
    return np.sum(diff**2)   # sum, not mean!
# Fix:
    return np.mean(np.sum(diff**2, axis=1))  # per-atom mean
```

脚注引用 PLUMED 文档和 SI：

> "LAMBDA is generally calculated as 2.3/`<rmsd>`**2" — plumed.org/doc-v2.9
> SI S3: "λ = 2.3 × inverse of MSD"

### English

Here's the root cause. The canonical formula for lambda in path CVs is `2.3 divided by mean-squared displacement`. The word "mean" is critical — it means averaged over atoms, not summed. Our script used `numpy.sum`, which gives the total squared displacement across all 112 C-alpha atoms (67.8 square angstroms). That gave lambda equal to 3.391 per nm squared. But PLUMED's RMSD action returns the per-atom mean, not the total sum, so the correct lambda should be computed from the per-atom mean MSD of 0.606 square angstroms, giving 379.77 per nm squared. The two values differ by exactly the number of atoms, 112 times. With the broken lambda, the adjacent-frame kernel weight was 0.77 instead of the canonical 0.10, so the CV couldn't distinguish frames. One `sum` that should have been a `mean`.

---

## Slide 8 — PLUMED Driver Re-Analysis

### 中文

**这一页是修复的验证。**

既然知道 bug 在哪，我不需要重新跑 46 ns 的 MD 来验证修复——PLUMED 有一个工具叫 `plumed driver`，可以在**离线**模式下对已有的轨迹文件重新计算 CV 值。这个工具比重跑 MD 快几个数量级（1.3 秒 vs 3 天）。

具体操作：

```bash
plumed driver \
    --plumed plumed_fixed.dat \
    --mf_xtc metad.xtc \
    --timestep 0.002 \
    --trajectory-stride 5000
```

- `--plumed plumed_fixed.dat`：用的是修复版（加了 `SQUARED` 关键字 + LAMBDA=379.77）
- `--mf_xtc metad.xtc`：读取 Job 41514529 产出的 xtc 轨迹
- `--timestep 0.002`：GROMACS 的时间步（单位 ps）
- `--trajectory-stride 5000`：告诉 driver xtc 每 5000 MD steps 才写一帧（= 每 10 ps 一帧），否则它会误算时间

启动时 PLUMED 打印了：

```
PLUMED:   lambda is 379.770000
PLUMED:   Consistency check completed! Your path cvs look good!
```

**第二行是 PLUMED 自带的 path CV 检查通过标志**。这条消息只在 driver 模式显示，`gmx mdrun` 接口不显示它——这也解释了为什么当时 Job 41514529 的 bug 没被 PLUMED 自己抓到。

结果：

- 新的 COLVAR 显示 **s(R) ≈ 1.04-1.06**，整段 46 ns 都是这个值
- 97.5% 的帧在 O basin（s < 5）
- 0 个帧在 PC 或 C

**物理上系统一直在 O basin 里**，根本没被推出去。原来坏 CV 显示的 s≈7.79 完全是数学伪影。为什么 MetaD 推不动？因为坏 CV 的梯度 `ds/dx` 几乎为零（所有构象的 s 值都被压缩到 7.7-7.8），梯度为零意味着 bias 转化成的物理力几乎为零，**46 ns 的 MetaD 实际上等价于 46 ns 的无偏置 MD**。

脚注：`rerun/COLVAR_rerun_fixed | plumed driver on Longleaf single_walker/`。

### English

Once I knew what the bug was, I didn't need to re-run 46 nanoseconds of molecular dynamics to verify the fix. PLUMED ships with a tool called `plumed driver` that takes an existing trajectory file and re-computes collective variables offline. It took 1.3 seconds. With the corrected lambda, PLUMED printed "Consistency check completed, your path cvs look good" — and this message only shows in driver mode, which is why our original `gmx mdrun` submission never flagged the bug. The new COLVAR showed `s` around 1.05 for the entire 46 nanoseconds — the system was actually in the Open basin the whole time. It wasn't stuck in PC; the broken CV was just mapping everything to 7.79. And because the CV gradient collapsed along with the CV itself, the bias potential produced essentially no physical force on the atoms. The 46 nanoseconds of "metadynamics" was effectively unbiased MD.

---

## Slide 9 — PATHMSD Actually Works (Re-diagnosis of FP-020)

### 中文

**这一页是今天最新的发现——比昨天的 FUNCPATHMSD 修复更深一层的修正。**

当时（上周）我们放弃 `PATHMSD` 换 `FUNCPATHMSD` 的理由是 FP-020 记录的两条：

1. conda 版 PLUMED 的 `libplumedKernel.so` 模块残缺
2. "`PATHMSD` 在 `mdrun` 中只认连续编号的 PDB"

**第一条是对的。第二条（今天发现）是错的**。

今天我用**源码编译版** PLUMED 2.9.2 + `plumed driver` + Longleaf 上原来的 path.pdb（非连续 serial 1614, 1621, 1643, ...）直接测试 `PATHMSD`，**一次就通过了**。没有报错，读取 15 个 frame 每个 112 原子全部正确。

所以当时我们看到的 "PATHMSD 失败" 的真实原因是 **conda 版 .so 残缺** + **path.pdb 尾部多一个 `END` 行**（这是今天新发现的 FP-023——删掉 trailing END 之后 PATHMSD 立刻就工作了）。**跟 serial 是否连续无关**。

**关键含义**：如果我当时直接用源码编译版 PLUMED + PATHMSD，整个 FP-022（FUNCPATHMSD LAMBDA convention 错误）本来就不会发生。FP-022 是由 FP-020 的误诊引起的衍生 bug。

中间表格是 FUNCPATHMSD 修复版 vs PATHMSD 原版（SI 一致）的对比：

| 指标                 | FUNCPATHMSD + SQUARED（昨天的修复） | **PATHMSD（今天验证，匹配 SI）**    |
| -------------------- | ----------------------------------- | ----------------------------------------- |
| path CV 代码行数     | 17（15 RMSD + FUNCPATHMSD + METAD） | **2**（PATHMSD + METAD）            |
| 46 ns 上 s(R) 范围   | [1.04, 1.06]                        | **[1.00, 1.70]**                    |
| COLVAR 中的 NaN 帧数 | **116 / 4631 (2.5%)**         | **0**                               |
| z(R) 范围            | 1.45 – 1.92 nm²（数值异常大）     | **0.004 – 0.084 nm²（物理合理）** |
| 和 SI 协议的匹配度   | 否（SI 用 "path CVs"）              | **是**                              |

**PATHMSD 各项指标都更好**：更简洁、更稳定（0 NaN）、z 值更物理。选择回到 PATHMSD 几乎没有理由不做。

底部代码块是 PATHMSD 的测试命令：

```bash
# Longleaf 上的 PATHMSD 驱动测试（offline，1.3 秒）
plumed driver --plumed plumed_pathmsd_test.dat \
    --mf_xtc metad.xtc --timestep 0.002 --trajectory-stride 5000
# 输出: Found 15 PDBs containing 112 atoms each → 无错误
```

脚注：`Longleaf single_walker/rerun/COLVAR_pathmsd | FP-020 updated in failure-patterns.md | Google Groups plumed-users: 'λ = 2.3/<rmsd>^2, × 100 for GROMACS'`

### English

This is the most recent finding, from this morning. We had originally abandoned `PATHMSD` because we thought it couldn't handle our non-sequential atom serials. Testing today with the source-compiled PLUMED 2.9.2 proved us wrong. `PATHMSD` reads our reference PDB cleanly, all 15 frames and 112 atoms, with no errors. The original problem was a combination of the broken conda `.so` library and a stray trailing `END` line in the PDB file that made PLUMED try to parse an empty sixteenth frame. The atom serials were never the issue. The comparison table on the right shows that `PATHMSD` is strictly better than the `FUNCPATHMSD` workaround: two lines of code instead of seventeen, zero NaN frames instead of 116, and physically reasonable `z(R)` values. I'm switching the production setup back to `PATHMSD`, which matches the SI protocol exactly.

---

## Slide 10 — Plan & Next Steps

### 中文

**最后这一页是下一步的计划 + 两个技术细节可能会被追问。**

在讲计划之前，先把两个可能被追问的技术细节过一下——这两个我在 debug 过程中反复遇到，PI 或者同组的人很可能问：

**问题 1：为什么 LAMBDA 要 ×100？**

因为 **Å 和 nm 的单位换算在 "距离的平方的倒数" 上变成 ×100**。
- `λ` 的单位是 `[距离]⁻²`（因为 `exp(-λ·MSD)` 里 MSD 是距离平方）
- 1 Å = 0.1 nm，所以 `1 Å⁻² = 100 nm⁻²`
- 我们用 Å 的坐标算出 `λ = 3.798 Å⁻²`
- GROMACS 内部用 nm，所以喂给 PLUMED 的 LAMBDA 必须是 `3.798 × 100 = 379.77 nm⁻²`
- 这个 ×100 很容易忘，而且 PLUMED 不会给你任何警告——只会静默地用错了的 λ 跑完整场模拟

**问题 2：PLUMED 为什么会出 bug？**

**conda-forge 版 PLUMED 2.9.2 的 `libplumedKernel.so` 是有残缺的构建**。具体说：
- PLUMED 的模块化设计：核心 action（比如 `PATHMSD`、`FUNCPATHMSD`、`METAD`）编译到 `libplumedKernel.so` 里
- conda-forge 的打包脚本在构建时某些 CMake flag 没传对，导致 path CV 相关的 symbol 没进去
- 结果：`gmx mdrun -plumed plumed.dat` 启动时，PLUMED 尝试 dlopen 这些 action，load 失败，报一个完全误导性的错（类似 "action not recognized"）
- 我当时把这个错归因为"PATHMSD 不认非连续 atom serial"——这个归因是错的
- **修法**：从 PLUMED 2.9.2 tarball 用 CMake 源码编译一份，用 `PLUMED_KERNEL=/work/.../plumed-2.9.2/lib/libplumedKernel.so` 指向它
- 这不是 PLUMED 本身的 bug，是 conda-forge packaging 的 bug

这两个合起来就是 FP-020 的真正内容。

---

**本周已完成**：

- ✓ PATHMSD 用 plumed driver 在 Longleaf 验证通过
- ✓ 更新 6-stage pipeline state（Stage 4 unblocked）
- ✓ 记录 FP-020 更正 + 新增 FP-023（path PDB 尾部 END 陷阱）
- ✓ **把 PATHMSD plumed.dat 部署到 Longleaf production 目录**（今天下午）
- ✓ **备份旧 Job 41514529 数据到 `archive_FP022_broken_2026-04-09/`**
- ✓ **重提交 50 ns initial run — Job 42679152，当前 RUNNING**（在 `c0301` 节点，path.sss ≈ 1.04，bias 正在累积，CV 起步健康度确认）

**下周**：

- [ ] 等 Job 42679152 完成（~3 天 HPC 时间）
- [ ] 跑 `plumed sum_hills --kt 2.908` 重构 FES
- [ ] 用 `analyze_fes.py` 对比 JACS 2019 参考值（ΔG(C-OPC) ≈ 5 kcal/mol，ΔG‡(PC→C) ≈ 6 kcal/mol）
- [ ] 如果收敛了 → 从轨迹里提取 10 个覆盖 O / PC / C 的 snapshots
- [ ] 用这 10 个 snapshots 做 SI 协议的 10-walker production（每个 walker 50-100 ns）

**目标：两周内产出可以和 JACS 2019 Figure 2a 对比的 FES**。

底部代码块是最终的 plumed.dat（完整 2 行的 PATHMSD 版本）：

```
path: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77
metad: METAD ARG=path.sss,path.zzz SIGMA=0.05 ADAPTIVE=GEOM \
       HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
PRINT ARG=path.sss,path.zzz,metad.bias FILE=COLVAR STRIDE=500
```

每个参数的来源和含义：

- **`PATHMSD REFERENCE=path_gromacs.pdb`**：参考路径文件，15 个 MODEL 合在一个 multi-model PDB 里。Atom serial 非连续（1614, 1621, ...），对应原始 AMBER 拓扑里 COMM 域 Cα 原子的真实索引。PLUMED 用这些 serial 号从 MD 轨迹里选对应原子做 RMSD。
- **`LAMBDA=379.77`**：单位 nm⁻²。公式 `λ = 2.3 / <rmsd>²`（per-atom MSD，Å² 单位）然后 × 100 转到 GROMACS 的 nm² 单位。对我们的 15 帧路径，per-atom `<rmsd>² = 0.6056 Å²`，所以 `λ = 2.3/0.6056 × 100 = 379.77`。
- **`ARG=path.sss,path.zzz`**：PATHMSD 输出两个 component：`sss`（沿路径进度）和 `zzz`（离路径的距离）。MetaD 同时在这两个维度上加 bias。
- **`SIGMA=0.05`**：Gaussian hill 的初始宽度。ADAPTIVE=GEOM 之后会动态调整，所以这个值只是种子值。
  - ⚠️ **2026-04-15 UPDATE (FP-024)**：当时说"只是种子值不影响"的这个说法是错的。实际上 ADAPTIVE=GEOM 下 SIGMA=0.05 会让 sigma_s 塌到 ≤0.07（path 轴 <0.5%），Gaussian 堆成针尖困在 s=1。正确用法需要加 `SIGMA_MIN=0.3,0.005 SIGMA_MAX=1.0,0.05`。详见 failure-patterns.md FP-024。
- **`ADAPTIVE=GEOM`**：自适应 Gaussian 宽度（几何平均方案）。来源：SI S3: "adaptive Gaussian width scheme"。
- **`HEIGHT=0.628`**：Gaussian hill 初始高度，单位 kJ/mol。SI 原值 0.15 kcal/mol，乘以 4.184 换成 kJ/mol。
- **`PACE=1000`**：每 1000 个 MD step 沉积一个 hill。MD timestep 是 0.002 ps，所以每 2 ps 一个 hill。SI 原文 "deposited every 2 ps"。
- **`BIASFACTOR=10`**：Well-tempered MetaD 的 γ 因子。SI 原值就是 10。
- **`TEMP=350`**：MetaD 内部用的温度（要和 .mdp 里的 `ref_t` 严格一致）。SI 原值 350 K（`P. furiosus` 嗜热古菌的最适温度）。
- **`FILE=HILLS`**：hill 记录文件，后续用 `plumed sum_hills` 重构 FES。
- **`STRIDE=500`**：COLVAR 每 500 step 输出一行（每 1 ps 一行）。

脚注：`replication/metadynamics/single_walker/plumed.dat (master branch) | SI S4 10-walker protocol description`

### English

Before wrapping up I want to flag two technical details in case you ask. First, why the factor of one hundred on lambda. The canonical path-CV formula gives lambda in inverse angstroms squared, but GROMACS works internally in nanometers. Since lambda has units of inverse distance squared and one angstrom is a tenth of a nanometer, the conversion factor is a hundred, not ten. I computed lambda as 3.798 in angstrom units, multiplied by one hundred, and got 379.77 in nanometer units. PLUMED does not warn you if you forget this factor — it will just silently run with a lambda that is a hundred times too small. Second, why the PLUMED build mattered. The conda-forge build of PLUMED 2.9.2 ships a `libplumedKernel.so` that is missing some of the path-CV symbols due to a packaging bug in the CMake flags. When `gmx mdrun` tries to load `PATHMSD` at runtime, the symbol is not found and mdrun crashes with a misleading error. I originally blamed non-sequential atom serials for this, but the real fix was to compile PLUMED 2.9.2 from the official tarball and point `PLUMED_KERNEL` at the source-built library. This is a packaging bug, not a PLUMED bug. Both of these together are what FP-020 really was.

Moving on to the plan. This week I verified `PATHMSD` works, corrected the FP-020 and FP-022 entries, and — as of this afternoon — I have already deployed the new two-line `PATHMSD` plumed.dat to Longleaf, archived the broken Job 41514529 data, and resubmitted the initial run. The new job, 42679152, is currently running on node `c0301`. First-minute health checks all passed: PATHMSD kernel loaded cleanly, the starting `path.sss` is around 1.04 which matches the offline rerun prediction, and the bias is accumulating normally. The run should finish in about three days of wall time. Next week, assuming the trajectory covers Open, PC, and Closed, I'll run `plumed sum_hills` with the correct kT of 2.908 kJ/mol, compare the resulting FES against the JACS 2019 reference values of roughly 5 kcal/mol for delta-G and 6 kcal/mol for the PC to C barrier, and then extract ten snapshots to launch the ten-walker production run. The target is to have a free energy surface comparable to Maria-Solano 2019 Figure 2a within two weeks. Questions?

---

## 附录：如果被问到的常见问题

### Q: 为什么是 2.3 这个魔数？

A: 来自 path CV 最初的 Branduardi 2007 paper 的建议：kernel 权重在相邻 frame 应该衰减到 exp(-2.3) ≈ 0.10。这个值让路径上的每个"桩子"清晰可分，同时保持足够的平滑性。2.3 ≈ ln(10)。

### Q: 为什么 SI 的 "80" 让你困惑？

A: SI 原句是 "λ = 2.3 × inverse of mean square displacement between successive frames, 80"。这个 "80" 可能是 (a) MSD=80 Å² (total SD 约定)，(b) 80 个 frame，或 (c) 一个脚注/引用编号。我们自己算 total SD 是 67.83 Å²，和 80 相差 15%——可能是路径端点选择不同导致的。这个歧义本身不影响修复，因为我们用 PLUMED 自己的约定算 LAMBDA 更可靠。

### Q: 为什么你现在才发现 PATHMSD 本来就能用？

A: 上周切换到 FUNCPATHMSD 的时候用的是 conda 版 PLUMED，它的 `.so` 确实残缺（FP-020）。当时同时遇到了 `.so` 问题 + path.pdb 尾部 END 问题，两个问题叠加表现为 "PATHMSD failed"，我们错误地归因于"非连续 serial"。今天用源码版 PLUMED + 去掉 trailing END 后一次就过，证明当时的归因是错的。

### Q: 为什么 FUNCPATHMSD 版本的 z(R) 值那么大（1.5-1.9 nm²）？

A: 还没完全搞清楚。FUNCPATHMSD 的 z 公式理论上和 PATHMSD 相同，但实际输出范围相差两个数量级。可能是 PLUMED FUNCPATHMSD 内部的数值实现对 sharp kernel 有边界问题（2.5% NaN 帧也支持这个猜想）。换回 PATHMSD 之后 z ∈ [0.004, 0.084] 完全合理，这个问题就不再 block 我们了。
