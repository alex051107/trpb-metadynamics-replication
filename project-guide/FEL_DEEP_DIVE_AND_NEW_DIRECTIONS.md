# 完整 Pipeline 深度讲解：从 PLP 参数化到 FEL 解读

> **读者**：Zhenpeng Liu（有 MD 经验的本科生，不熟悉 FEL / MetaDynamics / Path CV）
> **目的**：能在组会上讲清楚每一步的物理原因，经得起 PI 追问
> **阅读时间**：约 45 分钟
> **版本**：2026-04-01，经 mentor/critic/student-proxy 三轮审阅收敛

---

## 阅读导航

| 你的需求 | 从哪开始 |
|---------|---------|
| 快速过一遍全链条 | 总览图 → 每步的"一句话直觉" |
| 准备组会 | 重点读 Step 8-11 + FEL 三变体对比 + "5 个 PI 会问的问题" |
| 理解新方向 | 最后一章"新研究方向" |
| 理解你的角色 | "你在 Anima Lab 的角色定位" |

---

## 总览：Pipeline 一张图

```
PDB (5DVZ) → PLP 参数化 (GAFF+RESP) → tleap 体系搭建 → min1/min2 → heat1-7 → equil (NPT)
→ 500 ns production MD (NVT) → AMBER→GROMACS 转换 → Path CV 构建 → WT-MetaD (10 walkers)
→ FEL 重构 (sum_hills) → 收敛判断 → 与 JACS 2019 对比
```

---

## Part A：体系准备（Steps 1-5）

### Step 1: PLP 参数化 — RESP 电荷

**一句话直觉**：PLP 不在标准力场菜谱里，你得自己用量子化学算出它每个原子带多少电。

**为什么重要**：PLP 是催化核心。它的电荷分布决定了它和周围蛋白残基的静电作用方式。电荷算错，整个模拟从物理基础上就是错的——而且错误不会报 error，只会悄悄让 FEL 偏掉。

**RESP 是什么**：先用量子化学（HF/6-31G(d)）算分子周围的静电势（ESP），再找一组原子点电荷来拟合这个 ESP。加一个 restraint 让化学等价的原子电荷相同。

**为什么不用 AM1-BCC（更快的方法）**：AM1-BCC 是半经验方法，对普通药物分子够用。但 PLP 同时含磷酸基团（-2 电荷）、吡啶环、Schiff base 共轭体系——这种复杂电子结构需要从头算（ab initio）级别的精度。更关键的是，AMBER 力场体系的所有标准电荷都是用 HF/6-31G(d) 拟合的，电荷方法和力场要匹配，就像镜片和镜框要配套。

**Ain 中间体的总电荷推导**：

| 基团 | 贡献 | 依据 |
|------|------|------|
| 磷酸基 | -2 | pH 7.5 >> pKa2 6.2，双阴离子 |
| 酚 O3 | -1 | pH 7.5 >> pKa 5.8，去质子化 |
| 吡啶 N1 | 0 | ¹⁵N δ=294.7 ppm → 去质子化 (Caulkins 2014) |
| Schiff base NZ | +1 | ¹⁵N δ=202.3 ppm → 质子化 (Caulkins 2014) |
| **合计（LLP 残基本身）** | **-2** | 与 parameterize_plp.sh、PROTOCOL.md 一致 |

> **UNVERIFIED**：Schiff base NZ 的质子化状态是本项目最大的化学不确定性。SI 没有给出答案。当前脚本 `parameterize_plp.sh` 遵循文献主流选择（质子化，+1），但这需要 PI 确认。如果用含 ACE/NME capping 的片段做 Gaussian 计算，capping 基团本身是电中性的，所以总电荷仍然由 LLP 残基决定。

**ACE/NME capping 为什么必须**：从 PDB 提取 LLP 残基时，主链两端的肽键被"切断"了。如果拿着断键的分子做量子化学计算，断键处的电子分布会严重失真。ACE（乙酰基）封 N 端断键，NME（N-甲基酰胺）封 C 端断键——让分子边界处的电子结构恢复正常。这是物理上必须的，不只是格式要求。

> **常见误解**："电荷是从 PDB 文件读的。" 不是。PDB 只有坐标，没有电荷信息。电荷必须从量子化学计算得到。

---

### Step 2: tleap 体系搭建

**一句话直觉**：把蛋白质、PLP 参数、水、离子组装成一个可以跑模拟的完整体系。

**为什么重要**：tleap 是把"化学知识"变成"可计算的数学对象"的关键步骤。输出的 parm7（拓扑）+ inpcrd（坐标）是后面所有步骤的起点。

**力场组合**：

| 组件 | 力场 | 管什么 |
|------|------|--------|
| 蛋白质标准残基 | ff14SB | 20 种天然氨基酸的键参数+电荷 |
| PLP (Ain/LLP) | GAFF2 + RESP | 非标准残基的键参数 + 电荷 |
| 水 | TIP3P | 三点刚性水模型 |
| 离子 | Na+/Cl- | 中和体系总电荷 |

**溶剂化**：在蛋白质周围加一个 TIP3P 水的立方体 box，buffer 距离 10 Å。大约 ~15,000 个水分子。

**离子中和**：蛋白质+PLP 体系有净电荷，加对应的反离子让总电荷为零。周期性边界条件下 PME 需要电中性。

> **常见误解**："溶剂化只是加个水壳。" 不只是。box 大小直接影响周期性图像之间的相互作用。10 Å buffer 是确保蛋白质"看不到自己的镜像"的最低安全距离。

---

### Step 3: Minimization — 消除坏接触

**一句话直觉**：刚溶剂化的体系里水和蛋白质"挤得太紧"，先让它们放松一下。

| 阶段 | 做什么 | 为什么 |
|------|--------|--------|
| min1 | 固定蛋白质（500 kcal/mol/Å² restraint），只让水和离子动 | 先让溶剂找到合理位置，不破坏晶体结构里的蛋白质构型 |
| min2 | 全体系不加约束一起优化 | 消除蛋白质内部的 steric clash，特别是 PLP 周围新参数化的部分 |

> **常见误解**："最小化只是例行公事。" 不是。跳过最小化直接跑动力学，初始力可能大到直接把 active site 拉坏。

---

### Step 4: Heating — 阶梯加热 (0→350 K)

**一句话直觉**：慢慢给体系升温，让所有部分有时间适应。

**为什么 7 步而不是一步到位**：蛋白质骨架、PLP 辅因子、水网络的热容完全不同。瞬间加到 350 K 会让 thermostat 用极大的力猛拉体系，氢键网络崩溃，活性位点几何变形。阶梯加热让速度分布逐步接近 Maxwell-Boltzmann 分布。

| Step | 温度 | Restraint (kcal/mol/Å²) | 物理原因 |
|------|------|-----------|---------|
| heat1 | 0→50 K | 210 | 低温低动能，需要强约束防止溶剂挤压 |
| heat2 | 50→100 K | 165 | |
| heat3 | 100→150 K | 125 | |
| heat4 | 150→200 K | 85 | |
| heat5 | 200→250 K | 45 | 动能渐足，开始放开 |
| heat6 | 250→300 K | 10 | |
| heat7 | 300→350 K | 10 | 近工作温度，基本无约束 |

Heating 用 NVT（固定体积），因为此时不关心密度——先把温度带上去，密度平衡交给 equilibration。

> **常见误解**："restraint 大小是随便选的。" 这些值来自 JACS 2019 SI，是 Osuna 实验室验证过的方案。

---

### Step 5: Equilibration (NPT, 2 ns)

**一句话直觉**：温度到了 350 K，但盒子体积和溶剂密度还不对。用 NPT 让它们在正确的温度和压力下平衡。

**为什么 NPT**：tleap 建的 box 几何上合理，但不代表在 350 K、1 atm 下密度正确。NPT 的 barostat 调整盒子体积，直到溶剂 packing 达到正确密度。跳过这步直接进 NVT production = 把一个错误密度的盒子永远固定住。

参数：2 ns，350 K，1 atm，dt=2 fs，无 restraint。

> **常见误解**："2 ns 太短。" 对大多数蛋白-水体系，2 ns 足以让盒子体积和密度收敛。看密度曲线是否平台，不是看时间长短。

---

## Part B：Production MD 与格式转换（Steps 6-7）

### Step 6: 500 ns Production MD (NVT)

**一句话直觉**：正式记录蛋白质在 350 K 下"自由活动"的长轨迹。

**为什么 NVT 不是 NPT**：经过 NPT 平衡后密度已正确。Production 阶段固定体积，减少 barostat 引入的额外体积波动，让不同体系、不同时间窗之间的比较更干净。这也是 JACS 2019 的原始 protocol。

**为什么 350 K**：*P. furiosus* 是嗜热菌（最适温度 ~100°C），350 K 是这个酶在生理条件下的合理工作温度。不是"为了让蛋白动得快"。

**SHAKE 做什么**：约束含氢键的键长振动。氢的振动频率极高（~10 fs 周期），如果显式积分需要 ≤1 fs 步长。SHAKE "冻住"这些高频振动，让你安全使用 2 fs 步长——计算成本减半，保留我们关心的低频构象动力学。

**PME (Particle-Mesh Ewald) 做什么**：PLP 磷酸基（-2）、Schiff base、Lys82、Glu104 和水网络之间的静电作用不是 8 Å 以内就结束的。PME 在周期性边界条件下系统求和长程库仑力，而不是简单截断。对带电活性位点至关重要。

**500 ns 的真正作用**：不是为了看到 O→C transition（那可能需要 μs 级），而是：
1. 产生一个充分弛豫的起始构象给 MetaD
2. 提供用于提取 10 walkers 起始 snapshot 的轨迹

> **常见误解**："500 ns 就能看到 COMM domain 开合。" 大多数情况下看不到——这正是为什么需要 MetaDynamics 加速。

---

### Step 7: AMBER → GROMACS 转换

**一句话直觉**：把 AMBER 体系"翻译"成 GROMACS 格式，因为 MetaDynamics 必须用 GROMACS + PLUMED2。

**为什么要转**：JACS 2019 用 GROMACS 5.1.2 + PLUMED2 做 MetaD。frozen manifest 要求 strict reproduction。AMBER 负责 system prep + conventional MD，GROMACS + PLUMED2 负责 MetaD。

**ParmEd 做什么**：读 AMBER 的 parm7 + rst7，写出 GROMACS 的 topol.top + conf.gro。本质是"翻译力场记账方式"——不是重新参数化，是把同一组物理参数用另一种软件的语法表达。

**能量验证为什么必须**：转换后用 GROMACS 做 single-point 能量计算，和 AMBER 的分项能量对比（bond/angle/dihedral/vdW/electrostatics）。Ain/LLP 不是标准残基——topology 翻译错误不会让程序崩溃，但会悄悄改变 COMM domain 开合态的相对稳定性。最后表现为"FEL 和论文不一样"。

> **常见误解**："格式转换只是文件格式变了。" 不是。1-4 scaling convention、improper dihedral definition、cutoff scheme 任何一项翻译错，物理就变了。

---

## Part C：增强采样——MetaDynamics 核心概念（Steps 8-11）

### Step 8: Path CV (s, z) 构建

**一句话直觉**：给蛋白质的构象变化定义一个坐标系——你走到了 Open→Closed 路径的哪里（s），偏离这条路径多远（z）。

**比 RMSD 好在哪**：RMSD 把两种信息压成一个数——"走在正确路径上到了中间点"和"完全跑偏到另一个方向但恰好 RMSD 也不大"给出相同的值。Path CV 把这两件事分开。

**s(R) 的数学定义（直觉版）**：

设你有 N 个参考帧（这里 N=15），编号 1 到 N。当前蛋白质构象 R 和每个参考帧 i 之间有一个距离 d_i（用 COMM domain 的 Cα 均方位移衡量）。

```
s(R) = Σ_i [ i × exp(-λ × d_i²) ] / Σ_i [ exp(-λ × d_i²) ]
```

直觉：这是一个 **加权平均**。如果当前构象 R 最像第 5 帧（d_5 最小），那 exp(-λ × d_5²) 最大，s(R) ≈ 5。如果最像第 12 帧，s(R) ≈ 12。

- s(R) ≈ 1 意味着"你在 Open 端"
- s(R) ≈ 15 意味着"你在 Closed 端"
- s(R) ≈ 8 意味着"你在中间（PC 区域）"

**z(R) 的数学定义（直觉版）**：

```
z(R) = -(1/λ) × ln [ Σ_i exp(-λ × d_i²) ]
```

直觉：z(R) 度量的是"你离**最近的**参考帧有多远"。如果你正好站在某个参考帧上，z 很小（≈ 0）。如果你跑到了所有参考帧都很远的地方（off-path），z 很大。

- z(R) 小 → 你在参考路径附近
- z(R) 大 → 你跑偏了

**15 帧怎么来的**：从 PDB 1WDW（Open, PfTrpS）和 3CEP（Closed, StTrpS）提取 Cα 原子坐标（残基 97-184 + 282-305），在笛卡尔空间线性插值生成 15 个中间帧。15 是分辨率和数值稳定性之间的折中。

**λ 是什么**：λ = 2.3 / MSD（相邻帧的平均均方位移）。文献 MSD ≈ 80 Å² → λ ≈ 0.029 Å⁻²。

λ 控制"切换的锐度"：
- λ 太小 → 分不清相邻帧（路径分辨率塌缩）
- λ 太大 → 只对最近帧敏感，噪声被放大
- 2.3 这个系数是 Branduardi et al. 2007 推荐的经验值

> **常见误解**："线性插值的中间帧是物理上合理的构象。" 不一定。笛卡尔线性插值不尊重能量面曲率，可能产生碰撞或不物理的骨架几何。但 Path CV 用这些帧做"度量尺"，不需要每帧都是稳定构象。

---

### Step 9: Well-Tempered MetaDynamics

**一句话直觉**：在蛋白质去过的地方堆越来越小的"山丘"，逼迫它探索新构象，最终画出完整的自由能地图。

**Hill 沉积**：每 2 ps 在当前 (s, z) 位置放一个高斯 hill（初始高度 0.15 kcal/mol = 0.628 kJ/mol）。太大 → 推土机效应；太小 → 探索太慢。

**Bias factor (γ = 10) — 回答追问 Q1**：

γ 是 well-tempered MetaDynamics 的核心参数。它控制 hill 的衰减速率：

```
h(t) = h₀ × exp( -V_bias(s,t) / (kT × (γ-1)) )
```

其中 h₀ = 0.15 kcal/mol 是初始高度，V_bias(s,t) 是到时间 t 为止在位置 s 已经堆了多少偏置。

直觉：
- 第一次到一个新 basin 时，V_bias ≈ 0，hill 高度 ≈ h₀（全力推）
- 反复访问同一个 basin 后，V_bias 变大，hill 指数衰减（越来越轻推）
- 最终，堆积的偏置势收敛到 V_bias(s) = -(1-1/γ) × F(s)

γ 的三个极端：
- γ → ∞：退化为标准 MetaD（hill 永远不衰减，永远不收敛）
- γ = 1：退化为无偏模拟（没有任何偏置）
- γ = 10（我们用的）：偏置最终收敛到 -0.9 × F(s)，即真实自由能面的 90%

> γ 也可以理解成"bias 温度 = γ × T"。γ = 10, T = 350 K → bias 温度 3500 K。这意味着 CV 空间被探索的"有效温度"是 3500 K——大幅加速跨 basin 探索。但真实原子的温度始终是 350 K，只有 CV 维度被加速。

**从 biased trajectory 到 unbiased FES — 回答"不理解 A"**：

这是学生和初学者最常问的问题。MetaDynamics 跑出来的轨迹是 **biased**（蛋白质被偏置推着走），不是 equilibrium 采样。从 biased → unbiased 有两种理解方式：

**理解方式 1（WT-MetaD 特有的收敛性质）**：

WT-MetaD 的数学保证是：经过充分采样后，堆积的偏置势收敛到：

```
V_bias(s) → -(1 - 1/γ) × F(s)     （t → ∞）
```

所以真实的自由能面 F(s) 可以直接从收敛后的偏置势算出：

```
F(s) = -γ/(γ-1) × V_bias(s)
```

对 γ = 10：F(s) = -10/9 × V_bias(s) ≈ -1.11 × V_bias(s)。

`plumed sum_hills` 命令把 HILLS 文件里记录的所有高斯加起来。**关键细节**：对于 WT-MetaD，必须加 `--kt` flag 才能让 sum_hills 自动应用 γ/(γ-1) 校正得到 F(s,z)：

```bash
plumed sum_hills --hills HILLS --outfile fes.dat --mintozero --kt 0.695
```

其中 kT = 0.695 kcal/mol（350 K）。PLUMED 用这个 kT 值加上 HILLS 文件里记录的 bias factor 来计算 γ/(γ-1) 校正。

> **⚠️ 操作级陷阱**：不加 `--kt`，sum_hills 输出的是 raw -V_bias(s,z)，不是 F(s,z)。所有 ΔG 值会系统性偏差 ~11%（γ=10 时）。这个错误不会改变 FEL 的拓扑（basin 位置和排序不变），只影响深度和 barrier 高度——所以很容易犯且肉眼难以发现。

**理解方式 2（Boltzmann reweighting，更通用）**：

对于任何 biased trajectory（不只是 MetaD），原理是：

在 biased 模拟中，帧 i 的 Boltzmann 权重被偏置扭曲了。要恢复 unbiased 分布，需要给每一帧一个 reweighting factor：

```
w_i = exp( +V_bias(s_i, t_i) / kT )
```

然后用这些权重计算任何 observable 的 unbiased 期望值。这就是为什么你可以从 biased 轨迹计算 unbiased 的 K82-Q₂ distance 分布——只要正确 reweight。

**Adaptive Gaussian width**：hill 的宽度根据局部 FES 曲率自动调节。陡峭处用窄 hill，平坦处用宽 hill。减少手工调 σ 的脆弱性。

> **常见误解**："MetaDynamics 只是加速版 MD。" 不完全对。MD 采的是 canonical ensemble，MetaD 通过加 bias 改变了采样分布。你得到的不是"更快的真实轨迹"，而是 biased trajectory + 可从中重建 unbiased free energy 的 HILLS 文件。

---

### Step 10: 10 Walker 设置

**一句话直觉**：10 条并行模拟共享偏置信息，比 1 条长轨迹更快覆盖所有重要 basin。

**为什么不是 1 条长轨迹**：
1. **并行效率**：10 × 50 ns 的 wall-clock 时间比 1 × 500 ns 短 ~10 倍
2. **初始构象多样性**：10 walkers 从不同起始构象出发，避免被某一个 basin 长期困住
3. **协作探索**：walker A 填的坑，walker B 直接站在上面继续探索

**Snapshot 怎么提取**：从 500 ns conventional MD 或初步 single-walker MetaD 中选取覆盖不同 s(R) 区域的 10 个 snapshot。关键是多样性——不能 10 个 walker 都从 Open 态出发。

**HILLS 共享机制**：所有 walkers 读写同一个 HILLS 文件（或定期同步）。每个 walker 在计算下一步 bias 时，用的是所有 walkers 累积的 bias 历史。

> **常见误解**："10 walkers = 10 次独立模拟取平均。" 完全不是。它们共享 bias，是协作探索。每个 walker 受益于其他 walkers 已做的工作。

---

### Step 11: FEL 重构与解读

**一句话直觉**：把 MetaD 堆的所有山丘反转（乘以 -γ/(γ-1)），得到蛋白质构象的自由能地图。

**sum_hills 做什么**：

```bash
plumed sum_hills --hills HILLS --outfile fes.dat --mintozero --kt 0.695
```

把所有 walkers 的 bias 历史加起来，通过 `--kt 0.695`（350 K 对应的 kT，单位 kcal/mol）自动应用 γ/(γ-1) 校正，输出二维网格上的自由能值 F(s,z)。**不加 `--kt` 则输出 raw -V_bias，所有能量值偏 ~11%。**

**Basin / Barrier / ΔG 怎么读**：

| 特征 | 定义 | 用 kT 标注的阈值（350 K, kT ≈ 0.7 kcal/mol） |
|------|------|------|
| **Basin** | FEL 上的局部极小（蓝色谷底） | — |
| **Barrier** | 两个 basin 之间的最高点 | < 1 kT (~0.7 kcal/mol)：热涨落量级，接近自由切换 |
| | | 2-4 kT (1.4-2.8 kcal/mol)：可切换，但比 barrier-free 慢 1-2 个数量级 |
| | | > 15 kT (~10 kcal/mol)：在模拟时间尺度上基本被困住 |
| **ΔG(closed)** | G(C basin 最低点) - G(O basin 最低点) | ΔG < 0 → Closed population 更大 |

**O/PC/C 状态对应**：s(R) 1-5 = Open, 5-10 = PC, 10-15 = Closed

> **措辞注意**：ΔG < 0 说明 Closed 态热力学上更稳定、population 更高。这与更高的催化活性**正相关**（在 Osuna 的 3 个 TrpB 变体中观察到），但不能直接从 ΔG 数值推导 kcat。正确的说法是"ΔG 越负，productive closure 的 population 越高，这与活性趋势一致"，而不是"ΔG 负 = 活性高"。

**Productive vs. Unproductive Closure — 最关键的洞察**：

不是所有"到了 s=10-15"的构象都有催化能力。还需要后验分析指标：

| 指标 | 阈值 | 含义 | 来源 |
|------|------|------|------|
| COMM RMSD | < 1.5 Å | 相对 Closed 参考态的骨架偏差够小 | JACS 2019 Figure 3 analysis |
| K82-Q₂ distance | ≤ 3.6 Å | 赖氨酸和辅因子中间体足够近，催化几何正确 | JACS 2019 Figure 3 |

**s(R)/z(R) 是被加偏置的 CV（MetaD 的输入）。COMM RMSD 和 K82-Q₂ distance 是后验分析指标（对输出的解释工具）。不能混为一谈。** 这是项目中 FP-001 明确标记的概念边界。

**K82-Q₂ 距离的 reweighting 问题 — 回答追问 Q2**：

K82-Q₂ distance 没有被 bias，所以从 biased trajectory 直接测量**每一帧的几何值是准确的**（bias 不影响原子位于某个构型时的几何关系）。但是，如果你想知道"K82-Q₂ < 3.6 Å 的**概率是多少**"——即 population 统计——就需要 reweight。

因为 biased trajectory 在不同 basin 的停留时间被偏置扭曲了（barrier 低的 basin 被反复推走，停留时间比 equilibrium 短），直接数帧会给出错误的 population 比例。正确做法：

```plumed
rw: REWEIGHT_BIAS TEMP=350
hh: HISTOGRAM ARG=K82_Q2_DIST GRID_MIN=2.0 GRID_MAX=8.0 GRID_BIN=200 LOGWEIGHTS=rw
DUMPGRID GRID=hh FILE=k82_q2_reweighted.dat
```

总结：**每帧的几何值 = 可以直接测；population 分布 = 必须 reweight。**

---

## Part D：收敛判断与文献对比

### 收敛判断 — 回答"不理解 C"

**一句话直觉**：怎么知道 MetaD 跑够了？看自由能面是否不再随时间漂移。

**具体操作**（Block averaging）：

1. 把总模拟时间切成时间窗（如 0-100 ns, 100-200 ns, 200-300 ns ...）
2. 对每个窗口分别运行 `sum_hills --kt 0.695`，得到该时间段的 FES
3. 比较连续窗口的 FES：
   - 主要 basin 的位置是否稳定？
   - O-C basin 之间的 ΔG 是否趋于平台？
   - 是否有新 basin 突然出现？

**收敛的三个必要条件**：
1. **ΔG 平台**：连续时间窗的 O-C 相对能差变化趋于零
2. **Basin 拓扑稳定**：不再出现新的 basin 或已有 basin 的消失
3. **后验一致性**：K82-Q₂ distance 和 COMM RMSD 的 basin 归属与 FES 解释一致

> **没有普适的数值阈值。** "ΔG 变化 < 某个数就算收敛"取决于你需要的精度。JACS 2019 SI Figures S4-S5 展示的是 O/C 能量差随时间的演化，用的是视觉判断（曲线趋平）。如果要给一个 operational guideline：**当最后几个时间窗的 ΔG 变化幅度小于你关心的 basin 间能差的 1/3-1/2 时，可以认为初步收敛。** 比如如果 O-C 能差约 3 kcal/mol，变化 < 1 kcal/mol 算初步收敛。

> **收敛是必要条件，不是充分条件。** 如果 CV 漏掉了关键慢自由度，FES 可能收敛到一个错误的面——看起来"不再变了"，但是错的。这不是增加时间能解决的问题。

---

### 与 JACS 2019 对比

**对比顺序**（不要先盯着图像不像）：

1. FES 上主要 basin 的位置是否在合理的 s(R) 区间
2. O/PC/C 的相对稳定性**排序**是否与文献一致
3. Closed-like 区域的 z(R) 是否足够低（避免 off-path basin 被误认为真正闭合）
4. Reweighted K82-Q₂ distance 和 COMM RMSD 是否支持 productive closure
5. 不同时间窗 FES 是否趋于平台

**容忍度**：关键是**排序和定性特征一致**，不追求数值精确复刻。Basin 位置偏差 < 1-2 个 s(R) 单位算合理。ΔG 的绝对值偏差受力场精度、CV 局限、采样统计共同影响——在 ff14SB + GAFF/RESP 的精度下，期望绝对值完全一致是不现实的。

---

## Part E：FEL 在 TrpB 上说了什么

### 三种 TrpB 变体的 FEL 对比（**均为 Q₂ 中间体阶段**）

> **重要**：以下所有 FEL 描述和 kcat 关联分析，都是在 **Q₂（quinonoid 中间体）阶段**做的。不同催化中间体（Ain, Aex1, A-A, Q₂）的 FEL 拓扑完全不同。不能把 Q₂ 的结论直接泛化到其他中间体。

| 变体 | FEL 特征（Q₂ 阶段） | K82-Q₂ 距离 | kcat (s⁻¹) | 解读 |
|------|---------|------------|------|------|
| **PfTrpS** (αβ复合体) | O 和 PC 有 basin，C 态较高但可达 | ~3.6 Å（部分 productive） | 1.0 | TrpA 帮助 TrpB 偶尔"关到位" |
| **PfTrpB** (isolated) | 只有 O 区域 basin | > 4 Å（unproductive） | 0.31 | 没有 TrpA，COMM domain 关不到催化位置 |
| **PfTrpB0B2** (evolved) | O/PC/C 都有 basin，barrier ~2-3 kT | ≤ 3.6 Å（productive） | 2.9 | 6 个突变重塑 FEL，productive closure 变得容易 |

> K82-Q₂ 距离值来自 FEL 局部极小对应的代表性构象簇（结构聚类），不是单帧测量。

**核心结论**（Osuna 自己的表述）：**Population shift toward productive Closed conformations correlates with higher catalytic activity.** 这是一个在 3 个 TrpB 变体上观察到的 qualitative/mechanistic correlation，不是定量公式。

**为什么 PfTrpB0B2 的 6 个点突变能"重塑" FEL — 回答追问 Q4**：

这个问题很好，有两层回答：

**层次 1（结构层面）**：6 个突变中 60% 位于 COMM domain 或 α/β 界面。这些突变改变了残基间的非共价相互作用网络——盐桥断/成、氢键重排、疏水接触改变。这些"局部"的相互作用变化，改变了 COMM domain 关闭时的能量 balance：

- 如果某个突变让 Closed 态新形成了一个稳定盐桥（ΔG ~-2-5 kcal/mol），就可能把 Closed 从"不稳定"变成"和 Open 差不多"甚至"更稳定"
- 如果几个突变协同作用，可以创造一个全新的低能 basin

**层次 2（ensemble 层面）**：突变不只改变"结构像不像 Closed"，还改变"Closed 态的构象空间有多大"（entropy effect）。一个 basin 的自由能 = enthalpy - T×entropy。如果突变增加了 Closed 态的构象灵活性（更多 sub-states），entropy 贡献可以让这个 basin 更稳定，即使 enthalpy 没变多少。

> Osuna 2019 没有区分这两种效应。这是 FEL 的一个内在局限——F(s,z) 是 free energy（已包含 entropy），你无法从中分离 enthalpy 和 entropy 贡献。

**对你的项目意味着什么**：如果 GenSLM 生成的新 TrpB 序列的 FEL（Q₂ 阶段）显示出类似 PfTrpB0B2 的特征（productive C 态可达且稳定），那它**更可能**有高活性。反之亦然。但"更可能"≠"一定"。

---

## Part F：FEL 的局限——什么信息 FEL 给不了

1. **化学步骤**：FEL 只看构象变化，不包含键的断裂与形成。PLP 催化循环的化学势垒需要 QM/MM，不是经典力场 MetaD 能给的。

2. **Binding affinity**：FEL 不直接告诉底物进出的难易程度。

3. **产物释放**：涉及不同构象通道，不一定在 O→C path CV 上。

4. **CV 覆盖完整性（最根本的局限）**：Path CV 只描述沿 O→C 路径的投影。任何正交的慢运动都被"压扁"了。这不是增加时间能解决的——CV 质量是 FEL 质量的硬上限。

5. **收敛不确定性**：即使收敛了，绝对自由能值也有误差。当 basin 深度差只有 2-3 kcal/mol 而误差 ~1 kcal/mol 时，排序可能翻转。**FEL 的拓扑（哪些 basin 存在）比定量深度更可靠。**

6. **力场依赖**：FEL 只和 Hamiltonian（力场）一样好。ff14SB + GAFF/RESP 是一种近似。不同力场（如 CHARMM36m）可能产生不同的 FEL。对 COMM domain 的大尺度骨架运动，ff14SB 是 defensible 的；但对 PLP 化学细节，GAFF 的精度有限。

**CV 质量怎么评估 — 回答追问 Q3**：

没有完美的 diagnostic，但有几个后验信号：

1. **z(R) 分布**：如果 z(R) 在 MetaD 过程中持续飙高且不回落，说明体系经常跑到远离参考路径的地方——Path CV 可能没有覆盖真正重要的构象空间。

2. **Diffusion in CV space**：如果体系在某个 s(R) 区间反复振荡但不离开（even with bias pushing），可能有一个正交慢变量把它困住了。

3. **Reweighting consistency test**：用两种不同方法重建 FES（`sum_hills --kt 0.695` vs. Boltzmann reweighting），看结果是否一致。大幅不一致 = CV 可能有问题。

4. **最根本的检验**（也是方向 1）：用 ML 方法（Deep-TDA）学习 CV，看是否发现新通道。如果 ML CV 和 Path CV 给出相同的 FEL 拓扑 → Path CV 够用；如果不同 → Path CV 遗漏了重要自由度。

---

## Part G：你在 Anima Lab 的角色定位

### Anima Lab 的"AI for Science"大图景

Anima Lab（Caltech, Anima Anandkumar）不只做 GenSLM TrpB。他们的核心方法论是：**用大模型 + geometry-aware networks + scientific ML workflow 加速科学发现**。具体项目包括 Neural Operators（偏微分方程）、FourCastNet（天气预报）、physics-constrained generative models 等。GenSLM TrpB 是他们在蛋白质/酶方向的一个 application——用 genome-scale 语言模型生成新酶序列。

### GenSLM 的关键事实

- **不是普通 protein LM**：在 DNA codon 级别（64 个 token）而非 amino acid 级别（20 个 token）工作，保留了同义替换信息
- **规模**：在 ~1.1 亿条原核基因序列上预训练，TrpB 用 25M 参数版本 fine-tune
- **生成 pipeline**：ATG prompt → autoregressive sampling → length/ESMFold pLDDT filtering → 105 条进实验
- **关键设计决策**：Lambert 2026 **故意没有使用** physics-informed filters（docking, thermostability），避免过早引入 proxy bias
- **实验结果**：GenSLM-230 活性超过 PfTrpB0B2，且对多种非天然底物有活性

### 你擅长什么 / 不擅长什么

| | 你 | Anima Lab |
|---|---|---|
| **擅长** | MD 实操（PDB→production MD）、增强采样 protocol、FEL 物理解读 | AI 模型训练、大规模 sequence generation、HPC pipeline |
| **不擅长** | AI 模型训练、GenSLM 架构修改 | 全原子 MD 实操、力场参数化、FEL 的 mechanistic interpretation |

### 交叉点 = 你的 unique value

```text
Anima Lab: "我们能生成新 TrpB 序列，并用实验证明有些有活性"
     ↓
你: "我能用 FEL 解释为什么有些有活性——通过 COMM domain 构象动态"
     ↓
未来: "这个 physics signal 能不能反馈回生成模型？"
```

你不是"帮 Anima Lab 跑模拟的人"。你是 **bridge person**——把 GenSLM 的 sequence output 翻译成 physics-based conformational labels。

### 诚实的边界

- 你是本科暑研生，3 个月。目标是 **demonstrate capability**：跑通 benchmark + 做出 interpretable FEL
- Realistic scope：benchmark reproduction + 对 GenSLM-230 的第一次 MetaD comparison
- 不 claim 你已经解决了 closed-loop design 问题
- 如果被问"FEL filter 比 ESMFold pLDDT 更好吗"，诚实回答："还不知道。Benchmark 正是为了建立 calibration baseline。"

---

## Part H：新研究方向

### 回答追问 Q6：FEL-activity 只是 qualitative，怎么当 reward function？

这是整个项目最核心的张力。诚实的回答：

**这个暑假不需要解决定量问题。** 目标是：

1. **Benchmark 复刻成功**：证明你的 FEL 和 Osuna 一致 → 方法可信
2. **对 GenSLM-230 做 MetaD**：得到第 4-5 个 calibration point
3. **检验 rank-order consistency**：FEL 特征（productive C 态深度、barrier 高度）的排序是否和 kcat 排序一致？

> 如果 3-5 个变体的 Spearman rank correlation ρ > 0.8，这就是 sufficient justification 来 propose 更大规模的 calibration study。如果排序不一致，项目 pivot 到理解"为什么 FEL-activity mapping 在某些变体上 break down"——这同样有发表价值。

**关键认识**：你不需要 ΔG → kcat 的定量公式。你需要的是 **rank-order prediction**——"哪个变体 FEL 最好看"是否对应"哪个变体活性最高"。这比定量回归容易得多，也更 robust。

---

### 方向 1（推荐优先级最高）：Path CV vs. ML-learned CV — Osuna 的 FEL 有多完整？

**问题**：Deep-TDA 或 Deep-LNE 从数据驱动学习的 CV，是否会发现 Path CV 遗漏的构象通道？

**为什么重要**：直接检验 Osuna 2019 FEL 的完整性。如果一致 → 独立验证；如果不一致 → novel contribution。

**可行性**：FEASIBLE（如果 benchmark 及时完成）。需要 ~50-100 ns unbiased MD 训练 Deep-TDA → OPES 重跑 → 比较。额外 2-3 周。

**回答追问 Q5 和 Q7 — Deep-TDA 具体怎么做？是否有循环论证？**：

训练输入：每帧的原子坐标（通常是 Cα 坐标或某些 inter-residue distances），不是全原子。

训练标签：Deep-TDA 需要定义 target meta-stable states。**这里有两种策略**：

**策略 A（用 Path CV 的 basin 做标签）**：的确有循环论证的 flavor。但科学上是 defensible 的：你用 Path CV 定义的 basin 作为 *initial hypothesis*，训练 ML CV 后看它是否发现 *additional* basins。如果 ML CV 只看到同样的 3 个 basin → Path CV 完整性被 validated。如果发现第 4 个 basin → Path CV 不完整，且发现本身就证明了 ML CV 的价值。

**策略 B（用无偏 MD 聚类做标签）**：从 500 ns conventional MD 中用 TICA + k-means 聚类得到 meta-stable states。不依赖 Path CV 的 prior。更独立，但需要 conventional MD 本身采到足够多的构象多样性——对 TrpB 可能不够（500 ns 可能只在 O 态附近采样）。

训练数据量：一次 10-walker MetaD 产生 500-1000 ns 轨迹，每帧 ~1 ps → ~10⁵-10⁶ 帧。对 Deep-TDA 的 neural network（通常 2-3 层 MLP）来说，**数据量充足**。

**PI 可能的挑战**："如果两种 FEL 完全一致，这 publishable 吗？" **Yes。** 方法学验证本身有价值——"Path CV adequately captures TrpB COMM domain dynamics" 是一个有信息量的结论，尤其在 Yang et al. 2025 质疑了 empirical CVs 之后。

---

### 方向 2（推荐优先级第二）：Rank-order FEL-to-activity calibration

**问题**：FEL 特征的排序是否和实验 kcat 排序一致？

**怎么做**：不是 regression model（数据点太少会 overfit），而是 Spearman rank correlation。对 3-5 个有 FEL + kcat 的变体，计算 FEL 特征（ΔG、productive closure probability）的排序和 kcat 排序的 ρ。

**最低 bar**：如果 ρ > 0.8 且 p < 0.05（对 5 个数据点，ρ > 0.9 才能 p < 0.05），就有统计支撑说"FEL 排序能预测活性排序"。

**可行性**：MARGINAL。取决于能否在暑假内对 5+ 个变体完成 MetaD。计算上可行（3-7 GPU-days each），瓶颈是体系准备。

> **PI 挑战**："5 个点的 Spearman ρ 有什么统计意义？" 答案是承认 power 很低，但这是第一次在 TrpB 上做系统性 FEL-activity 对比。即使 ρ 不显著，rank mismatches 本身也是有价值的——它们指向"FEL 筛选在哪些情况下会失败"。

---

### 方向 3（降级为"开放问题"，不推荐作为暑研目标）：偏置势转移

**回答追问 Q8**：据我所知，**没有发表过的蛋白质体系偏置势转移工作**。小分子体系有一些相关工作（如 "funnel MetaDynamics" 的 bias initialization），但蛋白质构象变化的 CV 空间维度和复杂度完全不同。

**操作机制**（回答"不理解 D"）：概念上是把体系 A 已收敛的 HILLS 文件直接作为体系 B 的初始偏置——PLUMED 支持从预存 HILLS 重启。但问题在于：

1. 如果 B 的真实 FES 和 A 的拓扑不同（比如 B 有一个 A 没有的 basin），A 的偏置可能恰好把 B 推离那个新 basin → 你会**错过** B 最重要的特征
2. Path CV 的参考路径对 A 和 B 是同一条（都是 1WDW→3CEP），但突变可能改变了路径沿线的能量分布 → 转移的偏置假设了错误的 FES 形状

**判定**：这是一个 research *question*（"偏置势转移对序列变体有效吗？"），不是一个可以在暑研中执行的 direction。需要先有多个变体的独立 FEL 作为 ground truth，然后系统比较"转移 vs. 从头做"。这应该放到项目的 future work section，不应该作为暑研 deliverable。

---

## 5 个 PI 会问的问题 + 你的回答模板

### Q: "你怎么保证你复刻出的 FEL 是对的？"

> "对比分两层。第一层是 FEL 拓扑——basin 的数量、位置（O/PC/C 区间）、相对排序是否和 JACS 2019 Figure 2 一致。第二层是后验指标——reweighted K82-Q₂ distance 是否落在 productive 区间。我不追求 ΔG 的绝对值完全一致，因为力场精度和 CV 局限会引入系统误差。但如果 basin 排序和 productive closure 判据都一致，就足以说明 protocol 是可信的。"

### Q: "你怎么知道你的 Path CV 没有漏掉重要的构象通道？"

> "坦白说，目前我不知道——这正是我计划做 ML CV vs. Path CV 对比的原因。Path CV 假设 O→C 转换大致沿参考路径发生。如果真实路径有大曲率或正交分支，Path CV 会压扁它们。Yang et al. 2025 已经证明了 empirical CVs 可能产生 non-physical features。Deep-TDA 是一种 data-driven 的 CV，可以不依赖手工路径来发现 metastable states。如果两者给出相同的 FEL，Path CV 被验证；如果不同，就找到了 Path CV 遗漏的东西。"

### Q: "FEL-activity 关系只是 qualitative（3 个数据点），你怎么用它做筛选？"

> "我不需要定量公式。我需要的是 rank-order prediction——FEL 特征排序能否预测活性排序。这个暑假的目标是在 3-5 个变体上检验 rank consistency。如果一致，它就是一个有 mechanistic grounding 的 filter——比纯 sequence-based 的 ESMFold pLDDT 多了一层构象动态信息。如果不一致，我需要理解为什么——可能是 FEL 特征不够完整，也可能是某些变体的活性主要受化学步骤而非构象变化控制。"

### Q: "MetaDynamics 太慢了（3-7 天/变体），你怎么 scale？"

> "对，全原子 WT-MetaD 不适合筛选 60,000 个候选。实际策略是分层：先用便宜的 sequence/structure filters（ESMFold, SPM, 短 MD）把候选从 ~1000 缩到 ~50，再对 top 50 做 MetaD。MetaD 在这个 pipeline 里的角色是 second-stage mechanism-aware filter，不是 first-round brute-force screen。"

### Q: "这个项目和 Anima Lab 的其他工作有什么交叉？"

> "最直接的交叉是：Anima Lab 的 GenSLM 负责 proposal（生成候选序列），我负责 conformational physics validation（用 FEL 判断哪些候选的构象动态支持催化）。长远看，如果 FEL 特征可靠，可以把它蒸馏成 ML surrogate，作为 GenSLM 下一轮生成的 reward signal。但这个暑假的目标更具体：先证明这层 physics validation 本身是可信的。"

---

> **文档版本**：v1.0, 2026-04-01
> **审阅者**：mentor (FEL expert), critic (scientific rigor), student-proxy (learner perspective)
> **状态**：三轮审阅收敛完成
