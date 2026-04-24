# Consult: Miguel 激进配方 3.76 ns 还是卡在 O-basin，为什么？

你好，想请你帮我诊断一个 MetaDynamics initial exploration run 的卡住问题。

## 背景

我在复刻 Osuna 2019 JACS 的 TrpB MetaDynamics（O→C conformational path）。之前用过一套我们自己推算的参数（`ADAPTIVE=GEOM`, `HEIGHT=0.628 kcal/mol`, `BIASFACTOR=10`）做 single-walker + probe sweep（P1–P5），**所有 probe 全部卡在 O basin（s < 2），连 2 ns 都爬不出去**。

为此我们找到了原文作者 **Miguel Iglesias-Fernández**，他 2026-04-23 邮件给了权威配方（见 `miguel_email.md`）。其中 fallback single-walker 配方是专门为"激进 exploration"设计的：

- `ADAPTIVE=DIFF`（不是 GEOM，这是原配方的 SI 误读纠正）
- `HEIGHT=0.3 kcal/mol`（原 SI 是 0.628，他说用 0.3 + 更大 biasfactor）
- `BIASFACTOR=15`（原 SI 是 10，fallback 专门调大）
- `LAMBDA=3.77 Å⁻²`（Branduardi 公式 2.3/⟨MSD⟩ 对我们当前 path 的结果；Miguel 自己的是 80，但他的 path 比我们的密 21×，这是 path-construction alignment 的未解变量，不是现在要讨论的主题）
- `SIGMA=1000` steps（DIFF 方案的时间窗口，= 2 ps）
- `SIGMA_MIN=0.1,0.01` for `p1.sss, p1.zzz`
- `PACE=1000` steps (2 ps)
- `UPPER_WALLS AT=2.5 KAPPA=800` on `p1.zzz`
- `UNITS LENGTH=A ENERGY=kcal/mol`
- `TEMP=350 K`

见 `plumed.dat`。

## 运行情况

Job 45324928，跑在 NVIDIA V100，GROMACS 2026.0 + PLUMED 2.9.2 source-compiled。wall 5h，sim **3.76 ns**。

**结果依然卡在 O-basin**：

| 指标 | 值 |
|---|---|
| max_s（全程最大）| **1.4964** |
| max_s 时刻 | **1300.6 ps (1.3 ns)** |
| 当前 s (末尾) | ≈ 1.02 |
| 当前 z (末尾) | ≈ 2.3 (一直在撞 UPPER_WALLS=2.5) |

也就是说 **walker 在 1.3 ns 时短暂摸到 s=1.496，之后 2.4 ns 又退回来了**。

## σ 的演化（1882 个 hill）

这是最关键的数据。**`kerneltype=stretched-gaussian`, `multivariate=true`**。HILLS 列：

```
time  p1.sss  p1.zzz  σ_ss  σ_zz  σ_zs  height  biasf
```

| σ 通道 | SIGMA_MIN floor | min 观测 | median | max | 行为 |
|---|---|---|---|---|---|
| σ_ss（s 方向）| 0.1 | **0.0036** | 0.031 | 0.105 | 中位数**低于 floor 一个量级**；时不时 clamp 到 0.100，然后马上又掉到 0.004 |
| σ_zz（z 方向）| 0.01 | 0.036 | 0.196 | **4.00** | 撞 wall 的瞬间冲到 4.0 |

## 对比：和之前 P3 的"触底"是一回事吗？

| | P3（旧 GEOM 配方）| 45324928（Miguel DIFF 配方）|
|---|---|---|
| σ 卡死 floor？ | 是，长期粘在 SIGMA_MIN | **否**，在 floor 附近震荡 |
| walker 有过 s>2？ | 从来没 | 也没（max_s=1.496）|
| 换了 Miguel 激进配方有改善？ | — | **几乎没有** |

## 问题

1. **σ_ss 大部分时间低于 SIGMA_MIN floor（0.1）** —— 这个是 PLUMED 的 ADAPTIVE=DIFF 设计如此（HILLS 记录 pre-clamp 的 raw diffusion 估计，clamp 只在注入 Gaussian 时生效），还是真的有 bug？

2. **σ_ss 中位数 0.031 意味着什么物理？** 如果 DIFF 每 2 ps 窗口估计出来的 s-方向 RMS 位移就只有 0.03（s 的绝对 span 是 1-15），这直接说明"walker 在 s 维度根本没扩散"。那即便 wall bias 每 2 ps 加一个高度 0.3 kcal/mol 的 Gaussian，width 也这么窄，**填的坑横向大小只有 0.03，比 frame 间隔（~1）还小 30×**，等于什么都没填。

3. **max_s 在 1.3 ns 摸到 1.496 然后退回 —— 这说明曾经短暂突破，但后来 GPU 时间花在 z 方向反复撞 wall**（σ_zz max=4.0 = 撞墙瞬间信号）。

4. **我们是不是误解了 Miguel 的 fallback 配方**？他的"HEIGHT=0.3 BIASFACTOR=15"是不是在假设我们有**他那种更密的 path**（⟨MSD⟩~0.029 Å²）？在我们这种 ⟨MSD⟩~0.61 Å² 的 path 上，是不是本该配**更大的 HEIGHT**（比如 0.8-1.5）来补偿 frame 间隔太稀？

5. **还是说这根本不是 filling pattern 的问题，而是 path 几何在 O-endpoint 切线方向不对**（我们之前做过 step-3 诊断：probe_P1 前 2 ns 的 21 帧全部 OFF-TANGENT，cos(θ) mean=−0.111，f_perp mean=0.992），Miguel 的配方换汤不换药也跳不过这个结构 barrier？

## 我想从你这里得到

**不是**"再试一组参数"——那样我们会无限迭代。

**是**：在 path_cv + DIFF + UPPER_WALLS + 当前 path 几何这套设置下，**哪个变量最可能是 rate-limiter**？具体来说：

- (A) HEIGHT 太小（0.3 kcal/mol 填不过 O-basin 的局部 PES 壁）
- (B) σ_ss DIFF 估计本身是 floor 问题（需要抬 SIGMA_MIN_s，或者换回 GEOM 方案）
- (C) UPPER_WALLS AT=2.5 封死了正交逃逸方向，让 walker 只能在 s≈1 附近撞南墙
- (D) Path 几何问题（O-endpoint 切线不对齐），参数怎么调都解决不了，必须重建 path
- (E) 其它我没想到的

你读完 HILLS + COLVAR + plumed.dat 后，能不能给出**带推理链的 top-2 假设**，并建议一个**最小可证伪实验**（比如"只改 HEIGHT → 0.8，其他不动，跑 5 ns 看 max_s"）？

## 附件说明

- `plumed.dat` — 当前 production
- `HILLS` — 1882 行，完整
- `COLVAR` — 18800 行（2 ps stride），完整
- `metad.log` — PLUMED + GROMACS log
- `slurm-miguel_initial-45324928.out` — SLURM 输出
- `miguel_email.md` — Miguel 2026-04-23 权威邮件
- `path_driver.pdb` — 15-frame 112 Cα reference path（atom serials 1–112 per MODEL）

补充：Miguel 邮件里明确说"如果 10-walker 版本跑不动，就用 single-walker fallback（HEIGHT=0.3 BIASFACTOR=15）"。我们现在跑的就是 fallback，按他说**这已经是 exploration mode 最 aggressive 的了**。
