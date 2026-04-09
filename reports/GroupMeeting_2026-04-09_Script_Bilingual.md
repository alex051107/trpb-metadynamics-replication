# Group Meeting 2026-04-09 — 讲稿（中英对照）

> **使用说明**
> - **中文部分**：给自己看的超详细版，按时间线展开整个 debug 过程——看到了什么、推理了什么、哪里推错了、怎么纠正的。每个数字、每行代码、每个判断节点都讲清楚来源。
> - **英文部分**：明天 lab meeting 上要说的版本，讲清楚逻辑链但更简洁。
> - 讲稿顺序和 10 页 slides 一一对应。

---

## Slide 1 — Title

### 中文

开场。标题是 "TrpB MetaDynamics Benchmark — Weekly Progress Report"。这周的主线是一个 bug hunt——从看到一个"系统卡住"的现象开始，经过三轮错误诊断才找到真正的根因，而真正的根因又带出一个更深的发现：我们一周前切换 PLUMED action 的那个决定本身就是误诊引起的。

我会按**时间线**讲：先说上周的起点，然后按**每一个决策节点**往下走——我看到了什么、我怎么推理的、我为什么推错、后来是什么让我意识到错了。这样大家能看到完整的思考过程，而不是只看到最终结论。

### English

Good morning. Today's talk is a bug hunt story. I'll walk through the week chronologically, showing each decision point in the debugging process: what I saw, how I reasoned, where my reasoning was wrong, and what corrected it. The goal is for you to see the full thinking chain, not just the final answer.

---

## Slide 2 — Background

### 中文

快速背景，一句话：我在复刻 Osuna 组 2019 JACS 的 TrpB MetaDynamics 协议，给 Amin 的 STAR-MD benchmark 提供 ground truth FES，同时给 Raswanth 的 GenSLM + GRPO pipeline 当 conformational reward 信号。用的协议是 SI 原文：initial run → 从里面提 10 个 snapshots → 10 walkers × 50-100 ns production。我这周还在 initial run 这一步。

### English

Quick context. I'm replicating Maria-Solano 2019 JACS as a conformational baseline for two downstream consumers: Amin's STAR-MD benchmark needs ground truth FES, and Raswanth's GenSLM GRPO pipeline needs conformational reward signals. The SI protocol is initial run, extract ten snapshots, run a ten-walker production with fifty to one hundred nanoseconds per walker. I'm still at the initial-run stage.

---

## Slide 3 — Last Week's Progress

### 中文

先说上周完成的事，作为这周的起点：

1. **500 ns conventional MD 跑完了**（Job 40806029，71.5 小时）。全部参数来自 SI：ff14SB 力场，TIP3P 水，350 K，2 fs 时间步，NVT。目的是给 MetaD 提供一个已经充分平衡的起始构象。
2. **AMBER → GROMACS 格式转换**。用 ParmEd 工具，39,268 原子全部核对过。为什么要转？因为 SI 原文用 GROMACS 5.1.2 + PLUMED2 跑 MetaD，我们必须在 GROMACS 里跑（strict replication 原则）。
3. **PLUMED 源码编译**。这步当时是被迫的——conda-forge 装的 PLUMED 2.9.2 的 `libplumedKernel.so` 有模块残缺（少 `colvar/` `mapping/` `function/` 这些），直接用会让 `gmx mdrun -plumed` 启动时就报 `Unknown action` 错。这个 bug 被记作 **FP-020**，我们用源码编译版绕过去了。**这个"绕过"后面会回来咬我们**。
4. **单 walker MetaD 提交**：Job 41514529，用的 `FUNCPATHMSD` 写法（不是 SI 可能用的 `PATHMSD`）。**这个选择也是关键——下一张 slide 会讲为什么选 FUNCPATHMSD，以及这个选择埋下的雷**。

底部代码块是提交命令：
```
gmx mdrun -deffnm metad -plumed plumed.dat -ntmpi 1 -ntomp 8
```
`-ntmpi 1 -ntomp 8` 是因为 conda 装的 gmx 是 thread-MPI 版本，不支持跨节点 MPI，只能单节点开 8 个 OpenMP 线程。对应 Slurm 里的 `--cpus-per-task=8`。

**上周结束时我的心态**：一切就绪，等 Job 结果。我当时完全没意识到 plumed.dat 里有问题。

### English

Last week I finished the 500 nanosecond conventional MD run, converted it from AMBER to GROMACS format, compiled PLUMED 2.9.2 from source because the conda build had broken modules — that's FP-020, and it will come back to bite us — and submitted the single-walker MetaDynamics job. I used `FUNCPATHMSD` in the PLUMED input, not `PATHMSD` like the SI probably used, for reasons I'll explain on the next slide. At the end of last week I thought everything was ready and I was just waiting for the job to finish.

---

## Slide 4 — This Week: What I Saw First

### 中文

**这周一的第一件事：我去 Longleaf 上检查 Job 41514529 的进度**。这是整个 bug hunt 的起点。

我检查了几样东西：

**1. Job 状态**：
```
squeue -u liualex
```
显示 job 已经跑完（被 72 小时 walltime kill），不是干净完成的 50 ns。时间：跑到了 46.3 ns 就被杀了。第一反应：walltime 设短了，下次多订点时间就行。

**2. COLVAR 文件的时间序列**：
这才是真正让我皱眉头的地方。COLVAR 里记录的是 PLUMED 每 500 步输出的 CV 值和 bias 值。列的含义是 `time, path.s, path.z, metad.bias`。

我写了一个快速统计脚本：
```python
import numpy as np
d = np.loadtxt('COLVAR', comments='#')
t = d[:,0]; s = d[:,1]; z = d[:,2]; bias = d[:,3]

print(f'Time range: {t.min():.0f}-{t.max():.0f} ps')
print(f's(R) range: [{s.min():.3f}, {s.max():.3f}]')
print(f'z(R) range: [{z.min():.3f}, {z.max():.3f}]')
print(f'Frames in O (s<5):  {(s<5).sum()}')
print(f'Frames in PC (5-10): {((s>=5)&(s<10)).sum()}')
print(f'Frames in C (s>=10): {(s>=10).sum()}')
print(f'Bias range: [{bias.min():.1f}, {bias.max():.1f}] kJ/mol')
```

输出：
```
Time range: 0-46303 ps
s(R) range: [7.770, 7.833]   ← 只有 0.06 个单位！
z(R) range: [0.427, 0.668]
Frames in O  (s<5):  0
Frames in PC (5-10): 46304  ← 100%
Frames in C  (s>=10): 0
Bias range: [0.0, 61.7] kJ/mol
```

**这组数字同时告诉我三件事**：
- **s 值几乎没动**：0.06 个单位的范围——MetaDynamics 本来是要扫 1 到 15 的，结果只在 7.8 附近晃。
- **bias 涨到了 61.7 kJ/mol**：MetaD 一直在堆沙子，堆了一堆，说明它在努力推——但推不动。
- **100% 的帧都在 PC 区间**：这不是说 "偶尔去了 PC 又回来了"，是 **从 t=0 开始就一直在 PC**。

**这是我的第一个观察**。接下来我要做推理。

### English

First thing this week: I checked Job 41514529 on Longleaf. Three observations: the job got killed by walltime at 46.3 nanoseconds, the path progress coordinate `s(R)` was confined to the interval 7.77 through 7.83 for the entire run, and the accumulated metadynamics bias grew to 61.7 kilojoules per mole but the system never moved. All 46,304 output frames were in the PC window — none in Open, none in Closed. That's what I saw. The question was what it meant.

---

## Slide 5 — First Two Wrong Hypotheses

### 中文

**看到那组数据之后，我的第一反应是物理解释**。我完全没想过 CV 可能是坏的——我默认 CV 是对的，因为 plumed.dat 已经跑了几天没报错。

**假设 1（周一上午）：PC basin 太深，MetaD 推不动。**

逻辑是：
- COLVAR 显示系统 100% 在 PC 区域 → 物理上系统一定在 PC basin
- Bias 涨到 61.7 kJ/mol → 已经堆了很多 hill 但还推不出去 → 一定是能垒很高
- **结论：PC 是一个很深的坑，需要更大的 HEIGHT 或更多的 walker 才能翻出去**

当时我想的是："我只要换成 10-walker production，或者把 initial run 延长到 100 ns，就能解决。" 这个判断完全基于"CV 是对的"这个默认假设。

**假设 2（周一下午）：ADAPTIVE=GEOM 的 sigma 坍缩了**。

PLUMED 的 well-tempered MetaD 有一个 `ADAPTIVE=GEOM` 选项，让高斯 hill 的宽度根据局部 CV 波动自动调节。我当时的担心是：系统在 PC 里反复震荡，局部 CV 变化很小，自适应算法会把 sigma 调到很小——这样堆出来的 hill 又窄又高，只能填当前这一小块，根本推不到隔壁的坑。

为了验证这个假设，我去 HILLS 文件里看 sigma 值：
```python
hills = np.loadtxt('HILLS', comments='#')
sigma_s = hills[:,3]  # sigma for path.s column
sigma_z = hills[:,4]  # sigma for path.z column
print(f'sigma_s: [{sigma_s.min():.5f}, {sigma_s.max():.5f}]')
print(f'sigma_z: [{sigma_z.min():.5f}, {sigma_z.max():.5f}]')
```

输出：
```
sigma_s: [0.00155, 0.00168]  ← 稳定在 ~0.0016
sigma_z: [0.00472, 0.00473]  ← 几乎完全稳定
```

**这个观察推翻了假设 2**：sigma 在整个 46 ns 里都是稳定的，没有坍缩。如果 ADAPTIVE 坍缩了，sigma 值会随时间单调下降到零。所以不是 sigma 的问题。

**假设 1 仍然在桌子上**。我当时基本上相信了 "PC basin 就是很深" 这个结论，准备直接上 10-walker。

### English

When I first saw the data, I assumed the CV was correct and started looking for a physical explanation. My first hypothesis was that the PC basin was genuinely very deep and MetaDynamics couldn't push the system out — which would mean just launching more walkers would solve it. My second hypothesis was that `ADAPTIVE=GEOM` had collapsed the Gaussian width, so each hill was too narrow to reach neighboring basins. I checked the HILLS file for the sigma values — they were stable at about 0.0016, not decreasing. So sigma collapse was ruled out. Hypothesis one was still my working theory. And I was about to launch ten more walkers when a review pushed me to think harder.

---

## Slide 6 — The Self-Consistency Test (When I Knew the CV Was Broken)

### 中文

**这是整个 debug 过程的 turning point**。

周二我把当时的诊断（"PC basin 太深，上 10-walker"）发给 Codex 做 skeptical review。Codex 回来的反馈里有一句关键的话，大意是："你假设 CV 是对的。但你有没有验证过 CV 能正确识别自己的参考帧？"

这句话点醒了我。**Path CV 有一个内建的自一致性要求**：

$$s(R) = \frac{\sum_{i=1}^{15} i \cdot e^{-\lambda d_i^2}}{\sum_{i=1}^{15} e^{-\lambda d_i^2}}$$

其中 $d_i$ 是当前构象和第 i 个参考帧的 RMSD。**公式是自包含的**——如果我把第 8 帧本身作为"当前构象"喂进公式：
- $d_8 = 0$（自己和自己的 RMSD 是零）
- $e^{-\lambda \cdot 0} = 1$ （权重最大）
- 其他 $d_i$ 非零，$e^{-\lambda d_i^2}$ 远小于 1
- 所以加权平均 ≈ 8

**对 15 个参考帧做一遍同样的检验，理论上应该**：
```
frame_01 → s = 1
frame_02 → s = 2
...
frame_15 → s = 15
```

这是 path CV 最基础的合规性测试。如果连自己的参考帧都认不出来，CV 就是数学上坏的，后面所有基于它的物理解释都不成立。

我写了一个 Python 脚本 `01_self_consistency_test.py` 做这个测试。核心逻辑：

```python
import numpy as np

def load_models(pdb_path):
    """读取 multi-model PDB，返回 15 个 (112, 3) 的坐标数组"""
    models = []
    current = []
    for line in open(pdb_path):
        if line.startswith("MODEL"):
            current = []
        elif line.startswith("ENDMDL"):
            models.append(np.array(current, dtype=float))
        elif line.startswith("ATOM") and " CA " in line:
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            current.append([x, y, z])
    return models

def kabsch_rmsd(A, B):
    """Best-fit RMSD between two (N,3) coordinate sets"""
    A = A - A.mean(axis=0)
    B = B - B.mean(axis=0)
    H = A.T @ B
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    diff = A @ R.T - B
    return np.sqrt((diff ** 2).sum() / A.shape[0])

# 读 15 个参考帧（仓库里的 path.pdb，单位是 Å）
models = load_models("replication/metadynamics/path_cv/path.pdb")
# 转成 nm（PLUMED 内部单位）
models_nm = [m / 10.0 for m in models]

# 用坏掉的 LAMBDA
LAMBDA = 3.3910  # nm^-2, 这就是当前 plumed.dat 里的值

# 对每个参考帧喂回公式
for i in range(15):
    # 计算 frame_i 到其他所有帧的 RMSD (nm)
    rmsds = np.array([kabsch_rmsd(models_nm[i], models_nm[j]) for j in range(15)])
    # 注意：FUNCPATHMSD 的输入是 d，formulae 用 exp(-λ d)
    # 我们当时的 plumed.dat 没有 SQUARED 关键字，所以 d 就是 RMSD（不是 RMSD²）
    weights = np.exp(-LAMBDA * rmsds)   # 注意这里不是 rmsds**2，因为没有 SQUARED
    s_value = sum((j+1) * weights[j] for j in range(15)) / weights.sum()
    print(f"frame_{i+1:02d} → s = {s_value:.2f}")
```

**运行结果**（跑坏的 LAMBDA=3.391）：
```
frame_01 → s = 4.02   ← 应该是 1
frame_02 → s = 4.34   ← 应该是 2
frame_03 → s = 4.82   ← 应该是 3
frame_04 → s = 5.38   ← 应该是 4
frame_05 → s = 5.99   ← 应该是 5
frame_06 → s = 6.64   ← 应该是 6
frame_07 → s = 7.32   ← 应该是 7
frame_08 → s = 8.00   ← 对！但是对称性必然
frame_09 → s = 8.68   ← 应该是 9
...
frame_14 → s = 11.66  ← 应该是 14
frame_15 → s = 11.98  ← 应该是 15
```

**这组数字我还记得当时看到时的震惊**。定义 CV 的参考帧自己都认不出来。整条 [1, 15] 的路径被压缩成了 [4, 12]。Frame_8 输出 8 是因为 15 帧的对称性让两边相互抵消——这是唯一一个"正确"的值，但它是欺骗性的。

**这就同时回答了我一开始看到的所有现象**：
- COLVAR 里 s 卡在 7.79 附近——因为坏 CV 的可达范围本来就是 [4, 12]，加上对称性进一步压缩到中间 ≈ 8
- **系统物理上可能根本不在 PC basin**——它可能一直在 O basin（s 本来应该 ≈ 1），但坏 CV 把 O 的构象也翻译成了 s ≈ 7.8
- MetaD 推不动——因为坏 CV 的梯度 ds/dx 几乎为零（CV 对真实原子位移不敏感），bias 虽然堆到 61.7 kJ/mol，但转成原子上的力接近零

**我原来的假设 1 是完全错的**。系统不是卡在 PC basin，而是 CV 坏了，让 O/PC/C 都被翻译成差不多的 s 值。

### English

Here's the test that broke the case. A Codex review challenged my assumption that the CV was correct. Path CVs have a built-in sanity check: if you feed the k-th reference frame back into the formula, you should get `s` equal to k. I wrote a 30-line Python script to do this. With the current lambda of 3.391, frame 1 returned `s` equal to 4.02, and frame 15 returned 11.98. The entire path interval from 1 to 15 was being compressed into 4 to 12. Frame 8 returned 8 but only because of symmetry — it's a misleading coincidence. This single test invalidated my entire physical interpretation. The system wasn't stuck in PC; the CV was just mapping everything to around 7.8. And because the CV was flat, its gradient was near zero, so the 61 kilojoules of accumulated bias produced essentially no physical force. The 46 nanoseconds of "metadynamics" was effectively unbiased MD.

---

## Slide 7 — Root Cause: np.sum vs np.mean

### 中文

**知道 CV 坏了之后，下一个问题是"在哪坏的"**。

LAMBDA 值 3.391 是从哪来的？我去追踪源头，发现它来自 `generate_path_cv.py` 这个脚本——负责从两个端点晶体结构生成 15 帧路径、并计算 LAMBDA 值。

脚本里有一个关键函数 `calculate_msd`：
```python
def calculate_msd(coords1, coords2):
    """
    Calculate mean squared displacement (MSD) between two frames.
    """
    diff = coords1 - coords2
    return np.sum(diff**2)   # ← 这里！
```

**我一看就发现问题了**。函数名字叫 `calculate_msd`（mean squared displacement，注意这个 "mean"——应该是**平均**），但实现用的是 `np.sum`——**总和**。这是一个 naming/implementation mismatch。函数输出的不是 MSD，而是 TSSD（total sum of squared displacements）。

对 112 个 Cα 原子的相邻 frame，`np.sum` 给出的是：
```
total SD = Σᵢ |Δrᵢ|² = 67.83 Å²
```

而按 PLUMED 的标准 RMSD 定义，应该是：
```
per-atom MSD = (1/N_atoms) × Σᵢ |Δrᵢ|² = 67.83 / 112 = 0.6056 Å²
```

两者相差 **N_atoms = 112 倍**。

然后脚本用这个错的 "MSD" 算 LAMBDA：
```python
# 脚本里的逻辑
total_sd = calculate_msd(frame1, frame2)   # = 67.83 Å²  ← 实际是 total SD
lambda_angstrom = 2.3 / total_sd           # = 0.0339 Å⁻²
lambda_nm = lambda_angstrom * 100          # = 3.391 nm⁻²  (Å→nm 转换 × 100)
```

**正确的推导**（应该这么算）：
```python
per_atom_msd = np.mean(np.sum(diff**2, axis=1))  # 对原子维度求和，然后对原子数求平均
# 或等价: np.sum(diff**2) / N_atoms
# = 0.6056 Å²

lambda_angstrom = 2.3 / per_atom_msd       # = 3.798 Å⁻²
lambda_nm = lambda_angstrom * 100          # = 379.77 nm⁻²
```

**那个 `2.3 / <rmsd>²` 公式是从哪来的？**

PLUMED 官方文档 (`https://www.plumed.org/doc-v2.9/user-doc/html/_p_a_t_h_m_s_d.html`) 里有这句话：

> "LAMBDA is generally calculated as 2.3/\<rmsd\>^2 where rmsd is calculated as the distance between a frame in the reference and the next one."

Google Groups 的 plumed-users mailing list 也确认了同样的公式，并特别强调了单位转换：

> "If you use gromacs, the lambda value obtained should be multiplied by 100."

这个乘 100 就是因为 GROMACS 内部用 nm 而不是 Å，1 nm² = 100 Å²，所以 $\lambda$ 的单位从 Å⁻² 转到 nm⁻² 要乘以 100。

**为什么 0.1 这个 kernel 权重很重要？**

代入相邻 frame 的距离看 kernel 权重：

**坏的 LAMBDA = 3.391**：
```
exp(-LAMBDA × RMSD_adjacent) = exp(-3.391 × 0.0778) = exp(-0.264) = 0.77
```

**对的 LAMBDA = 379.77（带 SQUARED）**：
```
exp(-LAMBDA × MSD_adjacent) = exp(-379.77 × 0.006056) = exp(-2.30) = 0.10
```

0.10 这个数来自 path CV 原论文 (Branduardi 2007)。它是 `exp(-2.3)` 的四舍五入。**相邻 frame 的 kernel 权重应该是 10%**——这样每个 "里程碑" 对加权平均有清晰但非 dominant 的贡献，CV 能平滑地在路径上插值。

**坏的 0.77 意味着什么**？意味着相邻 frame 的权重差异不到 25%，所有 15 帧都在加权平均里 "近乎平等" 贡献，所以 s 严重坍缩向中间值。这就是我看到的现象。

**修复**：
```python
# 修好的 calculate_msd:
def calculate_msd(coords1, coords2):
    diff = coords1 - coords2
    return np.mean(np.sum(diff**2, axis=1))   # axis=1 先对 xyz 求和，然后 mean 平均原子
```

一行代码，`np.sum` → `np.mean`。差 112 倍。

### English

With the CV known to be broken, I traced lambda back to `generate_path_cv.py`. It computes lambda from a function called `calculate_msd`, which uses `numpy.sum` instead of `numpy.mean`. That's the bug. The function name says "MSD" (mean squared displacement) but returns the total sum over all 112 C-alpha atoms. The PLUMED `RMSD` action returns per-atom normalized values, so the correct lambda should be computed from the per-atom mean, not the total sum. The two differ by exactly the number of atoms, 112 times. With the broken lambda, the kernel weight between adjacent frames was 0.77 instead of the canonical 0.10. That's what collapsed the CV. The fix is literally `numpy.sum` becomes `numpy.mean`. One line.

---

## Slide 8 — Offline Verification with plumed driver

### 中文

**知道了 bug，下一步要验证修复**。但重新跑 46 ns MD 验证太贵（3 天）。

这里 PLUMED 有一个非常有用的工具：`plumed driver`。它可以在**离线模式**下对一个已有的轨迹文件（.xtc, .trr 等）重新计算 CV 值，不需要跑新的 MD。相当于"用新的 CV 定义重新分析旧数据"。

**具体做法**：

先写一个只包含 CV 定义、不包含 METAD action 的分析专用 plumed.dat：
```
r1: RMSD REFERENCE=frames/frame_01.pdb TYPE=OPTIMAL SQUARED
r2: RMSD REFERENCE=frames/frame_02.pdb TYPE=OPTIMAL SQUARED
...
r15: RMSD REFERENCE=frames/frame_15.pdb TYPE=OPTIMAL SQUARED
path: FUNCPATHMSD ARG=r1,...,r15 LAMBDA=379.77
PRINT ARG=path.s,path.z FILE=COLVAR_rerun_fixed STRIDE=1
```

这里加了 **`SQUARED` 关键字**——这是 FUNCPATHMSD 的要求。如果不加 SQUARED，PLUMED 的 RMSD action 输出的是原始 RMSD（单位 nm）；加了 SQUARED，输出的是 RMSD² 即 per-atom MSD（单位 nm²）。SI 公式 `λ = 2.3/MSD` 的 MSD 是 per-atom 的平方距离，所以我们要用 SQUARED 版本，让 FUNCPATHMSD 收到的 ARG 单位和 LAMBDA 单位匹配（nm² × nm⁻² = 无量纲）。

然后跑 driver：
```bash
plumed driver \
    --plumed plumed_analysis_fixed.dat \
    --mf_xtc metad.xtc \
    --timestep 0.002 \
    --trajectory-stride 5000
```

参数解释：
- `--plumed plumed_analysis_fixed.dat`：用修复版的 PLUMED 输入
- `--mf_xtc metad.xtc`：读取 Job 41514529 产出的压缩轨迹
- `--timestep 0.002`：这是**原来 MD 的时间步**（单位 ps），driver 需要知道这个来正确计算每帧的时间戳
- `--trajectory-stride 5000`：这是**原来 MD 写轨迹的频率**（每 5000 个 MD 步写一帧 = 每 10 ps 一帧），driver 用这个和 timestep 相乘算出每帧对应的真实时间

**PLUMED 启动时打印的消息**：
```
PLUMED:   lambda is 379.770000
PLUMED:   Consistency check completed! Your path cvs look good!
```

**第二行是关键**。这是 PLUMED 自己的 path CV 合规性检查消息。它会自动跑一个类似我手写的 self-consistency test，如果通过就打印这句话，不通过就报错。**这个检查只在 `plumed driver` 模式显示**——在 `gmx mdrun` 接口下不显示，所以当时 Job 41514529 的 bug 才能悄悄溜过去。如果我当时在提交 job 之前先用 driver 跑一下 CV，就能立刻发现问题。

**1.3 秒后 driver 完成**，输出了 4631 行新的 COLVAR 数据。我分析了一下：

```python
d = np.loadtxt('COLVAR_rerun_fixed', comments='#')
s = d[:,1]
print(f"s range: [{s.min():.3f}, {s.max():.3f}]")
print(f"s mean: {s.mean():.3f}, std: {s.std():.3f}")
print(f"Frames in O (s<5): {(s<5).sum()}")
```

输出：
```
s range: [1.04, 1.06]
s mean: 1.052, std: 0.005
Frames in O (s<5): 4515 / 4631 (97.5%)
```

**新的 s 值在 1.04-1.06 之间**，基本完全在 O basin。系统物理上从头到尾都在 O 附近，根本没离开。**修正的 CV 揭示了真相**：系统没被困在 PC basin，它根本没动。

这也解释了为什么 MetaD 推不动：CV 梯度几乎为零 → bias 作用力几乎为零 → 46 ns 等价于 46 ns 无偏置 MD（系统在 O 里做热涨落，没翻过任何能垒）。

### English

Once I knew the bug, I didn't need to re-run 46 nanoseconds of molecular dynamics. PLUMED ships with a tool called `plumed driver` that re-computes CVs on an existing trajectory file, offline. I wrote an analysis-only plumed.dat with the corrected lambda, and ran driver on the existing xtc. It finished in 1.3 seconds. PLUMED printed "consistency check completed, your path cvs look good" — which is the message it prints only in driver mode, not in `gmx mdrun`, which is why our original job never flagged the bug. The new COLVAR showed `s` around 1.05 for the entire 46 nanoseconds. The system was in the Open basin the whole time. It wasn't stuck in PC. The broken CV was just mapping everything to `s` around 7.8. And because the CV gradient collapsed along with the CV, the bias force was near zero. The 46 nanoseconds was effectively unbiased MD.

---

## Slide 9 — Going Deeper: PATHMSD Was Never the Problem

### 中文

**到这里 bug 已经找到并修好了（FUNCPATHMSD + SQUARED + LAMBDA=379.77）。但这周三晚上用户问了一个更深的问题**："为什么你们当时不直接用 SI 原版的 `PATHMSD`，要换成 `FUNCPATHMSD`？"

这个问题让我意识到：**我们一周前切换 action 的那个决定本身可能就是错的**。如果当时直接用 PATHMSD，整个 FUNCPATHMSD LAMBDA bug 本来就不会发生。

**让我追溯当时的决策记录**（FP-020 写在 `failure-patterns.md` 里）：

FP-020 原文记录了两条诊断：
1. `libplumedKernel.so` 模块残缺（conda 版 bug）
2. "PATHMSD 在 mdrun 中只认连续编号 PDB"

第二条是我当时看到一个报错后做的归因。报错大概长这样：
```
PLUMED: ERROR in input to action PATHMSD with label path :
number of atoms in a frame should be more than zero
```

当时我去看 `path.pdb` 的原子 serial 号是什么：
```bash
head -5 path.pdb
```
输出：
```
MODEL        1
ATOM   1614  CA  ALA A   1      55.739 218.928 175.580  1.00  0.00           C
ATOM   1621  CA  ALA A   2      58.166 221.449 174.074  1.00  0.00           C
ATOM   1643  CA  ALA A   3      58.234 221.993 170.324  1.00  0.00           C
ATOM   1657  CA  ALA A   4      61.401 223.996 169.808  1.00  0.00           C
```

**我看到这些 serial 号 1614, 1621, 1643, 1657...**——非连续！我的心里立刻想到："肯定是 PATHMSD 不接受非连续 serial"。

这个推理的问题是：**我只是看到了"非连续 serial"，然后把这个特征和报错信息匹配起来，没有去查 PLUMED 文档确认**。这是一个典型的"看到相关性就当因果"的错误。

我当时为什么没查文档？老实说：
- 当时很急着让 MetaD 跑起来（每天被 HPC 排队延迟）
- FUNCPATHMSD 语法看起来能绕过去（单独算每个 frame 的 RMSD，不需要多 model PDB）
- "非连续 serial" 看起来像一个合理的限制（PDB 标准不强制 serial 连续，但很多工具默认假设连续）
- **我完全没想去验证这个假设**——直接换了 action 把问题"解决"了

**今天我做了当时应该做的事情：去查文档**。

我开了三个并行的研究 agent：
1. 一个去读 PLUMED 2.9 的 PATHMSD 文档
2. 一个重新精读 SI 的 MetaDynamics 方法段落
3. 一个搜索已发表的使用 PATHMSD 的例子

**Agent 1 的关键发现**（PLUMED 文档）：

PATHMSD 文档页面 (`https://www.plumed.org/doc-v2.9/user-doc/html/_p_a_t_h_m_s_d.html`) 里的**示例**就用了**非连续原子 serial**：
```
ATOM      1  CL  ALA     1      -3.171   0.295   2.045  1.00  1.00
ATOM      5  CLP ALA     1      -1.819  -0.143   1.679  1.00  1.00   ← 跳过 2,3,4
ATOM      6  OL  ALA     1      -1.177  -0.889   2.401  1.00  1.00
ATOM      7  NL  ALA     1      -1.313   0.341   0.529  1.00  1.00
```

**PATHMSD 文档自己就用非连续 serial 做示例**，这直接证明了当时的归因是错的。

**Agent 3 的关键发现**（published examples）：

从 Google Groups plumed-users mailing list 找到一条权威引用：

> "The lambda parameter is very important and should be chosen with care, and is generally calculated using the formula **2.3/\<rmsd\>^2**, where rmsd is calculated as the distance between a frame in the reference and the next one. **If you use gromacs, the lambda value obtained should be multiplied by 100.**"

这完全对上了我们的正确值 379.77（`2.3 / 0.6056 Å² × 100 = 379.77 nm⁻²`）。

**有了这两个证据后，我决定直接在 Longleaf 上测试 PATHMSD**：

```bash
ssh longleaf
cd /work/users/l/i/liualex/AnimaLab/metadynamics/single_walker/rerun

# 写一个最小 PATHMSD 测试输入
cat > plumed_pathmsd_test.dat << 'EOF'
path: PATHMSD REFERENCE=../path_gromacs.pdb LAMBDA=379.77
PRINT ARG=path.sss,path.zzz FILE=COLVAR_pathmsd STRIDE=1
EOF

# 用源码编译版 PLUMED（不是 conda 版）跑 driver
export PLUMED_KERNEL=/work/users/l/i/liualex/plumed-2.9.2/lib/libplumedKernel.so
/work/users/l/i/liualex/plumed-2.9.2/bin/plumed driver \
    --plumed plumed_pathmsd_test.dat \
    --mf_xtc ../metad.xtc \
    --timestep 0.002 \
    --trajectory-stride 5000
```

**第一次运行**：又报了那个熟悉的错：
```
PLUMED: ERROR in input to action PATHMSD with label path :
number of atoms in a frame should be more than zero
```

**我楞了一下**——难道文档错了？但是 PLUMED 已经 `Found PDB: 15 containing 112 atoms` 了，说明前 15 帧都正确读了。那为什么还报"frame 里没有原子"？

我去看 `path.pdb` 的结构：
```bash
tail -5 path_gromacs.pdb
```
输出：
```
ATOM   4707  CA  ALA A 111      86.942 221.554 172.224  1.00  0.00           C
ATOM   4723  CA  ALA A 112      87.861 225.242 171.825  1.00  0.00           C
ENDMDL
END             ← 这里！
```

**最后一个 `ENDMDL` 之后还有一个 `END` 行**。PLUMED 的多 model 解析器把 `END` 当成了 "第 16 个 frame 的开始 marker"，然后发现第 16 帧里没有 `ATOM` 行，就报 "number of atoms in a frame should be more than zero"。

**这是一个典型的坑**。PDB 标准允许（鼓励）在文件末尾加 `END`，但 PLUMED 的 multi-model 解析对 `END` 和 `ENDMDL` 一视同仁。我把这个记成了 **FP-023**。

修复非常简单：
```bash
sed -i '/^END$/d' path_gromacs.pdb
```

删掉 trailing END 之后，PATHMSD **第二次运行就完全通过了**：

```
PLUMED:   Opening reference file ../path_gromacs.pdb
PLUMED:   found 112 atoms in input
PLUMED:   with indices :
PLUMED: 1614 1621 1643 1657 1681 1700 1719 1729 1744 1758 ...
PLUMED: ...
PLUMED:   Found PDB: 15 containing 112 atoms
PLUMED: Finished setup
```

**注意 PLUMED 打印出了所有 112 个原子的 serial 号——1614, 1621, 1643, 1657, ...——非连续的**。它完全能处理非连续 serial。一周前 FP-020 的归因是错的，**真正的原因是 conda 版 .so 残缺 + path.pdb 尾部 END**。

然后我对比了 PATHMSD 和 FUNCPATHMSD+SQUARED 两个版本在同一条 46 ns 轨迹上的输出：

| 指标 | FUNCPATHMSD + SQUARED（周二的修复）| **PATHMSD（今天验证）**|
|---|---|---|
| path CV 代码行数 | 17（15 RMSD + FUNCPATHMSD + METAD）| **2**（PATHMSD + METAD）|
| 46 ns 上 s(R) 范围 | [1.04, 1.06] | **[1.00, 1.70]** |
| COLVAR 中 NaN 帧数 | **116 / 4631 (2.5%)** | **0** |
| z(R) 范围 | 1.45 – 1.92 nm²（数值异常大）| **0.004 – 0.084 nm²（物理合理）**|
| 和 SI 的匹配度 | 否 | **是** |

**PATHMSD 每一项都更好**。尤其是 z(R)：FUNCPATHMSD 版本给 1.5-1.9 nm²，这个数值物理上不合理（z 是"离路径的距离"，系统在 O 附近不应该离路径这么远）；PATHMSD 给 0.004-0.08，完全正常。FUNCPATHMSD 的 z 异常可能是实现细节或数值边界问题——但我们换回 PATHMSD 就不用 care 了。

**决定**：换回 PATHMSD。最终的 plumed.dat 简洁到只有 2 行：

```
path: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77
metad: METAD ARG=path.sss,path.zzz SIGMA=0.05 ADAPTIVE=GEOM HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
PRINT ARG=path.sss,path.zzz,metad.bias FILE=COLVAR STRIDE=500
```

**整件事的教训**：当时 FP-020 的归因（"非连续 serial"）是一个典型的认知错误——看到一个特征（非连续 serial）和一个报错之间的相关性，没有做实验或查文档就当成因果。如果当时花 5 分钟查一下 PLUMED 文档看它的示例 PDB 长什么样，就能立刻看到文档自己就用非连续 serial，整个 FP-022 LAMBDA bug 链都不会发生。

### English

Once the bug was fixed with `FUNCPATHMSD + SQUARED + LAMBDA equals 379`, a review question from my advisor made me look harder: why did we switch away from PATHMSD in the first place? Last week's commit log says it was because PATHMSD couldn't handle our non-sequential atom serials — 1614, 1621, 1643, and so on. But I never actually checked the PLUMED documentation to verify that claim. I just saw an error message, saw non-sequential serials in the PDB, and matched them up in my head.

Today I did the check. The PATHMSD documentation page literally shows an example PDB with non-sequential serials — 1, 5, 6, 7. So PATHMSD has always supported non-sequential atom numbering. The original error I saw last week was caused by two different things stacked on top of each other: the broken conda `libplumedKernel.so` library, which is FP-020, and a stray trailing `END` line in the reference PDB that made PLUMED try to parse a sixteenth empty frame. That's FP-023 — a new failure pattern I documented today. Neither had anything to do with atom serials.

I tested PATHMSD directly on Longleaf with the source-compiled PLUMED. First attempt gave the same error. I looked at the PDB more carefully, saw the trailing `END`, removed it with one `sed` command, and PATHMSD ran cleanly. All 15 frames, all 112 atoms with their non-sequential serials 1614 through 4723, read correctly. The numerical comparison against FUNCPATHMSD shows PATHMSD is strictly better: two lines of code instead of seventeen, zero NaN frames instead of 116, and physically reasonable z values instead of anomalous ones. So I'm switching the production plumed.dat back to PATHMSD. Two lines. Matches the SI protocol exactly.

The lesson: last week I took a shortcut. I saw an error, made a plausible-sounding guess about the cause, and switched tools instead of reading the docs. That saved maybe an hour at the time, but it cost three days of HPC, a debugging session this week, and a silent 112-times bug in a CV parameter. If I had spent five minutes on the PATHMSD documentation page last week, none of this would have happened.

---

## Slide 10 — Plan

### 中文

**最后这一页是下一步计划**。

本周剩余：
- ✓ 今天完成：PATHMSD 在源码版 PLUMED 2.9.2 上验证通过
- ✓ 今天完成：更新 6-stage pipeline state；记录 FP-020 更正 + 新增 FP-023
- [ ] 今晚/明天：把新的 plumed.dat（2 行 PATHMSD 版本）scp 到 Longleaf production 目录
- [ ] 备份旧的 Job 41514529 数据到 `archive_FP022_FUNCPATHMSD_broken/`
- [ ] 重提交 50 ns initial run（SI 协议下的 initial run）

下周：
- [ ] 等待 initial run 完成（~3 天 HPC walltime）
- [ ] 从初步结果里看 s 是否真的能扫到 O 和 C 两端（这次 CV 是对的，系统应该能动）
- [ ] 如果 s 能扫到整条路径：从轨迹里提取 10 个覆盖 O/PC/C 的 snapshots
- [ ] 从这 10 个 snapshots 启动 SI 协议的 10-walker production（每 walker 50-100 ns）

**目标：两周内产出可以和 JACS 2019 Figure 2a 对比的 FES**。

最终的 plumed.dat（完整版，每个参数的来源和含义在附录里讲）：
```
path: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77

metad: METAD ARG=path.sss,path.zzz SIGMA=0.05 ADAPTIVE=GEOM \
       HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS

PRINT ARG=path.sss,path.zzz,metad.bias FILE=COLVAR STRIDE=500
```

### English

To wrap up. This week I went from "the system looks stuck in PC" to "the CV was broken" to "the CV bug was caused by an earlier misdiagnosis of which PLUMED action to use." Three bugs documented: FP-020 re-diagnosed, FP-022 obsolete, FP-023 new. The final production setup is two lines of PATHMSD, matching the SI protocol exactly. Next: deploy the new plumed.dat to Longleaf, backup the broken Job 41514529 data, resubmit the 50 nanosecond initial run. That takes about three days of HPC time. Then extract ten snapshots and launch the ten-walker production. Target is a publishable FES comparable to Maria-Solano 2019 Figure 2a within two weeks. Questions?

---

## 附录 A: 最终 plumed.dat 每个参数的来源

```
path: PATHMSD REFERENCE=path_gromacs.pdb LAMBDA=379.77
metad: METAD ARG=path.sss,path.zzz SIGMA=0.05 ADAPTIVE=GEOM HEIGHT=0.628 PACE=1000 BIASFACTOR=10 TEMP=350 FILE=HILLS
PRINT ARG=path.sss,path.zzz,metad.bias FILE=COLVAR STRIDE=500
```

| 参数 | 值 | 来源 | 含义 |
|------|-----|------|------|
| `PATHMSD` | (action 名) | SI 没明说但这是 PLUMED path CV 的标准 action | 一体式 path CV 实现，读 multi-model PDB，内部计算每帧 RMSD，组合成 s/z |
| `REFERENCE` | `path_gromacs.pdb` | 从 `generate_path_cv.py` 生成 | 15 个 MODEL 的 multi-model PDB，每个 MODEL 是 112 个 COMM 域 Cα 原子，非连续 serial (1614-4723) 对应 GROMACS 拓扑里的真实原子索引 |
| `LAMBDA` | 379.77 | 公式 `λ = 2.3 / per-atom MSD × 100` | 单位 nm⁻²。路径"锐度"参数。2.3 来自 Branduardi 2007 原论文，目的是让相邻 frame 权重 exp(-2.3) ≈ 0.10 |
| `ARG` | `path.sss,path.zzz` | PATHMSD 的 output 组件名（注意是 `.sss`/`.zzz`，不是 FUNCPATHMSD 的 `.s`/`.z`）| METAD 同时在这两个维度上加 bias：`sss` 是沿路径进度（1-15），`zzz` 是离路径的距离 |
| `SIGMA` | `0.05` | PLUMED 默认，seed 值 | ADAPTIVE=GEOM 会覆盖，所以只是初始值 |
| `ADAPTIVE` | `GEOM` | SI S3: "adaptive Gaussian width scheme" | 自适应 Gaussian 宽度（几何平均方案），根据局部 CV 波动自动调整 sigma |
| `HEIGHT` | `0.628` | SI S3: 0.15 kcal/mol × 4.184 | 单位 kJ/mol。Gaussian hill 初始高度，well-tempered 之后会衰减 |
| `PACE` | `1000` | SI S3: "deposited every 2 ps"，与 dt=0.002 ps 相乘 = 2 ps | 每 1000 个 MD step 沉积一个 hill |
| `BIASFACTOR` | `10` | SI S3: "bias factor of 10" | well-tempered γ 因子。控制 hill 高度随时间的衰减速度。等效温度 = T × γ = 3500 K |
| `TEMP` | `350` | SI S3: 350 K（P. furiosus 嗜热古菌的最适温度）| K。MetaD 内部温度，必须和 .mdp 里的 ref_t 严格一致 |
| `FILE=HILLS` | — | PLUMED 默认名 | 每 PACE 步写一个 hill 到这个文件，后续用 `plumed sum_hills` 重构 FES |
| `STRIDE=500` | `500` | 工程选择（每 1 ps 一行）| COLVAR 输出频率。500 步 × 0.002 ps = 每 1 ps 一行 |

---

## 附录 B: 可能被问到的问题 + 预答

### Q: 为什么你没一开始就用 PATHMSD？

A: 上周第一次试了 PATHMSD，用的是 conda 版 PLUMED，它的 `.so` 残缺，加上 path.pdb 尾部有个 trailing `END`，两个问题叠加表现为"PATHMSD failed"。我当时看到 path.pdb 的原子 serial 是非连续的（1614, 1621, ...），就把报错归因到"PATHMSD 不认非连续 serial"，没查文档确认就换成了 FUNCPATHMSD。这是一个归因错误。今天查文档发现 PATHMSD 自己的示例就用非连续 serial，证明当时的归因是错的。

### Q: 为什么 `2.3 / MSD` 这个公式里的 2.3？

A: 来自 Branduardi 2007 的 path CV 原论文。目的是让相邻 frame 的 kernel 权重等于 `exp(-2.3) ≈ 0.10`。这个 0.10 是经验值——太大（比如 0.5）会让 CV 过于平滑，相邻 frame 无法分辨；太小（比如 0.01）会让 CV 太尖锐，只有最近的 frame 有权重，丢失路径的连续性。0.10 是甜区。数学上 `2.3 ≈ ln(10)`，所以 `exp(-2.3) = 1/10`。

### Q: SI 里那个 "80" 到底是什么？

A: SI 原句是 `"λ = 2.3 × inverse of mean square displacement between successive frames, 80"`。这个 "80" 我到现在也没完全搞懂——可能的三种解释：(a) MSD = 80 Å² 在 total SD 约定下（我们算得 67.83 Å²，差 15%，可能因为端点选得略不同），(b) 80 个 frame 之类的，(c) 引用编号 80。歧义本身不影响修复——我们用 PLUMED 文档的标准公式 `λ = 2.3/per-atom MSD × 100` 算出来 379.77，再加上自一致性测试验证，这就是可靠的值。SI 那个 80 可能是他们自己的私下约定，我们不用去猜。

### Q: FUNCPATHMSD 的 z(R) 值异常大是为什么？

A: 还没完全搞清楚。FUNCPATHMSD 的 z 公式理论上和 PATHMSD 相同，但实际输出范围相差两个数量级（FUNCPATHMSD 给 1.5-1.9 nm²，PATHMSD 给 0.004-0.08 nm²）。可能的猜测：PLUMED 的 FUNCPATHMSD 内部对 sharp kernel 有数值边界问题（看 2.5% 的 NaN 帧数也支持这个）。换回 PATHMSD 后这个问题自动消失，所以我没继续深挖。

### Q: 为什么 `plumed driver` 能检测到 bug 但 `gmx mdrun` 不能？

A: `plumed driver` 启动时会跑一个 "Consistency check"——对每个参考帧喂回 CV 公式，看 s(frame_i) 是否接近 i。如果不接近就打印警告或报错。这个检查在 `gmx mdrun -plumed` 接口下不跑（或者至少不显示消息）。所以如果你直接提交 mdrun job，这个检查完全不会触发。**教训：任何 path CV 修改后，先用 `plumed driver` 跑一段现有轨迹做 consistency check，再上 mdrun**。
