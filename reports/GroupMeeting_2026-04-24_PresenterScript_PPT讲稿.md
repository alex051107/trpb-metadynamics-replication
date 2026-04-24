# GroupMeeting 2026-04-24 — PPT 讲稿

> **用法**: 对着念，每张 slide 对应 1-3 段话；口语，不要书面语
> **Meeting**: 1-on-1 with Yu Zhang · 2026-04-24 · ~20 min + 10 min Q&A
> **Deck arc**: 转折点 → 上周卡点 → Miguel contract → 排除假设 → FP-034 核心 → 修复结果 → 生物学 sanity → pilot → next
> **核心 hook**: "500 倍的加速"

---

## Slide 1 — Title: Week 7 — A Turning Point
（约 30-45 秒）

好，今天这次组会我想定义成整个 replication 项目的一个**转折点** week。

为什么是转折点。因为我们这周的关键 insight 是这样的：过去五六周我们一直在 MetaD layer 调参数——调 SIGMA、调 HEIGHT、调 wall——但这周我们终于发现，**真正阻塞 replication 的根本不是 MetaD 参数，是 path 坐标本身的定义方式**。换句话说，我们一直在对一把测量错的尺子做校准，尺子本身是错的。

这个发现直接带来一个数字：path 坐标修对之后 λ 提升了 **27 倍**，pilot 轨迹上的 s(R) 越过 basin 边界的速度拉开了 **500 倍**。这是今天最重要的两个数字。

---

## Slide 2 — 上周到本周一：所有 MetaD-layer 调参都失效
（约 1.5-2 分钟）

先快速过一下上周末到本周一的 timeline，这是我们最终意识到"参数 layer 已死"的那个过程。

上周五交给你的是 single-walker 50 ns 续跑，max s=3.494，卡在 O basin 出不去。我们当时的诊断方向是"sigma 太小 + height 太低"。接下来我做了三件事：第一，**把 HEIGHT 从 0.628 加倍到 1.25 kJ/mol**——没用，walker 还是 stall 在 s≈1.5；第二，**加 SIGMA floor 到 0.5 s-units**——也没用；第三，**加一道 wall 在 s=1.2 把 walker 往前推**——wall 倒是生效了，但数据显示 walker 撞到 wall 后就在 wall 上来回震荡，它不是"不想走"，它是"走不动"。

还有一个更有说服力的失败：我当时做了一个 PC 插值实验，手动把 MODEL8（中间 PC 态）插到 path 中段，重新算 λ，结果 λ 数值变化不到 5%。也就是说**无论我怎么动 MetaD 参数、怎么重排 path 的中段，整套 CV 的 sharpness 都没改善**。

到周一晚上结论就很明确了：**所有 MetaD-layer 的调参全都没用，问题一定在下层。** 下层就是 path 坐标本身。

---

## Slide 3 — Miguel contract: 作者亲自确认的参数
（约 2 分钟）

然后周二 Miguel 回信了。Miguel 是 Osuna 2019 的第一作者。这封回信我觉得值得单独拿一张 slide，因为它是 contract-level 的确认。

Miguel 给我们确认了两件事。第一件**FP-031**：之前我们 tutorial 里一直写 path CV 用的是 GEOM（几何几何距离），但 Miguel 说实际上 SI 里是 DIFF——DIFF 模式计算的是每对 snapshot 之间的 CV 差分平方和，而不是三维 Cartesian 距离。这个更正对 λ 的数值尺度有直接影响。第二件是 SIGMA、HEIGHT、BIASFACTOR 这些数值他都——确认。

**但是**——这是今天最关键的一个"但是"——Miguel **没有给我们 PATH.pdb 文件**。他只给了参数，没给坐标。这句话要记住，因为它就是后面 FP-034 bug 存在的前提。如果他当时发了一个 reference path 给我，我们就会直接对比、直接发现 mismatch，这个 bug 就不会存活两个月。但他没发，所以 path 构建这一步我们仍然在"自己造"的状态。

（停一下）所以周二的状态是：参数已 contract，坐标未 contract。问题只能在坐标。

---

## Slide 4 — 排除法：A/B/C 都被数据反驳
（约 1.5 分钟）

周三我系统性地用排除法把四个候选假设走了一遍。

**假设 A：Gaussian height 不够。** 反驳依据是前面说的——HEIGHT 从 0.628 加到 1.25 kJ/mol 没有任何改善，walker 的 stall 位置一模一样。pass，A 不是原因。

**假设 B：SIGMA floor 太低导致 Gaussian 塌成针尖。** 反驳依据是我们已经加了 SIGMA_MIN=0.3,0.005，HILLS 第 4 列读出来 σ_sss 从来没有低于 0.3。所以针尖假设在当前 run 里不成立。

**假设 C：Wall 设置有问题。** 反驳依据是加了 wall 以后 walker 直接撞 wall，这说明它**不是 wall 挡着它走**，是它根本没有沿 path 运动的驱动力。

A、B、C 都被数据反驳掉以后，剩下的只有 **D：path geometry 本身有问题**。这就把我们逼到 Slide 5——去看 path 是怎么构建的。

---

## Slide 5 — FP-034: 跨物种 residue number offset （核心）
（约 3 分钟）

好，Slide 5 是本周的核心，我会讲慢一点。

我们的 path CV 是用两个参考结构的插值算出来的：5DVZ 是 open state，4HPX 是 closed state。但是——**这两个是不同物种**。5DVZ 是 PfTrpB（Pyrococcus furiosus），4HPX 是 StTrpS（Salmonella typhimurium）。不同物种最麻烦的一件事是：**同一个序列位置在两个 PDB 里的 residue number 完全不同**。

看这张表（指向 slide 上的 residue offset 对比）。Pf 的 residue 56 对应 St 的 residue 53，Pf 的 residue 100 对应 St 的 residue 96——**整条链上有一个系统性的 3-4 残基 offset**。如果你直接按 residue number 去对齐 COMM domain 的 Cα——也就是说你以为你在比同一个残基的 Cα 位移，其实你比的是 "Pf 的 Phe95" vs "St 的 Tyr92"——这种情况下 per-atom MSD 会被人为放大。

（这里 pause for effect）现在最打脸的事情来了。我们仓库里早就有一个脚本叫 **`generate_path_cv.py`**。这个脚本**确实**调用了 Needleman-Wunsch sequence alignment，**确实**输出了一张 alignment 表。但是，**下游的坐标提取根本没用这张 alignment 表**——它用的是 raw residue number。alignment 被算出来了，然后被扔掉了。这是一个 silent bug，活了两个月。

为什么 silent？因为它不会报错。Kabsch 还是会跑，MSD 还是会出数字，λ 还是会算出来——只不过这些数字全都是错的。

这就是 **FP-034**：**跨物种 path CV 构建必须 wire up sequence alignment 到坐标提取阶段，不能只算不用。** 防范措施第 5 条是：从此以后坐标提取函数必须接收 alignment table 作为参数，并 assert "使用的 residue number 必须出自 alignment table"。

---

## Slide 6 — NW 修复之后：四个数字并排
（约 2.5 分钟）

修复很简单：把 Needleman-Wunsch 的输出真正 wire 到坐标提取里，让 Pf residue 100 对应 St residue 96 这种 mapping 被真正使用。

修复以后跑出来的数字——这张 slide 上的四个数字——我希望你记住。

**第一，sequence identity**：修复前 6.2%，修复后 **59.0%**。6.2% 是什么意思？说明我们之前对齐的那 112 对 Cα 里只有 7 个真的是同源残基，剩下 105 个是在瞎对。59% 才是 TrpB 保守 COMM domain 的真实同源水平。

**第二，端点 RMSD**：10.89 Å → **2.12 Å**。10.89 Å 对于 COMM domain 的 O→C 运动来说已经大到荒谬——COMM 的整体位移本来也就 4-5 Å。2.12 Å 才是合理的。

**第三，MSD_adj**（相邻帧 per-atom mean squared displacement）：0.606 nm² → **0.023 nm²**。缩小了 26 倍。这意味着 path 上相邻帧之间的"距离"从巨大变成了合理。

**第四，λ**：3.80 → **100.79 nm⁻²**。注意这里 λ 上升 27 倍不是因为公式变了，是因为 MSD_adj 分母变小了——λ = 2.3 / MSD_adj。

然后我做了两个独立的 self-consistency check。第一个是 Branduardi 的 kernel weight check——λ·MSD_adj 应该落在 2.3 附近，我们现在是 **2.32**，完全对。第二个是 driver self-projection：把 15 帧 reference 每一帧扔回 PLUMED driver，算出来的 s 应该是 1、2、3...15——我们跑出来完全 monotonic。

最后 Codex 独立复核了这整套修复，**7 项 check 里 7 项 PASS，1 项 inconclusive**（那一项是等 pilot 数据，今晚能出）。

---

## Slide 7 — 生物学 sanity check
（约 1.5 分钟）

修完之后我做的第一件事不是跑 pilot，而是——**拿三个已知结构往修好的 path 上投影，看它们落在哪里**。

5DW0 和 5DW3 是已知的 PC（partially closed）中间态，5DVZ 是 open。修好以后：5DVZ 落在 **s=1.1**（path 起点附近，完全合理），4HPX 落在 **s=14.9**（path 终点附近），**5DW0 落在 s=5.4，5DW3 落在 s=8.1**——两个 PC 结构干净地落在 path 中段，刚好是 O→C 转换应该发生的位置。这是一个强生物学 sanity check。

这里还要坦白一件事。上周我们做过一个叫 **path_piecewise audit** 的分析，结论是"MODEL8 落在 s=4 附近，所以 PC 被 path 误分类成 O 态"。那个 audit 其实**结论是错的**。错在哪——错在**它是在 naive path 上做的判断**，而 naive path 的 s 坐标本来就被 residue offset bug 污染了。这是 FP-034 的下游污染之一。我已经把那份 audit 标记为 "superseded by FP-034 sequence-aligned path"。

这也提醒我们：任何基于错误 CV 的下游结论都要重审。

---

## Slide 8 — Pilot 结果：500× 加速
（约 2.5 分钟）

好，最后上数据。这是本周最兴奋的一张 slide。

我用**完全相同的 start.gro**——就是之前那个 500 ns 经典 MD 的终态——分别在 naive path 和 corrected path 上跑短 pilot。

关键对比是这样的：**同一个 start.gro，在 naive path 上 s=1，在 corrected path 上 s=7**。这一句话信息量很大。它的意思是——**我们之前那个 500 ns 经典 MD 的终态，根本从来不在 O basin**。它一直在 PC region 附近。过去五周我们以为自己的 walker "卡在 O basin 出不去"，实际上 walker 从来就没在 O basin 里——我们只是被错误的 CV **误标注**了。

第二个对比是 pilot 本身的探索速度：**110 ps 的短 pilot 在 corrected path 上就跑到 max s=8.94；之前 naive path 跑了 7.7 ns 才到 max s=1.75**。同样时间单位换算一下，**大概是 500 倍的加速**。这就是今天开场说的那个 500×。

但我**不想 overstate**。这个 pilot 只跑了 110 ps，数据窗口很短。正式的 pilot 正在 Longleaf 上跑，gate 设的是 **max_s > 12**，如果 24 小时内能越过 12，就说明 corrected path 彻底解决了 CV 的 sharpness 问题，我们就可以进 Phase 2 10-walker primary production。如果没越过 12，我们再回来 debate。

---

## Slide 9 — Next steps + Q&A
（约 1 分钟讲 + 10 分钟 Q&A）

Next steps 非常明确。

第一，**明天早上读 pilot 的 max_s**，按 gate 判 Phase 2。第二，**10-walker primary production 的脚本已经 ready**——10 个 starting snapshot 从 500 ns 经典 MD 里挑，按你 2026-04-09 的指示用 PyMOL 眼看挑，不是 strided 的。第三，如果 Phase 2 开跑，预计 2026-05-01 之前能出第一版 FES，和 JACS 2019 Fig 2a 对比。

我就讲到这里。先开 Q&A，我估计你会问几个偏技术的点。

---

## 附录 — Q&A 急救包 / Yu Chen 会问的

| Yu 的问题 | 我的准备回答 |
|----------|-------------|
| "Branduardi kernel weight 在 1.26× 下只 0.16，是不是 too loose？" | Branduardi 建议的 target 是 0.10，tolerance 是 0.05-0.25。我们 **0.16 落在 tolerance 内**。更有说服力的是 driver self-projection—把 15 帧 reference 扔回去，s 值出来是 1, 2, 3...15 **完全 monotonic**，这说明 kernel 的 discrimination 是够的。 |
| "既然 generate_path_cv.py 算了 sequence alignment，为什么下游不用？" | **我坦白这是一个 silent bug**。alignment 被算出来了，写进了一张 table，但下游坐标提取函数硬编码用 `residue.number` 而不是 `alignment_table[residue.number]`。**FP-034 第 5 条防范措施**就是从此以后坐标提取必须接 alignment table 做参数，并 assert "每个使用的 residue number 必须在 alignment table 里存在对应"。 |
| "10-walker starting points 如果都在 s=7 附近，会不会 correlated？" | Starting points 是从 500 ns 经典 MD 里挑的 snapshot，虽然 mean s 大概 7，但 **thermal fluctuation 让实际 s 分布 span ~5-10**。另外 z(R) 方向的 spread 也会提供去相关。如果 Phase 2 跑出来发现 walker 之间 correlation 太高，我们会从更 diverse 的窗口再挑。 |
| "FP-031 GEOM→DIFF 怎么影响 λ？" | DIFF 模式是 CV 空间差分，scale 上和 GEOM 差一个系数。Miguel 确认 SI 里的 0.15 kcal/mol HEIGHT 和 10 BIASFACTOR 都是在 DIFF assumption 下。我们切到 DIFF 之后 λ 本身数值尺度没有因为模式变化而乱跳，主要的 27× 提升来自 residue alignment 修复。 |
| "为什么 naive path 上 start.gro 显示 s=1？" | 因为 naive path 把 residue offset 当成了 "真的位移"，所以任何和 5DVZ 结构接近的 snapshot 都会被错判成 "离起点很近"。corrected path 去掉这个 offset 之后才看到真实的 s=7。 |
| "有没有可能 corrected path 只是 reshift 了坐标，物理意义没变？" | 不是 reshift。reshift 会保持 path 上相邻帧的 MSD 不变。我们的 MSD_adj 从 0.606 **下降到 0.023 nm²**，这是 **geometry 本身变了**——之前那些 MSD 里混了大量"跨物种 residue mismatch 假位移"，修掉以后只剩真的 conformational change。 |
| "FES gate 为什么是 max_s > 12？" | 因为 path 范围是 1-15，**12 对应已经越过 PC middle region 进入 closed 的 vicinity**。max_s > 12 意味着 pilot 能 sample 到 path 的后段，这是 Phase 2 primary production 能 converge 的最低前提。 |
| "这个 bug 存在两个月，有没有更早的 warning signal 被 ignore？" | 有。**端点 RMSD 10.89 Å** 其实早就是个 red flag——COMM domain 的 O→C 位移文献上只有 4-5 Å。我们一直归因于 "flexible loop noise"。FP-034 之后我补了 assertion：**端点 RMSD > 4 Å 必须报警**。 |

---

**讲稿结束** — 总时长估算 ~20 分钟（Slide 1-9）+ 10 分钟 Q&A
